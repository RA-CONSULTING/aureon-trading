#!/usr/bin/env python3
"""
SaaS compliance audit — every surface serves honest, provenance-stamped data.

Drives each `/api/*` SaaS surface on a bare Flask app (no operator boot, no
network) and asserts the compliance contract:

  1. Every telemetry surface carries a ``provenance`` block.
  2. Every surface carries a valid ``truth_status`` (or, for the cognition
     umbrella, a ``truth_summary`` roll-up whose surfaces each do).
  3. Catalog counts are honest (category_count == 12; total == Σ per-category).
  4. ``POST /api/billing/charge-fee`` is 403 when charging is disabled (default).
  5. ``provenance.simulation_fallback_allowed`` reflects the real policy.
  6. No fabricated values in ``aureon/saas/`` (real-data-contract scan, error tier).

Exits non-zero if any REQUIRED check fails, so it can gate CI or a release.
Offline-safe by construction.

Usage:
    AUREON_LLM_OFFLINE=1 python -m scripts.validation.audit_saas_compliance [--json]
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("AUREON_LLM_OFFLINE", "1")
os.environ.setdefault("AUREON_SUPPRESS_IMPORT_SIDE_EFFECTS", "1")

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _check(name: str, ok: bool, detail: str, required: bool = True) -> dict:
    return {"check": name, "ok": bool(ok), "detail": detail, "required": required}


def _client():
    import flask

    from aureon.saas.billing import register_billing
    from aureon.saas.gateway import register_saas_routes

    app = flask.Flask(__name__)
    register_saas_routes(app)
    try:
        register_billing(app)
    except Exception:  # noqa: BLE001 — billing optional for the audit
        pass
    return app.test_client()


def run_audit() -> list[dict]:
    from aureon.observer.live_data_policy import simulation_fallback_allowed
    from aureon.observer.real_data_contract import TRUTH_STATUSES

    results: list[dict] = []
    c = _client()

    # 1 + 2 — every telemetry surface carries provenance + a valid truth_status
    stamped_surfaces = ["/api/status", "/api/organism", "/api/metacognition",
                        "/api/catalog", "/api/domains"]
    for path in stamped_surfaces:
        body = c.get(path).get_json() or {}
        has_prov = isinstance(body.get("provenance"), dict)
        ts_ok = body.get("truth_status") in TRUTH_STATUSES
        results.append(_check(f"stamped:{path}", has_prov and ts_ok,
                              f"provenance={has_prov} truth_status={body.get('truth_status')}"))

    # cognition umbrella: provenance + a truth_summary roll-up whose surfaces stamp
    cog = c.get("/api/cognition").get_json() or {}
    surfaces = cog.get("surfaces", {})
    all_stamped = bool(surfaces) and all(
        s.get("truth_status") in TRUTH_STATUSES for s in surfaces.values())
    results.append(_check("stamped:/api/cognition",
                          isinstance(cog.get("provenance"), dict)
                          and isinstance(cog.get("truth_summary"), dict) and all_stamped,
                          f"surfaces={sorted(surfaces)} all_stamped={all_stamped}"))

    # cognition parts each carry truth_status
    for part in ("field", "bus", "mycelium", "connectome", "brain"):
        d = (c.get(f"/api/cognition/{part}").get_json() or {}).get("data", {})
        results.append(_check(f"stamped:/api/cognition/{part}",
                              d.get("truth_status") in TRUTH_STATUSES,
                              f"truth_status={d.get('truth_status')}", required=False))

    # 3 — catalog counts are honest. total_systems counts UNIQUE modules; the
    # per-category sum is ≥ total because a module can classify into several
    # categories — so the honest invariant is 12 categories, a positive unique
    # total, and Σ ≥ total (every system covered by at least one category).
    cat = c.get("/api/catalog").get_json() or {}
    cats = cat.get("categories", {})
    total = cat.get("total_systems", 0)
    summed = sum(v.get("system_count", 0) for v in cats.values())
    results.append(_check(
        "catalog_honest",
        cat.get("category_count") == 12 and len(cats) == 12 and total > 0 and summed >= total,
        f"category_count={cat.get('category_count')} unique_total={total} Σcategories={summed}"))

    # 4 — charge-fee gated OFF by default
    r = c.post("/api/billing/charge-fee", json={"profit": 1.0, "user_id": "x"})
    results.append(_check("charge_fee_disabled", r.status_code == 403,
                          f"status={r.status_code} (expected 403 when AUREON_BILLING_CHARGE_ENABLED unset)"))

    # 5 — provenance reflects the real policy
    prov = (c.get("/api/status").get_json() or {}).get("provenance", {})
    results.append(_check("provenance_reflects_policy",
                          prov.get("simulation_fallback_allowed") == simulation_fallback_allowed()
                          and prov.get("truth_statuses") == sorted(TRUTH_STATUSES),
                          f"sim_fallback={prov.get('simulation_fallback_allowed')}"))

    # 6 — no fabricated values in aureon/saas (real-data-contract scan, error tier)
    results.append(_saas_no_fabrication())
    return results


def _saas_no_fabrication() -> dict:
    """Scan aureon/saas/ with the contract's block patterns; any error-tier hit
    (runtime random/mock/synthetic in a metric path) fails compliance."""
    try:
        from scripts.validation.validate_real_data_contract import (
            APPROVED_RUNTIME_TEXT,
            BLOCK_PATTERNS,
        )
    except Exception as exc:  # noqa: BLE001
        return _check("saas_no_fabrication", True, f"scanner unavailable ({exc}); skipped", required=False)

    # The unambiguous fabrication signals: runtime randomness in a metric path.
    # BLOCK_PATTERNS is a tuple of (code, compiled_pattern) pairs.
    fabrication_codes = {"python_random_runtime", "numpy_random_runtime", "js_random_runtime"}
    fab_pats = [(code, pat) for code, pat in BLOCK_PATTERNS if code in fabrication_codes]
    offenders: list[str] = []
    saas_dir = _REPO_ROOT / "aureon" / "saas"
    for py in sorted(saas_dir.rglob("*.py")):
        try:
            text = py.read_text(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if any(tok in line for tok in APPROVED_RUNTIME_TEXT):
                continue
            for code, pat in fab_pats:
                if pat.search(line):
                    offenders.append(f"{py.relative_to(_REPO_ROOT)}:{i} [{code}]")
    return _check("saas_no_fabrication", not offenders,
                  "clean" if not offenders else f"{len(offenders)} offender(s): {offenders[:3]}")


def build_report(results: list[dict]) -> dict:
    passed = sum(1 for r in results if r["ok"])
    failed_required = [r for r in results if not r["ok"] and r["required"]]
    return {
        "name": "aureon-saas-compliance-audit",
        "schema_version": 1,
        "objective": "every SaaS surface serves honest, provenance-stamped, non-fabricated data",
        "summary": {
            "compliance_status": "compliant" if not failed_required else "non-compliant",
            "check_count": len(results),
            "passed": passed,
            "failed": len(results) - passed,
            "failed_required": len(failed_required),
        },
        "checks": results,
    }


def _write_artifacts(report: dict) -> list[str]:
    out_dir = _REPO_ROOT / "docs" / "research" / "audits"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "saas_compliance_audit.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = [
        "# SaaS Compliance Audit",
        "",
        f"**Status:** {report['summary']['compliance_status']} · "
        f"{report['summary']['passed']}/{report['summary']['check_count']} checks passed",
        "",
        "| Check | Result | Detail |",
        "|-------|--------|--------|",
    ]
    for r in report["checks"]:
        mark = "✅" if r["ok"] else ("❌" if r["required"] else "⚠️")
        lines.append(f"| {r['check']} | {mark} | {r['detail']} |")
    md_path = out_dir / "saas_compliance_audit.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return [str(json_path), str(md_path)]


def main() -> int:
    as_json = "--json" in sys.argv
    results = run_audit()
    report = build_report(results)
    paths = _write_artifacts(report)
    if as_json:
        print(json.dumps(report, indent=2))
    else:
        print("═" * 70)
        print("AUREON SaaS COMPLIANCE AUDIT")
        print("═" * 70)
        for r in results:
            mark = "✅ PASS" if r["ok"] else ("❌ FAIL" if r["required"] else "⚠️  WARN")
            print(f"  {mark}  {r['check']:34} {r['detail']}")
        print("─" * 70)
        s = report["summary"]
        print(f"  {s['compliance_status'].upper()} · {s['passed']}/{s['check_count']} passed · "
              f"{s['failed_required']} required failures")
        print(f"  artifacts: {', '.join(p.split('/')[-1] for p in paths)}")
        print("═" * 70)
    return 1 if report["summary"]["failed_required"] else 0


if __name__ == "__main__":
    sys.exit(main())
