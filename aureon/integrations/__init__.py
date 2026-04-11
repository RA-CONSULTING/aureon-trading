"""
Aureon External Integrations
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sovereign bridges from the Aureon cognitive loops to external tools.
These are distinct from `aureon/bridges/` (which are HNC / trading domain
bridges) — here we wire two of the biggest local-first AI tools on the
planet directly into the vault:

  Ollama    — self-hosted LLM runner (chat, generate, embed, model mgmt)
  Obsidian  — local-first knowledge graph (vault CRUD, search, commands)

Each tool gets:
  1. A **bridge** — a thin, native-API client that speaks the tool's own
     protocol. No leaky abstractions. No OpenAI-compat only. Full surface.
  2. A **wiring** — hooks that plug the bridge into the recently-worked
     cognitive loops: AureonSelfFeedbackLoop, SelfDialogueEngine,
     ThoughtStreamLoop, and the VaultVoice personas.
  3. An **audit-trail entry** — each integration self-reports its health
     into IntegrationAuditTrail so the Queen can see what is connected.

Plus one cross-cutting module:

  NeuralPathwayMapper — walks the `aureon/` package tree and builds a
                        directed graph of module → module dependencies,
                        then writes it into `vault.pathway_graph` so the
                        system has a map of its own internal wiring.

See also:
  - docs/integrations/OLLAMA_OBSIDIAN.md (human-readable walkthrough)
  - IntegrationAuditTrail.CHECKLIST (machine-readable checklist)
"""

from aureon.integrations.audit_trail import (
    IntegrationAuditTrail,
    IntegrationStatus,
    CheckResult,
    INTEGRATION_CHECKLIST,
    run_full_audit,
)
from aureon.integrations.neural_pathway_mapper import (
    NeuralPathwayMapper,
    PathwayGraph,
    build_pathway_graph,
)
from aureon.integrations.wiring import wire_integrations, WiringResult

# Convenience re-exports — so callers can do
#   from aureon.integrations import OllamaBridge, ObsidianBridge
# without reaching into the submodules.
from aureon.integrations.ollama import (
    OllamaBridge,
    OllamaLLMAdapter,
    OllamaModel,
    OllamaPsEntry,
)
from aureon.integrations.obsidian import (
    ObsidianBridge,
    ObsidianSink,
    ObsidianSinkConfig,
    ObsidianMode,
    ObsidianNote,
)

__all__ = [
    # Audit + pathway
    "IntegrationAuditTrail",
    "IntegrationStatus",
    "CheckResult",
    "INTEGRATION_CHECKLIST",
    "run_full_audit",
    "NeuralPathwayMapper",
    "PathwayGraph",
    "build_pathway_graph",
    # Wiring
    "wire_integrations",
    "WiringResult",
    # Ollama
    "OllamaBridge",
    "OllamaLLMAdapter",
    "OllamaModel",
    "OllamaPsEntry",
    # Obsidian
    "ObsidianBridge",
    "ObsidianSink",
    "ObsidianSinkConfig",
    "ObsidianMode",
    "ObsidianNote",
]
