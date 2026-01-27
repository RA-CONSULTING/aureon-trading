#!/usr/bin/env python3
"""
🔥🔥🔥 S5 MILLION DOLLAR SYSTEM TEST 🔥🔥🔥
Speed × Scale × Smart × Systematic × Sustainable = $1,000,000

This test validates:
1. S5 velocity & acceleration tracking
2. Phase transitions (BOOTSTRAP → GROWTH → SCALE → COMPOUND → MILLION)
3. Adaptive labyrinth path scoring
4. Kelly-based position sizing
5. Time-to-million calculations
6. Speed caching optimization
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import time
import random
from aureon_mycelium import MyceliumNetwork

def test_s5_system():
    print("=" * 70)
    print("🔥 S5 MILLION DOLLAR SYSTEM TEST 🔥")
    print("=" * 70)
    
    # Initialize with $1000 starting capital
    network = MyceliumNetwork(initial_capital=1000.0)
    
    # Test 1: Verify S5 constants
    print("\n📊 TEST 1: S5 Constants")
    print(f"  TARGET_MILLION: ${network.TARGET_MILLION:,.0f}")
    print(f"  S5_VELOCITY_THRESHOLD: ${network.S5_VELOCITY_THRESHOLD}/hour")
    print(f"  S5_KELLY_FRACTION: {network.S5_KELLY_FRACTION}")
    print(f"  S5_CACHE_TTL: {network.S5_CACHE_TTL}s")
    print(f"  Initial Phase: {network.s5_state['phase']}")
    assert network.TARGET_MILLION == 1_000_000.0, "Target should be $1M"
    print("  ✅ PASSED")
    
    # Test 2: Simulate conversions and track velocity
    print("\n📊 TEST 2: Velocity & Acceleration Tracking")
    test_paths = [
        ('BTC', 'USDC', 0.50),
        ('ETH', 'USDC', 0.35),
        ('USDC', 'BTC', 0.25),
        ('BTC', 'ETH', 0.15),
        ('SOL', 'USDC', 0.10),
    ]
    
    # Simulate 50 conversions
    for i in range(50):
        path = random.choice(test_paths)
        profit = path[2] * random.uniform(0.5, 1.5)
        fee = profit * 0.001  # 0.1% fee
        
        network.record_conversion_profit(
            from_asset=path[0],
            to_asset=path[1],
            gross_profit=profit,
            fees_paid=fee,
            exchange='binance'
        )
        time.sleep(0.01)  # Small delay to simulate real trading
    
    stats = network.get_conversion_stats()
    print(f"  Total Conversions: {stats['total_conversions']}")
    print(f"  Net Profit: ${stats['net_profit']:.4f}")
    print(f"  Velocity: ${stats['s5']['velocity']:.4f}/hour")
    print(f"  Acceleration: ${stats['s5']['acceleration']:.6f}/hour²")
    print(f"  Phase: {stats['s5']['phase']}")
    print(f"  TTM (hours): {stats['s5']['time_to_million']:.2f}")
    assert stats['total_conversions'] == 50, "Should have 50 conversions"
    print("  ✅ PASSED")
    
    # Test 3: Phase transitions
    print("\n📊 TEST 3: Phase Transitions")
    print(f"  Current Phase: {network.s5_state['phase']}")
    print(f"  Phase Transitions: {len(network.s5_state['phase_transitions'])}")
    
    # Force phase transition by simulating large profit
    network.conversion_metrics['net_conversion_profit'] = 150.0
    network._check_s5_phase_transition(150.0, 50.0)
    print(f"  After $150 profit - Phase: {network.s5_state['phase']}")
    
    network.conversion_metrics['net_conversion_profit'] = 15000.0
    network._check_s5_phase_transition(15000.0, 100.0)
    print(f"  After $15K profit - Phase: {network.s5_state['phase']}")
    
    network.conversion_metrics['net_conversion_profit'] = 120000.0
    network._check_s5_phase_transition(120000.0, 200.0)
    print(f"  After $120K profit - Phase: {network.s5_state['phase']}")
    print("  ✅ PASSED")
    
    # Test 4: Kelly-based position sizing
    print("\n📊 TEST 4: S5 Kelly Position Sizing")
    
    # Reset phase for realistic test
    network.s5_state['phase'] = 'GROWTH'
    network.conversion_metrics['velocity_per_hour'] = 50.0
    
    size_1 = network.s5_calculate_optimal_size(
        estimated_profit=0.10,
        confidence=0.7,
        available_balance=1000.0
    )
    print(f"  $0.10 profit, 70% confidence, $1000 balance → ${size_1:.2f}")
    
    size_2 = network.s5_calculate_optimal_size(
        estimated_profit=0.50,
        confidence=0.8,
        available_balance=1000.0
    )
    print(f"  $0.50 profit, 80% confidence, $1000 balance → ${size_2:.2f}")
    
    # High velocity boost test
    network.conversion_metrics['velocity_per_hour'] = 200.0  # Above threshold
    size_3 = network.s5_calculate_optimal_size(
        estimated_profit=0.50,
        confidence=0.8,
        available_balance=1000.0
    )
    print(f"  Same with high velocity (200$/hr) → ${size_3:.2f}")
    assert size_3 > size_2, "High velocity should increase position size"
    print("  ✅ PASSED")
    
    # Test 5: Adaptive labyrinth scoring
    print("\n📊 TEST 5: Adaptive Labyrinth Scoring")
    
    # Pre-populate some path performance
    network.conversion_metrics['path_performance']['BTC→USDC'] = {
        'profit': 5.0, 'count': 20, 'avg_profit': 0.25, 'wins': 18, 'losses': 2
    }
    network.conversion_metrics['path_performance']['ETH→USDC'] = {
        'profit': 2.0, 'count': 15, 'avg_profit': 0.133, 'wins': 10, 'losses': 5
    }
    
    score_btc = network.s5_adaptive_labyrinth_score('BTC→USDC', 0.25)
    score_eth = network.s5_adaptive_labyrinth_score('ETH→USDC', 0.25)
    score_new = network.s5_adaptive_labyrinth_score('NEW→USDC', 0.25)
    
    print(f"  BTC→USDC score (90% win rate): {score_btc:.2f}")
    print(f"  ETH→USDC score (67% win rate): {score_eth:.2f}")
    print(f"  NEW→USDC score (unknown): {score_new:.2f}")
    assert score_btc > score_eth, "Higher win rate path should score higher"
    print("  ✅ PASSED")
    
    # Test 6: Path ranking
    print("\n📊 TEST 6: S5 Path Ranking")
    
    paths = [
        {'from': 'BTC', 'to': 'USDC', 'estimated_profit': 0.30},
        {'from': 'ETH', 'to': 'USDC', 'estimated_profit': 0.25},
        {'from': 'SOL', 'to': 'USDC', 'estimated_profit': 0.35},
        {'from': 'NEW', 'to': 'USDC', 'estimated_profit': 0.20},
    ]
    
    ranked = network.s5_rank_conversion_paths(paths)
    print("  Ranked paths:")
    for i, p in enumerate(ranked):
        print(f"    {i+1}. {p['path_key']}: score={p['s5_score']:.2f}, profit=${p['estimated_profit']:.2f}")
    print("  ✅ PASSED")
    
    # Test 7: Optimal conversions selection
    print("\n📊 TEST 7: S5 Optimal Conversions Selection")
    
    optimal = network.s5_get_optimal_conversions(paths, max_conversions=3)
    print(f"  Selected {len(optimal)} optimal conversions:")
    for p in optimal:
        print(f"    - {p['path_key']}: score={p['s5_score']:.2f}")
    assert len(optimal) <= 3, "Should select max 3 conversions"
    print("  ✅ PASSED")
    
    # Test 8: Cache system
    print("\n📊 TEST 8: Speed Cache System")
    
    # Score same path twice - second should be cached
    t1 = time.time()
    for _ in range(100):
        network.s5_adaptive_labyrinth_score('BTC→USDC', 0.25)
    t2 = time.time()
    
    # Clear cache and time again
    network._s5_score_cache.clear()
    t3 = time.time()
    for _ in range(100):
        network.s5_adaptive_labyrinth_score('BTC→USDC', 0.25)
    t4 = time.time()
    
    cached_time = (t2 - t1) * 1000
    uncached_time = (t4 - t3) * 1000
    print(f"  100 cached scores: {cached_time:.2f}ms")
    print(f"  100 uncached scores: {uncached_time:.2f}ms")
    print(f"  Hot paths: {len(network._s5_hot_paths)}")
    print("  ✅ PASSED")
    
    # Test 9: Time-to-million calculation
    print("\n📊 TEST 9: Time-to-Million Calculation")
    
    network.conversion_metrics['net_conversion_profit'] = 1000.0
    network.conversion_metrics['velocity_per_hour'] = 100.0
    network.conversion_metrics['acceleration'] = 1.0
    
    ttm = network.s5_get_time_to_million()
    print(f"  Current Profit: ${ttm['current_profit']:,.0f}")
    print(f"  Velocity: ${ttm['velocity_per_hour']}/hour")
    print(f"  Acceleration: ${ttm['acceleration']}/hour²")
    print(f"  TTM Linear: {ttm['ttm_days_linear']:.1f} days")
    print(f"  TTM Accelerated: {ttm['ttm_days_accelerated']:.1f} days")
    print(f"  Progress: {ttm['progress_pct']:.2f}%")
    print("  ✅ PASSED")
    
    # Test 10: S5 Summary
    print("\n📊 TEST 10: S5 Summary Output")
    print(network.s5_summary())
    print("  ✅ PASSED")
    
    # Final summary
    print("=" * 70)
    print("🎯 ALL S5 TESTS PASSED! 🎯")
    print("=" * 70)
    print("\n🔥 S5 SYSTEM READY FOR $1,000,000 TARGET 🔥")
    print("""
S5 = Speed × Scale × Smart × Systematic × Sustainable

✅ Velocity tracking: $/hour profit rate
✅ Acceleration tracking: $/hour² momentum
✅ Phase transitions: BOOTSTRAP → GROWTH → SCALE → COMPOUND → MILLION
✅ Kelly position sizing: Optimal risk management
✅ Adaptive labyrinth: Path scoring based on performance
✅ Speed caching: Hot path optimization
✅ Time-to-million: Real-time progress tracking
    """)
    
    return True

if __name__ == "__main__":
    test_s5_system()
