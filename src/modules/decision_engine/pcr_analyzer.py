"""
=========================================================
PCR Analyzer
=========================================================

Responsible for evaluating Put Call Ratio (PCR).

Institutional Interpretation

PCR > 1.30    : Extremely Bullish

1.10 - 1.30   : Bullish

1.00 - 1.10   : Mild Bullish

0.90 - 1.00   : Neutral

0.70 - 0.90   : Bearish

< 0.70        : Extremely Bearish
"""

from .models import (
    MarketFeatures,
    AnalyzerResult
)


class PCRAnalyzer:

    def analyze(
        self,
        features: MarketFeatures
    ) -> AnalyzerResult:

        pcr = features.pcr

        # ==================================================
        # EXTREMELY BULLISH
        # ==================================================

        if pcr >= 1.30:

            return AnalyzerResult(

                score=20,

                reasons=[
                    "Extremely Bullish PCR",
                    "Aggressive Put Writing"
                ]

            )

        # ==================================================
        # BULLISH
        # ==================================================

        elif pcr >= 1.10:

            return AnalyzerResult(

                score=18,

                reasons=[
                    "Bullish PCR",
                    "Healthy Put Writing"
                ]

            )

        # ==================================================
        # MILD BULLISH
        # ==================================================

        elif pcr >= 1.00:

            return AnalyzerResult(

                score=15,

                reasons=[
                    "PCR Above 1",
                    "Positive Market Sentiment"
                ]

            )

        # ==================================================
        # NEUTRAL
        # ==================================================

        elif pcr >= 0.90:

            return AnalyzerResult(

                score=10,

                reasons=[
                    "Neutral PCR"
                ],

                warnings=[
                    "No Strong PCR Edge"
                ]

            )

        # ==================================================
        # BEARISH
        # ==================================================

        elif pcr >= 0.70:

            return AnalyzerResult(

                score=5,

                reasons=[
                    "Bearish PCR"
                ],

                warnings=[
                    "Call Writers Dominating"
                ]

            )

        # ==================================================
        # EXTREMELY BEARISH
        # ==================================================

        return AnalyzerResult(

            score=2,

            reasons=[
                "Extremely Bearish PCR"
            ],

            warnings=[
                "Market Sentiment Weak"
            ]

        )


pcr_analyzer = PCRAnalyzer()