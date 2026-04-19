"""
Cognition pipeline — dataclass schemas.

One envelope threads through all seven phases. Each phase mutates its own
slot. The envelope is the unit of observation; the phases are lenses.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class StructuredIntent:
    """Phase 2 output. What the LLM (or heuristic) thinks the prompt wants."""

    primary_verb: str = "unknown"
    verb_chain: List[str] = field(default_factory=list)
    objects: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    time_horizon: str = "now"
    domain_category: str = "general"
    wants_creative: bool = False
    raw_llm_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_verb": self.primary_verb,
            "verb_chain": list(self.verb_chain),
            "objects": list(self.objects),
            "constraints": dict(self.constraints),
            "time_horizon": self.time_horizon,
            "domain_category": self.domain_category,
            "wants_creative": self.wants_creative,
            "raw_llm_text": self.raw_llm_text,
        }


@dataclass
class VaultLookup:
    """Phase 3 output. How warm the prompt-signature cache is."""

    hit: bool = False
    signature: str = ""
    prior_trace_ids: List[str] = field(default_factory=list)
    prior_collapsed_hash: Optional[str] = None
    warmth: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hit": self.hit,
            "signature": self.signature,
            "prior_trace_ids": list(self.prior_trace_ids),
            "prior_collapsed_hash": self.prior_collapsed_hash,
            "warmth": round(float(self.warmth), 6),
        }


@dataclass
class Enrichment:
    """Phase 4 output. External-source snippets when the vault is cold."""

    sources: List[str] = field(default_factory=list)
    snippets: List[Dict[str, Any]] = field(default_factory=list)
    ttl_expires_at: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sources": list(self.sources),
            "snippets": list(self.snippets),
            "ttl_expires_at": round(float(self.ttl_expires_at), 3),
        }


@dataclass
class ComplexityReading:
    """Phase 5 output. How wide to open the multiverse."""

    n_branches: int = 1
    score: float = 0.0
    components: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n_branches": int(self.n_branches),
            "score": round(float(self.score), 6),
            "components": {k: round(float(v), 6) for k, v in self.components.items()},
        }


@dataclass
class Branch:
    """Phase 6 output. One candidate interpretation."""

    branch_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    persona: str = "default"
    temperature: float = 0.7
    seed: int = 0
    candidate_text: str = ""
    candidate_intent: Optional[StructuredIntent] = None
    lambda_snapshot: float = 0.0
    latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "branch_id": self.branch_id,
            "persona": self.persona,
            "temperature": round(float(self.temperature), 3),
            "seed": int(self.seed),
            "candidate_text": self.candidate_text,
            "candidate_intent": self.candidate_intent.to_dict() if self.candidate_intent else None,
            "lambda_snapshot": round(float(self.lambda_snapshot), 6),
            "latency_ms": round(float(self.latency_ms), 3),
        }


@dataclass
class CollapsedOutput:
    """Phase 7 output. The single colour that survived the prism."""

    winning_branch_id: str = ""
    text: str = ""
    intent: Optional[StructuredIntent] = None
    lambda_at_collapse: float = 0.0
    conscience_verdict: str = "APPROVED"
    synthesized: bool = False
    runner_up_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "winning_branch_id": self.winning_branch_id,
            "text": self.text,
            "intent": self.intent.to_dict() if self.intent else None,
            "lambda_at_collapse": round(float(self.lambda_at_collapse), 6),
            "conscience_verdict": self.conscience_verdict,
            "synthesized": self.synthesized,
            "runner_up_ids": list(self.runner_up_ids),
        }


@dataclass
class DispatchResult:
    """What the peer substrate returned after collapse."""

    peer_name: str = "stubbed"
    status: str = "stubbed"
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "peer_name": self.peer_name,
            "status": self.status,
            "payload": dict(self.payload),
        }


@dataclass
class GoalEnvelope:
    """The single unit threaded through all seven phases."""

    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    prompt: str = ""
    submitted_at: float = field(default_factory=time.time)
    peer_id: Optional[str] = None
    session_id: Optional[str] = None

    intent: Optional[StructuredIntent] = None
    vault_hit: Optional[VaultLookup] = None
    enrichment: Optional[Enrichment] = None
    complexity: Optional[ComplexityReading] = None
    branches: List[Branch] = field(default_factory=list)
    collapsed: Optional[CollapsedOutput] = None
    dispatch: Optional[DispatchResult] = None

    phase_thought_ids: Dict[str, str] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "prompt": self.prompt,
            "submitted_at": round(float(self.submitted_at), 3),
            "peer_id": self.peer_id,
            "session_id": self.session_id,
            "intent": self.intent.to_dict() if self.intent else None,
            "vault_hit": self.vault_hit.to_dict() if self.vault_hit else None,
            "enrichment": self.enrichment.to_dict() if self.enrichment else None,
            "complexity": self.complexity.to_dict() if self.complexity else None,
            "branches": [b.to_dict() for b in self.branches],
            "collapsed": self.collapsed.to_dict() if self.collapsed else None,
            "dispatch": self.dispatch.to_dict() if self.dispatch else None,
            "phase_thought_ids": dict(self.phase_thought_ids),
            "errors": list(self.errors),
        }
