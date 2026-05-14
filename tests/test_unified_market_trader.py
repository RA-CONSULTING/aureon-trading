import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch


os.environ.setdefault("AUREON_SUPPRESS_IMPORT_SIDE_EFFECTS", "1")

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
        self.decision_feeds = []

    def _feed_unified_decision_engine(self, **kwargs):
        self.decision_feeds.append(kwargs)


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
        trader._runtime_instance_id = "test-runtime"
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
        trader._stream_cache_health = {}
        trader._orderbook_pressure_cache = {}
        trader._fast_money_intelligence = {}
        trader._extract_stream_cache_source_snapshot = lambda watchlist: {}  # type: ignore[method-assign]
        trader._last_tick_started_at = 0.0
        trader._last_tick_completed_at = 0.0
        trader._last_tick_error = ""
        trader._last_order_intent_at = 0.0
        trader._last_order_intent_signature = ""
        trader._latest_order_intents = {}
        trader._last_execution_at = 0.0
        trader._execution_memory = {}
        trader._latest_execution_results = {}
        trader._executor_route_lock = trader_mod.threading.Lock()
        trader._executor_route_inflight = {}
        trader._executor_route_results = {}
        trader._tick_phase = "idle"
        trader._tick_phase_at = time.time()
        trader._thought_bus = None
        trader._mycelium = None
        trader._api_governor = trader_mod.ExchangeCallGovernor()
        return trader

    def _with_live_executor_env(self):
        keys = {
            "AUREON_LIVE_TRADING": "1",
            "AUREON_AUDIT_MODE": "0",
            "AUREON_DISABLE_REAL_ORDERS": "0",
            "AUREON_DISABLE_EXCHANGE_MUTATIONS": "0",
            "DRY_RUN": "0",
            "AUREON_ORDER_INTENT_PUBLISH": "1",
            "AUREON_UNIFIED_ORDER_EXECUTOR": "1",
            "BINANCE_MARGIN_ENABLED": "true",
        }
        old = {key: os.environ.get(key) for key in keys}
        os.environ.update(keys)
        return old

    def _restore_env(self, old):
        for key, value in old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

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
        self.assertTrue(beat["model_signal_feed"]["used"])
        self.assertIn("model_signal", beat["symbols"]["BTCUSD"])

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

    def test_stream_cache_snapshot_feeds_fresh_websocket_symbols(self):
        trader = self._make_trader()
        ticker = trader_mod.SimpleNamespace(
            symbol="BTC",
            price=50123.45,
            bid=50120.0,
            ask=50125.0,
            change_24h=1.8,
            volume_24h=2_000_000_000.0,
            source="binance_ws",
            timestamp=time.time(),
            pair="BTCUSDT",
        )
        cache = trader_mod.SimpleNamespace(get_all_tickers=lambda max_age: {"BTC": ticker})

        with patch("aureon.data_feeds.unified_market_cache.get_market_cache", return_value=cache):
            source = trader_mod.UnifiedMarketTrader._extract_stream_cache_source_snapshot(trader, ["BTCUSD"])

        self.assertEqual(source["source"], "live_stream_cache")
        self.assertTrue(source["stream_health"]["fresh"])
        self.assertIn("BTCUSD", source["symbols"])
        self.assertEqual(source["symbols"]["BTCUSD"]["price"], 50123.45)
        self.assertEqual(trader._stream_cache_health["symbol_count"], 1)

    def test_route_price_uses_stream_cache_before_rest_quote(self):
        trader = self._make_trader()
        trader._stream_price_ticker = lambda symbol, max_age=trader_mod.STREAM_CACHE_MAX_AGE_SEC: trader_mod.SimpleNamespace(price=123.45)  # type: ignore[method-assign]

        class KrakenProbe:
            def best_price(self, symbol):
                raise AssertionError("REST quote should not be called when stream price is fresh")

        trader.kraken = trader_mod.SimpleNamespace(client=KrakenProbe())

        self.assertEqual(trader._estimate_route_price("kraken", "XBTUSD"), 123.45)

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

    def test_multi_exchange_order_flow_routes_all_four_venues(self):
        trader = self._make_trader()
        trader.kraken_ready = True
        trader.capital_ready = True
        trader._binance_diag = {"network_ok": True, "account_ok": True, "margin_available": True, "uk_mode": False}
        trader._kraken_tradable_symbols = lambda: {"BTCUSD": "XXBTZUSD"}  # type: ignore[method-assign]
        trader._capital_tradable_symbols = lambda: {"BTCUSD": "BTCUSD"}  # type: ignore[method-assign]
        trader._alpaca_tradable_symbols = lambda: {"BTCUSD": "BTC/USD"}  # type: ignore[method-assign]
        trader._binance_tradable_symbols = lambda: {"BTCUSD": "BTCUSDT"}  # type: ignore[method-assign]
        central_beat = {
            "symbols": {
                "BTCUSD": {
                    "strength": 0.9,
                    "confidence": 0.88,
                    "support_count": 4,
                    "side": "BUY",
                    "sources": ["kraken", "capital", "alpaca", "binance"],
                    "reference_price": 50000.0,
                    "change_pct": 1.2,
                }
            }
        }
        shared_market_feed = {"symbols": {"BTCUSD": 0.9}}

        order_flow = trader._build_global_order_flow_feed({}, {}, central_beat, shared_market_feed)
        top = order_flow["active_order_flow"][0]
        routes = {(route["venue"], route["market_type"]) for route in top["execution_routes"]}

        self.assertEqual(order_flow["active_order_flow_count"], 1)
        self.assertIn(("kraken", "spot"), routes)
        self.assertIn(("kraken", "margin"), routes)
        self.assertIn(("capital", "cfd"), routes)
        self.assertIn(("alpaca", "spot"), routes)
        self.assertIn(("binance", "spot"), routes)
        self.assertIn(("binance", "margin"), routes)
        self.assertEqual(top["ready_route_count"], 6)
        self.assertEqual(top["available_route_count"], 6)
        self.assertEqual(top["held_route_count"], 0)
        for route in top["execution_routes"]:
            self.assertGreater(route["model_count"], 0)
            self.assertTrue(route["model_coverage_ready"])
            self.assertEqual(route["trade_clearance_state"], "available")
            self.assertTrue(route["end_user_trade_available"])

        action_plan = trader._build_exchange_action_plan(order_flow)
        model_coverage = action_plan["model_coverage"]
        self.assertEqual(model_coverage["route_count"], 6)
        self.assertEqual(model_coverage["ready_route_count"], 6)
        self.assertEqual(action_plan["trade_path_state"], "runtime_clearance_pending")
        self.assertTrue(action_plan["end_user_trade_available"])

        shadow_report = trader._build_shadow_trade_report(order_flow, action_plan, persist=False)
        self.assertEqual(shadow_report["shadow_count"], 6)
        self.assertEqual(shadow_report["shadow_opened_count"], 6)
        self.assertTrue(shadow_report["self_measurement"]["all_four_exchange_routes_seen"])
        self.assertFalse(shadow_report["self_measurement"]["real_exchange_mutation"])
        self.assertIs(action_plan["shadow_trading"], shadow_report)
        for shadow in shadow_report["shadows"]:
            self.assertEqual(shadow["status"], "shadow_opened")
            self.assertFalse(shadow["real_order_submitted"])
            self.assertTrue(shadow["agent_review"]["logic_validated"])
            self.assertIn("hnc_alignment_agent", shadow["agent_review"]["agents"])
            self.assertIn("runtime_clearance_agent", shadow["agent_review"]["agents"])

    def test_profit_velocity_ranking_uses_cash_price_history_and_eta(self):
        trader = self._make_trader()
        trader.kraken_ready = True
        trader.capital_ready = True
        trader._binance_diag = {"network_ok": True, "account_ok": True, "margin_available": True, "uk_mode": False}
        trader._kraken_tradable_symbols = lambda: {"BTCUSD": "XXBTZUSD", "SOLUSD": "SOLUSDT"}  # type: ignore[method-assign]
        trader._kraken_spot_tradable_symbols = lambda: {"BTCUSD": "XBTUSD", "SOLUSD": "SOLUSD"}  # type: ignore[method-assign]
        trader._capital_tradable_symbols = lambda: {"BTCUSD": "BTCUSD", "SOLUSD": "SOLUSD"}  # type: ignore[method-assign]
        trader._alpaca_tradable_symbols = lambda: {"BTCUSD": "BTC/USD", "SOLUSD": "SOL/USD"}  # type: ignore[method-assign]
        trader._binance_tradable_symbols = lambda: {"BTCUSD": "BTCUSDT", "SOLUSD": "SOLUSDT"}  # type: ignore[method-assign]
        trader._read_shadow_trade_state = lambda: {  # type: ignore[method-assign]
            "prior_verifications": [
                {
                    "id": "sol-fast",
                    "route_signature": "binance:spot:SOLUSDT:BUY",
                    "symbol": "SOLUSD",
                    "status": "validated",
                    "opened_at_epoch": 1000.0,
                    "last_verified_epoch": 1030.0,
                    "eta_seconds_actual": 30.0,
                },
                {
                    "id": "btc-slow",
                    "route_signature": "binance:spot:BTCUSDT:BUY",
                    "symbol": "BTCUSD",
                    "status": "missed_eta",
                },
            ]
        }
        central_beat = {
            "symbols": {
                "BTCUSD": {
                    "confidence": 0.95,
                    "support_count": 2,
                    "side": "BUY",
                    "sources": ["kraken", "capital"],
                    "reference_price": 50000.0,
                    "change_pct": 0.02,
                    "model_alignment": True,
                },
                "SOLUSD": {
                    "confidence": 0.72,
                    "support_count": 4,
                    "side": "BUY",
                    "sources": ["kraken", "capital", "alpaca", "binance"],
                    "reference_price": 90.0,
                    "change_pct": 0.8,
                    "model_alignment": True,
                },
            }
        }
        shared_market_feed = {"symbols": {"BTCUSD": 0.95, "SOLUSD": 0.72}}

        order_flow = trader._build_global_order_flow_feed({}, {}, central_beat, shared_market_feed)
        top = order_flow["active_order_flow"][0]

        self.assertEqual(top["symbol"], "SOLUSD")
        self.assertGreater(top["profit_velocity_score"], order_flow["active_order_flow"][1]["profit_velocity_score"])
        self.assertEqual(top["history_validated_count"], 1)
        self.assertGreaterEqual(top["cash_capable_route_count"], 1)
        self.assertLessEqual(top["estimated_target_eta_sec"], trader_mod.SHADOW_TRADE_VALIDATION_HORIZON_SEC)
        self.assertGreater(top["intelligence_mesh_score"], 0.0)
        self.assertIn("intelligence_mesh", order_flow)
        self.assertEqual(order_flow["selection_process"]["mode"], "fast_money_profit_velocity_ranked_live_shadow_selection")
        self.assertGreaterEqual(top["fast_money_score"], 0.0)
        self.assertIn("fast_money_intelligence", order_flow)

    def test_fast_money_ranking_uses_volume_momentum_and_orderbook_pressure(self):
        trader = self._make_trader()
        trader.kraken_ready = True
        trader.capital_ready = True
        trader._binance_diag = {"network_ok": True, "account_ok": True, "margin_available": True, "uk_mode": False}
        trader._kraken_tradable_symbols = lambda: {"BTCUSD": "XXBTZUSD", "SOLUSD": "SOLUSDT"}  # type: ignore[method-assign]
        trader._kraken_spot_tradable_symbols = lambda: {"BTCUSD": "XBTUSD", "SOLUSD": "SOLUSD"}  # type: ignore[method-assign]
        trader._capital_tradable_symbols = lambda: {"BTCUSD": "BTCUSD", "SOLUSD": "SOLUSD"}  # type: ignore[method-assign]
        trader._alpaca_tradable_symbols = lambda: {"BTCUSD": "BTC/USD", "SOLUSD": "SOL/USD"}  # type: ignore[method-assign]
        trader._binance_tradable_symbols = lambda: {"BTCUSD": "BTCUSDT", "SOLUSD": "SOLUSDT"}  # type: ignore[method-assign]
        trader._orderbook_pressure_snapshot = lambda item: {  # type: ignore[method-assign]
            "available": True,
            "source": "test_orderbook",
            "symbol": item.get("symbol"),
            "side": item.get("side", "BUY"),
            "pressure_side": item.get("side", "BUY"),
            "score": 0.92 if item.get("symbol") == "SOLUSD" else 0.42,
            "signed_imbalance": 0.4 if item.get("symbol") == "SOLUSD" else -0.1,
        }
        central_beat = {
            "symbols": {
                "BTCUSD": {
                    "confidence": 0.93,
                    "support_count": 3,
                    "side": "BUY",
                    "sources": ["live_stream_cache", "kraken"],
                    "reference_price": 50000.0,
                    "change_pct": 0.04,
                    "change_pct_abs_max": 0.04,
                    "volume_24h": 9000000.0,
                    "freshest_age_sec": 1.0,
                    "model_alignment": True,
                },
                "SOLUSD": {
                    "confidence": 0.74,
                    "support_count": 4,
                    "side": "BUY",
                    "sources": ["live_stream_cache", "kraken", "capital", "binance"],
                    "reference_price": 90.0,
                    "change_pct": 0.92,
                    "change_pct_abs_max": 1.2,
                    "volume_24h": 65000000.0,
                    "freshest_age_sec": 0.4,
                    "fast_money_sources": ["live_stream_cache"],
                    "model_alignment": True,
                },
            }
        }
        shared_market_feed = {"symbols": {"BTCUSD": 0.93, "SOLUSD": 0.74}}

        order_flow = trader._build_global_order_flow_feed({}, {}, central_beat, shared_market_feed)
        top = order_flow["active_order_flow"][0]

        self.assertEqual(top["symbol"], "SOLUSD")
        self.assertTrue(top["fast_money_candidate"])
        self.assertGreater(top["fast_money_score"], order_flow["active_order_flow"][1]["fast_money_score"])
        self.assertEqual(top["fast_money_profile"]["momentum_tier"], "tier_1_hot")
        self.assertEqual(top["fast_money_profile"]["orderbook_alignment"], "aligned")
        self.assertEqual(order_flow["fast_money_intelligence"]["candidate_count"], 1)
        self.assertEqual(order_flow["fast_money_intelligence"]["orderbook_probe_count"], 1)

    def test_intelligence_mesh_reports_capability_presence_and_active_bridges(self):
        trader = self._make_trader()
        central_beat = {
            "source_count": 4,
            "model_signal_feed": {"used": True},
        }
        shadow_report = {"shadow_opened_count": 2, "active_shadow_count": 2, "validated_shadow_count": 1}
        hnc_proof = {
            "systems": {
                "hnc_master_protocol": {"passed": True},
                "hnc_probability_matrix": {"passed": True},
                "seer": {"passed": True},
                "lyra": {"passed": True},
                "king": {"passed": True},
            }
        }

        mesh = trader._build_intelligence_mesh(
            central_beat=central_beat,
            shadow_trade_report=shadow_report,
            hnc_cognitive_proof=hnc_proof,
        )

        self.assertGreater(mesh["present_count"], 10)
        self.assertGreater(mesh["active_this_cycle_count"], 5)
        self.assertGreater(mesh["selection_mesh_score"], 0.0)
        statuses = {item["name"]: item["status"] for item in mesh["capabilities"]}
        self.assertEqual(statuses["UnifiedSignalEngine"], "active")
        self.assertEqual(statuses["ShadowTradeValidator"], "active")
        self.assertIn(statuses["QueenOnlineResearcher"], {"active", "available_to_mesh"})

    def test_fresh_writer_lock_is_not_honored_when_owner_pid_is_dead(self):
        trader = self._make_trader()
        lock = {
            "instance_id": "other-runtime",
            "pid": 99999999,
            "heartbeat_at": time.time(),
        }

        self.assertFalse(trader._lock_owner_is_fresh(lock, time.time()))

    def test_shadow_trade_report_verifies_prior_shadow_against_current_price(self):
        trader = self._make_trader()
        previous_state = {
            "active_shadows": [
                {
                    "id": "shadow-old",
                    "route_signature": "kraken:spot:BTCUSD:BUY",
                    "symbol": "BTCUSD",
                    "venue": "kraken",
                    "market_type": "spot",
                    "route_symbol": "BTCUSD",
                    "side": "BUY",
                    "entry_price": 100.0,
                    "target_move_pct": 0.18,
                    "expected_by_epoch": time.time() + 30.0,
                    "status": "shadow_opened",
                }
            ]
        }
        order_flow = {
            "active_order_flow": [
                {
                    "symbol": "BTCUSD",
                    "side": "BUY",
                    "confidence": 0.2,
                    "reference_price": 101.0,
                    "execution_routes": [],
                }
            ]
        }

        report = trader._build_shadow_trade_report(order_flow, {"global_guards": []}, persist=False, previous_state=previous_state)

        self.assertEqual(report["validated_shadow_count"], 1)
        self.assertEqual(report["prior_verifications"][0]["status"], "validated")
        self.assertTrue(report["prior_verifications"][0]["target_hit"])

    def test_shared_order_flow_feeds_all_unified_targets(self):
        trader = self._make_trader()
        order_flow = {
            "shared_tradable_count": 1,
            "active_order_flow": [
                {
                    "symbol": "BTCUSD",
                    "side": "BUY",
                    "confidence": 0.8,
                    "kraken_symbol": "XXBTZUSD",
                    "capital_symbol": "BTCUSD",
                    "alpaca_symbol": "BTC/USD",
                    "binance_symbol": "BTCUSDT",
                    "execution_routes": [
                        {"venue": "kraken", "market_type": "margin", "symbol": "XXBTZUSD", "ready": True},
                        {"venue": "alpaca", "market_type": "spot", "symbol": "BTC/USD", "ready": True},
                        {"venue": "binance", "market_type": "spot", "symbol": "BTCUSDT", "ready": True},
                    ],
                }
            ],
        }

        trader._feed_shared_order_flow_to_decision_logic(order_flow)

        self.assertEqual(len(trader.kraken.decision_feeds), 1)
        self.assertEqual(len(trader.capital.decision_feeds), 1)
        self.assertEqual(len(trader.alpaca.decision_feeds), 1)
        self.assertEqual(len(trader.binance.decision_feeds), 1)
        self.assertEqual(trader.binance.decision_feeds[0]["metadata"]["binance_symbol"], "BTCUSDT")

    def test_spot_symbol_mapping_filters_non_crypto_cfds(self):
        trader = self._make_trader()

        self.assertEqual(trader._to_binance_symbol("BTCUSD"), "BTCUSDT")
        self.assertEqual(trader._to_alpaca_crypto_symbol("BTCUSD"), "BTC/USD")
        self.assertEqual(trader._to_binance_symbol("XAUUSD"), "")
        self.assertEqual(trader._to_alpaca_crypto_symbol("XAUUSD"), "")

    def test_runtime_executor_submits_direct_routes_and_delegates_existing_traders_when_gates_clear(self):
        old_env = self._with_live_executor_env()

        class KrakenExec:
            def __init__(self):
                self.spot_orders = []

            def place_market_order(self, symbol, side, quantity=None, quote_qty=None):
                self.spot_orders.append((symbol, side, quantity, quote_qty))
                return {"txid": [f"kraken-{len(self.spot_orders)}"], "status": "accepted"}

        class KrakenTrader:
            def __init__(self):
                self.client = KrakenExec()

        class AlpacaExec:
            init_error = ""
            is_authenticated = True

            def __init__(self):
                self.orders = []

            def place_market_order(self, symbol, side, quantity=None, quote_qty=None):
                self.orders.append((symbol, side, quantity, quote_qty))
                return {"id": f"alpaca-{len(self.orders)}", "status": "accepted"}

        class BinanceExec:
            def __init__(self):
                self.spot_orders = []
                self.margin_orders = []

            def get_24h_ticker(self, symbol):
                return {"lastPrice": "50000"}

            def place_market_order(self, symbol, side, quantity=None, quote_qty=None):
                self.spot_orders.append((symbol, side, quantity, quote_qty))
                return {"orderId": f"spot-{len(self.spot_orders)}", "status": "FILLED"}

            def place_margin_order(self, symbol, side, quantity, leverage=2, **kwargs):
                self.margin_orders.append((symbol, side, quantity, leverage))
                return {"orderId": f"margin-{len(self.margin_orders)}", "status": "FILLED"}

        try:
            trader = self._make_trader()
            trader.kraken = KrakenTrader()
            trader.kraken_ready = True
            trader.capital_ready = True
            trader.alpaca = AlpacaExec()
            trader.binance = BinanceExec()
            trader._last_tick_started_at = time.time()
            payload = {
                "combined": {"open_positions": 0},
                "exchange_action_plan": {
                    "order_intent_publish_enabled": True,
                    "global_blockers": [],
                },
                "shared_order_flow": {
                    "active_order_flow": [
                        {
                            "symbol": "BTCUSD",
                            "side": "BUY",
                            "confidence": 0.9,
                            "support_count": 4,
                            "sources": ["kraken", "capital", "alpaca", "binance"],
                            "execution_routes": [
                                {"venue": "kraken", "market_type": "spot", "symbol": "XBTUSD", "ready": True},
                                {"venue": "kraken", "market_type": "margin", "symbol": "XXBTZUSD", "ready": True, "execution_owner": "existing_autonomous_trader_tick"},
                                {"venue": "capital", "market_type": "cfd", "symbol": "BTCUSD", "ready": True, "execution_owner": "existing_autonomous_trader_tick"},
                                {"venue": "alpaca", "market_type": "spot", "symbol": "BTC/USD", "ready": True},
                                {"venue": "binance", "market_type": "spot", "symbol": "BTCUSDT", "ready": True},
                                {"venue": "binance", "market_type": "margin", "symbol": "BTCUSDT", "ready": True},
                            ],
                        }
                    ]
                },
            }

            summary = trader._execute_runtime_order_actions(payload)

            self.assertEqual(summary["submitted_count"], 4)
            self.assertEqual(summary["delegated_count"], 2)
            self.assertEqual(summary["held_count"], 0)
            self.assertEqual(summary["trade_path_state"], "available")
            self.assertEqual(trader.kraken.client.spot_orders[0], ("XBTUSD", "buy", None, trader_mod.KRAKEN_SPOT_QUOTE_USD))
            self.assertEqual(trader.alpaca.orders[0], ("BTC/USD", "buy", None, trader_mod.ORDER_EXECUTOR_QUOTE_USD))
            self.assertEqual(trader.binance.spot_orders[0], ("BTCUSDT", "BUY", None, trader_mod.ORDER_EXECUTOR_QUOTE_USD))
            self.assertEqual(trader.binance.margin_orders[0][0], "BTCUSDT")
            self.assertGreater(trader.binance.margin_orders[0][2], 0)
        finally:
            self._restore_env(old_env)

    def test_kraken_spot_buy_records_fee_aware_fast_profit_position(self):
        class KrakenExec:
            def __init__(self):
                self.orders = []

            def get_free_balance(self, asset):
                return 500.0 if asset in {"USD", "ZUSD"} else 0.0

            def get_ticker(self, symbol):
                return {"price": 100.0, "bid": 99.99, "ask": 100.01}

            def place_market_order(self, symbol, side, quantity=None, quote_qty=None):
                self.orders.append((symbol, side, quantity, quote_qty))
                return {"orderId": "KB1", "executedQty": "0.65", "status": "FILLED"}

        class KrakenTrader:
            def __init__(self):
                self.client = KrakenExec()

        with tempfile.TemporaryDirectory() as tmp:
            old_state = trader_mod.KRAKEN_SPOT_POSITION_STATE_PATH
            old_public = trader_mod.KRAKEN_SPOT_POSITION_PUBLIC_PATH
            trader_mod.KRAKEN_SPOT_POSITION_STATE_PATH = Path(tmp) / "state.json"
            trader_mod.KRAKEN_SPOT_POSITION_PUBLIC_PATH = Path(tmp) / "public.json"
            try:
                trader = self._make_trader()
                trader.kraken = KrakenTrader()
                result = trader._execute_kraken_spot_route("BUY", "XBTUSD", 65.0)

                self.assertTrue(result["ok"], result)
                self.assertEqual(result["cost_profile"]["estimated_round_trip_cost_usd"], 0.52)
                self.assertEqual(result["fast_profit_position"]["id"], "KB1")
                state = trader._load_kraken_spot_fast_profit_state()
                self.assertEqual(len(state["open_positions"]), 1)
                self.assertEqual(state["open_positions"][0]["entry_fee_usd"], 0.26)
            finally:
                trader_mod.KRAKEN_SPOT_POSITION_STATE_PATH = old_state
                trader_mod.KRAKEN_SPOT_POSITION_PUBLIC_PATH = old_public

    def test_kraken_spot_fast_profit_monitor_sells_only_true_net_profit(self):
        old_env = self._with_live_executor_env()

        class KrakenExec:
            def __init__(self):
                self.orders = []

            def get_ticker(self, symbol):
                return {"price": 101.0, "bid": 101.0, "ask": 101.02}

            def place_market_order(self, symbol, side, quantity=None, quote_qty=None):
                self.orders.append((symbol, side, quantity, quote_qty))
                return {"orderId": "KS1", "status": "FILLED"}

        class KrakenTrader:
            def __init__(self):
                self.client = KrakenExec()

        with tempfile.TemporaryDirectory() as tmp:
            old_state = trader_mod.KRAKEN_SPOT_POSITION_STATE_PATH
            old_public = trader_mod.KRAKEN_SPOT_POSITION_PUBLIC_PATH
            old_min = trader_mod.KRAKEN_SPOT_FAST_PROFIT_MIN_HOLD_SEC
            trader_mod.KRAKEN_SPOT_POSITION_STATE_PATH = Path(tmp) / "state.json"
            trader_mod.KRAKEN_SPOT_POSITION_PUBLIC_PATH = Path(tmp) / "public.json"
            trader_mod.KRAKEN_SPOT_FAST_PROFIT_MIN_HOLD_SEC = 0.0
            try:
                trader = self._make_trader()
                trader.kraken = KrakenTrader()
                trader.kraken_ready = True
                trader._kraken_spot_fast_profit_state = {
                    "schema_version": 1,
                    "open_positions": [{
                        "id": "P1",
                        "symbol": "XBTUSD",
                        "quantity": 1.0,
                        "entry_price": 100.0,
                        "entry_value_usd": 100.0,
                        "entry_fee_usd": 0.10,
                        "opened_at_epoch": time.time() - 5.0,
                        "status": "open",
                    }],
                    "closed_positions": [],
                    "last_check": {},
                }

                closed = trader._monitor_kraken_spot_fast_profit()

                self.assertEqual(len(closed), 1)
                self.assertEqual(trader.kraken.client.orders[0][1], "sell")
                self.assertGreater(closed[0]["fast_profit_capture"]["true_net_profit_usd"], 0.0)
                state = trader._load_kraken_spot_fast_profit_state()
                self.assertEqual(state["open_positions"], [])
                self.assertEqual(state["last_check"]["closed_count"], 1)
            finally:
                trader_mod.KRAKEN_SPOT_POSITION_STATE_PATH = old_state
                trader_mod.KRAKEN_SPOT_POSITION_PUBLIC_PATH = old_public
                trader_mod.KRAKEN_SPOT_FAST_PROFIT_MIN_HOLD_SEC = old_min
                self._restore_env(old_env)

    def test_executor_route_timeout_holds_tick_without_duplicate_route(self):
        old_timeout = trader_mod.ORDER_EXECUTOR_ROUTE_TIMEOUT_SEC
        old_abandon = trader_mod.ORDER_EXECUTOR_ROUTE_ABANDON_AFTER_SEC
        trader_mod.ORDER_EXECUTOR_ROUTE_TIMEOUT_SEC = 0.02
        trader_mod.ORDER_EXECUTOR_ROUTE_ABANDON_AFTER_SEC = 1.0
        try:
            trader = self._make_trader()
            route_key = "kraken:spot:XBTUSD:BUY"

            def slow_route():
                time.sleep(0.18)
                return {"ok": True, "venue": "kraken", "market_type": "spot", "symbol": "XBTUSD"}

            first = trader._run_executor_route_with_timeout(
                route_key,
                "kraken",
                "spot",
                "XBTUSD",
                "BUY",
                slow_route,
            )
            second = trader._run_executor_route_with_timeout(
                route_key,
                "kraken",
                "spot",
                "XBTUSD",
                "BUY",
                lambda: {"ok": True},
            )

            self.assertTrue(first["timeout"])
            self.assertEqual(first["reason"], "executor_route_timeout")
            self.assertEqual(second["reason"], "executor_route_inflight")

            time.sleep(0.25)
            snapshot = trader._executor_route_snapshot()
            self.assertEqual(snapshot["inflight_count"], 0)
            self.assertTrue(snapshot["latest_async_results"][0]["ok"])
            self.assertIn(route_key, trader._execution_memory)
        finally:
            trader_mod.ORDER_EXECUTOR_ROUTE_TIMEOUT_SEC = old_timeout
            trader_mod.ORDER_EXECUTOR_ROUTE_ABANDON_AFTER_SEC = old_abandon

    def test_hnc_cognitive_proof_runs_master_flow_over_real_runtime_data(self):
        trader = self._make_trader()
        central_beat = {
            "source_count": 4,
            "sources": [{"source": "kraken"}, {"source": "capital"}, {"source": "alpaca"}, {"source": "binance"}],
            "symbols": {
                "BTCUSD": {
                    "symbol": "BTCUSD",
                    "side": "BUY",
                    "confidence": 0.82,
                    "support_count": 4,
                    "reference_price": 50000.0,
                    "change_pct": 1.1,
                    "model_alignment": True,
                }
            },
        }
        order_flow = {
            "active_order_flow": [
                {
                    "symbol": "BTCUSD",
                    "side": "BUY",
                    "confidence": 0.82,
                    "support_count": 4,
                    "reference_price": 50000.0,
                    "change_pct": 1.1,
                    "model_alignment": True,
                    "execution_routes": [
                        {"venue": "kraken", "market_type": "spot", "symbol": "XBTUSD", "ready": True},
                        {"venue": "kraken", "market_type": "margin", "symbol": "XXBTZUSD", "ready": True},
                        {"venue": "capital", "market_type": "cfd", "symbol": "BTCUSD", "ready": True},
                        {"venue": "alpaca", "market_type": "spot", "symbol": "BTC/USD", "ready": True},
                        {"venue": "binance", "market_type": "spot", "symbol": "BTCUSDT", "ready": True},
                        {"venue": "binance", "market_type": "margin", "symbol": "BTCUSDT", "ready": True},
                    ],
                }
            ]
        }
        action_plan = {
            "venue_count": 6,
            "ready_venue_count": 6,
            "venues": {name: {"ready": True} for name in ["kraken_spot", "kraken_margin", "capital_cfd", "alpaca_spot", "binance_spot", "binance_margin"]},
            "runtime_clearances": [],
        }
        shadow_report = {
            "enabled": True,
            "shadow_opened_count": 6,
            "active_shadow_count": 6,
            "validated_shadow_count": 1,
            "self_measurement": {"agent_average_score": 0.91},
        }

        proof = trader._build_hnc_cognitive_proof(central_beat, order_flow, action_plan, shadow_report, persist=False)

        self.assertEqual(proof["auris_nodes"]["node_count"], 9)
        self.assertTrue(proof["real_data"]["passed"])
        self.assertTrue(proof["master_formula"]["evaluated"])
        self.assertGreater(proof["master_formula"]["score"], 0.5)
        self.assertTrue(proof["systems"]["seer"]["passed"])
        self.assertTrue(proof["systems"]["lyra"]["passed"])
        self.assertTrue(proof["systems"]["king"]["passed"])
        cycle = proof["operating_cycle"]
        self.assertEqual(cycle["cycle_order"], ["who", "what", "where", "when", "how", "act"])
        self.assertTrue(cycle["passed"])
        self.assertTrue(cycle["fed_to_decision_logic"])
        self.assertEqual(cycle["step_count"], 6)
        self.assertEqual(cycle["passed_count"], 6)
        self.assertEqual(cycle["auris_node_count"], 9)
        self.assertEqual(cycle["decision_output"]["action_state"], "runtime_gated_order_intent_ready")
        self.assertTrue(any(step["step"] == "hnc_operating_cycle" for step in proof["flow"]))
        self.assertEqual(proof["passed_count"], proof["step_count"])
        self.assertIs(action_plan["hnc_cognitive_proof"], proof)
        self.assertIs(action_plan["hnc_operating_cycle"], cycle)

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
        self.assertIn("api_governor", health)

    def test_runtime_health_marks_stalled_tick_without_confusing_heartbeat_freshness(self):
        trader = self._make_trader()
        now = time.time()
        trader._latest_dashboard_payload = {
            "generated_at": "2026-03-31T10:00:00",
            "runtime_heartbeat": {"heartbeat_at_iso": "2026-03-31T10:01:00"},
            "combined": {"open_positions": 1, "kraken_equity": 100.0, "capital_equity_gbp": 50.0},
        }
        trader.kraken_ready = True
        trader.capital_ready = True
        trader.alpaca = object()
        trader.binance = object()
        trader._binance_diag = {"network_ok": True}
        trader._last_tick_completed_at = now - 120
        trader._last_tick_started_at = now - 60

        health = trader.get_runtime_health()

        self.assertTrue(health["stale"])
        self.assertEqual(health["stale_reason"], "tick_in_progress_stalled")
        self.assertTrue(health["runtime_watchdog"]["tick_stale"])
        self.assertTrue(health["runtime_watchdog"]["file_heartbeat_is_not_market_freshness"])

    def test_open_positions_are_first_class_central_beat_symbols(self):
        trader = self._make_trader()
        source = trader._extract_trader_source_snapshot(
            "kraken",
            {
                "ok": True,
                "positions": [
                    {"symbol": "SOL/USD", "side": "LONG"},
                    {"pair": "XBT/USD", "direction": "SHORT"},
                ],
            },
        )

        self.assertIn("SOLUSD", source["symbols"])
        self.assertIn("BTCUSD", source["symbols"])
        self.assertEqual(source["symbols"]["SOLUSD"]["reason"], "open_position")
        self.assertEqual(source["top_confidence"], 1.0)

    def test_quote_probes_use_cache_before_second_api_call(self):
        trader = self._make_trader()

        class AlpacaProbe:
            def __init__(self):
                self.calls = 0
                self.init_error = ""
                self.is_authenticated = True

            def get_ticker(self, symbol):
                self.calls += 1
                return {"price": 100.0, "change_pct": 1.5}

        probe = AlpacaProbe()
        trader.alpaca = probe

        first = trader._extract_alpaca_source_snapshot(["BTCUSD"])
        second = trader._extract_alpaca_source_snapshot(["BTCUSD"])

        self.assertEqual(probe.calls, 1)
        self.assertEqual(first["symbols"]["BTCUSD"]["side"], "BUY")
        self.assertEqual(second["symbols"]["BTCUSD"]["side"], "BUY")


if __name__ == "__main__":
    unittest.main()
