#!/usr/bin/env python3
"""
Tests for the mesh auto-start path in create_app().

Uses a stub UDP transport so no real sockets are ever bound in the test
suite. Verifies that:
  - mesh_autostart defaults to OFF (no surprise threads in existing tests)
  - passing mesh_autostart=True + an injected discovery starts the
    discovery + gossip threads and exposes them via /api/bridge/discovery/peers
  - the endpoint returns the expected JSON contract in both the off and
    on cases
  - an announcement that arrives on the stub transport is picked up and
    surfaced via the HTTP endpoint
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from typing import Any, List, Optional, Tuple

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


class _StubTransport:
    """In-memory UDP stand-in for PhiBridgeDiscovery."""

    def __init__(self):
        self.sent: List[bytes] = []
        self.inbox: List[Tuple[bytes, Tuple[str, int]]] = []
        self._lock = threading.Lock()

    def open(self): pass
    def close(self): pass

    def send(self, data: bytes) -> None:
        with self._lock:
            self.sent.append(bytes(data))

    def recv(self) -> Optional[Tuple[bytes, Tuple[str, int]]]:
        with self._lock:
            if not self.inbox:
                time.sleep(0.01)  # mimic the socket timeout
                return None
            return self.inbox.pop(0)

    def feed(self, packet: Any, source_addr: Tuple[str, int] = ("10.0.0.9", 26181)):
        data = packet if isinstance(packet, (bytes, bytearray)) else json.dumps(packet).encode("utf-8")
        with self._lock:
            self.inbox.append((data, source_addr))


def _build_app(*, autostart: bool, inject_discovery: bool):
    """Build a Flask app with the mesh either off or on+stubbed."""
    from aureon.harmonic.phi_bridge_discovery import PhiBridgeDiscovery
    from aureon.harmonic.phi_bridge_mesh import reset_phi_bridge_mesh
    from aureon.vault import AureonSelfFeedbackLoop
    from aureon.vault.ui import create_app

    reset_phi_bridge_mesh()
    loop = AureonSelfFeedbackLoop(base_interval_s=0.01, enable_voice=False)

    discovery = None
    transport = None
    if inject_discovery:
        transport = _StubTransport()
        discovery = PhiBridgeDiscovery(
            peer_id="self-app",
            host="10.0.0.1",
            port=8000,
            label="self",
            kind="desktop",
            transport=transport,
            interval_s=0.05,
            peer_timeout_s=30.0,
        )

    app = create_app(
        loop=loop,
        mesh_autostart=autostart,
        mesh_discovery=discovery,
        mesh_port=8000,
    )
    app.testing = True
    return app.test_client(), loop, discovery, transport


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_autostart_off_by_default():
    from aureon.harmonic.phi_bridge_mesh import reset_phi_bridge_mesh
    from aureon.vault import AureonSelfFeedbackLoop
    from aureon.vault.ui import create_app

    os.environ.pop("AUREON_MESH_AUTOSTART", None)
    reset_phi_bridge_mesh()
    loop = AureonSelfFeedbackLoop(base_interval_s=0.01, enable_voice=False)
    app = create_app(loop=loop)

    # No discovery should be attached.
    assert app.config.get("AUREON_PHI_BRIDGE_DISCOVERY") is None
    # Mesh singleton exists but should not be running.
    mesh = app.config["AUREON_PHI_BRIDGE_MESH"]
    assert mesh is not None
    assert mesh._running is False


def test_discovery_peers_endpoint_when_off():
    client, _, _, _ = _build_app(autostart=False, inject_discovery=False)
    resp = client.get("/api/bridge/discovery/peers")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["running"] is False
    assert data["peers"] == []


def test_autostart_starts_threads_and_exposes_self():
    client, loop, discovery, transport = _build_app(autostart=True, inject_discovery=True)
    try:
        # Give the announce thread at least one tick.
        time.sleep(0.15)
        assert discovery is not None
        # It should have announced itself on the transport.
        assert discovery.announce_count >= 1
        # Mesh gossip loop should be running (even if there are no peers yet).
        from aureon.harmonic.phi_bridge_mesh import get_phi_bridge_mesh
        mesh = get_phi_bridge_mesh()
        assert mesh._running is True
    finally:
        discovery.stop()
        # Stop the mesh so we don't leak threads between tests.
        from aureon.harmonic.phi_bridge_mesh import get_phi_bridge_mesh
        get_phi_bridge_mesh().stop()


def test_discovery_peers_endpoint_after_announcement():
    client, loop, discovery, transport = _build_app(autostart=True, inject_discovery=True)
    try:
        # Feed a remote peer announcement into the stubbed transport.
        from aureon.harmonic.phi_bridge_discovery import ANNOUNCE_MAGIC, PROTO_VER
        transport.feed({
            "aureon": ANNOUNCE_MAGIC,
            "ver": PROTO_VER,
            "peer_id": "remote-desktop",
            "host": "10.0.0.42",
            "port": 8000,
            "label": "tina-macbook",
            "kind": "desktop",
            "fingerprint": "abc123",
            "ts": time.time(),
        })
        # Give the listen loop a chance to pick it up.
        deadline = time.time() + 1.0
        while time.time() < deadline and not discovery.known_peers():
            time.sleep(0.02)

        resp = client.get("/api/bridge/discovery/peers")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True
        assert data["running"] is True
        assert data["self_peer_id"] == "self-app"
        assert data["port"] == 8000
        peer_ids = [p["peer_id"] for p in data["peers"]]
        assert "remote-desktop" in peer_ids
        remote = next(p for p in data["peers"] if p["peer_id"] == "remote-desktop")
        assert remote["host"] == "10.0.0.42"
        assert remote["url_base"] == "http://10.0.0.42:8000"
    finally:
        discovery.stop()
        from aureon.harmonic.phi_bridge_mesh import get_phi_bridge_mesh
        get_phi_bridge_mesh().stop()


def test_env_var_turns_autostart_on():
    """AUREON_MESH_AUTOSTART=1 should be equivalent to mesh_autostart=True."""
    from aureon.harmonic.phi_bridge_discovery import PhiBridgeDiscovery
    from aureon.harmonic.phi_bridge_mesh import (
        get_phi_bridge_mesh,
        reset_phi_bridge_mesh,
    )
    from aureon.vault import AureonSelfFeedbackLoop
    from aureon.vault.ui import create_app

    os.environ["AUREON_MESH_AUTOSTART"] = "1"
    reset_phi_bridge_mesh()
    loop = AureonSelfFeedbackLoop(base_interval_s=0.01, enable_voice=False)

    transport = _StubTransport()
    discovery = PhiBridgeDiscovery(
        peer_id="env-app", host="10.0.0.5", port=9000,
        transport=transport, interval_s=0.05, peer_timeout_s=30.0,
    )

    app = create_app(loop=loop, mesh_discovery=discovery, mesh_port=9000)
    try:
        app.testing = True
        client = app.test_client()
        time.sleep(0.1)
        resp = client.get("/api/bridge/discovery/peers")
        data = resp.get_json()
        assert data["running"] is True
        assert data["self_peer_id"] == "env-app"
        assert data["port"] == 9000
        assert get_phi_bridge_mesh()._running is True
    finally:
        discovery.stop()
        get_phi_bridge_mesh().stop()
        os.environ.pop("AUREON_MESH_AUTOSTART", None)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
