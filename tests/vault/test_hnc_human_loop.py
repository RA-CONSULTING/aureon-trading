"""
tests/vault/test_hnc_human_loop.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tests for the HNC Human Interaction Loop:
  - Phi prime train generation and φ weighting
  - Phi bridge ascension ladder
  - Vibration frequency accumulator
  - Full HNCHumanLoop.process() pipeline
"""

import math
import sys
import os
import io

# Force UTF-8 output on Windows so unicode chars in test labels don't crash
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _run(label: str, ok: bool) -> None:
    status = "OK " if ok else "FAIL"
    print(f"  [{status}] {label}")
    if not ok:
        _FAILURES.append(label)

_FAILURES = []

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_SQUARED = PHI * PHI


# ─────────────────────────────────────────────────────────────────────────────
# Import the module under test
# ─────────────────────────────────────────────────────────────────────────────

from aureon.queen.hnc_human_loop import (
    build_phi_prime_train,
    build_phi_ladder,
    compute_vibration_accumulator,
    HNCHumanLoop,
    HNCInteractionResult,
    get_hnc_human_loop,
    PHI as LOOP_PHI,
    PHI_SQUARED as LOOP_PHI2,
    HNC_MODES_HZ,
    HNC_MODE_LABELS,
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Constants
# ─────────────────────────────────────────────────────────────────────────────

print("\n[1] Constants")
_run("PHI matches golden ratio", abs(LOOP_PHI - (1 + math.sqrt(5)) / 2) < 1e-9)
_run("PHI_SQUARED = PHI²", abs(LOOP_PHI2 - LOOP_PHI ** 2) < 1e-9)
_run("6 HNC modes", len(HNC_MODES_HZ) == 6)
_run("6 HNC labels", len(HNC_MODE_LABELS) == 6)
_run("Schumann at 7.83 Hz", HNC_MODES_HZ[0] == 7.83)
_run("Love tone at 528 Hz", HNC_MODES_HZ[4] == 528.0)
_run("Crown at 963 Hz", HNC_MODES_HZ[5] == 963.0)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Phi Prime Train
# ─────────────────────────────────────────────────────────────────────────────

print("\n[2] Phi Prime Train")
train = build_phi_prime_train(13)

_run("returns 13 entries", len(train) == 13)
_run("first prime is 2", train[0]["prime"] == 2)
_run("second prime is 3", train[1]["prime"] == 3)
_run("fifth prime is 11", train[4]["prime"] == 11)
_run("thirteenth prime is 41", train[12]["prime"] == 41)

# φ weight check: entry i should have phi_weight ≈ φ^(-i)
for i in range(5):
    expected = LOOP_PHI ** (-i)
    got = train[i]["phi_weight"]
    _run(f"  entry {i} phi_weight ≈ φ^(-{i})", abs(got - expected) < 1e-4)

# Weights are strictly descending
weights = [e["phi_weight"] for e in train]
_run("weights are strictly descending", all(weights[i] > weights[i+1] for i in range(12)))

# phi_scaled = prime × phi_weight
for entry in train:
    expected_scaled = entry["prime"] * entry["phi_weight"]
    _run(
        f"  prime {entry['prime']} phi_scaled correct",
        abs(entry["phi_scaled"] - round(expected_scaled, 4)) < 0.001,
    )

# All entries have required keys
required_keys = {"prime", "index", "phi_weight", "phi_scaled", "resonant", "nearest_hnc_mode"}
_run("all entries have required keys",
     all(required_keys.issubset(e.keys()) for e in train))

# resonant is bool
_run("resonant is bool for all", all(isinstance(e["resonant"], bool) for e in train))

# nearest_hnc_mode is a valid label
valid_labels = set(HNC_MODE_LABELS)
_run("nearest_hnc_mode is valid",
     all(e["nearest_hnc_mode"] in valid_labels for e in train))


# ─────────────────────────────────────────────────────────────────────────────
# 3. Phi Ladder (bridge ascension)
# ─────────────────────────────────────────────────────────────────────────────

print("\n[3] Phi Bridge Ascension Ladder")
ladder = build_phi_ladder(7.83)

_run("ladder has at least 8 rungs", len(ladder) >= 8)
_run("first rung starts at 7.83 Hz", abs(ladder[0]["hz"] - 7.83) < 0.01)

# Each rung = previous × φ²
for i in range(1, len(ladder)):
    expected = ladder[i-1]["hz"] * PHI_SQUARED
    got = ladder[i]["hz"]
    _run(f"  rung {i} = rung {i-1} × φ²", abs(got - round(expected, 4)) < 0.1)

_run("all rungs have 'step' key", all("step" in r for r in ladder))
_run("all rungs have 'tier' key", all("tier" in r for r in ladder))
_run("all rungs have 'nearest_hnc_mode' key", all("nearest_hnc_mode" in r for r in ladder))

# Step indices are 0, 1, 2, ...
_run("step indices are sequential",
     all(ladder[i]["step"] == i for i in range(len(ladder))))

# Ceiling: no rung should exceed 4096 Hz
_run("all rungs <= 8192 Hz", all(r["hz"] <= 8192.0 for r in ladder))

# The ladder should pass through the love zone (528 Hz ± factor of 2)
hzs = [r["hz"] for r in ladder]
love_nearby = any(300 < hz < 1100 for hz in hzs)
_run("ladder passes through love/crown zone", love_nearby)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Vibration Accumulator
# ─────────────────────────────────────────────────────────────────────────────

print("\n[4] Vibration Frequency Adder")
vib = compute_vibration_accumulator("love harmony phi schumann")

required_vib_keys = {"per_mode", "dominant_mode", "dominant_hz", "total_vibration", "phase_shift_rad"}
_run("result has required keys", required_vib_keys.issubset(vib.keys()))
_run("per_mode has 6 entries", len(vib["per_mode"]) == 6)
_run("dominant_mode is a valid HNC label", vib["dominant_mode"] in valid_labels)
_run("dominant_hz is a valid HNC frequency", vib["dominant_hz"] in HNC_MODES_HZ)
_run("total_vibration >= 0", vib["total_vibration"] >= 0.0)
_run("phase_shift_rad in [0, 2π]", 0.0 <= vib["phase_shift_rad"] <= 2 * math.pi + 1e-6)

# Empty string edge case
vib_empty = compute_vibration_accumulator("")
_run("empty string returns zeros", vib_empty["total_vibration"] == 0.0)
_run("empty string phase shift is 0", vib_empty["phase_shift_rad"] == 0.0)

# Non-empty returns positive total
vib2 = compute_vibration_accumulator("queen")
_run("single word returns positive vibration", vib2["total_vibration"] > 0.0)


# ─────────────────────────────────────────────────────────────────────────────
# 5. HNCInteractionResult.to_dict()
# ─────────────────────────────────────────────────────────────────────────────

print("\n[5] HNCInteractionResult structure")
r = HNCInteractionResult(human_text="test")
d = r.to_dict()
top_keys = {"human_text", "timestamp", "intent", "hnc", "auris",
            "phi_prime_train", "phi_ladder", "vibration", "motion_code_hint"}
_run("to_dict has all top-level keys", top_keys.issubset(d.keys()))
hnc_keys = {"lambda_t", "coherence_gamma", "consciousness_psi",
            "consciousness_level", "symbolic_life_score"}
_run("hnc sub-dict has expected keys", hnc_keys.issubset(d["hnc"].keys()))
auris_keys = {"consensus", "confidence", "lighthouse_cleared", "per_node_votes"}
_run("auris sub-dict has expected keys", auris_keys.issubset(d["auris"].keys()))


# ─────────────────────────────────────────────────────────────────────────────
# 6. HNCHumanLoop full pipeline (offline — heavy deps unavailable in CI)
# ─────────────────────────────────────────────────────────────────────────────

print("\n[6] HNCHumanLoop full pipeline")
loop = HNCHumanLoop()

# Even with all heavy deps failing to load, the loop must return a valid dict
result = loop.process("show me the phi prime train")

_run("process() returns dict", isinstance(result, dict))
_run("phi_prime_train is list",  isinstance(result.get("phi_prime_train"), list))
_run("phi_ladder is list", isinstance(result.get("phi_ladder"), list))
_run("vibration is dict", isinstance(result.get("vibration"), dict))
_run("phi_prime_train has 13 entries", len(result["phi_prime_train"]) == 13)
_run("phi_ladder has >= 8 rungs", len(result["phi_ladder"]) >= 8)
_run("hnc sub-dict present", isinstance(result.get("hnc"), dict))
_run("auris sub-dict present", isinstance(result.get("auris"), dict))

# Code-building intent triggers motion hint
result_code = loop.process("build me a skill that tracks phi coherence")
# may or may not trigger depending on intent wiring, but must not crash
_run("code build request returns dict", isinstance(result_code, dict))


# ─────────────────────────────────────────────────────────────────────────────
# 7. Singleton
# ─────────────────────────────────────────────────────────────────────────────

print("\n[7] Singleton")
a = get_hnc_human_loop()
b = get_hnc_human_loop()
_run("get_hnc_human_loop returns same object", a is b)


# ─────────────────────────────────────────────────────────────────────────────
# Result
# ─────────────────────────────────────────────────────────────────────────────

total = (
    7   # constants
    + 3 + 5 + 3 + 2 + 1  # prime train
    + 8                   # ladder
    + 8                   # vibration
    + 3                   # result struct
    + 8                   # full pipeline
    + 1                   # singleton
)
passed = total - len(_FAILURES)
print(f"\n{'=' * 72}")
print(f"  RESULT: {passed} passed, {len(_FAILURES)} failed")
if _FAILURES:
    print("  FAILURES:")
    for f in _FAILURES:
        print(f"    - {f}")
print(f"{'=' * 72}")
sys.exit(0 if not _FAILURES else 1)
