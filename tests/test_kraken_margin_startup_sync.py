#!/usr/bin/env python3
import unittest
from unittest.mock import patch

from aureon.exchanges.kraken_client import KrakenClient
from aureon.exchanges.kraken_margin_penny_trader import KrakenMarginArmyTrader


class TestKrakenMarginStartupSync(unittest.TestCase):
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
