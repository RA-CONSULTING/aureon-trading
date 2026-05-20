"""
CognitionPipeline — the seven-pane prism.

The pipeline is peer to the matcher, not its parent. A prompt enters,
seven phases bend it, and one colour falls out the far side. Each phase
publishes a Thought on the bus with ``trace_id`` linking back to Boot so
the CognitiveDashboard renders the cascade live.

M0 walking skeleton: every phase runs stubbed but publishes faithfully.
Real LLM, vault I/O, enrichment, Λ coupling, and conscience veto land
incrementally (M1–M7) without touching the orchestrator's shape.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, Optional

from aureon.cognition.schemas import (
    Branch,
    CollapsedOutput,
    ComplexityReading,
    DispatchResult,
    Enrichment,
    GoalEnvelope,
    StructuredIntent,
    VaultLookup,
)

logger = logging.getLogger("aureon.cognition.pipeline")

try:
    from aureon.core.aureon_thought_bus import Thought, get_thought_bus
    _HAS_THOUGHT_BUS = True
except Exception:
    get_thought_bus = None  # type: ignore[assignment]
    Thought = None  # type: ignore[assignment,misc]
    _HAS_THOUGHT_BUS = False


_PHASE_TOPICS = {
    "boot": "cognition.phase.boot",
    "comprehend": "cognition.phase.comprehend",
    "vault_check": "cognition.phase.vault_check",
    "external_fallback": "cognition.phase.external_fallback",
    "complexity_gate": "cognition.phase.complexity_gate",
    "multiverse": "cognition.phase.multiverse",
    "coherence_collapse": "cognition.phase.coherence_collapse",
    "complete": "cognition.complete",
}


class CognitionPipeline:
    """Seven-phase goal router. Peer to the matcher."""

    def __init__(self, bus: Any = None, source: str = "aureon.cognition") -> None:
        if bus is not None:
            self.bus = bus
        elif _HAS_THOUGHT_BUS and get_thought_bus is not None:
            self.bus = get_thought_bus()
        else:
            self.bus = None
        self.source = source

    # ------------------------------------------------------------------
    # Public entrypoint
    # ------------------------------------------------------------------

    def run(
        self,
        prompt: str,
        peer_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> GoalEnvelope:
        """Run a prompt through all seven phases. Returns the final envelope."""

        env = self._boot(prompt, peer_id=peer_id, session_id=session_id)
        env = self._comprehend(env)
        env = self._vault_check(env)
        env = self._external_fallback(env)
        env = self._complexity_gate(env)
        env = self._multiverse(env)
        env = self._coherence_collapse(env)
        self._emit_complete(env)
        return env

    # ------------------------------------------------------------------
    # Phase 1 — Boot
    # ------------------------------------------------------------------

    def _boot(
        self,
        prompt: str,
        peer_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> GoalEnvelope:
        env = GoalEnvelope(
            trace_id=uuid.uuid4().hex,
            prompt=prompt,
            submitted_at=time.time(),
            peer_id=peer_id,
            session_id=session_id,
        )
        self._publish(env, "boot", {"prompt": prompt, "peer_id": peer_id, "session_id": session_id})
        return env

    # ------------------------------------------------------------------
    # Phase 2 — Comprehend (M0 stub: first-word verb)
    # ------------------------------------------------------------------

    def _comprehend(self, env: GoalEnvelope) -> GoalEnvelope:
        tokens = (env.prompt or "").strip().split()
        primary_verb = tokens[0].lower() if tokens else "unknown"
        objects = [t for t in tokens[1:] if t.isalnum()]
        env.intent = StructuredIntent(
            primary_verb=primary_verb,
            verb_chain=[primary_verb] if primary_verb != "unknown" else [],
            objects=objects,
            domain_category="general",
            wants_creative=False,
            raw_llm_text="",
        )
        self._publish(env, "comprehend", {"intent": env.intent.to_dict(), "model": "m0-stub"})
        return env

    # ------------------------------------------------------------------
    # Phase 3 — Vault check (M0 stub: always miss)
    # ------------------------------------------------------------------

    def _vault_check(self, env: GoalEnvelope) -> GoalEnvelope:
        env.vault_hit = VaultLookup(hit=False, signature="", warmth=0.0)
        self._publish(env, "vault_check", env.vault_hit.to_dict())
        return env

    # ------------------------------------------------------------------
    # Phase 4 — External fallback (M0 stub: no-op)
    # ------------------------------------------------------------------

    def _external_fallback(self, env: GoalEnvelope) -> GoalEnvelope:
        env.enrichment = Enrichment(sources=[], snippets=[], ttl_expires_at=0.0)
        self._publish(env, "external_fallback", {"cache_hit": False, "snippet_count": 0, "skipped": True})
        return env

    # ------------------------------------------------------------------
    # Phase 5 — Complexity gate (M0 stub: N=1)
    # ------------------------------------------------------------------

    def _complexity_gate(self, env: GoalEnvelope) -> GoalEnvelope:
        env.complexity = ComplexityReading(
            n_branches=1,
            score=0.0,
            components={"token_depth": 0.0, "llm_self_rate": 0.0, "lambda_psi": 0.0},
        )
        self._publish(env, "complexity_gate", env.complexity.to_dict())
        return env

    # ------------------------------------------------------------------
    # Phase 6 — Multiverse (M0 stub: single passthrough branch)
    # ------------------------------------------------------------------

    def _multiverse(self, env: GoalEnvelope) -> GoalEnvelope:
        candidate_text = env.prompt
        branch = Branch(
            branch_id=uuid.uuid4().hex[:8],
            persona="default",
            temperature=0.0,
            seed=0,
            candidate_text=candidate_text,
            candidate_intent=env.intent,
            lambda_snapshot=0.0,
            latency_ms=0.0,
        )
        env.branches = [branch]
        self._publish(env, "multiverse", {"n_branches": 1, "branch_ids": [branch.branch_id]})
        return env

    # ------------------------------------------------------------------
    # Phase 7 — Coherence collapse (M0 stub: trivial pick)
    # ------------------------------------------------------------------

    def _coherence_collapse(self, env: GoalEnvelope) -> GoalEnvelope:
        if not env.branches:
            env.collapsed = CollapsedOutput(winning_branch_id="", text="", intent=env.intent)
        else:
            winner = env.branches[0]
            env.collapsed = CollapsedOutput(
                winning_branch_id=winner.branch_id,
                text=winner.candidate_text,
                intent=winner.candidate_intent,
                lambda_at_collapse=winner.lambda_snapshot,
                conscience_verdict="APPROVED",
                synthesized=False,
                runner_up_ids=[],
            )
        env.dispatch = DispatchResult(peer_name="stubbed", status="stubbed", payload={})
        self._publish(env, "coherence_collapse", env.collapsed.to_dict())
        return env

    # ------------------------------------------------------------------
    # Transport
    # ------------------------------------------------------------------

    def _emit_complete(self, env: GoalEnvelope) -> None:
        self._publish(env, "complete", env.to_dict())

    def _publish(self, env: GoalEnvelope, phase_key: str, payload: Dict[str, Any]) -> None:
        topic = _PHASE_TOPICS[phase_key]
        parent_id = self._last_thought_id(env)
        if self.bus is None or Thought is None:
            logger.debug("bus unavailable; dropping thought topic=%s trace=%s", topic, env.trace_id)
            env.phase_thought_ids[phase_key] = ""
            return
        try:
            thought = Thought(
                source=self.source,
                topic=topic,
                trace_id=env.trace_id,
                parent_id=parent_id,
                payload=dict(payload),
                meta={"phase": phase_key},
            )
            published = self.bus.publish(thought)
            env.phase_thought_ids[phase_key] = getattr(published, "id", "") or ""
        except Exception as exc:
            logger.exception("failed to publish %s thought: %s", topic, exc)
            env.errors.append({"phase": phase_key, "error": str(exc)})
            env.phase_thought_ids[phase_key] = ""

    @staticmethod
    def _last_thought_id(env: GoalEnvelope) -> Optional[str]:
        if not env.phase_thought_ids:
            return None
        for key in reversed(list(env.phase_thought_ids.keys())):
            tid = env.phase_thought_ids[key]
            if tid:
                return tid
        return None


def run_goal(
    prompt: str,
    bus: Any = None,
    peer_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> GoalEnvelope:
    """Convenience one-shot: instantiate a pipeline and run the prompt."""

    return CognitionPipeline(bus=bus).run(prompt, peer_id=peer_id, session_id=session_id)
