import sys
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
        trader._shared_market_feed = {}
        trader._shared_market_feed_at = 0.0
        trader._central_beat_feed = {}
        trader._central_beat_at = 0.0
        trader._central_beat_layers = {"trader": {}, "probe": {}, "merged": {}}
        trader._central_beat_history = []
        trader._central_source_memory = {}
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


if __name__ == "__main__":
    unittest.main()
