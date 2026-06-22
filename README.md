# 🧠 FinTech Risk Engine — `v3.0-live`

> Low-latency quantitative options analytics, real-time risk mechanics, and algorithmic signal alpha generation. Powered by streaming data and tight execution pipelines.

<p align="center">
  <img src="https://raw.githubusercontent.com/CPTMohit/FinTech_Risk_Engine/master/architecture_overview.png" alt="FinTech Risk Engine Architecture Diagram" width="100%" style="border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
</p>

---

### ⚡ The Stack

<p align="left">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" />
  <img src="https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white" />
  <img src="https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white" />
  <img src="https://img.shields.io/badge/Angel_One-007AFF?style=for-the-badge" />
</p>

---

### 🗺️ System Blueprint

<table>
  <tr>
    <td width="50%" valign="top">
      <h4>📥 Ingestion & Ticks</h4>
      <ul>
        <li><code>websocket_engine.py</code> handles ultra-low latency streaming ticks via Angel One SmartAPI.</li>
        <li>State persistence running concurrently with local session fallback.</li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h4>📊 Multi-Factor Processing</h4>
      <ul>
        <li><code>market_status.py</code> & <code>market_regime.py</code> dynamically compute macro volatility shifts.</li>
        <li>Real-time calculations for PCR and Options Chain Open Interest (OI) buildup.</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <h4>🚨 Alpha Alerts & Sizing</h4>
      <ul>
        <li><code>alert_engine.py</code> pushes rapid-fire market signals for NIFTY & BANKNIFTY.</li>
        <li><code>position_sizing.py</code> dynamically computes optimal risk exposure using the Kelly Criterion framework.</li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h4>📈 The Interface</h4>
      <ul>
        <li><code>test_app.py</code> boots up an interactive Streamlit UI for deep options analytics.</li>
        <li>Custom Plotly modules mapping real-time Greeks ($\Delta, \Gamma, \Theta, \nu$).</li>
      </ul>
    </td>
  </tr>
</table>

---

### 🚀 Quickstart

```bash
# Clone down the repository
git clone [https://github.com/CPTMohit/FinTech_Risk_Engine.git](https://github.com/CPTMohit/FinTech_Risk_Engine.git)

# Move into the environment
cd FinTech_Risk_Engine

# Spin up the engine dependencies
pip install -r requirements.txt

# Launch the live dashboard dashboard
streamlit run test_app.py
