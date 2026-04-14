#!/usr/bin/env python3
"""
AUREON HYPER TEST — 10× EXPANDED ULTIMATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The ultimate stress test, expanded by a factor of 10 across every axis:

  LLM capabilities        10 → 100  (10 families × 10 variants each)
  Parallel agents          4 → 40
  VM sessions             10 → 100
  Library chain depth    500 → 5000
  Swarm scouts             8 → 80
  Motion snapshots       800 → 8000
  Pillar alignment      5000 → 50000
  Tool registry ops    10000 → 100000
  VM dispatch          10000 → 100000
  Soak workers             4 → 40
  Total test runs         26 → 26 scaled + this hyper test

The hyper test itself authors 100 unique LLM capability skills across
10 families, validates every one, exercises every one, and runs a
40-agent parallel swarm.

  Family             Variants
  ──────────────────────────────────────────
  prompt             10 variants
  reasoning          10 variants (chain depths 1-10)
  planning           10 variants
  reflection         10 variants
  tool_use           10 variants (one per primitive)
  code_gen           10 variants
  recovery           10 variants
  delegation         10 variants
  memory             10 variants
  meta               10 variants

Usage:
  python tests/hyper/expanded_ultimate.py
  python tests/hyper/expanded_ultimate.py --families 1,2,3  # subset
"""

from __future__ import annotations

import argparse
import logging
import os
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


# ─────────────────────────────────────────────────────────────────────────────
# Reporting
# ─────────────────────────────────────────────────────────────────────────────

BANNER_WIDTH = 96


def banner(text: str, fill: str = "═") -> None:
    print()
    print(fill * BANNER_WIDTH)
    print(f"  {text}")
    print(fill * BANNER_WIDTH)


def info(text: str) -> None:
    print(f"        {text}")


def ok(text: str) -> None:
    print(f"  [OK]  {text}")


def err(text: str) -> None:
    print(f"  [!!]  {text}")


def progress(text: str) -> None:
    print(f"  ->    {text}")


# ─────────────────────────────────────────────────────────────────────────────
# Capability source generators (one per family)
# ─────────────────────────────────────────────────────────────────────────────


def _name(family: str, variant: str) -> str:
    return f"{family}_{variant}"


def gen_prompt_family() -> List[Tuple[str, str, SkillLevel, List[str], str]]:
    """10 prompt variants: different token budgets and styles."""
    variants = [
        ("default",    400, "You are a helpful reasoning engine."),
        ("short",      100, "Be concise. One sentence max."),
        ("long",       800, "Be thorough and detailed."),
        ("structured", 400, "Return structured JSON-like output."),
        ("code",       600, "Focus on code. Produce runnable snippets."),
        ("creative",   500, "Think creatively. Offer novel angles."),
        ("technical",  600, "Be technically precise."),
        ("terse",       80, "One-word answer if possible."),
        ("verbose",   1000, "Explain every detail."),
        ("json",       400, "Respond in strict JSON only."),
    ]
    out = []
    for name, max_toks, style in variants:
        full = _name("prompt", name)
        code = f'''
def {full}(query="", context=None, **kwargs):
    """Prompt variant: {name} (max_tokens={max_toks})"""
    emit_event("cap.{full}", {{"q": str(query)[:80]}})
    result = ai_reason(
        "{style} " + str(query),
        context=context,
        max_tokens={max_toks},
    )
    return {{
        "ok": result.get("ok", False),
        "text": result.get("text", ""),
        "variant": "{name}",
        "max_tokens": {max_toks},
    }}
'''
        out.append((full, code, SkillLevel.TASK, [], f"Prompt variant {name}"))
    return out


def gen_reasoning_family() -> List[Tuple[str, str, SkillLevel, List[str], str]]:
    """10 reasoning variants: chain depths 1..10."""
    out = []
    for depth in range(1, 11):
        full = _name("reason", f"chain_{depth}")
        code = f'''
def {full}(query="", **kwargs):
    """{depth}-step chain of thought"""
    chain = []
    prior = ""
    i = 0
    while i < {depth}:
        r = ai_reason(
            "Step " + str(i + 1) + " of {depth}: " + str(query),
            context={{"step": i + 1, "prior": str(prior)[:300]}},
            max_tokens=200,
        )
        chain.append(r)
        prior = str(prior) + " | " + str(r.get("text", ""))[:150]
        i = i + 1
    return {{
        "ok": all(c.get("ok", False) for c in chain),
        "depth": {depth},
        "steps": len(chain),
        "final_answer": str(prior)[:600],
    }}
'''
        out.append((full, code, SkillLevel.WORKFLOW, [], f"Reasoning depth {depth}"))
    return out


