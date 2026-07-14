"""Validate Aureon's repo-wide real-data contract.

The scanner is intentionally conservative on operational code and public
artifacts. Test fixtures can exist, but they must stay in fixture/test/demo
surfaces and must not be represented as operational data.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from aureon.observer.real_data_contract import (
    TRUTH_STATUSES,
    load_source_registry,
    registered_source_ids,
    validate_metric_envelope,
)

TEXT_SUFFIXES = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".md",
    ".ps1",
    ".bat",
    ".cmd",
    ".html",
}
MAX_SCAN_BYTES = 2_000_000

SKIP_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
}

QUARANTINE_PATH_PARTS = {
    "archive",
    "imports",
    "queen_backups",
    "aureon_generated_apps",
    "aureon_adaptive_skills",
    "logs",
    "state",
    "ws_cache",
    "fixtures",
}

QUARANTINE_PREFIXES = (
    "docs/audits/",
    "frontend/public/aureon_complex_build_artifacts/",
    "frontend/public/aureon_gold_intelligence/",
)

QUARANTINE_EXACT_PATHS = {
    "frontend/public/aureon_organism_runtime_status.json",
    "aureon/core/aureon_lattice.py",
    "aureon/core/aureon_mycelium.py",
    "aureon/harmonic/aureon_harmonic_reality.py",
    "aureon/trading/aureon_kraken_ecosystem.py",
    "aureon/trading/aureon_omega.py",
    "aureon/trading/aureon_queen_execute.py",
    "aureon/trading/aureon_queen_live_runner.py",
    "aureon/trading/aureon_the_play.py",
    "aureon/trading/aureon_the_play_old.py",
    "aureon/trading/aureon_tsx_trader.py",
    "aureon/trading/aureon_ultimate.py",
    "aureon/trading/aureon_unified_ecosystem.py",
    "aureon/trading/compound_king.py",
    "aureon/trading/micro_profit_labyrinth.py",
    "aureon/trading/unified_sniper_brain.py",
}

TEST_PATH_PARTS = {
    "tests",
    "test",
    "benchmarks",
    "benchmark",
    "stress",
    "mega",
    "hyper",
}

FIXTURE_NAME_TOKENS = (
    "backtest",
    "benchmark",
    "demo",
    "demonstration",
    "forensics",
    "historical",
    "replay",
    "sim",
    "simulated",
    "simulation",
    "stress",
    "test",
    "trainer",
    "training",
)

OPERATIONAL_PATH_PREFIXES = (
    "aureon/atn/",
    "aureon/core/",
    "aureon/data_feeds/",
    "aureon/exchanges/",
    "aureon/harmonic/",
    "aureon/integrations/",
    "aureon/operator/",
    "aureon/trading/",
    "scripts/launchers/",
    "scripts/validation/",
    "frontend/src/hooks/",
    "frontend/src/lib/",
    "frontend/src/services/",
    "frontend/public/",
    "server/",
)

BLOCK_PATTERNS = (
    ("demo_key", re.compile(r"\bDEMO" + r"_KEY\b")),
    ("allow_sim_fallback_on", re.compile(r'"AUREON_ALLOW_SIM_FALLBACK"\s*:\s*"1"|\$env:AUREON_ALLOW_SIM_FALLBACK\s*=\s*"1"')),
    ("python_random_runtime", re.compile(r"\brandom\.(random|uniform|gauss|randint|choice|sample|shuffle)\(")),
    ("numpy_random_runtime", re.compile(r"\bnp\.random\.|numpy\.random\.")),
    ("js_random_runtime", re.compile(r"\bMath\.random\s*\(")),
    ("mock_or_synthetic_marker", re.compile(r"\b(mock|synthetic|placeholder|fake)\b", re.IGNORECASE)),
)

APPROVED_RUNTIME_TEXT = (
    "simulation_fallback_allowed",
    "log_blocked_fallback",
    "fallback_marker",
    "make_test_fixture_metric",
    "truth_status",
    "test_fixture",
    "no_data",
    "real_derived",
    "validate_real_data_contract",
)

METRIC_TOKENS = (
    "amount",
    "amplitude",
    "change",
    "close",
    "coherence",
    "confidence",
    "density",
    "frequency",
    "high",
    "hrv",
    "index",
    "low",
    "metric",
    "move",
    "open",
    "pnl",
    "price",
    "quality",
    "score",
    "sentiment",
    "signal",
    "temperature",
    "value",
    "velocity",
    "volume",
    "win",
)


@dataclass
class Finding:
    severity: str
    code: str
    path: str
    line: int
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def repo_root_from(start: Path) -> Path:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / "aureon").is_dir() and (candidate / "data").is_dir():
            return candidate
    return current


def iter_text_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        rel_parts = set(current.relative_to(root).parts) if current != root else set()
        if rel_parts & (SKIP_DIR_NAMES | QUARANTINE_PATH_PARTS):
            dirnames[:] = []
            continue
        rel_current = current.relative_to(root).as_posix() if current != root else ""
        if rel_current and any((rel_current + "/").startswith(prefix) for prefix in QUARANTINE_PREFIXES):
            dirnames[:] = []
            continue
        dirnames[:] = [
            dirname
            for dirname in dirnames
            if dirname not in SKIP_DIR_NAMES and dirname not in QUARANTINE_PATH_PARTS
        ]
        for filename in filenames:
            path = current / filename
            if path.suffix.lower() in TEXT_SUFFIXES and path.stat().st_size <= MAX_SCAN_BYTES:
                yield path


def rel_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def is_quarantined(path: str) -> bool:
    parts = set(Path(path).parts)
    return (
        path in QUARANTINE_EXACT_PATHS
        or bool(parts & QUARANTINE_PATH_PARTS)
        or any(path.startswith(prefix) for prefix in QUARANTINE_PREFIXES)
    )


def is_test_fixture_path(path: str) -> bool:
    parts = set(Path(path).parts)
    filename = Path(path).name.lower()
    stem = Path(path).stem.lower()
    return (
        bool(parts & TEST_PATH_PARTS)
        or filename.startswith("test_")
        or filename.endswith("_test.py")
        or any(token in stem for token in FIXTURE_NAME_TOKENS)
    )


def is_operational_path(path: str) -> bool:
    return path.startswith(OPERATIONAL_PATH_PREFIXES) and not is_quarantined(path) and not is_test_fixture_path(path)


def approved_runtime_context(text: str) -> bool:
    return any(marker in text for marker in APPROVED_RUNTIME_TEXT)


def guarded_fallback_context(lines: list[str], line_no: int) -> bool:
    start = max(0, line_no - 220)
    context = "\n".join(lines[start:line_no])
    return (
        "simulation_fallback_allowed" in context
        or "log_blocked_fallback" in context
        or "AUREON_ALLOW_SIM_FALLBACK" in context
    )


def random_line_is_metric_like(line: str) -> bool:
    lower = line.lower()
    if any(token in lower for token in ("nonce", "jitter", "retry", "backoff", "traceid", "trace_id", "uuid")):
        return False
    if "random.choice" in lower or "random.sample" in lower or "random.shuffle" in lower:
        return any(token in lower for token in METRIC_TOKENS)
    return True


def scan_text_file(path: Path, root: Path) -> list[Finding]:
    rel = rel_posix(path, root)
    findings: list[Finding] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as exc:
        return [Finding("error", "unreadable", rel, 0, f"{type(exc).__name__}: {exc}")]

    operational = is_operational_path(rel)
    fixture = is_test_fixture_path(rel) or is_quarantined(rel)
    in_docstring = False
    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "//", "/*", "*")):
            continue
        triple_count = line.count('"""') + line.count("'''")
        docstring_line = in_docstring or triple_count > 0
        for code, pattern in BLOCK_PATTERNS:
            if not pattern.search(line):
                continue
            if code == "mock_or_synthetic_marker" and approved_runtime_context(line):
                continue
            if fixture:
                severity = "fixture"
            elif code in {"python_random_runtime", "numpy_random_runtime", "js_random_runtime"} and not random_line_is_metric_like(line):
                severity = "warning"
            elif code in {"python_random_runtime", "numpy_random_runtime", "js_random_runtime"} and guarded_fallback_context(lines, line_no):
                severity = "warning"
            elif code == "mock_or_synthetic_marker" or docstring_line:
                severity = "warning"
            elif operational:
                severity = "error"
            else:
                severity = "warning"
            findings.append(Finding(severity, code, rel, line_no, stripped[:240]))
        if triple_count % 2 == 1:
            in_docstring = not in_docstring
    return findings


