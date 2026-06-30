"""
=========================================================
Risk Engine
=========================================================
"""


class RiskEngine:

    def classify(
        self,
        confidence: int
    ) -> str:

        if confidence >= 90:
            return "VERY LOW"

        elif confidence >= 80:
            return "LOW"

        elif confidence >= 65:
            return "MEDIUM"

        elif confidence >= 50:
            return "HIGH"

        return "VERY HIGH"


risk_engine = RiskEngine()