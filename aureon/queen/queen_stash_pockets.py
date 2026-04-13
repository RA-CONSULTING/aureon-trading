"""
aureon/queen/queen_stash_pockets.py

Small per-goal scratch pads where agents dump intermediate findings
during the running loop. On close, pockets:
  1. Flush to ElephantMemory as a result event
  2. Crystallize into the KnowledgeDataset
  3. Publish 'stash.pocket.closed' to ThoughtBus

Agents can also retrieve from past stashes for puzzle-piecing.

The math angle protocol (NexusSystem) tags each dump with a phase
angle so dumps can be grouped by phase coherence rather than just
keyword overlap.

This is the user's intent: stop leaning on LLM, give every agent a
small organized pocket, dump-then-retrieve, build a knowledge dataset
that the running loop feeds back into itself.
"""

from __future__ import annotations

import logging
import math
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("aureon.queen.stash_pockets")


# ─────────────────────────────────────────────────────────────────────────────
# StashEntry — one dump
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class StashEntry:
    """One dumped thought / finding from an agent during the running loop."""

    key: str = ""
    value: str = ""
    tags: List[str] = field(default_factory=list)
    phase_angle: float = 0.0    # math angle protocol — radians [0, 2π]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─────────────────────────────────────────────────────────────────────────────
# StashPocket — one per goal
# ─────────────────────────────────────────────────────────────────────────────


class StashPocket:
    """
    A small scratch pad scoped to a single goal. Agents dump intermediate
    thoughts here as they execute. On close, the pocket flushes to elephant
    memory and crystallizes into the knowledge dataset.
    """

    def __init__(self, goal_id: str, owner: str = "agent"):
        self.goal_id = goal_id
        self.owner = owner
        self.pocket_id = uuid.uuid4().hex[:10]
        self.entries: List[StashEntry] = []
        self.opened_at = time.time()
        self.closed_at: Optional[float] = None
        self._lock = threading.Lock()

    def dump(
        self,
        key: str,
        value: str,
        tags: Optional[List[str]] = None,
        phase_angle: Optional[float] = None,
    ) -> StashEntry:
        """
        Dump a thought/finding into this pocket.

        Args:
            key: short identifier (e.g. step_id, intent name)
            value: the dumped text
            tags: optional list of tags (e.g. ["bitcoin", "analysis"])
            phase_angle: optional explicit phase, otherwise computed from text
        """
        if phase_angle is None:
            # Derive phase angle from text using the math angle protocol
            phase_angle = self._text_to_phase(value)

        entry = StashEntry(
            key=key or "",
            value=value or "",
            tags=list(tags or []),
            phase_angle=phase_angle,
        )
        with self._lock:
            self.entries.append(entry)
        return entry

    def retrieve(
        self,
        query: str = "",
        tag: str = "",
    ) -> List[StashEntry]:
        """
        Retrieve entries from THIS pocket only. Used by agents during
        a single goal to look back at what was already dumped.
        """
        with self._lock:
            results = list(self.entries)
        if tag:
            results = [e for e in results if tag in e.tags]
        if query:
            q = query.lower()
            results = [e for e in results if q in e.value.lower() or q in e.key.lower()]
        return results

    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "pocket_id": self.pocket_id,
                "goal_id": self.goal_id,
                "owner": self.owner,
                "opened_at": self.opened_at,
                "closed_at": self.closed_at,
                "entry_count": len(self.entries),
                "entries": [e.to_dict() for e in self.entries],
            }

    @staticmethod
    def _text_to_phase(text: str) -> float:
        """Map text to a phase angle [0, 2π] deterministically."""
        if not text:
            return 0.0
        total = sum(ord(c) for c in text[:200])
        return (total % 1000) / 1000.0 * 2 * math.pi


# ─────────────────────────────────────────────────────────────────────────────
# KnowledgeStashPockets — manager
# ─────────────────────────────────────────────────────────────────────────────


