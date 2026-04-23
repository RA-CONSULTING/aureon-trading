# AUREON Trading System - Windows One-Line Installer
# Run this in PowerShell: irm https://raw.githubusercontent.com/RA-CONSULTING/aureon-trading/main/production/Install-AUREON.ps1 | iex

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "    ╔═══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "    ║                                                                           ║" -ForegroundColor Cyan
Write-Host "    ║     █████╗ ██╗   ██╗██████╗ ███████╗ ██████╗ ███╗   ██╗                   ║" -ForegroundColor Cyan
Write-Host "    ║    ██╔══██╗██║   ██║██╔══██╗██╔════╝██╔═══██╗████╗  ██║                   ║" -ForegroundColor Cyan
Write-Host "    ║    ███████║██║   ██║██████╔╝█████╗  ██║   ██║██╔██╗ ██║                   ║" -ForegroundColor Cyan
Write-Host "    ║    ██╔══██║██║   ██║██╔══██╗██╔══╝  ██║   ██║██║╚██╗██║                   ║" -ForegroundColor Cyan
Write-Host "    ║    ██║  ██║╚██████╔╝██║  ██║███████╗╚██████╔╝██║ ╚████║                   ║" -ForegroundColor Cyan
Write-Host "    ║    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝                   ║" -ForegroundColor Cyan
Write-Host "    ║                                                                           ║" -ForegroundColor Cyan
Write-Host "    ║              🎮 PLUG & PLAY WINDOWS INSTALLER 🎮                          ║" -ForegroundColor Cyan
Write-Host "    ║                                                                           ║" -ForegroundColor Cyan
Write-Host "    ╚═══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$installDir = "$env:LOCALAPPDATA\AUREON"
$exePath = "$installDir\AUREON.exe"
$downloadUrl = "https://github.com/RA-CONSULTING/aureon-trading/releases/latest/download/AUREON.exe"

# Step 1: Create directory
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host "  Step 1: Creating Install Directory" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host ""

if (!(Test-Path $installDir)) {
    New-Item -ItemType Directory -Force -Path $installDir | Out-Null
    Write-Host "✅ Created: $installDir" -ForegroundColor Green
} else {
    Write-Host "✅ Directory exists: $installDir" -ForegroundColor Green
}

# Step 2: Download
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host "  Step 2: Downloading AUREON" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host ""
Write-Host "   Downloading from GitHub Releases..." -ForegroundColor Yellow
Write-Host "   URL: $downloadUrl" -ForegroundColor DarkGray

try {
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $downloadUrl -OutFile $exePath
    Write-Host "✅ Downloaded: $exePath" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "❌ Download failed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Please download manually from:" -ForegroundColor Yellow
    Write-Host "   https://github.com/RA-CONSULTING/aureon-trading/releases" -ForegroundColor Cyan
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 3: Create desktop shortcut
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host "  Step 3: Creating Desktop Shortcut" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host ""

try {
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\AUREON.lnk")
    $Shortcut.TargetPath = $exePath
    $Shortcut.WorkingDirectory = $installDir
    $Shortcut.Description = "AUREON Quantum Trading System"
    $Shortcut.Save()
    Write-Host "✅ Desktop shortcut created: AUREON" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Could not create desktop shortcut" -ForegroundColor Yellow
}

# Step 4: Create Start Menu entry
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host "  Step 4: Creating Start Menu Entry" -ForegroundColor White
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host ""

try {
    $startMenu = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
    $Shortcut = $WshShell.CreateShortcut("$startMenu\AUREON.lnk")
    $Shortcut.TargetPath = $exePath
    $Shortcut.WorkingDirectory = $installDir
    $Shortcut.Description = "AUREON Quantum Trading System"
    $Shortcut.Save()
    Write-Host "✅ Start Menu entry created" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Could not create Start Menu entry" -ForegroundColor Yellow
}

# Done!
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host ""
Write-Host "  ✅ INSTALLATION COMPLETE!" -ForegroundColor Green
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host ""
Write-Host "  🎮 AUREON Trading System has been installed!" -ForegroundColor Cyan
Write-Host ""
Write-Host "  To start:" -ForegroundColor White
Write-Host "  • Double-click 'AUREON' on your Desktop" -ForegroundColor Gray
Write-Host "  • Or find 'AUREON' in your Start Menu" -ForegroundColor Gray
Write-Host "  • Or run: $exePath" -ForegroundColor Gray
Write-Host ""
Write-Host "  First Run:" -ForegroundColor White
Write-Host "  • The setup wizard will guide you through configuration" -ForegroundColor Gray
Write-Host "  • Enter your exchange API keys (optional)" -ForegroundColor Gray
Write-Host "  • Choose dry-run or live trading mode" -ForegroundColor Gray
Write-Host ""
Write-Host "  Features:" -ForegroundColor White
Write-Host "  • 🎮 Game Mode - Visual Command Center UI" -ForegroundColor Gray
Write-Host "  • 💰 Trading Engine - Automated profit hunting" -ForegroundColor Gray
Write-Host "  • 🐋 Orca Kill Cycle - Aggressive profit mode" -ForegroundColor Gray
Write-Host "  • 👑 Queen Dashboard - Neural decision viewer" -ForegroundColor Gray
Write-Host ""
Write-Host "  Safety:" -ForegroundColor White
Write-Host "  • Starts in DRY RUN mode (no real trades)" -ForegroundColor Gray
Write-Host "  • Live trading requires explicit confirmation" -ForegroundColor Gray
Write-Host "  • Credentials stored in Windows Credential Manager" -ForegroundColor Gray
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host ""

$launch = Read-Host "Would you like to launch AUREON now? (Y/N)"
if ($launch -eq "Y" -or $launch -eq "y") {
    Write-Host ""
    Write-Host "🚀 Launching AUREON..." -ForegroundColor Cyan
    Start-Process $exePath
}

Write-Host ""
Write-Host "Thank you for installing AUREON!" -ForegroundColor Green
Write-Host ""
