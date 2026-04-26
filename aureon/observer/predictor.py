"""PredictionBus adapter for the HarmonicObserver.

The observer is a *describer* — it documents recurring features in the
live Λ(t) field. The PredictionBus contract wants a *predictor* — one
that returns a ``UnifiedSignal`` with direction / confidence / strength.
This module is the thin translator between the two.

Two entry points:

    make_predictor(observer)
        Factory that returns a closure ``predict_fn(data_signals, symbol)``
        bound to a specific observer. Use this when you want explicit
        control over which observer the bus consults.

    harmonic_observer_predictor(data_signals, symbol)
        Module-level callable that consults the observer singleton (see
        ``aureon.observer.get_observer``). Used by the autonomous wiring:
        any ``PredictionBus`` that runs ``auto_wire_prediction_bus`` will
        register this function under the name ``harmonic_observer``.

Mapping observer state → ``UnifiedSignal``
------------------------------------------

The observer doesn't itself hold an opinion about market direction. We
derive direction from rock alignment with the HNC reference frequencies
documented in ``aureon_lambda_engine.FREQUENCIES``:

    7.83 / 14.3 / 20.8 / 33.8  Hz   Schumann modes — coherent / calm
    432 Hz                          Universal Harmony — bullish anchor
    528 Hz                          DNA repair / Love — bullish anchor
    963 Hz                          Crown — bullish anchor
    440 Hz                          Parasite (dissonant) — bearish anchor

A rock close to a bullish anchor adds positive strength weighted by its
z-score; a rock close to the parasite frequency adds negative strength.
Confidence is the observer's coherence score (rock stability × alignment
× sparsity). Empty / chaotic fields produce a NEUTRAL signal with
confidence ≈ 0 — explicitly "no opinion", not "do nothing".
"""

from __future__ import annotations

import logging
import time
from typing import Callable, Dict, Optional

from aureon.observer.harmonic_observer import HarmonicObserver
from aureon.observer.rock import Rock

logger = logging.getLogger(__name__)


# Reference frequencies for direction inference. Must stay in sync with
# aureon.core.aureon_lambda_engine.FREQUENCIES + LOVE_HZ etc., but we
# don't import that module here to keep the predictor decoupled.
_BULLISH_ANCHORS_HZ = (7.83, 14.3, 20.8, 33.8, 432.0, 528.0, 963.0)
_BEARISH_ANCHORS_HZ = (440.0,)
_HZ_MATCH_TOLERANCE = 0.10        # 10% — same tolerance the observer uses


def _nearest_anchor_signed_strength(rock: Rock) -> float:
    """+1 if close to a bullish anchor, -1 if close to bearish, 0 otherwise."""
    if rock.dominant_hz <= 0:
        return 0.0
    for hz in _BULLISH_ANCHORS_HZ:
        rel = abs(rock.dominant_hz - hz) / max(hz, 1e-9)
        if rel <= _HZ_MATCH_TOLERANCE:
            return 1.0
    for hz in _BEARISH_ANCHORS_HZ:
        rel = abs(rock.dominant_hz - hz) / max(hz, 1e-9)
        if rel <= _HZ_MATCH_TOLERANCE:
            return -1.0
    return 0.0


