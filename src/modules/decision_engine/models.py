"""
Project: FLOW Decision Engine V2
Module: AI Decision Engine Models & Quantitative Features
Author: Mohit Singh
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# ==========================================================
# ADVANCED MARKET FEATURES
# ==========================================================

@dataclass
class MarketFeatures:
    # ------------------------------------------------------
    # Trend & Directional Structure
    # ------------------------------------------------------
    trend: str                    # STRONG BULLISH, BULLISH, SIDEWAYS, BEARISH, STRONG BEARISH
    market_regime: str            # TRENDING, RANGE BOUND, VOLATILE, BREAKOUT
    oi_structure: str             # LONG BUILDUP, SHORT COVERING, SHORT BUILDUP, LONG UNWINDING

    # ------------------------------------------------------
    # Spot & Derivatives Levels
    # ------------------------------------------------------
    spot: float
    option_premium: float
    support: float
    resistance: float
    max_pain: float = 0.0

    # ------------------------------------------------------
    # Option Chain Microstructure & PCR
    # ------------------------------------------------------
    pcr: float = 1.0
    pcr_trend: str = "NEUTRAL"     # EXPANDING, CONTRACTING, NEUTRAL
    oi_bias: str = "NEUTRAL"       # BULLISH, BEARISH, NEUTRAL

    # ------------------------------------------------------
    # Option Greeks & Volatility
    # ------------------------------------------------------
    delta: float = 0.50
    gamma: float = 0.015
    theta: float = -3.50
    vega: float = 12.0
    iv: float = 14.5

    # ------------------------------------------------------
    # Volume & Order Flow
    # ------------------------------------------------------
    call_volume: int = 0
    put_volume: int = 0

    # ------------------------------------------------------
    # Price Action & Technical Patterns
    # ------------------------------------------------------
    rsi: float = 52.0             # 0 to 100
    ema_9: float = 0.0
    ema_21: float = 0.0
    candlestick_pattern: str = "NONE" # BULLISH_ENGULFING, HAMMER_REJECTION, BEARISH_ENGULFING, SHOOTING_STAR, PINBAR
    market_structure: str = "HIGHER_HIGHS" # HIGHER_HIGHS, LOWER_LOWS, CONSOLIDATING

    # ------------------------------------------------------
    # Market Psychology & Retail Trap Dynamics
    # ------------------------------------------------------
    trap_state: str = "NONE"       # BULL_TRAP_REJECTION, BEAR_TRAP_REBOUND, LIQUIDITY_SWEEP, CLEAN_BREAKOUT
    fear_greed_score: float = 55.0 # 0 (Extreme Fear) to 100 (Extreme Greed)
    institutional_bias: str = "ACCUMULATION" # ACCUMULATION, DISTRIBUTION, NEUTRAL

    # ------------------------------------------------------
    # News & Macroeconomic Sentiment
    # ------------------------------------------------------
    news_sentiment_score: float = 0.25 # -1.0 (Extreme Negative) to +1.0 (Extreme Positive)
    macro_headline: str = "Positive domestic institutional inflows & stable interest rate outlook"


# ==========================================================
# SPECIALIST ANALYZER RESULT
# ==========================================================

@dataclass
class AnalyzerResult:
    score: int                     # -100 to +100 or specialist sub-score
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ==========================================================
# TRADE PLAN
# ==========================================================

@dataclass
class TradePlan:
    entry: float
    stop_loss: float
    target: float
    target_2: float = 0.0
    risk_reward: float = 2.0
    setup_type: str = "MOMENTUM_TREND" # TRAP_REVERSAL, BREAKOUT_CONTINUATION, MEAN_REVERSION


# ==========================================================
# FINAL AI DECISION RESULT
# ==========================================================

@dataclass
class DecisionResult:
    action: str                    # BUY CALL, BUY PUT, WATCH CALL, WATCH PUT, WAIT, NO TRADE
    score: int                     # -100 to +100
    confidence: int                # 0% to 100%
    risk: str                      # LOW, MODERATE, HIGH, VERY HIGH
    trade_plan: TradePlan
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    specialist_breakdown: Dict[str, Any] = field(default_factory=dict)