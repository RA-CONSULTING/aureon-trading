"""Predictor adapter contract.

Asserts the harmonic_observer predictor:
  * Returns a UnifiedSignal with valid direction / confidence / strength
  * Returns NEUTRAL conf=0 when the singleton is empty
  * Maps rocks at HNC bullish anchor frequencies → BULLISH bias
  * Maps rocks at the parasite frequency (440 Hz) → BEARISH bias
  * Doesn't raise on observer errors (returns NEUTRAL with payload.reason)

Doesn't require numpy — the predictor consumes the metrics_snapshot dict
shape, not the numpy-backed detector.
"""

from __future__ import annotations

import pytest

from aureon.observer import HarmonicObserver, set_observer
from aureon.observer.predictor import (
    harmonic_observer_predictor,
    make_predictor,
)
from aureon.observer.rock import Rock


def _build_obs_with_rocks(rocks_fast=(), rocks_slow=()):
    """Construct an observer and inject rock dicts into its catalogue."""
    obs = HarmonicObserver(
        trace_interval_s=1.0,
        publish_to_bus=False,
    )
    for r in rocks_fast:
        obs._rocks["fast"][r.id] = r
    for r in rocks_slow:
        obs._rocks["slow"][r.id] = r
    return obs


def test_predictor_returns_neutral_when_no_observer():
    """No singleton → NEUTRAL with reason."""
    sig = harmonic_observer_predictor({}, "BTCUSD")
    assert sig.direction == "NEUTRAL"
    assert sig.confidence == 0.0
    assert sig.strength == 0.0
    assert sig.payload.get("reason") == "observer_not_running"
    assert sig.source == "harmonic_observer"


def test_predictor_via_make_predictor_with_explicit_obs():
    obs = _build_obs_with_rocks()
    pred = make_predictor(obs)
    sig = pred({}, "ETHUSD")
    assert sig.direction in ("BULLISH", "BEARISH", "NEUTRAL")
    assert 0.0 <= sig.confidence <= 1.0
    assert -1.0 <= sig.strength <= 1.0
    assert sig.symbol == "ETHUSD"
    assert sig.source == "harmonic_observer"


def test_predictor_bullish_bias_on_528hz_rock():
    """A strong rock at the LOVE_HZ anchor (528 Hz) → BULLISH bias."""
    bullish = Rock(kind="band", scale="fast", dominant_hz=528.0,
                   amplitude=0.9, z_score=4.0)
    obs = _build_obs_with_rocks(rocks_fast=[bullish])
    set_observer(obs)
    sig = harmonic_observer_predictor({}, "BTCUSD")
    assert sig.direction == "BULLISH"
    assert sig.strength > 0.0
    assert sig.payload["n_aligned_rocks"] >= 1


def test_predictor_bearish_bias_on_440hz_rock():
    """A strong rock at the parasite frequency (440 Hz) → BEARISH bias."""
    bearish = Rock(kind="band", scale="fast", dominant_hz=440.0,
                   amplitude=0.9, z_score=4.0)
    obs = _build_obs_with_rocks(rocks_fast=[bearish])
    set_observer(obs)
    sig = harmonic_observer_predictor({}, "BTCUSD")
    assert sig.direction == "BEARISH"
    assert sig.strength < 0.0


def test_predictor_neutral_on_unrelated_frequency_rock():
    """A rock far from any anchor frequency → NEUTRAL."""
    misc = Rock(kind="band", scale="fast", dominant_hz=123.4,
                amplitude=0.9, z_score=4.0)
    obs = _build_obs_with_rocks(rocks_fast=[misc])
    set_observer(obs)
    sig = harmonic_observer_predictor({}, "BTCUSD")
    assert sig.direction == "NEUTRAL"
    assert sig.strength == 0.0


def test_predictor_handles_metrics_snapshot_failure():
    """If the observer's metrics_snapshot raises, predictor returns NEUTRAL."""
    obs = _build_obs_with_rocks()
    obs.metrics_snapshot = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
    set_observer(obs)
    sig = harmonic_observer_predictor({}, "BTCUSD")
    assert sig.direction == "NEUTRAL"
    assert sig.confidence == 0.0
    assert "predict_error" in sig.payload.get("reason", "")


def test_predictor_payload_includes_rocks_top():
    bullish = Rock(kind="band", scale="fast", dominant_hz=528.0,
                   amplitude=0.9, z_score=4.0)
    obs = _build_obs_with_rocks(rocks_fast=[bullish])
    set_observer(obs)
    sig = harmonic_observer_predictor({}, "BTCUSD")
    assert "rocks_top" in sig.payload
    assert isinstance(sig.payload["rocks_top"], list)
    assert sig.payload["rocks_top"]
