"""
SoulCompany — the soul's workforce: plan (read-only) then direct (through the
guarded hand).

Offline + hermetic: an isolated contract path, a fake guarded hand, and no
organism boot (the rich roster is consulted only when already loaded, so tests
exercise the light default workforce — deterministic). Proves the company
decomposes an intent into ordered, role-assigned work-orders without touching the
machine; that directing is DRY-RUN by default; that a blocked step halts the
company (it never pushes past a veto); and that every move goes through the hand.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    monkeypatch.setenv("AUREON_SOUL_CONTRACT_PATH", str(tmp_path / "contracts.json"))
    monkeypatch.delenv("AUREON_LOCAL_ACTIONS_ARMED", raising=False)
    import aureon.core.soul_company as sc

    monkeypatch.setattr(sc, "_company", None, raising=False)
    return tmp_path


class _FakeHand:
    """A stand-in LocalActionBridge: records every move and grounds it dry-run,
    but BLOCKS a forbidden verb (to prove a blocked step halts the company)."""

    def __init__(self, block=None):
        self.calls = []
        self._block = set(block or [])

    def perform(self, action, params=None, context=None):
        self.calls.append({"action": action, "params": params, "context": context})
        if action in self._block:
            return {"ok": False, "blocked": True, "executed": False, "dry_run": False}
        return {"ok": True, "blocked": False, "executed": False, "dry_run": True}


def _company(**kw):
    from aureon.core.soul_company import SoulCompany

    return SoulCompany(**kw)


# ── plan: read-only decomposition into role-assigned work-orders ──────────────

def test_plan_decomposes_into_role_assigned_work_orders():
    plan = _company().plan("open the project README and summarise it",
                           {"action": "read_repo_file", "params": {"path": "README.md"}})
    actions = [wo.action for wo in plan.work_orders]
    # a crew is fitted from the full company: an investigator, a fitting specialist
    # who carries the authored safe verb, and a reviewer — each work-order names a
    # role AND a department, and every verb is composed.
    assert "read_repo_file" in actions       # the authored safe verb enters the plan
    assert all(wo.role and wo.department and wo.action for wo in plan.work_orders)
    assert plan.directed is False            # planning never touches the machine
    assert len(plan.workforce) >= 8          # the WHOLE company is available to staff from
    assert len(plan.crew) >= 2               # a fitted crew was assembled
    assert all(m.get("role") and m.get("department") for m in plan.crew)


def test_plan_omits_unpermitted_verb_but_still_investigates():
    # a verb the company may not compose → no implementation work-order, but the
    # read-only investigation plan still stands (it never fabricates a mutation).
    plan = _company().plan("disable the safety gates",
                           {"action": "disable_safety", "params": {}})
    actions = [wo.action for wo in plan.work_orders]
    assert "disable_safety" not in actions
    assert "repo_search" in actions and "list_repo" in actions


def test_plan_is_read_only_no_execution(monkeypatch):
    # plan() must never call the hand — assert by giving it a hand that would record
    hand = _FakeHand()
    _company(bridge=hand).plan("do a thing", {})
    assert hand.calls == []


# ── direct: through the ONE guarded hand, dry-run by default ──────────────────

def test_direct_routes_every_work_order_through_the_hand():
    hand = _FakeHand()
    c = _company(bridge=hand)
    plan = c.plan("read README", {"action": "read_repo_file", "params": {"path": "README.md"}})
    c.direct(plan)
    assert plan.directed is True
    # every work-order went through the guarded hand, dry-run (nothing executed)
    assert len(hand.calls) == len(plan.work_orders)
    assert all((wo.outcome or {}).get("dry_run") for wo in plan.work_orders)
    assert all((wo.outcome or {}).get("executed") is False for wo in plan.work_orders)


def test_blocked_step_halts_the_company():
    # the reviewer's list_repo is blocked → the company stops there, never pushes past
    hand = _FakeHand(block=["list_repo"])
    c = _company(bridge=hand)
    plan = c.plan("investigate", {})   # [repo_search, list_repo]
    c.direct(plan)
    outcomes = [wo.outcome for wo in plan.work_orders]
    # the first work-order ran; the blocked one halted the rest
    assert outcomes[0] and outcomes[0].get("dry_run")
    blocked = [wo for wo in plan.work_orders if (wo.outcome or {}).get("blocked")]
    assert blocked, "a blocked step must be recorded"
    # nothing after the blocked step was attempted
    idx = plan.work_orders.index(blocked[0])
    assert all(wo.outcome is None for wo in plan.work_orders[idx + 1:])


def test_direct_persists_the_workflow(tmp_path):
    hand = _FakeHand()
    c = _company(bridge=hand)
    plan = c.plan("read README", {"action": "read_repo_file", "params": {"path": "README.md"}})
    c.direct(plan)
    assert plan.persisted and plan.persisted.get("goal_id")
    assert (tmp_path / "contracts.json").exists()  # recorded on the contract stack


def test_ascent_gate_widens_monotonically_and_never_reaches_a_live_verb():
    from aureon.core.soul_company import _COMPANY_VERBS, _ascent_allowed_verbs

    live = {"place_live_order", "execute_trade", "make_payment", "submit_hmrc", "send_email", "execute_shell"}
    prev: set[str] = set()
    for stage in range(8):
        allowed = _ascent_allowed_verbs(stage)
        assert allowed <= _COMPANY_VERBS            # never beyond the safe set
        assert allowed & live == set()              # never a live/irreversible verb
        assert prev <= allowed                       # monotone — awakening only widens
        prev = allowed
    # read-only at rest; the repo-authoring verbs only unlock higher up
    assert "write_repo_file" not in _ascent_allowed_verbs(0)
    assert "write_repo_file" in _ascent_allowed_verbs(6)


def test_full_workforce_and_fitted_crew():
    c = _company()
    roster = c.workforce()
    # the whole company — every department represented, from executive to a cleaner
    depts = {r.get("department") for r in roster}
    assert len(roster) >= 20 and {"executive", "engineering", "security_ops"} <= depts
    # the crew is FITTED to the brief: a trading brief pulls a trading specialist,
    # a code brief pulls an engineer — the department shifts with the intent.
    trade_crew = c.plan("take a margin position on the exchange for profit").crew
    code_crew = c.plan("fix the failing module and run the tests").crew
    assert any(m["department"] == "trading_data" for m in trade_crew)
    assert any(m["department"] == "engineering" for m in code_crew)
    # a lead owns it and a reviewer guards it, on every crew
    assert trade_crew[0]["department"] == "executive"
    assert trade_crew[-1]["department"] == "security_ops"


def test_missing_hand_never_crashes():
    # a company with no reachable hand degrades to "not directed", never raises
    class _NoHand:
        def perform(self, *a, **k):
            raise RuntimeError("no hand")

    c = _company(bridge=_NoHand())
    plan = c.plan("do a thing", {})
    out = c.direct(plan)
    # the first perform raised → that work-order records an error and the run halts
    assert out.work_orders[0].outcome and out.work_orders[0].outcome.get("error")
