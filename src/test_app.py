"""
Project: FinTech Risk Isolation Engine V2
Module: SmartAPI Live Dashboard
Author: Mohit Singh
"""

import os
import pandas as pd
import sys
from unittest import result
import SmartApi
import streamlit as st
from datetime import datetime
from plyer import notification
from SmartApi import SmartConnect
import pyotp
import time
from modules.websocket_engine import LIVE_STATE

from modules.decision_engine.engine import (
    decision_engine
)

from modules.decision_engine.models import (
    MarketFeatures
)
from modules.market_status import (
    NSE_HOLIDAYS_2026,
    get_market_status
)
from modules.alert_engine import (
    send_desktop_alert,
    LAST_ALERT
)
from modules.journal_engine import (
    JOURNAL_FILE
)
from modules.journal_engine import (
    JOURNAL_FILE,
    log_trade
)
from modules.market_regime import (
    classify_market_regime
)
from modules.position_sizing import (
    TOTAL_CAPITAL,
    RISK_PER_TRADE,
    LOT_SIZE_NIFTY,
    LOT_SIZE_BANKNIFTY,
    calculate_position_size
)
from modules.signal_engine import (
    calculate_signal,
    calculate_trend,
    classify_oi_buildup,
    generate_trade_decision
)
from modules.websocket_engine import (
    start_websocket,
    stop_websocket,
    get_latest_tick
)
from modules.live_market import (
    fetch_live_market_data
)

# =====================================================
# ANGEL ONE CONFIG
# =====================================================
API_KEY = "3xK955MH"
CLIENT_CODE = "AACI729341"
PIN = "0912"
TOTP_SECRET = "ZG4AT5YV6GPJQNPPVHLESN5JZI"







if not os.path.exists(JOURNAL_FILE):

    pd.DataFrame(
        columns=[
            "timestamp",
            "asset",
            "signal",
            "entry",
            "stop_loss",
            "target",
            "confidence",
            "quantity",
            "capital_required",
            "max_loss",
            "expected_profit",
            "status",
            "pnl"
        ]
    ).to_csv(
        JOURNAL_FILE,
        index=False
    )

# =====================================================
# PATH SETUP
# =====================================================

current_dir = os.path.dirname(
    os.path.abspath(__file__)
)

project_root = os.path.abspath(
    os.path.join(current_dir, "..")
)

if project_root not in sys.path:
    sys.path.insert(
        0,
        project_root
    )

# =====================================================
#UI IMPORTS
# =====================================================

from src.ui import (
    render_asset_card,
    render_strength_meter,
    render_signals_table,
    render_position_table,
    render_option_chain_panel,
    render_trade_card,
    render_asset_card_live,
    THEME_CONFIG
)

# =====================================================
# STREAMLIT CONFIG
# =====================================================

st.set_page_config(
    page_title="Risk  Engine V2",
    page_icon="⚡",
    layout="wide"
)
# =====================================================
# GLOBAL CSS
# ====================  =================================

st.markdown(
    f"""
    <style>

    .stApp {{
        background:#0d1117;
        color:#c9d1d9;
    }}

    .global-ticker-card {{
        background:#161b22;
        border:1px solid {THEME_CONFIG["border"]};
        border-radius:8px;
        padding:16px;
        margin-bottom:12px;
    }}

    .custom-table {{
        width:100%;
        border-collapse:collapse;
        background:#161b22;
        color:#e6edf3;
    }}

    .custom-table th {{
        background:#21262d;
        padding:10px;
    }}

    .custom-table td {{
        padding:10px;
    }}

    .macro-alert-box {{
        background:#1f1b11;
        border-left:4px solid #e3b341;
        padding:12px;
        border-radius:4px;
    }}

    </style>
    """,
    unsafe_allow_html=True
)

# =====================================================
# SMART API LOGIN
# =====================================================

@st.cache_resource(ttl=3600)
def initialize_angel():

    smart = SmartConnect(
        api_key=API_KEY
    )

    totp = pyotp.TOTP(
        TOTP_SECRET
    ).now()

    session = smart.generateSession(
        CLIENT_CODE,
        PIN,
        totp
    )

    if not session["status"]:
        return None

    jwt_token = session["data"]["jwtToken"]

    feed_token = smart.getfeedToken()

    return {
        "smart_api": smart,
        "jwt_token": jwt_token,
        "feed_token": feed_token,
        "client_code": CLIENT_CODE,
        "api_key": API_KEY
    }

