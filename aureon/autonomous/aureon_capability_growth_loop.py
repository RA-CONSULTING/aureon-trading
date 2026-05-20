"""Aureon's safe capability growth loop.

This is the controller for the repeatable cycle the organism needs:

audit -> benchmark -> score domains -> detect gaps -> author improvements
-> queue internal work -> write memory -> repeat.

The loop deliberately stays inside local, safe boundaries. It can generate and
validate new SkillLibrary skills and queue work orders for the organism, but it
does not place trades, submit accounts, pay money, expose secrets, or force a
restart. Code changes to the repo still go through the tested patch/restart
path; learned skills can be stored as validated local capabilities.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional, Sequence

from aureon.autonomous.aureon_goal_capability_map import build_goal_capability_map


SCHEMA_VERSION = "aureon-capability-growth-loop-v1"
DEFAULT_OUTPUT_MD = Path("docs/audits/aureon_capability_growth_loop.md")
DEFAULT_OUTPUT_JSON = Path("docs/audits/aureon_capability_growth_loop.json")
DEFAULT_STATE_PATH = Path("state/capability_growth_loop.json")
DEFAULT_CONTRACT_STATE = Path("state/capability_growth_contracts.json")
DEFAULT_SKILL_DIR = Path("state/capability_growth_skills")
DEFAULT_VAULT_NOTE = Path(".obsidian/Aureon Self Understanding/capability_growth_loop.md")

SAFE_ENV = {
    "AUREON_AUDIT_MODE": "1",
    "AUREON_LIVE_TRADING": "0",
    "AUREON_DISABLE_REAL_ORDERS": "1",
    "AUREON_ALLOW_SIM_FALLBACK": "1",
    "AUREON_QUIET_STARTUP": "1",
}

DOMAIN_ORDER = (
    "repo_self_catalog",
    "repo_organization",
    "whole_mind_wiring",
    "goal_contracts",
    "self_questioning_llm_vault",
    "code_architect_skill_authoring",
    "trading_cognition",
    "accounting_compliance",
    "research_vault",
    "hnc_saas_security",
    "operator_surfaces",
    "ignition_runtime",
    "validation_benchmarking",
)


@dataclass
class BenchmarkCheck:
    id: str
    command: list[str]
    status: str
    returncode: int
    duration_s: float
    stdout_tail: str = ""
    stderr_tail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DomainCapability:
    id: str
    name: str
    status: str
    score: float
    systems: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    improvement_hint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CapabilityGap:
    id: str
    domain: str
    title: str
    severity: str
    priority: int
    evidence: list[str]
    proposed_skill_name: str
    proposed_action: str
    route: str
    status: str = "planned"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuthoredImprovement:
    skill_name: str
    domain: str
    status: str
    validation_ok: bool
    registered: bool
    storage_path: str
    code_preview: str
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GrowthIteration:
    index: int
    started_at: str
    status: str
    domains: list[DomainCapability]
    gaps: list[CapabilityGap]
    authored_improvements: list[AuthoredImprovement]
    contract_plan: dict[str, Any]
    benchmark_checks: list[BenchmarkCheck]
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "started_at": self.started_at,
            "status": self.status,
            "domains": [item.to_dict() for item in self.domains],
            "gaps": [item.to_dict() for item in self.gaps],
            "authored_improvements": [item.to_dict() for item in self.authored_improvements],
            "contract_plan": dict(self.contract_plan),
            "benchmark_checks": [item.to_dict() for item in self.benchmark_checks],
            "summary": dict(self.summary),
        }


@dataclass
class CapabilityGrowthReport:
    schema_version: str
    generated_at: str
    repo_root: str
    status: str
    iterations: list[GrowthIteration]
    summary: dict[str, Any]
    safety: dict[str, Any]
    vault_memory: dict[str, Any]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "repo_root": self.repo_root,
            "status": self.status,
            "iterations": [item.to_dict() for item in self.iterations],
            "summary": dict(self.summary),
            "safety": dict(self.safety),
            "vault_memory": dict(self.vault_memory),
            "notes": list(self.notes),
        }


def repo_root_from(start: Optional[Path] = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "aureon").is_dir() and (candidate / "scripts").is_dir():
            return candidate
    return Path(__file__).resolve().parents[2]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def apply_safe_environment() -> dict[str, str]:
    os.environ.update(SAFE_ENV)
    try:
        from aureon.core.aureon_runtime_safety import apply_safe_runtime_environment

        apply_safe_runtime_environment(os.environ)
    except Exception:
        pass
    return {key: os.environ.get(key, "") for key in SAFE_ENV}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}", "path": str(path)}


def status_score(status: str) -> float:
    text = (status or "").lower()
    if "blocked" in text or "missing" in text or "failed" in text:
        return 0.20
    if "safe_simulation" in text:
        return 0.82
    if "attention" in text or "partial" in text:
        return 0.72
    if "working" in text or "complete" in text or "organized" in text or "ready" in text:
        return 1.0
    if text in {"present", "ok", "pass", "passed"}:
        return 1.0
    return 0.50


def _proof(readiness: dict[str, Any], proof_id: str) -> dict[str, Any]:
    for proof in readiness.get("proofs") or []:
        if proof.get("id") == proof_id:
            return proof
    return {}


def _domain_from_proof(
    readiness: dict[str, Any],
    proof_id: str,
    *,
    name: str,
    hint: str,
    systems: Optional[list[str]] = None,
    domain_id: Optional[str] = None,
) -> DomainCapability:
    resolved_id = domain_id or proof_id
    proof = _proof(readiness, proof_id)
    if not proof:
        return DomainCapability(
            id=resolved_id,
            name=name,
            status="missing",
            score=0.20,
            systems=systems or [],
            evidence={"proof_available": False},
            improvement_hint=hint,
        )
    status = proof.get("status") or "unknown"
    return DomainCapability(
        id=resolved_id,
        name=name,
        status=status,
        score=status_score(status),
        systems=proof.get("systems") or systems or [],
        evidence={
            "summary": proof.get("summary"),
            "evidence": proof.get("evidence") or {},
            "safety_boundary": proof.get("safety_boundary"),
        },
        improvement_hint=hint,
    )


def code_architect_capability(root: Path) -> DomainCapability:
    try:
        from aureon.code_architect import CodeArchitect, SkillLibrary

        library = SkillLibrary(storage_dir=root / DEFAULT_SKILL_DIR)
        architect = CodeArchitect(library=library, auto_wire=False)
        status = architect.get_status()
        score = 1.0 if status.get("validator") and status.get("library") else 0.72
        return DomainCapability(
            id="code_architect_skill_authoring",
            name="Code Architect Skill Authoring",
            status="working" if score >= 1.0 else "working_with_attention",
            score=score,
            systems=["CodeArchitect", "SkillLibrary", "SkillValidator", "SkillWriter"],
            evidence={"architect_status": status, "skill_library_path": str(library.library_path)},
            improvement_hint="Generate and validate skills for domain gaps, then promote stable skills into the active library.",
        )
    except Exception as exc:
        return DomainCapability(
            id="code_architect_skill_authoring",
            name="Code Architect Skill Authoring",
            status="blocked_or_missing",
            score=0.20,
            systems=["CodeArchitect", "SkillLibrary", "SkillValidator"],
            evidence={"error": f"{type(exc).__name__}: {exc}"},
            improvement_hint="Repair CodeArchitect imports and SkillLibrary persistence.",
        )


def validation_capability(benchmark_checks: Sequence[BenchmarkCheck]) -> DomainCapability:
    if not benchmark_checks:
        return DomainCapability(
            id="validation_benchmarking",
            name="Validation And Benchmark Loop",
            status="working_with_attention",
            score=0.72,
            systems=["pytest", "compileall", "benchmark reports", "capability growth loop"],
            evidence={"checks_run": 0, "note": "No checks were run in this cycle."},
            improvement_hint="Run safe focused tests and benchmarks in the growth loop, then feed failures back as gaps.",
        )
    failed = [item for item in benchmark_checks if item.status != "passed"]
    return DomainCapability(
        id="validation_benchmarking",
        name="Validation And Benchmark Loop",
        status="working" if not failed else "blocked_or_missing",
        score=1.0 if not failed else 0.20,
        systems=["pytest", "compileall", "benchmark reports", "capability growth loop"],
        evidence={
            "checks_run": len(benchmark_checks),
            "failed_checks": [item.id for item in failed],
        },
        improvement_hint="Convert failed checks into work orders and re-run after fixes.",
    )


def collect_domain_capabilities(
    root: Path,
    benchmark_checks: Sequence[BenchmarkCheck] = (),
) -> list[DomainCapability]:
    audits = root / "docs" / "audits"
    readiness = load_json(audits / "aureon_system_readiness_audit.json")
    self_catalog = load_json(audits / "aureon_repo_self_catalog.json")
    mind = load_json(audits / "mind_wiring_audit.json")
    goal_map = build_goal_capability_map(
        repo_root=root,
        current_goal=(
            "test benchmark audit fix capabilities, write improvements, "
            "repeat, self catalog, self enhancement, accounting, trading, research, hardened SaaS security"
        ),
    ).to_dict()

    catalog_summary = self_catalog.get("summary") or {}
    catalog_files = int(catalog_summary.get("cataloged_file_count") or 0)
    catalog_status = self_catalog.get("status") or "missing"
    mind_counts = mind.get("counts") or {}
    mind_bad = sum(int(mind_counts.get(key) or 0) for key in ("partial", "broken", "unknown"))

    domains = [
        DomainCapability(
            id="repo_self_catalog",
            name="Repo Self-Catalog",
            status=catalog_status if catalog_files else "missing",
            score=1.0 if catalog_files and not (catalog_summary.get("truncated")) else 0.20,
            systems=["AureonRepoSelfCatalog", "Obsidian repo self-catalog note", "per-file LLM context"],
            evidence={
                "cataloged_file_count": catalog_files,
                "subsystem_count": catalog_summary.get("subsystem_count"),
                "secret_metadata_only_count": catalog_summary.get("secret_metadata_only_count"),
                "coverage_policy": catalog_summary.get("coverage_policy"),
            },
            improvement_hint="Regenerate after code/data changes and use labels in self-questioning prompts.",
        ),
        _domain_from_proof(
            readiness,
            "repo_organization",
            name="Repo Organization",
            hint="Clear unstaged/attention ownership items or explicitly preserve them.",
        ),
        DomainCapability(
            id="whole_mind_wiring",
            name="Whole-Mind Wiring",
            status="working" if mind_counts and mind_bad == 0 else "working_with_attention",
            score=1.0 if mind_counts and mind_bad == 0 else 0.72,
            systems=["MindWiringAudit", "organism_spine", "ThoughtBus", "local service probes"],
            evidence={"counts": mind_counts},
            improvement_hint="Route any broken/partial/unknown systems into repair contracts.",
        ),
        _domain_from_proof(
            readiness,
            "goal_routing",
            name="Goal, Skill, Task, And Route Brain",
            hint="Ensure all major goal types map to safe route surfaces.",
            systems=["GoalCapabilityMap", "OrganismContractStack"],
            domain_id="goal_contracts",
        ),
        DomainCapability(
            id="self_questioning_llm_vault",
            name="Self-Questioning LLM And Vault",
            status=_proof(readiness, "llm_capability").get("status") or "missing",
            score=status_score(_proof(readiness, "llm_capability").get("status") or "missing"),
            systems=[
                "SelfQuestioningAI",
                "OllamaBridge",
                "AureonHybridAdapter",
                "ObsidianBridge",
                "repo_self_catalog context",
            ],
            evidence={
                "llm_proof": _proof(readiness, "llm_capability"),
                "research_vault": _proof(readiness, "research_vault"),
                "route_has_self_catalog": "self_catalog" in (goal_map.get("route_surfaces") or {}),
            },
            improvement_hint="Keep local LLM/vault available and feed self-catalog/accounting/trading evidence into prompts.",
        ),
        code_architect_capability(root),
        _domain_from_proof(
            readiness,
            "trading_brain",
            name="Trading Cognition",
            hint="Improve simulation, sizing, ETA verification, and safety gates before live paths.",
            domain_id="trading_cognition",
        ),
        _domain_from_proof(
            readiness,
            "accounting_brain",
            name="Accounting Compliance",
            hint="Close attention items, evidence gaps, and generated pack validation loops.",
            domain_id="accounting_compliance",
        ),
        _domain_from_proof(
            readiness,
            "research_vault",
            name="Research And Vault Memory",
            hint="Expand corpus retrieval, source linking, and vault ingestion.",
        ),
        _domain_from_proof(
            readiness,
            "hnc_saas_security",
            name="HNC SaaS Security Architect",
            hint="Implement tenant isolation, LLM/tool governance, zero-trust, and release-gate evidence before deployment.",
            systems=["HNCSaaSSecurityArchitect", "OrganismContractStack", "OWASP ASVS", "NIST zero trust"],
        ),
        _domain_from_proof(
            readiness,
            "operator_surfaces",
            name="Operator Surfaces",
            hint="Keep command center, frontend, and local service health checks reachable.",
            domain_id="operator_surfaces",
        ),
        _domain_from_proof(
            readiness,
            "ignition",
            name="Ignition Runtime",
            hint="Keep single boot preflight and safe live profile checks passing.",
            domain_id="ignition_runtime",
        ),
        validation_capability(benchmark_checks),
    ]
    return sorted(domains, key=lambda item: DOMAIN_ORDER.index(item.id) if item.id in DOMAIN_ORDER else 99)


def gap_for_domain(domain: DomainCapability) -> Optional[CapabilityGap]:
    if domain.score >= 0.90 and "attention" not in domain.status.lower():
        return None
    severity = "high" if domain.score < 0.50 else "medium"
    priority = 5 if severity == "high" else 3
    action = (
        f"Run safe audit/benchmark/fix loop for {domain.id}; use {', '.join(domain.systems[:4])}; "
        "write findings to vault and queue re-test."
    )
    return CapabilityGap(
        id=f"gap_{domain.id}",
        domain=domain.id,
        title=f"Improve {domain.name}",
        severity=severity,
        priority=priority,
        evidence=[
            f"status={domain.status}",
            f"score={domain.score:.2f}",
            domain.improvement_hint,
        ],
        proposed_skill_name=f"improve_{domain.id}",
        proposed_action=action,
        route="capability_growth_loop",
    )


def detect_capability_gaps(domains: Sequence[DomainCapability]) -> list[CapabilityGap]:
    gaps = [gap for domain in domains if (gap := gap_for_domain(domain))]
    gaps.sort(key=lambda item: (-item.priority, item.domain))
    return gaps


def safe_skill_code(gap: CapabilityGap) -> str:
    return (
        f"def {gap.proposed_skill_name}(**kwargs):\n"
        f"    \"\"\"Plan a safe improvement cycle for {gap.domain}.\"\"\"\n"
        "    return {\n"
        f"        'domain': {gap.domain!r},\n"
        f"        'title': {gap.title!r},\n"
        "        'cycle': ['audit', 'benchmark', 'fix', 'retest', 'write_memory'],\n"
        f"        'proposed_action': {gap.proposed_action!r},\n"
        "        'safety': {\n"
        "            'live_orders': 'blocked',\n"
        "            'official_filing': 'manual_only',\n"
        "            'payments': 'manual_only',\n"
        "            'secrets': 'metadata_only',\n"
        "        },\n"
        "        'input': dict(kwargs),\n"
        "    }\n"
    )


def author_improvement_skills(root: Path, gaps: Sequence[CapabilityGap], limit: int = 8) -> list[AuthoredImprovement]:
    authored: list[AuthoredImprovement] = []
    try:
        from aureon.code_architect import Skill, SkillLevel, SkillLibrary, SkillProposal, SkillStatus, SkillValidator
    except Exception as exc:
        return [
            AuthoredImprovement(
                skill_name="code_architect_unavailable",
                domain="code_architect_skill_authoring",
                status="blocked",
                validation_ok=False,
                registered=False,
                storage_path="",
                code_preview="",
                error=f"{type(exc).__name__}: {exc}",
            )
        ]

    library = SkillLibrary(storage_dir=root / DEFAULT_SKILL_DIR)
    validator = SkillValidator(strict_static=True)
    for gap in list(gaps)[: max(0, limit)]:
        code = safe_skill_code(gap)
        proposal = SkillProposal(
            name=gap.proposed_skill_name,
            description=gap.title,
            level=SkillLevel.TASK,
            category="capability_growth",
            code=code,
            entry_function=gap.proposed_skill_name,
            params_schema={"type": "object", "properties": {}},
            dependencies=[],
            observation_sources=[gap.id],
            reasoning="Generated by Aureon capability growth loop from audit/benchmark gap evidence.",
            target="local",
        )
        try:
            static_ok, static_errors = validator.static_check(proposal.code)
            skill = Skill.from_proposal(proposal)
            skill.queen_verdict = "STATIC_SAFE"
            skill.queen_confidence = 0.5
            skill.pillar_alignment_score = 0.5
            skill.pillar_lighthouse = False
            skill.harmonic_signature = {"capability_growth": 1.0}
            skill.status = SkillStatus.VALIDATED if static_ok else SkillStatus.BLOCKED
            if static_ok:
                library.add(skill, persist=False)
            authored.append(
                AuthoredImprovement(
                    skill_name=proposal.name,
                    domain=gap.domain,
                    status=skill.status.value if static_ok else "blocked",
                    validation_ok=bool(static_ok),
                    registered=bool(static_ok),
                    storage_path=str(library.library_path),
                    code_preview=code[:500],
                    error="" if static_ok else f"static_check failed: {static_errors[:3]}",
                )
            )
        except Exception as exc:
            authored.append(
                AuthoredImprovement(
                    skill_name=proposal.name,
                    domain=gap.domain,
                    status="blocked",
                    validation_ok=False,
                    registered=False,
                    storage_path=str(library.library_path),
                    code_preview=code[:500],
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
    if authored:
        library.save()
    return authored


def queue_growth_contracts(
    root: Path,
    gaps: Sequence[CapabilityGap],
    authored: Sequence[AuthoredImprovement],
    *,
    queue_contracts: bool,
) -> dict[str, Any]:
    if not queue_contracts:
        return {"queued_persistently": False, "gap_count": len(gaps), "authored_skill_count": len(authored)}
    try:
        from aureon.core.organism_contracts import OrganismContractStack

        stack = OrganismContractStack(
            state_path=root / DEFAULT_CONTRACT_STATE,
            source="capability_growth_loop",
        )
        workflow = stack.create_goal_workflow(
            "Continuously audit, benchmark, fix, and retest Aureon capabilities across every domain.",
            skills=[item.skill_name for item in authored if item.registered],
            route_surfaces=["capability_growth", "self_enhancement", "self_catalog", "contracts", "validation"],
            source="capability_growth_loop",
        )
        authored_by_domain = {item.domain: item.skill_name for item in authored if item.registered}
        gap_work_orders: list[dict[str, Any]] = []
        for gap in gaps:
            wo = stack.enqueue_work_order(
                f"Improve capability domain: {gap.domain}",
                "execute_internal_task",
                queue="organism.capability_growth",
                priority=gap.priority,
                payload={
                    "gap": gap.to_dict(),
                    "recommended_skill": authored_by_domain.get(gap.domain, gap.proposed_skill_name),
                    "cycle": ["audit", "benchmark", "fix", "retest", "write_memory"],
                },
                source="capability_growth_loop",
            )
            gap_work_orders.append(wo.to_dict())
        status = stack.publish_status()
        return {
            "queued_persistently": True,
            "state_path": str(root / DEFAULT_CONTRACT_STATE),
            "workflow": workflow,
            "gap_work_orders": gap_work_orders,
            "status": status,
        }
    except Exception as exc:
        return {"queued_persistently": False, "error": f"{type(exc).__name__}: {exc}"}


def default_benchmark_commands(root: Path, python_exe: str) -> list[tuple[str, list[str]]]:
    return [
        (
            "compile_growth_loop",
            [
                python_exe,
                "-m",
                "compileall",
                "aureon/autonomous/aureon_capability_growth_loop.py",
                "tests/test_capability_growth_loop.py",
            ],
        ),
        (
            "focused_growth_tests",
            [
                python_exe,
                "-m",
                "pytest",
                "tests/test_capability_growth_loop.py",
                "-q",
            ],
        ),
    ]


def run_benchmark_checks(
    root: Path,
    commands: Sequence[tuple[str, list[str]]],
    *,
    timeout_s: int = 120,
    runner: Optional[Callable[..., subprocess.CompletedProcess[str]]] = None,
) -> list[BenchmarkCheck]:
    env = os.environ.copy()
    env.update(SAFE_ENV)
    run = runner or subprocess.run
    checks: list[BenchmarkCheck] = []
    for check_id, command in commands:
        start = time.time()
        try:
            completed = run(
                command,
                cwd=str(root),
                env=env,
                text=True,
                capture_output=True,
                timeout=timeout_s,
            )
            duration = time.time() - start
            checks.append(
                BenchmarkCheck(
                    id=check_id,
                    command=list(command),
                    status="passed" if completed.returncode == 0 else "failed",
                    returncode=int(completed.returncode),
                    duration_s=round(duration, 3),
                    stdout_tail=(completed.stdout or "")[-2000:],
                    stderr_tail=(completed.stderr or "")[-2000:],
                )
            )
        except subprocess.TimeoutExpired as exc:
            checks.append(
                BenchmarkCheck(
                    id=check_id,
                    command=list(command),
                    status="timeout",
                    returncode=124,
                    duration_s=round(time.time() - start, 3),
                    stdout_tail=str(exc.stdout or "")[-2000:],
                    stderr_tail=str(exc.stderr or "")[-2000:],
                )
            )
    return checks


def build_iteration(
    root: Path,
    index: int,
    *,
    benchmark_checks: Sequence[BenchmarkCheck] = (),
    author_skills: bool = False,
    queue_contracts: bool = False,
    max_gaps: int = 8,
) -> GrowthIteration:
    started = utc_now()
    domains = collect_domain_capabilities(root, benchmark_checks=benchmark_checks)
    gaps = detect_capability_gaps(domains)[: max(0, max_gaps)]
    authored = author_improvement_skills(root, gaps, limit=max_gaps) if author_skills else []
    contract_plan = queue_growth_contracts(root, gaps, authored, queue_contracts=queue_contracts)
    blocked_domains = [item for item in domains if item.score < 0.50]
    attention_domains = [item for item in domains if item.score < 0.90 or "attention" in item.status.lower()]
    failed_checks = [item for item in benchmark_checks if item.status != "passed"]
    if blocked_domains or failed_checks:
        status = "needs_repair"
    elif attention_domains:
        status = "working_with_growth_items"
    else:
        status = "working_and_expanding"
    summary = {
        "domain_count": len(domains),
        "gap_count": len(gaps),
        "blocked_domain_count": len(blocked_domains),
        "attention_domain_count": len(attention_domains),
        "authored_improvement_count": len(authored),
        "registered_improvement_count": sum(1 for item in authored if item.registered),
        "benchmark_check_count": len(benchmark_checks),
        "failed_benchmark_count": len(failed_checks),
        "mean_score": round(sum(item.score for item in domains) / max(1, len(domains)), 3),
    }
    return GrowthIteration(
        index=index,
        started_at=started,
        status=status,
        domains=domains,
        gaps=gaps,
        authored_improvements=authored,
        contract_plan=contract_plan,
        benchmark_checks=list(benchmark_checks),
        summary=summary,
    )


def build_capability_growth_loop(
    repo_root: Optional[Path] = None,
    *,
    iterations: int = 1,
    run_checks: bool = False,
    author_skills: bool = False,
    queue_contracts: bool = False,
    max_gaps: int = 8,
    python_exe: Optional[str] = None,
) -> CapabilityGrowthReport:
    root = repo_root_from(repo_root)
    safe = apply_safe_environment()
    py = python_exe or sys.executable
    iteration_reports: list[GrowthIteration] = []
    benchmark_checks: list[BenchmarkCheck] = []
    for index in range(1, max(1, iterations) + 1):
        if run_checks:
            benchmark_checks = run_benchmark_checks(root, default_benchmark_commands(root, py))
        iteration_reports.append(
            build_iteration(
                root,
                index,
                benchmark_checks=benchmark_checks,
                author_skills=author_skills,
                queue_contracts=queue_contracts,
                max_gaps=max_gaps,
            )
        )
    latest = iteration_reports[-1]
    blocked = latest.summary.get("blocked_domain_count", 0)
    failed = latest.summary.get("failed_benchmark_count", 0)
    if blocked or failed:
        status = "growth_loop_needs_repair"
    elif latest.summary.get("gap_count", 0):
        status = "growth_loop_working_with_improvement_queue"
    else:
        status = "growth_loop_working_clean"
    vault_path = root / DEFAULT_VAULT_NOTE
    summary = {
        "iteration_count": len(iteration_reports),
        "latest_status": latest.status,
        "latest_gap_count": latest.summary.get("gap_count", 0),
        "latest_mean_score": latest.summary.get("mean_score", 0),
        "latest_registered_improvement_count": latest.summary.get("registered_improvement_count", 0),
        "latest_benchmark_check_count": latest.summary.get("benchmark_check_count", 0),
        "latest_failed_benchmark_count": latest.summary.get("failed_benchmark_count", 0),
        "contract_queue_persisted": bool(latest.contract_plan.get("queued_persistently")),
        "skill_authoring_enabled": bool(author_skills),
    }
    report = CapabilityGrowthReport(
        schema_version=SCHEMA_VERSION,
        generated_at=utc_now(),
        repo_root=str(root),
        status=status,
        iterations=iteration_reports,
        summary=summary,
        safety={
            **safe,
            "live_orders_allowed": False,
            "official_filing_manual_only": True,
            "payments_manual_only": True,
            "repo_code_patch_requires_tests_and_restart_handoff": True,
        },
        vault_memory={
            "status": "planned",
            "note_path": str(vault_path),
            "topic": "capability.growth.ready",
            "cycle": ["audit", "benchmark", "fix", "retest", "write_memory", "repeat"],
        },
        notes=[
            "This is the organism-level improvement loop across trading, accounting, research, cognition, LLM, vault, frontend, and runtime domains.",
            "HNC SaaS security joins the loop as a hardened zero-trust design and release-gate domain, not a promise of literal unhackability.",
            "The loop can author safe SkillLibrary improvements and queue work orders; repo patches still require tests and restart handoff.",
            "Live trading, official filing, payments, and secret exposure are not capabilities granted by this loop.",
        ],
    )
    return report


def render_markdown(report: CapabilityGrowthReport) -> str:
    def esc(value: Any) -> str:
        return str(value).replace("|", "\\|")

    lines: list[str] = []
    lines.append("# Aureon Capability Growth Loop")
    lines.append("")
    lines.append(f"- Generated: `{report.generated_at}`")
    lines.append(f"- Repo: `{report.repo_root}`")
    lines.append(f"- Status: `{report.status}`")
    lines.append("- Safety: audit/simulation/local skill authoring only; no live orders, official filing, payments, or secret exposure")
    lines.append("")
    lines.append("## Loop")
    lines.append("")
    lines.append("`audit -> benchmark -> score domains -> detect gaps -> author improvements -> queue work -> write memory -> repeat`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    for key, value in report.summary.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    latest = report.iterations[-1]
    lines.append("## Domain Scores")
    lines.append("")
    lines.append("| Domain | Status | Score | Improvement hint |")
    lines.append("| --- | --- | ---: | --- |")
    for domain in latest.domains:
        lines.append(f"| {esc(domain.name)} | `{domain.status}` | {domain.score:.2f} | {esc(domain.improvement_hint)} |")
    lines.append("")
    lines.append("## Improvement Queue")
    lines.append("")
    lines.append("| Priority | Gap | Domain | Proposed skill | Route |")
    lines.append("| ---: | --- | --- | --- | --- |")
    for gap in latest.gaps:
        lines.append(f"| {gap.priority} | {esc(gap.title)} | `{gap.domain}` | `{gap.proposed_skill_name}` | `{gap.route}` |")
    lines.append("")
    if latest.authored_improvements:
        lines.append("## Authored Improvements")
        lines.append("")
        lines.append("| Skill | Domain | Status | Registered |")
        lines.append("| --- | --- | --- | --- |")
        for item in latest.authored_improvements:
            lines.append(f"| `{item.skill_name}` | `{item.domain}` | `{item.status}` | `{item.registered}` |")
        lines.append("")
    if latest.benchmark_checks:
        lines.append("## Benchmark Checks")
        lines.append("")
        lines.append("| Check | Status | Seconds | Return code |")
        lines.append("| --- | --- | ---: | ---: |")
        for check in latest.benchmark_checks:
            lines.append(f"| `{check.id}` | `{check.status}` | {check.duration_s:.3f} | {check.returncode} |")
        lines.append("")
    lines.append("## Contract Plan")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(latest.contract_plan, indent=2, sort_keys=True, default=str)[:2600])
    lines.append("```")
    lines.append("")
    lines.append("## Vault Memory")
    lines.append("")
    for key, value in report.vault_memory.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    for note in report.notes:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def render_vault_note(report: CapabilityGrowthReport) -> str:
    latest = report.iterations[-1]
    lines = [
        "# Aureon Capability Growth Loop",
        "",
        "This note is the compact vault memory for the organism's repeatable improvement loop.",
        "",
        f"- Generated: `{report.generated_at}`",
        f"- Status: `{report.status}`",
        f"- Latest gaps: `{latest.summary.get('gap_count', 0)}`",
        f"- Latest mean score: `{latest.summary.get('mean_score', 0)}`",
        f"- Registered improvements: `{latest.summary.get('registered_improvement_count', 0)}`",
        "- Cycle: `audit -> benchmark -> fix -> retest -> write_memory -> repeat`",
        "",
        "## Current Improvement Focus",
        "",
    ]
    for gap in latest.gaps[:12]:
        lines.append(f"- `{gap.domain}`: {gap.title} via `{gap.proposed_skill_name}`")
    lines.append("")
    lines.append("Use `docs/audits/aureon_capability_growth_loop.json` for full evidence.")
    lines.append("")
    return "\n".join(lines)


def write_report(
    report: CapabilityGrowthReport,
    markdown_path: Path = DEFAULT_OUTPUT_MD,
    json_path: Path = DEFAULT_OUTPUT_JSON,
    state_path: Path = DEFAULT_STATE_PATH,
    *,
    write_vault: bool = True,
) -> tuple[Path, Path, Path, Optional[Path]]:
    root = Path(report.repo_root)
    md_path = markdown_path if markdown_path.is_absolute() else root / markdown_path
    js_path = json_path if json_path.is_absolute() else root / json_path
    st_path = state_path if state_path.is_absolute() else root / state_path
    vault_path: Optional[Path] = None
    if write_vault:
        vault_path = Path(report.vault_memory["note_path"])
        report.vault_memory["status"] = "written"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    js_path.parent.mkdir(parents=True, exist_ok=True)
    st_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_markdown(report), encoding="utf-8")
    payload = json.dumps(report.to_dict(), indent=2, sort_keys=True, default=str)
    js_path.write_text(payload, encoding="utf-8")
    st_path.write_text(payload, encoding="utf-8")
    if vault_path:
        vault_path.parent.mkdir(parents=True, exist_ok=True)
        vault_path.write_text(render_vault_note(report), encoding="utf-8")
    return md_path, js_path, st_path, vault_path


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Aureon's safe capability growth loop.")
    parser.add_argument("--repo-root", default="", help="Repo root; defaults to current Aureon repo.")
    parser.add_argument("--iterations", type=int, default=1, help="Number of growth iterations.")
    parser.add_argument("--run-checks", action="store_true", help="Run safe focused benchmark/check commands.")
    parser.add_argument("--author-skills", action="store_true", help="Generate validated local SkillLibrary improvement skills.")
    parser.add_argument("--queue-contracts", action="store_true", help="Persist improvement work orders.")
    parser.add_argument("--max-gaps", type=int, default=8, help="Maximum gaps to turn into improvements.")
    parser.add_argument("--python", default="", help="Python executable for check commands.")
    parser.add_argument("--markdown", default=str(DEFAULT_OUTPUT_MD), help="Markdown report path.")
    parser.add_argument("--json", default=str(DEFAULT_OUTPUT_JSON), help="JSON manifest path.")
    parser.add_argument("--state", default=str(DEFAULT_STATE_PATH), help="State JSON path.")
    parser.add_argument("--no-vault", action="store_true", help="Do not write the compact vault note.")
    parser.add_argument("--no-write", action="store_true", help="Print summary only.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from()
    report = build_capability_growth_loop(
        root,
        iterations=args.iterations,
        run_checks=args.run_checks,
        author_skills=args.author_skills,
        queue_contracts=args.queue_contracts,
        max_gaps=args.max_gaps,
        python_exe=args.python or None,
    )
    if args.no_write:
        print(json.dumps({"status": report.status, "summary": report.summary}, indent=2, sort_keys=True))
    else:
        md_path, js_path, state_path, vault_path = write_report(
            report,
            Path(args.markdown),
            Path(args.json),
            Path(args.state),
            write_vault=not args.no_vault,
        )
        print(
            json.dumps(
                {
                    "status": report.status,
                    "markdown": str(md_path),
                    "json": str(js_path),
                    "state": str(state_path),
                    "vault_note": str(vault_path) if vault_path else "",
                    "summary": report.summary,
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 2 if report.status == "growth_loop_needs_repair" else 0


if __name__ == "__main__":
    raise SystemExit(main())
