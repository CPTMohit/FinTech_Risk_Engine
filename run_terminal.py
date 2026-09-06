"""
Project: FinTech Risk Isolation Engine V2
Module: Terminal Launcher & Dev Server Runner
Author: Mohit Singh
"""

import sys
import os
import webbrowser
import uvicorn
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))
if str(CURRENT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR / "src"))

def main():
    print("=" * 70)
    print("  ⚡ FINTECH RISK ISOLATION ENGINE V2 - INSTITUTIONAL TRADING DESK  ")
    print("=" * 70)
    print("  ✓ High-Performance FastAPI Backend: http://127.0.0.1:8000")
    print("  ✓ Institutional Web Trading Terminal: http://127.0.0.1:8000/")
    print("  ✓ Interactive REST API Docs: http://127.0.0.1:8000/docs")
    print("  ✓ Realtime WebSocket Feed: ws://127.0.0.1:8000/ws/live")
    print("=" * 70)
    
    # Run Uvicorn server
    uvicorn.run("src.api_server:app", host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    main()
