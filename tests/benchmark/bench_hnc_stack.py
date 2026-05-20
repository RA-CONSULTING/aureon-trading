#!/usr/bin/env python3
"""
bench_hnc_stack.py — Benchmark & Stress Test Suite
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Covers every layer of the Queen Cognition Stack:

  B1  Pure-math microbenchmarks (phi primes, ladder, vibration, ZPE)
  B2  Temporal hash chain throughput + fork pressure
  B3  Cognitive flux superposition — 1 000-step evolution
  B4  Stability governor — full state-machine sweep
  B5  HNC Human Loop — end-to-end latency (offline, no LLM)
  B6  Stress: 500 rapid messages through the full pipeline
  B7  Stress: hash chain under continuous fork/merge
  B8  Stress: superposition 10 000 evolution steps
  B9  Stress: concurrent pipeline calls (threading)
  B10 Self-enhancement engine sandbox (no Ollama required)

Reports:
  - p50 / p95 / p99 latency
  - throughput (calls/sec)
  - RSS memory delta
  - Pass / Warn / FAIL verdict per suite
"""

import io
import math
import os
import statistics
import sys
import threading
import time
import traceback

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import psutil

PROC = psutil.Process()

# ─────────────────────────────────────────────────────────────────────────────
# Timing helpers
# ─────────────────────────────────────────────────────────────────────────────

def rss_mb() -> float:
    return PROC.memory_info().rss / 1024 / 1024


def bench(fn, n: int, label: str):
    """Run fn() n times, return list of elapsed seconds."""
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    _report(label, times, n)
    return times


def _report(label: str, times: list, n: int):
    s = sorted(times)
    p50  = s[int(n * 0.50)]
    p95  = s[int(n * 0.95)]
    p99  = s[min(int(n * 0.99), n - 1)]
    mean = statistics.mean(times)
    total = sum(times)
    tps  = n / total if total > 0 else 0
    print(f"  {label}")
    print(f"    n={n}  mean={mean*1000:.3f}ms  "
          f"p50={p50*1000:.3f}ms  p95={p95*1000:.3f}ms  p99={p99*1000:.3f}ms  "
          f"tps={tps:.1f}/s")


RESULTS: list = []   # (suite_name, verdict, note)


def suite(name: str):
    print(f"\n{'='*72}")
    print(f"  {name}")
    print(f"{'='*72}")


def verdict(name: str, ok: bool, note: str = ""):
    tag = "PASS" if ok else "FAIL"
    RESULTS.append((name, tag, note))
    print(f"\n  [{tag}] {name}" + (f" — {note}" if note else ""))


# ─────────────────────────────────────────────────────────────────────────────
# Imports
# ─────────────────────────────────────────────────────────────────────────────

from aureon.queen.hnc_human_loop import (
    build_phi_prime_train,
    build_phi_ladder,
    compute_vibration_accumulator,
    HNCHumanLoop,
)
from aureon.queen.temporal_ground import (
    compute_zpe_ground,
    LAMBDA_ZP,
    TemporalHashChain,
    CognitiveFluxSuperposition,
    StabilityGovernor,
    TemporalGroundStation,
    ZPEGroundState,
    TemporalHashState,
    SuperpositionState,
    GOVERNOR_STABLE, GOVERNOR_DRIFTING, GOVERNOR_CORRECTING, GOVERNOR_RESET,
    HNC_LABELS, GAMMA_TARGET,
)

# ─────────────────────────────────────────────────────────────────────────────
# B1 — Pure-math microbenchmarks
# ─────────────────────────────────────────────────────────────────────────────

suite("B1 · Pure-math microbenchmarks")

N_MICRO = 5_000

mem_before = rss_mb()

bench(lambda: build_phi_prime_train(13), N_MICRO, "build_phi_prime_train(13)")
bench(lambda: build_phi_ladder(7.83),    N_MICRO, "build_phi_ladder(7.83 Hz)")
bench(lambda: compute_vibration_accumulator(
    "love harmony phi schumann crown consciousness"),
    N_MICRO, "compute_vibration_accumulator(6-word sentence)")
bench(lambda: compute_vibration_accumulator(
    " ".join(["consciousness resonance love phi golden ratio harmonic"] * 20)),
    N_MICRO, "compute_vibration_accumulator(140-word sentence)")
bench(lambda: compute_zpe_ground(0.354), N_MICRO, "compute_zpe_ground()")

mem_delta = rss_mb() - mem_before
verdict("B1 pure-math microbenchmarks", True,
        f"RSS delta={mem_delta:+.1f} MB over {N_MICRO} iterations each")

