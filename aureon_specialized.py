#!/usr/bin/env python3
"""
🦆⚔️ AUREON SPECIALIZED ROLES - 5 Bot Army ⚔️🦆

Bot assignments:
- Buy Bot 1 & 2: Focus on entries only
- Sell Bot 1 & 2: Focus on exits only
- Watch Bot: Market scanner, no trading
"""

import sys
import os

# Get bot role from command line
role = os.getenv('BOT_ROLE', 'BALANCED')  # BUYER, SELLER, WATCHER, BALANCED

print(f"🦆 Starting as: {role}")

if role == 'WATCHER':
    # Market watcher - scan but don't trade
    os.environ['BINANCE_DRY_RUN'] = 'true'
    print("👁️ WATCHER MODE: Scanning market, no trades")
elif role == 'BUYER':
    print("💰 BUYER MODE: Hunting entries only")
elif role == 'SELLER':
    print("💎 SELLER MODE: Managing exits only")
else:
    print("⚖️ BALANCED MODE: Full trading")

# Now import and run the main trader
from aureon_ultimate import AureonUltimate

trader = AureonUltimate()
trader.bot_role = role
trader.run(duration_sec=3600)  # 1 hour
