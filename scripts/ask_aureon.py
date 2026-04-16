#!/usr/bin/env python3
"""
ask_aureon.py — talk to the Aureon persona vacuum.

Two modes. ONE-SHOT (pass a question as an argument):

    python scripts/ask_aureon.py "are we in a coherent state?"
    python scripts/ask_aureon.py "what should I pay attention to?" --mood mystic_love

REPL (no question argument — drops you into a conversational loop):

    python scripts/ask_aureon.py
    python scripts/ask_aureon.py --mood recurrence            # start in a mood
    echo -e "what is this?\\n/stats\\n/bye" | python scripts/ask_aureon.py

In REPL mode every turn grows the vault: the exchange is ingested as a
`conversation.turn` card, so later collapses see an ever-larger memory
and the personas can quote what was said earlier. Meta-commands:

    /help            list commands
    /stats           vault + winner histogram + action counters
    /history [n]     show the last n exchanges (default 10)
    /mood <name>     switch mood presets (ten available, 'none' to clear)
    /forget          wipe the conversation transcript (vault cards stay)
    /bye  or  /quit  exit with a summary

No API keys. A lightweight, deterministic PersonaResponseAdapter generates
persona-voiced text from (a) the persona identity embedded in the system
prompt, (b) the state cues the persona composed into its user-prompt,
and (c) if the conversation has run more than one turn, a tail of the
transcript so the answer stays continuous.
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

    The `session` reference (set by ConversationSession.attach) lets the
    adapter look at previous turns so the reply can echo continuity —
    e.g. "earlier Mystic answered you this: ..." — when we're past
    turn 1.
    """

    def __init__(self, question: str, seed: int = 0):
        self.question = str(question or "").strip()
        self._rng = random.Random(seed)
        self.session: Optional["ConversationSession"] = None

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
        continuity = self._continuity_bit()
        if continuity:
            reply_bits.append(continuity)
        if self.question:
            reply_bits.append(f"You asked: \u201c{self.question}\u201d")
            reply_bits.append(answer)
        else:
            reply_bits.append(answer)
        if closer:
            reply_bits.append(closer)

        text = " ".join(bit.rstrip() for bit in reply_bits if bit).strip()
        return LLMResponse(text=text, stop_reason="end_turn", model="persona-voice-local")

    def _continuity_bit(self) -> str:
        """If we're past turn 1, remind the operator what was said before."""
        if self.session is None or len(self.session.transcript) == 0:
            return ""
        last = self.session.transcript[-1]
        last_q = (last.get("question") or "").strip()
        last_persona = last.get("persona", "")
        if not last_q or not last_persona:
            return ""
        return f"Earlier you asked \u201c{last_q}\u201d and {last_persona} answered."

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
# ConversationSession — carries memory across turns
# ─────────────────────────────────────────────────────────────────────────────


