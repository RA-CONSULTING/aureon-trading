"""ThoughtBus emission contract.

When the observer detects a rock lifecycle event (formed / strengthened
/ weakened / vanished), it publishes ``harmonic.observer.rock`` to the
ThoughtBus. These tests verify the publish path uses the StubBus
correctly and that the payload shape matches what subscribers will
read.
"""

from __future__ import annotations

import pytest

from aureon.observer import HarmonicObserver
from aureon.observer.rock import Rock


def test_emit_formed_publishes_correct_topic_and_shape(stub_bus):
    obs = HarmonicObserver(
        trace_interval_s=1.0,
        publish_to_bus=True,
        bus=stub_bus,
    )
    r = Rock(kind="band", scale="fast", dominant_hz=7.83, amplitude=0.4, z_score=3.5)
    obs._emit("formed", r)

    assert stub_bus.topics() == ["harmonic.observer.rock"]
    payload = stub_bus.payloads_for("harmonic.observer.rock")[0]
    assert payload["event"] == "formed"
    assert "rock" in payload
    assert payload["rock"]["kind"] == "band"
    assert payload["rock"]["scale"] == "fast"
    assert abs(payload["rock"]["dominant_hz"] - 7.83) < 1e-6


def test_emit_lifecycle_kinds_all_publish(stub_bus):
    obs = HarmonicObserver(trace_interval_s=1.0, publish_to_bus=True, bus=stub_bus)
    r = Rock(kind="peak", scale="slow", dominant_hz=0.0, amplitude=0.9, z_score=4.0)
    for kind in ("formed", "strengthened", "weakened", "vanished"):
        obs._emit(kind, r)

    events = [p["event"] for p in stub_bus.payloads_for("harmonic.observer.rock")]
    assert events == ["formed", "strengthened", "weakened", "vanished"]


def test_publish_disabled_does_not_emit(stub_bus):
    obs = HarmonicObserver(
        trace_interval_s=1.0,
        publish_to_bus=False,
        bus=stub_bus,
    )
    r = Rock(kind="band", scale="fast", dominant_hz=1.0, amplitude=0.1, z_score=3.0)
    obs._emit("formed", r)
    assert stub_bus.events == []


def test_bus_failure_does_not_raise():
    """A throwing bus must not break the observer's call site."""
    class ExplodingBus:
        def publish(self, *a, **kw):
            raise RuntimeError("bus down")

    obs = HarmonicObserver(
        trace_interval_s=1.0,
        publish_to_bus=True,
        bus=ExplodingBus(),
    )
    r = Rock(kind="band", scale="fast", dominant_hz=1.0, amplitude=0.1, z_score=3.0)
    # Must not raise — observer wraps publish in try/except at debug log.
    obs._emit("formed", r)
    assert obs._n_events_emitted == 1
