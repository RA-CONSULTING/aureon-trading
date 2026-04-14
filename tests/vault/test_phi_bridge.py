#!/usr/bin/env python3
"""
Tests for aureon.harmonic.phi_bridge.PhiBridge.

Covers:
  - peer registration / re-registration / drop / timeout sweep
  - φ²-cadenced interval shrinks with peer count and respects bounds
  - exchange() round-trips peer state and returns the desktop view
  - vault.ingest() is called for join / state / drop / timeout
  - history is bounded and ordered
  - get_phi_bridge() / reset_phi_bridge() singleton lifecycle
"""

import os
import sys
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.harmonic.phi_bridge import (  # noqa: E402
    DEFAULT_BASE_INTERVAL_S,
    MAX_INTERVAL_S,
    MIN_INTERVAL_S,
    PHI,
    PHI_SQUARED,
    PhiBridge,
    get_phi_bridge,
    reset_phi_bridge,
)


PASS = 0
FAIL = 0


def check(condition: bool, msg: str) -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [OK] {msg}")
    else:
        FAIL += 1
        print(f"  [!!] {msg}")


class FakeVault:
    """Minimal vault stand-in for ingest + fingerprint + len."""

    def __init__(self):
        self.love_amplitude = 0.71
        self.gratitude_score = 0.65
        self.dominant_chakra = "love"
        self.cards = []

    def ingest(self, topic, payload, category=None):
        self.cards.append({"topic": topic, "payload": payload, "category": category})

    def fingerprint(self) -> str:
        return f"fake-fp-{len(self.cards)}"

    def __len__(self) -> int:
        return len(self.cards)


def test_register_and_drop():
    print("\n[1] Register, refresh, drop")
    vault = FakeVault()
    bridge = PhiBridge(vault=vault)

    p1 = bridge.register_peer(label="ayman-pixel", kind="phone", remote_addr="192.168.1.42")
    check(bool(p1.peer_id), "peer 1 got an id")
    check(bridge.peer_count() == 1, f"peer_count == 1 (got {bridge.peer_count()})")

    # Re-register same id refreshes last_seen, doesn't duplicate.
    same = bridge.register_peer(label="ayman-pixel", peer_id=p1.peer_id)
    check(same.peer_id == p1.peer_id, "re-register returns the same id")
    check(bridge.peer_count() == 1, "re-register does not duplicate")

    p2 = bridge.register_peer(label="laptop", kind="desktop", remote_addr="192.168.1.55")
    check(bridge.peer_count() == 2, "second peer registers")

    dropped = bridge.drop_peer(p1.peer_id)
    check(dropped, "drop_peer returns True for known id")
    check(bridge.peer_count() == 1, "peer_count drops to 1")
    check(not bridge.drop_peer("nope"), "drop_peer returns False for unknown id")

    join_topics = [c["topic"] for c in vault.cards if c["topic"] == "bridge.peer.joined"]
    drop_topics = [c["topic"] for c in vault.cards if c["topic"] == "bridge.peer.dropped"]
    check(len(join_topics) == 2, f"two join cards fed back to vault (got {len(join_topics)})")
    check(len(drop_topics) == 1, f"one drop card fed back to vault (got {len(drop_topics)})")
    check(
        all(c["category"] == "bridge_peer" for c in vault.cards),
        "all bridge cards categorised as bridge_peer",
    )


def test_cadence_scales_with_peers():
    print("\n[2] Cadence scales with peer count and respects bounds")
    bridge = PhiBridge(vault=FakeVault())

    cad0 = bridge.cadence()
    check(abs(cad0["phi_squared"] - PHI_SQUARED) < 1e-9, "phi_squared constant exposed")

    bridge.register_peer(label="a")
    cad1 = bridge.cadence()
    check(
        abs(cad1["interval_s"] - DEFAULT_BASE_INTERVAL_S) < 1e-6,
        f"one peer -> interval == DEFAULT_BASE_INTERVAL_S (got {cad1['interval_s']:.4f})",
    )

    bridge.register_peer(label="b")
    cad2 = bridge.cadence()
    expected_2 = DEFAULT_BASE_INTERVAL_S / PHI
    check(
        abs(cad2["interval_s"] - expected_2) < 1e-6,
        f"two peers -> interval == base/phi (got {cad2['interval_s']:.4f})",
    )

    # Saturate to confirm the floor.
    for i in range(20):
        bridge.register_peer(label=f"flood{i}")
    cad_n = bridge.cadence()
    check(
        cad_n["interval_s"] >= MIN_INTERVAL_S - 1e-9,
        f"interval respects MIN_INTERVAL_S floor (got {cad_n['interval_s']:.4f})",
    )
    check(
        cad_n["interval_s"] <= MAX_INTERVAL_S + 1e-9,
        f"interval respects MAX_INTERVAL_S ceiling (got {cad_n['interval_s']:.4f})",
    )
    check(cad_n["frequency_hz"] > cad1["frequency_hz"], "more peers -> higher heartbeat hz")


