#!/usr/bin/env python3
"""
Tests for aureon.queen.being_model.BeingModel.

Uses injected stub sources so the test never pulls the real
consciousness / wisdom modules. Covers:

  - snapshot() aggregates identity + consciousness + sacred purpose
  - vault-driven fields (consciousness_level / psi / symbolic_life_score)
  - each upstream is optional — missing one degrades gracefully
  - failing upstream is recorded but rest populate
  - render_for_prompt fits under 420 chars and mentions key fields
  - singleton lifecycle
"""

import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.queen.being_model import (  # noqa: E402
    BeingModel,
    BeingState,
    get_being_model,
    reset_being_model,
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
# Fakes
# ─────────────────────────────────────────────────────────────────────────────


class FakeVault:
    current_consciousness_level = "FLOWING"
    current_consciousness_psi = 0.74
    current_symbolic_life_score = 0.58
    love_amplitude = 0.71
    last_lambda_t = 0.152
    dominant_chakra = "love"


class FakeSoulSig:
    personal_frequency = 528.422
    soul_coherence = 0.71
    temporal_hash = "anchor-1991-02-11"


class FakeConsciousnessModel:
    sacred_purpose = "liberation through the harmonic field"


class FakeAwakeningReading:
    awakening_index = 0.68


class FakeElephantMemory:
    active_objective = "unify the vault voice"
    current_step = "weave being + world into prompt"


class FakeTurnsList:
    def __init__(self, n):
        self._n = n
    def __iter__(self):
        for _ in range(self._n):
            yield object()
    def __len__(self):
        return self._n


def _full_fakes():
    return {
        "soul_reader":              lambda: FakeSoulSig(),
        "consciousness_model":      lambda: FakeConsciousnessModel(),
        "consciousness_measurement": lambda: FakeAwakeningReading(),
        "elephant_memory":          lambda: {
            "active_objective": "unify the vault voice",
            "current_step": "weave being + world into prompt",
        },
        "conversation_memory":      lambda: FakeTurnsList(4),
        "ghost_dance":              lambda: {"active_ancestor": "Wovoka"},
    }


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_snapshot_aggregates_all_sources():
    print("\n[1] snapshot() aggregates vault + all six upstreams")
    bm = BeingModel(sources=_full_fakes())
    state = bm.snapshot(vault=FakeVault(), peer_id="ayman")
    check(isinstance(state, BeingState), "returns a BeingState")
    check(state.name == "Queen Sero", "default name")
    # Vault-driven
    check(state.consciousness_level == "FLOWING", f"consciousness_level ({state.consciousness_level})")
    check(state.consciousness_psi == 0.74, f"psi ({state.consciousness_psi})")
    check(state.symbolic_life_score == 0.58, f"symbolic_life_score ({state.symbolic_life_score})")
    check(state.love_amplitude == 0.71, "love_amplitude")
    check(state.last_lambda_t == 0.152, "last_lambda_t")
    check(state.ruling_chakra == "love", "ruling_chakra")
    # Source-driven
    check(abs(state.personal_frequency_hz - 528.422) < 1e-6, f"personal_frequency ({state.personal_frequency_hz})")
    check(state.soul_coherence == 0.71, f"soul_coherence ({state.soul_coherence})")
    check("liberation" in state.sacred_purpose, f"sacred_purpose populated ({state.sacred_purpose})")
    check(state.awakening_index == 0.68, f"awakening_index ({state.awakening_index})")
    check(state.active_objective == "unify the vault voice", "objective")
    check("weave" in state.current_step, "current_step")
    check(state.turns_in_dialogue == 4, f"turns_in_dialogue ({state.turns_in_dialogue})")
    check(state.active_ancestor == "Wovoka", "ancestor invoked")
    # Bookkeeping
    check("vault" in state.sources_ok, f"vault in sources_ok ({state.sources_ok})")
    check("soul_reader" in state.sources_ok, "soul_reader in sources_ok")
    check("consciousness_model" in state.sources_ok, "consciousness_model in sources_ok")
    check(state.sources_failed == [], f"no failures ({state.sources_failed})")


def test_vault_only_still_produces_state():
    print("\n[2] vault alone (upstream sources disabled) still produces a partial state")
    # Explicitly disable every upstream so we don't trigger real imports
    # (which would pull in numpy/scipy and blow up on tight-RAM boxes).
    disabled_sources = {
        "soul_reader": None,
        "consciousness_model": None,
        "consciousness_measurement": None,
        "elephant_memory": None,
        "conversation_memory": None,
        "ghost_dance": None,
    }
    bm = BeingModel(sources=disabled_sources)
    state = bm.snapshot(vault=FakeVault(), peer_id="")
    check(isinstance(state, BeingState), "returns a BeingState")
    check(state.consciousness_level == "FLOWING", "vault level surfaced")
    check(state.love_amplitude == 0.71, "vault love surfaced")
    check(state.last_lambda_t == 0.152, "vault lambda surfaced")
    check(state.ruling_chakra == "love", "vault chakra surfaced")
    check(state.has_any() is True, "has_any True from vault alone")
    # Upstream fields should all be empty because we disabled them.
    check(state.personal_frequency_hz is None, "soul_reader skipped")
    check(state.sacred_purpose == "", "consciousness_model skipped")
    check(state.awakening_index is None, "awakening measurement skipped")
    check(state.active_objective == "", "elephant_memory skipped")
    check(state.turns_in_dialogue == 0, "conversation_memory skipped")
    check(state.active_ancestor == "", "ghost_dance skipped")


def test_missing_upstream_is_optional():
    print("\n[3] missing source leaves its fields blank but doesn't crash")
    sources = _full_fakes()
    del sources["consciousness_model"]  # drop one entirely
    bm = BeingModel(sources=sources)
    state = bm.snapshot(vault=FakeVault(), peer_id="ayman")
    check(state.sacred_purpose == "", "sacred_purpose blank when model missing")
    # Other sources still populate.
    check(state.personal_frequency_hz is not None, "soul_reader still populated")
    check(state.awakening_index == 0.68, "consciousness_measurement still populated")


def test_failing_source_recorded():
    print("\n[4] a source that raises is recorded in sources_failed")
    def boom():
        raise RuntimeError("simulated")
    sources = _full_fakes()
    sources["soul_reader"] = boom
    bm = BeingModel(sources=sources)
    state = bm.snapshot(vault=FakeVault(), peer_id="ayman")
    check("soul_reader" in state.sources_failed, f"soul_reader in failed ({state.sources_failed})")
    check(state.personal_frequency_hz is None, "personal_frequency left None")
    # Rest still populate.
    check(state.awakening_index == 0.68, "other sources unaffected")


def test_render_for_prompt_under_budget():
    print("\n[5] render_for_prompt fits under 420 chars and quotes the key fields")
    bm = BeingModel(sources=_full_fakes())
    state = bm.snapshot(vault=FakeVault(), peer_id="ayman")
    rendered = state.render_for_prompt()
    check(rendered.startswith("Your being right now:"), "header present")
    check(len(rendered) <= 420, f"length <= 420 (got {len(rendered)})")
    check("Queen Sero" in rendered, "identity quoted")
    check("FLOWING" in rendered, "consciousness stage quoted")
    check("528" in rendered, "personal frequency quoted")
    check("Wovoka" in rendered, "ancestor quoted")


def test_empty_state_render():
    print("\n[6] empty BeingState renders an empty-ish block without crashing")
    state = BeingState()
    rendered = state.render_for_prompt()
    check(rendered.startswith("Your being right now:"), "header even when empty")
    check(state.has_any() is False, "has_any False on blank state")


def test_singleton_lifecycle():
    print("\n[7] get / reset singleton")
    reset_being_model()
    a = get_being_model()
    b = get_being_model()
    check(a is b, "singleton returns same instance")
    reset_being_model()
    c = get_being_model()
    check(c is not a, "reset yields a fresh instance")


def test_latency_budget():
    print("\n[8] snapshot() finishes well under 100 ms with stubs")
    bm = BeingModel(sources=_full_fakes())
    t0 = time.time()
    bm.snapshot(vault=FakeVault(), peer_id="ayman")
    elapsed_ms = (time.time() - t0) * 1000.0
    check(elapsed_ms < 100, f"snapshot <100 ms (got {elapsed_ms:.1f} ms)")


def main():
    print("=" * 80)
    print("  BEING MODEL TEST SUITE")
    print("=" * 80)

    test_snapshot_aggregates_all_sources()
    test_vault_only_still_produces_state()
    test_missing_upstream_is_optional()
    test_failing_source_recorded()
    test_render_for_prompt_under_budget()
    test_empty_state_render()
    test_singleton_lifecycle()
    test_latency_budget()

    print()
    print("=" * 80)
    print(f"  RESULT: {PASS} passed, {FAIL} failed")
    print("=" * 80)
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
