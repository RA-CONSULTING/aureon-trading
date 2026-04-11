"""
tests/vault/test_temporal_ground.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tests for the Temporal Ground Station:
  - Zero-Point Vacuum ground computation
  - Temporal Multiverse Hash chain + branching
  - Cognitive Flux Superposition evolution
  - Stability Governor state transitions
  - TemporalGroundStation.tick() integration
  - HNCHumanLoop includes temporal_ground key
"""

import io
import math
import sys
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

_FAILURES = []


def _run(label: str, ok: bool) -> None:
    status = "OK " if ok else "FAIL"
    print(f"  [{status}] {label}")
    if not ok:
        _FAILURES.append(label)


PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_SQUARED = PHI * PHI


# ─────────────────────────────────────────────────────────────────────────────
# Imports
# ─────────────────────────────────────────────────────────────────────────────

from aureon.queen.temporal_ground import (
    # Layer 1
    compute_zpe_ground,
    LAMBDA_ZP,
    ZPEGroundState,
    # Layer 2
    TemporalHashChain,
    TemporalHashState,
    GAMMA_TARGET,
    # Layer 3
    CognitiveFluxSuperposition,
    SuperpositionState,
    ZPE_FLOOR_EPSILON,
    # Layer 4
    StabilityGovernor,
    GOVERNOR_STABLE, GOVERNOR_DRIFTING, GOVERNOR_CORRECTING, GOVERNOR_RESET,
    # Integration
    TemporalGroundStation,
    TemporalGroundReport,
    get_temporal_ground_station,
    # Constants
    HNC_LABELS, HNC_MODES_HZ, HNC_WEIGHTS,
    PHI as TG_PHI, PHI_SQUARED as TG_PHI2, PHI_INV,
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Constants
# ─────────────────────────────────────────────────────────────────────────────

print("\n[1] Constants")
_run("PHI correct", abs(TG_PHI - PHI) < 1e-9)
_run("PHI_SQUARED correct", abs(TG_PHI2 - PHI ** 2) < 1e-9)
_run("PHI_INV = 1/PHI", abs(PHI_INV - 1.0 / PHI) < 1e-9)
_run("6 HNC modes", len(HNC_MODES_HZ) == 6)
_run("6 HNC labels", len(HNC_LABELS) == 6)
_run("weights sum to 1.0", abs(sum(HNC_WEIGHTS) - 1.0) < 1e-9)
_run("GAMMA_TARGET = 0.945", GAMMA_TARGET == 0.945)


# ─────────────────────────────────────────────────────────────────────────────
# 2. ZPE Ground (Layer 1)
# ─────────────────────────────────────────────────────────────────────────────

print("\n[2] Zero-Point Vacuum Ground")

# LAMBDA_ZP formula: sum(w * 0.5 * f/f_max)
expected_zp = sum(w * 0.5 * (f / HNC_MODES_HZ[-1])
                  for f, w in zip(HNC_MODES_HZ, HNC_WEIGHTS))
_run("LAMBDA_ZP formula correct", abs(LAMBDA_ZP - expected_zp) < 1e-9)
_run("LAMBDA_ZP in (0, 1)", 0.0 < LAMBDA_ZP < 1.0)

# Grounded case: lambda_t > LAMBDA_ZP
g = compute_zpe_ground(0.5)
_run("grounded=True when lambda_t > LAMBDA_ZP", g.grounded is True)
_run("correction_pulse=0 when grounded", g.correction_pulse == 0.0)
_run("zpe_distance = |lambda_t - LAMBDA_ZP|", abs(g.zpe_distance - abs(0.5 - LAMBDA_ZP)) < 1e-6)

# De-grounded case: lambda_t < LAMBDA_ZP
g2 = compute_zpe_ground(0.0)
_run("grounded=False when lambda_t=0", g2.grounded is False)
_run("correction_pulse > 0 when de-grounded", g2.correction_pulse > 0.0)
_run("correction_pulse = PHI_INV * (ZP - 0)", abs(g2.correction_pulse - PHI_INV * LAMBDA_ZP) < 1e-6)

# ZPE mode floors
_run("mode_zpe has 6 entries", len(g.mode_zpe) == 6)
_run("all mode_zpe labels correct", set(g.mode_zpe.keys()) == set(HNC_LABELS))
# schumann_1 has smallest ZPE floor, crown_963 has largest
_run("crown_963 ZPE > schumann_1 ZPE",
     g.mode_zpe["crown_963"] > g.mode_zpe["schumann_1"])

# to_dict
d = g.to_dict()
_run("to_dict has required keys",
     {"lambda_zp", "lambda_t", "zpe_distance", "grounded",
      "correction_pulse", "mode_zpe"}.issubset(d.keys()))


# ─────────────────────────────────────────────────────────────────────────────
# 3. Temporal Hash Chain (Layer 2)
# ─────────────────────────────────────────────────────────────────────────────

print("\n[3] Temporal Multiverse Hash Chain")

chain = TemporalHashChain()

# First tick — coherent
s1 = chain.tick(0.354, 0.978, 0.033, "NEUTRAL", 1, 1000.0)
_run("first hash is 64-char hex", len(s1.current_hash) == 64)
_run("chain_length == 1", s1.chain_length == 1)
_run("no active branches on coherent tick", s1.active_branches == 0)
_run("no fork on coherent tick", s1.forked_this_tick is False)
_run("harmonic_fingerprint has 6 entries", len(s1.harmonic_fingerprint) == 6)
_run("fingerprint values in [0, 15]",
     all(0 <= v <= 15 for v in s1.harmonic_fingerprint.values()))

# Second tick — still coherent
prev_hash = s1.current_hash
s2 = chain.tick(0.360, 0.982, 0.035, "BUY", 2, 1001.0)
_run("chain_length == 2", s2.chain_length == 2)
_run("previous_hash matches prior current_hash", s2.previous_hash == prev_hash)
_run("hash changes each tick", s2.current_hash != s1.current_hash)

# Third tick — incoherent (Gamma < 0.945 triggers fork)
s3 = chain.tick(0.200, 0.600, 0.010, "SELL", 0, 1002.0)
_run("fork opens when Gamma < 0.945", s3.forked_this_tick is True)
_run("active_branches == 1 after fork", s3.active_branches == 1)
_run("branch_ids has 1 entry", len(s3.branch_ids) == 1)

# Fourth tick — coherence recovered — fork merges
s4 = chain.tick(0.354, 0.960, 0.040, "NEUTRAL", 1, 1003.0)
_run("merged when Gamma recovers", s4.merged_this_tick is True)

# to_dict
d = s1.to_dict()
_run("to_dict has all required keys",
     {"current_hash", "previous_hash", "chain_length", "active_branches",
      "branch_ids", "harmonic_fingerprint",
      "forked_this_tick", "merged_this_tick"}.issubset(d.keys()))


# ─────────────────────────────────────────────────────────────────────────────
# 4. Cognitive Flux Superposition (Layer 3)
# ─────────────────────────────────────────────────────────────────────────────

print("\n[4] Cognitive Flux Superposition")

cfs = CognitiveFluxSuperposition()

# Evolve once at Gamma = 0.978 (high coherence)
sup1 = cfs.evolve(coherence_gamma=0.978)
_run("returns SuperpositionState", isinstance(sup1, SuperpositionState))
_run("6 amplitudes", len(sup1.amplitudes) == 6)
_run("6 probabilities", len(sup1.probabilities) == 6)
_run("6 phases", len(sup1.phases) == 6)
_run("norm > 0", sup1.norm > 0.0)
_run("dominant_basis is valid HNC label", sup1.dominant_basis in HNC_LABELS)
_run("classical_weight = Gamma", abs(sup1.classical_weight - 0.978) < 1e-4)
_run("vacuum_weight = sqrt(1-Gamma^2)",
     abs(sup1.vacuum_weight - math.sqrt(1 - 0.978 ** 2)) < 1e-4)

# All probabilities >= ZPE_FLOOR_EPSILON
_run("all probs >= ZPE_FLOOR_EPSILON",
     all(p >= ZPE_FLOOR_EPSILON for p in sup1.probabilities))

# Evolve again — phases must advance by phi^2
phases_before = list(sup1.phases)
sup2 = cfs.evolve(coherence_gamma=0.978)
for i in range(6):
    expected = (phases_before[i] + PHI_SQUARED) % (2 * math.pi)
    _run(f"  mode {i} phase advanced by phi^2",
         abs(sup2.phases[i] - expected) < 1e-9)

# Pure vacuum case (Gamma = 0)
sup_vac = cfs.evolve(coherence_gamma=0.0)
_run("gamma=0 gives classical_weight=0.0", sup_vac.classical_weight == 0.0)
_run("gamma=0 gives vacuum_weight=1.0", abs(sup_vac.vacuum_weight - 1.0) < 1e-9)
_run("gamma=0 norm > 0 (ZPE floor active)", sup_vac.norm > 0.0)

# Vibration collapse boosts resonant mode
vib = {label: (1.0 if label == "love_528" else 0.0) for label in HNC_LABELS}
cfs2 = CognitiveFluxSuperposition()
sup_base = cfs2.evolve(coherence_gamma=0.9)
sup_boosted = cfs2.evolve(coherence_gamma=0.9, vibration_per_mode=vib)
love_idx = list(HNC_LABELS).index("love_528")
_run("vibration boosts love_528 probability vs non-boosted",
     sup_boosted.probabilities[love_idx] >= sup_base.probabilities[love_idx])

# to_dict
d = sup1.to_dict()
_run("to_dict has required keys",
     {"amplitudes", "probabilities", "phases_rad",
      "norm", "dominant_basis",
      "classical_weight", "vacuum_weight"}.issubset(d.keys()))


# ─────────────────────────────────────────────────────────────────────────────
# 5. Stability Governor (Layer 4)
# ─────────────────────────────────────────────────────────────────────────────

print("\n[5] Stability Governor")


def _make_zpe(gamma: float, grounded: bool = True) -> "ZPEGroundState":
    return ZPEGroundState(
        lambda_zp=LAMBDA_ZP,
        lambda_t=gamma,
        zpe_distance=abs(gamma - GAMMA_TARGET),
        grounded=grounded,
        correction_pulse=0.0 if grounded else PHI_INV * (GAMMA_TARGET - gamma),
        mode_zpe={},
    )


def _make_hash(branches: int = 0) -> "TemporalHashState":
    return TemporalHashState(
        current_hash="a" * 64,
        previous_hash="0" * 64,
        chain_length=1,
        active_branches=branches,
        branch_ids=["x" * 8] * branches,
        harmonic_fingerprint={},
        forked_this_tick=branches > 0,
        merged_this_tick=False,
    )


def _make_sup(norm: float = 1.0) -> "SuperpositionState":
    return SuperpositionState(
        amplitudes=[(1.0, 0.0)] + [(0.0, 0.0)] * 5,
        probabilities=[norm / 6] * 6,
        phases=[0.0] * 6,
        norm=norm,
        dominant_basis=HNC_LABELS[0],
        classical_weight=0.9,
        vacuum_weight=0.1,
    )


gov = StabilityGovernor()

# STABLE: gamma >= 0.945, grounded, norm ok, no branches
r = gov.assess(_make_zpe(0.960, grounded=True), _make_hash(0), _make_sup(1.0))
_run("STABLE when gamma>=0.945, grounded, norm>=0.85", r.status == GOVERNOR_STABLE)
_run("STABLE advisory contains 'STABLE'", "STABLE" in r.advisory)
_run("correction_pulse == 0 when STABLE", r.correction_pulse == 0.0)

# CORRECTING: open branch
r2 = gov.assess(_make_zpe(0.960, grounded=True), _make_hash(1), _make_sup(1.0))
_run("CORRECTING when active branch exists", r2.status == GOVERNOR_CORRECTING)
_run("CORRECTING advisory contains 'fork'", "fork" in r2.advisory)

# CORRECTING: de-grounded
r3 = gov.assess(_make_zpe(0.800, grounded=False), _make_hash(0), _make_sup(1.0))
_run("CORRECTING when de-grounded", r3.status == GOVERNOR_CORRECTING)
_run("correction_pulse > 0 when de-grounded", r3.correction_pulse > 0.0)

# DRIFTING: low norm, no branches, grounded
r4 = gov.assess(_make_zpe(0.960, grounded=True), _make_hash(0), _make_sup(0.7))
_run("DRIFTING when norm < 0.85", r4.status == GOVERNOR_DRIFTING)

# RESET: 5 consecutive CORRECTING cycles trigger RESET on the 6th call
# (the governor increments the counter inside each CORRECTING cycle, then
#  checks >= threshold at the START of the next call)
gov2 = StabilityGovernor()
for _ in range(5):
    gov2.assess(_make_zpe(0.0, grounded=False), _make_hash(0), _make_sup(1.0))
r_reset = gov2.assess(_make_zpe(0.0, grounded=False), _make_hash(0), _make_sup(1.0))
_run("RESET after 5 consecutive CORRECTING", r_reset.status == GOVERNOR_RESET)
_run("consecutive_corrections resets to 0 after RESET",
     r_reset.consecutive_corrections == 0)

# to_dict
d = r.to_dict()
_run("GovernorReport to_dict has all keys",
     {"status", "gamma", "grounded", "superposition_norm",
      "active_branches", "correction_pulse",
      "consecutive_corrections", "advisory"}.issubset(d.keys()))


# ─────────────────────────────────────────────────────────────────────────────
# 6. TemporalGroundStation integration
# ─────────────────────────────────────────────────────────────────────────────

print("\n[6] TemporalGroundStation — full integration")

station = TemporalGroundStation()

rep = station.tick(
    lambda_t=0.354,
    coherence_gamma=0.978,
    consciousness_psi=0.033,
    auris_consensus="NEUTRAL",
    phi_resonance_count=1,
    vibration={
        "per_mode": {label: 0.5 for label in HNC_LABELS},
        "dominant_mode": "love_528",
        "total_vibration": 3.0,
    },
    timestamp=1000.0,
)

_run("returns TemporalGroundReport", isinstance(rep, TemporalGroundReport))

d = rep.to_dict()
required_top = {
    "timestamp", "temporal_hash", "chain_length", "active_branches",
    "forked", "harmonic_fingerprint", "zpe_distance", "grounded",
    "correction_pulse", "superposition", "governor_status",
    "governor_advisory", "zpe_mode_floors",
}
_run("to_dict has all top-level keys", required_top.issubset(d.keys()))
_run("temporal_hash is 64-char hex", len(d["temporal_hash"]) == 64)
_run("chain_length == 1 after first tick", d["chain_length"] == 1)
_run("superposition has norm key", "norm" in d["superposition"])
_run("governor_status is a string", isinstance(d["governor_status"], str))
_run("governor_status is valid",
     d["governor_status"] in {GOVERNOR_STABLE, GOVERNOR_DRIFTING,
                               GOVERNOR_CORRECTING, GOVERNOR_RESET})
_run("zpe_mode_floors has 6 entries", len(d["zpe_mode_floors"]) == 6)

# Second tick builds chain
rep2 = station.tick(
    lambda_t=0.360, coherence_gamma=0.982, consciousness_psi=0.035,
    auris_consensus="BUY", phi_resonance_count=2, timestamp=1001.0,
)
_run("chain_length == 2 after second tick", rep2.to_dict()["chain_length"] == 2)
_run("hash changes between ticks",
     rep2.to_dict()["temporal_hash"] != d["temporal_hash"])

# Fork: low gamma
rep3 = station.tick(
    lambda_t=0.100, coherence_gamma=0.5, consciousness_psi=0.005,
    auris_consensus="SELL", phi_resonance_count=0, timestamp=1002.0,
)
_run("fork opens on low gamma", rep3.to_dict()["forked"] is True)


# ─────────────────────────────────────────────────────────────────────────────
# 7. HNCHumanLoop includes temporal_ground
# ─────────────────────────────────────────────────────────────────────────────

print("\n[7] HNCHumanLoop.process() — temporal_ground key present")

from aureon.queen.hnc_human_loop import HNCHumanLoop

loop = HNCHumanLoop()
result = loop.process("govern the stability of the field")

_run("result has temporal_ground key", "temporal_ground" in result)
tg = result["temporal_ground"]
_run("temporal_ground is dict", isinstance(tg, dict))
_run("temporal_ground has governor_status",
     "governor_status" in tg)
_run("temporal_ground has temporal_hash",
     "temporal_hash" in tg and len(tg["temporal_hash"]) == 64)
_run("temporal_ground has superposition",
     "superposition" in tg and isinstance(tg["superposition"], dict))
_run("temporal_ground has zpe_distance", "zpe_distance" in tg)
_run("temporal_ground has grounded key", "grounded" in tg)

# Singleton
a = get_temporal_ground_station()
b = get_temporal_ground_station()
_run("singleton returns same object", a is b)


# ─────────────────────────────────────────────────────────────────────────────
# Result
# ─────────────────────────────────────────────────────────────────────────────

passed = sum(1 for _ in range(100) if True) - len(_FAILURES)
total_checks = (
    7    # constants
    + 12 # ZPE
    + 12 # hash chain
    + 14 # superposition
    + 10 # governor
    + 12 # station integration
    + 8  # loop integration
)
passed = total_checks - len(_FAILURES)

print(f"\n{'=' * 72}")
print(f"  RESULT: {passed} passed, {len(_FAILURES)} failed")
if _FAILURES:
    print("  FAILURES:")
    for f in _FAILURES:
        print(f"    - {f}")
print(f"{'=' * 72}")
sys.exit(0 if not _FAILURES else 1)
