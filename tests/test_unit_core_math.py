from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import unittest
import math
import sys
import os
from unittest.mock import MagicMock

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestUnitCoreMath(unittest.TestCase):
    
    def test_reality_branch_math(self):
        """Test RealityBranch core math logic: compute_coherence, update_lambda."""
        from aureon_quantum_mirror_scanner import RealityBranch
        
        branch = RealityBranch(
            branch_id="test",
            symbol="BTC/USD",
            exchange="kraken",
            p1_harmonic=0.7,
            p2_coherence=0.8,
            p3_stability=0.9
        )
        
        # Coherence = 1 - (max - min)
        # 1 - (0.9 - 0.7) = 0.8
        coherence = branch.compute_coherence()
        self.assertAlmostEqual(coherence, 0.8)
        
        # Check lambda update
        # lambda = exp(-alpha * drift)
        branch.drift_score = 0.5
        alpha = 0.1
        expected_lambda = math.exp(-alpha * 0.5)
        new_lambda = branch.update_lambda(alpha=alpha)
        self.assertAlmostEqual(new_lambda, expected_lambda)
        
        # Check compute_branch_score
        # S = avg(p) * P * C * Lambda
        # avg = 0.8. Let P = 1.0, C=0.8, L=expected_lambda
        branch.beneficial_probability = 1.0
        # Re-compute coherence to be safe
        branch.compute_coherence()
        
        score = branch.compute_branch_score()
        expected_score = 0.8 * 1.0 * 0.8 * expected_lambda
        self.assertAlmostEqual(score, expected_score)

    def test_timeline_anchor_strength(self):
        """Test TimelineAnchor validation logic and strength calculation."""
        from aureon_timeline_anchor_validator import TimelineAnchor, ValidationRecord, AnchorStatus, PHI
        
        anchor = TimelineAnchor(
            anchor_id="anchor_1",
            branch_id="branch_1",
            symbol="ETH/USD",
            exchange="binance"
        )
        
        # Add a successful validation
        record1 = ValidationRecord(
            timestamp=1000.0,
            validation_type="hourly",
            p1_score=0.9,
            p2_score=0.9, 
            p3_score=0.9,
            coherence=1.0,
            lambda_stability=1.0,
            drift=0.0,
            passed=True
        )
        anchor.add_validation(record1)
        
        # 1 success / 1 total = 1.0 ratio
        # coherence and stability should start moving towards 1.0
        # Since cumulative starts at 0, first update with alpha 0.3:
        # cum_cob = 0.3*1.0 + 0.7*0 = 0.3
        self.assertAlmostEqual(anchor.cumulative_coherence, 0.3)
        self.assertAlmostEqual(anchor.cumulative_stability, 0.3)
        
        # Strength = (ratio*0.4 + coh*0.3 + stab*0.3) * PHI
        # (1.0*0.4 + 0.3*0.3 + 0.3*0.3) * 1.618...
        # (0.4 + 0.09 + 0.09) * 1.618...
        # 0.58 * 1.618... = 0.938...
        
        # Status should become ANCHORED (>= 0.9)
        self.assertEqual(anchor.status, AnchorStatus.ANCHORED)
        
        # Fail one
        record2 = ValidationRecord(
            timestamp=1100.0,
            validation_type="hourly",
            p1_score=0.1,
            p2_score=0.1,
            p3_score=0.1,
            coherence=0.0,
            lambda_stability=0.0,
            drift=1.0,
            passed=False
        )
        anchor.add_validation(record2)
        
        self.assertEqual(anchor.successful_validations, 1)
        self.assertEqual(anchor.failed_validations, 1)
        # Strength should drop significantly

if __name__ == '__main__':
    unittest.main()
