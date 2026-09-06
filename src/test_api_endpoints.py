"""
Backend verification script for FastAPI endpoints
"""
import sys
import io
# Set stdout to UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from pathlib import Path
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from fastapi.testclient import TestClient
from api_server import app

client = TestClient(app)

def test_endpoints():
    print("Testing GET /api/status...")
    res = client.get("/api/status")
    assert res.status_code == 200, f"Status failed: {res.status_code}"
    print("  [PASS] /api/status:", res.json().get("market_status"))

    print("Testing GET /api/market/live...")
    res = client.get("/api/market/live")
    assert res.status_code == 200, f"Market live failed: {res.status_code}"
    assets = res.json()["assets"]
    assert "NIFTY 50 INDEX" in assets, "NIFTY missing"
    assert "BANK NIFTY INDEX" in assets, "BANKNIFTY missing"
    print(f"  [PASS] /api/market/live: NIFTY Spot={assets['NIFTY 50 INDEX']['spot']}, Action={assets['NIFTY 50 INDEX']['action']}")

    print("Testing GET /api/option-chain/NIFTY...")
    res = client.get("/api/option-chain/NIFTY")
    assert res.status_code == 200
    strikes = res.json()["strikes"]
    assert len(strikes) == 11, f"Expected 11 strikes, got {len(strikes)}"
    print(f"  [PASS] /api/option-chain/NIFTY: {len(strikes)} strikes, ATM={res.json()['atm_strike']}")

    print("Testing GET /api/chart/NIFTY...")
    res = client.get("/api/chart/NIFTY")
    assert res.status_code == 200
    bars = res.json()["bars"]
    assert len(bars) > 0, "No chart bars returned"
    print(f"  [PASS] /api/chart/NIFTY: {len(bars)} candlestick bars")

    print("Testing POST /api/trade/execute...")
    order = {
        "asset": "NIFTY 50 INDEX",
        "action": "BUY CALL",
        "symbol": "NIFTY",
        "strike": 24350,
        "option_type": "CE",
        "entry_price": 158.50,
        "stop_loss": 134.70,
        "target": 206.00,
        "quantity": 150,
        "lots": 2,
        "confidence": 88
    }
    res = client.post("/api/trade/execute", json=order)
    assert res.status_code == 200
    trade_id = res.json()["trade_id"]
    print(f"  [PASS] /api/trade/execute: Trade ID = {trade_id}")

    print("Testing GET /api/positions...")
    res = client.get("/api/positions")
    assert res.status_code == 200
    positions = res.json()["positions"]
    assert len(positions) > 0, "No positions found"
    print(f"  [PASS] /api/positions: {len(positions)} positions, total open={res.json()['summary']['total_open']}")

    print("Testing POST /api/trade/close...")
    res = client.post("/api/trade/close", json={"trade_id": trade_id, "exit_price": 172.00})
    assert res.status_code == 200
    print(f"  [PASS] /api/trade/close: Realized PnL = Rs.{res.json()['position']['realized_pnl']}")

    print("Testing GET /api/journal...")
    res = client.get("/api/journal")
    assert res.status_code == 200
    print(f"  [PASS] /api/journal: Total trades = {res.json()['stats']['total_trades']}")

    print("Testing GET /api/diagnostics...")
    res = client.get("/api/diagnostics")
    assert res.status_code == 200
    print(f"  [PASS] /api/diagnostics: Gateway = {res.json()['gateway']['provider']}")

    print("\nALL BACKEND API ENDPOINTS VERIFIED AND WORKING PERFECTLY!")

if __name__ == "__main__":
    test_endpoints()