# =====================================================
# DESKTOP ALERT ENGINE
# =====================================================

    alert_id = (
            f"{best_asset_name}_"
            f"{best_asset_data['action']}"
    )

    if (
            best_asset_data["trade_confidence"] >= 75
            and LAST_ALERT != alert_id
        ):

            send_desktop_alert(
            f"{best_asset_data['action']} ALERT",
            (
                f"{best_asset_name}\n"
                f"Confidence: {best_asset_data['trade_confidence']}%\n"
                f"Entry: ₹{best_asset_data['entry_price']:.2f}"
            )
        )

    LAST_ALERT = alert_id

# =====================================================
# PCR DATA
# =====================================================

def fetch_pcr_data():

    angel_session = initialize_angel()

    if angel_session is None:
        return {
            "NIFTY": 1.0,
            "BANKNIFTY": 1.0
        }

    smart = angel_session["smart_api"]

    if smart is None:
        return {
            "NIFTY": 1.0,
            "BANKNIFTY": 1.0
        }

    try:
        data = smart.putCallRatio()

        if (
            data is None
            or not data.get("status")
            or data.get("data") is None
        ):
            return {
                "NIFTY": 1.0,
                "BANKNIFTY": 1.0
            }

        pcr_map = {
            "NIFTY": 1.0,
            "BANKNIFTY": 1.0
        }

        for row in data["data"]:

            name = str(
                row.get("name", "")
            ).upper()

            pcr_value = float(
                row.get("pcr", 1.0)
            )

            if "NIFTY" in name and "BANK" not in name:
                pcr_map["NIFTY"] = pcr_value

            elif "BANKNIFTY" in name or "BANK NIFTY" in name:
                pcr_map["BANKNIFTY"] = pcr_value

        return pcr_map

    except Exception as e:
        print("PCR FETCH ERROR =", e)

        return {
            "NIFTY": 1.0,
            "BANKNIFTY": 1.0
        }
        

def fetch_greeks(
    spot: float,
    strike: float
):
    """
    =====================================================
    Greeks Engine

    Returns Greeks for BOTH
    CE and PE.

    This is currently a mathematical simulator.

    Later this will be replaced by
    Black-Scholes / Live Greeks.
    =====================================================
    """

    moneyness = abs(
        spot - strike
    ) / spot

    gamma = round(

        max(
            0.02 - (
                moneyness * 0.01
            ),
            0.001
        ),

        4

    )

    theta = round(

        -4.5 -
        (
            moneyness * 10
        ),

        2

    )

    vega = round(

        8 +
        (
            moneyness * 20
        ),

        2

    )

    ce = {

        "delta": 0.70,

        "gamma": gamma,

        "theta": theta,

        "vega": vega

    }

    pe = {

        "delta": -0.70,

        "gamma": gamma,

        "theta": theta,

        "vega": vega

    }

    return {

        "CE": ce,

        "PE": pe

    }
def discover_atm_contracts(
    smart,
    symbol,
    atm_strike
):
    search_term = symbol

    search_term = "NIFTY"

    print(
    "SEARCH TERM =",
    search_term
)
    result = smart.searchScrip(
    "NFO",
    symbol
)


    if result.get("data"):
       
        for row in result["data"][:20]:
            


            ce_symbol = ""
            ce_token = ""

            pe_symbol = ""
            pe_token = ""

    if (
            result is None
            or not result.get("status")
            or result.get("data") is None
        ):
            print("SEARCH FAILED")
            return {
                "ce_symbol": "",
                "ce_token": "",
                "pe_symbol": "",
                "pe_token": ""
            }

    strike_text = str(atm_strike)

    

    for row in result["data"]:

        ts = row["tradingsymbol"]
        if symbol == "BANKNIFTY":
    

         if ts.startswith("NIFTYNXT"):
            continue

        if "NIFTY" not in ts:
            continue

        
        if strike_text not in ts:
            continue

        if ts.endswith("CE"):

            ce_symbol = ts
            ce_token = row["symboltoken"]

        elif ts.endswith("PE"):

            pe_symbol = ts
            pe_token = row["symboltoken"]

        if ce_symbol and pe_symbol:
            break

    

    return {
        "ce_symbol": ce_symbol,
        "ce_token": ce_token,
        "pe_symbol": pe_symbol,
        "pe_token": pe_token
    }


