import sys
import time
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EXCHANGES_DIR = REPO_ROOT / "aureon" / "exchanges"
if str(EXCHANGES_DIR) not in sys.path:
    sys.path.insert(0, str(EXCHANGES_DIR))

import unified_market_trader as trader_mod


class FeedTarget:
    def __init__(self):
        self._hive_boosts = {}
        self._central_beat_symbols = {}
        self._central_beat_regime = {}


class UnifiedMarketTraderTests(unittest.TestCase):
    def _make_trader(self):
        trader = trader_mod.UnifiedMarketTrader.__new__(trader_mod.UnifiedMarketTrader)
        trader.kraken = FeedTarget()
        trader.capital = FeedTarget()
        trader.alpaca = FeedTarget()
        trader.binance = FeedTarget()
        trader.alpaca_trader = None
        trader.binance_trader = None
        trader.start_time = time.time()
        trader.kraken_ready = False
        trader.capital_ready = False
        trader.kraken_error = ""
        trader.capital_error = ""
        trader.alpaca_error = ""
        trader.binance_error = ""
        trader._last_auris_feed_at = 0.0
        trader._binance_diag = {}
        trader._shared_market_feed = {}
        trader._shared_market_feed_at = 0.0
        trader._central_beat_feed = {}
        trader._central_beat_at = 0.0
        trader._central_beat_layers = {"trader": {}, "probe": {}, "merged": {}}
        trader._central_beat_history = []
        trader._central_source_memory = {}
        trader._last_tick_started_at = 0.0
        trader._last_tick_completed_at = 0.0
        trader._last_tick_error = ""
        return trader

    def test_central_beat_merges_sources_into_symbol_metrics(self):
        trader = self._make_trader()
        kraken_payload = {
            "ok": True,
            "candidate_snapshot": [{"symbol": "XBT/USD", "side": "buy", "score": 0.8}],
            "decision_snapshot": {"symbol": "XBT/USD", "side": "buy", "decision": {"confidence": 0.9}},
        }
        capital_payload = {
            "ok": True,
            "candidate_snapshot": [{"symbol": "BTCUSD", "direction": "BUY", "score": 0.7}],
            "target_snapshot": {"symbol": "BTCUSD", "direction": "BUY", "score": 0.85},
        }

        beat = trader._build_central_beat_feed(kraken_payload, capital_payload)

        self.assertEqual(beat["source_count"], 2)
        self.assertIn("BTCUSD", beat["symbols"])
        self.assertEqual(beat["symbols"]["BTCUSD"]["side"], "BUY")
        self.assertGreaterEqual(beat["symbols"]["BTCUSD"]["support_count"], 2)

    def test_shared_market_feed_pushes_central_metrics_to_traders(self):
        trader = self._make_trader()
        central_beat = {
            "symbols": {
                "BTCUSD": {"strength": 0.88, "confidence": 0.75, "support_count": 3, "side": "BUY", "sources": ["kraken", "capital"]},
            },
            "regime": {"bias": "BUY", "confidence": 0.7, "source_count": 2},
        }

        shared = trader._sync_shared_market_feed(central_beat)

        self.assertIn("BTCUSD", shared["symbols"])
        self.assertEqual(trader.kraken._central_beat_regime["bias"], "BUY")
        self.assertEqual(trader.capital._central_beat_symbols["BTCUSD"]["support_count"], 3)
        self.assertEqual(trader.alpaca._central_beat_symbols["BTCUSD"]["support_count"], 3)
        self.assertEqual(trader.binance._central_beat_regime["bias"], "BUY")
        self.assertGreater(trader.kraken._hive_boosts["BTCUSD"], 0.0)

    def test_central_beat_reuses_recent_source_when_probe_drops_out(self):
        trader = self._make_trader()
        trader._extract_alpaca_source_snapshot = lambda watchlist: {  # type: ignore[method-assign]
            "source": "alpaca",
            "ready": True,
            "symbols": {"BTCUSD": {"symbol": "BTCUSD", "raw_symbol": "BTC/USD", "confidence": 0.6, "side": "BUY"}},
            "top_symbol": "BTCUSD",
            "top_side": "BUY",
            "top_confidence": 0.6,
        }
        trader._extract_binance_source_snapshot = lambda watchlist: {}  # type: ignore[method-assign]

        beat1 = trader._build_central_beat_feed({"ok": False}, {"ok": False})
        self.assertEqual(beat1["source_count"], 1)
        self.assertFalse(beat1["sources"][0]["stale"])

        trader._central_beat_at = 0.0
        trader._extract_alpaca_source_snapshot = lambda watchlist: {}  # type: ignore[method-assign]
        beat2 = trader._build_central_beat_feed({"ok": False}, {"ok": False})

        self.assertEqual(beat2["source_count"], 1)
        self.assertTrue(beat2["sources"][0]["stale"])
        self.assertEqual(beat2["sources"][0]["source"], "alpaca")

    def test_shared_order_flow_preserves_sell_direction_from_central_beat(self):
        trader = self._make_trader()
        trader._kraken_tradable_symbols = lambda: {"BTCUSD": "XXBTZUSD"}  # type: ignore[method-assign]
        trader._capital_tradable_symbols = lambda: {"BTCUSD": "BTCUSD"}  # type: ignore[method-assign]
        central_beat = {
            "symbols": {
                "BTCUSD": {
                    "strength": 0.82,
                    "confidence": 0.74,
                    "support_count": 2,
                    "side": "SELL",
                    "sources": ["kraken", "capital"],
                }
            }
        }
        shared_market_feed = {"symbols": {"BTCUSD": 0.82}}

        order_flow = trader._build_global_order_flow_feed({}, {}, central_beat, shared_market_feed)

        self.assertEqual(order_flow["active_order_flow"][0]["side"], "SELL")
        self.assertEqual(order_flow["active_order_flow"][0]["support_count"], 2)

    def test_get_local_dashboard_state_returns_cached_copy_without_rebuild(self):
        trader = self._make_trader()
        trader._latest_dashboard_payload = {"ok": True, "nested": {"value": 1}}

        def fail_build():
            raise AssertionError("dashboard read should not rebuild payload")

        trader._build_combined_payload = fail_build  # type: ignore[method-assign]

        payload = trader.get_local_dashboard_state()
        payload["nested"]["value"] = 9

        self.assertEqual(payload["nested"]["value"], 9)
        self.assertEqual(trader._latest_dashboard_payload["nested"]["value"], 1)

    def test_runtime_health_uses_cached_state_and_flags_missing_systems(self):
        trader = self._make_trader()
        trader._latest_dashboard_payload = {
            "generated_at": "2026-03-31T10:00:00",
            "runtime_minutes": 1.2,
            "preflight": {"overall": "yellow", "critical_failures": 1, "warnings": 2},
            "combined": {"open_positions": 0, "kraken_equity": 100.0, "capital_equity_gbp": 50.0},
        }
        trader.kraken_ready = True
        trader.capital_ready = True
        trader.alpaca = object()
        trader.binance = None
        trader._last_tick_completed_at = time.time()

        health = trader.get_runtime_health()

        self.assertFalse(health["ok"])
        self.assertTrue(health["trading_ready"])
        self.assertFalse(health["data_ready"])
        self.assertFalse(health["stale"])
        self.assertEqual(health["preflight_overall"], "yellow")


if __name__ == "__main__":
    unittest.main()
