"""
=========================================================
Greeks Analyzer
=========================================================

Responsible for evaluating option Greeks.

Evaluates

- Delta
- Gamma
- Theta
- Vega

Returns an institutional score.
"""

from .models import (
    MarketFeatures,
    AnalyzerResult
)


class GreeksAnalyzer:

    def analyze(
        self,
        features: MarketFeatures
    ) -> AnalyzerResult:

        score = 0

        reasons = []

        warnings = []

        # ==================================================
        # DELTA
        # ==================================================

        delta = abs(features.delta)

        if delta >= 0.70:

            score += 10

            reasons.append(
                "Strong Delta"
            )

        elif delta >= 0.50:

            score += 7

            reasons.append(
                "Healthy Delta"
            )

        elif delta >= 0.30:

            score += 4

            reasons.append(
                "Moderate Delta"
            )

        else:

            score += 1

            warnings.append(
                "Weak Delta"
            )

        # ==================================================
        # GAMMA
        # ==================================================

        gamma = features.gamma

        if gamma >= 0.05:

            score += 5

            reasons.append(
                "Strong Gamma"
            )

        elif gamma >= 0.02:

            score += 3

            reasons.append(
                "Stable Gamma"
            )

        else:

            warnings.append(
                "Low Gamma"
            )

        # ==================================================
        # THETA
        # ==================================================

        theta = abs(features.theta)

        if theta <= 5:

            score += 3

            reasons.append(
                "Low Theta Decay"
            )

        elif theta <= 10:

            score += 2

            reasons.append(
                "Acceptable Theta"
            )

        else:

            warnings.append(
                "High Theta Decay"
            )

        # ==================================================
        # VEGA
        # ==================================================

        vega = abs(features.vega)

        if vega <= 10:

            score += 2

            reasons.append(
                "Controlled Vega Exposure"
            )

        else:

            warnings.append(
                "High Vega Risk"
            )

        # ==================================================
        # BONUS
        # ==================================================

        if delta >= 0.70 and gamma >= 0.05:

            score += 2

            reasons.append(
                "Excellent Greeks Alignment"
            )

        # ==================================================
        # RETURN
        # ==================================================

        return AnalyzerResult(

            score=min(score, 20),

            reasons=reasons,

            warnings=warnings

        )


greeks_analyzer = GreeksAnalyzer()