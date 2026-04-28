"""Data shapes for the Theroux-style HNC field observer.

A *rock* is a recurring anchor feature in the Λ(t) trace — something that
shows up repeatedly enough to be worth noting. Four kinds:

    peak       — a persistent local maximum in the field amplitude
    plateau    — a sustained near-constant region
    transition — a recurring regime boundary (the field crossing a
                 threshold or its phase-space curvature spiking)
    band       — a dominant frequency band in the FFT spectrum

A *RockEvent* records lifecycle changes — a rock forming, strengthening,
weakening, or vanishing. Events are what get published to the
ThoughtBus; current rocks are what downstream consumers (the Queen
sentience layer, the Kelly gate) read from the observer's snapshot.

Both shapes are pure dataclasses with ``to_dict`` for JSON / ThoughtBus
serialisation. No numpy, no scipy — those are confined to the detector
in ``harmonic_observer.py``.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Literal, Optional

RockKind = Literal["peak", "plateau", "transition", "band"]
RockScale = Literal["fast", "slow"]
RockEventKind = Literal["formed", "strengthened", "weakened", "vanished"]


@dataclass
class Rock:
    """A recurring anchor feature in the Λ(t) trace.

    Attributes:
        id:                 stable identifier across observations
        kind:               peak / plateau / transition / band
        scale:              "fast" (hours window) or "slow" (days window)
        first_seen:         unix ts when this rock was first detected
        last_seen:          unix ts when it was last reaffirmed
        persistence_s:      ``last_seen - first_seen`` in seconds
        dominant_hz:        spectral centre (Hz) — meaningful for band/peak
        amplitude:          characteristic Λ amplitude of the feature
        z_score:            how far above the running noise floor the feature is
        alignment_partners: ids of other currently-active rocks that this one
                            is phase-coherent with (above the coherence threshold)
        meta:               free-form payload (e.g. raw FFT bin, regime label)
    """
    kind: RockKind
    scale: RockScale
    dominant_hz: float
    amplitude: float
    z_score: float = 0.0
    id: str = field(default_factory=lambda: f"rock_{uuid.uuid4().hex[:10]}")
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    persistence_s: float = 0.0
    alignment_partners: List[str] = field(default_factory=list)
    meta: Dict = field(default_factory=dict)

    def reaffirm(self, ts: Optional[float] = None) -> None:
        """Mark the rock as still present at ``ts`` (defaults to now)."""
        ts = ts if ts is not None else time.time()
        self.last_seen = ts
        self.persistence_s = max(0.0, ts - self.first_seen)

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["persistence_s"] = round(d["persistence_s"], 3)
        d["dominant_hz"] = round(d["dominant_hz"], 6)
        d["amplitude"] = round(d["amplitude"], 6)
        d["z_score"] = round(d["z_score"], 4)
        return d


@dataclass
class RockEvent:
    """Lifecycle event for a Rock — published to the ThoughtBus."""
    event: RockEventKind
    rock: Rock
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return {
            "event": self.event,
            "ts": self.ts,
            "rock": self.rock.to_dict(),
        }
