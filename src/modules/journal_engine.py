from datetime import datetime
import pandas as pd
JOURNAL_FILE = "trade_journal.csv"

def log_trade(state, asset_name):

    row = pd.DataFrame(
        [
            {
                "timestamp": datetime.now(),
                "asset": asset_name,
                "signal": state["action"],
                "entry": state["entry_price"],
                "stop_loss": state["stop_loss"],
                "target": state["target"],
                "confidence": state["trade_confidence"],
                "quantity": state["recommended_qty"],
                "capital_required": state["capital_required"],
                "max_loss": state["max_loss"],
                "expected_profit": state["expected_profit"],
                "status": "OPEN",
                "pnl": 0
            }
        ]
    )

    row.to_csv(
        JOURNAL_FILE,
        mode="a",
        header=False,
        index=False
    )
