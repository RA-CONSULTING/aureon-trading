#!/usr/bin/env python3
import time
import unittest

from aureon.exchanges.capital_cfd_trader import CAPITAL_MIN_PROFIT_GBP, CFD_FLAGS, CapitalCFDTrader, CFDPosition, CFDShadowTrade


class ClientStub:
    def __init__(self, positions=None, close_result=None, fallback_result=None, open_result=None, confirm_result=None, accounts=None, resolved_market=None, market_snapshot=None):
        self._positions = list(positions or [])
        self._position_batches = None
        self._close_result = close_result if close_result is not None else {"success": True}
        self._fallback_result = fallback_result if fallback_result is not None else {"dealReference": "FALLBACK"}
        self._open_result = open_result if open_result is not None else {"dealReference": "REF1"}
        self._confirm_result = confirm_result if confirm_result is not None else {"dealId": "DOPEN", "level": 7282.6}
        self._accounts = list(accounts or [{"accountId": "A1", "balance": 54.34, "available": 54.34, "currency": "GBP"}])
        self._resolved_market = dict(resolved_market or {"epic": "CS.D.SILVER.CFD.IP", "symbol": "SILVER"})
        self._market_snapshot = dict(market_snapshot or {
            "instrument": {"epic": "CS.D.SILVER.CFD.IP", "name": "Silver"},
            "snapshot": {"marketStatus": "TRADEABLE", "bid": 7249.8, "offer": 7251.8},
            "dealingRules": {"minDealSize": {"value": 1}},
        })
        self.order_calls = []

    def get_positions(self):
        if self._position_batches is not None:
            if len(self._position_batches) > 1:
                return list(self._position_batches.pop(0))
            return list(self._position_batches[0])
        return list(self._positions)

    def get_accounts(self):
        return list(self._accounts)

    def get_account_balance(self):
        return {}

    def close_position(self, deal_id: str):
        return dict(self._close_result)

    def place_market_order(self, symbol: str, side: str, size: float):
        side = side.upper()
        if side in {"BUY", "SELL"}:
            self.order_calls.append((symbol, side, size))
            return dict(self._open_result)
        return dict(self._fallback_result)

    def confirm_order(self, deal_reference: str):
        return dict(self._confirm_result)

    def _resolve_market(self, symbol: str):
        return dict(self._resolved_market)

    def _get_market_snapshot(self, epic: str):
        return dict(self._market_snapshot)


class ThoughtBusStub:
    def __init__(self):
        self.published = []

    def publish(self, thought):
        self.published.append(thought)

    def recall(self, prefix: str, limit: int = 8):
        return []


