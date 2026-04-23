#!/usr/bin/env python3
"""
Comprehensive integration test for research protocol modules:
  1. Cross-Substrate Solar Monitor
  2. Phase Transition Detector
  3. Bitcoin Lighthouse Forensics
  4. Statistical Analysis Engine (Granger, PCA, cross-correlation)
  5. Full pipeline integration

Gary Leckey | February 2026
"""

import sys
import os
import time
import math
import traceback
import numpy as np

# Track results
PASS = 0
FAIL = 0
TESTS = []

def test(name):
    """Test decorator."""
    def wrapper(func):
        def runner():
            global PASS, FAIL
            try:
                print(f"\n{'='*60}")
                print(f"TEST: {name}")
                print(f"{'='*60}")
                result = func()
                if result:
                    PASS += 1
                    TESTS.append((name, "PASS"))
                    print(f"  PASS: {name}")
                else:
                    FAIL += 1
                    TESTS.append((name, "FAIL"))
                    print(f"  FAIL: {name}")
            except Exception as e:
                FAIL += 1
                TESTS.append((name, f"ERROR: {e}"))
                print(f"  ERROR: {name} - {e}")
                traceback.print_exc()
        return runner
    return wrapper


# ===========================================================================
# TEST 1: Phase Transition Detector
# ===========================================================================

@test("Phase Transition Detector - Core Math")
def test_phase_detector_core():
    from aureon_phase_transition_detector import (
        PhaseSpaceEmbedder, GeometricAnalyzer,
        PhaseTransitionDetector, PhaseState
    )

    # Test Takens embedding
    embedder = PhaseSpaceEmbedder(dimension=5, time_delay=1)
    signal = np.sin(np.linspace(0, 4 * np.pi, 100))
    embedded = embedder.embed(signal)
    assert embedded.shape[1] == 5, f"Embedding dim wrong: {embedded.shape[1]}"
    assert embedded.shape[0] == 96, f"Embedding rows wrong: {embedded.shape[0]}"
    print(f"  Takens embedding: {embedded.shape} - OK")

    # Test curvature
    trajectory = embedded
    curvature = GeometricAnalyzer.compute_curvature(trajectory)
    assert len(curvature) == len(trajectory), "Curvature length mismatch"
    assert np.all(np.isfinite(curvature)), "Curvature has inf/nan"
    print(f"  Curvature range: [{curvature.min():.4f}, {curvature.max():.4f}] - OK")

    # Test coherence
    coherence = GeometricAnalyzer.compute_coherence(trajectory)
    assert 0 <= coherence <= 1, f"Coherence out of range: {coherence}"
    print(f"  Coherence: {coherence:.4f} - OK")

    # Test dimension estimation
    dim = GeometricAnalyzer.estimate_dimension(trajectory)
    assert dim >= 1, f"Dimension too low: {dim}"
    print(f"  Intrinsic dimension: {dim:.2f} - OK")

    return True


@test("Phase Transition Detector - Regime Detection")
def test_phase_detector_regimes():
    from aureon_phase_transition_detector import PhaseTransitionDetector, PhaseState

    detector = PhaseTransitionDetector(embedding_dim=8, memory_length=80)

    # Generate stable regime then crash
    np.random.seed(42)
    prices = [100.0]
    for i in range(250):
        if i < 120:
            ret = 0.0001 + 0.005 * np.random.randn()  # Stable
        elif i < 160:
            ret = -0.008 + 0.02 * np.random.randn()  # Crash
        else:
            ret = 0.002 + 0.01 * np.random.randn()  # Recovery
        prices.append(prices[-1] * (1 + ret))

    states_seen = set()
    for i, price in enumerate(prices):
        sig = detector.ingest(price, timestamp=float(i))
        if sig is not None:
            pred = detector.predict()
            if pred is not None:
                states_seen.add(pred.state)

    print(f"  States observed: {[s.value for s in states_seen]}")
    print(f"  Transitions detected: {len(detector.transition_history)}")
    assert len(states_seen) >= 1, "Should detect at least 1 state"
    assert len(detector.signature_history) > 0, "Should extract signatures"

    # Test navigation signal
    nav = detector.get_navigation_signal()
    assert nav in ("ENTER", "EXIT", "HOLD"), f"Invalid nav signal: {nav}"
    print(f"  Final navigation signal: {nav} - OK")

    return True


