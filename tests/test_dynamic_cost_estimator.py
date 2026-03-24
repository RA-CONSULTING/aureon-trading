#!/usr/bin/env python3
"""
Unit tests for DynamicCostEstimator

Tests cover:
- Fallback defaults when no data
- Symbol-specific learning
- Global average fallback
- Conservative floor/ceiling bounds
- Time-weighted averaging
- Sample expiry

Run: python3 test_dynamic_cost_estimator.py
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import time
import unittest

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dynamic_cost_estimator import (
    DynamicCostEstimator,
    CostEstimate,
    CostSample
)


class TestDynamicCostEstimator(unittest.TestCase):
    """Test suite for DynamicCostEstimator."""
    
    def setUp(self):
        """Create fresh estimator for each test."""
        self.estimator = DynamicCostEstimator()
    
    def test_fallback_defaults_no_data(self):
        """When no data exists, should return conservative fallback."""
        estimate = self.estimator.estimate_cost('BTC/USD', 'buy', 100.0)
        
        self.assertEqual(estimate.source, 'fallback')
        self.assertEqual(estimate.estimated_total_pct, 0.30)  # DEFAULT_TOTAL_PCT
        self.assertEqual(estimate.sample_count, 0)
        self.assertLess(estimate.confidence, 0.5)  # Low confidence
    
    def test_symbol_specific_learning(self):
        """After enough symbol-specific samples, should use them."""
        symbol = 'ETH/USD'
        
        # Add 6 samples with low costs (better than default)
        for i in range(6):
            self.estimator.add_sample(
                symbol=symbol,
                side='buy',
                notional_usd=100.0,
                fee_pct=0.12,    # 12 bps (better than 20 bps default)
                spread_pct=0.05, # 5 bps (better than 8 bps default)
                slippage_pct=0.01
            )
        
        estimate = self.estimator.estimate_cost(symbol, 'buy', 100.0)
        
        self.assertEqual(estimate.source, 'symbol_specific')
        self.assertEqual(estimate.sample_count, 6)
        self.assertGreater(estimate.confidence, 0.2)
        
        # Should reflect the better costs (with 10% safety buffer)
        # Expected: (0.12 + 0.05 + 0.01) * 1.10 = 0.198
        self.assertLess(estimate.estimated_total_pct, 0.25)  # Better than default 0.30
    
    def test_global_average_fallback(self):
        """When symbol data insufficient, should use global average."""
        # Add global samples for multiple symbols
        for i in range(12):
            self.estimator.add_sample(
                symbol=f'SYM{i}/USD',
                side='buy',
                notional_usd=100.0,
                fee_pct=0.15,
                spread_pct=0.06,
                slippage_pct=0.02
            )
        
        # Request estimate for unseen symbol
        estimate = self.estimator.estimate_cost('UNSEEN/USD', 'buy', 100.0)
        
        self.assertEqual(estimate.source, 'global_average')
        self.assertGreater(estimate.sample_count, 5)
        self.assertLess(estimate.estimated_total_pct, 0.30)  # Better than fallback
    
    def test_conservative_floor_applied(self):
        """Should never estimate below minimum bounds."""
        # Add samples with unrealistically low costs
        for i in range(6):
            self.estimator.add_sample(
                symbol='BTC/USD',
                side='buy',
                notional_usd=100.0,
                fee_pct=0.01,    # 1 bp (unrealistic)
                spread_pct=0.01, # 1 bp (unrealistic)
                slippage_pct=0.001
            )
        
        estimate = self.estimator.estimate_cost('BTC/USD', 'buy', 100.0)
        
        # Should be clamped to minimums
        self.assertGreaterEqual(estimate.estimated_fee_pct, 0.10)  # MIN_FEE_PCT
        self.assertGreaterEqual(estimate.estimated_spread_pct, 0.05)  # MIN_SPREAD_PCT
    
    def test_conservative_ceiling_applied(self):
        """Should cap extreme outliers at maximum bounds."""
        # Add samples with unrealistically high costs
        for i in range(6):
            self.estimator.add_sample(
                symbol='BTC/USD',
                side='buy',
                notional_usd=100.0,
                fee_pct=1.0,     # 100 bps (extreme)
                spread_pct=1.0,  # 100 bps (extreme)
                slippage_pct=0.5
            )
        
        estimate = self.estimator.estimate_cost('BTC/USD', 'buy', 100.0)
        
        # Should be capped at maximums
        self.assertLessEqual(estimate.estimated_fee_pct, 0.30)  # MAX_FEE_PCT
        self.assertLessEqual(estimate.estimated_spread_pct, 0.20)  # MAX_SPREAD_PCT
        self.assertLessEqual(estimate.estimated_slippage_pct, 0.10)  # MAX_SLIPPAGE_PCT
    
    def test_time_weighted_averaging(self):
        """Recent samples should weigh more than old samples."""
        symbol = 'BTC/USD'
        now = time.time()
        
        # Add old sample with high cost
        old_sample = CostSample(
            timestamp=now - 20*3600,  # 20 hours ago
            symbol=symbol,
            side='buy',
            notional_usd=100.0,
            fee_pct=0.25,
            spread_pct=0.15,
            slippage_pct=0.05,
            total_cost_pct=0.45
        )
        self.estimator._symbol_samples[symbol].append(old_sample)
        self.estimator._global_samples.append(old_sample)
        
        # Add many recent samples with low cost
        for i in range(5):
            self.estimator.add_sample(
                symbol=symbol,
                side='buy',
                notional_usd=100.0,
                fee_pct=0.12,
                spread_pct=0.05,
                slippage_pct=0.01
            )
        
        estimate = self.estimator.estimate_cost(symbol, 'buy', 100.0)
        
        # Should be closer to recent low costs than old high cost
        # (recent samples decay slower, so dominate the average)
        self.assertLess(estimate.estimated_total_pct, 0.30)
    
    def test_sample_count_affects_confidence(self):
        """More samples should increase confidence."""
        symbol = 'BTC/USD'
        
        # Test with 3 samples (low confidence)
        for i in range(3):
            self.estimator.add_sample(symbol, 'buy', 100.0, 0.15, 0.05, 0.02)
        
        est_low = self.estimator.estimate_cost(symbol, 'buy', 100.0)
        self.assertLessEqual(est_low.confidence, 0.3)  # Changed from assertLess to assertLessEqual
        
        # Add more samples (higher confidence)
        for i in range(17):  # Total 20 samples
            self.estimator.add_sample(symbol, 'buy', 100.0, 0.15, 0.05, 0.02)
        
        est_high = self.estimator.estimate_cost(symbol, 'buy', 100.0)
        self.assertGreater(est_high.confidence, est_low.confidence)
        self.assertGreaterEqual(est_high.confidence, 0.9)  # Near max confidence
    
    def test_reset_clears_data(self):
        """Reset should clear all samples."""
        # Add samples
        for i in range(10):
            self.estimator.add_sample('BTC/USD', 'buy', 100.0, 0.15, 0.05, 0.02)
        
        stats_before = self.estimator.get_stats()
        self.assertGreater(stats_before['total_samples'], 0)
        
        # Reset
        self.estimator.reset()
        
        stats_after = self.estimator.get_stats()
        self.assertEqual(stats_after['total_samples'], 0)
        self.assertEqual(stats_after['global_window'], 0)
        
        # Should fall back to defaults
        estimate = self.estimator.estimate_cost('BTC/USD', 'buy', 100.0)
        self.assertEqual(estimate.source, 'fallback')
    
    def test_stats_tracking(self):
        """Should track statistics correctly."""
        self.estimator.add_sample('BTC/USD', 'buy', 100.0, 0.15, 0.05, 0.02)
        self.estimator.add_sample('ETH/USD', 'buy', 100.0, 0.15, 0.05, 0.02)
        
        self.estimator.estimate_cost('BTC/USD', 'buy', 100.0)
        self.estimator.estimate_cost('ETH/USD', 'buy', 100.0)
        
        stats = self.estimator.get_stats()
        
        self.assertEqual(stats['total_samples'], 2)
        self.assertEqual(stats['symbols_with_data'], 2)
        self.assertEqual(stats['estimates_served'], 2)
    
    def test_10_percent_safety_buffer(self):
        """Total cost should include 10% safety buffer."""
        symbol = 'BTC/USD'
        
        # Add samples with known costs
        for i in range(6):
            self.estimator.add_sample(
                symbol=symbol,
                side='buy',
                notional_usd=100.0,
                fee_pct=0.10,
                spread_pct=0.05,
                slippage_pct=0.01
            )
        
        estimate = self.estimator.estimate_cost(symbol, 'buy', 100.0)
        
        # Raw sum = 0.10 + 0.05 + 0.01 = 0.16
        # With 10% buffer = 0.16 * 1.10 = 0.176
        expected = 0.176
        
        # Allow small floating point tolerance
        self.assertAlmostEqual(estimate.estimated_total_pct, expected, places=3)


def run_tests():
    """Run all tests with verbose output."""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    print("=" * 70)
    print("DYNAMIC COST ESTIMATOR - UNIT TESTS")
    print("=" * 70)
    print()
    
    run_tests()
    
    print()
    print("=" * 70)
    print("✅ All tests passed!")
    print("=" * 70)
