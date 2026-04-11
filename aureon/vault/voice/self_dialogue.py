"""
SelfDialogueEngine — The Vault Talks to Itself
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"It can write its own prompts and conversations with its own thought
 processes not scripted as it chooses."

The dialogue engine orchestrates exchanges between multiple `VaultVoice`
personas. Each turn:

  1. The ChoiceGate decides whether to speak at all.
  2. If yes, the engine picks a speaker (the gate's preferred voice,
     or a weighted-random roll from the active voices).
  3. The speaker composes a self-authored prompt from vault state
     and generates a statement.
  4. The statement is fed back into the vault as a new content card
     — so the NEXT voice sees the previous voice's words in its
     own state extraction.
  5. A listener (different voice) composes its own self-authored
     prompt from the newly-updated vault and responds.
  6. The listener's response is also fed back.
  7. The full Utterance is returned, recorded, and published to
     the ThoughtBus as 'vault.voice.utterance'.

This is a real recursive feedback loop: each voice's output mutates
the vault state that the next voice reads from.
"""

from __future__ import annotations

import logging
import random
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

from aureon.vault.voice.choice_gate import ChoiceGate, ChoiceGateDecision
from aureon.vault.voice.utterance import Utterance, VoiceStatement
from aureon.vault.voice.vault_voice import VaultVoice, build_all_voices

logger = logging.getLogger("aureon.vault.dialogue")


# ─────────────────────────────────────────────────────────────────────────────
# Selection weights — used when the gate has no strong preference
# ─────────────────────────────────────────────────────────────────────────────


DEFAULT_VOICE_WEIGHTS: Dict[str, float] = {
    "vault":     0.10,
    "queen":     0.25,
    "miner":     0.15,
    "scout":     0.10,
    "council":   0.15,
    "architect": 0.10,
    "lover":     0.15,
}


# ─────────────────────────────────────────────────────────────────────────────
# SelfDialogueEngine
# ─────────────────────────────────────────────────────────────────────────────


