"""
=========================================================
OI Analyzer
=========================================================

Responsible for evaluating Open Interest structure.

Institutional Interpretation

LONG BUILDUP      -> Strong Bullish

SHORT COVERING    -> Bullish

SHORT BUILDUP     -> Bearish

LONG UNWINDING    -> Weakness
"""

from .models import (
    MarketFeatures,
    AnalyzerResult
)


class OIAnalyzer:

    def analyze(
        self,
        features: MarketFeatures
    ) -> AnalyzerResult:

        oi = features.oi_structure.upper()

        # ==================================================
        # LONG BUILDUP
        # ==================================================

        if oi == "LONG BUILDUP":

            return AnalyzerResult(

                score=20,

                reasons=[
                    "Long Buildup Detected",
                    "Fresh Long Positions Added"
                ]

            )

        # ==================================================
        # SHORT COVERING
        # ==================================================

        elif oi == "SHORT COVERING":

            return AnalyzerResult(

                score=16,

                reasons=[
                    "Short Covering Detected",
                    "Bearish Positions Being Closed"
                ]

            )

        # ==================================================
        # SHORT BUILDUP
        # ==================================================

        elif oi == "SHORT BUILDUP":

            return AnalyzerResult(

                score=12,

                reasons=[
                    "Short Buildup Observed"
                ],

                warnings=[
                    "Bearish Pressure Increasing"
                ]

            )

        # ==================================================
        # LONG UNWINDING
        # ==================================================

        elif oi == "LONG UNWINDING":

            return AnalyzerResult(

                score=6,

                reasons=[
                    "Long Unwinding Detected"
                ],

                warnings=[
                    "Bullish Conviction Weakening"
                ]

            )

        # ==================================================
        # UNKNOWN
        # ==================================================

        return AnalyzerResult(

            score=2,

            reasons=[
                "Unknown Open Interest Structure"
            ],

            warnings=[
                "Unable to Interpret OI Pattern"
            ]

        )


oi_analyzer = OIAnalyzer()