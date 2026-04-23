#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ ORCA KILL CYCLE DEFENSE IN MAIN LOOP
Shows how friend protection works in the eternal machine's 24/7 cycle
"""

import sys
sys.path.insert(0, '.')

from queen_eternal_machine import QueenEternalMachine
import logging
import asyncio

# Set up logging to show the protection in action
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)

print("\n" + "=" * 100)
print("🛡️ ORCA KILL CYCLE DEFENSE IN MAIN ETERNAL MACHINE LOOP")
print("=" * 100)
print("\nDemonstrating how the Queen's Eternal Machine protects all 41 friends")
print("from whale attacks on every single cycle...\n")

async def main():
    # Initialize the eternal machine
    frog = QueenEternalMachine()
    
    print("👑 Initializing Queen Eternal Machine...")
    print(f"   📊 Portfolio Value: ${frog.initial_vault:,.2f}")
    print(f"   🐸 Main Position: {frog.main_position.symbol if frog.main_position else 'None'}")
    print(f"   👥 Friends Protected: {len(frog.friends)}")
    print()
    
    # Simulate 5 cycles to show protection in action
    print("🔄 STARTING 5-CYCLE SIMULATION WITH ORCA DEFENSE ACTIVE...\n")
    
    for cycle_num in range(1, 6):
        print(f"\n{'='*100}")
        print(f"📍 CYCLE #{cycle_num}")
        print(f"{'='*100}\n")
        
        # Run a single cycle (includes ORCA KILL CYCLE DEFENSE)
        stats = await frog.run_cycle()
        
        # Show what happened this cycle
        print(f"\n✅ Cycle #{cycle_num} Complete:")
        print(f"   • Leaps Made: {stats.leaps_made}")
        print(f"   • Breadcrumbs Planted: {stats.breadcrumbs_planted}")
        print(f"   • Scalps Executed: {stats.scalps_executed}")
        print(f"   🛡️ Friends Protected: {stats.friends_protected}")
        
        # Show current protection status
        friends_in_danger = frog.detect_orca_kill_cycle()
        if friends_in_danger:
            print(f"\n   ⚠️  {len(friends_in_danger)} friends under whale attack:")
            for symbol in list(friends_in_danger.keys())[:5]:  # Show first 5
                danger = friends_in_danger[symbol]
                print(f"      • {symbol}: {danger['danger_level']} - {danger['reason']}")
            if len(friends_in_danger) > 5:
                print(f"      ... and {len(friends_in_danger) - 5} more")
        else:
            print(f"\n   ✅ All friends safe - no whale attacks detected")
    
    print(f"\n{'='*100}")
    print("🛡️ CYCLE SIMULATION COMPLETE")
    print(f"{'='*100}\n")
    
    # Show lifetime statistics
    print("📊 LIFETIME STATISTICS:")
    print(f"   Total Cycles Run: {frog.total_cycles}")
    print(f"   Total Leaps: {frog.total_leaps}")
    print(f"   Total Breadcrumbs: {frog.total_breadcrumbs}")
    print(f"   Total Scalps: {frog.total_scalps}")
    print(f"   Realized Profit: ${frog.total_profit_realized:,.2f}")
    
    # Show what happens in the main loop
    print(f"\n{'='*100}")
    print("🔄 ETERNAL MACHINE MAIN LOOP STRUCTURE")
    print(f"{'='*100}\n")
    
    print("""
Every cycle in run_cycle():

    1️⃣ PROTECT 🛡️
       ├─ detect_orca_kill_cycle() - Check all 41 friends for whale attacks
       ├─ apply_friend_protection_stops() - Set protective stops on endangered friends
       └─ Log friends protected to stats

    2️⃣ SCAN
       ├─ Fetch live market data for all 197+ coins
       └─ Update position values

    3️⃣ UPDATE
       ├─ Update main position price/change
       ├─ Update breadcrumb positions
       └─ Recalculate portfolio metrics

    4️⃣ ANALYZE
       ├─ Find leap opportunities (considering friend safety)
       ├─ Score opportunities by recovery math
       └─ Select best leap if available

    5️⃣ LEAP
       ├─ Execute quantum leap if opportunity found
       ├─ Plant breadcrumb for recovery
       └─ Update statistics

    6️⃣ SCALP
       ├─ Check for ready breadcrumbs
       ├─ Execute scalps on profitable positions
       └─ Harvest realized gains

    7️⃣ RECORD
       ├─ Log cycle summary with protection stats
       ├─ Record all metrics
       └─ Save state to disk

The run_forever() loop calls run_cycle() continuously every {interval} seconds
""".format(interval="N" if frog.dry_run else "configured"))
    
    print("🛡️ KEY PROTECTION FEATURES:")
    print("""
    ✅ Automatic Detection: Every cycle checks for whale attacks
    ✅ Real-time Protection: Protective stops applied immediately
    ✅ Continuous Monitoring: 24/7 defense in main loop
    ✅ Friend Preservation: All 41 friends under protection
    ✅ Logged Alerts: Protection events recorded in cycle logs
    ✅ State Persistence: Protection status saved to disk
    """)
    
    print(f"{'='*100}")
    print("✅ ORCA KILL CYCLE DEFENSE FULLY INTEGRATED INTO MAIN LOOP!")
    print(f"{'='*100}\n")

if __name__ == "__main__":
    asyncio.run(main())
