#!/usr/bin/env python3
"""
Force Trade Test - Find out WHY no trades are executing
"""
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
from dotenv import load_dotenv
load_dotenv()

import os
import sys
sys.path.insert(0, '/workspaces/aureon-trading')

print("=" * 60)
print("🔥 FORCE TRADE TEST - Finding the blocker")
print("=" * 60)

# 1. Test Binance balance
print("\n1️⃣ Checking Binance Balance...")
try:
    from binance_client import BinanceClient
    client = BinanceClient()
    
    print("   Checking liquid stablecoins:")
    liquid_total = 0
    for asset in ['USDT', 'USDC', 'BUSD', 'FDUSD']:
        try:
            bal = client.get_balance(asset)
            if bal > 0:
                print(f"   ✅ {asset}: ${bal:.2f}")
                liquid_total += bal
        except Exception as e:
            print(f"   ⚠️  {asset}: Error - {e}")
    
    if liquid_total == 0:
        print(f"\n   ❌ PROBLEM: NO LIQUID FUNDS (Total: ${liquid_total:.2f})")
        print("   Checking for staked funds...")
        try:
            ldusdc = client.get_balance('LDUSDC')
            if ldusdc > 0:
                print(f"   🔒 LDUSDC (STAKED): ${ldusdc:.2f}")
                print("\n   💡 SOLUTION:")
                print("   1. Open Binance App/Website")
                print("   2. Go to: Earn → Simple Earn → Flexible Products")
                print("   3. Find LDUSDC → Click 'Redeem'")
                print("   4. Convert to USDC")
                print("   5. Wait 1-2 minutes for settlement")
                print("   6. Run system again")
                sys.exit(1)
        except:
            pass
        print("\n   ❌ CANNOT TRADE: Need at least $5 USDT or USDC")
        sys.exit(1)
    else:
        print(f"\n   ✅ Total Liquid Funds: ${liquid_total:.2f}")

except Exception as e:
    print(f"   ❌ Binance Error: {e}")
    sys.exit(1)

# 2. Test getting tickers
print("\n2️⃣ Checking Market Data...")
try:
    from unified_exchange_client import MultiExchangeClient
    multi_client = MultiExchangeClient()
    tickers = multi_client.get_24h_tickers()
    print(f"   ✅ Got {len(tickers)} tickers")
    
    if len(tickers) < 10:
        print(f"   ⚠️  Only {len(tickers)} tickers - this seems low")
    
    # Show a sample
    if tickers:
        sample = tickers[0]
        print(f"   Sample: {sample.get('symbol')} @ ${sample.get('lastPrice', 'N/A')}")
        
except Exception as e:
    print(f"   ❌ Market Data Error: {e}")

# 3. Test opportunity evaluation
print("\n3️⃣ Testing Opportunity Evaluation...")
try:
    # Get a simple ticker
    if tickers:
        test_ticker = None
        for t in tickers:
            if t.get('symbol', '').endswith('USDT'):
                test_ticker = t
                break
        
        if test_ticker:
            symbol = test_ticker['symbol']
            price = float(test_ticker.get('lastPrice', 0))
            change = float(test_ticker.get('priceChangePercent', 0))
            volume = float(test_ticker.get('quoteVolume', 0))
            
            print(f"   Testing: {symbol}")
            print(f"   Price: ${price:.2f} | Change: {change:+.2f}% | Vol: ${volume:,.0f}")
            
            # Check against filters
            MIN_VOLUME = 50000
            MIN_MOMENTUM = 0.5
            
            if volume < MIN_VOLUME:
                print(f"   ❌ FILTERED: Volume ${volume:,.0f} < ${MIN_VOLUME:,.0f}")
            elif abs(change) < MIN_MOMENTUM:
                print(f"   ❌ FILTERED: Momentum {abs(change):.2f}% < {MIN_MOMENTUM}%")
            else:
                print(f"   ✅ Passed basic filters")
                
except Exception as e:
    print(f"   ⚠️  Eval Error: {e}")

# 4. Show system configuration
print("\n4️⃣ System Configuration:")
print(f"   LIVE Mode: {os.getenv('LIVE', '0')}")
print(f"   Base Currency: {os.getenv('BASE_CURRENCY', 'USD')}")
print(f"   Exchange: {os.getenv('EXCHANGE', 'both')}")
print(f"   Min Trade: $5.00")
print(f"   Scout Deploy: IMMEDIATE (3 forced)")

print("\n" + "=" * 60)
print("🎯 TEST COMPLETE")
print("=" * 60)

# Summary
if liquid_total >= 5:
    print("\n✅ System SHOULD be able to trade")
    print("Next steps:")
    print("1. Run: python3 aureon_unified_ecosystem.py")
    print("2. Watch for 'DEPLOY_SCOUTS' or 'BUY' messages")
    print("3. If no trades after 1 minute, check MIN_SCORE threshold")
else:
    print("\n❌ System CANNOT trade - insufficient liquid funds")
