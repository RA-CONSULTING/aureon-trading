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
        trader._latest_order_error = ""
        trader._latest_order_trace_path = ""
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
