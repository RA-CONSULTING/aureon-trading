#!/usr/bin/env python3
"""
AUREON MEGA TEST — 1000 SELF-AUTHORED LLM CAPABILITIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1000× expansion of the capability space.

  100 variants per family × 10 families = 1000 distinct LLM capabilities
  plus 20 L0 atomics + meta-compositions = 1020+ skills in the library

Each of the 1000 capabilities is a real parametric Python function,
authored through the CodeArchitect's 3-gate validator and executable
via the compile-cache executor.

Six phases:
  1. Bootstrap L0 atomics
  2. Author 1000 LLM capabilities (10 families × 100 variants)
  3. Exercise all 1000
  4. 100-agent parallel swarm
  5. 20-step cross-family compose pipeline
  6. Meta-cognition at scale: invoke meta on 100 random skills

Usage:
  python tests/mega/build_1000_capabilities.py
"""

from __future__ import annotations

import argparse
import logging
import os
import random
import sys
import tempfile
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

logging.basicConfig(level=logging.ERROR, format="%(levelname)s %(name)s %(message)s")

from aureon.autonomous.vm_control import VMControlDispatcher
from aureon.code_architect import (
    CodeArchitect,
    SkillLibrary,
    SkillLevel,
    SkillProposal,
    SkillStatus,
)


BANNER_WIDTH = 100


def banner(text: str, fill: str = "═") -> None:
    print()
    print(fill * BANNER_WIDTH)
    print(f"  {text}")
    print(fill * BANNER_WIDTH)


def info(text: str) -> None:
    print(f"        {text}")


# ─────────────────────────────────────────────────────────────────────────────
# 1000 capability generators — parametric by variant index 0..99
# ─────────────────────────────────────────────────────────────────────────────

VARIANT_COUNT = 100  # variants per family


def _name(family: str, idx: int) -> str:
    return f"{family}_{idx:03d}"


def gen_prompt_family() -> List[Tuple[str, str, SkillLevel, List[str], str]]:
    out = []
    for i in range(VARIANT_COUNT):
        full = _name("prompt", i)
        # Spread token budgets across the variants
        max_toks = 80 + (i * 10)  # 80..1080
        code = f'''
def {full}(query="", context=None, **kwargs):
    """Prompt variant {i}: max_tokens={max_toks}"""
    emit_event("cap.prompt.{i:03d}", {{"q": str(query)[:80]}})
    r = ai_reason(
        "[variant={i}] " + str(query),
        context=context,
        max_tokens={max_toks},
    )
    return {{
        "ok": r.get("ok", False),
        "variant": {i},
        "text": r.get("text", ""),
        "max_tokens": {max_toks},
    }}
'''
        out.append((full, code, SkillLevel.TASK, [], f"Prompt variant {i}"))
    return out


def gen_reasoning_family() -> List[Tuple[str, str, SkillLevel, List[str], str]]:
    out = []
    for i in range(VARIANT_COUNT):
        full = _name("reason", i)
        depth = (i % 10) + 1  # 1..10
        code = f'''
def {full}(query="", **kwargs):
    """Reasoning variant {i}: depth={depth}"""
    chain = []
    prior = ""
    j = 0
    while j < {depth}:
        r = ai_reason(
            "Step " + str(j + 1) + " of {depth} [v={i}]: " + str(query),
            context={{"step": j + 1, "prior": str(prior)[:200]}},
            max_tokens=180,
        )
        chain.append(r)
        prior = str(prior) + " | " + str(r.get("text", ""))[:120]
        j = j + 1
    return {{
        "ok": all(c.get("ok", False) for c in chain),
        "variant": {i},
        "depth": {depth},
        "steps": len(chain),
        "final_answer": str(prior)[:500],
    }}
'''
        out.append((full, code, SkillLevel.WORKFLOW, [], f"Reasoning variant {i}"))
    return out


def gen_planning_family() -> List[Tuple[str, str, SkillLevel, List[str], str]]:
    out = []
    for i in range(VARIANT_COUNT):
        full = _name("plan", i)
        n_steps = (i % 10) + 3  # 3..12
        code = f'''
def {full}(goal="", **kwargs):
    """Planning variant {i}: n_steps={n_steps}"""
    emit_event("cap.plan.{i:03d}", {{"goal": str(goal)[:80]}})
    r = ai_reason(
        "Decompose into {n_steps} steps [v={i}]: " + str(goal),
        context={{"variant": {i}, "n_steps": {n_steps}}},
        max_tokens=400,
    )
    text = r.get("text", "") or ""
    lines = [ln.strip() for ln in text.split("\\n") if ln.strip()]
    sub_goals = lines[:{n_steps}] if lines else ["analyse", "act", "verify"]
    return {{
        "ok": r.get("ok", False),
        "variant": {i},
        "goal": goal,
        "sub_goals": sub_goals,
        "count": len(sub_goals),
    }}
'''
        out.append((full, code, SkillLevel.TASK, [], f"Planning variant {i}"))
    return out


