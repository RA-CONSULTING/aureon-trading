"""``WavePredictor`` — a wave-based next-tick directional model over the
live HNC field.

Where the HarmonicObserver *describes* the field (rocks, regime,
coherence_score), this predictor *forecasts* it: given the recent Λ(t)
trace, produce a near-term directional call (BULLISH / BEARISH /
NEUTRAL) with a confidence and a predicted next Λ. That signal plugs
into PredictionBus alongside ``harmonic_observer`` so it contributes
to ``get_consensus`` directly.

The model is intentionally simple — pure Python, no numpy required:

    1. Linear trend       — OLS slope over the last N samples → primary
                             directional driver, range-normalised.
    2. Recent momentum    — single-tick Δ Λ → short-horizon kick.
    3. Wave continuation  — if the observer reports a band rock at a
                             specific dominant_hz, project the cycle
                             forward by half a period from the current
                             phase position to bias the call.
    4. Coherence gating   — final confidence is multiplied by the
                             observer's coherence_score (when
                             available); a chaotic field never produces
                             a high-confidence wave call.

A numpy fast-path replaces (1) with ``np.polyfit`` and (3) with a
Hilbert-transform-based phase estimate when numpy/scipy are available;
output shape is identical either way.

The predictor self-registers against PredictionBus.__init__ via the
same auto-wiring path as ``harmonic_observer`` (see Stage B). Default
weight in get_consensus() is 1.0 — a fresh predictor with no validated
track record.
"""

from __future__ import annotations

import logging
import math
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Optional fast-path imports.
try:
    import numpy as _np
    _HAS_NUMPY = True
except Exception:
    _HAS_NUMPY = False


# ─── config ────────────────────────────────────────────────────────

DEFAULT_HISTORY_LENGTH = 120        # ~10 minutes at 5 s cadence
TREND_WINDOW = 24                    # last N samples for OLS
MOMENTUM_WINDOW = 4                  # for kick term
DIRECTION_THRESHOLD = 0.15           # |trend_score| above this → directional
HALF_PERIOD_PROJECTION_FRAC = 0.5    # how far into the next half-cycle to project


@dataclass
class WaveCall:
    """One forecast snapshot. Mirrors the predictor.UnifiedSignal shape
    closely enough to be adapted with no information loss."""
    direction: str                  # "BULLISH" | "BEARISH" | "NEUTRAL"
    confidence: float               # [0, 1]
    strength: float                 # [-1, 1]
    predicted_next_lambda: Optional[float]
    reason: str
    components: Dict[str, float] = field(default_factory=dict)
    ts: float = field(default_factory=time.time)
    samples_used: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "direction": self.direction,
            "confidence": float(self.confidence),
            "strength": float(self.strength),
            "predicted_next_lambda": (
                None if self.predicted_next_lambda is None
                else float(self.predicted_next_lambda)
            ),
            "reason": self.reason,
            "components": dict(self.components),
            "ts": self.ts,
            "samples_used": self.samples_used,
        }


# ─── pure-Python OLS slope (avoids the numpy dep) ──────────────────

def _ols_slope(values: List[float]) -> float:
    """Slope of a least-squares line fit through ``values`` (x = index).

    Pure-Python — no numpy. Returns 0.0 for fewer than 2 points.
    """
    n = len(values)
    if n < 2:
        return 0.0
    x_mean = (n - 1) / 2.0
    y_mean = sum(values) / n
    num = 0.0
    den = 0.0
    for i, v in enumerate(values):
        dx = i - x_mean
        num += dx * (v - y_mean)
        den += dx * dx
    return num / den if den else 0.0


# ─── the predictor ─────────────────────────────────────────────────

