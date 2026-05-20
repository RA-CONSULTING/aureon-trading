from __future__ import annotations

import argparse
import ast
import importlib
import importlib.util
import json
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


AUDIT_ENV_FLAGS = {
    "AUREON_AUDIT_MODE": "1",
    "AUREON_LIVE_TRADING": "0",
    "AUREON_DISABLE_REAL_ORDERS": "1",
    "AUREON_ALLOW_SIM_FALLBACK": "1",
    "AUREON_QUIET_STARTUP": "1",
}

STATUSES = ("wired", "partial", "broken", "vision_only", "unknown")
FRONTEND_PROBE_PORT = int(os.getenv("AUREON_FRONTEND_PORT") or os.getenv("FRONTEND_PORT") or "8081")

MIND_KEYWORDS = (
    "audit",
    "autonomous",
    "brain",
    "cogn",
    "conscious",
    "decision",
    "goal",
    "hive",
    "kraken_margin",
    "margin",
    "mind",
    "obsidian",
    "ollama",
    "oracle",
    "probability",
    "queen",
    "registry",
    "sentien",
    "self_question",
    "temporal",
    "thought",
    "account",
    "accounting",
    "tax",
    "hmrc",
    "ledger",
    "companies_house",
    "company_house",
    "ct600",
    "contract",
    "work_order",
    "queue",
)

SURFACE_MODULES = (
    {
        "name": "Unified Intelligence Registry",
        "module": "aureon.intelligence.aureon_unified_intelligence_registry",
        "class_name": "UnifiedDataPuller",
        "domain": "registry",
        "purpose": "Registry source of truth for intelligence categories and chain links.",
    },
    {
        "name": "Unified Decision Engine",
        "module": "aureon.intelligence.aureon_unified_decision_engine",
        "class_name": "UnifiedDecisionEngine",
        "domain": "decision",
        "purpose": "Aggregates signals into trading decisions.",
    },
    {
        "name": "ThoughtBus",
        "module": "aureon.core.aureon_thought_bus",
        "class_name": "ThoughtBus",
        "domain": "thought_bus",
        "purpose": "Internal event bus used by cognitive and trading systems.",
    },
    {
        "name": "Organism Contract Stack",
        "module": "aureon.core.organism_contracts",
        "class_name": "OrganismContractStack",
        "domain": "contract_stack",
        "purpose": "Typed internal goal, skill, task, job, and work-order contract queue for whole-organism coordination.",
    },
    {
        "name": "Autonomous Cognition Runtime",
        "module": "aureon.autonomous.aureon_cognition_runtime",
        "class_name": "AureonRuntime",
        "domain": "autonomous",
        "purpose": "Market snapshot to miner/risk/execution runtime.",
    },
    {
        "name": "Seven Phase Cognition Pipeline",
        "module": "aureon.cognition.pipeline",
        "class_name": "CognitionPipeline",
        "domain": "cognition",
        "purpose": "Prompt cognition pipeline that emits phase thoughts.",
    },
    {
        "name": "Queen Cognitive Brain",
        "module": "aureon.autonomous.aureon_cognitive_brain",
        "class_name": "QueenCognitiveBrain",
        "domain": "brain",
        "purpose": "Higher-level Queen cognitive feedback loop.",
    },
    {
        "name": "Queen Hive Mind",
        "module": "aureon.utils.aureon_queen_hive_mind",
        "class_name": "QueenHiveMind",
        "domain": "queen",
        "purpose": "Queen/Hive wiring hub for consciousness and market systems.",
    },
    {
        "name": "Mind Thought Action Hub",
        "module": "aureon.autonomous.aureon_mind_thought_action_hub",
        "class_name": "MindThoughtActionHub",
        "domain": "mind",
        "purpose": "Mind to ThoughtBus to Action visualization/service hub.",
    },
    {
        "name": "Self Questioning AI",
        "module": "aureon.autonomous.aureon_self_questioning_ai",
        "class_name": "SelfQuestioningAI",
        "domain": "autonomous",
        "purpose": "Safe autonomous self-questioning loop backed by Ollama, Obsidian, and ThoughtBus.",
    },
    {
        "name": "Goal Capability Map",
        "module": "aureon.autonomous.aureon_goal_capability_map",
        "class_name": "GoalCapabilityMap",
        "domain": "autonomous",
        "purpose": "Whole-organism goal directive that maps goals to available skills, tools, logic, code systems, memory, and ThoughtBus routes.",
    },
    {
        "name": "Accounting Context Bridge",
        "module": "aureon.queen.accounting_context_bridge",
        "class_name": "AccountingContextBridge",
        "domain": "accounting",
        "purpose": "Single safe read-only interface for final-ready accounting packs, compliance artifacts, vault ingestion, and ThoughtBus accounting status.",
    },
    {
        "name": "Accounting System Registry",
        "module": "Kings_Accounting_Suite.tools.accounting_system_registry",
        "class_name": "AccountingSystemRegistry",
        "domain": "accounting",
        "purpose": "Repo-wide safe inventory of accounting tools, data sources, generated artifacts, and manual filing boundaries.",
    },
    {
        "name": "Company Raw Data Intake",
        "module": "Kings_Accounting_Suite.tools.company_raw_data_intake",
        "class_name": "RawDataManifest",
        "domain": "accounting",
        "purpose": "Safe company raw-data inventory and routing layer for bank, statement, invoice, receipt, compliance, and evidence files.",
    },
    {
        "name": "Accounting Swarm Raw Data Wave Scan",
        "module": "Kings_Accounting_Suite.tools.accounting_swarm_data_wave_scan",
        "class_name": "run_accounting_swarm_data_wave_scan",
        "domain": "accounting",
        "purpose": "Wave-based raw-data sweep that hashes every file, runs provider lookup, folds evidence into the accounting flow, benchmarks the scan, and writes end-user confirmation/checklist artifacts.",
    },
    {
        "name": "Combined Bank Data",
        "module": "Kings_Accounting_Suite.tools.combined_bank_data",
        "class_name": "CombinedBankData",
        "domain": "accounting",
        "purpose": "Normalises all repo-held bank/account CSV exports into a single deduplicated accounting-period feed.",
    },
    {
        "name": "Autonomous Full Accounts Workflow",
        "module": "Kings_Accounting_Suite.tools.autonomous_full_accounts_workflow",
        "class_name": "run_autonomous_full_accounts_workflow",
        "domain": "accounting",
        "purpose": "Coordinates raw intake, bank normalisation, accounting gateway, statutory pack, ThoughtBus, and cognitive goal routing into one safe local accounts workflow.",
    },
    {
        "name": "End-User Accounting Automation",
        "module": "Kings_Accounting_Suite.tools.end_user_accounting_automation",
        "class_name": "run_end_user_accounting_automation",
        "domain": "accounting",
        "purpose": "Top-level raw-data-in/accounts-pack-out wrapper that maps generated artifacts to HMRC and Companies House requirement coverage while keeping filing manual.",
    },
    {
        "name": "Accounting Evidence Authoring",
        "module": "Kings_Accounting_Suite.tools.accounting_evidence_authoring",
        "class_name": "build_accounting_evidence_authoring_pack",
        "domain": "accounting",
        "purpose": "Generates internal evidence requests, petty-cash voucher templates, receipt/invoice prompts, and allocation memos from unified bank data without creating external evidence.",
    },
    {
        "name": "UK Accounting Requirements Brain",
        "module": "Kings_Accounting_Suite.tools.uk_accounting_requirements_brain",
        "class_name": "build_uk_accounting_requirements_brain",
        "domain": "accounting",
        "purpose": "Turns UK HMRC, VAT, UTR, Companies House, PAYE, CIS, and source-data requirements into accountant self-questions and manual filing evidence routes.",
    },
    {
        "name": "Full Company Accounts Generator",
        "module": "Kings_Accounting_Suite.tools.generate_full_company_accounts",
        "class_name": "main",
        "domain": "accounting",
        "purpose": "On-demand final-ready full company accounts generator; does not file with Companies House or HMRC.",
    },
    {
        "name": "Statutory Filing Support Pack",
        "module": "Kings_Accounting_Suite.tools.generate_statutory_filing_pack",
        "class_name": "main",
        "domain": "accounting",
        "purpose": "Builds Companies House final-ready accounts, CT600 manual-entry data, tax computation, and iXBRL readiness notes for manual filing.",
    },
    {
        "name": "Company House Tax Audit",
        "module": "Kings_Accounting_Suite.tools.company_house_tax_audit",
        "class_name": "main",
        "domain": "accounting",
        "purpose": "Read-only company accounts, Companies House, and HMRC compliance audit.",
    },
    {
        "name": "Period Accounts Pack Builder",
        "module": "Kings_Accounting_Suite.tools.build_period_accounts_pack",
        "class_name": "main",
        "domain": "accounting",
        "purpose": "Builds local final-ready accounts pack artifacts for the accounting period.",
    },
    {
        "name": "HNC Gateway",
        "module": "Kings_Accounting_Suite.core.hnc_gateway",
        "class_name": "HNCGateway",
        "domain": "accounting",
        "purpose": "One-button local accounting pipeline orchestration for imports, ledger, reports, and final-ready exports.",
    },
    {
        "name": "HNC Reports",
        "module": "Kings_Accounting_Suite.core.hnc_reports",
        "class_name": "FinancialReport",
        "domain": "accounting",
        "purpose": "Profit and loss, balance sheet, cash flow, aged debtors, CIS, management accounts, and tax summary report logic.",
    },
    {
        "name": "King Ledger",
        "module": "Kings_Accounting_Suite.core.king_ledger",
        "class_name": "KingLedger",
        "domain": "accounting",
        "purpose": "Double-entry bookkeeping and journal core.",
    },
    {
        "name": "King Accounting",
        "module": "Kings_Accounting_Suite.core.king_accounting",
        "class_name": "TheKing",
        "domain": "accounting",
        "purpose": "RoyalTreasury deciphers for transactions, cost basis, P&L, portfolio, tax, and audit alerts.",
    },
    {
        "name": "Kraken Margin Trader",
        "module": "aureon.exchanges.kraken_margin_penny_trader",
        "class_name": "KrakenMarginArmyTrader",
        "domain": "trading_decision",
        "purpose": "Kraken margin decision and execution path.",
    },
    {
        "name": "Unified Margin Brain",
        "module": "aureon.trading.unified_margin_brain",
        "class_name": "UnifiedMarginDecisionBrain",
        "domain": "trading_decision",
        "purpose": "Final margin approve/wait/reject decision layer.",
    },
    {
        "name": "Temporal Trade Cognition",
        "module": "aureon.trading.temporal_trade_cognition",
        "class_name": "TemporalTradeCognition",
        "domain": "temporal",
        "purpose": "Human-time ETA and prediction verification logic for trades.",
    },
    {
        "name": "Dynamic Margin Sizer",
        "module": "aureon.trading.dynamic_margin_sizer",
        "class_name": "DynamicMarginSizer",
        "domain": "margin",
        "purpose": "Collateral-aware margin position sizing.",
    },
)

