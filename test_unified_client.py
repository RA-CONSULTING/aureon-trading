#!/usr/bin/env python3
"""Test the unified exchange client to see why get_24h_tickers returns empty"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import json

sys.path.insert(0, '/workspaces/aureon-trading')

from unified_exchange_client import MultiExchangeClient

print("Testing MultiExchangeClient.get_24h_tickers()...")
print("="*60)

client = MultiExchangeClient()

print("\n1️⃣ Testing each exchange individually:")
print("-"*60)

# Check Kraken
print("\n🐙 KRAKEN:")
if hasattr(client, 'clients') and 'kraken' in client.clients:
    kraken_client = client.clients['kraken']
    print(f"   Client type: {type(kraken_client)}")
    print(f"   Has get_24h_tickers: {hasattr(kraken_client, 'get_24h_tickers')}")
    
    try:
        kraken_tickers = kraken_client.get_24h_tickers()
        print(f"   Returned: {len(kraken_tickers)} tickers")
        if kraken_tickers:
            print(f"   First ticker: {kraken_tickers[0]}")
    except Exception as e:
        print(f"   ERROR: {type(e).__name__}: {e}")
else:
    print("   NOT AVAILABLE")

# Check Binance
print("\n🟡 BINANCE:")
if hasattr(client, 'clients') and 'binance' in client.clients:
    binance_client = client.clients['binance']
    print(f"   Client type: {type(binance_client)}")
    print(f"   Has get_24h_tickers: {hasattr(binance_client, 'get_24h_tickers')}")
    
    try:
        binance_tickers = binance_client.get_24h_tickers()
        print(f"   Returned: {len(binance_tickers)} tickers")
        if binance_tickers:
            print(f"   First ticker: {binance_tickers[0]}")
    except Exception as e:
        print(f"   ERROR: {type(e).__name__}: {e}")
else:
    print("   NOT AVAILABLE")

# Check Capital
print("\n💼 CAPITAL.COM:")
if hasattr(client, 'clients') and 'capital' in client.clients:
    capital_client = client.clients['capital']
    print(f"   Client type: {type(capital_client)}")
    print(f"   Has get_24h_tickers: {hasattr(capital_client, 'get_24h_tickers')}")
    
    try:
        capital_tickers = capital_client.get_24h_tickers()
        print(f"   Returned: {len(capital_tickers)} tickers")
        if capital_tickers:
            print(f"   First ticker: {capital_tickers[0]}")
    except Exception as e:
        print(f"   ERROR: {type(e).__name__}: {e}")
else:
    print("   NOT AVAILABLE")

# Now test unified
print("\n\n2️⃣ Testing unified client:")
print("-"*60)

try:
    all_tickers = client.get_24h_tickers()
    print(f"✅ Total tickers from all exchanges: {len(all_tickers)}")
    if all_tickers:
        print("\nFirst 5 tickers:")
        for t in all_tickers[:5]:
            print(f"  {t.get('symbol', 'UNKNOWN'):12s} | {t.get('source', 'unknown'):8s} | Price: {t.get('lastPrice', 0)}")
    else:
        print("❌ NO TICKERS RETURNED - ALL EXCHANGES EMPTY")
        
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("Diagnostic complete.")
