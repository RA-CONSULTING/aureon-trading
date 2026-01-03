#!/bin/bash
# Run the Adaptive Conversion Commando self-test
cd /workspaces/aureon-trading
export AUREON_LADDER_ENABLED=1
export AUREON_LADDER_MODE=suggest
python aureon_conversion_commando.py