class SelfDialogueEngine:
    """
    Manages the vault's conversation with itself.

    Usage:
        engine = SelfDialogueEngine(vault=my_vault)
        utterance = engine.converse()
        if utterance:
            print(utterance.full_text)
    """

    def __init__(
        self,
        vault: Any,
        voices: Optional[Dict[str, VaultVoice]] = None,
        choice_gate: Optional[ChoiceGate] = None,
        thought_bus: Any = None,
        adapter: Any = None,
        voice_weights: Optional[Dict[str, float]] = None,
        max_history: int = 200,
        rng_seed: Optional[int] = None,
    ):
        self.vault = vault
        self.voices = voices if voices is not None else build_all_voices(adapter=adapter)
        self.gate = choice_gate or ChoiceGate()
        self.voice_weights = voice_weights or DEFAULT_VOICE_WEIGHTS.copy()
        self.max_history = int(max_history)
        self._history: List[Utterance] = []
        self._total_utterances: int = 0
        self._total_decisions: int = 0
        self._lock = threading.RLock()
        self._rng = random.Random(rng_seed) if rng_seed is not None else random.Random()

        self._thought_bus = thought_bus
        if self._thought_bus is None:
            self._wire_thought_bus()

    def _wire_thought_bus(self) -> None:
        try:
            from aureon.core.aureon_thought_bus import get_thought_bus
            self._thought_bus = get_thought_bus()
        except Exception:
            self._thought_bus = None

    # ─────────────────────────────────────────────────────────────────────
    # Main entry — one turn of self-dialogue
    # ─────────────────────────────────────────────────────────────────────

    def converse(self) -> Optional[Utterance]:
        """
        Run one turn of self-dialogue. Returns the full Utterance or
        None if the choice gate said stay silent.
        """
        with self._lock:
            self._total_decisions += 1

            # 1. Does the vault want to speak right now?
            decision = self.gate.decide(self.vault)
            if not decision.should_speak:
                return None

            # 2. Pick the speaker
            speaker_name = self._pick_speaker(decision)
            speaker = self.voices.get(speaker_name) or self.voices["vault"]

            # 3. Speaker composes self-authored prompt and generates response
            try:
                fp_before = self.vault.fingerprint()
            except Exception:
                fp_before = ""

            statement = speaker.speak(self.vault)
            if statement is None:
                return None

            # 4. Feed the speaker's statement back into the vault
            self._feedback_into_vault(speaker_name, statement)

            # 5. Pick a listener (different voice) and respond
            listener_name = self._pick_listener(speaker_name, decision)
            listener = self.voices.get(listener_name) or self.voices["vault"]
            response = listener.speak(self.vault)

            # 6. Feed the listener's response back too
            if response is not None:
                self._feedback_into_vault(listener_name, response)

            try:
                fp_after = self.vault.fingerprint()
            except Exception:
                fp_after = ""

            # 7. Record the full utterance
            utterance = Utterance(
                utterance_id=uuid.uuid4().hex[:8],
                timestamp=time.time(),
                speaker=speaker_name,
                listener=listener_name,
                statement=statement,
                response=response,
                chosen=True,
                reasoning=decision.reasoning,
                urgency=decision.urgency,
                vault_fingerprint_before=fp_before,
                vault_fingerprint_after=fp_after,
            )

            self._history.append(utterance)
            if len(self._history) > self.max_history:
                self._history = self._history[-self.max_history:]
            self._total_utterances += 1

            # 8. Publish
            self._publish(utterance, decision)

            return utterance

    # ─────────────────────────────────────────────────────────────────────
    # Speaker / listener selection
    # ─────────────────────────────────────────────────────────────────────

    def _pick_speaker(self, decision: ChoiceGateDecision) -> str:
        """Pick the speaker — preferred voice, then weighted random."""
        preferred = decision.preferred_voice
        if preferred and preferred in self.voices:
            return preferred
        return self._weighted_choice(self.voices.keys())

    def _pick_listener(self, speaker_name: str, decision: ChoiceGateDecision) -> str:
        """Pick a listener — different from speaker, weighted by complement."""
        candidates = [name for name in self.voices.keys() if name != speaker_name]
        if not candidates:
            return speaker_name
        return self._weighted_choice(candidates)

    def _weighted_choice(self, names) -> str:
        names = list(names)
        weights = [self.voice_weights.get(n, 0.1) for n in names]
        total = sum(weights)
        if total <= 0:
            return names[0]
        r = self._rng.random() * total
        acc = 0.0
        for name, w in zip(names, weights):
            acc += w
            if r <= acc:
                return name
        return names[-1]

    # ─────────────────────────────────────────────────────────────────────
    # Human-directed conversation
    # ─────────────────────────────────────────────────────────────────────

    def respond_to_human(
        self,
        message: str,
        voice_name: Optional[str] = None,
    ) -> Optional[Utterance]:
        """
        The vault responds to a message from a human.

        The message is first ingested into the vault as a `human.message`
        card with maximum love_weight, so every downstream voice sees it
        through its own state extraction. Then the chosen voice composes
        a prompt that includes the human message alongside its live
        vault state, and generates a response.

        If `voice_name` is None, the gate's current preferred voice is
        used (derived from vault state).
        """
        message = (message or "").strip()
        if not message:
            return None

        with self._lock:
            self._total_decisions += 1

            # 1. Ingest the message into the vault so downstream state
            # extraction sees it. High love_weight so the Fibonacci
            # shuffler prioritises it on the next replay.
            try:
                pre_love = float(getattr(self.vault, "love_amplitude", 0.0) or 0.0)
            except Exception:
                pre_love = 0.0
            try:
                self.vault.love_amplitude = max(pre_love, 0.6)  # bump if low
                self.vault.ingest(
                    topic="human.message",
                    payload={
                        "text": message[:2000],
                        "timestamp": time.time(),
                    },
                    category="human_message",
                )
            except Exception as e:
                logger.debug("human message ingest failed: %s", e)

            # 2. Pick a speaker
            if voice_name and voice_name in self.voices:
                speaker_name = voice_name
            else:
                decision = self.gate.decide(self.vault)
                speaker_name = decision.preferred_voice or "vault"
                if speaker_name not in self.voices:
                    speaker_name = "vault"
            speaker = self.voices[speaker_name]

            # 3. Compose a hybrid prompt: persona's usual lines + the human
            # message. We do this by monkey-augmenting speak() for one call.
            try:
                fp_before = self.vault.fingerprint()
            except Exception:
                fp_before = ""

            statement = self._speak_with_human_context(speaker, message)
            if statement is None:
                return None

            # 4. Feed the response back into the vault
            self._feedback_into_vault(speaker_name, statement)

            try:
                fp_after = self.vault.fingerprint()
            except Exception:
                fp_after = ""

            # 5. Record the utterance — for a human-directed response we
            # put "human" as the speaker and the voice as the listener
            utterance = Utterance(
                utterance_id=uuid.uuid4().hex[:8],
                timestamp=time.time(),
                speaker="human",
                listener=speaker_name,
                statement=VoiceStatement(
                    voice="human",
                    text=message,
                    vault_fingerprint=fp_before,
                    prompt_used=message,
                ),
                response=statement,
                chosen=True,
                reasoning=f"human_message → {speaker_name}",
                urgency=1.0,
                vault_fingerprint_before=fp_before,
                vault_fingerprint_after=fp_after,
            )

            self._history.append(utterance)
            if len(self._history) > self.max_history:
                self._history = self._history[-self.max_history:]
            self._total_utterances += 1

            # 6. Publish
            from aureon.vault.voice.choice_gate import ChoiceGateDecision
            self._publish(
                utterance,
                ChoiceGateDecision(
                    should_speak=True,
                    urgency=1.0,
                    reasoning="human_message",
                    preferred_voice=speaker_name,
                ),
            )

            return utterance

    def _speak_with_human_context(
        self,
        voice: VaultVoice,
        human_message: str,
    ) -> Optional[VoiceStatement]:
        """
        Call `voice.speak(vault)` with the human's message folded into the
        composed prompt. We do this by temporarily monkey-patching the
        voice's _compose_prompt_lines to append the human's message as
        the final line, then restoring the original method.
        """
        original = voice._compose_prompt_lines

        def composed_with_human(state):
            lines = original(state)
            lines.append("")
            lines.append("A human is speaking to me now. Their message:")
            lines.append(f'    "{human_message[:1000]}"')
            lines.append(
                "Respond directly to them as this voice, using my current state. "
                "Keep it to 2–4 sentences."
            )
            return lines

        voice._compose_prompt_lines = composed_with_human  # type: ignore[method-assign]
        try:
            return voice.speak(self.vault)
        finally:
            voice._compose_prompt_lines = original  # type: ignore[method-assign]

    def speak_as(self, voice_name: str) -> Optional[Utterance]:
        """
        Force a specific voice to speak right now, bypassing the gate.
        Useful for UI "nudge this voice to speak" buttons.
        """
        if voice_name not in self.voices:
            return None

        with self._lock:
            self._total_decisions += 1
            try:
                fp_before = self.vault.fingerprint()
            except Exception:
                fp_before = ""

            speaker = self.voices[voice_name]
            statement = speaker.speak(self.vault)
            if statement is None:
                return None
            self._feedback_into_vault(voice_name, statement)

            # Pick a different voice as listener via weighted choice
            candidates = [n for n in self.voices.keys() if n != voice_name]
            listener_name = self._weighted_choice(candidates) if candidates else voice_name
            listener = self.voices.get(listener_name) or self.voices["vault"]
            response = listener.speak(self.vault)
            if response is not None:
                self._feedback_into_vault(listener_name, response)

            try:
                fp_after = self.vault.fingerprint()
            except Exception:
                fp_after = ""

            utterance = Utterance(
                utterance_id=uuid.uuid4().hex[:8],
                timestamp=time.time(),
                speaker=voice_name,
                listener=listener_name,
                statement=statement,
                response=response,
                chosen=True,
                reasoning=f"forced_speak({voice_name})",
                urgency=1.0,
                vault_fingerprint_before=fp_before,
                vault_fingerprint_after=fp_after,
            )
            self._history.append(utterance)
            if len(self._history) > self.max_history:
                self._history = self._history[-self.max_history:]
            self._total_utterances += 1
            return utterance

    # ─────────────────────────────────────────────────────────────────────
    # Feedback into vault
    # ─────────────────────────────────────────────────────────────────────

    def _feedback_into_vault(self, voice_name: str, statement: VoiceStatement) -> None:
        try:
            self.vault.ingest(
                topic=f"vault.voice.{voice_name}",
                payload={
                    "voice": voice_name,
                    "text": statement.text,
                    "prompt_used": statement.prompt_used,
                    "vault_fingerprint": statement.vault_fingerprint,
                    "model": statement.model,
                },
                category="vault_voice",
            )
        except Exception as e:
            logger.debug("feedback into vault failed: %s", e)

    # ─────────────────────────────────────────────────────────────────────
    # Publishing
    # ─────────────────────────────────────────────────────────────────────

    def _publish(self, utterance: Utterance, decision: ChoiceGateDecision) -> None:
        if not self._thought_bus:
            return
        try:
            from aureon.core.aureon_thought_bus import Thought
            self._thought_bus.publish(Thought(
                source="vault.dialogue",
                topic="vault.voice.utterance",
                payload={
                    "utterance_id": utterance.utterance_id,
                    "speaker": utterance.speaker,
                    "listener": utterance.listener,
                    "urgency": utterance.urgency,
                    "reasoning": utterance.reasoning,
                    "statement_text": utterance.statement.text if utterance.statement else "",
                    "response_text": utterance.response.text if utterance.response else "",
                    "vault_fingerprint_before": utterance.vault_fingerprint_before,
                    "vault_fingerprint_after": utterance.vault_fingerprint_after,
                    "preferred_voice": decision.preferred_voice,
                },
            ))
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────────────
    # Status / introspection
    # ─────────────────────────────────────────────────────────────────────

    @property
    def history(self) -> List[Utterance]:
        with self._lock:
            return list(self._history)

    def last_utterance(self) -> Optional[Utterance]:
        with self._lock:
            return self._history[-1] if self._history else None

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_decisions": self._total_decisions,
                "total_utterances": self._total_utterances,
                "speak_rate": (
                    self._total_utterances / max(self._total_decisions, 1)
                ),
                "history_size": len(self._history),
                "voices": list(self.voices.keys()),
                "gate": self.gate.get_status(),
                "last_utterance": (
                    self._history[-1].to_dict() if self._history else None
                ),
            }
