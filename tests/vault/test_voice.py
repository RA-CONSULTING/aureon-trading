#!/usr/bin/env python3
"""
tests/vault/test_voice.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Voice layer tests:
  • VaultVoice base and 6 personas each compose a prompt from vault state
  • The composed prompt is not a template — different state → different lines
  • ChoiceGate decides when to speak based on vault state + urgency
  • SelfDialogueEngine runs a full exchange (speaker + listener) and feeds
    both utterances back into the vault
  • ThoughtStreamLoop runs N cycles synchronously
  • Integration: SelfFeedbackLoop.tick() speaks when the voice engine is on
"""

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.vault import (
    AureonVault,
    AureonSelfFeedbackLoop,
    ChoiceGate,
    build_all_voices,
    SelfDialogueEngine,
    ThoughtStreamLoop,
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


# ─────────────────────────────────────────────────────────────────────────────
# 1. VaultVoice composes non-scripted prompts
# ─────────────────────────────────────────────────────────────────────────────


def test_voices_compose_from_state():
    print("\n[1] Each voice composes self-authored prompts from vault state")
    vault = AureonVault()

    # First state — calm
    vault.love_amplitude = 0.3
    vault.gratitude_score = 0.5
    vault.last_casimir_force = 0.1
    vault.dominant_chakra = "foundation"
    vault.cortex_snapshot = {"delta": 0.3, "theta": 0.1, "alpha": 0.1,
                              "beta": 0.1, "gamma": 0.1}

    voices = build_all_voices()

    # Every voice produces a statement
    statements_1 = {}
    for name, voice in voices.items():
        s = voice.speak(vault)
        check(s is not None, f"{name} produced a statement")
        if s:
            check(len(s.prompt_used) > 20, f"{name} prompt_used is substantial")
            check(len(s.text) > 0, f"{name} adapter returned text")
            statements_1[name] = s.prompt_used

    # Now change the state drastically — prompts should differ
    vault.love_amplitude = 0.9
    vault.gratitude_score = 0.85
    vault.last_casimir_force = 5.2
    vault.dominant_chakra = "crown"
    vault.rally_active = True
    vault.cortex_snapshot = {"delta": 0.1, "theta": 0.1, "alpha": 0.4,
                              "beta": 0.35, "gamma": 0.55}

    statements_2 = {}
    for name, voice in voices.items():
        s = voice.speak(vault)
        if s:
            statements_2[name] = s.prompt_used

    # Verify at least half the voices produced DIFFERENT prompts from state 1
    different_count = sum(
        1 for name in statements_1
        if name in statements_2 and statements_1[name] != statements_2[name]
    )
    check(
        different_count >= len(statements_1) // 2,
        f"at least half the voices' prompts changed with state ({different_count}/{len(statements_1)})",
    )

    # Queen voice specifically mentions Λ(t) only when we set it
    vault.last_lambda_t = 0.87
    queen_stmt = voices["queen"].speak(vault)
    check(
        "0.870" in queen_stmt.prompt_used or "+0.87" in queen_stmt.prompt_used,
        "Queen voice names Λ(t) from state (not from a template)",
    )

    # Miner voice explicitly names the Casimir drift value it saw
    vault.last_casimir_force = 4.321
    miner_stmt = voices["miner"].speak(vault)
    check(
        "4.321" in miner_stmt.prompt_used,
        "Miner voice names the Casimir drift value from state",
    )


# ─────────────────────────────────────────────────────────────────────────────
# 2. ChoiceGate decides autonomously
# ─────────────────────────────────────────────────────────────────────────────


def test_choice_gate():
    print("\n[2] ChoiceGate decides based on vault state")
    vault = AureonVault()
    gate = ChoiceGate(min_interval_s=0.0, urgency_threshold=0.3, background_rate=0.0)

    # Quiet vault → should not speak
    vault.love_amplitude = 0.2
    vault.gratitude_score = 0.5
    vault.last_casimir_force = 0.05
    vault.cortex_snapshot["gamma"] = 0.05
    d_quiet = gate.decide(vault)
    check(not d_quiet.should_speak, f"quiet vault → silent (urgency={d_quiet.urgency:.2f})")

    # Rally mode → should speak
    vault.rally_active = True
    d_rally = gate.decide(vault)
    check(d_rally.should_speak, f"rally mode → speak (urgency={d_rally.urgency:.2f})")
    check(
        d_rally.preferred_voice == "council",
        f"rally prefers council voice (got {d_rally.preferred_voice})",
    )

    # Gamma spike → prefer queen
    # Use gamma = 0.8 so gamma_spike factor = min(0.4, 0.8 * 0.5) = 0.4 (clearly > threshold)
    vault.rally_active = False
    vault.cortex_snapshot["gamma"] = 0.8
    d_gamma = gate.decide(vault)
    check(
        d_gamma.should_speak,
        f"gamma spike → speak (urgency={d_gamma.urgency:.2f})",
    )
    check(d_gamma.preferred_voice == "queen", f"gamma prefers queen (got {d_gamma.preferred_voice})")

    # Casimir drift → prefer miner
    vault.cortex_snapshot["gamma"] = 0.05
    vault.last_casimir_force = 5.0
    d_drift = gate.decide(vault)
    check(
        d_drift.preferred_voice == "miner",
        f"drift prefers miner (got {d_drift.preferred_voice})",
    )

    # High love → prefer lover
    vault.last_casimir_force = 0.1
    vault.love_amplitude = 0.85
    d_love = gate.decide(vault)
    check(
        d_love.preferred_voice == "lover",
        f"high love prefers lover (got {d_love.preferred_voice})",
    )

    # Rate limit test — min_interval
    gate_rl = ChoiceGate(min_interval_s=10.0, urgency_threshold=0.0, background_rate=1.0)
    vault.rally_active = True
    d_a = gate_rl.decide(vault)
    d_b = gate_rl.decide(vault)
    check(d_a.should_speak, "first call passes rate limit")
    check(not d_b.should_speak, "second call within interval is suppressed")


# ─────────────────────────────────────────────────────────────────────────────
# 3. SelfDialogueEngine exchange
# ─────────────────────────────────────────────────────────────────────────────


def test_self_dialogue_engine():
    print("\n[3] SelfDialogueEngine runs exchanges and feeds them back")
    vault = AureonVault()
    vault.love_amplitude = 0.85
    vault.gratitude_score = 0.8
    vault.cortex_snapshot["gamma"] = 0.45
    vault.last_lambda_t = 0.65
    vault.dominant_chakra = "love"

    engine = SelfDialogueEngine(
        vault=vault,
        choice_gate=ChoiceGate(min_interval_s=0.0, urgency_threshold=0.1, background_rate=1.0, rng_seed=7),
    )

    size_before = len(vault)
    u = engine.converse()
    size_after = len(vault)

    check(u is not None, "converse produced an utterance")
    if u is None:
        return
    check(u.speaker != "", "utterance has a speaker")
    check(u.listener != "", "utterance has a listener")
    check(u.speaker != u.listener, f"speaker ({u.speaker}) ≠ listener ({u.listener})")
    check(u.statement is not None, "statement recorded")
    check(u.response is not None, "response recorded")
    check(
        size_after >= size_before + 2,
        f"vault grew by ≥2 from the exchange ({size_before}→{size_after})",
    )

    # Both statements should be vault_voice category
    voice_cards = vault.by_category("vault_voice")
    check(
        len(voice_cards) >= 2,
        f"vault_voice category has ≥2 cards ({len(voice_cards)})",
    )

    # Fingerprints before/after differ
    check(
        u.vault_fingerprint_before != u.vault_fingerprint_after,
        "vault fingerprint changed across the exchange",
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4. ThoughtStreamLoop runs cycles
# ─────────────────────────────────────────────────────────────────────────────


def test_thought_stream_loop():
    print("\n[4] ThoughtStreamLoop produces utterances over N cycles")
    vault = AureonVault()
    vault.love_amplitude = 0.85
    vault.gratitude_score = 0.8
    vault.cortex_snapshot["gamma"] = 0.45
    vault.rally_active = True  # guarantees an utterance

    engine = SelfDialogueEngine(
        vault=vault,
        choice_gate=ChoiceGate(min_interval_s=0.0, urgency_threshold=0.3, background_rate=0.0, rng_seed=1),
    )
    stream = ThoughtStreamLoop(vault=vault, engine=engine, base_interval_s=0.001)

    utterances = stream.run_n_cycles(5, sleep_between=False)
    check(len(utterances) >= 3, f"stream produced ≥3 utterances in 5 cycles (got {len(utterances)})")

    status = stream.get_status()
    check(status.cycles == 5, f"stream tracked cycles ({status.cycles})")
    check(status.utterances >= 3, f"stream tracked utterances ({status.utterances})")


# ─────────────────────────────────────────────────────────────────────────────
# 5. SelfFeedbackLoop integration — voice runs inside tick()
# ─────────────────────────────────────────────────────────────────────────────


def test_self_feedback_loop_voice_integration():
    print("\n[5] AureonSelfFeedbackLoop.tick() speaks when conditions are right")
    loop = AureonSelfFeedbackLoop(base_interval_s=0.01, enable_voice=True)

    # Force a speak-worthy state
    loop.vault.love_amplitude = 0.9
    loop.vault.gratitude_score = 0.85
    loop.vault.rally_active = True

    # Override the voice engine's gate to always speak
    loop.voice_engine.gate = ChoiceGate(
        min_interval_s=0.0, urgency_threshold=0.0, background_rate=1.0, rng_seed=42,
    )

    result = loop.tick()
    check(result.spoke, f"tick spoke when gate forced (spoke={result.spoke})")
    check(result.speaker != "", f"tick recorded speaker ({result.speaker})")
    check(result.listener != "", f"tick recorded listener ({result.listener})")
    check(len(result.utterance_preview) > 0, "tick recorded utterance preview")

    # Status exposes voice key
    status = loop.get_status()
    check("voice" in status, "status exposes voice section")
    check(
        status["voice"] is not None,
        f"voice status populated: {type(status.get('voice'))}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────


def main():
    print("=" * 80)
    print("  VAULT VOICE TEST SUITE")
    print("=" * 80)

    test_voices_compose_from_state()
    test_choice_gate()
    test_self_dialogue_engine()
    test_thought_stream_loop()
    test_self_feedback_loop_voice_integration()

    print()
    print("=" * 80)
    print(f"  RESULT: {PASS} passed, {FAIL} failed")
    print("=" * 80)
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
