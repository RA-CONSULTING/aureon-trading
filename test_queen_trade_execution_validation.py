#!/usr/bin/env python3
"""Tests for Queen autonomous trading subsystem and order-id validation."""

import unittest

from aureon_queen_autonomous_control import (
    AutonomousAction,
    AutonomousDecision,
    QueenAutonomousControl,
    SystemState,
)


class MockQueenExecutor:
    def __init__(self, result):
        self.result = result

    def execute_trade(self, symbol, side, amount, exchange):
        data = dict(self.result)
        data.setdefault("symbol", symbol)
        data.setdefault("side", side)
        data.setdefault("amount", amount)
        data.setdefault("exchange", exchange)
        return data


class QueenTradeExecutionValidationTests(unittest.TestCase):
    def _build_control(self):
        control = QueenAutonomousControl.__new__(QueenAutonomousControl)
        control.systems = {
            "temporal_dialer": SystemState(name="temporal_dialer", status="ONLINE"),
            "harmonic_chain_master": SystemState(name="harmonic_chain_master", status="ONLINE"),
            "probability_nexus": SystemState(name="probability_nexus", status="ONLINE"),
            "thought_bus": SystemState(name="thought_bus", status="ONLINE"),
        }
        control.queen = None
        return control

    def test_validate_trade_subsystems_reports_missing(self):
        control = self._build_control()
        control.systems["thought_bus"].status = "OFFLINE"

        status = control.validate_trade_subsystems()

        self.assertFalse(status["ready"])
        self.assertIn("thought_bus", status["missing"])

    def test_execute_trade_requires_valid_order_id(self):
        control = self._build_control()
        control.queen = MockQueenExecutor({"success": True, "order_id": ""})
        decision = AutonomousDecision(
            action=AutonomousAction.APPROVE_TRADE,
            parameters={"symbol": "BTC/USD", "side": "BUY", "amount": 100, "exchange": "kraken"},
        )

        result = control._execute_trade(decision)

        self.assertFalse(result["success"])
        self.assertIn("order id", result["reason"].lower())

    def test_execute_trade_accepts_buy_sell_convert_with_order_id(self):
        control = self._build_control()
        control.queen = MockQueenExecutor({"success": True, "order_id": "KRAKEN-123"})

        for side in ["BUY", "SELL", "CONVERT"]:
            with self.subTest(side=side):
                decision = AutonomousDecision(
                    action=AutonomousAction.APPROVE_TRADE,
                    parameters={"symbol": "ETH/USD", "side": side, "amount": 50, "exchange": "kraken"},
                )
                result = control._execute_trade(decision)
                self.assertTrue(result["success"])
                self.assertTrue(result["validated"])
                self.assertEqual(result["order_id"], "KRAKEN-123")

    def test_execute_trade_fails_when_required_subsystems_are_offline(self):
        control = self._build_control()
        control.systems["probability_nexus"].status = "ERROR"
        decision = AutonomousDecision(
            action=AutonomousAction.APPROVE_TRADE,
            parameters={"symbol": "SOL/USD", "side": "BUY", "amount": 25, "exchange": "kraken"},
        )

        result = control._execute_trade(decision)

        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "Required Queen subsystems offline")


if __name__ == "__main__":
    unittest.main()
