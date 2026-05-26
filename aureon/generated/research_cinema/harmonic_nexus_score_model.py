"""Generated Harmonic Nexus score model for Harmonic Nexus Score.

This file was generated from the online research cinema packet. It is a
deterministic helper, not trading authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


SOURCE_COUNT = 5
TOPIC = 'Harmonic Nexus Score'


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class HarmonicNexusScoreInputs:
    source_strength: float
    coherence_agreement: float
    repeatability: float
    friction_feasibility: float
    contradiction_handling: float

    def normalized(self) -> "HarmonicNexusScoreInputs":
        return HarmonicNexusScoreInputs(
            source_strength=_clamp01(self.source_strength),
            coherence_agreement=_clamp01(self.coherence_agreement),
            repeatability=_clamp01(self.repeatability),
            friction_feasibility=_clamp01(self.friction_feasibility),
            contradiction_handling=_clamp01(self.contradiction_handling),
        )


def harmonic_nexus_score(inputs: HarmonicNexusScoreInputs) -> float:
    """Return 0-100 bounded evidence/coherence score."""
    n = inputs.normalized()
    raw = (
        0.30 * n.source_strength
        + 0.25 * n.coherence_agreement
        + 0.20 * n.repeatability
        + 0.15 * n.friction_feasibility
        + 0.10 * n.contradiction_handling
    )
    return round(100.0 * _clamp01(raw), 6)


def score_breakdown(inputs: HarmonicNexusScoreInputs) -> Dict[str, float]:
    n = inputs.normalized()
    return {
        "source_strength": round(30.0 * n.source_strength, 6),
        "coherence_agreement": round(25.0 * n.coherence_agreement, 6),
        "repeatability": round(20.0 * n.repeatability, 6),
        "friction_feasibility": round(15.0 * n.friction_feasibility, 6),
        "contradiction_handling": round(10.0 * n.contradiction_handling, 6),
        "score": harmonic_nexus_score(n),
    }


def build_default_inputs() -> HarmonicNexusScoreInputs:
    """Build conservative defaults from packet source count."""
    source_strength = min(1.0, SOURCE_COUNT / 5.0)
    return HarmonicNexusScoreInputs(
        source_strength=source_strength,
        coherence_agreement=0.5,
        repeatability=0.0,
        friction_feasibility=0.5,
        contradiction_handling=0.5,
    )


__all__ = [
    "HarmonicNexusScoreInputs",
    "harmonic_nexus_score",
    "score_breakdown",
    "build_default_inputs",
]
