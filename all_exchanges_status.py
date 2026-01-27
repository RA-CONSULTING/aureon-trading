#!/usr/bin/env python3
"""
COMPREHENSIVE ACCOUNT STATUS - ALL EXCHANGES
Check which exchanges have liquid funds available for trading
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
from dotenv import load_dotenv

load_dotenv()

print("\n" + "="*70)
print("🌐 AUREON ECOSYSTEM - MULTI-EXCHANGE FUNDING STATUS")
print("="*70 + "\n")

# Check Binance
print("1️⃣  BINANCE (Crypto)")
print("-" * 70)
try:
    from binance.client import Client
    client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
    account = client.get_account()
    
    liquid = 0
    for b in account['balances']:
        amt = float(b['free'])
        if amt > 0.01 and b['asset'] in ['USDT', 'USDC', 'BUSD']:
            print(f"   ✅ {b['asset']}: ${amt:.2f}")
            liquid += amt
    
    if liquid < 10:
        print(f"   ❌ Total liquid: ${liquid:.2f} (Need $10+)")
    else:
        print(f"   ✅ Total liquid: ${liquid:.2f} - READY TO TRADE")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()

# Check Kraken
print("2️⃣  KRAKEN (Crypto + Forex)")
print("-" * 70)
try:
    import krakenex
    api = krakenex.API()
    api.load_key(os.path.expanduser('~/.kraken/kraken.key'))
    result = api.query_private('Balance')
    
    if 'error' in result and result['error']:
        print(f"   ⚠️  API Error: {result['error']}")
    else:
        liquid = 0
        for asset, amt in result.get('result', {}).items():
            amt = float(amt)
            clean = asset.replace('X', '').replace('Z', '')
            if amt > 0.01 and clean in ['USD', 'GBP', 'EUR', 'USDT', 'USDC']:
                print(f"   ✅ {clean}: ${amt:.2f}" if clean != 'EUR' else f"   ✅ {clean}: €{amt:.2f}")
                liquid += amt
        
        if liquid < 5:
            print(f"   ❌ Total liquid: ${liquid:.2f} (Need $5+)")
        else:
            print(f"   ✅ Total liquid: ${liquid:.2f} - READY TO TRADE")
except FileNotFoundError:
    print("   ⚠️  Kraken API key not configured (~/.kraken/kraken.key)")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()

# Check Capital.com
print("3️⃣  CAPITAL.COM (CFD/Forex)")
print("-" * 70)
try:
    from capital_client import CapitalClient
    capital = CapitalClient(os.getenv('CAPITAL_USER'), os.getenv('CAPITAL_PASSWORD'))
    balance = capital.get_account_info()
    
    if balance:
        available = balance.get('availableCash', 0)
        print(f"   💰 Available balance: ${available:.2f}")
        if available > 10:
            print(f"   ✅ READY TO TRADE")
        else:
            print(f"   ❌ Need $10+")
except Exception as e:
    print(f"   ⚠️  Not configured or error: {e}")

print()

# Check Alpaca
print("4️⃣  ALPACA (Stocks - Analytics Only)")
print("-" * 70)
try:
    from alpaca.trading.client import TradingClient
    client = TradingClient(os.getenv('APCA_API_KEY_ID'))
    account = client.get_account()
    
    cash = float(account.cash)
    print(f"   💰 Available cash: ${cash:.2f}")
    if cash > 1:
        print(f"   ⚠️  ANALYTICS ONLY - Not trading stocks")
    else:
        print(f"   ❌ No funds")
except Exception as e:
    print(f"   ⚠️  Not configured or error: {e}")

print()
print("="*70)
print("SYSTEM STATUS")
print("="*70)
print("""
The AUREON ECOSYSTEM is configured to trade on:
  • Binance (Min: $10 USDT/USDC)
  • Kraken (Min: $5 USD/GBP/EUR)
  • Capital.com (Min: $10 USD)
  • Alpaca (Analytics only - no trading)

⚠️  PROBLEM: Your accounts don't have LIQUID funds
    - Binance: Has ~$87 but in LDUSDC (STAKED - not tradable)
    - Kraken: Unknown (check above)
    - Capital: Unknown (check above)

✅ SOLUTION:
   1. Unstake LDUSDC on Binance Earn → Get liquid USDC
   2. Or deposit $10+ USDT directly to Binance Spot
   3. Or check/fund Kraken or Capital accounts
   
Once you have liquid funds on ANY exchange, the system WILL trade automatically.
""")
