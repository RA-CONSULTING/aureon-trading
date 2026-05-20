"""Publish HNC symbolic route-seal evidence."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from aureon.harmonic.hnc_symbolic_route_seal import (
    build_symbolic_route_seal,
    load_symbolic_catalog_manifest,
    symbolic_route_public_summary,
    validate_symbolic_route_seal,
)


SCHEMA_VERSION = "aureon-hnc-symbolic-route-report-v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_JSON = REPO_ROOT / "docs/audits/aureon_hnc_symbolic_route_seal.json"
DEFAULT_OUTPUT_MD = REPO_ROOT / "docs/audits/aureon_hnc_symbolic_route_seal.md"
DEFAULT_PUBLIC_JSON = REPO_ROOT / "frontend/public/aureon_hnc_symbolic_route_seal.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_hnc_symbolic_route_report() -> dict[str, Any]:
    manifest = load_symbolic_catalog_manifest()
    sample_routes = []
    samples = [
        ("repo:singularity_vault", {"intent": "sealed_repo_snapshot"}, {"domain": "repo_singularity_vault"}),
        ("env:exchange_credential_packet", {"env_key": "EXCHANGE_CREDENTIAL_PACKET"}, {"domain": "local_env_credentials"}),
        ("trading:decision_route", {"venue": "multi_exchange"}, {"domain": "hnc_auris_trading_cognition"}),
    ]
    for purpose, operator_aad, context in samples:
        seal = build_symbolic_route_seal(purpose=purpose, operator_aad=operator_aad, hnc_context=context)
        sample_routes.append(
            {
                "purpose": purpose,
                "summary": symbolic_route_public_summary(seal),
                "validation": validate_symbolic_route_seal(seal),
                "route": seal["route"],
                "route_seal_sha256": seal["route_seal_sha256"],
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "status": "symbolic_route_seal_ready",
        "catalog_manifest": manifest,
        "sample_routes": sample_routes,
        "security_boundary": {
            "role": "authenticated symbolic packet metadata",
            "not_a_cipher": True,
            "not_a_secret_store": True,
            "does_not_replace": "AES-GCM, HKDF, DPAPI, Windows Credential Manager, KMS, HSM, or OS permissions",
        },
        "acceptance": {
            "catalogs_present": manifest["summary"]["catalogs_present"],
            "symbol_count": manifest["summary"]["symbol_count"],
            "all_sample_routes_valid": all(route["validation"]["valid"] for route in sample_routes),
            "packet_tamper_effect": "route changes alter the HNC alignment hash and packet hash before decode",
        },
        "secret_policy": "metadata_only_no_secret_values",
    }


def render_markdown(report: dict[str, Any]) -> str:
    acceptance = report.get("acceptance", {})
    lines = [
        "# Aureon HNC Symbolic Route Seal",
        "",
        f"Generated: `{report.get('generated_at')}`",
        "",
        "## Summary",
        "",
        f"- Status: `{report.get('status')}`",
        f"- Catalogs present: `{acceptance.get('catalogs_present')}`",
        f"- Symbol count: `{acceptance.get('symbol_count')}`",
        f"- Sample routes valid: `{acceptance.get('all_sample_routes_valid')}`",
        f"- Tamper effect: {acceptance.get('packet_tamper_effect')}",
        "",
        "## Security Boundary",
        "",
        f"- Role: {report['security_boundary']['role']}",
        f"- Not a cipher: `{report['security_boundary']['not_a_cipher']}`",
        f"- Not a secret store: `{report['security_boundary']['not_a_secret_store']}`",
        f"- Does not replace: {report['security_boundary']['does_not_replace']}",
        "",
        "## Sample Routes",
        "",
    ]
    for route in report.get("sample_routes", []):
        summary = route.get("summary", {})
        lines.extend(
            [
                f"### `{route.get('purpose')}`",
                "",
                f"- Valid: `{summary.get('valid')}`",
                f"- Route seal SHA-256: `{route.get('route_seal_sha256')}`",
                f"- Rune: `{summary.get('rune')}`",
                f"- Auris symbol: `{summary.get('auris_symbol')}`",
                f"- Threshold layer: `{summary.get('threshold_layer')}`",
                "",
            ]
        )
    return "\n".join(lines)


def write_hnc_symbolic_route_report(
    report: dict[str, Any],
    output_json: Path = DEFAULT_OUTPUT_JSON,
    output_md: Path = DEFAULT_OUTPUT_MD,
    public_json: Path = DEFAULT_PUBLIC_JSON,
) -> tuple[Path, Path, Path]:
    for path in (output_json, output_md, public_json):
        path.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    public_json.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True), encoding="utf-8")
    return output_json, output_md, public_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Aureon HNC symbolic route-seal report.")
    parser.add_argument("--json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--md", type=Path, default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--public-json", type=Path, default=DEFAULT_PUBLIC_JSON)
    args = parser.parse_args(argv)
    report = build_hnc_symbolic_route_report()
    outputs = write_hnc_symbolic_route_report(report, args.json, args.md, args.public_json)
    print(json.dumps({"ok": True, "status": report["status"], "outputs": [str(path) for path in outputs]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
