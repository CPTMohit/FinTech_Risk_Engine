"""
Project: FinTech Risk Isolation Engine V2
Module: UI Renderer (Streamlit & Component Integration)
Author: Mohit Singh
"""

THEME_CONFIG = {
    "background": "#0e121a",
    "card_bg": "#111622",
    "border": "#1f293d",
    "text_muted": "#8492a6",
    "bullish": "#00f2a9",
    "bearish": "#ff3366",
    "neutral": "#f59e0b",
    "hyperlink": "#00d2ff",
    "accent_blue": "#3b82f6"
}

# =====================================================
# ASSET CARD
# =====================================================

def render_asset_card(asset_title, state):
    action = state.get("action", "NO TRADE")
    if "CALL" in action:
        action_color = THEME_CONFIG["bullish"]
        action_bg = "rgba(0, 242, 169, 0.12)"
        border_glow = "rgba(0, 242, 169, 0.3)"
    elif "PUT" in action:
        action_color = THEME_CONFIG["bearish"]
        action_bg = "rgba(255, 51, 102, 0.12)"
        border_glow = "rgba(255, 51, 102, 0.3)"
    else:
        action_color = THEME_CONFIG["neutral"]
        action_bg = "rgba(245, 158, 11, 0.12)"
        border_glow = "rgba(245, 158, 11, 0.3)"

    change = state.get("change_7d", 0.0)
    change_color = THEME_CONFIG["bullish"] if change >= 0 else THEME_CONFIG["bearish"]
    sign = "+" if change >= 0 else ""
    spot = state.get("spot", 0.0)
    prob = state.get("probability", 0.0)
    trend = state.get("trend", "UNKNOWN")
    regime = state.get("market_regime", "NORMAL")
    pcr = state.get("pcr", 1.0)
    oi = state.get("oi", 0)
    score = state.get("signal_score", 0)

    return f"""
    <div style="
        background: linear-gradient(145deg, #0e121a 0%, #111622 100%);
        border: 1px solid {border_glow};
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
        font-family: 'JetBrains Mono', 'Segoe UI', monospace;
    ">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="color:{THEME_CONFIG['text_muted']}; font-weight:800; font-size:14px; letter-spacing:0.5px;">
                ⚡ {asset_title}
            </span>
            <span style="
                color:{change_color};
                font-weight:bold;
                background:{change_color}18;
                padding:3px 8px;
                border-radius:4px;
                font-size:13px;
            ">
                {sign}{change:.2f}%
            </span>
        </div>

        <div style="font-size:32px; font-weight:800; color:#fff; margin:10px 0 6px 0;">
            ₹{spot:,.2f}
        </div>

        <div style="
            display:inline-block;
            background:{action_bg};
            color:{action_color};
            border:1px solid {action_color}40;
            padding:4px 12px;
            border-radius:20px;
            font-size:12px;
            font-weight:800;
            margin-bottom:14px;
        ">
            ACTION: {action} (Score: {score:+d})
        </div>

        <div style="
            display:grid;
            grid-template-columns: repeat(2, 1fr);
            gap:8px;
            font-size:12px;
            border-top:1px solid #1f293d;
            padding-top:12px;
            color:#94a3b8;
        ">
            <div>Confidence: <b style="color:#fff">{prob:.0f}%</b></div>
            <div>Trend: <b style="color:{change_color}">{trend}</b></div>
            <div>Regime: <b style="color:#38bdf8">{regime}</b></div>
            <div>PCR: <b style="color:#fff">{pcr:.2f}</b></div>
            <div>Total OI: <b style="color:#fff">{oi:,}</b></div>
            <div>Delta / Theta: <b style="color:#fff">{state.get('delta', 0):.2f} / {state.get('theta', 0):.1f}</b></div>
        </div>
    </div>
    """