class KnowledgeStashPockets:
    """
    Manager — opens, closes, and indexes pockets across goals.
    Each goal gets its own pocket. On close, content flows to:
      - ElephantMemory (long-term events)
      - KnowledgeDataset (crystallized fragments)
      - ThoughtBus ('stash.pocket.closed' event)
    """

    def __init__(
        self,
        elephant_memory: Any = None,
        knowledge_dataset: Any = None,
        nexus_system: Any = None,
        temporal_knowledge: Any = None,
        thought_bus: Any = None,
    ):
        self._elephant_memory = elephant_memory
        self._knowledge_dataset = knowledge_dataset
        self._nexus_system = nexus_system
        self._temporal_knowledge = temporal_knowledge
        self._thought_bus = thought_bus

        self._open_pockets: Dict[str, StashPocket] = {}
        self._closed_pockets: List[StashPocket] = []
        self._max_closed = 200
        self._lock = threading.RLock()
        self._created_at = time.time()
        self._opened_count = 0
        self._closed_count = 0
        self._fragments_crystallized = 0

    # ─────────────────────────────────────────────────────────────────────
    # Lifecycle
    # ─────────────────────────────────────────────────────────────────────
    def open_pocket(self, goal_id: str, owner: str = "agent") -> StashPocket:
        """Open a new pocket for a goal."""
        pocket = StashPocket(goal_id=goal_id, owner=owner)
        with self._lock:
            self._open_pockets[pocket.pocket_id] = pocket
            self._opened_count += 1

        if self._thought_bus is not None:
            try:
                self._thought_bus.publish(
                    "stash.pocket.opened",
                    {
                        "pocket_id": pocket.pocket_id,
                        "goal_id": goal_id,
                        "owner": owner,
                    },
                    source="stash_pockets",
                )
            except Exception:
                pass
        return pocket

    def close_pocket(self, pocket: StashPocket) -> Dict[str, Any]:
        """
        Close a pocket and flush its contents:
          1. ElephantMemory.remember_result(pocket.to_dict())
          2. KnowledgeDataset.absorb(pocket)
          3. Publish 'stash.pocket.closed' to ThoughtBus
        """
        pocket.closed_at = time.time()
        result: Dict[str, Any] = {
            "pocket_id": pocket.pocket_id,
            "goal_id": pocket.goal_id,
            "entries": len(pocket.entries),
            "duration_s": pocket.closed_at - pocket.opened_at,
            "fragments_crystallized": 0,
        }

        # 1. Flush to elephant memory
        if self._elephant_memory is not None:
            try:
                self._elephant_memory.remember_result(
                    payload={
                        "kind": "stash_pocket_close",
                        "pocket_id": pocket.pocket_id,
                        "goal_id": pocket.goal_id,
                        "entry_count": len(pocket.entries),
                        "preview": [
                            (e.key, e.value[:80])
                            for e in pocket.entries[:5]
                        ],
                    },
                    source="stash_pockets",
                )
            except Exception as exc:
                logger.debug("ElephantMemory flush failed: %s", exc)

        # 2. Crystallize into knowledge dataset
        if self._knowledge_dataset is not None:
            try:
                added = self._knowledge_dataset.absorb(pocket)
                result["fragments_crystallized"] = added
                self._fragments_crystallized += added
            except Exception as exc:
                logger.debug("KnowledgeDataset absorb failed: %s", exc)

        # 3. Publish to ThoughtBus
        if self._thought_bus is not None:
            try:
                self._thought_bus.publish(
                    "stash.pocket.closed",
                    {
                        "pocket_id": pocket.pocket_id,
                        "goal_id": pocket.goal_id,
                        "entries": len(pocket.entries),
                        "fragments": result["fragments_crystallized"],
                    },
                    source="stash_pockets",
                )
            except Exception:
                pass

        # 4. Move to closed list (bounded)
        with self._lock:
            self._open_pockets.pop(pocket.pocket_id, None)
            self._closed_pockets.append(pocket)
            while len(self._closed_pockets) > self._max_closed:
                self._closed_pockets.pop(0)
            self._closed_count += 1

        return result

    # ─────────────────────────────────────────────────────────────────────
    # Cross-pocket retrieval
    # ─────────────────────────────────────────────────────────────────────
    def query_all(
        self,
        query: str = "",
        tag: str = "",
        n: int = 10,
    ) -> List[StashEntry]:
        """
        Search across ALL pockets (open and recently-closed) for entries.
        Used by agents to piece together puzzles from past dumps.
        """
        results: List[StashEntry] = []
        with self._lock:
            all_pockets = list(self._open_pockets.values()) + list(self._closed_pockets)
        for pocket in all_pockets:
            results.extend(pocket.retrieve(query=query, tag=tag))
            if len(results) >= n * 2:
                break
        return results[:n]

    def get_pocket(self, pocket_id: str) -> Optional[StashPocket]:
        with self._lock:
            return self._open_pockets.get(pocket_id)

    # ─────────────────────────────────────────────────────────────────────
    # Status
    # ─────────────────────────────────────────────────────────────────────
    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "open_pockets": len(self._open_pockets),
                "closed_pockets": len(self._closed_pockets),
                "total_opened": self._opened_count,
                "total_closed": self._closed_count,
                "fragments_crystallized": self._fragments_crystallized,
                "uptime_s": round(time.time() - self._created_at, 1),
            }


# ─────────────────────────────────────────────────────────────────────────────
# Singleton accessor
# ─────────────────────────────────────────────────────────────────────────────

_singleton: Optional[KnowledgeStashPockets] = None
_singleton_lock = threading.Lock()


def get_stash_pockets(**kwargs) -> KnowledgeStashPockets:
    global _singleton
    with _singleton_lock:
        if _singleton is None:
            _singleton = KnowledgeStashPockets(**kwargs)
        return _singleton


def reset_stash_pockets() -> None:
    global _singleton
    with _singleton_lock:
        _singleton = None
