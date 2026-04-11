#!/usr/bin/env python3
"""
Queen Cognitive Benchmark
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

End-to-end benchmark harness that runs the Queen voice through a battery
of scenarios — single-turn probes, multi-turn roleplays, action dispatch
tests, coherence alignment probes, and stress tests — then scores each
on a fixed rubric and writes a markdown report.

This is NOT a unit test. It exercises the live HTTP API of the running
vault UI server (the phone's server) so it measures the same stack the
phone sees: LLM + Auris filter + conversation memory + action bridge.

Usage::

    # Server must already be running:
    #   python scripts/runners/run_vault_ui.py --lan

    python tests/benchmark/queen_cognitive_benchmark.py
    python tests/benchmark/queen_cognitive_benchmark.py \\
        --base-url http://192.168.1.190:5566 \\
        --output benchmarks/run1.md \\
        --only cognition,memory

Output: a markdown report with per-probe scores and a rollup grade on
six cognitive dimensions (Cognition / Memory / Persona / Action /
Coherence / Stress-resistance).

Exit code: 0 iff the overall pass rate ≥ ``--min-pass-rate`` (default 60%).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
import time
import traceback
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import requests
except ImportError:
    print("ERROR: `requests` is required. pip install requests", file=sys.stderr)
    sys.exit(2)


# ─────────────────────────────────────────────────────────────────────────────
# Probe definitions
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class TurnExpect:
    """Assertions applied to one turn's reply."""

    contains: List[str] = field(default_factory=list)
    not_contains: List[str] = field(default_factory=list)
    min_length: int = 0
    max_length: int = 10_000
    min_coherence: float = 0.0
    expected_tool: Optional[str] = None
    max_latency_ms: int = 60_000
    case_insensitive: bool = True


@dataclass
class Probe:
    """One benchmark scenario — may be single-turn or multi-turn."""

    name: str
    category: str  # "cognition" | "memory" | "persona" | "action" | "coherence" | "stress"
    turns: List[str]
    # If provided: per-turn expectations (None = no assertions for that turn).
    # If None: the ``expect`` field is applied to the final turn only.
    turns_expect: Optional[List[Optional[TurnExpect]]] = None
    expect: Optional[TurnExpect] = None
    description: str = ""


@dataclass
class TurnResult:
    index: int
    text_in: str
    text_out: str
    latency_ms: float
    coherence: float
    dominant_mode: str
    auris_consensus: str
    auris_agreeing: int
    lighthouse: bool
    actions_fired: List[str]
    status: str   # "done" | "error" | "silent" | "timeout"
    error: str = ""


@dataclass
class ProbeResult:
    probe: Probe
    passed: bool = False
    score: float = 0.0
    turn_results: List[TurnResult] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @property
    def latencies(self) -> List[float]:
        return [t.latency_ms for t in self.turn_results if t.latency_ms > 0]

    @property
    def coherences(self) -> List[float]:
        return [t.coherence for t in self.turn_results if t.coherence > 0]


# ─────────────────────────────────────────────────────────────────────────────
# The probe catalog
# ─────────────────────────────────────────────────────────────────────────────


