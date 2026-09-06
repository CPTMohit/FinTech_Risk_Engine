@echo off
title FLOW - Institutional Algorithmic & Paper Trading Terminal
echo ================================================================
echo   FLOW TRADING DESK - PRODUCTION SERVER LAUNCHER
echo ================================================================
cd /d "%~dp0"
echo Starting FastAPI ASGI Server on http://0.0.0.0:8000 ...
start "" http://127.0.0.1:8000
"..\.venv\Scripts\python.exe" -m uvicorn src.api_server:app --host 0.0.0.0 --port 8000
pause