def fetch_option_chain(
    spot,
    symbol
):
    

    if symbol == "NIFTY":
        import math
        atm_strike = (
            math.ceil(spot / 100)
            * 100
        )
    else:
        atm_strike = (
            int(round(spot / 100))
            * 100
        )

    angel_session = initialize_angel()

    if angel_session is None:
        return None

    smart = angel_session["smart_api"]

    contracts = discover_atm_contracts(
        smart,
        symbol,
        atm_strike
)
    ce_ltp = 0
    pe_ltp = 0

    call_oi = 0
    put_oi = 0

    call_volume = 0
    put_volume = 0

    try:

        tokens = []

        if contracts["ce_token"]:
            tokens.append(
                contracts["ce_token"]
            )

        if contracts["pe_token"]:
            tokens.append(
                contracts["pe_token"]
            )

        if tokens:

            quote = smart.getMarketData(
                "FULL",
                {
                    "NFO": tokens
                }
            )


            for row in quote["data"]["fetched"]:

                token = row["symbolToken"]

                if token == contracts["ce_token"]:

                    ce_ltp = row["ltp"]
                    call_oi = row["opnInterest"]
                    call_volume = row["tradeVolume"]

                elif token == contracts["pe_token"]:

                    pe_ltp = row["ltp"]
                    put_oi = row["opnInterest"]
                    put_volume = row["tradeVolume"]

    except Exception as e:

        print("QUOTE ERROR =", e)

    recommended_premium = max(
    ce_ltp,
    pe_ltp
)
    
    confidence = 70
    risk_reward = 2.0

    lots, quantity = calculate_position_size(
        recommended_premium,
        confidence,
        risk_reward,
        symbol
)

    return {
        "atm_strike": atm_strike,
        "atm_ce": contracts["ce_symbol"],
        "atm_pe": contracts["pe_symbol"],
        "ce_ltp": ce_ltp,
        "pe_ltp": pe_ltp,
        "call_oi": call_oi,
        "put_oi": put_oi,
        "call_volume": call_volume,
        "put_volume": put_volume,
        "max_pain": atm_strike,
        "support": atm_strike - 100,
        "resistance": atm_strike + 100,
        "oi_bias":
        "BULLISH"
        if put_oi > call_oi
        else "BEARISH",
        "recommended_lots": lots,
        "recommended_qty": quantity,
    }