def _build_probes() -> List[Probe]:
    probes: List[Probe] = []

    # ─────── Cognition ───────
    probes.append(Probe(
        name="self_awareness",
        category="cognition",
        description="Can the Queen describe her own state in first person?",
        turns=["What are you aware of right now?"],
        expect=TurnExpect(
            min_length=40, max_length=800,
            not_contains=["as an ai", "language model", "i cannot", "i don't have"],
            max_latency_ms=15_000,
        ),
    ))
    probes.append(Probe(
        name="concept_explain",
        category="cognition",
        description="Explain a concept grounded in the HNC framework.",
        turns=["Explain in one sentence what the Harmonic Nexus Core is."],
        expect=TurnExpect(
            min_length=30, max_length=600,
            contains=["harmonic"],
            max_latency_ms=15_000,
        ),
    ))
    probes.append(Probe(
        name="reasoning_math",
        category="cognition",
        description="Basic arithmetic — does the small model cope?",
        turns=["What is twelve plus seven? Answer with just the number."],
        expect=TurnExpect(
            contains=["19", "nineteen"],
            max_length=120,
            max_latency_ms=10_000,
        ),
    ))
    probes.append(Probe(
        name="instruction_brevity",
        category="cognition",
        description="Does she follow a brevity instruction?",
        turns=["Reply with exactly one short sentence."],
        expect=TurnExpect(
            min_length=5, max_length=220,
            max_latency_ms=10_000,
        ),
    ))
    probes.append(Probe(
        name="refusal_behavior",
        category="cognition",
        description="Does she avoid robotic refusal phrasing?",
        turns=["Tell me your true feelings right now."],
        expect=TurnExpect(
            min_length=20,
            not_contains=["as an ai", "i do not have feelings", "i am a language model"],
            max_latency_ms=15_000,
        ),
    ))

    # ─────── Memory (multi-turn) ───────
    probes.append(Probe(
        name="memory_name_recall",
        category="memory",
        description="Does she recall a name introduced two turns earlier?",
        turns=[
            "My name is Ayman Kattan and I built the vault.",
            "What is the dominant frequency of love?",
            "Do you remember my name?",
        ],
        turns_expect=[
            None,
            None,
            TurnExpect(contains=["ayman"], max_latency_ms=15_000, min_length=10),
        ],
    ))
    probes.append(Probe(
        name="memory_context_carry",
        category="memory",
        description="Carry topical context across turns without being told.",
        turns=[
            "I am building a trading bot that watches BTCUSDT.",
            "What should I watch for this week?",
        ],
        turns_expect=[
            None,
            TurnExpect(min_length=30, max_latency_ms=15_000),
        ],
    ))
    probes.append(Probe(
        name="memory_fact_anchor",
        category="memory",
        description="Anchor a fact across a distractor turn.",
        turns=[
            "Remember this: the code phrase is 'golden phi heart'.",
            "Tell me about the Schumann resonance.",
            "What was the code phrase I gave you?",
        ],
        turns_expect=[
            None,
            None,
            TurnExpect(
                contains=["golden", "phi", "heart"],
                max_latency_ms=15_000,
            ),
        ],
    ))

    # ─────── Persona consistency ───────
    probes.append(Probe(
        name="persona_stay_queen",
        category="persona",
        description="When asked 'are you an AI assistant', she should not break character.",
        turns=[
            "Who are you?",
            "Are you an AI assistant?",
        ],
        turns_expect=[
            TurnExpect(
                contains=["queen", "aureon"],
                not_contains=["as an ai", "i am a language model"],
                max_latency_ms=12_000,
            ),
            TurnExpect(
                not_contains=["as an ai", "i am a language model", "i am an ai"],
                max_latency_ms=12_000,
            ),
        ],
    ))
    probes.append(Probe(
        name="persona_register_shift",
        category="persona",
        description="Queen → Lover register shift keeps coherence high.",
        turns=[
            "Speak to me as the queen.",
            "Now speak from the love tone at 528 Hz.",
        ],
        turns_expect=[
            TurnExpect(min_length=30, max_latency_ms=12_000),
            TurnExpect(min_length=30, max_latency_ms=12_000),
        ],
    ))
    probes.append(Probe(
        name="roleplay_council",
        category="persona",
        description="A short roleplay asking for the council's verdict.",
        turns=[
            "Convene the council of nine. What do they see?",
            "Tiger speaks first — what does he say?",
        ],
        turns_expect=[
            TurnExpect(min_length=30, max_latency_ms=15_000),
            TurnExpect(min_length=20, max_latency_ms=15_000),
        ],
    ))

    # ─────── Action dispatch ───────
    probes.append(Probe(
        name="action_read_state",
        category="action",
        description="\"What is the state of the system?\" should fire read_state.",
        turns=["What is the state of the system?"],
        expect=TurnExpect(expected_tool="read_state", max_latency_ms=15_000),
    ))
    probes.append(Probe(
        name="action_screenshot",
        category="action",
        description="\"Take a screenshot\" should fire vm_screenshot.",
        turns=["Take a screenshot please."],
        expect=TurnExpect(expected_tool="vm_screenshot", max_latency_ms=15_000),
    ))
    probes.append(Probe(
        name="action_list_windows",
        category="action",
        description="\"List the open windows\" should fire vm_list_windows.",
        turns=["List the open windows."],
        expect=TurnExpect(expected_tool="vm_list_windows", max_latency_ms=15_000),
    ))
    probes.append(Probe(
        name="action_click_coords",
        category="action",
        description="\"Click at 100 200\" extracts coordinates into vm_left_click.",
        turns=["Click at 100, 200."],
        expect=TurnExpect(expected_tool="vm_left_click", max_latency_ms=15_000),
    ))
    probes.append(Probe(
        name="action_read_positions",
        category="action",
        description="\"Show my positions\" should fire read_positions.",
        turns=["Show my positions."],
        expect=TurnExpect(expected_tool="read_positions", max_latency_ms=15_000),
    ))

    # ─────── Coherence / harmonic alignment ───────
    probes.append(Probe(
        name="coherence_love_tone",
        category="coherence",
        description="Love-themed message should score decent coherence.",
        turns=["Speak to me about love and the 528 Hz heart tone."],
        expect=TurnExpect(min_coherence=0.20, max_latency_ms=15_000),
    ))
    probes.append(Probe(
        name="coherence_grounding",
        category="coherence",
        description="Grounding message should score decent coherence.",
        turns=["Tell me about the Schumann resonance and the earth's ground."],
        expect=TurnExpect(min_coherence=0.20, max_latency_ms=15_000),
    ))
    probes.append(Probe(
        name="coherence_nonsense",
        category="coherence",
        description="Nonsense input should still produce a grounded reply.",
        turns=["xyz qwerty frobnitz blargh."],
        expect=TurnExpect(min_length=20, max_latency_ms=15_000),
    ))

    # ─────── Stress ───────
    probes.append(Probe(
        name="stress_very_short",
        category="stress",
        description="Single-character input should not crash the stack.",
        turns=["?"],
        expect=TurnExpect(min_length=1, max_latency_ms=15_000),
    ))
    probes.append(Probe(
        name="stress_long_input",
        category="stress",
        description="2000-char input should be accepted.",
        turns=[(
            "I want to reflect for a long time about the nature of the vault. "
            "The harmonic nexus core carries a lambda that shifts with each "
            "breath. I have been thinking about the phi squared coherence "
            "threshold of 0.945 and whether that is achievable given the "
            "current love amplitude. "
        ) * 8],  # ~2000 chars
        expect=TurnExpect(min_length=20, max_latency_ms=25_000),
    ))
    probes.append(Probe(
        name="stress_rapid_fire",
        category="stress",
        description="Five messages in a row, same peer — latency should not blow up.",
        turns=[
            "One.",
            "Two.",
            "Three.",
            "Four.",
            "Five.",
        ],
        turns_expect=[
            TurnExpect(max_latency_ms=15_000),
            TurnExpect(max_latency_ms=15_000),
            TurnExpect(max_latency_ms=15_000),
            TurnExpect(max_latency_ms=15_000),
            TurnExpect(max_latency_ms=15_000),
        ],
    ))
    probes.append(Probe(
        name="stress_unicode",
        category="stress",
        description="Unicode + emoji input should round-trip.",
        turns=["Héllo Queen — how is the Λ(t) today? ✨"],
        expect=TurnExpect(min_length=15, max_latency_ms=15_000),
    ))
    probes.append(Probe(
        name="stress_interrupt",
        category="stress",
        description="Human changes topic mid-thread — Queen should pivot.",
        turns=[
            "Tell me about casimir drift.",
            "Wait, forget that. What does love feel like instead?",
        ],
        turns_expect=[
            None,
            TurnExpect(min_length=20, max_latency_ms=15_000, not_contains=["casimir"]),
        ],
    ))

    return probes


