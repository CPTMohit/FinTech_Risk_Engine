"""
=========================================================
Volume Analyzer
=========================================================

Responsible for evaluating

• Market Liquidity
• Participation
• Call vs Put Dominance
• Volume Conviction
"""

from .models import (
    MarketFeatures,
    AnalyzerResult
)


class VolumeAnalyzer:

    def analyze(
        self,
        features: MarketFeatures
    ) -> AnalyzerResult:

        call_volume = features.call_volume

        put_volume = features.put_volume

        total_volume = (
            call_volume +
            put_volume
        )

        score = 0

        reasons = []

        warnings = []

        # ==================================================
        # MARKET LIQUIDITY
        # ==================================================

        if total_volume >= 2_000_000:

            score += 5

            reasons.append(
                "Excellent Market Liquidity"
            )

        elif total_volume >= 1_000_000:

            score += 4

            reasons.append(
                "High Market Liquidity"
            )

        elif total_volume >= 500_000:

            score += 3

            reasons.append(
                "Moderate Liquidity"
            )

        else:

            score += 1

            warnings.append(
                "Low Market Liquidity"
            )

        # ==================================================
        # PARTICIPATION
        # ==================================================

        if call_volume > put_volume * 1.30:

            score += 3

            reasons.append(
                "Strong Call Participation"
            )

        elif put_volume > call_volume * 1.30:

            score += 3

            reasons.append(
                "Strong Put Participation"
            )

        else:

            score += 2

            reasons.append(
                "Balanced Participation"
            )

        # ==================================================
        # PARTICIPATION QUALITY
        # ==================================================

        imbalance = abs(
            call_volume - put_volume
        ) / max(
            total_volume,
            1
        )

        if imbalance > 0.60:

            warnings.append(
                "Extreme Volume Imbalance"
            )

        elif imbalance < 0.15:

            reasons.append(
                "Healthy Two-Way Participation"
            )

        # ==================================================
        # INSTITUTIONAL ACTIVITY
        # ==================================================

        average_volume = total_volume / 2

        if average_volume > 1_000_000:

            score += 2

            reasons.append(
                "Institutional Activity Detected"
            )

        # ==================================================
        # FINAL SCORE
        # ==================================================

        return AnalyzerResult(

            score=min(score, 10),

            reasons=reasons,

            warnings=warnings

        )


volume_analyzer = VolumeAnalyzer()