LOCAL_SERVICE_TARGETS = (
    {
        "id": "frontend.vite",
        "name": "Frontend Vite",
        "url": f"http://127.0.0.1:{FRONTEND_PROBE_PORT}",
        "source": "frontend/vite.config.ts",
    },
    {
        "id": "command_center",
        "name": "Aureon Command Center",
        "url": "http://127.0.0.1:8888/health",
        "source": "aureon/command_centers/aureon_command_center.py",
    },
    {
        "id": "queen_unified_dashboard",
        "name": "Queen Unified Dashboard",
        "url": "http://127.0.0.1:13000/health",
        "source": "aureon/monitors/aureon_queen_unified_dashboard.py",
    },
    {
        "id": "mind_thought_action_hub",
        "name": "Mind Thought Action Hub",
        "url": "http://127.0.0.1:13002",
        "source": "aureon/autonomous/aureon_mind_thought_action_hub.py",
    },
    {
        "id": "system_hub_dashboard",
        "name": "System Hub Dashboard",
        "url": "http://127.0.0.1:13001",
        "source": "aureon/command_centers/aureon_system_hub_dashboard.py",
    },
)

SAFE_ACTUAL_IMPORT_MODULES = {
    "aureon.autonomous.aureon_cognition_runtime",
    "aureon.cognition.pipeline",
    "aureon.core.aureon_thought_bus",
    "aureon.core.organism_contracts",
    "aureon.autonomous.aureon_self_questioning_ai",
    "aureon.autonomous.aureon_goal_capability_map",
    "aureon.trading.dynamic_margin_sizer",
    "aureon.trading.temporal_trade_cognition",
    "aureon.trading.unified_margin_brain",
    "aureon.queen.accounting_context_bridge",
    "Kings_Accounting_Suite.tools.accounting_system_registry",
    "Kings_Accounting_Suite.tools.combined_bank_data",
}

OUTPUT_MD = Path("docs/audits/mind_wiring_audit.md")
OUTPUT_JSON = Path("docs/audits/mind_wiring_audit.json")


class LiveOrderBlocked(RuntimeError):
    """Raised by the audit guard if any probe attempts to place an order."""


@dataclass
class ImportProbe:
    attempted: bool = False
    ok: Optional[bool] = None
    error: str = ""
    symbol_ok: Optional[bool] = None
    symbol_error: str = ""


