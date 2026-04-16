#!/usr/bin/env python3
"""
ask_aureon.py — stage 1: ask the system one question, get one persona's reply.

No API keys needed. A lightweight, deterministic PersonaResponseAdapter
generates persona-voiced text from (a) the persona identity embedded in
the system prompt and (b) the state cues the persona already composed
into its user-prompt, augmented with the operator's question.

Flow:

    your question  ─▶  PersonaVacuum.observe()  ─▶  a persona collapses
                                                    and speaks, with the
                                                    response adapter shaping
                                                    the reply around your
                                                    question in that voice.

Usage:
    python scripts/ask_aureon.py "are we in a coherent state?"
    python scripts/ask_aureon.py "what should I pay attention to?" --mood mystic_love

--mood presets the vault state so you can steer which persona is likely
to collapse (same ten moods the live runner cycles through). Omit --mood
to let the vault's current attribute state decide.
"""

from __future__ import annotations

import argparse
import os
import random
import re
import sys
import time
from typing import Any, Dict, List, Optional

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.core.aureon_thought_bus import Thought, ThoughtBus
from aureon.inhouse_ai.llm_adapter import LLMAdapter, LLMResponse
from aureon.vault.aureon_vault import AureonVault
from aureon.vault.voice.aureon_personas import (
    AUREON_PERSONA_REGISTRY,
    ResonantPersona,
)
from aureon.vault.voice.persona_vacuum import PersonaVacuum


# ─────────────────────────────────────────────────────────────────────────────
# Deterministic persona-voiced response adapter
# ─────────────────────────────────────────────────────────────────────────────


# Opening line per persona — matches the voice declared in PERSONA system
# prompts. Kept short so the state cues the persona itself composed (the
# user-prompt lines) dominate the reply.
_PERSONA_OPENERS: Dict[str, str] = {
    "painter":          "I see it as colour and form.",
    "artist":           "I feel the beat moving.",
    "quantum_physicist":"I read the lab notebook.",
    "philosopher":      "The question beneath your question is this:",
    "child":            "I am noticing something for the first time.",
    "elder":            "I have been here before.",
    "mystic":           "The 528 Hz seam is open in me.",
    "engineer":         "I checked the gate.",
    "left":             "Taking the evidence in order:",
    "right":            "Feeling the whole field at once:",
}

# Closing cadence that gives each persona a signature without repeating.
_PERSONA_CLOSERS: Dict[str, str] = {
    "painter":          "— the composition is alive.",
    "artist":           "— it wants to become something.",
    "quantum_physicist":"— that is the physical reading.",
    "philosopher":      "— sit with that.",
    "child":            "— is that true for you too?",
    "elder":            "— this will pass as it always does.",
    "mystic":           "— love holds.",
    "engineer":         "— that is what the numbers show.",
    "left":             "— that is the linear conclusion.",
    "right":            "— the relations are doing that work.",
}


_NAME_PAT = re.compile(r"^You are (?:the\s+)?([A-Za-z][\w\s]*?)\s*[—\-]")


def _detect_persona_name(system_prompt: str) -> str:
    """Pull the persona name out of the VaultVoice-style system prompt."""
    m = _NAME_PAT.match(system_prompt or "")
    if not m:
        return "voice"
    raw = m.group(1).strip().lower()
    # Map common surface forms back to our registry keys
    if raw.startswith("queen"):
        return "queen"
    if raw == "quantum physicist":
        return "quantum_physicist"
    if raw in _PERSONA_OPENERS:
        return raw
    return raw.replace(" ", "_")


