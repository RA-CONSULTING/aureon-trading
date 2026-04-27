"""
aureon_self_introspection.py — The organism looks at itself.

Gives the runtime unfettered read-access to its own source tree and decision
surface so the cognitive layer can, at any tick, answer:
  - "what modules am I made of right now?"
  - "what decision points exist in my code?"
  - "what is the current value of that decision point in-process?"
  - "what did I look like the last time I introspected?"

Pure reflection. No mutation here — mutation, if any, is routed through the
goal engine so the organism's own deciders own the choice. This module is
the eyes, not the hands.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import logging
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger("aureon.core.self_introspection")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_AUREON_ROOT = _REPO_ROOT / "aureon"


# ─────────────────────────────────────────────────────────────────────────────
# Data shapes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DecisionPoint:
    """A single decision point detected in the source tree."""
    kind: str              # "env_gate" | "enabled_flag" | "threshold" | "dry_run" | "deadline_mode"
    file: str              # relative path under aureon/
    line: int
    name: str              # variable / env key / class attr
    raw: str               # the source line as written
    current_value: Any = None
    notes: str = ""


@dataclass
class ModuleFingerprint:
    """A snapshot of one source file's identity."""
    path: str              # relative path
    sha256: str
    size: int
    mtime: float
    imports: Tuple[str, ...] = field(default_factory=tuple)
    classes: Tuple[str, ...] = field(default_factory=tuple)
    functions: Tuple[str, ...] = field(default_factory=tuple)


@dataclass
class IntrospectionSnapshot:
    """A single introspection pass."""
    taken_at: float
    modules_total: int
    modules_scanned: int
    decision_points: Tuple[DecisionPoint, ...] = field(default_factory=tuple)
    fingerprints: Tuple[ModuleFingerprint, ...] = field(default_factory=tuple)
    notes: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Core engine
# ─────────────────────────────────────────────────────────────────────────────

