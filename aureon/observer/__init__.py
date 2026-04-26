"""Theroux-style observer over the live HNC field.

Public surface:

    HarmonicObserver  — the observer (multi-scale buffers, rock detection)
    Rock              — recurring anchor feature in the Λ trace
    RockEvent         — lifecycle envelope published to the ThoughtBus

Stage A is the core — buffers, detection, ThoughtBus emission. Adapters
to PredictionBus, the Kelly gate, and the Queen sentience layer are
added in later stages (see /root/.claude/plans/let-s-organize-the-repo-serene-pine.md).
"""

from aureon.observer.harmonic_observer import HarmonicObserver
from aureon.observer.rock import Rock, RockEvent

__all__ = ["HarmonicObserver", "Rock", "RockEvent"]
