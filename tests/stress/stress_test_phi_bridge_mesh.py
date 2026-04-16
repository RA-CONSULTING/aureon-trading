#!/usr/bin/env python3
"""
Stress test for the φ-bridge P2P mesh, PersonaVacuum collapse, and the
Obsidian adapter. Not a pytest — a standalone script that prints metrics
and exits non-zero on any assertion failure.

Four dimensions:

  1. Mesh convergence on a 20-node sparse random graph (3 peers per node)
     with 20 unique cards per node. Gossip until full convergence or 200
     cycles. Measures: cycles to convergence, cards exchanged, wall time,
     final hash-set size per node.

  2. Thread-safety — 8 worker threads pounding gossip_once on one mesh
     against a pool of 12 peer handlers. Measures: thrown exceptions,
     final convergence, wall time.

  3. PersonaVacuum throughput — 20,000 observe() cycles over a stub bus
     with a stub vault. Measures: collapses/sec, winner distribution.

  4. Obsidian adapter scale — 500 markdown notes in a temp dir, sync_in
     twice (second pass must skip every file). Measures: wall time,
     dedup correctness.

Run:
    python tests/stress/stress_test_phi_bridge_mesh.py
"""

from __future__ import annotations

import os
import random
import shutil
import sys
import tempfile
import threading
import time
import tracemalloc
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.harmonic.phi_bridge_mesh import PhiBridgeMesh  # noqa: E402
from aureon.vault.aureon_vault import AureonVault, VaultContent  # noqa: E402
from aureon.vault.obsidian_adapter import ObsidianVaultAdapter  # noqa: E402
from aureon.vault.voice.aureon_personas import build_aureon_personas  # noqa: E402
from aureon.vault.voice.persona_vacuum import PersonaVacuum  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# Printing helpers
# ─────────────────────────────────────────────────────────────────────────────


GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def banner(title: str) -> None:
    bar = "━" * 76
    print(f"\n{CYAN}{bar}\n{title}\n{bar}{RESET}")


def ok(msg: str) -> None:
    print(f"  {GREEN}[PASS]{RESET} {msg}")


def fail(msg: str) -> None:
    print(f"  {RED}[FAIL]{RESET} {msg}")


def info(msg: str) -> None:
    print(f"  {YELLOW}[INFO]{RESET} {msg}")


# ─────────────────────────────────────────────────────────────────────────────
# Shared doubles
# ─────────────────────────────────────────────────────────────────────────────


class _StubPeer:
    def __init__(self, peer_id: str, url_base: str):
        self.peer_id = peer_id
        self.url_base = url_base


class _StubDiscovery:
    def __init__(self, peer_id: str, peers: List[_StubPeer]):
        self.peer_id = peer_id
        self._peers = peers

    def known_peers(self) -> List[_StubPeer]:
        return list(self._peers)

    def set_peers(self, peers: List[_StubPeer]) -> None:
        self._peers = list(peers)