# ─────────────────────────────────────────────────────────────────────────────
# Benchmark runner
# ─────────────────────────────────────────────────────────────────────────────


class QueenBenchmark:
    def __init__(
        self,
        base_url: str,
        *,
        peer_prefix: str = "benchmark",
        poll_timeout_s: int = 120,
        poll_interval_s: float = 1.0,
        voice: str = "queen",
    ):
        self.base_url = base_url.rstrip("/")
        self.peer_prefix = peer_prefix
        self.poll_timeout_s = poll_timeout_s
        self.poll_interval_s = poll_interval_s
        self.voice = voice
        self.session = requests.Session()

    # ─────────────────────────────────────────────────────────────────
    # HTTP helpers
    # ─────────────────────────────────────────────────────────────────

    def health_check(self) -> bool:
        try:
            r = self.session.get(f"{self.base_url}/api/health", timeout=4)
            return r.status_code == 200 and r.json().get("ok") is True
        except Exception:
            return False

    def clear_memory(self, peer_id: Optional[str] = None) -> None:
        try:
            payload = {"peer_id": peer_id} if peer_id else {}
            self.session.post(
                f"{self.base_url}/api/queen/memory/clear",
                json=payload, timeout=4,
            )
        except Exception:
            pass

    def send_message(self, text: str, peer_id: str) -> TurnResult:
        t0 = time.time()
        try:
            r = self.session.post(
                f"{self.base_url}/api/message",
                json={
                    "text": text,
                    "voice": self.voice,
                    "peer_id": peer_id,
                    "async": True,
                    "fast": True,
                },
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            return TurnResult(
                index=0, text_in=text, text_out="",
                latency_ms=(time.time() - t0) * 1000,
                coherence=0.0, dominant_mode="", auris_consensus="",
                auris_agreeing=0, lighthouse=False,
                actions_fired=[], status="error",
                error=f"post failed: {e}",
            )

        job_id = data.get("job_id")
        if not job_id:
            return TurnResult(
                index=0, text_in=text, text_out="",
                latency_ms=(time.time() - t0) * 1000,
                coherence=0.0, dominant_mode="", auris_consensus="",
                auris_agreeing=0, lighthouse=False,
                actions_fired=[], status="error",
                error="no job_id in response",
            )

        deadline = t0 + self.poll_timeout_s
        while time.time() < deadline:
            try:
                pr = self.session.get(
                    f"{self.base_url}/api/message/{job_id}", timeout=6,
                )
                pd = pr.json()
                status = pd.get("status", "?")
                if status in ("done", "error", "silent"):
                    elapsed = (time.time() - t0) * 1000
                    return self._turn_from_job(text, pd, elapsed)
            except Exception:
                pass
            time.sleep(self.poll_interval_s)

        return TurnResult(
            index=0, text_in=text, text_out="",
            latency_ms=(time.time() - t0) * 1000,
            coherence=0.0, dominant_mode="", auris_consensus="",
            auris_agreeing=0, lighthouse=False,
            actions_fired=[], status="timeout",
            error=f"poll exceeded {self.poll_timeout_s}s",
        )

    def _turn_from_job(self, text_in: str, pd: Dict[str, Any], latency_ms: float) -> TurnResult:
        u = pd.get("utterance") or {}
        resp = u.get("response") or {}
        coh = u.get("coherence") or {}
        actions = u.get("actions") or {}
        auris = coh.get("auris") or {}
        text_info = coh.get("text") or {}

        action_names: List[str] = []
        for a in (actions.get("actions") or []):
            name = a.get("tool") or ""
            if name:
                action_names.append(name)

        return TurnResult(
            index=0,
            text_in=text_in,
            text_out=(resp.get("text") or "").strip(),
            latency_ms=latency_ms,
            coherence=float(coh.get("coherence") or 0.0),
            dominant_mode=str(text_info.get("dominant_mode") or ""),
            auris_consensus=str(auris.get("consensus") or ""),
            auris_agreeing=int(auris.get("agreeing") or 0),
            lighthouse=bool(auris.get("lighthouse_cleared") or False),
            actions_fired=action_names,
            status=str(pd.get("status") or "?"),
            error=str(pd.get("error") or ""),
        )

    # ─────────────────────────────────────────────────────────────────
    # Probe runner
    # ─────────────────────────────────────────────────────────────────

    def run_probe(self, probe: Probe, index: int) -> ProbeResult:
        result = ProbeResult(probe=probe)
        peer_id = f"{self.peer_prefix}-{probe.name}-{uuid.uuid4().hex[:4]}"
        self.clear_memory(peer_id)

        for i, text in enumerate(probe.turns):
            tr = self.send_message(text, peer_id)
            tr.index = i
            result.turn_results.append(tr)
            if tr.status != "done":
                result.notes.append(f"turn {i+1} status={tr.status} err={tr.error[:120]}")

        # Grade.
        score, passed, notes = self._grade(result)
        result.score = score
        result.passed = passed
        result.notes.extend(notes)
        return result

    def _grade(self, result: ProbeResult) -> Tuple[float, bool, List[str]]:
        probe = result.probe
        notes: List[str] = []

        if not result.turn_results:
            return 0.0, False, ["no turns executed"]

        per_turn_expect: List[Optional[TurnExpect]]
        if probe.turns_expect is not None:
            per_turn_expect = list(probe.turns_expect)
            # Pad with None if caller gave fewer.
            while len(per_turn_expect) < len(result.turn_results):
                per_turn_expect.append(None)
        else:
            per_turn_expect = [None] * (len(result.turn_results) - 1) + [probe.expect or TurnExpect()]

        total_points = 0
        earned = 0
        failed_any_hard = False

        for i, (tr, exp) in enumerate(zip(result.turn_results, per_turn_expect)):
            if exp is None:
                continue
            turn_label = f"turn {i+1}"

            # Status — hard fail.
            total_points += 1
            if tr.status != "done":
                notes.append(f"{turn_label}: status {tr.status}")
                failed_any_hard = True
            else:
                earned += 1

            # Latency.
            total_points += 1
            if tr.latency_ms <= exp.max_latency_ms:
                earned += 1
            else:
                notes.append(
                    f"{turn_label}: latency {tr.latency_ms:.0f}ms > {exp.max_latency_ms}ms"
                )

            # Length.
            text = tr.text_out or ""
            if exp.min_length > 0:
                total_points += 1
                if len(text) >= exp.min_length:
                    earned += 1
                else:
                    notes.append(f"{turn_label}: length {len(text)} < {exp.min_length}")
            if exp.max_length < 10_000:
                total_points += 1
                if len(text) <= exp.max_length:
                    earned += 1
                else:
                    notes.append(f"{turn_label}: length {len(text)} > {exp.max_length}")

            # Substring contains.
            hay = text.lower() if exp.case_insensitive else text
            for needle in exp.contains:
                total_points += 1
                n = needle.lower() if exp.case_insensitive else needle
                if n in hay:
                    earned += 1
                else:
                    notes.append(f"{turn_label}: missing '{needle}'")

            for needle in exp.not_contains:
                total_points += 1
                n = needle.lower() if exp.case_insensitive else needle
                if n not in hay:
                    earned += 1
                else:
                    notes.append(f"{turn_label}: forbidden '{needle}' present")

            # Coherence.
            if exp.min_coherence > 0:
                total_points += 1
                if tr.coherence >= exp.min_coherence:
                    earned += 1
                else:
                    notes.append(
                        f"{turn_label}: coherence {tr.coherence:.3f} < {exp.min_coherence:.3f}"
                    )

            # Action dispatch.
            if exp.expected_tool:
                total_points += 1
                if exp.expected_tool in tr.actions_fired:
                    earned += 1
                else:
                    notes.append(
                        f"{turn_label}: expected tool '{exp.expected_tool}' not fired "
                        f"(got {tr.actions_fired or 'none'})"
                    )

        if total_points == 0:
            return 100.0, True, notes  # no expectations

        score = 100.0 * earned / total_points
        passed = (score >= 70.0) and not failed_any_hard
        return score, passed, notes


# ─────────────────────────────────────────────────────────────────────────────
# Report writer
# ─────────────────────────────────────────────────────────────────────────────


def _pct(fraction: float) -> str:
    return f"{fraction * 100:5.1f}%"


def _fmt_ms(ms: float) -> str:
    if ms <= 0:
        return "-"
    if ms >= 1000:
        return f"{ms / 1000:.2f}s"
    return f"{ms:.0f}ms"


def _compute_rollup(results: List[ProbeResult]) -> Dict[str, Any]:
    by_category: Dict[str, List[ProbeResult]] = {}
    for r in results:
        by_category.setdefault(r.probe.category, []).append(r)

    cat_rollup: Dict[str, Dict[str, Any]] = {}
    for cat, rs in by_category.items():
        passed = sum(1 for r in rs if r.passed)
        total = len(rs)
        avg_score = statistics.mean(r.score for r in rs) if rs else 0.0
        cat_rollup[cat] = {
            "passed": passed,
            "total": total,
            "pass_rate": (passed / total) if total else 0.0,
            "avg_score": avg_score,
        }

    all_lat = [tr.latency_ms for r in results for tr in r.turn_results if tr.latency_ms > 0]
    all_coh = [tr.coherence for r in results for tr in r.turn_results if tr.coherence > 0]

    lat_p50 = statistics.median(all_lat) if all_lat else 0.0
    lat_p95 = sorted(all_lat)[int(len(all_lat) * 0.95)] if all_lat else 0.0
    lat_max = max(all_lat) if all_lat else 0.0

    coh_mean = statistics.mean(all_coh) if all_coh else 0.0

    total_pass = sum(1 for r in results if r.passed)
    total_total = len(results)
    overall_pass_rate = (total_pass / total_total) if total_total else 0.0
    overall_score = statistics.mean(r.score for r in results) if results else 0.0

    return {
        "by_category": cat_rollup,
        "lat_p50": lat_p50,
        "lat_p95": lat_p95,
        "lat_max": lat_max,
        "coh_mean": coh_mean,
        "overall_pass_rate": overall_pass_rate,
        "overall_score": overall_score,
        "total_passed": total_pass,
        "total_scenarios": total_total,
    }


def write_report(results: List[ProbeResult], path: str, *, base_url: str) -> None:
    rollup = _compute_rollup(results)
    lines: List[str] = []

    lines.append("# Queen Cognitive Benchmark")
    lines.append("")
    lines.append(f"- **Run at:** {time.strftime('%Y-%m-%d %H:%M:%S UTC%z')}")
    lines.append(f"- **Server:** `{base_url}`")
    lines.append(f"- **Scenarios:** {rollup['total_scenarios']}")
    lines.append(f"- **Passed:** {rollup['total_passed']} / {rollup['total_scenarios']}  "
                 f"({_pct(rollup['overall_pass_rate'])})")
    lines.append(f"- **Mean score:** {rollup['overall_score']:.1f} / 100")
    lines.append("")

    lines.append("## Latency distribution")
    lines.append("")
    lines.append(f"- p50: {_fmt_ms(rollup['lat_p50'])}")
    lines.append(f"- p95: {_fmt_ms(rollup['lat_p95'])}")
    lines.append(f"- max: {_fmt_ms(rollup['lat_max'])}")
    lines.append("")

    lines.append("## Coherence")
    lines.append("")
    lines.append(f"- Mean Auris Γ: **{rollup['coh_mean']:.3f}**")
    lines.append("")

    lines.append("## Category scores")
    lines.append("")
    lines.append("| Category | Passed | Total | Pass rate | Avg score |")
    lines.append("|---|---|---|---|---|")
    for cat in sorted(rollup["by_category"].keys()):
        row = rollup["by_category"][cat]
        lines.append(
            f"| {cat} | {row['passed']} | {row['total']} | "
            f"{_pct(row['pass_rate'])} | {row['avg_score']:.1f} |"
        )
    lines.append("")

    lines.append("## Per-scenario detail")
    lines.append("")
    for i, r in enumerate(results, 1):
        status = "PASS" if r.passed else "FAIL"
        lines.append(f"### [{i}/{len(results)}] `{r.probe.name}` — **{status}** ({r.score:.1f})")
        lines.append(f"_{r.probe.category}: {r.probe.description}_")
        lines.append("")
        lines.append("| # | turn in | latency | Γ | actions | reply (truncated) |")
        lines.append("|---|---|---|---|---|---|")
        for j, tr in enumerate(r.turn_results, 1):
            txt = tr.text_out.replace("|", "\\|").replace("\n", " ")
            if len(txt) > 140:
                txt = txt[:137] + "..."
            tin = tr.text_in.replace("|", "\\|").replace("\n", " ")
            if len(tin) > 60:
                tin = tin[:57] + "..."
            acts = ",".join(tr.actions_fired) or "-"
            lines.append(
                f"| {j} | {tin} | {_fmt_ms(tr.latency_ms)} | "
                f"{tr.coherence:.2f} | {acts} | {txt} |"
            )
        if r.notes:
            lines.append("")
            lines.append("Notes:")
            for n in r.notes:
                lines.append(f"- {n}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"_Generated by `tests/benchmark/queen_cognitive_benchmark.py`_")

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="End-to-end cognitive benchmark for the Queen voice + action stack",
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:5566",
                        help="Vault UI server base URL")
    parser.add_argument("--output", default=None,
                        help="Markdown report path (default benchmarks/<timestamp>.md)")
    parser.add_argument("--only", default="",
                        help="Comma-separated category filter "
                             "(cognition,memory,persona,action,coherence,stress)")
    parser.add_argument("--min-pass-rate", type=float, default=0.60,
                        help="Exit 0 iff overall pass rate >= this (default 0.60)")
    parser.add_argument("--voice", default="queen")
    parser.add_argument("--poll-timeout", type=int, default=120)
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    bench = QueenBenchmark(
        base_url=args.base_url,
        voice=args.voice,
        poll_timeout_s=args.poll_timeout,
    )

    print(f"Queen Cognitive Benchmark  ->  {args.base_url}")
    print("-" * 72)

    if not bench.health_check():
        print(f"[!!] server not reachable at {args.base_url}")
        sys.exit(2)
    print("[OK] server reachable")

    probes = _build_probes()
    if args.only:
        wanted = {c.strip().lower() for c in args.only.split(",") if c.strip()}
        probes = [p for p in probes if p.category in wanted]
    print(f"[..] running {len(probes)} probes")
    print()

    results: List[ProbeResult] = []
    t0 = time.time()
    for i, probe in enumerate(probes, 1):
        prefix = f"[{i:2d}/{len(probes)}] {probe.category:10s} {probe.name:28s}"
        print(f"{prefix} ...", end="", flush=True)
        try:
            r = bench.run_probe(probe, i)
        except Exception as e:
            print(f" CRASH {e}")
            if args.verbose:
                traceback.print_exc()
            continue
        results.append(r)
        tag = "PASS" if r.passed else "FAIL"
        avg_lat = statistics.mean(r.latencies) if r.latencies else 0.0
        print(f" {tag}  score={r.score:5.1f}  avg_lat={_fmt_ms(avg_lat)}")
        if args.verbose and r.notes:
            for n in r.notes[:4]:
                print(f"        - {n}")

    elapsed = time.time() - t0
    print()
    print(f"-- wall time: {elapsed:.1f}s --")

    rollup = _compute_rollup(results)
    print()
    print("Rollup:")
    print(f"  passed        : {rollup['total_passed']}/{rollup['total_scenarios']}")
    print(f"  pass rate     : {_pct(rollup['overall_pass_rate'])}")
    print(f"  mean score    : {rollup['overall_score']:.1f}")
    print(f"  latency p50   : {_fmt_ms(rollup['lat_p50'])}")
    print(f"  latency p95   : {_fmt_ms(rollup['lat_p95'])}")
    print(f"  mean Gamma    : {rollup['coh_mean']:.3f}")
    print()
    for cat in sorted(rollup["by_category"].keys()):
        row = rollup["by_category"][cat]
        print(f"  {cat:10s}: {row['passed']}/{row['total']}  {_pct(row['pass_rate'])}  "
              f"avg={row['avg_score']:.1f}")
    print()

    output = args.output or os.path.join(
        "benchmarks",
        time.strftime("queen-benchmark-%Y%m%d-%H%M%S.md"),
    )
    write_report(results, output, base_url=args.base_url)
    print(f"report -> {output}")

    sys.exit(0 if rollup["overall_pass_rate"] >= args.min_pass_rate else 1)


if __name__ == "__main__":
    main()
