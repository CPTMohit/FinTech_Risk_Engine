"""
=========================================================
AI Decision Engine Models
=========================================================

Shared data models used across the complete AI
Decision Engine.
"""

from dataclasses import (
    dataclass,
    field
)

from typing import List


# ==========================================================
# MARKET FEATURES
# ==========================================================

@dataclass
class MarketFeatures:

    # ------------------------------------------------------
    # Market Direction
    # ------------------------------------------------------

    trend: str

    market_regime: str

    oi_structure: str

    # ------------------------------------------------------
    # Spot Market
    # ------------------------------------------------------

    spot: float

    option_premium: float

    support: float

    resistance: float

    # ------------------------------------------------------
    # PCR
    # ------------------------------------------------------

    pcr: float

    # ------------------------------------------------------
    # Greeks
    # ------------------------------------------------------

    delta: float

    gamma: float

    theta: float

    vega: float

    # ------------------------------------------------------
    # Volume
    # ------------------------------------------------------

    call_volume: int

    put_volume: int


# ==========================================================
# GENERIC ANALYZER RESULT
# ==========================================================

@dataclass
class AnalyzerResult:

    score: int

    reasons: List[str] = field(
        default_factory=list
    )

    warnings: List[str] = field(
        default_factory=list
    )


# ==========================================================
# TRADE PLAN
# ==========================================================

@dataclass
class TradePlan:

    entry: float

    stop_loss: float

    target: float

    risk_reward: float


# ==========================================================
# FINAL AI DECISION
# ==========================================================

@dataclass
class DecisionResult:

    action: str

    score: int

    confidence: int

    risk: str

    trade_plan: TradePlan

    reasons: List[str] = field(
        default_factory=list
    )

    warnings: List[str] = field(
        default_factory=list
    )