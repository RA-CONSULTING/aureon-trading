#!/usr/bin/env python3
"""
🔍 MINIMAL TRADE TEST - Why aren't trades executing?
"""
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import time
sys.path.insert(0, '/workspaces/aureon-trading')

os.environ['LIVE'] = '1'  # Force LIVE mode

from aureon_unified_ecosystem import AureonKrakenEcosystem

print("="*70)
print("🔍 MINIMAL TRADE TEST")
print("="*70)

# Initialize ecosystem
ecosystem = AureonKrakenEcosystem(initial_balance=74.83, dry_run=False)

# Refresh tickers
print("\n✅ STEP 1: Refresh tickers")
count = ecosystem.refresh_tickers()
print(f"   Loaded {count} tickers")

# Refresh equity
print("\n✅ STEP 2: Refresh equity")
ecosystem.refresh_equity()
print(f"   Cash available: £{ecosystem.cash_balance_gbp:.2f}")
print(f"   Min trade: £{ecosystem.CONFIG['MIN_TRADE_USD']}")
print(f"   Can trade? {ecosystem.cash_balance_gbp >= ecosystem.CONFIG['MIN_TRADE_USD']}")

# Find opportunities
print("\n✅ STEP 3: Find opportunities")
all_opps = ecosystem.find_opportunities()
print(f"   Found {len(all_opps)} opportunities")

if all_opps:
    print(f"\n   Top 5:")
    for i, opp in enumerate(all_opps[:5], 1):
        print(f"      {i}. {opp['symbol']:12} | Score: {opp.get('score', 'N/A'):5} | Γ={opp['coherence']:.2f}")
else:
    print("   ❌ NO OPPORTUNITIES FOUND!")
    
    # Debug: Check why
    print("\n✅ STEP 3B: Debug why no opportunities")
    
    # Check filters
    print(f"   MIN_SCORE threshold: {ecosystem.CONFIG['MIN_SCORE']}")
    print(f"   MIN_MOMENTUM threshold: {ecosystem.CONFIG['MIN_MOMENTUM']}")
    print(f"   MIN_VOLUME threshold: {ecosystem.CONFIG['MIN_VOLUME']}")
    print(f"   ENTRY_COHERENCE threshold: {ecosystem.CONFIG['ENTRY_COHERENCE']}")
    
    # Sample some tickers and their filters
    sample_tickers = list(ecosystem.ticker_cache.items())[:10]
    print(f"\n   Checking first 10 tickers:")
    for symbol, data in sample_tickers:
        change = data['change24h']
        volume = data['volume']
        price = data['price']
        
        pass_momentum = change >= ecosystem.CONFIG['MIN_MOMENTUM'] and change <= ecosystem.CONFIG['MAX_MOMENTUM']
        pass_volume = volume >= ecosystem.CONFIG['MIN_VOLUME']
        pass_price = price >= 0.0001
        
        reasons = []
        if not pass_momentum:
            reasons.append(f"momentum={change:.1f}%")
        if not pass_volume:
            reasons.append(f"vol={volume:.0f}")
        if not pass_price:
            reasons.append(f"price={price}")
            
        status = "✅" if (pass_momentum and pass_volume and pass_price) else "❌"
        reason_str = " | ".join(reasons) if reasons else "OK"
        print(f"      {status} {symbol:12} | {reason_str}")

# Try to open position if opportunity exists
if all_opps:
    print("\n✅ STEP 4: Try to open position")
    best_opp = all_opps[0]
    print(f"   Opening position: {best_opp['symbol']}")
    result = ecosystem.open_position(best_opp)
    if result:
        print(f"   ✅ Position opened!")
        print(f"      {result}")
    else:
        print(f"   ❌ Position NOT opened (check console for gates)")
        
    # Check if position was actually created
    if best_opp['symbol'] in ecosystem.positions:
        print(f"   ✅ Position found in ecosystem.positions!")
    else:
        print(f"   ❌ Position NOT in ecosystem.positions!")
else:
    print("\n⚠️  SKIPPING STEP 4: No opportunities to trade")

# Check final state
print("\n✅ STEP 5: Final state check")
print(f"   Total positions: {len(ecosystem.positions)}")
print(f"   Total trades: {ecosystem.tracker.total_trades}")
print(f"   Dry run mode: {ecosystem.dry_run}")

print("\n" + "="*70)
print("END TEST")
print("="*70)
