#!/usr/bin/env python3
"""
Test Scout Deployment - Verify force trades on startup
"""
import os
from dotenv import load_dotenv
load_dotenv()

# Force live mode
os.environ['LIVE'] = '1'
os.environ['DRY_RUN'] = '0'

from aureon_unified_ecosystem import AureonKrakenEcosystem, CONFIG

print("═══════════════════════════════════════")
print("🚀 SCOUT DEPLOYMENT TEST")
print("═══════════════════════════════════════")
print(f"DEPLOY_SCOUTS_IMMEDIATELY: {CONFIG['DEPLOY_SCOUTS_IMMEDIATELY']}")
print(f"SCOUT_MIN_MOMENTUM: {CONFIG['SCOUT_MIN_MOMENTUM']}%")
print(f"SCOUT_FORCE_COUNT: {CONFIG['SCOUT_FORCE_COUNT']}")
print(f"DRY_RUN: {os.getenv('DRY_RUN', '1')}")
print(f"LIVE: {os.getenv('LIVE', '0')}")
print()

# Initialize ecosystem
print("Initializing Aureon Kraken Ecosystem...")
ecosystem = AureonKrakenEcosystem(dry_run=False)

print(f"\nCurrent equity: £{ecosystem.total_equity_gbp:.2f}")
print(f"Cash balance: £{ecosystem.cash_balance_gbp:.2f}")
print(f"Positions: {len(ecosystem.positions)}")
print()

# Test _deploy_scouts method directly
print("Testing _deploy_scouts() method...")
print("═══════════════════════════════════════")

# First refresh tickers so we have data
print("Refreshing tickers...")
ecosystem.refresh_tickers()
print(f"Ticker cache size: {len(ecosystem.ticker_cache)}")
print()

# Now deploy scouts
print("Deploying scouts...")
ecosystem._deploy_scouts()

print()
print("═══════════════════════════════════════")
print("TEST COMPLETE")
print(f"Positions after scout deployment: {len(ecosystem.positions)}")
if ecosystem.positions:
    print("\n📊 Deployed Positions:")
    for symbol, pos in ecosystem.positions.items():
        print(f"  • {symbol}: {pos.quantity:.6f} @ £{pos.entry_price:.2f}")
print("═══════════════════════════════════════")
