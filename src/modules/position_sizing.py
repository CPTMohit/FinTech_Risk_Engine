# =========================
# V16 POSITION SIZING CONFIG
# =========================

TOTAL_CAPITAL = 100000      # Account Capital
RISK_PER_TRADE = 0.02       # 2% Risk Per Trade
LOT_SIZE_NIFTY = 75
LOT_SIZE_BANKNIFTY = 35

# =====================================================
# POSITION SIZING ENGINE (V16)
# =====================================================

def calculate_position_size(
    premium,
    confidence,
    risk_reward,
    symbol
):

    if premium <= 0:
        return 0, 0

    base_risk = (
        TOTAL_CAPITAL
        * RISK_PER_TRADE
        
    )
    

    confidence_multiplier = (
        confidence / 100
    )

    rr_multiplier = min(
        2.0,
        max(
            0.5,
            risk_reward
        )
    )

    adjusted_risk = (
        base_risk
        * confidence_multiplier
        * rr_multiplier
    )

    lot_size = (
        LOT_SIZE_NIFTY
        if symbol == "NIFTY"
        else LOT_SIZE_BANKNIFTY
    )

    cost_per_lot = (
        premium
        * lot_size
    )

    lots = max(
        1,
        int(
            adjusted_risk
            / cost_per_lot
        )
    )

    quantity = (
        lots
        * lot_size
    )

    return lots, quantity

