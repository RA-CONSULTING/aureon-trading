@echo off
echo ════════════════════════════════════════════════════════════
echo 🐙 AUREON TRADING - 8/8 SYSTEMS ACTIVE 🐙
echo ════════════════════════════════════════════════════════════
echo.

cd /d "%~dp0"
set LIVE=1

:loop
echo Starting trading at %date% %time%...
python aureon_unified_ecosystem.py
echo.
echo Trading stopped. Restarting in 10 seconds...
timeout /t 10
goto loop
