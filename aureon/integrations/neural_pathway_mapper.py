"""
NeuralPathwayMapper — The System Maps Its Own Internal Wiring
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"The internal system builds its own neural pathways based on its
current architecture."

This mapper treats the `aureon/` package tree as the system's own
nervous system. It walks every `.py` file, parses the imports with the
stdlib `ast` module, and produces a directed graph:

    node   = module dotted path (e.g. 'aureon.vault.voice.self_dialogue')
    edge   = "this module imports that other aureon module"
    cluster = top-level domain (vault, queen, harmonic, inhouse_ai, ...)

The resulting `PathwayGraph` is then written into
`AureonVault.pathway_graph` (which already exists as an empty dict on
the vault but was never populated) so the cognitive loops have a live
map of the system's own architecture they can reason over.

Three personas use this:

  • Queen   — checks how many domains are reachable from her slice
  • Miner   — looks for orphaned nodes (imported by nobody)
  • Architect — looks at pathway density to decide what to refactor

The mapper runs deterministically, needs no external deps beyond the
Python stdlib, and is safe to call on every self-feedback tick (the
graph is cached until the source files change on disk).
"""

from __future__ import annotations

import ast
import hashlib
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("aureon.integrations.pathway")

REPO_ROOT = Path(__file__).resolve().parents[2]
AUREON_ROOT = REPO_ROOT / "aureon"


# ─────────────────────────────────────────────────────────────────────────────
# Data types
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class PathwayGraph:
    """Directed graph of aureon.* module imports."""

    nodes: Set[str] = field(default_factory=set)
    edges: Dict[str, Set[str]] = field(default_factory=dict)
    clusters: Dict[str, Set[str]] = field(default_factory=dict)
    built_at: float = 0.0
    source_hash: str = ""

    def add_node(self, mod: str) -> None:
        self.nodes.add(mod)
        cluster = mod.split(".")[1] if mod.startswith("aureon.") else "unknown"
        self.clusters.setdefault(cluster, set()).add(mod)
        self.edges.setdefault(mod, set())

    def add_edge(self, src: str, dst: str) -> None:
        self.add_node(src)
        self.add_node(dst)
        self.edges[src].add(dst)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": sorted(self.nodes),
            "edges": {k: sorted(v) for k, v in self.edges.items() if v},
            "clusters": {k: sorted(v) for k, v in self.clusters.items()},
            "built_at": self.built_at,
            "source_hash": self.source_hash,
            "stats": self.stats(),
        }

    def stats(self) -> Dict[str, Any]:
        fan_in: Dict[str, int] = {n: 0 for n in self.nodes}
        fan_out: Dict[str, int] = {n: len(v) for n, v in self.edges.items()}
        for src, dsts in self.edges.items():
            for dst in dsts:
                fan_in[dst] = fan_in.get(dst, 0) + 1

        total_edges = sum(len(v) for v in self.edges.values())
        orphans = [n for n in self.nodes if fan_in.get(n, 0) == 0]
        most_referenced = sorted(
            fan_in.items(), key=lambda kv: kv[1], reverse=True
        )[:10]
        most_importing = sorted(
            fan_out.items(), key=lambda kv: kv[1], reverse=True
        )[:10]
        return {
            "node_count": len(self.nodes),
            "edge_count": total_edges,
            "cluster_count": len(self.clusters),
            "orphan_count": len(orphans),
            "avg_fan_out": (
                total_edges / max(len(self.nodes), 1)
            ),
            "most_referenced": most_referenced,
            "most_importing": most_importing,
            "cluster_sizes": {
                k: len(v) for k, v in self.clusters.items()
            },
        }

    def neighbors(self, mod: str, depth: int = 1) -> Set[str]:
        """Walk outgoing edges up to `depth` hops."""
        seen: Set[str] = {mod}
        frontier = {mod}
        for _ in range(max(0, depth)):
            new_frontier: Set[str] = set()
            for n in frontier:
                for dst in self.edges.get(n, ()):
                    if dst not in seen:
                        new_frontier.add(dst)
                        seen.add(dst)
            frontier = new_frontier
            if not frontier:
                break
        seen.discard(mod)
        return seen


# ─────────────────────────────────────────────────────────────────────────────
# NeuralPathwayMapper
# ─────────────────────────────────────────────────────────────────────────────


