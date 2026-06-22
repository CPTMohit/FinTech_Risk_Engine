"""
Project: FinTech Risk Isolation Engine V2
Module: SmartAPI Live Dashboard
Author: Mohit Singh
"""

import os
import pandas as pd
import sys
from unittest import result
import SmartApi
import streamlit as st
from datetime import datetime
from plyer import notification
from SmartApi import SmartConnect
import pyotp
from modules.market_status import (
    NSE_HOLIDAYS_2026,
    get_market_status
)
from modules.alert_engine import (
    send_desktop_alert,
    LAST_ALERT
)
from modules.journal_engine import (
    JOURNAL_FILE
)
from modules.journal_engine import (
    JOURNAL_FILE,
    log_trade
)
from modules.market_regime import (
    classify_market_regime
)
from modules.position_sizing import (
    TOTAL_CAPITAL,
    RISK_PER_TRADE,
    LOT_SIZE_NIFTY,
    LOT_SIZE_BANKNIFTY,
    calculate_position_size
)
from modules.signal_engine import (
    calculate_signal,
    calculate_trend,
    classify_oi_buildup,
    generate_trade_decision
)
# =====================================================
# ANGEL ONE CONFIG
# =====================================================
API_KEY = "3xK955MH"
CLIENT_CODE = "AACI729341"
PIN = "0912"
TOTP_SECRET = "ZG4AT5YV6GPJQNPPVHLESN5JZI"







if not os.path.exists(JOURNAL_FILE):

    pd.DataFrame(
        columns=[
            "timestamp",
            "asset",
            "signal",
            "entry",
            "stop_loss",
            "target",
            "confidence",
            "quantity",
            "capital_required",
            "max_loss",
            "expected_profit",
            "status",
            "pnl"
        ]
    ).to_csv(
        JOURNAL_FILE,
        index=False
    )

# =====================================================
# PATH SETUP
# =====================================================

current_dir = os.path.dirname(
    os.path.abspath(__file__)
)

project_root = os.path.abspath(
    os.path.join(current_dir, "..")
)

if project_root not in sys.path:
    sys.path.insert(
        0,
        project_root
    )

# =====================================================
#UI IMPORTS
# =====================================================

from src.ui import (
    render_asset_card,
    render_strength_meter,
    render_signals_table,
    render_position_table,
    render_option_chain_panel,
    render_trade_card,
    THEME_CONFIG
)

# =====================================================
# STREAMLIT CONFIG
# =====================================================

st.set_page_config(
    page_title="Risk  Engine V2",
    page_icon="⚡",
    layout="wide"
)

# =====================================================
# GLOBAL CSS
# =====================================================

st.markdown(
    f"""
    <style>

    .stApp {{
        background:#0d1117;
        color:#c9d1d9;
    }}

    .global-ticker-card {{
        background:#161b22;
        border:1px solid {THEME_CONFIG["border"]};
        border-radius:8px;
        padding:16px;
        margin-bottom:12px;
    }}

    .custom-table {{
        width:100%;
        border-collapse:collapse;
        background:#161b22;
        color:#e6edf3;
    }}

    .custom-table th {{
        background:#21262d;
        padding:10px;
    }}

    .custom-table td {{
        padding:10px;
    }}

    .macro-alert-box {{
        background:#1f1b11;
        border-left:4px solid #e3b341;
        padding:12px;
        border-radius:4px;
    }}

    </style>
    """,
    unsafe_allow_html=True
)

# =====================================================
# SMART API LOGIN
# =====================================================

@st.cache_resource(ttl=3600)
def initialize_angel():

    smart = SmartConnect(
        api_key=API_KEY
    )

    totp = pyotp.TOTP(
        TOTP_SECRET
    ).now()

    session = smart.generateSession(
        CLIENT_CODE,
        PIN,
        totp
    )

    if session["status"]:

        return smart

    return None


# =====================================================
# DESKTOP ALERT ENGINE
# =====================================================

    alert_id = (
            f"{best_asset_name}_"
            f"{best_asset_data['action']}"
    )

    if (
            best_asset_data["trade_confidence"] >= 75
            and LAST_ALERT != alert_id
        ):

            send_desktop_alert(
            f"{best_asset_data['action']} ALERT",
            (
                f"{best_asset_name}\n"
                f"Confidence: {best_asset_data['trade_confidence']}%\n"
                f"Entry: ₹{best_asset_data['entry_price']:.2f}"
            )
        )

    LAST_ALERT = alert_id
