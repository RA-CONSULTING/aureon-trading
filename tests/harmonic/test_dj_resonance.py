"""
Tests for aureon.harmonic.dj_resonance — the beat-driven resonance engine.

These tests exercise the engine with a stub bus so we can verify the exact
set of topics it emits per beat, without depending on the real ThoughtBus
or the vault.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest

from aureon.harmonic.dj_resonance import (
    DEFAULT_SET_PATH,
    PHI_SQUARED,
    PHRASE_BEATS,
    BeatPulse,
    DJResonanceEngine,
    DJTrack,
    camelot_to_hz,
    get_dj_resonance_engine,
    load_dj_set,
    reset_dj_resonance_engine,
)


# ─────────────────────────────────────────────────────────────────────────────
# Stub bus — records every publish in order.
# ─────────────────────────────────────────────────────────────────────────────


class StubBus:
    def __init__(self) -> None:
        self.events: List[Tuple[str, Dict[str, Any]]] = []
        self._lock = threading.Lock()

    def publish(self, topic: str, payload: Dict[str, Any], source: str = "") -> None:
        with self._lock:
            self.events.append((topic, dict(payload)))

    def topics(self) -> List[str]:
        return [t for t, _ in self.events]

    def payloads_for(self, topic: str) -> List[Dict[str, Any]]:
        return [p for t, p in self.events if t == topic]

    def clear(self) -> None:
        with self._lock:
            self.events.clear()


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _reset_singleton():
    reset_dj_resonance_engine()
    yield
    reset_dj_resonance_engine()


@pytest.fixture
def tiny_set(tmp_path: Path) -> Path:
    """A two-track set so tests advance fast and deterministically."""
    payload = {
        "set_name": "test",
        "schema_version": 1,
        "phrase_beats": PHRASE_BEATS,
        "tracks": [
            {
                "title": "Alpha",
                "artist": "Tester",
                "bpm": 120.0,
                "camelot": "8A",
                "energy": 6,
                "phrase_count": 2,           # 64 beats total
                "duration_s": 32.0,
                "drop_phrases": [2],         # drop on phrase 2
                "breakdown_phrases": [],
            },
            {
                "title": "Beta",
                "artist": "Tester",
                "bpm": 128.0,
                "camelot": "12A",
                "energy": 9,
                "phrase_count": 1,           # 32 beats total
                "duration_s": 15.0,
                "drop_phrases": [],
                "breakdown_phrases": [1],    # breakdown on phrase 1
            },
        ],
    }
    path = tmp_path / "tiny_set.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


# ─────────────────────────────────────────────────────────────────────────────
# Dataset tests
# ─────────────────────────────────────────────────────────────────────────────


def test_default_set_loads_and_is_nonempty():
    """The shipped data/dj/resonance_set.json must load cleanly."""
    assert DEFAULT_SET_PATH.exists(), f"Missing default set at {DEFAULT_SET_PATH}"
    tracks = load_dj_set()
    assert len(tracks) >= 8
    for t in tracks:
        assert isinstance(t, DJTrack)
        assert 60 <= t.bpm <= 200
        assert t.phrase_count >= 1
        assert t.total_beats == t.phrase_count * PHRASE_BEATS


def test_missing_set_returns_empty(tmp_path: Path):
    missing = tmp_path / "nope.json"
    assert load_dj_set(missing) == []


def test_camelot_to_hz_is_bounded():
    hz_1a = camelot_to_hz("1A")
    hz_12b = camelot_to_hz("12B")
    assert 430 <= hz_1a <= 530
    assert 430 <= hz_12b <= 530
    assert hz_12b > hz_1a


# ─────────────────────────────────────────────────────────────────────────────
# Engine tick tests (synchronous, no threads)
# ─────────────────────────────────────────────────────────────────────────────


def test_tick_publishes_full_topic_set(tiny_set: Path):
    bus = StubBus()
    engine = DJResonanceEngine(bus=bus, set_path=tiny_set)
    engine.load()

    pulse = engine.tick()
    assert isinstance(pulse, BeatPulse)
    assert pulse.beat_num == 0
    assert pulse.phrase_pos == 0
    assert pulse.is_phrase_start is True

    topics = bus.topics()
    # First tick: canonical pulse + phrase mark + love stream + skill
    assert "dj.beat.pulse" in topics
    assert "dj.phrase.mark" in topics
    assert "love.stream.528hz" in topics
    assert "skill.executed" in topics


def test_love_stream_payload_has_gamma_coherence(tiny_set: Path):
    """The piggyback on love.stream.528hz MUST include gamma_coherence —
    that's what drives vault.love_amplitude in _update_synthesised_state."""
    bus = StubBus()
    engine = DJResonanceEngine(bus=bus, set_path=tiny_set)
    engine.load()

    # Advance several beats into the phrase so coherence has climbed.
    for _ in range(16):
        engine.tick()

    love_payloads = bus.payloads_for("love.stream.528hz")
    assert len(love_payloads) == 16
    for p in love_payloads:
        assert "gamma_coherence" in p
        assert 0.0 <= p["gamma_coherence"] <= 1.0
        assert "dominant_frequency_hz" in p
        assert "dominant_chakra" in p

    # By beat 16 (mid-phrase, quarter 2) we should be above 0.5.
    assert love_payloads[-1]["gamma_coherence"] > 0.5


