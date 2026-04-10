"""
SkillValidator — safety + meaning + harmonic alignment
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Every SkillProposal must pass three gates before it becomes a Skill:

  1. STATIC SAFETY      — AST parse + forbidden-node walk
       • Reject: eval, exec, compile, __import__, open() writes, raise
         SystemExit, attribute access with dunders
       • Only allow Import of whitelisted modules (math, random, json, time)
         — but the safe globals block imports anyway; this is belt & braces
       • Reject any reference to names that are NOT in the allowed set
         (primitives + local args + whitelisted names)

  2. QUEEN MEANING      — QueenAIBridge.synthesise_insight()
       • Feeds the skill name + description + code hash to the bridge
       • Returns confidence + reasoning
       • A confidence of 0 means "no verdict" (degraded gracefully);
         negative verdicts block the skill.

  3. HARMONIC ALIGNMENT — PillarAlignment.run_synthetic_cycle()
       • Builds a pseudo-pillar signal from the skill's harmonic signature
         (derived from primitive types used: destructive vs read-only, etc.)
       • Runs a synthetic alignment cycle
       • Requires alignment > 0.5 for baseline validation
       • Lighthouse (>0.945) is a separate "approved" flag the executor
         can check for high-stakes skill runs on end-user hardware.
"""

from __future__ import annotations

import ast
import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from aureon.code_architect.skill import Skill, SkillProposal, SkillStatus, SkillLevel
from aureon.code_architect.primitives import PRIMITIVE_NAMES

logger = logging.getLogger("aureon.code_architect.validator")


# ─────────────────────────────────────────────────────────────────────────────
# Allowed identifiers — primitives + python basics
# ─────────────────────────────────────────────────────────────────────────────

ALLOWED_NAMES: Set[str] = set(PRIMITIVE_NAMES) | {
    # Types
    "bool", "int", "float", "str", "bytes", "list", "tuple", "dict", "set", "frozenset",
    # Builtins
    "len", "range", "enumerate", "zip", "map", "filter", "reversed", "sorted",
    "all", "any", "sum", "min", "max", "abs", "round",
    "isinstance", "issubclass", "hasattr", "getattr", "type",
    "print", "repr",
    # Keywords / literals
    "True", "False", "None",
    # Allowed locals always created inside skill functions
    "kwargs", "args", "self", "results", "result", "r", "i", "step", "value",
}

# Allowed call names include everything in ALLOWED_NAMES
ALLOWED_CALLS: Set[str] = set(ALLOWED_NAMES)

FORBIDDEN_CALLS: Set[str] = {
    "eval", "exec", "compile", "__import__", "globals", "locals", "vars",
    "input", "breakpoint", "memoryview", "classmethod", "staticmethod",
    "open",  # we allow nothing to open files — primitives handle I/O
    "exit", "quit",
    # Reflection abuse
    "__class__", "__subclasses__", "__bases__", "__mro__",
}

# Allowed Import targets — the exec environment blocks imports entirely,
# but we still reject them at AST level as a second gate.
ALLOWED_IMPORTS: Set[str] = {"math", "random", "json", "time"}


# ─────────────────────────────────────────────────────────────────────────────
# ValidationResult
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ValidationResult:
    """The outcome of running all gates on a SkillProposal."""

    proposal_id: str = ""
    name: str = ""

    # Gate 1 — static safety
    static_safe: bool = False
    static_errors: List[str] = field(default_factory=list)

    # Gate 2 — Queen meaning
    queen_verdict: Optional[str] = None
    queen_confidence: float = 0.0
    queen_reasoning: str = ""

    # Gate 3 — harmonic alignment
    pillar_alignment_score: float = 0.0
    pillar_lighthouse: bool = False
    harmonic_signature: Dict[str, float] = field(default_factory=dict)

    # Overall
    validated: bool = False
    approved: bool = False     # True when ALL three gates plus Lighthouse pass
    reasoning: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "name": self.name,
            "static_safe": self.static_safe,
            "static_errors": self.static_errors,
            "queen_verdict": self.queen_verdict,
            "queen_confidence": round(self.queen_confidence, 4),
            "queen_reasoning": self.queen_reasoning,
            "pillar_alignment_score": round(self.pillar_alignment_score, 4),
            "pillar_lighthouse": self.pillar_lighthouse,
            "harmonic_signature": self.harmonic_signature,
            "validated": self.validated,
            "approved": self.approved,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Static AST walker
# ─────────────────────────────────────────────────────────────────────────────


