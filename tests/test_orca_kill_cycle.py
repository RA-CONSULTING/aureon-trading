#!/usr/bin/env python3
"""Regression tests for full Orca kill cycle orchestration."""

import unittest
from typing import Dict, List

from orca_kill_executor import OrcaKillExecutor, OrcaPosition


class StubOrcaKillExecutor(OrcaKillExecutor):
    def __init__(self):
        self.dry_run = True
        self.positions: Dict[str, OrcaPosition] = {}
        self.kraken = None
        self.alpaca = None
        self.price_map: Dict[str, float] = {}
        self.closed: List[OrcaPosition] = []
        self.exec_calls: List[Dict] = []
        self.monitor_checks = 0

    def _init_exchanges(self):
        return

    def _load_positions(self):
        return

    def _save_positions(self):
        return

    def get_price(self, symbol: str, exchange: str) -> float:
        return float(self.price_map.get(f"{exchange}:{symbol}", self.price_map.get(symbol, 0.0)))

    def execute_kill(self, symbol: str, exchange: str, side: str, amount_usd=None, take_profit_pct=5.0, stop_loss_pct=-3.0):
        self.exec_calls.append(
            {"symbol": symbol, "exchange": exchange, "side": side, "amount_usd": amount_usd}
        )
        position = OrcaPosition(
            id="p1",
            symbol=symbol,
            exchange=exchange,
            side='long' if side == 'buy' else 'short',
            entry_price=10.0,
            entry_qty=1.0,
            entry_cost=10.0,
            entry_time=1.0,
            entry_order_id="order-1",
            take_profit_pct=take_profit_pct,
            stop_loss_pct=stop_loss_pct,
        )
        self.positions[position.id] = position
        return position

    def monitor_positions(self):
        self.monitor_checks += 1
        pos = self.positions["p1"]
        if self.monitor_checks >= 2:
            pos.status = "closed"
            pos.exit_reason = "take_profit"
            pos.realized_pnl = 1.25
            return [pos]
        return []


class OrcaKillCycleTests(unittest.TestCase):
    def test_selection_validates_tickers_and_chooses_priced_symbol(self):
        executor = StubOrcaKillExecutor()
        executor.price_map = {"alpaca:BTC/USD": 100000.0, "alpaca:ETH/USD": 3500.0}

        result = executor.select_trade_candidate(
            tickers=["BAD", "ETH/USD", "BTC/USD"],
            exchange="alpaca",
        )

        self.assertIsNotNone(result["selected"])
        self.assertEqual(result["selected"]["symbol"], "BTC/USD")
        invalid = [v for v in result["validations"] if not v["valid"]]
        self.assertTrue(any("BASE/QUOTE" in v["reason"] for v in invalid))

    def test_run_orca_kill_cycle_executes_then_monitors_to_profitable_close(self):
        executor = StubOrcaKillExecutor()
        executor.price_map = {"alpaca:ETH/USD": 3000.0}

        result = executor.run_orca_kill_cycle(
            tickers=["ETH/USD"],
            exchange="alpaca",
            side="buy",
            amount_usd=25.0,
            monitor_cycles=4,
            poll_seconds=0,
        )

        self.assertTrue(result["success"])
        self.assertTrue(result["profitable_close"])
        self.assertEqual(result["phase"], "closed")
        self.assertEqual(executor.exec_calls[0]["symbol"], "ETH/USD")
        self.assertGreaterEqual(executor.monitor_checks, 2)


if __name__ == "__main__":
    unittest.main()
