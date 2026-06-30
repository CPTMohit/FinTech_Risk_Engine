"""
=========================================================
AI Decision Engine V1
Author : Mohit Singh
Project : FinTech Risk Engine
=========================================================

Purpose
-------
Central brain of the trading platform.

Input:
    Market Features

Output:
    Unified Trade Decision

This module contains NO API calls.
It only reasons over market features.
"""

from dataclasses import dataclass
from typing import Dict, List


# =========================================================
# FEATURE MODEL
# =========================================================

@dataclass
class MarketFeatures:

    trend: str

    pcr: float

    oi_structure: str

    market_regime: str

    delta: float

    gamma: float

    theta: float

    vega: float

    call_volume: int

    put_volume: int

    support: float

    resistance: float

    spot: float


# =========================================================
# DECISION ENGINE
# =========================================================

class DecisionEngine:

    def __init__(self):

        self.max_score = 100

    # =====================================================
    # MAIN ENTRY
    # =====================================================

    def evaluate(
        self,
        features: MarketFeatures
    ) -> Dict:

        score = self.calculate_market_score(features)

        action = self.determine_action(
            score,
            features
        )

        confidence = self.calculate_confidence(
            score
        )

        reasons = self.generate_reasoning(
            features
        )

        warnings = self.generate_warnings(
            features
        )

        risk = self.calculate_risk(
            confidence
        )

        trade_plan = self.build_trade_plan(
            features,
            action
        )

        return {

            "score": score,

            "confidence": confidence,

            "action": action,

            "risk": risk,

            "reasons": reasons,

            "warnings": warnings,

            **trade_plan

        }

    # =====================================================
    # MARKET SCORE
    # =====================================================

    def calculate_market_score(
        self,
        f: MarketFeatures
    ):

        score = 0

        # ----------------------------
        # TREND
        # ----------------------------

        if f.trend == "BULLISH":
            score += 25

        elif f.trend == "BEARISH":
            score += 25

        else:
            score += 5

        # ----------------------------
        # PCR
        # ----------------------------

        if f.pcr >= 1.10:
            score += 20

        elif f.pcr >= 0.95:
            score += 15

        elif f.pcr >= 0.80:
            score += 8

        else:
            score += 3

        # ----------------------------
        # OI STRUCTURE
        # ----------------------------

        if f.oi_structure == "LONG BUILDUP":
            score += 20

        elif f.oi_structure == "SHORT COVERING":
            score += 15

        elif f.oi_structure == "SHORT BUILDUP":
            score += 10

        else:
            score += 5

        # ----------------------------
        # MARKET REGIME
        # ----------------------------

        if f.market_regime == "TRENDING":
            score += 15

        elif f.market_regime == "BREAKOUT MARKET":
            score += 12

        elif f.market_regime == "RANGE":
            score += 8

        else:
            score += 5

        # ----------------------------
        # DELTA
        # ----------------------------

        if abs(f.delta) >= 0.70:
            score += 10

        elif abs(f.delta) >= 0.50:
            score += 7

        else:
            score += 3

        # ----------------------------
        # VOLUME
        # ----------------------------

        total_volume = (
            f.call_volume +
            f.put_volume
        )

        if total_volume > 1_000_000:
            score += 5

        elif total_volume > 500_000:
            score += 3

        else:
            score += 1

        # ----------------------------
        # VOLATILITY
        # ----------------------------

        if abs(f.vega) < 10:
            score += 5

        else:
            score += 2

        return min(score, self.max_score)

    # =====================================================
    # ACTION
    # =====================================================

    def determine_action(
        self,
        score,
        f
    ):

        if score >= 80:

            if f.trend == "BULLISH":
                return "BUY CALL"

            elif f.trend == "BEARISH":
                return "BUY PUT"

        elif score >= 60:

            if f.trend == "BULLISH":
                return "WATCH CALL"

            elif f.trend == "BEARISH":
                return "WATCH PUT"

        return "NO TRADE"

    # =====================================================
    # CONFIDENCE
    # =====================================================

    def calculate_confidence(
        self,
        score
    ):

        return min(
            99,
            int(score)
        )

    # =====================================================
    # REASONS
    # =====================================================

    def generate_reasoning(
        self,
        f
    ) -> List[str]:

        reasons = []

        if f.trend == "BULLISH":
            reasons.append(
                "Bullish Trend"
            )

        if f.trend == "BEARISH":
            reasons.append(
                "Bearish Trend"
            )

        if f.pcr > 1:
            reasons.append(
                "Bullish PCR"
            )

        if f.oi_structure == "LONG BUILDUP":
            reasons.append(
                "Long Buildup"
            )

        if abs(f.delta) > 0.60:
            reasons.append(
                "Strong Delta"
            )

        if f.market_regime == "BREAKOUT MARKET":
            reasons.append(
                "Breakout Market"
            )

        return reasons

    # =====================================================
    # WARNINGS
    # =====================================================

    def generate_warnings(
        self,
        f
    ):

        warnings = []

        if abs(f.theta) > 15:
            warnings.append(
                "High Theta Decay"
            )

        if abs(f.vega) > 15:
            warnings.append(
                "High Volatility Risk"
            )

        return warnings

    # =====================================================
    # RISK
    # =====================================================

    def calculate_risk(
        self,
        confidence
    ):

        if confidence >= 85:
            return "LOW"

        elif confidence >= 65:
            return "MEDIUM"

        return "HIGH"

    # =====================================================
    # TRADE PLAN
    # =====================================================

    def build_trade_plan(
        self,
        f,
        action
    ):

        if action == "NO TRADE":

            return {

                "entry": None,

                "stop_loss": None,

                "target": None,

                "risk_reward": None

            }

        entry = f.spot

        stop = round(
            entry * 0.995,
            2
        )

        target = round(
            entry * 1.015,
            2
        )

        rr = round(
            (target - entry) /
            (entry - stop),
            2
        )

        return {

            "entry": entry,

            "stop_loss": stop,

            "target": target,

            "risk_reward": rr

        }


# =========================================================
# GLOBAL INSTANCE
# =========================================================

decision_engine = DecisionEngine()

if __name__ == "__main__":

    sample = MarketFeatures(
        trend="BULLISH",
        pcr=1.15,
        oi_structure="LONG BUILDUP",
        market_regime="BREAKOUT MARKET",
        delta=0.72,
        gamma=0.03,
        theta=-4.5,
        vega=8.2,
        call_volume=1200000,
        put_volume=900000,
        support=23900,
        resistance=24200,
        spot=24050
    )

    result = decision_engine.evaluate(sample)

    from pprint import pprint
    pprint(result)