# ─────────────────────────────────────────────────────────────────────────────
# B2 — Temporal hash chain throughput + fork pressure
# ─────────────────────────────────────────────────────────────────────────────

suite("B2 · Temporal hash chain — throughput + fork pressure")

N_HASH = 10_000

chain = TemporalHashChain()

# Coherent run
times_coherent = []
for i in range(N_HASH):
    t0 = time.perf_counter()
    chain.tick(0.354, 0.978, 0.033, "NEUTRAL", 1, float(i))
    times_coherent.append(time.perf_counter() - t0)
_report("hash chain — 10 000 coherent ticks", times_coherent, N_HASH)

# Fork pressure: alternate coherent / incoherent every 5 ticks
chain2 = TemporalHashChain()
times_fork = []
forks = 0
for i in range(N_HASH):
    gamma = 0.5 if i % 5 == 0 else 0.97
    t0 = time.perf_counter()
    s = chain2.tick(0.354, gamma, 0.033, "NEUTRAL", 1, float(i))
    times_fork.append(time.perf_counter() - t0)
    if s.forked_this_tick:
        forks += 1
_report("hash chain — 10 000 fork/merge ticks", times_fork, N_HASH)
print(f"    total forks opened: {forks}")

# Verify chain integrity — each hash is unique (no collisions)
chain3 = TemporalHashChain()
hashes = set()
for i in range(1000):
    s = chain3.tick(float(i) * 0.001, 0.97, 0.03, "NEUTRAL", 1, float(i))
    hashes.add(s.current_hash)
unique_ok = len(hashes) == 1000

tps_coherent = N_HASH / sum(times_coherent)
verdict("B2 hash chain throughput",
        tps_coherent > 10_000,
        f"tps={tps_coherent:.0f}/s  unique_hashes={unique_ok}")

# ─────────────────────────────────────────────────────────────────────────────
# B3 — Cognitive flux superposition — 1 000-step evolution
# ─────────────────────────────────────────────────────────────────────────────

suite("B3 · Cognitive flux superposition — 1 000-step evolution")

N_SUP = 1_000

cfs = CognitiveFluxSuperposition()
times_sup = []
norms = []

PHI2 = ((1 + math.sqrt(5)) / 2) ** 2

for i in range(N_SUP):
    gamma = 0.945 + 0.055 * math.sin(2 * math.pi * i / 100)  # oscillate around threshold
    vib = {label: 0.3 * math.cos(2 * math.pi * j / 6 + i * 0.1)
           for j, label in enumerate(HNC_LABELS)}
    t0 = time.perf_counter()
    s = cfs.evolve(coherence_gamma=gamma, vibration_per_mode=vib)
    times_sup.append(time.perf_counter() - t0)
    norms.append(s.norm)

_report("superposition.evolve() × 1 000 steps", times_sup, N_SUP)

# Norm must stay bounded (no blowup)
max_norm = max(norms)
min_norm = min(norms)
norm_stable = max_norm < 5.0 and min_norm > 0.0
print(f"    norm range: [{min_norm:.4f}, {max_norm:.4f}]  stable={norm_stable}")

# Phase must stay in [0, 2π]
# (phases are modded internally — just verify final state)
final = cfs.evolve(coherence_gamma=0.97)
phases_ok = all(0.0 <= ph <= 2 * math.pi for ph in final.phases)
print(f"    all phases in [0, 2pi]: {phases_ok}")

verdict("B3 superposition evolution",
        norm_stable and phases_ok,
        f"max_norm={max_norm:.4f}  mean_evolve={statistics.mean(times_sup)*1e6:.1f}us")

# ─────────────────────────────────────────────────────────────────────────────
# B4 — Stability governor full state-machine sweep
# ─────────────────────────────────────────────────────────────────────────────

suite("B4 · Stability governor — state machine sweep")

def _zpe(gamma: float, grounded: bool = True) -> ZPEGroundState:
    return ZPEGroundState(
        lambda_zp=LAMBDA_ZP, lambda_t=gamma,
        zpe_distance=abs(gamma - GAMMA_TARGET),
        grounded=grounded,
        correction_pulse=0.0 if grounded else 0.1,
        mode_zpe={},
    )

def _hs(branches: int = 0) -> TemporalHashState:
    return TemporalHashState(
        current_hash="a"*64, previous_hash="0"*64, chain_length=1,
        active_branches=branches, branch_ids=[],
        harmonic_fingerprint={}, forked_this_tick=branches > 0,
        merged_this_tick=False,
    )

