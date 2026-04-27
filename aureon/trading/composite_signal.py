"""
composite_signal.py — Multi-factor opportunity scorer for live trading.

The organism does not trade on noise. It waits for conviction:
  momentum  +  volatility  +  volume surge  +  historical pattern alignment

Returns a 0.0–1.0 signal score. Only trade when score ≥ threshold.
The survival instinct lowers the threshold when capital is declining — the
organism must eat to survive.
"""
from __future__ import annotations

import logging
import math
import sqlite3
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger("aureon.trading.composite_signal")

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _get_db_path() -> Optional[Path]:
    p = _REPO_ROOT / "state" / "aureon_global_history.sqlite"
    return p if p.exists() else None


# ─── Historical bar stats ──────────────────────────────────────────────────────

_bar_cache: dict = {}
_bar_cache_at: float = 0.0
_BAR_CACHE_TTL = 120.0  # refresh every 2 min


def _load_bar_stats() -> dict:
    """Load avg volume and ATR per symbol from market_bars (last 20 bars)."""
    global _bar_cache, _bar_cache_at
    now = time.time()
    if now - _bar_cache_at < _BAR_CACHE_TTL:
        return _bar_cache
    db = _get_db_path()
    if not db:
        return {}
    try:
        conn = sqlite3.connect(str(db), timeout=2, check_same_thread=False)
        rows = conn.execute("""
            SELECT symbol,
                   AVG(volume)              AS avg_vol,
                   AVG(price_high - price_low) AS avg_atr,
                   MAX(ingested_at_ms)      AS freshness
            FROM (
                SELECT symbol, volume, price_high, price_low, ingested_at_ms,
                       ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY time_start_ms DESC) AS rn
                FROM market_bars
            )
            WHERE rn <= 20
            GROUP BY symbol
        """).fetchall()
        conn.close()
        stats = {}
        for r in rows:
            sym = str(r[0] or "").upper()
            if sym:
                stats[sym] = {
                    "avg_vol": float(r[1] or 0),
                    "avg_atr": float(r[2] or 0),
                    "freshness_ms": int(r[3] or 0),
                }
        _bar_cache = stats
        _bar_cache_at = now
        return stats
    except Exception as e:
        logger.debug("composite_signal bar stats: %s", e)
        return {}


def _map_symbol(capital_epic: str) -> str:
    """Map Capital.com epic → market_bars symbol."""
    mapping = {
        "EURUSD": "EURUSD", "GBPUSD": "GBPUSD", "USDJPY": "USDJPY",
        "AUDUSD": "AUDUSD", "USDCAD": "USDCAD", "EURGBP": "EURGBP",
        "GOLD": "BTCUSD",  # no GOLD in bars — use BTC volatility as market proxy
        "US500": "SPY", "US30": "SPY", "UK100": "SPY",
        "AAPL": "AAPL", "TSLA": "TSLA", "NVDA": "NVDA",
        "AMZN": "AMZN", "MSFT": "MSFT",
    }
    return mapping.get(capital_epic.upper(), "")


# ─── Core scoring ──────────────────────────────────────────────────────────────

