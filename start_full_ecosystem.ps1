<#
.SYNOPSIS
    Starts the full Aureon Ecosystem on Windows.
    Launches the Quantum Miner (Brain) in the background and the Unified Trader in the foreground.

.DESCRIPTION
    1. Starts aureon_miner.py in a separate minimized window.
    2. Waits for the Brain State file to be generated in %TEMP%.
    3. Starts aureon_unified_ecosystem.py in the current window.
#>

Write-Host "🐙🌌 AUREON ECOSYSTEM LAUNCHER (WINDOWS) 🌌🐙" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

# Check for Python
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed or not in PATH."
    exit 1
}

# 1. Start the Quantum Miner (Brain)
Write-Host "🚀 Launching Quantum Miner (Brain)..." -ForegroundColor Yellow
$minerProcess = Start-Process -FilePath "python" -ArgumentList "aureon_miner.py" -PassThru -WindowStyle Minimized

if ($minerProcess.Id) {
    Write-Host "   ✅ Miner started with PID: $($minerProcess.Id)" -ForegroundColor Green
} else {
    Write-Error "   ❌ Failed to start Miner."
    exit 1
}

# 2. Wait for Brain State
$brainFile = Join-Path $env:TEMP "aureon_multidimensional_brain_output.json"
Write-Host "⏳ Waiting for Quantum Brain initialization..." -ForegroundColor Yellow
Write-Host "   Looking for: $brainFile" -ForegroundColor Gray

$timeout = 60
$elapsed = 0
while (-not (Test-Path $brainFile)) {
    Start-Sleep -Seconds 1
    $elapsed++
    Write-Host -NoNewline "."
    if ($elapsed -ge $timeout) {
        Write-Error "`n❌ Timeout waiting for Brain State file. Check miner logs."
        Stop-Process -Id $minerProcess.Id -ErrorAction SilentlyContinue
        exit 1
    }
}

Write-Host "`n✅ Brain State Detected!" -ForegroundColor Green

# 3. Start the Unified Trader
Write-Host "🚀 Launching Unified Ecosystem Trader..." -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

try {
    python aureon_unified_ecosystem.py
}
finally {
    # Cleanup on exit
    Write-Host "`n🛑 Shutting down ecosystem..." -ForegroundColor Yellow
    Stop-Process -Id $minerProcess.Id -ErrorAction SilentlyContinue
    Write-Host "   ✅ Miner stopped." -ForegroundColor Green
}