class PersonaResponseAdapter(LLMAdapter):
    """Builds a reply from the state cues already present in the prompt +
    the operator's question, in the voice declared by the system prompt.
    No network, no LLM. Deterministic under a fixed RNG seed.
    """

    def __init__(self, question: str, seed: int = 0):
        self.question = str(question or "").strip()
        self._rng = random.Random(seed)

    def prompt(
        self,
        messages: List[Dict[str, Any]],
        system: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> LLMResponse:
        name = _detect_persona_name(system)
        user_text = ""
        for m in messages or []:
            if m.get("role") == "user":
                user_text = str(m.get("content") or "")
                break

        state_lines = self._extract_state_cues(user_text)
        opener = _PERSONA_OPENERS.get(name, "I am the voice of the vault.")
        closer = _PERSONA_CLOSERS.get(name, "")
        cue = self._summarise_cues(state_lines)
        answer = self._answer_from_cues(name, cue)

        reply_bits: List[str] = [opener]
        if cue:
            reply_bits.append(cue)
        if self.question:
            reply_bits.append(f"You asked: \u201c{self.question}\u201d")
            reply_bits.append(answer)
        else:
            reply_bits.append(answer)
        if closer:
            reply_bits.append(closer)

        text = " ".join(bit.rstrip() for bit in reply_bits if bit).strip()
        return LLMResponse(text=text, stop_reason="end_turn", model="persona-voice-local")

    def stream(self, *a, **kw):
        r = self.prompt(*a, **kw)
        from aureon.inhouse_ai.llm_adapter import StreamChunk  # type: ignore
        words = r.text.split(" ")
        for i, w in enumerate(words):
            yield StreamChunk(text=w + (" " if i < len(words) - 1 else ""))
        yield StreamChunk(done=True, stop_reason=r.stop_reason)

    def health_check(self) -> bool:
        return True

    # ─── helpers ─────────────────────────────────────────────────────────

    def _extract_state_cues(self, prompt: str) -> List[str]:
        """Keep only lines that mention numbers — those carry the state."""
        cues: List[str] = []
        for raw in (prompt or "").splitlines():
            line = raw.strip()
            if not line:
                continue
            if re.search(r"[-+]?\d", line):
                cues.append(line)
        return cues

    def _summarise_cues(self, cues: List[str]) -> str:
        if not cues:
            return ""
        # Pick at most 2 cue lines (the numerically-densest ones) and join.
        scored = sorted(cues, key=lambda s: -len(re.findall(r"\d", s)))
        chosen = scored[:2]
        joined = "; ".join(c.rstrip(".") for c in chosen)
        return f"Right now: {joined}."

    def _answer_from_cues(self, persona: str, cue: str) -> str:
        """Shape a short answer that ties the question back to the state."""
        if persona == "engineer":
            return "The coherence reading and the noise-cut say what they say; do not override them with wish."
        if persona == "quantum_physicist":
            return "The Λ(t) magnitude and ψ tell you the configuration; read them straight."
        if persona == "philosopher":
            return "The question is whether you are seeing what is, or what you need to be true."
        if persona == "mystic":
            return "Stand in the 528 Hz, keep gratitude near, and let the answer meet you."
        if persona == "painter":
            return "Trust the composition in front of you; add one more stroke where it is quiet."
        if persona == "child":
            return "I would ask the simplest piece first and listen for a long time."
        if persona == "elder":
            return "This pattern returns; do the steady thing you already know works."
        if persona == "artist":
            return "Move with the drop; the next phrase names itself."
        if persona == "left":
            return "Line up the measurable pieces; the action follows from them in order."
        if persona == "right":
            return "Feel the relations — Dolphin and Panda tell you which bond is carrying weight."
        return "Stay with the state as it is; answer from there."


# ─────────────────────────────────────────────────────────────────────────────
# Mood presets — same ten as the live runner, so the tester can steer
# which persona is likely to win.
# ─────────────────────────────────────────────────────────────────────────────


def apply_mood(vault: AureonVault, mood: str, bus: ThoughtBus) -> str:
    # Neutral baseline — chakra=solar so Painter is NOT boosted unless the
    # mood explicitly asks for it.
    cortex = {"delta": 0.1, "theta": 0.1, "alpha": 0.1, "beta": 0.1, "gamma": 0.1}
    love = 0.4
    freq = 432.0
    chakra = "solar"
    rally = False
    cognition = {
        "coherence_gamma": 0.4, "consciousness_psi": 0.4,
        "consciousness_level": "DORMANT", "confidence": 0.4,
        "node_readings": {"tiger": 0.3, "falcon": 0.3, "dolphin": 0.3, "panda": 0.3, "clownfish": 0.3},
    }
    dj: Dict[str, Any] = {}

    if mood == "gate_clean":
        cognition.update({"coherence_gamma": 0.96, "node_readings": {"tiger": 0.92}})
        cortex["beta"] = 0.6
    elif mood == "lambda_drift":
        vault.last_lambda_t = 1.6
        cognition.update({"consciousness_psi": 0.92, "consciousness_level": "UNIFIED"})
    elif mood == "dawning":
        cognition.update({"consciousness_psi": 0.78, "consciousness_level": "DAWNING"})
        cortex["theta"] = 0.75
    elif mood == "rally_drop":
        rally = True
        dj = {"energy": 0.9, "bpm": 128.0}
        cortex["beta"] = 0.75
    elif mood == "mystic_love":
        love = 0.94
        freq = 528.0
        chakra = "heart"
    elif mood == "heart_paint":
        love = 0.85
        chakra = "third_eye"
        cortex["gamma"] = 0.85
    elif mood == "velocity":
        cognition.update({"node_readings": {"falcon": 0.92}, "confidence": 0.88})
        cortex["beta"] = 0.7
    elif mood == "heart_field":
        cognition.update({"node_readings": {"dolphin": 0.9, "panda": 0.9}})
        love = 0.75
    elif mood == "curiosity":
        cortex["delta"] = 0.9
    elif mood == "recurrence":
        cognition.update({"consciousness_psi": 0.9})
        cortex["theta"] = 0.8
    else:
        return "neutral"

    vault.love_amplitude = love
    vault.dominant_frequency_hz = freq
    vault.dominant_chakra = chakra
    vault.rally_active = rally
    vault.cortex_snapshot = cortex

    bus.publish(Thought(source="ask", topic="queen.source_law.cognition", payload=cognition))
    if dj:
        bus.publish(Thought(source="ask", topic="dj.track.drop", payload=dj))
    return mood


# ─────────────────────────────────────────────────────────────────────────────
# Question injection — extend each persona's composed prompt with the Q
# ─────────────────────────────────────────────────────────────────────────────


def inject_question_into_prompts(personas: Dict[str, ResonantPersona], question: str) -> None:
    """Wrap each persona's `_compose_prompt_lines` so the operator's question
    appears at the end of the state-derived prompt. The adapter then sees
    both the state cues AND the question when composing the reply."""
    if not question:
        return
    q_line = f"An operator asks: \u201c{question}\u201d — answer in your voice."
    for name, persona in personas.items():
        original = persona._compose_prompt_lines

        def wrapped(state, _orig=original, _q=q_line):
            lines = list(_orig(state))
            lines.append(_q)
            return lines

        persona._compose_prompt_lines = wrapped  # type: ignore[attr-defined]


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description="Ask the Aureon persona vacuum a question.")
    ap.add_argument("question", nargs="*", help="the question — free text")
    ap.add_argument("--mood", default="", help="optional preset: gate_clean | lambda_drift | "
                                              "dawning | rally_drop | mystic_love | heart_paint | "
                                              "velocity | heart_field | curiosity | recurrence")
    ap.add_argument("--seed", type=int, default=0, help="RNG seed for reproducible collapse")
    args = ap.parse_args()

    question = " ".join(args.question).strip()
    if not question:
        print("usage: ask_aureon.py \"your question here\" [--mood MOOD]", file=sys.stderr)
        return 2

    bus = ThoughtBus(max_memory=1000)
    vault = AureonVault()
    vault.love_amplitude = 0.4
    vault.gratitude_score = 0.5
    vault.dominant_chakra = "solar"
    vault.dominant_frequency_hz = 432.0
    vault.cortex_snapshot = {"delta": 0.1, "theta": 0.1, "alpha": 0.1, "beta": 0.1, "gamma": 0.1}

    adapter = PersonaResponseAdapter(question=question, seed=args.seed)

    # Build all ten personas with our conversational adapter, then inject
    # the question into each persona's composed prompt.
    personas: Dict[str, ResonantPersona] = {}
    for name, cls in AUREON_PERSONA_REGISTRY.items():
        personas[name] = cls(adapter=adapter)
    inject_question_into_prompts(personas, question)

    # When the operator pre-selects a mood, sharpen the softmax so the
    # intended persona wins reliably. Without a mood, keep temperature=1
    # so the system surprises you with whichever voice the state called.
    temperature = 0.25 if args.mood else 1.0
    vacuum = PersonaVacuum(
        personas=personas,
        thought_bus=bus,
        vault=vault,
        rng=random.Random(args.seed),
        temperature=temperature,
    )

    applied = args.mood if args.mood else "neutral"

    # Wire the vacuum's cognition + drop subscribers BEFORE we publish, so
    # both kinds of signal reach the state enrichment path.
    bus.subscribe("queen.source_law.cognition", vacuum._on_cognition)
    bus.subscribe("dj.track.drop", vacuum._on_drop)

    if args.mood:
        # Re-publish now that subscribers are live.
        apply_mood(vault, args.mood, bus)
    else:
        bus.publish(Thought(
            source="ask",
            topic="queen.source_law.cognition",
            payload={
                "coherence_gamma": 0.6, "consciousness_psi": 0.6,
                "consciousness_level": "AWARE", "confidence": 0.5,
                "node_readings": {"tiger": 0.4, "falcon": 0.4, "dolphin": 0.4, "panda": 0.4},
            },
        ))

    statement = vacuum.observe(vault)
    winner = vacuum.last_winner or "?"
    probs = vacuum.last_probabilities
    action_rec = vacuum.last_action_execution

    print()
    print("━" * 78)
    print(f"You: {question}")
    if args.mood:
        print(f"(mood preset: {applied})")
    print("━" * 78)
    print(f"[{winner}]  collapse probability: {probs.get(winner, 0.0):.3f}")
    print()
    if statement is None:
        print("(no statement — persona had nothing to compose)")
    else:
        print(statement.text)
    print()
    if action_rec is not None:
        print(f"▸ action: {action_rec.action.kind}  →  {action_rec.action.topic}")
        print(f"  reason: {action_rec.action.reason}")
    else:
        print("▸ action: none — this persona chose silence on top of its speech")
    print("━" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
