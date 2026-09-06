"""
=========================================================
FLOW News & Macro Sentiment Analyzer
=========================================================

Scores macro economic conditions and news sentiment
using deterministic rule-based heuristics derived from:
  - RBI / Fed policy stance
  - FII / DII fund flow trends
  - Global risk-on / risk-off cues (Nasdaq, Hang Seng)
  - Domestic triggers (Budget, earnings, geopolitical)
  - VIX environment

The analyzer uses the pre-computed news_sentiment_score
(-1.0 to +1.0) and macro_headline string from MarketFeatures
and applies keyword-based NLP rules + numerical scoring.

Output:
    AnalyzerResult (score range: -20 to +20)
"""

from .models import MarketFeatures, AnalyzerResult


# ==============================================================
# KEYWORD RULE DICTIONARIES
# ==============================================================

# Strong positive macro keywords (each adds weight)
STRONG_BULLISH_KEYWORDS = [
    "rate cut", "stimulus", "easing", "fed pivot", "rbi accommodative",
    "strong gdp", "record fii buying", "fii inflows", "dii buying",
    "q4 beat", "earnings beat", "results beat", "buyback", "dividend",
    "capex boost", "infrastructure spend", "record gst", "trade surplus",
    "inflation falls", "cpi down", "wpi easing", "current account surplus",
    "china stimulus", "global rally", "risk on", "bull market",
    "upgrade", "rating upgrade", "credit upgrade", "market reopen"
]

# Moderate positive keywords
MILD_BULLISH_KEYWORDS = [
    "steady growth", "stable", "positive outlook", "recovery",
    "resilient economy", "manageable deficit", "fii neutral",
    "dii support", "consolidation", "range bound positive",
    "oil falls", "rupee strengthens", "crude dip", "commodity relief",
    "positive cues", "green global", "asia positive", "europe positive"
]

# Strong negative macro keywords
STRONG_BEARISH_KEYWORDS = [
    "rate hike", "hawkish", "tightening", "recession fears",
    "fii outflows", "fii selling", "massive sell-off", "capital flight",
    "earnings miss", "profit warning", "guidance cut", "revenue miss",
    "geopolitical tension", "war", "conflict escalation", "border tension",
    "inflation surge", "cpi spike", "stagflation", "credit downgrade",
    "bank stress", "banking crisis", "liquidity crunch", "default risk",
    "china slowdown", "global selloff", "risk off", "bear market",
    "imf warning", "debt crisis", "currency crisis", "rupee crash"
]

# Moderate negative keywords
MILD_BEARISH_KEYWORDS = [
    "uncertainty", "caution", "profit booking", "mixed global cues",
    "weak asia", "crude rises", "oil surge", "commodity pressure",
    "trade deficit widening", "current account deficit", "rupee weak",
    "dii selling", "margin pressure", "input cost rise",
    "global caution", "fed hawkish tone", "wait and watch"
]


class NewsSentimentAnalyzer:

    def analyze(self, features: MarketFeatures) -> AnalyzerResult:

        score = 0
        reasons = []
        warnings = []

        sentiment_score = features.news_sentiment_score   # -1.0 to +1.0
        headline = features.macro_headline.lower()

        # ==============================================================
        # 1. QUANTITATIVE SENTIMENT SCORE (primary signal)
        # ==============================================================

        if sentiment_score >= 0.60:
            score += 20
            reasons.append(f"Strong Positive News Flow (Sentiment: {sentiment_score:+.2f}): Risk-on environment supportive of longs")

        elif sentiment_score >= 0.30:
            score += 14
            reasons.append(f"Positive Macro Backdrop (Sentiment: {sentiment_score:+.2f}): Tailwind for upside")

        elif sentiment_score >= 0.10:
            score += 8
            reasons.append(f"Mildly Positive Sentiment (Sentiment: {sentiment_score:+.2f}): Neutral to slight tailwind")

        elif sentiment_score >= -0.10:
            score += 3
            reasons.append(f"Neutral News Environment (Sentiment: {sentiment_score:+.2f}): No macro catalyst in play")

        elif sentiment_score >= -0.30:
            score -= 8
            reasons.append(f"Mildly Negative Macro (Sentiment: {sentiment_score:+.2f}): Slight headwind — trade with caution")
            warnings.append("Negative news flow may limit upside momentum")

        elif sentiment_score >= -0.60:
            score -= 14
            reasons.append(f"Negative News Pressure (Sentiment: {sentiment_score:+.2f}): Risk-off tone — hedge or stay out")
            warnings.append("FII selling / risk-off flows likely to suppress bulls")

        else:
            score -= 20
            reasons.append(f"Severe Negative Macro Shock (Sentiment: {sentiment_score:+.2f}): Major risk event — avoid all longs")
            warnings.append("Macro shock environment: stop-losses critical, size down aggressively")

        # ==============================================================
        # 2. KEYWORD NLP RULE SCAN ON HEADLINE
        # ==============================================================

        keyword_delta = 0

        for kw in STRONG_BULLISH_KEYWORDS:
            if kw in headline:
                keyword_delta += 4

        for kw in MILD_BULLISH_KEYWORDS:
            if kw in headline:
                keyword_delta += 2

        for kw in STRONG_BEARISH_KEYWORDS:
            if kw in headline:
                keyword_delta -= 4

        for kw in MILD_BEARISH_KEYWORDS:
            if kw in headline:
                keyword_delta -= 2

        # Clamp keyword delta contribution to +/- 8
        keyword_delta = max(-8, min(8, keyword_delta))
        score += keyword_delta

        if keyword_delta > 3:
            reasons.append(f"Headline NLP: Bullish keywords detected in macro news (+{keyword_delta} pts)")
        elif keyword_delta < -3:
            reasons.append(f"Headline NLP: Bearish keywords detected in macro news ({keyword_delta} pts)")
            warnings.append(f"Macro headline: \"{features.macro_headline[:80]}\"")

        # ==============================================================
        # 3. SPECIAL MACRO REGIME RULES
        # ==============================================================

        # High VIX environment check (derived from iv field)
        iv = features.iv
        if iv > 20:
            score -= 6
            warnings.append(f"Elevated IV ({iv:.1f}%): Options market pricing in stress — size down")
        elif iv > 25:
            score -= 12
            warnings.append(f"High IV ({iv:.1f}%): Fear spike — premium expensive, directional bets risky")
        elif iv < 12:
            score += 4
            reasons.append(f"Low IV ({iv:.1f}%): Complacency or calm environment — trend trades favorable")

        # Clamp final score
        score = max(-20, min(20, score))

        return AnalyzerResult(
            score=score,
            reasons=reasons,
            warnings=warnings,
            metadata={
                "sentiment_score": sentiment_score,
                "keyword_delta": keyword_delta,
                "iv": iv,
                "macro_headline": features.macro_headline[:100]
            }
        )


news_sentiment_analyzer = NewsSentimentAnalyzer()
