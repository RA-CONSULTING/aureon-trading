#!/usr/bin/env python3
"""
Flask test-client tests for POST /api/bridge/cards and GET /api/bridge/mesh/info.

Two Flask processes on the same LAN can now exchange VaultContent cards
through this endpoint. These tests verify the endpoint contract end-to-end
using Flask's test client and the real PhiBridgeMesh (no network).
"""

from __future__ import annotations

import json
import os
import sys

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

try:
    import importlib.util
    _FLASK = importlib.util.find_spec("flask") is not None
except Exception:
    _FLASK = False

pytestmark = pytest.mark.skipif(not _FLASK, reason="flask not installed")


def _build_client():
    """Spin up a Flask test client wired to a real AureonVault + PhiBridgeMesh."""
    from aureon.harmonic.phi_bridge_mesh import reset_phi_bridge_mesh
    from aureon.vault import AureonSelfFeedbackLoop
    from aureon.vault.ui import create_app
    reset_phi_bridge_mesh()  # fresh singleton per test

    loop = AureonSelfFeedbackLoop(base_interval_s=0.01, enable_voice=False)
    app = create_app(loop=loop)
    app.testing = True
    return app.test_client(), loop


def _card_dict(topic: str, payload) -> dict:
    """Build a card-shaped dict matching VaultContent.to_dict()."""
    from aureon.vault.aureon_vault import VaultContent
    card = VaultContent.build(
        category="bridge.test",
        source_topic=topic,
        payload=payload if isinstance(payload, dict) else {"value": payload},
    )
    return card.to_dict()


def test_cards_endpoint_accepts_and_returns_payload():
    client, loop = _build_client()
    remote_card = _card_dict("remote.hello", {"from": "peer-b", "n": 1})

    body = {
        "from_peer_id": "peer-b",
        "to_peer_id": "peer-a",
        "our_hashes": [remote_card["harmonic_hash"]],
        "cards": [remote_card],
        "ts": 1234.0,
    }
    resp = client.post("/api/bridge/cards",
                       data=json.dumps(body),
                       content_type="application/json")
    assert resp.status_code == 200, resp.get_data(as_text=True)
    data = resp.get_json()
    assert data["ok"] is True
    assert data["to_peer_id"] == "peer-b"
    assert data["cards_received"] == 1
    # Response should include card list + our_hashes so the sender can
    # update its known_hashes tally for us.
    assert isinstance(data.get("cards"), list)
    assert isinstance(data.get("our_hashes"), list)


def test_cards_endpoint_merges_into_vault():
    client, loop = _build_client()
    card_a = _card_dict("remote.a", {"side": "remote", "idx": 1})
    card_b = _card_dict("remote.b", {"side": "remote", "idx": 2})
    before = len(loop.vault)

    body = {
        "from_peer_id": "peer-remote",
        "our_hashes": [],
        "cards": [card_a, card_b],
    }
    resp = client.post("/api/bridge/cards",
                       data=json.dumps(body),
                       content_type="application/json")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["cards_received"] == 2
    # Vault now holds both hashes that were POSTed.
    hashes = {c.harmonic_hash for c in loop.vault._contents.values()}
    assert card_a["harmonic_hash"] in hashes
    assert card_b["harmonic_hash"] in hashes
    assert len(loop.vault) >= before + 2


def test_cards_endpoint_is_idempotent_by_hash():
    client, loop = _build_client()
    dup = _card_dict("remote.dup", {"n": 7})
    body = {"from_peer_id": "p", "our_hashes": [], "cards": [dup]}

    r1 = client.post("/api/bridge/cards", data=json.dumps(body),
                     content_type="application/json")
    r2 = client.post("/api/bridge/cards", data=json.dumps(body),
                     content_type="application/json")
    assert r1.status_code == 200 and r2.status_code == 200
    # Second call sees the hash already in our vault and doesn't re-add.
    assert r1.get_json()["cards_received"] == 1
    assert r2.get_json()["cards_received"] == 0
    # Exactly one copy of the card in the vault.
    matches = [c for c in loop.vault._contents.values()
               if c.harmonic_hash == dup["harmonic_hash"]]
    assert len(matches) == 1


def test_cards_endpoint_returns_our_cards_missing_from_peer():
    client, loop = _build_client()
    # Seed a local card the remote peer won't know about.
    from aureon.vault.aureon_vault import VaultContent
    local = VaultContent.build(category="local", source_topic="local.unique",
                               payload={"origin": "us"})
    loop.vault.add(local)

    body = {"from_peer_id": "peer-x", "our_hashes": [], "cards": []}
    resp = client.post("/api/bridge/cards", data=json.dumps(body),
                       content_type="application/json")
    data = resp.get_json()
    assert data["ok"] is True
    reply_hashes = {c["harmonic_hash"] for c in data["cards"]}
    assert local.harmonic_hash in reply_hashes


def test_cards_endpoint_rejects_non_object_body():
    client, _ = _build_client()
    resp = client.post("/api/bridge/cards", data=json.dumps([1, 2, 3]),
                       content_type="application/json")
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_mesh_info_endpoint():
    client, _ = _build_client()
    resp = client.get("/api/bridge/mesh/info")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["service"] == "phi_bridge_mesh"
    assert "interval_s" in data
    assert "gossip_cycles" in data


def test_two_flask_apps_converge_through_their_endpoints():
    """Simulate two machines by wiring client_a.post → app_b's handler.

    This is the real shape of the LAN case: each Flask app has a vault,
    the mesh endpoint ingests cards into that vault, and the two vaults
    should converge on the union of their hashes after a round trip."""
    from aureon.harmonic.phi_bridge_mesh import (
        PhiBridgeMesh,
        reset_phi_bridge_mesh,
    )
    from aureon.vault import AureonSelfFeedbackLoop
    from aureon.vault.aureon_vault import VaultContent
    from aureon.vault.ui import create_app

    # App A
    reset_phi_bridge_mesh()
    loop_a = AureonSelfFeedbackLoop(base_interval_s=0.01, enable_voice=False)
    card_a = VaultContent.build(category="g", source_topic="app.a", payload={"who": "a"})
    loop_a.vault.add(card_a)
    app_a = create_app(loop=loop_a); app_a.testing = True
    client_a = app_a.test_client()

    # App B — has a DIFFERENT card
    reset_phi_bridge_mesh()
    loop_b = AureonSelfFeedbackLoop(base_interval_s=0.01, enable_voice=False)
    card_b = VaultContent.build(category="g", source_topic="app.b", payload={"who": "b"})
    loop_b.vault.add(card_b)
    app_b = create_app(loop=loop_b); app_b.testing = True
    client_b = app_b.test_client()

    # A builds a payload from its own mesh (without the singleton because
    # we just reset it) and POSTs to B.
    mesh_a = PhiBridgeMesh(vault=loop_a.vault)
    payload = mesh_a.build_payload_for("peer-b")
    resp = client_b.post("/api/bridge/cards", data=json.dumps(payload),
                         content_type="application/json")
    assert resp.status_code == 200
    reply = resp.get_json()
    # B received A's card, B replies with its own unseen cards.
    mesh_a.apply_response("peer-b", reply)

    # Both vaults should now hold both hashes.
    hashes_a = {c.harmonic_hash for c in loop_a.vault._contents.values()}
    hashes_b = {c.harmonic_hash for c in loop_b.vault._contents.values()}
    assert card_a.harmonic_hash in hashes_a
    assert card_b.harmonic_hash in hashes_a
    assert card_a.harmonic_hash in hashes_b
    assert card_b.harmonic_hash in hashes_b


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
