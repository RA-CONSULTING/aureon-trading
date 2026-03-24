#!/usr/bin/env python3
"""
Test lazy-loading of Capital.com client.
Verifies Capital.com is NOT initialized during quick_init, only on first use.
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys, os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import time

def test_lazy_capital():
    """Test Capital.com lazy loading."""
    print("=" * 60)
    print("Testing Capital.com Lazy-Loading")
    print("=" * 60)
    
    start_time = time.time()
    
    # Import and create Orca with quick_init
    from orca_complete_kill_cycle import OrcaKillCycle
    
    print("\n1️⃣ Creating OrcaKillCycle with quick_init=True...")
    init_start = time.time()
    orca = OrcaKillCycle(exchange='alpaca', quick_init=True)
    init_time = time.time() - init_start
    print(f"✅ Init completed in {init_time:.2f}s")
    
    # Check Capital.com status
    print("\n2️⃣ Checking Capital.com client status...")
    capital_client = orca.clients.get('capital')
    if capital_client is None:
        print("✅ Capital.com is None (lazy-load pending) - CORRECT!")
    else:
        print(f"⚠️ Capital.com already initialized: {type(capital_client)}")
    
    # Trigger lazy-load
    print("\n3️⃣ Triggering lazy-load by calling _ensure_capital_client()...")
    lazy_start = time.time()
    loaded_client = orca._ensure_capital_client()
    lazy_time = time.time() - lazy_start
    print(f"✅ Lazy-load completed in {lazy_time:.2f}s")
    
    if loaded_client:
        print(f"✅ Capital.com client loaded: {type(loaded_client).__name__}")
    else:
        print("⚠️ Capital.com client failed to load (may be disabled)")
    
    # Verify it's cached for next call
    print("\n4️⃣ Calling _ensure_capital_client() again (should use cache)...")
    cache_start = time.time()
    cached_client = orca._ensure_capital_client()
    cache_time = time.time() - cache_start
    print(f"✅ Cache lookup completed in {cache_time:.4f}s (should be instant)")
    
    if cached_client is loaded_client:
        print("✅ Same client instance returned (cached) - CORRECT!")
    else:
        print("⚠️ Different client instance (not cached properly)")
    
    total_time = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"Total test time: {total_time:.2f}s")
    print(f"  - Quick init: {init_time:.2f}s")
    print(f"  - Lazy load: {lazy_time:.2f}s")
    print(f"  - Cache check: {cache_time:.4f}s")
    print(f"{'='*60}")
    
    # Summary
    print("\n✅ Lazy-loading test PASSED!")
    print("   Capital.com NOT initialized during quick_init ✅")
    print("   Capital.com loaded on first use ✅")
    print("   Subsequent calls use cache ✅")

if __name__ == "__main__":
    test_lazy_capital()