# =====================================================
# LIVE MARKET DATA
# =====================================================
def fetch_live_market_data():

    smart = initialize_angel()

    if smart is None:

        return None

    try:

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

        return {

            "NIFTY": {

                "spot":
                    float(
                        nifty["ltp"]
                    ),

                "close":
                    float(
                        nifty["close"]
                    ),

                "change":
                    float(
                        nifty["percentChange"]
                    ),

                "oi":
                    int(
                        nifty["opnInterest"]
                    )
            },

            "BANKNIFTY": {

                "spot":
                    float(
                        bank["ltp"]
                    ),

                "close":
                    float(
                        bank["close"]
                    ),

                "change":
                    float(
                        bank["percentChange"]
                    ),

                "oi":
                    int(
                        bank["opnInterest"]
                    )
            }
        }

    except Exception as e:

        st.error(
            f"Market Data Error: {e}"
        )

        return None

# =====================================================
# PCR DATA
# =====================================================

# @st.cache_data(ttl=60)
def fetch_pcr_data():

    smart = initialize_angel()

    data = smart.putCallRatio()

    print("PCR DATA =")
    print(data)

    pcr_map = {
        "NIFTY": 0.95,
        "BANKNIFTY": 0.95
    }

    for row in data["data"]:

        symbol = row["tradingSymbol"]

        if (
            symbol.startswith("NIFTY")
            and "NXT" not in symbol
            and symbol.endswith("FUT")
        ):

            pcr_map["NIFTY"] = float(
                row["pcr"]
            )

        elif (
            symbol.startswith("BANKNIFTY")
            and symbol.endswith("FUT")
        ):

            pcr_map["BANKNIFTY"] = float(
                row["pcr"]
            )

    print("FINAL PCR MAP =", pcr_map)

    return pcr_map

        

def fetch_greeks(
    spot,
    strike,
    option_type
):


    moneyness = abs(
        spot - strike
    ) / spot

    delta = (
        0.70
        if option_type == "CE"
        else -0.70
    )

    gamma = (
        round(
            0.02 - (moneyness * 0.01),
            4
        )
    )

    theta = (
        round(
            -4.5 - (moneyness * 10),
            2
        )
    )

    vega = (
        round(
            8 + (moneyness * 20),
            2
        )
    )

    return (
        delta,
        gamma,
        theta,
        vega
    )

def discover_atm_contracts(
    smart,
    symbol,
    atm_strike
):
    search_term = symbol

    search_term = "NIFTY"

    print(
    "SEARCH TERM =",
    search_term
)
    result = smart.searchScrip(
    "NFO",
    symbol
)

    print("SEARCH TERM =", symbol)
    print("SEARCH RESULT STATUS =", result.get("status"))

    if result.get("data"):
       
        for row in result["data"][:20]:
            print(row["tradingsymbol"])
            print("TOTAL RESULTS =", len(result["data"]))

            print("RAW SEARCH RESULT")


    ce_symbol = ""
    ce_token = ""

    pe_symbol = ""
    pe_token = ""

    if (
            result is None
            or not result.get("status")
            or result.get("data") is None
        ):
            print("SEARCH RESULT =", result)
            return {
                "ce_symbol": "",
                "ce_token": "",
                "pe_symbol": "",
                "pe_token": ""
            }

    strike_text = str(atm_strike)

    print("SYMBOL =", symbol)

    for row in result["data"]:

        ts = row["tradingsymbol"]
        if symbol == "BANKNIFTY":
            print(ts)

        if ts.startswith("NIFTYNXT"):
            continue

        if "NIFTY" not in ts:
            continue

        
        if strike_text not in ts:
            continue

        if ts.endswith("CE"):

            ce_symbol = ts
            ce_token = row["symboltoken"]

        elif ts.endswith("PE"):

            pe_symbol = ts
            pe_token = row["symboltoken"]

        if ce_symbol and pe_symbol:
            break

    print("CE =", ce_symbol, ce_token)
    print("PE =", pe_symbol, pe_token)

    return {
        "ce_symbol": ce_symbol,
        "ce_token": ce_token,
        "pe_symbol": pe_symbol,
        "pe_token": pe_token
    }


