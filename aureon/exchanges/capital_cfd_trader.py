"""
capital_cfd_trader.py  —  Autonomous CFD Trader for Capital.com

Covers the non-crypto slice of the financial system:
  • Forex   — EURUSD · GBPUSD · USDJPY · AUDUSD · USDCAD · EURGBP
  • Indices — UK100 · US500 · US30 · DE40
  • Commodities — GOLD · SILVER · OIL_CRUDE · NATURALGAS
  • Stocks (CFDs) — AAPL · TSLA · NVDA · AMZN · MSFT

Design principles:
  - tick() is headless (no sleep / no while-True) → called by orca main loop
  - Gated by Seer + Lyra quick-check before opening any position
  - TP / SL / 1-hour time-limit on every position
  - Max 3 concurrent CFD positions to protect margin
  - Phase-aware scoring: momentum + spread quality
  - Status lines for orca dashboard

Author: Aureon Trading System  |  March 2026
"""

import os
import time
import logging
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)
CAPITAL_TRACE_PATH = Path(os.getenv("CAPITAL_TRACE_PATH", os.path.join(os.path.dirname(__file__), "..", "..", "state", "capital_cfd_last_exchange_trace.json"))).resolve()

# ── IMPORT GUARDS ──────────────────────────────────────────────────────────────
try:
    from capital_client import CapitalClient
    HAS_CAPITAL = True
except ImportError:
    CapitalClient = None          # type: ignore
    HAS_CAPITAL = False

# Seer + Lyra lightweight gates (used directly — no full orchestrator needed)
try:
    from aureon_quadrumvirate import seer_should_trade, lyra_should_trade
    HAS_QUAD_GATES = True
except ImportError:
    HAS_QUAD_GATES = False
    seer_should_trade = None      # type: ignore
    lyra_should_trade = None      # type: ignore

# ── INSTRUMENT UNIVERSE ────────────────────────────────────────────────────────
# symbol → {class, tp_pct, sl_pct, size, max_spread_pct, momentum_threshold}
#   tp_pct / sl_pct  — take-profit / stop-loss as % of entry price
#   size             — position size in Capital.com lots / units
#   max_spread_pct   — reject trade if spread exceeds this % of mid-price
#   momentum_threshold — min |change_pct| to consider the move meaningful

CAPITAL_UNIVERSE: Dict[str, dict] = {
    # ── Forex (major pairs) ──────────────────────────────────────────────
    "EURUSD":     {"class": "forex",     "tp_pct": 0.35, "sl_pct": 0.20, "size": 0.01, "max_spread_pct": 0.06, "momentum_threshold": 0.06},
    "GBPUSD":     {"class": "forex",     "tp_pct": 0.35, "sl_pct": 0.20, "size": 0.01, "max_spread_pct": 0.08, "momentum_threshold": 0.06},
    "USDJPY":     {"class": "forex",     "tp_pct": 0.35, "sl_pct": 0.20, "size": 0.01, "max_spread_pct": 0.05, "momentum_threshold": 0.05},
    "AUDUSD":     {"class": "forex",     "tp_pct": 0.35, "sl_pct": 0.20, "size": 0.01, "max_spread_pct": 0.08, "momentum_threshold": 0.07},
    "USDCAD":     {"class": "forex",     "tp_pct": 0.35, "sl_pct": 0.20, "size": 0.01, "max_spread_pct": 0.08, "momentum_threshold": 0.07},
    "EURGBP":     {"class": "forex",     "tp_pct": 0.35, "sl_pct": 0.20, "size": 0.01, "max_spread_pct": 0.07, "momentum_threshold": 0.06},
    # ── Indices ──────────────────────────────────────────────────────────
    "UK100":      {"class": "index",     "tp_pct": 0.55, "sl_pct": 0.30, "size": 1,    "max_spread_pct": 0.05, "momentum_threshold": 0.10},
    "US500":      {"class": "index",     "tp_pct": 0.55, "sl_pct": 0.30, "size": 1,    "max_spread_pct": 0.05, "momentum_threshold": 0.10},
    "US30":       {"class": "index",     "tp_pct": 0.55, "sl_pct": 0.30, "size": 1,    "max_spread_pct": 0.05, "momentum_threshold": 0.10},
    "DE40":       {"class": "index",     "tp_pct": 0.55, "sl_pct": 0.30, "size": 1,    "max_spread_pct": 0.06, "momentum_threshold": 0.12},
    # ── Commodities ───────────────────────────────────────────────────────
    "GOLD":       {"class": "commodity", "tp_pct": 0.75, "sl_pct": 0.45, "size": 0.1,  "max_spread_pct": 0.08, "momentum_threshold": 0.15},
    "SILVER":     {"class": "commodity", "tp_pct": 0.75, "sl_pct": 0.45, "size": 1,    "max_spread_pct": 0.15, "momentum_threshold": 0.20},
    "OIL_CRUDE":  {"class": "commodity", "tp_pct": 0.75, "sl_pct": 0.45, "size": 1,    "max_spread_pct": 0.10, "momentum_threshold": 0.20},
    "NATURALGAS": {"class": "commodity", "tp_pct": 1.00, "sl_pct": 0.60, "size": 10,   "max_spread_pct": 0.25, "momentum_threshold": 0.30},
    # ── Stocks (CFDs) ─────────────────────────────────────────────────────
    "AAPL":       {"class": "stock",     "tp_pct": 0.90, "sl_pct": 0.55, "size": 1,    "max_spread_pct": 0.15, "momentum_threshold": 0.20},
    "TSLA":       {"class": "stock",     "tp_pct": 0.90, "sl_pct": 0.55, "size": 1,    "max_spread_pct": 0.20, "momentum_threshold": 0.25},
    "NVDA":       {"class": "stock",     "tp_pct": 0.90, "sl_pct": 0.55, "size": 1,    "max_spread_pct": 0.20, "momentum_threshold": 0.25},
    "AMZN":       {"class": "stock",     "tp_pct": 0.90, "sl_pct": 0.55, "size": 1,    "max_spread_pct": 0.15, "momentum_threshold": 0.20},
    "MSFT":       {"class": "stock",     "tp_pct": 0.90, "sl_pct": 0.55, "size": 1,    "max_spread_pct": 0.15, "momentum_threshold": 0.20},
}

