@echo off
setlocal

set "REPO_ROOT=%~dp0..\.."
if "%REPO_ROOT:~-1%"=="\" set "REPO_ROOT=%REPO_ROOT:~0,-1%"
set "PYTHON_EXE=%REPO_ROOT%\.venv\Scripts\python.exe"
set "SCRIPT_PATH=%REPO_ROOT%\aureon\exchanges\unified_market_trader.py"

if not exist "%PYTHON_EXE%" (
  echo Python venv not found: "%PYTHON_EXE%"
  exit /b 1
)

if not exist "%SCRIPT_PATH%" (
  echo Unified trader not found: "%SCRIPT_PATH%"
  exit /b 1
)

set "DOTENV_PATH=%REPO_ROOT%\.env"
set "PYTHONUNBUFFERED=1"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONPATH=%REPO_ROOT%;%REPO_ROOT%\aureon\core;%REPO_ROOT%\aureon\exchanges;%REPO_ROOT%\aureon\data_feeds;%REPO_ROOT%\aureon\monitors;%PYTHONPATH%"

rem Aggressive unified watchdog/reconnect timings
set "UNIFIED_EXCHANGE_REINIT_INTERVAL_SEC=8"
set "UNIFIED_CENTRAL_BEAT_REFRESH_SEC=2"
set "UNIFIED_CENTRAL_BEAT_STALE_AFTER_SEC=20"
set "UNIFIED_AURIS_FEED_MIN_INTERVAL_SEC=20"
set "UNIFIED_READY_STALE_AFTER_SEC=20"

rem Keep Capital scanning and refreshing continuously
set "CAPITAL_LIVE_REFRESH_ENABLED=true"
set "CAPITAL_LIVE_REFRESH_INTERVAL_SECS=0.5"
set "CAPITAL_LIVE_EVENT_MIN_INTERVAL_SECS=0.25"
set "CAPITAL_LIVE_EVENT_TRIGGER_PCT=0.0"
set "CAPITAL_PENNY_TAKE_PROFIT=true"
set "CAPITAL_SCAN_INTERVAL_SECS=1"
set "CAPITAL_MONITOR_INTERVAL_SECS=0.5"
set "CAPITAL_EXCHANGE_SYNC_SECS=2"
set "CAPITAL_QUAD_GATE_TTL_SECS=2"
set "CAPITAL_SLOT_FILL_INTERVAL_SECS=2"
set "CAPITAL_DEADMAN_STALE_SECS=20"
set "CAPITAL_HTTP_TIMEOUT_SECS=20"
set "CAPITAL_SESSION_RETRY_BACKOFF_SECS=8"

rem Force Alpaca stock scanning on for unified bridge/scanners
set "AUREON_SCAN_ALPACA_STOCKS=1"
set "ALPACA_INCLUDE_STOCKS=true"

rem Relax startup auth sensitivity on slower networks
set "ALPACA_TIMEOUT=12"
set "ALPACA_AUTH_TIMEOUT=8"
set "BINANCE_WS_DISABLE=false"

echo Repo root: "%REPO_ROOT%"
echo Python: "%PYTHON_EXE%"
echo Starting unified trader in aggressive live mode...

"%PYTHON_EXE%" "%SCRIPT_PATH%" --interval 0.5 %*
