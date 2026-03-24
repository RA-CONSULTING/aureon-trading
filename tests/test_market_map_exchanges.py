#!/usr/bin/env python3
"""Quick test of market map with all exchanges."""
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import json
sys.path.insert(0, '/workspaces/aureon-trading')

from collections import defaultdict

print("🗺️ TESTING MULTI-EXCHANGE MARKET MAP\n")

# First, show what we have cached from Coinbase
print("📊 CACHED DATA (from Coinbase 1-year historical):")
try:
    with open('crypto_market_map_cache.json', 'r') as f:
        cache = json.load(f)
    
    corr = cache.get('correlation_matrix', {})
    all_symbols = set(corr.keys())
    for syms in corr.values():
        all_symbols.update(syms.keys())
    
    print(f"   Symbols: {sorted(all_symbols)}")
    print(f"   Patterns: {len(cache.get('patterns', []))}")
except Exception as e:
    print(f"   No cache: {e}")

# Now test loading from Kraken
print("\n🐙 LOADING FROM KRAKEN:")
try:
    from kraken_client import KrakenClient, get_kraken_client
    kraken = get_kraken_client()
    pairs = kraken._load_asset_pairs()
    
    bases = set()
    for internal, info in pairs.items():
        if not internal.endswith('.d'):
            base = info.get('base', '')
            clean = base.replace('X', '').replace('Z', '') if base.startswith(('X', 'Z')) else base
            if clean == 'XBT':
                clean = 'BTC'
            if clean and len(clean) <= 6:
                bases.add(clean)
    
    print(f"   ✅ {len(pairs)} pairs, {len(bases)} unique assets")
    print(f"   Sample: {sorted(list(bases))[:20]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test Binance exchange info
print("\n🟡 LOADING FROM BINANCE:")
try:
    from binance_client import BinanceClient
    binance = get_binance_client()
    info = binance.exchange_info()
    symbols = info.get('symbols', [])
    
    bases = set()
    for sym in symbols:
        if sym.get('status') == 'TRADING':
            bases.add(sym.get('baseAsset', ''))
    
    print(f"   ✅ {len(symbols)} pairs, {len(bases)} unique assets")
    print(f"   Sample: {sorted(list(bases))[:20]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test Alpaca
print("\n🦙 LOADING FROM ALPACA:")
try:
    from alpaca_client import AlpacaClient
    alpaca = AlpacaClient()
    assets = alpaca.get_assets(status='active', asset_class='crypto') or []
    tradeable = [a for a in assets if a.get('tradable')]
    
    symbols = [a.get('symbol', '').split('/')[0] for a in tradeable]
    
    print(f"   ✅ {len(tradeable)} tradeable crypto assets")
    print(f"   Sample: {symbols[:20]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n✅ Multi-exchange test complete!")
