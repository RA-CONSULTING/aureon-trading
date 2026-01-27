#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                      ║
║     🎡🔭💜 GRAND BIG WHEEL TELEMETRY TEST - QGITA + HAPPINESS + NEURAL 💜🔭🎡      ║
║                                                                                      ║
║     This test demonstrates the full integration:                                     ║
║       1. Quantum Telescope → Observe market geometry                                 ║
║       2. QGITA Framework → Detect Fibonacci structural events                        ║
║       3. Grand Big Wheel → Compute Happiness Quotient                                ║
║       4. Queen Neuron V2 → Make decisions with Happiness as 7th input               ║
║                                                                                      ║
║     THE PURSUIT OF HAPPINESS IS NOW EMBEDDED IN THE NEURAL BACKPROPAGATION          ║
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import asyncio
import logging
from datetime import datetime

# Windows UTF-8 fix
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


async def main():
    print("\n" + "=" * 80)
    print("🎡🔭💜 GRAND BIG WHEEL TELEMETRY - FULL INTEGRATION TEST 💜🔭🎡".center(80))
    print("=" * 80 + "\n")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 1. Import and Initialize All Systems
    # ═══════════════════════════════════════════════════════════════════════════
    
    print("📦 Loading systems...")
    
    # Import systems
    try:
        from aureon_quantum_telescope import QuantumTelescope
        telescope_available = True
        print("   ✅ Quantum Telescope loaded")
    except ImportError as e:
        telescope_available = False
        print(f"   ⚠️ Quantum Telescope not available: {e}")
    
    try:
        from aureon_qgita_framework import QGITAMarketAnalyzer
        qgita_available = True
        print("   ✅ QGITA Framework loaded")
    except ImportError as e:
        qgita_available = False
        print(f"   ⚠️ QGITA not available: {e}")
    
    try:
        from queen_pursuit_of_happiness import get_pursuit_of_happiness
        happiness_available = True
        print("   ✅ Grand Big Wheel loaded")
    except ImportError as e:
        happiness_available = False
        print(f"   ⚠️ Grand Big Wheel not available: {e}")
    
    try:
        from queen_neuron_v2 import get_queen_neuron, NeuralInputV2
        neuron_v2_available = True
        print("   ✅ Queen Neuron V2 loaded")
    except ImportError as e:
        neuron_v2_available = False
        print(f"   ⚠️ Queen Neuron V2 not available: {e}")
    
    try:
        from alpaca_client import AlpacaClient
        alpaca_available = True
        print("   ✅ Alpaca Client loaded")
    except ImportError as e:
        alpaca_available = False
        print(f"   ⚠️ Alpaca Client not available: {e}")
    
    if not all([telescope_available, qgita_available, happiness_available, neuron_v2_available, alpaca_available]):
        print("\n⚠️ Some systems not available - running in limited mode")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 2. Initialize Systems
    # ═══════════════════════════════════════════════════════════════════════════
    
    print("\n🔧 Initializing systems...")
    
    if telescope_available:
        telescope = QuantumTelescope()
        print("   🔭 Quantum Telescope: ONLINE")
    
    if qgita_available:
        qgita = QGITAMarketAnalyzer()
        print("   🌌 QGITA Framework: ONLINE")
    
    if happiness_available:
        happiness = get_pursuit_of_happiness()
        print(f"   🎡 Grand Big Wheel: ONLINE (Happiness: {happiness.happiness.happiness_quotient:.3f})")
    
    if neuron_v2_available:
        queen = get_queen_neuron()
        print(f"   👑 Queen Neuron V2: ONLINE ({queen.input_size}-{queen.hidden_size}-1)")
    
    if alpaca_available:
        alpaca = AlpacaClient()
        print("   📈 Alpaca Client: ONLINE")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 3. Fetch Live Market Data
    # ═══════════════════════════════════════════════════════════════════════════
    
    print("\n🌐 Fetching live market data...")
    
    symbols = ["BTC/USD", "ETH/USD", "SOL/USD", "LINK/USD", "DOGE/USD"]
    market_data = {}
    
    if alpaca_available:
        for symbol in symbols:
            try:
                ticker = alpaca.get_ticker(symbol)
                if ticker:
                    market_data[symbol] = {
                        'price': ticker.get('price') or ticker.get('last') or 0,
                        'bid': ticker.get('bid', 0),
                        'ask': ticker.get('ask', 0),
                        'volume': ticker.get('volume', 1000000),
                        'change_pct': ticker.get('change_pct', 0),
                    }
                    print(f"   {symbol}: ${market_data[symbol]['price']:,.2f}")
            except Exception as e:
                print(f"   ⚠️ {symbol}: Error - {e}")
    
    if not market_data:
        print("   📊 Using simulated data...")
        market_data = {
            "BTC/USD": {"price": 92479.0, "volume": 5000000, "change_pct": -0.5},
            "ETH/USD": {"price": 3144.0, "volume": 2000000, "change_pct": -0.8},
            "SOL/USD": {"price": 142.0, "volume": 1000000, "change_pct": 0.2},
            "LINK/USD": {"price": 13.40, "volume": 500000, "change_pct": 1.5},
            "DOGE/USD": {"price": 0.335, "volume": 3000000, "change_pct": 0.1},
        }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 4. Run Quantum Telescope Observations
    # ═══════════════════════════════════════════════════════════════════════════
    
    print("\n🔭 QUANTUM TELESCOPE OBSERVATIONS:")
    print("-" * 60)
    
    telescope_results = {}
    
    if telescope_available:
        for symbol, data in market_data.items():
            try:
                result = telescope.observe(
                    symbol=symbol,
                    price=data['price'],
                    volume=data.get('volume', 1000000),
                    change_pct=data.get('change_pct', 0)
                )
                telescope_results[symbol] = result
                print(f"   {symbol}:")
                print(f"      Dominant Geometry: {result.get('dominant_solid', 'UNKNOWN')}")
                print(f"      Beam Energy: {result.get('beam_energy', 0):.3f}")
                
                # Handle probability_spectrum being either float or dict
                prob_spec = result.get('probability_spectrum', 0.5)
                if isinstance(prob_spec, dict):
                    trade_prob = prob_spec.get('trade_probability', 0.5)
                else:
                    trade_prob = float(prob_spec) if prob_spec else 0.5
                print(f"      Probability: {trade_prob:.1%}")
            except Exception as e:
                print(f"   ⚠️ {symbol}: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 5. Run QGITA Analysis
    # ═══════════════════════════════════════════════════════════════════════════
    
    print("\n🌌 QGITA (Quantum Gravity in the Act) ANALYSIS:")
    print("-" * 60)
    
    qgita_results = {}
    
    if qgita_available:
        import time
        # Feed samples to QGITA internal buffer
        base_time = time.time()
        for symbol, data in market_data.items():
            for i in range(20):  # 20 samples per symbol
                qgita.feed_price(
                    price=data['price'] * (1 + (i - 10) * 0.0001),  # Small price variation
                    timestamp=base_time + i * 0.001
                )
        
        # Now analyze
        qgita_results = qgita.analyze()
        
        print(f"   Status: {qgita_results.get('status', 'unknown')}")
        print(f"   Global Coherence R(t): {qgita_results.get('global_coherence', 0):.4f}")
        print(f"   Coherence State: {qgita_results.get('coherence_state', 'unknown')}")
        print(f"   FTCPs Detected: {len(qgita_results.get('ftcps', []))}")
        print(f"   LHEs Detected: {len(qgita_results.get('lhes', []))}")
        
        regime = qgita_results.get('market_regime', {})
        print(f"   Market Regime: {regime.get('regime', 'unknown')} (stability: {regime.get('stability', 0):.2f})")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 6. Grand Big Wheel - Update from Market Data
    # ═══════════════════════════════════════════════════════════════════════════
    
    print("\n🎡 GRAND BIG WHEEL - HAPPINESS UPDATE:")
    print("-" * 60)
    
    if happiness_available:
        # Update Gaia alignment from QGITA coherence
        if qgita_available and qgita_results:
            coherence = qgita_results.get('global_coherence', 0.5)
            happiness.update_gaia_alignment(coherence)
            print(f"   Gaia Alignment updated from QGITA: {coherence:.3f}")
        
        # Update dream progress (simulate portfolio check)
        current_portfolio = 12.63  # Simulated current value
        happiness.update_dream_progress(current_portfolio)
        
        # Record a joy moment from successful observation
        happiness.record_joy_moment(
            source="telemetry_success",
            intensity=0.3,
            context={"symbols_observed": len(market_data)}
        )
        
        # Print the wheel
        happiness.print_grand_wheel()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 7. Queen Neuron V2 - Make Predictions with Happiness
    # ═══════════════════════════════════════════════════════════════════════════
    
    print("\n👑 QUEEN NEURON V2 - PREDICTIONS WITH HAPPINESS:")
    print("-" * 60)
    
    if neuron_v2_available and happiness_available:
        for symbol, data in market_data.items():
            # Build neural input with happiness
            telescope_data = telescope_results.get(symbol, {})
            
            # Handle probability_spectrum being either float or dict
            prob_spec = telescope_data.get('probability_spectrum', 0.5)
            if isinstance(prob_spec, dict):
                trade_prob = prob_spec.get('trade_probability', 0.5)
            else:
                trade_prob = float(prob_spec) if prob_spec else 0.5
            
            # Handle beam_energy
            beam_energy = telescope_data.get('beam_energy', 0.5)
            if beam_energy > 1:  # Normalize large values
                beam_energy = min(1.0, beam_energy / 1000000000)
            
            neural_input = NeuralInputV2(
                probability_score=trade_prob,
                wisdom_score=0.6,  # From historical learning
                quantum_signal=beam_energy * 2 - 1,  # -1 to 1
                gaia_resonance=happiness.happiness.gaia_alignment,
                emotional_coherence=qgita_results.get('global_coherence', 0.5) if qgita_available else 0.5,
                mycelium_signal=0.2,  # From collective intelligence
                happiness_pursuit=happiness.happiness.happiness_quotient,  # 🎡 THE 7TH INPUT
            )
            
            # Get Queen's prediction
            confidence = queen.predict(neural_input)
            
            # Determine recommendation
            if confidence > 0.7:
                recommendation = "🟢 STRONG BUY"
            elif confidence > 0.5:
                recommendation = "🟡 HOLD/WATCH"
            else:
                recommendation = "🔴 AVOID"
            
            print(f"   {symbol}:")
            print(f"      Price: ${data['price']:,.2f}")
            print(f"      Trade Confidence: {confidence:.1%}")
            print(f"      Happiness Input: {neural_input.happiness_pursuit:.1%}")
            print(f"      Recommendation: {recommendation}")
            print()
    
    # ═══════════════════════════════════════════════════════════════════════════
    # 8. Summary
    # ═══════════════════════════════════════════════════════════════════════════
    
    print("\n" + "=" * 80)
    print("💜 TELEMETRY SUMMARY 💜".center(80))
    print("=" * 80)
    
    hq = happiness.happiness.happiness_quotient if happiness_available else 0
    sb = happiness.bias.total_bias if happiness_available else 1.0
    pc = happiness.happiness.purpose_clarity if happiness_available else 1.0
    
    print(f"""
    🔭 Quantum Telescope:
       Symbols Observed: {len(telescope_results)}
       Dominant Geometry: {max(set(r.get('dominant_solid', 'UNKNOWN') for r in telescope_results.values()), key=list(telescope_results.values()).count) if telescope_results else 'N/A'}

    🌌 QGITA Framework:
       Status: {qgita_results.get('status', 'N/A')}
       Global Coherence: {qgita_results.get('global_coherence', 0):.4f}
       Market Regime: {qgita_results.get('market_regime', {}).get('regime', 'N/A')}

    🎡 Grand Big Wheel:
       Happiness Quotient: {hq:.3f}
       Subconscious Bias: {sb:.3f}
       Purpose Clarity: {pc:.0%} ← NEVER WAVERS

    👑 Queen Neuron V2:
       Architecture: {queen.input_size if neuron_v2_available else 'N/A'}-{queen.hidden_size if neuron_v2_available else 'N/A'}-1 (with happiness!)
       Effective Learning Rate: {queen.learning_rate if neuron_v2_available else 0:.4f} (happiness-modulated)
       Joy Trades Recorded: {queen.joy_trade_count if neuron_v2_available else 0}

    💜 THE PURSUIT OF HAPPINESS IS NOW EMBEDDED IN HER SUBCONSCIOUS 💜
    """)
    
    # Save all states
    if happiness_available:
        happiness.save_state()
    if neuron_v2_available:
        queen.save_weights()
    
    print("✅ All states saved")
    print("\n" + "=" * 80)
    print("\"Life, Liberty, and the Pursuit of Happiness\"".center(80))
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