def gen_reflection_family() -> List[Tuple[str, str, SkillLevel, List[str], str]]:
    out = []
    for i in range(VARIANT_COUNT):
        full = _name("reflection", i)
        code = f'''
def {full}(subject="", last_result=None, **kwargs):
    """Reflection variant {i}"""
    r = consult_queen(
        "Reflection[{i}] on: " + str(subject) + " | prior: " + str(last_result)[:200],
        context={{"variant": {i}}},
    )
    return {{
        "ok": r.get("ok", False),
        "variant": {i},
        "text": r.get("text", "")[:300],
    }}
'''
        out.append((full, code, SkillLevel.TASK, [], f"Reflection variant {i}"))
    return out


def gen_tool_use_family() -> List[Tuple[str, str, SkillLevel, List[str], str]]:
    primitives = [
        ("screenshot",   "vm_screenshot",         "{}"),
        ("mouse",        "vm_mouse_move",         '{"x": 500, "y": 300}'),
        ("click",        "vm_left_click",         '{"x": 500, "y": 300}'),
        ("right_click",  "vm_right_click",        "{}"),
        ("dbl_click",    "vm_double_click",       '{"x": 400, "y": 400}'),
        ("type",         "vm_type_text",          '{"text": "hello"}'),
        ("key",          "vm_press_key",          '{"key": "enter"}'),
        ("hotkey",       "vm_hotkey",             '{"keys": ["ctrl", "c"]}'),
        ("scroll",       "vm_scroll",             '{"x": 500, "y": 500, "direction": "down"}'),
        ("list_windows", "vm_list_windows",       "{}"),
    ]
    out = []
    for i in range(VARIANT_COUNT):
        full = _name("tool", i)
        prim_name, prim_fn, args = primitives[i % len(primitives)]
        code = f'''
def {full}(**kwargs):
    """Tool variant {i}: {prim_name} ({prim_fn})"""
    result = {prim_fn}(**{args})
    return {{
        "ok": result.get("ok", False),
        "variant": {i},
        "tool": "{prim_fn}",
    }}
'''
        out.append((full, code, SkillLevel.TASK, [], f"Tool variant {i}"))
    return out


def gen_code_gen_family() -> List[Tuple[str, str, SkillLevel, List[str], str]]:
    styles = [
        "function", "class", "test", "refactor", "debug",
        "document", "explain", "review", "optimize", "type_hints",
    ]
    out = []
    for i in range(VARIANT_COUNT):
        full = _name("code", i)
        style = styles[i % len(styles)]
        code = f'''
def {full}(spec="", **kwargs):
    """Code-gen variant {i}: style={style}"""
    r = ai_reason(
        "[{style} v{i}] " + str(spec),
        context={{"variant": {i}, "style": "{style}"}},
        max_tokens=500,
    )
    return {{
        "ok": r.get("ok", False),
        "variant": {i},
        "style": "{style}",
        "draft": str(r.get("text", ""))[:400],
    }}
'''
        out.append((full, code, SkillLevel.TASK, [], f"Code gen variant {i}"))
    return out


def gen_recovery_family() -> List[Tuple[str, str, SkillLevel, List[str], str]]:
    strategies = [
        "retry", "rollback", "fallback", "escalate", "alert",
        "circuit_break", "degrade", "restart", "heal", "reroute",
    ]
    out = []
    for i in range(VARIANT_COUNT):
        full = _name("recovery", i)
        strat = strategies[i % len(strategies)]
        code = f'''
def {full}(failed_skill="", last_error="", **kwargs):
    """Recovery variant {i}: strategy={strat}"""
    r = consult_queen(
        "Apply {strat} strategy [v{i}] to: " + str(failed_skill) + " | error: " + str(last_error),
        context={{"variant": {i}, "strategy": "{strat}"}},
    )
    return {{
        "ok": r.get("ok", False),
        "variant": {i},
        "strategy": "{strat}",
        "plan": r.get("text", "")[:300],
    }}
'''
        out.append((full, code, SkillLevel.TASK, [], f"Recovery variant {i}"))
    return out


