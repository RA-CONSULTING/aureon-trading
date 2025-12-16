@echo off
echo 💎 AUREON MINER - LUMINA TURBO MODE 💎
echo.
echo Setting up Quantum Environment...
set LUMINA_THRESHOLD_W=0.1
set LUMINA_PUMP_SCALE=100.0

REM You can set your worker name here if you want to hardcode it
REM set MINING_WORKER=your_worker_name

echo.
echo Starting Miner...
echo Press Ctrl+C to stop.
echo.
python aureon_miner.py
pause
