#!/usr/bin/env python3
"""
Alpaca trader that mirrors the Capital CFD trader lifecycle for stock trading.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

try:
    from aureon.exchanges.alpaca_client import AlpacaClient
except ImportError:
    AlpacaClient = None  # type: ignore

try:
    from aureon.intelligence.aureon_brain import AureonBrain
except Exception:
    AureonBrain = None  # type: ignore

try:
    from aureon.intelligence.aureon_unified_intelligence_registry import get_unified_puller
    HAS_UNIFIED_REGISTRY = True
except Exception:
    get_unified_puller = None  # type: ignore
    HAS_UNIFIED_REGISTRY = False

try:
    from aureon.intelligence.aureon_unified_decision_engine import (
        UnifiedDecisionEngine,
        SignalInput,
        CoordinationInput,
        DecisionType,
        DecisionReason,
    )
    HAS_UNIFIED_DECISION = True
except Exception:
    UnifiedDecisionEngine = None  # type: ignore
    SignalInput = None  # type: ignore
    CoordinationInput = None  # type: ignore
    DecisionType = None  # type: ignore
    DecisionReason = None  # type: ignore
    HAS_UNIFIED_DECISION = False

try:
    from aureon.autonomous.autonomous_trading_orchestrator import AutonomousOrchestrator
    HAS_ALPACA_ORCHESTRATOR = True
except Exception:
    AutonomousOrchestrator = None  # type: ignore
    HAS_ALPACA_ORCHESTRATOR = False

try:
    from aureon.intelligence.aureon_timeline_oracle import get_timeline_oracle
    HAS_TIMELINE_ORACLE = True
except Exception:
    get_timeline_oracle = None  # type: ignore
    HAS_TIMELINE_ORACLE = False

try:
    from aureon.harmonic.aureon_harmonic_fusion import HarmonicWaveFusion
    HAS_HARMONIC_FUSION = True
except Exception:
    HarmonicWaveFusion = None  # type: ignore
    HAS_HARMONIC_FUSION = False

try:
    from aureon.core.aureon_thought_bus import Thought, get_thought_bus
    HAS_THOUGHT_BUS = True
except Exception:
    Thought = None  # type: ignore
    get_thought_bus = None  # type: ignore
    HAS_THOUGHT_BUS = False


logger = logging.getLogger(__name__)

ALPACA_CAPITAL_UNIVERSE: Dict[str, Dict[str, float]] = {
    "AAPL": {"tp_pct": 0.80, "sl_pct": 0.45, "size": 1, "max_spread_pct": 0.20, "momentum_threshold": 0.20},
    "TSLA": {"tp_pct": 1.00, "sl_pct": 0.60, "size": 1, "max_spread_pct": 0.30, "momentum_threshold": 0.30},
    "NVDA": {"tp_pct": 0.90, "sl_pct": 0.55, "size": 1, "max_spread_pct": 0.25, "momentum_threshold": 0.25},
    "AMZN": {"tp_pct": 0.80, "sl_pct": 0.45, "size": 1, "max_spread_pct": 0.20, "momentum_threshold": 0.20},
    "MSFT": {"tp_pct": 0.75, "sl_pct": 0.40, "size": 1, "max_spread_pct": 0.15, "momentum_threshold": 0.18},
    "META": {"tp_pct": 0.85, "sl_pct": 0.50, "size": 1, "max_spread_pct": 0.20, "momentum_threshold": 0.22},
    "AMD": {"tp_pct": 0.90, "sl_pct": 0.55, "size": 1, "max_spread_pct": 0.25, "momentum_threshold": 0.25},
    "SPY": {"tp_pct": 0.35, "sl_pct": 0.20, "size": 1, "max_spread_pct": 0.08, "momentum_threshold": 0.10},
    "QQQ": {"tp_pct": 0.45, "sl_pct": 0.25, "size": 1, "max_spread_pct": 0.10, "momentum_threshold": 0.12},
}
ALPACA_UNIVERSE_LIMIT = max(25, int(float(os.getenv("ALPACA_UNIVERSE_LIMIT", "250") or 250)))
ALPACA_SCAN_WINDOW = max(10, int(float(os.getenv("ALPACA_SCAN_WINDOW", "40") or 40)))
ALPACA_MIN_PRICE = max(0.1, float(os.getenv("ALPACA_MIN_PRICE", "2.0") or 2.0))
ALPACA_MIN_DOLLAR_VOLUME = max(10000.0, float(os.getenv("ALPACA_MIN_DOLLAR_VOLUME", "250000") or 250000))
ALPACA_INTEL_TOP_N = max(1, int(float(os.getenv("ALPACA_INTEL_TOP_N", "5") or 5)))

ALPACA_SELF_CONFIDENCE_ENABLED = os.getenv("ALPACA_SELF_CONFIDENCE_ENABLED", "1").strip().lower() not in {"0", "false", "no", "off"}
ALPACA_SELF_CONFIDENCE_MAX_BOOST = max(0.0, float(os.getenv("ALPACA_SELF_CONFIDENCE_MAX_BOOST", "0.08") or 0.08))
ALPACA_SELF_CONFIDENCE_MIN_VALIDATE_SECS = max(0.5, float(os.getenv("ALPACA_SELF_CONFIDENCE_MIN_VALIDATE_SECS", "2.5") or 2.5))
ALPACA_MIN_TARGET_USD = max(0.01, float(os.getenv("ALPACA_MIN_TARGET_USD", "0.01") or 0.01))

MAX_POSITIONS = 2
SCAN_INTERVAL_SECS = 5.0
MONITOR_INTERVAL_SECS = 2.0


@dataclass
class AlpacaShadowTrade:
    symbol: str
    direction: str
    size: float
    entry_price: float
    target_move_pct: float
    score: float
    opened_at: float = field(default_factory=time.time)
    current_price: float = 0.0
    peak_move_pct: float = 0.0
    validated: bool = False
    validation_time: float = 0.0

    @property
    def age_secs(self) -> float:
        return time.time() - self.opened_at

    @property
    def current_move_pct(self) -> float:
        price = self.current_price if self.current_price > 0 else self.entry_price
        if self.entry_price <= 0 or price <= 0:
            return 0.0
        if self.direction == "BUY":
            return ((price - self.entry_price) / self.entry_price) * 100.0
        return ((self.entry_price - price) / self.entry_price) * 100.0

    def update(self, price: float, validation_window_secs: float) -> None:
        if price <= 0:
            return
        self.current_price = price
        move_pct = self.current_move_pct
        self.peak_move_pct = max(self.peak_move_pct, move_pct)
        if not self.validated and move_pct >= self.target_move_pct and self.age_secs >= max(0.0, float(validation_window_secs or 0.0)):
            self.validated = True
            self.validation_time = time.time()


@dataclass
class AlpacaMomentumPosition:
    symbol: str
    order_id: str
    direction: str
    qty: float
    entry_price: float
    tp_price: float
    sl_price: float
    opened_at: float = field(default_factory=time.time)
    current_price: float = 0.0

    @property
    def age_secs(self) -> float:
        return time.time() - self.opened_at

    @property
    def pnl_pct(self) -> float:
        price = self.current_price if self.current_price > 0 else self.entry_price
        if self.entry_price <= 0 or price <= 0:
            return 0.0
        if self.direction == "BUY":
            return ((price - self.entry_price) / self.entry_price) * 100.0
        return ((self.entry_price - price) / self.entry_price) * 100.0

    def one_line(self) -> str:
        return (
            f"    LIVE   {self.direction:4} {self.symbol:5} [stock] "
            f"entry:{self.entry_price:.4f} now:{self.current_price or self.entry_price:.4f} "
            f"pnl:{self.pnl_pct:+.3f}% age:{self.age_secs/60.0:.1f}m"
        )


class AlpacaCapitalStyleTrader:
    SHADOW_MAX_ACTIVE = 4
    SHADOW_MIN_VALIDATE = 6.0
    SHADOW_MAX_AGE = 20.0 * 60.0

    def __init__(self) -> None:
        self.client: Optional[AlpacaClient] = AlpacaClient() if AlpacaClient is not None else None
        self.init_error = ""
        if self.client is None or not getattr(self.client, "is_authenticated", False):
            self.init_error = "alpaca_client_unavailable_or_not_authenticated"
            self.client = None

        self._universe_snapshot: Dict[str, Any] = {}
        self.positions: List[AlpacaMomentumPosition] = []
        self.shadow_trades: List[AlpacaShadowTrade] = []
        self.universe: Dict[str, Dict[str, float]] = self._build_universe()
        self._prices: Dict[str, Dict[str, float]] = {}
        self._latest_candidate_snapshot: List[Dict[str, Any]] = []
        self._latest_target_snapshot: Dict[str, Any] = {}
        self._latest_status_lines: List[str] = []
        self._latest_order_error = ""
        self._latest_monitor_line = ""
        self._recent_closed_trades: List[Dict[str, Any]] = []
        self._lane_snapshot: Dict[str, Any] = {}
        self._registry_snapshot: Dict[str, Any] = {}
        self._decision_snapshot: Dict[str, Any] = {}
        self._orchestrator_snapshot: Dict[str, Any] = {}
        self._thought_bus_snapshot: Dict[str, Any] = {}
        self._cognition_snapshot: Dict[str, Any] = {}
        self._swarm_snapshot: Dict[str, Any] = {
            "enabled": True,
            "leader": {},
            "votes": [],
            "ranked": [],
        }
        self._timeline_snapshot: Dict[str, Any] = {}
        self._fusion_snapshot: Dict[str, Any] = {}
        self._probability_snapshot: Dict[str, Any] = {}
        self._probability_snapshot_at: float = 0.0
        self._self_confidence_snapshot: Dict[str, Any] = {}
        self._scan_window_snapshot: Dict[str, Any] = {}
        self._shadow_validated_count = 0
        self._shadow_failed_count = 0
        self._shortable_cache: Dict[str, bool] = {}
        self._signal_brain = AureonBrain() if AureonBrain is not None else None
        self.unified_registry = get_unified_puller() if HAS_UNIFIED_REGISTRY and get_unified_puller is not None else None
        self.unified_decision_engine = UnifiedDecisionEngine() if HAS_UNIFIED_DECISION and UnifiedDecisionEngine is not None else None
        self.orchestrator = AutonomousOrchestrator(self) if HAS_ALPACA_ORCHESTRATOR and AutonomousOrchestrator is not None else None
        self.timeline_oracle = get_timeline_oracle() if HAS_TIMELINE_ORACLE and get_timeline_oracle is not None else None
        self.harmonic_fusion = HarmonicWaveFusion() if HAS_HARMONIC_FUSION and HarmonicWaveFusion is not None else None
        self.thought_bus = (
            get_thought_bus(os.path.join(os.path.dirname(__file__), "..", "..", "state", "alpaca_thoughts.jsonl"))
            if HAS_THOUGHT_BUS and get_thought_bus is not None else None
        )
        self._harmonic_wiring_audit: Dict[str, Any] = self._build_harmonic_wiring_audit()
        self._harmonic_wiring_audit_at: float = time.time()
        self.start_time = time.time()
        self._last_scan = 0.0
        self._last_monitor = 0.0
        self._scan_cursor = 0
        self.stats = {
            "trades_opened": 0.0,
            "trades_closed": 0.0,
            "winning_trades": 0.0,
            "losing_trades": 0.0,
            "total_pnl_usd": 0.0,
        }
        account = self.get_account_snapshot()
        self.starting_equity_usd = float(account.get("equity_usd", 0.0) or 0.0)

    @property
    def enabled(self) -> bool:
        return self.client is not None

    def _default_symbol_config(self, symbol: str) -> Dict[str, float]:
        seed = sum(ord(ch) for ch in symbol.upper())
        if seed % 7 == 0:
            return {"tp_pct": 1.00, "sl_pct": 0.60, "size": 1, "max_spread_pct": 0.30, "momentum_threshold": 0.30}
        if seed % 5 == 0:
            return {"tp_pct": 0.90, "sl_pct": 0.55, "size": 1, "max_spread_pct": 0.25, "momentum_threshold": 0.25}
        if seed % 3 == 0:
            return {"tp_pct": 0.80, "sl_pct": 0.45, "size": 1, "max_spread_pct": 0.20, "momentum_threshold": 0.20}
        return {"tp_pct": 0.70, "sl_pct": 0.40, "size": 1, "max_spread_pct": 0.18, "momentum_threshold": 0.18}

    def _is_symbol_quality_ok(self, symbol: str) -> bool:
        sym = (symbol or "").upper().strip()
        if not sym:
            return False
        bad_suffixes = ("W", "WS", "WT", "U", "RT", "R", "PRA", "PRB", "PRC", "PRD", "PRE", "PRF", "PRG")
        if "." in sym:
            return False
        if "-" in sym:
            return False
        if len(sym) > 5 and sym.endswith(bad_suffixes):
            return False
        return sym.isalnum()

    def _build_universe(self) -> Dict[str, Dict[str, float]]:
        if not self.client:
            self._universe_snapshot = {
                "mode": "fallback",
                "reason": "client_unavailable",
                "size": len(ALPACA_CAPITAL_UNIVERSE),
                "limit": ALPACA_UNIVERSE_LIMIT,
            }
            return dict(ALPACA_CAPITAL_UNIVERSE)
        try:
            symbols = list(dict.fromkeys(self.client.get_tradable_stock_symbols() or []))
        except Exception:
            symbols = []
        if not symbols:
            self._universe_snapshot = {
                "mode": "fallback",
                "reason": "tradable_stock_discovery_empty",
                "size": len(ALPACA_CAPITAL_UNIVERSE),
                "limit": ALPACA_UNIVERSE_LIMIT,
            }
            return dict(ALPACA_CAPITAL_UNIVERSE)
        preferred = list(ALPACA_CAPITAL_UNIVERSE.keys())
        extras = [sym for sym in symbols if sym not in ALPACA_CAPITAL_UNIVERSE and self._is_symbol_quality_ok(sym)]
        selected = (preferred + extras)[:ALPACA_UNIVERSE_LIMIT]
        universe: Dict[str, Dict[str, float]] = {}
        for sym in selected:
            universe[sym] = dict(ALPACA_CAPITAL_UNIVERSE.get(sym) or self._default_symbol_config(sym))
        self._universe_snapshot = {
            "mode": "live",
            "reason": "tradable_stock_discovery_ok",
            "size": len(universe),
            "limit": ALPACA_UNIVERSE_LIMIT,
            "discovered_symbols": len(symbols),
        }
        return universe

    def _direction_counts(self) -> Dict[str, int]:
        counts = {"BUY": 0, "SELL": 0}
        for pos in self.positions:
            direction = str(pos.direction or "").upper()
            counts[direction] = counts.get(direction, 0) + 1
        return counts

    def _is_shortable(self, symbol: str) -> bool:
        cached = self._shortable_cache.get(symbol.upper())
        if cached is not None:
            return cached
        allowed = bool(self.client and self.client.is_shortable(symbol))
        self._shortable_cache[symbol.upper()] = allowed
        return allowed

    def _refresh_registry_snapshot(self) -> None:
        snapshot: Dict[str, Any] = {}
        if self.unified_registry is not None:
            try:
                snapshot["categories"] = self.unified_registry.get_category_summary()
                snapshot["chain_flow"] = self.unified_registry.get_chain_flow()
            except Exception as e:
                snapshot["error"] = str(e)
        if not snapshot:
            snapshot = {
                "categories": {
                    "stocks": len(self.universe),
                    "open_positions": len(self.positions),
                    "shadow_positions": len(self.shadow_trades),
                },
                "universe_size": len(self.universe),
            }
        self._registry_snapshot = snapshot

    def _build_swarm_snapshot(self, scored: List[Dict[str, Any]]) -> Dict[str, Any]:
        ranked: List[Dict[str, Any]] = []
        for item in scored[:7]:
            votes = max(0, min(5, int(round(float(item.get("score", 0.0) or 0.0)))))
            ranked.append({
                "symbol": str(item.get("symbol") or ""),
                "direction": str(item.get("direction") or "").upper(),
                "votes": votes,
                "swarm_score": float(item.get("score", 0.0) or 0.0),
            })
        leader = dict(ranked[0]) if ranked else {}
        return {
            "enabled": True,
            "leader": leader,
            "votes": ranked,
            "ranked": ranked,
        }

    def _update_coordination_snapshots(self) -> None:
        target = dict(self._latest_target_snapshot or {})
        symbol = str(target.get("symbol") or "")
        side = str(target.get("direction") or "").upper()
        score = float(target.get("score", 0.0) or 0.0)
        net = float(target.get("expected_net_profit", 0.0) or 0.0)
        approved = bool(symbol and side in {"BUY", "SELL"} and score > 0 and net > 0)
        if symbol:
            self._feed_unified_decision_engine(symbol, side, score=max(0.0, min(1.0, score / 3.0)), metadata=target)
            self._orchestrator_snapshot = self._orchestrator_pretrade_gate(symbol, side)
            if not self._decision_snapshot:
                self._decision_snapshot = {
                    "symbol": symbol,
                    "side": side,
                    "decision": {
                        "type": "execute" if approved else "hold",
                        "confidence": max(0.0, min(1.0, score / 3.0)),
                    },
                }
        else:
            self._decision_snapshot = {}
            self._orchestrator_snapshot = {}

    def _refresh_prices(self) -> None:
        if not self.client:
            return
        symbols = list(self.universe.keys())
        if not symbols:
            self._scan_window_snapshot = {"start": 0, "end": 0, "size": 0, "total": 0}
            return
        total = len(symbols)
        window_size = min(ALPACA_SCAN_WINDOW, total)
        start = self._scan_cursor % total
        window = symbols[start:start + window_size]
        if len(window) < window_size:
            window += symbols[:window_size - len(window)]
        self._scan_cursor = (start + window_size) % total
        self._scan_window_snapshot = {
            "start": start,
            "end": (start + len(window) - 1) % total if window else start,
            "size": len(window),
            "total": total,
            "symbols": list(window[:5]),
        }
        snapshots = self.client.get_stock_snapshots(window) or {}
        for symbol in window:
            snap = snapshots.get(symbol) or {}
            latest_quote = snap.get("latestQuote", {}) or snap.get("latest_quote", {}) or {}
            daily_bar = snap.get("dailyBar", {}) or snap.get("daily_bar", {}) or {}
            prev_bar = snap.get("prevDailyBar", {}) or snap.get("prev_daily_bar", {}) or {}
            minute_bar = snap.get("minuteBar", {}) or snap.get("minute_bar", {}) or {}
            bid = float(latest_quote.get("bp", 0.0) or 0.0)
            ask = float(latest_quote.get("ap", 0.0) or 0.0)
            price = ((bid + ask) / 2.0) if bid > 0 and ask > 0 else float(daily_bar.get("c", 0.0) or minute_bar.get("c", 0.0) or 0.0)
            prev_close = float(prev_bar.get("c", 0.0) or 0.0)
            bar_volume = float(daily_bar.get("v", 0.0) or minute_bar.get("v", 0.0) or 0.0)
            dollar_volume = price * bar_volume
            if price < ALPACA_MIN_PRICE:
                self._prices.pop(symbol, None)
                continue
            if bid > 0 and ask > 0 and ask <= bid:
                self._prices.pop(symbol, None)
                continue
            if dollar_volume < ALPACA_MIN_DOLLAR_VOLUME:
                self._prices.pop(symbol, None)
                continue
            change_pct = ((price - prev_close) / prev_close * 100.0) if price > 0 and prev_close > 0 else 0.0
            self._prices[symbol] = {
                "price": price,
                "bid": bid,
                "ask": ask,
                "change_pct": change_pct,
                "dollar_volume": dollar_volume,
                "bar_volume": bar_volume,
            }

    def _capital_style_cost_profile(self, symbol: str, size: float, price: float, tp_pct: float) -> Dict[str, float]:
        ticker = self._prices.get(symbol, {})
        bid = float(ticker.get("bid", 0.0) or 0.0)
        ask = float(ticker.get("ask", 0.0) or 0.0)
        notional = max(float(size or 0.0) * float(price or 0.0), 0.0)
        expected_gross_profit = notional * (max(float(tp_pct or 0.0), 0.0) / 100.0)
        spread_cost = max(ask - bid, 0.0) * max(float(size or 0.0), 0.0) if bid > 0 and ask > 0 else 0.0
        slippage_cost = notional * 0.0001
        round_trip_cost = spread_cost + slippage_cost
        return {
            "notional": notional,
            "expected_gross_profit": expected_gross_profit,
            "round_trip_cost": round_trip_cost,
            "expected_net_profit": expected_gross_profit - round_trip_cost,
        }

    def _compute_self_confidence(self, candidate: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        snapshot: Dict[str, Any] = {
            "enabled": ALPACA_SELF_CONFIDENCE_ENABLED,
            "score": 0.0,
            "boost_multiplier": 1.0,
            "validation_window_secs": self.SHADOW_MIN_VALIDATE,
            "recent_success_ratio": 0.0,
            "alignment_score": 0.0,
            "rejection_pressure": 0.0,
            "reason": "disabled" if not ALPACA_SELF_CONFIDENCE_ENABLED else "cold_start",
        }
        if not ALPACA_SELF_CONFIDENCE_ENABLED:
            return snapshot

        validated = float(self._shadow_validated_count or 0.0)
        failed = float(self._shadow_failed_count or 0.0)
        completed = validated + failed
        if completed > 0:
            recent_success_ratio = validated / completed
        else:
            opened = float(self.stats.get("trades_opened", 0.0) or 0.0)
            wins = float(self.stats.get("winning_trades", 0.0) or 0.0)
            recent_success_ratio = (wins / opened) if opened > 0 else 0.5

        source = dict(candidate or self._latest_target_snapshot or {})
        alignment_score = max(0.0, min(1.0, abs(float(source.get("change_pct", 0.0) or 0.0)) / 1.5))
        rejection_pressure = 1.0 if self._latest_order_error else 0.0
        raw_score = (recent_success_ratio * 0.5) + (alignment_score * 0.4) + ((1.0 - rejection_pressure) * 0.1)
        score = max(0.0, min(1.0, raw_score))
        boost_multiplier = 1.0 + max(0.0, score - 0.5) * 2.0 * ALPACA_SELF_CONFIDENCE_MAX_BOOST
        validation_window = max(
            ALPACA_SELF_CONFIDENCE_MIN_VALIDATE_SECS,
            float(self.SHADOW_MIN_VALIDATE) - max(0.0, score - 0.55) * (float(self.SHADOW_MIN_VALIDATE) - ALPACA_SELF_CONFIDENCE_MIN_VALIDATE_SECS),
        )
        snapshot.update({
            "score": score,
            "boost_multiplier": boost_multiplier,
            "validation_window_secs": validation_window,
            "recent_success_ratio": recent_success_ratio,
            "alignment_score": alignment_score,
            "rejection_pressure": rejection_pressure,
            "reason": "armed" if score >= 0.55 else "warming_up",
        })
        return snapshot

    def _compute_growth_metrics(self) -> Dict[str, Any]:
        runtime_secs = max(1.0, time.time() - self.start_time)
        runtime_hours = runtime_secs / 3600.0
        pnl = float(self.stats.get("total_pnl_usd", 0.0) or 0.0)
        trades_closed = int(self.stats.get("trades_closed", 0.0) or 0.0)
        wins = int(self.stats.get("winning_trades", 0.0) or 0.0)
        losses = int(self.stats.get("losing_trades", 0.0) or 0.0)
        equity_now = float(self.get_account_snapshot().get("equity_usd", 0.0) or 0.0)
        equity_start = float(self.starting_equity_usd or 0.0)
        equity_growth_pct = ((equity_now - equity_start) / equity_start * 100.0) if equity_start > 0 else 0.0
        pnl_per_hour = pnl / runtime_hours if runtime_hours > 0 else 0.0
        trades_per_hour = trades_closed / runtime_hours if runtime_hours > 0 else 0.0
        avg_pnl = pnl / trades_closed if trades_closed > 0 else 0.0
        recent = list(self._recent_closed_trades or [])[-3:]
        recent_pnl = sum(float(item.get("net_pnl", 0.0) or 0.0) for item in recent)
        recent_avg = recent_pnl / len(recent) if recent else 0.0
        trend = "steady"
        if recent_avg > avg_pnl + 1e-9:
            trend = "accelerating"
        elif recent_avg < avg_pnl - 1e-9:
            trend = "cooling"
        return {
            "runtime_hours": runtime_hours,
            "equity_growth_pct": equity_growth_pct,
            "pnl_per_hour_usd": pnl_per_hour,
            "trades_per_hour": trades_per_hour,
            "avg_pnl_per_close_usd": avg_pnl,
            "recent_avg_pnl_usd": recent_avg,
            "recent_total_pnl_usd": recent_pnl,
            "win_rate": (wins / trades_closed) if trades_closed > 0 else 0.0,
            "closed_trades": trades_closed,
            "wins": wins,
            "losses": losses,
            "trend": trend,
        }

    def _refresh_thought_bus_snapshot(self) -> None:
        if self.thought_bus is None:
            self._thought_bus_snapshot = {}
            self._cognition_snapshot = {}
            return
        try:
            market_events = self.thought_bus.recall("market.", limit=8)
            decision_events = self.thought_bus.recall("decisions.", limit=8)
            cognition_events = self.thought_bus.recall("brain.", limit=8)
            queen_events = self.thought_bus.recall("queen.", limit=8)
            self._thought_bus_snapshot = {"market_events": len(market_events), "decision_events": len(decision_events)}
            self._cognition_snapshot = {"cognition_events": len(cognition_events), "queen_events": len(queen_events)}
        except Exception as e:
            self._thought_bus_snapshot = {"error": str(e)}
            self._cognition_snapshot = {"error": str(e)}

    def _publish_market_snapshot_to_thought_bus(self) -> None:
        if self.thought_bus is None or Thought is None or not self._latest_candidate_snapshot:
            return
        try:
            market_by_symbol: Dict[str, Dict[str, Any]] = {}
            universe: List[str] = []
            for candidate in self._latest_candidate_snapshot[:7]:
                symbol = str(candidate.get("symbol") or "").upper()
                if not symbol:
                    continue
                universe.append(symbol)
                market_by_symbol[symbol] = {
                    "momentum": float(candidate.get("change_pct", 0.0) or 0.0),
                    "score": float(candidate.get("score", 0.0) or 0.0),
                    "spread_pct": float(candidate.get("spread_pct", 0.0) or 0.0),
                    "direction": str(candidate.get("direction") or "BUY").upper(),
                }
            self.thought_bus.publish(Thought(
                source="alpaca_capital_style_trader",
                topic="market.snapshot",
                payload={"venue": "alpaca", "universe": universe, "market_by_symbol": market_by_symbol},
                meta={"mode": "alpaca_capital_style"},
            ))
        except Exception as e:
            logger.debug("Alpaca ThoughtBus publish failed: %s", e)

    def _publish_learning_update(self, record: Dict[str, Any]) -> None:
        if self.thought_bus is None or Thought is None:
            return
        learning_update = dict(record.get("learning_update") or {})
        if not learning_update:
            return
        try:
            symbol = str(record.get("symbol") or "").upper()
            payload = {
                "venue": "alpaca",
                "symbol": symbol,
                "direction": str(record.get("direction") or "").upper(),
                "net_pnl_usd": float(record.get("net_pnl", 0.0) or 0.0),
                "reason": str(record.get("reason") or ""),
                "learning_update": learning_update,
            }
            self.thought_bus.publish(Thought(
                source="alpaca_capital_style_trader",
                topic="brain.learning",
                payload=payload,
                meta={"mode": "alpaca_capital_style", "expressive": True},
            ))
            self.thought_bus.publish(Thought(
                source="alpaca_capital_style_trader",
                topic="queen.learning",
                payload={
                    "voice": (
                        f"I learned from {symbol}. "
                        f"Net outcome was {float(record.get('net_pnl', 0.0) or 0.0):+.2f} USD, "
                        f"and my bias is now {float(learning_update.get('symbol_bias', 0.0) or 0.0):+.3f}."
                    ),
                    **payload,
                },
                meta={"mode": "alpaca_capital_style", "expressive": True},
            ))
        except Exception as e:
            logger.debug("Alpaca learning publish failed: %s", e)

    def _feed_unified_decision_engine(self, symbol: str, side: str, score: float = 0.5, metadata: Optional[dict] = None) -> None:
        if self.unified_decision_engine is None or SignalInput is None:
            return
        try:
            direction = "bullish" if str(side).upper() == "BUY" else "bearish"
            self.unified_decision_engine.add_signal(
                SignalInput(
                    source="alpaca_capital_style_trader",
                    symbol=symbol,
                    direction=direction,
                    strength=max(0.0, min(1.0, float(score))),
                    metadata=metadata or {},
                )
            )
            if CoordinationInput is not None:
                self.unified_decision_engine.set_coordination_state(
                    CoordinationInput(
                        orca_ready=True,
                        all_systems_ready=1,
                        total_systems=1,
                        blockers=[],
                    )
                )
            decision = None
            if DecisionType is not None and DecisionReason is not None:
                decision = self.unified_decision_engine.generate_decision(
                    symbol,
                    DecisionType.BUY if str(side).upper() == "BUY" else DecisionType.SELL,
                    DecisionReason.SIGNAL_STRENGTH,
                )
            self._decision_snapshot = {
                "symbol": symbol,
                "side": str(side).upper(),
                "score": float(score),
                "decision": {
                    "type": decision.decision_type.value,
                    "confidence": decision.confidence,
                    "reason": decision.reason.value,
                } if decision else None,
            }
        except Exception as e:
            self._decision_snapshot = {"error": str(e), "symbol": symbol, "side": str(side).upper()}

    def _score_timeline_oracle(self, symbol: str, side: str, price: float, change_pct: float) -> Dict[str, Any]:
        result = {"bonus": 0.0, "action": "hold", "confidence": 0.0, "reason": "timeline_unavailable"}
        if self.timeline_oracle is None:
            return result
        try:
            action, confidence, reason = self.timeline_oracle.get_approved_action(
                symbol=symbol,
                price=price,
                volume=max(abs(change_pct), 0.01),
                change_pct=change_pct,
            )
            action_value = getattr(action, "value", "hold") if action is not None else "hold"
            confidence = float(confidence or 0.0)
            expected = "buy" if str(side).upper() == "BUY" else "sell"
            bonus = (confidence - 0.5) * 2.0
            if action_value == expected:
                bonus += 0.5
            elif action_value not in {"hold", "wait"}:
                bonus -= 0.75
            result.update({
                "bonus": max(-1.5, min(2.0, bonus)),
                "action": action_value,
                "confidence": confidence,
                "reason": str(reason or ""),
            })
        except Exception as e:
            result["error"] = str(e)
        self._timeline_snapshot = {"symbol": symbol, "side": str(side).upper(), **result}
        return result

    def _score_harmonic_fusion(self, symbol: str, side: str) -> Dict[str, Any]:
        result = {"bonus": 0.0, "global_coherence": 0.0, "symbol_coherence": 0.0}
        if self.harmonic_fusion is None:
            return result
        try:
            state = self.harmonic_fusion.get_harmonic_state() or {}
            phase = self.harmonic_fusion.get_symbol_phase(symbol) or {}
            global_coh = float(state.get("global_coherence", 0.0) or 0.0)
            symbol_coh = float(phase.get("coherence", phase.get("amplitude", 0.0)) or 0.0)
            bonus = max(-1.5, min(2.0, (global_coh - 0.5) * 2.0 + (symbol_coh - 0.5) * 2.0))
            result.update({
                "bonus": bonus,
                "global_coherence": global_coh,
                "symbol_coherence": symbol_coh,
            })
        except Exception as e:
            result["error"] = str(e)
        self._fusion_snapshot = {"symbol": symbol, "side": str(side).upper(), **result}
        return result

    def _orchestrator_pretrade_gate(self, symbol: str, side: str) -> Dict[str, Any]:
        result = {"approved": True, "reason": "orchestrator_unavailable", "sizing": {}}
        if self.orchestrator is None:
            return result
        try:
            approved, reason, sizing = self.orchestrator.gate_pre_trade(symbol, str(side).lower())
            result = {"approved": bool(approved), "reason": str(reason or "ok"), "sizing": sizing or {}}
        except Exception as e:
            result = {"approved": True, "reason": f"fail_open:{e}", "sizing": {}}
        return {"symbol": symbol, "side": str(side).upper(), **result}

    def _probability_validation_snapshot(self, force: bool = False) -> Dict[str, Any]:
        now = time.time()
        if not force and self._probability_snapshot and (now - self._probability_snapshot_at) < 30.0:
            return dict(self._probability_snapshot)
        payload = {
            "ok": True,
            "direction_accuracy": 0.0,
            "profit_factor": 0.0,
            "updated": "",
            "reason": "alpaca_fail_open",
        }
        self._probability_snapshot = payload
        self._probability_snapshot_at = now
        return dict(payload)

    def _build_harmonic_wiring_audit(self) -> Dict[str, Any]:
        return {
            "timeline_oracle": self.timeline_oracle is not None,
            "harmonic_fusion": self.harmonic_fusion is not None,
            "unified_registry": self.unified_registry is not None,
            "unified_decision_engine": self.unified_decision_engine is not None,
            "orchestrator": self.orchestrator is not None,
            "thought_bus": self.thought_bus is not None,
        }

    def _apply_intelligence_overlays(self, scored: List[Dict[str, Any]]) -> None:
        ranked = [
            item for item in scored
            if float(item.get("score", 0.0) or 0.0) > 0
        ]
        ranked.sort(key=lambda item: float(item.get("score", 0.0) or 0.0), reverse=True)
        for item in ranked[:ALPACA_INTEL_TOP_N]:
            base_score = float(item.get("score", 0.0) or 0.0)
            if base_score <= 0:
                continue
            symbol = str(item.get("symbol") or "")
            side = str(item.get("direction") or "BUY").upper()
            price = float(item.get("price", 0.0) or 0.0)
            change_pct = float(item.get("change_pct", 0.0) or 0.0)
            timeline = self._score_timeline_oracle(symbol, side, price, change_pct)
            fusion = self._score_harmonic_fusion(symbol, side)
            gate = self._orchestrator_pretrade_gate(symbol, side)
            item["timeline_bonus"] = float(timeline.get("bonus", 0.0) or 0.0)
            item["timeline_action"] = str(timeline.get("action", "hold") or "hold")
            item["timeline_confidence"] = float(timeline.get("confidence", 0.0) or 0.0)
            item["fusion_bonus"] = float(fusion.get("bonus", 0.0) or 0.0)
            item["fusion_global_coherence"] = float(fusion.get("global_coherence", 0.0) or 0.0)
            item["fusion_symbol_coherence"] = float(fusion.get("symbol_coherence", 0.0) or 0.0)
            item["brain_coherence"] = float(fusion.get("symbol_coherence", 0.0) or 0.0)
            item["orchestrator_reason"] = str(gate.get("reason") or "")
            item["orchestrator_approved"] = bool(gate.get("approved"))
            if not gate.get("approved"):
                item["score"] = 0.0
                item["intel_reason"] = f"orchestrator_gate:{gate.get('reason') or 'blocked'}"
                continue
            item["score"] = max(0.0, base_score + float(timeline.get("bonus", 0.0) or 0.0) * 1.25 + float(fusion.get("bonus", 0.0) or 0.0))
            confidence = self._compute_self_confidence(item)
            item["self_confidence"] = float(confidence.get("score", 0.0) or 0.0)
            item["self_confidence_boost"] = float(confidence.get("boost_multiplier", 1.0) or 1.0)
            item["self_confidence_reason"] = str(confidence.get("reason") or "")
            item["score"] = max(0.0, float(item.get("score", 0.0) or 0.0) * item["self_confidence_boost"])

    def _score_symbol(self, symbol: str, cfg: Dict[str, float], ticker: Dict[str, float]) -> Tuple[float, str]:
        price = float(ticker.get("price", 0.0) or 0.0)
        bid = float(ticker.get("bid", 0.0) or 0.0)
        ask = float(ticker.get("ask", 0.0) or 0.0)
        change_pct = float(ticker.get("change_pct", 0.0) or 0.0)
        if price <= 0:
            return 0.0, ""
        spread_pct = ((ask - bid) / price * 100.0) if bid > 0 and ask > 0 else 0.0
        if spread_pct > float(cfg.get("max_spread_pct", 0.2) or 0.2):
            return 0.0, ""
        threshold = float(cfg.get("momentum_threshold", 0.2) or 0.2)
        if abs(change_pct) < threshold:
            return 0.0, ""
        direction = "BUY" if change_pct > 0 else "SELL"
        if direction == "SELL" and not self._is_shortable(symbol):
            return 0.0, ""
        costs = self._capital_style_cost_profile(symbol, float(cfg.get("size", 1.0) or 1.0), price, float(cfg.get("tp_pct", 0.0) or 0.0))
        if float(costs.get("expected_net_profit", 0.0) or 0.0) <= 0:
            return 0.0, direction
        score = abs(change_pct) - (spread_pct * 0.25)
        score += min(1.5, float(costs["expected_net_profit"]) / max(ALPACA_MIN_TARGET_USD, 0.0001)) * 0.2
        central_symbols = getattr(self, "_central_beat_symbols", {}) or {}
        central_regime = getattr(self, "_central_beat_regime", {}) or {}
        central_signal = central_symbols.get(symbol) or central_symbols.get(symbol.upper()) or {}
        if isinstance(central_signal, dict) and central_signal:
            support_count = max(1, int(central_signal.get("support_count", 1) or 1))
            central_side = str(central_signal.get("side") or direction).upper()
            central_strength = max(0.0, float(central_signal.get("strength", 0.0) or 0.0))
            aligned = central_side == direction
            multiplier = 1.0 + min(0.18, central_strength * 0.12 + (support_count - 1) * 0.03)
            if aligned:
                score *= multiplier
            else:
                score *= max(0.82, 1.0 - min(0.18, central_strength * 0.10))
        if isinstance(central_regime, dict) and central_regime:
            regime_bias = str(central_regime.get("bias") or direction).upper()
            regime_conf = max(0.0, min(1.0, float(central_regime.get("confidence", 0.0) or 0.0)))
            if regime_conf > 0:
                regime_multiplier = 1.0 + regime_conf * 0.05 if regime_bias == direction else 1.0 - regime_conf * 0.05
                score *= max(0.9, regime_multiplier)
        confidence = self._compute_self_confidence({
            "symbol": symbol,
            "direction": direction,
            "change_pct": change_pct,
            "spread_pct": spread_pct,
            **costs,
        })
        score *= float(confidence.get("boost_multiplier", 1.0) or 1.0)
        if self._signal_brain is not None:
            features = {
                "momentum": change_pct,
                "volatility": max(spread_pct, 0.0001),
                "trend_strength": min(abs(change_pct) / max(threshold, 0.01), 1.0),
                "rsi": 50.0 + max(-40.0, min(40.0, change_pct * 10.0)),
            }
            decision = self._signal_brain.decide(symbol, score, features, [score])
            if decision is None:
                return 0.0, direction
            score = float(decision.score)
        return max(0.0, score), direction

    def _find_best_opportunity(self) -> Optional[Tuple[str, Dict[str, float], Dict[str, float]]]:
        counts = self._direction_counts()
        scored: List[Dict[str, Any]] = []
        for symbol, cfg in self.universe.items():
            ticker = self._prices.get(symbol) or {}
            score, direction = self._score_symbol(symbol, cfg, ticker)
            costs = self._capital_style_cost_profile(symbol, float(cfg.get("size", 1.0) or 1.0), float(ticker.get("price", 0.0) or 0.0), float(cfg.get("tp_pct", 0.0) or 0.0))
            scored.append({
                "symbol": symbol,
                "direction": direction,
                "asset_class": "stock",
                "score": score,
                "price": float(ticker.get("price", 0.0) or 0.0),
                "change_pct": float(ticker.get("change_pct", 0.0) or 0.0),
                "spread_pct": (((float(ticker.get("ask", 0.0) or 0.0) - float(ticker.get("bid", 0.0) or 0.0)) / max(float(ticker.get("price", 0.0) or 0.0), 0.0001)) * 100.0),
                "profit_target_usd": ALPACA_MIN_TARGET_USD,
                **costs,
            })
        self._apply_intelligence_overlays(scored)
        scored.sort(key=lambda item: float(item.get("score", 0.0) or 0.0), reverse=True)
        self._latest_candidate_snapshot = scored[:7]
        self._swarm_snapshot = self._build_swarm_snapshot(scored)
        self._latest_target_snapshot = dict(scored[0]) if scored else {}
        for item in scored:
            symbol = str(item.get("symbol") or "")
            direction = str(item.get("direction") or "")
            if float(item.get("score", 0.0) or 0.0) <= 0 or direction not in {"BUY", "SELL"}:
                continue
            if counts.get(direction, 0) >= 1 or len(self.positions) >= MAX_POSITIONS:
                continue
            if self._shadow_blocks_symbol(symbol, direction):
                continue
            cfg = dict(self.universe[symbol])
            cfg["direction"] = direction
            self._latest_target_snapshot = dict(item)
            return symbol, cfg, dict(self._prices.get(symbol) or {})
        return None

    def _shadow_blocks_symbol(self, symbol: str, direction: str) -> bool:
        for pos in self.positions:
            if pos.symbol == symbol and str(pos.direction or "").upper() == direction:
                return True
        for shadow in self.shadow_trades:
            if shadow.symbol == symbol and str(shadow.direction or "").upper() == direction:
                return True
        return False

    def _create_shadow(self, symbol: str, cfg: Dict[str, float], ticker: Dict[str, float]) -> Optional[AlpacaShadowTrade]:
        if len(self.shadow_trades) >= self.SHADOW_MAX_ACTIVE:
            return None
        direction = str(cfg.get("direction") or "BUY").upper()
        if self._shadow_blocks_symbol(symbol, direction):
            return None
        price = float(ticker.get("price") or ticker.get("ask") or ticker.get("bid") or 0.0)
        if price <= 0:
            return None
        size = float(cfg.get("size", 1.0) or 1.0)
        target_move_pct = max(float(cfg.get("tp_pct", 0.0) or 0.0) * 0.35, 0.05)
        score = 0.0
        for candidate in self._latest_candidate_snapshot:
            if str(candidate.get("symbol") or "").upper() == symbol.upper():
                score = float(candidate.get("score", 0.0) or 0.0)
                break
        shadow = AlpacaShadowTrade(
            symbol=symbol,
            direction=direction,
            size=size,
            entry_price=price,
            target_move_pct=target_move_pct,
            score=score,
        )
        self.shadow_trades.append(shadow)
        self._latest_monitor_line = f"ALPACA SHADOW OPEN {symbol} {direction} entry={price:.4f} need={shadow.target_move_pct:.4f}%"
        logger.info("ALPACA SHADOW OPENED: %s %s entry=%.4f need %.4f%%", symbol, direction, price, shadow.target_move_pct)
        return shadow

    def _update_shadows(self) -> None:
        confidence = self._compute_self_confidence()
        validation_window = float(confidence.get("validation_window_secs", self.SHADOW_MIN_VALIDATE) or self.SHADOW_MIN_VALIDATE)
        survivors: List[AlpacaShadowTrade] = []
        for shadow in self.shadow_trades:
            price = float(self._prices.get(shadow.symbol, {}).get("price", 0.0) or 0.0)
            if price > 0:
                shadow.update(price, validation_window)
            if shadow.validated:
                survivors.append(shadow)
                continue
            if shadow.age_secs > self.SHADOW_MAX_AGE:
                self._shadow_failed_count += 1
                logger.info(
                    "ALPACA SHADOW EXPIRED: %s %s moved=%+.4f%% need=%.4f%% age=%.0fs",
                    shadow.symbol,
                    shadow.direction,
                    shadow.current_move_pct,
                    shadow.target_move_pct,
                    shadow.age_secs,
                )
                continue
            survivors.append(shadow)
        self.shadow_trades = survivors

    def _promote_shadow(self, shadow: AlpacaShadowTrade) -> Optional[AlpacaMomentumPosition]:
        ticker = dict(self._prices.get(shadow.symbol) or {})
        cfg = dict(self.universe.get(shadow.symbol) or {})
        if not ticker or not cfg:
            return None
        cfg["direction"] = shadow.direction
        cfg["size"] = shadow.size
        pos = self._open_position(shadow.symbol, cfg, ticker)
        if pos is not None:
            self._shadow_validated_count += 1
            self._latest_monitor_line = f"ALPACA SHADOW PROMOTED {shadow.symbol} {shadow.direction} order={pos.order_id}"
            logger.info("ALPACA SHADOW PROMOTED: %s %s peak=%+.4f%%", shadow.symbol, shadow.direction, shadow.peak_move_pct)
        return pos

    def _sync_positions(self) -> None:
        if not self.client:
            return
        open_positions = self.client.get_positions() or []
        synced: List[AlpacaMomentumPosition] = []
        existing = {p.symbol: p for p in self.positions}
        for raw in open_positions:
            symbol = str(raw.get("symbol") or "").upper()
            qty_raw = float(raw.get("qty", 0.0) or 0.0)
            qty = abs(qty_raw)
            if qty <= 0 or symbol not in self.universe:
                continue
            side = "BUY" if qty_raw > 0 else "SELL"
            entry_price = float(raw.get("avg_entry_price", 0.0) or 0.0)
            cfg = self.universe[symbol]
            tp_price = entry_price * (1 + float(cfg["tp_pct"]) / 100.0) if side == "BUY" else entry_price * (1 - float(cfg["tp_pct"]) / 100.0)
            sl_price = entry_price * (1 - float(cfg["sl_pct"]) / 100.0) if side == "BUY" else entry_price * (1 + float(cfg["sl_pct"]) / 100.0)
            current_price = float(raw.get("current_price", 0.0) or self._prices.get(symbol, {}).get("price", 0.0) or entry_price)
            prior = existing.get(symbol)
            synced.append(
                AlpacaMomentumPosition(
                    symbol=symbol,
                    order_id=str(raw.get("asset_id") or raw.get("symbol") or symbol),
                    direction=side,
                    qty=qty,
                    entry_price=entry_price,
                    tp_price=tp_price,
                    sl_price=sl_price,
                    opened_at=prior.opened_at if prior is not None else time.time(),
                    current_price=current_price,
                )
            )
        self.positions = synced

    def free_existing_assets(self) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        liquidated: List[Dict[str, Any]] = []
        open_positions = self.client.get_positions() or []
        for raw in open_positions:
            symbol = str(raw.get("symbol") or "").upper()
            qty_raw = float(raw.get("qty", 0.0) or 0.0)
            qty = abs(qty_raw)
            if not symbol or qty <= 0:
                continue
            side = "sell" if qty_raw > 0 else "buy"
            result = self.client.place_market_order(symbol, side, quantity=qty)
            if not isinstance(result, dict) or result.get("status") in {"rejected", "canceled"} or result.get("code"):
                self._latest_order_error = f"{symbol} liquidation rejected"
                continue
            liquidated.append({
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "order_id": str(result.get("id") or ""),
                "reason": "FREE_ASSETS",
            })
        if liquidated:
            self._latest_monitor_line = f"ALPACA FREE ASSETS closed={len(liquidated)}"
        return liquidated

    def _open_position(self, symbol: str, cfg: Dict[str, float], ticker: Dict[str, float]) -> Optional[AlpacaMomentumPosition]:
        if not self.client:
            return None
        direction = str(cfg.get("direction") or "BUY").upper()
        qty = float(cfg.get("size", 1.0) or 1.0)
        side = "buy" if direction == "BUY" else "sell"
        entry_price = float(ticker.get("ask" if direction == "BUY" else "bid", ticker.get("price", 0.0)) or 0.0)
        if entry_price <= 0:
            return None
        result = self.client.place_market_order(symbol, side, quantity=qty)
        if not isinstance(result, dict) or result.get("status") in {"rejected", "canceled"} or result.get("code"):
            self._latest_order_error = f"{symbol} order rejected"
            return None
        tp_price = entry_price * (1 + float(cfg["tp_pct"]) / 100.0) if direction == "BUY" else entry_price * (1 - float(cfg["tp_pct"]) / 100.0)
        sl_price = entry_price * (1 - float(cfg["sl_pct"]) / 100.0) if direction == "BUY" else entry_price * (1 + float(cfg["sl_pct"]) / 100.0)
        pos = AlpacaMomentumPosition(
            symbol=symbol,
            order_id=str(result.get("id") or symbol),
            direction=direction,
            qty=qty,
            entry_price=entry_price,
            tp_price=tp_price,
            sl_price=sl_price,
            current_price=entry_price,
        )
        self.positions = [p for p in self.positions if p.symbol != symbol]
        self.positions.append(pos)
        self.stats["trades_opened"] += 1
        self._latest_order_error = ""
        logger.info("ALPACA CAPITAL OPEN: %s %s qty=%s entry=%.4f", symbol, direction, qty, entry_price)
        return pos

    def _close_position(self, pos: AlpacaMomentumPosition, reason: str) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None
        side = "sell" if pos.direction == "BUY" else "buy"
        result = self.client.place_market_order(pos.symbol, side, quantity=pos.qty)
        if not isinstance(result, dict) or result.get("status") in {"rejected", "canceled"} or result.get("code"):
            self._latest_order_error = f"{pos.symbol} close rejected"
            return None
        exit_price = float(self._prices.get(pos.symbol, {}).get("price", pos.current_price or pos.entry_price) or pos.entry_price)
        pnl = ((exit_price - pos.entry_price) * pos.qty) if pos.direction == "BUY" else ((pos.entry_price - exit_price) * pos.qty)
        self.stats["trades_closed"] += 1
        self.stats["total_pnl_usd"] += pnl
        if pnl >= 0:
            self.stats["winning_trades"] += 1
        else:
            self.stats["losing_trades"] += 1
        record = {
            "symbol": pos.symbol,
            "direction": pos.direction,
            "entry_price": pos.entry_price,
            "exit_price": exit_price,
            "net_pnl": pnl,
            "reason": reason,
            "closed_at": time.time(),
        }
        if self._signal_brain is not None and hasattr(self._signal_brain, "learn_from_outcome"):
            try:
                record["learning_update"] = self._signal_brain.learn_from_outcome(
                    pos.symbol,
                    pnl,
                    confidence=max(0.1, min(1.0, abs(pos.pnl_pct) / 2.0)),
                )
            except Exception:
                pass
        self._publish_learning_update(record)
        self._recent_closed_trades.append(record)
        self._recent_closed_trades = self._recent_closed_trades[-5:]
        logger.info("ALPACA CAPITAL CLOSE: %s %s pnl=%+.4f reason=%s", pos.symbol, pos.direction, pnl, reason)
        return record

    def _monitor_positions(self) -> List[Dict[str, Any]]:
        closed: List[Dict[str, Any]] = []
        remaining: List[AlpacaMomentumPosition] = []
        for pos in self.positions:
            price = float(self._prices.get(pos.symbol, {}).get("price", pos.current_price or pos.entry_price) or pos.entry_price)
            pos.current_price = price
            hit_tp = price >= pos.tp_price if pos.direction == "BUY" else price <= pos.tp_price
            hit_sl = price <= pos.sl_price if pos.direction == "BUY" else price >= pos.sl_price
            if hit_tp:
                record = self._close_position(pos, "TP_HIT")
                if record:
                    closed.append(record)
                continue
            if hit_sl:
                record = self._close_position(pos, "SL_HIT")
                if record:
                    closed.append(record)
                continue
            remaining.append(pos)
        self.positions = remaining
        return closed

    def _build_lane_snapshot(self) -> Dict[str, Any]:
        lanes: Dict[str, Any] = {}
        for direction in ("BUY", "SELL"):
            live = next((pos for pos in self.positions if pos.direction == direction), None)
            validated = next((shadow for shadow in self.shadow_trades if shadow.direction == direction and shadow.validated), None)
            queued = next((shadow for shadow in self.shadow_trades if shadow.direction == direction and not shadow.validated), None)
            next_action = "manage_position" if live else ("promote_shadow" if validated else ("await_shadow_validation" if queued else "scan_for_candidate"))
            lanes[direction] = {
                "next_action": next_action,
                "position_symbol": live.symbol if live else "",
                "validated_shadow_symbol": validated.symbol if validated else "",
                "queued_shadow_symbol": queued.symbol if queued else "",
            }
        self._lane_snapshot = lanes
        return lanes

    def get_account_snapshot(self) -> Dict[str, float]:
        if not self.client:
            return {"equity_usd": 0.0, "cash_usd": 0.0, "buying_power_usd": 0.0}
        acct = self.client.get_account() or {}
        return {
            "equity_usd": float(acct.get("equity", 0.0) or 0.0),
            "cash_usd": float(acct.get("cash", 0.0) or 0.0),
            "buying_power_usd": float(acct.get("buying_power", 0.0) or 0.0),
        }

    def status_lines(self) -> List[str]:
        snap = self.get_account_snapshot()
        runtime_m = (time.time() - self.start_time) / 60.0
        eq_delta = snap["equity_usd"] - self.starting_equity_usd if self.starting_equity_usd > 0 else 0.0
        growth = self._compute_growth_metrics()
        confidence = self._compute_self_confidence()
        lines = [
            f"  ALPACA STATUS | runtime={runtime_m:.1f}m",
            f"  Equity=${snap['equity_usd']:.2f} | Cash=${snap['cash_usd']:.2f} | BuyingPower=${snap['buying_power_usd']:.2f} | EqDelta={eq_delta:+.2f}",
            (
                f"  ALPACA STOCKS: {len(self.positions)} open / {int(self.stats['trades_closed'])} closed | "
                f"W:{int(self.stats['winning_trades'])} L:{int(self.stats['losing_trades'])} | "
                f"PnL:${float(self.stats['total_pnl_usd']):+.2f} | gate:open"
            ),
            f"  Shadows: {len(self.shadow_trades)} active | validated={self._shadow_validated_count} failed={self._shadow_failed_count}",
            (
                f"  Confidence: {float(confidence.get('score', 0.0) or 0.0):.2f} "
                f"| boost={float(confidence.get('boost_multiplier', 1.0) or 1.0):.2f}x "
                f"| promote_wait={float(confidence.get('validation_window_secs', self.SHADOW_MIN_VALIDATE) or self.SHADOW_MIN_VALIDATE):.1f}s "
                f"| mode={confidence.get('reason', 'n/a')}"
            ),
            (
                f"  Growth: eq={float(growth.get('equity_growth_pct', 0.0) or 0.0):+.2f}% "
                f"| pnl/hr=${float(growth.get('pnl_per_hour_usd', 0.0) or 0.0):+.3f} "
                f"| trades/hr={float(growth.get('trades_per_hour', 0.0) or 0.0):.2f} "
                f"| avg/close=${float(growth.get('avg_pnl_per_close_usd', 0.0) or 0.0):+.3f} "
                f"| trend={growth.get('trend', 'steady')}"
            ),
        ]
        if self._signal_brain is not None and hasattr(self._signal_brain, "learning_snapshot"):
            try:
                learning = self._signal_brain.learning_snapshot()
                lines.append(
                    f"  Learning: feedback={int(learning.get('total_feedback', 0) or 0)} "
                    f"| win_bias={float(learning.get('win_bias', 0.0) or 0.0):.2f}"
                )
            except Exception:
                pass
        if self._universe_snapshot:
            lines.append(
                f"  Universe: mode={self._universe_snapshot.get('mode', 'unknown')} "
                f"size={int(self._universe_snapshot.get('size', len(self.universe)) or len(self.universe))} "
                f"reason={self._universe_snapshot.get('reason', 'n/a')}"
            )
        if self._scan_window_snapshot:
            lines.append(
                f"  ScanWindow: {int(self._scan_window_snapshot.get('size', 0) or 0)}/"
                f"{int(self._scan_window_snapshot.get('total', len(self.universe)) or len(self.universe))} "
                f"start={int(self._scan_window_snapshot.get('start', 0) or 0)}"
            )
        if self._lane_snapshot:
            buy_lane = self._lane_snapshot.get("BUY", {}) or {}
            sell_lane = self._lane_snapshot.get("SELL", {}) or {}
            lines.append(
                f"  Lanes: BUY={buy_lane.get('next_action', 'scan_for_candidate')} "
                f"[pos={buy_lane.get('position_symbol', '-') or '-'} valid={buy_lane.get('validated_shadow_symbol', '-') or '-'} queue={buy_lane.get('queued_shadow_symbol', '-') or '-'}]"
            )
            lines.append(
                f"         SELL={sell_lane.get('next_action', 'scan_for_candidate')} "
                f"[pos={sell_lane.get('position_symbol', '-') or '-'} valid={sell_lane.get('validated_shadow_symbol', '-') or '-'} queue={sell_lane.get('queued_shadow_symbol', '-') or '-'}]"
            )
        if self._latest_order_error:
            lines.append(f"    Last order: {self._latest_order_error}")
        if self._latest_target_snapshot:
            tgt = self._latest_target_snapshot
            lines.append(
                f"  Target: {tgt.get('symbol', '?')} {tgt.get('direction', '?')} [stock] "
                f"score={float(tgt.get('score', 0.0) or 0.0):.3f} "
                f"chg={float(tgt.get('change_pct', 0.0) or 0.0):+.3f}% "
                f"goal=${float(tgt.get('profit_target_usd', ALPACA_MIN_TARGET_USD) or ALPACA_MIN_TARGET_USD):.2f}"
            )
            lines.append(
                f"    HFT: net=${float(tgt.get('expected_net_profit', 0.0) or 0.0):+.4f} "
                f"cost=${float(tgt.get('round_trip_cost', 0.0) or 0.0):.4f} "
                f"coh={float(tgt.get('brain_coherence', confidence.get('alignment_score', 0.0)) or 0.0):.3f}"
            )
            lines.append(
                f"    Intel: timeline={float(tgt.get('timeline_confidence', 0.0) or 0.0):.2f} "
                f"fusion={float(tgt.get('fusion_global_coherence', 0.0) or 0.0):.2f} "
                f"orch={tgt.get('orchestrator_reason', 'n/a')}"
            )
        if self._latest_candidate_snapshot:
            lines.append("  Top 7 candidates:")
            for idx, item in enumerate(self._latest_candidate_snapshot[:7], start=1):
                lines.append(
                    f"    #{idx} {item.get('symbol', '?')} {item.get('direction', '?')} [stock] "
                    f"score={float(item.get('score', 0.0) or 0.0):.3f} "
                    f"chg={float(item.get('change_pct', 0.0) or 0.0):+.3f}% "
                    f"spr={float(item.get('spread_pct', 0.0) or 0.0):.3f}% "
                    f"net=${float(item.get('expected_net_profit', 0.0) or 0.0):+.4f} "
                    f"goal=${float(item.get('profit_target_usd', ALPACA_MIN_TARGET_USD) or ALPACA_MIN_TARGET_USD):.2f}"
                )
        swarm_leader = dict(self._swarm_snapshot.get("leader", {}) or {})
        if swarm_leader:
            lines.append(
                f"  Swarm: {swarm_leader.get('symbol', '?')} {swarm_leader.get('direction', '?')} "
                f"votes={int(swarm_leader.get('votes', 0) or 0)} "
                f"swarm={float(swarm_leader.get('swarm_score', 0.0) or 0.0):.3f}"
            )
        for pos in self.positions:
            lines.append(pos.one_line())
        for shadow in self.shadow_trades[:4]:
            lines.append(
                f"    SHADOW {shadow.direction:4} {shadow.symbol:5} [stock] "
                f"entry:{shadow.entry_price:.4f} now:{shadow.current_price or shadow.entry_price:.4f} "
                f"move:{shadow.current_move_pct:+.3f}% need:{shadow.target_move_pct:.3f}% "
                f"age:{shadow.age_secs/60.0:.1f}m{' VALID' if shadow.validated else ''}"
            )
        for trade in reversed(self._recent_closed_trades[-3:]):
            lines.append(
                f"  CLOSE: {trade.get('symbol', '?')} {trade.get('direction', '?')} "
                f"{float(trade.get('net_pnl', 0.0) or 0.0):+.2f} USD reason={trade.get('reason', '?')}"
            )
        if self._registry_snapshot.get("categories"):
            lines.append(f"  Registry: {len(self._registry_snapshot.get('categories', {}))} categories linked")
        if self._decision_snapshot:
            if self._decision_snapshot.get("decision"):
                decision = self._decision_snapshot.get("decision", {}) or {}
                lines.append(
                    f"  Decision: {self._decision_snapshot.get('symbol', '?')} {self._decision_snapshot.get('side', '?')} "
                    f"-> {decision.get('type', '?')} conf={float(decision.get('confidence', 0.0) or 0.0):.2f}"
                )
            elif self._decision_snapshot.get("error"):
                lines.append(f"  Decision: error={self._decision_snapshot.get('error')}")
        if self._orchestrator_snapshot:
            lines.append(
                f"  Orchestrator: {self._orchestrator_snapshot.get('symbol', '?')} "
                f"{self._orchestrator_snapshot.get('side', '?')} "
                f"approved={self._orchestrator_snapshot.get('approved', True)} "
                f"reason={self._orchestrator_snapshot.get('reason', '')}"
            )
        if self._thought_bus_snapshot:
            if self._thought_bus_snapshot.get("error"):
                lines.append(f"  ThoughtBus: error={self._thought_bus_snapshot.get('error')}")
            else:
                lines.append(
                    f"  ThoughtBus: market={int(self._thought_bus_snapshot.get('market_events', 0) or 0)} "
                    f"decision={int(self._thought_bus_snapshot.get('decision_events', 0) or 0)}"
                )
        if self._cognition_snapshot:
            if self._cognition_snapshot.get("error"):
                lines.append(f"  Cognition: error={self._cognition_snapshot.get('error')}")
            else:
                lines.append(
                    f"  Cognition: brain={int(self._cognition_snapshot.get('cognition_events', 0) or 0)} "
                    f"queen={int(self._cognition_snapshot.get('queen_events', 0) or 0)}"
                )
        if self._harmonic_wiring_audit:
            ready = sum(1 for value in self._harmonic_wiring_audit.values() if value)
            lines.append(f"  Harmonics: {ready}/{len(self._harmonic_wiring_audit)} wired")
        self._latest_status_lines = lines
        return lines

    def get_dashboard_payload(self) -> Dict[str, Any]:
        growth = self._compute_growth_metrics()
        snap = self.get_account_snapshot()
        return {
            "exchange": "alpaca",
            "mode": "capital_style_stocks",
            "ok": self.enabled,
            "equity_usd": snap["equity_usd"],
            "cash_usd": snap["cash_usd"],
            "buying_power_usd": snap["buying_power_usd"],
            "positions": [
                {
                    "symbol": pos.symbol,
                    "order_id": pos.order_id,
                    "direction": pos.direction,
                    "qty": pos.qty,
                    "entry_price": pos.entry_price,
                    "current_price": pos.current_price,
                    "tp_price": pos.tp_price,
                    "sl_price": pos.sl_price,
                    "age_secs": pos.age_secs,
                    "pnl_pct": pos.pnl_pct,
                }
                for pos in self.positions
            ],
            "shadows": [
                {
                    "symbol": shadow.symbol,
                    "direction": shadow.direction,
                    "size": shadow.size,
                    "entry_price": shadow.entry_price,
                    "current_price": shadow.current_price,
                    "target_move_pct": shadow.target_move_pct,
                    "peak_move_pct": shadow.peak_move_pct,
                    "validated": shadow.validated,
                    "age_secs": shadow.age_secs,
                }
                for shadow in self.shadow_trades
            ],
            "lane_snapshot": dict(self._lane_snapshot),
            "swarm_snapshot": dict(self._swarm_snapshot),
            "registry_snapshot": dict(self._registry_snapshot),
            "decision_snapshot": dict(self._decision_snapshot),
            "orchestrator_snapshot": dict(self._orchestrator_snapshot),
            "timeline_snapshot": dict(self._timeline_snapshot),
            "fusion_snapshot": dict(self._fusion_snapshot),
            "harmonic_wiring_audit": dict(self._harmonic_wiring_audit),
            "universe_snapshot": dict(self._universe_snapshot),
            "scan_window_snapshot": dict(self._scan_window_snapshot),
            "target_snapshot": dict(self._latest_target_snapshot),
            "candidate_snapshot": list(self._latest_candidate_snapshot),
            "growth_metrics": dict(growth),
            "recent_closed_trades": list(self._recent_closed_trades[-5:]),
            "thought_bus_snapshot": dict(self._thought_bus_snapshot),
            "cognition_snapshot": dict(self._cognition_snapshot),
        }

    def tick(self) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        self._refresh_prices()
        self._sync_positions()
        now = time.time()
        closed: List[Dict[str, Any]] = []
        if now - self._last_monitor >= MONITOR_INTERVAL_SECS:
            self._last_monitor = now
            closed.extend(self._monitor_positions())
            self._update_shadows()
            for shadow in list(self.shadow_trades):
                if shadow.validated:
                    pos = self._promote_shadow(shadow)
                    if pos is not None and shadow in self.shadow_trades:
                        self.shadow_trades.remove(shadow)
        if now - self._last_scan >= SCAN_INTERVAL_SECS:
            self._last_scan = now
            if len(self.positions) < MAX_POSITIONS:
                best = self._find_best_opportunity()
                if best is not None:
                    symbol, cfg, ticker = best
                    self._create_shadow(symbol, cfg, ticker)
        if now - float(self._harmonic_wiring_audit_at or 0.0) > 120.0:
            self._harmonic_wiring_audit = self._build_harmonic_wiring_audit()
            self._harmonic_wiring_audit_at = now
        self._probability_validation_snapshot()
        self._build_lane_snapshot()
        self._refresh_registry_snapshot()
        self._update_coordination_snapshots()
        self._publish_market_snapshot_to_thought_bus()
        self._refresh_thought_bus_snapshot()
        self.status_lines()
        return closed