def gen_planning_family() -> List[Tuple[str, str, SkillLevel, List[str], str]]:
    """10 planning variants: different decomposition strategies."""
    variants = [
        ("short",       3),  ("medium",      5),  ("long",       8),
        ("deep",       10),  ("wide",        5),  ("sequential", 5),
        ("parallel",    5),  ("milestones",  4),  ("phases",     5),
        ("sprint",      6),
    ]
    out = []
    for name, n_steps in variants:
        full = _name("plan", name)
        # Use "\\n" in the template so the generated source gets a literal
        # backslash-n (which Python parses as a newline char at compile time).
        code = f'''
def {full}(goal="", **kwargs):
    """Planning variant: {name} ({n_steps} steps)"""
    emit_event("cap.{full}", {{"goal": str(goal)[:80]}})
    r = ai_reason(
        "Decompose this goal into {n_steps} ordered steps: " + str(goal),
        context={{"variant": "{name}", "n_steps": {n_steps}}},
        max_tokens=500,
    )
    text = r.get("text", "") or ""
    lines = [ln.strip() for ln in text.split("\\n") if ln.strip()]
    sub_goals = lines[:{n_steps}] if lines else ["Analyse", "Act", "Verify"]
    return {{
        "ok": r.get("ok", False),
        "variant": "{name}",
        "goal": goal,
        "sub_goals": sub_goals,
        "count": len(sub_goals),
    }}
'''
        out.append((full, code, SkillLevel.TASK, [], f"Planning variant {name}"))
    return out


def gen_reflection_family() -> List[Tuple[str, str, SkillLevel, List[str], str]]:
    """10 reflection variants."""
    variants = ["reflect", "critique", "affirm", "retrospect", "prospect",
                "introspect", "evaluate", "assess", "review", "meta"]
    out = []
    for i, name in enumerate(variants):
        full = _name("reflection", name)
        code = f'''
def {full}(subject="", last_result=None, **kwargs):
    """Reflection variant: {name}"""
    query = "{name.capitalize()} on: " + str(subject) + ". Prior: " + str(last_result)[:300]
    r = consult_queen(query, context={{"variant": "{name}"}})
    return {{
        "ok": r.get("ok", False),
        "variant": "{name}",
        "text": r.get("text", "")[:400],
    }}
'''
        out.append((full, code, SkillLevel.TASK, [], f"Reflection variant {name}"))
    return out


def gen_tool_use_family() -> List[Tuple[str, str, SkillLevel, List[str], str]]:
    """10 tool-use variants — one for each VM primitive category."""
    tools = [
        ("screenshot",    "vm_screenshot",        "{}"),
        ("click",         "vm_left_click",        '{"x": 500, "y": 300}'),
        ("type",          "vm_type_text",         '{"text": "hello"}'),
        ("key",           "vm_press_key",         '{"key": "enter"}'),
        ("hotkey",        "vm_hotkey",            '{"keys": ["ctrl", "c"]}'),
        ("scroll",        "vm_scroll",            '{"x": 500, "y": 300, "direction": "down"}'),
        ("focus",         "vm_focus_window",      '{"title": "Desktop"}'),
        ("list_windows",  "vm_list_windows",      "{}"),
        ("shell",         "vm_execute_shell",     '{"command": "whoami"}'),
        ("powershell",    "vm_execute_powershell", '{"command": "Get-Process"}'),
    ]
    out = []
    for name, primitive, args_literal in tools:
        full = _name("tool", name)
        code = f'''
def {full}(**kwargs):
    """Tool use variant: {name} ({primitive})"""
    result = {primitive}(**{args_literal})
    return {{
        "ok": result.get("ok", False),
        "tool": "{primitive}",
        "variant": "{name}",
        "data": result.get("data", {{}}),
    }}
'''
        out.append((full, code, SkillLevel.TASK, [], f"Tool use {name}"))
    return out


def gen_code_gen_family() -> List[Tuple[str, str, SkillLevel, List[str], str]]:
    """10 code-generation variants."""
    variants = [
        ("function", "a simple function"),
        ("class",    "a class"),
        ("test",     "a unit test"),
        ("refactor", "refactor code"),
        ("debug",    "debug a snippet"),
        ("document", "add documentation"),
        ("explain",  "explain a snippet"),
        ("review",   "review code quality"),
        ("optimize", "optimise performance"),
        ("type",     "add type hints"),
    ]
    out = []
    for name, style in variants:
        full = _name("code", name)
        code = f'''
def {full}(spec="", **kwargs):
    """Code gen variant: {name} ({style})"""
    r = ai_reason(
        "Write Python to {style}: " + str(spec),
        context={{"variant": "{name}", "style": "{style}"}},
        max_tokens=600,
    )
    return {{
        "ok": r.get("ok", False),
        "variant": "{name}",
        "draft": str(r.get("text", ""))[:500],
    }}
'''
        out.append((full, code, SkillLevel.TASK, [], f"Code gen {name}"))
    return out


