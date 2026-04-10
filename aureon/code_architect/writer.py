"""
SkillWriter — turns observed patterns into executable Python skills
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Two modes of operation:

  1. TEMPLATE MODE (deterministic, always available)
     Takes an ObservedPattern and emits a Python function that calls the
     primitive sequence directly. No LLM required — perfect for stress tests,
     CI, and environments without a model server.

  2. AI MODE (in-house adapter)
     Prompts the AureonBrainAdapter / AureonLocalAdapter to:
       • Invent a meaningful name
       • Write a Python function that uses the primitives
       • Explain its reasoning
     Then returns a SkillProposal.

Both modes produce SkillProposal objects. The writer also supports:
  • propose_atomic(action, params)        — L0 skills (single primitive wrap)
  • propose_compound(name, steps)         — L1/L2 manual composition
  • propose_workflow(name, task_names)    — L3 composition of tasks
  • propose_role(name, workflow_names)    — L4 role assembly (e.g., be_ceo)
"""

from __future__ import annotations

import logging
import re
import textwrap
import time
from typing import Any, Dict, List, Optional

from aureon.code_architect.skill import (
    Skill,
    SkillProposal,
    SkillLevel,
)
from aureon.code_architect.observer import ObservedPattern

logger = logging.getLogger("aureon.code_architect.writer")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


_NAME_SANITISE = re.compile(r"[^a-zA-Z0-9_]")


def sanitise_name(name: str, fallback: str = "skill") -> str:
    """Make a string a valid Python function name."""
    if not name:
        return fallback
    cleaned = _NAME_SANITISE.sub("_", name.strip()).strip("_").lower()
    if not cleaned:
        cleaned = fallback
    if cleaned[0].isdigit():
        cleaned = f"s_{cleaned}"
    return cleaned[:64]


def _indent(code: str, spaces: int = 4) -> str:
    pad = " " * spaces
    return "\n".join(pad + line if line.strip() else line for line in code.split("\n"))


# ─────────────────────────────────────────────────────────────────────────────
# SkillWriter
# ─────────────────────────────────────────────────────────────────────────────