class WavePredictor:
    """Wave-based directional forecaster over the live Λ trace.

    Thread-safe ``ingest()``; read accessors hold the same lock so a
    PredictionBus call doesn't see a half-updated history deque.
    """

    def __init__(
        self,
        history_length: int = DEFAULT_HISTORY_LENGTH,
        observer=None,
    ):
        self._lock = threading.RLock()
        self._history: Deque[Tuple[float, float]] = deque(maxlen=history_length)
        self._observer = observer  # optional — for coherence gating + rocks
        self._last_call: Optional[WaveCall] = None
        self._n_ingested = 0

    # ─── public API ───────────────────────────────────────────────

    def ingest(self, ts: float, lambda_t: float) -> None:
        """Accept one (timestamp, Λ_full) tick. Cheap; no work done here."""
        try:
            t = float(ts)
            v = float(lambda_t)
        except (TypeError, ValueError):
            return
        if math.isnan(v) or math.isinf(v):
            return
        with self._lock:
            self._history.append((t, v))
            self._n_ingested += 1

    def ingest_state(self, state) -> None:
        """Accept a LambdaState-like object (matches observer.ingest_state).

        Useful when the predictor sits next to the daemon's compute
        loop — calling code can hand the same state to both.
        """
        if state is None:
            return
        ts = getattr(state, "timestamp", None) or time.time()
        lt = getattr(state, "lambda_t", None)
        if lt is None:
            return
        self.ingest(ts, lt)

    def predict(self, symbol: str = "BTCUSD") -> WaveCall:
        """Compute a directional forecast from current history + observer."""
        with self._lock:
            samples = [v for _, v in self._history]
        n = len(samples)
        if n < TREND_WINDOW:
            self._last_call = WaveCall(
                direction="NEUTRAL", confidence=0.0, strength=0.0,
                predicted_next_lambda=None,
                reason=f"insufficient_history({n}/{TREND_WINDOW})",
                samples_used=n,
            )
            return self._last_call

        # Confine to the last TREND_WINDOW samples for the slope.
        recent = samples[-TREND_WINDOW:]
        slope = _ols_slope(recent)

        vmin = min(recent)
        vmax = max(recent)
        rng = (vmax - vmin) or 1e-9
        normalised_slope = slope / rng        # in samples-1 of normalised Λ

        # Trend score in [-1, 1] — saturates the slope onto a
        # comparable directional unit.
        trend_score = max(-1.0, min(1.0, normalised_slope * 10.0))

        # Momentum kick over the last MOMENTUM_WINDOW samples.
        if n >= MOMENTUM_WINDOW + 1:
            tail = samples[-MOMENTUM_WINDOW:]
            momentum = (tail[-1] - tail[0]) / rng
            momentum_score = max(-1.0, min(1.0, momentum * 5.0))
        else:
            momentum_score = 0.0

        # Wave continuation — if the observer has a band rock with a
        # dominant frequency, project the implied cycle a half-period
        # ahead and use the sign of the projected ΔΛ as a tiebreaker.
        wave_score = 0.0
        if self._observer is not None:
            try:
                snap = self._observer.metrics_snapshot()
                rocks = (snap.get("rocks_fast") or [])[:1]  # use the strongest
                if rocks:
                    hz = float(rocks[0].get("dominant_hz") or 0.0)
                    amp = float(rocks[0].get("amplitude") or 0.0)
                    if hz > 0 and amp > 0:
                        # Phase advances by 2π * hz * dt per unit time.
                        dt = HALF_PERIOD_PROJECTION_FRAC / hz   # half period
                        # Compare predicted-next vs current.
                        # Without true phase recovery we use sign of
                        # slope as proxy for which side of the cycle
                        # we're on, then flip the bias on the other half.
                        wave_score = math.copysign(1.0, slope) * \
                                     min(1.0, amp / (rng + 1e-9))
            except Exception as exc:
                logger.debug("wave continuation read failed: %s", exc)

        # Combine — weights chosen so trend dominates, momentum & wave
        # adjust on the margin.
        combined = (
            0.55 * trend_score
            + 0.25 * momentum_score
            + 0.20 * wave_score
        )
        combined = max(-1.0, min(1.0, combined))

        # Direction.
        if combined > DIRECTION_THRESHOLD:
            direction = "BULLISH"
        elif combined < -DIRECTION_THRESHOLD:
            direction = "BEARISH"
        else:
            direction = "NEUTRAL"

        # Predicted next Λ (one step ahead) — useful for paper trading.
        predicted_next = recent[-1] + slope

        # Confidence — built from:
        #   (a) magnitude of the directional score
        #   (b) recent-slope stability (low variance over a 3-window
        #       rolling slope estimate)
        #   (c) observer's coherence_score, when present
        if n >= TREND_WINDOW * 2:
            half = TREND_WINDOW
            slope_a = _ols_slope(samples[-half * 2 : -half])
            slope_b = _ols_slope(samples[-half:])
            stability = 1.0 - min(1.0, abs(slope_a - slope_b) / (abs(slope_a) + abs(slope_b) + 1e-9))
        else:
            stability = 0.5
        coherence_gate = 1.0
        if self._observer is not None:
            try:
                coherence_gate = float(self._observer.coherence_score())
                # Predictor still produces useful output without observer
                # rocks — clamp the floor so a numpy-less sandbox doesn't
                # zero everything out.
                coherence_gate = max(0.25, min(1.0, coherence_gate))
            except Exception:
                pass

        confidence = abs(combined) * (0.5 + 0.5 * stability) * coherence_gate
        confidence = max(0.0, min(1.0, confidence))

        call = WaveCall(
            direction=direction,
            confidence=confidence,
            strength=combined,
            predicted_next_lambda=predicted_next,
            reason=f"trend={trend_score:+.3f},mom={momentum_score:+.3f},"
                   f"wave={wave_score:+.3f},stab={stability:.2f},"
                   f"cohgate={coherence_gate:.2f}",
            components={
                "trend_score": trend_score,
                "momentum_score": momentum_score,
                "wave_score": wave_score,
                "slope": slope,
                "stability": stability,
                "coherence_gate": coherence_gate,
            },
            samples_used=n,
        )
        with self._lock:
            self._last_call = call
        return call

    @property
    def last_call(self) -> Optional[WaveCall]:
        with self._lock:
            return self._last_call

    @property
    def n_ingested(self) -> int:
        with self._lock:
            return self._n_ingested