class ConversationSession:
    """Ties together the bus, vault, vacuum, and adapter across turns."""

    MOODS = (
        "gate_clean", "lambda_drift", "dawning", "rally_drop", "mystic_love",
        "heart_paint", "velocity", "heart_field", "curiosity", "recurrence",
    )

    def __init__(self, bus: ThoughtBus, vault: AureonVault,
                 vacuum: PersonaVacuum, adapter: "PersonaResponseAdapter",
                 current_mood: Optional[str] = None):
        self.bus = bus
        self.vault = vault
        self.vacuum = vacuum
        self.adapter = adapter
        self.adapter.session = self
        self.transcript: List[Dict[str, Any]] = []
        self.current_mood = current_mood or ""

    # ─── turn mechanics ──────────────────────────────────────────────────

    def ask(self, question: str) -> Dict[str, Any]:
        question = (question or "").strip()
        if not question:
            return {}

        # Re-apply the mood at each turn so the vault state reflects the
        # intended regime (or run on whatever accumulated state there is
        # when mood is None).
        if self.current_mood:
            apply_mood(self.vault, self.current_mood, self.bus)

        # Update the adapter's question and re-inject the question line
        # into every persona's composed prompt.
        self.adapter.question = question
        inject_question_into_prompts(self.vacuum._personas, question)

        # Tighten the softmax when a mood is set so the intended persona
        # wins reliably; otherwise let the state speak.
        self.vacuum._temperature = 0.25 if self.current_mood else 1.0

        statement = self.vacuum.observe(self.vault)
        winner = self.vacuum.last_winner or "?"
        prob = self.vacuum.last_probabilities.get(winner, 0.0)
        action_rec = self.vacuum.last_action_execution
        text = statement.text if statement is not None else "(silence)"

        turn_rec: Dict[str, Any] = {
            "turn": len(self.transcript) + 1,
            "ts": time.time(),
            "mood": self.current_mood or "neutral",
            "question": question,
            "persona": winner,
            "probability": prob,
            "response": text,
            "action_kind": action_rec.action.kind if action_rec else "",
            "action_topic": action_rec.action.topic if action_rec else "",
        }
        self.transcript.append(turn_rec)

        # Persist the exchange as a vault card so memory accumulates.
        try:
            self.vault.ingest(topic="conversation.turn", payload=dict(turn_rec))
        except Exception:
            pass
        return turn_rec

    # ─── introspection ───────────────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        winners: Dict[str, int] = {}
        kinds: Dict[str, int] = {}
        topics: Dict[str, int] = {}
        for t in self.transcript:
            winners[t["persona"]] = winners.get(t["persona"], 0) + 1
            if t["action_kind"]:
                kinds[t["action_kind"]] = kinds.get(t["action_kind"], 0) + 1
            if t["action_topic"]:
                topics[t["action_topic"]] = topics.get(t["action_topic"], 0) + 1
        return {
            "turns": len(self.transcript),
            "vault_cards": len(self.vault),
            "current_mood": self.current_mood or "neutral",
            "winner_histogram": dict(sorted(winners.items(), key=lambda kv: -kv[1])),
            "action_kinds": kinds,
            "action_topics": topics,
        }

    def recent(self, n: int = 10) -> List[Dict[str, Any]]:
        return list(self.transcript[-int(max(1, n)):])


# ─────────────────────────────────────────────────────────────────────────────
# REPL — commands and loop
# ─────────────────────────────────────────────────────────────────────────────


_HELP = """\
  /help                  this help
  /stats                 show conversation + vault stats
  /history [n]           show last n exchanges (default 10)
  /mood <name|none>      change or clear mood
                         moods: gate_clean lambda_drift dawning rally_drop
                                mystic_love heart_paint velocity heart_field
                                curiosity recurrence
  /forget                clear transcript (vault cards are kept)
  /bye  /quit  /exit     exit
"""


def _print_turn(turn: Dict[str, Any]) -> None:
    mood = turn["mood"] if turn["mood"] != "neutral" else ""
    mood_s = f"  (mood={mood})" if mood else ""
    prob = turn["probability"]
    print()
    print(f"[{turn['persona']}]{mood_s}  p={prob:.3f}  turn={turn['turn']}")
    print(turn["response"])
    if turn["action_kind"]:
        print(f"\u25b8 action: {turn['action_kind']}  \u2192  {turn['action_topic']}")


def _print_stats(session: ConversationSession) -> None:
    s = session.stats()
    print()
    print(f"turns:        {s['turns']}")
    print(f"vault cards:  {s['vault_cards']}")
    print(f"current mood: {s['current_mood']}")
    if s["winner_histogram"]:
        print("winners:")
        for name, count in s["winner_histogram"].items():
            bar = "\u2588" * count
            print(f"  {name:<20s} {count:4d}  {bar}")
    if s["action_topics"]:
        print("action topics:")
        for topic, count in sorted(s["action_topics"].items(), key=lambda kv: -kv[1]):
            print(f"  {topic:<40s} {count:4d}")


def _print_history(session: ConversationSession, n: int) -> None:
    if not session.transcript:
        print("(no exchanges yet)")
        return
    for t in session.recent(n):
        snippet = (t["response"] or "").replace("\n", " ")
        if len(snippet) > 140:
            snippet = snippet[:137] + "..."
        print(f"  [{t['turn']:3d}] ({t['persona']:<18s}) {t['question']}")
        print(f"          {snippet}")


def run_repl(session: ConversationSession) -> int:
    print("aureon persona vacuum — REPL. type /help for commands, /bye to exit.")
    if session.current_mood:
        print(f"starting mood: {session.current_mood}")
    try:
        while True:
            try:
                line = input("> ").strip()
            except EOFError:
                print()
                break
            if not line:
                continue
            if line.startswith("/"):
                if not _dispatch_command(session, line):
                    break
                continue
            turn = session.ask(line)
            if turn:
                _print_turn(turn)
    finally:
        print()
        print("\u2501" * 72)
        print("session summary")
        print("\u2501" * 72)
        _print_stats(session)
    return 0


