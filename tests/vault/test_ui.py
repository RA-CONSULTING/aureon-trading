#!/usr/bin/env python3
"""
tests/vault/test_ui.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Flask test-client tests for the vault UI server.

  • GET /                  serves the chat HTML
  • GET /api/health        returns loop + voice status
  • GET /api/status        returns full nested status dict
  • GET /api/voices        lists the 7 personas
  • GET /api/utterances    returns empty list initially, then populated
  • POST /api/message      ingests a human message + returns a response
  • POST /api/speak        forces a specific voice to speak
  • POST /api/converse     runs one converse() cycle
  • POST /api/tick         runs one full loop.tick()
  • POST /api/loop/start   starts the background loop
  • POST /api/loop/stop    stops the background loop

Uses Flask's test_client so no network server is booted.
"""

import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

try:
    import importlib.util
    _FLASK = importlib.util.find_spec("flask") is not None
except Exception:
    _FLASK = False


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


# ─────────────────────────────────────────────────────────────────────────────
# Build app + client
# ─────────────────────────────────────────────────────────────────────────────


def _build_client():
    from aureon.vault import AureonSelfFeedbackLoop, ChoiceGate
    from aureon.vault.ui import create_app

    loop = AureonSelfFeedbackLoop(base_interval_s=0.01, enable_voice=True)
    # Lower the rate limit so multiple tests can speak in sequence
    loop.voice_engine.gate = ChoiceGate(
        min_interval_s=0.0, urgency_threshold=0.0, background_rate=1.0, rng_seed=7,
    )
    # Prime state so the voices have something to say
    loop.vault.love_amplitude = 0.85
    loop.vault.gratitude_score = 0.80
    loop.vault.cortex_snapshot["gamma"] = 0.45
    loop.vault.last_lambda_t = 0.6

    app = create_app(loop=loop)
    app.testing = True
    return app.test_client(), loop


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_index_and_health():
    print("\n[1] index page + health")
    client, loop = _build_client()

    r = client.get("/")
    check(r.status_code == 200, f"GET / returned 200 (got {r.status_code})")
    check(b"AUREON VAULT" in r.data or b"Aureon Vault" in r.data,
          "index.html mentions the vault name")

    r = client.get("/api/health")
    check(r.status_code == 200, "health endpoint reachable")
    data = r.get_json()
    check(data.get("ok"), "health.ok is True")
    check(data.get("voice_enabled") is True, "voice is enabled on the loop")
    check(data.get("loop_id") == loop.loop_id, "health returns the loop_id")


def test_status_and_voices():
    print("\n[2] status + voices endpoints")
    client, loop = _build_client()

    r = client.get("/api/status")
    data = r.get_json()
    check(data.get("ok"), "/api/status ok")
    status = data["status"]
    for key in ("loop_id", "cycles", "vault", "clock", "casimir", "auris",
                "deployer", "pinger", "rally", "voice"):
        check(key in status, f"status exposes {key}")

    r = client.get("/api/voices")
    data = r.get_json()
    check(data.get("ok"), "/api/voices ok")
    voices = data["voices"]
    check(len(voices) == 7, f"7 voices registered (got {len(voices)})")
    for expected in ("vault", "queen", "miner", "scout", "council", "architect", "lover"):
        check(expected in voices, f"{expected} voice is registered")


def test_message_endpoint():
    print("\n[3] POST /api/message — human talks to the vault")
    client, loop = _build_client()

    r = client.post(
        "/api/message",
        data=json.dumps({"text": "How are you feeling?", "voice": "queen"}),
        content_type="application/json",
    )
    check(r.status_code == 200, f"POST /api/message returned 200 (got {r.status_code})")
    data = r.get_json()
    check(data.get("ok"), "message response ok")
    check("utterance" in data, "utterance in response")

    u = data["utterance"]
    check(u["speaker"] == "human", f"speaker is 'human' (got {u.get('speaker')})")
    check(u["listener"] == "queen", f"listener is 'queen' (got {u.get('listener')})")
    check(u["statement"]["text"] == "How are you feeling?",
          "statement echoes the human message")
    check(u["response"] is not None, "response present")
    check(len(u["response"]["text"]) > 10, "response text is substantive")


