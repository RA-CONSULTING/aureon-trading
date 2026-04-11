#!/usr/bin/env python3
"""
Voice layer tests.

  - Each persona composes a prompt from live vault state
  - ChoiceGate decides when to speak
  - SelfDialogueEngine runs speaker/listener exchanges
  - Human-directed replies now gather a full internal chorus first
  - ThoughtStreamLoop runs multiple cycles
  - SelfFeedbackLoop.tick() speaks when voice is enabled
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.vault import (  # noqa: E402
    AureonSelfFeedbackLoop,
    AureonVault,
    ChoiceGate,
    SelfDialogueEngine,
    ThoughtStreamLoop,
    build_all_voices,
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


def test_voices_compose_from_state():
    print("\n[1] Each voice composes self-authored prompts from vault state")
    vault = AureonVault()

    vault.love_amplitude = 0.3
    vault.gratitude_score = 0.5
    vault.last_casimir_force = 0.1
    vault.dominant_chakra = "foundation"
    vault.cortex_snapshot = {
        "delta": 0.3,
        "theta": 0.1,
        "alpha": 0.1,
        "beta": 0.1,
        "gamma": 0.1,
    }

    voices = build_all_voices()
    statements_1 = {}
    for name, voice in voices.items():
        statement = voice.speak(vault)
        check(statement is not None, f"{name} produced a statement")
        if statement:
            check(len(statement.prompt_used) > 20, f"{name} prompt_used is substantial")
            check(len(statement.text) > 0, f"{name} adapter returned text")
            statements_1[name] = statement.prompt_used

    vault.love_amplitude = 0.9
    vault.gratitude_score = 0.85
    vault.last_casimir_force = 5.2
    vault.dominant_chakra = "crown"
    vault.rally_active = True
    vault.cortex_snapshot = {
        "delta": 0.1,
        "theta": 0.1,
        "alpha": 0.4,
        "beta": 0.35,
        "gamma": 0.55,
    }

    statements_2 = {}
    for name, voice in voices.items():
        statement = voice.speak(vault)
        if statement:
            statements_2[name] = statement.prompt_used

    different_count = sum(
        1
        for name in statements_1
        if name in statements_2 and statements_1[name] != statements_2[name]
    )
    check(
        different_count >= len(statements_1) // 2,
        f"at least half the voices' prompts changed with state ({different_count}/{len(statements_1)})",
    )

    vault.last_lambda_t = 0.87
    queen_stmt = voices["queen"].speak(vault)
    check(
        "0.870" in queen_stmt.prompt_used or "+0.87" in queen_stmt.prompt_used,
        "Queen voice names Lambda(t) from state",
    )

    vault.last_casimir_force = 4.321
    miner_stmt = voices["miner"].speak(vault)
    check(
        "4.321" in miner_stmt.prompt_used,
        "Miner voice names the Casimir drift value from state",
    )


def test_choice_gate():
    print("\n[2] ChoiceGate decides based on vault state")
    vault = AureonVault()
    gate = ChoiceGate(min_interval_s=0.0, urgency_threshold=0.3, background_rate=0.0)

    vault.love_amplitude = 0.2
    vault.gratitude_score = 0.5
    vault.last_casimir_force = 0.05
    vault.cortex_snapshot["gamma"] = 0.05
    quiet = gate.decide(vault)
    check(not quiet.should_speak, f"quiet vault -> silent (urgency={quiet.urgency:.2f})")

    vault.rally_active = True
    rally = gate.decide(vault)
    check(rally.should_speak, f"rally mode -> speak (urgency={rally.urgency:.2f})")
    check(rally.preferred_voice == "council", f"rally prefers council voice (got {rally.preferred_voice})")

    vault.rally_active = False
    vault.cortex_snapshot["gamma"] = 0.8
    gamma = gate.decide(vault)
    check(gamma.should_speak, f"gamma spike -> speak (urgency={gamma.urgency:.2f})")
    check(gamma.preferred_voice == "queen", f"gamma prefers queen (got {gamma.preferred_voice})")

    vault.cortex_snapshot["gamma"] = 0.05
    vault.last_casimir_force = 5.0
    drift = gate.decide(vault)
    check(drift.preferred_voice == "miner", f"drift prefers miner (got {drift.preferred_voice})")

    vault.last_casimir_force = 0.1
    vault.love_amplitude = 0.85
    love = gate.decide(vault)
    check(love.preferred_voice == "lover", f"high love prefers lover (got {love.preferred_voice})")

    gate_rl = ChoiceGate(min_interval_s=10.0, urgency_threshold=0.0, background_rate=1.0)
    vault.rally_active = True
    first = gate_rl.decide(vault)
    second = gate_rl.decide(vault)
    check(first.should_speak, "first call passes rate limit")
    check(not second.should_speak, "second call within interval is suppressed")


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
    utterance = engine.converse()
    size_after = len(vault)

    check(utterance is not None, "converse produced an utterance")
    if utterance is None:
        return
    check(utterance.speaker != "", "utterance has a speaker")
    check(utterance.listener != "", "utterance has a listener")
    check(utterance.speaker != utterance.listener, f"speaker ({utterance.speaker}) != listener ({utterance.listener})")
    check(utterance.statement is not None, "statement recorded")
    check(utterance.response is not None, "response recorded")
    check(size_after >= size_before + 2, f"vault grew by >=2 from the exchange ({size_before}->{size_after})")

    voice_cards = vault.by_category("vault_voice")
    check(len(voice_cards) >= 2, f"vault_voice category has >=2 cards ({len(voice_cards)})")
    check(
        utterance.vault_fingerprint_before != utterance.vault_fingerprint_after,
        "vault fingerprint changed across the exchange",
    )


def test_human_response_runs_chorus():
    print("\n[4] Human-directed response gathers the full chorus first")
    vault = AureonVault()
    vault.love_amplitude = 0.82
    vault.gratitude_score = 0.76
    vault.cortex_snapshot["gamma"] = 0.41
    vault.last_lambda_t = 0.58
    vault.dominant_chakra = "love"

    engine = SelfDialogueEngine(
        vault=vault,
        choice_gate=ChoiceGate(min_interval_s=0.0, urgency_threshold=0.0, background_rate=1.0, rng_seed=3),
    )

    voice_cards_before = len(vault.by_category("vault_voice"))
    utterance = engine.respond_to_human("Do all of you hear me?", voice_name="queen")
    voice_cards_after = len(vault.by_category("vault_voice"))

    check(utterance is not None, "human message produced an utterance")
    if utterance is None:
        return
    check(utterance.listener == "queen", f"requested final voice is queen (got {utterance.listener})")
    check(len(utterance.chorus) == len(engine.voices), f"chorus includes all voices ({len(utterance.chorus)})")
    check({item.voice for item in utterance.chorus} == set(engine.voices.keys()), "chorus covers every registered voice")
    check("chorus(" in utterance.reasoning, f"reasoning records chorus flow ({utterance.reasoning})")
    check(
        voice_cards_after >= voice_cards_before + len(engine.voices) + 1,
        f"chorus + final response fed back into vault ({voice_cards_before}->{voice_cards_after})",
    )
    check(utterance.response is not None, "final response recorded")
    check(len(utterance.response.text) > 10, "final response text is substantive")


def test_thought_stream_loop():
    print("\n[5] ThoughtStreamLoop produces utterances over N cycles")
    vault = AureonVault()
    vault.love_amplitude = 0.85
    vault.gratitude_score = 0.8
    vault.cortex_snapshot["gamma"] = 0.45
    vault.rally_active = True

    engine = SelfDialogueEngine(
        vault=vault,
        choice_gate=ChoiceGate(min_interval_s=0.0, urgency_threshold=0.3, background_rate=0.0, rng_seed=1),
    )
    stream = ThoughtStreamLoop(vault=vault, engine=engine, base_interval_s=0.001)

    utterances = stream.run_n_cycles(5, sleep_between=False)
    check(len(utterances) >= 3, f"stream produced >=3 utterances in 5 cycles (got {len(utterances)})")

    status = stream.get_status()
    check(status.cycles == 5, f"stream tracked cycles ({status.cycles})")
    check(status.utterances >= 3, f"stream tracked utterances ({status.utterances})")


def test_self_feedback_loop_voice_integration():
    print("\n[6] AureonSelfFeedbackLoop.tick() speaks when conditions are right")
    loop = AureonSelfFeedbackLoop(base_interval_s=0.01, enable_voice=True)

    loop.vault.love_amplitude = 0.9
    loop.vault.gratitude_score = 0.85
    loop.vault.rally_active = True

    loop.voice_engine.gate = ChoiceGate(
        min_interval_s=0.0,
        urgency_threshold=0.0,
        background_rate=1.0,
        rng_seed=42,
    )

    result = loop.tick()
    check(result.spoke, f"tick spoke when gate forced (spoke={result.spoke})")
    check(result.speaker != "", f"tick recorded speaker ({result.speaker})")
    check(result.listener != "", f"tick recorded listener ({result.listener})")
    check(len(result.utterance_preview) > 0, "tick recorded utterance preview")

    status = loop.get_status()
    check("voice" in status, "status exposes voice section")
    check(status["voice"] is not None, f"voice status populated: {type(status.get('voice'))}")


def main():
    print("=" * 80)
    print("  VAULT VOICE TEST SUITE")
    print("=" * 80)

    test_voices_compose_from_state()
    test_choice_gate()
    test_self_dialogue_engine()
    test_human_response_runs_chorus()
    test_thought_stream_loop()
    test_self_feedback_loop_voice_integration()

    print()
    print("=" * 80)
    print(f"  RESULT: {PASS} passed, {FAIL} failed")
    print("=" * 80)
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
