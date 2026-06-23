from test_app import initialize_angel
from modules.websocket_engine import start_websocket

session = initialize_angel()

start_websocket(
    session["jwt_token"],
    session["api_key"],
    session["client_code"],
    session["feed_token"]
)
angel_session = initialize_angel()

start_websocket(
    angel_session["jwt_token"],
    angel_session["api_key"],
    angel_session["client_code"],
    angel_session["feed_token"]
)