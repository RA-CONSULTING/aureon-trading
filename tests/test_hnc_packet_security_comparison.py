import json

from aureon.autonomous.aureon_hnc_packet_security_comparison import (
    SCHEMA_VERSION,
    build_hnc_packet_security_comparison,
    write_hnc_packet_security_comparison,
)


def _row(report, method):
    return next(row for row in report["rows"] if row["method"] == method)


def test_hnc_packet_security_comparison_scores_relative_security():
    report = build_hnc_packet_security_comparison()

    hnc = _row(report, "Aureon HNC harmonic packet v1")
    swarm = _row(report, "Aureon HNC swarm two-way locknote packet v1")
    plaintext = _row(report, "Plaintext .env values")
    base64_row = _row(report, "Base64/encoding only")
    sha_only = _row(report, "SHA-256 hash only")
    kms = _row(report, "Cloud KMS / HSM-backed envelope encryption")

    assert report["schema_version"] == SCHEMA_VERSION
    assert hnc["score"] > plaintext["score"]
    assert hnc["score"] > base64_row["score"]
    assert hnc["score"] > sha_only["score"]
    assert swarm["score"] > hnc["score"]
    assert kms["score"] > hnc["score"]
    assert report["summary"]["breaker_passed"] is True
    assert report["summary"]["swarm_breaker_passed"] is True
    assert report["summary"]["symbolic_route_bound_to_packets"] is True
    assert report["summary"]["symbolic_route_catalogs_present"] >= 4
    assert report["summary"]["main_weakness"] == "operator-managed key custody"


def test_hnc_packet_security_comparison_writes_public_reports(tmp_path):
    report = build_hnc_packet_security_comparison()
    output_json, output_md, public_json = write_hnc_packet_security_comparison(
        report,
        tmp_path / "docs" / "audits" / "aureon_hnc_packet_security_comparison.json",
        tmp_path / "docs" / "audits" / "aureon_hnc_packet_security_comparison.md",
        tmp_path / "frontend" / "public" / "aureon_hnc_packet_security_comparison.json",
    )

    payload = json.loads(output_json.read_text(encoding="utf-8"))
    markdown = output_md.read_text(encoding="utf-8")

    assert output_json.exists()
    assert output_md.exists()
    assert public_json.exists()
    assert payload["secret_policy"] == "metadata_only_no_secret_values"
    assert "comparison-sample-secret" not in json.dumps(payload)
    assert "comparison-swarm-secret" not in json.dumps(payload)
    assert "Aureon HNC Packet Security Comparison" in markdown
    assert "Windows Credential Manager" in markdown
    assert "swarm" in markdown.lower()
    assert "Symbolic route" in markdown
