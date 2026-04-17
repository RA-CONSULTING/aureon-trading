#!/usr/bin/env python3
"""
Tests for PhiBridgeMesh — P2P vault-card gossip.

All transport is stubbed. We verify:
  - build_payload_for respects per-peer known_hashes
  - apply_response merges cards, dedups by harmonic_hash, updates state
  - handle_inbound is the symmetric server-side of the exchange
  - gossip_to happy-path and error-path
  - gossip_once iterates discovered peers
  - two mesh nodes sharing a vault-stub converge after a few cycles
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.harmonic.phi_bridge_mesh import PhiBridgeMesh  # noqa: E402
from aureon.vault.aureon_vault import VaultContent  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# Test doubles
# ─────────────────────────────────────────────────────────────────────────────


class _StubVault:
    """Vault double exposing only what PhiBridgeMesh touches."""

    def __init__(self):
        from collections import OrderedDict
        self._contents: OrderedDict = OrderedDict()
        self.love_amplitude = 0.5

    def add(self, content: VaultContent) -> None:
        self._contents[content.content_id] = content

    def fingerprint(self) -> str:
        return f"fp-{len(self._contents)}"

    def seed(self, cards: List[VaultContent]) -> None:
        for c in cards:
            self.add(c)


class _StubDiscovery:
    def __init__(self, peer_id: str, peers):
        self.peer_id = peer_id
        self._peers = list(peers)

    def known_peers(self):
        return list(self._peers)


class _StubPeer:
    def __init__(self, peer_id: str, host: str, port: int):
        self.peer_id = peer_id
        self.host = host
        self.port = port

    @property
    def url_base(self):
        return f"http://{self.host}:{self.port}"


class _RoutedClient:
    """In-memory HTTP client that routes to handlers keyed by url_base."""

    def __init__(self):
        self.routes: Dict[str, Any] = {}
        self.calls: List[Dict[str, Any]] = []
        self.fail_urls: set = set()

    def mount(self, url_base: str, mesh: "PhiBridgeMesh") -> None:
        self.routes[url_base] = mesh

    def post_json(self, url: str, body: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append({"url": url, "body": body})
        if url in self.fail_urls:
            raise ConnectionError(f"simulated failure for {url}")
        base = url.rsplit("/api/", 1)[0]
        mesh = self.routes.get(base)
        if mesh is None:
            raise ConnectionError(f"no route for {url}")
        return mesh.handle_inbound(body)


def _card(topic: str, payload: Dict[str, Any]) -> VaultContent:
    return VaultContent.build(category="generic", source_topic=topic, payload=payload)


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_build_payload_for_includes_all_cards_when_peer_unknown():
    vault = _StubVault()
    vault.seed([_card("t.a", {"n": 1}), _card("t.b", {"n": 2})])
    mesh = PhiBridgeMesh(
        vault=vault,
        discovery=_StubDiscovery("self", []),
        client=_RoutedClient(),
    )
    payload = mesh.build_payload_for("remote")
    assert payload["from_peer_id"] == "self"
    assert payload["to_peer_id"] == "remote"
    assert len(payload["cards"]) == 2
    assert sorted(payload["our_hashes"]) == sorted(c.harmonic_hash for c in vault._contents.values())


def test_build_payload_for_skips_known_hashes():
    vault = _StubVault()
    a = _card("t.a", {"n": 1})
    b = _card("t.b", {"n": 2})
    vault.seed([a, b])
    mesh = PhiBridgeMesh(
        vault=vault,
        discovery=_StubDiscovery("self", []),
        client=_RoutedClient(),
    )
    # Simulate a previous exchange where peer reported it already has card `a`.
    mesh.apply_response("remote", {"cards": [], "our_hashes": [a.harmonic_hash]})
    payload = mesh.build_payload_for("remote")
    sent_hashes = {c["harmonic_hash"] for c in payload["cards"]}
    assert a.harmonic_hash not in sent_hashes
    assert b.harmonic_hash in sent_hashes


def test_apply_response_merges_cards():
    vault = _StubVault()
    mesh = PhiBridgeMesh(
        vault=vault,
        discovery=_StubDiscovery("self", []),
        client=_RoutedClient(),
    )
    incoming = _card("t.remote", {"n": 99}).to_dict()
    stats = mesh.apply_response("remote", {"cards": [incoming], "our_hashes": []})
    assert stats["cards_in"] == 1
    assert any(c.harmonic_hash == incoming["harmonic_hash"] for c in vault._contents.values())


def test_apply_response_is_idempotent():
    vault = _StubVault()
    mesh = PhiBridgeMesh(
        vault=vault,
        discovery=_StubDiscovery("self", []),
        client=_RoutedClient(),
    )
    incoming = _card("t.remote", {"n": 1}).to_dict()
    s1 = mesh.apply_response("remote", {"cards": [incoming], "our_hashes": []})
    s2 = mesh.apply_response("remote", {"cards": [incoming], "our_hashes": []})
    assert s1["cards_in"] == 1
    assert s2["cards_in"] == 0
    assert len(vault._contents) == 1


def test_handle_inbound_merges_and_replies_with_missing_cards():
    vault = _StubVault()
    local_a = _card("t.local", {"side": "local"})
    vault.seed([local_a])
    mesh = PhiBridgeMesh(
        vault=vault,
        discovery=_StubDiscovery("self", []),
        client=_RoutedClient(),
    )
    remote_b = _card("t.remote", {"side": "remote"}).to_dict()
    payload = {
        "from_peer_id": "remote", "to_peer_id": "self",
        "our_hashes": [remote_b["harmonic_hash"]],
        "cards": [remote_b],
    }
    resp = mesh.handle_inbound(payload)
    assert resp["ok"] is True
    assert resp["cards_received"] == 1
    # Reply should include our local card (remote doesn't have it)
    reply_hashes = {c["harmonic_hash"] for c in resp["cards"]}
    assert local_a.harmonic_hash in reply_hashes
    assert remote_b["harmonic_hash"] not in reply_hashes


def test_gossip_to_reports_error_when_client_fails():
    vault = _StubVault()
    vault.seed([_card("t.a", {"n": 1})])
    client = _RoutedClient()
    peer = _StubPeer("remote", "10.0.0.5", 8000)
    client.fail_urls.add(peer.url_base + "/api/bridge/cards")
    mesh = PhiBridgeMesh(
        vault=vault,
        discovery=_StubDiscovery("self", [peer]),
        client=client,
    )
    result = mesh.gossip_to(peer)
    assert result["ok"] is False
    assert "simulated failure" in result["error"]


def test_gossip_once_iterates_peers():
    v_a = _StubVault()
    v_a.seed([_card("a", {"n": 1})])
    mesh_a = PhiBridgeMesh(vault=v_a, discovery=_StubDiscovery("a", []), client=_RoutedClient())

    v_b = _StubVault()
    v_b.seed([_card("b", {"n": 2})])
    mesh_b = PhiBridgeMesh(vault=v_b, discovery=_StubDiscovery("b", []), client=_RoutedClient())

    v_c = _StubVault()
    v_c.seed([_card("c", {"n": 3})])
    mesh_c = PhiBridgeMesh(vault=v_c, discovery=_StubDiscovery("c", []), client=_RoutedClient())

    client = _RoutedClient()
    peer_b = _StubPeer("b", "h-b", 80)
    peer_c = _StubPeer("c", "h-c", 80)
    client.mount(peer_b.url_base, mesh_b)
    client.mount(peer_c.url_base, mesh_c)

    mesh_a.client = client
    mesh_a.discovery = _StubDiscovery("a", [peer_b, peer_c])

    out = mesh_a.gossip_once()
    assert out["ok"] is True
    assert out["peers"] == 2
    assert out["results"]["b"]["ok"] is True
    assert out["results"]["c"]["ok"] is True


def test_two_nodes_converge_after_gossip_round_trip():
    """Full end-to-end: A knows card X, B knows card Y. After one round
    of gossip A→B, both should hold X and Y."""
    v_a = _StubVault()
    card_x = _card("topic.x", {"from": "A", "value": 11})
    v_a.seed([card_x])

    v_b = _StubVault()
    card_y = _card("topic.y", {"from": "B", "value": 22})
    v_b.seed([card_y])

    mesh_a = PhiBridgeMesh(vault=v_a, discovery=_StubDiscovery("A", []), client=_RoutedClient())
    mesh_b = PhiBridgeMesh(vault=v_b, discovery=_StubDiscovery("B", []), client=_RoutedClient())

    client = _RoutedClient()
    peer_b = _StubPeer("B", "node-b", 80)
    client.mount(peer_b.url_base, mesh_b)

    mesh_a.client = client
    mesh_a.discovery = _StubDiscovery("A", [peer_b])

    result = mesh_a.gossip_to(peer_b)
    assert result["ok"] is True
    # Both vaults now hold both hashes
    hashes_a = {c.harmonic_hash for c in v_a._contents.values()}
    hashes_b = {c.harmonic_hash for c in v_b._contents.values()}
    assert card_x.harmonic_hash in hashes_a and card_y.harmonic_hash in hashes_a
    assert card_x.harmonic_hash in hashes_b and card_y.harmonic_hash in hashes_b


def test_three_nodes_converge_over_two_cycles():
    """A↔B↔C topology (linear). After two gossip cycles from A through B
    to C, a card born on A should reach C."""
    v_a = _StubVault()
    v_b = _StubVault()
    v_c = _StubVault()
    card_x = _card("topic.x", {"origin": "A"})
    v_a.seed([card_x])

    client = _RoutedClient()
    mesh_a = PhiBridgeMesh(vault=v_a, discovery=_StubDiscovery("A", []), client=client)
    mesh_b = PhiBridgeMesh(vault=v_b, discovery=_StubDiscovery("B", []), client=client)
    mesh_c = PhiBridgeMesh(vault=v_c, discovery=_StubDiscovery("C", []), client=client)

    peer_b = _StubPeer("B", "node-b", 80)
    peer_c = _StubPeer("C", "node-c", 80)
    client.mount(peer_b.url_base, mesh_b)
    client.mount(peer_c.url_base, mesh_c)

    mesh_a.discovery = _StubDiscovery("A", [peer_b])  # A knows B
    mesh_b.discovery = _StubDiscovery("B", [peer_c])  # B knows C

    # Cycle 1: A → B (B learns x)
    mesh_a.gossip_once()
    assert card_x.harmonic_hash in {c.harmonic_hash for c in v_b._contents.values()}
    # Cycle 2: B → C (C learns x)
    mesh_b.gossip_once()
    assert card_x.harmonic_hash in {c.harmonic_hash for c in v_c._contents.values()}


def test_info_returns_structured_report():
    vault = _StubVault()
    vault.seed([_card("t.a", {"n": 1})])
    mesh = PhiBridgeMesh(
        vault=vault,
        discovery=_StubDiscovery("self", []),
        client=_RoutedClient(),
    )
    info = mesh.info()
    assert info["service"] == "phi_bridge_mesh"
    assert info["running"] is False
    assert info["interval_s"] > 0


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
