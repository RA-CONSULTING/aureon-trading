#!/usr/bin/env python3
"""
🌌🪞⚓ STARGATE PROTOCOL STATUS CHECK
Quick utility to verify all Stargate Protocol systems are active.
"""
import sys
import os

# Windows UTF-8 Fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        if hasattr(sys.stdout, 'buffer') and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        # Skip stderr wrapping (causes Windows exit errors)
    except Exception:
        pass

import logging

# Suppress noisy logs
logging.getLogger('aureon_mycelium').setLevel(logging.WARNING)
logging.getLogger('aureon_unified_ecosystem').setLevel(logging.WARNING)
logging.getLogger('aureon_probability_nexus').setLevel(logging.WARNING)
logging.getLogger('aureon_thought_bus').setLevel(logging.WARNING)
logging.getLogger('mycelium_whale_sonar').setLevel(logging.WARNING)

def check_stargate_status():
    """Check status of all Stargate Protocol systems."""
    print()
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║          🌌🪞⚓ STARGATE PROTOCOL STATUS CHECK ⚓🪞🌌                 ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()
    
    results = {
        'stargate_protocol': False,
        'quantum_mirror_scanner': False,
        'timeline_anchor_validator': False,
        'queen_wired': False,
    }
    
    # Check Stargate Protocol Engine
    print("🌌 STARGATE PROTOCOL ENGINE")
    print("─" * 60)
    try:
        from aureon_stargate_protocol import create_stargate_engine
        engine = create_stargate_engine(with_integrations=False)
        results['stargate_protocol'] = True
        
        status = engine.get_status()
        print(f"   ✅ Engine: ACTIVE")
        print(f"   🗺️ Planetary Nodes: {status.get('planetary_nodes', 0)}")
        print(f"   🪞 Quantum Mirrors: {status.get('quantum_mirrors', 0)}")
        print(f"   🧘 Conscious Nodes: {status.get('conscious_nodes', 0)}")
        print(f"   🌍 Global Coherence: {status.get('global_coherence', 0):.3f}")
        print(f"   ⚡ Standing Wave Intensity: {status.get('standing_wave_intensity', 0):.3f}")
        
        # List stargates
        for sg_id in list(engine.stargates.keys())[:6]:
            sg = engine.stargates[sg_id]
            print(f"   ⭐ {sg.name}: {sg.resonance_frequency}Hz (Casimir: {sg.casimir_strength:.2f})")
        if len(engine.stargates) > 6:
            print(f"   ... and {len(engine.stargates) - 6} more nodes")
        
    except Exception as e:
        print(f"   ❌ Engine: NOT AVAILABLE ({e})")
    
    print()
    
    # Check Quantum Mirror Scanner
    print("🔮 QUANTUM MIRROR SCANNER")
    print("─" * 60)
    try:
        from aureon_quantum_mirror_scanner import create_quantum_scanner
        scanner = create_quantum_scanner(with_integrations=False)
        results['quantum_mirror_scanner'] = True
        
        status = scanner.get_status()
        print(f"   ✅ Scanner: ACTIVE")
        print(f"   📊 Reality Branches: {status.get('total_branches', 0)}")
        print(f"   ✅ Validated: {status.get('validated_branches', 0)}")
        print(f"   🔴 Rejected: {status.get('rejected_branches', 0)}")
        print(f"   ⏳ Pending: {status.get('pending_branches', 0)}")
        print(f"   🌀 Convergences: {status.get('convergences', 0)}")
        print(f"   🌍 Global Coherence: {status.get('global_coherence', 0):.3f}")
        
    except Exception as e:
        print(f"   ❌ Scanner: NOT AVAILABLE ({e})")
    
    print()
    
    # Check Timeline Anchor Validator
    print("⚓ TIMELINE ANCHOR VALIDATOR")
    print("─" * 60)
    try:
        from aureon_timeline_anchor_validator import create_timeline_validator
        validator = create_timeline_validator(with_integrations=False)
        results['timeline_anchor_validator'] = True
        
        status = validator.get_status()
        print(f"   ✅ Validator: ACTIVE")
        print(f"   📋 Pending Anchors: {status.get('pending_count', 0)}")
        print(f"   ✅ Anchored Timelines: {status.get('anchored_count', 0)}")
        print(f"   📊 Total Validations: {status.get('total_validations', 0)}")
        print(f"   🎯 Execution-Ready: {status.get('execution_ready', 0)}")
        print(f"   ⏰ Validation Cycles: {status.get('validation_cycles', 'N/A')}")
        
    except Exception as e:
        print(f"   ❌ Validator: NOT AVAILABLE ({e})")
    
    print()
    
    # Check Queen Wiring
    print("👑 QUEEN HIVE MIND INTEGRATION")
    print("─" * 60)
    try:
        from aureon_queen_hive_mind import get_queen, wire_all_systems
        queen = get_queen(initial_capital=100.0)
        wire_results = wire_all_systems(queen)
        
        # Check specific Stargate Protocol systems
        stargate_wired = hasattr(queen, 'stargate_engine') and queen.stargate_engine is not None
        scanner_wired = hasattr(queen, 'quantum_mirror_scanner') and queen.quantum_mirror_scanner is not None
        validator_wired = hasattr(queen, 'timeline_validator') and queen.timeline_validator is not None
        
        results['queen_wired'] = stargate_wired and scanner_wired and validator_wired
        
        print(f"   Stargate Protocol: {'✅ WIRED' if stargate_wired else '❌ NOT WIRED'}")
        print(f"   Quantum Scanner:   {'✅ WIRED' if scanner_wired else '❌ NOT WIRED'}")
        print(f"   Timeline Validator:{'✅ WIRED' if validator_wired else '❌ NOT WIRED'}")
        
        if results['queen_wired']:
            print()
            print("   🌌 Queen can now:")
            print("   • Access 12 planetary stargate nodes")
            print("   • Pull quantum mirrors (potential timelines)")
            print("   • Scan reality branches with 3-pass validation")
            print("   • Detect timeline convergences")
            print("   • Anchor beneficial timelines over 7-day cycles")
            print("   • Execute on 4th pass when coherence > φ (0.618)")
        
    except Exception as e:
        print(f"   ❌ Queen: NOT AVAILABLE ({e})")
    
    print()
    print("═" * 70)
    
    # Summary
    all_ok = all(results.values())
    if all_ok:
        print("🌌✅ ALL STARGATE PROTOCOL SYSTEMS ACTIVE ✅🌌")
        print()
        print("   The Queen has access to:")
        print("   • 12 planetary stargate nodes (sacred sites)")
        print("   • 4 quantum mirrors (potential timelines)")
        print("   • Reality branch scanning (market as timelines)")
        print("   • Timeline convergence detection")
        print("   • 7-day extended validation cycles")
        print("   • 4th pass execution gate (φ threshold)")
        print()
        print("   'The future is not written—it is chosen.'")
    else:
        print("⚠️ SOME STARGATE PROTOCOL SYSTEMS UNAVAILABLE")
        for name, ok in results.items():
            status = "✅" if ok else "❌"
            print(f"   {status} {name}")
    
    print("═" * 70)
    print()
    
    return all_ok


if __name__ == "__main__":
    success = check_stargate_status()
    sys.exit(0 if success else 1)