def test_message_auto_voice_pick():
    print("\n[4] POST /api/message with no voice → gate picks")
    client, _loop = _build_client()

    r = client.post(
        "/api/message",
        data=json.dumps({"text": "Are we in rally mode?"}),
        content_type="application/json",
    )
    data = r.get_json()
    check(data.get("ok"), "auto-voice response ok")
    listener = data["utterance"]["listener"]
    known = {"vault", "queen", "miner", "scout", "council", "architect", "lover"}
    check(listener in known, f"auto-picked listener is a known voice (got {listener})")


def test_speak_and_converse():
    print("\n[5] POST /api/speak and /api/converse")
    client, _loop = _build_client()

    r = client.post(
        "/api/speak",
        data=json.dumps({"voice": "miner"}),
        content_type="application/json",
    )
    data = r.get_json()
    check(data.get("ok"), "/api/speak ok")
    check("utterance" in data, "speak returned an utterance")
    check(data["utterance"]["speaker"] == "miner",
          f"speaker is miner (got {data['utterance'].get('speaker')})")

    r = client.post("/api/converse")
    data = r.get_json()
    check(data.get("ok"), "/api/converse ok")
    # converse() should speak under our forced gate
    check(data.get("spoke") is True, "converse spoke under forced gate")


def test_tick_endpoint():
    print("\n[6] POST /api/tick runs one loop tick")
    client, loop = _build_client()

    cycles_before = loop._cycle
    r = client.post("/api/tick")
    data = r.get_json()
    check(data.get("ok"), "/api/tick ok")
    check(loop._cycle == cycles_before + 1, "cycle counter incremented")
    check("tick" in data, "tick result returned")
    tick = data["tick"]
    for key in ("cycle", "vault_size", "casimir_force", "auris_consensus",
                "rally_active", "ping_sent", "spoke"):
        check(key in tick, f"tick result has {key}")


def test_utterances_endpoint():
    print("\n[7] GET /api/utterances returns history")
    client, _loop = _build_client()

    # Send a few messages
    for msg in ["hello", "are you there", "who am I talking to"]:
        client.post(
            "/api/message",
            data=json.dumps({"text": msg, "voice": "queen"}),
            content_type="application/json",
        )

    r = client.get("/api/utterances?n=10")
    data = r.get_json()
    check(data.get("ok"), "/api/utterances ok")
    check(data["count"] >= 3, f"at least 3 utterances recorded (got {data['count']})")

    # Verify the statements echo our messages
    texts = [u["statement"]["text"] for u in data["utterances"] if u.get("statement")]
    check("hello" in texts, "first message preserved in history")


def test_loop_start_stop():
    print("\n[8] POST /api/loop/start and /api/loop/stop")
    client, loop = _build_client()

    r = client.post("/api/loop/start")
    data = r.get_json()
    check(data.get("ok"), "/api/loop/start ok")
    check(data.get("running") is True, "running=True after start")

    r = client.post("/api/loop/stop")
    data = r.get_json()
    check(data.get("ok"), "/api/loop/stop ok")
    check(data.get("running") is False, "running=False after stop")


def main():
    print("=" * 80)
    print("  VAULT UI TEST SUITE")
    print("=" * 80)

    if not _FLASK:
        print("\n  [SKIP] Flask is not installed — UI tests cannot run")
        sys.exit(0)

    test_index_and_health()
    test_status_and_voices()
    test_message_endpoint()
    test_message_auto_voice_pick()
    test_speak_and_converse()
    test_tick_endpoint()
    test_utterances_endpoint()
    test_loop_start_stop()

    print()
    print("=" * 80)
    print(f"  RESULT: {PASS} passed, {FAIL} failed")
    print("=" * 80)
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
