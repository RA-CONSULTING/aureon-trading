import json
import subprocess
from pathlib import Path

from aureon.autonomous.aureon_capability_growth_loop import (
    BenchmarkCheck,
    author_improvement_skills,
    build_capability_growth_loop,
    collect_domain_capabilities,
    detect_capability_gaps,
    render_markdown,
    run_benchmark_checks,
    write_report,
)


def _seed_audits(root: Path) -> None:
    audits = root / "docs" / "audits"
    audits.mkdir(parents=True)
    (root / "aureon").mkdir(exist_ok=True)
    (root / "scripts").mkdir(exist_ok=True)
    (audits / "aureon_repo_self_catalog.json").write_text(
        json.dumps(
            {
                "status": "catalog_complete_with_attention_items",
                "summary": {
                    "cataloged_file_count": 42,
                    "subsystem_count": 8,
                    "secret_metadata_only_count": 2,
                    "coverage_policy": "all project files labelled",
                    "truncated": False,
                },
            }
        ),
        encoding="utf-8",
    )
    (audits / "mind_wiring_audit.json").write_text(
        json.dumps({"counts": {"wired": 10, "partial": 0, "broken": 0, "unknown": 0}}),
        encoding="utf-8",
    )
    proofs = [
        {"id": "repo_organization", "status": "working", "summary": "ok", "systems": ["RepoWideOrganizationAudit"]},
        {"id": "goal_routing", "status": "working", "summary": "ok", "systems": ["GoalCapabilityMap"]},
        {"id": "trading_brain", "status": "working_safe_simulation", "summary": "safe sim", "systems": ["UnifiedMarginBrain"]},
        {"id": "accounting_brain", "status": "working_with_attention", "summary": "manual filing", "systems": ["AccountingContextBridge"]},
        {"id": "research_vault", "status": "working", "summary": "ok", "systems": ["ResearchCorpusIndex"]},
        {"id": "llm_capability", "status": "working_with_attention", "summary": "fallback", "systems": ["AureonHybridAdapter"]},
        {"id": "operator_surfaces", "status": "working", "summary": "ok", "systems": ["dashboard"]},
        {"id": "ignition", "status": "working", "summary": "ok", "systems": ["scripts/aureon_ignition.py"]},
    ]
    (audits / "aureon_system_readiness_audit.json").write_text(
        json.dumps({"status": "working_with_attention_items", "summary": {"real_orders_allowed": False}, "proofs": proofs}),
        encoding="utf-8",
    )


def test_collect_domains_and_detect_gaps(tmp_path):
    _seed_audits(tmp_path)

    domains = collect_domain_capabilities(tmp_path)
    gaps = detect_capability_gaps(domains)

    ids = {domain.id for domain in domains}
    assert "repo_self_catalog" in ids
    assert "code_architect_skill_authoring" in ids
    assert "accounting_compliance" in ids
    assert any(gap.domain == "accounting_compliance" for gap in gaps)
    assert any(gap.route == "capability_growth_loop" for gap in gaps)


def test_author_improvement_skills_writes_validated_skill_library(tmp_path):
    _seed_audits(tmp_path)
    gaps = detect_capability_gaps(collect_domain_capabilities(tmp_path))[:2]

    authored = author_improvement_skills(tmp_path, gaps, limit=2)

    assert authored
    assert all(item.validation_ok for item in authored)
    assert all(item.registered for item in authored)
    library_path = tmp_path / "state" / "capability_growth_skills" / "skill_library.json"
    assert library_path.exists()
    data = json.loads(library_path.read_text(encoding="utf-8"))
    assert data["count"] >= 1


def test_run_benchmark_checks_records_pass_and_failure(tmp_path):
    def fake_runner(command, cwd, env, text, capture_output, timeout):
        return subprocess.CompletedProcess(
            args=command,
            returncode=0 if command[-1] == "pass" else 1,
            stdout="ok",
            stderr="bad" if command[-1] != "pass" else "",
        )

    checks = run_benchmark_checks(
        tmp_path,
        [
            ("passing", ["python", "pass"]),
            ("failing", ["python", "fail"]),
        ],
        runner=fake_runner,
    )

    assert checks[0].status == "passed"
    assert checks[1].status == "failed"


def test_build_growth_loop_writes_report_vault_and_contracts(tmp_path):
    _seed_audits(tmp_path)
    report = build_capability_growth_loop(
        tmp_path,
        iterations=1,
        run_checks=False,
        author_skills=True,
        queue_contracts=True,
        max_gaps=3,
    )

    assert report.schema_version == "aureon-capability-growth-loop-v1"
    assert report.summary["iteration_count"] == 1
    assert report.summary["latest_gap_count"] >= 1
    assert report.summary["latest_registered_improvement_count"] >= 1
    assert report.iterations[0].contract_plan["queued_persistently"] is True

    markdown = render_markdown(report)
    assert "Aureon Capability Growth Loop" in markdown
    assert "audit -> benchmark" in markdown

    md_path, json_path, state_path, vault_path = write_report(
        report,
        tmp_path / "growth.md",
        tmp_path / "growth.json",
        tmp_path / "growth_state.json",
    )

    assert md_path.exists()
    assert json_path.exists()
    assert state_path.exists()
    assert vault_path and vault_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["vault_memory"]["status"] == "written"


def test_validation_domain_uses_benchmark_results(tmp_path):
    _seed_audits(tmp_path)
    failed = BenchmarkCheck(
        id="demo_fail",
        command=["python", "-c", "exit(1)"],
        status="failed",
        returncode=1,
        duration_s=0.1,
    )

    report = build_capability_growth_loop(tmp_path, iterations=1, run_checks=False)
    # Build an iteration path directly with the failed check via domain collection.
    domains = collect_domain_capabilities(tmp_path, benchmark_checks=[failed])
    validation = [domain for domain in domains if domain.id == "validation_benchmarking"][0]

    assert report.summary["iteration_count"] == 1
    assert validation.status == "blocked_or_missing"
    assert validation.score == 0.20
