"""
Aureon Code Architect — Self-Authoring Skill System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"From move the mouse to be a CEO" — a single pipeline that learns skills
by watching the swarm motion environment, writes its own code, validates
meaning via the Queen's metacognition + pillar alignment, and executes on
either a virtual machine or an end-user's actual computer.

  OBSERVE → PROPOSE → WRITE → VALIDATE → STORE → EXECUTE → FEEDBACK

Skill hierarchy (5 levels):
  L0 ATOMIC    : single primitive call (vm_mouse_move, vm_left_click, ...)
  L1 COMPOUND  : a sequence of L0 atomics     (click_somewhere, type_sentence)
  L2 TASK      : a sequence of L1 compounds   (open_file_explorer, fill_form)
  L3 WORKFLOW  : a sequence of L2 tasks       (morning_routine, research_topic)
  L4 ROLE      : a full persona               (be_ceo, be_engineer, be_scout)

Each skill is a Python function whose source code is written by the in-house
AI (or from a deterministic template), validated via:
  1. AST-level static safety (whitelist imports, reject eval/exec/compile,
     reject file writes outside the sandbox, reject network calls)
  2. QueenAIBridge meaning validation (does the skill align with sacred
     purpose?)
  3. PillarAlignment quality gate (is the proposal harmonically coherent?)
  4. Optional Lighthouse check (γ > 0.945 before a skill is approved to run
     on end-user hardware)

Modules:
  - skill.py         : Skill / SkillProposal / SkillLevel dataclasses
  - skill_library.py : Persistent JSON skill registry
  - primitives.py    : Safe primitives that skills can call + safe exec context
  - observer.py      : ObservationEngine — watches swarm motion for candidates
  - writer.py        : SkillWriter — generates Python code for new skills
  - validator.py     : SkillValidator — AST + Queen + pillar approvals
  - executor.py      : SkillExecutor — runs skills, resolves dependencies
  - architect.py     : CodeArchitect — the top-level orchestrator

Gary Leckey / Aureon Institute — 2026
"""

from aureon.code_architect.skill import (
    Skill,
    SkillProposal,
    SkillLevel,
    SkillStatus,
)
from aureon.code_architect.skill_library import (
    SkillLibrary,
    get_skill_library,
)
from aureon.code_architect.primitives import (
    get_primitives,
    get_safe_globals,
    PRIMITIVE_NAMES,
)
from aureon.code_architect.observer import (
    ObservationEngine,
    ObservedPattern,
)
from aureon.code_architect.writer import (
    SkillWriter,
)
from aureon.code_architect.validator import (
    SkillValidator,
    ValidationResult,
)
from aureon.code_architect.executor import (
    SkillExecutor,
    SkillExecutionResult,
)
from aureon.code_architect.architect import (
    CodeArchitect,
    get_code_architect,
)

__all__ = [
    # Skills
    "Skill",
    "SkillProposal",
    "SkillLevel",
    "SkillStatus",
    # Library
    "SkillLibrary",
    "get_skill_library",
    # Primitives
    "get_primitives",
    "get_safe_globals",
    "PRIMITIVE_NAMES",
    # Pipeline components
    "ObservationEngine",
    "ObservedPattern",
    "SkillWriter",
    "SkillValidator",
    "ValidationResult",
    "SkillExecutor",
    "SkillExecutionResult",
    # Orchestrator
    "CodeArchitect",
    "get_code_architect",
]