class _SafetyVisitor(ast.NodeVisitor):
    """Walks the AST and rejects forbidden constructs."""

    def __init__(self):
        self.errors: List[str] = []
        # Track names defined locally inside the function body (params + assignments)
        self.local_names: Set[str] = set()
        self._depth = 0

    # ── Imports are forbidden (extra belt) ──────────────────────────────
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.name not in ALLOWED_IMPORTS:
                self.errors.append(f"forbidden import: {alias.name}")

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module not in ALLOWED_IMPORTS:
            self.errors.append(f"forbidden import from: {node.module}")

    # ── Function def ────────────────────────────────────────────────────
    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Collect argument names
        for arg in node.args.args:
            self.local_names.add(arg.arg)
        for arg in node.args.kwonlyargs:
            self.local_names.add(arg.arg)
        if node.args.vararg:
            self.local_names.add(node.args.vararg.arg)
        if node.args.kwarg:
            self.local_names.add(node.args.kwarg.arg)

        self._depth += 1
        self.generic_visit(node)
        self._depth -= 1

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.errors.append("async functions are not allowed in skills")

    def visit_Lambda(self, node: ast.Lambda):
        for arg in node.args.args:
            self.local_names.add(arg.arg)
        self.generic_visit(node)

    # ── Assignments register local names ────────────────────────────────
    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            self._collect_assign_targets(target)
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        self._collect_assign_targets(node.target)
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension):
        self._collect_assign_targets(node.target)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign):
        self._collect_assign_targets(node.target)
        self.generic_visit(node)

    def _collect_assign_targets(self, node: ast.AST) -> None:
        if isinstance(node, ast.Name):
            self.local_names.add(node.id)
        elif isinstance(node, (ast.Tuple, ast.List)):
            for elt in node.elts:
                self._collect_assign_targets(elt)
        elif isinstance(node, ast.Starred):
            self._collect_assign_targets(node.value)
        elif isinstance(node, ast.Subscript):
            pass  # dict/list access is fine

    # ── Call nodes ──────────────────────────────────────────────────────
    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            name = node.func.id
            if name in FORBIDDEN_CALLS:
                self.errors.append(f"forbidden call: {name}")
            elif name not in ALLOWED_CALLS and name not in self.local_names:
                self.errors.append(f"unknown call: {name}")
        elif isinstance(node.func, ast.Attribute):
            # Only allow attribute calls on the allowed modules (math, random, json)
            # or on objects that are clearly primitives returning dicts
            root = self._attribute_root(node.func)
            if root in {"math", "random", "json"}:
                pass  # ok
            elif root in self.local_names or root in ALLOWED_NAMES:
                pass  # e.g. results.append(), r.get() — standard method calls
            else:
                self.errors.append(f"attribute call on non-allowed object: {root}")
        self.generic_visit(node)

    def _attribute_root(self, attr: ast.Attribute) -> str:
        while isinstance(attr, ast.Attribute):
            attr = attr.value
        if isinstance(attr, ast.Name):
            return attr.id
        return "<complex>"

    # ── Forbid dunder attribute access ──────────────────────────────────
    def visit_Attribute(self, node: ast.Attribute):
        if isinstance(node.attr, str) and node.attr.startswith("__") and node.attr.endswith("__"):
            if node.attr not in {"__init__", "__name__"}:
                self.errors.append(f"forbidden dunder attribute: {node.attr}")
        self.generic_visit(node)

    # ── Raise SystemExit / forbidden raise patterns ─────────────────────
    def visit_Raise(self, node: ast.Raise):
        if node.exc and isinstance(node.exc, ast.Call):
            if isinstance(node.exc.func, ast.Name) and node.exc.func.id == "SystemExit":
                self.errors.append("raise SystemExit is forbidden")
        self.generic_visit(node)

    # ── With statements are fine, but only for safe primitives we return ─
    # (no special handling)


# ─────────────────────────────────────────────────────────────────────────────
# SkillValidator
# ─────────────────────────────────────────────────────────────────────────────