def validate_registry(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    registry = load_source_registry(root)
    sources = registry.get("sources", {})
    if not isinstance(sources, dict):
        return [Finding("error", "source_registry_invalid", "data/real_data_sources.json", 0, "sources must be object")]
    for source_id, source in sources.items():
        if not isinstance(source, dict):
            findings.append(Finding("error", "source_registry_invalid", "data/real_data_sources.json", 0, str(source_id)))
            continue
        for key in ("name", "category", "endpoint", "freshness_ttl_sec", "derived_metrics_allowed"):
            if key not in source:
                findings.append(
                    Finding("error", "source_registry_missing_field", "data/real_data_sources.json", 0, f"{source_id}.{key}")
                )
        demo_key_marker = "DEMO" + "_KEY"
        if demo_key_marker in json.dumps(source):
            findings.append(Finding("error", "source_registry_demo_key", "data/real_data_sources.json", 0, str(source_id)))
    return findings


def validate_public_metric_json(path: Path, root: Path, source_ids: set[str]) -> list[Finding]:
    rel = rel_posix(path, root)
    findings: list[Finding] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return findings

    metric_envelope_keys = {
        "source_id",
        "source_name",
        "source_url",
        "collected_at",
        "freshness_ttl_sec",
        "is_operational_metric",
    }

    def walk(value: Any, trail: str) -> None:
        if isinstance(value, dict):
            if "truth_status" in value:
                if metric_envelope_keys & set(value):
                    try:
                        validate_metric_envelope(value, registry_source_ids=source_ids)
                    except ValueError as exc:
                        findings.append(Finding("error", "invalid_metric_envelope", rel, 0, f"{trail}: {exc}"))
                    return
            for key, child in value.items():
                walk(child, f"{trail}.{key}" if trail else str(key))
        elif isinstance(value, list):
            for idx, child in enumerate(value):
                walk(child, f"{trail}[{idx}]")

    walk(payload, "")
    return findings


def run(root: Path, *, strict: bool = False, json_output: bool = False) -> int:
    findings: list[Finding] = []
    findings.extend(validate_registry(root))
    source_ids = registered_source_ids(root)
    if "test_fixture" not in source_ids:
        findings.append(Finding("error", "source_registry_missing_test_fixture", "data/real_data_sources.json", 0, ""))

    for path in iter_text_files(root):
        findings.extend(scan_text_file(path, root))
        rel = rel_posix(path, root)
        if rel.startswith("frontend/public/") and path.suffix.lower() == ".json":
            findings.extend(validate_public_metric_json(path, root, source_ids))

    error_count = sum(1 for item in findings if item.severity == "error")
    warning_count = sum(1 for item in findings if item.severity == "warning")
    fixture_count = sum(1 for item in findings if item.severity == "fixture")
    summary = {
        "schema_version": "aureon-real-data-contract-validation-v1",
        "root": str(root),
        "truth_statuses": sorted(TRUTH_STATUSES),
        "error_count": error_count,
        "warning_count": warning_count,
        "fixture_count": fixture_count,
        "source_count": len(source_ids),
        "findings": [item.to_dict() for item in findings],
    }

    if json_output:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            "real-data contract: "
            f"errors={error_count} warnings={warning_count} fixtures={fixture_count} sources={len(source_ids)}"
        )
        for item in findings[:200]:
            text = item.text.encode("ascii", errors="replace").decode("ascii")
            print(f"{item.severity.upper()} {item.code} {item.path}:{item.line} {text}")
        if len(findings) > 200:
            print(f"... {len(findings) - 200} additional findings omitted")

    return 1 if error_count or (strict and warning_count) else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failure.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)
    root = repo_root_from(Path(args.repo_root))
    return run(root, strict=args.strict, json_output=args.json)


if __name__ == "__main__":
    raise SystemExit(main())
