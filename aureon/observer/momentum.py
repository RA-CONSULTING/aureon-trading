"""Recency-weighted momentum tracker over the live data sources.

The HarmonicObserver describes the field state. The WavePredictor
forecasts the next tick. This module sits between them and the bus —
it watches every data source the daemon pulls (Schumann amplitude, Kp
index, GDELT article count, BTC price ticks if wired, etc.) and
maintains multi-horizon EMA traces so the operator can see momentum
*forming* in real time across multiple timeframes simultaneously.

Why this exists separately from the observer's rocks: rocks are
*persistent anchor features* in the Λ field — they require enough
samples to characterise. Momentum is the *rate of change in the
underlying source values themselves*, computable from a single new
tick once two EMAs are populated. Different question, different
answer, different actionability.

What it produces:

    MomentumState dataclass per source — short/mid/long EMA values,
    crossovers, and a signed momentum_score in [-1, 1] derived from
    EMA spread relative to the source's recent volatility.

    momentum_predict_fn — adapter that registers as the bus predictor
    "momentum_tracker" and votes BULLISH/BEARISH based on which
    sources are accelerating in which direction.

Recency weighting:

    Three exponential moving averages per source, with halflife in
    samples:
        short  → halflife 5    (immediate momentum)
        mid    → halflife 30   (session-scale)
        long   → halflife 240  (regime-scale)

    Crossovers (short crosses mid, mid crosses long) are momentum
    confirmation events — the operator sees them on the live feed
    immediately, and the bus predictor uses them as primary signal.

    The "recent signals get at the relevant timeframe" intent: the
    short EMA is what acts on the latest tick; the mid EMA is what
    acts on the last hour or so; the long EMA is what acts on the
    overnight/multi-day regime. All three are exposed; the predictor
    fuses them with recency weights (0.5, 0.3, 0.2 by default).
"""

from __future__ import annotations

import logging
import math
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Deque, Dict, List, Optional

logger = logging.getLogger(__name__)


# ─── horizon halflives (in samples) ────────────────────────────────

SHORT_HALFLIFE = 5
MID_HALFLIFE = 30
LONG_HALFLIFE = 240

# Recency weights when fusing the three horizons into one momentum_score.
WEIGHT_SHORT = 0.50
WEIGHT_MID = 0.30
WEIGHT_LONG = 0.20

# Direction threshold for the bus predictor.
DIRECTION_THRESHOLD = 0.10


def _halflife_alpha(halflife: float) -> float:
    """Return the EMA smoothing constant for a given halflife in samples."""
    if halflife <= 0:
        return 1.0
    return 1.0 - math.pow(0.5, 1.0 / halflife)


_ALPHA_SHORT = _halflife_alpha(SHORT_HALFLIFE)
_ALPHA_MID = _halflife_alpha(MID_HALFLIFE)
_ALPHA_LONG = _halflife_alpha(LONG_HALFLIFE)


# ─── per-source state ──────────────────────────────────────────────

@dataclass
class MomentumState:
    """Live momentum readout for one data source."""
    name: str
    n_ingested: int = 0
    last_value: Optional[float] = None
    last_ts: Optional[float] = None

    short_ema: Optional[float] = None
    mid_ema: Optional[float] = None
    long_ema: Optional[float] = None

    short_minus_mid: float = 0.0
    mid_minus_long: float = 0.0

    momentum_score: float = 0.0   # signed [-1, 1], recency-weighted
    direction: str = "NEUTRAL"
    confidence: float = 0.0       # how persistent recent crossovers are

    # Rolling tail for variance / direction-stability calc
    tail: Deque[float] = field(default_factory=lambda: deque(maxlen=64))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "n": self.n_ingested,
            "last_value": self.last_value,
            "last_ts": self.last_ts,
            "short_ema": self.short_ema,
            "mid_ema": self.mid_ema,
            "long_ema": self.long_ema,
            "short_minus_mid": round(self.short_minus_mid, 6),
            "mid_minus_long": round(self.mid_minus_long, 6),
            "momentum_score": round(self.momentum_score, 6),
            "direction": self.direction,
            "confidence": round(self.confidence, 4),
        }


# ─── tracker ───────────────────────────────────────────────────────

