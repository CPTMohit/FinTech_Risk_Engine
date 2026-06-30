"""
=========================================================
Trend Analyzer
=========================================================

Responsible for evaluating the market trend.

This analyzer ONLY evaluates trend.

Output:
    AnalyzerResult
"""

from .models import (
    MarketFeatures,
    AnalyzerResult
)


class TrendAnalyzer:

    def analyze(
        self,
        features: MarketFeatures
    ) -> AnalyzerResult:

        trend = features.trend.upper()

        # ==================================================
        # BULLISH
        # ==================================================

        if trend == "BULLISH":

            return AnalyzerResult(

                score=25,

                reasons=[
                    "Bullish Trend Confirmed"
                ]

            )

        # ==================================================
        # BEARISH
        # ==================================================

        elif trend == "BEARISH":

            return AnalyzerResult(

                score=25,

                reasons=[
                    "Bearish Trend Confirmed"
                ]

            )

        # ==================================================
        # SIDEWAYS
        # ==================================================

        elif trend == "SIDEWAYS":

            return AnalyzerResult(

                score=10,

                reasons=[
                    "Sideways Market"
                ],

                warnings=[
                    "Trend Strength Weak"
                ]

            )

        # ==================================================
        # RANGING
        # ==================================================

        elif trend == "RANGING":

            return AnalyzerResult(

                score=8,

                reasons=[
                    "Range Bound Market"
                ],

                warnings=[
                    "Breakout Confirmation Needed"
                ]

            )

        # ==================================================
        # UNKNOWN
        # ==================================================

        return AnalyzerResult(

            score=5,

            reasons=[
                "Unknown Trend"
            ],

            warnings=[
                "Trend Detection Failed"
            ]

        )


trend_analyzer = TrendAnalyzer()