def _build_unified_signal(observer: HarmonicObserver, symbol: str):
    """Build a UnifiedSignal from the observer's current snapshot.

    Imported lazily so this module doesn't pull in autonomy_hub at
    import-time (avoids any future circular-import risk).
    """
    from aureon.autonomous.aureon_autonomy_hub import UnifiedSignal

    snap = observer.metrics_snapshot()
    rocks_dicts = list(snap.get("rocks_fast", [])) + list(snap.get("rocks_slow", []))

    # Weight each rock's anchor sign by its z_score; sum and normalise
    # against the total z-score mass to get a [-1, 1] strength.
    weighted = 0.0
    total_z = 0.0
    n_aligned = 0
    for rd in rocks_dicts:
        # rd is a serialised Rock dict. Re-hydrate just enough to inspect.
        hz = float(rd.get("dominant_hz", 0.0) or 0.0)
        z = float(rd.get("z_score", 0.0) or 0.0)
        if hz <= 0:
            continue
        sign = 0.0
        for h in _BULLISH_ANCHORS_HZ:
            if abs(hz - h) / max(h, 1e-9) <= _HZ_MATCH_TOLERANCE:
                sign = 1.0
                break
        if sign == 0.0:
            for h in _BEARISH_ANCHORS_HZ:
                if abs(hz - h) / max(h, 1e-9) <= _HZ_MATCH_TOLERANCE:
                    sign = -1.0
                    break
        if sign != 0.0:
            n_aligned += 1
            weighted += sign * max(0.0, z)
            total_z += max(0.0, z)

    strength = 0.0
    if total_z > 0:
        strength = max(-1.0, min(1.0, weighted / total_z))

    if strength > 0.1:
        direction = "BULLISH"
    elif strength < -0.1:
        direction = "BEARISH"
    else:
        direction = "NEUTRAL"

    confidence = float(snap.get("coherence_score", 0.0) or 0.0)
    confidence = max(0.0, min(1.0, confidence))

    return UnifiedSignal(
        source="harmonic_observer",
        signal_type="prediction",
        symbol=symbol,
        direction=direction,
        confidence=confidence,
        strength=strength,
        payload={
            "regime": snap.get("regime", "WARMING"),
            "coherence_score": confidence,
            "n_rocks_fast": snap.get("n_samples_fast", 0) and len(snap.get("rocks_fast", [])),
            "n_rocks_slow": snap.get("n_samples_slow", 0) and len(snap.get("rocks_slow", [])),
            "n_aligned_rocks": n_aligned,
            "rocks_top": rocks_dicts[:5],
            "uptime_s": snap.get("uptime_s", 0.0),
        },
        timestamp=time.time(),
    )


def _build_neutral_signal(symbol: str, reason: str):
    """Fallback used when no observer is running."""
    from aureon.autonomous.aureon_autonomy_hub import UnifiedSignal
    return UnifiedSignal(
        source="harmonic_observer",
        signal_type="prediction",
        symbol=symbol,
        direction="NEUTRAL",
        confidence=0.0,
        strength=0.0,
        payload={"reason": reason},
        timestamp=time.time(),
    )


def make_predictor(observer: HarmonicObserver) -> Callable:
    """Return ``predict_fn(data_signals, symbol) → UnifiedSignal`` bound to ``observer``.

    Use this when you want a specific observer instance plugged into a
    specific PredictionBus, e.g. in tests or multi-tenant setups. The
    autonomous wiring uses the singleton-based predictor below instead.
    """
    def predict_fn(data_signals: Optional[Dict] = None, symbol: str = "BTCUSD"):
        try:
            return _build_unified_signal(observer, symbol)
        except Exception as exc:
            logger.debug("harmonic_observer predict failed: %s", exc)
            return _build_neutral_signal(symbol, f"predict_error:{type(exc).__name__}")
    predict_fn.__name__ = "harmonic_observer_predict"
    return predict_fn


def harmonic_observer_predictor(data_signals: Optional[Dict] = None,
                                symbol: str = "BTCUSD"):
    """Module-level predictor that consults the observer singleton.

    Returns a NEUTRAL ``UnifiedSignal`` with confidence 0.0 if no observer
    has been constructed yet — keeps the PredictionBus consensus
    untouched in that case.
    """
    from aureon.observer import get_observer
    obs = get_observer()
    if obs is None:
        return _build_neutral_signal(symbol, "observer_not_running")
    try:
        return _build_unified_signal(obs, symbol)
    except Exception as exc:
        logger.debug("harmonic_observer_predictor failed: %s", exc)
        return _build_neutral_signal(symbol, f"predict_error:{type(exc).__name__}")
