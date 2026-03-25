#!/usr/bin/env python3
import unittest
from unittest.mock import patch

from aureon.exchanges.kraken_client import KrakenClient
from aureon.exchanges.kraken_margin_penny_trader import KrakenMarginArmyTrader


class TestKrakenMarginStartupSync(unittest.TestCase):
    def test_validator_required_move_pct_uses_trade_profit_validator_when_available(self):
        trader = KrakenMarginArmyTrader.__new__(KrakenMarginArmyTrader)
        trader.trade_profit_validator = type("ValidatorStub", (), {
            "get_exchange_costs": staticmethod(lambda exchange, value, is_taker=True, symbol="": {
                "total": 2.0,
            })
        })()
        trader._validator_snapshot = {}

        required_move_pct, round_trip_cost = trader._validator_required_move_pct(
            trade_value=100.0,
            profit_target_usd=1.27,
            symbol="BTC/USD",
        )

        self.assertAlmostEqual(round_trip_cost, 4.0)
        self.assertAlmostEqual(required_move_pct, 5.27)
        self.assertEqual(trader._validator_snapshot["source"], "validator")

    def test_apply_brain_gate_to_candidates_filters_rejected_entries(self):
        trader = KrakenMarginArmyTrader.__new__(KrakenMarginArmyTrader)

        class BrainStub:
            def decide(self, symbol, base_score, features, population_scores):
                if symbol == "ETH/USD":
                    return None
                return type("Decision", (), {"score": base_score + 1.5, "coherence": 0.81})()

        trader.signal_brain = BrainStub()
        trader._brain_snapshot = {}
        info1 = type("Info", (), {"pair": "BTC/USD", "momentum": 1.2, "spread_pct": 0.1})()
        info2 = type("Info", (), {"pair": "ETH/USD", "momentum": 0.8, "spread_pct": 0.1})()
        candidates = [
            (info1, "buy", 1.0, 100.0, 5, 4.0, 1.1, 0.5, 1.0, 10.0, 0.8),
            (info2, "buy", 1.0, 100.0, 5, 3.5, 1.0, 0.5, 0.9, 12.0, 0.7),
        ]

        gated = trader._apply_brain_gate_to_candidates(candidates)

        self.assertEqual(len(gated), 1)
        self.assertEqual(gated[0][0].pair, "BTC/USD")
        self.assertAlmostEqual(gated[0][5], 5.5)
        self.assertEqual(trader._brain_snapshot["ETH/USD"]["decision"], "rejected")

    def test_validated_net_pnl_subtracts_slippage_and_spread_buffer(self):
        trader = KrakenMarginArmyTrader.__new__(KrakenMarginArmyTrader)
        trader.trade_profit_validator = type("ValidatorStub", (), {
            "get_exchange_costs": staticmethod(lambda exchange, value, is_taker=True, symbol="": {
                "slippage": 0.2,
                "spread": 0.3,
            })
        })()

        validated = trader._validated_net_pnl("BTC/USD", exit_value=100.0, net_pnl=2.0)

        self.assertAlmostEqual(validated, 1.5)

    def test_close_margin_position_returns_no_position_instead_of_volume_zero(self):
        client = KrakenClient.__new__(KrakenClient)
        client.dry_run = False
        client.get_open_margin_positions = lambda do_calcs=False: []
        client._resolve_pair = lambda symbol: ("XBTUSD", {"lot_decimals": 8})

        result = client.close_margin_position("BTC/USD", side="sell", volume=None)

        self.assertEqual(result, {"error": "no_position", "symbol": "BTC/USD"})

    def test_load_state_reconciles_live_kraken_positions_without_local_state_file(self):
        trader = KrakenMarginArmyTrader.__new__(KrakenMarginArmyTrader)
        trader.dry_run = False
        trader.active_long = None
        trader.active_short = None
        trader.active_trade = None
        trader.total_profit = 0
        trader.total_trades = 0
        trader.winning_trades = 0
        trader.shadow_validated_count = 0
        trader.shadow_failed_count = 0
        trader.completed_trades = []
        trader.orchestrator = None
        trader._start_stream_for = lambda symbol: None
        trader._save_state = lambda: None
        trader._binance_symbol_for_pair = lambda pair: "BTCUSDT"
        trader.client = type("ClientStub", (), {})()
        trader.client._int_to_alt = {"XXBTZUSD": "BTC/USD"}
        trader.client.get_open_margin_positions = lambda do_calcs=True: [{
            "pair": "XXBTZUSD",
            "side": "buy",
            "volume": 0.01,
            "cost": 850.0,
            "fee": 3.0,
            "open_time": 1700000000.0,
            "position_id": "P123",
            "leverage": "5",
        }]

        with patch("aureon.exchanges.kraken_margin_penny_trader.os.path.exists", return_value=False):
            trader._load_state()

        self.assertIsNotNone(trader.active_long)
        self.assertIsNone(trader.active_short)
        self.assertEqual(trader.active_long.pair, "BTC/USD")
        self.assertEqual(trader.active_long.side, "buy")
        self.assertEqual(trader.active_long.order_id, "P123")
        self.assertGreater(trader.active_long.breakeven_price, trader.active_long.entry_price)


if __name__ == "__main__":
    unittest.main(verbosity=2)
