"""
=========================================================
Chief AI Decision Engine
=========================================================

This is the brain of the trading system.

Responsibilities
----------------
1. Run every specialist analyzer
2. Aggregate scores
3. Calculate confidence
4. Determine action
5. Classify risk
6. Build trade plan
7. Return one unified DecisionResult
"""

from .models import (
    MarketFeatures,
    DecisionResult
)

from .trend_analyzer import trend_analyzer
from .pcr_analyzer import pcr_analyzer
from .oi_analyzer import oi_analyzer
from .greeks_analyzer import greeks_analyzer
from .regime_analyzer import regime_analyzer
from .volume_analyzer import volume_analyzer

from .confidence_engine import confidence_engine
from .risk_engine import risk_engine
from .planner import trade_planner


class DecisionEngine:

    def __init__(self):

        self.analyzers = [

            trend_analyzer,

            pcr_analyzer,

            oi_analyzer,

            greeks_analyzer,

            regime_analyzer,

            volume_analyzer

        ]

    # =====================================================
    # MAIN ENTRY
    # =====================================================

    def evaluate(
        self,
        features: MarketFeatures
    ) -> DecisionResult:

        total_score = 0

        reasons = []

        warnings = []

        # ===============================================
        # RUN EVERY AI ANALYZER
        # ===============================================

        for analyzer in self.analyzers:

            result = analyzer.analyze(
                features
            )

            total_score += result.score

            reasons.extend(
                result.reasons
            )

            warnings.extend(
                result.warnings
            )

        # ===============================================
        # NORMALIZE SCORE
        # ===============================================

        total_score = min(
            total_score,
            100
        )

        # ===============================================
        # CONFIDENCE
        # ===============================================

        confidence = (
            confidence_engine.calculate(
                total_score
            )
        )

        # ===============================================
        # ACTION
        # ===============================================

        action = self.determine_action(

            confidence,

            features

        )

        # ===============================================
        # RISK
        # ===============================================

        risk = risk_engine.classify(
            confidence
        )

        # ===============================================
        # TRADE PLAN
        # ===============================================

        trade_plan = trade_planner.build(

        action,

        features.option_premium

)
        print("ACTION =", action)
        print("TRADE PLAN =", trade_plan)
        # ===============================================
        # FINAL RESULT
        # ===============================================

        return DecisionResult(

            action=action,

            score=total_score,

            confidence=confidence,

            risk=risk,

            trade_plan=trade_plan,

            reasons=reasons,

            warnings=warnings

        )

    # =====================================================
    # ACTION ENGINE
    # =====================================================

    def determine_action(

        self,

        confidence,

        features

    ):

        trend = features.trend.upper()

        # ---------------------------------------------

        if confidence >= 90:

            if trend == "BULLISH":

                return "BUY CALL"

            elif trend == "BEARISH":

                return "BUY PUT"

        # ---------------------------------------------

        elif confidence >= 75:

            if trend == "BULLISH":

                return "WATCH CALL"

            elif trend == "BEARISH":

                return "WATCH PUT"

        # ---------------------------------------------

        elif confidence >= 60:

            return "WAIT"

        # ---------------------------------------------

        return "NO TRADE"


# =========================================================
# GLOBAL ENGINE INSTANCE
# =========================================================

decision_engine = DecisionEngine()