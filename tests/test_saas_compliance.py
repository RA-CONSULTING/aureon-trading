"""
SaaS compliance — every surface serves honest, provenance-stamped data.

Offline; exercises the compliance audit's own `run_audit()` so the test and the
CLI assert the same contract. Skips if flask isn't installed.
"""

from __future__ import annotations

import pytest

pytest.importorskip("flask", reason="SaaS compliance requires the `.[operator]` extra")

from scripts.validation.audit_saas_compliance import build_report, run_audit  # noqa: E402


def test_all_required_compliance_checks_pass():
    results = run_audit()
    failed_required = [r for r in results if not r["ok"] and r["required"]]
    assert not failed_required, f"required compliance failures: {failed_required}"


def test_report_marks_compliant():
    report = build_report(run_audit())
    assert report["summary"]["compliance_status"] == "compliant"
    assert report["summary"]["failed_required"] == 0


def test_every_surface_is_stamped():
    results = {r["check"]: r for r in run_audit()}
    for surface in ("stamped:/api/status", "stamped:/api/organism",
                    "stamped:/api/metacognition", "stamped:/api/catalog",
                    "stamped:/api/domains", "stamped:/api/cognition"):
        assert results[surface]["ok"], f"{surface} not compliant: {results[surface]['detail']}"


def test_charge_fee_gated_off():
    results = {r["check"]: r for r in run_audit()}
    assert results["charge_fee_disabled"]["ok"]
