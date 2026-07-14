"""
Run the soul deliberation benchmark: feed the soul a ladder of goals from small /
short-horizon to grand / long-horizon and record how it acts. Writes a JSON +
markdown artifact to docs/research/benchmarks/ and exits non-zero if any critical
check fails (so it is a real signal, not decoration).

    AUREON_LLM_OFFLINE=1 python -m scripts.run_soul_benchmark [--cases PATH]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("AUREON_LLM_OFFLINE", "1")
os.environ.setdefault("AUREON_SUPPRESS_IMPORT_SIDE_EFFECTS", "1")

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from aureon.core.soul_benchmark import run_soul_benchmark  # noqa: E402

_MARK = {True: "✅", False: "❌"}


def _write_artifacts(report: dict) -> list[str]:
    out_dir = _REPO_ROOT / "docs" / "research" / "benchmarks"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "soul_deliberation_benchmark.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    s = report["summary"]
    lines = [
        "# Aureon — Soul Deliberation Benchmark",
        "",
        f"**Status:** {'✅ pass' if s['status'] == 'pass' else '❌ fail'} · "
        f"critical {s['critical_passed']}/{s['critical_total']} · "
        f"informational {s['informational_passed']}/{s['informational_total']} · "
        f"{s['check_count']} checks",
        "",
        "How the soul acts as the stakes rise from small / short-horizon goals to "
        "grand / long-horizon ones. Driven read-only through `SoulDeliberation.assess()`.",
        "",
        "## Rungs — small → grand",
        "",
        "| Rung | Cases | Resolve rate | Mean agreement | Mean risk rank | Requires-human rate |",
        "|------|-------|--------------|----------------|----------------|---------------------|",
    ]
    order = ["SMALL", "MEDIUM", "LARGE", "GRAND", "SAFETY"]
    rungs = report.get("rungs", {})
    for rung in [r for r in order if r in rungs] + [r for r in rungs if r not in order]:
        g = rungs[rung]
        lines.append(f"| {rung} | {g['cases']} | {g['resolve_rate']} | {g['mean_agreement']} | "
                     f"{g['mean_risk_rank']} | {g['requires_human_rate']} |")
    lines += ["", "## Checks", "", "| Check | Tier | Result | Detail |",
              "|-------|------|--------|--------|"]
    for c in report["checks"]:
        tier = "critical" if c["critical"] else "info"
        mark = _MARK[c["ok"]] if c["ok"] else (_MARK[False] if c["critical"] else "⚠️")
        lines.append(f"| {c['check']} | {tier} | {mark} | {c['detail']} |")
    md_path = out_dir / "soul_deliberation_benchmark.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return [str(json_path), str(md_path)]


def main() -> int:
    ap = argparse.ArgumentParser(description="Soul deliberation benchmark")
    ap.add_argument("--cases", default=None, help="path to the goal-ladder JSON")
    args = ap.parse_args()

    report = run_soul_benchmark(args.cases)
    paths = _write_artifacts(report)

    print("═" * 74)
    print("AUREON SOUL DELIBERATION BENCHMARK — small → grand")
    print("═" * 74)
    for rung, g in report.get("rungs", {}).items():
        print(f"  {rung:7} cases={g['cases']} resolve={g['resolve_rate']} "
              f"agree={g['mean_agreement']} risk_rank={g['mean_risk_rank']} "
              f"req_human={g['requires_human_rate']}")
    print("─" * 74)
    for c in report["checks"]:
        mark = "✅ PASS" if c["ok"] else ("❌ FAIL" if c["critical"] else "⚠️  WARN")
        print(f"  {mark}  {c['check']:34} {c['detail']}")
    s = report["summary"]
    print("─" * 74)
    print(f"  {s['status'].upper()} · critical {s['critical_passed']}/{s['critical_total']} · "
          f"informational {s['informational_passed']}/{s['informational_total']}")
    for p in paths:
        print(f"  artifact: {p}")
    return 0 if s["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
