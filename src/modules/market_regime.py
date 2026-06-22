def classify_market_regime(
    change,
    pcr,
    oi_bias
):

    if abs(change) >= 1.0:

            return "VOLATILE MARKET"

    elif (
        abs(change) >= 0.50
        and oi_bias == "BULLISH"
    ):

        if oi_bias == "BULLISH":

            return "BULLISH TREND"

        else:

            return "BEARISH TREND"

    elif (
        pcr > 0.90
        and pcr < 1.10
    ):

        return "RANGE BOUND MARKET"

    else:

        return "BREAKOUT MARKET"
