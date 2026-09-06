"""
=========================================================
FLOW Chief AI Decision Engine V2
=========================================================

The brain of the FLOW trading desk.

Architecture: 9-Specialist Weighted Scoring Model

Scoring Weights (Total = 100 pts max)
---------------------------------------
  Pattern Analyzer      25 pts  (candlestick + EMA + RSI structure)
  Psychology Analyzer   25 pts  (retail traps + fear/greed + institutional)
  OI Analyzer           20 pts  (derivative open interest buildup/unwind)
  PCR Analyzer          15 pts  (put-call ratio institutional signal)
  News Sentiment        15 pts  (macro + news NLP score)
  Greeks Analyzer       10 pts  (delta/vega favorability)
  Regime Analyzer        8 pts  (trending vs ranging vs volatile)
  Volume Analyzer        8 pts  (call/put volume flow)
  Trend Analyzer         5 pts  (raw directional trend label)

Decision Thresholds (aggregate weighted score)
-----------------------------------------------
  >= +72 : BUY CALL       (strong bullish conviction)
  >= +55 : WATCH CALL     (bullish lean — wait for entry trigger)
  <= -72 : BUY PUT        (strong bearish conviction)
  <= -55 : WATCH PUT      (bearish lean — wait for entry trigger)
  -55 to +55, |score| < 40 : WAIT (ambiguous — market undecided)
  |score| >= 40 but < 55  : WAIT (directional but not strong enough)
  SIDEWAYS + no clear signal: NO TRADE

Responsibilities:
-----------------
  1. Run all 9 specialist analyzers
  2. Apply directional weighting (bullish/bearish sign-aware)
  3. Normalize to [-100, +100] scale
  4. Determine action based on signed score
  5. Build trade plan
  6. Return unified DecisionResult with full reasoning chain
"""

from .models import MarketFeatures, DecisionResult

# --- Existing Analyzers ---
from .trend_analyzer import trend_analyzer
from .pcr_analyzer import pcr_analyzer
from .oi_analyzer import oi_analyzer
from .greeks_analyzer import greeks_analyzer
from .regime_analyzer import regime_analyzer
from .volume_analyzer import volume_analyzer

# --- New V2 Specialist Analyzers ---
from .psychology_analyzer import psychology_analyzer
from .news_sentiment_analyzer import news_sentiment_analyzer
from .pattern_analyzer import pattern_analyzer

from .confidence_engine import confidence_engine
from .risk_engine import risk_engine
from .planner import trade_planner


# Weights for each analyzer (must reflect the docstring above)
ANALYZER_WEIGHTS = {
    "pattern":     1.20,   # Pattern has highest alpha — price is truth
    "psychology":  1.20,   # Human psychology is the biggest edge
    "oi":          1.00,   # OI is institutional positioning
    "pcr":         0.80,   # PCR is derivative sentiment
    "news":        0.80,   # News/macro backdrop
    "greeks":      0.50,   # Greeks add precision
    "regime":      0.40,   # Market regime context
    "volume":      0.40,   # Volume flow confirmation
    "trend":       0.25,   # Trend label (supporting signal only)
}


