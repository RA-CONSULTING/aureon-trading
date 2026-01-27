#!/usr/bin/env python3
"""Quick test to verify the fallback ticker system works"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os

sys.path.insert(0, '/workspaces/aureon-trading')
os.chdir('/workspaces/aureon-trading')

from aureon_unified_ecosystem import AureonKrakenEcosystem

print("Testing fallback ticker system...")
print("="*70)

# Create ecosystem instance
eco = AureonKrakenEcosystem(initial_balance=74.83, dry_run=False)

print(f"\n1. Initial ticker cache: {len(eco.ticker_cache)} symbols")

# Try refresh
print(f"\n2. Calling refresh_tickers()...")
count = eco.refresh_tickers()
print(f"   Result: {count} symbols loaded")
print(f"   Cache size: {len(eco.ticker_cache)}")

if eco.ticker_cache:
    print(f"\n3. First 5 symbols in cache:")
    for i, (sym, data) in enumerate(list(eco.ticker_cache.items())[:5]):
        print(f"   {i+1}. {sym}: ${data.get('price', 0):.2f}, change: {data.get('change24h', 0):.1f}%")
else:
    print("\n❌ Ticker cache is EMPTY!")
    sys.exit(1)

# Try to find opportunities
print(f"\n4. Calling find_opportunities()...")
opps = eco.find_opportunities()
print(f"   Found: {len(opps)} opportunities")

if opps:
    print(f"\n5. Top 5 opportunities:")
    for i, opp in enumerate(sorted(opps, key=lambda x: -x.get('score', 0))[:5]):
        print(f"   {i+1}. {opp['symbol']:10s} Score: {opp.get('score', 0):.1f}, Coherence: {opp.get('coherence', 0):.2f}")
else:
    print("\n⚠️ No opportunities found!")

print("\n" + "="*70)
print("✅ Test complete")
