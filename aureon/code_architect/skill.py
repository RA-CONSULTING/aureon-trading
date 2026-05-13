"""
Skill — the atomic unit of learned behaviour
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Defines the data model for every skill in the library.
"""

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class SkillLevel(enum.IntEnum):
    """
    Hierarchical level of a skill.

    L0 → primitive atomic action (vm_mouse_move, execute_shell, ...)
    L1 → compound (2-10 atomics in sequence)
    L2 → task     (named objective, uses L0+L1)
    L3 → workflow (sequence of tasks, has branching)
    L4 → role     (persona — uses L0..L3, has long-term goals)
    """

    ATOMIC = 0
    COMPOUND = 1
    TASK = 2
    WORKFLOW = 3
    ROLE = 4


class SkillStatus(enum.Enum):
    """Lifecycle state of a skill."""

    PROPOSED = "proposed"           # code generated but not yet validated
    VALIDATED = "validated"         # passed all validators, safe to execute
    APPROVED = "approved"           # blessed by Queen metacognition + pillar alignment
    ACTIVE = "active"               # currently running / hot
    DEPRECATED = "deprecated"       # superseded by a better skill
    BLOCKED = "blocked"             # failed validation, do not run


# ─────────────────────────────────────────────────────────────────────────────
# SkillProposal — the raw output of the writer before validation
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class SkillProposal:
    """
    A proposed skill that has been written but not yet validated.
    Flows: Observer → Writer → (SkillProposal) → Validator → Skill
    """

    proposal_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    level: SkillLevel = SkillLevel.ATOMIC
    category: str = "general"
    code: str = ""
    entry_function: str = ""
    params_schema: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)     # other skill names
    observation_sources: List[str] = field(default_factory=list)  # snapshot ids
    created_at: float = field(default_factory=time.time)
    created_by: str = "code_architect"
    reasoning: str = ""                 # why the writer proposed this
    target: str = "vm"                  # vm | local | either
    expression_context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "name": self.name,
            "description": self.description,
            "level": int(self.level),
            "category": self.category,
            "code": self.code,
            "entry_function": self.entry_function,
            "params_schema": self.params_schema,
            "dependencies": self.dependencies,
            "observation_sources": self.observation_sources,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "reasoning": self.reasoning,
            "target": self.target,
            "expression_context": self.expression_context,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Skill — validated and stored in the library
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class Skill:
    """A validated, executable skill."""

    skill_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    level: SkillLevel = SkillLevel.ATOMIC
    category: str = "general"

    # Code
    code: str = ""                      # Python function source
    entry_function: str = ""            # name of the function to call
    params_schema: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)

    # Provenance
    created_at: float = field(default_factory=time.time)
    created_by: str = "code_architect"
    observation_sources: List[str] = field(default_factory=list)

    # Status
    status: SkillStatus = SkillStatus.PROPOSED
    target: str = "vm"                  # vm | local | either

    # Metacognitive feedback
    queen_verdict: Optional[str] = None        # from Queen bridge
    queen_confidence: float = 0.0
    pillar_alignment_score: float = 0.0
    pillar_lighthouse: bool = False
    harmonic_signature: Dict[str, float] = field(default_factory=dict)

    # Execution stats
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    last_execution_at: Optional[float] = None
    last_error: Optional[str] = None
    mean_duration_s: float = 0.0

    # Tags
    tags: List[str] = field(default_factory=list)
    expression_context: Dict[str, Any] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        if self.execution_count == 0:
            return 0.0
        return self.success_count / self.execution_count

    @property
    def confidence(self) -> float:
        """
        Composite confidence = success_rate × queen_confidence × alignment.
        New skills start at 0 and earn confidence through execution.
        """
        if self.execution_count == 0:
            return 0.5 * max(self.queen_confidence, 0.0) * max(self.pillar_alignment_score, 0.0)
        return self.success_rate * max(self.queen_confidence, 0.5) * max(self.pillar_alignment_score, 0.5)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "level": int(self.level),
            "level_name": self.level.name,
            "category": self.category,
            "code": self.code,
            "entry_function": self.entry_function,
            "params_schema": self.params_schema,
            "dependencies": self.dependencies,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "observation_sources": self.observation_sources,
            "status": self.status.value,
            "target": self.target,
            "queen_verdict": self.queen_verdict,
            "queen_confidence": self.queen_confidence,
            "pillar_alignment_score": self.pillar_alignment_score,
            "pillar_lighthouse": self.pillar_lighthouse,
            "harmonic_signature": self.harmonic_signature,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": round(self.success_rate, 4),
            "confidence": round(self.confidence, 4),
            "last_execution_at": self.last_execution_at,
            "last_error": self.last_error,
            "mean_duration_s": round(self.mean_duration_s, 4),
            "tags": self.tags,
            "expression_context": self.expression_context,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        """Rehydrate a Skill from a dict (JSON load)."""
        skill = cls()
        skill.skill_id = data.get("skill_id", skill.skill_id)
        skill.name = data.get("name", "")
        skill.description = data.get("description", "")
        skill.level = SkillLevel(int(data.get("level", 0)))
        skill.category = data.get("category", "general")
        skill.code = data.get("code", "")
        skill.entry_function = data.get("entry_function", "")
        skill.params_schema = data.get("params_schema", {}) or {}
        skill.dependencies = data.get("dependencies", []) or []
        skill.created_at = float(data.get("created_at", time.time()))
        skill.created_by = data.get("created_by", "code_architect")
        skill.observation_sources = data.get("observation_sources", []) or []
        status_val = data.get("status", "proposed")
        try:
            skill.status = SkillStatus(status_val)
        except ValueError:
            skill.status = SkillStatus.PROPOSED
        skill.target = data.get("target", "vm")
        skill.queen_verdict = data.get("queen_verdict")
        skill.queen_confidence = float(data.get("queen_confidence", 0.0) or 0.0)
        skill.pillar_alignment_score = float(data.get("pillar_alignment_score", 0.0) or 0.0)
        skill.pillar_lighthouse = bool(data.get("pillar_lighthouse", False))
        skill.harmonic_signature = data.get("harmonic_signature", {}) or {}
        skill.execution_count = int(data.get("execution_count", 0) or 0)
        skill.success_count = int(data.get("success_count", 0) or 0)
        skill.failure_count = int(data.get("failure_count", 0) or 0)
        skill.last_execution_at = data.get("last_execution_at")
        skill.last_error = data.get("last_error")
        skill.mean_duration_s = float(data.get("mean_duration_s", 0.0) or 0.0)
        skill.tags = data.get("tags", []) or []
        skill.expression_context = data.get("expression_context", {}) or {}
        return skill

    @classmethod
    def from_proposal(cls, proposal: SkillProposal) -> "Skill":
        """Build a Skill from a SkillProposal."""
        return cls(
            name=proposal.name,
            description=proposal.description,
            level=proposal.level,
            category=proposal.category,
            code=proposal.code,
            entry_function=proposal.entry_function,
            params_schema=proposal.params_schema,
            dependencies=proposal.dependencies,
            created_by=proposal.created_by,
            observation_sources=proposal.observation_sources,
            target=proposal.target,
            status=SkillStatus.PROPOSED,
            expression_context=proposal.expression_context,
        )