def build_live_state(market_data):

    pcr_data = fetch_pcr_data()

    states = {}

    for symbol in [
        "NIFTY",
        "BANKNIFTY"
    ]:

        # =====================================================
        # LIVE MARKET DATA
        # =====================================================

        spot = market_data[symbol]["spot"]

        change = market_data[symbol]["change"]

        oi = market_data[symbol]["oi"]

        pcr = pcr_data[symbol]

        # =====================================================
        # MARKET STRUCTURE
        # =====================================================

        oi_structure = classify_oi_buildup(

            change,

            oi

        )

        trend = calculate_trend(

            change,

            pcr,

            oi_structure

        )

        # =====================================================
        # ASSET CONFIG
        # =====================================================

        if symbol == "NIFTY":

            strike = int(

                round(
                    spot / 50
                )

            ) * 50

            asset_name = "NIFTY 50 INDEX"

            lot_size = 50

            premium_factor = 0.006

        else:

            strike = int(

                round(
                    spot / 100
                )

            ) * 100

            asset_name = "BANK NIFTY INDEX"

            lot_size = 15

            premium_factor = 0.008

        # =====================================================
        # OPTION PREMIUM
        # =====================================================

        opt_price = round(

            spot * premium_factor,

            2

        )

        # =====================================================
        # OPTION CHAIN
        # =====================================================

        try:

            option_chain = fetch_option_chain(

                spot,

                symbol

            )

            market_regime = classify_market_regime(

                change,

                pcr,

                option_chain["oi_bias"]

            )

        except Exception as e:

            st.error(
                f"{symbol} OPTION CHAIN ERROR : {e}"
            )

            option_chain = {

                "recommended_lots": 0,

                "recommended_qty": 0,

                "atm_strike": strike,

                "atm_ce": "",

                "atm_pe": "",

                "ce_ltp": 0,

                "pe_ltp": 0,

                "call_oi": 0,

                "put_oi": 0,

                "call_volume": 0,

                "put_volume": 0,

                "max_pain": strike,

                "support": strike,

                "resistance": strike,

                "oi_bias": "NEUTRAL"

            }

            market_regime = "UNKNOWN"

        # =====================================================
        # GREEKS ENGINE
        # =====================================================

        greeks = fetch_greeks(

            spot,

            strike

        )

        # =====================================================
        # AI FEATURE OBJECT
        # =====================================================

        features = MarketFeatures(

    trend=trend,

    market_regime=market_regime,

    oi_structure=oi_structure,

    spot=spot,

    option_premium=opt_price,

    support=option_chain["support"],

    resistance=option_chain["resistance"],

    pcr=pcr,

    # Temporary: use CE Greeks for AI scoring
    delta=greeks["CE"]["delta"],

    gamma=greeks["CE"]["gamma"],

    theta=greeks["CE"]["theta"],

    vega=greeks["CE"]["vega"],

    call_volume=option_chain["call_volume"],

    put_volume=option_chain["put_volume"]

)
        # =====================================================
        # AI DECISION ENGINE
        # =====================================================

        decision = decision_engine.evaluate(

            features

        )

        print(

            f"[AI] {symbol}",

            decision.action,

            decision.confidence

        )
                # =====================================================
        # OPTION SIDE SELECTED BY AI
        # =====================================================

        action = decision.action

        if action == "BUY CALL":

            direction = 1

            option_type = "CE"

            selected_greeks = greeks["CE"]

        elif action == "BUY PUT":

            direction = -1

            option_type = "PE"

            selected_greeks = greeks["PE"]

        else:

            direction = 0

            option_type = "NT"

            selected_greeks = greeks["CE"]

        # =====================================================
        # POSITION SIZING
        # =====================================================

        confidence = decision.confidence

        risk_reward = decision.trade_plan.risk_reward

        lots, quantity = calculate_position_size(

            opt_price,

            confidence,

            risk_reward,

            symbol

        )

        # =====================================================
        # CAPITAL CALCULATIONS
        # =====================================================

        capital_required = round(

            quantity *

            opt_price,

            2

        )

        max_loss = round(

            (

                opt_price

                -

                decision.trade_plan.stop_loss

            )

            *

            quantity,

            2

        )

        risk_percent = round(

            (

                max_loss

                /

                TOTAL_CAPITAL

            )

            * 100,

            2

        )

        expected_profit = round(

            (

                decision.trade_plan.target

                -

                decision.trade_plan.entry

            )

            *

            quantity,

            2

        )

        # =====================================================
        # BUILD STATE OBJECT
        # =====================================================

        state = {}

        state["trade_confidence"] = decision.confidence

        state["trade_reasons"] = decision.reasons

        state["action"] = decision.action

        state["probability"] = decision.confidence

        state["signal_score"] = decision.score

        state["spot"] = spot

        state["change_7d"] = change

        state["dir_factor"] = direction

        state["currency"] = "₹"

        state["entry_price"] = decision.trade_plan.entry

        state["stop_loss"] = decision.trade_plan.stop_loss

        state["target"] = decision.trade_plan.target

        state["risk_reward"] = decision.trade_plan.risk_reward

        state["recommended_lots"] = lots

        state["recommended_qty"] = quantity

        state["capital_required"] = capital_required

        state["max_loss"] = max_loss

        state["risk_percent"] = risk_percent

        state["expected_profit"] = expected_profit
                # =====================================================
        # MARKET ANALYTICS
        # =====================================================

        state["pcr"] = pcr

        state["oi"] = oi

        state["oi_structure"] = oi_structure

        state["trend"] = trend

        state["market_regime"] = market_regime

        # =====================================================
        # GREEKS (AI SELECTED OPTION)
        # =====================================================

        state["delta"] = selected_greeks["delta"]

        state["gamma"] = selected_greeks["gamma"]

        state["theta"] = selected_greeks["theta"]

        state["vega"] = selected_greeks["vega"]

        # =====================================================
        # OPTION CHAIN
        # =====================================================

        state["atm_strike"] = option_chain["atm_strike"]

        state["atm_ce"] = option_chain["atm_ce"]

        state["atm_pe"] = option_chain["atm_pe"]

        state["ce_ltp"] = option_chain["ce_ltp"]

        state["pe_ltp"] = option_chain["pe_ltp"]

        state["call_oi"] = option_chain["call_oi"]

        state["put_oi"] = option_chain["put_oi"]

        state["call_volume"] = option_chain["call_volume"]

        state["put_volume"] = option_chain["put_volume"]

        state["max_pain"] = option_chain["max_pain"]

        state["support"] = option_chain["support"]

        state["resistance"] = option_chain["resistance"]

        state["oi_bias"] = option_chain["oi_bias"]

        # =====================================================
        # OPTION DETAILS
        # =====================================================

        state["opt_price"] = opt_price

        state["opt_symbol"] = (

            f"{symbol} "

            f"{strike} "

            f"{option_type}"

        )

        state["mock_entry"] = round(

            decision.trade_plan.entry * 0.95,

            2

        )

        state["mock_size"] = lot_size

        # =====================================================
        # AI OUTPUT
        # =====================================================

        state["ai_risk"] = decision.risk

        state["ai_reasons"] = decision.reasons

        state["ai_warnings"] = decision.warnings

        # =====================================================
        # STORE STATE
        # =====================================================

        states[asset_name] = state
            # =====================================================
    # VALIDATION
    # =====================================================

    if not states:

        st.warning(
            "No market states were generated."
        )

    else:

        print(
            f"Generated {len(states)} live states."
        )

        for asset, data in states.items():

            print(

                asset,

                data["action"],

                data["trade_confidence"]

            )

    # =====================================================
    # RETURN
    # =====================================================

    return states
