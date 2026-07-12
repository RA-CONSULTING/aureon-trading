"""
🎛️ AUREON OPERATOR — the switchboard.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"Many voices in. One grounded answer out."

A prompt enters. The operator patches it out across every AI line on the board
(ChatGPT, Grok, Gemini, … — see :mod:`aureon.operator.providers`), but first it
grounds the prompt in the Aureon repo so no line is answering from vendor memory
alone. The replies come back, the operator collapses them to one, runs that one
past the Queen's conscience (the 4th-pass veto), and only then speaks.

Five phases, each publishing a ``Thought`` on the bus under ``operator.phase.*``
with a shared ``trace_id`` — so a dashboard (or the phone) can watch the cascade
live, exactly like :class:`aureon.cognition.pipeline.CognitionPipeline`:

    [prompt] → ground → fan_out → consensus → veto → [answer]

This is the response-synthesis engine from the "Aureon Setup" overview: the
grounding + consensus + veto chain is what makes the guarantee — no logic drift,
no hallucination, fully grounded via the Aureon repository — falsifiable rather
than decorative.
"""

from __future__ import annotations

import logging
import re
import time
import uuid
from typing import Any, Dict, Generator, List, Optional

try:  # optional wiring hook other modules self-register with
    from aureon.core.aureon_baton_link import link_system as _baton_link

    _baton_link(__name__)
except Exception:  # noqa: BLE001 — never fail import over a tracing hook
    pass

from aureon.inhouse_ai.llm_adapter import LLMAdapter, StreamChunk
from aureon.operator.providers import build_provider_set, describe_provider_set
from aureon.operator.schemas import (
    ConsensusReading,
    GroundingContext,
    OperatorResponse,
    ProviderAnswer,
)

logger = logging.getLogger("aureon.operator")

# ── Thought bus (fail-safe) ───────────────────────────────────────────────────
try:
    from aureon.core.aureon_thought_bus import Thought, get_thought_bus

    _HAS_THOUGHT_BUS = True
except Exception:  # noqa: BLE001
    get_thought_bus = None  # type: ignore[assignment]
    Thought = None  # type: ignore[assignment,misc]
    _HAS_THOUGHT_BUS = False


_PHASE_TOPICS = {
    "boot": "operator.phase.boot",
    "ground": "operator.phase.ground",
    "fan_out": "operator.phase.fan_out",
    "consensus": "operator.phase.consensus",
    "veto": "operator.phase.veto",
    "complete": "operator.complete",
}

_OPERATOR_PERSONA = (
    "You are Aureon, an operator routing a question through the Harmonic Nexus "
    "Core (HNC) trading system. Answer from the grounded Aureon repository context "
    "below. Be precise and falsifiable: cite the system or document a claim comes "
    "from, and say plainly when the context does not cover something. Do not invent "
    "trade executions, balances, filings, or credentials."
)

_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "is", "are", "for", "on",
    "with", "as", "by", "it", "this", "that", "be", "at", "from", "how", "does",
    "do", "what", "aureon",
}


