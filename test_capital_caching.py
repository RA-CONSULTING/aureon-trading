#!/usr/bin/env python3
"""
Simple test: Verify Capital.com lazy-loading logic.
Tests only the Capital.com client initialization, not full Orca.
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys, os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import time

def test_capital_session_caching():
    """Test Capital.com session caching to avoid repeated API calls."""
    print("=" * 60)
    print("Testing Capital.com Session Caching")
    print("=" * 60)
    
    try:
        from capital_client import CapitalClient
    except ImportError as e:
        print(f"❌ Cannot import Capital.com client: {e}")
        return
    
    print("\n1️⃣ Creating CapitalClient (first time)...")
    start1 = time.time()
    client1 = CapitalClient()
    time1 = time.time() - start1
    print(f"✅ First client created in {time1:.2f}s")
    print(f"   Enabled: {client1.enabled}")
    print(f"   CST: {'SET' if client1.cst else 'NONE'}")
    print(f"   Token: {'SET' if client1.x_security_token else 'NONE'}")
    
    if not client1.enabled:
        print("\n⚠️ Capital.com is disabled (check API keys)")
        print("   ✅ Lazy-loading would skip this client entirely")
        return
    
    print("\n2️⃣ Creating CapitalClient (second time - within 50 min window)...")
    start2 = time.time()
    client2 = CapitalClient()
    time2 = time.time() - start2
    print(f"✅ Second client created in {time2:.2f}s")
    print(f"   Should be FASTER if session caching works")
    print(f"   First: {time1:.2f}s, Second: {time2:.2f}s")
    
    if time2 < time1 * 0.5:
        print(f"   ✅ Session caching WORKING (50% faster)")
    else:
        print(f"   ⚠️ Session may not be cached (similar times)")
    
    print("\n3️⃣ Testing _create_session() caching...")
    print("   Calling _create_session() - should skip if cached...")
    start3 = time.time()
    client1._create_session()
    time3 = time.time() - start3
    print(f"   ✅ _create_session() completed in {time3:.4f}s")
    
    if time3 < 0.01:
        print(f"   ✅ Session cache WORKING (instant return)")
    else:
        print(f"   ⚠️ Session may have been refreshed ({time3:.2f}s)")
    
    print(f"\n{'='*60}")
    print("✅ Capital.com session caching test complete!")
    print(f"{'='*60}")

if __name__ == "__main__":
    test_capital_session_caching()
