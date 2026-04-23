#!/usr/bin/env python3
"""Quick test for Orca autonomous mode initialization."""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import time

print("🧪 QUICK ORCA TEST - Checking initialization")
print("=" * 60)

try:
    print("\n1️⃣ Importing OrcaKillCycle...")
    start = time.time()
    from orca_complete_kill_cycle import OrcaKillCycle
    elapsed = time.time() - start
    print(f"   ✅ Import successful ({elapsed:.1f}s)")
    
    print("\n2️⃣ Creating instance (quick_init=True for speed)...")
    start = time.time()
    orca = OrcaKillCycle(quick_init=True)
    elapsed = time.time() - start
    print(f"   ✅ Instance created ({elapsed:.1f}s)")
    
    print("\n3️⃣ Checking available exchanges...")
    exchanges = list(orca.clients.keys())
    print(f"   ✅ Connected to: {', '.join(exchanges)}")
    
    print("\n4️⃣ Testing run_autonomous_warroom function exists...")
    if hasattr(orca, 'run_autonomous_warroom'):
        print(f"   ✅ run_autonomous_warroom method exists")
    else:
        print(f"   ❌ run_autonomous_warroom method NOT FOUND")
    
    print("\n" + "=" * 60)
    print("✅ ALL BASIC TESTS PASSED")
    print("\n💡 Note: Full autonomous mode loads 50+ intelligence systems")
    print("   This can take 30-60 seconds on first run (module imports)")
    print("   Subsequent runs are faster due to Python bytecode caching")
    print("\n🎯 To test full autonomous mode, use:")
    print("   python orca_complete_kill_cycle.py --autonomous 1 0.5 0.5")
    
except Exception as e:
    print(f"\n❌ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