def render_asset_card_live(asset_title, spot, change, oi):
    change_color = THEME_CONFIG["bullish"] if change >= 0 else THEME_CONFIG["bearish"]
    sign = "+" if change >= 0 else ""

    return f"""
    <div style="
        background:#0e121a;
        border:1px solid {THEME_CONFIG['border']};
        border-radius:10px;
        padding:16px;
        margin-bottom:12px;
        font-family:'JetBrains Mono', monospace;
    ">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="color:{THEME_CONFIG['text_muted']}; font-weight:700;">{asset_title}</span>
            <span style="color:{change_color}; font-weight:700;">{sign}{change:.2f}%</span>
        </div>
        <div style="font-size:28px; font-weight:800; color:#fff; margin:6px 0;">₹{spot:,.2f}</div>
        <div style="font-size:11px; color:{THEME_CONFIG['text_muted']};">OI: <b style="color:#fff">{oi:,}</b></div>
    </div>
    """


# =====================================================
# STRENGTH METER
# =====================================================

def render_strength_meter(title, states):
    nifty_prob = states.get("NIFTY 50 INDEX", {}).get("probability", 50)
    bank_prob = states.get("BANK NIFTY INDEX", {}).get("probability", 50)

    return f"""
    <div style="
        background: #0e121a;
        border: 1px solid {THEME_CONFIG['border']};
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 16px;
        font-family: 'JetBrains Mono', monospace;
    ">
        <div style="display:flex; justify-content:space-between; margin-bottom:10px; font-size:13px; font-weight:700;">
            <span style="color:#fff;">📊 {title}</span>
            <span style="color:{THEME_CONFIG['accent_blue']};">
                NIFTY: <b style="color:{THEME_CONFIG['bullish']}">{nifty_prob:.0f}%</b> | 
                BANK: <b style="color:{THEME_CONFIG['hyperlink']}">{bank_prob:.0f}%</b>
            </span>
        </div>
        <div style="display:flex; height:10px; background:#182030; border-radius:5px; overflow:hidden;">
            <div style="width:{nifty_prob}%; background:{THEME_CONFIG['bullish']}; transition:width 0.5s;"></div>
            <div style="width:{bank_prob}%; background:{THEME_CONFIG['hyperlink']}; transition:width 0.5s;"></div>
        </div>
    </div>
    """


# =====================================================
# SIGNAL TABLE
# =====================================================

def render_signals_table(states):
    rows = []
    highest_prob_val = -1
    highest_prob_asset = None

    for asset_name, state in states.items():
        action = state.get("action", "NO TRADE")
        if "CALL" in action:
            color = THEME_CONFIG["bullish"]
        elif "PUT" in action:
            color = THEME_CONFIG["bearish"]
        else:
            color = THEME_CONFIG["neutral"]

        row = f"""
        <tr style="border-bottom:1px solid #1f293d; font-family:'JetBrains Mono', monospace;">
            <td style="padding:10px; font-weight:bold; color:#fff;">{state.get('opt_symbol', asset_name)}</td>
            <td style="padding:10px; color:{color}; font-weight:bold;">{action}</td>
            <td style="padding:10px; color:#cbd5e1;">{state.get('pcr', 1.0):.2f}</td>
            <td style="padding:10px; color:#cbd5e1;">{state.get('oi', 0):,}</td>
            <td style="padding:10px; color:#38bdf8;">{state.get('oi_structure', 'NORMAL')}</td>
            <td style="padding:10px; color:{color};">{state.get('trend', 'UNKNOWN')}</td>
            <td style="padding:10px; font-weight:bold; color:{color};">{state.get('signal_score', 0):+d}</td>
            <td style="padding:10px; color:#cbd5e1;">{state.get('delta', 0):.2f}</td>
            <td style="padding:10px; color:#cbd5e1;">{state.get('gamma', 0):.4f}</td>
            <td style="padding:10px; color:#cbd5e1;">{state.get('theta', 0):.2f}</td>
            <td style="padding:10px; color:#cbd5e1;">{state.get('vega', 0):.2f}</td>
            <td style="padding:10px; font-weight:bold; color:{THEME_CONFIG['bullish']};">{state.get('probability', 0):.0f}%</td>
        </tr>
        """
        rows.append(row)

        prob = state.get("probability", 0)
        if prob > highest_prob_val:
            highest_prob_val = prob
            highest_prob_asset = (asset_name, state)

    return "".join(rows), highest_prob_asset, highest_prob_val


