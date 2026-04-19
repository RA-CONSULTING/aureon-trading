#!/usr/bin/env python3
"""
Tests for LifeContext, scan_for_opportunity, and the OpportunityScanner.

What's being proved:
  - LifeEvent round-trips through to_dict / from_dict
  - LifeContext.add persists via vault.ingest and auto-extracts tags
  - archive / complete / remove mutate status / drop the event
  - load_from_vault rebuilds the in-memory table from cards
  - Each persona's scan_for_opportunity matches on tags / keywords and
    returns a non-empty, event-specific goal text
  - Personas without OPPORTUNITY_TAGS default to None
  - OpportunityScanner fires one goal.submit.request per (persona, event)
    per dedupe window, and the actuator publishes them
  - Stale recent-entries expire and scan again
  - Scanner's scan_once is idempotent within the window
"""

from __future__ import annotations

import os
import sys
import time
from typing import Any, Callable, Dict, List

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.vault.aureon_vault import AureonVault  # noqa: E402
from aureon.vault.voice.aureon_personas import (  # noqa: E402
    ArtistVoice,
    ChildVoice,
    EngineerVoice,
    MysticVoice,
    QuantumPhysicistVoice,
    ResonantPersona,
    build_aureon_personas,
)
from aureon.vault.voice.life_context import LifeContext, LifeEvent  # noqa: E402
from aureon.vault.voice.opportunity_scanner import OpportunityScanner  # noqa: E402
from aureon.vault.voice.persona_action import PersonaActuator  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# Stubs
# ─────────────────────────────────────────────────────────────────────────────


class _StubBus:
    def __init__(self):
        self.published: List[Any] = []
        self._subs: Dict[str, List[Callable]] = {}

    def publish(self, thought=None, **kwargs):
        if thought is None:
            class _T:
                pass
            t = _T()
            t.topic = kwargs.get("topic", "")
            t.payload = kwargs.get("payload", {})
            t.source = kwargs.get("source", "")
            thought = t
        self.published.append(thought)
        for topic, handlers in self._subs.items():
            match = (topic == "*") or (topic == thought.topic) or (
                topic.endswith(".*") and thought.topic.startswith(topic[:-1])
            )
            if match:
                for h in handlers:
                    h(thought)
        return thought

    def subscribe(self, topic: str, handler: Callable) -> None:
        self._subs.setdefault(topic, []).append(handler)


class _StubAdapter:
    def prompt(self, messages, system, max_tokens):
        class _R:
            text = "."
            model = "stub"
            usage = {"total_tokens": 1}
        return _R()


# ─────────────────────────────────────────────────────────────────────────────
# LifeEvent / LifeContext
# ─────────────────────────────────────────────────────────────────────────────


def test_life_event_round_trip():
    e = LifeEvent(title="Wedding", description="on the beach", date="May 12",
                  tags=["wedding", "family"])
    d = e.to_dict()
    e2 = LifeEvent.from_dict(d)
    assert e2.event_id == e.event_id
    assert e2.title == "Wedding"
    assert e2.tags == ["wedding", "family"]


def test_life_context_add_auto_extracts_tags():
    ctx = LifeContext()
    e = ctx.add("Wedding", description="Sister's marriage on the coast", date="May 12")
    assert "wedding" in e.tags
    assert "family" in e.tags  # "sister" matches family keyword


def test_life_context_add_persists_to_vault():
    v = AureonVault()
    ctx = LifeContext(vault=v)
    e = ctx.add("Thesis defence", description="PhD dissertation", date="June 3")
    # Event stored in the vault as a life.event card.
    topics = [c.source_topic for c in v._contents.values()]
    assert "life.event" in topics
    card = next(c for c in v._contents.values() if c.source_topic == "life.event")
    assert card.payload["event_id"] == e.event_id
    assert "learning" in card.payload["tags"]


def test_life_context_archive_and_complete():
    v = AureonVault()
    ctx = LifeContext(vault=v)
    e = ctx.add("Presentation")
    assert len(ctx.active()) == 1
    ctx.archive(e.event_id)
    assert len(ctx.active()) == 0
    assert len(ctx.all()) == 1  # archived but still there
    ctx.complete(e.event_id)
    assert ctx.get(e.event_id).status == "completed"


def test_life_context_remove():
    ctx = LifeContext()
    e = ctx.add("Test")
    assert ctx.remove(e.event_id) is True
    assert ctx.get(e.event_id) is None
    assert ctx.remove("nonexistent") is False


def test_life_context_load_from_vault():
    v = AureonVault()
    ctx1 = LifeContext(vault=v)
    ctx1.add("Wedding", date="May 12")
    ctx1.add("Interview", date="June 1")
    ctx2 = LifeContext()
    n = ctx2.load_from_vault(v)
    assert n == 2
    titles = {e.title for e in ctx2.all()}
    assert titles == {"Wedding", "Interview"}


def test_life_context_rejects_blank_title():
    ctx = LifeContext()
    with pytest.raises(ValueError):
        ctx.add("   ")


# ─────────────────────────────────────────────────────────────────────────────
# Per-persona scan_for_opportunity
# ─────────────────────────────────────────────────────────────────────────────


def _event(title, tags=None, date="", description=""):
    return LifeEvent(title=title, tags=list(tags or []), date=date,
                     description=description)


def test_artist_scans_wedding():
    a = ArtistVoice(adapter=_StubAdapter())
    goal = a.scan_for_opportunity(_event("Wedding in May", tags=["wedding"], date="May 12"))
    assert goal is not None
    assert "Wedding in May" in goal
    assert "May 12" in goal
    assert "svg" in goal.lower() or "visual" in goal.lower()


