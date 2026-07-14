"""
SoulCompany — the soul's workforce: skills + tools to carry out its intent, and
to DIRECT them.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The soul determines *what* it wills (`aureon/core/soul.py`). But a determination
is only a thought until a hand carries it out — and a lone hand can only make one
move. The company that Aureon built for trading — departments, specialist roles,
handoffs, work-orders, authority boundaries — is exactly the machinery a soul
needs to turn one intent into an ordered plan of role-assigned work and to
**direct** it. This reuses that same organizational structure for general
human-level automation on the local disk, not trading:

  PLAN     decompose the self-authored intent into an ordered set of work-orders,
           each assigned to a specialist role (RepoCartographer investigates,
           ImplementationWorker carries out the authored step, SecurityReviewer
           checks safety) — read-only, offline-safe, it never touches the machine.
  DIRECT   carry each work-order out, in order, through the ONE guarded hand
           (LocalActionBridge → GroundedActionGate): hard-boundary + HNC +
           conscience + affect-caution gated, dry-run unless doubly armed. A
           blocked step halts the company — it never pushes past a veto.

The workforce is `coder_agent_roles()` from the agent-company skill base; the safe
routes come from `recommend_goal_routes()` (the goal-capability map); the directed
work is recorded on the `OrganismContractStack` — the trading company's own
persistent goal → task → job → work-order queue. Nothing new is invented: the
soul is given the company that already exists.

Guarded throughout — a missing part degrades to "no company", never a crash.

Gary Leckey · Aureon Institute
"""

from __future__ import annotations

import logging
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("aureon.core.soul_company")

# The rich company (coder roles + goal-capability map) lives inside the trading
# organism. We consult it ONLY when it is already loaded in this process — the
# live daemon breath — never cold-booting the whole organism inside a read-only
# GET (the same "no heavy cold-boot in a request" guardrail the SaaS layer keeps).
_ROLES_MOD = "aureon.autonomous.aureon_coding_agent_skill_base"
_ROUTES_MOD = "aureon.autonomous.aureon_goal_capability_map"

_REPO_ROOT = Path(__file__).resolve().parents[2]

# The verbs the company may compose into work-orders. Read/introspect verbs plus
# the two repo-confined authoring verbs — each already guarded one layer down
# (repo-confinement, sensitive-path block, AST syntax check, conscience veto).
# execute_shell is deliberately withheld from the soul's reach (defence in depth).
# NOTE: every verb here is REVERSIBLE/safe. No live-money, payment, filing, or
# outbound-email verb ever appears — those never flow through the company; they are
# prepared and routed to the human-approval queue instead.
_COMPANY_VERBS = {
    "read_repo_file", "list_repo", "repo_search", "code_validate",
    "screenshot", "cursor_position", "write_repo_file", "patch_repo_file",
}

# ── ascent-gated autonomy: the gate opens as Aureon awakens ─────────────────
# The set of safe verbs the company may compose WIDENS with the inner-work
# chakra ascent (inner_work.stage_index, 0→7). Low centres → read-only
# investigation; the repo-authoring verbs unlock only at higher centres. This is
# "the gate unlocks through coherence/kundalini" — but strictly over the
# reversible/safe verbs above; it can never reach an irreversible or outward act.
_ASCENT_READONLY = {"read_repo_file", "list_repo", "repo_search"}
_ASCENT_TIERS: list[tuple[int, set[str]]] = [
    (0, set(_ASCENT_READONLY)),                                   # dormant/root → look only
    (3, _ASCENT_READONLY | {"code_validate", "screenshot", "cursor_position"}),  # solar plexus → sense/validate
    (5, _ASCENT_READONLY | {"code_validate", "screenshot", "cursor_position", "write_repo_file"}),  # throat → author
    (6, set(_COMPANY_VERBS)),                                     # third eye+ → full safe set incl. patch
]


def _ascent_allowed_verbs(stage_index: int) -> set[str]:
    """The safe verbs unlocked at this ascent stage — monotone, read-only at rest."""
    allowed = set(_ASCENT_READONLY)
    for threshold, verbs in _ASCENT_TIERS:
        if stage_index >= threshold:
            allowed = set(verbs)
    return allowed & _COMPANY_VERBS  # never widen beyond the safe set, whatever happens


