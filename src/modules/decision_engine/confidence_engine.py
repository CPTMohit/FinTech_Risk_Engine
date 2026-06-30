"""
=========================================================
Confidence Engine
=========================================================

Converts market score into institutional confidence.
"""


class ConfidenceEngine:

    def calculate(
        self,
        score: int
    ) -> int:

        if score >= 95:
            return 99

        elif score >= 90:
            return 95

        elif score >= 80:
            return 90

        elif score >= 70:
            return 80

        elif score >= 60:
            return 70

        elif score >= 50:
            return 60

        return max(score, 0)


confidence_engine = ConfidenceEngine()