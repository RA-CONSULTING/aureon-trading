#!/usr/bin/env python3
"""Run Aureon Trading Ecosystem with LIVE trading"""

import subprocess
import sys
import os

os.chdir('/workspaces/aureon-trading')

# Set environment
os.environ['LIVE'] = '1'
os.environ['DEPLOY_SCOUTS_IMMEDIATELY'] = 'True'

print("Starting Aureon Unified Ecosystem with LIVE=1...")
print("="*70)
print()

# Run with Python
result = subprocess.run([sys.executable, 'aureon_unified_ecosystem.py'], 
                       env=os.environ.copy())

sys.exit(result.returncode)
