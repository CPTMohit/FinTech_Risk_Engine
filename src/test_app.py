"""
Project: FinTech Risk Isolation Engine V2
Module: SmartAPI Live Dashboard
Author: Mohit Singh
"""

import os
import sys
import SmartApi
import streamlit as st
from datetime import datetime

from SmartApi import SmartConnect
import pyotp

# =====================================================
# ANGEL ONE CONFIG
# =====================================================
API_KEY = "3xK955MH"
CLIENT_CODE = "AACI729341"
PIN = "0912"
TOTP_SECRET = "ZG4AT5YV6GPJQNPPVHLESN5JZI"

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
    if symbol != "NIFTY":

     return {
        "ce_symbol": "",
        "ce_token": "",
        "pe_symbol": "",
        "pe_token": ""
    }

    search_term = (
        f"NIFTY24DEC29{atm_strike}"
    )

    print(
    "SEARCH TERM =",
    search_term
)

    result = smart.searchScrip(
        "NFO",
        search_term
    )

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

    for row in result["data"]:

            ts = row["tradingsymbol"]

            if ts.endswith("CE"):

                ce_symbol = ts
                ce_token = row["symboltoken"]

            elif ts.endswith("PE"):

                pe_symbol = ts
                pe_token = row["symboltoken"]

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

    print(contracts)

    ce_ltp = 0
    pe_ltp = 0

    try:

        if contracts["ce_symbol"]:

            ce_data = smart.ltpData(
            "NFO",
            contracts["ce_symbol"],
            contracts["ce_token"]
        )

            ce_ltp = ce_data["data"]["ltp"]

    except Exception:
        ce_ltp = 0

    try:

        if contracts["pe_symbol"]:

            pe_data = smart.ltpData(
            "NFO",
            contracts["pe_symbol"],
            contracts["pe_token"]
        )

            pe_ltp = pe_data["data"]["ltp"]

    except Exception:
        pe_ltp = 0


    print(contracts)
    return {
    "atm_strike": atm_strike,
    "atm_ce": contracts["ce_symbol"],
    "atm_pe": contracts["pe_symbol"],
    "ce_ltp": ce_ltp,
    "pe_ltp": pe_ltp,
    "call_oi": 2500000,
    "put_oi": 3200000,
    "call_volume": 450000,
    "put_volume": 510000,
    "max_pain": atm_strike
}

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

    if state["pcr"] > 0.9:

        score += 20

        reasons.append(
            "PCR Supportive"
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

    if state["call_volume"] < state["put_volume"]:

        score += 10

        reasons.append(
            "Put Side Dominance"
        )

    confidence = min(
        score,
        95
    )

    return (
        confidence,
        reasons
    )

def build_live_state(
    market_data
):

    pcr_data = (
        fetch_pcr_data()
    )

    states = {}

    for symbol in [
        "NIFTY",
        "BANKNIFTY"
    ]:

        spot = (
            market_data[symbol]["spot"]
        )

        change = (
            market_data[symbol]["change"]
        )

        oi = (
            market_data[symbol]["oi"]
        )

        pcr = (
            pcr_data[symbol]
        )

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

        option_chain = fetch_option_chain(
                spot,
                symbol
        )

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

        states[
                asset_name
            ] = {

            "trade_confidence":
                confidence,

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

            "opt_price":
                opt_price,

            "opt_symbol":
                f"{symbol} "
                f"{strike} "
                f"{option_type}",

            "mock_entry":
                opt_price * 0.95,

            "mock_size":
                lot_size
                
        }

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

# =====================================================
# TOP CARDS
# =====================================================

col1, col2 = st.columns(2)

with col1:

   st.html(
    render_asset_card(
        "NIFTY 50 INDEX",
        global_fund_states[
           "NIFTY 50 INDEX"
    ] 
    )
)

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

# =====================================================
# TRADE OF THE MOMENT
# =====================================================

st.subheader(
    "🎯 Trade Recommendation Engine"
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

    