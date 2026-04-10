"""
CodeArchitect — the top-level self-authoring skill orchestrator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ties the full pipeline together:

  Observer  →  Writer  →  Validator  →  Library  →  Executor
      │           │          │            │            │
      └ swarm     └ in-house └ Queen      └ JSON      └ VM/local
        motion      AI         meaning     store       dispatch

Usage:
    from aureon.code_architect import get_code_architect

    arch = get_code_architect()
    arch.bootstrap_atomics()                        # seed L0 skills
    arch.teach_compound("click_and_type", ["vm_left_click", "vm_type_text"])
    arch.build_workflow("morning_routine", ["check_mail", "review_calendar"])
    arch.build_role("be_ceo", ["morning_routine", "strategic_planning"])

    arch.execute_skill("be_ceo")                    # runs the whole tree

High-level API:
  - bootstrap_atomics()       : seed all 20 VM primitives as L0 skills
  - observe_and_propose()     : run one observe→propose cycle on the observer
  - learn_from_pattern(p)     : turn an ObservedPattern into a stored Skill
  - teach_compound(n, deps)   : manually compose a compound skill
  - build_workflow(n, tasks)  : manually compose a workflow
  - build_role(n, workflows)  : manually compose a role
  - execute_skill(name)       : run a skill through the full tree
  - get_status()              : full pipeline health
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional

from aureon.code_architect.skill import (
    Skill,
    SkillProposal,
    SkillLevel,
    SkillStatus,
)
from aureon.code_architect.skill_library import SkillLibrary, get_skill_library
from aureon.code_architect.primitives import VM_ACTION_NAMES
from aureon.code_architect.observer import ObservationEngine, ObservedPattern
from aureon.code_architect.writer import SkillWriter
from aureon.code_architect.validator import SkillValidator
from aureon.code_architect.executor import SkillExecutor, SkillExecutionResult

logger = logging.getLogger("aureon.code_architect.architect")


class CodeArchitect:
    """The top-level orchestrator of the self-authoring skill pipeline."""

    def __init__(
        self,
        library: Optional[SkillLibrary] = None,
        adapter: Any = None,
        dispatcher: Any = None,
        queen_bridge: Any = None,
        pillar_alignment: Any = None,
        thought_bus: Any = None,
        auto_wire: bool = True,
    ):
        # Use `is not None` rather than `or` because an empty library is
        # falsy (SkillLibrary.__len__ == 0 initially) and would otherwise
        # silently fall through to the singleton.
        self.library = library if library is not None else get_skill_library()
        self.writer = SkillWriter(adapter=adapter)
        self.validator = SkillValidator(
            queen_bridge=queen_bridge,
            pillar_alignment=pillar_alignment,
        )
        self.observer = ObservationEngine(window_size=3, min_occurrences=2)
        self.executor = SkillExecutor(
            library=self.library,
            dispatcher=dispatcher,
            validator=self.validator,
            thought_bus=thought_bus,
        )

        self._lock = threading.RLock()
        self._created_at = time.time()

        if auto_wire:
            self._auto_wire()

    def _auto_wire(self) -> None:
        # VM dispatcher
        if self.executor.dispatcher is None:
            try:
                from aureon.autonomous.vm_control import get_vm_dispatcher
                self.executor.dispatcher = get_vm_dispatcher()
            except Exception:
                pass

        # ThoughtBus
        if self.executor.thought_bus is None:
            try:
                from aureon.core.aureon_thought_bus import ThoughtBus
                self.executor.thought_bus = ThoughtBus()
            except Exception:
                pass

        # Load adapter for the writer (if not already)
        if self.writer.adapter is None:
            try:
                from aureon.inhouse_ai.llm_adapter import AureonBrainAdapter
                self.writer.adapter = AureonBrainAdapter()
            except Exception:
                pass

        # S03: Eager-wire validator's Queen bridge + pillar alignment.
        # Without this, the validator only lazy-loads them on first
        # validate() call, which means an audit right after __init__
        # sees them as None.
        try:
            self.validator._load_subsystems()
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────────────
    # Bootstrapping — seed the L0 atomic skills
    # ─────────────────────────────────────────────────────────────────────

    def bootstrap_atomics(self, overwrite: bool = False) -> List[Skill]:
        """
        Seed the library with L0 atomic skills for every VM primitive.

        Returns the list of skills created/verified.
        """
        created: List[Skill] = []
        for action in VM_ACTION_NAMES:
            skill_name = action  # keep name matching the primitive (e.g. "left_click")
            if not overwrite and self.library.contains(skill_name):
                created.append(self.library.get(skill_name))
                continue

            proposal = self.writer.propose_atomic(
                action=action,
                name=skill_name,
                description=f"Atomic VM primitive: {action}",
                category="atomic",
                target="vm",
            )
            skill = self._store_if_valid(proposal)
            if skill:
                created.append(skill)

        self.library.save()
        logger.info("Bootstrapped %d atomic skills", len(created))
        return created

    def _store_if_valid(self, proposal: SkillProposal) -> Optional[Skill]:
        """Validate a proposal and store it in the library if it passes."""
        validation = self.validator.validate(proposal)
        skill = Skill.from_proposal(proposal)

        # Fold validation verdict into the skill
        skill.queen_verdict = validation.queen_verdict
        skill.queen_confidence = validation.queen_confidence
        skill.pillar_alignment_score = validation.pillar_alignment_score
        skill.pillar_lighthouse = validation.pillar_lighthouse
        skill.harmonic_signature = validation.harmonic_signature

        if not validation.validated:
            skill.status = SkillStatus.BLOCKED
            skill.last_error = validation.reasoning
            logger.warning("Skill %s blocked: %s", skill.name, validation.reasoning)
            # Still store blocked skills so the user can inspect them
            self.library.add(skill, persist=False)
            return None

        if validation.approved:
            skill.status = SkillStatus.APPROVED
        else:
            skill.status = SkillStatus.VALIDATED

        self.library.add(skill, persist=False)
        return skill

    # ─────────────────────────────────────────────────────────────────────
    # Observation → pattern → skill
    # ─────────────────────────────────────────────────────────────────────

    def observe_and_propose(self) -> List[Skill]:
        """
        Pull all pending patterns from the observer and turn each into a
        validated, stored skill. Returns the list of new skills.
        """
        patterns = self.observer.get_pending_patterns(clear=True)
        created: List[Skill] = []
        for pattern in patterns:
            skill = self.learn_from_pattern(pattern)
            if skill:
                created.append(skill)
        if created:
            self.library.save()
        return created

    def learn_from_pattern(self, pattern: ObservedPattern) -> Optional[Skill]:
        """Generate + validate + store a skill from an ObservedPattern."""
        proposal = self.writer.propose_from_pattern(pattern)
        if self.library.contains(proposal.name):
            # Append a suffix to avoid collisions
            base = proposal.name
            suffix = 1
            while self.library.contains(f"{base}_{suffix}"):
                suffix += 1
            proposal.name = f"{base}_{suffix}"
            proposal.entry_function = proposal.name
            # Regenerate code with the new name
            proposal.code = proposal.code.replace(f"def {base}(", f"def {proposal.name}(", 1)
        return self._store_if_valid(proposal)

    # ─────────────────────────────────────────────────────────────────────
    # Manual composition — teach compound/workflow/role skills
    # ─────────────────────────────────────────────────────────────────────

    def teach_compound(
        self,
        name: str,
        dependency_skill_names: List[str],
        description: str = "",
    ) -> Optional[Skill]:
        """Teach a compound (L1/L2) skill composed of existing skills."""
        proposal = self.writer.propose_compound(
            name=name,
            dependency_skill_names=dependency_skill_names,
            description=description,
            level=SkillLevel.COMPOUND,
            category="compound",
        )
        skill = self._store_if_valid(proposal)
        self.library.save()
        return skill

    def build_task(
        self,
        name: str,
        dependency_skill_names: List[str],
        description: str = "",
    ) -> Optional[Skill]:
        """Build an L2 task skill."""
        proposal = self.writer.propose_compound(
            name=name,
            dependency_skill_names=dependency_skill_names,
            description=description,
            level=SkillLevel.TASK,
            category="task",
        )
        skill = self._store_if_valid(proposal)
        self.library.save()
        return skill

    def build_workflow(
        self,
        name: str,
        task_skill_names: List[str],
        description: str = "",
    ) -> Optional[Skill]:
        """Build an L3 workflow."""
        proposal = self.writer.propose_workflow(
            name=name,
            task_skill_names=task_skill_names,
            description=description,
        )
        skill = self._store_if_valid(proposal)
        self.library.save()
        return skill

    def build_role(
        self,
        name: str,
        workflow_skill_names: List[str],
        description: str = "",
    ) -> Optional[Skill]:
        """
        Build an L4 role (persona) — e.g. be_ceo, be_engineer, be_scout.

        The role's generated code emits 'role.enter' / 'role.exit' events
        and calls each workflow in sequence via call_skill().
        """
        proposal = self.writer.propose_role(
            name=name,
            workflow_skill_names=workflow_skill_names,
            description=description,
        )
        skill = self._store_if_valid(proposal)
        self.library.save()
        return skill

    # ─────────────────────────────────────────────────────────────────────
    # Execution
    # ─────────────────────────────────────────────────────────────────────

    def execute_skill(
        self,
        skill_name: str,
        params: Optional[Dict[str, Any]] = None,
        resolve_deps: bool = True,
    ) -> SkillExecutionResult:
        """
        Execute a skill by name.

        If resolve_deps=True, pre-compiles the full dependency tree first.
        """
        if resolve_deps:
            return self.executor.execute_with_dependencies(skill_name, params=params)
        return self.executor.execute_by_name(skill_name, params=params)

    # ─────────────────────────────────────────────────────────────────────
    # High-level: build the "be a CEO" persona from scratch
    # ─────────────────────────────────────────────────────────────────────

    def demo_build_ceo_persona(self) -> Dict[str, Any]:
        """
        Full demo: build a complete skill tree from L0 atomics up to a L4
        "be_ceo" role, using only the VM primitives that already exist.

        This proves the full hierarchical composition pipeline works
        without any real LLM — purely through template-mode composition
        and validated execution.

        Returns a summary dict.
        """
        # 1. Seed L0 atomics
        atomics = self.bootstrap_atomics()

        # 2. Build a few L1 compound skills from existing primitives
        compound_specs = [
            ("click_somewhere", ["mouse_move", "left_click"]),
            ("type_a_sentence", ["type_text", "press_key"]),
            ("inspect_screen",  ["screenshot", "list_windows"]),
            ("run_command",     ["execute_shell"]),
            ("read_powershell", ["execute_powershell"]),
        ]
        compounds: List[Optional[Skill]] = []
        for name, deps in compound_specs:
            s = self.teach_compound(name=name, dependency_skill_names=deps,
                                    description=f"Compound: {name.replace('_', ' ')}")
            compounds.append(s)

        # 3. Build L2 tasks from compounds
        task_specs = [
            ("check_mail", ["inspect_screen", "click_somewhere", "type_a_sentence"]),
            ("review_calendar", ["inspect_screen", "click_somewhere"]),
            ("analyse_market", ["run_command", "inspect_screen"]),
            ("make_a_decision", ["read_powershell", "type_a_sentence"]),
            ("delegate_tasks", ["type_a_sentence", "click_somewhere"]),
            ("strategic_thinking", ["inspect_screen", "read_powershell", "type_a_sentence"]),
        ]
        tasks: List[Optional[Skill]] = []
        for name, deps in task_specs:
            t = self.build_task(name=name, dependency_skill_names=deps,
                                description=f"Task: {name.replace('_', ' ')}")
            tasks.append(t)

        # 4. Build L3 workflows from tasks
        workflow_specs = [
            ("morning_routine", ["check_mail", "review_calendar", "analyse_market"]),
            ("strategic_planning", ["analyse_market", "strategic_thinking", "make_a_decision"]),
            ("leadership_cycle", ["delegate_tasks", "strategic_thinking"]),
            ("end_of_day", ["review_calendar", "delegate_tasks"]),
        ]
        workflows: List[Optional[Skill]] = []
        for name, deps in workflow_specs:
            w = self.build_workflow(name=name, task_skill_names=deps,
                                    description=f"Workflow: {name.replace('_', ' ')}")
            workflows.append(w)

        # 5. Build the L4 role — be_ceo
        ceo = self.build_role(
            name="be_ceo",
            workflow_skill_names=[
                "morning_routine",
                "strategic_planning",
                "leadership_cycle",
                "end_of_day",
            ],
            description="Persona: act as a CEO — orchestrate the full day cycle",
        )

        # 6. Summary
        return {
            "atomics_count": len([s for s in atomics if s is not None]),
            "compound_count": len([s for s in compounds if s is not None]),
            "task_count": len([s for s in tasks if s is not None]),
            "workflow_count": len([s for s in workflows if s is not None]),
            "role_built": ceo is not None,
            "ceo_skill_id": ceo.skill_id if ceo else None,
            "ceo_status": ceo.status.value if ceo else None,
            "ceo_dependencies": ceo.dependencies if ceo else [],
            "library_size": len(self.library),
        }

    # ─────────────────────────────────────────────────────────────────────
    # Status
    # ─────────────────────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        return {
            "uptime_s": round(time.time() - self._created_at, 2),
            "library": self.library.get_stats(),
            "writer": self.writer.get_stats(),
            "validator": self.validator.get_stats(),
            "executor": self.executor.get_status(),
            "observer": self.observer.get_status(),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────


_architect_instance: Optional[CodeArchitect] = None
_architect_lock = threading.Lock()


def get_code_architect(**kwargs) -> CodeArchitect:
    """Get or create the singleton CodeArchitect."""
    global _architect_instance
    with _architect_lock:
        if _architect_instance is None:
            _architect_instance = CodeArchitect(**kwargs)
        return _architect_instance
