import json

from aureon.autonomous.hnc_authorized_attack_lab import (
    build_authorized_attack_lab_report,
    load_historical_tactic_knowledge,
    render_markdown,
    validate_target_scope,
    write_report,
)


def _make_fake_repo(root):
    (root / "aureon" / "core").mkdir(parents=True)
    (root / "aureon" / "autonomous").mkdir(parents=True)
    (root / "scripts").mkdir()
    (root / "docs" / "audits").mkdir(parents=True)
    (root / "docs" / "runbooks").mkdir(parents=True)
    (root / "frontend" / "src" / "lib").mkdir(parents=True)
    (root / "docs" / "SECURITY.md").write_text("Report vulnerability. Never commit secret material.\n", encoding="utf-8")
    (root / "docs" / "runbooks" / "SECURITY_TRADING.md").write_text("Trading risk and live order gates.\n", encoding="utf-8")
    (root / "docs" / "audits" / "hnc_saas_security_blueprint.md").write_text(
        "unhackable zero-trust authorized self-attack\n",
        encoding="utf-8",
    )
    (root / "frontend" / "src" / "lib" / "harmonic-nexus-auth.ts").write_text(
        "export class HarmonicNexusAuth { autoLogin() { return true } }\n",
        encoding="utf-8",
    )
    (root / "aureon" / "core" / "organism_contracts.py").write_text(
        "UNSAFE_ACTION_TYPES = {'place_live_order'}\n",
        encoding="utf-8",
    )


def test_scope_validation_blocks_external_targets(tmp_path):
    _make_fake_repo(tmp_path)

    decisions = validate_target_scope(tmp_path, ["https://example.com", "http://127.0.0.1:8000", "docs"])

    assert decisions[0].allowed is False
    assert decisions[1].allowed is True
    assert decisions[2].allowed is True


def test_historical_knowledge_turns_local_memory_into_defensive_lessons(tmp_path):
    _make_fake_repo(tmp_path)

    lessons = load_historical_tactic_knowledge(tmp_path)
    families = {lesson.family for lesson in lessons}

    assert "access_control" in families
    assert "llm_tool_governance" in families
    assert "financial_authority" in families
    assert all("phishing" not in lesson.safe_simulation.lower() for lesson in lessons)


def test_authorized_attack_lab_runs_static_simulation_and_queues_fixes(tmp_path):
    _make_fake_repo(tmp_path)

    report = build_authorized_attack_lab_report(
        tmp_path,
        targets=["http://localhost:8787"],
        execute_simulations=True,
        queue_fixes=True,
    )
    data = report.to_dict()

    assert data["status"] == "simulations_completed_with_findings"
    assert data["summary"]["external_attacks_allowed"] is False
    assert data["summary"]["authorized_self_attack_required"] is True
    assert data["summary"]["attack_case_count"] >= 6
    assert any(finding["id"] == "finding_auth_autologin_surface" for finding in data["findings"])
    assert data["contract_plan"]["queued_persistently"] is True


def test_attack_lab_fails_closed_on_external_target(tmp_path):
    _make_fake_repo(tmp_path)

    report = build_authorized_attack_lab_report(
        tmp_path,
        targets=["https://not-owned.example"],
        execute_simulations=True,
        queue_fixes=True,
    )

    assert report.status == "blocked_target_scope"
    assert report.summary["blocked_scope_count"] == 1
    assert report.summary["fix_contracts_queued"] is False


def test_attack_lab_report_outputs(tmp_path):
    _make_fake_repo(tmp_path)
    report = build_authorized_attack_lab_report(tmp_path)

    markdown = render_markdown(report)
    assert "HNC Authorized Attack Lab" in markdown
    assert "authorized self-attack" in markdown

    md_path, json_path, vault_path = write_report(
        report,
        tmp_path / "attack_lab.md",
        tmp_path / "attack_lab.json",
        tmp_path / "vault.md",
    )

    assert md_path.exists()
    assert vault_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["summary"]["historical_lesson_count"] >= 6
