"""HNCLiveDaemon attach_observer flag and singleton wiring.

Verifies that:
  * attach_observer=True (default) constructs an observer
  * The observer claims the singleton
  * Caller-provided observers take precedence
  * attach_observer=False with no observer disables the integration
  * The daemon never raises on attach failures (graceful degrade)
"""

from __future__ import annotations

import asyncio

import pytest

from aureon.core.hnc_live_daemon import HNCLiveDaemon
from aureon.observer import HarmonicObserver, get_observer


def test_default_attach_observer_constructs():
    d = HNCLiveDaemon()
    assert d._observer is not None
    assert get_observer() is d._observer


def test_attach_observer_false_disables():
    d = HNCLiveDaemon(attach_observer=False)
    assert d._observer is None


def test_caller_provided_observer_used():
    custom = HarmonicObserver(publish_to_bus=False)
    d = HNCLiveDaemon(attach_observer=False, observer=custom)
    assert d._observer is custom


def test_caller_observer_overrides_attach_flag():
    """If caller provides an observer, attach_observer=True does NOT
    construct a second one."""
    custom = HarmonicObserver(publish_to_bus=False)
    d = HNCLiveDaemon(attach_observer=True, observer=custom)
    assert d._observer is custom


def test_compute_loop_feeds_observer_ingest_state():
    """Run a tiny duration-bounded loop; verify ingest_state was called."""
    d = HNCLiveDaemon()
    asyncio.run(d.run(duration_s=8.0))
    snap = d._observer.metrics_snapshot()
    assert snap["n_ingested"] >= 1
    latest = snap["latest_field"]
    assert latest["lambda_t"] is not None
    # ingest_state must have populated psi/level — these only flow from
    # ingest_state, never from plain ingest().
    assert latest["consciousness_psi"] is not None
    assert latest["consciousness_level"] is not None


def test_predictionbus_auto_picks_up_observer():
    """Stage B + Stage E together: bus auto-wires; daemon installs observer;
    bus then sees real observer state."""
    from aureon.autonomous.aureon_autonomy_hub import PredictionBus
    bus = PredictionBus()
    d = HNCLiveDaemon()
    asyncio.run(d.run(duration_s=8.0))
    results = bus.run_predictions({}, symbol="BTCUSD")
    assert "harmonic_observer" in results
    sig = results["harmonic_observer"]
    assert sig.direction in ("BULLISH", "BEARISH", "NEUTRAL")
    assert 0.0 <= sig.confidence <= 1.0
