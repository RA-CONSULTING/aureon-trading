#!/usr/bin/env python3
"""
Direct check - what is ACTUALLY wrong with the trading system?
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import json
from datetime import datetime

print("=== AUREON ECOSYSTEM DIAGNOSTIC ===\n")

# 1. Check what's actually configured to run
print("1. CHECKING CONFIGURATION:")
print(f"   LIVE mode: {os.getenv('LIVE', 'NOT SET')}")
print(f"   EXCHANGE: {os.getenv('EXCHANGE', 'NOT SET')}")
print(f"   DRY_RUN: {os.getenv('DRY_RUN', 'NOT SET')}")
print(f"   BASE_CURRENCY: {os.getenv('BASE_CURRENCY', 'NOT SET')}")
print()

# 2. Check state file
print("2. CHECKING STATE FILE:")
try:
    with open('aureon_kraken_state.json', 'r') as f:
        state = json.load(f)
    print(f"   ✅ State file loaded")
    print(f"   Balance: {state.get('balance', 0)}")
    print(f"   Total trades: {state.get('total_trades', 0)}")
    print(f"   Iteration: {state.get('iteration', 0)}")
    print(f"   Active positions: {len(state.get('positions', {}))}")
    print(f"   Last update: {state.get('last_update', 'never')}")
    
    if state.get('total_trades', 0) == 0 and state.get('iteration', 0) > 0:
        print("   ⚠️  PROBLEM: System has run but placed NO trades")
except FileNotFoundError:
    print("   ❌ State file not found - system never started")
except Exception as e:
    print(f"   ❌ Error reading state: {e}")
print()

# 3. Check if APIs are configured
print("3. CHECKING API KEYS:")
api_keys = {
    'BINANCE_API_KEY': os.getenv('BINANCE_API_KEY'),
    'BINANCE_API_SECRET': os.getenv('BINANCE_API_SECRET'),
    'KRAKEN_API_KEY': os.getenv('KRAKEN_API_KEY'),
    'KRAKEN_API_SECRET': os.getenv('KRAKEN_API_SECRET'),
}

for key, value in api_keys.items():
    if value:
        print(f"   ✅ {key}: configured ({len(value)} chars)")
    else:
        print(f"   ❌ {key}: NOT SET")
print()

# 4. Test import of main system
print("4. TESTING SYSTEM IMPORTS:")
try:
    sys.path.insert(0, '/workspaces/aureon-trading')
    from aureon_unified_ecosystem import AureonKrakenEcosystem, CONFIG
    print("   ✅ Main ecosystem imports successfully")
    print(f"   MIN_SCORE configured: {CONFIG.get('MIN_SCORE', 'not set')}")
    print(f"   MIN_MOMENTUM configured: {CONFIG.get('MIN_MOMENTUM', 'not set')}")
    print(f"   FORCE_TRADE mode: {CONFIG.get('FORCE_TRADE', False)}")
    print(f"   DEPLOY_SCOUTS_IMMEDIATELY: {CONFIG.get('DEPLOY_SCOUTS_IMMEDIATELY', False)}")
except ImportError as e:
    print(f"   ❌ Import error: {e}")
except SyntaxError as e:
    print(f"   ❌ Syntax error in ecosystem: {e}")
print()

# 5. Quick Binance balance check
print("5. CHECKING ACTUAL BINANCE BALANCE:")
try:
    from binance.client import Client
    from dotenv import load_dotenv
    load_dotenv()
    
    client = Client(
        os.getenv('BINANCE_API_KEY'),
        os.getenv('BINANCE_API_SECRET')
    )
    
    account = client.get_account()
    liquid_total = 0
    staked_total = 0
    
    for balance in account['balances']:
        free = float(balance['free'])
        locked = float(balance['locked'])
        total = free + locked
        
        if total > 0.01:
            asset = balance['asset']
            if asset in ['USDT', 'USDC', 'BUSD', 'FDUSD']:
                print(f"   ✅ {asset}: ${total:.2f} LIQUID")
                liquid_total += total
            elif asset.startswith('LD'):
                print(f"   🔒 {asset}: ${total:.2f} STAKED (not tradable)")
                staked_total += total
            else:
                if total > 1:
                    print(f"   📦 {asset}: {total:.8f}")
    
    print(f"\n   💰 LIQUID STABLECOINS: ${liquid_total:.2f}")
    print(f"   🔒 STAKED ASSETS: ${staked_total:.2f}")
    
    if liquid_total < 10:
        print(f"\n   ❌ INSUFFICIENT LIQUID FUNDS FOR TRADING")
        print(f"   Need at least $10, you have ${liquid_total:.2f}")
        if staked_total > 0:
            print(f"\n   💡 You have ${staked_total:.2f} staked - UNSTAKE IT!")
            print("   Steps:")
            print("   1. Go to Binance → Earn → Simple Earn")
            print("   2. Click 'Redeem' on your staked assets")
            print("   3. Wait 1-2 minutes for settlement")
        exit(1)
    else:
        print(f"\n   ✅ SUFFICIENT FUNDS TO TRADE")
        
except Exception as e:
    print(f"   ❌ Binance check failed: {e}")
    import traceback
    traceback.print_exc()
print()

print("=== DIAGNOSTIC COMPLETE ===")
