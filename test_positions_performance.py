#!/usr/bin/env python3
"""Test portfolio endpoint response time."""
import asyncio
import json
import os
import time

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')

from live_position_viewer import get_binance_positions, get_alpaca_positions, get_kraken_positions

async def test_positions():
    """Test each exchange position fetch time."""
    print("\n" + "=" * 80)
    print("⏱️  POSITION FETCH PERFORMANCE TEST")
    print("=" * 80 + "\n")
    
    # Test Binance
    print("🟡 BINANCE:")
    start = time.time()
    try:
        bin_pos = await asyncio.wait_for(
            asyncio.to_thread(get_binance_positions),
            timeout=5.0
        )
        elapsed = time.time() - start
        print(f"   ✅ Fetched in {elapsed:.2f}s: {len(bin_pos) if bin_pos else 0} positions")
        if bin_pos:
            for pos in bin_pos[:2]:
                print(f"      {pos.get('symbol')}: {pos.get('quantity')} @ ${pos.get('current_price')}")
    except asyncio.TimeoutError:
        print(f"   ❌ TIMEOUT (5s) - Binance fetch hung")
    except Exception as e:
        print(f"   ⚠️ Error: {e}")
    
    # Test Alpaca
    print("\n🦙 ALPACA:")
    start = time.time()
    try:
        alp_pos = await asyncio.wait_for(
            asyncio.to_thread(get_alpaca_positions),
            timeout=5.0
        )
        elapsed = time.time() - start
        print(f"   ✅ Fetched in {elapsed:.2f}s: {len(alp_pos) if alp_pos else 0} positions")
        if alp_pos:
            for pos in alp_pos[:2]:
                print(f"      {pos.get('symbol')}: {pos.get('quantity')} @ ${pos.get('current_price')}")
    except asyncio.TimeoutError:
        print(f"   ❌ TIMEOUT (5s) - Alpaca fetch hung")
    except Exception as e:
        print(f"   ⚠️ Error: {e}")
    
    # Test Kraken
    print("\n🐙 KRAKEN:")
    start = time.time()
    try:
        krk_pos = await asyncio.wait_for(
            asyncio.to_thread(get_kraken_positions),
            timeout=5.0
        )
        elapsed = time.time() - start
        print(f"   ✅ Fetched in {elapsed:.2f}s: {len(krk_pos) if krk_pos else 0} positions")
        if krk_pos:
            for pos in krk_pos[:2]:
                print(f"      {pos.get('symbol', pos.get('pair'))}: {pos.get('quantity')} @ ${pos.get('current_price')}")
    except asyncio.TimeoutError:
        print(f"   ❌ TIMEOUT (5s) - Kraken fetch hung")
    except Exception as e:
        print(f"   ⚠️ Error: {e}")
    
    print("\n" + "=" * 80)
    print("Test complete")
    print("=" * 80 + "\n")

if __name__ == '__main__':
    asyncio.run(test_positions())
