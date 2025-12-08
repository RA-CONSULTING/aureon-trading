#!/usr/bin/env python3
"""
Check logs and diagnose the error in aureon_unified_ecosystem.py
"""
import os
import sys
import json
import traceback

print("\n" + "="*70)
print("🔍 CHECKING SYSTEM LOGS AND ERRORS")
print("="*70 + "\n")

# Try importing and see what error occurs
sys.path.insert(0, '/workspaces/aureon-trading')

print("1️⃣ Testing core imports...")
print("-"*70)

try:
    from dotenv import load_dotenv
    print("   ✅ dotenv")
    load_dotenv()
except Exception as e:
    print(f"   ❌ dotenv: {e}")
    sys.exit(1)

try:
    from binance.client import Client
    print("   ✅ binance.client")
except Exception as e:
    print(f"   ❌ binance.client: {e}")
    sys.exit(1)

try:
    import krakenex
    print("   ✅ krakenex")
except Exception as e:
    print(f"   ❌ krakenex: {e}")
    sys.exit(1)

try:
    from unified_exchange_client import MultiExchangeClient
    print("   ✅ unified_exchange_client.MultiExchangeClient")
except Exception as e:
    print(f"   ❌ unified_exchange_client: {e}")
    print(f"      {traceback.format_exc()}")
    sys.exit(1)

print("\n2️⃣ Testing aureon_unified_ecosystem import...")
print("-"*70)

try:
    from aureon_unified_ecosystem import AureonKrakenEcosystem
    print("   ✅ aureon_unified_ecosystem.AureonKrakenEcosystem")
except Exception as e:
    print(f"   ❌ aureon_unified_ecosystem: {e}")
    print(f"\nFull traceback:")
    print(traceback.format_exc())
    sys.exit(1)

print("\n3️⃣ Checking Binance API connection...")
print("-"*70)

try:
    key = os.getenv('BINANCE_API_KEY')
    secret = os.getenv('BINANCE_API_SECRET')
    
    if not key or not secret:
        print("   ❌ Missing API keys in .env")
        sys.exit(1)
    
    client = Client(key, secret)
    account = client.get_account()
    
    balances = account.get('balances', [])
    usdc = next((b for b in balances if b['asset'] in ['USDC', 'USDT']), None)
    
    if usdc:
        free = float(usdc.get('free', 0))
        print(f"   ✅ Binance connected")
        print(f"      USDC/USDT Free: ${free:.2f}")
        
        if free < 5:
            print(f"\n   ⚠️  WARNING: Low funds (${free:.2f})")
        else:
            print(f"      ✅ Sufficient for trading")
    else:
        print(f"   ⚠️  No USDC/USDT found")
        
except Exception as e:
    print(f"   ❌ Binance error: {e}")
    print(traceback.format_exc())
    sys.exit(1)

print("\n4️⃣ Checking state file...")
print("-"*70)

if os.path.exists('aureon_kraken_state.json'):
    with open('aureon_kraken_state.json') as f:
        state = json.load(f)
    print(f"   ✅ State file exists")
    print(f"      Balance: ${state.get('balance', 0):.2f}")
    print(f"      Trades: {state.get('total_trades', 0)}")
    print(f"      Iteration: {state.get('iteration', 0)}")
else:
    print(f"   ℹ️  State file will be created on first run")

print("\n5️⃣ Testing system initialization...")
print("-"*70)

try:
    ecosystem = AureonKrakenEcosystem()
    print(f"   ✅ AureonKrakenEcosystem initialized")
    print(f"      LIVE: {ecosystem.LIVE}")
    print(f"      DRY_RUN: {ecosystem.DRY_RUN}")
except Exception as e:
    print(f"   ❌ Initialization error: {e}")
    print(f"\nFull traceback:")
    print(traceback.format_exc())
    sys.exit(1)

print("\n" + "="*70)
print("✅ ALL SYSTEMS OPERATIONAL")
print("="*70)
print("\nYou can now run:")
print("  python3 aureon_unified_ecosystem.py")
print("\n")