def _dispatch_command(session: ConversationSession, line: str) -> bool:
    """Run a /slash command. Return False to exit the REPL."""
    parts = line[1:].split()
    if not parts:
        return True
    cmd = parts[0].lower()
    rest = parts[1:]
    if cmd in ("bye", "quit", "exit"):
        return False
    if cmd == "help":
        print(_HELP)
    elif cmd == "stats":
        _print_stats(session)
    elif cmd == "history":
        n = int(rest[0]) if rest and rest[0].isdigit() else 10
        _print_history(session, n)
    elif cmd == "mood":
        if not rest:
            print(f"current mood: {session.current_mood or 'neutral'}")
        else:
            target = rest[0].lower()
            if target in ("none", "neutral", "clear"):
                session.current_mood = ""
                print("mood cleared.")
            elif target in ConversationSession.MOODS:
                session.current_mood = target
                print(f"mood set to {target}.")
            else:
                print(f"unknown mood {target!r}. valid: {', '.join(ConversationSession.MOODS)}")
    elif cmd == "forget":
        session.transcript.clear()
        print("transcript cleared; vault cards kept.")
    else:
        print(f"unknown command: /{cmd}. try /help")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────


def _build_session(seed: int, mood: str) -> ConversationSession:
    bus = ThoughtBus(max_memory=2000)
    vault = AureonVault()
    vault.love_amplitude = 0.4
    vault.gratitude_score = 0.5
    vault.dominant_chakra = "solar"
    vault.dominant_frequency_hz = 432.0
    vault.cortex_snapshot = {"delta": 0.1, "theta": 0.1, "alpha": 0.1, "beta": 0.1, "gamma": 0.1}

    adapter = PersonaResponseAdapter(question="", seed=seed)
    personas: Dict[str, ResonantPersona] = {
        name: cls(adapter=adapter) for name, cls in AUREON_PERSONA_REGISTRY.items()
    }
    vacuum = PersonaVacuum(
        personas=personas,
        thought_bus=bus,
        vault=vault,
        rng=random.Random(seed),
        temperature=1.0,
    )
    # Wire subscribers once; subsequent mood applications hit live subs.
    bus.subscribe("queen.source_law.cognition", vacuum._on_cognition)
    bus.subscribe("dj.track.drop", vacuum._on_drop)

    # Baseline cognition so the very first collapse has something to read.
    bus.publish(Thought(
        source="ask",
        topic="queen.source_law.cognition",
        payload={
            "coherence_gamma": 0.5, "consciousness_psi": 0.5,
            "consciousness_level": "AWARE", "confidence": 0.5,
            "node_readings": {"tiger": 0.4, "falcon": 0.4, "dolphin": 0.4, "panda": 0.4},
        },
    ))

    return ConversationSession(bus=bus, vault=vault, vacuum=vacuum,
                               adapter=adapter, current_mood=mood or "")


def main() -> int:
    ap = argparse.ArgumentParser(description="Talk to the Aureon persona vacuum.")
    ap.add_argument("question", nargs="*", help="question — free text; omit to enter REPL")
    ap.add_argument("--mood", default="", help="optional mood preset")
    ap.add_argument("--seed", type=int, default=0, help="RNG seed for reproducible collapse")
    ap.add_argument("--repl", action="store_true",
                    help="force REPL mode even if a question was provided")
    args = ap.parse_args()

    question = " ".join(args.question).strip()
    session = _build_session(seed=args.seed, mood=args.mood)

    if question and not args.repl:
        # One-shot mode — stage 1 behaviour.
        turn = session.ask(question)
        print()
        print("\u2501" * 72)
        print(f"You: {question}")
        if session.current_mood:
            print(f"(mood preset: {session.current_mood})")
        print("\u2501" * 72)
        _print_turn(turn)
        print()
        return 0

    # REPL mode.
    if question:
        # User passed both a question and --repl — answer it first, then
        # drop into the loop.
        turn = session.ask(question)
        _print_turn(turn)
    return run_repl(session)


if __name__ == "__main__":
    raise SystemExit(main())
