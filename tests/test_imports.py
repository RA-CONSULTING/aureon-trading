#!/usr/bin/env python3
"""Quick test to verify all neural system imports work."""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
sys.path.insert(0, '/workspaces/aureon-trading')

print("🔬 Testing Neural System Imports...")
print("=" * 60)

# Test 1: Lighthouse
try:
    from aureon_lighthouse import LighthousePatternDetector
    print("✅ Lighthouse (LighthousePatternDetector): IMPORTED")
except Exception as e:
    print(f"❌ Lighthouse: FAILED - {e}")

# Test 2: HNC Probability Matrix
try:
    from hnc_probability_matrix import HNCProbabilityIntegration
    print("✅ HNC Matrix (HNCProbabilityIntegration): IMPORTED")
except Exception as e:
    print(f"❌ HNC Matrix: FAILED - {e}")

# Test 3: Unified Ecosystem
try:
    from aureon_unified_ecosystem import AureonKrakenEcosystem, AdaptiveLearningEngine
    print("✅ Unified Ecosystem (AureonKrakenEcosystem): IMPORTED")
    print("✅ Adaptive Learner (AdaptiveLearningEngine): IMPORTED")
except Exception as e:
    print(f"❌ Unified Ecosystem: FAILED - {e}")

# Test 4: V14 Dance Enhancer
try:
    from s5_v14_labyrinth import V14DanceEnhancer
    print("✅ V14 Dance Enhancer: IMPORTED")
except Exception as e:
    print(f"❌ V14 Dance Enhancer: FAILED - {e}")

# Test 5: Mycelium
try:
    from mycelium_conversion_hub import MyceliumConversionHub
    print("✅ Mycelium Conversion Hub: IMPORTED")
except Exception as e:
    print(f"❌ Mycelium: FAILED - {e}")

# Test 6: Timeline Oracle
try:
    from aureon_timeline_oracle import TimelineOracle
    print("✅ Timeline Oracle: IMPORTED")
except Exception as e:
    print(f"❌ Timeline Oracle: FAILED - {e}")

print("=" * 60)
print("🔬 Import Test Complete!")
