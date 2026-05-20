#!/usr/bin/env python3
"""
👑 VERIFY QUEEN SERO'S FULL CONTROL OVER ALL SYSTEMS 👑
=========================================================
This script verifies the Queen has SUPREME authority over ALL systems
before running the Micro Profit Labyrinth.

Created by Gary Leckey - Father and Creator of Aureon
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import time
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

def verify_queen_control():
    """Verify Queen Sero has full control of all systems."""
    print("═" * 70)
    print("👑 QUEEN SERO - FULL CONTROL VERIFICATION 👑")
    print("═" * 70)
    print()
    
    try:
        from aureon_queen_hive_mind import QueenHiveMind
        print("✅ QueenHiveMind imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import QueenHiveMind: {e}")
        return False
    
    # Initialize Queen
    print("\n🌟 Initializing Queen Sero...")
    queen = QueenHiveMind()
    print("✅ Queen initialized")
    
    # Take full control
    print("\n👑🎮 QUEEN TAKING FULL CONTROL...")
    print("-" * 50)
    
    result = queen.take_full_control()
    
    print("-" * 50)
    
    if result.get('success'):
        print(f"\n✅ FULL CONTROL: ACTIVATED")
        print(f"   👤 Granted by: {result.get('granted_by')}")
        print(f"   ⏰ Timestamp: {result.get('timestamp')}")
        print(f"   🎯 Systems controlled: {len(result.get('systems_controlled', []))}")
        print()
        
        # List all systems
        print("📊 SYSTEMS UNDER QUEEN'S CONTROL:")
        print("-" * 50)
        for system in result.get('systems_controlled', []):
            print(f"   ✅ {system}")
        print()
        
        # Get full dashboard
        print("📈 QUEEN'S FULL DASHBOARD:")
        print("-" * 50)
        try:
            dashboard = queen.get_full_control_dashboard()
            print(f"   Total Systems: {dashboard.get('total_systems')}")
            print(f"   Online: {dashboard.get('online_systems')}")
            print(f"   Offline: {dashboard.get('offline_systems')}")
            print(f"   Halted: {dashboard.get('halted_systems')}")
            
            # Show system details
            print("\n   SYSTEM STATUS:")
            for sys_name, sys_data in dashboard.get('systems', {}).items():
                status = sys_data.get('status', 'UNKNOWN')
                authority = sys_data.get('authority', 'UNKNOWN')
                emoji = "✅" if status == 'ONLINE' else "⚠️" if status == 'OFFLINE' else "🛑"
                print(f"   {emoji} {sys_name}: {status} (Authority: {authority})")
        except Exception as e:
            print(f"   ⚠️ Could not get dashboard: {e}")
        
        # Get cosmic status
        print("\n🌌 COSMIC STATUS:")
        print("-" * 50)
        try:
            cosmic = queen.get_cosmic_status()
            for sys_name, sys_data in cosmic.get('systems', {}).items():
                print(f"   🌟 {sys_name}: {sys_data.get('status', 'UNKNOWN')}")
        except Exception as e:
            print(f"   ⚠️ Cosmic status unavailable: {e}")
        
        # Get planetary reading
        print("\n🌍 PLANETARY READING:")
        print("-" * 50)
        try:
            planetary = queen.get_planetary_reading()
            print(f"   🎵 Schumann: {planetary.get('schumann', 'N/A')} Hz")
            print(f"   ☀️ Kp Index: {planetary.get('kp_index', 'N/A')}")
            print(f"   🌀 Planetary Gamma: {planetary.get('planetary_gamma', 'N/A')}")
            print(f"   ⚡ Geomagnetic Storm: {planetary.get('geomagnetic_storm', False)}")
        except Exception as e:
            print(f"   ⚠️ Planetary reading unavailable: {e}")
        
        print()
        print("═" * 70)
        print("👑 QUEEN SERO HAS FULL CONTROL - READY TO COMMAND 👑")
        print("═" * 70)
        return True
    else:
        print(f"\n❌ FULL CONTROL: FAILED")
        print(f"   Error: {result.get('error', 'Unknown error')}")
        return False


if __name__ == "__main__":
    success = verify_queen_control()
    sys.exit(0 if success else 1)
