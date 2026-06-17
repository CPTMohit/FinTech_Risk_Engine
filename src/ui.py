"""
Project: FinTech Risk Isolation Engine V2
Module: UI Renderer
Author: Mohit Singh
"""

THEME_CONFIG = {
    "background": "#161b22",
    "border": "#30363d",
    "text_muted": "#8c9bae",
    "bullish": "#00FFCC",
    "bearish": "#FF3366",
    "neutral": "#FBBF24",
    "hyperlink": "#38BDF8"
}


# =====================================================
# ASSET CARD
# =====================================================

def render_asset_card(asset_title, state):

    if state["action"] == "BUY CALL":
        action_color = THEME_CONFIG["bullish"]

    elif state["action"] == "BUY PUT":
        action_color = THEME_CONFIG["bearish"]

    else:
        action_color = THEME_CONFIG["neutral"]

    change_color = (
        THEME_CONFIG["bullish"]
        if state["change_7d"] >= 0
        else THEME_CONFIG["bearish"]
    )

    sign = (
        "+"
        if state["change_7d"] >= 0
        else ""
    )

    return f"""
    <div class="global-ticker-card">

        <div style="
            display:flex;
            justify-content:space-between;
            align-items:center;
        ">

            <span style="
                color:{THEME_CONFIG['text_muted']};
                font-weight:bold;
            ">
                {asset_title}
            </span>

            <span style="
                color:{change_color};
                font-weight:bold;
            ">
                {sign}{state['change_7d']:.2f}%
            </span>

        </div>

        <div style="
            font-size:32px;
            font-weight:bold;
            margin-top:8px;
            margin-bottom:8px;
        ">
            ₹{state['spot']:,.2f}
        </div>

        <div style="
            color:{action_color};
            font-weight:bold;
        ">
            {state['action']}
        </div>

        <hr>

        <div>
            Probability:
            <b>{state['probability']:.1f}%</b>
        </div>

        <div>
            Trend:
            <b>{state['trend']}</b>
        </div>

        <div>
            PCR:
            <b>{state['pcr']:.2f}</b>
        </div>

        <div>
            OI:
            <b>{state['oi']:,}</b>
        </div>

        <div>
            Score:
            <b>{state['signal_score']}</b>
        </div>

        <div>
    Delta:
    <b>{state['delta']:.2f}</b>
    </div>

    <div>
        Gamma:
        <b>{state['gamma']:.4f}</b>
    </div>

    <div>
        Theta:
        <b>{state['theta']:.2f}</b>
    </div>

    <div>
        Vega:
        <b>{state['vega']:.2f}</b>
    </div>

</div>
    """


# =====================================================
# STRENGTH METER
# =====================================================

def render_strength_meter(title, states):

    nifty_prob = (
        states["NIFTY 50 INDEX"]["probability"]
    )

    bank_prob = (
        states["BANK NIFTY INDEX"]["probability"]
    )

    return f"""
    <div style="
        background:#161b22;
        border:1px solid {THEME_CONFIG['border']};
        border-radius:8px;
        padding:15px;
    ">

        <div style="
            display:flex;
            justify-content:space-between;
            margin-bottom:10px;
        ">

            <span>{title}</span>

            <span>
                NIFTY {nifty_prob:.0f}% |
                BANK {bank_prob:.0f}%
            </span>

        </div>

        <div style="
            display:flex;
            height:12px;
            overflow:hidden;
            border-radius:4px;
        ">

            <div style="
                width:{nifty_prob}%;
                background:{THEME_CONFIG['bullish']};
            ">
            </div>

            <div style="
                width:{bank_prob}%;
                background:{THEME_CONFIG['hyperlink']};
            ">
            </div>

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

        if state["action"] == "BUY CALL":
            color = THEME_CONFIG["bullish"]

        elif state["action"] == "BUY PUT":
            color = THEME_CONFIG["bearish"]

        else:
            color = THEME_CONFIG["neutral"]

        row = f"""
        <tr>

            <td>{state['opt_symbol']}</td>

            <td style="
                color:{color};
                font-weight:bold;
            ">
                {state['action']}
            </td>

            <td>{state['pcr']:.2f}</td>

            <td>{state['oi']:,}</td>

            <td>{state['oi_structure']}</td>

            <td>{state['trend']}</td>

           <td>{state['signal_score']}</td>

            <td>{state['delta']:.2f}</td>

            <td>{state['gamma']:.4f}</td>

            <td>{state['theta']:.2f}</td>

            <td>{state['vega']:.2f}</td>

            <td>{state['probability']:.1f}%</td>
        </tr>
        """

        rows.append(row)

        if state["probability"] > highest_prob_val:

            highest_prob_val = (
                state["probability"]
            )

            highest_prob_asset = (
                asset_name,
                state
            )

    return (
        "".join(rows),
        highest_prob_asset,
        highest_prob_val
    )


# =====================================================
# POSITION TABLE
# =====================================================

def render_position_table(states):

    rows = []

    total_pnl = 0.0

    for asset_name, state in states.items():

        entry = (
            state["mock_entry"]
        )

        spot = (
            state["spot"]
        )

        size = (
            state["mock_size"]
        )

        if state["dir_factor"] > 0:

            direction = "LONG"

            pnl = (
                (spot - entry)
                * size
            )

        elif state["dir_factor"] < 0:

            direction = "SHORT"

            pnl = (
                (entry - spot)
                * size
            )

        else:

            direction = "FLAT"

            pnl = 0

        total_pnl += pnl

        pnl_color = (
            THEME_CONFIG["bullish"]
            if pnl >= 0
            else THEME_CONFIG["bearish"]
        )

        rows.append(
            f"""
            <tr>

                <td>{asset_name}</td>

                <td>{direction}</td>

                <td>{size}</td>

                <td>₹{entry:,.2f}</td>

                <td>₹{spot:,.2f}</td>

                <td style="
                    color:{pnl_color};
                    font-weight:bold;
                ">
                    ₹{pnl:,.2f}
                </td>

            </tr>
            """
        )

    summary_color = (
        THEME_CONFIG["bullish"]
        if total_pnl >= 0
        else THEME_CONFIG["bearish"]
    )

    return (
        "".join(rows),
        total_pnl,
        summary_color
    )