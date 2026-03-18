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
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

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
    "quad_gate_ttl":      30.0,  # Cache Seer/Lyra gate results for N secs
}


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

        # Timing
        self._last_scan:    float = 0.0
        self._last_monitor: float = 0.0

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

        for symbol, cfg in CAPITAL_UNIVERSE.items():
            if symbol in already_held:
                continue
            ticker = self._get_price(symbol)
            if not ticker:
                continue
            score = self._score_symbol(symbol, cfg, ticker)
            if score > best_score:
                best_score = score
                best = (symbol, cfg, ticker)

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
        tp_price = ask * (1 + cfg["tp_pct"] / 100)
        sl_price = ask * (1 - cfg["sl_pct"] / 100)

        try:
            result = self.client.place_market_order(symbol, "BUY", size)
            if result.get("rejected") or result.get("error"):
                reason = result.get("reason") or result.get("error", "unknown")
                logger.debug(f"CFD open rejected {symbol}: {reason}")
                return None

            deal_ref = result.get("dealReference", "")
            deal_id  = result.get("dealId", deal_ref) or deal_ref
            epic     = ticker.get("epic", symbol)
            fill_price = ask  # Estimate; confirm_order may refine

            # Attempt to confirm fill price from Capital.com confirmation
            if deal_ref:
                try:
                    conf = self.client.confirm_order(deal_ref)
                    deal_id    = conf.get("dealId", deal_id) or deal_id
                    fill_price = float(conf.get("level", fill_price) or fill_price)
                    tp_price   = fill_price * (1 + cfg["tp_pct"] / 100)
                    sl_price   = fill_price * (1 - cfg["sl_pct"] / 100)
                except Exception:
                    pass

            pos = CFDPosition(
                symbol=symbol,
                deal_id=deal_id or deal_ref,
                epic=epic,
                direction="BUY",
                size=size,
                entry_price=fill_price,
                tp_price=tp_price,
                sl_price=sl_price,
                asset_class=cfg["class"],
                current_price=fill_price,
            )
            self.positions.append(pos)
            self.stats["trades_opened"] += 1

            print(
                f"  CAPITAL CFD OPEN:  {symbol:12} [{cfg['class'].upper():9}] "
                f"BUY {size} @ {fill_price:.5g} | "
                f"TP:{tp_price:.5g}  SL:{sl_price:.5g}"
            )
            return pos

        except Exception as _e:
            logger.debug(f"CFD open exception {symbol}: {_e}")
            return None

    def _close_position(self, pos: CFDPosition, reason: str) -> dict:
        """
        Close a CFD position via Capital.com DELETE /positions/{dealId}.
        Falls back to a reverse market order if DELETE fails.
        Returns a closed-trade record compatible with orca session_stats.
        """
        pnl_gbp = 0.0

        if self.client and pos.deal_id:
            try:
                result = self.client.close_position(pos.deal_id)
                if not result.get("success"):
                    # Fallback: reverse market order to flatten the position
                    opposite = "SELL" if pos.direction == "BUY" else "BUY"
                    self.client.place_market_order(pos.symbol, opposite, pos.size)
            except Exception as _e:
                logger.debug(f"CFD close error {pos.symbol}: {_e}")

        # Estimate PnL from tracked prices
        cp = pos.current_price if pos.current_price > 0 else pos.entry_price
        if pos.entry_price > 0 and cp > 0:
            if pos.direction == "BUY":
                pnl_pct = (cp - pos.entry_price) / pos.entry_price
            else:
                pnl_pct = (pos.entry_price - cp) / pos.entry_price
            pnl_gbp = pnl_pct * pos.entry_price * pos.size

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

        return {
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

    def _update_position_prices(self) -> None:
        """Refresh current_price on all tracked positions from the price cache."""
        for pos in self.positions:
            ticker = self._get_price(pos.symbol)
            if ticker:
                cp = float(ticker.get("price") or 0)
                if cp > 0:
                    pos.current_price = cp

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

        return closed_this_tick

    # ── STATUS ─────────────────────────────────────────────────────────────────
    def status_lines(self) -> List[str]:
        """Return human-readable status lines for orca dashboard / print_status."""
        w = int(self.stats["winning_trades"])
        l = int(self.stats["losing_trades"])
        c = int(self.stats["trades_closed"])
        pnl = self.stats["total_pnl_gbp"]
        gate = "ARMED" if HAS_QUAD_GATES else "open"

        lines: List[str] = [
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
        for pos in self.positions:
            lines.append(pos.one_line())
        return lines

    def recommendations_summary(self) -> str:
        """One-liner for quick console display."""
        return (
            f"Capital CFD: {len(self.positions)}/{int(CFD_CONFIG['max_positions'])} pos | "
            f"PnL:{self.stats['total_pnl_gbp']:+.2f} GBP"
        )