# =====================================================
# POSITION TABLE
# =====================================================

def render_position_table(states):
    rows = []
    total_pnl = 0.0

    for asset_name, state in states.items():
        entry = state.get("mock_entry", 100.0)
        spot = state.get("spot", 100.0)
        size = state.get("mock_size", 50)
        dir_factor = state.get("dir_factor", 0)

        if dir_factor > 0:
            direction = "LONG"
            pnl = (spot - entry) * size
        elif dir_factor < 0:
            direction = "SHORT"
            pnl = (entry - spot) * size
        else:
            direction = "FLAT"
            pnl = 0.0

        total_pnl += pnl
        pnl_color = THEME_CONFIG["bullish"] if pnl >= 0 else THEME_CONFIG["bearish"]

        rows.append(f"""
        <tr style="border-bottom:1px solid #1f293d; font-family:'JetBrains Mono', monospace;">
            <td style="padding:10px; font-weight:bold; color:#fff;">{asset_name}</td>
            <td style="padding:10px; color:{pnl_color}; font-weight:bold;">{direction}</td>
            <td style="padding:10px; color:#cbd5e1;">{size}</td>
            <td style="padding:10px; color:#cbd5e1;">₹{entry:,.2f}</td>
            <td style="padding:10px; color:#cbd5e1;">₹{spot:,.2f}</td>
            <td style="padding:10px; color:{pnl_color}; font-weight:bold;">₹{pnl:+,.2f}</td>
        </tr>
        """)

    summary_color = THEME_CONFIG["bullish"] if total_pnl >= 0 else THEME_CONFIG["bearish"]
    return "".join(rows), total_pnl, summary_color


# =====================================================
# OPTION CHAIN PANEL
# =====================================================

def render_option_chain_panel(states):
    html = ""
    for asset_name, state in states.items():
        html += f"""
        <div style="
            background:#0e121a;
            border:1px solid {THEME_CONFIG['border']};
            border-radius:10px;
            padding:18px;
            margin-bottom:14px;
            font-family:'JetBrains Mono', monospace;
        ">
            <h4 style="color:#fff; margin-bottom:12px; font-size:15px;">⛓ {asset_name} Option Chain Metrics</h4>
            <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:10px; font-size:12px; color:#94a3b8;">
                <div>ATM Strike: <b style="color:#38bdf8;">{state.get('atm_strike', '--')}</b></div>
                <div>CE LTP: <b style="color:{THEME_CONFIG['bullish']};">₹{state.get('ce_ltp', 0):.2f}</b></div>
                <div>PE LTP: <b style="color:{THEME_CONFIG['bearish']};">₹{state.get('pe_ltp', 0):.2f}</b></div>
                <div>Call OI: <b style="color:#fff;">{state.get('call_oi', 0):,}</b></div>
                <div>Put OI: <b style="color:#fff;">{state.get('put_oi', 0):,}</b></div>
                <div>Max Pain: <b style="color:#f59e0b;">{state.get('max_pain', '--')}</b></div>
                <div>Support (S1): <b style="color:{THEME_CONFIG['bullish']};">{state.get('support', '--')}</b></div>
                <div>Resistance (R1): <b style="color:{THEME_CONFIG['bearish']};">{state.get('resistance', '--')}</b></div>
                <div>OI Bias: <b style="color:{THEME_CONFIG['hyperlink']};">{state.get('oi_bias', 'NEUTRAL')}</b></div>
            </div>
        </div>
        """
    return html


# =====================================================
# TRADE OF THE MOMENT CARD
# =====================================================