def gen_recovery_family() -> List[Tuple[str, str, SkillLevel, List[str], str]]:
    """10 recovery variants."""
    variants = ["retry", "rollback", "fallback", "escalate", "alert",
                "circuit_break", "degrade", "restart", "heal", "reroute"]
    out = []
    for name in variants:
        full = _name("recovery", name)
        code = f'''
def {full}(failed_skill="", last_error="", **kwargs):
    """Recovery variant: {name}"""
    r = consult_queen(
        "Recovery strategy '{name}' for skill " + str(failed_skill) + ": " + str(last_error),
        context={{"variant": "{name}", "failed": failed_skill}},
    )
    return {{
        "ok": r.get("ok", False),
        "variant": "{name}",
        "plan": r.get("text", "")[:400],
    }}
'''
        out.append((full, code, SkillLevel.TASK, [], f"Recovery {name}"))
    return out


def gen_delegation_family() -> List[Tuple[str, str, SkillLevel, List[str], str]]:
    """10 delegation variants."""
    variants = ["direct", "best_match", "random", "weighted", "chain",
                "parallel", "sequential", "race", "consensus", "vote"]
    out = []
    for name in variants:
        full = _name("delegate", name)
        code = f'''
def {full}(skill_name="", **kwargs):
    """Delegation variant: {name}"""
    available = list_skills()
    if not available.get("ok", False):
        return {{"ok": False, "variant": "{name}", "error": "no_skills"}}
    names = available.get("skills", [])
    if skill_name and skill_name in names:
        result = call_skill(str(skill_name))
        return {{
            "ok": result.get("ok", False),
            "variant": "{name}",
            "delegated_to": skill_name,
        }}
    return {{
        "ok": True,
        "variant": "{name}",
        "library_size": len(names),
    }}
'''
        out.append((full, code, SkillLevel.TASK, [], f"Delegation {name}"))
    return out


def gen_memory_family() -> List[Tuple[str, str, SkillLevel, List[str], str]]:
    """10 memory variants."""
    variants = ["remember_fact", "recall_fact", "list_facts", "index_facts",
                "search_facts", "summarise", "compress", "expand",
                "prune", "audit"]
    out = []
    for name in variants:
        full = _name("memory", name)
        code = f'''
def {full}(target="", key="fact", value="", **kwargs):
    """Memory variant: {name}"""
    if "remember" in "{name}" or "index" in "{name}":
        r = remember(str(target) or "memory_family", str(key), str(value))
        return {{"ok": r.get("ok", False), "variant": "{name}", "op": "write"}}
    if "recall" in "{name}" or "search" in "{name}":
        r = recall(str(target) or "memory_family", str(key))
        return {{"ok": r.get("ok", False), "variant": "{name}", "op": "read"}}
    available = list_skills()
    return {{
        "ok": available.get("ok", False),
        "variant": "{name}",
        "op": "enumerate",
        "count": available.get("count", 0),
    }}
'''
        out.append((full, code, SkillLevel.TASK, [], f"Memory {name}"))
    return out


def gen_meta_family() -> List[Tuple[str, str, SkillLevel, List[str], str]]:
    """10 meta-cognitive variants."""
    variants = ["improve", "learn", "compose", "decompose", "abstract",
                "instantiate", "audit", "reflect", "plan", "execute"]
    out = []
    for name in variants:
        full = _name("meta", name)
        code = f'''
def {full}(target="", **kwargs):
    """Meta variant: {name}"""
    emit_event("cap.meta.{name}", {{"target": str(target)[:80]}})
    r = consult_queen(
        "Meta operation '{name}' on target: " + str(target),
        context={{"variant": "{name}"}},
    )
    available = list_skills()
    return {{
        "ok": r.get("ok", False),
        "variant": "{name}",
        "insight": r.get("text", "")[:300],
        "library_size": available.get("count", 0),
    }}
'''
        out.append((full, code, SkillLevel.ROLE, [], f"Meta {name}"))
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
class HyperHarness:
    tmp: Path
    dispatcher: VMControlDispatcher = field(default=None)
    lib: SkillLibrary = field(default=None)
    architect: CodeArchitect = field(default=None)
    authored: List[str] = field(default_factory=list)
    blocked: List[Tuple[str, str]] = field(default_factory=list)

    @classmethod
    def build(cls) -> "HyperHarness":
        tmp = Path(tempfile.mkdtemp(prefix="aureon_hyper_"))
        h = cls(tmp=tmp)
        h.dispatcher = VMControlDispatcher()
        sid = h.dispatcher.create_session(backend="simulated", name="hyper-vm", make_default=True)
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


