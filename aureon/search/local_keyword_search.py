"""Local keyword reader for Aureon's search fabric.

This scans real repo text/test/doc files and returns path, line, and short
snippet evidence. It deliberately skips common dependency/build folders and
credential-looking files so keyword scans do not become accidental secret
capture.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = Path("state/aureon_swarm_keyword_search_latest.json")
PUBLIC_PATH = Path("frontend/public/aureon_swarm_keyword_search_latest.json")

TEXT_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".jsonl",
    ".md",
    ".txt",
    ".yml",
    ".yaml",
    ".toml",
    ".html",
    ".css",
    ".scss",
    ".csv",
}

SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "dist",
    "node_modules",
    "site-packages",
}

SENSITIVE_NAME_PARTS = {
    ".env",
    "credential",
    "credentials",
    "secret",
    "secrets",
    "private_key",
    "apikey",
    "api_key",
    "token",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rooted(root: Optional[Path], rel: Path) -> Path:
    base = Path(root or REPO_ROOT).resolve()
    return rel if rel.is_absolute() else base / rel


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return str(path)


def _safe_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    os.replace(tmp_path, path)


def _iter_candidate_files(scope_root: Path, patterns: Sequence[str]) -> Iterable[Path]:
    for pattern in patterns:
        for path in scope_root.rglob(pattern):
            if not path.is_file():
                continue
            parts = {part.lower() for part in path.parts}
            if parts & SKIP_DIRS:
                continue
            name = path.name.lower()
            if any(marker in name for marker in SENSITIVE_NAME_PARTS):
                continue
            if path.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            yield path


def _line_matches(line: str, terms: Sequence[str], require_all: bool) -> bool:
    lower = line.lower()
    if require_all:
        return all(term in lower for term in terms)
    return any(term in lower for term in terms)


def _snippet(line: str, limit: int = 240) -> str:
    cleaned = re.sub(r"\s+", " ", line.strip())
    return cleaned[:limit]


def run_keyword_search(
    *,
    keyword: str,
    scope: str = "tests",
    patterns: Optional[Sequence[str]] = None,
    max_results: int = 40,
    max_file_bytes: int = 512_000,
    require_all_terms: bool = False,
    repo_root: Optional[Path] = None,
    write_artifact: bool = True,
) -> Dict[str, Any]:
    """Scan real local files for a keyword or phrase.

    The returned results contain short snippets so an operator can inspect the
    match. Public artifacts are still bounded and skip credential-looking files.
    """

    root = Path(repo_root or REPO_ROOT).resolve()
    scope_path = _rooted(root, Path(scope or ".")).resolve()
    if not scope_path.exists():
        payload = {
            "status": "keyword_scope_missing",
            "generated_at": _utc_now(),
            "keyword": keyword,
            "scope": scope,
            "results": [],
            "summary": {
                "scanned_file_count": 0,
                "matched_file_count": 0,
                "match_count": 0,
                "skipped_file_count": 0,
            },
        }
        if write_artifact:
            _safe_write_json(_rooted(root, STATE_PATH), payload)
            _safe_write_json(_rooted(root, PUBLIC_PATH), payload)
        return payload

    terms = [term.lower() for term in re.findall(r"[A-Za-z0-9_./:-]+", keyword or "") if term.strip()]
    if not terms:
        terms = [(keyword or "").strip().lower()]
    terms = [term for term in terms if term]
    globs = list(patterns or ["*"])

    results: List[Dict[str, Any]] = []
    matched_files: set[str] = set()
    scanned = 0
    skipped = 0

    for path in _iter_candidate_files(scope_path, globs):
        try:
            if path.stat().st_size > max_file_bytes:
                skipped += 1
                continue
            scanned += 1
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            skipped += 1
            continue

        file_match_count = 0
        for line_no, line in enumerate(text.splitlines(), 1):
            if not _line_matches(line, terms, require_all_terms):
                continue
            file_match_count += 1
            matched_files.add(_rel(root, path))
            if len(results) < max_results:
                results.append(
                    {
                        "path": _rel(root, path),
                        "line": line_no,
                        "snippet": _snippet(line),
                        "match_terms": [term for term in terms if term in line.lower()],
                    }
                )
        if len(results) >= max_results and len(matched_files) >= max_results:
            break

    payload = {
        "status": "keyword_search_completed",
        "generated_at": _utc_now(),
        "mode": "real_local_text_keyword_search",
        "keyword": keyword,
        "scope": _rel(root, scope_path),
        "patterns": globs,
        "require_all_terms": require_all_terms,
        "summary": {
            "scanned_file_count": scanned,
            "matched_file_count": len(matched_files),
            "match_count": len(results),
            "skipped_file_count": skipped,
            "max_results": max_results,
            "credential_files_skipped": True,
            "no_synthetic_capture": True,
        },
        "results": results,
        "matched_paths": sorted(matched_files)[:100],
        "source_paths": {
            "state": STATE_PATH.as_posix(),
            "public": PUBLIC_PATH.as_posix(),
        },
    }
    if write_artifact:
        _safe_write_json(_rooted(root, STATE_PATH), payload)
        _safe_write_json(_rooted(root, PUBLIC_PATH), payload)
    return payload


__all__ = ["run_keyword_search"]