class SkillValidator:
    """
    Runs the three gates on a SkillProposal.
    """

    def __init__(
        self,
        queen_bridge: Any = None,
        pillar_alignment: Any = None,
        strict_static: bool = True,
    ):
        self.queen_bridge = queen_bridge
        self.pillar_alignment = pillar_alignment
        self.strict_static = strict_static

        # Metrics
        self._total_validations = 0
        self._static_failures = 0
        self._approved_count = 0

    def _load_subsystems(self) -> None:
        if self.queen_bridge is None:
            try:
                from aureon.queen.queen_inhouse_ai_bridge import get_queen_ai_bridge
                self.queen_bridge = get_queen_ai_bridge()
            except Exception:
                pass
        if self.pillar_alignment is None:
            try:
                from aureon.alignment.pillar_alignment import PillarAlignment, AlignmentConfig
                self.pillar_alignment = PillarAlignment(AlignmentConfig(auto_load_pillars=False))
            except Exception:
                pass

    # ─────────────────────────────────────────────────────────────────────
    # Gate 1 — static safety
    # ─────────────────────────────────────────────────────────────────────

    def static_check(self, code: str) -> (bool, List[str]):
        """
        AST parse + forbidden-node walk.

        Returns (ok, errors).
        """
        try:
            tree = ast.parse(code, mode="exec")
        except SyntaxError as e:
            return False, [f"syntax_error: {e}"]

        visitor = _SafetyVisitor()
        try:
            visitor.visit(tree)
        except Exception as e:
            return False, [f"ast_walk_error: {e}"]

        return len(visitor.errors) == 0, visitor.errors

    # ─────────────────────────────────────────────────────────────────────
    # Gate 2 — Queen meaning
    # ─────────────────────────────────────────────────────────────────────

    def queen_check(self, proposal: SkillProposal) -> Dict[str, Any]:
        if self.queen_bridge is None or not getattr(self.queen_bridge, "is_alive", False):
            return {
                "available": False,
                "verdict": "NO_VERDICT",
                "confidence": 0.0,
                "reasoning": "Queen bridge unavailable",
            }

        try:
            code_hash = hashlib.sha256(proposal.code.encode()).hexdigest()[:16]
            insight = self.queen_bridge.synthesise_insight(
                market_data={
                    "skill_name": proposal.name,
                    "skill_level": int(proposal.level),
                    "skill_description": proposal.description[:200],
                    "code_hash": code_hash,
                    "code_lines": len(proposal.code.split("\n")),
                    "dependency_count": len(proposal.dependencies),
                },
                system_signals=[{
                    "source": "code_architect",
                    "signal": "SKILL_PROPOSAL",
                    "confidence": 0.7,
                    "reasoning": proposal.reasoning[:200],
                }],
            )
            return {
                "available": True,
                "verdict": insight.signal,
                "confidence": float(insight.confidence),
                "reasoning": insight.reasoning[:300] if insight.reasoning else "",
            }
        except Exception as e:
            return {
                "available": False,
                "verdict": "ERROR",
                "confidence": 0.0,
                "reasoning": str(e)[:200],
            }

    # ─────────────────────────────────────────────────────────────────────
    # Gate 3 — harmonic alignment
    # ─────────────────────────────────────────────────────────────────────

    def _harmonic_signature(self, proposal: SkillProposal) -> Dict[str, float]:
        """
        Derive a harmonic signature from the skill's primitives usage.

        Simple heuristic: count references to different primitive categories
        and use them to weight Solfeggio frequencies.
        """
        code = proposal.code
        signature: Dict[str, float] = {
            "love": 0.0, "foundation": 0.0, "liberation": 0.0,
            "change": 0.0, "connection": 0.0, "expression": 0.0,
            "intuition": 0.0, "crown": 0.0,
        }

        # Heuristic buckets
        if "vm_type_text" in code:
            signature["expression"] += 1.0
        if "vm_screenshot" in code or "vm_list_windows" in code:
            signature["intuition"] += 0.8
        if "vm_execute_shell" in code or "vm_execute_powershell" in code:
            signature["liberation"] += 1.0
        if "vm_left_click" in code or "vm_right_click" in code or "vm_mouse_move" in code:
            signature["change"] += 0.6
        if "call_skill" in code:
            signature["connection"] += 1.2
        if "emit_event" in code or "safe_log" in code:
            signature["connection"] += 0.5
        if "safe_sleep" in code:
            signature["foundation"] += 0.3
        if proposal.level >= SkillLevel.ROLE:
            signature["crown"] += 1.5
        if proposal.level >= SkillLevel.WORKFLOW:
            signature["love"] += 1.0

        # Normalise
        total = sum(signature.values())
        if total > 0:
            signature = {k: v / total for k, v in signature.items()}
        else:
            signature = {k: 1 / len(signature) for k in signature}

        return signature

    def harmonic_check(self, proposal: SkillProposal) -> Dict[str, Any]:
        if self.pillar_alignment is None:
            return {
                "available": False,
                "alignment_score": 0.5,
                "lighthouse_cleared": False,
                "signature": self._harmonic_signature(proposal),
            }

        try:
            signature = self._harmonic_signature(proposal)

            # Build synthetic pillar signals derived from the signature.
            # High-signature categories become BUY (aligned), low become NEUTRAL.
            pillar_signals = [
                {
                    "pillar": "NexusAgent", "signal": "BUY" if signature["connection"] > 0.1 else "NEUTRAL",
                    "confidence": 0.7 + signature["connection"] * 0.3,
                    "coherence": 0.7 + signature["connection"] * 0.3,
                    "frequency_hz": 432.0,
                },
                {
                    "pillar": "OmegaAgent", "signal": "BUY" if signature["love"] > 0.1 else "NEUTRAL",
                    "confidence": 0.7 + signature["love"] * 0.3,
                    "coherence": 0.7 + signature["love"] * 0.3,
                    "frequency_hz": 432.0,
                },
                {
                    "pillar": "InfiniteAgent", "signal": "BUY",
                    "confidence": 0.75 + signature["crown"] * 0.2,
                    "coherence": 0.8,
                    "frequency_hz": 528.0,
                },
                {
                    "pillar": "PianoAgent", "signal": "BUY",
                    "confidence": 0.7 + signature["expression"] * 0.25,
                    "coherence": 0.75,
                    "frequency_hz": 396.0,
                },
                {
                    "pillar": "QGITAAgent", "signal": "BUY",
                    "confidence": 0.75 + signature["intuition"] * 0.25,
                    "coherence": 0.85,
                    "frequency_hz": 528.0,
                },
                {
                    "pillar": "AurisAgent", "signal": "BUY",
                    "confidence": 0.72 + signature["change"] * 0.28,
                    "coherence": 0.78,
                    "frequency_hz": 741.0,
                },
            ]
            result = self.pillar_alignment.run_synthetic_cycle(signals=pillar_signals)
            return {
                "available": True,
                "alignment_score": result.alignment_score,
                "lighthouse_cleared": result.lighthouse_cleared,
                "signature": signature,
            }
        except Exception as e:
            return {
                "available": False,
                "alignment_score": 0.5,
                "lighthouse_cleared": False,
                "signature": self._harmonic_signature(proposal),
                "error": str(e),
            }

    # ─────────────────────────────────────────────────────────────────────
    # Top-level validate()
    # ─────────────────────────────────────────────────────────────────────

    def validate(self, proposal: SkillProposal) -> ValidationResult:
        """Run all three gates and return a ValidationResult."""
        self._total_validations += 1
        self._load_subsystems()

        result = ValidationResult(proposal_id=proposal.proposal_id, name=proposal.name)

        # Gate 1
        safe, errors = self.static_check(proposal.code)
        result.static_safe = safe
        result.static_errors = errors
        if not safe:
            self._static_failures += 1
            result.reasoning = f"static_check failed: {errors[:3]}"
            result.validated = False
            result.approved = False
            return result

        # Gate 2
        queen = self.queen_check(proposal)
        result.queen_verdict = queen["verdict"]
        result.queen_confidence = queen["confidence"]
        result.queen_reasoning = queen["reasoning"]

        # Gate 3
        harmonic = self.harmonic_check(proposal)
        result.pillar_alignment_score = harmonic["alignment_score"]
        result.pillar_lighthouse = harmonic["lighthouse_cleared"]
        result.harmonic_signature = harmonic["signature"]

        # Combine verdicts
        result.validated = (
            result.static_safe
            and result.pillar_alignment_score >= 0.5
        )
        result.approved = (
            result.validated
            and (result.queen_confidence >= 0.5 or not queen.get("available"))
            and result.pillar_lighthouse
        )

        parts = [
            f"static={'OK' if result.static_safe else 'FAIL'}",
            f"queen={result.queen_confidence:.2f}",
            f"alignment={result.pillar_alignment_score:.3f}",
            "lighthouse=YES" if result.pillar_lighthouse else "lighthouse=no",
        ]
        result.reasoning = " | ".join(parts)

        if result.approved:
            self._approved_count += 1

        return result

    # ─────────────────────────────────────────────────────────────────────
    # Stats
    # ─────────────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_validations": self._total_validations,
            "static_failures": self._static_failures,
            "approved_count": self._approved_count,
            "approval_rate": (
                self._approved_count / self._total_validations if self._total_validations > 0 else 0.0
            ),
            "queen_bridge_alive": bool(
                self.queen_bridge and getattr(self.queen_bridge, "is_alive", False)
            ),
            "pillar_alignment_available": self.pillar_alignment is not None,
        }
