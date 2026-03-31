#!/usr/bin/env python3
"""
Audit the Aureon Python runtime graph.

This does not try to force every Python file into one execution graph. Instead,
it separates the repo into:
1. core runtime modules used by the live trading spine
2. standalone scripts/tools with no inbound links
3. internal imports that resolve to missing repo modules
"""

from __future__ import annotations

import ast
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "aureon"
FOCUS_DIRS = {
    "analytics",
    "bridges",
    "core",
    "data_feeds",
    "decoders",
    "exchanges",
    "harmonic",
    "intelligence",
    "monitors",
    "portfolio",
    "scanners",
    "strategies",
    "trading",
    "utils",
}
RUNTIME_ROOTS = {
    "aureon.exchanges.unified_market_trader",
    "aureon.exchanges.capital_swarm_runner",
    "aureon.exchanges.kraken_margin_penny_trader",
    "aureon.exchanges.capital_cfd_trader",
    "aureon.exchanges.alpaca_capital_runner",
    "aureon.exchanges.alpaca_capital_style_trader",
}


def iter_focus_files() -> List[Path]:
    files: List[Path] = []
    for path in PACKAGE.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        rel = path.relative_to(PACKAGE)
        if len(rel.parts) < 2:
            continue
        if rel.parts[0] in FOCUS_DIRS:
            files.append(path)
    return files


def module_name(path: Path) -> str:
    return ".".join(path.relative_to(ROOT).with_suffix("").parts)


def resolve_import(current_mod: str, node: ast.ImportFrom) -> str:
    if not node.module:
        return ""
    if node.level and current_mod.startswith("aureon."):
        base = current_mod.split(".")[:-1]
        up = max(0, len(base) - (node.level - 1))
        return ".".join(base[:up] + node.module.split("."))
    return node.module


def nearest_known_module(name: str, known: Set[str]) -> str:
    parts = name.split(".")
    for i in range(len(parts), 1, -1):
        candidate = ".".join(parts[:i])
        if candidate in known:
            return candidate
    return ""


def build_graph(paths: Iterable[Path]) -> Tuple[Dict[str, Set[str]], Counter, Dict[str, Set[str]], List[str], List[str]]:
    known = {module_name(path) for path in paths}
    graph: Dict[str, Set[str]] = defaultdict(set)
    inbound: Counter = Counter()
    missing: Dict[str, Set[str]] = defaultdict(set)
    syntax_errors: List[str] = []
    main_files: List[str] = []

    for path in paths:
        mod = module_name(path)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except Exception as exc:
            syntax_errors.append(f"{path.relative_to(ROOT)} :: {exc}")
            continue

        has_main = False
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                try:
                    expr = ast.unparse(node.test)
                except Exception:
                    expr = ""
                if "__name__" in expr and "__main__" in expr:
                    has_main = True
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if not alias.name.startswith("aureon."):
                        continue
                    target = nearest_known_module(alias.name, known)
                    if target:
                        graph[mod].add(target)
                        inbound[target] += 1
            elif isinstance(node, ast.ImportFrom):
                resolved = resolve_import(mod, node)
                if not resolved.startswith("aureon."):
                    continue
                target = nearest_known_module(resolved, known)
                if target:
                    graph[mod].add(target)
                    inbound[target] += 1
                else:
                    missing[resolved].add(str(path.relative_to(ROOT)))
        if has_main:
            main_files.append(str(path.relative_to(ROOT)))

    return graph, inbound, missing, syntax_errors, main_files


def reachable_from(roots: Iterable[str], graph: Dict[str, Set[str]]) -> Set[str]:
    seen: Set[str] = set()
    stack = [root for root in roots if root in graph or root in RUNTIME_ROOTS]
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        for dep in graph.get(node, set()):
            if dep not in seen:
                stack.append(dep)
    return seen


def main() -> None:
    files = iter_focus_files()
    graph, inbound, missing, syntax_errors, main_files = build_graph(files)
    known = sorted(module_name(path) for path in files)
    reachable = reachable_from(RUNTIME_ROOTS, graph)
    standalone = sorted(mod for mod in known if inbound.get(mod, 0) == 0 and mod not in RUNTIME_ROOTS)

    print(f"FOCUS_MODULES {len(known)}")
    print(f"SYNTAX_ERRORS {len(syntax_errors)}")
    for item in syntax_errors[:20]:
        print(f"SYNTAX {item}")

    print(f"RUNTIME_REACHABLE {len(reachable)}")
    for mod in sorted(reachable)[:80]:
        print(f"REACHABLE {mod}")

    print(f"STANDALONE_FOCUS {len(standalone)}")
    for mod in standalone[:120]:
        print(f"STANDALONE {mod}")

    print(f"MAIN_FILES {len(main_files)}")
    for mod in main_files[:80]:
        print(f"MAIN {mod}")

    print(f"MISSING_INTERNAL {len(missing)}")
    for name, users in sorted(missing.items())[:80]:
        joined = ", ".join(sorted(users)[:4])
        print(f"MISSING {name} USED_BY {joined}")


if __name__ == "__main__":
    main()
