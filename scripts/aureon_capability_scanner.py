#!/usr/bin/env python3
"""
AUREON CAPABILITY SCANNER
═════════════════════════

Discovers and validates ALL Aureon Python modules, reporting:
- Import status (can the module be imported?)
- Available classes and functions
- Key entry points and CLI capabilities
- Integration bridges (Ollama, Obsidian, World Data)
- Coding skills and architect primitives
- LLM adapters and agent runners

Usage:
    python scripts/aureon_capability_scanner.py
    python scripts/aureon_capability_scanner.py --json
    python scripts/aureon_capability_scanner.py --focus coding,llm,integrations
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "aureon"


@dataclass
class CapabilityModule:
    module_path: str
    import_ok: bool = False
    error: Optional[str] = None
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    has_main: bool = False
    entry_points: List[str] = field(default_factory=list)


@dataclass
class CapabilityReport:
    generated_at: str
    root: str
    total_modules: int = 0
    import_ok: int = 0
    import_failed: int = 0
    modules: List[CapabilityModule] = field(default_factory=list)
    categories: Dict[str, Any] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "root": self.root,
            "total_modules": self.total_modules,
            "import_ok": self.import_ok,
            "import_failed": self.import_failed,
            "modules": [asdict(m) for m in self.modules],
            "categories": self.categories,
            "summary": self.summary,
        }


# Modules we care most about for the murge integration
FOCUS_MODULES: Dict[str, List[str]] = {
    "coding": [
        "aureon.code_architect.architect",
        "aureon.code_architect.executor",
        "aureon.code_architect.observer",
        "aureon.code_architect.skill_library",
        "aureon.code_architect.validator",
        "aureon.code_architect.writer",
        "aureon.autonomous.aureon_repo_task_bridge",
        "aureon.autonomous.aureon_safe_code_control",
        "aureon.core.goal_execution_engine",
    ],
    "llm": [
        "aureon.inhouse_ai.llm_adapter",
        "aureon.inhouse_ai.agent_runner",
        "aureon.inhouse_ai.orchestrator",
        "aureon.inhouse_ai.agent",
        "aureon.inhouse_ai.agent_pool",
        "aureon.inhouse_ai.task_queue",
        "aureon.inhouse_ai.team",
        "aureon.integrations.ollama.ollama_bridge",
        "aureon.integrations.ollama.ollama_adapter",
    ],
    "integrations": [
        "aureon.integrations.obsidian.obsidian_bridge",
        "aureon.integrations.obsidian.obsidian_sink",
        "aureon.integrations.world_data.world_data_ingester",
        "aureon.integrations.wiring",
        "aureon.integrations.audit_trail",
        "aureon.integrations.neural_pathway_mapper",
    ],
    "queen": [
        "aureon.queen.queen_action_bridge",
        "aureon.queen.queen_prose_composer",
        "aureon.queen.self_enhancement_engine",
        "aureon.queen.knowledge_interpreter",
        "aureon.queen.temporal_knowledge",
        "aureon.queen.vault_knowledge_bridge",
        "aureon.queen.conversation_memory",
        "aureon.queen.meaning_resolver",
    ],
    "vault": [
        "aureon.vault.aureon_vault",
        "aureon.vault.voice.vault_voice",
        "aureon.vault.voice.self_dialogue",
        "aureon.vault.auris_metacognition",
        "aureon.vault.self_feedback_loop",
        "aureon.vault.hnc_deployer",
    ],
    "autonomous": [
        "aureon.autonomous.aureon_autonomy_hub",
        "aureon.autonomous.aureon_full_orchestrator",
        "aureon.autonomous.aureon_queen_autonomous",
        "aureon.autonomous.aureon_repo_task_bridge",
        "aureon.autonomous.vm_control.dispatcher",
    ],
}


def discover_modules() -> List[str]:
    modules: List[str] = []
    if not PACKAGE.exists():
        return modules
    for path in PACKAGE.rglob("*.py"):
        if "__pycache__" in path.parts or path.name.startswith("_"):
            continue
        rel = path.relative_to(PACKAGE)
        parts = list(rel.with_suffix("").parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        module_name = "aureon." + ".".join(parts)
        modules.append(module_name)
    return sorted(set(modules))


def scan_module(module_name: str) -> CapabilityModule:
    result = CapabilityModule(module_path=module_name)
    try:
        mod = importlib.import_module(module_name)
        result.import_ok = True
        for name, obj in inspect.getmembers(mod):
            if inspect.isclass(obj) and obj.__module__ == module_name:
                result.classes.append(name)
            elif inspect.isfunction(obj) and obj.__module__ == module_name:
                result.functions.append(name)
        # Check for main block
        source = inspect.getsource(mod)
        result.has_main = '__name__ == "__main__"' in source or "if __name__" in source
    except Exception as exc:
        result.import_ok = False
        result.error = f"{type(exc).__name__}: {exc}"
    return result


def run_scan(args: argparse.Namespace) -> CapabilityReport:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    report = CapabilityReport(
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        root=str(ROOT),
    )

    focus_sets: List[str] = []
    if args.focus:
        focus_sets = [s.strip() for s in args.focus.split(",")]

    if focus_sets:
        module_names = []
        for cat in focus_sets:
            module_names.extend(FOCUS_MODULES.get(cat, []))
        module_names = sorted(set(module_names))
    else:
        module_names = discover_modules()

    report.total_modules = len(module_names)

    for name in module_names:
        mod = scan_module(name)
        report.modules.append(mod)
        if mod.import_ok:
            report.import_ok += 1
        else:
            report.import_failed += 1

    # Build category summaries
    for cat, mods in FOCUS_MODULES.items():
        found = [m for m in report.modules if m.module_path in mods]
        report.categories[cat] = {
            "total": len(mods),
            "import_ok": sum(1 for m in found if m.import_ok),
            "import_failed": sum(1 for m in found if not m.import_ok),
            "modules": [asdict(m) for m in found],
        }

    report.summary = {
        "pass_rate_percent": round(report.import_ok / max(report.total_modules, 1) * 100, 1),
        "coding_ready": report.categories.get("coding", {}).get("import_ok", 0) > 0,
        "llm_ready": report.categories.get("llm", {}).get("import_ok", 0) > 0,
        "integrations_ready": report.categories.get("integrations", {}).get("import_ok", 0) > 0,
        "queen_ready": report.categories.get("queen", {}).get("import_ok", 0) > 0,
        "vault_ready": report.categories.get("vault", {}).get("import_ok", 0) > 0,
        "autonomous_ready": report.categories.get("autonomous", {}).get("import_ok", 0) > 0,
    }

    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="Scan Aureon capabilities")
    ap.add_argument("--json", action="store_true", help="Emit JSON only")
    ap.add_argument("--focus", default="", help="Comma-separated categories: coding,llm,integrations,queen,vault,autonomous")
    args = ap.parse_args()

    report = run_scan(args)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return 0 if report.import_failed == 0 else 1

    print("═══════════════════════════════════════════════════════════════════════════════")
    print("  AUREON CAPABILITY SCANNER")
    print("═══════════════════════════════════════════════════════════════════════════════")
    print(f"  Root: {report.root}")
    print(f"  Modules scanned: {report.total_modules}")
    print(f"  Import OK: {report.import_ok}")
    print(f"  Import failed: {report.import_failed}")
    print(f"  Pass rate: {report.summary['pass_rate_percent']}%")
    print("")

    for cat, data in report.categories.items():
        ok = data["import_ok"]
        total = data["total"]
        status = "✓" if ok == total else "~" if ok > 0 else "✗"
        print(f"  {status} {cat.upper():14} {ok}/{total} modules importable")
        for m in data["modules"]:
            if not m["import_ok"]:
                print(f"      ✗ {m['module_path']}: {m['error'][:80]}")

    print("")
    print("═══════════════════════════════════════════════════════════════════════════════")
    print(f"  CODING:        {'READY' if report.summary['coding_ready'] else 'ATTENTION'}")
    print(f"  LLM:           {'READY' if report.summary['llm_ready'] else 'ATTENTION'}")
    print(f"  INTEGRATIONS:  {'READY' if report.summary['integrations_ready'] else 'ATTENTION'}")
    print(f"  QUEEN:         {'READY' if report.summary['queen_ready'] else 'ATTENTION'}")
    print(f"  VAULT:         {'READY' if report.summary['vault_ready'] else 'ATTENTION'}")
    print(f"  AUTONOMOUS:    {'READY' if report.summary['autonomous_ready'] else 'ATTENTION'}")
    print("═══════════════════════════════════════════════════════════════════════════════")

    return 0 if report.import_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