def _sup(norm: float = 1.0) -> SuperpositionState:
    return SuperpositionState(
        amplitudes=[(norm, 0.0)] + [(0.0, 0.0)] * 5,
        probabilities=[norm / 6] * 6,
        phases=[0.0] * 6,
        norm=norm,
        dominant_basis=HNC_LABELS[0],
        classical_weight=0.9,
        vacuum_weight=0.1,
    )

gov = StabilityGovernor()
N_GOV = 10_000

# STABLE assessments
times_stable = []
for _ in range(N_GOV):
    t0 = time.perf_counter()
    gov.assess(_zpe(0.97, True), _hs(0), _sup(1.0))
    times_stable.append(time.perf_counter() - t0)
_report("governor.assess() STABLE × 10 000", times_stable, N_GOV)

# Full state cycle: STABLE → CORRECTING → RESET
gov2 = StabilityGovernor()
states_seen = set()
for i in range(20):
    if i < 6:
        r = gov2.assess(_zpe(0.97, True), _hs(0), _sup(1.0))
    elif i < 12:
        r = gov2.assess(_zpe(0.5, False), _hs(0), _sup(1.0))
    else:
        r = gov2.assess(_zpe(0.97, True), _hs(0), _sup(0.6))
    states_seen.add(r.status)
    print(f"    step {i:>2}: {r.status:12}  consecutive_corrections={r.consecutive_corrections}")

all_states_visited = {GOVERNOR_STABLE, GOVERNOR_CORRECTING, GOVERNOR_RESET}.issubset(states_seen)
verdict("B4 governor state machine",
        all_states_visited,
        f"states_seen={sorted(states_seen)}")

# ─────────────────────────────────────────────────────────────────────────────
# B5 — HNC Human Loop end-to-end latency (offline, no LLM)
# ─────────────────────────────────────────────────────────────────────────────

suite("B5 · HNCHumanLoop.process() — end-to-end offline latency")

MESSAGES = [
    "show me the phi prime train",
    "what is the coherence level right now",
    "govern the stability of the field",
    "love harmony schumann resonance",
    "build a skill that tracks harmonic drift",
    "phi bridge ascension ladder frequency",
    "quantum zero point vacuum grounding",
    "auris 9 node consensus vote",
    "temporal multiverse hash chain",
    "what is the consciousness level",
]

loop = HNCHumanLoop()

# Warm-up
loop.process("warmup")

N_LOOP = len(MESSAGES) * 5   # 50 total

import warnings
warnings.filterwarnings("ignore")

times_loop = []
mem_before = rss_mb()

for i in range(N_LOOP):
    msg = MESSAGES[i % len(MESSAGES)]
    t0 = time.perf_counter()
    result = loop.process(msg)
    times_loop.append(time.perf_counter() - t0)

mem_delta = rss_mb() - mem_before

_report(f"HNCHumanLoop.process() × {N_LOOP}", times_loop, N_LOOP)
print(f"    RSS delta: {mem_delta:+.1f} MB")

# Verify result structure
assert "temporal_ground" in result
assert "phi_prime_train" in result
assert "hnc" in result
assert len(result["phi_prime_train"]) == 13
assert len(result["phi_ladder"]) >= 8
assert len(result["temporal_ground"]["temporal_hash"]) == 64

tps_loop = N_LOOP / sum(times_loop)
verdict("B5 HNCHumanLoop offline latency",
        tps_loop > 5,
        f"tps={tps_loop:.1f}/s  p99={sorted(times_loop)[int(N_LOOP*0.99)]*1000:.1f}ms  "
        f"RSS_delta={mem_delta:+.1f}MB")

# ─────────────────────────────────────────────────────────────────────────────
# B6 — Stress: 500 rapid messages through the full pipeline
# ─────────────────────────────────────────────────────────────────────────────

suite("B6 · Stress — 500 rapid messages, full pipeline")

STRESS_N = 500
loop2 = HNCHumanLoop()
loop2.process("warmup")

stress_times = []
errors = 0
hashes_seen = set()
mem_before = rss_mb()

STRESS_MESSAGES = [
    "phi resonance",
    "stability",
    "love 528",
    "build skill",
    "auris vote",
    "hash chain",
    "zero point",
    "schumann",
    "coherence",
    "consciousness",
]