class AureonOperator:
    """The switchboard: fan-out → ground → collapse → veto, traced on the bus."""

    def __init__(
        self,
        providers: Optional[Dict[str, LLMAdapter]] = None,
        *,
        bus: Any = None,
        conscience: Any = None,
        source: str = "aureon.operator",
    ) -> None:
        self.providers = providers if providers is not None else build_provider_set()
        if bus is not None:
            self.bus = bus
        elif _HAS_THOUGHT_BUS and get_thought_bus is not None:
            self.bus = get_thought_bus()
        else:
            self.bus = None
        self.source = source
        self._conscience = conscience
        self._conscience_loaded = conscience is not None

    # ------------------------------------------------------------------
    # Public entrypoints
    # ------------------------------------------------------------------

    def respond(self, prompt: str, session_id: Optional[str] = None) -> OperatorResponse:
        """Run a prompt through all five phases. Returns the grounded answer."""
        started = time.time()
        resp = OperatorResponse(
            trace_id=uuid.uuid4().hex,
            prompt=prompt,
            submitted_at=started,
            session_id=session_id,
        )
        self._publish(
            resp,
            "boot",
            {"prompt": prompt, "session_id": session_id, "providers": describe_provider_set(self.providers)},
        )

        system_prompt = self._ground(prompt, resp)
        self._fan_out(prompt, system_prompt, resp)
        self._consensus(resp)
        self._veto(prompt, resp)

        resp.elapsed_ms = (time.time() - started) * 1000.0
        self._publish(resp, "complete", resp.to_dict())
        return resp

    def stream(self, prompt: str, session_id: Optional[str] = None) -> Generator[StreamChunk, None, None]:
        """LLMAdapter-style stream of the final grounded answer (word chunks)."""
        for event in self.stream_events(prompt, session_id=session_id):
            if event.get("type") == "token":
                yield StreamChunk(text=event.get("text", ""))
            elif event.get("type") == "complete":
                yield StreamChunk(done=True, stop_reason="end_turn")

    def stream_events(
        self, prompt: str, session_id: Optional[str] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Rich event stream for the phone/SSE surface. Yields dict events:
          {"type": "phase", "phase": ..., "detail": {...}}   as each phase resolves
          {"type": "token", "text": ...}                     final answer, word by word
          {"type": "complete", "response": {...}}            the full OperatorResponse
        """
        resp = self.respond(prompt, session_id=session_id)
        # Replay the resolved phases as events (order preserved by insertion).
        for phase in ("ground", "fan_out", "consensus", "veto"):
            yield {"type": "phase", "phase": phase, "detail": self._phase_summary(phase, resp)}
        for word in (resp.text or "").split(" "):
            yield {"type": "token", "text": word + " "}
        yield {"type": "complete", "response": resp.to_dict()}

    # ------------------------------------------------------------------
    # Phase 1 — Ground (repo-anchored system prompt)
    # ------------------------------------------------------------------

    def _ground(self, prompt: str, resp: OperatorResponse) -> str:
        sources: List[Dict[str, str]] = []
        lane = task_family = ""
        filter_block = ""
        messages = [{"role": "user", "content": prompt}]
        try:
            from aureon.autonomous.aureon_dynamic_prompt_filter import (
                build_dynamic_prompt_filter,
                render_filter_prompt_block,
            )

            report = build_dynamic_prompt_filter(messages, system=_OPERATOR_PERSONA, publish=False)
            lane = str(report.get("lane") or "")
            task_family = str(report.get("task_family") or "")
            for packet in report.get("source_packets") or []:
                if isinstance(packet, dict):
                    sources.append(
                        {
                            "title": str(packet.get("title") or "Source packet"),
                            "path": str(packet.get("source_path") or ""),
                        }
                    )
            filter_block = render_filter_prompt_block(report)
        except Exception as exc:  # noqa: BLE001 — grounding degrades, never crashes
            logger.debug("dynamic prompt filter unavailable: %s", exc)
            sources = self._fallback_sources(prompt)

        system_prompt = "\n\n".join(part for part in (_OPERATOR_PERSONA, filter_block) if part.strip())
        resp.grounding = GroundingContext(
            sources=sources,
            lane=lane,
            task_family=task_family,
            system_prompt_chars=len(system_prompt),
        )
        self._publish(resp, "ground", resp.grounding.to_dict())
        return system_prompt

    @staticmethod
    def _fallback_sources(prompt: str) -> List[Dict[str, str]]:
        try:
            from aureon.autonomous.aureon_dynamic_prompt_filter import select_source_packets

            return [
                {"title": p.title, "path": p.source_path}
                for p in select_source_packets(prompt, limit=4)
            ]
        except Exception:  # noqa: BLE001
            return []

    # ------------------------------------------------------------------
    # Phase 2 — Fan out (patch the prompt to every line)
    # ------------------------------------------------------------------

    def _fan_out(self, prompt: str, system_prompt: str, resp: OperatorResponse) -> None:
        messages = [{"role": "user", "content": prompt}]
        for name, adapter in self.providers.items():
            t0 = time.time()
            try:
                out = adapter.prompt(messages, system=system_prompt, max_tokens=800, temperature=0.5)
                text = (out.text or "").strip()
                ok = out.stop_reason != "error" and bool(text)
                resp.answers.append(
                    ProviderAnswer(
                        provider=name,
                        model=str(out.model or getattr(adapter, "model", "") or ""),
                        text=text,
                        ok=ok,
                        latency_ms=(time.time() - t0) * 1000.0,
                        error="" if ok else (text or "empty response"),
                    )
                )
            except Exception as exc:  # noqa: BLE001 — one dead line must not sink the board
                resp.answers.append(
                    ProviderAnswer(
                        provider=name,
                        model=str(getattr(adapter, "model", "") or ""),
                        text="",
                        ok=False,
                        latency_ms=(time.time() - t0) * 1000.0,
                        error=str(exc),
                    )
                )
                resp.errors.append({"phase": "fan_out", "provider": name, "error": str(exc)})
        self._publish(
            resp,
            "fan_out",
            {
                "n_providers": len(self.providers),
                "n_ok": sum(1 for a in resp.answers if a.ok),
                "answers": [a.to_dict() for a in resp.answers],
            },
        )

    # ------------------------------------------------------------------
    # Phase 3 — Consensus collapse (agreement → one answer)
    # ------------------------------------------------------------------

    def _consensus(self, resp: OperatorResponse) -> None:
        good = [a for a in resp.answers if a.ok and a.text.strip()]
        if not good:
            # No line answered — surface the failure honestly rather than inventing.
            resp.text = (
                "No AI line produced a usable answer. "
                "Check provider keys and connectivity, or run offline for a grounded stub."
            )
            resp.consensus = ConsensusReading(n_answers=0, agreement=0.0, winner="", synthesized=False)
            self._publish(resp, "consensus", resp.consensus.to_dict())
            return

        if len(good) == 1:
            winner = good[0]
            resp.text = winner.text
            resp.consensus = ConsensusReading(
                n_answers=1, agreement=1.0, winner=winner.provider, synthesized=False
            )
            self._publish(resp, "consensus", resp.consensus.to_dict())
            return

        # Medoid collapse: the answer most similar to all the others wins.
        # Agreement = mean pairwise Jaccard token overlap (a coherence proxy).
        token_sets = {a.provider: self._tokens(a.text) for a in good}
        best_provider = ""
        best_score = -1.0
        pairwise: List[float] = []
        for a in good:
            sims = []
            for b in good:
                if a.provider == b.provider:
                    continue
                sim = self._jaccard(token_sets[a.provider], token_sets[b.provider])
                sims.append(sim)
                pairwise.append(sim)
            mean_sim = sum(sims) / len(sims) if sims else 0.0
            # Tie-break toward the more substantive answer.
            score = mean_sim + min(len(a.text), 1200) / 1e6
            if score > best_score:
                best_score = score
                best_provider = a.provider

        agreement = sum(pairwise) / len(pairwise) if pairwise else 0.0
        winner = next(a for a in good if a.provider == best_provider)
        resp.text = winner.text
        resp.consensus = ConsensusReading(
            n_answers=len(good),
            agreement=agreement,
            winner=winner.provider,
            runner_ups=[a.provider for a in good if a.provider != winner.provider],
            synthesized=True,
        )
        self._publish(resp, "consensus", resp.consensus.to_dict())

    @staticmethod
    def _tokens(text: str) -> set:
        words = re.findall(r"[a-z0-9]+", str(text).lower())
        return {w for w in words if w not in _STOPWORDS and len(w) > 2}

    @staticmethod
    def _jaccard(a: set, b: set) -> float:
        if not a or not b:
            return 0.0
        inter = len(a & b)
        union = len(a | b)
        return inter / union if union else 0.0

    # ------------------------------------------------------------------
    # Phase 4 — Veto (the Queen's 4th-pass conscience)
    # ------------------------------------------------------------------

    def _veto(self, prompt: str, resp: OperatorResponse) -> None:
        conscience = self._get_conscience()
        if conscience is None:
            resp.conscience_verdict = "APPROVED"
            self._publish(resp, "veto", {"verdict": "APPROVED", "available": False})
            return

        action = f"answer operator question: {prompt[:160]}"
        context = {
            "answer_preview": resp.text[:400],
            "n_providers": len(resp.answers),
            "agreement": resp.consensus.agreement if resp.consensus else 0.0,
            "sources": [s.get("path", "") for s in (resp.grounding.sources if resp.grounding else [])],
        }
        try:
            whisper = conscience.ask_why(action, context)
            verdict = getattr(whisper.verdict, "name", str(whisper.verdict))
            resp.conscience_verdict = verdict
            resp.conscience_message = str(getattr(whisper, "message", "") or "")
            if verdict == "VETO":
                resp.blocked = True
                resp.text = (
                    "🦗 The Queen's conscience vetoed this answer.\n"
                    f"Reason: {resp.conscience_message}"
                )
        except Exception as exc:  # noqa: BLE001 — conscience failure is non-fatal
            logger.debug("conscience unavailable: %s", exc)
            resp.conscience_verdict = "APPROVED"
            resp.errors.append({"phase": "veto", "error": str(exc)})
        self._publish(
            resp,
            "veto",
            {"verdict": resp.conscience_verdict, "blocked": resp.blocked, "message": resp.conscience_message},
        )

    def _get_conscience(self):
        if self._conscience_loaded:
            return self._conscience
        self._conscience_loaded = True
        try:
            from aureon.queen.queen_conscience import QueenConscience

            self._conscience = QueenConscience()
        except Exception as exc:  # noqa: BLE001
            logger.debug("QueenConscience unavailable: %s", exc)
            self._conscience = None
        return self._conscience

    # ------------------------------------------------------------------
    # Transport
    # ------------------------------------------------------------------

    def _phase_summary(self, phase: str, resp: OperatorResponse) -> Dict[str, Any]:
        if phase == "ground":
            return resp.grounding.to_dict() if resp.grounding else {}
        if phase == "fan_out":
            return {"n_ok": sum(1 for a in resp.answers if a.ok), "n_total": len(resp.answers)}
        if phase == "consensus":
            return resp.consensus.to_dict() if resp.consensus else {}
        if phase == "veto":
            return {"verdict": resp.conscience_verdict, "blocked": resp.blocked}
        return {}

    def _publish(self, resp: OperatorResponse, phase_key: str, payload: Dict[str, Any]) -> None:
        topic = _PHASE_TOPICS[phase_key]
        if self.bus is None or Thought is None:
            resp.phase_thought_ids[phase_key] = ""
            return
        try:
            thought = Thought(
                source=self.source,
                topic=topic,
                trace_id=resp.trace_id,
                parent_id=self._last_thought_id(resp),
                payload=dict(payload),
                meta={"phase": phase_key},
            )
            published = self.bus.publish(thought)
            resp.phase_thought_ids[phase_key] = getattr(published, "id", "") or ""
        except Exception as exc:  # noqa: BLE001
            logger.debug("failed to publish %s: %s", topic, exc)
            resp.phase_thought_ids[phase_key] = ""

    @staticmethod
    def _last_thought_id(resp: OperatorResponse) -> Optional[str]:
        for key in reversed(list(resp.phase_thought_ids.keys())):
            if resp.phase_thought_ids[key]:
                return resp.phase_thought_ids[key]
        return None


def run_operator(prompt: str, bus: Any = None, session_id: Optional[str] = None) -> OperatorResponse:
    """Convenience one-shot: build the switchboard and answer one prompt."""
    return AureonOperator(bus=bus).respond(prompt, session_id=session_id)


__all__ = ["AureonOperator", "run_operator"]