class TestCapitalCFDSync(unittest.TestCase):
    def _build_trader(self, client):
        trader = CapitalCFDTrader.__new__(CapitalCFDTrader)
        trader.client = client
        trader.positions = []
        trader.shadow_trades = []
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
        trader._latest_tick_line = ""
        trader._latest_order_error = ""
        trader._latest_order_trace_path = ""
        trader._capital_snapshot_cache = {}
        trader._capital_snapshot_error = ""
        trader._latest_target_snapshot = {}
        trader._latest_candidate_snapshot = []
        trader._swarm_snapshot = {"enabled": True, "leader": {}, "votes": [], "ranked": []}
        trader._hive_boosts = {}
        trader._rejection_cooldowns = {}
        trader._quad_gate_at = 0.0
        trader._quad_gate_ok = True
        trader._signal_brain = None
        trader._trade_profit_validator = None
        trader.unified_registry = None
        trader.unified_decision_engine = None
        trader.orchestrator = None
        trader.timeline_oracle = None
        trader.harmonic_fusion = None
        trader.thought_bus = None
        trader._registry_snapshot = {}
        trader._decision_snapshot = {}
        trader._orchestrator_snapshot = {}
        trader._timeline_snapshot = {}
        trader._fusion_snapshot = {}
        trader._lane_snapshot = {}
        trader._thought_bus_snapshot = {}
        trader._cognition_snapshot = {}
        trader._recent_closed_trades = []
        trader._shadow_validated_count = 0
        trader._shadow_failed_count = 0
        trader._dtp_trackers = {}
        trader.start_time = time.time()
        trader.starting_equity_gbp = 0.0
        trader._required_tp_pct_for_profit = lambda price, size: (CAPITAL_MIN_PROFIT_GBP / max(price * size, 0.0001)) * 100.0
        return trader

    def test_capital_preflight_reports_minimum_size_failure(self):
        trader = self._build_trader(ClientStub(market_snapshot={
            "instrument": {"epic": "CS.D.SILVER.CFD.IP", "name": "Silver"},
            "snapshot": {"marketStatus": "TRADEABLE", "bid": 7249.8, "offer": 7251.8},
            "dealingRules": {"minDealSize": {"value": 2}},
        }))

        preflight = trader._capital_preflight(
            "SILVER",
            1,
            {"price": 7250.8, "bid": 7249.8, "ask": 7251.8, "epic": "CS.D.SILVER.CFD.IP"},
            {"class": "commodity", "size": 1, "tp_pct": 0.75, "sl_pct": 0.45},
        )

        self.assertFalse(preflight["ok"])
        self.assertEqual(preflight["minimum_deal_size"], 2.0)
        self.assertIn("below Capital minimum", preflight["reason"])

    def test_capital_preflight_reports_market_status_and_balance(self):
        trader = self._build_trader(ClientStub(
            accounts=[{"accountId": "A1", "balance": 54.34, "available": 12.5, "currency": "GBP"}],
            market_snapshot={
                "instrument": {"epic": "CS.D.SILVER.CFD.IP", "name": "Silver"},
                "snapshot": {"marketStatus": "CLOSED", "bid": 7249.8, "offer": 7251.8},
                "dealingRules": {"minDealSize": {"value": 1}},
            },
        ))

        preflight = trader._capital_preflight(
            "SILVER",
            1,
            {"price": 7250.8, "bid": 7249.8, "ask": 7251.8, "epic": "CS.D.SILVER.CFD.IP"},
            {"class": "commodity", "size": 1, "tp_pct": 0.75, "sl_pct": 0.45},
        )

        self.assertFalse(preflight["ok"])
        self.assertEqual(preflight["available_balance"], 12.5)
        self.assertEqual(preflight["market_status"], "CLOSED")
        self.assertEqual(preflight["epic"], "CS.D.SILVER.CFD.IP")
        self.assertGreater(preflight["spread"], 0.0)
        self.assertIn("market not tradeable", preflight["reason"])

    def test_open_position_stops_on_preflight_failure(self):
        client = ClientStub(market_snapshot={
            "instrument": {"epic": "CS.D.SILVER.CFD.IP", "name": "Silver"},
            "snapshot": {"marketStatus": "TRADEABLE", "bid": 7249.8, "offer": 7251.8},
            "dealingRules": {"minDealSize": {"value": 2}},
        })
        trader = self._build_trader(client)

        result = trader._open_position(
            "SILVER",
            {"class": "commodity", "size": 1, "tp_pct": 0.75, "sl_pct": 0.45},
            {"price": 7282.6, "ask": 7282.6, "bid": 7281.6, "epic": "CS.D.SILVER.CFD.IP"},
        )

        self.assertIsNone(result)
        self.assertIn("preflight failed", trader._latest_order_error)
        self.assertEqual(client.order_calls, [])

    def test_sized_cfg_from_preflight_raises_to_capital_minimum_when_affordable(self):
        trader = self._build_trader(ClientStub())

        adjusted = trader._sized_cfg_from_preflight(
            {"class": "commodity", "size": 1, "tp_pct": 0.75, "sl_pct": 0.45},
            {"minimum_deal_size": 2, "price": 10, "available_balance": 54.34},
        )

        self.assertIsNotNone(adjusted)
        self.assertEqual(adjusted["size"], 2)

    def test_sized_cfg_from_preflight_refuses_unaffordable_minimum(self):
        trader = self._build_trader(ClientStub())

        adjusted = trader._sized_cfg_from_preflight(
            {"class": "commodity", "size": 1, "tp_pct": 0.75, "sl_pct": 0.45},
            {"minimum_deal_size": 10, "price": 100, "available_balance": 54.34},
        )

        self.assertIsNone(adjusted)

    def test_apply_hft_analysis_zeroes_candidate_when_costs_fail(self):
        trader = self._build_trader(ClientStub())
        trader._capital_cost_profile = lambda symbol, size, price, tp_pct: {
            "notional": 100.0,
            "expected_gross_profit": 0.01,
            "round_trip_cost": 0.05,
            "expected_net_profit": -0.04,
        }

        scored = [{
            "symbol": "SILVER",
            "score": 2.0,
            "size": 1.0,
            "price": 100.0,
            "change_pct": 2.0,
            "spread_pct": 0.1,
            "tp_pct": 0.75,
        }]

        trader._apply_hft_analysis(scored)

        self.assertEqual(scored[0]["score"], 0.0)
        self.assertEqual(scored[0]["hft_reason"], "cost_gate")

    def test_apply_hft_analysis_uses_signal_brain_when_available(self):
        class BrainStub:
            def decide(self, symbol, base_score, features, population_scores):
                class Decision:
                    score = base_score * 3
                    coherence = 0.77
                return Decision()

        trader = self._build_trader(ClientStub())
        trader._signal_brain = BrainStub()
        trader._capital_cost_profile = lambda symbol, size, price, tp_pct: {
            "notional": 100.0,
            "expected_gross_profit": 2.0,
            "round_trip_cost": 0.2,
            "expected_net_profit": 1.8,
        }

        scored = [{
            "symbol": "SILVER",
            "score": 2.0,
            "size": 1.0,
            "price": 100.0,
            "change_pct": 2.0,
            "spread_pct": 0.1,
            "tp_pct": 0.75,
        }]

        trader._apply_hft_analysis(scored)

        self.assertEqual(scored[0]["score"], 6.0)
        self.assertEqual(scored[0]["brain_coherence"], 0.77)

    def test_status_lines_include_latest_monitor_line(self):
        trader = self._build_trader(ClientStub())
        trader._latest_monitor_line = "CAPITAL SLOT FILL EURUSD BUY deal=D1"

        lines = trader.status_lines()

        self.assertTrue(any("Monitor: CAPITAL SLOT FILL EURUSD BUY deal=D1" in line for line in lines))

    def test_get_capital_snapshot_reuses_last_good_snapshot_when_feed_goes_empty(self):
        client = ClientStub(accounts=[{"accountId": "A1", "balance": 129.07, "available": 129.07, "currency": "GBP"}])
        trader = self._build_trader(client)

        first = trader.get_capital_snapshot()
        client._accounts = []
        second = trader.get_capital_snapshot()

        self.assertEqual(first["equity_gbp"], 129.07)
        self.assertEqual(second["equity_gbp"], 129.07)
        self.assertEqual(second["free_gbp"], 129.07)
        self.assertEqual(second.get("stale", 0.0), 1.0)

    def test_status_lines_include_tick_and_stale_capital_feed(self):
        trader = self._build_trader(ClientStub())
        trader._latest_tick_line = "CAPITAL TICK sync=0.01s prices=0.02s"
        trader._capital_snapshot_cache = {
            "equity_gbp": 129.07,
            "free_gbp": 129.07,
            "used_gbp": 0.0,
            "budget_gbp": 90.35,
            "target_pct_equity": 0.01,
        }

        trader.client._accounts = []
        lines = trader.status_lines()

        self.assertTrue(any("Tick: CAPITAL TICK sync=0.01s prices=0.02s" in line for line in lines))
        self.assertTrue(any("CapitalFeed: stale_snapshot" in line for line in lines))

    def test_capital_cost_profile_uses_passed_quote_not_refetched_quote(self):
        trader = self._build_trader(ClientStub())
        trader._trade_profit_validator = object()
        trader._get_price = lambda symbol: {"bid": 1.0, "ask": 99.0}

        profile = trader._capital_cost_profile(
            "EURUSD",
            0.01,
            1.085,
            0.921658986175115,
            bid=1.08498,
            ask=1.08502,
        )

        self.assertAlmostEqual(profile["round_trip_cost"], 0.0000005, places=10)
        self.assertGreater(profile["expected_net_profit"], 0.00009)

    def test_capital_preflight_no_longer_produces_absurd_stock_costs_from_mismatched_refetch(self):
        client = ClientStub(
            accounts=[{"accountId": "A1", "balance": 129.07, "available": 129.07, "currency": "GBP"}],
            market_snapshot={
                "instrument": {"epic": "AAPL.EPIC", "name": "Apple"},
                "snapshot": {"marketStatus": "TRADEABLE", "bid": 199.96, "offer": 200.04},
                "dealingRules": {"minDealSize": {"value": 1}},
            },
        )
        trader = self._build_trader(client)
        trader._trade_profit_validator = object()
        trader._get_price = lambda symbol: {"bid": 150.0, "ask": 175.0}

        preflight = trader._capital_preflight(
            "AAPL",
            1.0,
            {"price": 200.0, "bid": 199.96, "ask": 200.04, "epic": "AAPL.EPIC"},
            {"class": "stock", "size": 1.0, "tp_pct": 0.9, "sl_pct": 0.55},
        )

        self.assertLess(preflight["round_trip_cost"], 0.2)
        self.assertGreater(preflight["expected_net_profit"], 1.6)
        self.assertTrue(preflight["ok"])

    def test_queue_background_shadows_runs_even_when_live_lanes_are_full(self):
        trader = self._build_trader(ClientStub())
        trader.positions = [
            CFDPosition("US100", "D1", "E1", "BUY", 1.0, 100.0, 101.0, 99.0, "indices"),
            CFDPosition("AUDUSD", "D2", "E2", "SELL", 0.01, 1.0, 0.99, 1.01, "currencies"),
        ]
        created = []
        trader._ranked_opportunities = lambda: [
            ("US500", {"direction": "SELL", "class": "index", "size": 1.0}, {"price": 5000.0, "bid": 4999.0, "ask": 5001.0}),
            ("EURUSD", {"direction": "BUY", "class": "forex", "size": 0.01}, {"price": 1.085, "bid": 1.0849, "ask": 1.0851}),
        ]
        trader._capital_preflight = lambda symbol, size, ticker, cfg: {
            "ok": True,
            "symbol": symbol,
            "price": ticker.get("price"),
            "bid": ticker.get("bid"),
            "ask": ticker.get("ask"),
        }
        trader._create_shadow = lambda symbol, cfg, ticker: created.append((symbol, cfg["direction"])) or object()

        queued = trader._queue_background_shadows()

        self.assertEqual(queued, 2)
        self.assertEqual(created, [("US500", "SELL"), ("EURUSD", "BUY")])

    def test_active_universe_can_focus_symbols(self):
        trader = self._build_trader(ClientStub())
        original = __import__("aureon.exchanges.capital_cfd_trader", fromlist=["CAPITAL_FOCUS_SYMBOLS"])
        old_focus = original.CAPITAL_FOCUS_SYMBOLS
        try:
            original.CAPITAL_FOCUS_SYMBOLS = ("GOLD",)
            active = trader._active_universe()
            self.assertEqual(set(active.keys()), {"GOLD"})
        finally:
            original.CAPITAL_FOCUS_SYMBOLS = old_focus

    def test_deadman_guard_flattens_positions_when_stale(self):
        trader = self._build_trader(ClientStub())
        trader.positions = [
            CFDPosition("GOLD", "D1", "E1", "BUY", 0.1, 3000.0, 3020.0, 2980.0, "commodity"),
            CFDPosition("GOLD", "D2", "E2", "SELL", 0.1, 3000.0, 2980.0, 3020.0, "commodity"),
        ]
        closed = []
        trader._close_position = lambda pos, reason: closed.append((pos.deal_id, reason)) or {"deal_id": pos.deal_id}

        original = __import__("aureon.exchanges.capital_cfd_trader", fromlist=["CAPITAL_DEADMAN_ENABLED", "CAPITAL_DEADMAN_STALE_SECS"])
        old_enabled = original.CAPITAL_DEADMAN_ENABLED
        old_stale = original.CAPITAL_DEADMAN_STALE_SECS
        try:
            original.CAPITAL_DEADMAN_ENABLED = True
            original.CAPITAL_DEADMAN_STALE_SECS = 5.0
            trader._last_deadman_kick_at = time.time() - 10.0
            trader._deadman_guard(time.time())
        finally:
            original.CAPITAL_DEADMAN_ENABLED = old_enabled
            original.CAPITAL_DEADMAN_STALE_SECS = old_stale

        self.assertEqual(len(closed), 2)
        self.assertTrue(all("DEADMAN_STALE" in reason for _, reason in closed))

    def test_continuous_watch_symbols_includes_universe_positions_and_shadows(self):
        trader = self._build_trader(ClientStub())
        trader.positions = [
            CFDPosition("US100", "D1", "E1", "BUY", 1.0, 100.0, 101.0, 99.0, "indices"),
        ]
        trader.shadow_trades = [
            CFDShadowTrade("GOLD", "BUY", "commodity", 0.1, 3000.0, 0.75, 10.0),
        ]
        original = __import__("aureon.exchanges.capital_cfd_trader", fromlist=["CAPITAL_FOCUS_SYMBOLS"])
        old_focus = original.CAPITAL_FOCUS_SYMBOLS
        try:
            original.CAPITAL_FOCUS_SYMBOLS = ("GOLD",)
            watched = trader._continuous_watch_symbols()
        finally:
            original.CAPITAL_FOCUS_SYMBOLS = old_focus

        self.assertEqual(watched, ["GOLD", "US100"])

    def test_handle_live_price_events_triggers_actuation_on_meaningful_move(self):
        trader = self._build_trader(ClientStub())
        calls = []
        trader._quad_gate = lambda: True
        trader._find_best_opportunity = lambda: calls.append("find")
        trader._queue_background_shadows = lambda: calls.append("queue") or 1
        trader._fill_live_monitoring_slots = lambda now: calls.append("fill") or True

        original = __import__("aureon.exchanges.capital_cfd_trader", fromlist=["CAPITAL_LIVE_EVENT_TRIGGER_PCT"])
        old_trigger = original.CAPITAL_LIVE_EVENT_TRIGGER_PCT
        try:
            original.CAPITAL_LIVE_EVENT_TRIGGER_PCT = 0.03
            trader._last_live_event_at = 0.0
            trader._handle_live_price_events(
                {"GOLD": {"price": 3000.0}},
                {"GOLD": {"price": 3001.2}},
            )
        finally:
            original.CAPITAL_LIVE_EVENT_TRIGGER_PCT = old_trigger

        self.assertEqual(calls, ["find", "queue", "fill"])

    def test_self_confidence_boosts_score_when_recent_validation_is_strong(self):
        trader = self._build_trader(ClientStub())
        trader._shadow_validated_count = 5
        trader._shadow_failed_count = 0
        trader._capital_cost_profile = lambda symbol, size, price, tp_pct: {
            "notional": 100.0,
            "expected_gross_profit": 2.0,
            "round_trip_cost": 0.2,
            "expected_net_profit": 1.8,
        }
        scored = [{
            "symbol": "SILVER",
            "direction": "BUY",
            "score": 2.0,
            "size": 1.0,
            "price": 100.0,
            "change_pct": 2.0,
            "spread_pct": 0.1,
            "tp_pct": 0.75,
            "brain_coherence": 0.8,
        }]

        trader._apply_intelligence_overlays(scored)

        self.assertGreater(scored[0]["self_confidence"], 0.55)
        self.assertGreater(scored[0]["self_confidence_boost"], 1.0)
        self.assertGreater(scored[0]["score"], 2.0)

    def test_shadow_promotion_gate_shortens_wait_when_confidence_is_high(self):
        trader = self._build_trader(ClientStub())
        trader._shadow_validated_count = 4
        trader._shadow_failed_count = 0
        trader._latest_target_snapshot = {
            "symbol": "SILVER",
            "direction": "BUY",
            "timeline_confidence": 0.9,
            "fusion_global_coherence": 0.9,
        }
        trader._latest_candidate_snapshot = [{
            "symbol": "SILVER",
            "direction": "BUY",
            "brain_coherence": 0.9,
        }]
        trader._probability_validation_snapshot = lambda force=False: {
            "ok": True,
            "direction_accuracy": 0.9,
            "profit_factor": 1.5,
        }
        gate = trader._build_shadow_promotion_gate(
            CFDShadowTrade(
                symbol="SILVER",
                direction="BUY",
                asset_class="commodity",
                size=1,
                entry_price=100.0,
                target_move_pct=0.1,
                score=2.0,
            ),
            {"change_pct": 1.5},
        )

        self.assertTrue(gate["ok"])
        self.assertLess(gate["validation_window_secs"], trader.SHADOW_MIN_VALIDATE)

    def test_growth_metrics_capture_session_velocity_and_trend(self):
        trader = self._build_trader(ClientStub())
        trader.start_time = time.time() - 3600
        trader.starting_equity_gbp = 100.0
        trader.get_capital_snapshot = lambda: {
            "equity_gbp": 112.0,
            "free_gbp": 90.0,
            "used_gbp": 22.0,
            "budget_gbp": 50.0,
            "target_pct_equity": 0.01,
        }
        trader.stats.update({
            "trades_closed": 4.0,
            "winning_trades": 3.0,
            "losing_trades": 1.0,
            "total_pnl_gbp": 8.0,
        })
        trader._recent_closed_trades = [
            {"net_pnl": 1.0},
            {"net_pnl": 3.0},
            {"net_pnl": 6.0},
        ]

        metrics = trader._compute_growth_metrics()

        self.assertAlmostEqual(metrics["equity_growth_pct"], 12.0)
        self.assertGreater(metrics["pnl_per_hour_gbp"], 7.9)
        self.assertAlmostEqual(metrics["trades_per_hour"], 4.0, places=1)
        self.assertEqual(metrics["trend"], "accelerating")

    def test_capital_cost_profile_uses_live_spread_instead_of_generic_fee_profile(self):
        trader = self._build_trader(ClientStub())
        trader._trade_profit_validator = object()
        trader._prices = {
            "SILVER": {"bid": 99.9, "ask": 100.1, "price": 100.0}
        }

        costs = trader._capital_cost_profile("SILVER", 1.0, 100.0, 0.75)

        self.assertAlmostEqual(costs["expected_gross_profit"], 0.75, places=4)
        self.assertLess(costs["round_trip_cost"], 0.25)
        self.assertGreater(costs["expected_net_profit"], 0.5)

    def test_close_position_feeds_learning_back_into_brain(self):
        class BrainStub:
            def __init__(self):
                self.calls = []

            def learn_from_outcome(self, symbol, pnl, confidence=0.5):
                self.calls.append((symbol, pnl, confidence))
                return {"symbol_bias": 0.1, "reward": pnl}

            def learning_snapshot(self):
                return {"total_feedback": 1.0, "win_bias": 1.0}

        trader = self._build_trader(ClientStub(close_result={"success": True}))
        trader._signal_brain = BrainStub()
        trader._latest_candidate_snapshot = [{
            "symbol": "SILVER",
            "brain_coherence": 0.8,
            "self_confidence": 0.7,
        }]
        pos = CFDPosition(
            symbol="SILVER",
            deal_id="D5",
            epic="CS.D.SILVER.CFD.IP",
            direction="BUY",
            size=1,
            entry_price=100.0,
            tp_price=101.0,
            sl_price=99.0,
            asset_class="commodity",
            current_price=101.0,
        )

        record = trader._close_position(pos, "TP_HIT")

        self.assertIn("learning_update", record)
        self.assertEqual(trader._signal_brain.calls[0][0], "SILVER")
        self.assertGreater(trader._signal_brain.calls[0][1], 0.0)

    def test_close_position_publishes_learning_to_queen_systems(self):
        class BrainStub:
            def learn_from_outcome(self, symbol, pnl, confidence=0.5):
                return {"symbol_bias": 0.12, "reward": pnl}

        trader = self._build_trader(ClientStub(close_result={"success": True}))
        trader._signal_brain = BrainStub()
        trader.thought_bus = ThoughtBusStub()
        from aureon.core.aureon_thought_bus import Thought
        import aureon.exchanges.capital_cfd_trader as capital_cfd_trader_module
        capital_cfd_trader_module.Thought = Thought
        pos = CFDPosition(
            symbol="SILVER",
            deal_id="D6",
            epic="CS.D.SILVER.CFD.IP",
            direction="BUY",
            size=1,
            entry_price=100.0,
            tp_price=101.0,
            sl_price=99.0,
            asset_class="commodity",
            current_price=101.0,
        )

        trader._close_position(pos, "TP_HIT")

        topics = [thought.topic for thought in trader.thought_bus.published]
        self.assertIn("brain.learning", topics)
        self.assertIn("queen.learning", topics)

    def test_score_symbol_maps_negative_momentum_to_sell(self):
        trader = self._build_trader(ClientStub())

        score, direction = trader._score_symbol(
            "SILVER",
            {"class": "commodity", "size": 1, "tp_pct": 0.75, "sl_pct": 0.45, "max_spread_pct": 0.15, "momentum_threshold": 0.20},
            {"price": 100.0, "bid": 99.9, "ask": 100.1, "change_pct": -2.5},
        )

        self.assertGreater(score, 0.0)
        self.assertEqual(direction, "SELL")

    def test_effective_tp_pct_uses_penny_target_when_enabled(self):
        old_flag = CFD_FLAGS["penny_take_profit"]
        CFD_FLAGS["penny_take_profit"] = True
        try:
            trader = self._build_trader(ClientStub())
            effective_tp_pct = trader._effective_tp_pct(100.0, 1.0, {"tp_pct": 0.75})
            self.assertAlmostEqual(effective_tp_pct, 0.01)
        finally:
            CFD_FLAGS["penny_take_profit"] = old_flag

    def test_tick_skips_failed_top_candidate_and_moves_to_next(self):
        trader = self._build_trader(ClientStub())
        trader._last_scan = 0.0
        trader._last_monitor = time.time()
        trader._sync_positions_from_exchange = lambda force=False: None
        trader._refresh_prices = lambda: None
        trader._monitor_positions = lambda: []
        trader._quad_gate = lambda: True
        trader.status_lines = lambda: []
        trader._find_best_opportunity = lambda: ("SILVER", {"class": "commodity", "size": 1}, {"price": 10, "ask": 10, "bid": 9.9})
        trader._ranked_opportunities = lambda: [
            ("SILVER", {"class": "commodity", "size": 1}, {"price": 10, "ask": 10, "bid": 9.9}),
            ("GOLD", {"class": "commodity", "size": 1}, {"price": 10, "ask": 10, "bid": 9.9}),
        ]
        trader._capital_preflight = lambda symbol, size, ticker, cfg=None: {
            "ok": symbol == "GOLD",
            "reason": "rejected by preflight" if symbol == "SILVER" else "ok",
            "market_status": "TRADEABLE",
            "minimum_deal_size": 1.0,
            "available_balance": 54.34,
        }
        opened = []
        trader._create_shadow = lambda symbol, cfg, ticker: opened.append(symbol) or object()

        trader.tick()

        self.assertEqual(opened, ["GOLD"])
        self.assertIn("rejected by preflight", trader._latest_order_error)

    def test_tick_rescans_immediately_after_close_without_waiting_for_scan_interval(self):
        trader = self._build_trader(ClientStub())
        trader.positions = []
        trader._last_scan = time.time()
        trader._last_monitor = 0.0
        trader._sync_positions_from_exchange = lambda force=False: None
        trader._refresh_prices = lambda: None
        trader._update_position_prices = lambda: None
        trader._monitor_positions = lambda: [{"symbol": "SILVER", "pnl_gbp": 0.12}]
        trader._quad_gate = lambda: True
        trader.status_lines = lambda: []
        trader._find_best_opportunity = lambda: ("GOLD", {"class": "commodity", "size": 1}, {"price": 10, "ask": 10, "bid": 9.9})
        trader._ranked_opportunities = lambda: [
            ("GOLD", {"class": "commodity", "size": 1}, {"price": 10, "ask": 10, "bid": 9.9}),
        ]
        trader._capital_preflight = lambda symbol, size, ticker, cfg=None: {
            "ok": True,
            "reason": "ok",
            "market_status": "TRADEABLE",
            "minimum_deal_size": 1.0,
            "available_balance": 54.34,
        }
        opened = []
        trader._create_shadow = lambda symbol, cfg, ticker: opened.append(symbol) or object()

        closed = trader.tick()

        self.assertEqual(len(closed), 1)
        self.assertEqual(opened, ["GOLD"])

    def test_ranked_opportunities_skips_direction_that_is_already_open(self):
        trader = self._build_trader(ClientStub())
        trader.positions = [
            CFDPosition(
                symbol="SILVER",
                deal_id="DBUY",
                epic="CS.D.SILVER.CFD.IP",
                direction="BUY",
                size=1,
                entry_price=7282.6,
                tp_price=7337.2,
                sl_price=7249.8,
                asset_class="commodity",
                current_price=7282.6,
            )
        ]
        trader._latest_candidate_snapshot = [
            {"symbol": "SILVER", "direction": "BUY", "score": 3.0},
            {"symbol": "GOLD", "direction": "BUY", "score": 2.0},
            {"symbol": "SILVER", "direction": "SELL", "score": 1.8},
        ]
        trader._get_price = lambda symbol: {"price": 10, "bid": 9.9, "ask": 10.1}

        ranked = trader._ranked_opportunities()

        self.assertEqual([(sym, cfg["direction"]) for sym, cfg, _ in ranked], [("SILVER", "SELL")])

    def test_tick_can_open_one_buy_and_one_sell_in_same_cycle(self):
        trader = self._build_trader(ClientStub())
        trader.positions = []
        trader._last_scan = 0.0
        trader._last_monitor = time.time()
        trader._sync_positions_from_exchange = lambda force=False: None
        trader._refresh_prices = lambda: None
        trader._monitor_positions = lambda: []
        trader._quad_gate = lambda: True
        trader.status_lines = lambda: []
        trader._find_best_opportunity = lambda: ("SILVER", {"class": "commodity", "size": 1, "direction": "BUY"}, {"price": 10, "ask": 10, "bid": 9.9})
        trader._ranked_opportunities = lambda: [
            ("SILVER", {"class": "commodity", "size": 1, "direction": "BUY"}, {"price": 10, "ask": 10, "bid": 9.9}),
            ("GOLD", {"class": "commodity", "size": 1, "direction": "SELL"}, {"price": 10, "ask": 10.1, "bid": 10}),
            ("TSLA", {"class": "stock", "size": 1, "direction": "BUY"}, {"price": 10, "ask": 10, "bid": 9.9}),
        ]
        trader._capital_preflight = lambda symbol, size, ticker, cfg=None: {
            "ok": True,
            "reason": "ok",
            "market_status": "TRADEABLE",
            "minimum_deal_size": 1.0,
            "available_balance": 54.34,
        }

        opened = []
        def _shadow(symbol, cfg, ticker):
            opened.append((symbol, cfg["direction"]))
            trader.positions.append(
                CFDPosition(
                    symbol=symbol,
                    deal_id=f"D-{symbol}",
                    epic=f"EPIC-{symbol}",
                    direction=cfg["direction"],
                    size=1,
                    entry_price=10,
                    tp_price=11 if cfg["direction"] == "BUY" else 9,
                    sl_price=9 if cfg["direction"] == "BUY" else 11,
                    asset_class=cfg["class"],
                    current_price=10,
                )
            )
            return object()
        trader._create_shadow = _shadow

        trader.tick()

        self.assertEqual(opened, [("SILVER", "BUY"), ("GOLD", "SELL")])

    def test_build_swarm_snapshot_prefers_consensus_leader(self):
        trader = self._build_trader(ClientStub())

        snapshot = trader._build_swarm_snapshot([
            {
                "symbol": "SILVER",
                "direction": "BUY",
                "score": 2.4,
                "change_pct": 1.8,
                "expected_net_profit": 0.14,
                "spread_pct": 0.03,
                "eta_to_target": 0.2,
                "brain_coherence": 0.7,
            },
            {
                "symbol": "GOLD",
                "direction": "SELL",
                "score": 1.8,
                "change_pct": -2.5,
                "expected_net_profit": 0.05,
                "spread_pct": 0.06,
                "eta_to_target": 0.5,
                "brain_coherence": 0.5,
            },
        ])

        self.assertEqual(snapshot["leader"]["symbol"], "SILVER")
        self.assertEqual(snapshot["leader"]["direction"], "BUY")
        self.assertGreaterEqual(snapshot["leader"]["votes"], 3)

    def test_ranked_opportunities_uses_swarm_order_when_available(self):
        trader = self._build_trader(ClientStub())
        trader._latest_candidate_snapshot = [
            {"symbol": "SILVER", "direction": "BUY", "score": 1.5},
            {"symbol": "GOLD", "direction": "SELL", "score": 2.2},
        ]
        trader._swarm_snapshot = {
            "enabled": True,
            "leader": {"symbol": "SILVER", "direction": "BUY", "swarm_score": 8.0, "votes": 3},
            "votes": [],
            "ranked": [
                {"symbol": "SILVER", "direction": "BUY", "swarm_score": 8.0},
                {"symbol": "GOLD", "direction": "SELL", "swarm_score": 5.0},
            ],
        }
        trader._get_price = lambda symbol: {"price": 10, "bid": 9.9, "ask": 10.1}

        ranked = trader._ranked_opportunities()

        self.assertEqual([(sym, cfg["direction"]) for sym, cfg, _ in ranked], [("SILVER", "BUY"), ("GOLD", "SELL")])

    def test_apply_intelligence_overlays_can_block_candidate_via_orchestrator(self):
        class OrchestratorStub:
            def gate_pre_trade(self, symbol, side):
                if symbol == "SILVER":
                    return False, "confidence_too_low", {}
                return True, "ok", {}

        trader = self._build_trader(ClientStub())
        trader.orchestrator = OrchestratorStub()
        trader.timeline_oracle = None
        trader.harmonic_fusion = None
        scored = [
            {"symbol": "SILVER", "direction": "BUY", "score": 2.0, "price": 100.0, "change_pct": 1.5},
            {"symbol": "GOLD", "direction": "SELL", "score": 1.5, "price": 100.0, "change_pct": -1.2},
        ]

        trader._apply_intelligence_overlays(scored)

        self.assertEqual(scored[0]["score"], 0.0)
        self.assertIn("orchestrator_gate", scored[0]["intel_reason"])
        self.assertTrue(scored[1]["score"] > 0.0)

    def test_can_open_candidate_skips_symbol_on_active_rejection_cooldown(self):
        trader = self._build_trader(ClientStub())

        trader._record_rejection("SILVER", "BUY", "preflight_failed")

        self.assertFalse(trader._can_open_candidate("SILVER", "BUY"))
        self.assertTrue(trader._can_open_candidate("SILVER", "SELL"))

    def test_build_lane_snapshot_prefers_validated_shadow_as_next_in_line(self):
        trader = self._build_trader(ClientStub())
        trader.positions = [
            CFDPosition(
                symbol="SILVER",
                deal_id="DBUY",
                epic="EPIC-SILVER",
                direction="BUY",
                size=1,
                entry_price=10,
                tp_price=11,
                sl_price=9,
                asset_class="commodity",
                current_price=10,
            )
        ]
        validated_sell = CFDShadowTrade(
            symbol="GOLD",
            direction="SELL",
            asset_class="commodity",
            size=1,
            entry_price=10,
            target_move_pct=0.1,
            score=2.0,
        )
        validated_sell.validated = True
        queued_buy = CFDShadowTrade(
            symbol="TSLA",
            direction="BUY",
            asset_class="stock",
            size=1,
            entry_price=10,
            target_move_pct=0.1,
            score=1.0,
        )
        trader.shadow_trades = [queued_buy, validated_sell]

        lanes = trader._build_lane_snapshot()

        self.assertEqual(lanes["BUY"]["position_symbol"], "SILVER")
        self.assertEqual(lanes["SELL"]["validated_shadow_symbol"], "GOLD")
        self.assertEqual(lanes["SELL"]["next_action"], "promote_validated_shadow")

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
        trader = self._build_trader(ClientStub(
            open_result={"dealReference": "REF-DELAY"},
            confirm_result={"dealId": "DDELAY", "level": 7282.6},
        ))
        trader.client._position_batches = [[], [], [live_position]]

        result = trader._open_position(
            "SILVER",
            {"class": "commodity", "size": 1, "tp_pct": 0.75, "sl_pct": 0.45},
            {"price": 7282.6, "ask": 7282.6, "epic": "CS.D.SILVER.CFD.IP"},
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.deal_id, "DDELAY")

    def test_open_position_requires_exchange_validation(self):
        trader = self._build_trader(ClientStub(
            positions=[],
            open_result={"dealReference": "REF-NO-LIVE"},
            confirm_result={"dealId": "D-NO-LIVE", "level": 7282.6},
        ))

        result = trader._open_position(
            "SILVER",
            {"class": "commodity", "size": 1, "tp_pct": 0.75, "sl_pct": 0.45},
            {"price": 7282.6, "ask": 7282.6, "epic": "CS.D.SILVER.CFD.IP"},
        )

        self.assertIsNone(result)
        self.assertEqual(trader.positions, [])
        self.assertEqual(trader.stats["trades_opened"], 0.0)

    def test_open_position_stops_immediately_on_capital_reject_reason(self):
        trader = self._build_trader(ClientStub(
            positions=[],
            open_result={"dealReference": "REF-REJECT"},
            confirm_result={
                "dealId": "D-REJECT",
                "dealStatus": "REJECTED",
                "rejectReason": "RISK_CHECK",
                "status": "DELETED",
            },
        ))

        result = trader._open_position(
            "SILVER",
            {"class": "commodity", "size": 1, "tp_pct": 0.75, "sl_pct": 0.45},
            {"price": 7282.6, "ask": 7282.6, "epic": "CS.D.SILVER.CFD.IP"},
        )

        self.assertIsNone(result)
        self.assertIn("RISK_CHECK", trader._latest_order_error)

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
        trader._dtp_trackers = {}
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
        trader = self._build_trader(ClientStub(
            positions=[live_position],
            open_result={"dealReference": "REF1"},
            confirm_result={"dealId": "DOPEN", "level": 7282.6},
        ))

        result = trader._open_position(
            "SILVER",
            {"class": "commodity", "size": 1, "tp_pct": 0.75, "sl_pct": 0.45},
            {"price": 7282.6, "ask": 7282.6, "epic": "CS.D.SILVER.CFD.IP"},
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.deal_id, "DOPEN")
        self.assertEqual(len(trader.positions), 1)
        self.assertEqual(trader.stats["trades_opened"], 1.0)

    def test_open_position_accepts_verified_live_sell_deal(self):
        live_position = {
            "position": {
                "dealId": "DSELL",
                "direction": "SELL",
                "size": 1,
                "level": 7249.8,
            },
            "market": {
                "epic": "CS.D.SILVER.CFD.IP",
                "symbol": "SILVER",
                "bid": 7249.8,
                "offer": 7251.8,
                "instrumentType": "COMMODITY",
            },
        }
        client = ClientStub(
            positions=[live_position],
            open_result={"dealReference": "REFSELL"},
            confirm_result={"dealId": "DSELL", "level": 7249.8},
        )
        trader = self._build_trader(client)

        result = trader._open_position(
            "SILVER",
            {"class": "commodity", "size": 1, "tp_pct": 0.75, "sl_pct": 0.45, "direction": "SELL"},
            {"price": 7250.8, "ask": 7251.8, "bid": 7249.8, "epic": "CS.D.SILVER.CFD.IP"},
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.direction, "SELL")
        self.assertLess(result.tp_price, result.entry_price)
        self.assertGreater(result.sl_price, result.entry_price)
        self.assertEqual(client.order_calls[-1], ("SILVER", "SELL", 1))

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
        trader._dtp_trackers = {}

        closed = trader._monitor_positions()

        self.assertEqual(closed, [])
        self.assertEqual(len(trader.positions), 1)
        self.assertEqual(trader.positions[0].deal_id, "D2")

    def test_monitor_profit_only_mode_does_not_close_losing_position(self):
        old_flag = CFD_FLAGS["profit_only_closes"]
        CFD_FLAGS["profit_only_closes"] = True
        try:
            trader = CapitalCFDTrader.__new__(CapitalCFDTrader)
            trader.client = ClientStub(close_result={"success": True})
            trader.positions = [
                CFDPosition(
                    symbol="SILVER",
                    deal_id="D3",
                    epic="CS.D.SILVER.CFD.IP",
                    direction="BUY",
                    size=1,
                    entry_price=7282.6,
                    tp_price=7337.2,
                    sl_price=7249.8,
                    asset_class="commodity",
                    current_price=7240.0,
                )
            ]
            trader._recent_closed_trades = []
            trader._latest_monitor_line = ""
            trader._dtp_trackers = {}

            closed = trader._monitor_positions()

            self.assertEqual(closed, [])
            self.assertEqual(len(trader.positions), 1)
            self.assertIn("mode=profit_only", trader._latest_monitor_line)
        finally:
            CFD_FLAGS["profit_only_closes"] = old_flag

    def test_monitor_profit_only_mode_closes_profitable_position(self):
        old_flag = CFD_FLAGS["profit_only_closes"]
        CFD_FLAGS["profit_only_closes"] = True
        try:
            trader = CapitalCFDTrader.__new__(CapitalCFDTrader)
            trader.client = ClientStub(close_result={"success": True})
            trader.positions = [
                CFDPosition(
                    symbol="SILVER",
                    deal_id="D4",
                    epic="CS.D.SILVER.CFD.IP",
                    direction="BUY",
                    size=1,
                    entry_price=7282.6,
                    tp_price=7330.0,
                    sl_price=7249.8,
                    asset_class="commodity",
                    current_price=7335.0,
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
            trader._dtp_trackers = {}

            closed = trader._monitor_positions()

            self.assertEqual(len(closed), 1)
            self.assertEqual(trader.positions, [])
            self.assertGreater(closed[0]["net_pnl"], 0.0)
        finally:
            CFD_FLAGS["profit_only_closes"] = old_flag

    def test_score_symbol_uses_central_beat_alignment(self):
        trader = self._build_trader(ClientStub())
        trader._effective_tp_pct = lambda price, size, cfg: 0.5
        trader._central_beat_symbols = {
            "SILVER": {"side": "BUY", "support_count": 3, "strength": 0.9},
        }
        trader._central_beat_regime = {"bias": "BUY", "confidence": 0.8}
        ticker = {"price": 100.0, "bid": 99.9, "ask": 100.1, "change_pct": 0.4}
        cfg = {"max_spread_pct": 0.01, "momentum_threshold": 0.1, "size": 1.0}
        boosted_score, direction = trader._score_symbol("SILVER", cfg, ticker)

        trader._central_beat_symbols = {}
        trader._central_beat_regime = {}
        plain_score, _ = trader._score_symbol("SILVER", cfg, ticker)

        self.assertEqual(direction, "BUY")
        self.assertGreater(boosted_score, plain_score)

    def test_fill_live_monitoring_slots_opens_one_buy_and_one_sell(self):
        trader = self._build_trader(ClientStub())
        trader._last_slot_fill_attempt = {"BUY": 0.0, "SELL": 0.0}
        trader._capital_preflight = lambda symbol, size, ticker, cfg=None: {
            "ok": False,
            "reason": "expected net profit -0.0010 does not clear costs 0.0020",
            "price": ticker.get("price"),
            "bid": ticker.get("bid"),
            "ask": ticker.get("ask"),
        }
        opened = []
        class Opened:
            def __init__(self, deal_id):
                self.deal_id = deal_id
        trader._open_position = lambda symbol, cfg, ticker: opened.append((symbol, cfg["direction"])) or Opened(f"{symbol}-{cfg['direction']}")
        trader._latest_candidate_snapshot = [
            {"symbol": "SILVER", "direction": "BUY", "score": 0.0},
            {"symbol": "GOLD", "direction": "SELL", "score": 0.0},
        ]
        trader._prices = {
            "SILVER": {"price": 100.0, "bid": 99.9, "ask": 100.1},
            "GOLD": {"price": 200.0, "bid": 199.9, "ask": 200.1},
        }

        result = trader._fill_live_monitoring_slots(100.0)

        self.assertTrue(result)
        self.assertEqual(opened, [("SILVER", "BUY"), ("GOLD", "SELL")])


if __name__ == "__main__":
    unittest.main(verbosity=2)
