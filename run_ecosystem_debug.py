#!/usr/bin/env python3
"""
Run ecosystem with full error capture - 1 iteration only
"""
import os
import sys
import traceback

sys.path.insert(0, '/workspaces/aureon-trading')

try:
    print("🚀 Starting Aureon Unified Ecosystem...")
    print("="*70)
    
    from aureon_unified_ecosystem import AureonKrakenEcosystem
    
    print("\n✅ Ecosystem imported successfully")
    print("Initializing...")
    
    # Initialize in dry run mode for safety (will auto-detect live if LIVE=1)
    dry_run = os.getenv('LIVE', '0') != '1'
    
    ecosystem = AureonKrakenEcosystem(
        initial_balance=100.0,
        dry_run=dry_run
    )
    
    print(f"✅ Ecosystem initialized")
    print(f"   DRY_RUN: {ecosystem.dry_run}")
    print(f"   Equity: £{ecosystem.total_equity_gbp:.2f}")
    
    print("\n🔄 Running 1 iteration...")
    print("-"*70 + "\n")
    
    # Run with very short interval - 1 iteration
    ecosystem.run(interval=1.0, max_minutes=0.1)
    
    print("\n" + "-"*70)
    print("✅ Iteration complete!")
    
except KeyboardInterrupt:
    print("\n\n⏹️  Stopped by user")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print(f"\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)
