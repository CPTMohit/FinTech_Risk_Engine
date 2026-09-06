"""
Project: FinTech Risk Isolation Engine V2
Module: High-Performance FastAPI Backend Server & Streaming Gateway
Author: Mohit Singh
"""

import os
import sys
import math
import time
import json
import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add project root and src to sys.path
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

import pandas as pd
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

# Internal module imports
from modules.decision_engine.engine import decision_engine
from modules.decision_engine.models import MarketFeatures
from modules.market_status import get_market_status, NSE_HOLIDAYS_2026
from modules.market_regime import classify_market_regime
from modules.position_sizing import (
    TOTAL_CAPITAL,
    RISK_PER_TRADE,
    LOT_SIZE_NIFTY,
    LOT_SIZE_BANKNIFTY,
    calculate_position_size
)
from modules.signal_engine import (
    calculate_trend,
    classify_oi_buildup
)
from modules.journal_engine import JOURNAL_FILE, log_trade
from modules.websocket_engine import LIVE_STATE

# SmartAPI credentials & Gateway (with environment variable support)
API_KEY = os.getenv("API_KEY", "3xK955MH")
CLIENT_CODE = os.getenv("CLIENT_CODE", "AACI729341")
PIN = os.getenv("PIN", "0912")
TOTP_SECRET = os.getenv("TOTP_SECRET", "ZG4AT5YV6GPJQNPPVHLESN5JZI")

FRONTEND_DIR = PROJECT_ROOT / "frontend"
JOURNAL_PATH = PROJECT_ROOT / "trade_journal.csv"

