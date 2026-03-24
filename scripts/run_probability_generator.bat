@echo off
:loop
echo Generating probability batch...
python generate_live_probability_batch.py
echo Sleeping for 60 seconds...
timeout /t 60
goto loop
