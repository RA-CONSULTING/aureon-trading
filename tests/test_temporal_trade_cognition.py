#!/usr/bin/env python3
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from aureon.monitors.margin_goal_recorder import MarginGoalRecorder
from aureon.trading.temporal_trade_cognition import TemporalTradeCognition


class TestTemporalTradeCognition(unittest.TestCase):
    def test_plan_trade_has_human_time_and_expected_by(self):
        cognition = TemporalTradeCognition()

        plan = cognition.plan_trade(
            pair="BTC/USD",
            side="buy",
            ticker_symbol="BTCUSDT",
            entry_price=100.0,
            target_price=101.0,
            required_move_pct=1.0,
            profit_target_usd=0.10,
            eta_minutes=3.0,
            confidence=0.8,
            now=1_700_000_000.0,
        )

        self.assertEqual(plan["pair"], "BTC/USD")
        self.assertEqual(plan["opened_at"]["epoch"], 1_700_000_000.0)
        self.assertEqual(plan["expected_by"]["epoch"], 1_700_000_180.0)
        self.assertAlmostEqual(plan["eta_minutes"], 3.0)
        self.assertGreater(plan["probability"], 0.5)

    def test_verify_reports_on_track_and_missed_eta(self):
        cognition = TemporalTradeCognition()
        plan = cognition.plan_trade(
            pair="BTC/USD",
            side="buy",
            ticker_symbol="BTCUSDT",
            entry_price=100.0,
            target_price=101.0,
            required_move_pct=1.0,
            profit_target_usd=0.10,
            eta_minutes=3.0,
            confidence=0.8,
            now=1_700_000_000.0,
        )

        on_track = cognition.verify(
            plan,
            current_price=100.55,
            validated_net_pnl=0.02,
            now=1_700_000_090.0,
        )
        missed = cognition.verify(
            plan,
            current_price=100.20,
            validated_net_pnl=0.02,
            now=1_700_000_181.0,
        )

        self.assertEqual(on_track["status"], "on_track")
        self.assertEqual(missed["status"], "missed_eta")
        self.assertTrue(missed["due"])

    def test_sell_plan_progress_uses_downward_price_move(self):
        cognition = TemporalTradeCognition()
        plan = cognition.plan_trade(
            pair="ETH/USD",
            side="sell",
            ticker_symbol="ETHUSDT",
            entry_price=100.0,
            target_price=99.0,
            required_move_pct=1.0,
            profit_target_usd=0.10,
            eta_minutes=3.0,
            confidence=0.8,
            now=1_700_000_000.0,
        )

        verification = cognition.verify(
            plan,
            current_price=99.4,
            validated_net_pnl=0.03,
            now=1_700_000_060.0,
        )

        self.assertGreater(verification["price_progress"], 0.0)
        self.assertGreater(verification["direction_move_pct"], 0.0)

    def test_goal_recorder_accepts_route_to_profit_candidate_shape(self):
        info = type("Info", (), {
            "pair": "BTC/USD",
            "momentum": 1.2,
            "spread_pct": 0.1,
            "volume_24h": 1000.0,
        })()

        with tempfile.TemporaryDirectory() as tmp:
            proof_path = os.path.join(tmp, "proof.jsonl")
            with patch("aureon.monitors.margin_goal_recorder.PROOF_FILE", proof_path):
                recorder = MarginGoalRecorder()
                recorder.record_scan(
                    [(info, "buy", 1.0, 10.0, 5, 2.0, 0.5, 0.1, 1.2, 3.0, 4.0)],
                    winner_pair="BTC/USD",
                    winner_side="buy",
                )

            with open(proof_path, encoding="utf-8") as handle:
                record = json.loads(handle.readline())

        self.assertEqual(record["candidates"][0]["route_to_profit"], 4.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
