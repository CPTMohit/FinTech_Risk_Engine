"""
Project: AlphaQuant Global Cross-Asset Derivatives & Equity Center
Module: Enterprise Master Desktop Terminal & Real-Time Socket Intercept Engine
Author: Mohit Singh
System Version: V11.0 Enterprise Real-Time Sync (True Live Stream & Cheap OTM Matrix)

CLEANED UP - Modular architecture with external modules
"""

import streamlit as st

# Import modular components
from gateway import AngelOneDataGateway
from models import get_models
from utils import compute_finbert_sentiment
from data_processor import get_asset_universe, process_asset_data
from ui import (
    get_theme_config, 
    render_strength_meter, 
    render_asset_card, 
    render_position_table,
    render_signals_table
)


# ========================================================
# PAGE CONFIGURATION
# ========================================================
st.set_page_config(
    page_title="QuantGlobal Terminal",
    layout="wide",
    initial_sidebar_state="expanded"
)


def load_css():
    """Load custom CSS styling"""
    css = """
    <style>
    .terminal-header {
        background-color: #0F1524;
        border-left: 4px solid #00FFCC;
        padding: 12px;
        margin: 16px 0;
        font-weight: bold;
        color: #00FFCC;
        font-family: monospace;
    }
    .global-ticker-card {
        background-color: #1a2332;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        border-left: 3px solid #00FFCC;
    }
    .ticker-buy {
        border-left-color: #00FFCC;
    }
    .ticker-sell {
        border-left-color: #FF3366;
    }
    .ticker-neutral {
        border-left-color: #8C9BAE;
    }
    .strength-bar-container {
        display: flex;
        height: 24px;
        background-color: #0F1524;
        border-radius: 4px;
        overflow: hidden;
        margin-top: 8px;
    }
    .terminal-table {
        width: 100%;
        border-collapse: collapse;
        font-family: monospace;
        font-size: 0.75rem;
        margin: 12px 0;
    }
    .terminal-table thead {
        background-color: #0F1524;
        border-bottom: 2px solid #00FFCC;
    }
    .terminal-table th {
        padding: 8px;
        color: #00FFCC;
        font-weight: bold;
        text-align: left;
    }
    .terminal-table td {
        padding: 8px;
        border-bottom: 1px solid #2D3748;
        color: #FFF;
    }
    .alert-banner {
        background-color: #0F1524;
        padding: 12px;
        border-radius: 4px;
        margin: 12px 0;
    }
    .pre-breakout-flash {
        background-color: #1a2332;
        border-left: 4px solid #FF6B6B;
        padding: 8px;
        margin: 4px 0;
        font-family: monospace;
        font-size: 0.8rem;
    }
    .news-headline {
        background-color: #1a2332;
        padding: 8px;
        margin: 4px 0;
        border-radius: 4px;
        font-size: 0.75rem;
    }
    </style>
    """
    st.html(css)


load_css()


# ========================================================
# Initialize session state
# ========================================================
if "live_ticks" not in st.session_state:
    st.session_state.live_ticks = {
        "NIFTY 50 INDEX OPTIONS": 22100.0,
        "BANK NIFTY INDEX OPTIONS": 46800.0,
        "RELIANCE INDUSTRIES": 2850.0,
        "BITCOIN DERIVATIVES": 62500.0
    }

if "api_gateway" not in st.session_state:
    st.session_state.api_gateway = None