class DecisionEngine:

    def __init__(self):
        self.specialist_map = [
            ("pattern",    pattern_analyzer),
            ("psychology", psychology_analyzer),
            ("oi",         oi_analyzer),
            ("pcr",        pcr_analyzer),
            ("news",       news_sentiment_analyzer),
            ("greeks",     greeks_analyzer),
            ("regime",     regime_analyzer),
            ("volume",     volume_analyzer),
            ("trend",      trend_analyzer),
        ]

    # =====================================================
    # MAIN ENTRY
    # =====================================================

    def evaluate(self, features: MarketFeatures) -> DecisionResult:

        weighted_score = 0.0
        reasons = []
        warnings = []
        specialist_breakdown = {}

        # ===============================================
        # RUN ALL SPECIALIST ANALYZERS WITH WEIGHTS
        # ===============================================

        for name, analyzer in self.specialist_map:
            result = analyzer.analyze(features)
            weight = ANALYZER_WEIGHTS.get(name, 1.0)
            contribution = result.score * weight
            weighted_score += contribution

            reasons.extend(result.reasons)
            warnings.extend(result.warnings)

            specialist_breakdown[name] = {
                "raw_score": result.score,
                "weight": weight,
                "contribution": round(contribution, 1),
                "reasons": result.reasons,
                "warnings": result.warnings,
                "metadata": result.metadata
            }

        # ===============================================
        # NORMALIZE TO [-100, +100]
        # ===============================================

        # Max theoretical weighted score
        max_raw = sum(
            25 * w for k, w in ANALYZER_WEIGHTS.items()
            if k in ["pattern", "psychology"]
        ) + sum(
            20 * w for k, w in ANALYZER_WEIGHTS.items()
            if k in ["oi"]
        ) + sum(
            15 * w for k, w in ANALYZER_WEIGHTS.items()
            if k in ["pcr", "news"]
        ) + sum(
            10 * w for k, w in ANALYZER_WEIGHTS.items()
            if k in ["greeks"]
        ) + sum(
            8 * w for k, w in ANALYZER_WEIGHTS.items()
            if k in ["regime", "volume"]
        ) + sum(
            5 * w for k, w in ANALYZER_WEIGHTS.items()
            if k in ["trend"]
        )
        # Roughly ~120-130 pts max — normalize to 100
        max_raw = max(max_raw, 1)
        normalized_score = round((weighted_score / max_raw) * 100)
        normalized_score = max(-100, min(100, normalized_score))

        # ===============================================
        # CONFIDENCE (0-100%)
        # ===============================================

        confidence = confidence_engine.calculate(abs(normalized_score))

        # ===============================================
        # ACTION DETERMINATION (sign-aware)
        # ===============================================

        action = self._determine_action(normalized_score, features)

        # ===============================================
        # RISK CLASSIFICATION
        # ===============================================

        risk = risk_engine.classify(confidence)

        # ===============================================
        # TRADE PLAN
        # ===============================================

        trade_plan = trade_planner.build(action, features.option_premium)

        # ===============================================
        # DEDUPLICATE & SORT REASONS
        # ===============================================

        seen = set()
        unique_reasons = []
        for r in reasons:
            if r not in seen:
                seen.add(r)
                unique_reasons.append(r)

        seen_w = set()
        unique_warnings = []
        for w in warnings:
            if w not in seen_w:
                seen_w.add(w)
                unique_warnings.append(w)

        return DecisionResult(
            action=action,
            score=normalized_score,
            confidence=confidence,
            risk=risk,
            trade_plan=trade_plan,
            reasons=unique_reasons,
            warnings=unique_warnings,
            specialist_breakdown=specialist_breakdown
        )

    # =====================================================
    # SIGN-AWARE ACTION ENGINE
    # =====================================================

    def _determine_action(self, score: int, features: MarketFeatures) -> str:

        trend = features.trend.upper()
        trap = features.trap_state.upper()

        # Hard override: trap states always win (protect capital)
        if trap == "BULL_TRAP_REJECTION" and score > 0:
            return "WATCH PUT"  # Reversal setup

        if trap == "BEAR_TRAP_REBOUND" and score < 0:
            return "WATCH CALL"  # Bounce setup

        # Standard action matrix (sign-aware)
        if score >= 72:
            return "BUY CALL"

        elif score >= 55:
            return "WATCH CALL"

        elif score <= -72:
            return "BUY PUT"

        elif score <= -55:
            return "WATCH PUT"

        elif -40 <= score <= 40:
            # Truly ambiguous — no trade unless trend is very strong
            if "STRONG" in trend:
                return "WAIT"
            return "NO TRADE"

        else:
            # |score| between 40-55: directional but not confident enough
            return "WAIT"


# =========================================================
# GLOBAL ENGINE INSTANCE
# =========================================================

decision_engine = DecisionEngine()