def render_trade_card(asset_name, state):
    reasons = state.get("trade_reasons", ["High-conviction algorithmic setup identified."])
    reasons_html = "".join([f"<li style='margin-bottom:4px; color:#cbd5e1;'>✓ {r}</li>" for r in reasons])

    action = state.get("action", "NO TRADE")
    action_color = THEME_CONFIG["bullish"] if "CALL" in action else (THEME_CONFIG["bearish"] if "PUT" in action else THEME_CONFIG["neutral"])

    return f"""
    <div style="
        background: linear-gradient(145deg, #0e121a 0%, #141a26 100%);
        border: 1px solid {action_color}40;
        border-radius: 12px;
        padding: 22px;
        margin-bottom: 18px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.5);
        font-family: 'JetBrains Mono', 'Segoe UI', monospace;
    ">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
            <div>
                <span style="font-size:11px; color:{THEME_CONFIG['text_muted']}; font-weight:bold; letter-spacing:0.5px;">ALGORITHMIC TRADE RECOMMENDATION</span>
                <h3 style="color:#fff; margin:2px 0 0 0; font-size:18px;">🎯 {asset_name}</h3>
            </div>
            <div style="
                background:{action_color}20;
                color:{action_color};
                border:1px solid {action_color};
                padding:6px 16px;
                border-radius:20px;
                font-weight:800;
                font-size:13px;
            ">
                {action} ({state.get('trade_confidence', 0)}% Confidence)
            </div>
        </div>

        <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:12px; margin-bottom:16px;">
            <div style="background:#090c13; padding:10px; border-radius:6px;">
                <div style="font-size:10px; color:{THEME_CONFIG['text_muted']};">ENTRY PRICE</div>
                <div style="font-size:16px; font-weight:800; color:#fff; margin-top:2px;">₹{state.get('entry_price', 0):.2f}</div>
            </div>
            <div style="background:#090c13; padding:10px; border-radius:6px;">
                <div style="font-size:10px; color:{THEME_CONFIG['text_muted']};">STOP LOSS</div>
                <div style="font-size:16px; font-weight:800; color:{THEME_CONFIG['bearish']}; margin-top:2px;">₹{state.get('stop_loss', 0):.2f}</div>
            </div>
            <div style="background:#090c13; padding:10px; border-radius:6px;">
                <div style="font-size:10px; color:{THEME_CONFIG['text_muted']};">TARGET</div>
                <div style="font-size:16px; font-weight:800; color:{THEME_CONFIG['bullish']}; margin-top:2px;">₹{state.get('target', 0):.2f}</div>
            </div>
            <div style="background:#090c13; padding:10px; border-radius:6px;">
                <div style="font-size:10px; color:{THEME_CONFIG['text_muted']};">RISK : REWARD</div>
                <div style="font-size:16px; font-weight:800; color:#38bdf8; margin-top:2px;">{state.get('risk_reward', 0):.2f} : 1</div>
            </div>
        </div>

        <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:10px; font-size:12px; color:#94a3b8; border-top:1px solid #1f293d; padding-top:12px; margin-bottom:12px;">
            <div>Position Size: <b style="color:#fff;">{state.get('recommended_lots', 0)} Lots ({state.get('recommended_qty', 0)} Qty)</b></div>
            <div>Capital Required: <b style="color:#fff;">₹{state.get('capital_required', 0):,.2f}</b></div>
            <div>Expected Profit: <b style="color:{THEME_CONFIG['bullish']};">₹{state.get('expected_profit', 0):,.2f}</b></div>
        </div>

        <div style="background:#090c13; padding:12px; border-radius:6px; font-size:11px;">
            <div style="color:{THEME_CONFIG['hyperlink']}; font-weight:bold; margin-bottom:6px;">AI RATIONALE:</div>
            <ul style="margin:0; padding-left:14px; list-style-type:none;">
                {reasons_html}
            </ul>
        </div>
    </div>
    """