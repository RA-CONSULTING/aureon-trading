"""Aureon coding-agent skill base and web-learning map.

This module teaches Aureon how to see its coding capability as a living
system:

repo code -> skill library -> coder agents -> web/repo learning sources
-> improvement work orders -> CodeArchitect/Queen writer -> tests/retest.

It is evidence-only by default. Online probes are read-only and optional.
No exchange mutation, filing, payment, credential reveal, or arbitrary code
application happens here.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

from aureon.autonomous.aureon_saas_system_inventory import repo_root_from

try:
    from aureon.queen.queen_code_architect import QueenCodeArchitect
except Exception:  # pragma: no cover
    QueenCodeArchitect = None  # type: ignore[assignment]


SCHEMA_VERSION = "aureon-coding-agent-skill-base-v2"
DEFAULT_OUTPUT_JSON = Path("docs/audits/aureon_coding_agent_skill_base.json")
DEFAULT_OUTPUT_MD = Path("docs/audits/aureon_coding_agent_skill_base.md")
DEFAULT_PUBLIC_JSON = Path("frontend/public/aureon_coding_agent_skill_base.json")
DEFAULT_STATE_PATH = Path("state/aureon_coding_agent_skill_base_last_run.json")
DEFAULT_VAULT_NOTE = Path(".obsidian/Aureon Self Understanding/aureon_coding_agent_skill_base.md")
DEFAULT_COMPONENT = Path("frontend/src/components/generated/AureonCodingAgentSkillBaseConsole.tsx")
DEFAULT_APP_PATH = Path("frontend/src/App.tsx")

IGNORED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "queen_backups",
}

CODE_EXTENSIONS = {
    ".py": "python",
    ".tsx": "react_typescript",
    ".ts": "typescript",
    ".jsx": "react_javascript",
    ".js": "javascript",
    ".ps1": "powershell",
    ".cmd": "windows_batch",
    ".json": "json_contract",
    ".md": "documentation",
    ".html": "html",
    ".css": "css",
    ".sql": "sql",
}

OFFICIAL_LEARNING_SOURCES = [
    {
        "id": "python_docs",
        "title": "Python documentation",
        "url": "https://docs.python.org/3/",
        "skill_domains": ["python", "testing", "tooling"],
    },
    {
        "id": "pytest_docs",
        "title": "pytest documentation",
        "url": "https://docs.pytest.org/",
        "skill_domains": ["testing", "quality_gate"],
    },
    {
        "id": "typescript_docs",
        "title": "TypeScript handbook",
        "url": "https://www.typescriptlang.org/docs/",
        "skill_domains": ["typescript", "frontend"],
    },
    {
        "id": "react_docs",
        "title": "React documentation",
        "url": "https://react.dev/learn",
        "skill_domains": ["react", "frontend"],
    },
    {
        "id": "vite_docs",
        "title": "Vite guide",
        "url": "https://vite.dev/guide/",
        "skill_domains": ["frontend", "build"],
    },
    {
        "id": "owasp_asvs",
        "title": "OWASP ASVS project",
        "url": "https://owasp.org/www-project-application-security-verification-standard/",
        "skill_domains": ["security", "review"],
    },
    {
        "id": "binance_api_docs",
        "title": "Binance API documentation",
        "url": "https://developers.binance.com/docs",
        "skill_domains": ["exchange_api", "market_data"],
    },
    {
        "id": "kraken_api_docs",
        "title": "Kraken API documentation",
        "url": "https://docs.kraken.com/api/",
        "skill_domains": ["exchange_api", "market_data"],
    },
    {
        "id": "alpaca_api_docs",
        "title": "Alpaca API documentation",
        "url": "https://docs.alpaca.markets/",
        "skill_domains": ["exchange_api", "market_data"],
    },
]

WEB_LEARNING_QUERIES = [
    {
        "id": "python_ast_safe_transform",
        "query": "official Python ast documentation safe code transformation",
        "why": "Improve safe code analysis and patch validation.",
    },
    {
        "id": "react_accessible_dashboard_patterns",
        "query": "React official docs accessible dashboard component patterns",
        "why": "Improve frontend console components and UI smoke tests.",
    },
    {
        "id": "pytest_fixture_patterns",
        "query": "pytest official documentation fixtures monkeypatch tmp_path",
        "why": "Improve generated tests for Aureon self-repair work.",
    },
    {
        "id": "exchange_api_rate_limits",
        "query": "official Binance Kraken Alpaca API rate limits documentation",
        "why": "Teach coder agents to preserve market-data governor logic.",
    },
]


@dataclass
class CoderAgentRole:
    name: str
    purpose: str
    owns: list[str]
    reads: list[str]
    writes: list[str]
    tools: list[str]
    evidence_required: list[str]
    safety_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CodingWorkOrder:
    id: str
    title: str
    status: str
    priority: int
    owner_agent: str
    reason: str
    proposed_action: str
    validation: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CodingLogicRule:
    id: str
    who: list[str]
    what: str
    where: list[str]
    when: list[str]
    how: list[str]
    validation: list[str]
    evidence: list[str]
    safety_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}", "path": str(path)}


def _iter_repo_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORED_DIRS for part in path.relative_to(root).parts):
            continue
        if path.suffix.lower() in CODE_EXTENSIONS:
            files.append(path)
    return files


def classify_repo_code(root: Path) -> dict[str, Any]:
    files = _iter_repo_files(root)
    by_language: Counter[str] = Counter()
    by_domain: Counter[str] = Counter()
    examples: dict[str, list[str]] = {}
    for path in files:
        rel = path.relative_to(root).as_posix()
        language = CODE_EXTENSIONS.get(path.suffix.lower(), "other")
        by_language[language] += 1
        domain = _domain_for_path(rel)
        by_domain[domain] += 1
        examples.setdefault(domain, [])
        if len(examples[domain]) < 8:
            examples[domain].append(rel)
    return {
        "file_count": len(files),
        "by_language": dict(sorted(by_language.items())),
        "by_domain": dict(sorted(by_domain.items())),
        "examples": dict(sorted(examples.items())),
    }


def _domain_for_path(rel: str) -> str:
    text = rel.lower()
    if text.startswith("frontend/") or "/components/" in text or text.endswith((".tsx", ".css")):
        return "frontend"
    if "exchange" in text or "trading" in text or "kraken" in text or "binance" in text or "alpaca" in text:
        return "trading"
    if "account" in text or "hmrc" in text or "ct600" in text:
        return "accounting"
    if "test" in text or "pytest" in text:
        return "testing"
    if "code_architect" in text or "safe_code" in text:
        return "code_architect"
    if "security" in text or "auth" in text or "kyc" in text:
        return "security"
    if "voice" in text or "vault" in text or "knowledge" in text:
        return "knowledge_voice"
    if "autonomous" in text or "goal" in text or "agent" in text:
        return "autonomy"
    return "core"


def skill_library_snapshot(root: Path) -> dict[str, Any]:
    snapshots: list[dict[str, Any]] = []
    for storage_dir in (root / "state" / "skills", root / "state" / "capability_growth_skills"):
        library_path = storage_dir / "skill_library.json"
        raw = load_json(library_path)
        skills = raw.get("skills") if isinstance(raw.get("skills"), list) else []
        by_level = Counter(str(item.get("level_name") or item.get("level") or "unknown") for item in skills if isinstance(item, dict))
        by_status = Counter(str(item.get("status") or "unknown") for item in skills if isinstance(item, dict))
        snapshots.append(
            {
                "storage_dir": storage_dir.as_posix(),
                "library_path": library_path.as_posix(),
                "exists": library_path.exists(),
                "count": len(skills),
                "by_level": dict(sorted(by_level.items())),
                "by_status": dict(sorted(by_status.items())),
                "examples": [
                    {
                        "name": item.get("name"),
                        "level": item.get("level_name") or item.get("level"),
                        "status": item.get("status"),
                        "category": item.get("category"),
                    }
                    for item in skills[:12]
                    if isinstance(item, dict)
                ],
            }
        )
    return {
        "libraries": snapshots,
        "total_skill_count": sum(int(item.get("count") or 0) for item in snapshots),
    }


def tool_registry_snapshot(root: Path) -> dict[str, Any]:
    names: list[str] = []
    agent_core_intents: list[str] = []
    errors: list[str] = []
    try:
        from aureon.inhouse_ai.tool_registry import ToolRegistry

        registry = ToolRegistry(include_builtins=True)
        names = sorted(registry.names())
    except Exception as exc:
        errors.append(f"ToolRegistry: {type(exc).__name__}: {exc}")

    try:
        from aureon.autonomous.aureon_agent_core import INTENT_MAP

        agent_core_intents = sorted(set(INTENT_MAP.values()))
    except Exception as exc:
        errors.append(f"AureonAgentCore: {type(exc).__name__}: {exc}")

    required = ["web_search", "web_fetch", "repo_search", "execute_shell", "skill_base_status"]
    return {
        "inhouse_tool_count": len(names),
        "inhouse_tools": names,
        "agent_core_intents": agent_core_intents,
        "required_coder_tools": required,
        "missing_required_coder_tools": [name for name in required if name not in names],
        "errors": errors,
    }


def coder_agent_roles() -> list[CoderAgentRole]:
    return [
        CoderAgentRole(
            name="RepoCartographer",
            purpose="Map existing code, tests, generated reports, and ownership boundaries before any edit.",
            owns=["repo map", "dependency hints", "path evidence"],
            reads=["aureon/**", "frontend/src/**", "tests/**", "docs/audits/**"],
            writes=["docs/audits/aureon_coding_agent_skill_base.json"],
            tools=["repo_search", "read_state", "skill_base_status"],
            evidence_required=["path list", "source count", "domain classification"],
            safety_boundary="Read-only except its own audit manifests.",
        ),
        CoderAgentRole(
            name="WebLearningScout",
            purpose="Use web_search and web_fetch to learn from official docs and open-source API documentation.",
            owns=["learning queries", "source summaries", "freshness evidence"],
            reads=["official docs", "public API docs", "repo manifests"],
            writes=["docs/audits/aureon_coding_agent_skill_base.md"],
            tools=["web_search", "web_fetch", "publish_thought"],
            evidence_required=["source url", "fetch status", "why source was relevant"],
            safety_boundary="Read-only online learning; no code copied blindly and no credential transmission.",
        ),
        CoderAgentRole(
            name="ImplementationWorker",
            purpose="Turn approved work orders into scoped code patches through CodeArchitect and QueenCodeArchitect.",
            owns=["implementation patch", "generated component or module", "authoring evidence"],
            reads=["repo map", "tests", "coding standards", "source manifests"],
            writes=["aureon/**", "frontend/src/**", "tests/**"],
            tools=["repo_search", "execute_shell", "skill_base_status"],
            evidence_required=["diff summary", "writer provenance", "validation command"],
            safety_boundary="Repo writes must be scoped and retested; no live trading or external mutation.",
        ),
        CoderAgentRole(
            name="TestPilot",
            purpose="Run compile, unit, frontend build, and smoke checks after each code change.",
            owns=["test plan", "test output", "regression risk"],
            reads=["tests/**", "package.json", "docs/audits/**"],
            writes=["docs/audits/aureon_repo_self_repair.json"],
            tools=["execute_shell", "repo_search"],
            evidence_required=["command", "return code", "stdout/stderr tail"],
            safety_boundary="Can run local tests/builds only; no destructive shell operations.",
        ),
        CoderAgentRole(
            name="SecurityReviewer",
            purpose="Check generated code for credential exposure, unsafe mutation, and missing evidence gates.",
            owns=["security review", "safety blocker records", "redaction checks"],
            reads=["repo_search", "public manifests", "tests"],
            writes=["docs/audits/security review notes"],
            tools=["repo_search", "execute_shell"],
            evidence_required=["blocked pattern scan", "secret redaction result"],
            safety_boundary="May report blockers; may not bypass payment, filing, credential, or live-order boundaries.",
        ),
    ]


def coding_logic_rules() -> list[CodingLogicRule]:
    return [
        CodingLogicRule(
            id="frontend.interface_logic",
            who=["RepoCartographer", "ImplementationWorker", "TestPilot"],
            what="React/TypeScript interface work, generated console panels, hooks, services, styling, and browser smoke checks.",
            where=["frontend/src/App.tsx", "frontend/src/components/**", "frontend/src/hooks/**", "frontend/src/services/**", "frontend/public/*.json"],
            when=[
                "A goal asks for a visible console, operational dashboard, adapter, or human-readable status surface.",
                "A public JSON manifest already exists or the task creates one through QueenCodeArchitect.",
                "The frontend build or browser smoke check is part of the acceptance evidence.",
            ],
            how=[
                "Read the public manifest contract before rendering UI fields.",
                "Prefer generated read-only operational cards for system evidence.",
                "Mount new generated panels from App.tsx and keep imports explicit.",
                "Run npm build or a focused browser smoke check after UI edits.",
            ],
            validation=["npm run build", "browser smoke test on the local console", "public manifest loads with no stale fake state"],
            evidence=["frontend/public manifest path", "generated component path", "App.tsx mount line", "build or smoke-test result"],
            safety_boundary="Frontend panels may display evidence and operator actions only; they may not reveal secrets or bypass runtime gates.",
        ),
        CodingLogicRule(
            id="backend.autonomous_logic",
            who=["RepoCartographer", "ImplementationWorker", "SecurityReviewer", "TestPilot"],
            what="Python autonomous modules, goal routing, self-repair, observer refresh, mind hub, and coding-agent orchestration.",
            where=["aureon/autonomous/**", "aureon/core/goal_execution_engine.py", "aureon/inhouse_ai/**", "tests/test_*"],
            when=[
                "A goal needs a new internal capability, agent skill, repo-learning loop, or evidence-producing workflow.",
                "Existing goal routes cannot classify the operator request accurately.",
                "The change needs repeatable local tests and a state/audit artifact.",
            ],
            how=[
                "Classify the request into an intent before writing code.",
                "Add the smallest module or route that fits existing GoalExecutionEngine patterns.",
                "Emit state, docs/audits, and frontend/public evidence when the capability is user-visible.",
                "Add focused pytest coverage for routing, files written, and validation semantics.",
            ],
            validation=["python -m compileall", "focused pytest for the route/module", "GoalExecutionEngine validation result is valid"],
            evidence=["goal id", "intent", "authoring path", "state artifact", "test command"],
            safety_boundary="Autonomous logic may author repo files through QueenCodeArchitect, but external mutations remain outside this layer.",
        ),
        CodingLogicRule(
            id="trading.exchange_logic",
            who=["RepoCartographer", "WebLearningScout", "SecurityReviewer", "TestPilot"],
            what="Exchange clients, market telemetry, rate governors, flight tests, stale-data logic, and order-intent evidence.",
            where=["aureon/exchanges/**", "aureon/bots/**", "state/unified_runtime_status.json", "tests/test_unified_market_status_server.py"],
            when=[
                "A task changes Binance, Kraken, Alpaca, Capital, spot, margin, market data, or trading readiness logic.",
                "Official exchange documentation or rate-limit behavior may have changed.",
                "The runtime reports stale ticks, guard blockers, or missing exchange coverage.",
            ],
            how=[
                "Use WebLearningScout to fetch official exchange docs before changing client behavior.",
                "Preserve stale-data, open-position, rate-limit, and reboot-window evidence.",
                "Separate shadow-trade validation from live order mutation.",
                "Expose status through the runtime manifest and console rather than hidden logs only.",
            ],
            validation=["flight-test endpoint", "unified market status tests", "API governor utilization evidence", "shadow-trade reconciliation"],
            evidence=["official docs url", "exchange client path", "runtime status snapshot", "shadow/live mode field"],
            safety_boundary="Trading code can improve observation, shadow validation, and gated order intent; it cannot remove exchange/risk/runtime gates.",
        ),
        CodingLogicRule(
            id="accounting.legal_pack_logic",
            who=["RepoCartographer", "WebLearningScout", "SecurityReviewer", "TestPilot"],
            what="UK accounting, HMRC/Companies House support packs, CT600 support data, filing checklists, and manual-only evidence.",
            where=["Kings_Accounting_Suite/**", "aureon/queen/accounting_context_bridge.py", "docs/audits/accounting_system_registry.json", "tests/test_*accounting*"],
            when=[
                "A task changes statutory filing packs, tax computations, CT financial-year splits, or requirements matrices.",
                "Official HMRC or Companies House guidance is cited or needs refreshing.",
                "The output could affect manual filing, payment, or legal records.",
            ],
            how=[
                "Keep full accounting-period totals unchanged unless a test proves the change is additive.",
                "Add support breakdowns as separate files/sections with reconciliation fields.",
                "Cite official sources in support notes and keep filings manual-only.",
                "Run focused accounting tests before regenerating packs.",
            ],
            validation=["statutory pack tests", "requirements matrix includes new support file", "manual-only filing boundary remains visible"],
            evidence=["source transaction count", "period/fiscal split", "reconciliation tolerance", "official guidance url"],
            safety_boundary="Accounting logic can prepare support documents only; it cannot submit filings, make payments, or expose credentials.",
        ),
        CodingLogicRule(
            id="voice.knowledge_expression_logic",
            who=["RepoCartographer", "ImplementationWorker", "SecurityReviewer"],
            what="Voice core, expression profile, HNC/Auris state translation, document artifacts, and human-readable prose.",
            where=["aureon/vault/voice/**", "state/aureon_expression_profile.json", "docs/audits/aureon_harmonic_affect_state.json", "tests/test_*voice*"],
            when=[
                "A task asks Aureon to explain itself, write documents, translate state, or reduce raw telemetry into human language.",
                "The output risks repeating template fragments or dumping raw internal data.",
                "The response needs grounded state with evidence retained separately.",
            ],
            how=[
                "Classify sources into voice facets before composing prose.",
                "Translate sensory/HNC fields into readable language while preserving raw evidence paths.",
                "Run repetition and redaction checks before writing public artifacts.",
                "Route document and console wording through the same voice profile.",
            ],
            validation=["voice unit tests", "novelty/repetition report", "redaction scan", "artifact path evidence"],
            evidence=["facets used", "state inputs", "redaction result", "novelty checks"],
            safety_boundary="Voice may describe synthetic state as system-state translation, not as unverified human biological sensation.",
        ),
        CodingLogicRule(
            id="quality.security_repair_logic",
            who=["SecurityReviewer", "TestPilot", "ImplementationWorker"],
            what="Test failures, build failures, secret scans, unsafe shell patterns, and self-repair work orders.",
            where=["tests/**", "docs/audits/aureon_repo_self_repair.json", "state/aureon_*last_run.json", "frontend/package.json"],
            when=[
                "A build/test fails or a generated artifact reports blockers.",
                "A public manifest could include secrets, private keys, or personal filing identifiers.",
                "A code change touches shared runtime, security, trading, or legal surfaces.",
            ],
            how=[
                "Capture the failing command and shortest useful output.",
                "Patch only the owned file set for the active goal.",
                "Rerun the exact failing command, then the focused regression suite.",
                "Publish blocker and repair evidence for the next agent loop.",
            ],
            validation=["pytest return code", "npm build return code", "secret pattern scan", "self-repair status"],
            evidence=["command", "return code", "stdout/stderr tail", "files changed"],
            safety_boundary="Repair agents may not use destructive git commands or revert unrelated user changes.",
        ),
    ]


def build_coding_logic_map(profile: dict[str, Any]) -> dict[str, Any]:
    rules = [rule.to_dict() for rule in coding_logic_rules()]
    file_area_index: dict[str, dict[str, Any]] = {}
    for rule in rules:
        for pattern in rule["where"]:
            file_area_index[pattern] = {
                "logic_rule": rule["id"],
                "owners": rule["who"],
                "primary_validation": rule["validation"][:2],
            }

    agent_route_index: dict[str, list[str]] = {}
    for rule in rules:
        for agent in rule["who"]:
            agent_route_index.setdefault(agent, []).append(rule["id"])

    repo_domains = sorted(((profile.get("repo_code") or {}).get("by_domain") or {}).keys())
    return {
        "status": "who_what_where_when_how_ready",
        "principle": "Every coding task is routed by who owns it, what kind of logic it changes, where the files live, when learning or writing is allowed, and how proof is produced.",
        "rules": rules,
        "file_area_index": file_area_index,
        "agent_route_index": dict(sorted(agent_route_index.items())),
        "repo_domains_seen": repo_domains,
        "decision_loop": [
            "who: select the responsible coder-agent chain",
            "what: classify the task domain and risk",
            "where: map file paths and public/state evidence contracts",
            "when: decide whether to learn, patch, test, pause, or escalate",
            "how: write through the Queen path, validate, publish evidence, and feed failures back",
        ],
        "write_protocol": {
            "context_first": True,
            "official_docs_for_external_api_changes": True,
            "queen_writer_required": True,
            "tests_required_for_code_changes": True,
            "public_evidence_required_for_operator_visible_capabilities": True,
            "do_not_revert_unowned_changes": True,
        },
    }


def build_work_orders(profile: dict[str, Any]) -> list[CodingWorkOrder]:
    tools = profile.get("tool_registry", {})
    missing_tools = list(tools.get("missing_required_coder_tools") or [])
    orders: list[CodingWorkOrder] = []
    if missing_tools:
        orders.append(
            CodingWorkOrder(
                id="coding_agents.register_missing_tools",
                title="Register missing coder web/repo tools",
                status="blocked_until_tool_registry_updated",
                priority=100,
                owner_agent="ImplementationWorker",
                reason=f"Missing coder tools: {', '.join(missing_tools)}",
                proposed_action="Add the missing built-ins to aureon.inhouse_ai.tool_registry and retest.",
                validation=["ToolRegistry names include every required coder tool."],
            )
        )
    else:
        orders.append(
            CodingWorkOrder(
                id="coding_agents.web_tools_active",
                title="Coder web/repo tools active",
                status="ready",
                priority=95,
                owner_agent="WebLearningScout",
                reason="In-house agents can now search the web, fetch docs, search the repo, and read skill-base status.",
                proposed_action="Use bounded official-doc learning before proposing coding improvements.",
                validation=["web_search", "web_fetch", "repo_search", "skill_base_status"],
            )
        )

    logic_map = profile.get("coding_logic_map") or {}
    logic_rules = list(logic_map.get("rules") or [])
    orders.append(
        CodingWorkOrder(
            id="coding_agents.who_what_where_when_how_logic",
            title="Use who/what/where/when/how coding route before writing files",
            status="active",
            priority=96,
            owner_agent="RepoCartographer",
            reason=f"{len(logic_rules)} coding logic rules route work across file areas, agents, validation, and evidence.",
            proposed_action="Before each code task, classify the task with coding_logic_map and assign the agent chain plus validation commands.",
            validation=["coding_logic_map.status == who_what_where_when_how_ready", "file_area_index has owned write paths"],
        )
    )

    skill_count = int((profile.get("skill_libraries") or {}).get("total_skill_count") or 0)
    if skill_count == 0:
        orders.append(
            CodingWorkOrder(
                id="coding_agents.bootstrap_skill_library",
                title="Bootstrap CodeArchitect skill library",
                status="planned",
                priority=90,
                owner_agent="ImplementationWorker",
                reason="No active skills found in the primary skill libraries.",
                proposed_action="Run CodeArchitect.bootstrap_atomics, then compose repo_search, test_runner, frontend_builder, and docs_research workflow skills.",
                validation=["state/skills/skill_library.json exists", "atomic skills validated"],
            )
        )
    else:
        orders.append(
            CodingWorkOrder(
                id="coding_agents.skill_library_explained",
                title="Explain active skill library to operator and agents",
                status="ready",
                priority=85,
                owner_agent="RepoCartographer",
                reason=f"{skill_count} skills are visible across known SkillLibrary stores.",
                proposed_action="Keep publishing skill summaries into frontend/public/aureon_coding_agent_skill_base.json.",
                validation=["Skill counts grouped by level and status."],
            )
        )

    repo_languages = (profile.get("repo_code") or {}).get("by_language") or {}
    for language, count in sorted(repo_languages.items(), key=lambda item: (-int(item[1]), item[0]))[:8]:
        orders.append(
            CodingWorkOrder(
                id=f"coding_agents.learn_{re.sub(r'[^a-z0-9]+', '_', language.lower())}",
                title=f"Learn and improve {language} coding patterns",
                status="learning_queued",
                priority=70,
                owner_agent="WebLearningScout",
                reason=f"Repo contains {count} {language} files.",
                proposed_action="Search official docs, compare against local patterns, then create scoped improvement proposals with tests.",
                validation=["official source recorded", "repo path evidence recorded", "tests proposed"],
            )
        )
    return orders


def run_online_probes(limit: int = 3) -> dict[str, Any]:
    """Run bounded read-only web probes through AureonAgentCore."""

    results: list[dict[str, Any]] = []
    search_results: list[dict[str, Any]] = []
    try:
        from aureon.autonomous.aureon_agent_core import AureonAgentCore

        agent = AureonAgentCore()
        for source in OFFICIAL_LEARNING_SOURCES[: max(0, limit)]:
            fetched = agent.web_fetch(str(source["url"]))
            results.append(
                {
                    "id": source["id"],
                    "url": source["url"],
                    "success": bool(fetched.get("success")),
                    "status_code": fetched.get("status_code"),
                    "sample_chars": len(str(fetched.get("text") or "")),
                    "error": fetched.get("error", ""),
                }
            )
        for query in WEB_LEARNING_QUERIES[: max(0, min(limit, 2))]:
            found = agent.web_search(str(query["query"]), num_results=3)
            search_results.append(
                {
                    "id": query["id"],
                    "query": query["query"],
                    "result_count": len(found) if isinstance(found, list) else 0,
                    "results": found[:3] if isinstance(found, list) else [],
                }
            )
    except Exception as exc:
        return {
            "enabled": True,
            "status": "probe_failed",
            "error": f"{type(exc).__name__}: {exc}",
            "fetches": results,
            "searches": search_results,
        }
    return {
        "enabled": True,
        "status": "probe_complete",
        "fetches": results,
        "searches": search_results,
    }


def render_component() -> str:
    return r'''import { useEffect, useMemo, useState, type ReactNode } from "react";
import { BrainCircuit, Code2, Globe2, SearchCheck, ShieldCheck, UsersRound } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

type JsonMap = Record<string, any>;

async function fetchJson(url: string): Promise<JsonMap> {
  try {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) return {};
    return await response.json();
  } catch {
    return {};
  }
}

function fmt(value: unknown): string {
  const number = Number(value || 0);
  return Number.isFinite(number) ? number.toLocaleString() : String(value || "0");
}

export function AureonCodingAgentSkillBaseConsole() {
  const [profile, setProfile] = useState<JsonMap>({});

  useEffect(() => {
    let cancelled = false;
    fetchJson("/aureon_coding_agent_skill_base.json").then((payload) => {
      if (!cancelled) setProfile(payload);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const summary = profile.summary || {};
  const agents = Array.isArray(profile.coder_agents) ? profile.coder_agents : [];
  const orders = Array.isArray(profile.coding_work_orders) ? profile.coding_work_orders : [];
  const tools = profile.tool_registry || {};
  const repoCode = profile.repo_code || {};
  const domains = repoCode.by_domain || {};
  const languages = repoCode.by_language || {};
  const logicMap = profile.coding_logic_map || {};
  const logicRules = Array.isArray(logicMap.rules) ? logicMap.rules : [];
  const sources = Array.isArray(profile.official_learning_sources) ? profile.official_learning_sources : [];
  const visibleOrders = useMemo(() => orders.slice(0, 30), [orders]);

  return (
    <Card className="mb-5 bg-card/80">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <BrainCircuit className="h-4 w-4 text-primary" />
          Aureon Coding Agent Skill Base
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-2">
          <Badge variant="outline" className="border-green-500/40 bg-green-500/10 text-green-100">{profile.status || "pending"}</Badge>
          <Badge variant="outline" className="border-border bg-muted/20 text-muted-foreground">updated {profile.generated_at ? new Date(profile.generated_at).toLocaleTimeString() : "pending"}</Badge>
          <Badge variant="outline" className="border-blue-500/40 bg-blue-500/10 text-blue-100">web tools {summary.web_tools_ready ? "ready" : "attention"}</Badge>
          <Badge variant="outline" className="border-purple-500/40 bg-purple-500/10 text-purple-100">{logicMap.status || "logic pending"}</Badge>
        </div>
        <div className="grid gap-2 md:grid-cols-6">
          <Stat icon={UsersRound} label="coder agents" value={summary.coder_agent_count} />
          <Stat icon={Code2} label="repo files" value={repoCode.file_count} />
          <Stat icon={BrainCircuit} label="skills" value={summary.skill_count} />
          <Stat icon={Globe2} label="learning sources" value={sources.length} />
          <Stat icon={ShieldCheck} label="logic rules" value={logicRules.length} />
          <Stat icon={SearchCheck} label="work orders" value={orders.length} />
        </div>
        <div className="grid gap-3 lg:grid-cols-3">
          <Panel title="Agents">
            {agents.slice(0, 6).map((agent: JsonMap) => (
              <div key={agent.name} className="rounded-md border border-border/40 bg-muted/10 p-3">
                <div className="text-sm font-medium">{agent.name}</div>
                <div className="mt-1 text-xs text-muted-foreground">{agent.purpose}</div>
              </div>
            ))}
          </Panel>
          <Panel title="Skill And Tool State">
            <Mini label="In-house tools" value={tools.inhouse_tool_count} />
            <Mini label="Missing coder tools" value={(tools.missing_required_coder_tools || []).length} />
            <Mini label="Languages" value={Object.keys(languages).length} />
            <Mini label="Domains" value={Object.keys(domains).length} />
          </Panel>
          <Panel title="Learning Sources">
            {sources.slice(0, 7).map((source: JsonMap) => (
              <div key={source.id} className="rounded-md border border-border/40 bg-muted/10 p-2">
                <div className="text-xs font-medium">{source.title}</div>
                <div className="truncate font-mono text-[10px] text-muted-foreground">{source.url}</div>
              </div>
            ))}
          </Panel>
        </div>
        <Panel title="Who What Where When How">
          <div className="text-xs text-muted-foreground">{logicMap.principle || "Coding route pending."}</div>
          <div className="grid gap-2 lg:grid-cols-2">
            {logicRules.slice(0, 6).map((rule: JsonMap) => (
              <div key={rule.id} className="rounded-md border border-border/40 bg-muted/10 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="text-sm font-medium">{rule.id}</div>
                  <Badge variant="outline" className="border-border bg-muted/20 text-muted-foreground">{(rule.who || []).slice(0, 2).join(" + ")}</Badge>
                </div>
                <div className="mt-2 text-xs text-muted-foreground">{rule.what}</div>
                <div className="mt-2 truncate font-mono text-[10px] text-green-100">{(rule.where || []).slice(0, 3).join(" | ")}</div>
              </div>
            ))}
          </div>
        </Panel>
        <ScrollArea className="h-[320px] pr-3">
          <div className="space-y-2">
            {visibleOrders.map((order: JsonMap) => (
              <div key={order.id} className="rounded-md border border-border/40 bg-muted/10 p-3">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <div className="text-sm font-medium">{order.title}</div>
                    <div className="mt-1 text-xs text-muted-foreground">{order.reason}</div>
                  </div>
                  <Badge variant="outline" className="border-border bg-muted/20 text-muted-foreground">{order.owner_agent}</Badge>
                </div>
                <div className="mt-2 text-xs text-green-100">{order.proposed_action}</div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

function Stat({ icon: Icon, label, value }: { icon: any; label: string; value: unknown }) {
  return (
    <div className="rounded-md border border-border/40 bg-muted/10 p-3">
      <div className="flex items-center gap-2 text-[11px] uppercase text-muted-foreground"><Icon className="h-3.5 w-3.5" />{label}</div>
      <div className="mt-1 text-lg font-semibold">{fmt(value)}</div>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="space-y-2 rounded-md border border-border/40 bg-muted/10 p-3">
      <div className="flex items-center gap-2 text-sm font-medium"><ShieldCheck className="h-4 w-4 text-primary" />{title}</div>
      <div className="space-y-2">{children}</div>
    </div>
  );
}

function Mini({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="flex items-center justify-between rounded-md border border-border/30 bg-background/20 px-3 py-2 text-xs">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-semibold">{fmt(value)}</span>
    </div>
  );
}
'''


def mount_component_in_app(app_text: str) -> str:
    import_line = 'import { AureonCodingAgentSkillBaseConsole } from "@/components/generated/AureonCodingAgentSkillBaseConsole";'
    if import_line not in app_text:
        anchor = 'import { AureonWorkOrderExecutionConsole } from "@/components/generated/AureonWorkOrderExecutionConsole";'
        fallback_anchor = 'import { AureonGeneratedOperationalConsole } from "@/components/generated/AureonGeneratedOperationalConsole";'
        if anchor in app_text:
            app_text = app_text.replace(anchor, f"{anchor}\n{import_line}", 1)
        elif fallback_anchor in app_text:
            app_text = app_text.replace(fallback_anchor, f"{fallback_anchor}\n{import_line}", 1)

    mount_line = "        <AureonCodingAgentSkillBaseConsole />"
    if mount_line not in app_text:
        anchor = "        <AureonWorkOrderExecutionConsole />"
        fallback_anchor = "        <AureonGeneratedOperationalConsole />"
        if anchor in app_text:
            app_text = app_text.replace(anchor, f"{anchor}\n{mount_line}", 1)
        elif fallback_anchor in app_text:
            app_text = app_text.replace(fallback_anchor, f"{fallback_anchor}\n{mount_line}", 1)
    return app_text


def build_profile(goal: str, *, root: Optional[Path] = None, online: bool = False, online_limit: int = 3) -> dict[str, Any]:
    repo_root = repo_root_from(root)
    repo_code = classify_repo_code(repo_root)
    skill_libraries = skill_library_snapshot(repo_root)
    tools = tool_registry_snapshot(repo_root)
    agents = [role.to_dict() for role in coder_agent_roles()]
    profile: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "repo_root": str(repo_root),
        "status": "coding_agent_skill_base_ready" if not tools.get("missing_required_coder_tools") else "coding_agent_skill_base_ready_with_tool_gaps",
        "goal": goal,
        "summary": {
            "coder_agent_count": len(agents),
            "repo_code_file_count": repo_code.get("file_count", 0),
            "skill_count": skill_libraries.get("total_skill_count", 0),
            "web_tools_ready": not bool(tools.get("missing_required_coder_tools")),
            "official_learning_source_count": len(OFFICIAL_LEARNING_SOURCES),
            "web_learning_query_count": len(WEB_LEARNING_QUERIES),
        },
        "coder_agents": agents,
        "repo_code": repo_code,
        "skill_libraries": skill_libraries,
        "tool_registry": tools,
        "official_learning_sources": list(OFFICIAL_LEARNING_SOURCES),
        "web_learning_queries": list(WEB_LEARNING_QUERIES),
        "web_probe": run_online_probes(online_limit) if online else {"enabled": False, "status": "not_requested"},
        "learning_flow": [
            "RepoCartographer maps existing code and evidence paths.",
            "WebLearningScout searches/fetches official docs and public API references.",
            "ImplementationWorker converts verified learning into scoped work orders.",
            "SecurityReviewer checks redaction, mutation boundaries, and unsafe patterns.",
            "TestPilot runs focused tests/builds and feeds failures back into repo self-repair.",
        ],
        "safety": {
            "web_learning_read_only": True,
            "official_sources_preferred": True,
            "secret_values_written": False,
            "external_mutations": False,
            "live_trading_mutation": False,
            "repo_writes_require_queen_writer_and_tests": True,
        },
        "authoring_path": [
            "GoalExecutionEngine.submit_goal",
            "GoalExecutionEngine._execute_coding_agent_skill_base",
            "aureon.autonomous.aureon_coding_agent_skill_base.build_and_write_profile",
            "QueenCodeArchitect.write_file",
        ],
    }
    profile["coding_logic_map"] = build_coding_logic_map(profile)
    profile["summary"]["coding_logic_rule_count"] = len((profile["coding_logic_map"] or {}).get("rules") or [])
    profile["coding_work_orders"] = [order.to_dict() for order in build_work_orders(profile)]
    profile["summary"]["coding_work_order_count"] = len(profile["coding_work_orders"])
    return profile


def render_markdown(profile: dict[str, Any]) -> str:
    lines = [
        "# Aureon Coding Agent Skill Base",
        "",
        f"- Generated: `{profile.get('generated_at')}`",
        f"- Status: `{profile.get('status')}`",
        f"- Goal: {profile.get('goal')}",
        "",
        "## Summary",
        "",
    ]
    for key, value in (profile.get("summary") or {}).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Coder Agents", ""])
    for agent in profile.get("coder_agents") or []:
        lines.append(f"- `{agent['name']}`: {agent['purpose']}")
    lines.extend(["", "## Tool Registry", ""])
    tools = profile.get("tool_registry") or {}
    lines.append(f"- In-house tools: `{', '.join(tools.get('inhouse_tools') or [])}`")
    missing = tools.get("missing_required_coder_tools") or []
    lines.append(f"- Missing required coder tools: `{', '.join(missing) if missing else 'none'}`")
    lines.extend(["", "## Learning Sources", ""])
    for source in profile.get("official_learning_sources") or []:
        lines.append(f"- `{source['id']}`: {source['title']} - {source['url']}")
    logic_map = profile.get("coding_logic_map") or {}
    lines.extend(["", "## Who What Where When How Coding Logic", ""])
    lines.append(str(logic_map.get("principle") or ""))
    lines.extend(["", "### Decision Loop", ""])
    for item in logic_map.get("decision_loop") or []:
        lines.append(f"- {item}")
    lines.extend(["", "### Rules", ""])
    for rule in logic_map.get("rules") or []:
        lines.append(f"- `{rule['id']}`")
        lines.append(f"  - who: {', '.join(rule.get('who') or [])}")
        lines.append(f"  - what: {rule.get('what')}")
        lines.append(f"  - where: {', '.join(rule.get('where') or [])}")
        lines.append(f"  - when: {'; '.join(rule.get('when') or [])}")
        lines.append(f"  - how: {'; '.join(rule.get('how') or [])}")
    lines.extend(["", "## Coding Work Orders", ""])
    for order in profile.get("coding_work_orders") or []:
        lines.append(f"- `{order['status']}` `{order['owner_agent']}` {order['title']}: {order['proposed_action']}")
    lines.extend(["", "## Safety", ""])
    for key, value in (profile.get("safety") or {}).items():
        lines.append(f"- `{key}`: `{value}`")
    return "\n".join(lines) + "\n"


def write_profile(profile: dict[str, Any], root: Path) -> dict[str, Any]:
    payload = json.dumps(profile, indent=2, sort_keys=True, default=str)
    markdown = render_markdown(profile)
    files = {
        DEFAULT_OUTPUT_JSON.as_posix(): payload,
        DEFAULT_OUTPUT_MD.as_posix(): markdown,
        DEFAULT_PUBLIC_JSON.as_posix(): payload,
        DEFAULT_STATE_PATH.as_posix(): payload,
        DEFAULT_VAULT_NOTE.as_posix(): markdown,
        DEFAULT_COMPONENT.as_posix(): render_component(),
    }
    app_path = root / DEFAULT_APP_PATH
    if app_path.exists():
        files[DEFAULT_APP_PATH.as_posix()] = mount_component_in_app(app_path.read_text(encoding="utf-8", errors="replace"))

    if QueenCodeArchitect is not None:
        queen = QueenCodeArchitect(repo_path=str(root))
        for rel, content in files.items():
            ok = queen.write_file(rel, content, backup=True)
            if not ok:
                raise RuntimeError(f"QueenCodeArchitect refused to write {rel}")
        return {"writer": "QueenCodeArchitect", "created_files": list(getattr(queen, "created_files", []))}

    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return {"writer": "direct_python_fallback", "created_files": list(files)}


def build_and_write_profile(
    goal: str,
    *,
    root: Optional[Path] = None,
    online: bool = False,
    online_limit: int = 3,
) -> dict[str, Any]:
    repo_root = repo_root_from(root)
    profile = build_profile(goal, root=repo_root, online=online, online_limit=online_limit)
    write_info = write_profile(profile, repo_root)
    result = dict(profile)
    result["write_info"] = write_info
    state_payload = json.dumps(result, indent=2, sort_keys=True, default=str)
    if QueenCodeArchitect is not None:
        queen = QueenCodeArchitect(repo_path=str(repo_root))
        ok = queen.write_file(DEFAULT_STATE_PATH.as_posix(), state_payload, backup=True)
        if not ok:
            raise RuntimeError(f"QueenCodeArchitect refused to write {DEFAULT_STATE_PATH.as_posix()}")
    else:
        state_path = repo_root / DEFAULT_STATE_PATH
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(state_payload, encoding="utf-8")
    return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build Aureon's coding-agent skill base profile.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--goal", default="Teach Aureon to use its agents as coders and learn coding skills.")
    parser.add_argument("--online", action="store_true", help="Run bounded read-only web search/fetch probes.")
    parser.add_argument("--online-limit", type=int, default=3)
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from()
    result = build_and_write_profile(args.goal, root=root, online=args.online, online_limit=args.online_limit)
    print(json.dumps({"status": result["status"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