class SelfIntrospection:
    """
    The organism's reflective surface.

    Usage:
        intro = SelfIntrospection()
        snap = intro.scan()                 # full pass
        points = intro.find_decision_points("dry_run")
        source = intro.read_own("aureon/core/integrated_cognitive_system.py")
        live = intro.live_value("aureon.core.integrated_cognitive_system", "os")

    Designed to be cheap enough to call every tick but opt-in because a full
    scan walks the whole tree. Use `scan(fast=True)` for the fingerprint-only
    pass (no AST), or `scan_incremental(since_ts)` for modifications only.
    """

    # Patterns we treat as decision points. Conservative — we want signal, not noise.
    _ENV_GATE_HINTS = ("os.getenv", "os.environ.get")
    _ENABLED_HINTS = ("enabled = False", "enabled=False", "enabled = True", "enabled=True")
    _DRY_HINTS = ("dry_run = True", "dry_run=True", "dry_run = False", "dry_run=False")
    _DEADLINE_HINTS = ("DEADLINE_MODE = True", "DEADLINE_MODE = False")

    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = (root or _AUREON_ROOT).resolve()
        self._last_snapshot: Optional[IntrospectionSnapshot] = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # File discovery
    # ------------------------------------------------------------------
    def iter_modules(self) -> Iterable[Path]:
        for p in self.root.rglob("*.py"):
            # Skip __pycache__ and anything clearly not source we own.
            parts = set(p.parts)
            if "__pycache__" in parts:
                continue
            yield p

    def relpath(self, p: Path) -> str:
        try:
            return str(p.relative_to(_REPO_ROOT)).replace("\\", "/")
        except Exception:
            return str(p)

    # ------------------------------------------------------------------
    # Raw source access
    # ------------------------------------------------------------------
    def read_own(self, rel_or_abs: str) -> str:
        """Return the text of a file in the tree. Path may be relative to repo root."""
        p = Path(rel_or_abs)
        if not p.is_absolute():
            p = _REPO_ROOT / p
        return p.read_text(encoding="utf-8", errors="replace")

    def source_of(self, obj: Any) -> str:
        """Return the source of a live Python object via `inspect`."""
        try:
            return inspect.getsource(obj)
        except Exception as e:
            return f"# source unavailable: {e}\n"

    def fingerprint(self, p: Path) -> ModuleFingerprint:
        data = p.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        imports: List[str] = []
        classes: List[str] = []
        functions: List[str] = []
        try:
            tree = ast.parse(data.decode("utf-8", errors="replace"), filename=str(p))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    functions.append(node.name)
        except SyntaxError:
            pass

        try:
            st = p.stat()
            mtime = st.st_mtime
            size = st.st_size
        except Exception:
            mtime = 0.0
            size = len(data)

        return ModuleFingerprint(
            path=self.relpath(p),
            sha256=sha,
            size=size,
            mtime=mtime,
            imports=tuple(sorted(set(imports))),
            classes=tuple(classes),
            functions=tuple(functions),
        )

    # ------------------------------------------------------------------
    # Decision-point extraction
    # ------------------------------------------------------------------
    def extract_decision_points(self, p: Path) -> List[DecisionPoint]:
        """
        Scan one file for decision points. Kept simple and line-oriented so it
        works even when the AST is partially malformed.
        """
        rel = self.relpath(p)
        points: List[DecisionPoint] = []
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return points

        for idx, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # Env-var gates
            for hint in self._ENV_GATE_HINTS:
                if hint in stripped:
                    # Try to pull the env var name
                    name = self._first_string_literal(stripped) or "?"
                    points.append(DecisionPoint(
                        kind="env_gate",
                        file=rel,
                        line=idx,
                        name=name,
                        raw=stripped,
                        current_value=os.environ.get(name) if name != "?" else None,
                    ))
                    break

            # Enabled flags
            for hint in self._ENABLED_HINTS:
                if hint in stripped:
                    points.append(DecisionPoint(
                        kind="enabled_flag",
                        file=rel,
                        line=idx,
                        name="enabled",
                        raw=stripped,
                        current_value="True" in hint,
                    ))
                    break

            # Dry run defaults
            for hint in self._DRY_HINTS:
                if hint in stripped:
                    points.append(DecisionPoint(
                        kind="dry_run",
                        file=rel,
                        line=idx,
                        name="dry_run",
                        raw=stripped,
                        current_value="True" in hint,
                    ))
                    break

            # DEADLINE_MODE constants
            for hint in self._DEADLINE_HINTS:
                if hint in stripped:
                    points.append(DecisionPoint(
                        kind="deadline_mode",
                        file=rel,
                        line=idx,
                        name="DEADLINE_MODE",
                        raw=stripped,
                        current_value="True" in hint,
                    ))
                    break

        return points

    @staticmethod
    def _first_string_literal(line: str) -> Optional[str]:
        for quote in ("'", '"'):
            i = line.find(quote)
            if i < 0:
                continue
            j = line.find(quote, i + 1)
            if j > i:
                return line[i + 1:j]
        return None

    # ------------------------------------------------------------------
    # Live value lookup
    # ------------------------------------------------------------------
    def live_value(self, dotted: str, attr: str) -> Any:
        """
        Read the current in-process value of module.attr without importing
        fresh — returns None if the module is not already loaded, because
        forcing imports at introspection time would have side effects.
        """
        mod = sys.modules.get(dotted)
        if mod is None:
            return None
        return getattr(mod, attr, None)

    def loaded_modules(self, prefix: str = "aureon.") -> Tuple[str, ...]:
        return tuple(sorted(m for m in sys.modules if m.startswith(prefix)))

    # ------------------------------------------------------------------
    # Full pass
    # ------------------------------------------------------------------
    def scan(self, fast: bool = False, limit: Optional[int] = None) -> IntrospectionSnapshot:
        """
        Walk the tree, fingerprint every module, and (unless fast=True) extract
        decision points. Returns a snapshot and caches it as the most recent.
        """
        started = time.time()
        paths = list(self.iter_modules())
        scanned = 0
        fps: List[ModuleFingerprint] = []
        points: List[DecisionPoint] = []

        for p in paths:
            if limit is not None and scanned >= limit:
                break
            try:
                fps.append(self.fingerprint(p))
                if not fast:
                    points.extend(self.extract_decision_points(p))
                scanned += 1
            except Exception as e:
                logger.debug("introspection: skipped %s (%s)", p, e)

        snap = IntrospectionSnapshot(
            taken_at=started,
            modules_total=len(paths),
            modules_scanned=scanned,
            decision_points=tuple(points),
            fingerprints=tuple(fps),
            notes=f"fast={fast}, limit={limit}",
        )
        with self._lock:
            self._last_snapshot = snap
        return snap

    def last_snapshot(self) -> Optional[IntrospectionSnapshot]:
        with self._lock:
            return self._last_snapshot

    def find_decision_points(self, kind_or_name: str) -> Tuple[DecisionPoint, ...]:
        """Filter the last snapshot by kind or name substring."""
        snap = self.last_snapshot()
        if snap is None:
            snap = self.scan()
        q = kind_or_name.lower()
        return tuple(
            dp for dp in snap.decision_points
            if q in dp.kind.lower() or q in dp.name.lower() or q in dp.raw.lower()
        )

    def reachability(
        self,
        entry_points: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        """
        Compute which aureon.* modules are reachable from the given entry
        points via static AST import analysis. Default entry is the ICS
        orchestrator.

        Returns:
            {
              "entry_points":   [...],
              "all_count":      N,      # every aureon.* module on disk
              "reachable_count": R,     # reached via import BFS
              "dormant_count":  D,      # all - reachable
              "reach_ratio":    R/N,
              "dormant_by_package": { "aureon.trading": ..., ... },
              "reachable":      sorted list of reachable dotted names,
              "dormant":        sorted list of dormant dotted names,
            }

        This is the organism's honest answer to "is every file wired to my
        design?" — the dormant list is exactly the work the architect can
        be fed as wire-in edit targets.
        """
        if entry_points is None:
            entry_points = ["aureon.core.integrated_cognitive_system"]
        entries = [str(e) for e in entry_points]

        snap = self.last_snapshot() or self.scan()

        # Map dotted-module-name -> fingerprint, so package dirs (__init__.py)
        # also register as their dotted parent name.
        module_map: Dict[str, ModuleFingerprint] = {}
        for fp in snap.fingerprints:
            p = fp.path
            if not p.startswith("aureon/") or not p.endswith(".py"):
                continue
            name = p[:-3].replace("/", ".")
            if name.endswith(".__init__"):
                name = name[:-len(".__init__")]
            module_map[name] = fp

        all_mods = set(module_map)

        # BFS over aureon.* imports. For each imported name, prefer an exact
        # match; otherwise walk prefixes from longest to shortest to hit the
        # nearest package node we know about.
        reachable: set = set()
        frontier = list(entries)
        while frontier:
            cur = frontier.pop()
            if cur in reachable or cur not in module_map:
                continue
            reachable.add(cur)
            fp = module_map[cur]
            for imp in fp.imports:
                if not isinstance(imp, str) or not imp.startswith("aureon"):
                    continue
                if imp in module_map:
                    if imp not in reachable:
                        frontier.append(imp)
                    continue
                parts = imp.split(".")
                for i in range(len(parts), 0, -1):
                    pref = ".".join(parts[:i])
                    if pref in module_map and pref not in reachable:
                        frontier.append(pref)
                        break

        dormant = all_mods - reachable

        from collections import defaultdict
        by_package: Dict[str, int] = defaultdict(int)
        for m in dormant:
            top = ".".join(m.split(".")[:2])  # aureon.X
            by_package[top] += 1

        return {
            "entry_points": entries,
            "all_count": len(all_mods),
            "reachable_count": len(reachable),
            "dormant_count": len(dormant),
            "reach_ratio": (len(reachable) / len(all_mods)) if all_mods else 0.0,
            "dormant_by_package": dict(sorted(by_package.items(), key=lambda x: -x[1])),
            "reachable": sorted(reachable),
            "dormant": sorted(dormant),
        }

    def summary(self) -> Dict[str, Any]:
        """A compact dict the organism can publish to its ThoughtBus."""
        snap = self.last_snapshot() or self.scan()
        by_kind: Dict[str, int] = {}
        for dp in snap.decision_points:
            by_kind[dp.kind] = by_kind.get(dp.kind, 0) + 1
        return {
            "taken_at": snap.taken_at,
            "modules_total": snap.modules_total,
            "modules_scanned": snap.modules_scanned,
            "decision_points_total": len(snap.decision_points),
            "decision_points_by_kind": by_kind,
            "loaded_aureon_modules": len(self.loaded_modules()),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Singleton convenience
# ─────────────────────────────────────────────────────────────────────────────

_instance: Optional[SelfIntrospection] = None
_instance_lock = threading.Lock()


def get_self_introspection() -> SelfIntrospection:
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = SelfIntrospection()
        return _instance


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    intro = get_self_introspection()
    snap = intro.scan()
    print(f"scanned {snap.modules_scanned}/{snap.modules_total} modules in aureon/")
    print(f"decision points found: {len(snap.decision_points)}")
    from collections import Counter
    kinds = Counter(dp.kind for dp in snap.decision_points)
    for k, n in kinds.most_common():
        print(f"  {k:>15}: {n}")