def fetch_option_chain(
    spot,
    symbol
):
    print("=" * 50)
    print("FETCH OPTION CHAIN")
    print("SYMBOL =", symbol)
    print("SPOT =", spot)
    print("=" * 50)

    if symbol == "NIFTY":
        import math
        atm_strike = (
            math.ceil(spot / 100)
            * 100
        )
    else:
        atm_strike = (
            int(round(spot / 100))
            * 100
        )

    print(
        "SPOT =",
        spot,
        "ATM =",
        atm_strike
    )
 
    smart = initialize_angel()

    contracts = discover_atm_contracts(
    smart,
    symbol,
    atm_strike
)
    ce_ltp = 0
    pe_ltp = 0

    call_oi = 0
    put_oi = 0

    call_volume = 0
    put_volume = 0

    try:

        tokens = []

        if contracts["ce_token"]:
            tokens.append(
                contracts["ce_token"]
            )

        if contracts["pe_token"]:
            tokens.append(
                contracts["pe_token"]
            )

        if tokens:

            quote = smart.getMarketData(
                "FULL",
                {
                    "NFO": tokens
                }
            )


            for row in quote["data"]["fetched"]:

                token = row["symbolToken"]

                if token == contracts["ce_token"]:

                    ce_ltp = row["ltp"]
                    call_oi = row["opnInterest"]
                    call_volume = row["tradeVolume"]

                elif token == contracts["pe_token"]:

                    pe_ltp = row["ltp"]
                    put_oi = row["opnInterest"]
                    put_volume = row["tradeVolume"]

    except Exception as e:

        print("QUOTE ERROR =", e)

    recommended_premium = max(
    ce_ltp,
    pe_ltp
)
    
    confidence = 70
    risk_reward = 2.0

    lots, quantity = calculate_position_size(
        recommended_premium,
        confidence,
        risk_reward,
        symbol
)

    return {
        "atm_strike": atm_strike,
        "atm_ce": contracts["ce_symbol"],
        "atm_pe": contracts["pe_symbol"],
        "ce_ltp": ce_ltp,
        "pe_ltp": pe_ltp,
        "call_oi": call_oi,
        "put_oi": put_oi,
        "call_volume": call_volume,
        "put_volume": put_volume,
        "max_pain": atm_strike,
        "support": atm_strike - 100,
        "resistance": atm_strike + 100,
        "oi_bias":
        "BULLISH"
        if put_oi > call_oi
        else "BEARISH",
        "recommended_lots": lots,
        "recommended_qty": quantity,
    }