def test_skill_executed_ok_follows_phrase_position(tiny_set: Path):
    """Beats at the edge of a phrase (pos 0/1) are 'misses', beats in the
    body of the phrase are 'lands'. Gratitude EMA follows this."""
    bus = StubBus()
    engine = DJResonanceEngine(bus=bus, set_path=tiny_set)
    engine.load()

    for _ in range(PHRASE_BEATS):
        engine.tick()

    skill_payloads = bus.payloads_for("skill.executed")
    assert len(skill_payloads) == PHRASE_BEATS
    # First two beats (phrase edge) should be misses.
    assert skill_payloads[0]["ok"] is False
    assert skill_payloads[1]["ok"] is False
    # Later beats should be lands.
    lands = [p for p in skill_payloads if p["ok"]]
    assert len(lands) >= PHRASE_BEATS // 2


def test_drop_marker_emitted_on_configured_phrase(tiny_set: Path):
    """Phrase 2 is configured as a drop on the Alpha track (1-indexed).
    Drops are emitted on the first beat of that phrase."""
    bus = StubBus()
    engine = DJResonanceEngine(bus=bus, set_path=tiny_set)
    engine.load()

    # Advance through phrase 1 (32 beats) → phrase 2 starts on beat 32.
    for _ in range(PHRASE_BEATS + 1):
        engine.tick()

    drops = bus.payloads_for("dj.track.drop")
    assert len(drops) == 1
    assert drops[0]["track"] == "Alpha"
    assert drops[0]["phrase_num"] == 1  # 0-indexed internally


def test_track_transition_fires_at_end_of_track(tiny_set: Path):
    bus = StubBus()
    engine = DJResonanceEngine(bus=bus, set_path=tiny_set)
    engine.load()

    # Alpha has 2 * 32 = 64 beats. Transition fires when we advance past it.
    for _ in range(65):
        engine.tick()

    transitions = bus.payloads_for("dj.track.transition")
    assert len(transitions) == 1
    assert transitions[0]["to_title"] == "Beta"
    assert transitions[0]["to_bpm"] == 128.0


def test_phrase_mark_count_matches_phrase_starts(tiny_set: Path):
    bus = StubBus()
    engine = DJResonanceEngine(bus=bus, set_path=tiny_set)
    engine.load()

    for _ in range(PHRASE_BEATS * 3):  # three phrases worth of beats
        engine.tick()

    marks = bus.payloads_for("dj.phrase.mark")
    # We expect one mark at the start of each phrase we crossed.
    assert len(marks) == 3


def test_coherence_climbs_within_a_phrase(tiny_set: Path):
    """A DJ builds tension through the phrase. Coherence at beat 28 should
    exceed coherence at beat 4 within the same phrase."""
    bus = StubBus()
    engine = DJResonanceEngine(bus=bus, set_path=tiny_set)
    engine.load()

    pulses: List[BeatPulse] = []
    for _ in range(PHRASE_BEATS):
        p = engine.tick()
        assert p is not None
        pulses.append(p)

    assert pulses[28].coherence > pulses[4].coherence


def test_engine_no_bus_still_runs(tiny_set: Path):
    """A missing bus must not break the engine — it just no-ops publishes."""
    engine = DJResonanceEngine(bus=None, set_path=tiny_set)
    engine.load()
    engine._bus = None  # force no-op path even if singleton would resolve
    pulse = engine.tick()
    assert pulse is not None


def test_status_reports_progression(tiny_set: Path):
    bus = StubBus()
    engine = DJResonanceEngine(bus=bus, set_path=tiny_set)
    engine.load()
    for _ in range(5):
        engine.tick()
    s = engine.status()
    assert s["track_count"] == 2
    assert s["total_beats_played"] == 5
    assert s["current_track"]["title"] == "Alpha"
    assert s["last_pulse"]["beat_num"] == 4


# ─────────────────────────────────────────────────────────────────────────────
# Singleton tests
# ─────────────────────────────────────────────────────────────────────────────


def test_singleton_is_shared():
    a = get_dj_resonance_engine()
    b = get_dj_resonance_engine()
    assert a is b


def test_reset_drops_singleton():
    a = get_dj_resonance_engine()
    reset_dj_resonance_engine()
    b = get_dj_resonance_engine()
    assert a is not b
