#!/usr/bin/env python3
"""Test Ocean Scanner functionality."""
import asyncio
import os
import sys
import subprocess

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')

from aureon_ocean_scanner import OceanScanner
from kraken_client import KrakenClient
from binance_client import BinanceClient
from alpaca_client import AlpacaClient

async def test_ocean():
    """Test ocean scanner end-to-end."""
    print("🌊 TESTING OCEAN SCANNER")
    print("=" * 70)
    
    # Initialize exchanges
    print("\n1. Initializing exchanges...")
    exchanges = {
        'kraken': KrakenClient(),
        'binance': BinanceClient(),
        'alpaca': AlpacaClient()
    }
    print("   ✅ Exchanges loaded")
    
    # Create scanner
    print("\n2. Creating OceanScanner...")
    scanner = OceanScanner(exchanges)
    print("   ✅ OceanScanner created")
    
    # Discover universe
    print("\n3. Discovering universe...")
    universe = await scanner.discover_universe()
    total = sum(universe.values())
    print(f"   ✅ Universe discovered: {total:,} symbols")
    for ex, count in universe.items():
        print(f"      • {ex}: {count:,}")
    
    # Scan ocean
    print("\n4. Scanning ocean for opportunities...")
    opportunities = await scanner.scan_ocean(limit=100)
    print(f"   ✅ Found {len(opportunities) if opportunities else 0} opportunities")
    if opportunities:
        for i, opp in enumerate(opportunities[:3], 1):
            print(f"      {i}. {opp.symbol:<10} ({opp.exchange:<8}) - Score: {opp.ocean_score:.2f} - {opp.reason[:40]}")
    
    # Get summary
    print("\n5. Getting ocean summary...")
    summary = scanner.get_ocean_summary()
    print("   Summary:")
    for key, value in summary.items():
        if key == 'top_5':
            print(f"      • {key}: {len(value)} items")
        elif key == 'universe_size' and isinstance(value, dict):
            print(f"      • {key}: {value.get('total', 0):,} total")
        else:
            print(f"      • {key}: {value}")
    
    print("\n" + "=" * 70)
    print("✅ OCEAN SCANNER TEST COMPLETE")

if __name__ == '__main__':
    asyncio.run(test_ocean())