def test_exchange_round_trip():
    print("\n[3] exchange() round-trips state and surfaces desktop view")
    vault = FakeVault()
    bridge = PhiBridge(vault=vault)
    peer = bridge.register_peer(label="phone", kind="phone")

    state_in = {
        "battery": 0.86,
        "orientation": "portrait",
        "screen_on": True,
        "felt_mood": "calm",
    }
    result = bridge.exchange(
        peer.peer_id, peer_state=state_in, peer_fingerprint="phone-fp-1"
    )

    check(result["ok"] is True, "exchange returns ok=True")
    check(result["peer_id"] == peer.peer_id, "response carries peer_id")
    check("desktop" in result and "fingerprint" in result["desktop"], "response has desktop view with fingerprint")
    check(result["desktop"]["love_amplitude"] == 0.71, "desktop view forwards love_amplitude from vault")
    check(result["desktop"]["card_count"] >= 1, "desktop view forwards card_count")
    check(result["echo"]["fingerprint"] == "phone-fp-1", "echo carries the peer fingerprint")
    check(set(result["echo"]["received_keys"]) == set(state_in.keys()), "echo carries the received state keys")
    check(result["cadence"]["interval_s"] > 0, "cadence interval included in response")

    state_card = next(
        (c for c in vault.cards if c["topic"] == "bridge.peer.state"), None
    )
    check(state_card is not None, "peer state fed back into vault as bridge.peer.state card")
    if state_card:
        check(state_card["payload"]["state"]["battery"] == 0.86, "vault card preserved peer state")
        check(state_card["payload"]["fingerprint"] == "phone-fp-1", "vault card preserved peer fingerprint")

    # Auto-register on unknown peer id.
    auto = bridge.exchange("ghost-id", peer_state={"label": "rogue", "kind": "tablet"})
    check(auto["ok"] is True, "exchange auto-registers an unknown peer id")
    check(any(p["peer_id"] == "ghost-id" for p in bridge.peers()), "ghost peer is now in peers()")

    refreshed = next(p for p in bridge.peers() if p["peer_id"] == peer.peer_id)
    check(refreshed["packets_in"] >= 1, "packets_in counter incremented")
    check(refreshed["packets_out"] >= 1, "packets_out counter incremented")


def test_timeout_sweep():
    print("\n[4] Idle peers are swept after peer_timeout_s")
    vault = FakeVault()
    bridge = PhiBridge(vault=vault, peer_timeout_s=0.05)
    peer = bridge.register_peer(label="ephemeral")
    check(bridge.peer_count() == 1, "peer registered")
    time.sleep(0.12)
    # Any read triggers the sweep.
    cnt = bridge.peer_count()
    check(cnt == 0, f"idle peer swept (count={cnt})")
    timeout_card = next(
        (c for c in vault.cards if c["topic"] == "bridge.peer.timeout"), None
    )
    check(timeout_card is not None, "timeout fed back to vault as bridge.peer.timeout")
    if timeout_card:
        check(timeout_card["payload"]["peer_id"] == peer.peer_id, "timeout card names the swept peer")


def test_history_bound():
    print("\n[5] Packet history is bounded and ordered")
    bridge = PhiBridge(vault=FakeVault(), max_history=10)
    peer = bridge.register_peer(label="hist")
    for i in range(25):
        bridge.exchange(peer.peer_id, peer_state={"i": i})
    hist = bridge.history(n=100)
    check(len(hist) == 10, f"history length capped at max_history (got {len(hist)})")
    timestamps = [p["timestamp"] for p in hist]
    check(timestamps == sorted(timestamps), "history is in chronological order")


def test_singleton_lifecycle():
    print("\n[6] get_phi_bridge / reset_phi_bridge")
    reset_phi_bridge()
    vault = FakeVault()
    a = get_phi_bridge(vault=vault)
    b = get_phi_bridge()
    check(a is b, "get_phi_bridge returns the same instance")
    check(a.vault is vault, "vault attached on first construction")
    reset_phi_bridge()
    c = get_phi_bridge()
    check(c is not a, "reset_phi_bridge yields a fresh instance")


def main():
    print("=" * 80)
    print("  PHI BRIDGE TEST SUITE")
    print("=" * 80)

    test_register_and_drop()
    test_cadence_scales_with_peers()
    test_exchange_round_trip()
    test_timeout_sweep()
    test_history_bound()
    test_singleton_lifecycle()

    print()
    print("=" * 80)
    print(f"  RESULT: {PASS} passed, {FAIL} failed")
    print("=" * 80)
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
