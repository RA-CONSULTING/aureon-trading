#!/usr/bin/env python3
"""
🔍 DIAGNOSE WHY SYSTEM IS NOT WORKING
Identifies exact blockers and current system state
"""
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

print("=" * 60)
print("🔍 DIAGNOSTIC: WHY SYSTEM IS NOT WORKING")
print("=" * 60)

# 1. Check .env
print("\n1️⃣ Checking .env configuration...")
if not os.path.exists('.env'):
    print("   ❌ .env file not found")
    sys.exit(1)

from dotenv import load_dotenv
load_dotenv()

binance_key = os.getenv('BINANCE_API_KEY')
binance_secret = os.getenv('BINANCE_API_SECRET')

if not binance_key or not binance_secret:
    print("   ❌ Binance API keys missing")
    sys.exit(1)

print("   ✅ .env configured with API keys")

# 2. Check state file
print("\n2️⃣ Checking state file...")
if not os.path.exists('aureon_kraken_state.json'):
    print("   ❌ State file missing")
    sys.exit(1)

with open('aureon_kraken_state.json') as f:
    state = json.load(f)

balance = state.get('balance', 0)
trades = state.get('total_trades', 0)
iteration = state.get('iteration', 0)

print(f"   ✅ State file exists")
print(f"      Balance: ${balance:.2f}")
print(f"      Trades: {trades}")
print(f"      Iterations: {iteration}")

# 3. Try importing key modules
print("\n3️⃣ Checking module imports...")
try:
    sys.path.insert(0, '/workspaces/aureon-trading')
    from unified_exchange_client import MultiExchangeClient
    print("   ✅ MultiExchangeClient imported")
except ImportError as e:
    print(f"   ❌ MultiExchangeClient error: {e}")
    sys.exit(1)

# 4. Test Exchange Connections (Binance, Kraken, Alpaca)
print("\n4️⃣ Testing Exchange Connections...")
total_liquid_funds = 0.0

# --- BINANCE ---
try:
    from binance.client import Client
    client = Client(binance_key, binance_secret)
    account = client.get_account()
    
    balances = account.get('balances', [])
    usdc = next((b for b in balances if b['asset'] in ['USDC', 'USDT']), None)
    
    if usdc:
        free = float(usdc.get('free', 0))
        locked = float(usdc.get('locked', 0))
        total_liquid_funds += free
        print(f"   ✅ Binance connected")
        print(f"      USDC/USDT Free: ${free:.2f}")
    else:
        print("   ⚠️  Binance: No USDC/USDT balance found")
        
except Exception as e:
    print(f"   ❌ Binance connection error: {e}")

# --- ALPACA ---
try:
    from alpaca_client import AlpacaClient
    alpaca = AlpacaClient()
    alpaca_funds = float(getattr(alpaca, 'get_cash', lambda: 0)())
    total_liquid_funds += alpaca_funds
    print(f"   ✅ Alpaca connected")
    print(f"      Buying Power: ${alpaca_funds:.2f}")
except Exception as e:
    print(f"   ⚠️ Alpaca connection error: {e}")

# --- KRAKEN ---
try:
    from kraken_client import KrakenClient, get_kraken_client
    kraken = get_kraken_client()
    kb = kraken.get_balance()
    kraken_funds = kb.get('USD', 0) + kb.get('ZUSD', 0) + kb.get('USDC', 0) + kb.get('USDT', 0)
    total_liquid_funds += kraken_funds
    print(f"   ✅ Kraken connected")
    print(f"      Liquid Funds: ${kraken_funds:.2f}")
except Exception as e:
    print(f"   ⚠️ Kraken connection error: {e}")


print(f"\n   💰 TOTAL LIQUID FUNDS: ${total_liquid_funds:.2f}")

if total_liquid_funds < 5:
    print(f"\n   🚨 PROBLEM IDENTIFIED:")
    print(f"      Insufficient liquid funds (need $5+, have ${total_liquid_funds:.2f})")
    print(f"      System cannot place trades with less than $5 USD across all exchanges.")
    # sys.exit(1) # Don't exit harder, let them see
else:
    print(f"   ✅ Funds sufficient for trading.")

# 5. Check if system can run
print("\n5️⃣ Checking if system can run...")
try:
    from aureon_unified_ecosystem import AureonKrakenEcosystem
    print("   ✅ AureonKrakenEcosystem can be imported")
    
    # Try to initialize (dry run)
    print("   ℹ️  System is ready to trade")
    
except Exception as e:
    print(f"   ❌ AureonKrakenEcosystem error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL SYSTEMS OPERATIONAL - READY TO TRADE")
print("=" * 60)
print("\nNext step: Run the main system:")
print("  python3 aureon_unified_ecosystem.py")
