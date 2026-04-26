"""Shared fixtures for the HarmonicObserver test suite.

Resets the observer singleton between every test so cross-test state
leakage can't mask bugs (e.g. a singleton from one test surviving into
the "no observer" assertion of another).
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Tuple

import pytest


@pytest.fixture(autouse=True)
def _reset_observer_singleton():
    """Clear the observer singleton before and after every test."""
    import aureon.observer as obs_mod
    obs_mod._observer_singleton = None
    yield
    obs_mod._observer_singleton = None


class StubBus:
    """Records every publish call in order. Mirrors tests/harmonic/StubBus."""

    def __init__(self) -> None:
        self.events: List[Tuple[str, Dict[str, Any]]] = []
        self._lock = threading.Lock()

    def publish(self, *args, **kwargs) -> None:
        topic = kwargs.get("topic", args[0] if args else "")
        payload = kwargs.get("payload", args[1] if len(args) > 1 else {})
        with self._lock:
            self.events.append((str(topic), dict(payload) if isinstance(payload, dict) else payload))

    def topics(self) -> List[str]:
        return [t for t, _ in self.events]

    def payloads_for(self, topic: str) -> List[Dict[str, Any]]:
        return [p for t, p in self.events if t == topic]

    def clear(self) -> None:
        with self._lock:
            self.events.clear()


@pytest.fixture
def stub_bus() -> StubBus:
    return StubBus()
