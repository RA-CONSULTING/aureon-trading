#!/usr/bin/env python3
"""
Tests for PhiBridgeDiscovery — LAN peer discovery state machine.

Uses a stub UDP transport so no sockets are ever bound.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from typing import Any, List, Optional, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.harmonic.phi_bridge_discovery import (  # noqa: E402
    ANNOUNCE_MAGIC,
    PROTO_VER,
    PhiBridgeDiscovery,
    RemotePeer,
)


class _StubTransport:
    """Minimal transport: send() stashes; recv() drains a prepared inbox."""

    def __init__(self):
        self.sent: List[bytes] = []
        self.inbox: List[Tuple[bytes, Tuple[str, int]]] = []
        self._lock = threading.Lock()

    def open(self) -> None:
        pass

    def close(self) -> None:
        pass

    def send(self, data: bytes) -> None:
        with self._lock:
            self.sent.append(bytes(data))

    def recv(self) -> Optional[Tuple[bytes, Tuple[str, int]]]:
        with self._lock:
            if not self.inbox:
                return None
            return self.inbox.pop(0)

    def feed(self, packet: Any, source_addr: Tuple[str, int] = ("192.168.1.99", 26181)):
        data = packet if isinstance(packet, (bytes, bytearray)) else json.dumps(packet).encode("utf-8")
        with self._lock:
            self.inbox.append((data, source_addr))


def _build(**kwargs) -> Tuple[PhiBridgeDiscovery, _StubTransport]:
    t = _StubTransport()
    d = PhiBridgeDiscovery(
        peer_id=kwargs.pop("peer_id", "self-aaaa"),
        host=kwargs.pop("host", "10.0.0.1"),
        port=kwargs.pop("port", 8765),
        label=kwargs.pop("label", "self-box"),
        kind=kwargs.pop("kind", "desktop"),
        transport=t,
        **kwargs,
    )
    return d, t


def test_announcement_shape_is_valid():
    d, _ = _build(fingerprint_fn=lambda: "fp-123")
    ann = d.build_announcement()
    assert ann["aureon"] == ANNOUNCE_MAGIC
    assert ann["ver"] == PROTO_VER
    assert ann["peer_id"] == "self-aaaa"
    assert ann["host"] == "10.0.0.1"
    assert ann["port"] == 8765
    assert ann["label"] == "self-box"
    assert ann["kind"] == "desktop"
    assert ann["fingerprint"] == "fp-123"
    assert isinstance(ann["ts"], float)


def test_announce_once_sends_packet():
    d, t = _build()
    assert d.announce_once() is True
    assert len(t.sent) == 1
    decoded = json.loads(t.sent[0].decode("utf-8"))
    assert decoded["aureon"] == ANNOUNCE_MAGIC
    assert decoded["peer_id"] == "self-aaaa"


def test_record_announcement_accepts_valid_peer():
    d, _ = _build()
    peer = d.record_announcement({
        "aureon": ANNOUNCE_MAGIC,
        "ver": PROTO_VER,
        "peer_id": "other-bbbb",
        "host": "10.0.0.2",
        "port": 9000,
        "label": "phone",
        "kind": "phone",
        "fingerprint": "fp-remote",
        "ts": time.time(),
    })
    assert peer is not None
    assert isinstance(peer, RemotePeer)
    assert peer.peer_id == "other-bbbb"
    assert peer.host == "10.0.0.2"
    assert peer.port == 9000
    known = d.known_peers()
    assert len(known) == 1
    assert known[0].peer_id == "other-bbbb"


def test_record_announcement_ignores_self_echoes():
    d, _ = _build(peer_id="self-aaaa")
    result = d.record_announcement({
        "aureon": ANNOUNCE_MAGIC,
        "ver": PROTO_VER,
        "peer_id": "self-aaaa",  # our own
        "host": "10.0.0.1", "port": 8765, "label": "us", "kind": "desktop",
    })
    assert result is None
    assert d.known_peers() == []


def test_record_announcement_rejects_bad_magic_or_version():
    d, _ = _build()
    assert d.record_announcement({"aureon": "wrong", "ver": PROTO_VER, "peer_id": "x"}) is None
    assert d.record_announcement({"aureon": ANNOUNCE_MAGIC, "ver": 99, "peer_id": "y"}) is None
    assert d.record_announcement({"peer_id": "z"}) is None
    assert d.known_peers() == []


def test_record_announcement_fills_host_from_source_addr():
    d, _ = _build()
    peer = d.record_announcement(
        {"aureon": ANNOUNCE_MAGIC, "ver": PROTO_VER, "peer_id": "p1", "port": 7000},
        source_addr=("172.16.0.5", 26181),
    )
    assert peer is not None
    assert peer.host == "172.16.0.5"


def test_repeated_announcements_refresh_last_seen():
    d, _ = _build(peer_timeout_s=0.0)
    pkt = {"aureon": ANNOUNCE_MAGIC, "ver": PROTO_VER, "peer_id": "p2", "host": "h", "port": 1}
    first = d.record_announcement(pkt)
    assert first is not None
    t1 = first.last_seen
    time.sleep(0.01)
    second = d.record_announcement(pkt)
    assert second is not None
    assert second.last_seen >= t1
    # Same object, same peer_id
    assert len(d.known_peers()) == 1


def test_peer_timeout_removes_stale_entries():
    d, _ = _build(peer_timeout_s=0.02)
    d.record_announcement(
        {"aureon": ANNOUNCE_MAGIC, "ver": PROTO_VER, "peer_id": "stale", "host": "h", "port": 1}
    )
    assert len(d.known_peers()) == 1
    time.sleep(0.05)
    d._sweep_stale()
    assert d.known_peers() == []


def test_start_stop_threads_live_and_die(monkeypatch=None):
    d, t = _build(interval_s=0.05, peer_timeout_s=5.0)
    d.start()
    try:
        # Announce loop should tick at least once
        time.sleep(0.2)
        assert d.announce_count >= 1
        # Feed a remote announcement and confirm it's ingested
        t.feed({
            "aureon": ANNOUNCE_MAGIC, "ver": PROTO_VER,
            "peer_id": "remote-xyz", "host": "10.0.0.9", "port": 8000,
            "label": "tablet", "kind": "tablet",
        })
        # Wait for listen loop to pick it up
        deadline = time.time() + 1.0
        while time.time() < deadline and not d.known_peers():
            time.sleep(0.02)
        assert len(d.known_peers()) == 1
        assert d.known_peers()[0].peer_id == "remote-xyz"
    finally:
        d.stop()


def test_on_peer_seen_callback_fires():
    calls: List[RemotePeer] = []
    t = _StubTransport()
    d = PhiBridgeDiscovery(
        peer_id="self", host="h", port=1, transport=t,
        on_peer_seen=lambda p: calls.append(p),
    )
    d.record_announcement(
        {"aureon": ANNOUNCE_MAGIC, "ver": PROTO_VER, "peer_id": "new", "host": "h2", "port": 2}
    )
    assert len(calls) == 1
    assert calls[0].peer_id == "new"
    # Second announcement from same peer should NOT fire callback again
    d.record_announcement(
        {"aureon": ANNOUNCE_MAGIC, "ver": PROTO_VER, "peer_id": "new", "host": "h2", "port": 2}
    )
    assert len(calls) == 1


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