@dataclass
class MindAuditEntry:
    id: str
    name: str
    domain: str
    sources: List[str]
    declared_module: str
    resolved_module: str = ""
    path: str = ""
    class_name: str = ""
    purpose: str = ""
    status: str = "unknown"
    import_probe: ImportProbe = field(default_factory=ImportProbe)
    evidence: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    event_topics: List[str] = field(default_factory=list)
    decision_path_links: List[str] = field(default_factory=list)
    next_action: str = ""

    def merge(self, other: "MindAuditEntry") -> None:
        for source in other.sources:
            if source not in self.sources:
                self.sources.append(source)
        if not self.name and other.name:
            self.name = other.name
        if not self.domain and other.domain:
            self.domain = other.domain
        if not self.class_name and other.class_name:
            self.class_name = other.class_name
        if not self.purpose and other.purpose:
            self.purpose = other.purpose
        if not self.resolved_module and other.resolved_module:
            self.resolved_module = other.resolved_module
        if not self.path and other.path:
            self.path = other.path
        for attr in ("evidence", "errors", "event_topics", "decision_path_links"):
            existing = getattr(self, attr)
            for item in getattr(other, attr):
                if item and item not in existing:
                    existing.append(item)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["sources"] = sorted(self.sources)
        data["evidence"] = sorted(set(self.evidence))
        data["errors"] = sorted(set(self.errors))
        data["event_topics"] = sorted(set(self.event_topics))
        data["decision_path_links"] = sorted(set(self.decision_path_links))
        return data


@dataclass
class LocalServiceProbe:
    id: str
    name: str
    url: str
    source: str
    status: str
    detail: str = ""
    latency_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MindAuditReport:
    generated_at: str
    repo_root: str
    safety: Dict[str, str]
    counts: Dict[str, int]
    entries: List[MindAuditEntry]
    service_probes: List[LocalServiceProbe] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "repo_root": self.repo_root,
            "safety": dict(self.safety),
            "counts": dict(self.counts),
            "entries": [entry.to_dict() for entry in self.entries],
            "service_probes": [probe.to_dict() for probe in self.service_probes],
            "notes": list(self.notes),
        }


def apply_audit_environment() -> Dict[str, str]:
    """Force safe audit posture before any probe imports trading modules."""

    applied = {}
    for key, value in AUDIT_ENV_FLAGS.items():
        os.environ[key] = value
        applied[key] = value
    return applied


def blocked_order(*args: Any, **kwargs: Any) -> None:
    raise LiveOrderBlocked("mind wiring audit blocked a live order path")


def repo_root_from(start: Optional[Path] = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "aureon").is_dir():
            return candidate
    return Path(__file__).resolve().parents[2]


def _skip_path(path: Path) -> bool:
    skip_parts = {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        ".cache",
        "cache",
        "build",
        "dist",
        "node_modules",
        "output",
        "venv",
    }
    return any(part in skip_parts for part in path.parts)


def iter_python_files(repo_root: Path) -> Iterable[Path]:
    roots = [repo_root / "aureon", repo_root / "Kings_Accounting_Suite"]
    files: List[Path] = []
    for root in roots:
        if root.exists():
            files.extend(path for path in root.rglob("*.py") if not _skip_path(path))
    return files


def module_from_path(repo_root: Path, path: Path) -> str:
    rel = path.resolve().relative_to(repo_root.resolve()).with_suffix("")
    return ".".join(rel.parts)


def build_module_index(repo_root: Path) -> Tuple[Dict[str, List[Tuple[str, str]]], Dict[str, str]]:
    by_stem: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    by_module: Dict[str, str] = {}
    for path in iter_python_files(repo_root):
        module = module_from_path(repo_root, path)
        rel = path.relative_to(repo_root).as_posix()
        by_stem[path.stem].append((module, rel))
        by_module[module] = rel
    return dict(by_stem), by_module


