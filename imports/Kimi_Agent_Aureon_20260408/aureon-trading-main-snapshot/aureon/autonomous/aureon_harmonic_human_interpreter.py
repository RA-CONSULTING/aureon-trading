#!/usr/bin/env python3
"""
Harmonic interpretation layer for human voice/text commands.

This does not perform DSP. It maps transcript patterns into a small,
stable emotional/coherence model so the voice cognition layer can use
the repo's harmonic language without depending on heavy runtime systems.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List


LOVE_FREQUENCY = 528.0
QUEEN_FREQUENCY = 963.0
EARTH_FREQUENCY = 7.83


@dataclass
class HarmonicInterpretation:
    transcript: str
    tone: str
    intent_energy: str
    coherence: float
    urgency: float
    resonance_band_hz: float
    tags: List[str]

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


class HarmonicHumanInterpreter:
    def interpret(self, transcript: str) -> HarmonicInterpretation:
        text = (transcript or "").strip()
        lower = text.lower()

        tags: List[str] = []
        coherence = 0.72
        urgency = 0.25
        band = LOVE_FREQUENCY
        tone = "steady"
        intent_energy = "directive"

        if any(word in lower for word in ["help", "please", "can you", "could you"]):
            tone = "collaborative"
            tags.append("polite")
            coherence += 0.05

        if any(word in lower for word in ["stop", "now", "immediately", "emergency", "urgent"]):
            tone = "urgent"
            intent_energy = "protective"
            urgency = 0.95
            band = QUEEN_FREQUENCY
            tags.append("safety")

        if any(word in lower for word in ["what do you understand", "what did you hear", "explain", "think"]):
            tone = "reflective"
            intent_energy = "meta"
            band = EARTH_FREQUENCY * 8
            tags.append("meta")

        if any(word in lower for word in ["search", "find", "inspect", "open", "read"]):
            tags.append("exploration")
            coherence += 0.04

        if any(word in lower for word in ["click", "press", "move", "type", "enter"]):
            tags.append("desktop")
            intent_energy = "actuation"

        if any(word in lower for word in ["that", "it", "there", "this"]):
            tags.append("contextual_reference")
            coherence -= 0.12

        if len(text.split()) <= 2:
            coherence -= 0.1
            tags.append("short_utterance")

        coherence = max(0.0, min(1.0, coherence))

        if coherence >= 0.82:
            tags.append("clear_resonance")
        elif coherence <= 0.55:
            tags.append("clarification_needed")

        return HarmonicInterpretation(
            transcript=text,
            tone=tone,
            intent_energy=intent_energy,
            coherence=coherence,
            urgency=urgency,
            resonance_band_hz=band,
            tags=tags,
        )
