import json

from aureon.autonomous.aureon_hnc_symbolic_route_report import (
    SCHEMA_VERSION,
    build_hnc_symbolic_route_report,
    write_hnc_symbolic_route_report,
)


def test_hnc_symbolic_route_report_builds_valid_sample_routes():
    report = build_hnc_symbolic_route_report()

    assert report["schema_version"] == SCHEMA_VERSION
    assert report["status"] == "symbolic_route_seal_ready"
    assert report["acceptance"]["catalogs_present"] >= 4
    assert report["acceptance"]["all_sample_routes_valid"] is True
    assert report["security_boundary"]["not_a_cipher"] is True


def test_hnc_symbolic_route_report_writes_public_artifacts(tmp_path):
    report = build_hnc_symbolic_route_report()
    output_json, output_md, public_json = write_hnc_symbolic_route_report(
        report,
        tmp_path / "docs" / "audits" / "aureon_hnc_symbolic_route_seal.json",
        tmp_path / "docs" / "audits" / "aureon_hnc_symbolic_route_seal.md",
        tmp_path / "frontend" / "public" / "aureon_hnc_symbolic_route_seal.json",
    )

    payload = json.loads(output_json.read_text(encoding="utf-8"))
    markdown = output_md.read_text(encoding="utf-8")

    assert output_json.exists()
    assert output_md.exists()
    assert public_json.exists()
    assert payload["secret_policy"] == "metadata_only_no_secret_values"
    assert "Aureon HNC Symbolic Route Seal" in markdown
    assert "Does not replace" in markdown
