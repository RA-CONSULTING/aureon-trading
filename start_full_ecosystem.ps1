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

Write-Host "[*] AUREON ECOSYSTEM LAUNCHER (WINDOWS) [*]" -ForegroundColor Cyan
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
Write-Host "[>>] Getting latest code from main..." -ForegroundColor Yellow

try {
    # First, stash any local changes (secrets, config)
    Write-Host "   [>] Saving local changes..." -ForegroundColor Gray
    $hasChanges = git status --porcelain 2>&1
    if ($hasChanges) {
        git stash push -m "auto-stash before pull" 2>&1 | Out-Null
        Write-Host "   [OK] Local changes stashed" -ForegroundColor Green
        $didStash = $true
    } else {
        Write-Host "   [--] No local changes to stash" -ForegroundColor Gray
        $didStash = $false
    }
    
    # Fetch and reset to latest main
    Write-Host "   [>] Fetching latest from origin..." -ForegroundColor Gray
    git fetch origin main 2>&1 | Out-Null
    
    # Reset to origin/main to get clean latest
    git reset --hard origin/main 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   [OK] Code updated to latest main" -ForegroundColor Green
    } else {
        Write-Warning "   [!] Reset had issues"
    }
} catch {
    Write-Warning "   [!] Could not update: $_"
}

# Restore stashed changes (contains secrets/local config)
Write-Host ""
Write-Host "[>>] Restoring local configuration..." -ForegroundColor Yellow

try {
    # Check if there are any stashes
    $stashList = git stash list 2>&1
    
    if ($stashList) {
        Write-Host "   Found stash: $($stashList.Split([char]10)[0])" -ForegroundColor Gray
        
        # Apply the latest stash (stash@{0})
        $stashResult = git stash pop 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   [OK] Stash applied successfully" -ForegroundColor Green
        } else {
            # If pop fails due to conflicts, try apply instead
            Write-Warning "   [!] Stash pop had conflicts, trying apply..."
            git stash apply 2>&1 | Out-Null
            Write-Host "   [OK] Stash applied (may need manual merge)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   [--] No stash found (using repo config)" -ForegroundColor Gray
    }
} catch {
    Write-Warning "   [!] Could not apply stash: $_"
    Write-Host "   Continuing without stash..." -ForegroundColor Gray
}

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan

# Set environment variables for UTF-8 encoding to prevent UnicodeEncodeError
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONLEGACYWINDOWSSTDIO = "utf-8"

# 1. Start the Quantum Miner (Brain)
Write-Host "[>>] Launching Quantum Miner (Brain)..." -ForegroundColor Yellow
$minerProcess = Start-Process -FilePath "python" -ArgumentList "aureon_miner.py" -PassThru -WindowStyle Minimized

if ($minerProcess.Id) {
    Write-Host "   [OK] Miner started with PID: $($minerProcess.Id)" -ForegroundColor Green
} else {
    Write-Error "   [FAIL] Failed to start Miner."
    exit 1
}

# 2. Wait for Brain State
$brainFile = Join-Path $env:TEMP "aureon_multidimensional_brain_output.json"
Write-Host "[..] Waiting for Quantum Brain initialization..." -ForegroundColor Yellow
Write-Host "   Looking for: $brainFile" -ForegroundColor Gray

$timeout = 60
$elapsed = 0
while (-not (Test-Path $brainFile)) {
    Start-Sleep -Seconds 1
    $elapsed++
    Write-Host -NoNewline "."
    if ($elapsed -ge $timeout) {
        Write-Host ""
        Write-Error "[FAIL] Timeout waiting for Brain State file. Check miner logs."
        Stop-Process -Id $minerProcess.Id -ErrorAction SilentlyContinue
        exit 1
    }
}

Write-Host ""
Write-Host "[OK] Brain State Detected!" -ForegroundColor Green

# 3. Start the Unified Ecosystem Engine
Write-Host "[>>] Launching Unified Ecosystem Engine..." -ForegroundColor Yellow
$ecosystemProcess = Start-Process -FilePath "python" -ArgumentList "aureon_unified_ecosystem.py" -PassThru -WindowStyle Minimized

if ($ecosystemProcess.Id) {
    Write-Host "   [OK] Ecosystem Engine started with PID: $($ecosystemProcess.Id)" -ForegroundColor Green
} else {
    Write-Error "   [FAIL] Failed to start Ecosystem Engine."
    Stop-Process -Id $minerProcess.Id -ErrorAction SilentlyContinue
    exit 1
}

# 4. Give Ecosystem time to initialize
Write-Host "[..] Waiting for Ecosystem initialization (5s)..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
Write-Host "   [OK] Ecosystem ready" -ForegroundColor Green

# 5. Start the Unified Live Trader
Write-Host ""
Write-Host "===================================================" -ForegroundColor Green
Write-Host "[>>] Launching Unified Live Trader (v6)..." -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green
Write-Host ""

try {
    python aureon_unified_live.py
}
finally {
    # Cleanup on exit
    Write-Host ""
    Write-Host "[XX] Shutting down ecosystem..." -ForegroundColor Yellow
    
    if ($minerProcess) {
        Stop-Process -Id $minerProcess.Id -ErrorAction SilentlyContinue
        Write-Host "   [OK] Miner stopped." -ForegroundColor Green
    }
    
    if ($ecosystemProcess) {
        Stop-Process -Id $ecosystemProcess.Id -ErrorAction SilentlyContinue
        Write-Host "   [OK] Ecosystem Engine stopped." -ForegroundColor Green
    }
}