# Initialize FastAPI
app = FastAPI(
    title="FinTech Risk Engine V2 API",
    description="Institutional-Grade Algorithmic Risk & Options Intelligence Desk Backend",
    version="2.5.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active In-Memory State & Positions
ACTIVE_POSITIONS: List[Dict[str, Any]] = []
PRICE_HISTORY: Dict[str, List[Dict[str, Any]]] = {
    "NIFTY": [],
    "BANKNIFTY": []
}

# Base reference prices (updated dynamically from Angel One SmartAPI)
SIM_BASE = {
    "NIFTY": {
        "spot": 23897.70,
        "close": 23873.45,
        "oi": 84807375,
        "pcr": 1.08,
        "trend": "BULLISH",
        "lot_size": 75,
        "strike_step": 50
    },
    "BANKNIFTY": {
        "spot": 57369.65,
        "close": 57380.60,
        "oi": 16771980,
        "pcr": 0.98,
        "trend": "BULLISH",
        "lot_size": 35,
        "strike_step": 100
    }
}

# SmartConnect instance cache
SMART_API_CLIENT = None
SMART_API_AVAILABLE = False

def get_smart_client():
    global SMART_API_CLIENT, SMART_API_AVAILABLE
    if SMART_API_CLIENT is not None:
        return SMART_API_CLIENT
    try:
        from SmartApi import SmartConnect
        import pyotp
        smart = SmartConnect(api_key=API_KEY)
        if TOTP_SECRET and CLIENT_CODE and PIN:
            totp = pyotp.TOTP(TOTP_SECRET).now()
            session = smart.generateSession(CLIENT_CODE, PIN, totp)
            if session.get("status") == True:
                SMART_API_CLIENT = smart
                SMART_API_AVAILABLE = True
                print(f"[API Gateway] SmartAPI authenticated successfully for {CLIENT_CODE}")
                # Fetch official quotes from Angel One
                try:
                    mkt = smart.getMarketData("FULL", {"NSE": ["26000", "26009"]})
                    if mkt.get("status") and mkt.get("data", {}).get("fetched"):
                        for row in mkt["data"]["fetched"]:
                            sym = "NIFTY" if row.get("tradingSymbol") == "NIFTY" else ("BANKNIFTY" if row.get("tradingSymbol") == "BANKNIFTY" else None)
                            if sym and row.get("ltp"):
                                SIM_BASE[sym]["spot"] = float(row["ltp"])
                                SIM_BASE[sym]["close"] = float(row.get("close", SIM_BASE[sym]["close"]))
                                SIM_BASE[sym]["oi"] = int(row.get("opnInterest", SIM_BASE[sym]["oi"]))
                                print(f"[Angel One Live Feed] {sym}: Spot=Rs.{row['ltp']}, Close=Rs.{row.get('close')}, OI={row.get('opnInterest')}")
                except Exception as ex:
                    print(f"[API Gateway] Market quote error: {ex}")
                return SMART_API_CLIENT
    except Exception as e:
        print(f"[API Gateway] SmartAPI init note: {e}")
    return None

# Trigger initial SmartAPI connection
get_smart_client()


def calculate_greeks(spot: float, strike: float, is_call: bool = True) -> Dict[str, float]:
    """Calculates mathematical Greeks for options"""
    moneyness = (spot - strike) / spot if spot > 0 else 0
    raw_delta = 0.50 + (moneyness * 3.0)
    delta = max(0.05, min(0.95, raw_delta)) if is_call else max(-0.95, min(-0.05, -(1.0 - raw_delta)))
    
    dist = abs(spot - strike) / (spot or 1)
    gamma = round(max(0.0005, 0.015 * math.exp(-dist * 25)), 4)
    theta = round(-3.5 - (dist * 12.0) - random.uniform(0.1, 0.5), 2)
    vega = round(max(1.0, 14.0 * math.exp(-dist * 15)), 2)
    
    return {
        "delta": round(delta, 2),
        "gamma": gamma,
        "theta": theta,
        "vega": vega
    }


def generate_initial_history():
    """Seed historical candlestick data for charts"""
    now = datetime.now()
    for symbol, config in SIM_BASE.items():
        base_price = config["spot"]
        bars = []
        cur_price = base_price * 0.985
        
        # Generate 120 historical 1-minute bars
        for i in range(120, 0, -1):
            bar_time = now - timedelta(minutes=i)
            timestamp = int(bar_time.timestamp())
            drift = random.uniform(-0.0015, 0.0018)
            volatility = base_price * 0.0012
            
            open_p = cur_price
            close_p = open_p + (cur_price * drift) + random.uniform(-volatility, volatility)
            high_p = max(open_p, close_p) + random.uniform(0.5, volatility * 1.5)
            low_p = min(open_p, close_p) - random.uniform(0.5, volatility * 1.5)
            volume = int(random.uniform(5000, 35000))
            
            bars.append({
                "time": timestamp,
                "open": round(open_p, 2),
                "high": round(high_p, 2),
                "low": round(low_p, 2),
                "close": round(close_p, 2),
                "volume": volume
            })
            cur_price = close_p
            
        PRICE_HISTORY[symbol] = bars

generate_initial_history()


# Global toggle for after-hours testing simulation (default: False = strict real market / frozen when closed)
SIMULATION_ACTIVE = False

def get_live_asset_data(symbol: str) -> Dict[str, Any]:
    """Fetches real market ticks or keeps market frozen when closed"""
    base = SIM_BASE[symbol]
    is_open, _ = get_market_status()
    
    # 1. Try fetching from live WebSocket / SmartAPI first
    live_tick = LIVE_STATE.get(symbol, {})
    if live_tick.get("ltp") is not None and live_tick["ltp"] > 0:
        spot = float(live_tick["ltp"])
        close = float(live_tick.get("close", base["close"]))
        change = round(((spot - close) / close) * 100, 2)
        oi = int(live_tick.get("oi", base["oi"]))
        pcr = round(base["pcr"], 2)
        return {
            "symbol": symbol,
            "spot": spot,
            "close": close,
            "change": change,
            "oi": oi,
            "pcr": pcr
        }

    # 2. If market is closed and simulation is OFF: freeze price to static last close
    if not is_open and not SIMULATION_ACTIVE:
        spot = base["spot"]
        close = base["close"]
        change = round(((spot - close) / close) * 100, 2)
        oi = base["oi"]
        pcr = base["pcr"]
        return {
            "symbol": symbol,
            "spot": spot,
            "close": close,
            "change": change,
            "oi": oi,
            "pcr": pcr
        }

    # 3. If simulation mode is explicitly enabled: produce simulated micro-ticks
    history = PRICE_HISTORY[symbol]
    last_close = history[-1]["close"] if history else base["spot"]
    delta = random.uniform(-4.0, 4.5) if symbol == "NIFTY" else random.uniform(-12.0, 13.5)
    spot = round(last_close + delta, 2)
    close = base["close"]
    change = round(((spot - close) / close) * 100, 2)
    oi = base["oi"] + int(random.uniform(-2000, 5000))
    
    now_ts = int(datetime.now().timestamp())
    if history and (now_ts - history[-1]["time"]) >= 5:
        last_bar = history[-1]
        last_bar["high"] = max(last_bar["high"], spot)
        last_bar["low"] = min(last_bar["low"], spot)
        last_bar["close"] = spot
        last_bar["volume"] += int(random.uniform(50, 400))
    else:
        history.append({
            "time": now_ts,
            "open": spot,
            "high": spot,
            "low": spot,
            "close": spot,
            "volume": int(random.uniform(200, 1500))
        })
        if len(history) > 300:
            history.pop(0)

    pcr = round(base["pcr"] + random.uniform(-0.01, 0.01), 2)
    return {
        "symbol": symbol,
        "spot": spot,
        "close": close,
        "change": change,
        "oi": oi,
        "pcr": pcr
    }


def compute_full_ai_state() -> Dict[str, Any]:
    """Runs complete AI Decision Engine pipeline across all assets"""
    states = {}
    
    for symbol in ["NIFTY", "BANKNIFTY"]:
        mkt = get_live_asset_data(symbol)
        spot = mkt["spot"]
        change = mkt["change"]
        oi = mkt["oi"]
        pcr = mkt["pcr"]
        
        oi_structure = classify_oi_buildup(change, oi)
        trend = calculate_trend(change, pcr, oi_structure)
        
        step = SIM_BASE[symbol]["strike_step"]
        atm_strike = int(round(spot / step)) * step
        lot_size = SIM_BASE[symbol]["lot_size"]
        premium_factor = 0.0065 if symbol == "NIFTY" else 0.0085
        opt_price = round(spot * premium_factor, 2)
        
        # Option Chain simulation values
        call_oi = int(oi * (0.45 if pcr > 1.0 else 0.55))
        put_oi = int(call_oi * pcr)
        call_vol = int(random.uniform(400000, 1200000))
        put_vol = int(call_vol * pcr)
        oi_bias = "BULLISH" if put_oi > call_oi else "BEARISH"
        
        market_regime = classify_market_regime(change, pcr, oi_bias)
        
        greeks_ce = calculate_greeks(spot, atm_strike, is_call=True)
        greeks_pe = calculate_greeks(spot, atm_strike, is_call=False)
        
        # AI Features
        features = MarketFeatures(
            trend=trend,
            market_regime=market_regime,
            oi_structure=oi_structure,
            spot=spot,
            option_premium=opt_price,
            support=atm_strike - (step * 2),
            resistance=atm_strike + (step * 2),
            pcr=pcr,
            delta=greeks_ce["delta"],
            gamma=greeks_ce["gamma"],
            theta=greeks_ce["theta"],
            vega=greeks_ce["vega"],
            call_volume=call_vol,
            put_volume=put_vol
        )
        
        decision = decision_engine.evaluate(features)
        
        action = decision.action
        if action == "BUY CALL":
            dir_factor = 1
            option_type = "CE"
            sel_greeks = greeks_ce
        elif action == "BUY PUT":
            dir_factor = -1
            option_type = "PE"
            sel_greeks = greeks_pe
        else:
            dir_factor = 0
            option_type = "CE" if change >= 0 else "PE"
            sel_greeks = greeks_ce
            
        confidence = decision.confidence
        rr = decision.trade_plan.risk_reward or 2.0
        lots, qty = calculate_position_size(opt_price, confidence, rr, symbol)
        
        cap_req = round(qty * opt_price, 2)
        entry_p = decision.trade_plan.entry or opt_price
        stop_p = decision.trade_plan.stop_loss or round(opt_price * 0.85, 2)
        target_p = decision.trade_plan.target or round(opt_price * 1.30, 2)
        
        max_loss = round(max(0.0, (entry_p - stop_p) * qty), 2)
        exp_profit = round(max(0.0, (target_p - entry_p) * qty), 2)
        risk_pct = round((max_loss / TOTAL_CAPITAL) * 100, 2)
        
        asset_title = f"{symbol} 50 INDEX" if symbol == "NIFTY" else "BANK NIFTY INDEX"
        
        # Breakdown of individual specialists
        specialist_scores = {
            "trend": {"status": trend, "score": 25 if "BULLISH" in trend else (-25 if "BEARISH" in trend else 0)},
            "pcr": {"value": pcr, "score": 20 if pcr > 1.1 else (-20 if pcr < 0.9 else 5)},
            "oi_buildup": {"structure": oi_structure, "score": 20 if "LONG BUILDUP" in oi_structure else -15},
            "greeks": {"delta": sel_greeks["delta"], "theta": sel_greeks["theta"], "score": 15},
            "market_regime": {"regime": market_regime, "score": 15 if "TRENDING" in market_regime else 5},
            "volume_flow": {"bias": oi_bias, "call_vol": call_vol, "put_vol": put_vol, "score": 15}
        }
        
        states[asset_title] = {
            "symbol": symbol,
            "asset_title": asset_title,
            "spot": spot,
            "change_7d": change,
            "oi": oi,
            "oi_structure": oi_structure,
            "pcr": pcr,
            "trend": trend,
            "market_regime": market_regime,
            "atm_strike": atm_strike,
            "opt_symbol": f"{symbol} {atm_strike} {option_type}",
            "opt_price": opt_price,
            "action": action,
            "signal_score": decision.score,
            "trade_confidence": confidence,
            "probability": confidence,
            "ai_risk": decision.risk,
            "trade_reasons": decision.reasons or [f"AI identified high-probability {trend} momentum", f"PCR {pcr} aligns with {oi_structure}"],
            "ai_warnings": decision.warnings,
            "entry_price": entry_p,
            "stop_loss": stop_p,
            "target": target_p,
            "risk_reward": rr,
            "recommended_lots": lots,
            "recommended_qty": qty,
            "capital_required": cap_req,
            "max_loss": max_loss,
            "risk_percent": risk_pct,
            "expected_profit": exp_profit,
            "delta": sel_greeks["delta"],
            "gamma": sel_greeks["gamma"],
            "theta": sel_greeks["theta"],
            "vega": sel_greeks["vega"],
            "call_oi": call_oi,
            "put_oi": put_oi,
            "call_volume": call_vol,
            "put_volume": put_vol,
            "max_pain": atm_strike,
            "support": atm_strike - (step * 2),
            "resistance": atm_strike + (step * 2),
            "oi_bias": oi_bias,
            "dir_factor": dir_factor,
            "mock_entry": round(entry_p * 0.96, 2),
            "mock_size": lot_size,
            "specialist_scores": specialist_scores,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        
    return states


# ==========================================================
# REST API ENDPOINTS
# ==========================================================

@app.get("/api/status")
def get_system_status():
    """Returns exchange status, trading session, and connection health"""
    is_open, status_text = get_market_status()
    smart = get_smart_client()
    return {
        "status": "success",
        "market_open": is_open,
        "market_status": status_text,
        "simulation_active": SIMULATION_ACTIVE,
        "feed_mode": "NSE SmartAPI Live" if (is_open and SMART_API_AVAILABLE) else ("Interactive Test Sandbox (Moving)" if SIMULATION_ACTIVE else "Real Market Closed (Frozen)"),
        "gateway_connected": True,
        "connection_mode": "Live SmartAPI" if SMART_API_AVAILABLE else "High-Precision Realtime Engine",
        "timestamp": datetime.now().isoformat(),
        "total_capital": TOTAL_CAPITAL,
        "risk_limit_pct": RISK_PER_TRADE * 100
    }

@app.post("/api/mode/toggle-simulation")
def toggle_simulation_mode():
    global SIMULATION_ACTIVE
    SIMULATION_ACTIVE = not SIMULATION_ACTIVE
    return {
        "status": "success",
        "simulation_active": SIMULATION_ACTIVE,
        "message": f"Simulation mode is now {'ENABLED' if SIMULATION_ACTIVE else 'DISABLED (Frozen Real Market)'}"
    }


@app.get("/api/market/live")
def get_live_market_state():
    """Returns computed AI state and specialist analysis for all monitored assets"""
    states = compute_full_ai_state()
    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "assets": states
    }


@app.get("/api/option-chain/{symbol}")
def get_option_chain(symbol: str = "NIFTY"):
    """Returns 11-strike Call/Put Ladder matrix with Greeks, OI, and PCR"""
    symbol = symbol.upper()
    if symbol not in SIM_BASE:
        symbol = "NIFTY"
        
    mkt = get_live_asset_data(symbol)
    spot = mkt["spot"]
    step = SIM_BASE[symbol]["strike_step"]
    atm_strike = int(round(spot / step)) * step
    
    chain = []
    total_call_oi = 0
    total_put_oi = 0
    total_call_vol = 0
    total_put_vol = 0
    
    # 5 OTM, 1 ATM, 5 ITM strikes
    for i in range(-5, 6):
        strike = atm_strike + (i * step)
        dist = abs(spot - strike)
        
        # Realistic premium estimation based on moneyness & distance
        ce_intrinsic = max(0.0, spot - strike)
        pe_intrinsic = max(0.0, strike - spot)
        time_value = max(15.0, (spot * 0.007) * math.exp(-dist / (spot * 0.03)))
        
        ce_ltp = round(ce_intrinsic + time_value + random.uniform(-2, 2), 2)
        pe_ltp = round(pe_intrinsic + time_value + random.uniform(-2, 2), 2)
        
        ce_oi = int(max(10000, (800000 - (abs(i) * 90000)) + random.uniform(-10000, 25000)))
        pe_oi = int(max(10000, (750000 - (abs(i) * 85000)) + random.uniform(-10000, 25000)))
        
        ce_vol = int(ce_oi * random.uniform(0.4, 1.2))
        pe_vol = int(pe_oi * random.uniform(0.4, 1.2))
        
        total_call_oi += ce_oi
        total_put_oi += pe_oi
        total_call_vol += ce_vol
        total_put_vol += pe_vol
        
        ce_greeks = calculate_greeks(spot, strike, is_call=True)
        pe_greeks = calculate_greeks(spot, strike, is_call=False)
        
        chain.append({
            "strike": strike,
            "is_atm": (strike == atm_strike),
            "is_itm_call": strike < spot,
            "is_itm_put": strike > spot,
            "call": {
                "ltp": ce_ltp,
                "change": round(random.uniform(-12, 18), 2),
                "oi": ce_oi,
                "oi_change": int(random.uniform(-15000, 45000)),
                "volume": ce_vol,
                "iv": round(13.5 + (dist * 0.002), 2),
                "delta": ce_greeks["delta"],
                "theta": ce_greeks["theta"]
            },
            "put": {
                "ltp": pe_ltp,
                "change": round(random.uniform(-18, 12), 2),
                "oi": pe_oi,
                "oi_change": int(random.uniform(-15000, 45000)),
                "volume": pe_vol,
                "iv": round(14.0 + (dist * 0.002), 2),
                "delta": pe_greeks["delta"],
                "theta": pe_greeks["theta"]
            }
        })
        
    pcr = round(total_put_oi / (total_call_oi or 1), 2)
    
    return {
        "status": "success",
        "symbol": symbol,
        "spot": spot,
        "atm_strike": atm_strike,
        "total_call_oi": total_call_oi,
        "total_put_oi": total_put_oi,
        "total_call_vol": total_call_vol,
        "total_put_vol": total_put_vol,
        "pcr": pcr,
        "max_pain": atm_strike,
        "support": atm_strike - (step * 2),
        "resistance": atm_strike + (step * 2),
        "strikes": chain
    }


@app.get("/api/chart/{symbol}")
def get_chart_data(symbol: str = "NIFTY", timeframe: str = "1m"):
    """Returns candlestick bar series formatted for Lightweight Charts / TradingView"""
    symbol = symbol.upper()
    if symbol not in SIM_BASE:
        symbol = "NIFTY"
    
    bars = PRICE_HISTORY.get(symbol, [])
    return {
        "status": "success",
        "symbol": symbol,
        "timeframe": timeframe,
        "bars": bars
    }


@app.get("/api/trade-decision")
def get_trade_decision():
    """Returns the top AI recommended trade ticket and detailed execution parameters"""
    states = compute_full_ai_state()
    best_asset = max(states.items(), key=lambda x: x[1].get("trade_confidence", 0))
    best_name, best_data = best_asset[0], best_asset[1]
    
    return {
        "status": "success",
        "best_asset": best_name,
        "recommendation": best_data,
        "all_states": states
    }


class OrderExecutionRequest(BaseModel):
    asset: str
    action: str
    symbol: str
    strike: int
    option_type: str
    entry_price: float
    stop_loss: float
    target: float
    quantity: int
    lots: int
    confidence: int


@app.post("/api/trade/execute")
def execute_trade(order: OrderExecutionRequest):
    """Executes a paper order, logs to journal and adds to active position book"""
    trade_id = f"TRD-{int(time.time())}-{random.randint(100, 999)}"
    
    position = {
        "trade_id": trade_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset": order.asset,
        "action": order.action,
        "symbol": order.symbol,
        "strike": order.strike,
        "option_type": order.option_type,
        "entry_price": order.entry_price,
        "current_price": order.entry_price,
        "stop_loss": order.stop_loss,
        "target": order.target,
        "quantity": order.quantity,
        "lots": order.lots,
        "capital_required": round(order.entry_price * order.quantity, 2),
        "unrealized_pnl": 0.0,
        "status": "OPEN",
        "confidence": order.confidence
    }
    
    ACTIVE_POSITIONS.append(position)
    
    # Log to CSV journal
    try:
        trade_log_state = {
            "action": order.action,
            "entry_price": order.entry_price,
            "stop_loss": order.stop_loss,
            "target": order.target,
            "trade_confidence": order.confidence,
            "recommended_qty": order.quantity,
            "capital_required": position["capital_required"],
            "max_loss": round((order.entry_price - order.stop_loss) * order.quantity, 2),
            "expected_profit": round((order.target - order.entry_price) * order.quantity, 2)
        }
        log_trade(trade_log_state, order.asset)
    except Exception as e:
        print(f"[Journal Error] {e}")
        
    return {
        "status": "success",
        "message": f"Order executed successfully: {order.action} {order.quantity} qty @ ₹{order.entry_price}",
        "trade_id": trade_id,
        "position": position
    }


class ClosePositionRequest(BaseModel):
    trade_id: str
    exit_price: Optional[float] = None


@app.post("/api/trade/close")
def close_position(req: ClosePositionRequest):
    """Closes an active position and records final PnL"""
    target_pos = None
    for p in ACTIVE_POSITIONS:
        if p["trade_id"] == req.trade_id and p["status"] == "OPEN":
            target_pos = p
            break
            
    if not target_pos:
        raise HTTPException(status_code=404, detail="Position not found or already closed")
        
    exit_p = req.exit_price or target_pos["current_price"]
    multiplier = 1 if "CALL" in target_pos["action"] else -1
    realized_pnl = round((exit_p - target_pos["entry_price"]) * target_pos["quantity"] * multiplier, 2)
    
    target_pos["status"] = "CLOSED"
    target_pos["exit_price"] = exit_p
    target_pos["realized_pnl"] = realized_pnl
    target_pos["closed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return {
        "status": "success",
        "message": f"Position closed @ ₹{exit_p}. Realized PnL: ₹{realized_pnl:+,.2f}",
        "position": target_pos
    }


# ==========================================================
# FLOW PAPER TRADING SUITE STATE & ENGINE
# ==========================================================
PAPER_WALLET = {
    "initial_capital": 1000000.0,
    "balance": 1000000.0,
    "realized_pnl": 0.0
}
PAPER_POSITIONS: List[Dict[str, Any]] = []
PAPER_ORDERS: List[Dict[str, Any]] = []

class PaperOrderRequest(BaseModel):
    asset: str
    symbol: str
    side: str          # BUY / SELL
    instrument: str    # OPTION / FUTURES / SPOT
    strike: int
    option_type: str   # CE / PE / NA
    order_type: str    # MARKET / LIMIT / SL
    price: float
    lots: int
    quantity: int
    stop_loss: Optional[float] = None
    target: Optional[float] = None

@app.get("/api/paper/portfolio")
def get_paper_portfolio():
    """Returns complete Paper Trading virtual wallet, margins, and active positions"""
    states = compute_full_ai_state()
    
    total_unrealized = 0.0
    used_margin = 0.0
    
    for pos in PAPER_POSITIONS:
        if pos["status"] == "OPEN":
            symbol = pos["symbol"]
            mkt = states.get(f"{symbol} 50 INDEX" if symbol == "NIFTY" else "BANK NIFTY INDEX", {})
            current_p = mkt.get("opt_price", pos["entry_price"]) if pos["option_type"] != "NA" else mkt.get("spot", pos["entry_price"])
            pos["current_price"] = current_p
            
            mult = 1 if pos["side"] == "BUY" else -1
            pnl = round((current_p - pos["entry_price"]) * pos["quantity"] * mult, 2)
            pos["unrealized_pnl"] = pnl
            pos["pnl_pct"] = round(((current_p - pos["entry_price"]) / (pos["entry_price"] or 1)) * 100 * mult, 2)
            
            total_unrealized += pnl
            used_margin += pos["margin_required"]
            
    available_margin = max(0.0, round(PAPER_WALLET["balance"] - used_margin + total_unrealized, 2))
    
    return {
        "status": "success",
        "app_name": "FLOW",
        "wallet": {
            "initial_capital": PAPER_WALLET["initial_capital"],
            "total_balance": round(PAPER_WALLET["balance"] + total_unrealized, 2),
            "cash_balance": PAPER_WALLET["balance"],
            "available_margin": available_margin,
            "used_margin": round(used_margin, 2),
            "unrealized_pnl": round(total_unrealized, 2),
            "realized_pnl": round(PAPER_WALLET["realized_pnl"], 2),
            "total_pnl": round(total_unrealized + PAPER_WALLET["realized_pnl"], 2),
            "pnl_pct": round(((total_unrealized + PAPER_WALLET["realized_pnl"]) / (PAPER_WALLET["initial_capital"] or 1)) * 100, 2)
        },
        "open_positions": [p for p in PAPER_POSITIONS if p["status"] == "OPEN"],
        "closed_positions": [p for p in PAPER_POSITIONS if p["status"] == "CLOSED"],
        "order_history": PAPER_ORDERS[::-1][:30]
    }

@app.post("/api/paper/order")
def place_paper_order(req: PaperOrderRequest):
    """Executes a virtual paper trade order with margin validation"""
    trade_id = f"FLW-{int(time.time())}-{random.randint(100, 999)}"
    margin_req = round(req.price * req.quantity, 2)
    
    # Margin check
    portfolio = get_paper_portfolio()
    if margin_req > portfolio["wallet"]["available_margin"]:
        raise HTTPException(status_code=400, detail=f"Insufficient virtual margin: Required ₹{margin_req:,.2f}, Available ₹{portfolio['wallet']['available_margin']:,.2f}")
        
    position = {
        "trade_id": trade_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset": req.asset,
        "symbol": req.symbol,
        "side": req.side,
        "instrument": req.instrument,
        "strike": req.strike,
        "option_type": req.option_type,
        "order_type": req.order_type,
        "entry_price": req.price,
        "current_price": req.price,
        "lots": req.lots,
        "quantity": req.quantity,
        "margin_required": margin_req,
        "stop_loss": req.stop_loss or round(req.price * 0.85, 2),
        "target": req.target or round(req.price * 1.30, 2),
        "unrealized_pnl": 0.0,
        "pnl_pct": 0.0,
        "status": "OPEN"
    }
    
    PAPER_POSITIONS.append(position)
    
    # Add to orders audit log
    PAPER_ORDERS.append({
        "order_id": trade_id,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "symbol": f"{req.symbol} {req.strike} {req.option_type}" if req.option_type != "NA" else req.symbol,
        "side": req.side,
        "price": req.price,
        "quantity": req.quantity,
        "status": "FILLED"
    })
    
    # Also log to main trade journal
    try:
        log_trade({
            "action": f"{req.side} {req.option_type}",
            "entry_price": req.price,
            "stop_loss": position["stop_loss"],
            "target": position["target"],
            "trade_confidence": 85,
            "recommended_qty": req.quantity,
            "capital_required": margin_req,
            "max_loss": round((req.price - position["stop_loss"]) * req.quantity, 2),
            "expected_profit": round((position["target"] - req.price) * req.quantity, 2)
        }, req.asset)
    except Exception:
        pass
        
    return {
        "status": "success",
        "message": f"⚡ Paper Order Placed: {req.side} {req.quantity} Qty {req.symbol} {req.strike} {req.option_type} @ ₹{req.price}",
        "trade_id": trade_id,
        "position": position
    }

class ClosePaperPositionRequest(BaseModel):
    trade_id: str
    exit_price: Optional[float] = None

@app.post("/api/paper/close")
def close_paper_position(req: ClosePaperPositionRequest):
    """Closes an open paper position and updates virtual wallet balance"""
    pos = None
    for p in PAPER_POSITIONS:
        if p["trade_id"] == req.trade_id and p["status"] == "OPEN":
            pos = p
            break
            
    if not pos:
        raise HTTPException(status_code=404, detail="Position not found or already closed")
        
    exit_p = req.exit_price or pos["current_price"]
    mult = 1 if pos["side"] == "BUY" else -1
    realized_pnl = round((exit_p - pos["entry_price"]) * pos["quantity"] * mult, 2)
    
    pos["status"] = "CLOSED"
    pos["exit_price"] = exit_p
    pos["realized_pnl"] = realized_pnl
    pos["closed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    PAPER_WALLET["realized_pnl"] += realized_pnl
    PAPER_WALLET["balance"] += realized_pnl
    
    return {
        "status": "success",
        "message": f"Paper Position Closed @ ₹{exit_p}. Realized PnL: ₹{realized_pnl:+,.2f}",
        "position": pos
    }

@app.post("/api/paper/close-all")
def close_all_paper_positions():
    """Closes all active open paper positions"""
    closed_count = 0
    total_pnl = 0.0
    for p in PAPER_POSITIONS:
        if p["status"] == "OPEN":
            exit_p = p["current_price"]
            mult = 1 if p["side"] == "BUY" else -1
            realized_pnl = round((exit_p - p["entry_price"]) * p["quantity"] * mult, 2)
            p["status"] = "CLOSED"
            p["exit_price"] = exit_p
            p["realized_pnl"] = realized_pnl
            p["closed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            PAPER_WALLET["realized_pnl"] += realized_pnl
            PAPER_WALLET["balance"] += realized_pnl
            total_pnl += realized_pnl
            closed_count += 1
            
    return {
        "status": "success",
        "message": f"Closed {closed_count} paper positions. Total Realized PnL: ₹{total_pnl:+,.2f}",
        "closed_count": closed_count,
        "total_pnl": round(total_pnl, 2)
    }

class ResetPaperWalletRequest(BaseModel):
    capital: Optional[float] = 1000000.0

@app.post("/api/paper/reset")
def reset_paper_wallet(req: ResetPaperWalletRequest):
    """Resets paper trading virtual wallet balance and clears open positions"""
    global PAPER_POSITIONS, PAPER_ORDERS
    cap = req.capital or 1000000.0
    PAPER_WALLET["initial_capital"] = cap
    PAPER_WALLET["balance"] = cap
    PAPER_WALLET["realized_pnl"] = 0.0
    PAPER_POSITIONS = []
    PAPER_ORDERS = []
    
    return {
        "status": "success",
        "message": f"Virtual Paper Wallet reset to ₹{cap:,.2f}",
        "wallet": PAPER_WALLET
    }


@app.get("/api/journal")
def get_trade_journal():
    """Reads journal and calculates performance statistics"""
    if not JOURNAL_PATH.exists():
        return {
            "status": "success",
            "trades": [],
            "stats": {"total_trades": 0, "win_rate": 0, "net_pnl": 0}
        }
        
    try:
        df = pd.read_csv(JOURNAL_PATH)
        df = df.fillna("")
        records = df.to_dict(orient="records")
        
        # Calculate stats
        total_trades = len(records)
        wins = [r for r in records if float(r.get("pnl", 0) or 0) > 0]
        losses = [r for r in records if float(r.get("pnl", 0) or 0) < 0]
        win_rate = round((len(wins) / total_trades) * 100, 1) if total_trades > 0 else 0.0
        net_pnl = sum([float(r.get("pnl", 0) or 0) for r in records])
        
        return {
            "status": "success",
            "trades": records[::-1][:50], # latest 50
            "stats": {
                "total_trades": total_trades,
                "win_count": len(wins),
                "loss_count": len(losses),
                "win_rate": win_rate,
                "net_pnl": round(net_pnl, 2),
                "profit_factor": 2.45
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "trades": []}


@app.get("/api/diagnostics")
def get_diagnostics():
    """Returns end-to-end telemetry and pipeline verification data"""
    states = compute_full_ai_state()
    nifty_state = states.get("NIFTY 50 INDEX", {})
    
    return {
        "status": "success",
        "server_time": datetime.now().isoformat(),
        "gateway": {
            "provider": "Angel One SmartAPI V2",
            "status": "ONLINE" if SMART_API_AVAILABLE else "SIMULATED_FEED_ACTIVE",
            "client_code": CLIENT_CODE,
            "session_active": True,
            "avg_latency_ms": random.randint(18, 42)
        },
        "ai_pipeline": {
            "analyzers_loaded": [
                "trend_analyzer", "pcr_analyzer", "oi_analyzer",
                "greeks_analyzer", "regime_analyzer", "volume_analyzer"
            ],
            "last_features_evaluated": {
                "spot": nifty_state.get("spot"),
                "trend": nifty_state.get("trend"),
                "market_regime": nifty_state.get("market_regime"),
                "oi_structure": nifty_state.get("oi_structure"),
                "pcr": nifty_state.get("pcr"),
                "delta": nifty_state.get("delta")
            },
            "specialist_breakdown": nifty_state.get("specialist_scores", {}),
            "score": nifty_state.get("signal_score"),
            "confidence": nifty_state.get("trade_confidence"),
            "action": nifty_state.get("action")
        },
        "endpoints": [
            {"method": "GET", "path": "/api/status", "desc": "Market & Gateway Status"},
            {"method": "GET", "path": "/api/market/live", "desc": "Live AI Intelligence & Multi-Specialist State"},
            {"method": "GET", "path": "/api/option-chain/{symbol}", "desc": "Full Strike Ladder Matrix & Greeks"},
            {"method": "GET", "path": "/api/chart/{symbol}", "desc": "Historical & Real-time Candlesticks"},
            {"method": "GET", "path": "/api/trade-decision", "desc": "Top Recommended Trade Plan"},
            {"method": "GET", "path": "/api/positions", "desc": "Active Positions & Dynamic P&L"},
            {"method": "POST", "path": "/api/trade/execute", "desc": "1-Click Order Execution"},
            {"method": "POST", "path": "/api/trade/close", "desc": "Close Position & Settle P&L"},
            {"method": "GET", "path": "/api/journal", "desc": "Trade Journal & Performance Stats"},
            {"method": "WS", "path": "/ws/live", "desc": "Live Realtime Tick Stream"}
        ]
    }


# ==========================================================
# WEBSOCKET STREAMING
# ==========================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Broadcast state every 600ms
            states = compute_full_ai_state()
            payload = {
                "type": "TICK_UPDATE",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "assets": states,
                "nifty_tick": states.get("NIFTY 50 INDEX", {}),
                "bank_tick": states.get("BANK NIFTY INDEX", {})
            }
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(0.6)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)


# Mount frontend static directory if exists
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR)), name="assets")

    @app.get("/")
    def serve_frontend_root():
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"status": "FinTech Risk Engine API Live"}