@test("Phase Transition Detector - Multi-Symbol Monitor")
def test_multi_symbol():
    from aureon_phase_transition_detector import MultiSymbolPhaseMonitor

    symbols = ["BTC", "ETH", "SOL"]
    monitor = MultiSymbolPhaseMonitor(symbols)

    np.random.seed(123)
    for t in range(200):
        for sym in symbols:
            price = 100 + t * 0.1 + np.random.randn() * 2
            monitor.ingest(sym, price, timestamp=float(t))

    result = monitor.scan_all()
    print(f"  Global state: {result['global_state']}")
    print(f"  Symbols with data: {result['symbols_with_data']}")
    print(f"  State distribution: {result['state_distribution']}")
    assert result["symbols_monitored"] == 3
    return True


# ===========================================================================
# TEST 2: Cross-Substrate Monitor
# ===========================================================================

@test("Cross-Substrate Monitor - Data Structures")
def test_cross_substrate_structures():
    from aureon_cross_substrate_monitor import (
        SolarSnapshot, SubstrateSnapshot, CrossSubstrateEvent,
        FLARE_THRESHOLD_FLUX
    )

    solar = SolarSnapshot(
        timestamp="2026-02-13T00:00:00Z",
        xray_flux=1e-4,  # X1.0 class
        kp_index=6,
        solar_wind_speed=800,
        proton_density=15.0,
        bz_component=-10.0,
    )
    assert solar.is_storm(), "Kp=6 should be storm"
    assert solar.is_flare(), "X1.0 should be flare"
    print(f"  Solar snapshot: storm={solar.is_storm()}, flare={solar.is_flare()} - OK")

    quiet = SolarSnapshot(
        timestamp="2026-02-13T00:00:00Z",
        xray_flux=1e-7,
        kp_index=2,
        solar_wind_speed=350,
        proton_density=5.0,
        bz_component=2.0,
    )
    assert not quiet.is_storm(), "Kp=2 should not be storm"
    assert not quiet.is_flare(), "1e-7 should not be flare"
    print(f"  Quiet solar: storm={quiet.is_storm()}, flare={quiet.is_flare()} - OK")

    return True


@test("Cross-Substrate Analyzer - Cross-Correlation")
def test_cross_correlation():
    from aureon_cross_substrate_monitor import CrossSubstrateAnalyzer

    analyzer = CrossSubstrateAnalyzer()

    # Correlated signals with lag
    np.random.seed(42)
    n = 200
    solar = np.random.randn(n)
    # Substrate lags solar by 3 steps
    substrate = np.roll(solar, 3) * 0.8 + np.random.randn(n) * 0.3

    result = analyzer.cross_correlation(solar, substrate, max_lag=10)
    print(f"  Peak correlation: {result['peak_correlation']}")
    print(f"  Peak lag: {result['peak_lag_hours']}h")
    print(f"  Significant: {result['significant']}")

    assert abs(result["peak_correlation"]) > 0.2, "Should find correlation"
    return True


@test("Cross-Substrate Analyzer - Granger Causality")
def test_granger():
    from aureon_cross_substrate_monitor import CrossSubstrateAnalyzer

    analyzer = CrossSubstrateAnalyzer()

    # Create causal relationship: x causes y with 2-step lag
    np.random.seed(42)
    n = 300
    x = np.random.randn(n)
    y = np.zeros(n)
    for i in range(2, n):
        y[i] = 0.6 * y[i - 1] + 0.4 * x[i - 2] + 0.2 * np.random.randn()

    result = analyzer.granger_causality(x, y, max_lag=5)
    print(f"  Min p-value: {result['min_p_value']:.6f}")
    print(f"  Best lag: {result['best_lag_hours']}h")
    print(f"  Significant: {result['significant']}")

    # Should detect causality
    assert result["min_p_value"] < 0.05, f"Should detect causality: p={result['min_p_value']}"
    return True


@test("Cross-Substrate Analyzer - PCA Unified System Test")
def test_pca():
    from aureon_cross_substrate_monitor import CrossSubstrateAnalyzer

    analyzer = CrossSubstrateAnalyzer()

    # Case 1: Unified system (all driven by single factor)
    np.random.seed(42)
    n = 100
    driver = np.random.randn(n)
    unified = np.column_stack([
        driver + 0.1 * np.random.randn(n),
        driver * 0.9 + 0.1 * np.random.randn(n),
        driver * 1.1 + 0.1 * np.random.randn(n),
    ])

    result = analyzer.pca_unified_system_test(unified)
    print(f"  Unified system PC1: {result['pc1_variance']:.4f}")
    print(f"  Is unified: {result['unified']}")
    assert result["pc1_variance"] > 0.80, "Should detect unified system"

    # Case 2: Independent systems
    independent = np.column_stack([
        np.random.randn(n),
        np.random.randn(n),
        np.random.randn(n),
    ])
    result2 = analyzer.pca_unified_system_test(independent)
    print(f"  Independent PC1: {result2['pc1_variance']:.4f}")
    print(f"  Is unified: {result2['unified']}")
    assert not result2["unified"], "Should not detect unified system for independent data"

    return True


