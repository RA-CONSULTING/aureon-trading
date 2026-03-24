from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import logging

# Ensure we can import from local dir
sys.path.insert(0, os.getcwd())

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("VerifyAutonomous")

print("=" * 60)
print("👑🎮 VERIFYING QUEEN AUTONOMOUS CONTROL")
print("=" * 60)

try:
    print("1. Importing module...")
    from aureon_queen_autonomous_control import create_queen_autonomous_control
    print("   ✅ Import successful")

    print("\n2. Creating Sovereign Controller...")
    control = create_queen_autonomous_control(sovereignty='SOVEREIGN')
    print("   ✅ Controller created")

    print("\n3. Checking Status...")
    status = control.get_full_status()
    print(f"   ✅ Sovereignty: {status['sovereignty_level']}")
    print(f"   ✅ Systems Online: {status['systems_online']}/{status['systems_total']}")
    
    if control.temporal_dialer:
        print("\n4. Tuning Temporal Dialer...")
        control.temporal_dialer.tune_frequency(7.83)
        print("   ✅ Tuned to 7.83Hz")

    print("\n5. Testing Perception...")
    perception = control.perceive()
    q = perception.get('quantum', {})
    print(f"   ✅ Omega: {q.get('omega'):.4f}")
    print(f"   ✅ Direction: {q.get('direction')}")
    print(f"   ✅ Gaia: {perception.get('gaia_alignment'):.1%}")
    print(f"   ✅ Crown: {perception.get('crown_activation'):.1%}")

    print("\n6. Testing Decision...")
    context = {
        'symbol': 'ETH/USD',
        'probability': 0.8,
        'pip_score': 0.85, 
        'drift': 0.02,
        'exchange': 'kraken',
        'expected_pnl': 0.05
    }
    decision = control.decide(perception, context)
    print(f"   ✅ Action: {decision.action.name}")
    print(f"   ✅ Reason: {decision.reason}")

    print("\n✨ FINAL RESULT: SUCCESS")
    print("👑 Queen Sero is fully operational and autonomous.")

except Exception as e:
    print(f"\n❌ FINAL RESULT: FAILED")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
