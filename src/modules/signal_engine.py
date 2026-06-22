# =====================================================
# SIGNAL ENGINE
# =====================================================

def calculate_signal(
    change,
    pcr
):

    score = 0

    if change > 0.30:
        score += 20

    elif change < -0.30:
        score -= 20

    if pcr < 0.95:
        score += 20

    elif pcr > 1.05:
        score -= 20

    if score >= 30:

        action = "BUY CALL"

    elif score <= -30:

        action = "BUY PUT"

    else:

        action = "NO TRADE"

    probability = min(
        99,
        max(
            55,
            50 + abs(score)
        )
    )

    return (
        action,
        score,
        probability
    )
# =====================================================
# BUILD LIVE STATE
# =====================================================
def calculate_trend(
    change,
    pcr,
    oi_structure
):

    if (
        change > 0.30
        and pcr > 0.90
        and oi_structure == "LONG BUILDUP"
    ):
        return "STRONG BULLISH"

    elif (
        change > 0
        and pcr > 0.80
    ):
        return "BULLISH"

    elif (
        change < -0.30
        and pcr < 0.80
        and oi_structure == "SHORT BUILDUP"
    ):
        return "STRONG BEARISH"

    elif (
        change < 0
        and pcr < 0.90
    ):
        return "BEARISH"

    return "SIDEWAYS"

def classify_oi_buildup(change_pct, oi):

    if change_pct > 0.30 and oi > 100000000:
        return "LONG BUILDUP"

    elif change_pct < -0.30 and oi > 100000000:
        return "SHORT BUILDUP"

    elif change_pct > 0 and oi < 100000000:
        return "SHORT COVERING"

    else:
        return "LONG UNWINDING" 


def generate_trade_decision(
    state
):

    score = 0

    reasons = []

    if state["trend"] in [
        "BULLISH",
        "STRONG BULLISH"
    ]:

        score += 25

        reasons.append(
            "Bullish Trend"
        )

    if state["pcr"] > 1.10:

        score += 25

        reasons.append(
        "Strong Bullish PCR"
    )

    elif state["pcr"] > 1.00:

        score += 15

        reasons.append(
            "Bullish PCR"
    )

    elif state["pcr"] < 0.80:

        score -= 25

        reasons.append(
            "Strong Bearish PCR"
    )

    elif state["pcr"] < 0.90:

        score -= 15

        reasons.append(
         "Bearish PCR"
    )

    if state["oi_structure"] in [
        "LONG BUILDUP",
        "SHORT COVERING"
    ]:

        score += 20

        reasons.append(
            "Positive OI Structure"
        )

    if state["delta"] > 0:

        score += 15

        reasons.append(
            "Positive Delta"
        )

    if state["put_volume"] > state["call_volume"]:

        score -= 10

        reasons.append(
            "Put Side Dominance"
    )

    else:

        score += 10

        reasons.append(
            "Call Side Dominance"
    )

    confidence = min(
        score,
        95
    )

    return (
        confidence,
        reasons
    )
