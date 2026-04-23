"""
aureon_code_integrator.py — The organism writes its own source, under review.

When the Code Architect authors a change that targets existing aureon source
(not a new skill in the library, but an edit to a .py file already in the
tree), the change does not land directly. It lands *here*:

  1. PROPOSE    the change. We locate `old_text` inside `target_path`,
                build the would-be resulting file in memory, and run a
                static syntax check (ast.parse + compile) against it.
                A pending record is written to
                    state/integrations_pending/<id>.json
                with the full before-snapshot and the new text.

  2. CONFIRM    the change by id. We take a backup of the current file
                under state/code_integrator_backups/<path>/<ts>.bak,
                write the new content, run one more compile on disk,
                and append an audit line to
                    state/integrations_applied.jsonl
                with the unified diff. If the on-disk compile fails we
                restore from backup and record the failure.

  3. REJECT     the change by id. The pending record is moved to
                    state/integrations_rejected.jsonl. No file is touched.

  4. LIST       pending edits.
  5. HISTORY    recent applied / rejected edits (audit log).

The module never applies a change without an explicit `confirm_edit`
call. It never writes outside the aureon-trading repository root. It
refuses to touch files under `state/` (runtime scratch) or anywhere
outside `aureon/`, `scripts/`, or repo-root `.py` files by default.

Typical flow from outside:
    ci = get_code_integrator()
    prop = ci.propose_edit(
        target_path="aureon/core/aureon_lambda_engine.py",
        old_text="PHI = 1.618",
        new_text="PHI = 1.6180339887498948",
        rationale="tighten constant to 16 digits",
    )
    # inspect prop["before_snapshot"], prop["after_preview"], prop["syntax_ok"]
    ci.confirm_edit(prop["pending_id"])
    # the file is now modified and the change is in state/integrations_applied.jsonl
"""

from __future__ import annotations

import ast
import difflib
import hashlib
import json
import logging
import py_compile
import shutil
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("aureon.core.code_integrator")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_STATE_ROOT = _REPO_ROOT / "state"
_PENDING_DIR = _STATE_ROOT / "integrations_pending"
_APPLIED_LOG = _STATE_ROOT / "integrations_applied.jsonl"
_REJECTED_LOG = _STATE_ROOT / "integrations_rejected.jsonl"
_BACKUP_ROOT = _STATE_ROOT / "code_integrator_backups"

# Paths the integrator is permitted to touch, relative to repo root. These
# are prefixes — `aureon/` covers every module under aureon-trading/aureon/.
_DEFAULT_ALLOWED_PREFIXES: Tuple[str, ...] = (
    "aureon/",
    "scripts/",
)

# Paths the integrator refuses to touch even if an allowed prefix also matches.
_DEFAULT_DENIED_PREFIXES: Tuple[str, ...] = (
    "state/",
    ".git/",
    "__pycache__/",
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _now() -> float:
    return time.time()


def _relpath(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(_REPO_ROOT)).replace("\\", "/")
    except Exception:
        return str(p)


def _resolve_repo_path(target_path: str) -> Path:
    """Resolve `target_path` to an absolute path inside the repo, or raise."""
    candidate = Path(target_path)
    if not candidate.is_absolute():
        candidate = _REPO_ROOT / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(_REPO_ROOT)
    except ValueError:
        raise ValueError(f"path escapes repo root: {target_path}")
    return candidate


def _check_allowed(target_path: str,
                   allowed: Tuple[str, ...],
                   denied: Tuple[str, ...]) -> None:
    rel = target_path.replace("\\", "/").lstrip("./")
    for bad in denied:
        if rel.startswith(bad):
            raise PermissionError(f"path under denied prefix {bad!r}: {rel}")
    # Root-level .py files are permitted even without a prefix match.
    if "/" not in rel and rel.endswith(".py"):
        return
    for good in allowed:
        if rel.startswith(good):
            return
    raise PermissionError(
        f"path {rel!r} is outside allowed prefixes {allowed!r}"
    )


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _unified_diff(before: str, after: str, rel: str) -> str:
    diff = difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=f"a/{rel}",
        tofile=f"b/{rel}",
        n=3,
    )
    return "".join(diff)