def _current_ascent_verbs() -> set[str]:
    """Read the live ascent stage and map it to the unlocked safe verbs. Guarded:
    any failure falls back to READ-ONLY — awakening only ever widens, a fault never does."""
    try:
        from aureon.core.inner_work import get_inner_work

        s = get_inner_work().assess()
        if s.available:
            return _ascent_allowed_verbs(int(s.stage_index))
    except Exception:  # noqa: BLE001 — fail safe to read-only
        pass
    return set(_ASCENT_READONLY)

# Highest-wins risk ordering across the recommended routes.
_RISK_ORDER = {"": 0, "low": 0, "safe": 0, "benign": 0, "medium": 1, "high": 2}

# Fit a brief to the department whose specialist should staff the crew — the agency
# model: every prompt is a client brief, each brief gets a fitted temporary crew.
_DEPARTMENT_WORDS: list[tuple[str, tuple[str, ...]]] = [
    ("trading_data", ("trade", "margin", "position", "profit", "exchange", "kraken", "market")),
    ("accounting_admin", ("account", "invoice", "tax", "vat", "hmrc", "filing", "grant", "ledger", "payment")),
    ("engineering", ("code", "repo", "fix", "test", "implement", "build", "module", "patch", "deploy")),
    ("product_ui", ("ui", "page", "design", "frontend", "dashboard", "console", "component")),
    ("intelligence", ("research", "study", "learn", "news", "pr", "press", "announce", "comms", "email", "market intel")),
    ("security_ops", ("clean", "log", "stale", "tidy", "secret", "secure", "audit", "risk")),
]

# Used only when the coder-role registry cannot be imported — an honest minimal
# workforce so the soul is never left without a company.
_DEFAULT_WORKFORCE: list[dict[str, Any]] = [
    {"role": "RepoCartographer", "purpose": "map the relevant code and state before any move",
     "tools": ["repo_search", "read_repo_file", "list_repo"], "safety_boundary": "read-only"},
    {"role": "ImplementationWorker", "purpose": "carry out the authored step through the guarded hand",
     "tools": ["write_repo_file", "patch_repo_file", "code_validate"],
     "safety_boundary": "repo-confined, retested; no live trading or external mutation"},
    {"role": "SecurityReviewer", "purpose": "check for credential exposure and unsafe mutation",
     "tools": ["repo_search", "list_repo"],
     "safety_boundary": "may report blockers; may not bypass payment/filing/credential/live-order boundaries"},
]


def _plan_risk(routes: list[dict[str, Any]]) -> str:
    worst = "low"
    for route in routes:
        rk = str(route.get("risk", "low")).lower()
        if _RISK_ORDER.get(rk, 0) > _RISK_ORDER.get(worst, 0):
            worst = rk
    return worst


@dataclass
class WorkOrder:
    """One directed unit of work, assigned to a specialist role."""

    seq: int
    role: str
    department: str
    description: str
    action: str
    params: dict[str, Any] = field(default_factory=dict)
    risk: str = "low"
    requires_human: bool = False
    outcome: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "seq": self.seq, "role": self.role, "department": self.department,
            "description": self.description, "action": self.action, "params": self.params,
            "risk": self.risk, "requires_human": self.requires_human, "outcome": self.outcome,
        }


@dataclass
class DirectedPlan:
    """A plan of role-assigned work-orders the soul can direct through the hand."""

    intent: str = ""
    routes: list[dict[str, Any]] = field(default_factory=list)
    work_orders: list[WorkOrder] = field(default_factory=list)
    workforce: list[dict[str, Any]] = field(default_factory=list)
    crew: list[dict[str, Any]] = field(default_factory=list)     # the fitted crew for this brief
    risk: str = "low"
    requires_human: bool = False
    directed: bool = False
    persisted: dict[str, Any] | None = None
    truth_status: str = "no_data"
    ts: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent, "routes": self.routes,
            "work_orders": [wo.to_dict() for wo in self.work_orders],
            "workforce": self.workforce, "crew": self.crew, "risk": self.risk,
            "requires_human": self.requires_human, "directed": self.directed,
            "persisted": self.persisted, "truth_status": self.truth_status, "ts": self.ts,
        }