def score(
    epic: str,
    change_pct: float,
    bid: float,
    ask: float,
    high: float,
    low: float,
    price: float,
    current_volume: float = 0.0,
) -> tuple[float, dict]:
    """
    Compute composite signal score (0.0–1.0) + breakdown dict.

    Factors:
      1. Momentum      (30%) — directional move size
      2. Volatility    (30%) — daily range breadth
      3. Alignment     (20%) — momentum moving WITH the day's range
      4. Volume surge  (20%) — current vol vs historical avg (if available)

    Requires score ≥ 0.45 to be considered tradeable.
    """
    breakdown = {}
    total = 0.0

    # ── 1. Momentum ───────────────────────────────────────────────────────
    # Normalize: 0.3% move = full score. Forex typical daily 0.1–0.4%.
    mom = min(abs(change_pct) / 0.30, 1.0)
    breakdown["momentum"] = round(mom, 3)
    total += mom * 0.30

    # ── 2. Volatility (daily range) ───────────────────────────────────────
    vol_score = 0.0
    if price > 0 and high > low:
        range_pct = (high - low) / price * 100.0
        # 0.3% daily range = full score for forex; higher for commodities/indices
        vol_score = min(range_pct / 0.30, 1.0)
    breakdown["volatility"] = round(vol_score, 3)
    total += vol_score * 0.30

    # ── 3. Alignment: momentum direction matches range size ───────────────
    align_score = 0.0
    if price > 0 and high > low:
        range_pct = (high - low) / price * 100.0
        if range_pct > 0.001:
            align_score = min(abs(change_pct) / range_pct, 1.0)
    breakdown["alignment"] = round(align_score, 3)
    total += align_score * 0.20

    # ── 4. Volume surge from historical bars ─────────────────────────────
    vol_surge = 0.5  # neutral default when no data
    bar_sym = _map_symbol(epic)
    if bar_sym:
        stats = _load_bar_stats()
        hist = stats.get(bar_sym, {})
        avg_v = hist.get("avg_vol", 0.0)
        if avg_v > 0 and current_volume > 0:
            ratio = current_volume / avg_v
            # 2x average volume = full score, 0.5x = half score
            vol_surge = min(ratio / 2.0, 1.0)
            breakdown["volume_ratio"] = round(ratio, 2)
    breakdown["volume_surge"] = round(vol_surge, 3)
    total += vol_surge * 0.20

    # ── Spread penalty: wide spreads reduce score ─────────────────────────
    if price > 0 and ask > bid > 0:
        spread_pct = (ask - bid) / price * 100.0
        if spread_pct > 0.05:  # above 0.05% spread → penalise
            penalty = min((spread_pct - 0.05) / 0.2, 0.3)
            total = max(0.0, total - penalty)
            breakdown["spread_penalty"] = round(penalty, 3)

    total = min(total, 1.0)
    breakdown["composite"] = round(total, 3)
    return total, breakdown


# ─── Survival instinct ────────────────────────────────────────────────────────

class SurvivalInstinct:
    """
    The organism monitors its own capital trajectory.
    If capital is shrinking: SURVIVAL mode — lower threshold, hunt harder.
    If capital is stable/growing: HUNT mode — selective, high-conviction only.
    """

    SURVIVAL_THRESHOLD = 0.38   # Desperate — take any real opportunity
    HUNT_THRESHOLD     = 0.48   # Normal — wait for clear signals
    GROW_THRESHOLD     = 0.52   # Growing — only high-conviction entries

    def __init__(self):
        self._equity_history: list[float] = []
        self._last_update: float = 0.0
        self.mode: str = "HUNT"
        self.threshold: float = self.HUNT_THRESHOLD

    def update(self, current_equity_gbp: float) -> None:
        now = time.time()
        if now - self._last_update < 30.0:
            return
        self._last_update = now
        if current_equity_gbp <= 0:
            return
        self._equity_history.append(current_equity_gbp)
        if len(self._equity_history) > 10:
            self._equity_history = self._equity_history[-10:]

        if len(self._equity_history) >= 3:
            recent = self._equity_history[-3:]
            slope = (recent[-1] - recent[0]) / max(recent[0], 0.01)
            if slope < -0.02:  # down >2% over last 3 readings
                self.mode = "SURVIVAL"
                self.threshold = self.SURVIVAL_THRESHOLD
            elif slope > 0.02:  # up >2%
                self.mode = "GROW"
                self.threshold = self.GROW_THRESHOLD
            else:
                self.mode = "HUNT"
                self.threshold = self.HUNT_THRESHOLD

        logger.debug("SurvivalInstinct: mode=%s threshold=%.2f equity=£%.2f",
                     self.mode, self.threshold, current_equity_gbp)

    def should_trade(self, composite_score: float) -> bool:
        return composite_score >= self.threshold

    def status(self) -> dict:
        return {
            "mode": self.mode,
            "threshold": self.threshold,
            "equity_history": list(self._equity_history[-5:]),
        }


# Singleton
_survival = SurvivalInstinct()


def get_survival_instinct() -> SurvivalInstinct:
    return _survival
