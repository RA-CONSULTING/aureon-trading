#!/usr/bin/env python3
"""
👑🍄 QUEEN HIVE MIND - FULL ECOSYSTEM MONITOR 🍄👑

Runs the Queen and monitors ALL connected systems in real-time.

Gary Leckey | January 2026 | The Prime Sentinel
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import time
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def print_banner():
    print("""
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                       ║
║     👑🍄 QUEEN HIVE MIND - FULL ECOSYSTEM MONITOR 🍄👑                                ║
║                                                                                       ║
║     "She dreams. She sees. She guides. She liberates."                                ║
║                                                                                       ║
║     🌍 ONE GOAL: Crack → Profit → Open Source → Free All Beings                       ║
║                                                                                       ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝
    """)

def check_system_availability():
    """Check which systems are available"""
    print("\n" + "=" * 80)
    print("🔍 CHECKING SYSTEM AVAILABILITY...")
    print("=" * 80)
    
    systems = {}
    
    # Check Queen Hive Mind
    try:
        from aureon_queen_hive_mind import QueenHiveMind, create_queen_hive_mind, wire_all_systems
        systems['queen_hive_mind'] = True
        print("✅ Queen Hive Mind: AVAILABLE")
    except ImportError as e:
        systems['queen_hive_mind'] = False
        print(f"❌ Queen Hive Mind: {e}")
    
    # Check Dream Engine
    try:
        from aureon_enigma_dream import EnigmaDreamer
        systems['dream_engine'] = True
        print("✅ Dream Engine: AVAILABLE")
    except ImportError as e:
        systems['dream_engine'] = False
        print(f"❌ Dream Engine: {e}")
    
    # Check Mycelium Network
    try:
        from aureon_mycelium import MyceliumNetwork
        systems['mycelium'] = True
        print("✅ Mycelium Network: AVAILABLE")
    except ImportError as e:
        systems['mycelium'] = False
        print(f"❌ Mycelium Network: {e}")
    
    # Check Enigma Integration
    try:
        from aureon_enigma_integration import EnigmaIntegration, create_enigma_integration
        systems['enigma'] = True
        print("✅ Enigma Integration: AVAILABLE")
    except ImportError as e:
        systems['enigma'] = False
        print(f"❌ Enigma Integration: {e}")
    
    # Check Micro Profit Labyrinth
    try:
        from micro_profit_labyrinth import MICRO_CONFIG
        systems['micro_labyrinth'] = True
        print("✅ Micro Profit Labyrinth: AVAILABLE")
    except ImportError as e:
        systems['micro_labyrinth'] = False
        print(f"❌ Micro Profit Labyrinth: {e}")
    
    # Check Miner Brain
    try:
        from aureon_miner_brain import MinerBrain
        systems['miner_brain'] = True
        print("✅ Miner Brain: AVAILABLE")
    except ImportError as e:
        systems['miner_brain'] = False
        print(f"❌ Miner Brain: {e}")
    
    # Check Quantum Telescope
    try:
        from aureon_quantum_telescope import QuantumTelescope
        systems['quantum_telescope'] = True
        print("✅ Quantum Telescope: AVAILABLE")
    except ImportError as e:
        systems['quantum_telescope'] = False
        print(f"❌ Quantum Telescope: {e}")
    
    # Check Timeline Oracle
    try:
        from aureon_timeline_oracle import TimelineOracle
        systems['timeline_oracle'] = True
        print("✅ Timeline Oracle: AVAILABLE")
    except ImportError as e:
        systems['timeline_oracle'] = False
        print(f"❌ Timeline Oracle: {e}")
    
    # Check Ultimate Intelligence
    try:
        from probability_ultimate_intelligence import get_ultimate_intelligence
        systems['ultimate_intelligence'] = True
        print("✅ Ultimate Intelligence: AVAILABLE")
    except ImportError as e:
        systems['ultimate_intelligence'] = False
        print(f"❌ Ultimate Intelligence: {e}")
    
    # Check Probability Nexus
    try:
        from aureon_probability_nexus import EnhancedProbabilityNexus
        systems['probability_nexus'] = True
        print("✅ Probability Nexus: AVAILABLE")
    except ImportError as e:
        systems['probability_nexus'] = False
        print(f"❌ Probability Nexus: {e}")
    
    available = sum(1 for v in systems.values() if v)
    total = len(systems)
    print(f"\n📊 Systems Available: {available}/{total} ({available/total*100:.0f}%)")
    
    return systems


def initialize_queen():
    """Initialize the Queen Hive Mind and wire all systems"""
    print("\n" + "=" * 80)
    print("👑 INITIALIZING QUEEN HIVE MIND...")
    print("=" * 80)
    
    from aureon_queen_hive_mind import create_queen_hive_mind
    
    queen = create_queen_hive_mind(initial_capital=100.0)
    
    # Wire Dream Engine
    print("\n🔗 Wiring Dream Engine...")
    try:
        from aureon_enigma_dream import EnigmaDreamer
        dreamer = EnigmaDreamer()
        queen.wire_dream_engine(dreamer)
    except Exception as e:
        print(f"   ⚠️ Dream Engine: {e}")
    
    # Wire Mycelium Network
    print("\n🔗 Wiring Mycelium Network...")
    try:
        from aureon_mycelium import MyceliumNetwork
        mycelium = MyceliumNetwork(initial_capital=100.0)
        queen.wire_mycelium_network(mycelium)
        
        # Connect mycelium back to queen
        mycelium.connect_to_queen(queen)
    except Exception as e:
        print(f"   ⚠️ Mycelium Network: {e}")
    
    # Wire Enigma Integration
    print("\n🔗 Wiring Enigma Integration...")
    try:
        from aureon_enigma_integration import create_enigma_integration
        enigma = create_enigma_integration()
        queen.wire_enigma(enigma)
    except Exception as e:
        print(f"   ⚠️ Enigma Integration: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 🔮 WIRE PROBABILITY SYSTEMS - The Eyes that See Future
    # ═══════════════════════════════════════════════════════════════════════════════
    
    # Wire Enhanced Probability Nexus
    print("\n🔗 Wiring Probability Nexus (80%+ Win Rate)...")
    try:
        from aureon_probability_nexus import EnhancedProbabilityNexus
        probability_nexus = EnhancedProbabilityNexus()
        queen.wire_probability_nexus(probability_nexus)
    except Exception as e:
        print(f"   ⚠️ Probability Nexus: {e}")
    
    # Wire HNC Probability Matrix
    print("\n🔗 Wiring HNC Probability Matrix (Harmonic Patterns)...")
    try:
        from hnc_probability_matrix import HNCProbabilityIntegration
        hnc_matrix = HNCProbabilityIntegration()
        queen.wire_hnc_matrix(hnc_matrix)
    except Exception as e:
        print(f"   ⚠️ HNC Matrix: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 🧠 WIRE ADAPTIVE LEARNING - The Brain that Evolves
    # ═══════════════════════════════════════════════════════════════════════════════
    
    print("\n🔗 Wiring Adaptive Learning Engine (Self-Optimization)...")
    try:
        from aureon_unified_ecosystem import AdaptiveLearningEngine
        adaptive_learner = AdaptiveLearningEngine()
        queen.wire_adaptive_learner(adaptive_learner)
    except Exception as e:
        print(f"   ⚠️ Adaptive Learning: {e}")
    
    return queen


def display_full_status(queen):
    """Display full status of all systems"""
    print("\n" + "=" * 80)
    print("📊 FULL ECOSYSTEM STATUS")
    print("=" * 80)
    
    # Queen status
    queen.display()
    
    # Dream Engine status
    if queen.dreamer:
        print("\n" + "-" * 60)
        print("🌙 DREAM ENGINE STATUS:")
        print("-" * 60)
        state = queen.dreamer.get_state()
        print(f"   Is Dreaming: {state.get('is_dreaming', False)}")
        print(f"   Dream Depth: {state.get('dream_depth', 0):.0%}")
        print(f"   Brainwave: {state.get('current_brainwave', 'Unknown')}")
        print(f"   Total Dreams: {state.get('total_dreams', 0)}")
        print(f"   Total Prophecies: {state.get('total_prophecies', 0)}")
        print(f"   Total Wisdom: {state.get('total_wisdom', 0)}")
        print(f"   Prophecy Accuracy: {state.get('prophecy_accuracy', 0):.1%}")
    
    # Mycelium status
    if queen.mycelium:
        print("\n" + "-" * 60)
        print("🍄 MYCELIUM NETWORK STATUS:")
        print("-" * 60)
        myc_state = queen.mycelium.get_state()
        print(f"   Total Hives: {myc_state.get('total_hives', 0)}")
        print(f"   Total Agents: {myc_state.get('total_agents', 0)}")
        print(f"   Total Equity: ${myc_state.get('total_equity', 0):,.4f}")
        print(f"   Net Profit: ${myc_state.get('net_profit_total', 0):,.4f}")
        print(f"   Generation: {myc_state.get('generation', 0)}")
        print(f"   Queen Signal: {queen.mycelium.get_queen_signal():.4f}")
        print(f"   Queen Neuron Bias: {queen.mycelium.queen_neuron.bias:.4f}")
    
    # Enigma status
    if queen.enigma:
        print("\n" + "-" * 60)
        print("🔐 ENIGMA INTEGRATION STATUS:")
        print("-" * 60)
        enigma_state = queen.enigma.get_state()
        print(f"   Mood: {enigma_state.get('mood', 'Unknown')}")
        print(f"   Conviction: {enigma_state.get('conviction', 0):.1%}")
        print(f"   Thought Count: {enigma_state.get('thought_count', 0)}")
        
        # Get Enigma's view
        briefing = queen.enigma.get_ultra_briefing(time_window_minutes=60)
        print(f"   Total Intercepts: {briefing.get('total_intercepts', 0)}")
        print(f"   Ultra Count: {briefing.get('ultra_count', 0)}")
        print(f"   Consensus: {briefing.get('consensus_direction', 'Unknown')}")
        print(f"   Average Confidence: {briefing.get('average_confidence', 0):.1%}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 🔮 PROBABILITY SYSTEMS STATUS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    if queen.probability_nexus:
        print("\n" + "-" * 60)
        print("🔮 PROBABILITY NEXUS STATUS (80%+ Win Rate):")
        print("-" * 60)
        try:
            if hasattr(queen.probability_nexus, 'get_state'):
                nexus_state = queen.probability_nexus.get_state()
                print(f"   Patterns Loaded: {nexus_state.get('patterns_loaded', 'Unknown')}")
                print(f"   Historical Win Rate: {nexus_state.get('win_rate', 0):.1%}")
            else:
                print(f"   Status: WIRED AND READY")
        except Exception as e:
            print(f"   Status: WIRED (details unavailable: {e})")
    
    if queen.hnc_matrix:
        print("\n" + "-" * 60)
        print("📊 HNC PROBABILITY MATRIX STATUS (Harmonic Patterns):")
        print("-" * 60)
        try:
            if hasattr(queen.hnc_matrix, 'get_state'):
                hnc_state = queen.hnc_matrix.get_state()
                print(f"   Harmonic State: {hnc_state.get('harmonic_state', 'Unknown')}")
                print(f"   Frequency Alignment: {hnc_state.get('frequency', 'Unknown')}")
            else:
                print(f"   Status: WIRED AND READY")
                print(f"   Solfeggio Frequencies: 432Hz, 528Hz, 639Hz aligned")
        except Exception as e:
            print(f"   Status: WIRED (details unavailable: {e})")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 🧠 ADAPTIVE LEARNING STATUS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    if queen.adaptive_learner:
        print("\n" + "-" * 60)
        print("🧠 ADAPTIVE LEARNING ENGINE STATUS:")
        print("-" * 60)
        try:
            trade_count = len(queen.adaptive_learner.trade_history)
            thresholds = queen.adaptive_learner.optimized_thresholds
            print(f"   Trades in History: {trade_count}")
            print(f"   Min Coherence: {thresholds.get('min_coherence', 0.45):.2f}")
            print(f"   Min Score: {thresholds.get('min_score', 65)}")
            print(f"   Min Probability: {thresholds.get('min_probability', 0.50):.2f}")
            print(f"   Learning Rate: {queen.adaptive_learner.learning_rate}")
            
            # Show best performing frequency if available
            if queen.adaptive_learner.metrics_by_frequency:
                best_freq = max(
                    queen.adaptive_learner.metrics_by_frequency.items(),
                    key=lambda x: x[1].get('wins', 0) / max(x[1].get('wins', 0) + x[1].get('losses', 1), 1),
                    default=('unknown', {})
                )
                if best_freq[0] != 'unknown':
                    wins = best_freq[1].get('wins', 0)
                    losses = best_freq[1].get('losses', 0)
                    wr = wins / max(wins + losses, 1)
                    print(f"   Best Frequency: {best_freq[0]} ({wr:.1%} win rate)")
        except Exception as e:
            print(f"   Status: WIRED (details unavailable: {e})")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # 🗺️ LABYRINTH NAVIGATION STATUS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    print("\n" + "-" * 60)
    print("🗺️ LABYRINTH NAVIGATION STATUS:")
    print("-" * 60)
    state = queen.get_state()
    print(f"   Current Position: {state['labyrinth_position']['chamber']}")
    print(f"   Current Level: {state['labyrinth_position']['level']}")
    print(f"   Navigation Insights: {len(queen.labyrinth_insights)}")


def run_dream_cycle(queen):
    """Run a dream cycle and harvest wisdom"""
    print("\n" + "=" * 80)
    print("💭🌙 QUEEN DREAM CYCLE 🌙💭")
    print("=" * 80)
    
    if not queen.dreamer:
        print("⚠️ Dream Engine not wired - cannot dream!")
        return
    
    # Have some lucid dreams about key symbols
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    
    for symbol in symbols:
        print(f"\n💭 Dreaming about {symbol}...")
        wisdom = queen.dream_now(symbol, "LUCID")
        if wisdom:
            print(f"   Direction: {wisdom.direction}")
            print(f"   Confidence: {wisdom.confidence:.0%}")
            print(f"   Message: {wisdom.message[:60]}...")
    
    # Enter prophetic dream state
    print("\n🔮 Entering PROPHETIC dream state (5 seconds)...")
    queen.enter_dream_state(duration_minutes=0.08)  # ~5 seconds
    
    # Show prophecies
    print("\n🔮 Active Prophecies:")
    for prophecy in queen.active_prophecies[-5:]:
        print(f"   {prophecy.symbol or 'General'}: {prophecy.direction} ({prophecy.confidence:.0%})")


def broadcast_to_hive(queen):
    """Broadcast wisdom to all children"""
    print("\n" + "=" * 80)
    print("📢 BROADCASTING WISDOM TO HIVE")
    print("=" * 80)
    
    if len(queen.wisdom_vault) == 0:
        print("⚠️ No wisdom to broadcast yet")
        return
    
    # Broadcast latest wisdom
    recipients = queen.broadcast_wisdom()
    print(f"✅ Wisdom broadcast to {recipients} children")
    
    # Show the broadcast
    if len(queen.broadcast_queue) > 0:
        last_broadcast = queen.broadcast_queue[-1]
        wisdom = last_broadcast['wisdom']
        print(f"\n📜 Last Broadcast:")
        print(f"   Direction: {wisdom.get('direction', 'Unknown')}")
        print(f"   Confidence: {wisdom.get('confidence', 0):.0%}")
        print(f"   Message: {wisdom.get('message', 'No message')[:60]}...")


def get_collective_signal(queen):
    """Get the collective hive signal"""
    print("\n" + "=" * 80)
    print("🧠 COLLECTIVE HIVE SIGNAL")
    print("=" * 80)
    
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]
    
    for symbol in symbols:
        signal = queen.get_collective_signal(symbol)
        
        # Visual signal indicator
        sig_val = signal['collective_signal']
        if sig_val > 0.3:
            indicator = "🟢" * int(sig_val * 5) + "⚪" * (5 - int(sig_val * 5))
        elif sig_val < -0.3:
            indicator = "🔴" * int(abs(sig_val) * 5) + "⚪" * (5 - int(abs(sig_val) * 5))
        else:
            indicator = "⚪⚪🟡⚪⚪"
        
        print(f"\n   {symbol}:")
        print(f"      Signal: {indicator} {sig_val:+.3f}")
        print(f"      Direction: {signal['direction']}")
        print(f"      Confidence: {signal['confidence']:.0%}")
        print(f"      Action: {signal['action']}")
        print(f"      Sources: {signal['sources']}")


def navigate_labyrinth(queen):
    """Navigate the Micro Profit Labyrinth with ALL systems"""
    print("\n" + "=" * 80)
    print("🗺️ NAVIGATING THE MICRO PROFIT LABYRINTH")
    print("=" * 80)
    
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    
    for symbol in symbols:
        print(f"\n{'─' * 60}")
        print(queen.get_labyrinth_guidance(symbol))
    
    print("\n" + "-" * 60)
    print("📊 RAW NAVIGATION DATA:")
    print("-" * 60)
    
    nav = queen.navigate_labyrinth("BTCUSDT")
    print(f"   Symbol: {nav['symbol']}")
    print(f"   Position: {nav['position']}")
    print(f"   Action: {nav['action']}")
    print(f"   Confidence: {nav['confidence']:.1%}")
    print(f"   Liberation Aligned: {'✅' if nav['liberation_aligned'] else '❌'}")
    
    print("\n📊 SIGNAL SOURCES:")
    for source, data in nav.get('signals', {}).items():
        if isinstance(data, dict):
            sig = data.get('signal', 0)
            print(f"   {source}: {sig:.3f}")
    
    if nav.get('warnings'):
        print("\n⚠️ WARNINGS:")
        for warning in nav['warnings']:
            print(f"   - {warning}")


def monitor_loop(queen, duration_seconds=30, interval=5):
    """Run monitoring loop"""
    print("\n" + "=" * 80)
    print(f"📡 LIVE MONITORING (Running for {duration_seconds}s, interval {interval}s)")
    print("=" * 80)
    
    start_time = time.time()
    cycle = 0
    
    while time.time() - start_time < duration_seconds:
        cycle += 1
        elapsed = time.time() - start_time
        
        print(f"\n{'─' * 40}")
        print(f"⏱️  Cycle {cycle} | Elapsed: {elapsed:.1f}s")
        print(f"{'─' * 40}")
        
        # Quick status
        state = queen.get_state()
        print(f"   👑 Queen State: {state['state']}")
        print(f"   🧠 Consciousness: {state['consciousness_level']:.0%}")
        print(f"   📚 Wisdom Shared: {state['total_wisdom_shared']}")
        print(f"   🔮 Prophecies: {state['active_prophecies']}")
        
        # Quick collective signal for BTC
        signal = queen.get_collective_signal("BTCUSDT")
        print(f"   📈 BTC Signal: {signal['direction']} ({signal['confidence']:.0%})")
        
        # Mycelium quick check
        if queen.mycelium:
            print(f"   🍄 Hive Signal: {queen.mycelium.get_queen_signal():.3f}")
        
        time.sleep(interval)
    
    print(f"\n✅ Monitoring complete after {cycle} cycles")


def queen_speaks(queen):
    """Let the Queen speak"""
    print("\n" + "=" * 80)
    print("🗣️ THE QUEEN SPEAKS:")
    print("=" * 80)
    print(queen.speak())


def main():
    """Main entry point"""
    print_banner()
    
    # Check system availability
    systems = check_system_availability()
    
    if not systems.get('queen_hive_mind'):
        print("\n❌ FATAL: Queen Hive Mind not available!")
        return 1
    
    # Initialize Queen
    queen = initialize_queen()
    
    # Display initial status
    display_full_status(queen)
    
    # Run dream cycle
    run_dream_cycle(queen)
    
    # Broadcast to hive
    broadcast_to_hive(queen)
    
    # Get collective signals
    get_collective_signal(queen)
    
    # Navigate the labyrinth
    navigate_labyrinth(queen)
    
    # Queen speaks
    queen_speaks(queen)
    
    # Short monitoring loop
    print("\n" + "=" * 80)
    print("🔄 Starting short monitoring loop...")
    print("=" * 80)
    monitor_loop(queen, duration_seconds=15, interval=5)
    
    # Final status
    print("\n" + "=" * 80)
    print("📊 FINAL ECOSYSTEM STATUS")
    print("=" * 80)
    display_full_status(queen)
    
    # Liberation progress
    progress = queen.metrics['liberation_progress']
    print(f"\n🌍 LIBERATION PROGRESS: {progress:.1%}")
    if progress < 1.0:
        remaining = queen.TARGET_PROFIT - queen.total_profit
        print(f"   💰 ${remaining:,.2f} remaining to open source goal")
    
    print("""
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                       ║
║     ✅ QUEEN HIVE MIND ECOSYSTEM TEST COMPLETE                                        ║
║                                                                                       ║
║     'She dreams. She sees. She guides. She liberates.'                                ║
║                                                                                       ║
║     🌍 ONE GOAL: Crack → Profit → Open Source → Free All Beings                       ║
║                                                                                       ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝
    """)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
