import streamlit as st

from modules.websocket_engine import (
    get_latest_tick
)


def fetch_live_market_data(
    initialize_angel
):

    angel_session = initialize_angel()

    if angel_session is None:
        st.error("Angel One Login Failed")
        st.stop()

    smart = angel_session["smart_api"]

    if smart is None:
        return None

    try:

        nifty_tick = get_latest_tick(
            "NIFTY"
        )

        bank_tick = get_latest_tick(
            "BANKNIFTY"
        )

        market = smart.getMarketData(
            "FULL",
            {
                "NSE": [
                    "26000",
                    "26009"
                ]
            }
        )

        fetched = market["data"]["fetched"]

        nifty = fetched[0]
        bank = fetched[1]

        nifty_spot = (
            nifty_tick["ltp"]
            if nifty_tick.get("ltp") is not None
            else float(
                nifty["ltp"]
            )
        )

        bank_spot = (
            bank_tick["ltp"]
            if bank_tick.get("ltp") is not None
            else float(
                bank["ltp"]
            )
        )

        return {

            "NIFTY": {

                "spot": nifty_spot,

                "close": float(
                    nifty["close"]
                ),

                "change": float(
                    nifty["percentChange"]
                ),

                "oi": int(
                    nifty["opnInterest"]
                )
            },

            "BANKNIFTY": {

                "spot": bank_spot,

                "close": float(
                    bank["close"]
                ),

                "change": float(
                    bank["percentChange"]
                ),

                "oi": int(
                    bank["opnInterest"]
                )
            }
        }

    except Exception as e:

        st.error(
            f"Market Data Error: {e}"
        )

        return None
    st.write(
    market_data["NIFTY"]["spot"]
)

    st.write(
    market_data["BANKNIFTY"]["spot"]
)