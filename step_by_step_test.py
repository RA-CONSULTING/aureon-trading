#!/usr/bin/env python3
"""
Minimal test - Import each component step by step
"""
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import traceback

sys.path.insert(0, '/workspaces/aureon-trading')
os.chdir('/workspaces/aureon-trading')

print("Step-by-step import test:\n")

# Step 1
try:
    print("1. Importing dotenv...")
    from dotenv import load_dotenv
    load_dotenv()
    print("   ✅ SUCCESS\n")
except Exception as e:
    print(f"   ❌ FAILED: {e}\n")
    traceback.print_exc()
    sys.exit(1)

# Step 2
try:
    print("2. Importing binance_client...")
    from binance_client import BinanceClient
    print("   ✅ SUCCESS\n")
except Exception as e:
    print(f"   ❌ FAILED: {e}\n")
    traceback.print_exc()
    sys.exit(1)

# Step 3
try:
    print("3. Importing kraken_client...")
    from kraken_client import KrakenClient
    print("   ✅ SUCCESS\n")
except Exception as e:
    print(f"   ❌ FAILED: {e}\n")
    traceback.print_exc()
    sys.exit(1)

# Step 4
try:
    print("4. Importing alpaca_client...")
    from alpaca_client import AlpacaClient
    print("   ✅ SUCCESS\n")
except Exception as e:
    print(f"   ❌ FAILED: {e}\n")
    traceback.print_exc()
    sys.exit(1)

# Step 5
try:
    print("5. Importing capital_client...")
    from capital_client import CapitalClient
    print("   ✅ SUCCESS\n")
except Exception as e:
    print(f"   ❌ FAILED: {e}\n")
    traceback.print_exc()
    sys.exit(1)

# Step 6
try:
    print("6. Importing unified_exchange_client...")
    from unified_exchange_client import UnifiedExchangeClient, MultiExchangeClient
    print("   ✅ SUCCESS\n")
except Exception as e:
    print(f"   ❌ FAILED: {e}\n")
    traceback.print_exc()
    sys.exit(1)

# Step 7 - THE BIG ONE
try:
    print("7. Importing aureon_unified_ecosystem...")
    print("   (This may take a moment...)\n")
    from aureon_unified_ecosystem import AureonKrakenEcosystem
    print("   ✅ SUCCESS\n")
except Exception as e:
    print(f"   ❌ FAILED: {e}\n")
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)

# Step 8
try:
    print("8. Creating AureonKrakenEcosystem instance...")
    ecosystem = AureonKrakenEcosystem(initial_balance=100.0, dry_run=True)
    print("   ✅ SUCCESS\n")
except Exception as e:
    print(f"   ❌ FAILED: {e}\n")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*70)
print("✅ ALL STEPS PASSED - SYSTEM IS OPERATIONAL")
print("="*70)
print("\nYou can now run:")
print("  python3 aureon_unified_ecosystem.py")
print("\nOr with LIVE mode:")
print("  LIVE=1 python3 aureon_unified_ecosystem.py")
