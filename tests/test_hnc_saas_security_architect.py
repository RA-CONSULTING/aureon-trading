import json

from aureon.autonomous.hnc_saas_security_architect import (
    build_hnc_saas_security_blueprint,
    inventory_hnc_systems,
    render_markdown,
    write_report,
)


def _make_fake_repo(root):
    (root / "aureon" / "core").mkdir(parents=True)
    (root / "aureon" / "autonomous").mkdir(parents=True)
    (root / "scripts").mkdir()
    (root / "frontend" / "src" / "lib").mkdir(parents=True)
    (root / "Kings_Accounting_Suite" / "core").mkdir(parents=True)
    (root / "aureon" / "core" / "hnc_gateway.py").write_text(
        "class HNCGateway:\n    pass\n",
        encoding="utf-8",
    )
    (root / "Kings_Accounting_Suite" / "core" / "hnc_tax.py").write_text(
        "class HNCAurisValidator:\n    pass\nVAT = True\nHMRC = True\n",
        encoding="utf-8",
    )
    (root / "frontend" / "src" / "lib" / "harmonic-nexus-auth.ts").write_text(
        "export class HarmonicNexusAuth { validateSession() { return true } }\n",
        encoding="utf-8",
    )


def test_inventory_finds_hnc_surfaces_without_importing(tmp_path):
    _make_fake_repo(tmp_path)

    inventory = inventory_hnc_systems(tmp_path)
    paths = {item["path"] for item in inventory}

    assert "aureon/core/hnc_gateway.py" in paths
    assert "Kings_Accounting_Suite/core/hnc_tax.py" in paths
    assert any(item["surface_type"] == "frontend_identity_hnc" for item in inventory)


def test_blueprint_makes_unhackable_the_internal_benchmark_loop(tmp_path):
    _make_fake_repo(tmp_path)

    blueprint = build_hnc_saas_security_blueprint(tmp_path)
    data = blueprint.to_dict()
    control_domains = {item["domain"] for item in data["controls"]}

    assert data["status"] == "blueprint_ready_implementation_required"
    assert data["summary"]["unhackable_internal_goal_active"] is True
    assert data["summary"]["public_unhackable_claim_allowed"] is False
    assert data["summary"]["security_target"] == "unhackable_pursuit_loop"
    assert data["summary"]["authorized_self_attack_required"] is True
    assert data["summary"]["unhackable_benchmark_count"] >= 8
    assert "unhackable_pursuit_loop" in data
    assert "tenant_isolation" in control_domains
    assert "ai_llm_tool_governance" in control_domains
    assert "trading_authority_boundary" in control_domains
    assert "accounting_filing_boundary" in control_domains
    assert all(gate["blocks_release"] for gate in data["release_gates"])


def test_blueprint_queues_safe_contracts(tmp_path):
    _make_fake_repo(tmp_path)

    blueprint = build_hnc_saas_security_blueprint(
        tmp_path,
        queue_contracts=True,
        contract_state_path=tmp_path / "state" / "hnc_saas_contracts.json",
    )
    contract_plan = blueprint.contract_plan

    assert blueprint.status == "blueprint_ready_implementation_queued"
    assert contract_plan["queued_persistently"] is True
    assert contract_plan["work_order_count"] == blueprint.summary["control_count"]
    assert contract_plan["benchmark_work_order_count"] == blueprint.summary["unhackable_benchmark_count"]
    assert contract_plan["status"]["queue_count"] >= (
        blueprint.summary["control_count"] + blueprint.summary["unhackable_benchmark_count"]
    )
    assert (tmp_path / "state" / "hnc_saas_contracts.json").exists()


def test_markdown_and_json_outputs_include_release_gates(tmp_path):
    _make_fake_repo(tmp_path)
    blueprint = build_hnc_saas_security_blueprint(tmp_path)

    markdown = render_markdown(blueprint)
    assert "HNC SaaS Security Blueprint" in markdown
    assert "Release Gates" in markdown
    assert "Unhackable Pursuit Loop" in markdown
    assert "try_to_break_own_system" in markdown
    assert "zero-trust" in markdown.lower()

    md_path, json_path, vault_path = write_report(
        blueprint,
        tmp_path / "blueprint.md",
        tmp_path / "blueprint.json",
        tmp_path / "vault.md",
    )
    assert md_path.exists()
    assert vault_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["summary"]["control_count"] >= 12
    assert data["summary"]["unhackable_internal_goal_active"] is True
