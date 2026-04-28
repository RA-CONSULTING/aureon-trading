"""Theroux-style observer over the live HNC field.

Public surface:

    HarmonicObserver         — the observer (multi-scale buffers, detection)
    Rock                     — recurring anchor feature in the Λ trace
    RockEvent                — lifecycle envelope published to the ThoughtBus
    get_observer()           — global singleton accessor (None until first construct)
    set_observer(obs)        — register a constructed observer as the singleton

The singleton pattern mirrors ``aureon.core.aureon_thought_bus.get_thought_bus``
so any module that wants a stable handle on "the live observer running in
this process" can grab it without dependency injection. The first
``HarmonicObserver`` constructed automatically becomes the singleton; the
PredictionBus auto-wires against it on its own ``__init__``.
"""

from threading import Lock
from typing import Optional

from aureon.observer.harmonic_observer import HarmonicObserver
from aureon.observer.rock import Rock, RockEvent

__all__ = [
    "HarmonicObserver", "Rock", "RockEvent",
    "get_observer", "set_observer",
    "make_predictor", "wire_harmonic_observer", "auto_wire_prediction_bus",
    "PREDICTOR_NAME", "PREDICTOR_WEIGHT",
]


# ─── singleton plumbing ────────────────────────────────────────────

_observer_singleton: Optional[HarmonicObserver] = None
_singleton_lock = Lock()


def get_observer() -> Optional[HarmonicObserver]:
    """Return the process-wide observer if one has been constructed.

    Returns None when no observer exists yet. Callers should treat
    ``None`` as "observer not running" and fall back to defaults — the
    Queen sentience context, the Kelly gate, and the predictor adapter
    all do this so the rest of the system stays operational with the
    observer disabled.
    """
    return _observer_singleton


def set_observer(obs: HarmonicObserver) -> None:
    """Register ``obs`` as the singleton. Idempotent for the same instance."""
    global _observer_singleton
    with _singleton_lock:
        _observer_singleton = obs


# Auto-register: the first HarmonicObserver constructed claims the
# singleton. Wrap __init__ rather than __new__ so subclass behaviour is
# preserved and we don't fight Python's instance creation.
_orig_init = HarmonicObserver.__init__


def _init_with_singleton_register(self, *args, **kwargs):
    _orig_init(self, *args, **kwargs)
    global _observer_singleton
    with _singleton_lock:
        if _observer_singleton is None:
            _observer_singleton = self


HarmonicObserver.__init__ = _init_with_singleton_register  # type: ignore[assignment]


# Re-export the predictor / wiring helpers at the package root. Imported
# at the bottom so the singleton plumbing is in place before they bind.
from aureon.observer.predictor import make_predictor  # noqa: E402
from aureon.observer.wiring import (  # noqa: E402
    PREDICTOR_NAME,
    PREDICTOR_WEIGHT,
    auto_wire_prediction_bus,
    wire_harmonic_observer,
)
