"""
Aureon Vault Voice — The System Speaks to Itself
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The voice layer gives the self-feedback vault the ability to write its
own prompts and have conversations with itself through its own thought
processes — not scripted, as it chooses.

Five modules:

  utterance.py          — VoiceStatement + Utterance dataclasses
  choice_gate.py        — ChoiceGate decides WHEN the vault speaks
  vault_voice.py        — Seven personas: Vault, Queen, Miner, Scout,
                          Council, Architect, Lover. Each composes
                          self-authored prompts from vault state.
  self_dialogue.py      — SelfDialogueEngine orchestrates exchanges
                          between voices, feeding outputs back into
                          the vault so each voice shapes the next.
  thought_stream_loop.py — Background daemon that runs the dialogue
                          engine at the love+gratitude cadence.

Gary Leckey / Aureon Institute — 2026
"""

from aureon.vault.voice.utterance import Utterance, VoiceStatement
from aureon.vault.voice.choice_gate import ChoiceGate, ChoiceGateDecision
from aureon.vault.voice.vault_voice import (
    VaultVoice,
    QueenVoice,
    MinerVoice,
    ScoutVoice,
    CouncilVoice,
    ArchitectVoice,
    LoverVoice,
    VOICE_REGISTRY,
    build_all_voices,
)
from aureon.vault.voice.self_dialogue import (
    SelfDialogueEngine,
    DEFAULT_VOICE_WEIGHTS,
)
from aureon.vault.voice.thought_stream_loop import (
    ThoughtStreamLoop,
    ThoughtStreamStatus,
)
from aureon.vault.voice.aureon_personas import (
    ResonantPersona,
    PainterVoice,
    ArtistVoice,
    QuantumPhysicistVoice,
    PhilosopherVoice,
    ChildVoice,
    ElderVoice,
    MysticVoice,
    EngineerVoice,
    LeftVoice,
    RightVoice,
    AUREON_PERSONA_REGISTRY,
    build_aureon_personas,
)
from aureon.vault.voice.persona_vacuum import (
    PersonaVacuum,
    get_persona_vacuum,
)
from aureon.vault.voice.persona_action import (
    PersonaAction,
    ActionExecution,
    PersonaActuator,
)
from aureon.vault.voice.affinity_chorus import (
    AffinityChorus,
    AffinityContribution,
    DEFAULT_TTL_S as CHORUS_DEFAULT_TTL_S,
    vault_fingerprint_seed,
    make_vault_seed_fn,
)
from aureon.vault.voice.life_context import LifeContext, LifeEvent
from aureon.vault.voice.opportunity_scanner import (
    OpportunityScanner,
    OpportunityHit,
)
from aureon.vault.voice.symbolic_life_bridge import SymbolicLifeBridge

__all__ = [
    # Utterance
    "Utterance",
    "VoiceStatement",
    # Choice gate
    "ChoiceGate",
    "ChoiceGateDecision",
    # Voices
    "VaultVoice",
    "QueenVoice",
    "MinerVoice",
    "ScoutVoice",
    "CouncilVoice",
    "ArchitectVoice",
    "LoverVoice",
    "VOICE_REGISTRY",
    "build_all_voices",
    # Dialogue engine
    "SelfDialogueEngine",
    "DEFAULT_VOICE_WEIGHTS",
    # Thought stream loop
    "ThoughtStreamLoop",
    "ThoughtStreamStatus",
    # Resonant personas (quantum superposition layer)
    "ResonantPersona",
    "PainterVoice",
    "ArtistVoice",
    "QuantumPhysicistVoice",
    "PhilosopherVoice",
    "ChildVoice",
    "ElderVoice",
    "MysticVoice",
    "EngineerVoice",
    "LeftVoice",
    "RightVoice",
    "AUREON_PERSONA_REGISTRY",
    "build_aureon_personas",
    "PersonaVacuum",
    "get_persona_vacuum",
    # Action layer (speak → act)
    "PersonaAction",
    "ActionExecution",
    "PersonaActuator",
    # Unified-collapse layer
    "AffinityChorus",
    "AffinityContribution",
    "CHORUS_DEFAULT_TTL_S",
    "vault_fingerprint_seed",
    "make_vault_seed_fn",
    # Life context + opportunity scanning
    "LifeContext",
    "LifeEvent",
    "OpportunityScanner",
    "OpportunityHit",
    "SymbolicLifeBridge",
]
