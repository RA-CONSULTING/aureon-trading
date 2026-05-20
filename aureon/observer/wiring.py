"""Autonomous wiring helpers for the HarmonicObserver.

These let any PredictionBus pick up the observer predictor without a
caller having to remember to register it. The autonomy hub calls
``auto_wire_prediction_bus`` from ``PredictionBus.__init__``; that's the
single attach point that makes the whole system flow without manual
glue code.

Three entry points:

    wire_harmonic_observer(prediction_bus, observer=None, name=...)
        Explicit registration. Pass an observer or fall through to the
        singleton. Used in tests and for custom pipelines.

    auto_wire_prediction_bus(prediction_bus)
        Hooked into ``PredictionBus.__init__``. Idempotent — safe to call
        many times; only registers once per bus instance.

    PREDICTOR_NAME
        Canonical name string the predictor registers under. Matches the
        key in ``PredictionBus.weight_map``.
"""

from __future__ import annotations

import logging
from typing import Optional

from aureon.observer.harmonic_observer import HarmonicObserver
from aureon.observer.predictor import (
    harmonic_observer_predictor,
    make_predictor,
)

logger = logging.getLogger(__name__)


PREDICTOR_NAME = "harmonic_observer"
PREDICTOR_WEIGHT = 1.5  # mirrors PredictionBus.weight_map entry


def wire_harmonic_observer(
    prediction_bus,
    observer: Optional[HarmonicObserver] = None,
    name: str = PREDICTOR_NAME,
) -> bool:
    """Register the predictor on ``prediction_bus``. Returns True on success.

    If ``observer`` is None, the predictor consults the observer singleton
    at call-time, so wiring is safe even before any observer exists.
    """
    if prediction_bus is None:
        return False
    try:
        if observer is not None:
            prediction_bus.register_predictor(name, make_predictor(observer))
        else:
            prediction_bus.register_predictor(name, harmonic_observer_predictor)
        return True
    except Exception as exc:
        logger.debug("wire_harmonic_observer failed: %s", exc)
        return False


def auto_wire_prediction_bus(prediction_bus) -> bool:
    """Idempotently register the singleton-based predictor on ``prediction_bus``.

    Called from inside ``PredictionBus.__init__`` so any code path that
    constructs a bus gets the observer plugged in automatically. Marks
    the bus with a sentinel attribute so repeated calls are safe.
    """
    if prediction_bus is None:
        return False
    if getattr(prediction_bus, "_harmonic_observer_wired", False):
        return True
    ok = wire_harmonic_observer(prediction_bus, observer=None)
    if ok:
        setattr(prediction_bus, "_harmonic_observer_wired", True)
        logger.info("auto-wired harmonic_observer predictor onto PredictionBus")
    return ok
