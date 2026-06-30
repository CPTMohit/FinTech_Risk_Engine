"""
=========================================================
Market Regime Analyzer
=========================================================

Responsible for evaluating the current market regime.

Possible Regimes

- TRENDING
- BREAKOUT MARKET
- PULLBACK
- RANGE
- VOLATILE
"""

from .models import (
    MarketFeatures,
    AnalyzerResult
)


class RegimeAnalyzer:

    def analyze(
        self,
        features: MarketFeatures
    ) -> AnalyzerResult:

        regime = features.market_regime.upper()

        # ==================================================
        # TRENDING
        # ==================================================

        if regime == "TRENDING":

            return AnalyzerResult(

                score=15,

                reasons=[
                    "Strong Trending Market",
                    "Trend Following Conditions"
                ]

            )

        # ==================================================
        # BREAKOUT
        # ==================================================

        elif regime == "BREAKOUT MARKET":

            return AnalyzerResult(

                score=14,

                reasons=[
                    "Breakout Confirmed",
                    "Momentum Expansion"
                ]

            )

        # ==================================================
        # PULLBACK
        # ==================================================

        elif regime == "PULLBACK":

            return AnalyzerResult(

                score=10,

                reasons=[
                    "Healthy Pullback",
                    "Possible Trend Continuation"
                ]

            )

        # ==================================================
        # RANGE
        # ==================================================

        elif regime == "RANGE":

            return AnalyzerResult(

                score=8,

                reasons=[
                    "Range Bound Market"
                ],

                warnings=[
                    "Breakout Awaited"
                ]

            )

        # ==================================================
        # VOLATILE
        # ==================================================

        elif regime == "VOLATILE":

            return AnalyzerResult(

                score=6,

                reasons=[
                    "Highly Volatile Market"
                ],

                warnings=[
                    "Reduce Position Size",
                    "High Price Swings"
                ]

            )

        # ==================================================
        # UNKNOWN
        # ==================================================

        return AnalyzerResult(

            score=3,

            reasons=[
                "Unknown Market Regime"
            ],

            warnings=[
                "Unable to Classify Market"
            ]

        )


regime_analyzer = RegimeAnalyzer()