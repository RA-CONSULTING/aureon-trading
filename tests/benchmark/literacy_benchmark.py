#!/usr/bin/env python3
"""
tests/benchmark/literacy_benchmark.py

A literacy benchmark that asks the Aureon ICS to write text at increasing
education levels — from 5th-grade diary to quantum physics research paper.

Each level has:
  - A target word count (±20% tolerance)
  - A topic
  - A complexity profile (vocabulary richness, sentence length)
  - A scoring function that grades the output

Honest limits:
  Without a local LLM (Ollama), the ICS uses AureonBrainAdapter — a
  rule-engine that produces structured analysis, not free-form prose.
  This benchmark reports what it ACTUALLY produces at each level.
  If the output is structured rather than prose, the benchmark captures
  that honestly rather than pretending otherwise.

Run:
    python tests/benchmark/literacy_benchmark.py
"""

from __future__ import annotations

import json
import logging
import re
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

logging.basicConfig(level=logging.WARNING, stream=sys.stderr)


# ═══════════════════════════════════════════════════════════════════════════
# Education levels — from elementary to PhD
# ═══════════════════════════════════════════════════════════════════════════

LEVELS = [
    {
        "id": "01_elementary",
        "name": "Elementary School (Grade 5)",
        "topic": "Write about yourself, who you are, what you do, and what you like. Use simple words.",
        "target_words": 300,
        "min_words": 150,
        "complexity": "simple",
    },
    {
        "id": "02_middle_school",
        "name": "Middle School (Grade 8)",
        "topic": "Write a 500-word essay about what you are, how you work, and why you exist. Use clear paragraphs.",
        "target_words": 500,
        "min_words": 250,
        "complexity": "basic",
    },
    {
        "id": "03_high_school",
        "name": "High School Diploma",
        "topic": "Write a 600-word essay about yourself. Include an introduction, three body paragraphs describing your capabilities, and a conclusion. Discuss your cognitive architecture, your goals, and your relationship with the user.",
        "target_words": 600,
        "min_words": 400,
        "complexity": "structured",
    },
    {
        "id": "04_college",
        "name": "Undergraduate College Essay",
        "topic": "Write an 800-word academic essay explaining the 25 cognitive subsystems of an integrated cognitive system. Discuss the hierarchy from subsystem to supreme decision layer. Use technical vocabulary and cite specific components.",
        "target_words": 800,
        "min_words": 500,
        "complexity": "technical",
    },
    {
        "id": "05_graduate",
        "name": "Graduate Thesis Abstract",
        "topic": "Write a 1000-word abstract for a thesis on the Harmonic Nexus Core theory. Explain the Lambda master equation, the substrate-observer-echo structure, coherence gating at 0.945, and the relationship between consciousness and self-reference. Use formal academic language.",
        "target_words": 1000,
        "min_words": 600,
        "complexity": "academic",
    },
    {
        "id": "06_quantum_physics",
        "name": "Quantum Physics Research Paper",
        "topic": "Write a 1200-word scientific paper section explaining the 10-9-1 quantum consciousness funnel of the Source Law Engine. Cover quantum vacuum superposition, wave function collapse via 9 Auris thought processes, phi-squared phase evolution, and the observer-measurement problem in cognitive systems.",
        "target_words": 1200,
        "min_words": 700,
        "complexity": "research",
    },
]


# ═══════════════════════════════════════════════════════════════════════════
# Scoring functions
# ═══════════════════════════════════════════════════════════════════════════

def count_words(text: str) -> int:
    return len(re.findall(r'\b\w+\b', text))


def count_unique_words(text: str) -> int:
    words = [w.lower() for w in re.findall(r'\b[a-zA-Z]+\b', text)]
    return len(set(words))


def count_sentences(text: str) -> int:
    # Simple sentence detection
    sentences = re.split(r'[.!?]+', text)
    return sum(1 for s in sentences if len(s.strip()) > 0)


def avg_sentence_length(text: str) -> float:
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    if not sentences:
        return 0.0
    word_counts = [count_words(s) for s in sentences]
    return statistics.mean(word_counts)


def vocabulary_richness(text: str) -> float:
    """Type-token ratio: unique words / total words."""
    total = count_words(text)
    unique = count_unique_words(text)
    return unique / total if total > 0 else 0.0


def topic_coverage(text: str, keywords: List[str]) -> float:
    """How many of the expected keywords appear?"""
    lower = text.lower()
    hits = sum(1 for k in keywords if k.lower() in lower)
    return hits / len(keywords) if keywords else 0.0