@test("Cross-Substrate Analyzer - Falsification Check")
def test_falsification():
    from aureon_cross_substrate_monitor import CrossSubstrateAnalyzer

    analyzer = CrossSubstrateAnalyzer()

    # Scenario: hypothesis should be falsified (weak evidence)
    weak_corrs = [
        {"peak_correlation": 0.1, "peak_lag_hours": 3, "significant": False},
        {"peak_correlation": 0.15, "peak_lag_hours": 8, "significant": False},
        {"peak_correlation": 0.05, "peak_lag_hours": -2, "significant": False},
    ]
    weak_pca = {"pc1_variance": 0.35, "unified": False}
    weak_granger = [{"min_p_value": 0.4, "significant": False}]

    result = analyzer.check_falsification(weak_corrs, weak_pca, weak_granger)
    print(f"  Falsified: {result['falsified']}")
    print(f"  Reasons: {result['reasons']}")
    assert result["falsified"], "Weak evidence should falsify hypothesis"

    # Scenario: hypothesis survives (strong evidence)
    strong_corrs = [
        {"peak_correlation": 0.7, "peak_lag_hours": 3, "significant": True},
        {"peak_correlation": 0.65, "peak_lag_hours": 4, "significant": True},
        {"peak_correlation": 0.8, "peak_lag_hours": 3, "significant": True},
    ]
    strong_pca = {"pc1_variance": 0.92, "unified": True}
    strong_granger = [{"min_p_value": 0.001, "significant": True}]

    result2 = analyzer.check_falsification(strong_corrs, strong_pca, strong_granger)
    print(f"  Survives: {not result2['falsified']}")
    assert not result2["falsified"], "Strong evidence should survive falsification"

    return True


# ===========================================================================
# TEST 3: Bitcoin Lighthouse Forensics (existing module)
# ===========================================================================

@test("Bitcoin Lighthouse Forensics - Pattern Recognition")
def test_lighthouse_forensics():
    from bitcoin_lighthouse_forensics import (
        LighthousePatternRecognition, LighthouseSignature
    )

    lpr = LighthousePatternRecognition(embedding_dim=8, memory_length=100)

    # Generate returns
    np.random.seed(42)
    returns = np.random.randn(120) * 0.01

    sig = lpr.extract_signature(returns, idx=0)
    assert isinstance(sig, LighthouseSignature)
    assert 0 <= sig.coherence <= 1, f"Coherence out of range: {sig.coherence}"
    assert np.isfinite(sig.curvature), "Curvature should be finite"
    print(f"  Curvature: {sig.curvature:.4f}")
    print(f"  Coherence: {sig.coherence:.4f}")
    print(f"  Dimension: {sig.dimension:.2f}")

    pred = lpr.predict_transition(sig)
    assert "transition_probability" in pred
    assert "risk_state" in pred
    print(f"  Transition probability: {pred['transition_probability']:.4f}")
    print(f"  Risk state: {pred['risk_state']}")

    return True


# ===========================================================================
# TEST 4: Integration - Phase Detector + Lighthouse
# ===========================================================================

@test("Integration - Phase Detector + Lighthouse Pipeline")
def test_integration_pipeline():
    from aureon_phase_transition_detector import PhaseTransitionDetector
    from bitcoin_lighthouse_forensics import LighthousePatternRecognition

    # Both systems analyze the same price data
    np.random.seed(42)
    prices = [50000.0]
    for i in range(300):
        if i < 150:
            ret = 0.0001 + 0.012 * np.random.randn()
        elif i < 200:
            ret = -0.004 + 0.025 * np.random.randn()
        else:
            ret = 0.001 + 0.015 * np.random.randn()
        prices.append(prices[-1] * (1 + ret))

    prices = np.array(prices)
    returns = np.diff(np.log(prices))

    # Phase detector
    detector = PhaseTransitionDetector(embedding_dim=8, memory_length=100)
    phase_signals = []
    for i, p in enumerate(prices):
        sig = detector.ingest(p, timestamp=float(i))
        if sig is not None:
            pred = detector.predict()
            if pred is not None:
                phase_signals.append(pred.state.value)

    # Lighthouse
    lighthouse = LighthousePatternRecognition(embedding_dim=8, memory_length=100)
    lh_signals = []
    for i in range(100, len(returns)):
        window = returns[i - 100:i]
        sig = lighthouse.extract_signature(window, idx=i)
        pred = lighthouse.predict_transition(sig)
        lh_signals.append(pred["risk_state"])

    print(f"  Phase detector signals: {len(phase_signals)}")
    print(f"  Lighthouse signals: {len(lh_signals)}")

    # Both should detect the crash regime
    phase_states = set(phase_signals)
    lh_states = set(lh_signals)
    print(f"  Phase states seen: {phase_states}")
    print(f"  Lighthouse states seen: {lh_states}")

    assert len(phase_states) >= 1, "Phase detector should detect states"
    assert len(lh_states) >= 1, "Lighthouse should produce states"
    assert len(phase_signals) > 100, "Phase detector should produce many signals"
    assert len(lh_signals) > 100, "Lighthouse should produce many signals"

    return True