class MomentumTracker:
    """Multi-source, multi-horizon momentum.

    Thread-safe ingest; bus predictor reads ``current_state`` snapshots.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._sources: Dict[str, MomentumState] = {}
        self._n_ingested_total = 0
        self._started_at = time.time()

    def ingest(self, source: str, value: float, ts: Optional[float] = None) -> None:
        """Feed one (source, value) tick. EMAs update incrementally."""
        try:
            v = float(value)
        except (TypeError, ValueError):
            return
        if math.isnan(v) or math.isinf(v):
            return
        t = float(ts) if ts is not None else time.time()

        with self._lock:
            st = self._sources.get(source)
            if st is None:
                st = MomentumState(name=source)
                self._sources[source] = st

            # First sample seeds all three EMAs to the value (avoids the
            # spurious initial trend most EMA implementations suffer from).
            if st.short_ema is None:
                st.short_ema = v
                st.mid_ema = v
                st.long_ema = v
            else:
                st.short_ema = st.short_ema + _ALPHA_SHORT * (v - st.short_ema)
                st.mid_ema = st.mid_ema + _ALPHA_MID * (v - st.mid_ema)
                st.long_ema = st.long_ema + _ALPHA_LONG * (v - st.long_ema)

            st.last_value = v
            st.last_ts = t
            st.n_ingested += 1
            st.tail.append(v)
            self._n_ingested_total += 1

            # Crossovers — relative to current value to keep them scale-aware.
            scale = max(abs(v), 1e-9)
            st.short_minus_mid = (st.short_ema - st.mid_ema) / scale
            st.mid_minus_long = (st.mid_ema - st.long_ema) / scale

            # Momentum score: recency-weighted blend of the two crossovers
            # plus a momentum-of-momentum from the last-tick delta.
            last_delta = (v - (st.tail[-2] if len(st.tail) >= 2 else v)) / scale
            raw = (
                WEIGHT_SHORT * st.short_minus_mid * 10.0
                + WEIGHT_MID * st.mid_minus_long * 10.0
                + WEIGHT_LONG * last_delta * 5.0
            )
            st.momentum_score = max(-1.0, min(1.0, raw))

            if st.momentum_score > DIRECTION_THRESHOLD:
                st.direction = "BULLISH"
            elif st.momentum_score < -DIRECTION_THRESHOLD:
                st.direction = "BEARISH"
            else:
                st.direction = "NEUTRAL"

            # Confidence — proxy for "is this momentum persistent?". Low
            # variance in the recent tail = high confidence; rapid sign
            # flips kill confidence.
            if len(st.tail) >= 4:
                tl = list(st.tail)
                mu = sum(tl) / len(tl)
                var = sum((x - mu) ** 2 for x in tl) / len(tl)
                cov = math.sqrt(var) / max(abs(mu), 1e-9)
                # Lower coefficient-of-variation → higher confidence.
                stability = 1.0 / (1.0 + cov * 5.0)
                # Sign-stability: of the last 5 deltas, how many agree
                # with the current direction?
                deltas = [tl[i] - tl[i - 1] for i in range(1, len(tl))][-5:]
                if deltas:
                    same_sign = sum(
                        1 for d in deltas
                        if (d > 0 and st.direction == "BULLISH")
                        or (d < 0 and st.direction == "BEARISH")
                        or (abs(d) < 1e-12 and st.direction == "NEUTRAL")
                    )
                    sign_consistency = same_sign / len(deltas)
                else:
                    sign_consistency = 0.5
                st.confidence = max(0.0, min(1.0, 0.5 * stability + 0.5 * sign_consistency))
            else:
                st.confidence = 0.0

    # ─── public read API ──────────────────────────────────────────

    def current_state(self, source: Optional[str] = None) -> Dict[str, Any]:
        with self._lock:
            if source is not None:
                st = self._sources.get(source)
                return st.to_dict() if st else {}
            return {n: st.to_dict() for n, st in self._sources.items()}

    def aggregate(self) -> Dict[str, Any]:
        """Fuse all sources into one signed-strength momentum reading."""
        with self._lock:
            if not self._sources:
                return {
                    "direction": "NEUTRAL",
                    "confidence": 0.0,
                    "strength": 0.0,
                    "n_sources": 0,
                    "n_bullish": 0,
                    "n_bearish": 0,
                    "n_neutral": 0,
                }
            n_bull = sum(1 for s in self._sources.values() if s.direction == "BULLISH")
            n_bear = sum(1 for s in self._sources.values() if s.direction == "BEARISH")
            n_neut = sum(1 for s in self._sources.values() if s.direction == "NEUTRAL")
            # Confidence-weighted strength average.
            total_weight = 0.0
            weighted = 0.0
            total_conf = 0.0
            for s in self._sources.values():
                w = max(0.0, s.confidence)
                weighted += s.momentum_score * w
                total_weight += w
                total_conf += s.confidence
            strength = (weighted / total_weight) if total_weight > 0 else 0.0
            avg_conf = total_conf / len(self._sources)
            if strength > DIRECTION_THRESHOLD:
                direction = "BULLISH"
            elif strength < -DIRECTION_THRESHOLD:
                direction = "BEARISH"
            else:
                direction = "NEUTRAL"
            return {
                "direction": direction,
                "confidence": round(avg_conf, 4),
                "strength": round(strength, 6),
                "n_sources": len(self._sources),
                "n_bullish": n_bull,
                "n_bearish": n_bear,
                "n_neutral": n_neut,
            }

    @property
    def n_sources(self) -> int:
        with self._lock:
            return len(self._sources)


# ─── singleton + auto-wire (mirrors observer + wave_predictor) ─────

_singleton: Optional[MomentumTracker] = None
_singleton_lock = threading.Lock()


def get_momentum_tracker() -> Optional[MomentumTracker]:
    return _singleton


def set_momentum_tracker(t: MomentumTracker) -> None:
    global _singleton
    with _singleton_lock:
        _singleton = t


_orig_init = MomentumTracker.__init__


def _init_with_singleton(self, *a, **kw):
    _orig_init(self, *a, **kw)
    global _singleton
    with _singleton_lock:
        if _singleton is None:
            _singleton = self


MomentumTracker.__init__ = _init_with_singleton  # type: ignore[assignment]


# ─── PredictionBus adapter ─────────────────────────────────────────

PREDICTOR_NAME = "momentum_tracker"
PREDICTOR_WEIGHT = 1.0


def _build_unified_signal(tracker: MomentumTracker, symbol: str):
    from aureon.autonomous.aureon_autonomy_hub import UnifiedSignal
    agg = tracker.aggregate()
    return UnifiedSignal(
        source=PREDICTOR_NAME,
        signal_type="prediction",
        symbol=symbol,
        direction=agg["direction"],
        confidence=float(agg["confidence"]),
        strength=float(agg["strength"]),
        payload={
            "n_sources": agg["n_sources"],
            "n_bullish": agg["n_bullish"],
            "n_bearish": agg["n_bearish"],
            "n_neutral": agg["n_neutral"],
            "per_source": tracker.current_state(),
        },
        timestamp=time.time(),
    )


def _neutral(symbol: str, reason: str):
    from aureon.autonomous.aureon_autonomy_hub import UnifiedSignal
    return UnifiedSignal(
        source=PREDICTOR_NAME,
        signal_type="prediction",
        symbol=symbol,
        direction="NEUTRAL",
        confidence=0.0,
        strength=0.0,
        payload={"reason": reason},
        timestamp=time.time(),
    )


def momentum_predict_fn(_data_signals=None, symbol: str = "BTCUSD"):
    t = get_momentum_tracker()
    if t is None or t.n_sources == 0:
        return _neutral(symbol, "momentum_tracker_no_data")
    try:
        return _build_unified_signal(t, symbol)
    except Exception as exc:
        logger.debug("momentum_predict_fn failed: %s", exc)
        return _neutral(symbol, f"predict_error:{type(exc).__name__}")


def auto_wire_prediction_bus(prediction_bus) -> bool:
    if prediction_bus is None:
        return False
    if getattr(prediction_bus, "_momentum_tracker_wired", False):
        return True
    try:
        prediction_bus.register_predictor(PREDICTOR_NAME, momentum_predict_fn)
        setattr(prediction_bus, "_momentum_tracker_wired", True)
        logger.info("auto-wired momentum_tracker onto PredictionBus")
        return True
    except Exception as exc:
        logger.debug("momentum auto-wire failed: %s", exc)
        return False
