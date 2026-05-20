from __future__ import annotations

import os
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


SKIP_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    ".cache",
    "cache",
    "dist",
    "build",
    "node_modules",
    "output",
    "venv",
}

DOMAIN_MARKERS = (
    ("accounting", ("account", "accounting", "tax", "hmrc", "companies_house", "company_house", "company", "ledger", "filing", "ct600", "utr", "vat", "cis", "paye", "confirmation", "invoice", "receipt", "petty", "voucher", "evidence", "balance", "statement", "compliance", "payroll")),
    ("thought_bus", ("thought", "bus", "chirp")),
    ("contract_stack", ("contract", "work_order", "queue", "directive", "task", "job")),
    ("trading_decision", ("trade", "trader", "execution", "executor", "kraken_margin")),
    ("market_data", ("feed", "market", "ticker", "websocket", "ws")),
    ("whale_tracking", ("whale", "orca", "moby")),
    ("counter_intel", ("bot", "firm", "counter", "surveillance")),
    ("probability", ("probability", "quantum", "timeline", "nexus", "stargate")),
    ("cognition", ("cogn", "sentien", "conscious", "meta")),
    ("queen", ("queen", "sero", "voice")),
    ("brain", ("brain", "mind", "hive", "neuron")),
    ("autonomous", ("autonomous", "orchestrator", "agent", "control")),
    ("registry", ("registry", "audit", "manifest", "spine")),
)


@dataclass(frozen=True)
class OrganismNode:
    id: str
    name: str
    module: str
    path: str
    domain: str
    organism_topic: str
    sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OrganismManifest:
    generated_at: float
    repo_root: str
    nodes: List[OrganismNode]
    topics: Dict[str, str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "repo_root": self.repo_root,
            "nodes": [node.to_dict() for node in self.nodes],
            "topics": dict(self.topics),
        }

    def by_module(self) -> Dict[str, OrganismNode]:
        return {node.module: node for node in self.nodes}


def _repo_root(start: Optional[Path] = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "aureon").is_dir():
            return candidate
    return Path(__file__).resolve().parents[2]


def _iter_python_files(root: Path) -> Iterable[Path]:
    for scan_root in (root / "aureon", root / "Kings_Accounting_Suite"):
        if not scan_root.exists():
            continue
        for path in scan_root.rglob("*.py"):
            rel_parts = path.resolve().relative_to(root.resolve()).parts
            if any(part in SKIP_PARTS for part in rel_parts):
                continue
            yield path


def _module_from_path(root: Path, path: Path) -> str:
    rel = path.resolve().relative_to(root.resolve()).with_suffix("")
    return ".".join(rel.parts)


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", ".", value.lower()).strip(".")
    return slug or "unknown"


def infer_domain(module: str, path: str = "") -> str:
    haystack = f"{module} {path}".lower()
    for domain, markers in DOMAIN_MARKERS:
        if any(marker in haystack for marker in markers):
            return domain
    parts = module.split(".")
    return parts[1] if len(parts) > 1 else "aureon"


def organism_topic(module: str, domain: Optional[str] = None) -> str:
    resolved_domain = domain or infer_domain(module)
    return f"organism.{_slug(resolved_domain)}.{_slug(module.rsplit('.', 1)[-1])}"


def build_organism_manifest(repo_root: Optional[Path] = None) -> OrganismManifest:
    root = _repo_root(repo_root)
    nodes: Dict[str, OrganismNode] = {}

    for path in _iter_python_files(root):
        module = _module_from_path(root, path)
        rel_path = path.relative_to(root).as_posix()
        domain = infer_domain(module, rel_path)
        nodes[module] = OrganismNode(
            id=_slug(module),
            name=module.rsplit(".", 1)[-1],
            module=module,
            path=rel_path,
            domain=domain,
            organism_topic=organism_topic(module, domain),
            sources=["repo_scan"],
        )

    for system in _registry_systems():
        module = system.get("module", "")
        if not module:
            continue
        if not module.startswith("aureon."):
            # The audit resolver owns short-name to package mapping. The spine
            # still records the declared identity for chain-level visibility.
            declared = module
        else:
            declared = module
        if declared in nodes:
            existing = nodes[declared]
            sources = sorted(set(existing.sources + [f"registry:{system.get('category', 'unknown')}"]))
            nodes[declared] = OrganismNode(
                id=existing.id,
                name=system.get("name") or existing.name,
                module=existing.module,
                path=existing.path,
                domain=system.get("category") or existing.domain,
                organism_topic=organism_topic(existing.module, system.get("category") or existing.domain),
                sources=sources,
            )

    sorted_nodes = sorted(nodes.values(), key=lambda node: (node.domain, node.module))
    return OrganismManifest(
        generated_at=time.time(),
        repo_root=str(root),
        nodes=sorted_nodes,
        topics={node.module: node.organism_topic for node in sorted_nodes},
    )


def _registry_systems() -> List[Dict[str, str]]:
    try:
        from aureon.intelligence.aureon_unified_intelligence_registry import CATEGORIES
    except Exception:
        return []

    systems: List[Dict[str, str]] = []
    for category_key, category in CATEGORIES.items():
        for system in getattr(category, "systems", []):
            systems.append(
                {
                    "category": category_key,
                    "name": getattr(system, "name", ""),
                    "module": getattr(system, "module", ""),
                }
            )
    return systems


def connect_organism(
    bus: Optional[Any] = None,
    repo_root: Optional[Path] = None,
    publish_heartbeat: bool = False,
) -> OrganismManifest:
    """Return the organism manifest and optionally publish a safe heartbeat.

    The heartbeat is opt-in so tests and audits can inspect the organism map
    without waking runtime systems. When enabled, it emits metadata only and
    never places orders or calls exchange clients.
    """

    manifest = build_organism_manifest(repo_root=repo_root)
    if not publish_heartbeat:
        return manifest

    if bus is None:
        from aureon.core.aureon_thought_bus import ThoughtBus

        bus = ThoughtBus(persist_path=None)

    try:
        from aureon.core.aureon_thought_bus import Thought

        bus.publish(
            Thought(
                source="aureon_organism_spine",
                topic="organism.spine.ready",
                payload={
                    "node_count": len(manifest.nodes),
                    "domains": sorted({node.domain for node in manifest.nodes}),
                    "audit_mode": os.getenv("AUREON_AUDIT_MODE", "0"),
                },
            )
        )
    except Exception:
        pass
    return manifest


__all__ = [
    "OrganismManifest",
    "OrganismNode",
    "build_organism_manifest",
    "connect_organism",
    "infer_domain",
    "organism_topic",
]
