import os
import sys
import time
import traceback
from binance_client import BinanceClient
from kraken_client import KrakenClient
from alpaca_client import AlpacaClient

print("=" * 80)
print("🔍 EXCHANGE DIAGNOSTIC TOOL")
print("=" * 80)

# 1. BINANCE CHECK
print("\n🟡 CHECKING BINANCE...")
try:
    b = BinanceClient()
    print(f"   API Key: {b.api_key[:4]}...{b.api_key[-4:]}")
    print(f"   Testnet: {b.use_testnet}")
    print(f"   Dry Run: {b.dry_run}")
    print(f"   UK Mode: {b.uk_mode}")
    
    # Check time sync
    print(f"   Time Offset: {b._time_offset_ms}ms")
    
    # Check balances
    print("   Requesting account info...")
    try:
        info = b.account()
        print(f"   Account Type: {info.get('accountType', 'Unknown')}")
        print(f"   Can Trade: {info.get('canTrade', False)}")
        print(f"   Permissions: {info.get('permissions', [])}")
        
        balances = info.get('balances', [])
        found_assets = 0
        for bal in balances:
            free = float(bal.get('free', 0))
            locked = float(bal.get('locked', 0))
            if free > 0 or locked > 0:
                print(f"   💰 {bal['asset']}: Free={free}, Locked={locked}")
                found_assets += 1
        
        if found_assets == 0:
            print("   ⚠️ No positive balances found on Binance.")
            
    except Exception as e:
        print(f"   ❌ BINANCE ACCOUNT ERROR: {e}")
        traceback.print_exc()

except Exception as e:
    print(f"   ❌ BINANCE INIT ERROR: {e}")
    traceback.print_exc()

# 2. KRAKEN CHECK
print("\n🐙 CHECKING KRAKEN...")
try:
    k = KrakenClient()
    print(f"   API Key: {k.api_key[:4]}...{k.api_key[-4:]}")
    print(f"   Dry Run: {k.dry_run}")
    
    # Check balances
    print("   Requesting balances...")
    try:
        balances = k.get_account_balance()
        if balances:
            for asset, amount in balances.items():
                print(f"   💰 {asset}: {amount}")
        else:
            print("   ⚠️ No balances returned from Kraken.")
    except Exception as e:
        print(f"   ❌ KRAKEN BALANCE ERROR: {e}")
        traceback.print_exc()

except Exception as e:
    print(f"   ❌ KRAKEN INIT ERROR: {e}")
    traceback.print_exc()

# 3. ALPACA CHECK
print("\n🦙 CHECKING ALPACA...")
try:
    a = AlpacaClient()
    print(f"   API Key: {a.api_key[:4]}...{a.api_key[-4:]}")
    print(f"   Paper: {a.use_paper}")
    
    # Check account
    print("   Requesting account...")
    try:
        acc = a.get_account()
        print(f"   Status: {acc.get('status')}")
        print(f"   Cash: ${acc.get('cash')}")
        print(f"   Buying Power: ${acc.get('buying_power')}")
    except Exception as e:
        print(f"   ❌ ALPACA ACCOUNT ERROR: {e}")
        traceback.print_exc()
    
except Exception as e:
    print(f"   ❌ ALPACA INIT ERROR: {e}")
    traceback.print_exc()

print("\n" + "=" * 80)
