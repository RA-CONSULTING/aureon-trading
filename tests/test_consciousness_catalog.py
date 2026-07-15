"""
Consciousness catalog — the organism's inner capabilities, categorized.

Offline + hermetic: the catalog is registry-as-data, so it builds without a running
operator. Proves every consciousness organ is present and grouped by category; each
surface carries a route, a known safety posture, and an honest truth_status; a dormant
organ degrades to no_data (never a fabricated capability); and the route mounts on a bare
Flask app and never 500s.
"""

from __future__ import annotations

import pytest

from aureon.observer.real_data_contract import TRUTH_STATUSES
from aureon.saas.consciousness_catalog import (
    CATEGORIES,
    SAFETY_POSTURES,
    build_consciousness_catalog,
)

_EXPECTED_KEYS = {"metacognition", "affect", "soul", "inner_work", "pursuit",
                  "approval_desk", "company", "connectome"}


# ── the catalog categorizes every organ ──────────────────────────────────────

def test_catalog_enumerates_every_organ():
    cat = build_consciousness_catalog()
    keys = {s["key"] for s in cat["surfaces"]}
    assert keys == _EXPECTED_KEYS
    assert cat["counts"]["total"] == len(_EXPECTED_KEYS)
    assert cat["counts"]["category_count"] == len(CATEGORIES)


def test_every_surface_is_well_formed():
    cat = build_consciousness_catalog()
    for s in cat["surfaces"]:
        assert s["route"].startswith("/api/")
        assert s["category"] in CATEGORIES
        assert s["safety_posture"] in SAFETY_POSTURES
        assert s["posture_note"]                       # each posture is explained
        assert s["truth_status"] in TRUTH_STATUSES     # honest, from the real vocabulary
        assert isinstance(s["available"], bool)


def test_surfaces_are_grouped_by_category():
    cat = build_consciousness_catalog()
    for name, block in cat["categories"].items():
        assert name in CATEGORIES
        assert block["purpose"]
        assert block["surface_count"] == len(block["surfaces"])
        for s in block["surfaces"]:
            assert s["category"] == name
    # every surface lands in exactly one category
    grouped = sum(b["surface_count"] for b in cat["categories"].values())
    assert grouped == cat["counts"]["total"]


def test_safety_postures_are_the_three_honest_ones():
    cat = build_consciousness_catalog()
    postures = {s["safety_posture"] for s in cat["surfaces"]}
    assert postures <= {"read_only_assess", "records_only_gated", "reversible_ascent_gated"}
    # the desk records-only; the workforce is ascent-gated; the rest are read-only
    by_key = {s["key"]: s["safety_posture"] for s in cat["surfaces"]}
    assert by_key["approval_desk"] == "records_only_gated"
    assert by_key["company"] == "reversible_ascent_gated"
    assert by_key["soul"] == "read_only_assess"


def test_provenance_and_rollup():
    cat = build_consciousness_catalog()
    assert "provenance" in cat and cat["truth_status"] in TRUTH_STATUSES
    assert cat["counts"]["operational"] <= cat["counts"]["total"]
    assert sum(cat["counts"]["by_safety_posture"].values()) == cat["counts"]["total"]


def test_dormant_organ_is_no_data_never_fabricated(monkeypatch):
    # a broken accessor must degrade to no_data, never invent a capability status
    import aureon.saas.consciousness_catalog as cc

    monkeypatch.setattr(cc, "_probe", lambda entry: {"available": False, "truth_status": "no_data"})
    cat = cc.build_consciousness_catalog()
    assert cat["counts"]["operational"] == 0
    assert cat["truth_status"] == "no_data"
    assert all(s["truth_status"] == "no_data" for s in cat["surfaces"])
    # ...but the categorization (the static map) still stands
    assert {s["key"] for s in cat["surfaces"]} == _EXPECTED_KEYS


# ── the route mounts on a bare Flask app and never 500s ───────────────────────

def _saas_client():
    flask = pytest.importorskip("flask", reason="SaaS gateway requires the `.[operator]` extra")
    from aureon.saas.gateway import register_saas_routes

    app = flask.Flask(__name__)
    register_saas_routes(app)
    return app.test_client()


def test_consciousness_route():
    r = _saas_client().get("/api/consciousness")
    assert r.status_code == 200
    body = r.get_json()
    assert body["counts"]["total"] == len(_EXPECTED_KEYS)
    assert "provenance" in body and body["truth_status"] in TRUTH_STATUSES
    assert set(body["categories"]) == set(CATEGORIES)
