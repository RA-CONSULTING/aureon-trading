"""
PersonaVacuum — Ten Voices in Superposition, Collapsed on Observation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The PersonaVacuum mirrors the 10-9-1 Source Law pattern at the persona layer:

    superposition  : ten ResonantPersona instances, none speaking
    passive input  : dj.track.drop (beat energy)
                     queen.source_law.cognition (Λ, ψ, Γ, node readings)
    trigger        : persona.observe (a thought on the bus, or a direct call)
    collapse       : softmax affinity over all ten → sample one → that one speaks
    output         : persona.collapse   {winner, probabilities}
                     persona.thought    {VoiceStatement payload}
                     vault.ingest(topic="persona.thought", payload=...)

Between observations the vacuum is idle — no polling, no prompt composition.
Matches the "Pandora's box sealed" discipline of
aureon/queen/queen_source_law.py.

Gary Leckey · Aureon Institute — April 2026
"""

from __future__ import annotations

import logging
import math
import os
import random
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple

from aureon.vault.voice.aureon_personas import (
    AUREON_PERSONA_REGISTRY,
    ResonantPersona,
    build_aureon_personas,
)
from aureon.vault.voice.utterance import VoiceStatement

logger = logging.getLogger("aureon.vault.voice.persona_vacuum")

_DEFAULT_TEMPERATURE = 1.0


def _softmax(scores: List[float], temperature: float) -> List[float]:
    """Numerically stable softmax with temperature. Empty input → []."""
    if not scores:
        return []
    t = max(1e-6, float(temperature))
    scaled = [float(s) / t for s in scores]
    m = max(scaled)
    exps = [math.exp(s - m) for s in scaled]
    z = sum(exps)
    if z <= 0:
        return [1.0 / len(scores)] * len(scores)
    return [e / z for e in exps]