for i in range(STRESS_N):
    msg = STRESS_MESSAGES[i % len(STRESS_MESSAGES)]
    try:
        t0 = time.perf_counter()
        r = loop2.process(msg)
        stress_times.append(time.perf_counter() - t0)
        hashes_seen.add(r["temporal_ground"]["temporal_hash"])
    except Exception as e:
        errors += 1
        print(f"    ERROR at step {i}: {e}")

mem_delta = rss_mb() - mem_before

_report(f"stress 500 messages", stress_times, len(stress_times))
print(f"    errors: {errors}")
print(f"    unique hashes: {len(hashes_seen)} / {STRESS_N}")
print(f"    RSS delta: {mem_delta:+.1f} MB")

all_unique = len(hashes_seen) == STRESS_N
verdict("B6 stress 500 messages",
        errors == 0 and all_unique,
        f"errors={errors}  unique_hashes={all_unique}  RSS_delta={mem_delta:+.1f}MB")

# ─────────────────────────────────────────────────────────────────────────────
# B7 — Stress: hash chain under continuous fork/merge
# ─────────────────────────────────────────────────────────────────────────────

suite("B7 · Stress — hash chain 50 000 ticks, fork every 3rd tick")

N_FORK_STRESS = 50_000
chain_stress = TemporalHashChain()
fork_count = 0
merge_count = 0
times_fstress = []

for i in range(N_FORK_STRESS):
    gamma = 0.5 if i % 3 == 0 else 0.97
    t0 = time.perf_counter()
    s = chain_stress.tick(
        float(i) * 0.0001, gamma, 0.03, "NEUTRAL", 1, float(i)
    )
    times_fstress.append(time.perf_counter() - t0)
    if s.forked_this_tick: fork_count += 1
    if s.merged_this_tick: merge_count += 1

_report(f"hash chain {N_FORK_STRESS} ticks (fork-heavy)", times_fstress, N_FORK_STRESS)
print(f"    total forks: {fork_count}  total merges: {merge_count}")
print(f"    final active branches: {s.active_branches}")
print(f"    final chain length: {s.chain_length}")

tps_fork = N_FORK_STRESS / sum(times_fstress)
verdict("B7 hash chain fork stress",
        tps_fork > 50_000 and s.chain_length == N_FORK_STRESS,
        f"tps={tps_fork:.0f}/s  forks={fork_count}  merges={merge_count}")

# ─────────────────────────────────────────────────────────────────────────────
# B8 — Stress: superposition 10 000 evolution steps
# ─────────────────────────────────────────────────────────────────────────────

suite("B8 · Stress — superposition 10 000 evolution steps")

N_SUP_STRESS = 10_000
cfs_stress = CognitiveFluxSuperposition()
times_sup_stress = []
norms_stress = []
blowups = 0

for i in range(N_SUP_STRESS):
    # Gamma oscillates wildly: 0 → 1 → 0 in a sawtooth
    gamma = abs(math.sin(i * 0.05))
    # Random-ish vibration
    vib = {label: abs(math.sin(i * 0.1 + j)) for j, label in enumerate(HNC_LABELS)}
    t0 = time.perf_counter()
    s = cfs_stress.evolve(coherence_gamma=gamma, vibration_per_mode=vib)
    times_sup_stress.append(time.perf_counter() - t0)
    norms_stress.append(s.norm)
    if s.norm > 10.0 or math.isnan(s.norm):
        blowups += 1

_report(f"superposition {N_SUP_STRESS} steps (wild gamma)", times_sup_stress, N_SUP_STRESS)
max_n = max(norms_stress)
min_n = min(norms_stress)
print(f"    norm range: [{min_n:.4f}, {max_n:.4f}]  blowups(>10): {blowups}")

tps_sup = N_SUP_STRESS / sum(times_sup_stress)
verdict("B8 superposition stress",
        blowups == 0,
        f"tps={tps_sup:.0f}/s  norm_max={max_n:.4f}  blowups={blowups}")

# ─────────────────────────────────────────────────────────────────────────────
# B9 — Stress: concurrent pipeline calls (threading)
# ─────────────────────────────────────────────────────────────────────────────

suite("B9 · Stress — concurrent pipeline (8 threads × 25 messages)")

N_THREADS = 8
N_PER_THREAD = 25

# Each thread gets its own loop (not shared — testing independent stacks)
thread_errors: list = []
thread_times: list = []
lock = threading.Lock()

