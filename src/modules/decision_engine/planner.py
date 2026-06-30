"""
=========================================================
Trade Planner
=========================================================
"""

from .models import TradePlan


class TradePlanner:

    def build(
        self,
        action,
        premium
    ) -> TradePlan:

        # No execution for these actions
        if action in [
            "NO TRADE",
            "WAIT",
            "WATCH CALL",
            "WATCH PUT"
        ]:

            return TradePlan(
                entry=0.0,
                stop_loss=0.0,
                target=0.0,
                risk_reward=0.0
            )

        # Build option trade
        entry = round(
            premium,
            2
        )

        stop = round(
            premium * 0.90,
            2
        )

        target = round(
            premium * 1.30,
            2
        )

        risk = entry - stop

        reward = target - entry

        rr = round(
            reward / risk,
            2
        ) if risk > 0 else 0.0

        return TradePlan(
            entry=entry,
            stop_loss=stop,
            target=target,
            risk_reward=rr
        )


trade_planner = TradePlanner()