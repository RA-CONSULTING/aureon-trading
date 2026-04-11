#!/usr/bin/env python3
"""
Tests for aureon.queen.conversation_memory.ConversationMemory.

Covers:
  - record / recent round-trip per peer
  - peers don't cross-contaminate
  - max_turns_per_peer cap
  - max_peers eviction (LRU by last_touch)
  - idle TTL sweep
  - clear / clear_all
  - format_as_prompt_block output shape
  - disk persistence round-trip
  - thread safety under concurrent writes
"""

import json
import os
import sys
import tempfile
import threading
import time

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.queen.conversation_memory import (  # noqa: E402
    ConversationMemory,
    Thread,
    Turn,
    get_conversation_memory,
    reset_conversation_memory,
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


def _fresh_memory(**kw):
    # Isolate tests from the repo's real state dir.
    tmp = tempfile.mkdtemp(prefix="aureon_conv_test_")
    path = os.path.join(tmp, "memory.json")
    return ConversationMemory(persist_path=path, autoload=False, **kw)


def test_record_and_recent():
    print("\n[1] record + recent round-trip per peer")
    m = _fresh_memory()
    m.record("peer-a", "human", "hello")
    m.record("peer-a", "queen", "tranquility holds")
    m.record("peer-a", "human", "good")
    turns = m.recent("peer-a", n=10)
    check(len(turns) == 3, f"3 turns recorded (got {len(turns)})")
    check(turns[0].role == "human" and turns[0].text == "hello", "first turn preserved")
    check(turns[1].role == "queen" and "tranquility" in turns[1].text, "second turn preserved")
    check(turns[-1].text == "good", "order preserved")
    check(all(t.timestamp > 0 for t in turns), "timestamps populated")


def test_peers_isolated():
    print("\n[2] peers do not cross-contaminate")
    m = _fresh_memory()
    m.record("a", "human", "msg from a")
    m.record("b", "human", "msg from b")
    m.record("a", "queen", "reply to a")
    a = m.recent("a")
    b = m.recent("b")
    check(len(a) == 2 and len(b) == 1, f"a has 2, b has 1 (got {len(a)}, {len(b)})")
    check(all("a" in t.text for t in a), "peer a only has a's turns")
    check(all("b" in t.text for t in b), "peer b only has b's turns")


def test_max_turns_cap():
    print("\n[3] max_turns_per_peer caps the ring buffer")
    m = _fresh_memory(max_turns_per_peer=5)
    for i in range(12):
        m.record("p", "human", f"msg {i}")
    turns = m.recent("p", n=10)
    check(len(turns) == 5, f"cap at 5 (got {len(turns)})")
    check(turns[0].text == "msg 7" and turns[-1].text == "msg 11", f"FIFO eviction kept the tail ({turns[0].text} .. {turns[-1].text})")


def test_max_peers_eviction():
    print("\n[4] max_peers evicts oldest by last_touch")
    m = _fresh_memory(max_peers=3)
    m.record("p1", "human", "one")
    time.sleep(0.01)
    m.record("p2", "human", "two")
    time.sleep(0.01)
    m.record("p3", "human", "three")
    # Touching p1 bumps its last_touch forward.
    time.sleep(0.01)
    m.record("p1", "human", "again")
    # Adding p4 should evict p2 (the now-oldest by last_touch).
    time.sleep(0.01)
    m.record("p4", "human", "four")
    peers = set(m.peers())
    check("p1" in peers and "p3" in peers and "p4" in peers, f"p1/p3/p4 retained (got {peers})")
    check("p2" not in peers, f"p2 evicted (got {peers})")


def test_idle_ttl_sweep():
    print("\n[5] idle peers are swept after peer_idle_ttl_s")
    m = _fresh_memory(peer_idle_ttl_s=0.05)
    m.record("ghost", "human", "hi")
    check("ghost" in m.peers(), "peer present pre-sweep")
    time.sleep(0.15)
    peers = m.peers()  # triggers sweep
    check("ghost" not in peers, f"peer swept after TTL (got {peers})")


def test_clear_and_clear_all():
    print("\n[6] clear / clear_all")
    m = _fresh_memory()
    m.record("a", "human", "x")
    m.record("b", "human", "y")
    check(m.clear("a") is True, "clear(a) returns True")
    check(m.clear("a") is False, "clear(a) second time returns False")
    check("b" in m.peers(), "b still present")
    m.clear_all()
    check(m.peers() == [], "clear_all removes everyone")


def test_format_as_prompt_block():
    print("\n[7] format_as_prompt_block emits a compact block")
    m = _fresh_memory()
    m.record("p", "human", "what is your state")
    m.record("p", "queen", "tranquility and harmony, Lambda at -0.15")
    m.record("p", "human", "are you sure?")
    block = m.format_as_prompt_block("p", n=10)
    check(block.startswith("Recent conversation:"), "block has header")
    check("human: what is your state" in block, "first human turn present")
    check("you: tranquility" in block, "queen's turn tagged as 'you'")
    check("human: are you sure?" in block, "latest human turn present")

    # No memory for an unknown peer -> empty string.
    check(m.format_as_prompt_block("nobody") == "", "empty for unknown peer")

    # Very long turn gets truncated.
    long_text = "x" * 1000
    m.record("p", "human", long_text)
    block2 = m.format_as_prompt_block("p", n=10, max_chars_per_turn=50)
    check("..." in block2, "long turn truncated with ellipsis")


def test_persistence_roundtrip():
    print("\n[8] persistence round-trips through disk")
    tmp = tempfile.mkdtemp(prefix="aureon_conv_persist_")
    path = os.path.join(tmp, "memory.json")
    m1 = ConversationMemory(persist_path=path, autoload=False)
    m1.record("p", "human", "remember me")
    m1.record("p", "queen", "always")
    check(os.path.exists(path), "persist file written")

    # Sanity-check the file is valid JSON.
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    check(payload.get("version") == 2, "version stamped")
    check(len(payload.get("threads", [])) == 1, "one thread serialised")

    # New instance should reload it.
    m2 = ConversationMemory(persist_path=path, autoload=True)
    turns = m2.recent("p", n=10)
    check(len(turns) == 2, f"reloaded 2 turns (got {len(turns)})")
    check(turns[0].text == "remember me", "first turn reloaded")
    check(turns[1].text == "always", "second turn reloaded")


def test_thread_safety():
    print("\n[9] concurrent writes don't corrupt state")
    m = _fresh_memory(max_turns_per_peer=1000)

    def worker(peer_id, n):
        for i in range(n):
            m.record(peer_id, "human", f"{peer_id}-{i}")

    threads = []
    for pid in ("t1", "t2", "t3"):
        t = threading.Thread(target=worker, args=(pid, 50))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    counts = {p: len(m.recent(p, n=1000)) for p in ("t1", "t2", "t3")}
    check(all(c == 50 for c in counts.values()), f"each thread got 50 turns ({counts})")


def test_facts_roundtrip():
    print("\n[11] facts field records through record() and persists")
    tmp = tempfile.mkdtemp(prefix="aureon_conv_facts_")
    path = os.path.join(tmp, "memory.json")
    m1 = ConversationMemory(persist_path=path, autoload=False)
    m1.record(
        "p",
        "human",
        "what is 12 plus 7",
        facts={"math": {"expression": "12+7", "result": 19}},
    )
    m1.record(
        "p",
        "queen",
        "nineteen",
        facts={"math_confirmed": 19},
    )

    turns = m1.recent("p", n=10)
    check(len(turns) == 2, f"two turns recorded (got {len(turns)})")
    check(turns[0].facts["math"]["result"] == 19, "first turn facts present")
    check(turns[1].facts["math_confirmed"] == 19, "second turn facts present")

    # Round-trip through disk.
    m2 = ConversationMemory(persist_path=path, autoload=True)
    turns2 = m2.recent("p", n=10)
    check(len(turns2) == 2, "both turns survived persistence")
    check(turns2[0].facts["math"]["result"] == 19, "facts survived persistence")

    # Legacy v1 file (no facts key) still loads — turns get empty facts.
    legacy_path = os.path.join(tmp, "legacy.json")
    with open(legacy_path, "w", encoding="utf-8") as f:
        json.dump({
            "version": 1,
            "saved_at": time.time(),
            "threads": [{
                "peer_id": "old",
                "created_at": time.time() - 10,
                "last_touch": time.time(),
                "turns": [
                    {"role": "human", "text": "hello", "timestamp": time.time(), "meta": {}},
                    {"role": "queen", "text": "hi there", "timestamp": time.time(), "meta": {}},
                ],
            }],
        }, f)
    m3 = ConversationMemory(persist_path=legacy_path, autoload=True)
    legacy_turns = m3.recent("old", n=10)
    check(len(legacy_turns) == 2, f"legacy v1 file loaded ({len(legacy_turns)} turns)")
    check(
        all(t.facts == {} for t in legacy_turns),
        "legacy turns load with empty facts",
    )
    check(legacy_turns[0].text == "hello", "legacy text preserved")


def test_recent_facts_merge():
    print("\n[12] recent_facts merges across turns, later overrides earlier")
    m = _fresh_memory()
    m.record("p", "human", "what is 2+2", facts={"math": {"expression": "2+2", "result": 4}})
    m.record("p", "queen", "four", facts={"note": "simple"})
    m.record("p", "human", "what is 3+3", facts={"math": {"expression": "3+3", "result": 6}})

    merged = m.recent_facts("p", n=10)
    check(merged.get("note") == "simple", f"earlier-only key preserved ({merged.get('note')!r})")
    check(
        merged.get("math", {}).get("result") == 6,
        f"later 'math' overrode earlier (got {merged.get('math')})",
    )

    # Unknown peer → empty merge.
    check(m.recent_facts("nobody") == {}, "unknown peer returns empty merge")

    # n=0 → empty merge (no turns consulted).
    check(m.recent_facts("p", n=0) == {}, "n=0 returns empty")


def test_persist_version_bump():
    print("\n[13] persist writes version 2")
    tmp = tempfile.mkdtemp(prefix="aureon_conv_version_")
    path = os.path.join(tmp, "memory.json")
    m = ConversationMemory(persist_path=path, autoload=False)
    m.record("p", "human", "hi")
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    check(payload.get("version") == 2, f"version == 2 (got {payload.get('version')})")


def test_get_reset_singleton():
    print("\n[10] get / reset singleton")
    reset_conversation_memory()
    a = get_conversation_memory()
    b = get_conversation_memory()
    check(a is b, "singleton returns same instance")
    reset_conversation_memory()
    c = get_conversation_memory()
    check(c is not a, "reset yields a new instance")


def main():
    print("=" * 80)
    print("  CONVERSATION MEMORY TEST SUITE")
    print("=" * 80)

    test_record_and_recent()
    test_peers_isolated()
    test_max_turns_cap()
    test_max_peers_eviction()
    test_idle_ttl_sweep()
    test_clear_and_clear_all()
    test_format_as_prompt_block()
    test_persistence_roundtrip()
    test_thread_safety()
    test_facts_roundtrip()
    test_recent_facts_merge()
    test_persist_version_bump()
    test_get_reset_singleton()

    print()
    print("=" * 80)
    print(f"  RESULT: {PASS} passed, {FAIL} failed")
    print("=" * 80)
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
