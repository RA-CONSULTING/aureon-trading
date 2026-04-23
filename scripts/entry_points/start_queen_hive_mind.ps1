Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Aureon Hive Mind Launcher (Real Data Only)" -ForegroundColor Cyan
Write-Host "================================================"

if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
  Write-Error "Python is not installed or not in PATH."
  exit 1
}

# Real data only + live trading flags
$env:REAL_DATA_ONLY = "1"
$env:LIVE = "1"
$env:BINANCE_DRY_RUN = "false"
$env:KRAKEN_DRY_RUN = "false"
$env:ALPACA_DRY_RUN = "false"
$env:ALPACA_PAPER = "false"
$env:BINANCE_USE_TESTNET = "false"
$env:CAPITAL_DEMO = "0"
$env:SIMULATED_ATTACKS = "false"
$env:SENTIENCE_FORCE_PERFECT = "0"
$env:LIVE_TRADING_AUTO_CONFIRM = "ENABLE LIVE TRADING"

# Windows UTF-8 safety
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONLEGACYWINDOWSSTDIO = "utf-8"

# Start Queen Hive Mind (ordered startup sequence)
Write-Host "[1/2] Starting Queen Hive Mind startup sequence..." -ForegroundColor Yellow
$startupProcess = Start-Process -FilePath "python" -ArgumentList "aureon_unified_startup.py" -PassThru -WindowStyle Minimized

if (-not $startupProcess.Id) {
  Write-Error "Failed to start aureon_unified_startup.py"
  exit 1
}

Write-Host "   Hive Mind PID: $($startupProcess.Id)" -ForegroundColor Green
Write-Host "   Waiting for systems to initialize (5s)..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# Start Live Trading (auto-confirmed)
Write-Host "[2/2] Starting live trading engine..." -ForegroundColor Yellow
python run_live_trading.py