def safe_find_spec(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except Exception:
        return False


def resolve_module_name(
    declared_module: str,
    repo_root: Path,
    by_stem: Dict[str, List[Tuple[str, str]]],
    by_module: Dict[str, str],
) -> Tuple[str, str, List[str]]:
    """Resolve short registry module names to importable package paths."""

    declared = (declared_module or "").strip().replace("/", ".").replace("\\", ".")
    declared = declared[:-3] if declared.endswith(".py") else declared
    evidence: List[str] = []
    if not declared:
        return "", "", evidence

    candidates: List[Tuple[str, str]] = []
    stem = declared.rsplit(".", 1)[-1]
    if declared in by_module:
        candidates.append((declared, by_module[declared]))
    for module, rel_path in by_stem.get(stem, []):
        candidates.append((module, rel_path))

    if not declared.startswith("aureon."):
        prefixed = f"aureon.{declared}"
        if prefixed in by_module:
            candidates.append((prefixed, by_module[prefixed]))

    seen = set()
    unique_candidates = []
    for module, rel_path in candidates:
        if module not in seen:
            unique_candidates.append((module, rel_path))
            seen.add(module)

    if unique_candidates:
        module, rel_path = unique_candidates[0]
        if module != declared:
            evidence.append(f"resolved short module '{declared}' -> '{module}'")
        return module, rel_path, evidence

    return "", "", evidence


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "unknown"


def domain_from_module(module: str, name: str = "") -> str:
    joined = f"{module} {name}".lower()
    if any(token in joined for token in ("account", "tax", "hmrc", "ledger", "ct600", "companies_house", "company_house", "filing")):
        return "accounting"
    if "thought" in joined:
        return "thought_bus"
    if "kraken_margin" in joined or "margin" in joined:
        return "margin"
    if "decision" in joined or "trader" in joined or "executor" in joined:
        return "trading_decision"
    if "queen" in joined:
        return "queen"
    if "brain" in joined:
        return "brain"
    if "cogn" in joined:
        return "cognition"
    if "probability" in joined or "nexus" in joined:
        return "probability"
    if "temporal" in joined or "time" in joined:
        return "temporal"
    if "registry" in joined:
        return "registry"
    if "autonomous" in joined:
        return "autonomous"
    if "hive" in joined or "mind" in joined:
        return "mind"
    return "mind"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def first_doc_line(text: str) -> str:
    try:
        module = ast.parse(text)
        doc = ast.get_docstring(module) or ""
        return doc.strip().splitlines()[0][:240] if doc.strip() else ""
    except Exception:
        match = re.search(r'"""(.*?)"""', text, re.DOTALL)
        if match:
            return match.group(1).strip().splitlines()[0][:240]
    return ""


def ast_profile(path: Path) -> Dict[str, Any]:
    text = read_text(path)
    profile = {
        "classes": [],
        "functions": [],
        "topics": [],
        "imports": [],
        "has_placeholder": False,
        "doc": first_doc_line(text),
    }
    lowered = text.lower()
    profile["has_placeholder"] = any(
        marker in lowered
        for marker in ("todo:", "pass  #", "not implemented", "placeholder", "m0 stub", "stubbed")
    )
    try:
        tree = ast.parse(text, filename=str(path))
    except Exception as exc:
        profile["parse_error"] = str(exc)
        return profile

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            profile["classes"].append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            profile["functions"].append(node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                profile["imports"].append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            profile["imports"].append(node.module)
        elif isinstance(node, ast.Call):
            profile["topics"].extend(_topics_from_call(node))

    profile["classes"] = sorted(set(profile["classes"]))
    profile["functions"] = sorted(set(profile["functions"]))
    profile["imports"] = sorted(set(profile["imports"]))
    profile["topics"] = sorted(set(profile["topics"]))
    return profile


def _string_value(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts = []
        for item in node.values:
            if isinstance(item, ast.Constant) and isinstance(item.value, str):
                parts.append(item.value)
            else:
                parts.append("*")
        return "".join(parts)
    return None


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def _topics_from_call(node: ast.Call) -> List[str]:
    topics: List[str] = []
    call_name = _call_name(node.func)
    if call_name.endswith((".publish", ".subscribe", ".think")):
        if node.args:
            value = _string_value(node.args[0])
            if value:
                topics.append(value)
        for kw in node.keywords:
            if kw.arg == "topic":
                value = _string_value(kw.value)
                if value:
                    topics.append(value)
    if call_name.endswith("Thought"):
        for kw in node.keywords:
            if kw.arg == "topic":
                value = _string_value(kw.value)
                if value:
                    topics.append(value)
    return topics


def import_probe(
    module_name: str,
    class_name: str = "",
    do_imports: bool = True,
    profile: Optional[Dict[str, Any]] = None,
    actual_import: bool = False,
    repo_file_exists: bool = False,
) -> ImportProbe:
    probe = ImportProbe(attempted=do_imports)
    if not do_imports or not module_name:
        return probe

    if not actual_import:
        probe.ok = bool(repo_file_exists)
        if not probe.ok:
            probe.error = "repo module file not found"
            return probe
        if class_name:
            symbols = set((profile or {}).get("classes", [])) | set((profile or {}).get("functions", []))
            probe.symbol_ok = class_name in symbols
            if not probe.symbol_ok:
                probe.symbol_error = f"missing symbol {class_name}"
        return probe

    try:
        module = importlib.import_module(module_name)
        probe.ok = True
    except Exception as exc:
        probe.ok = False
        probe.error = f"{type(exc).__name__}: {exc}"
        return probe

    if class_name:
        if hasattr(module, class_name):
            probe.symbol_ok = True
        else:
            probe.symbol_ok = False
            probe.symbol_error = f"missing symbol {class_name}"
    return probe


def surface_texts(repo_root: Path) -> Dict[str, str]:
    surfaces = [
        "aureon/core/aureon_organism_spine.py",
        "aureon/exchanges/kraken_margin_penny_trader.py",
        "aureon/intelligence/aureon_unified_decision_engine.py",
        "aureon/intelligence/aureon_unified_intelligence_registry.py",
        "aureon/core/aureon_thought_bus.py",
        "aureon/core/organism_contracts.py",
        "aureon/autonomous/aureon_cognition_runtime.py",
        "aureon/cognition/pipeline.py",
        "aureon/autonomous/aureon_cognitive_brain.py",
        "aureon/utils/aureon_queen_hive_mind.py",
        "aureon/autonomous/aureon_mind_thought_action_hub.py",
        "aureon/autonomous/aureon_goal_capability_map.py",
        "aureon/queen/accounting_context_bridge.py",
        "aureon/queen/meaning_resolver.py",
        "aureon/core/integrated_cognitive_system.py",
        "scripts/aureon_ignition.py",
        "Kings_Accounting_Suite/tools/generate_full_company_accounts.py",
        "Kings_Accounting_Suite/tools/company_house_tax_audit.py",
        "Kings_Accounting_Suite/tools/build_period_accounts_pack.py",
    ]
    return {rel: read_text(repo_root / rel) for rel in surfaces}


def build_organism_maps(repo_root: Path) -> Tuple[Dict[str, Any], Dict[str, List[Any]]]:
    try:
        from aureon.core.aureon_organism_spine import build_organism_manifest
    except Exception:
        return {}, {}

    manifest = build_organism_manifest(repo_root=repo_root)
    by_module = manifest.by_module()
    by_stem: Dict[str, List[Any]] = defaultdict(list)
    for node in manifest.nodes:
        by_stem[node.module.rsplit(".", 1)[-1]].append(node)
    return by_module, by_stem


def attach_organism_evidence(
    entry: MindAuditEntry,
    organism_by_module: Dict[str, Any],
    organism_by_stem: Dict[str, List[Any]],
) -> None:
    node = None
    if entry.resolved_module:
        node = organism_by_module.get(entry.resolved_module)
    if node is None and entry.declared_module:
        node = organism_by_module.get(entry.declared_module)
    if node is None:
        stem = (entry.resolved_module or entry.declared_module).rsplit(".", 1)[-1]
        matches = organism_by_stem.get(stem, [])
        if len(matches) == 1:
            node = matches[0]

    if node is None:
        return

    if "organism_spine" not in entry.decision_path_links:
        entry.decision_path_links.append("organism_spine")
    if node.organism_topic not in entry.event_topics:
        entry.event_topics.append(node.organism_topic)
    if "organism_spine" not in entry.sources:
        entry.sources.append("organism_spine")
    entry.evidence.append(
        f"aureon/core/aureon_organism_spine.py registers {node.module} as {node.organism_topic}"
    )


def find_wiring_evidence(entry: MindAuditEntry, surfaces: Dict[str, str]) -> None:
    tokens = {
        entry.declared_module.rsplit(".", 1)[-1],
        entry.resolved_module.rsplit(".", 1)[-1],
        entry.class_name,
    }
    tokens = {token for token in tokens if token}
    for rel, text in surfaces.items():
        if not text:
            continue
        hits = [token for token in tokens if token and token in text]
        if not hits:
            continue
        if "kraken_margin_penny_trader.py" in rel:
            link = "kraken_margin_decision_path"
        elif "aureon_cognition_runtime.py" in rel:
            link = "autonomous_runtime_path"
        elif "pipeline.py" in rel:
            link = "seven_phase_cognition_path"
        elif "aureon_thought_bus.py" in rel:
            link = "thought_bus_core"
        elif "organism_contracts.py" in rel:
            link = "organism_contract_stack"
        elif "aureon_unified_decision_engine.py" in rel:
            link = "unified_decision_engine"
        elif "aureon_unified_intelligence_registry.py" in rel:
            link = "unified_registry"
        elif "queen_hive_mind.py" in rel:
            link = "queen_hive_mind"
        elif "mind_thought_action_hub.py" in rel:
            link = "mind_thought_action_hub"
        elif "accounting_context_bridge.py" in rel:
            link = "accounting_context_bridge"
        elif "generate_full_company_accounts.py" in rel:
            link = "draft_accounts_generator"
        elif "company_house_tax_audit.py" in rel:
            link = "company_house_tax_audit"
        elif "aureon_ignition.py" in rel:
            link = "ignition_preflight"
        else:
            link = rel
        if link not in entry.decision_path_links:
            entry.decision_path_links.append(link)
        entry.evidence.append(f"{rel} references {', '.join(sorted(hits))}")


def classify_entry(entry: MindAuditEntry, profile: Dict[str, Any], is_surface: bool = False) -> None:
    file_exists = bool(entry.path)
    has_topics = bool(entry.event_topics)
    has_wiring = bool(entry.decision_path_links)
    import_ok = entry.import_probe.ok
    symbol_ok = entry.import_probe.symbol_ok
    has_placeholder = bool(profile.get("has_placeholder"))

    if entry.import_probe.attempted and import_ok is False:
        entry.status = "broken"
        entry.errors.append(entry.import_probe.error)
    elif entry.class_name and symbol_ok is False:
        entry.status = "broken"
        entry.errors.append(entry.import_probe.symbol_error)
    elif not file_exists and not entry.resolved_module:
        if has_placeholder or "vision" in entry.purpose.lower() or "planned" in entry.purpose.lower():
            entry.status = "vision_only"
        else:
            entry.status = "broken"
            entry.errors.append("declared module could not be resolved to a repo file or import spec")
    elif has_placeholder and not has_wiring and not has_topics:
        entry.status = "vision_only"
    elif is_surface or has_wiring or (has_topics and import_ok is not False):
        entry.status = "wired"
    elif file_exists or import_ok:
        entry.status = "partial"
    else:
        entry.status = "unknown"

    entry.next_action = next_action_for(entry)


def next_action_for(entry: MindAuditEntry) -> str:
    if entry.status == "wired":
        return "Keep in audit manifest; add runtime health checks if this is critical path."
    if entry.status == "partial":
        return "Connect through ThoughtBus or the unified decision path, then add a focused smoke test."
    if entry.status == "broken":
        if entry.resolved_module:
            return "Fix import/symbol/runtime error or remove the stale registry reference."
        return "Map the registry name to a real module path or mark it vision_only with an owner."
    if entry.status == "vision_only":
        return "Keep as planned capability; do not count as runnable until a module and test exist."
    return "Add evidence, owner, and a concrete wiring target."


def registry_entries(
    repo_root: Path,
    by_stem: Dict[str, List[Tuple[str, str]]],
    by_module: Dict[str, str],
    do_imports: bool,
    profiles: Dict[str, Dict[str, Any]],
    surfaces: Dict[str, str],
    organism_by_module: Optional[Dict[str, Any]] = None,
    organism_by_stem: Optional[Dict[str, List[Any]]] = None,
) -> List[MindAuditEntry]:
    entries: List[MindAuditEntry] = []
    try:
        from aureon.intelligence.aureon_unified_intelligence_registry import CATEGORIES
    except Exception as exc:
        entry = MindAuditEntry(
            id="registry-load-failure",
            name="Unified Intelligence Registry",
            domain="registry",
            sources=["registry"],
            declared_module="aureon.intelligence.aureon_unified_intelligence_registry",
            status="broken",
            errors=[f"{type(exc).__name__}: {exc}"],
            next_action="Fix registry import before full mind audit can trust declared categories.",
        )
        return [entry]

    for category_key, category in CATEGORIES.items():
        for system in category.systems:
            resolved, rel_path, evidence = resolve_module_name(
                system.module,
                repo_root,
                by_stem,
                by_module,
            )
            entry = MindAuditEntry(
                id=slugify(f"registry-{category_key}-{system.name}-{system.module}"),
                name=system.name,
                domain=category_key,
                sources=[f"registry:{category_key}"],
                declared_module=system.module,
                resolved_module=resolved,
                path=rel_path,
                class_name=system.main_class or "",
                purpose=system.purpose or getattr(category, "description", ""),
                event_topics=list(system.thought_bus_topics or []),
                evidence=evidence,
            )
            if resolved and resolved in profiles:
                entry.event_topics = sorted(set(entry.event_topics) | set(profiles[resolved].get("topics", [])))
            attach_organism_evidence(entry, organism_by_module or {}, organism_by_stem or {})
            profile = profiles.get(resolved, {})
            entry.import_probe = import_probe(
                resolved,
                entry.class_name,
                do_imports=do_imports,
                profile=profile,
                actual_import=resolved in SAFE_ACTUAL_IMPORT_MODULES,
                repo_file_exists=bool(rel_path),
            )
            find_wiring_evidence(entry, surfaces)
            classify_entry(entry, profile, is_surface=False)
            entries.append(entry)
    return entries


def overlay_entries(
    repo_root: Path,
    by_stem: Dict[str, List[Tuple[str, str]]],
    by_module: Dict[str, str],
    do_imports: bool,
    profiles: Dict[str, Dict[str, Any]],
    surfaces: Dict[str, str],
    organism_by_module: Optional[Dict[str, Any]] = None,
    organism_by_stem: Optional[Dict[str, List[Any]]] = None,
) -> List[MindAuditEntry]:
    entries: List[MindAuditEntry] = []
    for item in SURFACE_MODULES:
        module = str(item["module"])
        resolved, rel_path, evidence = resolve_module_name(module, repo_root, by_stem, by_module)
        resolved = resolved or module
        rel_path = rel_path or by_module.get(resolved, "")
        profile = profiles.get(resolved, {})
        entry = MindAuditEntry(
            id=slugify(f"surface-{module}"),
            name=str(item["name"]),
            domain=str(item["domain"]),
            sources=["overlay:surface"],
            declared_module=module,
            resolved_module=resolved,
            path=rel_path,
            class_name=str(item.get("class_name") or ""),
            purpose=str(item["purpose"]),
            event_topics=list(profile.get("topics", [])),
            evidence=evidence,
        )
        attach_organism_evidence(entry, organism_by_module or {}, organism_by_stem or {})
        entry.import_probe = import_probe(
            resolved,
            entry.class_name,
            do_imports=do_imports,
            profile=profile,
            actual_import=resolved in SAFE_ACTUAL_IMPORT_MODULES,
            repo_file_exists=bool(rel_path),
        )
        find_wiring_evidence(entry, surfaces)
        classify_entry(entry, profile, is_surface=True)
        entries.append(entry)
    return entries


def discovered_mind_entries(
    repo_root: Path,
    by_module: Dict[str, str],
    do_imports: bool,
    profiles: Dict[str, Dict[str, Any]],
    surfaces: Dict[str, str],
    organism_by_module: Optional[Dict[str, Any]] = None,
    organism_by_stem: Optional[Dict[str, List[Any]]] = None,
) -> List[MindAuditEntry]:
    entries: List[MindAuditEntry] = []
    for module, rel_path in sorted(by_module.items()):
        if not module.startswith("aureon."):
            continue
        haystack = f"{module} {rel_path}".lower()
        if not any(keyword in haystack for keyword in MIND_KEYWORDS):
            continue
        profile = profiles.get(module, {})
        class_name = ""
        classes = profile.get("classes", [])
        if classes:
            class_name = str(classes[0])
        name = module.rsplit(".", 1)[-1]
        entry = MindAuditEntry(
            id=slugify(f"discovery-{module}"),
            name=name,
            domain=domain_from_module(module, name),
            sources=["discovery:keyword_scan"],
            declared_module=module,
            resolved_module=module,
            path=rel_path,
            class_name=class_name,
            purpose=str(profile.get("doc") or "Discovered by mind keyword scan."),
            event_topics=list(profile.get("topics", [])),
        )
        attach_organism_evidence(entry, organism_by_module or {}, organism_by_stem or {})
        entry.import_probe = import_probe(
            module,
            "",
            do_imports=do_imports,
            profile=profile,
            actual_import=module in SAFE_ACTUAL_IMPORT_MODULES,
            repo_file_exists=True,
        )
        find_wiring_evidence(entry, surfaces)
        classify_entry(entry, profile, is_surface=False)
        entries.append(entry)
    return entries


def merge_entries(entries: Sequence[MindAuditEntry]) -> List[MindAuditEntry]:
    merged: Dict[str, MindAuditEntry] = {}
    for entry in entries:
        key = entry.resolved_module or entry.declared_module or entry.id
        if key in merged:
            existing = merged[key]
            previous_status = existing.status
            existing.merge(entry)
            if _status_rank(entry.status) < _status_rank(previous_status):
                existing.status = entry.status
                existing.next_action = next_action_for(existing)
            if entry.import_probe.attempted and not existing.import_probe.attempted:
                existing.import_probe = entry.import_probe
        else:
            merged[key] = entry
    return sorted(merged.values(), key=lambda e: (e.domain, e.status, e.name.lower()))


def _status_rank(status: str) -> int:
    order = {"broken": 0, "partial": 1, "unknown": 2, "vision_only": 3, "wired": 4}
    return order.get(status, 2)


def build_profiles(repo_root: Path, by_module: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
    profiles: Dict[str, Dict[str, Any]] = {}
    for module, rel_path in by_module.items():
        profiles[module] = ast_profile(repo_root / rel_path)
    return profiles


def probe_http_service(target: Dict[str, str], timeout: float = 0.5) -> LocalServiceProbe:
    start = time.monotonic()
    url = target["url"]
    parsed = urllib.parse.urlparse(url)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if host:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                pass
        except (ConnectionRefusedError, TimeoutError, socket.timeout, OSError) as exc:
            detail = str(exc)
            return LocalServiceProbe(
                id=target["id"],
                name=target["name"],
                url=url,
                source=target["source"],
                status="not_running",
                detail=detail[:240] or f"no listener on {host}:{port}",
            )

    try:
        request = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            latency = (time.monotonic() - start) * 1000.0
            return LocalServiceProbe(
                id=target["id"],
                name=target["name"],
                url=url,
                source=target["source"],
                status="reachable",
                detail=f"HTTP {response.status}",
                latency_ms=round(latency, 2),
            )
    except urllib.error.HTTPError as exc:
        latency = (time.monotonic() - start) * 1000.0
        return LocalServiceProbe(
            id=target["id"],
            name=target["name"],
            url=url,
            source=target["source"],
            status="reachable_error_status",
            detail=f"HTTP {exc.code}",
            latency_ms=round(latency, 2),
        )
    except (urllib.error.URLError, TimeoutError, socket.timeout, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        detail = str(reason)
        status = "not_running"
        if "timed out" in detail.lower():
            status = "timeout"
        return LocalServiceProbe(
            id=target["id"],
            name=target["name"],
            url=url,
            source=target["source"],
            status=status,
            detail=detail[:240],
        )


def probe_cognition_runtime() -> LocalServiceProbe:
    try:
        from aureon.autonomous.aureon_cognition_runtime import AureonRuntime

        calls: List[Dict[str, Any]] = []

        def audit_order_guard(**kwargs: Any) -> Dict[str, Any]:
            calls.append(dict(kwargs))
            raise LiveOrderBlocked("audit runtime guard blocked order placement")

        runtime = AureonRuntime(persist_path=None, place_order_fn=audit_order_guard)
        runtime.tick(["AUDIT"], {"AUDIT": {"momentum": 0.0, "gamma": 0.0}})
        if calls:
            return LocalServiceProbe(
                id="cognition.runtime",
                name="Autonomous Cognition Runtime",
                url="in-process://aureon-runtime",
                source="aureon/autonomous/aureon_cognition_runtime.py",
                status="unsafe_order_path",
                detail="Runtime attempted an order during no-signal audit tick.",
            )
        thoughts = runtime.recent_thoughts(limit=10)
        return LocalServiceProbe(
            id="cognition.runtime",
            name="Autonomous Cognition Runtime",
            url="in-process://aureon-runtime",
            source="aureon/autonomous/aureon_cognition_runtime.py",
            status="safe_simulated",
            detail=f"tick completed with {len(thoughts)} in-memory thoughts and no orders",
        )
    except Exception as exc:
        detail = f"{type(exc).__name__}: {exc}"
        status = "blocked_missing_credentials" if "credential" in detail.lower() else "probe_failed"
        return LocalServiceProbe(
            id="cognition.runtime",
            name="Autonomous Cognition Runtime",
            url="in-process://aureon-runtime",
            source="aureon/autonomous/aureon_cognition_runtime.py",
            status=status,
            detail=detail[:240],
        )


def probe_cognition_pipeline() -> LocalServiceProbe:
    try:
        from aureon.cognition.pipeline import CognitionPipeline
        from aureon.core.aureon_thought_bus import ThoughtBus

        bus = ThoughtBus(persist_path=None)
        pipeline = CognitionPipeline(bus=bus)
        env = pipeline.run("audit the whole mind wiring", session_id="mind-audit")
        thoughts = bus.recall(limit=20)
        return LocalServiceProbe(
            id="cognition.pipeline",
            name="Seven Phase Cognition Pipeline",
            url="in-process://cognition-pipeline",
            source="aureon/cognition/pipeline.py",
            status="safe_simulated",
            detail=f"trace={env.trace_id} thoughts={len(thoughts)} errors={len(env.errors)}",
        )
    except Exception as exc:
        return LocalServiceProbe(
            id="cognition.pipeline",
            name="Seven Phase Cognition Pipeline",
            url="in-process://cognition-pipeline",
            source="aureon/cognition/pipeline.py",
            status="probe_failed",
            detail=f"{type(exc).__name__}: {exc}"[:240],
        )


def probe_accounting_context() -> LocalServiceProbe:
    try:
        from aureon.queen.accounting_context_bridge import get_accounting_context_bridge

        bridge = get_accounting_context_bridge()
        status = bridge.status()
        context = bridge.load_context()
        safety = context.get("safety") or {}
        readiness = status.get("accounting_readiness") or {}
        statutory = status.get("statutory_filing_pack") or {}
        raw_summary = ((status.get("raw_data_manifest") or {}).get("summary") or {})
        workflow = status.get("autonomous_workflow") or {}
        cognitive = workflow.get("cognitive_review") or status.get("cognitive_review") or {}
        vault_memory = workflow.get("vault_memory") or status.get("vault_memory") or {}
        handoff_pack = status.get("human_filing_handoff_pack") or workflow.get("human_filing_handoff_pack") or {}
        handoff_readiness = handoff_pack.get("readiness") or {}
        evidence_authoring = (
            status.get("accounting_evidence_authoring")
            or handoff_pack.get("accounting_evidence_authoring")
            or workflow.get("accounting_evidence_authoring")
            or {}
        )
        evidence_summary = evidence_authoring.get("summary") or {}
        llm_authoring = evidence_authoring.get("llm_document_authoring") or evidence_summary.get("llm_document_authoring") or {}
        end_user = status.get("end_user_accounting_automation") or {}
        end_user_coverage = end_user.get("requirement_coverage") or []
        end_user_generated = sum(
            1
            for item in end_user_coverage
            if str(item.get("status", "")).startswith("generated")
            or str(item.get("status", "")).startswith("final_ready")
        )
        swarm_scan = status.get("swarm_raw_data_wave_scan") or {}
        swarm_benchmark = swarm_scan.get("benchmark") or {}
        swarm_consensus = ((swarm_scan.get("waves") or {}).get("phi_swarm_consensus") or {})
        end_user_confirmation = status.get("end_user_confirmation") or {}
        confirmation_payload = end_user_confirmation.get("confirmation") or end_user_confirmation
        uk_brain = (
            status.get("uk_accounting_requirements_brain")
            or handoff_pack.get("uk_accounting_requirements_brain")
            or workflow.get("uk_accounting_requirements_brain")
            or {}
        )
        uk_summary = uk_brain.get("summary") or {}
        uk_figures = uk_brain.get("figures") or {}
        unsafe = any(
            bool(safety.get(key))
            for key in ("submits_to_companies_house", "submits_to_hmrc", "pays_tax_or_penalties")
        )
        if unsafe:
            return LocalServiceProbe(
                id="accounting.context",
                name="Accounting Context Bridge",
                url="in-process://accounting-context",
                source="aureon/queen/accounting_context_bridge.py",
                status="unsafe_order_path",
                detail="Accounting safety flags indicate external filing/payment would be allowed.",
            )
        return LocalServiceProbe(
            id="accounting.context",
            name="Accounting Context Bridge",
            url="in-process://accounting-context",
            source="aureon/queen/accounting_context_bridge.py",
            status="safe_simulated",
            detail=(
                f"company={status.get('company_number')} "
                f"build={status.get('accounts_build_status')} "
                f"overdue={status.get('overdue_count', 0)} "
                f"manual_filing={status.get('manual_filing_required')} "
                f"tools={(status.get('accounting_system_registry') or {}).get('module_count', 0)} "
                f"bank_sources={(status.get('combined_bank_data') or {}).get('transaction_source_count', (status.get('combined_bank_data') or {}).get('csv_source_count', 0))} "
                f"ready={readiness.get('ready', 'unknown')} "
                f"statutory_outputs={len(statutory.get('outputs') or {})} "
                f"raw_files={raw_summary.get('file_count', 0)} "
                f"autonomous={workflow.get('status', 'unknown')} "
                f"handoff={handoff_pack.get('status', 'unknown')} "
                f"handoff_ready={handoff_readiness.get('ready_for_manual_upload', handoff_readiness.get('ready_for_manual_review', 'unknown'))} "
                f"evidence_requests={evidence_summary.get('draft_count', 0)} "
                f"evidence_docs={evidence_summary.get('generated_document_count', 0)} "
                f"llm_docs={llm_authoring.get('completed_count', 0)} "
                f"llm_status={llm_authoring.get('status', 'unknown')} "
                f"end_user={end_user.get('status', 'unknown')} "
                f"end_user_coverage={end_user_generated}/{len(end_user_coverage)} "
                f"swarm_files={swarm_benchmark.get('files_scanned', 0)} "
                f"swarm_consensus={swarm_consensus.get('status', 'unknown')} "
                f"end_user_confirmed={len(confirmation_payload.get('what_aureon_confirmed') or [])} "
                f"uk_requirements={uk_summary.get('requirement_count', 0)} "
                f"uk_questions={uk_summary.get('question_count', 0)} "
                f"vat_over_threshold={uk_figures.get('turnover_over_vat_threshold', 'unknown')} "
                f"vault_memory={vault_memory.get('status', 'unknown')} "
                f"self_questioning={cognitive.get('status', 'unknown')}"
            ),
        )
    except Exception as exc:
        detail = f"{type(exc).__name__}: {exc}"
        status = "blocked_missing_credentials" if "credential" in detail.lower() else "probe_failed"
        return LocalServiceProbe(
            id="accounting.context",
            name="Accounting Context Bridge",
            url="in-process://accounting-context",
            source="aureon/queen/accounting_context_bridge.py",
            status=status,
            detail=detail[:240],
        )


def local_service_probes(enabled: bool) -> List[LocalServiceProbe]:
    if not enabled:
        return []
    probes = [probe_http_service(target) for target in LOCAL_SERVICE_TARGETS]
    probes.append(probe_cognition_runtime())
    probes.append(probe_cognition_pipeline())
    probes.append(probe_accounting_context())
    return probes


def count_statuses(entries: Sequence[MindAuditEntry]) -> Dict[str, int]:
    counts = Counter(entry.status for entry in entries)
    result = {status: counts.get(status, 0) for status in STATUSES}
    result["total"] = len(entries)
    return result


def build_report(
    repo_root: Optional[Path] = None,
    do_static: bool = True,
    do_imports: bool = True,
    do_local_services: bool = False,
) -> MindAuditReport:
    root = repo_root_from(repo_root)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    safety = apply_audit_environment()
    by_stem, by_module = build_module_index(root)
    profiles = build_profiles(root, by_module) if do_static else {}
    surfaces = surface_texts(root) if do_static else {}
    organism_by_module, organism_by_stem = build_organism_maps(root)

    entries: List[MindAuditEntry] = []
    entries.extend(
        registry_entries(
            root,
            by_stem,
            by_module,
            do_imports,
            profiles,
            surfaces,
            organism_by_module,
            organism_by_stem,
        )
    )
    entries.extend(
        overlay_entries(
            root,
            by_stem,
            by_module,
            do_imports,
            profiles,
            surfaces,
            organism_by_module,
            organism_by_stem,
        )
    )
    entries.extend(
        discovered_mind_entries(
            root,
            by_module,
            do_imports,
            profiles,
            surfaces,
            organism_by_module,
            organism_by_stem,
        )
    )
    merged = merge_entries(entries)
    probes = local_service_probes(do_local_services)

    notes = [
        "Audit mode forced live trading off and real order placement disabled.",
        f"Organism spine registered {len(organism_by_module)} repo modules into shared organism topics.",
        "Vision-only systems are listed for planning but are not counted as runnable.",
        "Local service probing checks existing localhost endpoints and safe in-process simulations; it does not place exchange orders.",
        "Accounting probing is read-only; final-ready accounts generation is on demand and official Companies House/HMRC filing stays manual.",
    ]
    if not do_imports:
        notes.append("Import checks were skipped for this run.")
    if not do_local_services:
        notes.append("Local service probes were skipped for this run.")

    return MindAuditReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        repo_root=str(root),
        safety=safety,
        counts=count_statuses(merged),
        entries=merged,
        service_probes=probes,
        notes=notes,
    )


def render_markdown(report: MindAuditReport) -> str:
    lines: List[str] = []
    lines.append("# Aureon Whole-Mind Wiring Audit")
    lines.append("")
    lines.append(f"- Generated: `{report.generated_at}`")
    lines.append(f"- Repo: `{report.repo_root}`")
    lines.append("- Safety: audit mode on, live trading off, real orders disabled")
    lines.append("")
    lines.append("## Status Summary")
    lines.append("")
    for status in STATUSES:
        lines.append(f"- `{status}`: {report.counts.get(status, 0)}")
    lines.append(f"- `total`: {report.counts.get('total', 0)}")
    lines.append("")

    if report.service_probes:
        lines.append("## Local Service Probes")
        lines.append("")
        lines.append("| Service | Status | Target | Detail |")
        lines.append("| --- | --- | --- | --- |")
        for probe in report.service_probes:
            detail = probe.detail.replace("|", "\\|")
            lines.append(f"| {probe.name} | `{probe.status}` | `{probe.url}` | {detail} |")
        lines.append("")

    lines.append("## Wiring Checklist")
    lines.append("")
    by_domain: Dict[str, List[MindAuditEntry]] = defaultdict(list)
    for entry in report.entries:
        by_domain[entry.domain].append(entry)

    for domain in sorted(by_domain):
        lines.append(f"### {domain}")
        lines.append("")
        lines.append("| Status | System | Module | Evidence | Next action |")
        lines.append("| --- | --- | --- | --- | --- |")
        for entry in sorted(by_domain[domain], key=lambda e: (e.status, e.name.lower())):
            module = entry.resolved_module or entry.declared_module or ""
            evidence = "; ".join(entry.evidence[:2] or entry.decision_path_links[:2] or entry.event_topics[:2])
            if len(evidence) > 180:
                evidence = evidence[:177] + "..."
            evidence = evidence.replace("|", "\\|")
            next_action = entry.next_action.replace("|", "\\|")
            lines.append(
                f"| `{entry.status}` | {entry.name} | `{module}` | {evidence or 'No wiring evidence found'} | {next_action} |"
            )
        lines.append("")

    broken = [entry for entry in report.entries if entry.status == "broken"]
    if broken:
        lines.append("## Broken Or Unresolved")
        lines.append("")
        for entry in broken[:80]:
            module = entry.resolved_module or entry.declared_module
            error = "; ".join(entry.errors[:2]) or "unresolved"
            lines.append(f"- `{entry.name}` (`{module}`): {error}")
        if len(broken) > 80:
            lines.append(f"- ... {len(broken) - 80} more broken entries in JSON manifest")
        lines.append("")

    partial = [entry for entry in report.entries if entry.status == "partial"]
    if partial:
        lines.append("## Highest Priority Wiring Gaps")
        lines.append("")
        for entry in partial[:30]:
            module = entry.resolved_module or entry.declared_module
            lines.append(f"- `{entry.name}` (`{module}`): {entry.next_action}")
        lines.append("")

    lines.append("## Notes")
    lines.append("")
    for note in report.notes:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def write_report(report: MindAuditReport, markdown_path: Path = OUTPUT_MD, json_path: Path = OUTPUT_JSON) -> None:
    root = Path(report.repo_root)
    md_path = markdown_path if markdown_path.is_absolute() else root / markdown_path
    js_path = json_path if json_path.is_absolute() else root / json_path
    md_path.parent.mkdir(parents=True, exist_ok=True)
    js_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_markdown(report), encoding="utf-8")
    js_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit Aureon's whole-mind cognitive wiring.")
    parser.add_argument("--repo-root", default="", help="Repo root; defaults to current repo.")
    parser.add_argument("--static", action="store_true", default=False, help="Run static AST/topic scans.")
    parser.add_argument("--imports", action="store_true", default=False, help="Run import and symbol checks.")
    parser.add_argument("--local-services", action="store_true", default=False, help="Probe local services safely.")
    parser.add_argument("--no-write", action="store_true", help="Print JSON summary without writing artifacts.")
    parser.add_argument("--markdown", default=str(OUTPUT_MD), help="Markdown report path.")
    parser.add_argument("--json", default=str(OUTPUT_JSON), help="JSON manifest path.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from()
    do_static = args.static or not (args.static or args.imports or args.local_services)
    do_imports = args.imports or not (args.static or args.imports or args.local_services)
    do_services = args.local_services
    report = build_report(
        repo_root=root,
        do_static=do_static,
        do_imports=do_imports,
        do_local_services=do_services,
    )
    if not args.no_write:
        write_report(report, Path(args.markdown), Path(args.json))

    print(json.dumps({"counts": report.counts, "service_probes": [p.to_dict() for p in report.service_probes]}, indent=2))
    unsafe = [probe for probe in report.service_probes if probe.status == "unsafe_order_path"]
    return 2 if unsafe else 0


if __name__ == "__main__":
    raise SystemExit(main())
