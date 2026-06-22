"""
Project: FinTech Risk Isolation Engine
Module: Production Streamlit UI Dashboard Entry Point
Author: Mohit Singh
Description: Synthesizes live market feeds, live text sentiment analysis, and 
             XGBoost regression inferences into an institutional options telemetry layout.
"""

import os
import sys
import streamlit as st
import numpy as np
import pandas as pd
import time

# ==============================================================================
# CRITICAL FIX: Explicitly inject project root into sys.path to eliminate relative import errors
# ==============================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Absolute structural imports from the project core
from src.models import load_production_models, load_production_xgb_model
from src.data_processor import compile_live_market_state
# FIXED: Changed from src.ui_rendering to src.ui to match your actual file tree
from src.ui import (
    render_strength_meter, 
    render_asset_card, 
    render_position_table, 
    render_signals_table,
    THEME_CONFIG
)

# 1. Page Configuration and Theme Structuring
st.set_page_config(
    page_title="🇮🇳 Live Indian Market Options Risk Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom layout overrides to handle the premium dark terminal aesthetic
st.markdown(f"""
    <style>
        .stApp {{
            background-color: #0d1117;
            color: #c9d1d9;
        }}
        .global-ticker-card {{
            background-color: #161b22;
            border: 1px solid {THEME_CONFIG['border']};
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }}
        .strength-bar-container {{
            background-color: #21262d;
            border-radius: 4px;
            overflow: hidden;
            display: flex;
            height: 10px;
            margin-top: 6px;
        }}
        .custom-table {{
            width: 100%;
            border-collapse: collapse;
            font-family: monospace;
            font-size: 0.85rem;
            background-color: #161b22;
            color: #e6edf3;
            border: 1px solid {THEME_CONFIG['border']};
        }}
        .custom-table th {{
            background-color: #21262d;
            color: #8c9bae;
            text-align: left;
            padding: 10px;
            border-bottom: 2px solid {THEME_CONFIG['border']};
        }}
        .custom-table td {{
            padding: 10px;
            border-bottom: 1px solid {THEME_CONFIG['border']};
        }}
        .macro-alert-box {{
            background-color: #1f1b11;
            border-left: 4px solid #e3b341;
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 16px;
            font-size: 0.85rem;
        }}
    </style>
""", unsafe_allow_html=True)

# 2. Institutional Model Resource Allocation Core
st.title("🇮🇳 NIFTY & BANK NIFTY LIVE OPTIONS RISK DESK")
st.caption("Quant Architecture Model Node Active | Target Horizon: Intraday Expirations")

with st.spinner("[*] Bootstrapping Deep Learning Context and Model Resource Matrices..."):
    tokenizer, nlp_model, device = load_production_models()
    xgb_model = load_production_xgb_model()

# 3. Sidebar Simulated Live Market Control Deck
st.sidebar.header("🕹️ Live Market Injection Deck")
st.sidebar.markdown("Use these parameters to simulate real-time Indian stock market feeds:")

sim_nifty = st.sidebar.slider("Nifty 50 Spot Level", 21000.0, 25000.0, 23550.0, step=5.0)
sim_banknifty = st.sidebar.slider("Bank Nifty Spot Level", 48000.0, 54000.0, 51200.0, step=10.0)

st.sidebar.markdown("---")
st.sidebar.subheader("📰 Live Financial Streaming Feed")
headline_input = st.sidebar.text_area(
    "Enter Incoming Macro/Corporate News:",
    "RBI monetary policy statement suggests positive liquidity framework shifts while commercial banks indicate strong asset-quality performance."
)

# 4. Generate Mock Lookback Historical Arrays to feed Delta and Technical Pipelines
np.random.seed(42)
hist_nifty_base = list(np.linspace(sim_nifty - 150, sim_nifty - 10, 20))
hist_bank_base = list(np.linspace(sim_banknifty - 400, sim_banknifty - 20, 20))

# Bundle operational tracking telemetry dictionaries
live_quotes_feed = {"^NSEI": sim_nifty, "^NSEBANK": sim_banknifty}
historical_lookup_cache = {"^NSEI": hist_nifty_base, "^NSEBANK": hist_bank_base}
live_news_stream = [headline_input]

# 5. Execute Live Machine Learning State Synthesis Compilation
global_fund_states = compile_live_market_state(
    live_quotes=live_quotes_feed,
    historic_base_data=historical_lookup_cache,
    live_news_stream=live_news_stream,
    tokenizer=tokenizer,
    nlp_model=nlp_model,
    device=device
)

# 6. Render Dashboard Presentation Layer Components
col1, col2 = st.columns(2)
with col1:
    nifty_html = render_asset_card("NIFTY 50 INDEX", global_fund_states["NIFTY 50 INDEX"])
    st.markdown(nifty_html, unsafe_allow_html=True)
with col2:
    bank_html = render_asset_card("BANK NIFTY INDEX", global_fund_states["BANK NIFTY INDEX"])
    st.markdown(bank_html, unsafe_allow_html=True)

# Mid Row: Market Momentum Delta Power Meters
st.subheader("📊 Market Delta Power Breakdown")
strength_html = render_strength_meter("DERIVATIVES MARKET ENSEMBLE", global_fund_states)
st.markdown(strength_html, unsafe_allow_html=True)

# Split Bottom Layout: High-Frequency Derivative Signals & Active Trading Book
col_sig, col_pos = st.columns([1.1, 0.9])

with col_sig:
    st.subheader("⚡ Live High-Frequency Options Sweep Signals")
    signal_rows, highest_prob_asset, highest_prob_val = render_signals_table(global_fund_states)
    
    signals_table_html = f"""
    <table class='custom-table'>
        <thead>
            <tr>
                <th>OPTION SYMBOL</th>
                <th>TRADE SYSTEM SETUP</th>
                <th>ENTRY (LIMIT)</th>
                <th>STOP LOSS</th>
                <th>TARGET INFERENCE</th>
                <th>ML WIN PROB</th>
                <th>RISK REWARD</th>
            </tr>
        </thead>
        <tbody>
            {signal_rows}
        </tbody>
    </table>
    """
    st.markdown(signals_table_html, unsafe_allow_html=True)

with col_pos:
    st.subheader("💼 Active Mock Derivatives Portfolio Book")
    rows_html, total_unrealized_pnl, pnl_summary_color = render_position_table(global_fund_states)
    
    positions_table_html = f"""
    <table class='custom-table'>
        <thead>
            <tr>
                <th>ASSET OVERVIEW</th>
                <th>DIRECTION</th>
                <th>CONTRACT SIZE</th>
                <th>ENTRY PRICE</th>
                <th>CURRENT SPOT</th>
                <th>UNREALIZED PNL</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
            <tr style='background-color: #21262d; font-weight: bold;'>
                <td colspan='5' style='text-align: right; color:#8c9bae;'>AGGREGATE PORTFOLIO PNL RUNTIME VALUE:</td>
                <td style='color:{pnl_summary_color}; font-size:1rem;'>₹{total_unrealized_pnl:,.2f}</td>
            </tr>
        </tbody>
    </table>
    """
    st.markdown(positions_table_html, unsafe_allow_html=True)

# Bottom Row Focus: Top Structural Setup Highlight Node
if highest_prob_asset:
    asset_name, asset_fs, trade_type, opt_entry, opt_target, opt_sl, rr, alert_text, coordinate = highest_prob_asset
    st.markdown("---")
    st.markdown(f"""
    <div class='macro-alert-box'>
        <b style='color:#e3b341; font-size:1rem;'>🎯 HIGHEST CONFIDENCE ALPHA OPPORTUNITY DETECTED</b><br>
        <span style='color:#fff;'><b>Asset:</b> {asset_name} | <b>Recommended Action:</b> {trade_type} | <b>Target Entry Strike Coordination:</b> ₹{coordinate:,.2f}</span><br>
        <span style='color:#8c9bae; font-size:0.8rem;'>{alert_text}</span>
    </div>
    """, unsafe_allow_html=True)