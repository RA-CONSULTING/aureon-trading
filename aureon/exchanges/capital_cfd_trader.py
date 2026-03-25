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

try:
    from aureon.intelligence.aureon_brain import AureonBrain
    HAS_AUREON_BRAIN = True
except Exception:
    AureonBrain = None            # type: ignore
    HAS_AUREON_BRAIN = False

try:
    from aureon.portfolio.trade_profit_validator import TradeProfitValidator
    HAS_TRADE_PROFIT_VALIDATOR = True
except Exception:
    TradeProfitValidator = None   # type: ignore
    HAS_TRADE_PROFIT_VALIDATOR = False

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
def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except Exception:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


CFD_CONFIG: Dict[str, float] = {
    "max_positions":      _env_float("CAPITAL_MAX_POSITIONS", 2.0),   # One BUY lane and one SELL lane
    "price_ttl_secs":    _env_float("CAPITAL_PRICE_TTL_SECS", 10.0),  # Price cache lifetime
    "position_ttl_secs": _env_float("CAPITAL_POSITION_TTL_SECS", 3600.0), # Max hold time per position (1 hour — stallion rule)
    "scan_interval_secs": _env_float("CAPITAL_SCAN_INTERVAL_SECS", 5.0),  # Opportunity scan interval
    "monitor_interval":   _env_float("CAPITAL_MONITOR_INTERVAL_SECS", 2.0),  # Position monitor interval
    "exchange_sync_secs": _env_float("CAPITAL_EXCHANGE_SYNC_SECS", 5.0),  # Reconcile local CFD positions against Capital.com
    "quad_gate_ttl":      _env_float("CAPITAL_QUAD_GATE_TTL_SECS", 10.0),  # Cache Seer/Lyra gate results for N secs
}
CFD_FLAGS = {
    "profit_only_closes": _env_bool("CAPITAL_PROFIT_ONLY_CLOSES", True),
    "penny_take_profit": _env_bool("CAPITAL_PENNY_TAKE_PROFIT", True),
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
        self._signal_brain = AureonBrain() if HAS_AUREON_BRAIN and AureonBrain is not None else None
        self._trade_profit_validator = (
            TradeProfitValidator(validation_log_file=os.path.join(os.path.dirname(__file__), "..", "..", "state", "capital_trade_validations.json"))
            if HAS_TRADE_PROFIT_VALIDATOR and TradeProfitValidator is not None
            else None
        )

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

    def _effective_tp_pct(self, price: float, size: float, cfg: Optional[dict] = None) -> float:
        required_tp_pct = self._required_tp_pct_for_profit(price, size)
        configured_tp_pct = float((cfg or {}).get("tp_pct", 0.0) or 0.0)
        if CFD_FLAGS["penny_take_profit"]:
            return required_tp_pct
        return max(configured_tp_pct, required_tp_pct)

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

    def _extract_capital_min_size(self, market_info: dict) -> float:
        """Best-effort extraction of Capital's minimum deal size for a market."""
        if not isinstance(market_info, dict):
            return 0.0
        instrument = market_info.get("instrument", {}) if isinstance(market_info.get("instrument"), dict) else {}
        dealing_rules = market_info.get("dealingRules", {}) if isinstance(market_info.get("dealingRules"), dict) else {}
        candidates = [
            dealing_rules.get("minDealSize", {}).get("value") if isinstance(dealing_rules.get("minDealSize"), dict) else dealing_rules.get("minDealSize"),
            instrument.get("minDealSize"),
            market_info.get("minDealSize"),
        ]
        for candidate in candidates:
            try:
                value = float(candidate or 0.0)
                if value > 0:
                    return value
            except (TypeError, ValueError):
                continue
        return 0.0

    def _market_status_text(self, market_info: dict) -> str:
        if not isinstance(market_info, dict):
            return "UNKNOWN"
        snapshot = market_info.get("snapshot", {}) if isinstance(market_info.get("snapshot"), dict) else {}
        instrument = market_info.get("instrument", {}) if isinstance(market_info.get("instrument"), dict) else {}
        for candidate in (
            snapshot.get("marketStatus"),
            market_info.get("marketStatus"),
            instrument.get("marketStatus"),
            instrument.get("tradingStatus"),
            market_info.get("status"),
        ):
            text = str(candidate or "").strip()
            if text:
                return text.upper()
        return "UNKNOWN"

    def _capital_preflight(self, symbol: str, size: float, ticker: dict, cfg: Optional[dict] = None) -> Dict[str, Any]:
        """Collect exchange-side constraints before placing a Capital market order."""
        preflight: Dict[str, Any] = {
            "symbol": symbol,
            "epic": str(ticker.get("epic") or symbol),
            "requested_size": float(size or 0.0),
            "available_balance": 0.0,
            "market_status": "UNKNOWN",
            "minimum_deal_size": 0.0,
            "price": float(ticker.get("price") or 0.0),
            "spread": 0.0,
            "spread_pct": 0.0,
            "expected_gross_profit": 0.0,
            "expected_net_profit": 0.0,
            "round_trip_cost": 0.0,
            "ok": False,
            "reason": "",
        }
        if not self.client:
            preflight["reason"] = "capital client unavailable"
            return preflight

        try:
            accounts = self.client.get_accounts()
        except Exception as _e:
            accounts = []
            preflight["accounts_error"] = str(_e)
        preflight["accounts"] = accounts
        preflight["available_balance"] = float(
            sum(float(acc.get("available", 0.0) or 0.0) for acc in accounts)
        )

        market_summary: Dict[str, Any] = {}
        market_detail: Dict[str, Any] = {}
        try:
            if hasattr(self.client, "_resolve_market"):
                resolved = self.client._resolve_market(symbol)  # type: ignore[attr-defined]
                if isinstance(resolved, dict):
                    market_summary = resolved
                    preflight["epic"] = str(resolved.get("epic") or preflight["epic"])
        except Exception as _e:
            preflight["market_resolve_error"] = str(_e)

        try:
            if hasattr(self.client, "_get_market_snapshot"):
                snapshot = self.client._get_market_snapshot(preflight["epic"])  # type: ignore[attr-defined]
                if isinstance(snapshot, dict):
                    market_detail = snapshot
        except Exception as _e:
            preflight["market_snapshot_error"] = str(_e)

        market_info = market_detail or market_summary
        preflight["market_status"] = self._market_status_text(market_info)
        preflight["minimum_deal_size"] = self._extract_capital_min_size(market_info)

        snapshot = market_detail.get("snapshot", {}) if isinstance(market_detail.get("snapshot"), dict) else {}
        bid = float(
            ticker.get("bid")
            or snapshot.get("bid")
            or market_summary.get("bid")
            or 0.0
        )
        ask = float(
            ticker.get("ask")
            or snapshot.get("offer")
            or market_summary.get("offer")
            or 0.0
        )
        price = float(
            ticker.get("price")
            or ((bid + ask) / 2.0 if bid > 0 and ask > 0 else 0.0)
            or snapshot.get("midOpen")
            or 0.0
        )
        spread = max(ask - bid, 0.0) if bid > 0 and ask > 0 else 0.0
        preflight["price"] = price
        preflight["bid"] = bid
        preflight["ask"] = ask
        preflight["spread"] = spread
        preflight["spread_pct"] = (spread / price * 100.0) if price > 0 and spread > 0 else 0.0

        if isinstance(cfg, dict):
            effective_tp_pct = self._effective_tp_pct(price or ask or 0.0, preflight["requested_size"], cfg)
            cost_profile = self._capital_cost_profile(symbol, preflight["requested_size"], price or ask or 0.0, effective_tp_pct)
            preflight.update(cost_profile)
            preflight["effective_tp_pct"] = effective_tp_pct

        if preflight["requested_size"] <= 0:
            preflight["reason"] = "requested size <= 0"
            return preflight
        if preflight["minimum_deal_size"] > 0 and preflight["requested_size"] < preflight["minimum_deal_size"]:
            preflight["reason"] = (
                f"requested size {preflight['requested_size']:.6g} below Capital minimum "
                f"{preflight['minimum_deal_size']:.6g}"
            )
            return preflight
        if preflight["available_balance"] <= 0:
            preflight["reason"] = "available account balance <= 0"
            return preflight

        allowed_statuses = {"TRADEABLE", "TRADEABLE_ONLINE", "OPEN", "EDITS_ONLY", "ONLINE"}
        market_status = str(preflight["market_status"] or "").upper()
        if market_status and market_status not in allowed_statuses and market_status != "UNKNOWN":
            preflight["reason"] = f"market not tradeable: {market_status}"
            return preflight
        if price <= 0 and ask <= 0:
            preflight["reason"] = "missing live price"
            return preflight
        if isinstance(cfg, dict) and float(preflight.get("expected_net_profit", 0.0) or 0.0) <= 0:
            preflight["reason"] = (
                f"expected net profit {float(preflight.get('expected_net_profit', 0.0) or 0.0):+.4f} "
                f"does not clear costs {float(preflight.get('round_trip_cost', 0.0) or 0.0):.4f}"
            )
            return preflight

        preflight["ok"] = True
        preflight["reason"] = "ok"
        return preflight

    def _sized_cfg_from_preflight(self, cfg: dict, preflight: Dict[str, Any]) -> Optional[dict]:
        """Raise size to Capital's minimum when that is affordable and otherwise valid."""
        adjusted = dict(cfg)
        requested_size = float(adjusted.get("size", 0.0) or 0.0)
        minimum_size = float(preflight.get("minimum_deal_size", 0.0) or 0.0)
        price = float(preflight.get("price", 0.0) or 0.0)
        available_balance = float(preflight.get("available_balance", 0.0) or 0.0)
        if minimum_size <= 0 or minimum_size <= requested_size:
            return adjusted
        if price <= 0:
            return None
        if available_balance > 0 and (minimum_size * price) > available_balance:
            return None
        adjusted["size"] = minimum_size
        return adjusted

    def _capital_cost_profile(self, symbol: str, size: float, price: float, tp_pct: float) -> Dict[str, float]:
        """Estimate whether a Capital trade clears execution costs with the configured target."""
        notional = max(float(size or 0.0) * float(price or 0.0), 0.0)
        expected_gross_profit = notional * (max(float(tp_pct or 0.0), 0.0) / 100.0)
        if self._trade_profit_validator is None or notional <= 0:
            return {
                "notional": notional,
                "expected_gross_profit": expected_gross_profit,
                "round_trip_cost": 0.0,
                "expected_net_profit": expected_gross_profit,
            }
        try:
            costs = self._trade_profit_validator.get_exchange_costs(
                "capital",
                notional,
                is_taker=True,
                symbol=symbol,
            )
            round_trip_cost = float(costs.get("total", 0.0) or 0.0) * 2.0
        except Exception:
            round_trip_cost = 0.0
        return {
            "notional": notional,
            "expected_gross_profit": expected_gross_profit,
            "round_trip_cost": round_trip_cost,
            "expected_net_profit": expected_gross_profit - round_trip_cost,
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
        tp_pct = self._effective_tp_pct(entry_price, size, cfg)
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
    def _score_symbol(self, symbol: str, cfg: dict, ticker: dict) -> Tuple[float, str]:
        """
        Score a candidate for BUY/SELL entry.
        Returns (0.0, "") = skip; (>0.0, direction) = attractive, higher is better.

        Scoring:
          base = momentum magnitude (abs(change_pct))
          penalty = spread quality cost
          gate = spread too wide → 0
          gate = abs(momentum) below threshold → 0
        """
        price      = float(ticker.get("price") or 0)
        bid        = float(ticker.get("bid")   or 0)
        ask        = float(ticker.get("ask")   or 0)
        change_pct = float(ticker.get("change_pct") or 0)

        if price <= 0 or bid <= 0 or ask <= 0:
            return 0.0, ""

        # Spread guard
        spread_pct = (ask - bid) / price * 100
        max_spread = cfg.get("max_spread_pct", 0.2) * 100   # convert → %
        if spread_pct > max_spread:
            return 0.0, ""

        # Momentum gate — trade in the direction of the move
        threshold = cfg.get("momentum_threshold", 0.10)
        if abs(change_pct) < threshold:
            return 0.0, ""
        direction = "BUY" if change_pct > 0 else "SELL"

        # Score = momentum minus spread drag
        score = abs(change_pct) - spread_pct * 0.15

        # Must have enough room to clear the realized-profit floor.
        size = float(cfg.get("size", 0.0) or 0.0)
        required_tp_pct = self._required_tp_pct_for_profit(price, size)
        effective_tp_pct = self._effective_tp_pct(price, size, cfg)
        if effective_tp_pct <= 0:
            return 0.0, ""

        expected_profit_gbp = price * size * (effective_tp_pct / 100.0)
        if expected_profit_gbp < CAPITAL_MIN_PROFIT_GBP:
            return 0.0, ""

        score += min(1.0, expected_profit_gbp / max(CAPITAL_MIN_PROFIT_GBP, 0.0001)) * 0.25

        # Hive Mind ripple amplifier — Market Harp signals shared by TradingHiveMind
        # A ripple on a correlated market boosts this symbol's momentum score
        hive_factor = self._hive_boosts.get(symbol, self._hive_boosts.get(symbol.upper(), 0.0))
        if hive_factor > 0:
            score = score * (1.0 + float(hive_factor) * 0.40)

        return max(0.0, score), direction

    def _apply_hft_analysis(self, scored: List[Dict[str, Any]]) -> None:
        """Use the repo's viable HFT/intel helpers on Capital candidates."""
        positive_scores = [float(item.get("score", 0.0) or 0.0) for item in scored if float(item.get("score", 0.0) or 0.0) > 0]
        for item in scored:
            symbol = str(item.get("symbol") or "")
            score = float(item.get("score", 0.0) or 0.0)
            size = float(item.get("size", 0.0) or 0.0)
            price = float(item.get("price", 0.0) or 0.0)
            change_pct = float(item.get("change_pct", 0.0) or 0.0)
            spread_pct = float(item.get("spread_pct", 0.0) or 0.0)
            tp_pct = float(item.get("tp_pct", 0.0) or 0.0)

            cost_profile = self._capital_cost_profile(symbol, size, price, tp_pct)
            item.update(cost_profile)
            if cost_profile["expected_net_profit"] <= 0:
                item["hft_reason"] = "cost_gate"
                item["score"] = 0.0
                continue

            if self._signal_brain is None:
                item["brain_coherence"] = 0.0
                continue

            threshold = max(float(CAPITAL_UNIVERSE.get(symbol, {}).get("momentum_threshold", 0.1) or 0.1), 0.01)
            features = {
                "momentum": change_pct,
                "volatility": max(spread_pct, 0.0001),
                "trend_strength": min(abs(change_pct) / threshold, 1.0),
                "rsi": 50.0 + max(-45.0, min(45.0, change_pct * 10.0)),
            }
            try:
                decision = self._signal_brain.decide(symbol, score, features, positive_scores or [score])
            except Exception:
                decision = None

            if decision is None:
                item["brain_coherence"] = 0.0
                item["hft_reason"] = "brain_gate"
                item["score"] = 0.0
                continue

            item["brain_coherence"] = float(decision.coherence)
            item["score"] = float(decision.score)

    def _direction_counts(self) -> Dict[str, int]:
        counts = {"BUY": 0, "SELL": 0}
        for pos in self.positions:
            direction = str(getattr(pos, "direction", "") or "").upper()
            if direction in counts:
                counts[direction] += 1
        return counts

    def _can_open_candidate(self, symbol: str, direction: str, counts: Optional[Dict[str, int]] = None) -> bool:
        direction = str(direction or "").upper()
        if direction not in {"BUY", "SELL"}:
            return False
        if counts is None:
            counts = self._direction_counts()
        if counts.get(direction, 0) >= 1:
            return False
        for pos in self.positions:
            if pos.symbol == symbol and str(pos.direction or "").upper() == direction:
                return False
        return len(self.positions) < int(CFD_CONFIG["max_positions"])

    def _find_best_opportunity(self) -> Optional[Tuple[str, dict, dict]]:
        """
        Scan universe for the highest-scored directional opportunity.
        Returns (symbol, cfg, ticker) or None.
        """
        max_pos = int(CFD_CONFIG["max_positions"])
        if len(self.positions) >= max_pos:
            return None

        direction_counts = self._direction_counts()
        best_score = 0.0
        best: Optional[Tuple[str, dict, dict]] = None
        scored: List[Dict[str, Any]] = []

        for symbol, cfg in CAPITAL_UNIVERSE.items():
            ticker = self._get_price(symbol)
            if not ticker:
                continue
            score, direction = self._score_symbol(symbol, cfg, ticker)
            if not self._can_open_candidate(symbol, direction, direction_counts):
                continue
            price = float(ticker.get("price") or 0.0)
            bid = float(ticker.get("bid") or 0.0)
            ask = float(ticker.get("ask") or 0.0)
            spread_pct = ((ask - bid) / price * 100.0) if price > 0 and bid > 0 and ask > 0 else 0.0
            required_tp_pct = self._required_tp_pct_for_profit(price, float(cfg.get("size", 0.0) or 0.0))
            effective_tp_pct = self._effective_tp_pct(price, float(cfg.get("size", 0.0) or 0.0), cfg)
            scored.append({
                "symbol": symbol,
                "direction": direction,
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
                best = (symbol, {**cfg, "direction": direction}, ticker)

        self._apply_hft_analysis(scored)
        scored.sort(key=lambda item: float(item.get("score", 0.0) or 0.0), reverse=True)
        self._latest_candidate_snapshot = scored[:7]
        if best is not None:
            symbol, cfg, ticker = best
            self._latest_target_snapshot = {
                "symbol": symbol,
                "direction": cfg.get("direction", "BUY"),
                "asset_class": cfg.get("class", "unknown"),
                "score": best_score,
                "price": float(ticker.get("price") or 0.0),
                "change_pct": float(ticker.get("change_pct") or 0.0),
                "size": float(cfg.get("size", 0.0) or 0.0),
                "tp_pct": max(
                    self._effective_tp_pct(
                        float(ticker.get("price") or 0.0),
                        float(cfg.get("size", 0.0) or 0.0),
                        cfg,
                    ),
                    0.0,
                ),
                "sl_pct": float(cfg.get("sl_pct", 0.0) or 0.0),
                "profit_target_gbp": CAPITAL_MIN_PROFIT_GBP,
            }
            for candidate in scored:
                if str(candidate.get("symbol") or "").upper() == symbol:
                    self._latest_target_snapshot.update({
                        "brain_coherence": float(candidate.get("brain_coherence", 0.0) or 0.0),
                        "expected_net_profit": float(candidate.get("expected_net_profit", 0.0) or 0.0),
                        "round_trip_cost": float(candidate.get("round_trip_cost", 0.0) or 0.0),
                    })
                    break
        else:
            self._latest_target_snapshot = {}
        return best

    def _ranked_opportunities(self) -> List[Tuple[str, dict, dict]]:
        ranked: List[Tuple[str, dict, dict]] = []
        direction_counts = self._direction_counts()
        for candidate in self._latest_candidate_snapshot:
            symbol = str(candidate.get("symbol") or "").upper()
            direction = str(candidate.get("direction") or "BUY").upper()
            cfg = CAPITAL_UNIVERSE.get(symbol)
            ticker = self._get_price(symbol)
            if (
                symbol
                and cfg
                and ticker
                and float(candidate.get("score", 0.0) or 0.0) > 0
                and self._can_open_candidate(symbol, direction, direction_counts)
            ):
                ranked.append((symbol, {**dict(cfg), "direction": direction}, ticker))
        return ranked

    # ── POSITION MANAGEMENT ────────────────────────────────────────────────────
    def _open_position(self, symbol: str, cfg: dict, ticker: dict) -> Optional[CFDPosition]:
        """Open a BUY or SELL CFD position on Capital.com."""
        if not self.client:
            return None

        ask   = float(ticker.get("ask") or ticker.get("price") or 0)
        bid   = float(ticker.get("bid") or ticker.get("price") or 0)
        direction = str(cfg.get("direction") or "BUY").upper()
        entry_price = ask if direction == "BUY" else bid
        if entry_price <= 0:
            return None

        size     = cfg["size"]
        effective_tp_pct = self._effective_tp_pct(entry_price, size, cfg)
        if direction == "BUY":
            tp_price = entry_price * (1 + effective_tp_pct / 100)
            sl_price = entry_price * (1 - cfg["sl_pct"] / 100)
        else:
            tp_price = entry_price * (1 - effective_tp_pct / 100)
            sl_price = entry_price * (1 + cfg["sl_pct"] / 100)

        try:
            preflight = self._capital_preflight(symbol, float(size), ticker, cfg)
            trace_payload: Dict[str, Any] = {
                "symbol": symbol,
                "direction": direction,
                "size": size,
                "ticker": dict(ticker),
                "preflight": preflight,
                "known_deal_ids_before": [],
                "order_response": None,
                "confirm_response": None,
                "positions_snapshots": [],
                "validated": False,
            }
            if not preflight.get("ok"):
                self._latest_order_error = f"{symbol} preflight failed: {preflight.get('reason') or 'unknown'}"
                trace_payload["final_error"] = self._latest_order_error
                self._write_exchange_trace(trace_payload)
                logger.warning("CFD preflight failed for %s: %s", symbol, preflight.get("reason") or "unknown")
                return None
            known_deal_ids = {
                str((raw.get("position", {}) if isinstance(raw, dict) else {}).get("dealId") or "")
                for raw in self.client.get_positions()
            }
            trace_payload["known_deal_ids_before"] = sorted([d for d in known_deal_ids if d])
            result = self.client.place_market_order(symbol, direction, size)
            trace_payload["order_response"] = dict(result) if isinstance(result, dict) else result
            if result.get("rejected") or result.get("error"):
                reason = result.get("reason") or result.get("error", "unknown")
                self._latest_order_error = f"{symbol} open rejected: {reason}"
                self._write_exchange_trace(trace_payload)
                logger.debug(f"CFD open rejected {symbol}: {reason}")
                return None

            deal_ref = result.get("dealReference", "")
            deal_id  = result.get("dealId", deal_ref) or deal_ref
            epic     = ticker.get("epic", symbol)
            fill_price = entry_price  # Estimate; confirm_order may refine
            confirmed_ok = False

            # Attempt to confirm fill price from Capital.com confirmation
            if deal_ref:
                try:
                    conf = self.client.confirm_order(deal_ref)
                    trace_payload["confirm_response"] = dict(conf) if isinstance(conf, dict) else conf
                    deal_status = str(conf.get("dealStatus") or "").upper()
                    reject_reason = str(conf.get("rejectReason") or conf.get("reason") or "").strip()
                    confirm_status = str(conf.get("status") or "").upper()
                    if reject_reason or deal_status == "REJECTED" or confirm_status == "DELETED":
                        self._latest_order_error = f"{symbol} rejected by Capital: {reject_reason or deal_status or confirm_status}"
                        trace_payload["validated"] = False
                        trace_payload["final_error"] = self._latest_order_error
                        self._write_exchange_trace(trace_payload)
                        logger.warning("CFD open rejected by Capital for %s: %s", symbol, reject_reason or deal_status or confirm_status)
                        return None
                    if not conf.get("error") and not conf.get("reason"):
                        deal_id    = conf.get("dealId", deal_id) or deal_id
                        fill_price = float(conf.get("level", fill_price) or fill_price)
                        effective_tp_pct = self._effective_tp_pct(fill_price, size, cfg)
                        if direction == "BUY":
                            tp_price = fill_price * (1 + effective_tp_pct / 100)
                            sl_price = fill_price * (1 - cfg["sl_pct"] / 100)
                        else:
                            tp_price = fill_price * (1 - effective_tp_pct / 100)
                            sl_price = fill_price * (1 + cfg["sl_pct"] / 100)
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
                    if raw_deal_id and raw_deal_id not in known_deal_ids and raw_symbol == symbol and raw_direction == direction:
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
                f"CAPITAL OPEN {symbol} {direction} deal={pos.deal_id} size={size} entry={pos.entry_price:.5g} "
                f"tp={pos.tp_price:.5g} sl={pos.sl_price:.5g}"
            )

            print(
                f"  CAPITAL CFD OPEN:  {symbol:12} [{cfg['class'].upper():9}] "
                f"{direction} {size} @ {pos.entry_price:.5g} | "
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
            "deal_id":          pos.deal_id,
            "asset_class":      pos.asset_class,
            "direction":        pos.direction,
            "entry_price":      pos.entry_price,
            "exit_price":       cp,
            "size":             pos.size,
            "net_pnl":          pnl_gbp,
            "net_pnl_currency": "GBP",
            "reason":           reason,
            "age_secs":         pos.age_secs,
            "closed_at":        datetime.now().isoformat(),
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

    def _position_pnl_gbp(self, pos: CFDPosition) -> float:
        cp = pos.current_price if pos.current_price > 0 else pos.entry_price
        if pos.entry_price <= 0 or cp <= 0:
            return 0.0
        if pos.direction == "BUY":
            pnl_pct = (cp - pos.entry_price) / pos.entry_price
        else:
            pnl_pct = (pos.entry_price - cp) / pos.entry_price
        return pnl_pct * pos.entry_price * pos.size

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
            pnl_gbp = self._position_pnl_gbp(pos)

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

            if close_reason and CFD_FLAGS["profit_only_closes"] and pnl_gbp <= 0:
                self._latest_monitor_line = (
                    f"CAPITAL HOLD {pos.symbol} reason={close_reason} pnl={pnl_gbp:+.4f}GBP "
                    f"mode=profit_only"
                )
                close_reason = None

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
        should_scan = (now - self._last_scan >= CFD_CONFIG["scan_interval_secs"]) or bool(closed_this_tick)
        if should_scan:
            self._last_scan = now

            if len(self.positions) < int(CFD_CONFIG["max_positions"]):
                # Quick Seer + Lyra gate before committing capital
                if self._quad_gate():
                    self._find_best_opportunity()
                    opened_directions = {str(pos.direction or "").upper() for pos in self.positions}
                    for sym, cfg, ticker in self._ranked_opportunities():
                        direction = str(cfg.get("direction", "BUY") or "BUY").upper()
                        if direction in opened_directions:
                            continue
                        preflight = self._capital_preflight(sym, float(cfg.get("size", 0.0) or 0.0), ticker, cfg)
                        working_cfg = dict(cfg)
                        if (not preflight.get("ok")) and "below Capital minimum" in str(preflight.get("reason") or ""):
                            adjusted_cfg = self._sized_cfg_from_preflight(cfg, preflight)
                            if adjusted_cfg is not None:
                                adjusted_preflight = self._capital_preflight(
                                    sym,
                                    float(adjusted_cfg.get("size", 0.0) or 0.0),
                                    ticker,
                                    adjusted_cfg,
                                )
                                if adjusted_preflight.get("ok"):
                                    working_cfg = adjusted_cfg
                                    preflight = adjusted_preflight

                        self._latest_target_snapshot = {
                            **dict(self._latest_target_snapshot),
                            "symbol": sym,
                            "direction": str(working_cfg.get("direction", "BUY") or "BUY").upper(),
                            "asset_class": working_cfg.get("class", cfg.get("class", "unknown")),
                            "size": float(working_cfg.get("size", 0.0) or 0.0),
                            "preflight_reason": str(preflight.get("reason") or ""),
                            "market_status": str(preflight.get("market_status") or ""),
                            "minimum_deal_size": float(preflight.get("minimum_deal_size", 0.0) or 0.0),
                            "available_balance": float(preflight.get("available_balance", 0.0) or 0.0),
                        }

                        if not preflight.get("ok"):
                            self._latest_order_error = f"{sym} preflight failed: {preflight.get('reason') or 'unknown'}"
                            logger.warning("CFD candidate skipped for %s: %s", sym, preflight.get("reason") or "unknown")
                            continue

                        if self._open_position(sym, working_cfg, ticker) is not None:
                            opened_directions.add(direction)
                            if opened_directions >= {"BUY", "SELL"} or len(self.positions) >= int(CFD_CONFIG["max_positions"]):
                                break
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
                f"  Target: {target.get('symbol', '?')} {target.get('direction', '?')} [{target.get('asset_class', '?')}] "
                f"score={float(target.get('score', 0.0) or 0.0):.3f} "
                f"chg={float(target.get('change_pct', 0.0) or 0.0):+.3f}% "
                f"goal=£{float(target.get('profit_target_gbp', CAPITAL_MIN_PROFIT_GBP) or CAPITAL_MIN_PROFIT_GBP):.2f}"
            )
            if "expected_net_profit" in target:
                lines.append(
                    f"    HFT: net=£{float(target.get('expected_net_profit', 0.0) or 0.0):+.4f} "
                    f"cost=£{float(target.get('round_trip_cost', 0.0) or 0.0):.4f} "
                    f"coh={float(target.get('brain_coherence', 0.0) or 0.0):.3f}"
                )
        if self._latest_candidate_snapshot:
            lines.append("  Top 7 candidates:")
            for idx, candidate in enumerate(self._latest_candidate_snapshot[:7], start=1):
                lines.append(
                    f"    #{idx} {candidate.get('symbol', '?')} {candidate.get('direction', '?')} [{candidate.get('asset_class', '?')}] "
                    f"score={float(candidate.get('score', 0.0) or 0.0):.3f} "
                    f"chg={float(candidate.get('change_pct', 0.0) or 0.0):+.3f}% "
                    f"spr={float(candidate.get('spread_pct', 0.0) or 0.0):.3f}% "
                    f"net=£{float(candidate.get('expected_net_profit', 0.0) or 0.0):+.4f} "
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
                    "deal_id": pos.deal_id,
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