class PersonaVacuum:
    """Ten resonant personas held in superposition; collapses on observation."""

    def __init__(
        self,
        adapter: Any = None,
        personas: Optional[Dict[str, ResonantPersona]] = None,
        thought_bus: Any = None,
        rng: Optional[random.Random] = None,
        temperature: Optional[float] = None,
    ):
        self._personas: Dict[str, ResonantPersona] = (
            personas if personas is not None else build_aureon_personas(adapter=adapter)
        )
        self._rng = rng or random.Random()
        self._temperature = self._resolve_temperature(temperature)
        self._lock = threading.Lock()
        self._latest_cognition: Dict[str, Any] = {}
        self._latest_drop: Dict[str, Any] = {}
        self._last_winner: Optional[str] = None
        self._last_probabilities: Dict[str, float] = {}
        self._collapse_count = 0
        self._thought_bus = thought_bus
        if self._thought_bus is None:
            self._thought_bus = self._load_thought_bus()
        self._subscribed = False

    @staticmethod
    def _resolve_temperature(explicit: Optional[float]) -> float:
        if explicit is not None:
            try:
                return max(1e-6, float(explicit))
            except (TypeError, ValueError):
                pass
        raw = os.environ.get("AUREON_PERSONA_TEMPERATURE")
        if raw:
            try:
                return max(1e-6, float(raw))
            except ValueError:
                pass
        return _DEFAULT_TEMPERATURE

    @staticmethod
    def _load_thought_bus() -> Any:
        try:
            from aureon.core.aureon_thought_bus import get_thought_bus
            return get_thought_bus()
        except Exception as e:
            logger.debug("PersonaVacuum: thought bus unavailable: %s", e)
            return None

    # ─────────────────────────────────────────────────────────────────────
    # Bus wiring
    # ─────────────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Subscribe to the three trigger topics. Safe to call twice."""
        if self._subscribed or self._thought_bus is None:
            return
        try:
            self._thought_bus.subscribe("dj.track.drop", self._on_drop)
            self._thought_bus.subscribe("queen.source_law.cognition", self._on_cognition)
            self._thought_bus.subscribe("persona.observe", self._on_observe_trigger)
            self._subscribed = True
            logger.info("[PERSONA VACUUM] subscribed; %d personas in superposition", len(self._personas))
        except Exception as e:
            logger.debug("PersonaVacuum: subscribe failed: %s", e)

    def _on_drop(self, thought: Any) -> None:
        payload = getattr(thought, "payload", {}) or {}
        if isinstance(payload, dict):
            with self._lock:
                self._latest_drop = dict(payload)

    def _on_cognition(self, thought: Any) -> None:
        payload = getattr(thought, "payload", {}) or {}
        if isinstance(payload, dict):
            with self._lock:
                self._latest_cognition = dict(payload)

    def _on_observe_trigger(self, thought: Any) -> None:
        payload = getattr(thought, "payload", {}) or {}
        vault = payload.get("vault") if isinstance(payload, dict) else None
        self.observe(vault)

    # ─────────────────────────────────────────────────────────────────────
    # Collapse
    # ─────────────────────────────────────────────────────────────────────

    def observe(self, vault: Any = None) -> Optional[VoiceStatement]:
        """Open the box. Sample one persona. Have it speak. Publish. Feed back."""
        state = self._build_state(vault)
        winner_name, probs, scores = self._sample(state)
        if winner_name is None:
            return None

        persona = self._personas[winner_name]
        statement = self._safe_speak(persona, vault)

        with self._lock:
            self._collapse_count += 1
            self._last_winner = winner_name
            self._last_probabilities = dict(probs)

        self._publish_collapse(winner_name, probs, scores, state)
        if statement is not None:
            self._publish_thought(statement)
            self._feed_vault(vault, statement)
        return statement

    def _build_state(self, vault: Any) -> Dict[str, Any]:
        """Vault slice ∪ latest cognition ∪ latest drop."""
        base: Dict[str, Any] = {}
        if vault is not None:
            try:
                base = dict(ResonantPersona._extract_slice(self._any_persona(), vault))
            except Exception as e:
                logger.debug("PersonaVacuum: vault slice failed: %s", e)
        with self._lock:
            cognition = dict(self._latest_cognition)
            drop = dict(self._latest_drop)
        base["consciousness_psi"] = float(cognition.get("consciousness_psi", 0.0) or 0.0)
        base["coherence_gamma"] = float(cognition.get("coherence_gamma", 0.0) or 0.0)
        base["consciousness_level"] = str(cognition.get("consciousness_level", "") or "")
        base["confidence"] = float(cognition.get("confidence", 0.0) or 0.0)
        base["node_readings"] = dict(cognition.get("node_readings") or {})
        base["dj_drop"] = drop
        return base

    def _any_persona(self) -> ResonantPersona:
        return next(iter(self._personas.values()))

    def _sample(
        self, state: Dict[str, Any]
    ) -> Tuple[Optional[str], Dict[str, float], Dict[str, float]]:
        names: List[str] = list(self._personas.keys())
        if not names:
            return None, {}, {}
        raw: List[float] = []
        for name in names:
            try:
                score = float(self._personas[name].compute_affinity(state))
            except Exception as e:
                logger.debug("PersonaVacuum: %s affinity failed: %s", name, e)
                score = 0.0
            raw.append(max(0.0, score))
        probs = _softmax(raw, self._temperature)
        r = self._rng.random()
        cum = 0.0
        winner = names[-1]
        for name, p in zip(names, probs):
            cum += p
            if r <= cum:
                winner = name
                break
        prob_dict = {n: p for n, p in zip(names, probs)}
        score_dict = {n: s for n, s in zip(names, raw)}
        return winner, prob_dict, score_dict

    def _safe_speak(self, persona: ResonantPersona, vault: Any) -> Optional[VoiceStatement]:
        try:
            return persona.speak(vault)
        except Exception as e:
            logger.debug("PersonaVacuum: %s speak failed: %s", persona.NAME, e)
            return None

    # ─────────────────────────────────────────────────────────────────────
    # Publishing + vault feedback
    # ─────────────────────────────────────────────────────────────────────

    def _publish_collapse(
        self,
        winner: str,
        probs: Dict[str, float],
        scores: Dict[str, float],
        state: Dict[str, Any],
    ) -> None:
        if self._thought_bus is None:
            return
        try:
            from aureon.core.aureon_thought_bus import Thought
            self._thought_bus.publish(Thought(
                source="persona_vacuum",
                topic="persona.collapse",
                payload={
                    "winner": winner,
                    "probabilities": {k: round(v, 6) for k, v in probs.items()},
                    "scores": {k: round(v, 6) for k, v in scores.items()},
                    "cycle": self._collapse_count,
                    "temperature": self._temperature,
                    "trigger_state": {
                        "coherence_gamma": state.get("coherence_gamma"),
                        "consciousness_psi": state.get("consciousness_psi"),
                        "drop_energy": (state.get("dj_drop") or {}).get("energy"),
                    },
                },
            ))
        except Exception as e:
            logger.debug("PersonaVacuum: collapse publish failed: %s", e)

    def _publish_thought(self, statement: VoiceStatement) -> None:
        if self._thought_bus is None:
            return
        try:
            from aureon.core.aureon_thought_bus import Thought
            self._thought_bus.publish(Thought(
                source="persona_vacuum",
                topic="persona.thought",
                payload=statement.to_dict(),
            ))
        except Exception as e:
            logger.debug("PersonaVacuum: thought publish failed: %s", e)

    def _feed_vault(self, vault: Any, statement: VoiceStatement) -> None:
        if vault is None:
            return
        ingest: Optional[Callable] = getattr(vault, "ingest", None)
        if not callable(ingest):
            return
        try:
            ingest(topic="persona.thought", payload=statement.to_dict())
        except Exception as e:
            logger.debug("PersonaVacuum: vault ingest failed: %s", e)

    # ─────────────────────────────────────────────────────────────────────
    # Introspection
    # ─────────────────────────────────────────────────────────────────────

    @property
    def last_winner(self) -> Optional[str]:
        return self._last_winner

    @property
    def last_probabilities(self) -> Dict[str, float]:
        with self._lock:
            return dict(self._last_probabilities)

    @property
    def collapse_count(self) -> int:
        return self._collapse_count

    @property
    def temperature(self) -> float:
        return self._temperature

    @property
    def persona_names(self) -> List[str]:
        return list(self._personas.keys())


# ─────────────────────────────────────────────────────────────────────────────
# Singleton accessor
# ─────────────────────────────────────────────────────────────────────────────


_PERSONA_VACUUM: Optional[PersonaVacuum] = None
_SINGLETON_LOCK = threading.Lock()


def get_persona_vacuum() -> PersonaVacuum:
    """Return the process-wide PersonaVacuum, creating and wiring it on first use."""
    global _PERSONA_VACUUM
    with _SINGLETON_LOCK:
        if _PERSONA_VACUUM is None:
            _PERSONA_VACUUM = PersonaVacuum()
            _PERSONA_VACUUM.start()
        return _PERSONA_VACUUM


__all__ = [
    "PersonaVacuum",
    "get_persona_vacuum",
]