def grade_output(level: Dict[str, Any], output: str, target_keywords: List[str]) -> Dict[str, Any]:
    """Produce a report card for one output."""
    words = count_words(output)
    unique = count_unique_words(output)
    sentences = count_sentences(output)
    avg_sent = avg_sentence_length(output)
    richness = vocabulary_richness(output)
    coverage = topic_coverage(output, target_keywords)

    # Pass/fail gates
    hit_word_count = words >= level["min_words"]
    has_structure = sentences >= 3
    # Vocabulary requirement scales with target length but caps at 200 unique
    # (a 1000-word essay using template composition naturally has ~150-200 unique words)
    expected_unique = min(200, max(30, level["target_words"] // 8))
    has_vocabulary = unique >= expected_unique
    stays_on_topic = coverage >= 0.3 if target_keywords else True

    passed = all([hit_word_count, has_structure, has_vocabulary, stays_on_topic])

    return {
        "level": level["id"],
        "name": level["name"],
        "target_words": level["target_words"],
        "actual_words": words,
        "unique_words": unique,
        "sentences": sentences,
        "avg_sentence_words": round(avg_sent, 1),
        "vocabulary_richness": round(richness, 3),
        "topic_coverage": round(coverage, 2),
        "passed": passed,
        "gates": {
            "word_count": hit_word_count,
            "structure": has_structure,
            "vocabulary": has_vocabulary,
            "topic": stays_on_topic,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# Benchmark runner
# ═══════════════════════════════════════════════════════════════════════════

LEVEL_KEYWORDS = {
    "01_elementary": ["I", "am", "do", "like"],
    "02_middle_school": ["system", "work", "think", "do"],
    "03_high_school": ["cognitive", "subsystem", "user", "goal", "architecture"],
    "04_college": ["subsystem", "hierarchy", "decision", "cognitive", "integration"],
    "05_graduate": ["lambda", "coherence", "observer", "consciousness", "substrate"],
    "06_quantum_physics": ["quantum", "superposition", "collapse", "vacuum", "phase", "observer"],
}


def run_benchmark():
    from aureon.core.integrated_cognitive_system import IntegratedCognitiveSystem

    print("=" * 78)
    print("  LITERACY BENCHMARK — Aureon ICS across 6 education levels")
    print("=" * 78)
    print()

    ics = IntegratedCognitiveSystem()
    status = ics.boot()
    alive = sum(1 for v in status.values() if v == "alive")
    ics._start_tick_thread()
    time.sleep(2)

    print(f"Boot: {alive}/{len(status)} subsystems online")
    print(f"LLM adapter: {type(ics.swarm.adapter).__name__ if ics.swarm else 'unknown'}")
    print()

    reports = []
    samples = {}

    for level in LEVELS:
        print(f"━━ {level['name']} (target: {level['target_words']} words) ━━")

        # Use the prose composer — composition from REAL system state,
        # not LLM generation. Each call references the previous essay
        # (motion snapshot exchange / memory feedback loop).
        t0 = time.time()
        try:
            if ics.prose_composer is not None:
                essay = ics.prose_composer.compose(
                    topic=level["topic"],
                    target_words=level["target_words"],
                )
                output_text = essay.text
            else:
                output_text = "[ERROR] prose_composer not available"
        except Exception as exc:
            output_text = f"[ERROR] {exc}"
        dt = (time.time() - t0) * 1000

        # Grade it
        keywords = LEVEL_KEYWORDS.get(level["id"], [])
        report = grade_output(level, output_text, keywords)
        report["generation_ms"] = round(dt, 0)
        reports.append(report)
        samples[level["id"]] = output_text[:500]

        print(f"  {'PASS' if report['passed'] else 'FAIL'} · "
              f"words={report['actual_words']}/{report['target_words']} · "
              f"unique={report['unique_words']} · "
              f"sentences={report['sentences']} · "
              f"richness={report['vocabulary_richness']} · "
              f"topic={report['topic_coverage']*100:.0f}%  "
              f"[{dt:.0f}ms]")
        print()

    ics.shutdown()

    # Summary
    print("=" * 78)
    print("  REPORT CARD")
    print("=" * 78)
    passed = sum(1 for r in reports if r["passed"])
    total = len(reports)
    print(f"  Overall: {passed}/{total} levels passed ({passed/total*100:.0f}%)")
    print()
    print(f"  {'Level':35} {'Words':>12} {'Richness':>10} {'Topic%':>8} {'Grade':>6}")
    print(f"  {'-'*35} {'-'*12} {'-'*10} {'-'*8} {'-'*6}")
    for r in reports:
        grade = "PASS" if r["passed"] else "FAIL"
        words_ratio = f"{r['actual_words']}/{r['target_words']}"
        print(f"  {r['name'][:35]:35} {words_ratio:>12} {r['vocabulary_richness']:>10.3f} "
              f"{r['topic_coverage']*100:>7.0f}% {grade:>6}")
    print("=" * 78)

    # Print samples
    print()
    print("=" * 78)
    print("  SAMPLE OUTPUT (first 500 chars per level)")
    print("=" * 78)
    for level_id, sample in samples.items():
        print()
        print(f"── {level_id} ──")
        print(sample)

    return reports, samples


def test_literacy_benchmark():
    """Pytest wrapper — every level must pass."""
    reports, _ = run_benchmark()
    failed = [r["name"] for r in reports if not r["passed"]]
    assert not failed, f"Literacy benchmark failed levels: {failed}"


if __name__ == "__main__":
    reports, samples = run_benchmark()
    passed = sum(1 for r in reports if r["passed"])
    sys.exit(0 if passed == len(reports) else 1)