class SkillWriter:
    """Generates SkillProposal objects from observations or manual specs."""

    def __init__(self, adapter: Any = None):
        self.adapter = adapter          # optional: AureonBrainAdapter / Local / Hybrid
        self._use_ai = adapter is not None

        # Metrics
        self._proposals_created = 0
        self._ai_proposals = 0
        self._template_proposals = 0

    def _load_adapter_if_needed(self) -> None:
        if self.adapter is not None:
            return
        try:
            from aureon.inhouse_ai.llm_adapter import AureonBrainAdapter
            self.adapter = AureonBrainAdapter()
            self._use_ai = True
        except Exception:
            self._use_ai = False

    # ─────────────────────────────────────────────────────────────────────
    # Level 0 — atomic (single primitive wrapper)
    # ─────────────────────────────────────────────────────────────────────

    def propose_atomic(
        self,
        action: str,
        params_schema: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
        description: str = "",
        category: str = "atomic",
        target: str = "vm",
    ) -> SkillProposal:
        """
        Wrap a single primitive as an atomic L0 skill.

        The generated code looks like:

            def the_name(**kwargs):
                return vm_action(**kwargs)
        """
        # Ensure the action is a known primitive name
        primitive_name = action if action.startswith("vm_") else f"vm_{action}"
        skill_name = sanitise_name(name or primitive_name)

        params_schema = params_schema or {"type": "object", "properties": {}}

        code = textwrap.dedent(f"""
            def {skill_name}(**kwargs):
                \"\"\"{description or f"Atomic skill wrapping {primitive_name}"}\"\"\"
                return {primitive_name}(**kwargs)
        """).strip()

        proposal = SkillProposal(
            name=skill_name,
            description=description or f"Atomic: call {primitive_name}",
            level=SkillLevel.ATOMIC,
            category=category,
            code=code,
            entry_function=skill_name,
            params_schema=params_schema,
            dependencies=[],
            reasoning=f"Atomic skill directly wrapping primitive {primitive_name}",
            target=target,
        )
        self._proposals_created += 1
        self._template_proposals += 1
        return proposal

    # ─────────────────────────────────────────────────────────────────────
    # Level 1 — compound (from an ObservedPattern)
    # ─────────────────────────────────────────────────────────────────────

    def propose_from_pattern(
        self,
        pattern: ObservedPattern,
        name: Optional[str] = None,
        description: Optional[str] = None,
        level: SkillLevel = SkillLevel.COMPOUND,
        use_ai: Optional[bool] = None,
    ) -> SkillProposal:
        """
        Generate a SkillProposal from an ObservedPattern.

        Uses template mode by default; if use_ai=True (or the writer has
        an adapter and use_ai is None) it asks the in-house adapter to
        refine the name and description.
        """
        base_name = sanitise_name(name or pattern.suggested_name or f"pattern_{pattern.signature}")
        base_desc = description or pattern.suggested_description or f"Compound skill from pattern {pattern.signature}"

        # ── Template generation (always run) ────────────────────────────
        code = self._template_code_for_pattern(base_name, base_desc, pattern)

        proposal = SkillProposal(
            name=base_name,
            description=base_desc,
            level=level,
            category="compound",
            code=code,
            entry_function=base_name,
            params_schema={"type": "object", "properties": {}},
            dependencies=[],
            observation_sources=[pattern.signature],
            reasoning=(
                f"Compound skill assembled from observed pattern occurring "
                f"{pattern.occurrence_count} times with coherence {pattern.coherence:.3f}"
            ),
            target="vm",
        )
        self._template_proposals += 1

        # ── Optional AI refinement of name/description ──────────────────
        should_use_ai = self._use_ai if use_ai is None else bool(use_ai)
        if should_use_ai:
            self._load_adapter_if_needed()
        if should_use_ai and self.adapter is not None:
            refined = self._refine_with_ai(proposal, pattern)
            if refined:
                proposal = refined
                self._ai_proposals += 1

        self._proposals_created += 1
        return proposal

    def _template_code_for_pattern(
        self,
        name: str,
        description: str,
        pattern: ObservedPattern,
    ) -> str:
        """Emit a Python function that replays the pattern's primitive sequence."""
        lines: List[str] = []
        lines.append(f"def {name}(**kwargs):")
        # Docstring
        lines.append(f'    """{description}"""')
        lines.append("    results = []")
        for i, action in enumerate(pattern.action_sequence):
            action_name = action["action"]
            # Ensure it uses the vm_ prefix for VM primitives
            primitive_name = action_name if action_name in {"observe_snapshot", "emit_event", "call_skill", "safe_sleep", "safe_log"} else action_name
            if not primitive_name.startswith("vm_") and primitive_name not in {"observe_snapshot", "emit_event", "call_skill", "safe_sleep", "safe_log"}:
                primitive_name = f"vm_{primitive_name}"

            # Skip the observe_snapshot pseudo-action — it's observational, not executable
            if primitive_name == "observe_snapshot":
                lines.append(f"    # step {i}: observation (skipped — observational only)")
                continue

            # Sanitise params: quote string values, pass numbers directly
            params = action.get("params") or {}
            param_strs: List[str] = []
            for k, v in params.items():
                # Skip non-serialisable or VM-specific bookkeeping fields
                if k in ("simulated", "session_id"):
                    continue
                if isinstance(v, str):
                    safe_v = v.replace("\\", "\\\\").replace('"', '\\"')
                    param_strs.append(f'{k}="{safe_v}"')
                elif isinstance(v, (int, float, bool)):
                    param_strs.append(f"{k}={v}")
                elif v is None:
                    continue
                elif isinstance(v, (list, tuple)):
                    param_strs.append(f"{k}={list(v)}")
            param_src = ", ".join(param_strs)
            lines.append(f"    results.append({primitive_name}({param_src}))")

        lines.append("    return {'ok': True, 'steps': len(results), 'results': results}")
        return "\n".join(lines)

    def _refine_with_ai(self, proposal: SkillProposal, pattern: ObservedPattern) -> Optional[SkillProposal]:
        """Ask the adapter to refine the name + description (not the code)."""
        try:
            system = (
                "You are the Aureon code architect. Given an observed action sequence, "
                "invent a short snake_case function name and a one-sentence description "
                "that captures the *intent* of the sequence. Respond in JSON like "
                "{\"name\": \"...\", \"description\": \"...\"}."
            )
            actions_summary = " → ".join(a["action"] for a in pattern.action_sequence)
            user = f"Action sequence: {actions_summary}\nOccurrences: {pattern.occurrence_count}"
            response = self.adapter.prompt(
                messages=[{"role": "user", "content": user}],
                system=system,
                max_tokens=200,
            )
            text = response.text or ""
            # Try to extract JSON
            import json, re as _re
            match = _re.search(r"\{[^{}]*\"name\"[^{}]*\}", text, _re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                new_name = sanitise_name(data.get("name", proposal.name))
                new_desc = str(data.get("description", proposal.description))[:240]
                if new_name and new_name != proposal.name:
                    # Regenerate the code with the new function name
                    new_code = proposal.code.replace(f"def {proposal.name}(", f"def {new_name}(", 1)
                    proposal.code = new_code
                    proposal.entry_function = new_name
                    proposal.name = new_name
                proposal.description = new_desc
                proposal.reasoning = (
                    proposal.reasoning + f" | Refined by in-house AI: {new_desc[:80]}"
                )
        except Exception as e:
            logger.debug("AI refinement skipped: %s", e)
        return proposal

    # ─────────────────────────────────────────────────────────────────────
    # Level 2 / 3 / 4 — manual composition
    # ─────────────────────────────────────────────────────────────────────

    def propose_compound(
        self,
        name: str,
        dependency_skill_names: List[str],
        description: str = "",
        level: SkillLevel = SkillLevel.COMPOUND,
        category: str = "compound",
        target: str = "vm",
    ) -> SkillProposal:
        """
        Propose a skill that invokes a list of lower-level skills in order.

        The generated function calls `call_skill(name)` for each dependency.
        """
        skill_name = sanitise_name(name)
        description = description or f"Compound of {len(dependency_skill_names)} skills"

        lines = [f"def {skill_name}(**kwargs):"]
        lines.append(f'    """{description}"""')
        lines.append("    results = []")
        for dep in dependency_skill_names:
            safe_dep = sanitise_name(dep)
            lines.append(f'    results.append(call_skill("{safe_dep}"))')
        lines.append("    return {'ok': all(r.get('ok', False) for r in results), 'steps': len(results), 'results': results}")
        code = "\n".join(lines)

        proposal = SkillProposal(
            name=skill_name,
            description=description,
            level=level,
            category=category,
            code=code,
            entry_function=skill_name,
            params_schema={"type": "object", "properties": {}},
            dependencies=[sanitise_name(d) for d in dependency_skill_names],
            reasoning=f"Composition of {len(dependency_skill_names)} sub-skills",
            target=target,
        )
        self._proposals_created += 1
        self._template_proposals += 1
        return proposal

    def propose_workflow(
        self,
        name: str,
        task_skill_names: List[str],
        description: str = "",
    ) -> SkillProposal:
        return self.propose_compound(
            name=name,
            dependency_skill_names=task_skill_names,
            description=description or f"Workflow {name}: {len(task_skill_names)} tasks",
            level=SkillLevel.WORKFLOW,
            category="workflow",
        )

    def propose_role(
        self,
        name: str,
        workflow_skill_names: List[str],
        description: str = "",
    ) -> SkillProposal:
        """
        Propose a Level 4 ROLE skill (a persona) that composes workflows.

        Example: propose_role("be_ceo", ["morning_routine", "strategic_planning",
                                          "financial_review", "end_of_day"])
        """
        skill_name = sanitise_name(name)
        description = description or f"Role {skill_name}: {len(workflow_skill_names)} workflows"

        lines = [f"def {skill_name}(**kwargs):"]
        lines.append(f'    """{description}"""')
        lines.append("    emit_event('role.enter', {'role': '" + skill_name + "'})")
        lines.append("    safe_log('Entering role: " + skill_name + "')")
        lines.append("    results = []")
        for wf in workflow_skill_names:
            safe_wf = sanitise_name(wf)
            lines.append(f'    r = call_skill("{safe_wf}")')
            lines.append(f'    results.append(r)')
            lines.append("    safe_sleep(0.05)  # pacing between workflows")
        lines.append("    emit_event('role.exit', {'role': '" + skill_name + "', 'success': all(r.get('ok', False) for r in results)})")
        lines.append("    return {'ok': all(r.get('ok', False) for r in results), 'role': '" + skill_name + "', 'workflows': len(results), 'results': results}")
        code = "\n".join(lines)

        proposal = SkillProposal(
            name=skill_name,
            description=description,
            level=SkillLevel.ROLE,
            category="role",
            code=code,
            entry_function=skill_name,
            params_schema={"type": "object", "properties": {}},
            dependencies=[sanitise_name(w) for w in workflow_skill_names],
            reasoning=f"Role persona composing {len(workflow_skill_names)} workflows",
            target="either",
        )
        self._proposals_created += 1
        self._template_proposals += 1
        return proposal

    # ─────────────────────────────────────────────────────────────────────
    # Stats
    # ─────────────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        return {
            "proposals_created": self._proposals_created,
            "template_proposals": self._template_proposals,
            "ai_proposals": self._ai_proposals,
            "adapter_available": self.adapter is not None,
        }
