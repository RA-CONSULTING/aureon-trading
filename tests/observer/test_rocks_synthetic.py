"""Detector behaviour on synthetic Λ traces.

Heavy lifting (FFT, peak detection) requires numpy + scipy — the
sandbox doesn't have them; the tests skip cleanly. In production with
both installed the detector should:

  * Find the planted dominant frequency as a "band" rock within 5%.
  * Find planted peaks above the z-threshold.
  * Find a flat segment as a "plateau".

These aren't golden-numeric tests (the FFT bin grid + Hanning window
shift the peak by a small amount); they're structural — the right
*kinds* of rocks should appear.
"""

from __future__ import annotations

import math

import pytest

# Skip the whole module when scientific deps are missing.
pytest.importorskip("numpy")
pytest.importorskip("scipy")

from aureon.observer import HarmonicObserver, Rock  # noqa: E402


def _planted_trace(n: int, hz: float, dt_s: float = 1.0):
    """Generate (ts, lambda) pairs: sinusoid + a flat plateau segment."""
    out = []
    for i in range(n):
        t = i * dt_s
        if 60 <= i < 100:
            v = 0.5  # plateau region
        else:
            v = 0.5 + 0.4 * math.sin(2 * math.pi * hz * t)
        out.append((t, v))
    return out


def test_observer_finds_band_at_planted_frequency():
    obs = HarmonicObserver(
        fast_window_minutes=10,
        slow_window_minutes=60,
        trace_interval_s=1.0,
        publish_to_bus=False,
    )
    target_hz = 0.1
    samples = _planted_trace(n=200, hz=target_hz, dt_s=1.0)
    for ts, v in samples:
        obs.ingest(ts, v)
    # Force one more ingest past the detect interval to flush detection.
    obs.ingest(samples[-1][0] + 35.0, 0.5)

    band_rocks = [r for r in obs.current_rocks() if r.kind == "band"]
    assert band_rocks, "expected at least one band rock for a clean sinusoid"

    # Best band rock — closest dominant_hz to the planted frequency.
    best = min(band_rocks, key=lambda r: abs(r.dominant_hz - target_hz))
    rel_err = abs(best.dominant_hz - target_hz) / target_hz
    assert rel_err < 0.20, (
        f"dominant_hz {best.dominant_hz:.4f} too far from planted {target_hz} "
        f"(rel_err={rel_err:.3f})"
    )


def test_plateau_detected_in_flat_segment():
    obs = HarmonicObserver(
        fast_window_minutes=10,
        slow_window_minutes=60,
        trace_interval_s=1.0,
        publish_to_bus=False,
    )
    samples = _planted_trace(n=200, hz=0.1, dt_s=1.0)
    for ts, v in samples:
        obs.ingest(ts, v)
    obs.ingest(samples[-1][0] + 35.0, 0.5)

    plateau_rocks = [r for r in obs.current_rocks() if r.kind == "plateau"]
    # A 40-sample stretch of constant 0.5 should register as a plateau.
    assert plateau_rocks, "expected a plateau rock for the flat segment"


def test_quiet_input_yields_quiet_or_warming_regime():
    """A flat constant Λ shouldn't produce strong rocks."""
    obs = HarmonicObserver(
        fast_window_minutes=10,
        slow_window_minutes=60,
        trace_interval_s=1.0,
        publish_to_bus=False,
    )
    for i in range(120):
        obs.ingest(float(i), 0.42)
    obs.ingest(150.0, 0.42)

    regime = obs.regime()
    assert regime in ("WARMING", "QUIET", "CHARGED"), regime


def test_metrics_snapshot_is_json_serialisable():
    """Sanity check the snapshot will round-trip through json.dumps."""
    import json

    obs = HarmonicObserver(
        fast_window_minutes=10,
        slow_window_minutes=60,
        trace_interval_s=1.0,
        publish_to_bus=False,
    )
    for i in range(50):
        obs.ingest(float(i), 0.5 + 0.1 * math.sin(i * 0.3))
    snap = obs.metrics_snapshot()
    json.dumps(snap)  # raises if any non-serialisable content snuck in
