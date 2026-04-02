@echo off
setlocal

set "REPO_ROOT=%~dp0..\.."
if "%REPO_ROOT:~-1%"=="\" set "REPO_ROOT=%REPO_ROOT:~0,-1%"
set "PYTHON_EXE=%REPO_ROOT%\.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
  echo Python venv not found: "%PYTHON_EXE%"
  exit /b 1
)

set "PYTHONUNBUFFERED=1"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONPATH=%REPO_ROOT%;%REPO_ROOT%\aureon\core;%REPO_ROOT%\aureon\exchanges;%REPO_ROOT%\aureon\data_feeds;%REPO_ROOT%\aureon\monitors;%REPO_ROOT%\aureon\intelligence;%REPO_ROOT%\aureon\queen;%PYTHONPATH%"

echo ============================================================
echo  AUREON GLOBAL HISTORY - FULL INGEST (with Queen Knowledge)
echo  DB: state\aureon_global_history.sqlite
echo ============================================================
echo.

echo [1/7] Syncing account trades (Kraken, Binance, Alpaca, Capital)...
"%PYTHON_EXE%" "%REPO_ROOT%\scripts\python\sync_global_history_db.py" %*
echo.

echo [2/7] Ingesting yfinance (stocks, indices, forex, commodities, ETFs)...
"%PYTHON_EXE%" "%REPO_ROOT%\scripts\python\ingest_yfinance.py" --all --days 1825 %*
echo.

echo [3/7] Ingesting FRED macro indicators (rates, GDP, CPI, employment)...
"%PYTHON_EXE%" "%REPO_ROOT%\scripts\python\ingest_fred.py" --category all %*
echo.

echo [4/7] Ingesting existing feeds (CoinGecko, news, Glassnode, Coinbase, macro)...
"%PYTHON_EXE%" "%REPO_ROOT%\scripts\python\ingest_existing_feeds.py" --feeds all %*
echo.

echo [5/7] Ingesting CoinAPI market history...
"%PYTHON_EXE%" "%REPO_ROOT%\scripts\python\ingest_market_history.py" --coinapi --coinapi-pairs BTC/USD,ETH/USD,XRP/USD,SOL/USD --days 365 %*
echo.

echo [6/7] Ingesting economic calendar and geopolitical events...
"%PYTHON_EXE%" "%REPO_ROOT%\scripts\python\ingest_economic_calendar.py" --sources all --seed-events %*
echo.

echo [7/7] Ingesting Queen knowledge (consciousness, memories, insights, thoughts, strategies)...
"%PYTHON_EXE%" "%REPO_ROOT%\scripts\python\ingest_queen_knowledge.py" --sources all %*
echo.

echo ============================================================
echo  FULL INGEST COMPLETE (including Queen Knowledge)
echo ============================================================

echo.
echo To query the unified dataset:
echo   sqlite3 state\aureon_global_history.sqlite
echo.
echo Quick stats:
"%PYTHON_EXE%" -c "import sqlite3; c=sqlite3.connect('%REPO_ROOT%/state/aureon_global_history.sqlite'); [print(f'  {r[0]:25s} {r[1]:>10,d} rows') for r in c.execute(\"SELECT name, (SELECT COUNT(1) FROM \" || name || \") FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%%' ORDER BY name;\").fetchall()]; c.close()"
