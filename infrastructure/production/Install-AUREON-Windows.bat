@echo off
REM ═══════════════════════════════════════════════════════════════════════════
REM 🎮👑 AUREON TRADING SYSTEM - WINDOWS PLUG & PLAY INSTALLER 👑🎮
REM ═══════════════════════════════════════════════════════════════════════════
REM Downloads AUREON.exe from GitHub and creates a desktop shortcut
REM No Docker, no terminal, no dependencies - just download and run!
REM ═══════════════════════════════════════════════════════════════════════════

title AUREON Trading System - Plug ^& Play Installer
color 0A

echo.
echo     ╔═══════════════════════════════════════════════════════════════════════════╗
echo     ║                                                                           ║
echo     ║     █████╗ ██╗   ██╗██████╗ ███████╗ ██████╗ ███╗   ██╗                   ║
echo     ║    ██╔══██╗██║   ██║██╔══██╗██╔════╝██╔═══██╗████╗  ██║                   ║
echo     ║    ███████║██║   ██║██████╔╝█████╗  ██║   ██║██╔██╗ ██║                   ║
echo     ║    ██╔══██║██║   ██║██╔══██╗██╔══╝  ██║   ██║██║╚██╗██║                   ║
echo     ║    ██║  ██║╚██████╔╝██║  ██║███████╗╚██████╔╝██║ ╚████║                   ║
echo     ║    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝                   ║
echo     ║                                                                           ║
echo     ║              🎮 PLUG ^& PLAY WINDOWS INSTALLER 🎮                         ║
echo     ║                                                                           ║
echo     ╚═══════════════════════════════════════════════════════════════════════════╝
echo.

set "INSTALL_DIR=%LOCALAPPDATA%\AUREON"
set "EXE_NAME=AUREON.exe"
set "DOWNLOAD_URL=https://github.com/RA-CONSULTING/aureon-trading/releases/latest/download/AUREON.exe"

echo ═══════════════════════════════════════════════════════════════════════════
echo   Step 1: Creating Install Directory
echo ═══════════════════════════════════════════════════════════════════════════
echo.

if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    echo ✅ Created: %INSTALL_DIR%
) else (
    echo ✅ Directory exists: %INSTALL_DIR%
)

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo   Step 2: Downloading AUREON
echo ═══════════════════════════════════════════════════════════════════════════
echo.
echo    Downloading from GitHub Releases...
echo    URL: %DOWNLOAD_URL%
echo.

REM Download using PowerShell (available on all modern Windows)
powershell -Command "& { $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile '%INSTALL_DIR%\%EXE_NAME%' }"

if %errorLevel% neq 0 (
    echo.
    echo ❌ Download failed!
    echo.
    echo    Please download manually from:
    echo    https://github.com/RA-CONSULTING/aureon-trading/releases
    echo.
    pause
    exit /b 1
)

echo ✅ Downloaded: %INSTALL_DIR%\%EXE_NAME%

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo   Step 3: Creating Desktop Shortcut
echo ═══════════════════════════════════════════════════════════════════════════
echo.

REM Create desktop shortcut using PowerShell
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%USERPROFILE%\Desktop\AUREON.lnk'); $s.TargetPath = '%INSTALL_DIR%\%EXE_NAME%'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Description = 'AUREON Quantum Trading System'; $s.Save()"

if %errorLevel% neq 0 (
    echo ⚠️  Could not create desktop shortcut
    echo    You can manually create a shortcut to: %INSTALL_DIR%\%EXE_NAME%
) else (
    echo ✅ Desktop shortcut created: AUREON
)

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo   Step 4: Creating Start Menu Entry
echo ═══════════════════════════════════════════════════════════════════════════
echo.

set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%START_MENU%\AUREON.lnk'); $s.TargetPath = '%INSTALL_DIR%\%EXE_NAME%'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Description = 'AUREON Quantum Trading System'; $s.Save()"

if %errorLevel% neq 0 (
    echo ⚠️  Could not create Start Menu entry
) else (
    echo ✅ Start Menu entry created
)

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo.
echo   ✅ INSTALLATION COMPLETE!
echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo.
echo   🎮 AUREON Trading System has been installed!
echo.
echo   To start:
echo   • Double-click 'AUREON' on your Desktop
echo   • Or find 'AUREON' in your Start Menu
echo   • Or run: %INSTALL_DIR%\%EXE_NAME%
echo.
echo   First Run:
echo   • The setup wizard will guide you through configuration
echo   • Enter your exchange API keys (optional)
echo   • Choose dry-run or live trading mode
echo.
echo   Features:
echo   • 🎮 Game Mode - Visual Command Center UI
echo   • 💰 Trading Engine - Automated profit hunting
echo   • 🐋 Orca Kill Cycle - Aggressive profit mode
echo   • 👑 Queen Dashboard - Neural decision viewer
echo.
echo   Safety:
echo   • Starts in DRY RUN mode (no real trades)
echo   • Live trading requires explicit confirmation
echo   • Credentials stored in Windows Credential Manager
echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo.

set /p LAUNCH="Would you like to launch AUREON now? (Y/N): "
if /i "%LAUNCH%"=="Y" (
    echo.
    echo 🚀 Launching AUREON...
    start "" "%INSTALL_DIR%\%EXE_NAME%"
)

echo.
echo Thank you for installing AUREON!
echo.
pause
