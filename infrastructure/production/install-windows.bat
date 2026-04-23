@echo off
REM ═══════════════════════════════════════════════════════════════════════════
REM 🎮👑 AUREON TRADING SYSTEM - WINDOWS INSTALLER 👑🎮
REM ═══════════════════════════════════════════════════════════════════════════
REM One-click installer for Windows
REM Downloads Docker Desktop if needed, builds image, and launches
REM ═══════════════════════════════════════════════════════════════════════════

title AUREON Trading System Installer
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
echo     ║                    🎮 WINDOWS INSTALLER 🎮                               ║
echo     ║                                                                           ║
echo     ╚═══════════════════════════════════════════════════════════════════════════╝
echo.

REM Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ⚠️  Please run this installer as Administrator!
    echo     Right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo ═══════════════════════════════════════════════════════════════════════════
echo   Step 1: Checking Prerequisites
echo ═══════════════════════════════════════════════════════════════════════════
echo.

REM Check for Docker
docker --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Docker not found!
    echo.
    echo    AUREON runs in a secure Docker container.
    echo    Please install Docker Desktop first:
    echo.
    echo    https://www.docker.com/products/docker-desktop
    echo.
    echo    After installing Docker:
    echo    1. Start Docker Desktop
    echo    2. Wait for it to fully start
    echo    3. Run this installer again
    echo.
    pause
    exit /b 1
)
echo ✅ Docker found

REM Check Docker is running
docker info >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Docker is not running!
    echo    Please start Docker Desktop and wait for it to fully load.
    pause
    exit /b 1
)
echo ✅ Docker is running

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo   Step 2: Building AUREON Trading System
echo ═══════════════════════════════════════════════════════════════════════════
echo.

REM Build the Docker image
echo 🔨 Building Docker image (this may take a few minutes)...
docker build -t aureon-trading:latest -f production\Dockerfile .
if %errorLevel% neq 0 (
    echo ❌ Build failed! Please check the error messages above.
    pause
    exit /b 1
)
echo ✅ Docker image built successfully

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo   Step 3: Creating Data Volumes
echo ═══════════════════════════════════════════════════════════════════════════
echo.

REM Create volumes for persistent data
docker volume create aureon-data >nul 2>&1
docker volume create aureon-logs >nul 2>&1
docker volume create aureon-config >nul 2>&1
echo ✅ Data volumes created

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo   Step 4: Creating Desktop Shortcut
echo ═══════════════════════════════════════════════════════════════════════════
echo.

REM Create launcher batch file with resource limits
echo @echo off > "%USERPROFILE%\Desktop\AUREON.bat"
echo title AUREON Trading System >> "%USERPROFILE%\Desktop\AUREON.bat"
echo color 0A >> "%USERPROFILE%\Desktop\AUREON.bat"
echo echo Starting AUREON Trading System v1.0.0... >> "%USERPROFILE%\Desktop\AUREON.bat"
echo docker start aureon-game 2^>nul ^|^| docker run -d --name aureon-game -p 8888:8888 -v aureon-data:/aureon/data -v aureon-logs:/aureon/logs -v aureon-config:/aureon/config --memory=2g --cpus=2.0 --restart=unless-stopped aureon-trading:latest >> "%USERPROFILE%\Desktop\AUREON.bat"
echo timeout /t 5 /nobreak ^>nul >> "%USERPROFILE%\Desktop\AUREON.bat"
echo start http://localhost:8888 >> "%USERPROFILE%\Desktop\AUREON.bat"
echo echo. >> "%USERPROFILE%\Desktop\AUREON.bat"
echo echo AUREON is running at: http://localhost:8888 >> "%USERPROFILE%\Desktop\AUREON.bat"
echo echo Press any key to stop... >> "%USERPROFILE%\Desktop\AUREON.bat"
echo pause ^>nul >> "%USERPROFILE%\Desktop\AUREON.bat"
echo docker stop aureon-game >> "%USERPROFILE%\Desktop\AUREON.bat"

echo ✅ Desktop shortcut created: AUREON.bat

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo   ✅ INSTALLATION COMPLETE!
echo ═══════════════════════════════════════════════════════════════════════════
echo.
echo   🎮 AUREON Trading System has been installed!
echo.
echo   To start trading:
echo   1. Double-click 'AUREON.bat' on your Desktop
echo   2. Your browser will open to the Command Center
echo   3. Complete the first-time setup wizard
echo.
echo   Or run manually:
echo     docker run -it -p 8888:8888 aureon-trading:latest
echo.
echo   Dashboard URL: http://localhost:8888
echo.
echo ═══════════════════════════════════════════════════════════════════════════

set /p LAUNCH="Would you like to launch AUREON now? (Y/N): "
if /i "%LAUNCH%"=="Y" (
    echo.
    echo 🚀 Launching AUREON...
    docker run -d --name aureon-game -p 8888:8888 -v aureon-data:/aureon/data -v aureon-logs:/aureon/logs -v aureon-config:/aureon/config aureon-trading:latest
    timeout /t 5 /nobreak >nul
    start http://localhost:8888
)

echo.
pause
