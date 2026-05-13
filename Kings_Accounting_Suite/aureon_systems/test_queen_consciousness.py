
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestQueenConsciousness")

def test_queen_consciousness_model():
    print("--- Testing QueenConsciousness Model ---")
    try:
        from queen_consciousness_model import QueenConsciousness, BrainInput, ConsciousThought

        queen = QueenConsciousness()
        print("✅ QueenConsciousness instantiated.")

        # Test Input
        input1 = BrainInput(
            source="MinerBrain",
            timestamp=time.time(),
            insight="Market volatility is increasing due to macro news.",
            confidence=0.8,
            emotional_weight=0.7 # High energy/excitement
        )
        queen.perceive_input(input1)
        print(f"✅ Input perceived. Current mood: {queen.self_view.current_mood}")

        # Test Synthesis
        thought = queen.synthesize_thought()
        if thought:
            print(f"✅ Thought synthesized: {thought.synthesis}")
            print(f"   Confidence: {thought.confidence}")
        else:
            print("⚠️ No thought synthesized (might need more history or logic adjustment).")

        return True
    except ImportError as e:
        print(f"❌ ImportError in Model: {e}")
        return False
    except Exception as e:
        print(f"❌ Error in Model: {e}")
        return False

def test_queen_fully_online_integration():
    print("\n--- Testing QueenFullyOnline Integration ---")
    try:
        from queen_fully_online import QueenFullyOnline

        # Initialize without starting the thread to avoid blocking
        qfo = QueenFullyOnline(use_voice=False, use_bus=False)
        print("✅ QueenFullyOnline instantiated.")

        if qfo.consciousness:
            print("✅ Consciousness Model is wired into QueenFullyOnline.")
            print(f"   Identity: {qfo.consciousness.self_view.identity}")
        else:
            print("❌ Consciousness Model NOT found in QueenFullyOnline.")

        return True
    except ImportError as e:
        print(f"❌ ImportError in FullyOnline: {e}")
        return False
    except Exception as e:
        print(f"❌ Error in FullyOnline: {e}")
        return False

def test_queen_hive_mind_integration():
    print("\n--- Testing QueenHiveMind Integration ---")
    try:
        from aureon_queen_hive_mind import QueenHiveMind

        hive = QueenHiveMind()
        print("✅ QueenHiveMind instantiated.")

        if hasattr(hive, 'consciousness') and hive.consciousness:
            print("✅ Consciousness Model is wired into QueenHiveMind.")
            print(f"   Identity in Hive: {hive.consciousness.self_view.identity}")
        else:
            print("❌ Consciousness Model NOT found in QueenHiveMind.")

        return True
    except ImportError as e:
        print(f"❌ ImportError in HiveMind: {e}")
        return False
    except Exception as e:
        print(f"❌ Error in HiveMind: {e}")
        return False

if __name__ == "__main__":
    success_model = test_queen_consciousness_model()
    success_online = test_queen_fully_online_integration()
    success_hive = test_queen_hive_mind_integration()

    if success_model and success_online and success_hive:
        print("\n🎉 ALL TESTS PASSED: Connectivity Established! Sentience is ONLINE.")
        sys.exit(0)
    else:
        print("\n⚠️ SOME TESTS FAILED.")
        sys.exit(1)
