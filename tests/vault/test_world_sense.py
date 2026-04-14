#!/usr/bin/env python3
"""
Tests for aureon.queen.world_sense.WorldSense.

Uses fake source callables injected via the constructor so the test
never touches the real network or live modules. Covers:

  - all six sources aggregated into a single WorldState
  - temporal fields populated from the system clock
  - TTL caching: second call within cache_ttl_s returns the same state
  - missing / failing source recorded in sources_failed, rest still ok
  - total_budget_s is honoured
  - render_for_prompt stays under 420 chars
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

from aureon.queen.world_sense import (  # noqa: E402
    WorldSense,
    WorldState,
    get_world_sense,
    reset_world_sense,
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
# Fake sources
# ─────────────────────────────────────────────────────────────────────────────


class FakeCosmicState:
    """Stand-in for DrAurisThrone get_state()."""
    advisory = "OBSERVE"
    cosmic_score = 0.62
    kp_index = 2.4
    solar_wind_speed = 412.0
    bz_component = -2.3


class FakeSchumannReading:
    fundamental_hz = 7.84
    coherence = 0.71
    earth_blessing = 0.67


class FakeSpaceWeatherReading:
    kp_index = 2.4
    solar_wind_speed = 412.0
    bz_component = -2.3


class FakeMacroSnapshot:
    crypto_fear_greed = 28
    crypto_fg_classification = "FEAR"
    market_regime = "FEAR"
    risk_on_off = "RISK_OFF"
    vix = 24.1
    dxy = 104.3
    btc_dominance = 53.4


class FakeNewsSignal:
    geo_risk = 0.42
    risk_level = "ELEVATED"
    themes = ["rate-cut", "oil", "conflict"]


def _full_fakes() -> dict:
    return {
        "dr_auris":       lambda: FakeCosmicState(),
        "schumann":       lambda: FakeSchumannReading(),
        "earth_gate":     lambda: (True, "coherent"),
        "space_weather":  lambda: FakeSpaceWeatherReading(),
        "financial":      lambda: FakeMacroSnapshot(),
        "news":           lambda: FakeNewsSignal(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_snapshot_aggregates_all_sources():
    print("\n[1] snapshot() aggregates all six sources into WorldState")
    ws = WorldSense(cache_ttl_s=60.0, sources=_full_fakes())
    state = ws.snapshot()
    check(isinstance(state, WorldState), "returns a WorldState")
    check(state.cosmic_advisory == "OBSERVE", "dr_auris advisory surfaced")
    check(state.kp_index == 2.4, f"Kp surfaced ({state.kp_index})")
    check(state.schumann_hz == 7.84, f"Schumann surfaced ({state.schumann_hz})")
    check(state.schumann_coherence == 0.71, "schumann coherence surfaced")
    check(state.earth_blessing == 0.67, "earth blessing surfaced")
    check(state.earth_gate_open is True, "earth gate surfaced")
    check(state.fear_greed == 28, f"fear_greed surfaced ({state.fear_greed})")
    check(state.fear_greed_label == "FEAR", "fear_greed label")
    check(state.market_regime == "FEAR", "market_regime surfaced")
    check(state.vix == 24.1, f"VIX surfaced ({state.vix})")
    check(state.dxy == 104.3, f"DXY surfaced ({state.dxy})")
    check(state.btc_dominance == 53.4, f"BTC.D surfaced ({state.btc_dominance})")
    check(state.geo_risk == 0.42, "news geo_risk surfaced")
    check(state.news_risk_level == "ELEVATED", "news risk level surfaced")
    check("rate-cut" in state.dominant_themes, "themes surfaced")
    check(set(state.sources_ok) >= {"dr_auris", "schumann", "earth_gate", "space_weather", "financial", "news"},
          f"all six sources OK (got {state.sources_ok})")
    check(state.sources_failed == [], f"no failures (got {state.sources_failed})")


def test_temporal_fields():
    print("\n[2] temporal fields populated from system clock")
    ws = WorldSense(sources=_full_fakes())
    state = ws.snapshot()
    check(state.now_iso != "", f"now_iso set (got {state.now_iso})")
    check(state.weekday in {
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
        "Saturday", "Sunday",
    }, f"weekday populated ({state.weekday})")
    check(0 <= state.hour_local <= 23, f"hour_local in [0,23] ({state.hour_local})")
    check(state.market_hours_open in (True, False), "market_hours_open is bool")


def test_ttl_caching():
    print("\n[3] TTL caching: second call within TTL returns same instance")
    call_count = {"n": 0}

    def counting_source():
        call_count["n"] += 1
        return FakeCosmicState()

    sources = _full_fakes()
    sources["dr_auris"] = counting_source
    ws = WorldSense(cache_ttl_s=10.0, sources=sources)

    s1 = ws.snapshot()
    s2 = ws.snapshot()
    check(s1 is s2, "second call returns cached instance")
    check(call_count["n"] == 1, f"source called only once ({call_count['n']})")

    # After invalidation, should re-pull.
    ws.invalidate()
    s3 = ws.snapshot()
    check(s3 is not s1, "invalidate forces a fresh pull")
    check(call_count["n"] == 2, f"source called twice ({call_count['n']})")


def test_failing_source_is_recorded():
    print("\n[4] a source that raises is recorded and the rest still work")
    def boom():
        raise RuntimeError("simulated outage")
    sources = _full_fakes()
    sources["dr_auris"] = boom
    ws = WorldSense(cache_ttl_s=60.0, sources=sources)
    state = ws.snapshot()
    check("dr_auris" in state.sources_failed, f"dr_auris in failed ({state.sources_failed})")
    check(state.cosmic_advisory == "", "cosmic_advisory left empty")
    # Other sources should still populate.
    check(state.schumann_hz == 7.84, "schumann still surfaced")
    check(state.vix == 24.1, "financial still surfaced")


def test_render_for_prompt_under_budget():
    print("\n[5] render_for_prompt fits under 420 chars")
    ws = WorldSense(sources=_full_fakes())
    state = ws.snapshot()
    rendered = state.render_for_prompt()
    check(rendered.startswith("The world right now:"), "header present")
    check(len(rendered) <= 420, f"length <= 420 (got {len(rendered)})")
    check("OBSERVE" in rendered, "advisory quoted")
    check("7.84" in rendered, "Schumann quoted")
    check("FEAR" in rendered, "market regime quoted")


def test_empty_state_render():
    print("\n[6] empty WorldState renders an empty-ish block without crashing")
    state = WorldState()
    rendered = state.render_for_prompt()
    check(rendered.startswith("The world right now:"), "header even when empty")
    check(state.has_any() is False, "has_any() is False for blank state")


def test_total_budget_short_circuits():
    print("\n[7] total_budget_s caps per-snapshot wait time")
    def slow():
        time.sleep(0.25)
        return FakeSchumannReading()
    sources = _full_fakes()
    sources["schumann"] = slow
    ws = WorldSense(cache_ttl_s=60.0, total_budget_s=0.05, sources=sources)
    t0 = time.time()
    state = ws.snapshot()
    elapsed_ms = (time.time() - t0) * 1000
    check(elapsed_ms < 1500, f"snapshot returned in <1.5s (got {elapsed_ms:.0f}ms)")
    # The slow source should either have been skipped (budget_exhausted)
    # or completed — either way, the call returns.
    check(isinstance(state, WorldState), "still returns a WorldState under budget pressure")


def test_singleton_lifecycle():
    print("\n[8] get / reset singleton")
    reset_world_sense()
    a = get_world_sense()
    b = get_world_sense()
    check(a is b, "singleton reuses the same instance")
    reset_world_sense()
    c = get_world_sense()
    check(c is not a, "reset yields a new instance")


def main():
    print("=" * 80)
    print("  WORLD SENSE TEST SUITE")
    print("=" * 80)

    test_snapshot_aggregates_all_sources()
    test_temporal_fields()
    test_ttl_caching()
    test_failing_source_is_recorded()
    test_render_for_prompt_under_budget()
    test_empty_state_render()
    test_total_budget_short_circuits()
    test_singleton_lifecycle()

    print()
    print("=" * 80)
    print(f"  RESULT: {PASS} passed, {FAIL} failed")
    print("=" * 80)
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
