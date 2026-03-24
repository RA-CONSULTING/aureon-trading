#!/usr/bin/env python3
"""Debug ticker and opportunity issue"""
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import json
sys.path.insert(0, '/workspaces/aureon-trading')

print("=" * 70)
print("🔍 COMPREHENSIVE TICKER & OPPORTUNITY DEBUG")
print("=" * 70)

# 1. Check environment
print("\n✅ STEP 1: Environment Setup")
os.environ['LIVE'] = '1'
print(f"   LIVE = {os.environ.get('LIVE')}")
print(f"   DRY_RUN = {os.environ.get('DRY_RUN', 'NOT SET')}")

# 2. Check imports
print("\n✅ STEP 2: Loading Core Modules")
try:
    from unified_exchange_client import MultiExchangeClient
    print("   ✅ unified_exchange_client")
except Exception as e:
    print(f"   ❌ {e}")
    sys.exit(1)

# 3. Initialize client
print("\n✅ STEP 3: Initialize MultiExchangeClient")
try:
    multi = MultiExchangeClient(dry_run=False)
    print(f"   ✅ Clients: {list(multi.clients.keys())}")
except Exception as e:
    print(f"   ❌ {e}")
    sys.exit(1)

# 4. Get tickers
print("\n✅ STEP 4: Fetch Tickers")
try:
    tickers = multi.get_24h_tickers()
    print(f"   ✅ Got {len(tickers)} tickers")
    if tickers:
        print(f"\n   Sample tickers:")
        for t in tickers[:10]:
            sym = t.get('symbol', 'N/A')
            price = t.get('lastPrice', 0)
            change = t.get('priceChangePercent', 0)
            volume = t.get('quoteVolume', 0)
            print(f"      {sym:12s} ${price:10.6f} {change:+6.2f}% Vol: {volume:12.0f}")
    else:
        print("   ❌ NO TICKERS RETURNED!")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 5. Try to run AureonKrakenEcosystem briefly
print("\n✅ STEP 5: Initialize AureonKrakenEcosystem")
try:
    from aureon_unified_ecosystem import AureonKrakenEcosystem, CONFIG
    
    eco = AureonKrakenEcosystem(initial_balance=74.83, dry_run=False)
    print(f"   ✅ Ecosystem initialized")
    print(f"   Cash balance: ${eco.cash_balance_gbp:.2f}")
    print(f"   MIN_TRADE_USD: ${CONFIG['MIN_TRADE_USD']}")
    print(f"   MIN_SCORE: {CONFIG['MIN_SCORE']}")
    print(f"   ENTRY_COHERENCE: {CONFIG['ENTRY_COHERENCE']}")
    
    # Refresh tickers
    print("\n✅ STEP 6: Refresh Tickers in Ecosystem")
    count = eco.refresh_tickers()
    print(f"   ✅ Loaded {count} tickers into ecosystem cache")
    
    # Find opportunities
    print("\n✅ STEP 7: Find Opportunities")
    opps = eco.find_opportunities()
    print(f"   ✅ Found {len(opps)} opportunities")
    
    if opps:
        print(f"\n   Top 5 opportunities:")
        for opp in opps[:5]:
            sym = opp['symbol']
            score = opp['score']
            coh = opp['coherence']
            change = opp['change24h']
            print(f"      {sym:12s} Score: {score:6.1f} Γ: {coh:.2f} {change:+6.2f}%")
    else:
        print("   ⚠️ NO OPPORTUNITIES FOUND")
        print("\n   Checking why...")
        if not eco.ticker_cache:
            print("   → ticker_cache is EMPTY")
        else:
            print(f"   → ticker_cache has {len(eco.ticker_cache)} symbols")
            # Check first symbol for filtering
            first_sym = list(eco.ticker_cache.keys())[0]
            data = eco.ticker_cache[first_sym]
            print(f"\n   Example ticker: {first_sym}")
            print(f"      price: {data.get('price')}")
            print(f"      change24h: {data.get('change24h')}")
            print(f"      volume: {data.get('volume')}")
            print(f"      source: {data.get('source')}")
            
            # Check why it was filtered
            change = data['change24h']
            price = data['price']
            volume = data['volume']
            print(f"\n   Filtering checks for {first_sym}:")
            print(f"      MIN_MOMENTUM ({CONFIG['MIN_MOMENTUM']}): {change:.2f} >= {CONFIG['MIN_MOMENTUM']} ? {change >= CONFIG['MIN_MOMENTUM']}")
            print(f"      MAX_MOMENTUM ({CONFIG['MAX_MOMENTUM']}): {change:.2f} <= {CONFIG['MAX_MOMENTUM']} ? {change <= CONFIG['MAX_MOMENTUM']}")
            print(f"      MIN_VOLUME ({CONFIG['MIN_VOLUME']}): {volume:.0f} >= {CONFIG['MIN_VOLUME']} ? {volume >= CONFIG['MIN_VOLUME']}")
            print(f"      price check: {price:.6f} >= 0.0001 ? {price >= 0.0001}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ DEBUG COMPLETE")
print("=" * 70)
