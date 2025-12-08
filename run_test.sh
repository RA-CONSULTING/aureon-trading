#!/bin/bash
cd /workspaces/aureon-trading
LIVE=1 timeout 45 python3 aureon_unified_ecosystem.py 2>&1 | head -200
