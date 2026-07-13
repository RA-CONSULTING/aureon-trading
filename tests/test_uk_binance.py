#!/usr/bin/env python3
"""Quick test for UK Binance handling."""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import asyncio
import os
import sys
from pathlib import Path
os.chdir(Path(__file__).resolve().parents[1])

from micro_profit_labyrinth import MicroProfitLabyrinth

async def main():
    print("=" * 60)
    print("🇬🇧 UK BINANCE RESTRICTION TEST")
    print("=" * 60)
    
    labyrinth = MicroProfitLabyrinth(live=False)
    await labyrinth.initialize()
    
    # Show UK pairs status
    print(f'\n🇬🇧 UK Mode: {labyrinth.binance_uk_mode}')
    print(f'   Cached pairs: {len(labyrinth.binance_uk_allowed_pairs)}')
    
    # Test some pairs
    test_pairs = ['BTCUSDC', 'ETHUSDC', 'SOLUSDC', 'BTCUSDT', 'ETHUSDT']
    print('\n   Testing pair access:')
    for pair in test_pairs:
        allowed = labyrinth.is_binance_pair_allowed(pair)
        status = "✅ Allowed" if allowed else "❌ Blocked"
        print(f'      {pair}: {status}')
    
    # Fetch data
    print('\n📊 Fetching prices...')
    await labyrinth.fetch_prices()
    print(f'   {len(labyrinth.prices)} assets priced')
    print(f'   {len(labyrinth.ticker_cache)} pairs in ticker cache')
    
    # Check if USDC pairs are in ticker_cache
    print('\n🟡 Binance USDC pairs in ticker_cache:')
    usdc_pairs = [k for k in labyrinth.ticker_cache.keys() if 'binance:' in k and 'USDC' in k]
    print(f'   Found {len(usdc_pairs)} USDC pairs')
    for p in sorted(usdc_pairs)[:10]:
        print(f'      {p}')
    
    # Fetch balances
    print('\n📊 Fetching balances...')
    await labyrinth.fetch_balances()
    
    # Show Binance balance
    binance_bal = labyrinth.exchange_balances.get('binance', {})
    print(f'\n🟡 Binance Balances: {binance_bal}')
    
    # Find opportunities for Binance only
    print('\n🔍 Finding Binance opportunities...')
    opps = await labyrinth.find_opportunities_for_exchange('binance')
    print(f'\n✅ Found {len(opps)} opportunities')
    
    for opp in opps[:10]:
        print(f'   {opp.from_asset} -> {opp.to_asset}: ${opp.expected_pnl_usd:.4f} (score: {opp.combined_score:.1f})')

if __name__ == '__main__':
    asyncio.run(main())
