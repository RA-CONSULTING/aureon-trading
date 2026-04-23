#!/usr/bin/env python3
"""
🔍 DIAGNOSE WHY NO TRADES ARE BEING MADE
"""
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import json
import logging

sys.path.insert(0, '/workspaces/aureon-trading')

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print("="*60)
print("🔍 TRADE EXECUTION DIAGNOSTICS")
print("="*60)

# 1. Check environment variables
print("\n✅ STEP 1: Environment Variables")
print(f"  LIVE = {os.getenv('LIVE', 'NOT SET')}")
print(f"  DRY_RUN = {os.getenv('DRY_RUN', 'NOT SET')}")
print(f"  FORCE_TRADE = {os.getenv('FORCE_TRADE', 'NOT SET')}")

# 2. Check state file
print("\n✅ STEP 2: State File")
try:
    with open('aureon_kraken_state.json') as f:
        state = json.load(f)
        print(f"  Balance: ${state.get('balance', 0):.2f}")
        print(f"  Total Trades: {state.get('total_trades', 0)}")
        print(f"  Positions: {len(state.get('positions', {}))}")
        print(f"  Iteration: {state.get('iteration', 0)}")
except Exception as e:
    print(f"  ❌ Error: {e}")

# 3. Check unified_exchange_client
print("\n✅ STEP 3: Unified Exchange Client")
try:
    from unified_exchange_client import UnifiedExchangeClient, MultiExchangeClient
    print(f"  ✅ unified_exchange_client imports OK")
    
    # Try to initialize
    multi = MultiExchangeClient(dry_run=False)
    print(f"  ✅ MultiExchangeClient initialized (dry_run=False)")
    print(f"  Clients available: {list(multi.clients.keys())}")
except Exception as e:
    print(f"  ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# 4. Check Binance connection
print("\n✅ STEP 4: Binance Connection")
try:
    from binance_client import BinanceClient
    binance = BinanceClient(dry_run=False)
    balance = binance.get_balance()
    print(f"  ✅ Binance connected")
    print(f"  Account: {balance}")
except Exception as e:
    print(f"  ❌ Binance error: {e}")

# 5. Check Kraken connection
print("\n✅ STEP 5: Kraken Connection")
try:
    from kraken_client import KrakenClient
    kraken = KrakenClient(dry_run=False)
    balance = kraken.get_balance()
    print(f"  ✅ Kraken connected")
    print(f"  Balance: {balance}")
except Exception as e:
    print(f"  ❌ Kraken error: {e}")

# 6. Check if MIN_TRADE_USD is the blocker
print("\n✅ STEP 6: Trade Size Analysis")
print(f"  Balance: $74.83")
print(f"  MIN_TRADE_USD (likely): $5.00")
print(f"  Can trade? {74.83 >= 5.0} ✅")

# 7. Check if MIN_SCORE threshold is blocking trades
print("\n✅ STEP 7: Score Threshold")
print(f"  MIN_SCORE (from config): 60")
print(f"  Can opportunities reach 60? Need to test scoring...")

# 8. Run quick opportunity scan
print("\n✅ STEP 8: Opportunity Scan")
try:
    from aureon_unified_ecosystem import MultiExchangeOrchestrator
    multi = MultiExchangeClient(dry_run=False)
    orchestrator = MultiExchangeOrchestrator(multi)
    
    opportunities = orchestrator.scan_all_exchanges()
    print(f"  Total opportunities found: {sum(len(opps) for opps in opportunities.values())}")
    for ex, opps in opportunities.items():
        if opps:
            top_score = max(opp['score'] for opp in opps)
            print(f"    {ex.upper()}: {len(opps)} opportunities, top score: {top_score:.1f}")
except Exception as e:
    print(f"  ❌ Scan error: {e}")
    import traceback
    traceback.print_exc()

# 9. Check if there's a gate preventing trades
print("\n✅ STEP 9: Trade Gates")
print("  Checking CONFIG flags...")
try:
    from aureon_unified_ecosystem import CONFIG
    print(f"  DEPLOY_SCOUTS_IMMEDIATELY: {CONFIG.get('DEPLOY_SCOUTS_IMMEDIATELY', 'NOT SET')}")
    print(f"  MIN_SCORE: {CONFIG.get('MIN_SCORE', 'NOT SET')}")
    print(f"  MIN_VOLUME: {CONFIG.get('MIN_VOLUME', 'NOT SET')}")
    print(f"  MIN_MOMENTUM: {CONFIG.get('MIN_MOMENTUM', 'NOT SET')}")
    print(f"  ENTRY_COHERENCE: {CONFIG.get('ENTRY_COHERENCE', 'NOT SET')}")
except Exception as e:
    print(f"  ❌ Config error: {e}")

print("\n" + "="*60)
print("END DIAGNOSTICS")
print("="*60)