# ── CONFIG ─────────────────────────────────────────────────────────────────────
CFD_CONFIG: Dict[str, float] = {
    "max_positions":      1.0,   # ONE active CFD position — Stallion Rule / Hive Mind discipline
    "price_ttl_secs":    20.0,   # Price cache lifetime
    "position_ttl_secs": 3600.0, # Max hold time per position (1 hour — stallion rule)
    "scan_interval_secs": 30.0,  # Opportunity scan interval
    "monitor_interval":    5.0,  # Position monitor interval
    "exchange_sync_secs": 15.0,  # Reconcile local CFD positions against Capital.com
    "quad_gate_ttl":      30.0,  # Cache Seer/Lyra gate results for N secs
}

CAPITAL_MIN_PROFIT_GBP = 0.01


# ── DATA CLASSES ───────────────────────────────────────────────────────────────
@dataclass
class CFDPosition:
    """A live Capital.com CFD position tracked by the trader."""
    symbol:        str
    deal_id:       str
    epic:          str
    direction:     str       # "BUY" or "SELL"
    size:          float
    entry_price:   float
    tp_price:      float
    sl_price:      float
    asset_class:   str
    opened_at:     float = field(default_factory=time.time)
    current_price: float = 0.0

    @property
    def age_secs(self) -> float:
        return time.time() - self.opened_at

    @property
    def pnl_pct(self) -> float:
        if self.entry_price <= 0 or self.current_price <= 0:
            return 0.0
        if self.direction == "BUY":
            return (self.current_price - self.entry_price) / self.entry_price * 100
        return (self.entry_price - self.current_price) / self.entry_price * 100

    def one_line(self) -> str:
        age_m = self.age_secs / 60
        pnl_s = f"{self.pnl_pct:+.3f}%"
        tp_dist = abs(self.tp_price - self.current_price) / self.current_price * 100 if self.current_price > 0 else 0
        return (
            f"    {self.direction:4} {self.symbol:12} [{self.asset_class:9}] "
            f"entry:{self.entry_price:.5g}  now:{self.current_price:.5g}  "
            f"PnL:{pnl_s}  TP-dist:{tp_dist:.2f}%  age:{age_m:.1f}m"
        )


