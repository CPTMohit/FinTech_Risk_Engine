"""
Project: FinTech Risk Isolation Engine V2
Module: SmartAPI Live Dashboard
Author: Mohit Singh
"""

import os
import sys
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

@st.cache_data(ttl=5)
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

@st.cache_data(ttl=60)
def fetch_pcr_data():

    return {

        "NIFTY": 0.94,

        "BANKNIFTY": 0.99
    }

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

def classify_oi_buildup(change_pct, oi):

    if change_pct > 0.30 and oi > 100000000:
        return "LONG BUILDUP"

    elif change_pct < -0.30 and oi > 100000000:
        return "SHORT BUILDUP"

    elif change_pct > 0 and oi < 100000000:
        return "SHORT COVERING"

    else:
        return "LONG UNWINDING" 

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

        states[
            asset_name
        ] = {

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
                <th>SCORE</th>
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

    