# ─────────────────────────────────────────────────────────────────────────────
# Dataclasses
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PendingEdit:
    pending_id: str
    target_path: str           # repo-relative
    rationale: str
    before_text: str
    after_text: str
    before_sha: str
    after_sha: str
    syntax_ok: bool
    syntax_error: str
    proposed_at: float
    match_count: int           # how many times old_text appeared in before_text

    def preview(self, lines: int = 12) -> str:
        diff = _unified_diff(self.before_text, self.after_text, self.target_path)
        snippet = diff.splitlines()[:lines]
        return "\n".join(snippet)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pending_id": self.pending_id,
            "target_path": self.target_path,
            "rationale": self.rationale,
            "before_sha": self.before_sha,
            "after_sha": self.after_sha,
            "syntax_ok": self.syntax_ok,
            "syntax_error": self.syntax_error,
            "proposed_at": self.proposed_at,
            "match_count": self.match_count,
        }


# ─────────────────────────────────────────────────────────────────────────────
# The integrator
# ─────────────────────────────────────────────────────────────────────────────

class CodeIntegrator:
    """
    Holds a pending queue of proposed source edits, syntax-checks them,
    and applies them only on explicit confirm.
    """

    def __init__(
        self,
        allowed_prefixes: Tuple[str, ...] = _DEFAULT_ALLOWED_PREFIXES,
        denied_prefixes: Tuple[str, ...] = _DEFAULT_DENIED_PREFIXES,
    ) -> None:
        self.allowed_prefixes = tuple(allowed_prefixes)
        self.denied_prefixes = tuple(denied_prefixes)
        self._lock = threading.Lock()
        _PENDING_DIR.mkdir(parents=True, exist_ok=True)
        _BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Propose
    # ------------------------------------------------------------------
    def propose_edit(
        self,
        target_path: str,
        old_text: str,
        new_text: str,
        rationale: str = "",
    ) -> Dict[str, Any]:
        """
        Build a pending edit. Does NOT touch the file on disk.

        Returns:
            {
              "ok": bool,
              "pending_id": "...",
              "target_path": "aureon/...",
              "match_count": int,
              "before_sha": "...",
              "after_sha": "...",
              "syntax_ok": bool,
              "syntax_error": str,
              "preview": "<unified diff, trimmed>"
            }
        """
        try:
            _check_allowed(target_path, self.allowed_prefixes, self.denied_prefixes)
            abs_path = _resolve_repo_path(target_path)
        except (PermissionError, ValueError) as e:
            return {"ok": False, "error": str(e)}

        if not abs_path.exists():
            return {"ok": False, "error": f"file not found: {target_path}"}

        try:
            before_text = abs_path.read_text(encoding="utf-8")
        except Exception as e:
            return {"ok": False, "error": f"read failed: {e}"}

        if not old_text:
            return {"ok": False, "error": "old_text cannot be empty"}

        match_count = before_text.count(old_text)
        if match_count == 0:
            return {
                "ok": False,
                "error": "old_text not found in target file",
                "match_count": 0,
            }
        if match_count > 1:
            return {
                "ok": False,
                "error": (
                    f"old_text matches {match_count} times — refusing "
                    "non-unique edit. Widen old_text to include surrounding "
                    "context so the match becomes unique."
                ),
                "match_count": match_count,
            }

        # Build the would-be file.
        after_text = before_text.replace(old_text, new_text, 1)

        # Syntax check the *would-be* content.
        syntax_ok, syntax_err = self._syntax_check(after_text, target_path)

        pending_id = f"pe_{int(_now() * 1000)}_{uuid.uuid4().hex[:8]}"
        pending = PendingEdit(
            pending_id=pending_id,
            target_path=_relpath(abs_path),
            rationale=rationale or "",
            before_text=before_text,
            after_text=after_text,
            before_sha=_sha256(before_text),
            after_sha=_sha256(after_text),
            syntax_ok=syntax_ok,
            syntax_error=syntax_err,
            proposed_at=_now(),
            match_count=match_count,
        )

        with self._lock:
            self._write_pending(pending)

        return {
            "ok": True,
            "pending_id": pending_id,
            "target_path": pending.target_path,
            "match_count": match_count,
            "before_sha": pending.before_sha,
            "after_sha": pending.after_sha,
            "syntax_ok": syntax_ok,
            "syntax_error": syntax_err,
            "preview": pending.preview(lines=24),
        }

    # ------------------------------------------------------------------
    # Confirm / reject
    # ------------------------------------------------------------------
    def confirm_edit(self, pending_id: str) -> Dict[str, Any]:
        """Apply the pending edit after backing up the current file."""
        with self._lock:
            pending = self._load_pending(pending_id)
            if pending is None:
                return {"ok": False, "error": f"no such pending edit: {pending_id}"}

            if not pending.syntax_ok:
                return {
                    "ok": False,
                    "error": "refusing to apply: syntax check failed",
                    "syntax_error": pending.syntax_error,
                }

            try:
                abs_path = _resolve_repo_path(pending.target_path)
            except Exception as e:
                return {"ok": False, "error": f"path resolve: {e}"}

            if not abs_path.exists():
                return {"ok": False, "error": "target file disappeared"}

            # Guard: before_sha must still match current disk contents.
            try:
                current = abs_path.read_text(encoding="utf-8")
            except Exception as e:
                return {"ok": False, "error": f"re-read failed: {e}"}

            if _sha256(current) != pending.before_sha:
                return {
                    "ok": False,
                    "error": (
                        "target file changed since the edit was proposed — "
                        "re-propose against the new file state."
                    ),
                }

            # Backup.
            backup_path = self._backup(abs_path, current)

            # Write and compile.
            try:
                abs_path.write_text(pending.after_text, encoding="utf-8")
            except Exception as e:
                return {"ok": False, "error": f"write failed: {e}"}

            compile_ok, compile_err = self._disk_compile(abs_path)
            if not compile_ok:
                # Roll back.
                try:
                    abs_path.write_text(current, encoding="utf-8")
                except Exception:
                    pass
                return {
                    "ok": False,
                    "error": "applied file failed on-disk compile — rolled back",
                    "compile_error": compile_err,
                    "backup_path": str(backup_path),
                }

            # Audit.
            diff = _unified_diff(pending.before_text, pending.after_text, pending.target_path)
            record = {
                "applied_at": _now(),
                "pending_id": pending.pending_id,
                "target_path": pending.target_path,
                "rationale": pending.rationale,
                "before_sha": pending.before_sha,
                "after_sha": pending.after_sha,
                "backup_path": _relpath(backup_path),
                "diff": diff,
            }
            self._append_log(_APPLIED_LOG, record)
            self._delete_pending(pending_id)

            return {
                "ok": True,
                "applied_at": record["applied_at"],
                "pending_id": pending_id,
                "target_path": pending.target_path,
                "backup_path": _relpath(backup_path),
                "diff": diff,
            }

    def reject_edit(self, pending_id: str, reason: str = "") -> Dict[str, Any]:
        """Discard a pending edit; write a rejection audit line."""
        with self._lock:
            pending = self._load_pending(pending_id)
            if pending is None:
                return {"ok": False, "error": f"no such pending edit: {pending_id}"}

            record = {
                "rejected_at": _now(),
                "pending_id": pending.pending_id,
                "target_path": pending.target_path,
                "rationale": pending.rationale,
                "reason": reason or "",
                "before_sha": pending.before_sha,
                "after_sha": pending.after_sha,
            }
            self._append_log(_REJECTED_LOG, record)
            self._delete_pending(pending_id)
            return {"ok": True, "pending_id": pending_id}

    # ------------------------------------------------------------------
    # Listing / history
    # ------------------------------------------------------------------
    def list_pending(self) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        if not _PENDING_DIR.exists():
            return result
        for p in sorted(_PENDING_DIR.glob("*.json")):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                # Strip bulk text from the listing; caller can fetch full
                # via inspect_pending(id).
                light = {
                    k: v
                    for k, v in data.items()
                    if k not in ("before_text", "after_text")
                }
                result.append(light)
            except Exception:
                continue
        return result

    def inspect_pending(self, pending_id: str) -> Optional[Dict[str, Any]]:
        pending = self._load_pending(pending_id)
        if pending is None:
            return None
        d = pending.to_dict()
        d["preview"] = pending.preview(lines=40)
        return d

    def history(self, limit: int = 20, kind: str = "applied") -> List[Dict[str, Any]]:
        path = _APPLIED_LOG if kind == "applied" else _REJECTED_LOG
        if not path.exists():
            return []
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception:
            return []
        recent = lines[-limit:] if limit > 0 else lines
        out: List[Dict[str, Any]] = []
        for ln in recent:
            ln = ln.strip()
            if not ln:
                continue
            try:
                out.append(json.loads(ln))
            except Exception:
                continue
        return out

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _syntax_check(self, text: str, target_path: str) -> Tuple[bool, str]:
        # We only full-parse .py files; everything else gets a pass.
        if not target_path.endswith(".py"):
            return True, ""
        try:
            ast.parse(text, filename=target_path)
        except SyntaxError as e:
            return False, f"SyntaxError at line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, f"parse failed: {e}"
        return True, ""

    def _disk_compile(self, path: Path) -> Tuple[bool, str]:
        if path.suffix != ".py":
            return True, ""
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as e:
            return False, str(e)
        except Exception as e:
            return False, f"py_compile error: {e}"
        return True, ""

    def _pending_file(self, pending_id: str) -> Path:
        return _PENDING_DIR / f"{pending_id}.json"

    def _write_pending(self, pending: PendingEdit) -> None:
        data = {
            "pending_id": pending.pending_id,
            "target_path": pending.target_path,
            "rationale": pending.rationale,
            "before_text": pending.before_text,
            "after_text": pending.after_text,
            "before_sha": pending.before_sha,
            "after_sha": pending.after_sha,
            "syntax_ok": pending.syntax_ok,
            "syntax_error": pending.syntax_error,
            "proposed_at": pending.proposed_at,
            "match_count": pending.match_count,
        }
        self._pending_file(pending.pending_id).write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )

    def _load_pending(self, pending_id: str) -> Optional[PendingEdit]:
        fp = self._pending_file(pending_id)
        if not fp.exists():
            return None
        try:
            d = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            return None
        return PendingEdit(
            pending_id=d["pending_id"],
            target_path=d["target_path"],
            rationale=d.get("rationale", ""),
            before_text=d["before_text"],
            after_text=d["after_text"],
            before_sha=d["before_sha"],
            after_sha=d["after_sha"],
            syntax_ok=bool(d.get("syntax_ok", False)),
            syntax_error=d.get("syntax_error", ""),
            proposed_at=float(d.get("proposed_at", 0.0)),
            match_count=int(d.get("match_count", 0)),
        )

    def _delete_pending(self, pending_id: str) -> None:
        try:
            self._pending_file(pending_id).unlink(missing_ok=True)
        except Exception:
            pass

    def _backup(self, abs_path: Path, content: str) -> Path:
        ts = time.strftime("%Y%m%d_%H%M%S")
        rel = _relpath(abs_path)
        bk_dir = _BACKUP_ROOT / rel
        bk_dir.mkdir(parents=True, exist_ok=True)
        bk_path = bk_dir / f"{ts}.bak"
        try:
            bk_path.write_text(content, encoding="utf-8")
        except Exception as e:
            logger.warning("backup write failed (%s): %s", bk_path, e)
        return bk_path

    def _append_log(self, path: Path, record: Dict[str, Any]) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, default=str) + "\n")
        except Exception as e:
            logger.warning("log append failed (%s): %s", path, e)


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────

