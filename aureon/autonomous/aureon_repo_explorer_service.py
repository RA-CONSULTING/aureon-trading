#!/usr/bin/env python3
"""
Local repo explorer service for safe codebase inspection.
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[2]
TEXT_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".txt", ".yml", ".yaml", ".toml", ".ini", ".css", ".html"
}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}


class RepoExplorerService:
    def __init__(self, repo_root: Optional[Path] = None) -> None:
        self.repo_root = Path(repo_root or DEFAULT_REPO_ROOT)

    def list_files(self, limit: int = 200) -> List[str]:
        files: List[str] = []
        for root, dirs, filenames in os.walk(self.repo_root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for filename in filenames:
                path = Path(root) / filename
                try:
                    files.append(str(path.relative_to(self.repo_root)))
                except Exception:
                    continue
                if len(files) >= limit:
                    return files
        return files

    def find_files(self, pattern: str, limit: int = 100) -> List[str]:
        rx = re.compile(pattern, re.IGNORECASE)
        results: List[str] = []
        for rel in self.list_files(limit=5000):
            if rx.search(rel):
                results.append(rel)
                if len(results) >= limit:
                    break
        return results

    def search_text(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        q = query.lower()
        hits: List[Dict[str, Any]] = []
        for rel in self.list_files(limit=5000):
            path = self.repo_root / rel
            if path.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for idx, line in enumerate(text.splitlines(), start=1):
                if q in line.lower():
                    hits.append({"path": rel, "line": idx, "text": line.strip()[:300]})
                    if len(hits) >= limit:
                        return hits
        return hits

    def inspect_file(self, rel_path: str, max_lines: int = 200) -> Dict[str, Any]:
        path = self.repo_root / rel_path
        if not path.exists():
            return {"ok": False, "error": "file_not_found", "path": rel_path}
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            return {"ok": False, "error": str(e), "path": rel_path}
        lines = text.splitlines()
        return {
            "ok": True,
            "path": rel_path,
            "size": path.stat().st_size,
            "line_count": len(lines),
            "preview": lines[:max_lines],
            "modified_at": path.stat().st_mtime,
        }

    def suggest_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        tasks: List[Dict[str, Any]] = []
        todo_hits = self.search_text("TODO", limit=limit)
        for hit in todo_hits:
            tasks.append({
                "title": f"Review TODO in {hit['path']}",
                "summary": hit["text"],
                "target_files": [hit["path"]],
                "source": "repo_explorer.todo",
                "created_at": time.time(),
            })
        if len(tasks) < limit:
            fixme_hits = self.search_text("FIXME", limit=limit - len(tasks))
            for hit in fixme_hits:
                tasks.append({
                    "title": f"Review FIXME in {hit['path']}",
                    "summary": hit["text"],
                    "target_files": [hit["path"]],
                    "source": "repo_explorer.fixme",
                    "created_at": time.time(),
                })
        return tasks[:limit]


def build_default_repo_explorer() -> RepoExplorerService:
    return RepoExplorerService()


if __name__ == "__main__":
    explorer = build_default_repo_explorer()
    print({"files": explorer.list_files(limit=20)})
