#!/usr/bin/env python3
import unittest

from aureon.exchanges.capital_cfd_trader import CAPITAL_MIN_PROFIT_GBP, CapitalCFDTrader, CFDPosition


class ClientStub:
    def __init__(self, positions=None, close_result=None, fallback_result=None, open_result=None, confirm_result=None):
        self._positions = list(positions or [])
        self._position_batches = None
        self._close_result = close_result if close_result is not None else {"success": True}
        self._fallback_result = fallback_result if fallback_result is not None else {"dealReference": "FALLBACK"}
        self._open_result = open_result if open_result is not None else {"dealReference": "REF1"}
        self._confirm_result = confirm_result if confirm_result is not None else {"dealId": "DOPEN", "level": 7282.6}

    def get_positions(self):
        if self._position_batches is not None:
            if len(self._position_batches) > 1:
                return list(self._position_batches.pop(0))
            return list(self._position_batches[0])
        return list(self._positions)

    def close_position(self, deal_id: str):
        return dict(self._close_result)

    def place_market_order(self, symbol: str, side: str, size: float):
        if side.upper() == "BUY":
            return dict(self._open_result)
        return dict(self._fallback_result)

    def confirm_order(self, deal_reference: str):
        return dict(self._confirm_result)


class TestCapitalCFDSync(unittest.TestCase):
    def test_open_position_accepts_verified_live_deal_after_short_delay(self):
        live_position = {
            "position": {
                "dealId": "DDELAY",
                "direction": "BUY",
                "size": 1,
                "level": 7282.6,
            },
            "market": {
                "epic": "CS.D.SILVER.CFD.IP",
                "symbol": "SILVER",
                "bid": 7249.8,
                "offer": 7251.8,
                "instrumentType": "COMMODITY",
            },
        }
        trader = CapitalCFDTrader.__new__(CapitalCFDTrader)
        trader.client = ClientStub(
            open_result={"dealReference": "REF-DELAY"},
            confirm_result={"dealId": "DDELAY", "level": 7282.6},
        )
        trader.client._position_batches = [[], [], [live_position]]
        trader.positions = []
        trader.stats = {
            "trades_opened": 0.0,
            "trades_closed": 0.0,
            "winning_trades": 0.0,
            "losing_trades": 0.0,
            "total_pnl_gbp": 0.0,
            "best_trade": 0.0,
            "worst_trade": 0.0,
        }
        trader._latest_monitor_line = ""
        trader._latest_order_error = ""
        trader._required_tp_pct_for_profit = lambda price, size: (CAPITAL_MIN_PROFIT_GBP / max(price * size, 0.0001)) * 100.0

        result = trader._open_position(
            "SILVER",
            {"class": "commodity", "size": 1, "tp_pct": 0.75, "sl_pct": 0.45},
            {"price": 7282.6, "ask": 7282.6, "epic": "CS.D.SILVER.CFD.IP"},
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.deal_id, "DDELAY")

    def test_open_position_requires_exchange_validation(self):
        trader = CapitalCFDTrader.__new__(CapitalCFDTrader)
        trader.client = ClientStub(
            positions=[],
            open_result={"dealReference": "REF-NO-LIVE"},
            confirm_result={"dealId": "D-NO-LIVE", "level": 7282.6},
        )
        trader.positions = []
        trader.stats = {
            "trades_opened": 0.0,
            "trades_closed": 0.0,
            "winning_trades": 0.0,
            "losing_trades": 0.0,
            "total_pnl_gbp": 0.0,
            "best_trade": 0.0,
            "worst_trade": 0.0,
        }
        trader._latest_monitor_line = ""
        trader._latest_order_error = ""
        trader._required_tp_pct_for_profit = lambda price, size: (CAPITAL_MIN_PROFIT_GBP / max(price * size, 0.0001)) * 100.0

        result = trader._open_position(
            "SILVER",
            {"class": "commodity", "size": 1, "tp_pct": 0.75, "sl_pct": 0.45},
            {"price": 7282.6, "ask": 7282.6, "epic": "CS.D.SILVER.CFD.IP"},
        )

        self.assertIsNone(result)
        self.assertEqual(trader.positions, [])
        self.assertEqual(trader.stats["trades_opened"], 0.0)

    def test_sync_positions_from_exchange_rebuilds_live_position(self):
        trader = CapitalCFDTrader.__new__(CapitalCFDTrader)
        trader.client = ClientStub(positions=[{
            "position": {
                "dealId": "D1",
                "direction": "BUY",
                "size": 1,
                "level": 7282.6,
            },
            "market": {
                "epic": "CS.D.SILVER.CFD.IP",
                "symbol": "SILVER",
                "bid": 7249.8,
                "offer": 7251.8,
                "instrumentType": "COMMODITY",
            },
        }])
        trader.positions = []
        trader._last_exchange_sync = 0.0
        trader._required_tp_pct_for_profit = lambda price, size: (CAPITAL_MIN_PROFIT_GBP / max(price * size, 0.0001)) * 100.0

        trader._sync_positions_from_exchange(force=True)

        self.assertEqual(len(trader.positions), 1)
        pos = trader.positions[0]
        self.assertEqual(pos.symbol, "SILVER")
        self.assertEqual(pos.deal_id, "D1")
        self.assertEqual(pos.direction, "BUY")
        self.assertGreater(pos.tp_price, pos.entry_price)

    def test_open_position_accepts_verified_live_deal(self):
        live_position = {
            "position": {
                "dealId": "DOPEN",
                "direction": "BUY",
                "size": 1,
                "level": 7282.6,
            },
            "market": {
                "epic": "CS.D.SILVER.CFD.IP",
                "symbol": "SILVER",
                "bid": 7249.8,
                "offer": 7251.8,
                "instrumentType": "COMMODITY",
            },
        }
        trader = CapitalCFDTrader.__new__(CapitalCFDTrader)
        trader.client = ClientStub(
            positions=[live_position],
            open_result={"dealReference": "REF1"},
            confirm_result={"dealId": "DOPEN", "level": 7282.6},
        )
        trader.positions = []
        trader.stats = {
            "trades_opened": 0.0,
            "trades_closed": 0.0,
            "winning_trades": 0.0,
            "losing_trades": 0.0,
            "total_pnl_gbp": 0.0,
            "best_trade": 0.0,
            "worst_trade": 0.0,
        }
        trader._latest_monitor_line = ""
        trader._latest_order_error = ""
        trader._required_tp_pct_for_profit = lambda price, size: (CAPITAL_MIN_PROFIT_GBP / max(price * size, 0.0001)) * 100.0

        result = trader._open_position(
            "SILVER",
            {"class": "commodity", "size": 1, "tp_pct": 0.75, "sl_pct": 0.45},
            {"price": 7282.6, "ask": 7282.6, "epic": "CS.D.SILVER.CFD.IP"},
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.deal_id, "DOPEN")
        self.assertEqual(len(trader.positions), 1)
        self.assertEqual(trader.stats["trades_opened"], 1.0)

    def test_monitor_keeps_position_when_close_fails_and_exchange_still_reports_it(self):
        trader = CapitalCFDTrader.__new__(CapitalCFDTrader)
        trader.client = ClientStub(
            positions=[{"position": {"dealId": "D2"}}],
            close_result={"success": False, "error": "rejected"},
            fallback_result={"rejected": True, "error": "blocked"},
        )
        trader.positions = [
            CFDPosition(
                symbol="SILVER",
                deal_id="D2",
                epic="CS.D.SILVER.CFD.IP",
                direction="BUY",
                size=1,
                entry_price=7282.6,
                tp_price=7300.0,
                sl_price=7200.0,
                asset_class="commodity",
                current_price=7305.0,
            )
        ]
        trader.stats = {
            "trades_opened": 0.0,
            "trades_closed": 0.0,
            "winning_trades": 0.0,
            "losing_trades": 0.0,
            "total_pnl_gbp": 0.0,
            "best_trade": 0.0,
            "worst_trade": 0.0,
        }
        trader._recent_closed_trades = []
        trader._latest_monitor_line = ""

        closed = trader._monitor_positions()

        self.assertEqual(closed, [])
        self.assertEqual(len(trader.positions), 1)
        self.assertEqual(trader.positions[0].deal_id, "D2")


if __name__ == "__main__":
    unittest.main(verbosity=2)
