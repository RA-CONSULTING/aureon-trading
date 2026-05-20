#!/usr/bin/env python3
"""
Tests for the mesh wiring in create_app().

The mesh always starts at app boot now — no kill-switches. Tests inject
a stub UDP transport via a pre-built PhiBridgeDiscovery so we don't
touch real sockets.
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
                time.sleep(0.01)
                return None
            return self.inbox.pop(0)

    def feed(self, packet: Any, source_addr: Tuple[str, int] = ("10.0.0.9", 26181)):
        data = packet if isinstance(packet, (bytes, bytearray)) else json.dumps(packet).encode("utf-8")
        with self._lock:
            self.inbox.append((data, source_addr))


def _build_app(*, inject_discovery: bool = True):
    """Build a Flask app with an injected stub-transport discovery so
    UDP sockets never bind during tests. When no discovery is injected
    the real one is built (may bind real sockets — use sparingly)."""
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
        mesh_discovery=discovery,
        mesh_port=8000,
    )
    app.testing = True
    return app.test_client(), loop, discovery, transport


def _cleanup(discovery):
    if discovery is not None:
        discovery.stop()
    from aureon.harmonic.phi_bridge_mesh import get_phi_bridge_mesh
    get_phi_bridge_mesh().stop()


def test_mesh_starts_at_app_boot_when_discovery_injected():
    client, loop, discovery, transport = _build_app(inject_discovery=True)
    try:
        # Give the announce thread at least one tick.
        time.sleep(0.15)
        assert discovery is not None
        assert discovery.announce_count >= 1
        from aureon.harmonic.phi_bridge_mesh import get_phi_bridge_mesh
        assert get_phi_bridge_mesh()._running is True
    finally:
        _cleanup(discovery)


def test_discovery_peers_endpoint_exposes_self():
    client, loop, discovery, transport = _build_app(inject_discovery=True)
    try:
        time.sleep(0.1)
        resp = client.get("/api/bridge/discovery/peers")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True
        assert data["running"] is True
        assert data["self_peer_id"] == "self-app"
        assert data["port"] == 8000
    finally:
        _cleanup(discovery)


def test_remote_announcement_surfaces_via_endpoint():
    client, loop, discovery, transport = _build_app(inject_discovery=True)
    try:
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
        deadline = time.time() + 1.0
        while time.time() < deadline and not discovery.known_peers():
            time.sleep(0.02)

        resp = client.get("/api/bridge/discovery/peers")
        data = resp.get_json()
        peer_ids = [p["peer_id"] for p in data["peers"]]
        assert "remote-desktop" in peer_ids
        remote = next(p for p in data["peers"] if p["peer_id"] == "remote-desktop")
        assert remote["host"] == "10.0.0.42"
        assert remote["url_base"] == "http://10.0.0.42:8000"
    finally:
        _cleanup(discovery)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