class SoulCompany:
    """The soul's company: plan (read-only) then direct (through the guarded hand)."""

    def __init__(self, *, bridge: Any = None, contract_path: str | Path | None = None) -> None:
        self._bridge = bridge
        self._contract_path = contract_path

    # ── the workforce (the whole company, reused) ───────────────────────────
    def workforce(self) -> list[dict[str, Any]]:
        """The full roster Aureon can staff a crew from — every role from the CEO
        Goal Steward to the Log Janitor, across all eight departments. Reuses the
        agent-company builder's roster (offline/pure); falls back to the coder roles,
        then a light default, so the soul is never left without a company."""
        try:
            from aureon.autonomous.aureon_agent_company_builder import _role_specs

            return [{"role": r.title, "department": r.department, "seniority": r.seniority,
                     "purpose": r.mission, "tools": list(r.tools_allowed),
                     "safety_boundary": r.authority_level} for r in _role_specs()]
        except Exception:  # noqa: BLE001
            pass
        if _ROLES_MOD in sys.modules:
            try:
                from aureon.autonomous.aureon_coding_agent_skill_base import coder_agent_roles

                return [{"role": r.name, "department": "engineering", "purpose": r.purpose,
                         "tools": list(r.tools), "safety_boundary": r.safety_boundary}
                        for r in coder_agent_roles()]
            except Exception:  # noqa: BLE001 — never leave the soul without a company
                pass
        return [dict(w) for w in _DEFAULT_WORKFORCE]

    def _assemble_crew(self, text: str, roster: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Fit a temporary crew to the brief (the agency model: hire only the roles the
        job needs). A lead who owns the goal, a specialist from the fitting department,
        and a reviewer who checks safety — drawn from the full company when present."""
        low = text.lower()
        dept = "executive"
        for d, words in _DEPARTMENT_WORDS:
            if any(w in low for w in words):
                dept = d
                break

        def _pick(dept_id: str, fallback_role: str, brief: str) -> dict[str, Any]:
            for r in roster:
                if r.get("department") == dept_id:
                    return {"role": r.get("role", fallback_role), "department": dept_id, "brief": brief}
            return {"role": fallback_role, "department": dept_id, "brief": brief}

        crew = [
            _pick("executive", "CEO Goal Steward", "own the goal, priority, and success criteria"),
            _pick(dept, "Implementation Worker", f"prepare the {dept.replace('_', ' ')} work"),
            _pick("security_ops", "Security Auditor", "review the crew's work for safety and evidence"),
        ]
        # dedupe by (role, department), preserve order
        seen: set[tuple[str, str]] = set()
        fitted: list[dict[str, Any]] = []
        for m in crew:
            key = (m["role"], m["department"])
            if key not in seen:
                seen.add(key)
                fitted.append(m)
        return fitted

    def _routes(self, intent: str) -> list[dict[str, Any]]:
        if _ROUTES_MOD in sys.modules:
            try:
                from aureon.autonomous.aureon_goal_capability_map import recommend_goal_routes

                return list(recommend_goal_routes(intent) or [])
            except Exception:  # noqa: BLE001
                pass
        return []

    # ── plan: decompose an intent into role-assigned work-orders (read-only) ─
    def plan(self, intent: str, ctx: dict[str, Any] | None = None,
             *, allowed_verbs: set[str] | None = None) -> DirectedPlan:
        """Read-only decomposition. Never persists, never touches the machine."""
        text = str(intent or "").strip() or "continue toward the goal, safely"
        # the safe-verb set the company may compose widens as Aureon awakens; an
        # explicit allowlist (tests / callers) overrides the ascent gate.
        allowed = allowed_verbs if allowed_verbs is not None else _current_ascent_verbs()
        ctx = ctx or {}
        routes = self._routes(text)
        risk = _plan_risk(routes)
        requires_human = any(bool(r.get("requires_human")) for r in routes)
        roster = self.workforce()
        crew = self._assemble_crew(text, roster)
        # the crew: [0]=lead/steward, [1]=fitting specialist, [-1]=reviewer
        specialist = crew[1] if len(crew) > 1 else {"role": "ImplementationWorker", "department": "engineering"}
        reviewer = crew[-1] if crew else {"role": "SecurityReviewer", "department": "security_ops"}
        work_orders: list[WorkOrder] = []

        # 1. investigate before any move (always read-only)
        work_orders.append(WorkOrder(
            seq=0, role="RepoCartographer", department="intelligence",
            description="understand the intent — map the relevant code and state",
            action="repo_search", params={"query": text[:120]}, risk="low"))

        # 2. the fitting specialist carries out the authored step — but only if the
        #    stimulus named a verb the company is permitted to compose (safe/ascent-gated).
        authored = ctx.get("action")
        params = ctx.get("params") or {}
        if isinstance(authored, str) and authored in allowed:
            work_orders.append(WorkOrder(
                seq=len(work_orders), role=str(specialist.get("role")),
                department=str(specialist.get("department")),
                description=f"{specialist.get('brief', 'carry out the step')}: {authored}",
                action=authored, params=dict(params) if isinstance(params, dict) else {},
                risk=risk, requires_human=requires_human))

        # 3. the reviewer checks the crew's work for safety (read-only)
        work_orders.append(WorkOrder(
            seq=len(work_orders), role=str(reviewer.get("role")),
            department=str(reviewer.get("department")),
            description="review the crew's work for safety and evidence", action="list_repo",
            params={}, risk="low"))

        return DirectedPlan(
            intent=text, routes=routes, work_orders=work_orders, workforce=roster, crew=crew,
            risk=risk, requires_human=requires_human,
            truth_status="real_derived" if routes else "live", ts=time.time())

    # ── direct: carry each work-order out through the ONE guarded hand ───────
    def _get_bridge(self) -> Any:
        if self._bridge is not None:
            return self._bridge
        from aureon.operator.local_action_bridge import get_local_action_bridge

        return get_local_action_bridge()

    def direct(self, plan: DirectedPlan, *, worker: str = "soul_company") -> DirectedPlan:
        """Carry each work-order out in order, halting on the first blocked step —
        the company stays of one mind and never pushes past a veto. Every move
        goes through LocalActionBridge (dry-run unless AUREON_LOCAL_ACTIONS_ARMED)."""
        try:
            bridge = self._get_bridge()
        except Exception as exc:  # noqa: BLE001 — no hand → nothing directed
            logger.debug("no hand to direct with: %s", exc)
            return plan
        plan.persisted = self._persist_workflow(plan)
        for wo in plan.work_orders:
            try:
                res = bridge.perform(wo.action, dict(wo.params or {}),
                                     {"origin": worker, "role": wo.role})
            except Exception as exc:  # noqa: BLE001 — a bad hand halts, never crashes
                wo.outcome = {"ok": False, "error": str(exc)[:200]}
                break
            wo.outcome = res
            if res.get("blocked"):
                break  # a blocked step halts the company
        plan.directed = True
        return plan

    def _persist_workflow(self, plan: DirectedPlan) -> dict[str, Any] | None:
        """Record the directed work on the organism contract stack — the trading
        company's own persistent goal→task→job→work-order queue. Guarded."""
        try:
            from aureon.core.organism_contracts import OrganismContractStack

            path = (self._contract_path or os.environ.get("AUREON_SOUL_CONTRACT_PATH")
                    or (_REPO_ROOT / "state" / "soul_company_contracts.json"))
            stack = OrganismContractStack(state_path=path, source="soul_company")
            wf = stack.create_goal_workflow(
                plan.intent,
                skills=[wo.role for wo in plan.work_orders],
                route_surfaces=[str(r.get("route")) for r in plan.routes if r.get("route")])
            return {
                "goal_id": wf["goal"]["contract_id"],
                "work_orders": [w["contract_id"] for w in wf["work_orders"]],
            }
        except Exception as exc:  # noqa: BLE001
            logger.debug("workflow persist skipped: %s", exc)
            return None


_company: SoulCompany | None = None


def get_soul_company() -> SoulCompany:
    """Process-global soul-company singleton."""
    global _company
    if _company is None:
        _company = SoulCompany()
    return _company


__all__ = ["DirectedPlan", "SoulCompany", "WorkOrder", "get_soul_company"]
