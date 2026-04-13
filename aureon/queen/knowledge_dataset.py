"""
aureon/queen/knowledge_dataset.py

KnowledgeDataset — crystallizes stash pocket dumps into a tag-indexed,
phase-coherent knowledge base.

Architecture:
    Goal A → stash pocket → dumps → KnowledgeFragments → indexed
    Goal B → planning → relevant_for_goal(text) → retrieves A's fragments
    Subsequent goals build on prior knowledge instead of starting fresh.

The dataset is persisted to state/knowledge_dataset.json so accumulated
learning survives across ICS restarts. Coherence between fragments is
scored using the math angle protocol (NexusSystem) — NOT an LLM.

This is how the system learns from itself.
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
import threading
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("aureon.queen.knowledge_dataset")


# ─────────────────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class KnowledgeFragment:
    """One crystallized piece of knowledge from a stash pocket dump."""

    text: str
    tags: List[str] = field(default_factory=list)
    source_goal: str = ""
    source_owner: str = ""
    phase_angle: float = 0.0       # math angle protocol — radians [0, 2π]
    coherence_score: float = 0.5   # [0, 1] — alignment with the dataset
    timestamp: float = field(default_factory=time.time)
    times_retrieved: int = 0       # popularity counter

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeFragment":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ─────────────────────────────────────────────────────────────────────────────
# Tokeniser — light, no NLP libraries
# ─────────────────────────────────────────────────────────────────────────────


_STOPWORDS = frozenset(
    "a an the and or but if then so to of in on at by for from with into about "
    "is are was were be been being have has had do does did i you it we they "
    "this that these those my your our their".split()
)


def _tokenize(text: str) -> List[str]:
    """Lowercase word tokens with stopwords removed."""
    if not text:
        return []
    words = re.findall(r"[a-zA-Z]{3,}", text.lower())
    return [w for w in words if w not in _STOPWORDS]


def _keyword_overlap(a: List[str], b: List[str]) -> float:
    """Jaccard similarity over token sets."""
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _text_to_phase_angle(text: str) -> float:
    """
    Map a text string to a phase angle in [0, 2π] using a deterministic hash.
    The math angle protocol uses these phases for coherence scoring.
    Same content → same phase. Similar content → similar phase (modulo hash).
    """
    if not text:
        return 0.0
    # Use sum of token char codes mod 2π for a simple deterministic mapping
    tokens = _tokenize(text)
    if not tokens:
        return 0.0
    total = sum(sum(ord(c) for c in t) for t in tokens)
    return (total % 1000) / 1000.0 * 2 * math.pi


# ─────────────────────────────────────────────────────────────────────────────
# KnowledgeDataset
# ─────────────────────────────────────────────────────────────────────────────


class KnowledgeDataset:
    """
    Tag-indexed, phase-coherent knowledge base that persists across sessions.
    Crystallizes stash pocket dumps into queryable fragments.

    No LLM dependency. Uses keyword overlap + tag matching + math-angle phase
    coherence (via NexusSystem) for scoring.
    """

    def __init__(
        self,
        nexus_system: Any = None,
        path: Optional[str] = None,
        max_fragments: int = 2000,
    ):
        self._fragments: List[KnowledgeFragment] = []
        self._tag_index: Dict[str, List[int]] = defaultdict(list)
        self._lock = threading.RLock()
        self._max_fragments = max_fragments
        self._nexus = nexus_system

        # Persistence path
        if path is None:
            repo_root = Path(__file__).resolve().parents[2]
            self._path = repo_root / "state" / "knowledge_dataset.json"
        else:
            self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

        self._created_at = time.time()
        self._absorb_count = 0
        self._retrieve_count = 0
        self._load()

    # ─────────────────────────────────────────────────────────────────────
    # Persistence
    # ─────────────────────────────────────────────────────────────────────
    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            for frag_dict in data.get("fragments", []):
                frag = KnowledgeFragment.from_dict(frag_dict)
                self._fragments.append(frag)
                idx = len(self._fragments) - 1
                for tag in frag.tags:
                    self._tag_index[tag].append(idx)
            logger.info("KnowledgeDataset: loaded %d fragments from %s",
                         len(self._fragments), self._path)
        except Exception as exc:
            logger.warning("KnowledgeDataset load failed: %s", exc)

    def save(self) -> None:
        """Atomic JSON write — knowledge survives restart."""
        try:
            with self._lock:
                data = {
                    "fragments": [f.to_dict() for f in self._fragments],
                    "saved_at": time.time(),
                    "version": 1,
                }
            tmp = self._path.with_suffix(self._path.suffix + ".tmp")
            tmp.write_text(json.dumps(data), encoding="utf-8")
            os.replace(tmp, self._path)
        except Exception as exc:
            logger.debug("KnowledgeDataset save failed: %s", exc)

    # ─────────────────────────────────────────────────────────────────────
    # Coherence scoring (math angle protocol)
    # ─────────────────────────────────────────────────────────────────────
    def _coherence_with_dataset(self, phase: float) -> float:
        """
        Score how aligned a new fragment's phase is with existing fragments.
        Uses the math angle protocol: complex phase sum normalised.
        Returns a value in [0, 1].
        """
        if not self._fragments:
            return 0.5  # neutral
        # Take a sample of recent fragment phases
        sample = self._fragments[-50:]
        try:
            import cmath
            phases = [f.phase_angle for f in sample] + [phase]
            complex_sum = sum(cmath.exp(1j * p) for p in phases)
            coherence = abs(complex_sum) / len(phases)
            return max(0.0, min(1.0, coherence))
        except Exception:
            return 0.5

    # ─────────────────────────────────────────────────────────────────────
    # Absorption — crystallize a stash pocket into fragments
    # ─────────────────────────────────────────────────────────────────────
    def absorb(self, pocket: Any) -> int:
        """
        Crystallize all entries in a stash pocket into KnowledgeFragments.
        Returns the number of fragments added.
        """
        added = 0
        try:
            entries = getattr(pocket, "entries", [])
            goal_id = getattr(pocket, "goal_id", "")
            owner = getattr(pocket, "owner", "")

            with self._lock:
                for entry in entries:
                    text = getattr(entry, "value", "") or ""
                    tags = list(getattr(entry, "tags", []) or [])
                    phase = getattr(entry, "phase_angle", 0.0)

                    # Skip empty dumps
                    if not text or not text.strip():
                        continue

                    # Compute coherence with existing dataset
                    coherence = self._coherence_with_dataset(phase)

                    fragment = KnowledgeFragment(
                        text=text[:1000],  # cap fragment length
                        tags=tags,
                        source_goal=goal_id,
                        source_owner=owner,
                        phase_angle=phase,
                        coherence_score=coherence,
                        timestamp=getattr(entry, "timestamp", time.time()),
                    )
                    self._fragments.append(fragment)
                    idx = len(self._fragments) - 1
                    for tag in tags:
                        self._tag_index[tag].append(idx)
                    added += 1

                # Evict oldest if over cap
                while len(self._fragments) > self._max_fragments:
                    evicted = self._fragments.pop(0)
                    # Rebuild tag index lazily — only necessary if eviction happens
                    self._tag_index.clear()
                    for i, frag in enumerate(self._fragments):
                        for tag in frag.tags:
                            self._tag_index[tag].append(i)
                    break  # only loop once after rebuild

            self._absorb_count += 1
            if added > 0:
                self.save()
        except Exception as exc:
            logger.debug("KnowledgeDataset absorb failed: %s", exc)
        return added

    # ─────────────────────────────────────────────────────────────────────
    # Query API
    # ─────────────────────────────────────────────────────────────────────
    def find_by_tag(self, tag: str, n: int = 5) -> List[KnowledgeFragment]:
        with self._lock:
            indices = self._tag_index.get(tag, [])
            results = [self._fragments[i] for i in indices[-n:] if i < len(self._fragments)]
            for r in results:
                r.times_retrieved += 1
            self._retrieve_count += 1
            return results

    def find_similar(self, text: str, n: int = 5) -> List[KnowledgeFragment]:
        """Keyword overlap + tag scoring. No LLM."""
        query_tokens = _tokenize(text)
        if not query_tokens:
            return []
        with self._lock:
            scored: List[Tuple[float, KnowledgeFragment]] = []
            for frag in self._fragments:
                frag_tokens = _tokenize(frag.text)
                score = _keyword_overlap(query_tokens, frag_tokens)
                # Tag bonus
                tag_overlap = sum(1 for t in frag.tags if t.lower() in text.lower())
                score += 0.1 * tag_overlap
                if score > 0:
                    scored.append((score, frag))
            scored.sort(key=lambda x: -x[0])
            results = [f for _, f in scored[:n]]
            for r in results:
                r.times_retrieved += 1
            self._retrieve_count += 1
            return results

    def find_by_phase(
        self,
        target_angle: float,
        tolerance: float = 0.5,
        n: int = 5,
    ) -> List[KnowledgeFragment]:
        """Phase-locked retrieval (math angle protocol)."""
        with self._lock:
            scored: List[Tuple[float, KnowledgeFragment]] = []
            for frag in self._fragments:
                # Wrap phase difference to [0, π]
                diff = abs(frag.phase_angle - target_angle)
                if diff > math.pi:
                    diff = 2 * math.pi - diff
                if diff <= tolerance:
                    scored.append((diff, frag))
            scored.sort(key=lambda x: x[0])
            results = [f for _, f in scored[:n]]
            for r in results:
                r.times_retrieved += 1
            self._retrieve_count += 1
            return results

    def relevant_for_goal(
        self,
        goal_text: str,
        n: int = 5,
    ) -> List[KnowledgeFragment]:
        """
        Used by the goal engine BEFORE running a goal — retrieves prior
        knowledge that might help piece together the puzzle.
        Combines keyword similarity + phase coherence.
        """
        # Phase-locked + keyword-similar combined search
        target_phase = _text_to_phase_angle(goal_text)
        keyword_hits = self.find_similar(goal_text, n=n * 2)
        phase_hits = self.find_by_phase(target_phase, tolerance=0.8, n=n * 2)

        # Merge and dedupe
        seen_ids = set()
        results: List[KnowledgeFragment] = []
        for frag in keyword_hits + phase_hits:
            fid = id(frag)
            if fid in seen_ids:
                continue
            seen_ids.add(fid)
            results.append(frag)
            if len(results) >= n:
                break
        return results

    # ─────────────────────────────────────────────────────────────────────
    # Status
    # ─────────────────────────────────────────────────────────────────────
    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "fragments": len(self._fragments),
                "unique_tags": len(self._tag_index),
                "absorptions": self._absorb_count,
                "retrievals": self._retrieve_count,
                "uptime_s": round(time.time() - self._created_at, 1),
                "path": str(self._path),
                "max_fragments": self._max_fragments,
            }


# ─────────────────────────────────────────────────────────────────────────────
# Singleton accessor
# ─────────────────────────────────────────────────────────────────────────────

_singleton: Optional[KnowledgeDataset] = None
_singleton_lock = threading.Lock()


def get_knowledge_dataset(nexus_system: Any = None) -> KnowledgeDataset:
    global _singleton
    with _singleton_lock:
        if _singleton is None:
            _singleton = KnowledgeDataset(nexus_system=nexus_system)
        return _singleton


def reset_knowledge_dataset() -> None:
    global _singleton
    with _singleton_lock:
        _singleton = None
