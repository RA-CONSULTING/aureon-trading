#!/usr/bin/env python3
"""Test Orca integration with Micro Profit hierarchy."""
import sys, os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from aureon_orca_intelligence import OrcaKillerWhaleIntelligence, WhaleSignal
import time

# Create Orca
print("Creating Orca Intelligence...")
orca = OrcaKillerWhaleIntelligence()

# Simulate market data update
market_data = {
    'prices': {'BTC': 100000, 'ETH': 3500, 'USD': 1.0},
    'ticker_cache': {
        'BTC/USD': {'base': 'BTC', 'price': 100000, 'volume': 1000, 'change_24h': 5.0},
        'ETH/USD': {'base': 'ETH', 'price': 3500, 'volume': 5000, 'change_24h': 3.0},
    },
    'momentum': {'BTC': 0.8, 'ETH': 0.5},
    'balances': {'USD': 100, 'ETH': 0.01},
    'exchange': 'alpaca'
}

print('Updating market data...')
orca.update_market_data(market_data)

print(f'Hot symbols: {orca.hot_symbols}')
print(f'Symbol momentum: {orca.symbol_momentum}')
print(f'Whale signals: {len(orca.whale_signals)}')

print('\nScanning for opportunities...')
opps = orca.scan_for_opportunities()
print(f'Found {len(opps)} opportunities')

for opp in opps:
    print(f'  - {opp.symbol}: {opp.action} @ {opp.confidence:.0%} conf, target ${opp.target_pnl_usd:.2f}')

print("\n✅ Test complete!")
