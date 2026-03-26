#!/usr/bin/env python3
"""Generate Capital harmonic/probability wiring audit artifacts."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from aureon.exchanges.capital_cfd_trader import CapitalCFDTrader


def main() -> int:
    repo_root = REPO_ROOT
    reports_dir = repo_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    trader = CapitalCFDTrader.__new__(CapitalCFDTrader)
    audit = CapitalCFDTrader._build_harmonic_wiring_audit(trader)

    json_path = reports_dir / "capital_harmonic_wiring_audit.json"
    md_path = reports_dir / "capital_harmonic_wiring_audit.md"

    json_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    lines = [
        "# Capital Harmonic Wiring Audit",
        "",
        f"Generated: {datetime.utcnow().isoformat()}Z",
        "",
        f"- Overall: {'PASS' if audit.get('ok') else 'PARTIAL'}",
        f"- Passed checks: {audit.get('passed', 0)}/{audit.get('total', 0)}",
        "",
        "## Checks",
        "",
        "| Name | Kind | Status | Target | Reason |",
        "|---|---|---|---|---|",
    ]

    for item in audit.get("checks", []):
        status = "✅" if item.get("ok") else "❌"
        lines.append(
            f"| {item.get('name','')} | {item.get('kind','')} | {status} | `{item.get('target','')}` | {item.get('reason','')} |"
        )

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