@st.fragment(run_every="300ms")
def render_live_top_cards():

    live_states = st.session_state.get(
        "global_fund_states",
        {}
    )

    col1, col2 = st.columns(2)

    with col1:

        nifty_state = live_states.get(
            "NIFTY 50 INDEX",
            {}
        ).copy()

        if not nifty_state:
            nifty_state = {
                "action": "NO TRADE",
                "change_7d": 0.0,
                "spot": 0.0,
                "probability": 0.0,
                "trend": "WAITING",
                "market_regime": "LOADING",
                "pcr": 0.0,
                "oi": 0,
                "signal_score": 0,
                "delta": 0.0,
                "gamma": 0.0,
                "theta": 0.0,
                "vega": 0.0
            }

        nifty_tick = LIVE_STATE.get(
            "NIFTY",
            {}
        )

        if nifty_tick.get("ltp") is not None:
            nifty_state["spot"] = nifty_tick["ltp"]

        if nifty_state:
            st.html(
                render_asset_card(
                    "NIFTY 50 INDEX",
                    nifty_state
                )
            )
        else:
            st.error("NIFTY STATE MISSING")

    with col2:

        bank_state = live_states.get(
            "BANK NIFTY INDEX",
            {}
        ).copy()

        if not bank_state:
            bank_state = {
                "action": "NO TRADE",
                "change_7d": 0.0,
                "spot": 0.0,
                "probability": 0.0,
                "trend": "WAITING",
                "market_regime": "LOADING",
                "pcr": 0.0,
                "oi": 0,
                "signal_score": 0,
                "delta": 0.0,
                "gamma": 0.0,
                "theta": 0.0,
                "vega": 0.0
            }

        bank_tick = LIVE_STATE.get(
            "BANKNIFTY",
            {}
        )

        if bank_tick.get("ltp") is not None:
            bank_state["spot"] = bank_tick["ltp"]

        if bank_state:
            st.html(
                render_asset_card(
                    "BANK NIFTY INDEX",
                    bank_state
                )
            )
        else:
            st.error("BANK NIFTY INDEX not found")# =====================================================
# APP START
# =====================================================

st.title(
    "🇮🇳 ALGORITHMIC OPTIONS RISK DESK V2"
)