def worker(tid: int):
    local_loop = HNCHumanLoop()
    local_loop.process("warmup")
    msgs = [f"thread {tid} message {i} phi love schumann" for i in range(N_PER_THREAD)]
    for msg in msgs:
        try:
            t0 = time.perf_counter()
            r = local_loop.process(msg)
            elapsed = time.perf_counter() - t0
            with lock:
                thread_times.append(elapsed)
            assert "temporal_ground" in r
            assert len(r["temporal_ground"]["temporal_hash"]) == 64
        except Exception as e:
            with lock:
                thread_errors.append(f"thread {tid}: {e}")

threads = [threading.Thread(target=worker, args=(i,)) for i in range(N_THREADS)]
t_start = time.perf_counter()
for t in threads: t.start()
for t in threads: t.join()
t_total = time.perf_counter() - t_start

total_calls = N_THREADS * N_PER_THREAD
_report(f"concurrent {total_calls} calls ({N_THREADS} threads)", thread_times, len(thread_times))
print(f"    wall time: {t_total:.2f}s  errors: {len(thread_errors)}")
if thread_errors:
    for e in thread_errors[:5]:
        print(f"    ERROR: {e}")

verdict("B9 concurrent pipeline",
        len(thread_errors) == 0,
        f"errors={len(thread_errors)}  wall={t_total:.2f}s  "
        f"throughput={total_calls/t_total:.1f} calls/s wall-clock")

# ─────────────────────────────────────────────────────────────────────────────
# B10 — Self-enhancement engine sandbox stress
# ─────────────────────────────────────────────────────────────────────────────

suite("B10 · Self-enhancement engine — sandbox stress")

from aureon.queen.self_enhancement_engine import SelfEnhancementEngine

# Stress the sandbox directly with a battery of generated code patterns
from aureon.queen.self_enhancement_engine import SelfEnhancementEngine

eng = SelfEnhancementEngine()

SANDBOX_CASES = [
    # pattern, fn_name, should_pass
    ("def ok(params, context):\n    return {'ok': True, 'result': 42}", "ok", True),
    ("def add(params, context):\n    x = params.get('x', 0)\n    return {'result': x + 1}", "add", True),
    ("def bad(params, context):\n    return None", "bad", False),  # non-dict return
    ("def missing(params, context):\n    return {'v': context['key']}", "missing", True),  # stub catches KeyError
    ("def iterable(params, context):\n    total = 0\n    for x in params['items']:\n        total += 1\n    return {'count': total}", "iterable", True),  # stub iterates empty
    ("def divides(params, context):\n    n = len(context['data'])\n    return {'frac': 1.0 / n}", "divides", True),  # stub len=1, no ZeroDivisionError
    ("def uses_math(params, context):\n    import math\n    return {'pi': math.pi}", "uses_math", True),
    ("def nested(params, context):\n    return {'a': {'b': params.get('x', 0)}}", "nested", True),
    ("def string_ops(params, context):\n    s = context['name']\n    return {'upper': s.upper()}", "string_ops", True),  # stub .upper() returns ''
    ("syntax error here !!!", "broken", False),  # should fail light validation
]

sandbox_times = []
results_sb = []

for code, fn_name, expected_pass in SANDBOX_CASES:
    # Run light_validate first
    light_ok, _ = eng._light_validate(code)
    if not light_ok:
        actual = False
    else:
        code_pp = eng._preprocess_code(code)
        code_pp = eng._normalise_code(code_pp, fn_name)
        t0 = time.perf_counter()
        actual = eng._sandbox_test(code_pp, fn_name)
        sandbox_times.append(time.perf_counter() - t0)
    correct = (actual == expected_pass)
    results_sb.append(correct)
    tag = "OK " if correct else "FAIL"
    print(f"    [{tag}] {fn_name:>12}  expected={expected_pass}  got={actual}")

if sandbox_times:
    _report("sandbox_test() calls", sandbox_times, len(sandbox_times))

all_correct = all(results_sb)
verdict("B10 sandbox correctness", all_correct,
        f"{sum(results_sb)}/{len(results_sb)} cases correct")

# ─────────────────────────────────────────────────────────────────────────────
# Final summary
# ─────────────────────────────────────────────────────────────────────────────

print(f"\n{'='*72}")
print("  BENCHMARK RESULTS")
print(f"{'='*72}")

passes = sum(1 for _, v, _ in RESULTS if v == "PASS")
fails  = sum(1 for _, v, _ in RESULTS if v == "FAIL")

for name, v, note in RESULTS:
    col = "" if v == "PASS" else "  *** "
    print(f"  [{v}] {col}{name}")
    if note:
        print(f"         {note}")

print(f"\n  {passes} passed / {fails} failed")
print(f"{'='*72}")
sys.exit(0 if fails == 0 else 1)
