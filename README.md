# 🧠 FinTech Risk Engine

A real-time quantitative trading and options analytics system driven by modular data pipelines and predictive risk mechanics.

---

## 🗺️ System Architecture Overview

The pipeline ingests streaming market data, processes multi-factor options metrics, and delivers dynamic trading states via an interactive dashboard interface.

<p align="center">
  <img src="https://raw.githubusercontent.com/CPTMohit/FinTech_Risk_Engine/main/architecture_overview.png" alt="FinTech Risk Engine Architecture Diagram" width="100%">
</p>

---

## ⚡ Core Engineering Modules

* **`websocket_engine.py`**: Manages low-latency connections to Angel One SmartAPI for streaming live ticks.
* **`market_status.py` & `market_regime.py`**: Tracks global market context, volatility classification, and structural trend shifting.
* **`alert_engine.py`**: Dispatches real-time, high-probability parameter warnings (PCR, India VIX alerts).
* **`position_sizing.py`**: Implements quantitative risk assessment models using Kelly Criterion mechanics.
* **`journal_engine.py`**: Logs performance states, trades, and diagnostic outputs to local storage.

---

## 🛠️ Technology Stack

* **Language & Core:** Python, NumPy, Pandas
* **Data Sources:** Angel One SmartAPI, SmartWebSocketV2
* **Visualization:** Streamlit, Plotly
