#!/usr/bin/env python3
import os
import unittest
from unittest.mock import patch

from queen_force_trade_governance import evaluate_queen_force_trade_authority


class QueenForceTradeGovernanceTests(unittest.TestCase):
    def test_denies_without_explicit_approval(self):
        with patch.dict(os.environ, {"AUREON_QUEEN_FORCE_TRADE_ONLY": "true"}, clear=False):
            os.environ.pop("AUREON_QUEEN_FORCE_TRADE_APPROVED", None)
            decision = evaluate_queen_force_trade_authority()

        self.assertFalse(decision.allowed)
        self.assertTrue(any("AUREON_QUEEN_FORCE_TRADE_APPROVED=true" in r for r in decision.missing_requirements))

    def test_allows_when_policy_bypassed(self):
        with patch.dict(os.environ, {"AUREON_QUEEN_FORCE_TRADE_ONLY": "false"}, clear=False):
            decision = evaluate_queen_force_trade_authority()

        self.assertTrue(decision.allowed)
        self.assertIn("bypassed", decision.reason.lower())


if __name__ == "__main__":
    unittest.main()
