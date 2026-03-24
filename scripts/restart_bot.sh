#!/bin/bash
echo "Stopping old bot..."
pkill -f s5_intelligent_dance.py
sleep 2
echo "Starting new aggressive bot..."
python3 s5_intelligent_dance.py