# ========================================================
# GATEWAY SETUP
# ========================================================
def setup_gateway_sidebar():
    """Setup Angel One SmartAPI gateway in sidebar"""
    st.sidebar.markdown("### 🔌 ANGEL ONE SMARTAPI INTERCONNECT")
    
    angel_client_code = st.sidebar.text_input(
        "Client ID / User Code", 
        placeholder="e.g., S123456", 
        type="default"
    )
    angel_password = st.sidebar.text_input("Password / MPIN", type="password")
    angel_totp_secret = st.sidebar.text_input(
        "TOTP Alphanumeric Secret",
        help="Get this from Angel One SmartAPI portal when enabling TOTP",
        type="password"
    )
    angel_api_key = st.sidebar.text_input("SmartAPI Application Key", type="password")

    if st.sidebar.button("Initialize Production Feed"):
        if not angel_client_code or not angel_password or not angel_api_key:
            st.sidebar.error("Client ID, Password, and API Key are mandatory.")
        else:
            st.session_state.api_gateway = AngelOneDataGateway(api_key=angel_api_key)
            
            success, msg = st.session_state.api_gateway.authenticate(
                client_code=angel_client_code,
                password=angel_password,
                totp_secret=angel_totp_secret
            )
            
            if success:
                st.sidebar.success("Connected! SmartAPI Session established.")
            else:
                st.sidebar.error(msg)


# ========================================================
# MAIN APPLICATION
# ========================================================
def main():
    """Main application entry point"""
    
    setup_gateway_sidebar()
    tokenizer, nlp_model, device = get_models()
    
    # Page header
    st.markdown(
        "<h2 style='letter-spacing: -1px; font-weight:900; margin-bottom: 0px;'>📊 QUANTGLOBAL WORKSPACE TERMINAL</h2>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='font-family: monospace; color:#8C9BAE; font-size:0.8rem; margin-top:0px;'>V11.0 Enterprise Real-Time Sync: Sub-Second Live WebSocket Streaming Protocol</p>",
        unsafe_allow_html=True
    )
    
    # Search and horizon selector
    col_search, col_tf = st.columns([2, 1])
    with col_search:
        search_query = st.text_input(
            "COMMAND LINE INTERFACE",
            placeholder="Search Ticker/Asset (e.g., NIFTY, BTC)...",
            label_visibility="collapsed"
        )
    with col_tf:
        selected_horizon = st.selectbox(
            "HORIZON DESK",
            ["M5 (Intraday Momentum)", "H1 (Swing Struct)", "D1 (Macro Institutional)"],
            label_visibility="collapsed"
        )
    
    execute_workspace_telemetry(search_query, selected_horizon, tokenizer, nlp_model, device)