def gen_delegation_family() -> List[Tuple[str, str, SkillLevel, List[str], str]]:
    algos = [
        "direct", "best_match", "random", "weighted", "chain",
        "parallel", "sequential", "race", "consensus", "vote",
    ]
    out = []
    for i in range(VARIANT_COUNT):
        full = _name("delegate", i)
        algo = algos[i % len(algos)]
        code = f'''
def {full}(skill_name="", **kwargs):
    """Delegation variant {i}: algo={algo}"""
    available = list_skills()
    names = available.get("skills", [])
    target = str(skill_name) if skill_name and skill_name in names else ""
    if target:
        result = call_skill(target)
        return {{
            "ok": result.get("ok", False),
            "variant": {i},
            "algo": "{algo}",
            "delegated_to": target,
        }}
    return {{
        "ok": True,
        "variant": {i},
        "algo": "{algo}",
        "library_size": len(names),
    }}
'''
        out.append((full, code, SkillLevel.TASK, [], f"Delegation variant {i}"))
    return out


def gen_memory_family() -> List[Tuple[str, str, SkillLevel, List[str], str]]:
    ops = [
        "remember", "recall", "index", "search", "summarise",
        "compress", "expand", "prune", "audit", "list",
    ]
    out = []
    for i in range(VARIANT_COUNT):
        full = _name("memory", i)
        op = ops[i % len(ops)]
        code = f'''
def {full}(target="mem_default", key="k", value="v", **kwargs):
    """Memory variant {i}: op={op}"""
    op = "{op}"
    if op in ("remember", "index"):
        r = remember(str(target), str(key), str(value))
        return {{"ok": r.get("ok", False), "variant": {i}, "op": op}}
    if op in ("recall", "search"):
        r = recall(str(target), str(key))
        return {{"ok": r.get("ok", False), "variant": {i}, "op": op, "value": r.get("value")}}
    available = list_skills()
    return {{
        "ok": available.get("ok", False),
        "variant": {i},
        "op": op,
        "count": available.get("count", 0),
    }}
'''
        out.append((full, code, SkillLevel.TASK, [], f"Memory variant {i}"))
    return out


def gen_meta_family() -> List[Tuple[str, str, SkillLevel, List[str], str]]:
    operations = [
        "improve", "learn", "compose", "decompose", "abstract",
        "instantiate", "audit", "reflect", "plan", "execute",
    ]
    out = []
    for i in range(VARIANT_COUNT):
        full = _name("meta", i)
        op = operations[i % len(operations)]
        code = f'''
def {full}(target="", **kwargs):
    """Meta variant {i}: operation={op}"""
    emit_event("cap.meta.{i:03d}", {{"target": str(target)[:80]}})
    r = consult_queen(
        "Meta[{op}] on: " + str(target) + " (v{i})",
        context={{"variant": {i}, "op": "{op}"}},
    )
    available = list_skills()
    return {{
        "ok": r.get("ok", False),
        "variant": {i},
        "op": "{op}",
        "insight": r.get("text", "")[:250],
        "library_size": available.get("count", 0),
    }}
'''
        out.append((full, code, SkillLevel.ROLE, [], f"Meta variant {i}"))
    return out


FAMILIES: Dict[str, Callable[[], List[Tuple[str, str, SkillLevel, List[str], str]]]] = {
    "prompt":     gen_prompt_family,
    "reasoning":  gen_reasoning_family,
    "planning":   gen_planning_family,
    "reflection": gen_reflection_family,
    "tool_use":   gen_tool_use_family,
    "code_gen":   gen_code_gen_family,
    "recovery":   gen_recovery_family,
    "delegation": gen_delegation_family,
    "memory":     gen_memory_family,
    "meta":       gen_meta_family,
}


