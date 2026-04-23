@echo off
echo ========================================
echo   AUREON Desktop App Builder
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

:: Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

:: Build executable
echo.
echo Building aureon.exe...
pyinstaller --onefile --windowed --name aureon --icon=aureon.ico ^
    --add-data "*.py;." ^
    --hidden-import keyring.backends.Windows ^
    launcher.py

echo.
echo ========================================
echo   Build complete!
echo   Output: dist\aureon.exe
echo ========================================
pause
