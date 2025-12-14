<#
.SYNOPSIS
    Starts the full Aureon Ecosystem on Windows.
    Pulls latest code from main, applies stash, then launches the system.

.DESCRIPTION
    1. Pulls latest code from GitHub main branch.
    2. Applies the latest stash (if any) to restore local secrets/config.
    3. Starts aureon_miner.py in a separate minimized window.
    4. Waits for the Brain State file to be generated in %TEMP%.
    5. Starts aureon_unified_ecosystem.py in the current window.
#>

Write-Host "🐙🌌 AUREON ECOSYSTEM LAUNCHER (WINDOWS) 🌌🐙" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

# Check for Git
if (-not (Get-Command "git" -ErrorAction SilentlyContinue)) {
    Write-Error "Git is not installed or not in PATH."
    exit 1
}

# Check for Python
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Error "Python is not installed or not in PATH."
    exit 1
}

# ============================================
# GIT: Pull latest and restore stash
# ============================================
Write-Host ""
Write-Host "📥 Pulling latest code from main..." -ForegroundColor Yellow

try {
    # Fetch and pull latest
    git fetch origin main 2>&1 | Out-Null
    $pullResult = git pull origin main 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Code updated successfully" -ForegroundColor Green
        if ($pullResult -match "Already up to date") {
            Write-Host "   📌 Already up to date" -ForegroundColor Gray
        } else {
            Write-Host "   📦 New changes pulled" -ForegroundColor Cyan
        }
    } else {
        Write-Warning "   ⚠️ Pull had issues (may have local changes)"
        Write-Host "   Attempting to continue..." -ForegroundColor Gray
    }
} catch {
    Write-Warning "   ⚠️ Could not pull: $_"
}

# Apply latest stash (contains secrets/local config)
Write-Host ""
Write-Host "🔐 Restoring local configuration from stash..." -ForegroundColor Yellow

try {
    # Check if there are any stashes
    $stashList = git stash list 2>&1
    
    if ($stashList) {
        Write-Host "   Found stash: $($stashList.Split("`n")[0])" -ForegroundColor Gray
        
        # Apply the latest stash (stash@{0})
        $stashResult = git stash pop 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Stash applied successfully" -ForegroundColor Green
        } else {
            # If pop fails due to conflicts, try apply instead
            Write-Warning "   ⚠️ Stash pop had conflicts, trying apply..."
            git stash apply 2>&1 | Out-Null
            Write-Host "   ✅ Stash applied (may need manual merge)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   📌 No stash found (using repo config)" -ForegroundColor Gray
    }
} catch {
    Write-Warning "   ⚠️ Could not apply stash: $_"
    Write-Host "   Continuing without stash..." -ForegroundColor Gray
}

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan

# Set environment variables for UTF-8 encoding to prevent UnicodeEncodeError
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONLEGACYWINDOWSSTDIO = "utf-8"

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