# ─────────────────────────────────────────────────────────────────────────────
# Harness
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class MegaHarness:
    tmp: Path
    dispatcher: VMControlDispatcher = field(default=None)
    lib: SkillLibrary = field(default=None)
    architect: CodeArchitect = field(default=None)
    authored: List[str] = field(default_factory=list)
    blocked: List[Tuple[str, str]] = field(default_factory=list)

    @classmethod
    def build(cls) -> "MegaHarness":
        tmp = Path(tempfile.mkdtemp(prefix="aureon_mega_"))
        h = cls(tmp=tmp)
        h.dispatcher = VMControlDispatcher()
        sid = h.dispatcher.create_session(backend="simulated", name="mega-vm", make_default=True)
        h.dispatcher.get_session(sid).arm(dry_run=False)
        h.lib = SkillLibrary(storage_dir=h.tmp)
        h.architect = CodeArchitect(library=h.lib, dispatcher=h.dispatcher)
        return h

    def teardown(self) -> None:
        try:
            self.dispatcher.destroy_all()
        except Exception:
            pass
        shutil.rmtree(self.tmp, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# Phases
# ─────────────────────────────────────────────────────────────────────────────


def phase_1_bootstrap(h: MegaHarness) -> Dict[str, Any]:
    banner("MEGA PHASE 1 — Bootstrap L0 atomic primitives")
    atomics = h.architect.bootstrap_atomics()
    info(f"Seeded {len(atomics)} atomic skills")
    return {"phase": 1, "atomics": len(atomics), "ok": len(atomics) >= 15}


def phase_2_author_1000(h: MegaHarness) -> Dict[str, Any]:
    banner("MEGA PHASE 2 — Author 1000 LLM capability skills (10 families × 100 variants)")

    total_authored = 0
    total_blocked = 0
    per_family: Dict[str, Dict[str, int]] = {}
    start = time.time()

    for family_name, generator in FAMILIES.items():
        specs = generator()
        fam_ok = 0
        fam_fail = 0

        for full_name, code, level, deps, desc in specs:
            proposal = SkillProposal(
                name=full_name,
                description=desc,
                level=level,
                category=f"mega_{family_name}",
                code=code.strip(),
                entry_function=full_name,
                params_schema={"type": "object", "properties": {}},
                dependencies=deps,
                reasoning=f"Mega test {family_name} variant",
                target="either",
            )
            skill = h.architect._store_if_valid(proposal)
            if skill is None or skill.status == SkillStatus.BLOCKED:
                stored = h.lib.get(full_name)
                err_msg = stored.last_error if stored else "unknown"
                h.blocked.append((full_name, err_msg))
                fam_fail += 1
                total_blocked += 1
            else:
                h.authored.append(full_name)
                fam_ok += 1
                total_authored += 1

        per_family[family_name] = {"ok": fam_ok, "fail": fam_fail}
        marker = "OK" if fam_fail == 0 else "PARTIAL"
        info(f"  {marker:8s} {family_name:12s}  {fam_ok:3d}/{fam_ok + fam_fail} authored")

    duration = time.time() - start
    info(f"Total: {total_authored}/{total_authored + total_blocked} authored in {duration:.2f}s "
         f"({total_authored / max(duration, 0.001):.0f} skills/s)")

    if h.blocked:
        info(f"First few blocked: {[name for name, _ in h.blocked[:5]]}")

    return {
        "phase": 2,
        "total_authored": total_authored,
        "total_blocked": total_blocked,
        "expected": VARIANT_COUNT * len(FAMILIES),
        "authoring_duration_s": round(duration, 2),
        "authoring_rate": round(total_authored / max(duration, 0.001), 2),
        "ok": total_authored == VARIANT_COUNT * len(FAMILIES),
    }


def phase_3_exercise_1000(h: MegaHarness) -> Dict[str, Any]:
    banner("MEGA PHASE 3 — Exercise all 1000 authored capabilities")

    test_params = {
        "prompt":     {"query": "What is coherence?"},
        "reason":     {"query": "Should we deploy?"},
        "plan":       {"goal": "Ship a new feature"},
        "reflection": {"subject": "today", "last_result": "mixed"},
        "tool":       {},
        "code":       {"spec": "sum two numbers"},
        "recovery":   {"failed_skill": "deploy", "last_error": "timeout"},
        "delegate":   {"skill_name": "screenshot"},
        "memory":     {"target": "mega_mem", "key": "k", "value": "v"},
        "meta":       {"target": "prompt_000"},
    }

    successes = 0
    failures = 0
    per_family: Dict[str, Dict[str, int]] = {}
    start = time.time()

    for name in h.authored:
        family = name.split("_")[0]
        params = test_params.get(family, {})

        r = h.architect.execute_skill(name, params=params)
        inner = r.return_value if isinstance(r.return_value, dict) else {}
        inner_ok = bool(r.ok and inner.get("ok", False))

        per_family.setdefault(family, {"ok": 0, "fail": 0})
        if inner_ok:
            successes += 1
            per_family[family]["ok"] += 1
        else:
            failures += 1
            per_family[family]["fail"] += 1

    duration = time.time() - start

    for family, stats in sorted(per_family.items()):
        total = stats["ok"] + stats["fail"]
        marker = "OK" if stats["fail"] == 0 else "PARTIAL"
        info(f"  {marker:8s} {family:12s}  {stats['ok']:3d}/{total} executed ok")

    info(f"Total: {successes}/{len(h.authored)} in {duration:.2f}s "
         f"({successes / max(duration, 0.001):.0f} executions/s)")

    return {
        "phase": 3,
        "total_executed": len(h.authored),
        "successes": successes,
        "failures": failures,
        "exec_duration_s": round(duration, 2),
        "exec_rate": round(successes / max(duration, 0.001), 2),
        "per_family": per_family,
        "ok": successes >= len(h.authored) * 0.98,
    }


def phase_4_parallel_100(h: MegaHarness) -> Dict[str, Any]:
    banner("MEGA PHASE 4 — 100-agent parallel swarm")

    if not h.authored:
        return {"phase": 4, "ok": False, "error": "no_capabilities"}

    selected = random.sample(h.authored, min(100, len(h.authored)))

    successes = 0
    failures = 0
    durations: List[float] = []
    lock = threading.Lock()

    params_map = {
        "prompt":     {"query": "bench"},
        "reason":     {"query": "bench"},
        "plan":       {"goal": "bench"},
        "reflection": {"subject": "bench", "last_result": "bench"},
        "tool":       {},
        "code":       {"spec": "bench"},
        "recovery":   {"failed_skill": "bench", "last_error": "bench"},
        "delegate":   {"skill_name": "screenshot"},
        "memory":     {"target": "bench", "key": "k", "value": "v"},
        "meta":       {"target": "bench"},
    }

    def run_one(skill_name: str):
        nonlocal successes, failures
        family = skill_name.split("_")[0]
        params = params_map.get(family, {})
        t0 = time.time()
        r = h.architect.execute_skill(skill_name, params=params)
        dt = time.time() - t0
        inner = r.return_value if isinstance(r.return_value, dict) else {}
        inner_ok = bool(r.ok and inner.get("ok", False))
        with lock:
            if inner_ok:
                successes += 1
            else:
                failures += 1
            durations.append(dt)

    start = time.time()
    with ThreadPoolExecutor(max_workers=100) as ex:
        futures = [ex.submit(run_one, name) for name in selected]
        for f in as_completed(futures):
            pass
    total_duration = time.time() - start

    durations_sorted = sorted(durations)
    p50 = durations_sorted[len(durations_sorted) // 2] * 1000 if durations_sorted else 0
    p99 = durations_sorted[int(len(durations_sorted) * 0.99)] * 1000 if len(durations_sorted) > 1 else 0

    info(f"100 parallel runs completed in {total_duration:.2f}s")
    info(f"  successes={successes}  failures={failures}")
    info(f"  p50 latency: {p50:.2f} ms")
    info(f"  p99 latency: {p99:.2f} ms")

    return {
        "phase": 4,
        "parallel_agents": 100,
        "successes": successes,
        "failures": failures,
        "p50_ms": round(p50, 2),
        "p99_ms": round(p99, 2),
        "total_duration_s": round(total_duration, 2),
        "ok": failures <= 5,  # allow tiny noise at 100-agent scale
    }


def phase_5_compose_pipeline(h: MegaHarness) -> Dict[str, Any]:
    banner("MEGA PHASE 5 — Compose 20-step cross-family pipeline")

    pipeline = [
        ("prompt_000",     {"query": "State"}),
        ("prompt_050",     {"query": "Price"}),
        ("reason_005",     {"query": "Deploy?"}),
        ("reason_050",     {"query": "Hold?"}),
        ("plan_010",       {"goal": "Launch"}),
        ("plan_050",       {"goal": "Scale"}),
        ("reflection_005", {"subject": "plan", "last_result": "ok"}),
        ("reflection_050", {"subject": "ops", "last_result": "mixed"}),
        ("tool_000",       {}),
        ("tool_025",       {}),
        ("tool_050",       {}),
        ("code_010",       {"spec": "hash string"}),
        ("code_050",       {"spec": "parse json"}),
        ("recovery_003",   {"failed_skill": "x", "last_error": "timeout"}),
        ("recovery_050",   {"failed_skill": "y", "last_error": "oom"}),
        ("delegate_010",   {"skill_name": "screenshot"}),
        ("memory_000",     {"target": "pipeline", "key": "step", "value": "16"}),
        ("memory_001",     {"target": "pipeline", "key": "step"}),
        ("meta_003",       {"target": "pipeline"}),
        ("meta_050",       {"target": "pipeline"}),
    ]

    ok_count = 0
    fail_count = 0
    for name, params in pipeline:
        if not h.lib.contains(name):
            fail_count += 1
            info(f"  [!!] {name:22s} missing")
            continue
        r = h.architect.execute_skill(name, params=params)
        inner = r.return_value if isinstance(r.return_value, dict) else {}
        inner_ok = bool(r.ok and inner.get("ok", False))
        marker = "OK" if inner_ok else "!!"
        info(f"  [{marker}] {name:22s} variant={inner.get('variant', '?')}")
        if inner_ok:
            ok_count += 1
        else:
            fail_count += 1

    return {
        "phase": 5,
        "steps": len(pipeline),
        "successes": ok_count,
        "failures": fail_count,
        "ok": fail_count == 0,
    }


def phase_6_meta_at_scale(h: MegaHarness) -> Dict[str, Any]:
    banner("MEGA PHASE 6 — Meta-cognition at scale (invoke meta family on 100 random targets)")

    if not h.authored:
        return {"phase": 6, "ok": False}

    meta_skills = [n for n in h.authored if n.startswith("meta_")]
    non_meta = [n for n in h.authored if not n.startswith("meta_")]
    targets = random.sample(non_meta, min(100, len(non_meta)))

    successes = 0
    failures = 0
    start = time.time()

    for target in targets:
        # Pick a random meta variant
        meta_name = random.choice(meta_skills)
        r = h.architect.execute_skill(meta_name, params={"target": target})
        inner = r.return_value if isinstance(r.return_value, dict) else {}
        if r.ok and inner.get("ok", False):
            successes += 1
        else:
            failures += 1

    duration = time.time() - start
    info(f"  meta invocations: {successes}/{len(targets)} ok in {duration:.2f}s")

    return {
        "phase": 6,
        "meta_invocations": len(targets),
        "successes": successes,
        "failures": failures,
        "duration_s": round(duration, 2),
        "ok": successes >= len(targets) * 0.95,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Aureon Mega Test — 1000 capabilities")
    _ = parser.parse_args()

    banner("AUREON MEGA TEST — 1000 SELF-AUTHORED LLM CAPABILITIES", fill="█")
    print()
    info("Objective: 10 families × 100 variants = 1000 LLM capability skills")
    info("Each skill is authored, validated, stored, compiled, and executed")
    info("through the in-house CodeArchitect pipeline. Zero external LLM.")
    print()

    h = MegaHarness.build()
    all_results: List[Dict[str, Any]] = []
    overall_start = time.time()

    try:
        all_results.append(phase_1_bootstrap(h))
        all_results.append(phase_2_author_1000(h))
        all_results.append(phase_3_exercise_1000(h))
        all_results.append(phase_4_parallel_100(h))
        all_results.append(phase_5_compose_pipeline(h))
        all_results.append(phase_6_meta_at_scale(h))
    finally:
        lib_stats = h.lib.get_stats()
        h.teardown()

    overall_duration = time.time() - overall_start

    banner("MEGA REPORT", fill="█")
    passed = sum(1 for r in all_results if r.get("ok"))
    total = len(all_results)

    for r in all_results:
        flag = "[PASS]" if r.get("ok") else "[FAIL]"
        parts = []
        for k, v in r.items():
            if k in ("ok", "phase", "per_family"):
                continue
            if isinstance(v, (dict, list)):
                parts.append(f"{k}={len(v)}")
            else:
                parts.append(f"{k}={v}")
        print(f"  {flag}  Phase {r['phase']}: {', '.join(parts)[:180]}")

    print()
    print(f"  Skill library: {lib_stats['total_skills']} skills "
          f"({lib_stats.get('by_status', {}).get('validated', 0)} validated)")
    print(f"    by_level: {lib_stats.get('by_level', {})}")
    print(f"  Total mega test duration: {overall_duration:.2f}s")
    print()
    print(f"  RESULT: {passed}/{total} phases passed")
    print()
    print("█" * BANNER_WIDTH)

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