def phase_bootstrap(h: HyperHarness) -> Dict[str, Any]:
    banner("HYPER PHASE 1 — Bootstrap L0 atomics")
    atomics = h.architect.bootstrap_atomics()
    info(f"Seeded {len(atomics)} atomic skills")
    return {"phase": 1, "atomics": len(atomics), "ok": len(atomics) >= 15}


def phase_author_100(h: HyperHarness, families_filter: List[str] = None) -> Dict[str, Any]:
    banner("HYPER PHASE 2 — Author 100 LLM capability skills (10 families × 10 variants)")

    total_authored = 0
    total_blocked = 0
    per_family: Dict[str, Dict[str, int]] = {}

    target_families = families_filter or list(FAMILIES.keys())

    for family_name in target_families:
        generator = FAMILIES.get(family_name)
        if not generator:
            continue

        specs = generator()
        fam_ok = 0
        fam_fail = 0

        for full_name, code, level, deps, desc in specs:
            proposal = SkillProposal(
                name=full_name,
                description=desc,
                level=level,
                category=f"hyper_{family_name}",
                code=code.strip(),
                entry_function=full_name,
                params_schema={"type": "object", "properties": {}},
                dependencies=deps,
                reasoning=f"Hyper test {family_name} variant",
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
        status = "OK" if fam_fail == 0 else "PARTIAL"
        info(f"{status:8s} {family_name:12s}  {fam_ok}/{fam_ok + fam_fail} authored")

    # Show blocked details (if any)
    if h.blocked:
        print()
        info("Blocked skills:")
        for name, error in h.blocked[:10]:
            info(f"  {name}: {error[:80]}")
        if len(h.blocked) > 10:
            info(f"  ... and {len(h.blocked) - 10} more")

    expected = len(target_families) * 10
    return {
        "phase": 2,
        "total_authored": total_authored,
        "total_blocked": total_blocked,
        "expected": expected,
        "per_family": per_family,
        "ok": total_authored == expected,
    }


def phase_exercise_100(h: HyperHarness) -> Dict[str, Any]:
    banner("HYPER PHASE 3 — Exercise all 100 authored capabilities")

    test_params = {
        "prompt":     {"query": "What is coherence?"},
        "reason":     {"query": "Should we deploy?"},
        "plan":       {"goal": "Ship a new feature"},
        "reflection": {"subject": "today", "last_result": "mixed"},
        "tool":       {},
        "code":       {"spec": "add two numbers"},
        "recovery":   {"failed_skill": "deploy", "last_error": "timeout"},
        "delegate":   {"skill_name": "screenshot"},
        "memory":     {"target": "test", "key": "k", "value": "v"},
        "meta":       {"target": "prompt_default"},
    }

    successes = 0
    failures = 0
    per_family: Dict[str, Dict[str, int]] = {}

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

    # Report
    for family, stats in sorted(per_family.items()):
        total = stats["ok"] + stats["fail"]
        marker = "OK" if stats["fail"] == 0 else "PARTIAL"
        info(f"{marker:8s} {family:12s}  {stats['ok']}/{total} executed ok")

    return {
        "phase": 3,
        "total_executed": len(h.authored),
        "successes": successes,
        "failures": failures,
        "per_family": per_family,
        "ok": successes >= len(h.authored) * 0.95,  # at least 95% should work
    }


def phase_parallel_40(h: HyperHarness) -> Dict[str, Any]:
    banner("HYPER PHASE 4 — 40-agent parallel swarm")

    if not h.authored:
        return {"phase": 4, "ok": False, "error": "no_capabilities"}

    # Pick 40 distinct skill executions
    import random
    selected = random.sample(h.authored, min(40, len(h.authored)))

    successes = 0
    failures = 0
    durations: List[float] = []
    lock = threading.Lock()

    def run_one(skill_name: str):
        nonlocal successes, failures
        family = skill_name.split("_")[0]
        params = {
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
        }.get(family, {})

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

    with ThreadPoolExecutor(max_workers=40) as ex:
        futures = [ex.submit(run_one, name) for name in selected]
        for f in as_completed(futures):
            pass

    p50 = sorted(durations)[len(durations) // 2] * 1000 if durations else 0
    p99 = sorted(durations)[int(len(durations) * 0.99)] * 1000 if len(durations) > 1 else 0

    info(f"40 parallel runs:  successes={successes}  failures={failures}")
    info(f"  p50 latency: {p50:.2f} ms")
    info(f"  p99 latency: {p99:.2f} ms")

    return {
        "phase": 4,
        "parallel_agents": 40,
        "successes": successes,
        "failures": failures,
        "p50_ms": round(p50, 2),
        "p99_ms": round(p99, 2),
        "ok": failures == 0,
    }


def phase_compose_pipeline(h: HyperHarness) -> Dict[str, Any]:
    banner("HYPER PHASE 5 — Compose 10-step multi-family pipeline")

    # Compose one skill from each family into a 10-step workflow
    pipeline = [
        ("prompt_default",   {"query": "What is the market state?"}),
        ("reason_chain_3",   {"query": "Is BTC bullish?"}),
        ("plan_medium",      {"goal": "Ship new feature"}),
        ("reflection_reflect", {"subject": "plan", "last_result": "OK"}),
        ("tool_screenshot",  {}),
        ("code_function",    {"spec": "hash a string"}),
        ("recovery_retry",   {"failed_skill": "step_5", "last_error": "timeout"}),
        ("delegate_direct",  {"skill_name": "screenshot"}),
        ("memory_remember_fact", {"target": "pipeline", "key": "completed", "value": "true"}),
        ("meta_audit",       {"target": "pipeline"}),
    ]

    results = []
    all_ok = True
    for name, params in pipeline:
        if not h.lib.contains(name):
            results.append((name, False, "not_authored"))
            all_ok = False
            continue
        r = h.architect.execute_skill(name, params=params)
        inner = r.return_value if isinstance(r.return_value, dict) else {}
        inner_ok = bool(r.ok and inner.get("ok", False))
        results.append((name, inner_ok, inner.get("variant", "?")))
        if not inner_ok:
            all_ok = False

    for name, step_ok, variant in results:
        marker = "OK" if step_ok else "!!"
        info(f"[{marker}] {name:28s} variant={variant}")

    return {
        "phase": 5,
        "steps": len(pipeline),
        "successes": sum(1 for _, ok, _ in results if ok),
        "ok": all_ok,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Aureon 10x Hyper Test")
    parser.add_argument("--families", type=str, default="",
                        help="Comma-separated family names (default: all)")
    args = parser.parse_args()

    banner("AUREON HYPER TEST — 10× EXPANDED ULTIMATE (100 LLM CAPABILITIES)", fill="█")
    print()
    info("Objective: 10× expansion across every dimension")
    info("  LLM capabilities:  10 → 100")
    info("  Parallel agents:    4 → 40")
    info("  Library size:      30 → ~120 (20 atomics + 100 capabilities)")
    info("  Cross-family compose pipeline: 10 steps across all 10 families")
    info("Mode: fully in-house AI, zero external LLM")

    families_filter = None
    if args.families:
        families_filter = [f.strip() for f in args.families.split(",")]

    harness = HyperHarness.build()
    all_results: List[Dict[str, Any]] = []

    try:
        all_results.append(phase_bootstrap(harness))
        all_results.append(phase_author_100(harness, families_filter))
        all_results.append(phase_exercise_100(harness))
        all_results.append(phase_parallel_40(harness))
        all_results.append(phase_compose_pipeline(harness))
    finally:
        lib_stats = harness.lib.get_stats()
        harness.teardown()

    banner("HYPER REPORT", fill="█")

    passed = sum(1 for r in all_results if r.get("ok"))
    total = len(all_results)

    for r in all_results:
        flag = "[PASS]" if r.get("ok") else "[FAIL]"
        summary_parts = []
        for k, v in r.items():
            if k in ("ok", "phase", "per_family"):
                continue
            if isinstance(v, (dict, list)):
                summary_parts.append(f"{k}={len(v) if isinstance(v, list) else '...'}")
            else:
                summary_parts.append(f"{k}={v}")
        print(f"  {flag}  Phase {r['phase']}: {', '.join(summary_parts)[:170]}")

    print()
    print(f"  Skill library: {lib_stats['total_skills']} skills "
          f"({lib_stats.get('by_status', {}).get('validated', 0)} validated)")
    print(f"    by_level:  {lib_stats.get('by_level', {})}")
    print()
    print(f"  RESULT: {passed}/{total} phases passed")
    print()
    print("█" * BANNER_WIDTH)

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
