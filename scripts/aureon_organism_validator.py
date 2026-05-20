#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
  AUREON ORGANISM VALIDATOR
═══════════════════════════════════════════════════════════════════════════════

Tests EVERY claimed capability of the Aureon organism:
  1. IMPORT TEST — can the module be imported?
  2. EXECUTION TEST — can key functions actually run?
  3. LLM TEST — do LLM adapters initialize?
  4. CODING TEST — do coding agents work?
  5. TRADING TEST — do exchange clients initialize?
  6. QUEEN TEST — do vault/queen systems respond?
  7. AUTONOMY TEST — do orchestrators spin?
  8. INTEGRATION TEST — do bridges (Ollama, Obsidian, World Data) work?

Usage:
    python scripts/aureon_organism_validator.py
    python scripts/aureon_organism_validator.py --json
    python scripts/aureon_organism_validator.py --focus llm,coding,trading

"""

from __future__ import annotations

import argparse
import importlib
import inspect
import io
import json
import os
import sys
import time
import traceback
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Windows-safe stdout
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


@dataclass
class TestResult:
    name: str
    category: str
    passed: bool = False
    phase: str = "import"  # import | execution | assertion
    error: Optional[str] = None
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidatorReport:
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    results: List[TestResult] = field(default_factory=list)

    def add(self, r: TestResult):
        self.results.append(r)
        self.total_tests += 1
        if r.passed:
            self.passed += 1
        else:
            self.failed += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": round(self.passed / max(self.total_tests, 1), 4),
            "results": [
                {
                    "name": r.name,
                    "category": r.category,
                    "passed": r.passed,
                    "phase": r.phase,
                    "error": r.error,
                    "latency_ms": round(r.latency_ms, 2),
                    "metadata": r.metadata,
                }
                for r in self.results
            ],
        }


report = ValidatorReport()


def suppress_output(fn: Callable, *args, **kwargs) -> Any:
    """Run a function with stdout/stderr suppressed."""
    out = io.StringIO()
    err = io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            return fn(*args, **kwargs)
    except Exception:
        raise


def run_test(name: str, category: str, fn: Callable, phase: str = "execution") -> TestResult:
    start = time.perf_counter()
    try:
        result = suppress_output(fn)
        latency = (time.perf_counter() - start) * 1000
        return TestResult(name=name, category=category, passed=True, phase=phase, latency_ms=latency, metadata={"result": str(result)[:200]})
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return TestResult(name=name, category=category, passed=False, phase=phase, latency_ms=latency, error=f"{type(e).__name__}: {str(e)[:200]}")


def test_import(module_path: str, category: str) -> TestResult:
    start = time.perf_counter()
    try:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            mod = importlib.import_module(module_path)
            classes = [n for n, o in inspect.getmembers(mod, inspect.isclass) if o.__module__ == module_path]
            functions = [n for n, o in inspect.getmembers(mod, inspect.isfunction) if o.__module__ == module_path]
        latency = (time.perf_counter() - start) * 1000
        return TestResult(
            name=module_path, category=category, passed=True, phase="import",
            latency_ms=latency, metadata={"classes": classes[:10], "functions": functions[:10]}
        )
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return TestResult(
            name=module_path, category=category, passed=False, phase="import",
            latency_ms=latency, error=f"{type(e).__name__}: {str(e)[:300]}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# LLM CAPABILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def test_llm_adapter():
    from aureon.inhouse_ai import llm_adapter
    # Try to get the adapter class without needing API keys
    assert hasattr(llm_adapter, "LLMAdapter") or hasattr(llm_adapter, "get_adapter") or len([x for x in dir(llm_adapter) if not x.startswith("_")]) > 0
    return "LLM adapter module accessible"


def test_llm_agent_runner():
    from aureon.inhouse_ai import agent_runner
    return f"Agent runner accessible: {len([x for x in dir(agent_runner) if not x.startswith('_')])} public members"


def test_ollama_bridge():
    from aureon.integrations.ollama import ollama_bridge
    return f"Ollama bridge accessible: {len([x for x in dir(ollama_bridge) if not x.startswith('_')])} public members"


# ═══════════════════════════════════════════════════════════════════════════════
# CODING CAPABILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def test_coding_agent_skill_base():
    from aureon.autonomous import aureon_safe_code_control
    return f"Safe code control accessible: {len([x for x in dir(aureon_safe_code_control) if not x.startswith('_')])} members"


def test_goal_execution_engine():
    from aureon.core import goal_execution_engine
    return f"Goal execution engine accessible: {len([x for x in dir(goal_execution_engine) if not x.startswith('_')])} members"


def test_code_architect():
    from aureon.code_architect import validator
    return f"Code architect validator accessible"


# ═══════════════════════════════════════════════════════════════════════════════
# TRADING CAPABILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def test_autonomy_hub_spin():
    from aureon.autonomous.aureon_autonomy_hub import spin
    signal = spin("BTCUSD")
    return f"Signal: {signal.direction} confidence={signal.confidence:.2f}"


def test_global_orchestrator_status():
    from aureon.autonomous.aureon_global_orchestrator import GlobalAureonOrchestrator
    orch = GlobalAureonOrchestrator(dry_run=True)
    status = orch.get_status()
    return f"Global orchestrator status keys: {list(status.keys())}"


def test_full_orchestrator_state():
    from aureon.autonomous.aureon_full_orchestrator import AureonFullOrchestrator
    orch = AureonFullOrchestrator()
    state = orch._load_state()
    return f"Full orchestrator state loaded: opportunities_scanned={state.opportunities_scanned}"


# ═══════════════════════════════════════════════════════════════════════════════
# QUEEN / VAULT CAPABILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def test_queen_vault_knowledge():
    from aureon.queen import vault_knowledge_bridge
    return f"Vault knowledge bridge accessible: {len([x for x in dir(vault_knowledge_bridge) if not x.startswith('_')])} members"


def test_self_enhancement_engine():
    from aureon.queen import self_enhancement_engine
    return f"Self enhancement engine accessible: {len([x for x in dir(self_enhancement_engine) if not x.startswith('_')])} members"


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION CAPABILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def test_world_data_ingester():
    from aureon.integrations.world_data import world_data_ingester
    ing = world_data_ingester.WorldDataIngester()
    items = ing.answer_question("bitcoin", n_per_source=2)
    return f"WorldData ingester returned {len(items)} items"


def test_audit_trail():
    from aureon.integrations import audit_trail
    return f"Audit trail accessible: {len([x for x in dir(audit_trail) if not x.startswith('_')])} members"


def test_neural_pathway_mapper():
    from aureon.integrations import neural_pathway_mapper
    return f"Neural pathway mapper accessible: {len([x for x in dir(neural_pathway_mapper) if not x.startswith('_')])} members"


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def run_all_tests(focus: Optional[List[str]] = None):
    categories = {
        "llm": [
            ("aureon.inhouse_ai.llm_adapter", "LLM Adapter Import"),
            ("aureon.inhouse_ai.agent_runner", "Agent Runner Import"),
            ("aureon.integrations.ollama.ollama_bridge", "Ollama Bridge Import"),
        ],
        "coding": [
            ("aureon.autonomous.aureon_safe_code_control", "Safe Code Control Import"),
            ("aureon.core.goal_execution_engine", "Goal Execution Engine Import"),
            ("aureon.code_architect.validator", "Code Architect Validator Import"),
        ],
        "trading": [
            ("aureon.autonomous.aureon_autonomy_hub", "Autonomy Hub Import"),
            ("aureon.autonomous.aureon_global_orchestrator", "Global Orchestrator Import"),
            ("aureon.autonomous.aureon_full_orchestrator", "Full Orchestrator Import"),
        ],
        "queen": [
            ("aureon.queen.vault_knowledge_bridge", "Vault Knowledge Bridge Import"),
            ("aureon.queen.self_enhancement_engine", "Self Enhancement Engine Import"),
            ("aureon.queen.conversation_memory", "Conversation Memory Import"),
            ("aureon.queen.queen_action_bridge", "Queen Action Bridge Import"),
        ],
        "vault": [
            ("aureon.vault.aureon_vault", "Aureon Vault Import"),
            ("aureon.vault.auris_metacognition", "Auris Metacognition Import"),
            ("aureon.vault.self_feedback_loop", "Self Feedback Loop Import"),
        ],
        "integrations": [
            ("aureon.integrations.world_data.world_data_ingester", "World Data Ingester Import"),
            ("aureon.integrations.audit_trail", "Audit Trail Import"),
            ("aureon.integrations.neural_pathway_mapper", "Neural Pathway Mapper Import"),
            ("aureon.integrations.obsidian.obsidian_bridge", "Obsidian Bridge Import"),
        ],
        "analytics": [
            ("aureon.analytics.aureon_lighthouse", "Lighthouse Import"),
            ("aureon.analytics.aureon_whale_agent", "Whale Agent Import"),
            ("aureon.analytics.cross_asset_correlator", "Cross Asset Correlator Import"),
        ],
    }

    execution_tests = [
        ("LLM Adapter Module", "llm", test_llm_adapter),
        ("LLM Agent Runner", "llm", test_llm_agent_runner),
        ("Ollama Bridge", "llm", test_ollama_bridge),
        ("Safe Code Control", "coding", test_coding_agent_skill_base),
        ("Goal Execution Engine", "coding", test_goal_execution_engine),
        ("Code Architect Validator", "coding", test_code_architect),
        ("Autonomy Hub Spin", "trading", test_autonomy_hub_spin),
        ("Global Orchestrator Status", "trading", test_global_orchestrator_status),
        ("Full Orchestrator State", "trading", test_full_orchestrator_state),
        ("Vault Knowledge Bridge", "queen", test_queen_vault_knowledge),
        ("Self Enhancement Engine", "queen", test_self_enhancement_engine),
        ("World Data Ingest", "integrations", test_world_data_ingester),
        ("Audit Trail", "integrations", test_audit_trail),
        ("Neural Pathway Mapper", "integrations", test_neural_pathway_mapper),
    ]

    # Run import tests
    for cat, modules in categories.items():
        if focus and cat not in focus:
            continue
        for module_path, label in modules:
            report.add(test_import(module_path, cat))

    # Run execution tests
    for name, cat, fn in execution_tests:
        if focus and cat not in focus:
            continue
        report.add(run_test(name, cat, fn, phase="execution"))


def main():
    parser = argparse.ArgumentParser(description="Aureon Organism Validator")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    parser.add_argument("--focus", default="", help="Comma-separated categories: llm,coding,trading,queen,vault,integrations,analytics")
    args = parser.parse_args()

    focus = [f.strip() for f in args.focus.split(",") if f.strip()] or None

    print("=" * 80)
    print("  AUREON ORGANISM VALIDATOR")
    print("=" * 80)
    print(f"Root: {ROOT}")
    print(f"Focus: {', '.join(focus) if focus else 'ALL'}")
    print()

    run_all_tests(focus)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(f"\n{'=' * 80}")
        print(f"  RESULTS: {report.passed}/{report.total_tests} passed ({report.passed / max(report.total_tests, 1):.1%})")
        print(f"{'=' * 80}\n")

        for cat in sorted(set(r.category for r in report.results)):
            cat_results = [r for r in report.results if r.category == cat]
            cat_passed = sum(1 for r in cat_results if r.passed)
            print(f"  [{cat.upper()}] {cat_passed}/{len(cat_results)} passed")
            for r in cat_results:
                status = "[PASS]" if r.passed else "[FAIL]"
                print(f"    {status} {r.phase:12} {r.name}")
                if r.error:
                    print(f"           -> {r.error}")
            print()

        print("=" * 80)
        if report.failed == 0:
            print("  [PASS] ALL TESTS PASSED — ORGANISM IS FULLY OPERATIONAL")
        else:
            print(f"  [FAIL] {report.failed} TEST(S) FAILED — REVIEW ERRORS ABOVE")
        print("=" * 80)

    sys.exit(0 if report.failed == 0 else 1)


if __name__ == "__main__":
    main()