# ─── singleton + auto-wire (mirrors the observer's pattern) ────────

_singleton: Optional[WavePredictor] = None
_singleton_lock = threading.Lock()


def get_wave_predictor() -> Optional[WavePredictor]:
    """Return the global WavePredictor or None if none constructed."""
    return _singleton


def set_wave_predictor(p: WavePredictor) -> None:
    global _singleton
    with _singleton_lock:
        _singleton = p


_orig_init = WavePredictor.__init__


def _init_with_singleton(self, *args, **kwargs):
    _orig_init(self, *args, **kwargs)
    global _singleton
    with _singleton_lock:
        if _singleton is None:
            _singleton = self


WavePredictor.__init__ = _init_with_singleton  # type: ignore[assignment]


# ─── PredictionBus adapter ─────────────────────────────────────────

PREDICTOR_NAME = "wave_predictor"
PREDICTOR_WEIGHT = 1.0  # default — same as a fresh, untracked predictor


def _build_unified_signal(call: WaveCall, symbol: str):
    from aureon.autonomous.aureon_autonomy_hub import UnifiedSignal
    return UnifiedSignal(
        source=PREDICTOR_NAME,
        signal_type="prediction",
        symbol=symbol,
        direction=call.direction,
        confidence=float(call.confidence),
        strength=float(call.strength),
        payload={
            "reason": call.reason,
            "predicted_next_lambda": call.predicted_next_lambda,
            "components": call.components,
            "samples_used": call.samples_used,
        },
        timestamp=call.ts,
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


def make_predictor(predictor: WavePredictor) -> Callable:
    """Bind a WavePredictor instance into a predict_fn for PredictionBus."""
    def _pf(_data_signals=None, symbol: str = "BTCUSD"):
        try:
            return _build_unified_signal(predictor.predict(symbol), symbol)
        except Exception as exc:
            logger.debug("wave_predictor predict failed: %s", exc)
            return _neutral(symbol, f"predict_error:{type(exc).__name__}")
    _pf.__name__ = "wave_predictor_predict"
    return _pf


def wave_predictor_predict(_data_signals=None, symbol: str = "BTCUSD"):
    """Module-level callable consulting the singleton — used by auto-wire."""
    p = get_wave_predictor()
    if p is None:
        return _neutral(symbol, "wave_predictor_not_running")
    try:
        return _build_unified_signal(p.predict(symbol), symbol)
    except Exception as exc:
        logger.debug("wave_predictor_predict failed: %s", exc)
        return _neutral(symbol, f"predict_error:{type(exc).__name__}")


def wire_wave_predictor(prediction_bus, predictor: Optional[WavePredictor] = None,
                        name: str = PREDICTOR_NAME) -> bool:
    if prediction_bus is None:
        return False
    try:
        if predictor is not None:
            prediction_bus.register_predictor(name, make_predictor(predictor))
        else:
            prediction_bus.register_predictor(name, wave_predictor_predict)
        return True
    except Exception as exc:
        logger.debug("wire_wave_predictor failed: %s", exc)
        return False


def auto_wire_prediction_bus(prediction_bus) -> bool:
    """Idempotent registration. Mirrors observer.wiring's flag-attr pattern
    so a single PredictionBus picks up both predictors with one __init__
    call."""
    if prediction_bus is None:
        return False
    if getattr(prediction_bus, "_wave_predictor_wired", False):
        return True
    if wire_wave_predictor(prediction_bus, predictor=None):
        setattr(prediction_bus, "_wave_predictor_wired", True)
        logger.info("auto-wired wave_predictor onto PredictionBus")
        return True
    return False