class NeuralPathwayMapper:
    """
    Walks `aureon/` and builds a module-level dependency graph via
    `ast.parse(...)`. Caches the result so self-feedback ticks are cheap.
    """

    def __init__(
        self,
        root: Optional[Path] = None,
        exclude_clusters: Optional[List[str]] = None,
    ):
        self.root = Path(root or AUREON_ROOT)
        self.exclude_clusters = set(exclude_clusters or [])
        self._cached_graph: Optional[PathwayGraph] = None

    # ─────────────────────────────────────────────────────────────────────
    # Build
    # ─────────────────────────────────────────────────────────────────────

    def build_graph(
        self,
        max_modules: Optional[int] = None,
        force: bool = False,
    ) -> PathwayGraph:
        """
        Parse every `.py` file under `aureon/` and return a PathwayGraph.
        Caches by content hash so repeat calls are free until files change.
        """
        source_hash = self._hash_sources(max_modules=max_modules)
        if (
            not force
            and self._cached_graph is not None
            and self._cached_graph.source_hash == source_hash
        ):
            return self._cached_graph

        graph = PathwayGraph(source_hash=source_hash, built_at=time.time())
        count = 0
        for py_file in self._iter_py_files():
            if max_modules is not None and count >= max_modules:
                break
            mod = self._path_to_module(py_file)
            if mod is None:
                continue
            cluster = mod.split(".")[1] if mod.startswith("aureon.") else "_root_"
            if cluster in self.exclude_clusters:
                continue
            graph.add_node(mod)
            try:
                text = py_file.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(text, filename=str(py_file))
            except (SyntaxError, UnicodeDecodeError, OSError) as e:
                logger.debug("pathway parse skipped %s: %s", py_file, e)
                count += 1
                continue

            for imported in self._extract_aureon_imports(tree, current_module=mod):
                graph.add_edge(mod, imported)
            count += 1

        self._cached_graph = graph
        return graph

    # ─────────────────────────────────────────────────────────────────────
    # Vault wiring — writes the graph into vault.pathway_graph
    # ─────────────────────────────────────────────────────────────────────

    def write_to_vault(self, vault: Any, max_modules: Optional[int] = None) -> Dict[str, Any]:
        """
        Build the graph and mirror it into `vault.pathway_graph` (which
        the AureonVault already declares as an empty dict). Returns the
        stats dict so callers can log/announce.
        """
        graph = self.build_graph(max_modules=max_modules)
        try:
            vault.pathway_graph = {
                src: sorted(dsts) for src, dsts in graph.edges.items() if dsts
            }
        except Exception as e:
            logger.debug("write_to_vault failed: %s", e)
        try:
            vault.ingest(
                topic="pathway.graph.built",
                payload={
                    "nodes": len(graph.nodes),
                    "edges": sum(len(v) for v in graph.edges.values()),
                    "clusters": sorted(graph.clusters.keys()),
                    "source_hash": graph.source_hash,
                    "built_at": graph.built_at,
                },
                category="pathway_graph",
            )
        except Exception:
            pass
        return graph.stats()

    # ─────────────────────────────────────────────────────────────────────
    # Internals
    # ─────────────────────────────────────────────────────────────────────

    def _iter_py_files(self) -> List[Path]:
        """Yield every `.py` file under `aureon/` in a stable order."""
        if not self.root.is_dir():
            return []
        files: List[Path] = []
        for dirpath, dirnames, filenames in os.walk(self.root):
            # Skip the usual noise
            dirnames[:] = [
                d for d in dirnames
                if d not in ("__pycache__", ".git", "node_modules", ".pytest_cache")
            ]
            for name in filenames:
                if not name.endswith(".py"):
                    continue
                files.append(Path(dirpath) / name)
        files.sort()
        return files

    def _path_to_module(self, py_file: Path) -> Optional[str]:
        """Convert a .py path to its dotted 'aureon.*' module name."""
        try:
            rel = py_file.relative_to(self.root.parent)
        except ValueError:
            return None
        parts = list(rel.with_suffix("").parts)
        if not parts or parts[0] != "aureon":
            return None
        if parts[-1] == "__init__":
            parts = parts[:-1]
        return ".".join(parts)

    def _hash_sources(self, max_modules: Optional[int] = None) -> str:
        """Hash file paths + mtimes so the cache invalidates on change."""
        h = hashlib.sha256()
        count = 0
        for f in self._iter_py_files():
            if max_modules is not None and count >= max_modules:
                break
            try:
                stat = f.stat()
                h.update(str(f).encode("utf-8"))
                h.update(str(int(stat.st_mtime)).encode("utf-8"))
                h.update(str(stat.st_size).encode("utf-8"))
            except OSError:
                pass
            count += 1
        return h.hexdigest()[:16]

    def _extract_aureon_imports(
        self,
        tree: ast.AST,
        current_module: str,
    ) -> Set[str]:
        """Pull every 'aureon.*' target out of the AST."""
        out: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("aureon"):
                        out.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    # Relative import — resolve against current_module
                    base = current_module.split(".")
                    if node.level > len(base):
                        continue
                    base = base[: -node.level] if node.level > 0 else base
                    parts = list(base)
                    if node.module:
                        parts.append(node.module)
                    target = ".".join(parts)
                    if target.startswith("aureon"):
                        out.add(target)
                elif node.module and node.module.startswith("aureon"):
                    out.add(node.module)
        out.discard(current_module)
        return out


# ─────────────────────────────────────────────────────────────────────────────
# One-shot convenience
# ─────────────────────────────────────────────────────────────────────────────


def build_pathway_graph(
    max_modules: Optional[int] = None,
    exclude_clusters: Optional[List[str]] = None,
) -> PathwayGraph:
    """Top-level helper — build a fresh graph in one call."""
    mapper = NeuralPathwayMapper(exclude_clusters=exclude_clusters)
    return mapper.build_graph(max_modules=max_modules)