def build_live_state(market_data):

    print("BUILD LIVE STATE STARTED")
    pcr_data = (
        fetch_pcr_data()
    )

    states = {}

    for symbol in [
        "NIFTY",
        "BANKNIFTY"
    ]:
        print("PROCESSING =", symbol)
        spot = (
            market_data[symbol]["spot"]
        )
        print("PROCESSING =", symbol)
        print("SPOT =", spot)

        change = (
            market_data[symbol]["change"]
        )

        oi = (
            market_data[symbol]["oi"]
        )

        pcr = (
            pcr_data[symbol]
        )
        print("PCR =", pcr)

        (
            action,
            score,
            probability
        ) = calculate_signal(
            change,
            pcr
        )
        oi_structure = classify_oi_buildup(
            change,
            oi
        )

        trend = calculate_trend(
            change,
            pcr,
            oi_structure
        )
        



        if action == "BUY CALL":

            direction = 1

        elif action == "BUY PUT":

            direction = -1

        else:

            direction = 0

        if symbol == "NIFTY":

            strike = (
                int(
                    round(
                        spot / 50
                    )
                ) * 50
            )

            asset_name = (
                "NIFTY 50 INDEX"
            )

            lot_size = 50

            premium_factor = (
                0.006
            )

        else:

            strike = (
                int(
                    round(
                        spot / 100
                    )
                ) * 100
            )

            asset_name = (
                "BANK NIFTY INDEX"
            )

            lot_size = 15

            premium_factor = (
                0.008
            )

        opt_price = (
            spot *
            premium_factor
        )

        option_type = (
            "CE"
            if direction > 0
            else (
                "PE"
                if direction < 0
                else "NT"
            )
        )

        (
            delta,
            gamma,
            theta,
            vega
        ) = fetch_greeks(
            spot,
            strike,
            option_type
        )

        try:
            print("PROCESSING =", symbol)
            option_chain = fetch_option_chain(
                spot,
                symbol
            )

            market_regime = classify_market_regime(
            change,
            pcr,
            option_chain["oi_bias"]
        )

            print("OPTION CHAIN OK =", symbol)
            if symbol == "NIFTY":
              print("NIFTY OPTION CHAIN =", option_chain)

        except Exception as e:

            print(
                "OPTION CHAIN ERROR:",
                symbol,
                e
            )

            continue

        confidence, reasons = (
            generate_trade_decision(
                {
                    "trend": trend,
                    "pcr": pcr,
                    "oi_structure": oi_structure,
                    "delta": delta,
                    "call_volume": option_chain["call_volume"],
                    "put_volume": option_chain["put_volume"]
                }
            
            )
        )
        print("DECISION OK =", symbol)
        capital_required = round(
            option_chain["recommended_qty"]
            * opt_price,
            2
        )

        max_loss = round(
            (
                opt_price
                - (opt_price * 0.90)
            )
            * option_chain["recommended_qty"],
            2
        )
        risk_percent = round(
             (max_loss / 100000) * 100,
            2
            )
        expected_profit = round(
    (
        (opt_price * 1.20)
        - opt_price
    )
    * option_chain["recommended_qty"],
    2
)   

        states[
            asset_name
        ] = {

            "trade_confidence":
                confidence,
           
            "recommended_lots":
                option_chain["recommended_lots"],

            "recommended_qty":
                option_chain["recommended_qty"],

            "capital_required":
                    capital_required,

            "max_loss":
                    max_loss,
            "risk_percent":
                risk_percent,
            
            "expected_profit":
                    expected_profit,

            "trade_reasons":
                reasons,

            "spot":
                spot,

            "change_7d":
                change,

            "dir_factor":
                direction,

            "currency":
                "₹",

            "action":
                action,

            "probability":
                probability,

            "signal_score":
                score,

            "pcr":
                pcr,

           "oi":
                 oi,

            "oi_structure":
                  oi_structure,
            "trend":
                trend,
            
            "market_regime":
                market_regime,

            "delta":
                delta,

            "gamma":
                gamma,

            "theta":
                theta,

            "vega":
                vega,

            "atm_strike":
                 option_chain["atm_strike"],

            "atm_ce":
                option_chain["atm_ce"],

            "atm_pe":
                option_chain["atm_pe"],

            "ce_ltp":
                option_chain["ce_ltp"],

            "pe_ltp":
                option_chain["pe_ltp"],

            "call_oi":
                option_chain["call_oi"],

            "put_oi":
                    option_chain["put_oi"],

            "call_volume":
                option_chain["call_volume"],

            "put_volume":
                option_chain["put_volume"],
            
            "max_pain":
                option_chain["max_pain"],

            "support":
                option_chain["support"],

            "resistance":
                option_chain["resistance"],

            "oi_bias":
                option_chain["oi_bias"],

            "entry_price":
                    opt_price,

            "stop_loss":
                    round(
                        opt_price * 0.90,
                                    2
                        ),

            "target":
                    round(
                        opt_price * 1.20,
                                    2
                        ),

            "risk_reward":
                    round(
                        (
                            (opt_price * 1.20) - opt_price
                        )
                        /
                        (
                            opt_price - (opt_price * 0.90)
                        ),
                        2
                ),

            "opt_price":
                opt_price,

            "opt_symbol":
                f"{symbol} "
                f"{strike} "
                f"{option_type}",

            "mock_entry":
                opt_price * 0.95,

            "mock_size":
                lot_size,
           
        }
    print("FINAL STATES =", list(states.keys()))
    return states

# =====================================================
# APP START
# =====================================================

st.title(
    "🇮🇳 ALGORITHMIC OPTIONS RISK DESK V2"
)

st.caption(
    f"System Time: "
    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "
    f"| SmartAPI Connected "
    f"| Refresh: 5 Seconds"
)
is_open, market_status = get_market_status()

st.info(
    f"📈 {market_status}"
)
if not is_open:

    st.warning(
        f"🚫 {market_status}"
    )

    #st.stop()

market_data = (
    fetch_live_market_data()
)

if market_data is None:

    st.stop()

global_fund_states = (
    build_live_state(
        market_data
    )
)
is_open, market_status = get_market_status()

st.info(
    f"📈 {market_status}"
)
# =====================================================
# TOP CARDS
# =====================================================

col1, col2 = st.columns(2)

with col1:


    if "NIFTY 50 INDEX" in global_fund_states:

        st.html(
        render_asset_card(
            "NIFTY 50 INDEX",
            global_fund_states[
                "NIFTY 50 INDEX"
            ]
        )
    )

    else:

        st.error("NIFTY STATE MISSING")
    

with col2:

    st.html(
         render_asset_card(
            "BANK NIFTY INDEX",
            global_fund_states[
                "BANK NIFTY INDEX"
            ]
        )
    )


