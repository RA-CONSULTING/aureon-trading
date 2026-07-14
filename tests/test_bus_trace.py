"""
Cross-process bus trace — the dedicated per-signal file bridge.

Offline + hermetic: every test points AUREON_BUS_TRACE_DIR at a tmp dir, so no
real state/ file is touched. Covers the helper directly + the three signals it
bridges (local-action → Λ, sub-fields, consensus), each proven to cross a
process boundary by writing via one bus and reading via a SECOND, empty bus.
"""

from __future__ import annotations

import pytest

from aureon.core import bus_trace as bt
from aureon.core.aureon_thought_bus import ThoughtBus


@pytest.fixture(autouse=True)
def _tmp_trace_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("AUREON_BUS_TRACE_DIR", str(tmp_path))
    return tmp_path


# ── the helper ──────────────────────────────────────────────────────────────

def test_append_read_roundtrip():
    bt.append_trace("sig", {"i": 1, "v": 0.1})
    bt.append_trace("sig", {"i": 2, "v": 0.2})
    rows = bt.read_trace("sig")
    assert [r["i"] for r in rows] == [1, 2]
    assert bt.read_trace_latest("sig")["i"] == 2


def test_missing_trace_is_no_data():
    assert bt.read_trace("absent") == []
    assert bt.read_trace_latest("absent") is None


def test_read_limit_returns_tail():
    for i in range(50):
        bt.append_trace("sig", {"i": i})
    rows = bt.read_trace("sig", limit=5)
    assert [r["i"] for r in rows] == [45, 46, 47, 48, 49]


def test_cap_compaction_bounds_the_file(_tmp_trace_dir):
    for i in range(2500):
        bt.append_trace("sig", {"i": i}, cap=500)
    # Never grows without bound: compacted to <= 2*cap lines.
    line_count = sum(1 for _ in bt.trace_path("sig").open())
    assert line_count <= 1000
    # And the most recent rows survive.
    assert bt.read_trace_latest("sig")["i"] == 2499


def test_corrupt_line_is_skipped(_tmp_trace_dir):
    bt.append_trace("sig", {"i": 1})
    with bt.trace_path("sig").open("a", encoding="utf-8") as fh:
        fh.write("{ this is not json\n")
    bt.append_trace("sig", {"i": 2})
    rows = bt.read_trace("sig")
    assert [r["i"] for r in rows] == [1, 2]  # the garbage line is skipped, not fatal


# ── the three bridged signals cross a process boundary ────────────────────────

def test_subfields_cross_process():
    from aureon.core import hnc_field as hf

    class _S:
        symbolic_life_score = 0.66
        coherence_gamma = 1.1
        consciousness_level = "aware"

    bus_a = ThoughtBus(persist_path=None)
    hf.publish_subfield("queen_cortex", _S(), bus=bus_a)  # writes the trace too
    bus_b = ThoughtBus(persist_path=None)  # a DIFFERENT process's empty bus
    subs = hf.read_subfields(bus_b)
    assert "queen_cortex" in subs
    assert subs["queen_cortex"]["symbolic_life_score"] == 0.66


def test_subfields_same_process_wins_on_collision():
    """Recall-first invariance: a same-process (fresher) value overrides the trace."""
    from aureon.core import hnc_field as hf

    class _Old:
        symbolic_life_score = 0.20
        coherence_gamma = 0.5
        consciousness_level = "dim"

    class _New:
        symbolic_life_score = 0.90
        coherence_gamma = 1.4
        consciousness_level = "bright"

    bus_a = ThoughtBus(persist_path=None)
    hf.publish_subfield("queen_cortex", _Old(), bus=bus_a)  # trace gets the old value
    bus_b = ThoughtBus(persist_path=None)
    hf.publish_subfield("queen_cortex", _New(), bus=bus_b)  # in-process fresh value
    subs = hf.read_subfields(bus_b)
    assert subs["queen_cortex"]["symbolic_life_score"] == 0.90  # in-process wins


def test_local_action_verdicts_cross_process():
    bt.append_trace("local_action_verdict", {"approved": True, "verdict": "APPROVED"})
    bt.append_trace("local_action_verdict", {"approved": False, "verdict": "VETOED"})
    rows = bt.read_trace("local_action_verdict", limit=200)
    approved = sum(1 for v in rows if v.get("approved"))
    vetoed = sum(1 for v in rows if v.get("verdict") in ("VETOED", "BLOCKED"))
    assert len(rows) == 2 and approved == 1 and vetoed == 1


def test_grounded_gate_writes_verdict_trace():
    """The gate mirrors every verdict to the trace so the HNC daemon (another
    process) senses local moves in Λ(t)."""
    from aureon.operator.grounded_action import GroundedActionGate

    gate = GroundedActionGate(bus=ThoughtBus(persist_path=None), enable_llm=False)
    gate.ground("read_repo_file", {"path": "README.md"})
    rows = bt.read_trace("local_action_verdict")
    assert rows, "expected the gate to write a verdict trace row"
    assert "verdict" in rows[-1]


def test_consensus_crosses_process():
    import aureon.core.organism_daemon as od
    from aureon.saas.cognitive import _consensus_event

    class _C:
        def status(self):
            return {"coverage_pct": 5.0, "woven": 30, "failed": 2, "baton_linked": 101}

    bus_a = ThoughtBus(persist_path=None)
    od.breathe_field({"bus": bus_a, "connectome": _C()})  # writes organism_consensus trace
    bus_b = ThoughtBus(persist_path=None)
    ev = _consensus_event(bus_b)  # empty bus → must read the trace
    assert ev is not None
    assert ev["source"] == "consensus_trace_file"
    assert ev["age_s"] is not None
    assert "blended" in ev["payload"]
