"""
Cognitive Systems SaaS — verified read surfaces for the whole substrate.

Offline + hermetic: the bus surfaces run against a freshly-constructed
``ThoughtBus`` (never the global singleton), the brain surface reads a temp
JSON via env override, and the mycelium surface is asserted NOT to cold-boot the
network. Route tests mount the SaaS routes on a bare Flask app so the operator
process is never started.
"""

from __future__ import annotations

import json

import pytest

from aureon.core.aureon_thought_bus import Thought, ThoughtBus
from aureon.observer.real_data_contract import TRUTH_STATUSES
from aureon.saas.cognitive import (
    brain_surface,
    build_cognitive_payload,
    bus_surface,
    connectome_surface,
    field_surface,
    mycelium_surface,
)


def _bus_with_pulse() -> ThoughtBus:
    b = ThoughtBus()
    b.publish(Thought(
        source="test", topic="symbolic.life.pulse",
        payload={"symbolic_life_score": 0.72, "coherence_gamma": 1.18,
                 "consciousness_level": "aware", "source": "test_pulse"},
    ))
    b.publish(Thought(
        source="queen", topic="symbolic.life.subfield",
        payload={"source": "queen", "symbolic_life_score": 0.64, "coherence_gamma": 1.0},
    ))
    return b


# ── per-surface truth ──────────────────────────────────────────────────────────

def test_field_surface_live_with_pulse():
    s = field_surface(_bus_with_pulse())
    assert s["truth_status"] == "live"
    assert s["canonical"]["available"] is True
    assert s["subfields"]["count"] >= 1
    assert s["blended"]["available"] is True


def test_field_surface_no_data_on_empty_bus(monkeypatch):
    # Empty bus AND no trace file → honest no_data, never a fabricated number.
    monkeypatch.setenv("AUREON_HNC_TRACE_PATH", "/nonexistent/hnc_trace.jsonl")
    s = field_surface(ThoughtBus())
    assert s["truth_status"] == "no_data"
    assert "blocker" in s


def test_bus_surface_live_topology():
    s = bus_surface(_bus_with_pulse())
    assert s["truth_status"] == "live"
    assert s["cognitive_links"]["symbolic.life.pulse"]["recent"] >= 1
    assert s["cognitive_links_flowing"] >= 1


def test_mycelium_surface_never_cold_boots():
    """A status read must not construct the (heavy) mesh singleton."""
    import aureon.core.aureon_mycelium as myc

    myc._mycelium_instance = None  # ensure dormant
    s = mycelium_surface()
    assert s["truth_status"] == "no_data"
    assert "blocker" in s
    # The invariant: the surface read did NOT spawn the network.
    assert myc._mycelium_instance is None


def test_mycelium_surface_live_when_singleton_exists():
    import aureon.core.aureon_mycelium as myc

    class _FakeMesh:
        def get_mesh_status(self):
            return {"coherence": 0.9, "queen_signal": 0.1, "hive_count": 2,
                    "agent_count": 10, "connected_systems": [{"name": "a"}, {"name": "b"}],
                    "external_signals": 0, "broadcasts_pending": 0}

        def get_growth_stats(self):
            return {"net_profit_total": 1.0, "growth_percentage": 0.0, "profit_rate_per_day": 0.0}

    prev = myc._mycelium_instance
    myc._mycelium_instance = _FakeMesh()
    try:
        s = mycelium_surface()
        assert s["truth_status"] == "live"
        assert s["connected_count"] == 2
        assert s["connected_systems"] == ["a", "b"]
        assert s["growth"]["net_profit_total"] == 1.0
    finally:
        myc._mycelium_instance = prev


def test_connectome_surface_reads_body_map():
    s = connectome_surface()
    # Connectome is cheap + always constructable → live body-map.
    assert s["truth_status"] == "live"
    assert "nodes" in s["body_map"]
    assert isinstance(s["nodes_by_status"], dict)


def test_brain_surface_real_derived_from_files(tmp_path, monkeypatch):
    preds = tmp_path / "preds.json"
    preds.write_text(json.dumps({
        "predictions": [
            {"validated": True, "was_correct": True},
            {"validated": True, "was_correct": False},
            {"validated": False},
        ],
        "last_updated": "2026-07-14",
    }), encoding="utf-8")
    know = tmp_path / "know.json"
    know.write_text(json.dumps([{"timestamp": 1}, {"timestamp": 2}]), encoding="utf-8")

    monkeypatch.setenv("AUREON_BRAIN_PREDICTIONS_PATH", str(preds))
    monkeypatch.setenv("AUREON_BRAIN_KNOWLEDGE_PATH", str(know))
    s = brain_surface()
    assert s["truth_status"] == "real_derived"
    assert s["accuracy"]["total_predictions"] == 3
    assert s["accuracy"]["validated"] == 2
    assert s["accuracy"]["accuracy_pct"] == 50.0
    assert s["knowledge"]["entries"] == 2


def test_brain_surface_no_data_when_absent(tmp_path, monkeypatch):
    monkeypatch.setenv("AUREON_BRAIN_PREDICTIONS_PATH", str(tmp_path / "missing1.json"))
    monkeypatch.setenv("AUREON_BRAIN_KNOWLEDGE_PATH", str(tmp_path / "missing2.json"))
    s = brain_surface()
    assert s["truth_status"] == "no_data"
    assert "blocker" in s


# ── the umbrella payload ─────────────────────────────────────────────────────

def test_build_cognitive_payload_shape():
    payload = build_cognitive_payload()
    assert payload["available"] is True
    assert payload["product_domain"] == "cognition"
    assert set(payload["surfaces"]) == {"field", "bus", "mycelium", "connectome", "brain"}
    # Every surface carries a valid truth_status drawn from the contract vocabulary.
    for surface in payload["surfaces"].values():
        assert surface["truth_status"] in TRUTH_STATUSES
    # Provenance header + roll-up present.
    prov = payload["provenance"]
    assert "simulation_fallback_allowed" in prov
    assert isinstance(prov["truth_statuses"], list)
    assert "operational_ready" in payload["truth_summary"]
    assert payload["operational_ready"] + payload["blocked"] <= 5
    # The catalog view lists all five backing accessors.
    assert len(payload["registry"]) == 5


def test_provenance_never_fabricates():
    """simulation_fallback_allowed must reflect the real policy (default off)."""
    payload = build_cognitive_payload()
    assert isinstance(payload["provenance"]["simulation_fallback_allowed"], bool)


# ── routes on a bare Flask app (no operator boot) ───────────────────────────────

def _saas_client():
    flask = pytest.importorskip("flask", reason="SaaS gateway requires the `.[operator]` extra")
    from aureon.saas.gateway import register_saas_routes

    app = flask.Flask(__name__)
    register_saas_routes(app)
    return app.test_client()


@pytest.mark.parametrize("path,part", [
    ("/api/cognition/field", "field"),
    ("/api/cognition/bus", "bus"),
    ("/api/cognition/mycelium", "mycelium"),
    ("/api/cognition/connectome", "connectome"),
    ("/api/cognition/brain", "brain"),
])
def test_cognition_part_routes(path, part):
    r = _saas_client().get(path)
    assert r.status_code == 200
    body = r.get_json()
    assert body["surface"] == part
    assert body["data"]["truth_status"] in TRUTH_STATUSES


def test_cognition_umbrella_route():
    r = _saas_client().get("/api/cognition")
    assert r.status_code == 200
    body = r.get_json()
    assert body["available"] is True
    assert set(body["surfaces"]) == {"field", "bus", "mycelium", "connectome", "brain"}
    assert "provenance" in body and "truth_summary" in body