# =====================================================
# STRENGTH METER
# =====================================================

st.subheader(
    "📊 Signal Strength Matrix"
)

st.html(
    render_strength_meter(
        "PCR + OI + PRICE MODEL",
        global_fund_states
    )
)

# =====================================================
# SIGNAL TABLE
# =====================================================

st.subheader(
    "⚡ Signal Matrix"
)

(
    signal_rows,
    highest_prob_asset,
    highest_prob_val
) = render_signals_table(
    global_fund_states
)

st.html(
    f"""
    <table class="custom-table">

        <thead>

            <tr>

                <th>OPTION</th>
                <th>SIGNAL</th>
                <th>PCR</th>
                <th>OI</th>
                <th>OI BUILDUP</th>
                <th>TREND</th>
                <th>SCORE</th>
                <th>DELTA</th>
                <th>GAMMA</th>
                <th>THETA</th>
                <th>VEGA</th>
                <th>PROBABILITY</th>

            </tr>

        </thead>

        <tbody>

            {signal_rows}

        </tbody>

    </table>
    """,
)

# =====================================================
# POSITION TABLE
# =====================================================

st.subheader(
    "💼 Position Book"
)

(
    rows_html,
    total_unrealized_pnl,
    pnl_color
) = render_position_table(
    global_fund_states
)

st.html(
    f"""
            <table class="custom-table">

        <thead>

            <tr>

                <th>ASSET</th>
                <th>DIRECTION</th>
                <th>SIZE</th>
                <th>ENTRY</th>
                <th>SPOT</th>
                <th>PNL</th>

            </tr>

        </thead>

        <tbody>

            {rows_html}

            <tr>

                <td colspan="5"
                    style="
                    text-align:right;
                    color:#8c9bae;
                    "
                >
                    TOTAL PNL
                </td>

                <td
                    style="
                    color:{pnl_color};
                    font-weight:bold;
                    "
                >
                    ₹{total_unrealized_pnl:,.2f}
                </td>

            </tr>

        </tbody>

    </table>
    """,
)

best_asset = max(
    global_fund_states.items(),
    key=lambda x: x[1]["trade_confidence"]
)

best_asset_name = best_asset[0]

best_asset_data = best_asset[1]

if best_asset_data["trade_confidence"] < 40:

    best_asset_name = best_asset[0]

    best_asset_data["action"] = "NO TRADE"  

    best_asset_data["trade_confidence"] = 0

    best_asset_data["trade_reasons"] = [
        "No setup meets minimum confidence threshold"
    ]

# =====================================================
# TRADE OF THE MOMENT
# =====================================================

st.subheader(
    "🎯 Trade Recommendation Engine"
)
if (
    best_asset_data["trade_confidence"] > 40
    and best_asset_data["action"] != "NO TRADE"
):

    log_trade(
        best_asset_data,
        best_asset_name
    )
st.html(
    render_trade_card(
        best_asset_name,
        best_asset_data
    ),
)



# =====================================================
# OPTION CHAIN INTELLIGENCE
# =====================================================

st.subheader(
    "🎯 Option Chain Intelligence"
)

st.html(
    render_option_chain_panel(
        global_fund_states
    ),
)

# =====================================================
# PRIMARY SIGNAL
# =====================================================

if highest_prob_asset:

    asset_name = (
        highest_prob_asset[0]
    )

    asset_data = (
        highest_prob_asset[1]
    )

    st.markdown("---")

    st.html(
        f"""
        <div class="macro-alert-box">

            <b>
                🎯 PRIMARY SIGNAL
            </b>

            <br><br>

            Asset:
            <b>{asset_name}</b>

            <br>

            Signal:
            <b>{asset_data['action']}</b>

            <br>

            PCR:
            <b>{asset_data['pcr']:.2f}</b>
            <br>

            Trend:
                <b>{asset_data['trend']}</b>

        OI Buildup:
                <b>{asset_data['oi_structure']}</b>

            <br>

            OI:
            <b>{asset_data['oi']:,}</b>

            <br>

            Score:
            <b>{asset_data['signal_score']}</b>

            <br>

            Probability:
            <b>{asset_data['probability']:.1f}%</b>

        </div>
        """,
    )
    st.markdown("---")

st.subheader(
    "📒 Trade Journal"
)

journal_df = pd.read_csv(
    JOURNAL_FILE
)

st.dataframe(
    journal_df.tail(10),
    use_container_width=True
)

    