class _RoutedClient:
    """In-memory HTTP: routes POST url → PhiBridgeMesh.handle_inbound."""

    def __init__(self):
        self.routes: Dict[str, PhiBridgeMesh] = {}
        self.posts = 0
        self.failures = 0
        self._lock = threading.Lock()

    def mount(self, url_base: str, mesh: PhiBridgeMesh) -> None:
        self.routes[url_base] = mesh

    def post_json(self, url: str, body: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            self.posts += 1
        base = url.rsplit("/api/", 1)[0]
        mesh = self.routes.get(base)
        if mesh is None:
            with self._lock:
                self.failures += 1
            raise ConnectionError(f"no route for {url}")
        return mesh.handle_inbound(body)


def _card(owner: str, idx: int) -> VaultContent:
    return VaultContent.build(
        category="stress.card",
        source_topic=f"stress.{owner}",
        payload={"owner": owner, "idx": idx, "data": f"payload-{owner}-{idx}"},
    )


def _hashes(vault: AureonVault) -> set:
    return {c.harmonic_hash for c in vault._contents.values()}


# ─────────────────────────────────────────────────────────────────────────────
# 1. Mesh convergence on a sparse random graph
# ─────────────────────────────────────────────────────────────────────────────


def stress_mesh_convergence(
    n_nodes: int = 20,
    cards_per_node: int = 20,
    peers_per_node: int = 3,
    max_cycles: int = 200,
    seed: int = 7,
) -> bool:
    banner(f"[1] Mesh convergence  N={n_nodes} nodes  {cards_per_node} cards each  "
           f"{peers_per_node} peers each")

    rng = random.Random(seed)
    vaults: List[AureonVault] = []
    meshes: List[PhiBridgeMesh] = []
    client = _RoutedClient()
    stubs: List[_StubPeer] = []

    for i in range(n_nodes):
        v = AureonVault()
        for j in range(cards_per_node):
            v.add(_card(f"n{i}", j))
        vaults.append(v)
        url_base = f"http://node-{i}:80"
        stub = _StubPeer(f"n{i}", url_base)
        stubs.append(stub)

    for i in range(n_nodes):
        # Pick peers_per_node random other nodes as this node's peers.
        others = [j for j in range(n_nodes) if j != i]
        rng.shuffle(others)
        my_peers = [stubs[j] for j in others[:peers_per_node]]
        mesh = PhiBridgeMesh(
            vault=vaults[i],
            discovery=_StubDiscovery(f"n{i}", my_peers),
            client=client,
        )
        meshes.append(mesh)
        client.mount(stubs[i].url_base, mesh)

    all_hashes: set = set()
    for v in vaults:
        all_hashes.update(_hashes(v))
    target = len(all_hashes)
    info(f"total unique cards across mesh: {target}")

    tracemalloc.start()
    t0 = time.perf_counter()

    converged = False
    cycles = 0
    for cycle in range(max_cycles):
        cycles += 1
        for mesh in meshes:
            mesh.gossip_once()
        sizes = [len(_hashes(v)) for v in vaults]
        if all(s == target for s in sizes):
            converged = True
            break

    dt = time.perf_counter() - t0
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    sizes = [len(_hashes(v)) for v in vaults]
    info(f"cycles run:            {cycles}")
    info(f"wall time:             {dt*1000:.1f} ms")
    info(f"posts issued:          {client.posts}")
    info(f"client failures:       {client.failures}")
    info(f"peak python memory:    {peak_mem/1024:.1f} KB")
    info(f"final hash-count min/avg/max: {min(sizes)}/{sum(sizes)/len(sizes):.1f}/{max(sizes)}")

    if not converged:
        fail(f"did NOT converge after {cycles} cycles — "
             f"min={min(sizes)} target={target}")
        return False

    # Sanity: every vault must actually hold the same hash set.
    ref = _hashes(vaults[0])
    all_equal = all(_hashes(v) == ref for v in vaults)
    if not all_equal:
        fail("convergence size reached but hash sets differ between nodes")
        return False
    ok(f"all {n_nodes} vaults converged to identical {target}-card hash set in {cycles} cycles")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# 2. Thread safety — concurrent gossip_once on one mesh node
# ─────────────────────────────────────────────────────────────────────────────


def stress_thread_safety(
    n_peers: int = 12,
    n_threads: int = 8,
    rounds_per_thread: int = 400,
    cards_per_peer: int = 5,
    seed: int = 11,
) -> bool:
    banner(f"[2] Thread safety  {n_threads} threads × {rounds_per_thread} gossip rounds  "
           f"vs {n_peers} peers")

    rng = random.Random(seed)
    client = _RoutedClient()
    peer_vaults: List[AureonVault] = []
    peer_stubs: List[_StubPeer] = []

    for i in range(n_peers):
        v = AureonVault()
        for j in range(cards_per_peer):
            v.add(_card(f"peer{i}", j))
        peer_vaults.append(v)
        stub = _StubPeer(f"peer{i}", f"http://peer-{i}:80")
        peer_stubs.append(stub)
        mesh = PhiBridgeMesh(
            vault=v,
            discovery=_StubDiscovery(f"peer{i}", []),
            client=client,
        )
        client.mount(stub.url_base, mesh)

    central_vault = AureonVault()
    central_mesh = PhiBridgeMesh(
        vault=central_vault,
        discovery=_StubDiscovery("central", peer_stubs),
        client=client,
    )

    errors: List[Exception] = []
    error_lock = threading.Lock()

    def worker(tid: int) -> None:
        local_rng = random.Random(seed + tid)
        try:
            for _ in range(rounds_per_thread):
                # Bias towards gossip_once, occasional direct gossip_to
                if local_rng.random() < 0.2:
                    central_mesh.gossip_to(local_rng.choice(peer_stubs))
                else:
                    central_mesh.gossip_once()
        except Exception as e:
            with error_lock:
                errors.append(e)

    t0 = time.perf_counter()
    threads = [threading.Thread(target=worker, args=(i,), daemon=True) for i in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    dt = time.perf_counter() - t0

    info(f"threads:         {n_threads}")
    info(f"total rounds:    {n_threads * rounds_per_thread}")
    info(f"wall time:       {dt*1000:.1f} ms")
    info(f"posts issued:    {client.posts}")
    info(f"client failures: {client.failures}")
    info(f"central vault size: {len(central_vault)}")

    if errors:
        fail(f"{len(errors)} thread errors: {errors[0]!r}")
        return False

    # Every peer's cards should now be in the central vault.
    expected_hashes: set = set()
    for v in peer_vaults:
        expected_hashes.update(_hashes(v))
    central_hashes = _hashes(central_vault)
    missing = expected_hashes - central_hashes
    if missing:
        fail(f"central vault missing {len(missing)} peer cards after concurrent gossip")
        return False

    # Vault integrity: len() must equal _contents size — no torn inserts.
    if len(central_vault) != len(central_vault._contents):
        fail(f"vault length mismatch: len={len(central_vault)} _contents={len(central_vault._contents)}")
        return False

    ok(f"no thread errors; vault integrity intact; all {len(expected_hashes)} peer hashes present")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# 3. PersonaVacuum throughput
# ─────────────────────────────────────────────────────────────────────────────


class _StubAdapter:
    def prompt(self, messages, system, max_tokens):
        class _R:
            text = "s"
            model = "stub"
            usage = {"total_tokens": 1}
        return _R()


class _SilentBus:
    def publish(self, *a, **kw): return None
    def subscribe(self, *a, **kw): return None


def stress_persona_throughput(n: int = 20_000, seed: int = 13) -> bool:
    banner(f"[3] PersonaVacuum throughput  {n:,} observe() cycles")

    rng = random.Random(seed)
    personas = build_aureon_personas(adapter=_StubAdapter())
    vacuum = PersonaVacuum(
        personas=personas,
        thought_bus=_SilentBus(),
        rng=random.Random(seed),
        temperature=1.0,
    )

    class _V:
        def __init__(self):
            self.love_amplitude = 0.5
            self.gratitude_score = 0.5
            self.last_casimir_force = 0.0
            self.last_lambda_t = 0.0
            self.dominant_chakra = "heart"
            self.dominant_frequency_hz = 528.0
            self.rally_active = False
            self.cortex_snapshot = {"delta": 0.2, "theta": 0.2, "alpha": 0.2, "beta": 0.2, "gamma": 0.2}

        def fingerprint(self):
            return ""

        def __len__(self):
            return 10

    vault = _V()
    winners: Counter = Counter()
    errors: List[Exception] = []

    t0 = time.perf_counter()
    for i in range(n):
        # Randomly tweak state every ~64 calls so affinities shift around
        if i % 64 == 0:
            vault.love_amplitude = rng.random()
            vault.gratitude_score = rng.random()
            vault.last_lambda_t = (rng.random() - 0.5) * 2
            vault.dominant_frequency_hz = rng.choice([174, 285, 396, 528, 639, 741, 852, 963])
            vault.rally_active = rng.random() < 0.2
        try:
            vacuum.observe(vault)
            winners[vacuum.last_winner] += 1
        except Exception as e:
            errors.append(e)
            if len(errors) > 3:
                break
    dt = time.perf_counter() - t0

    rate = n / max(dt, 1e-9)
    info(f"wall time:       {dt*1000:.1f} ms")
    info(f"throughput:      {rate:,.0f} observe/sec")
    info(f"collapse count:  {vacuum.collapse_count}")
    info(f"distinct winners: {len(winners)}")
    for name, count in winners.most_common():
        pct = 100 * count / max(1, sum(winners.values()))
        print(f"        {name:<20s} {count:6d}  ({pct:4.1f}%)")

    if errors:
        fail(f"{len(errors)} errors, first: {errors[0]!r}")
        return False
    if len(winners) < 5:
        fail(f"only {len(winners)} distinct winners in {n} observations — distribution too narrow")
        return False
    ok("throughput stable, no errors, broad winner distribution")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# 4. Obsidian adapter scale
# ─────────────────────────────────────────────────────────────────────────────


def stress_obsidian_scale(n_notes: int = 500) -> bool:
    banner(f"[4] Obsidian adapter  {n_notes} notes")

    tmpdir = Path(tempfile.mkdtemp(prefix="aureon_stress_obsidian_"))
    try:
        # Write N notes, half with frontmatter
        for i in range(n_notes):
            path = tmpdir / f"note_{i:04d}.md"
            if i % 2 == 0:
                body = f"# note {i}\n\nThis is stress note {i}.\nLine 2.\n"
                path.write_text(body, encoding="utf-8")
            else:
                fm = f"---\ntitle: stress note {i}\ntags: [stress, n{i}]\n---\nbody {i}\n"
                path.write_text(fm, encoding="utf-8")

        vault = AureonVault()
        adapter = ObsidianVaultAdapter(vault=vault, obsidian_root=tmpdir)

        t0 = time.perf_counter()
        n1 = adapter.sync_in()
        t1 = time.perf_counter()
        n2 = adapter.sync_in()
        t2 = time.perf_counter()

        info(f"first sync_in ingested:  {n1}")
        info(f"first sync wall time:    {(t1-t0)*1000:.1f} ms  ({n_notes/(t1-t0):,.0f} notes/sec)")
        info(f"second sync_in ingested: {n2}  (should be 0 — dedup)")
        info(f"second sync wall time:   {(t2-t1)*1000:.1f} ms")
        info(f"vault card count:        {len(vault)}")

        if n1 != n_notes:
            fail(f"first sync ingested {n1} / {n_notes}")
            return False
        if n2 != 0:
            fail(f"second sync ingested {n2} — dedup broken")
            return False
        if len(vault) != n_notes:
            fail(f"vault ended with {len(vault)} cards, expected {n_notes}")
            return False
        ok("500-file ingest + dedup clean")
        return True
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────


def main() -> int:
    results: Dict[str, bool] = {}
    results["mesh_convergence"] = stress_mesh_convergence()
    results["thread_safety"] = stress_thread_safety()
    results["persona_throughput"] = stress_persona_throughput()
    results["obsidian_scale"] = stress_obsidian_scale()

    banner("Summary")
    for name, passed in results.items():
        (ok if passed else fail)(f"{name}: {'PASS' if passed else 'FAIL'}")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