def test_artist_ignores_unrelated_event():
    a = ArtistVoice(adapter=_StubAdapter())
    assert a.scan_for_opportunity(_event("Hospital appointment", tags=["health"])) is None


def test_quantum_physicist_scans_research_like_event():
    qp = QuantumPhysicistVoice(adapter=_StubAdapter())
    # Keyword hit via search_blob — no tag explicitly "research"
    goal = qp.scan_for_opportunity(_event(
        "Thesis on quantum gravity", description="PhD dissertation",
        tags=["learning"],
    ))
    assert goal is not None
    assert "research" in goal.lower() or "papers" in goal.lower()


def test_engineer_scans_work_deadline():
    eng = EngineerVoice(adapter=_StubAdapter())
    goal = eng.scan_for_opportunity(_event(
        "Client pitch deadline", tags=["work"], date="Friday",
    ))
    assert goal is not None
    assert "build" in goal.lower() or "module" in goal.lower() or "tool" in goal.lower()


def test_mystic_scans_grief():
    m = MysticVoice(adapter=_StubAdapter())
    goal = m.scan_for_opportunity(_event(
        "Funeral for grandfather", tags=["grief", "family"], date="next Sunday",
    ))
    assert goal is not None
    assert "528" in goal or "blessing" in goal.lower() or "invocation" in goal.lower()


def test_persona_without_opportunity_tags_returns_none():
    child = ChildVoice(adapter=_StubAdapter())
    assert child.OPPORTUNITY_TAGS == ()
    assert child.scan_for_opportunity(_event("Anything", tags=["wedding"])) is None


def test_archived_event_is_skipped():
    a = ArtistVoice(adapter=_StubAdapter())
    e = _event("Old wedding", tags=["wedding"])
    e.status = "archived"
    assert a.scan_for_opportunity(e) is None


# ─────────────────────────────────────────────────────────────────────────────
# OpportunityScanner
# ─────────────────────────────────────────────────────────────────────────────


def test_scanner_fires_goal_for_matching_persona():
    bus = _StubBus()
    actuator = PersonaActuator(thought_bus=bus)
    ctx = LifeContext()
    ctx.add("Wedding in May", tags=["wedding"], date="May 12")

    personas = build_aureon_personas(adapter=_StubAdapter())
    scanner = OpportunityScanner(
        personas=personas, life_context=ctx, actuator=actuator,
        dedupe_window_s=3600.0, interval_s=999.0,
    )
    fired = scanner.scan_once()
    # At least Artist + Mystic have wedding in their tags
    firing_personas = {h.persona for h in fired}
    assert "artist" in firing_personas
    assert "mystic" in firing_personas
    # Bus saw the corresponding goal.submit.request publications
    topics = [t.topic for t in bus.published]
    request_count = sum(1 for t in topics if t == "goal.submit.request")
    assert request_count == len(fired) >= 2


def test_scanner_dedupes_within_window():
    bus = _StubBus()
    actuator = PersonaActuator(thought_bus=bus)
    ctx = LifeContext()
    ctx.add("Wedding", tags=["wedding"])
    personas = build_aureon_personas(adapter=_StubAdapter())
    scanner = OpportunityScanner(
        personas=personas, life_context=ctx, actuator=actuator,
        dedupe_window_s=3600.0, interval_s=999.0,
    )
    first = scanner.scan_once()
    second = scanner.scan_once()
    assert len(first) > 0
    assert second == []  # dedupe prevents re-firing


def test_scanner_refires_after_window_expires():
    bus = _StubBus()
    actuator = PersonaActuator(thought_bus=bus)
    ctx = LifeContext()
    ctx.add("Wedding", tags=["wedding"])
    personas = {"artist": ArtistVoice(adapter=_StubAdapter())}
    scanner = OpportunityScanner(
        personas=personas, life_context=ctx, actuator=actuator,
        dedupe_window_s=0.05, interval_s=999.0,
    )
    first = scanner.scan_once()
    assert len(first) == 1
    time.sleep(0.1)
    second = scanner.scan_once()
    assert len(second) == 1  # window expired, fires again


def test_scanner_history_accumulates():
    bus = _StubBus()
    actuator = PersonaActuator(thought_bus=bus)
    ctx = LifeContext()
    ctx.add("Wedding", tags=["wedding"])
    ctx.add("Birthday", tags=["birthday"])
    personas = {
        "artist": ArtistVoice(adapter=_StubAdapter()),
        "mystic": MysticVoice(adapter=_StubAdapter()),
    }
    scanner = OpportunityScanner(
        personas=personas, life_context=ctx, actuator=actuator,
        dedupe_window_s=3600.0, interval_s=999.0,
    )
    scanner.scan_once()
    hist = scanner.history()
    assert len(hist) >= 2
    assert all("goal_text" in h for h in hist)
    assert all(h["persona"] in ("artist", "mystic") for h in hist)


def test_scanner_ignores_archived_events():
    bus = _StubBus()
    actuator = PersonaActuator(thought_bus=bus)
    ctx = LifeContext()
    e = ctx.add("Wedding", tags=["wedding"])
    ctx.archive(e.event_id)
    personas = {"artist": ArtistVoice(adapter=_StubAdapter())}
    scanner = OpportunityScanner(
        personas=personas, life_context=ctx, actuator=actuator,
        dedupe_window_s=3600.0, interval_s=999.0,
    )
    assert scanner.scan_once() == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