# ===========================================================================
# TEST 5: Solar Monitor Collection
# ===========================================================================

@test("Cross-Substrate Monitor - Collection Cycle")
def test_monitor_collection():
    from aureon_cross_substrate_monitor import CrossSubstrateMonitor

    monitor = CrossSubstrateMonitor()

    # Simulate 5 collection cycles
    for i in range(5):
        snapshot = monitor.collect_snapshot()
        assert "substrate" in snapshot
        assert "collection_number" in snapshot
        assert snapshot["collection_number"] == i + 1

    summary = monitor.get_collection_summary()
    print(f"  Total snapshots: {summary['total_snapshots']}")
    print(f"  Days collected: {summary['days_collected']}")
    print(f"  Completion: {summary['completion_pct']}%")
    assert summary["total_snapshots"] == 5

    return True


# ===========================================================================
# TEST 6: Ecosystem Integration Check
# ===========================================================================

@test("Ecosystem Integration - Module Imports")
def test_ecosystem_imports():
    """Verify new modules can be imported alongside existing ones."""
    modules_loaded = []

    try:
        from aureon_phase_transition_detector import PhaseTransitionDetector
        modules_loaded.append("phase_transition_detector")
    except ImportError as e:
        print(f"  WARNING: phase_transition_detector: {e}")

    try:
        from aureon_cross_substrate_monitor import CrossSubstrateMonitor
        modules_loaded.append("cross_substrate_monitor")
    except ImportError as e:
        print(f"  WARNING: cross_substrate_monitor: {e}")

    try:
        from bitcoin_lighthouse_forensics import BitcoinLighthouseForensics
        modules_loaded.append("bitcoin_lighthouse_forensics")
    except ImportError as e:
        print(f"  WARNING: bitcoin_lighthouse_forensics: {e}")

    try:
        from aureon_lighthouse import LighthouseEventType
        modules_loaded.append("aureon_lighthouse")
    except ImportError as e:
        print(f"  WARNING: aureon_lighthouse: {e}")

    try:
        from queen_solar_system_awareness import QueenSolarSystemAwareness
        modules_loaded.append("queen_solar_system_awareness")
    except ImportError as e:
        print(f"  WARNING: queen_solar_system_awareness: {e}")

    print(f"  Modules loaded: {len(modules_loaded)}/{5}")
    for m in modules_loaded:
        print(f"    {m}")

    assert len(modules_loaded) >= 3, f"Need at least 3 modules, got {len(modules_loaded)}"
    return True


# ===========================================================================
# RUN ALL TESTS
# ===========================================================================

def main():
    print("\n" + "=" * 60)
    print("RESEARCH PROTOCOL - COMPREHENSIVE INTEGRATION TEST")
    print("Gary Leckey | February 2026")
    print("=" * 60)

    tests = [
        test_phase_detector_core,
        test_phase_detector_regimes,
        test_multi_symbol,
        test_cross_substrate_structures,
        test_cross_correlation,
        test_granger,
        test_pca,
        test_falsification,
        test_lighthouse_forensics,
        test_integration_pipeline,
        test_monitor_collection,
        test_ecosystem_imports,
    ]

    for t in tests:
        t()

    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    for name, result in TESTS:
        icon = "PASS" if result == "PASS" else "FAIL"
        print(f"  [{icon}] {name}")

    print(f"\n  Total: {PASS + FAIL}")
    print(f"  Passed: {PASS}")
    print(f"  Failed: {FAIL}")

    if FAIL == 0:
        print("\n  ALL TESTS PASSED")
    else:
        print(f"\n  {FAIL} TEST(S) FAILED")

    return FAIL == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
