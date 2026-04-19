"""
aureon.cognition
================

The prism has seven panes. Prompt enters as white light; the pipeline bends
it through Boot → Comprehend → Vault → External Fallback → Complexity →
Multiverse → Coherence Collapse, until one colour remains. Peer to the
matcher, not its parent — every phase publishes a Thought on the bus keyed
by a single ``trace_id`` so the CognitiveDashboard renders the cascade live.
"""

from __future__ import annotations

from aureon.cognition.pipeline import CognitionPipeline, run_goal
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

__all__ = [
    "CognitionPipeline",
    "run_goal",
    "GoalEnvelope",
    "StructuredIntent",
    "VaultLookup",
    "Enrichment",
    "ComplexityReading",
    "Branch",
    "CollapsedOutput",
    "DispatchResult",
]