@st.fragment(run_every=1)
def execute_workspace_telemetry(search_query, selected_horizon, tokenizer, nlp_model, device):
    """Execute the real-time workspace telemetry and rendering"""
    
    t_cfg = get_theme_config()
    asset_universe = get_asset_universe()
    
    # Headlines for sentiment analysis
    india_headlines = [
        "NSE structural tracking shows domestic mutual funds absorbing institutional selling blocks.",
        "Retail derivative positioning hits overleveraged conditions near resistance bands.",
        "FII block orders signal cautious rollover pacing into upcoming options expiry sessions."
    ]
    crypto_headlines = [
        "Retail funding rates hit extreme premiums causing squeeze vulnerability cascades.",
        "Whale wallet aggregation patterns highlight long absorption layers at critical discount floors.",
        "Deribit option surface skew indicates heavy call buying, introducing retail trap configurations."
    ]
    
    # Compute sentiment
    ind_sentiment, ind_news = compute_finbert_sentiment(india_headlines, tokenizer, nlp_model, device)
    cry_sentiment, cry_news = compute_finbert_sentiment(crypto_headlines, tokenizer, nlp_model, device)
    
    # Process all assets
    global_fund_states = {}
    for f_label, f_meta in asset_universe.items():
        current_spot = st.session_state.live_ticks.get(f_label, f_meta["mock_entry"])
        asset_state = process_asset_data(f_label, f_meta, current_spot, ind_sentiment, cry_sentiment)
        if asset_state:
            global_fund_states[f_label] = asset_state
    
    # Display live alerts
    pre_breakout_alerts = []
    for f_label, fs in global_fund_states.items():
        spot_p = fs["spot"]
        if fs["dir_factor"] == 1:
            entry_target = fs["floor"] + ((spot_p - fs["floor"]) * 0.2)
            distance = (spot_p - entry_target) / spot_p
            if 0 < distance <= 0.0050:
                pre_breakout_alerts.append(
                    f"⏱️ <b>[LIVE WEBSOCKET TRIGGER]</b> {f_label} sweeping support liquidity block! "
                    f"OTM CALL <b>{fs['opt_symbol']}</b> is hyper-active. Premium: {fs['currency']}{fs['opt_price'] * 0.95:,.2f}."
                )
        elif fs["dir_factor"] == -1:
            entry_target = fs["ceiling"] - ((fs["ceiling"] - spot_p) * 0.2)
            distance = (entry_target - spot_p) / spot_p
            if 0 < distance <= 0.0050:
                pre_breakout_alerts.append(
                    f"⏱️ <b>[LIVE WEBSOCKET TRIGGER]</b> {f_label} hitting macro institutional offer wall limits! "
                    f"OTM PUT <b>{fs['opt_symbol']}</b> premium pricing: {fs['currency']}{fs['opt_price'] * 0.95:,.2f}."
                )
    
    if pre_breakout_alerts:
        st.html("<div class='terminal-header'>🚨 LIVE HIGH-FREQUENCY DATA WIRE (0.5s TICK SAMPLING)</div>")
        for alert in pre_breakout_alerts:
            st.html(f"<div class='pre-breakout-flash'>{alert}</div>")
    
    # Global strength meters
    st.html(f"<div class='terminal-header'>🌐 GLOBAL LIVE MARKET SURVEILLANCE ({selected_horizon})</div>")
    ind_assets = {k: v for k, v in global_fund_states.items() if v["market"] == "India"}
    cry_assets = {k: v for k, v in global_fund_states.items() if v["market"] == "Crypto"}
    
    col_mb1, col_mb2 = st.columns(2)
    with col_mb1:
        st.html(render_strength_meter("NSE ORDERFLOW", ind_assets, t_cfg))
    with col_mb2:
        st.html(render_strength_meter("CRYPTO BOOK DELTA", cry_assets, t_cfg))
    
    # Tabs for India and Crypto
    tab_ind, tab_cry = st.tabs(["🇮🇳 INDIAN SESSIONS (NSE CORE)", "🪙 CONTINUOUS DIGITAL STREAM (CRYPTO)"])
    
    with tab_ind:
        c1, c2 = st.columns([2, 1])
        with c1:
            sub_cols = st.columns(2)
            for idx, (f_label, fs) in enumerate(ind_assets.items()):
                with sub_cols[idx % 2]:
                    st.html(render_asset_card(f_label, fs, t_cfg, show_7d=False))
        with c2:
            st.markdown(f"**Calculated FinBERT Sentiment Vector:** `{ind_sentiment:+.4f}`")
            for item in ind_news:
                c = t_cfg['accent'] if "BULL" in item['label'] else ("#FF3366" if "BEAR" in item['label'] else "#8C9BAE")
                st.html(f"<div class='news-headline'><span style='color:{c}; font-weight:bold;'>[{item['label']}]</span> {item['text']}</div>")
    
    with tab_cry:
        c1, c2 = st.columns([2, 1])
        with c1:
            sub_cols = st.columns(2)
            for idx, (f_label, fs) in enumerate(cry_assets.items()):
                with sub_cols[idx % 2]:
                    st.html(render_asset_card(f_label, fs, t_cfg, show_7d=False))
        with c2:
            st.markdown(f"**Calculated FinBERT Sentiment Vector:** `{cry_sentiment:+.4f}`")
            for item in cry_news:
                c = t_cfg['accent'] if "BULL" in item['label'] else ("#FF3366" if "BEAR" in item['label'] else "#8C9BAE")
                st.html(f"<div class='news-headline'><span style='color:{c}; font-weight:bold;'>[{item['label']}]</span> {item['text']}</div>")
    
    # Active positions
    st.markdown("<br>", unsafe_allow_html=True)
    st.html("<div class='terminal-header'>💼 ACTIVE DEPLOYED BOOK: REAL-TIME POSITION TRACKER</div>")
    
    rows_html, total_unrealized_pnl, pnl_summary_color = render_position_table(global_fund_states, t_cfg)
    
    st.html(f"""
        <table class='terminal-table'>
            <thead>
                <tr>
                    <th>ASSET SPECIFICATION</th>
                    <th>VECTOR</th>
                    <th>VOLUME SIZE</th>
                    <th>AVG ENTRY PRICE</th>
                    <th>LIVE TICK SPOT</th>
                    <th>FLOATING P&L</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
                <tr style='background-color:#0F1524; font-weight:bold;'>
                    <td colspan='5' style='text-align:right; color:#8C9BAE;'>AGGREGATED FLOATING PN&L:</td>
                    <td style='color:{pnl_summary_color};'>{total_unrealized_pnl:,.2f}</td>
                </tr>
            </tbody>
        </table>
    """)
    
    # High-frequency signals
    st.markdown("<br>", unsafe_allow_html=True)
    st.html("<div class='terminal-header'>🎯 HIGH-FREQUENCY CONFLUENCE SIGNALS (LIVE CHEAP OTM vs EXTREME EXITS)</div>")
    
    signal_rows, highest_prob_asset, highest_prob_val = render_signals_table(global_fund_states, t_cfg)
    
    st.html(f"""
        <table class='terminal-table'>
            <thead>
                <tr>
                    <th>HIGH-GAMMA LIVE CONTRACT</th>
                    <th>PREDICTIVE VECTOR</th>
                    <th>LIVE OTM ENTRY</th>
                    <th>HARD STOP LOSS</th>
                    <th>EXTREME TARGET</th>
                    <th>CONFLUENCE RATIO</th>
                    <th>PROFIT FACTOR</th>
                </tr>
            </thead>
            <tbody>
                {signal_rows}
            </tbody>
        </table>
    """)
    
    # Best trade
    if highest_prob_asset:
        name, h_fs, h_type, h_opt_entry, h_opt_target, h_opt_sl, h_rr, h_alert, h_und_entry = highest_prob_asset
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"### 💎 LIVE STREAM SELECTION ACCELERATOR")
        
        col_box, col_stats = st.columns([2, 1])
        with col_box:
            st.html(f"""
                <div class='alert-banner' style='border: 2px solid {t_cfg['accent']};'>
                    <b style='font-size:0.95rem; color:{t_cfg['accent']};'>🎯 PRIMARY SYSTEM SWEEP: {h_fs['opt_symbol']} ({name})</b><br><br>
                    <b>TARGET TYPE:</b> <span style='color:#FFF; background-color:#1F293D; padding:2px 6px; border-radius:4px;'>Strike {h_fs['opt_strike']:.0f} {h_fs['opt_type']}</span><br>
                    <b>LIVE UNDERLYING TICK ENTRY:</b> {h_fs['currency']}{h_und_entry:,.2f}<br>
                    <b>REAL-TIME STREAM DIAGNOSTIC:</b> Live floating P&L shifts are auto-calibrating option greeks.<br><br>
                    <span style='color:{t_cfg['accent']}; font-weight:bold;'>REAL-TIME ACTIONABLE ROUTE:</span> {h_alert}
                </div>
            """)
        with col_stats:
            st.html(f"""
                <div style='background-color:#161D2B; padding:12px; border-radius:4px; border:1px solid {t_cfg['border']}; min-height:135px; font-family:monospace; font-size:0.75rem; line-height:1.4;'>
                    <span style='color:#8C9BAE;'>CONFLUENCE PROBABILITY:</span><br>
                    <b style='font-size:1.4rem; color:{t_cfg['accent']}'>{highest_prob_val:.1f}% Active</b><br>
                    • Live Entry Premium: <span style='color:{t_cfg['accent']}; font-weight:bold;'>{h_fs['currency']}{h_opt_entry:,.2f}</span><br>
                    • Extreme Target: <span style='color:#38BDF8; font-weight:bold;'>{h_fs['currency']}{h_opt_target:,.2f}</span><br>
                    • Hard Stop Loss: <span style='color:#FF3366; font-weight:bold;'>{h_fs['currency']}{h_opt_sl:,.2f}</span>
                </div>
            """)


if __name__ == "__main__":
    main()