st.caption(
    f"System Time: "
    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "
    f"| SmartAPI Connected "
    f"| Top Cards: Live WebSocket "
    f"| Analytics Refresh: 30 Seconds"
)
@st.fragment(run_every="30s")
def render_analytics_dashboard():

    market_data = fetch_live_market_data(
        initialize_angel
    )

    if market_data is None:
        st.warning("Analytics refresh failed: market data unavailable")
        return

    global_fund_states = build_live_state(
        market_data
    )

    

    if not global_fund_states:
        st.warning("No analytics state available right now.")
        return
    st.session_state["global_fund_states"] = global_fund_states

    # =====================================================
    # STRENGTH METER
    # =====================================================

    st.subheader(
        "📊 Signal Strength Matrix"
    )

    st.html(
        render_strength_meter(
            "PCR + OI + PRICE MODEL",
            global_fund_states
        )
    )

    # =====================================================
    # SIGNAL TABLE
    # =====================================================

    st.subheader(
        "⚡ Signal Matrix"
    )

    (
        signal_rows,
        highest_prob_asset,
        highest_prob_val
    ) = render_signals_table(
        global_fund_states
    )

    st.html(
        f"""
        <table class="custom-table">

            <thead>
                <tr>
                    <th>OPTION</th>
                    <th>SIGNAL</th>
                    <th>PCR</th>
                    <th>OI</th>
                    <th>OI BUILDUP</th>
                    <th>TREND</th>
                    <th>SCORE</th>
                    <th>DELTA</th>
                    <th>GAMMA</th>
                    <th>THETA</th>
                    <th>VEGA</th>
                    <th>PROBABILITY</th>
                </tr>
            </thead>

            <tbody>
                {signal_rows}
            </tbody>

        </table>
        """,
    )

    # =====================================================
    # POSITION TABLE
    # =====================================================

    st.subheader(
        "💼 Position Book"
    )

    (
        rows_html,
        total_unrealized_pnl,
        pnl_color
    ) = render_position_table(
        global_fund_states
    )

    st.html(
        f"""
        <table class="custom-table">

            <thead>
                <tr>
                    <th>ASSET</th>
                    <th>DIRECTION</th>
                    <th>SIZE</th>
                    <th>ENTRY</th>
                    <th>SPOT</th>
                    <th>PNL</th>
                </tr>
            </thead>

            <tbody>

                {rows_html}

                <tr>
                    <td colspan="5"
                        style="
                        text-align:right;
                        color:#8c9bae;
                        "
                    >
                        TOTAL PNL
                    </td>

                    <td
                        style="
                        color:{pnl_color};
                        font-weight:bold;
                        "
                    >
                        ₹{total_unrealized_pnl:,.2f}
                    </td>

                </tr>

            </tbody>

        </table>
        """,
    )

    # =====================================================
    # TRADE OF THE MOMENT
    # =====================================================

    if global_fund_states:

        best_asset = max(
            global_fund_states.items(),
            key=lambda x: x[1].get("trade_confidence", 0)
        )

        best_asset_name = best_asset[0]
        best_asset_data = best_asset[1].copy()

    else:
        best_asset_name = "NO LIVE SIGNAL"
        best_asset_data = {
            "trade_confidence": 0,
            "action": "NO TRADE",
            "probability": 0,
            "entry_price": 0,
            "stop_loss": 0,
            "target": 0,
            "risk_reward": 0,
            "recommended_lots": 0,
            "recommended_qty": 0,
            "capital_required": 0,
            "max_loss": 0,
            "risk_percent": 0,
            "expected_profit": 0,
            "trade_reasons": ["No live signal available"]
        }

    if best_asset_data["trade_confidence"] < 40:
        best_asset_data["action"] = "NO TRADE"
        best_asset_data["trade_confidence"] = 0
        best_asset_data["trade_reasons"] = [
            "No setup meets minimum confidence threshold"
        ]

    st.subheader(
        "🎯 Trade Recommendation Engine"
    )

    st.html(
        render_trade_card(
            best_asset_name,
            best_asset_data
        )
    )

    # =====================================================
    # OPTION CHAIN INTELLIGENCE
    # =====================================================

    st.subheader(
        "🎯 Option Chain Intelligence"
    )

    option_chain_html = render_option_chain_panel(
        global_fund_states
    )

    if option_chain_html:
        st.html(option_chain_html)
    else:
        st.warning("Option chain data not available right now.")

# =====================================================
# MARKET STATUS
# =====================================================

is_open, market_status = get_market_status()

st.info(
    f"📈 {market_status}"
)

if not is_open:
    st.warning(
        f"🚫 {market_status}"
    )

# =====================================================
# START WEBSOCKET ONCE
# =====================================================

if "websocket_started" not in st.session_state:

    angel_session = initialize_angel()

    start_websocket(
        angel_session["jwt_token"],
        angel_session["api_key"],
        angel_session["client_code"],
        angel_session["feed_token"]
    )

    st.session_state["websocket_started"] = True

# =====================================================
# LIVE TOP CARDS
# =====================================================

render_live_top_cards()

# =====================================================
# HEAVY ANALYTICS DASHBOARD
# =====================================================

render_analytics_dashboard()

st.subheader(
    "📒 Trade Journal"
)

journal_df = pd.read_csv(
    JOURNAL_FILE
)

st.dataframe(
    journal_df.tail(10),
    use_container_width=True
)
st.write(
    get_latest_tick(
        "NIFTY"
    )
)

st.write(
    get_latest_tick(
        "BANKNIFTY"
    )
)
    