# ── MAIN CLASS ─────────────────────────────────────────────────────────────────
class CapitalCFDTrader:
    """
    Autonomous CFD trader for Capital.com (non-crypto asset classes).

    Instruments: Forex · Indices · Commodities · Stocks (CFDs)

    Designed to run inside orca_complete_kill_cycle via tick().
    Each tick() call executes one complete cycle:
      Phase 0: Refresh price cache
      Phase 1: Monitor open positions → TP / SL / time-limit
      Phase 2: Scan for new opportunity → Seer/Lyra gate → open
    Returns list of closed-trade records for orca session_stats.
    """

    def __init__(self) -> None:
        self.client: Optional[CapitalClient] = None

        # Open position tracking
        self.positions: List[CFDPosition] = []

        # Price cache
        self._prices: Dict[str, dict] = {}
        self._prices_fetched_at: float = 0.0
        self._latest_candidate_snapshot: List[Dict[str, Any]] = []
        self._latest_target_snapshot: Dict[str, Any] = {}
        self._latest_status_lines: List[str] = []
        self._latest_monitor_line: str = ""
        self._latest_order_error: str = ""
        self._latest_order_trace_path: str = str(CAPITAL_TRACE_PATH)
        self._recent_closed_trades: List[dict] = []
        self.start_time: float = time.time()
        self.starting_equity_gbp: float = 0.0

        # Timing
        self._last_scan:    float = 0.0
        self._last_monitor: float = 0.0
        self._last_exchange_sync: float = 0.0

        # Cached Seer/Lyra gate result
        self._quad_gate_ok:  bool  = True   # Fail-open
        self._quad_gate_at:  float = 0.0

        # Hive Mind shared intelligence — set externally by TradingHiveMind
        # {symbol/alias: confidence_factor 0.0–1.0} from Market Harp ripples
        self._hive_boosts:   Dict[str, float] = {}

        # Session statistics
        self.stats: Dict[str, float] = {
            "trades_opened":  0.0,
            "trades_closed":  0.0,
            "winning_trades": 0.0,
            "losing_trades":  0.0,
            "total_pnl_gbp":  0.0,
            "best_trade":     0.0,
            "worst_trade":    0.0,
        }

        # Init Capital.com client
        if HAS_CAPITAL:
            try:
                self.client = CapitalClient()  # type: ignore[misc]
                if not getattr(self.client, "enabled", False):
                    logger.info("CapitalCFDTrader: Capital.com credentials missing — trader disabled")
                    self.client = None
                else:
                    logger.info("CapitalCFDTrader: Capital.com client READY")
                    snap = self.get_capital_snapshot()
                    self.starting_equity_gbp = float(snap.get("equity_gbp", 0.0) or 0.0)
                    self._sync_positions_from_exchange(force=True)
            except Exception as _e:
                logger.debug(f"CapitalCFDTrader: client init failed: {_e}")
                self.client = None
        else:
            logger.info("CapitalCFDTrader: capital_client not installed — disabled")

    # ── PROPERTIES ─────────────────────────────────────────────────────────────
    @property
    def enabled(self) -> bool:
        return self.client is not None and getattr(self.client, "enabled", False)

    @property
    def position_count(self) -> int:
        return len(self.positions)

    def _required_tp_pct_for_profit(self, price: float, size: float) -> float:
        """Minimum percentage move required to realize the configured absolute GBP target."""
        notional = max(price * size, 0.0001)
        return (CAPITAL_MIN_PROFIT_GBP / notional) * 100.0

    def _write_exchange_trace(self, payload: Dict[str, Any]) -> None:
        """Persist the latest raw Capital exchange payloads for debugging live behavior."""
        try:
            CAPITAL_TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
            trace = dict(payload)
            trace["written_at"] = time.time()
            with open(CAPITAL_TRACE_PATH, "w", encoding="utf-8") as f:
                json.dump(trace, f, indent=2, default=str)
            self._latest_order_trace_path = str(CAPITAL_TRACE_PATH)
        except Exception as _e:
            logger.debug(f"Capital trace write failed: {_e}")

    def get_capital_snapshot(self) -> Dict[str, float]:
        """Expose Capital.com account state in the same style as the Kraken trader."""
        if not self.client:
            return {
                "equity_gbp": 0.0,
                "free_gbp": 0.0,
                "used_gbp": 0.0,
                "budget_gbp": 0.0,
                "target_pct_equity": 0.0,
            }
        accounts = self.client.get_accounts()
        if not accounts:
            balances = self.client.get_account_balance()
            equity = float(sum(float(v or 0.0) for v in balances.values()))
            free = equity
        else:
            equity = sum(float(acc.get("balance", 0.0) or 0.0) for acc in accounts)
            free = sum(float(acc.get("available", 0.0) or 0.0) for acc in accounts)
        used = max(0.0, equity - free)
        budget = free * 0.70
        target_pct = (CAPITAL_MIN_PROFIT_GBP / equity * 100.0) if equity > 0 else 0.0
        return {
            "equity_gbp": equity,
            "free_gbp": free,
            "used_gbp": used,
            "budget_gbp": budget,
            "target_pct_equity": target_pct,
        }

    # ── PRICES ─────────────────────────────────────────────────────────────────
    def _refresh_prices(self) -> None:
        """Fetch prices for all universe symbols (thread-safe via concurrent futures)."""
        if not self.client:
            return
        if time.time() - self._prices_fetched_at < CFD_CONFIG["price_ttl_secs"]:
            return
        try:
            raw = self.client.get_tickers_for_symbols(list(CAPITAL_UNIVERSE.keys()))
            if raw:
                self._prices = raw
                self._prices_fetched_at = time.time()
        except Exception as _e:
            logger.debug(f"CFD price refresh error: {_e}")

    def _get_price(self, symbol: str) -> Optional[dict]:
        return self._prices.get(symbol.upper())

    def _canonical_symbol(self, value: Optional[str]) -> str:
        if not value:
            return ""
        return "".join(ch for ch in str(value).upper() if ch.isalnum())

    def _symbol_from_market(self, market: dict) -> str:
        candidates = [
            market.get("symbol"),
            market.get("instrumentName"),
            market.get("epic"),
            market.get("marketId"),
        ]
        for candidate in candidates:
            canon = self._canonical_symbol(candidate)
            if canon in CAPITAL_UNIVERSE:
                return canon
        for candidate in candidates:
            canon = self._canonical_symbol(candidate)
            for known in CAPITAL_UNIVERSE:
                if canon == self._canonical_symbol(known):
                    return known
        return self._canonical_symbol(candidates[0]) or str(candidates[0] or "")

    def _position_from_exchange(self, raw: dict) -> Optional[CFDPosition]:
        position = raw.get("position", {}) if isinstance(raw, dict) else {}
        market = raw.get("market", {}) if isinstance(raw, dict) else {}

        deal_id = str(position.get("dealId") or position.get("dealReference") or "").strip()
        direction = str(position.get("direction") or "").upper()
        size = float(position.get("size", 0.0) or 0.0)
        entry_price = float(position.get("level", 0.0) or 0.0)
        epic = str(market.get("epic") or position.get("epic") or "").strip()
        symbol = self._symbol_from_market(market or position)
        if not deal_id or direction not in ("BUY", "SELL") or size <= 0 or entry_price <= 0:
            return None

        price = float(market.get("price") or 0.0)
        bid = float(market.get("bid") or 0.0)
        ask = float(market.get("offer") or market.get("ask") or 0.0)
        current_price = price or ((bid + ask) / 2 if bid > 0 and ask > 0 else bid or ask or entry_price)

        asset_class = str(market.get("instrumentType") or market.get("marketType") or "").lower()
        if not asset_class:
            asset_class = CAPITAL_UNIVERSE.get(symbol, {}).get("class", "unknown")

        tp_level = float(position.get("limitLevel", 0.0) or 0.0)
        sl_level = float(position.get("stopLevel", 0.0) or 0.0)
        cfg = CAPITAL_UNIVERSE.get(symbol, {})
        tp_pct = max(float(cfg.get("tp_pct", 0.0) or 0.0), self._required_tp_pct_for_profit(entry_price, size))
        sl_pct = float(cfg.get("sl_pct", 0.0) or 0.0)
        if tp_level <= 0:
            tp_level = entry_price * (1 + tp_pct / 100.0) if direction == "BUY" else entry_price * (1 - tp_pct / 100.0)
        if sl_level <= 0:
            sl_level = entry_price * (1 - sl_pct / 100.0) if direction == "BUY" else entry_price * (1 + sl_pct / 100.0)

        opened_at = time.time()
        raw_created = position.get("createdDateUTC") or position.get("createdDate")
        if isinstance(raw_created, (int, float)):
            opened_at = float(raw_created)

        return CFDPosition(
            symbol=symbol,
            deal_id=deal_id,
            epic=epic or symbol,
            direction=direction,
            size=size,
            entry_price=entry_price,
            tp_price=tp_level,
            sl_price=sl_level,
            asset_class=asset_class,
            opened_at=opened_at,
            current_price=current_price,
        )

    def _sync_positions_from_exchange(self, force: bool = False) -> None:
        """Reconcile local CFD position state against Capital.com's open positions."""
        if not self.client:
            return
        now = time.time()
        if not force and (now - self._last_exchange_sync) < CFD_CONFIG["exchange_sync_secs"]:
            return
        self._last_exchange_sync = now

        try:
            raw_positions = self.client.get_positions()
            live_positions: List[CFDPosition] = []
            for raw in raw_positions:
                pos = self._position_from_exchange(raw)
                if pos is not None:
                    live_positions.append(pos)

            existing_by_deal = {p.deal_id: p for p in self.positions}
            merged: List[CFDPosition] = []
            for live in live_positions:
                existing = existing_by_deal.get(live.deal_id)
                if existing is not None:
                    live.opened_at = existing.opened_at
                    if existing.current_price > 0:
                        live.current_price = existing.current_price
                merged.append(live)

            self.positions = merged
        except Exception as _e:
            logger.debug(f"Capital CFD sync error: {_e}")

    # ── QUADRUMVIRATE GATE (lightweight) ───────────────────────────────────────
    def _quad_gate(self) -> bool:
        """
        Quick Seer + Lyra gate — cached for quad_gate_ttl secs.
        Returns True if trading is permitted (fail-open if unavailable).
        """
        if not HAS_QUAD_GATES:
            return True
        now = time.time()
        if now - self._quad_gate_at < CFD_CONFIG["quad_gate_ttl"]:
            return self._quad_gate_ok
        self._quad_gate_at = now
        try:
            seer_ok = seer_should_trade() if seer_should_trade else True   # type: ignore[misc]
            lyra_ok = lyra_should_trade() if lyra_should_trade else True   # type: ignore[misc]
            self._quad_gate_ok = seer_ok and lyra_ok
        except Exception:
            self._quad_gate_ok = True   # Fail-open
        return self._quad_gate_ok

    # ── OPPORTUNITY SCANNER ────────────────────────────────────────────────────
    def _score_symbol(self, symbol: str, cfg: dict, ticker: dict) -> float:
        """
        Score a candidate for BUY entry.
        Returns 0.0 = skip; >0.0 = attractive, higher is better.

        Scoring:
          base = momentum magnitude (change_pct)
          penalty = spread quality cost
          gate = spread too wide → 0
          gate = momentum below threshold → 0
        """
        price      = float(ticker.get("price") or 0)
        bid        = float(ticker.get("bid")   or 0)
        ask        = float(ticker.get("ask")   or 0)
        change_pct = float(ticker.get("change_pct") or 0)

        if price <= 0 or bid <= 0 or ask <= 0:
            return 0.0

        # Spread guard
        spread_pct = (ask - bid) / price * 100
        max_spread = cfg.get("max_spread_pct", 0.2) * 100   # convert → %
        if spread_pct > max_spread:
            return 0.0

        # Momentum gate — only trade when price is moving positively
        threshold = cfg.get("momentum_threshold", 0.10)
        if change_pct < threshold:          # Only BUY on upward momentum
            return 0.0

        # Score = momentum minus spread drag
        score = change_pct - spread_pct * 0.15

        # Must have enough room to clear the realized-profit floor.
        size = float(cfg.get("size", 0.0) or 0.0)
        required_tp_pct = self._required_tp_pct_for_profit(price, size)
        configured_tp_pct = float(cfg.get("tp_pct", 0.0) or 0.0)
        if configured_tp_pct < required_tp_pct:
            return 0.0

        expected_profit_gbp = price * size * (configured_tp_pct / 100.0)
        if expected_profit_gbp < CAPITAL_MIN_PROFIT_GBP:
            return 0.0

        score += min(1.0, expected_profit_gbp / max(CAPITAL_MIN_PROFIT_GBP, 0.0001)) * 0.25

        # Hive Mind ripple amplifier — Market Harp signals shared by TradingHiveMind
        # A ripple on a correlated market boosts this symbol's momentum score
        hive_factor = self._hive_boosts.get(symbol, self._hive_boosts.get(symbol.upper(), 0.0))
        if hive_factor > 0:
            score = score * (1.0 + float(hive_factor) * 0.40)

        return max(0.0, score)

    def _find_best_opportunity(self) -> Optional[Tuple[str, dict, dict]]:
        """
        Scan universe for the highest-scored BUY opportunity.
        Returns (symbol, cfg, ticker) or None.
        """
        max_pos = int(CFD_CONFIG["max_positions"])
        if len(self.positions) >= max_pos:
            return None

        already_held = {p.symbol for p in self.positions}
        best_score = 0.0
        best: Optional[Tuple[str, dict, dict]] = None
        scored: List[Dict[str, Any]] = []

        for symbol, cfg in CAPITAL_UNIVERSE.items():
            if symbol in already_held:
                continue
            ticker = self._get_price(symbol)
            if not ticker:
                continue
            score = self._score_symbol(symbol, cfg, ticker)
            price = float(ticker.get("price") or 0.0)
            bid = float(ticker.get("bid") or 0.0)
            ask = float(ticker.get("ask") or 0.0)
            spread_pct = ((ask - bid) / price * 100.0) if price > 0 and bid > 0 and ask > 0 else 0.0
            required_tp_pct = self._required_tp_pct_for_profit(price, float(cfg.get("size", 0.0) or 0.0))
            effective_tp_pct = max(float(cfg.get("tp_pct", 0.0) or 0.0), required_tp_pct)
            scored.append({
                "symbol": symbol,
                "asset_class": cfg.get("class", "unknown"),
                "score": score,
                "price": price,
                "bid": bid,
                "ask": ask,
                "spread_pct": spread_pct,
                "change_pct": float(ticker.get("change_pct") or 0.0),
                "size": float(cfg.get("size", 0.0) or 0.0),
                "tp_pct": effective_tp_pct,
                "sl_pct": float(cfg.get("sl_pct", 0.0) or 0.0),
                "profit_target_gbp": CAPITAL_MIN_PROFIT_GBP,
                "required_tp_pct": required_tp_pct,
            })
            if score > best_score:
                best_score = score
                best = (symbol, cfg, ticker)

        scored.sort(key=lambda item: float(item.get("score", 0.0) or 0.0), reverse=True)
        self._latest_candidate_snapshot = scored[:7]
        if best is not None:
            symbol, cfg, ticker = best
            self._latest_target_snapshot = {
                "symbol": symbol,
                "asset_class": cfg.get("class", "unknown"),
                "score": best_score,
                "price": float(ticker.get("price") or 0.0),
                "change_pct": float(ticker.get("change_pct") or 0.0),
                "size": float(cfg.get("size", 0.0) or 0.0),
                "tp_pct": max(
                    float(cfg.get("tp_pct", 0.0) or 0.0),
                    self._required_tp_pct_for_profit(
                        float(ticker.get("price") or 0.0),
                        float(cfg.get("size", 0.0) or 0.0),
                    ),
                ),
                "sl_pct": float(cfg.get("sl_pct", 0.0) or 0.0),
                "profit_target_gbp": CAPITAL_MIN_PROFIT_GBP,
            }
        else:
            self._latest_target_snapshot = {}
        return best

    # ── POSITION MANAGEMENT ────────────────────────────────────────────────────
    def _open_position(self, symbol: str, cfg: dict, ticker: dict) -> Optional[CFDPosition]:
        """Open a BUY CFD position on Capital.com."""
        if not self.client:
            return None

        ask   = float(ticker.get("ask") or ticker.get("price") or 0)
        price = float(ticker.get("price") or ask)
        if ask <= 0:
            return None

        size     = cfg["size"]
        effective_tp_pct = max(float(cfg["tp_pct"]), self._required_tp_pct_for_profit(ask, size))
        tp_price = ask * (1 + effective_tp_pct / 100)
        sl_price = ask * (1 - cfg["sl_pct"] / 100)

        try:
            known_deal_ids = {
                str((raw.get("position", {}) if isinstance(raw, dict) else {}).get("dealId") or "")
                for raw in self.client.get_positions()
            }
            result = self.client.place_market_order(symbol, "BUY", size)
            trace_payload: Dict[str, Any] = {
                "symbol": symbol,
                "size": size,
                "ticker": dict(ticker),
                "known_deal_ids_before": sorted([d for d in known_deal_ids if d]),
                "order_response": dict(result) if isinstance(result, dict) else result,
                "confirm_response": None,
                "positions_snapshots": [],
                "validated": False,
            }
            if result.get("rejected") or result.get("error"):
                reason = result.get("reason") or result.get("error", "unknown")
                self._latest_order_error = f"{symbol} open rejected: {reason}"
                self._write_exchange_trace(trace_payload)
                logger.debug(f"CFD open rejected {symbol}: {reason}")
                return None

            deal_ref = result.get("dealReference", "")
            deal_id  = result.get("dealId", deal_ref) or deal_ref
            epic     = ticker.get("epic", symbol)
            fill_price = ask  # Estimate; confirm_order may refine
            confirmed_ok = False

            # Attempt to confirm fill price from Capital.com confirmation
            if deal_ref:
                try:
                    conf = self.client.confirm_order(deal_ref)
                    trace_payload["confirm_response"] = dict(conf) if isinstance(conf, dict) else conf
                    if not conf.get("error") and not conf.get("reason"):
                        deal_id    = conf.get("dealId", deal_id) or deal_id
                        fill_price = float(conf.get("level", fill_price) or fill_price)
                        effective_tp_pct = max(float(cfg["tp_pct"]), self._required_tp_pct_for_profit(fill_price, size))
                        tp_price   = fill_price * (1 + effective_tp_pct / 100)
                        sl_price   = fill_price * (1 - cfg["sl_pct"] / 100)
                        confirmed_ok = bool(deal_id)
                except Exception:
                    pass

            live_raw = None
            for _attempt in range(4):
                position_snapshot = self.client.get_positions()
                trace_payload["positions_snapshots"].append(position_snapshot)
                for raw in position_snapshot:
                    raw_pos = raw.get("position", {}) if isinstance(raw, dict) else {}
                    raw_market = raw.get("market", {}) if isinstance(raw, dict) else {}
                    raw_deal_id = str(raw_pos.get("dealId") or raw_pos.get("dealReference") or "")
                    raw_symbol = self._symbol_from_market(raw_market or raw_pos)
                    raw_direction = str(raw_pos.get("direction") or "").upper()
                    if deal_id and raw_deal_id == str(deal_id):
                        live_raw = raw
                        break
                    if raw_deal_id and raw_deal_id not in known_deal_ids and raw_symbol == symbol and raw_direction == "BUY":
                        live_raw = raw
                        deal_id = raw_deal_id
                        break
                if live_raw is not None:
                    break
                time.sleep(0.5)

            if live_raw is None:
                self._latest_order_error = (
                    f"{symbol} open not validated: deal_ref={deal_ref or 'none'} "
                    f"deal_id={deal_id or 'none'} confirmed={confirmed_ok}"
                )
                trace_payload["validated"] = False
                trace_payload["final_error"] = self._latest_order_error
                self._write_exchange_trace(trace_payload)
                logger.warning(
                    "CFD open not validated on exchange for %s (deal_ref=%s deal_id=%s confirmed=%s)",
                    symbol, deal_ref, deal_id, confirmed_ok
                )
                return None

            pos = self._position_from_exchange(live_raw)
            if pos is None:
                logger.warning("CFD open validation returned unusable position for %s", symbol)
                trace_payload["validated"] = False
                trace_payload["final_error"] = f"{symbol} validated raw position could not be parsed"
                self._write_exchange_trace(trace_payload)
                return None
            pos.epic = epic or pos.epic
            pos.current_price = fill_price if fill_price > 0 else pos.current_price
            self.positions = [p for p in self.positions if p.deal_id != pos.deal_id]
            self.positions.append(pos)
            self.stats["trades_opened"] += 1
            self._latest_order_error = ""
            trace_payload["validated"] = True
            trace_payload["validated_deal_id"] = pos.deal_id
            trace_payload["validated_position"] = {
                "symbol": pos.symbol,
                "deal_id": pos.deal_id,
                "epic": pos.epic,
                "direction": pos.direction,
                "entry_price": pos.entry_price,
                "tp_price": pos.tp_price,
                "sl_price": pos.sl_price,
            }
            self._write_exchange_trace(trace_payload)
            self._latest_monitor_line = (
                f"CAPITAL OPEN {symbol} BUY deal={pos.deal_id} size={size} entry={pos.entry_price:.5g} "
                f"tp={pos.tp_price:.5g} sl={pos.sl_price:.5g}"
            )

            print(
                f"  CAPITAL CFD OPEN:  {symbol:12} [{cfg['class'].upper():9}] "
                f"BUY {size} @ {pos.entry_price:.5g} | "
                f"TP:{pos.tp_price:.5g}  SL:{pos.sl_price:.5g} | Deal:{pos.deal_id}"
            )
            return pos

        except Exception as _e:
            self._latest_order_error = f"{symbol} open exception: {_e}"
            self._write_exchange_trace({
                "symbol": symbol,
                "size": size,
                "ticker": dict(ticker),
                "validated": False,
                "final_error": self._latest_order_error,
            })
            logger.debug(f"CFD open exception {symbol}: {_e}")
            return None

    def _close_position(self, pos: CFDPosition, reason: str) -> dict:
        """
        Close a CFD position via Capital.com DELETE /positions/{dealId}.
        Falls back to a reverse market order if DELETE fails.
        Returns a closed-trade record compatible with orca session_stats.
        """
        close_ok = False
        close_detail: Dict[str, Any] = {}
        pnl_gbp = 0.0

        if self.client and pos.deal_id:
            try:
                result = self.client.close_position(pos.deal_id)
                close_ok = bool(result.get("success"))
                close_detail = dict(result)
                if not close_ok:
                    # Fallback: reverse market order to flatten the position
                    opposite = "SELL" if pos.direction == "BUY" else "BUY"
                    fallback = self.client.place_market_order(pos.symbol, opposite, pos.size)
                    close_detail["fallback"] = fallback
                    close_ok = not bool(fallback.get("rejected") or fallback.get("error"))
            except Exception as _e:
                logger.debug(f"CFD close error {pos.symbol}: {_e}")
                close_detail = {"error": str(_e)}

        if self.client and pos.deal_id:
            try:
                still_open = False
                for raw in self.client.get_positions():
                    raw_pos = raw.get("position", {}) if isinstance(raw, dict) else {}
                    if str(raw_pos.get("dealId") or raw_pos.get("dealReference") or "") == pos.deal_id:
                        still_open = True
                        break
                if still_open:
                    close_ok = False
            except Exception as _e:
                logger.debug(f"CFD close verification skipped {pos.symbol}: {_e}")

        # Estimate PnL from tracked prices
        cp = pos.current_price if pos.current_price > 0 else pos.entry_price
        if pos.entry_price > 0 and cp > 0:
            if pos.direction == "BUY":
                pnl_pct = (cp - pos.entry_price) / pos.entry_price
            else:
                pnl_pct = (pos.entry_price - cp) / pos.entry_price
            pnl_gbp = pnl_pct * pos.entry_price * pos.size

        if not close_ok:
            return {
                "error": "close_failed",
                "symbol": pos.symbol,
                "deal_id": pos.deal_id,
                "reason": reason,
                "detail": close_detail,
            }

        # Update session stats
        self.stats["trades_closed"]  += 1
        self.stats["total_pnl_gbp"]  += pnl_gbp
        if pnl_gbp > 0:
            self.stats["winning_trades"] += 1
            self.stats["best_trade"] = max(self.stats["best_trade"], pnl_gbp)
        else:
            self.stats["losing_trades"] += 1
            self.stats["worst_trade"] = min(self.stats["worst_trade"], pnl_gbp)

        print(
            f"  CAPITAL CFD CLOSE: {pos.symbol:12} [{pos.asset_class.upper():9}] "
            f"{reason}  |  PnL: {pnl_gbp:+.4f} GBP  age:{pos.age_secs/60:.1f}m"
        )
        self._latest_monitor_line = (
            f"CAPITAL CLOSE {pos.symbol} {reason} pnl={pnl_gbp:+.4f}GBP age={pos.age_secs/60:.1f}m"
        )

        record = {
            "symbol":           pos.symbol,
            "asset_class":      pos.asset_class,
            "direction":        pos.direction,
            "entry_price":      pos.entry_price,
            "exit_price":       cp,
            "size":             pos.size,
            "net_pnl":          pnl_gbp,
            "net_pnl_currency": "GBP",
            "reason":           reason,
            "age_secs":         pos.age_secs,
        }
        self._recent_closed_trades.append(record)
        self._recent_closed_trades = self._recent_closed_trades[-5:]
        return record

    def _update_position_prices(self) -> None:
        """Refresh current_price on all tracked positions from the price cache."""
        for pos in self.positions:
            ticker = self._get_price(pos.symbol)
            if ticker:
                cp = float(ticker.get("price") or 0)
                if cp > 0:
                    pos.current_price = cp
                    self._latest_monitor_line = (
                        f"CAPITAL MONITOR {pos.symbol} now={cp:.5g} entry={pos.entry_price:.5g} "
                        f"pnl={pos.pnl_pct:+.3f}% tp={pos.tp_price:.5g} sl={pos.sl_price:.5g}"
                    )

    def _monitor_positions(self) -> List[dict]:
        """
        Check TP / SL / 1-hour time-limit on every open position.
        Closes any that trip a condition. Returns list of closed-trade records.
        """
        closed:    List[dict]       = []
        remaining: List[CFDPosition] = []
        max_age = CFD_CONFIG["position_ttl_secs"]

        for pos in self.positions:
            if pos.current_price <= 0:
                remaining.append(pos)
                continue

            close_reason: Optional[str] = None

            if pos.direction == "BUY":
                if pos.current_price >= pos.tp_price:
                    close_reason = f"TP_HIT {pos.current_price:.5g}>={pos.tp_price:.5g}"
                elif pos.current_price <= pos.sl_price:
                    close_reason = f"SL_HIT {pos.current_price:.5g}<={pos.sl_price:.5g}"
            else:   # SELL
                if pos.current_price <= pos.tp_price:
                    close_reason = f"TP_HIT {pos.current_price:.5g}<={pos.tp_price:.5g}"
                elif pos.current_price >= pos.sl_price:
                    close_reason = f"SL_HIT {pos.current_price:.5g}>={pos.sl_price:.5g}"

            if close_reason is None and pos.age_secs >= max_age:
                close_reason = f"TIME_LIMIT {pos.age_secs/60:.0f}m"

            if close_reason:
                record = self._close_position(pos, close_reason)
                if record.get("error"):
                    remaining.append(pos)
                else:
                    closed.append(record)
            else:
                remaining.append(pos)

        self.positions = remaining
        return closed

    # ── HEADLESS TICK ──────────────────────────────────────────────────────────
    def tick(self) -> List[dict]:
        """
        Execute ONE complete autonomous CFD cycle (no sleep, no loop).
        Called by orca_complete_kill_cycle run_autonomous() every N seconds.

        Phases:
          0 – Refresh price cache (rate-limited to price_ttl_secs)
          1 – Update position prices + check TP/SL/time-limit
          2 – Quadrumvirate gate → scan → open if green

        Returns: list of closed-trade records
        """
        if not self.client:
            return []

        now = time.time()
        closed_this_tick: List[dict] = []

        self._sync_positions_from_exchange()

        # Phase 0: price refresh
        self._refresh_prices()

        # Phase 1: monitor open positions
        if now - self._last_monitor >= CFD_CONFIG["monitor_interval"]:
            self._last_monitor = now
            self._update_position_prices()
            closed_this_tick.extend(self._monitor_positions())

        # Phase 2: scan for new opportunity
        if now - self._last_scan >= CFD_CONFIG["scan_interval_secs"]:
            self._last_scan = now

            if len(self.positions) < int(CFD_CONFIG["max_positions"]):
                # Quick Seer + Lyra gate before committing capital
                if self._quad_gate():
                    opportunity = self._find_best_opportunity()
                    if opportunity:
                        sym, cfg, ticker = opportunity
                        self._open_position(sym, cfg, ticker)
                else:
                    logger.debug("CFD tick: Quadrumvirate gate CLOSED — scan skipped")

        self.status_lines()
        return closed_this_tick

    # ── STATUS ─────────────────────────────────────────────────────────────────
    def status_lines(self) -> List[str]:
        """Return human-readable status lines for orca dashboard / print_status."""
        w = int(self.stats["winning_trades"])
        l = int(self.stats["losing_trades"])
        c = int(self.stats["trades_closed"])
        pnl = self.stats["total_pnl_gbp"]
        gate = "ARMED" if HAS_QUAD_GATES else "open"
        capital = self.get_capital_snapshot()
        eq_delta = capital["equity_gbp"] - self.starting_equity_gbp if self.starting_equity_gbp > 0 else 0.0
        runtime_m = (time.time() - self.start_time) / 60.0

        lines: List[str] = [
            f"  CAPITAL STATUS | runtime={runtime_m:.1f}m",
            (
                f"  Equity={capital['equity_gbp']:.2f} GBP | Free={capital['free_gbp']:.2f} GBP | "
                f"Used={capital['used_gbp']:.2f} GBP | Budget={capital['budget_gbp']:.2f} GBP | "
                f"EqDelta={eq_delta:+.2f} GBP"
            ),
            f"  CAPITAL CFD: {len(self.positions)} open / {c} closed | "
            f"W:{w} L:{l} | PnL:{pnl:+.2f} GBP | gate:{gate}"
        ]
        # Asset-class breakdown
        by_class: Dict[str, int] = {}
        for pos in self.positions:
            by_class[pos.asset_class] = by_class.get(pos.asset_class, 0) + 1
        if by_class:
            breakdown = "  ".join(f"{cls}:{n}" for cls, n in sorted(by_class.items()))
            lines.append(f"    Classes: {breakdown}")
        if self._latest_order_error:
            lines.append(f"    Last order: {self._latest_order_error}")
            lines.append(f"    Trace: {self._latest_order_trace_path}")
        for pos in self.positions:
            lines.append(pos.one_line())
        if self._latest_target_snapshot:
            target = self._latest_target_snapshot
            lines.append(
                f"  Target: {target.get('symbol', '?')} [{target.get('asset_class', '?')}] "
                f"score={float(target.get('score', 0.0) or 0.0):.3f} "
                f"chg={float(target.get('change_pct', 0.0) or 0.0):+.3f}% "
                f"goal=£{float(target.get('profit_target_gbp', CAPITAL_MIN_PROFIT_GBP) or CAPITAL_MIN_PROFIT_GBP):.2f}"
            )
        if self._latest_candidate_snapshot:
            lines.append("  Top 7 candidates:")
            for idx, candidate in enumerate(self._latest_candidate_snapshot[:7], start=1):
                lines.append(
                    f"    #{idx} {candidate.get('symbol', '?')} [{candidate.get('asset_class', '?')}] "
                    f"score={float(candidate.get('score', 0.0) or 0.0):.3f} "
                    f"chg={float(candidate.get('change_pct', 0.0) or 0.0):+.3f}% "
                    f"spr={float(candidate.get('spread_pct', 0.0) or 0.0):.3f}% "
                    f"goal=£{float(candidate.get('profit_target_gbp', CAPITAL_MIN_PROFIT_GBP) or CAPITAL_MIN_PROFIT_GBP):.2f}"
                )
        for trade in reversed(self._recent_closed_trades[-3:]):
            lines.append(
                f"  CLOSE: {trade.get('symbol', '?')} {trade.get('direction', '?')} "
                f"{float(trade.get('net_pnl', 0.0) or 0.0):+.2f} GBP reason={trade.get('reason', '?')}"
            )
        self._latest_status_lines = lines
        return lines

    def recommendations_summary(self) -> str:
        """One-liner for quick console display."""
        return (
            f"Capital CFD: {len(self.positions)}/{int(CFD_CONFIG['max_positions'])} pos | "
            f"PnL:{self.stats['total_pnl_gbp']:+.2f} GBP"
        )

    def get_dashboard_payload(self) -> Dict[str, Any]:
        """Expose Capital trader state in the same local-dashboard style as the margin trader."""
        capital = self.get_capital_snapshot()
        return {
            "exchange": "capital",
            "mode": "cfd",
            "ok": self.enabled,
            "equity_gbp": capital["equity_gbp"],
            "free_gbp": capital["free_gbp"],
            "used_gbp": capital["used_gbp"],
            "budget_gbp": capital["budget_gbp"],
            "target_pct_equity": capital["target_pct_equity"],
            "positions": [
                {
                    "symbol": pos.symbol,
                    "epic": pos.epic,
                    "direction": pos.direction,
                    "size": pos.size,
                    "entry_price": pos.entry_price,
                    "current_price": pos.current_price,
                    "tp_price": pos.tp_price,
                    "sl_price": pos.sl_price,
                    "asset_class": pos.asset_class,
                    "age_secs": pos.age_secs,
                    "pnl_pct": pos.pnl_pct,
                }
                for pos in self.positions
            ],
            "stats": dict(self.stats),
            "latest_monitor_line": self._latest_monitor_line,
            "status_lines": self._latest_status_lines[-16:],
            "candidate_snapshot": list(self._latest_candidate_snapshot),
            "target_snapshot": dict(self._latest_target_snapshot),
            "recent_closed_trades": list(self._recent_closed_trades[-5:]),
        }
