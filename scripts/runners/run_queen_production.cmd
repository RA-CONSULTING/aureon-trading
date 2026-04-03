@echo off
setlocal

set "REPO_ROOT=%~dp0..\.."
if "%REPO_ROOT:~-1%"=="\" set "REPO_ROOT=%REPO_ROOT:~0,-1%"
set "PYTHON_EXE=%REPO_ROOT%\.venv\Scripts\python.exe"

set "PYTHONUNBUFFERED=1"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONPATH=%REPO_ROOT%;%REPO_ROOT%\aureon\core;%REPO_ROOT%\aureon\exchanges;%REPO_ROOT%\aureon\queen;%REPO_ROOT%\aureon\autonomous;%REPO_ROOT%\aureon\intelligence;%REPO_ROOT%\aureon\data_feeds;%REPO_ROOT%\aureon\harmonic;%REPO_ROOT%\aureon\bridges;%REPO_ROOT%\aureon\utils;%REPO_ROOT%\aureon\wisdom;%REPO_ROOT%\aureon\scanners;%REPO_ROOT%\aureon\strategies;%REPO_ROOT%\aureon\simulation;%REPO_ROOT%\aureon\bots;%REPO_ROOT%\aureon\trading;%REPO_ROOT%\aureon\decoders;%REPO_ROOT%\aureon\monitors;%REPO_ROOT%\aureon\analytics;%REPO_ROOT%\aureon\bots_intelligence;%REPO_ROOT%\aureon\portfolio"

rem Disable Capital deadman during off-hours
set "CAPITAL_DEADMAN_STALE_SECS=300"

echo ============================================================
echo   QUEEN SERO — PRODUCTION MODE (auto-restart)
echo   http://localhost:5299
echo ============================================================

:loop
echo.
echo [%date% %time%] Starting Queen Sero...
"%PYTHON_EXE%" "%REPO_ROOT%\aureon\autonomous\aureon_face_app.py"
echo.
echo [%date% %time%] Queen stopped. Restarting in 5 seconds...
timeout /t 5 /nobreak >nul
goto loop