_instance: Optional[CodeIntegrator] = None
_instance_lock = threading.Lock()


def get_code_integrator() -> CodeIntegrator:
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = CodeIntegrator()
        return _instance


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Aureon code integrator CLI.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List pending edits")

    p_hist = sub.add_parser("history", help="Show applied/rejected history")
    p_hist.add_argument("--kind", choices=("applied", "rejected"), default="applied")
    p_hist.add_argument("--limit", type=int, default=10)

    p_show = sub.add_parser("show", help="Show full pending edit with diff preview")
    p_show.add_argument("pending_id")

    p_confirm = sub.add_parser("confirm", help="Confirm a pending edit by id")
    p_confirm.add_argument("pending_id")

    p_reject = sub.add_parser("reject", help="Reject a pending edit by id")
    p_reject.add_argument("pending_id")
    p_reject.add_argument("--reason", default="")

    p_propose = sub.add_parser("propose", help="Propose an edit from file contents on stdin")
    p_propose.add_argument("--target", required=True)
    p_propose.add_argument("--old", required=True, help="Path to a file containing old_text")
    p_propose.add_argument("--new", required=True, help="Path to a file containing new_text")
    p_propose.add_argument("--rationale", default="")

    args = parser.parse_args()
    ci = get_code_integrator()

    if args.cmd == "list":
        print(json.dumps(ci.list_pending(), indent=2, default=str))
    elif args.cmd == "history":
        print(json.dumps(ci.history(limit=args.limit, kind=args.kind), indent=2, default=str))
    elif args.cmd == "show":
        d = ci.inspect_pending(args.pending_id)
        print(json.dumps(d, indent=2, default=str) if d else "not found")
    elif args.cmd == "confirm":
        print(json.dumps(ci.confirm_edit(args.pending_id), indent=2, default=str))
    elif args.cmd == "reject":
        print(json.dumps(ci.reject_edit(args.pending_id, reason=args.reason), indent=2, default=str))
    elif args.cmd == "propose":
        old_text = Path(args.old).read_text(encoding="utf-8")
        new_text = Path(args.new).read_text(encoding="utf-8")
        result = ci.propose_edit(
            target_path=args.target,
            old_text=old_text,
            new_text=new_text,
            rationale=args.rationale,
        )
        print(json.dumps(result, indent=2, default=str))
