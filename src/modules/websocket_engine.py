from SmartApi.smartWebSocketV2 import SmartWebSocketV2
import threading

sws = None

LIVE_STATE = {
    "NIFTY": {
        "ltp": None,
        "previous_ltp": None,
        "timestamp": None
    },
    "BANKNIFTY": {
        "ltp": None,
        "previous_ltp": None,
        "timestamp": None
    }
}
from datetime import datetime

def on_data(wsapp, message):
    

    global LIVE_STATE

    token = message.get("token")

    ltp = (
        message.get(
            "last_traded_price",
            0
        ) / 100
    )

    timestamp = datetime.now()
    if token == "26000":

        LIVE_STATE["NIFTY"] = {

            "ltp": ltp,

            "timestamp": timestamp
        }

    elif token == "26009":
        

        LIVE_STATE["BANKNIFTY"] = {

            "ltp": ltp,

            "timestamp": timestamp
        }


def on_open(wsapp):

    print("WEBSOCKET CONNECTED")

    try:

        correlation_id = "risk_engine"

        mode = 1

        token_list = [
            {
                "exchangeType": 1,
                "tokens": [
                    "26000",
                    "26009"
                ]
            }
        ]

        sws.subscribe(
            correlation_id,
            mode,
            token_list
        )

        print("SUBSCRIBED TO NIFTY/BANKNIFTY")

    except Exception as e:

        print("SUBSCRIBE ERROR")
        print(e)


def on_error(wsapp, error):

    print("WEBSOCKET ERROR")
    print(error)


def on_close(wsapp):

    print("WEBSOCKET CLOSED")


def start_websocket(
    jwt_token,
    api_key,
    client_code,
    feed_token
):

    global sws

    print("Starting WebSocket Engine...")

    sws = SmartWebSocketV2(
        jwt_token,
        api_key,
        client_code,
        feed_token
    )

    sws.on_open = on_open
    sws.on_data = on_data
    sws.on_error = on_error
    sws.on_close = on_close

    print("WebSocket Object Created")

    print("Connecting WebSocket...")

    threading.Thread(
        target=sws.connect,
        daemon=True
    ).start()

def stop_websocket():

    global sws

    if sws:
        sws.close_connection()


def get_latest_tick(symbol):

    return LIVE_STATE.get(
        symbol,
        {}
    )