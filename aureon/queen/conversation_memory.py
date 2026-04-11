"""
ConversationMemory — per-peer short-term dialogue memory.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The vault already stores every utterance as a card, but those cards are
Fibonacci-shuffled and don't form a coherent *conversation thread*. When
the Queen answers the phone she needs something much simpler: the last
few turns of the conversation she's having with THIS specific peer, in
order, verbatim, so she can speak naturally instead of reintroducing
herself every message.

This module is that layer. It:

  * Keys conversations by ``peer_id`` — the id every phone gets from
    ``aureon/harmonic/phi_bridge.py``. A single desktop can talk to
    multiple phones in parallel without their threads crossing.
  * Stores the last N turns per peer as ``(role, text, timestamp)``
    tuples where role is "human" or voice name.
  * Auto-expires peers that have been silent for more than the idle TTL
    so stale threads don't leak memory.
  * Is thread-safe (the Flask server hits it from multiple request
    workers + the warm ping thread).
  * Optionally persists threads to ``state/conversation_memory.json`` so
    a server restart doesn't amnesia the Queen.

Usage::

    mem = get_conversation_memory()
    mem.record("peer-abc", "human", "what is your state")
    mem.record("peer-abc", "queen", "tranquil, Λ at -0.15")
    turns = mem.recent("peer-abc", n=6)
    for t in turns:
        print(t.role, ":", t.text)
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("aureon.queen.conversation_memory")


# ─────────────────────────────────────────────────────────────────────────────
# Data types
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class Turn:
    """One line of spoken conversation."""

    role: str            # "human" | voice name ("queen", "lover", …)
    text: str
    timestamp: float = field(default_factory=time.time)
    meta: Dict[str, Any] = field(default_factory=dict)
    # Facts learned during this turn (e.g. by the MeaningResolver: a math
    # result, a Dr Auris snapshot, a research snippet reference). Carried
    # forward so later turns can recall what was computed earlier.
    facts: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "text": self.text,
            "timestamp": self.timestamp,
            "meta": self.meta,
            "facts": self.facts,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Turn":
        return cls(
            role=str(d.get("role", "human")),
            text=str(d.get("text", "")),
            timestamp=float(d.get("timestamp", time.time())),
            meta=dict(d.get("meta", {}) or {}),
            # Version-1 files have no facts field — default to empty.
            facts=dict(d.get("facts", {}) or {}),
        )


@dataclass
class Thread:
    """One peer's conversation thread."""

    peer_id: str
    turns: List[Turn] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_touch: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "peer_id": self.peer_id,
            "created_at": self.created_at,
            "last_touch": self.last_touch,
            "turns": [t.to_dict() for t in self.turns],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Thread":
        return cls(
            peer_id=str(d.get("peer_id", "")),
            created_at=float(d.get("created_at", time.time())),
            last_touch=float(d.get("last_touch", time.time())),
            turns=[Turn.from_dict(t) for t in d.get("turns", []) or []],
        )


# ─────────────────────────────────────────────────────────────────────────────
# ConversationMemory
# ─────────────────────────────────────────────────────────────────────────────


DEFAULT_STATE_PATH = os.path.join("state", "conversation_memory.json")


class ConversationMemory:
    """
    Thread-safe per-peer short-term conversation store.

    Not a long-term memory — the vault already does that via its card
    store. This is the literal dialogue log the Queen needs to sound
    like she's *continuing* a conversation rather than starting fresh
    on every turn.
    """

    def __init__(
        self,
        *,
        max_turns_per_peer: int = 20,
        peer_idle_ttl_s: float = 30 * 60,  # 30 min default
        max_peers: int = 32,
        persist_path: Optional[str] = DEFAULT_STATE_PATH,
        autoload: bool = True,
    ):
        self.max_turns_per_peer = int(max_turns_per_peer)
        self.peer_idle_ttl_s = float(peer_idle_ttl_s)
        self.max_peers = int(max_peers)
        self.persist_path = persist_path
        self._threads: Dict[str, Thread] = {}
        self._lock = threading.RLock()

        if autoload and persist_path:
            try:
                self._load()
            except Exception as e:
                logger.debug("ConversationMemory: autoload failed: %s", e)

    # ─────────────────────────────────────────────────────────────────
    # Core API
    # ─────────────────────────────────────────────────────────────────

    def record(
        self,
        peer_id: str,
        role: str,
        text: str,
        *,
        meta: Optional[Dict[str, Any]] = None,
        facts: Optional[Dict[str, Any]] = None,
    ) -> Turn:
        """Append one turn to the peer's thread."""
        pid = (peer_id or "").strip() or "anon"
        clean_text = (text or "").strip()
        turn = Turn(
            role=str(role or "human"),
            text=clean_text,
            meta=dict(meta or {}),
            facts=dict(facts or {}),
        )
        with self._lock:
            self._sweep_locked()
            thread = self._threads.get(pid)
            if thread is None:
                if len(self._threads) >= self.max_peers:
                    self._evict_oldest_locked()
                thread = Thread(peer_id=pid)
                self._threads[pid] = thread
            thread.turns.append(turn)
            if len(thread.turns) > self.max_turns_per_peer:
                thread.turns = thread.turns[-self.max_turns_per_peer:]
            thread.last_touch = time.time()
            self._persist_locked()
            return turn

    def recent(self, peer_id: str, n: int = 6) -> List[Turn]:
        """Return the last ``n`` turns for this peer, oldest first."""
        pid = (peer_id or "").strip() or "anon"
        with self._lock:
            self._sweep_locked()
            thread = self._threads.get(pid)
            if thread is None:
                return []
            count = max(0, int(n))
            return list(thread.turns[-count:]) if count else []

    def recent_facts(self, peer_id: str, n: int = 6) -> Dict[str, Any]:
        """
        Merged view of the ``facts`` dicts from this peer's last ``n``
        turns. Later turns override earlier turns on key collision.

        Used by the MeaningResolver so the Queen can carry a computed
        math result, a Dr Auris reading, or a research snippet reference
        across multiple turns without having to re-derive it each time.
        """
        turns = self.recent(peer_id, n=n)
        merged: Dict[str, Any] = {}
        for t in turns:
            if not t.facts:
                continue
            for k, v in t.facts.items():
                merged[k] = v
        return merged

    def clear(self, peer_id: str) -> bool:
        pid = (peer_id or "").strip() or "anon"
        with self._lock:
            if pid in self._threads:
                del self._threads[pid]
                self._persist_locked()
                return True
            return False

    def clear_all(self) -> None:
        with self._lock:
            self._threads.clear()
            self._persist_locked()

    def peers(self) -> List[str]:
        with self._lock:
            self._sweep_locked()
            return list(self._threads.keys())

    def summary(self) -> Dict[str, Any]:
        """High-level stats useful for /api/queen/memory."""
        with self._lock:
            self._sweep_locked()
            return {
                "peer_count": len(self._threads),
                "max_turns_per_peer": self.max_turns_per_peer,
                "peer_idle_ttl_s": self.peer_idle_ttl_s,
                "persist_path": self.persist_path,
                "peers": [
                    {
                        "peer_id": pid,
                        "turns": len(t.turns),
                        "created_at": t.created_at,
                        "last_touch": t.last_touch,
                        "age_s": max(0.0, time.time() - t.created_at),
                        "idle_s": max(0.0, time.time() - t.last_touch),
                    }
                    for pid, t in self._threads.items()
                ],
            }

    def format_as_prompt_block(
        self,
        peer_id: str,
        *,
        n: int = 6,
        max_chars_per_turn: int = 240,
    ) -> str:
        """
        Render the last turns as a compact "Recent conversation" block
        the LLM can consume. Empty string if no memory.
        """
        turns = self.recent(peer_id, n=n)
        if not turns:
            return ""
        lines = ["Recent conversation:"]
        for t in turns:
            role_tag = "you" if t.role not in ("human", "user") else "human"
            body = t.text.replace("\n", " ").strip()
            if len(body) > max_chars_per_turn:
                body = body[: max_chars_per_turn - 3].rstrip() + "..."
            lines.append(f"  {role_tag}: {body}")
        return "\n".join(lines)

    # ─────────────────────────────────────────────────────────────────
    # Housekeeping
    # ─────────────────────────────────────────────────────────────────

    def _sweep_locked(self) -> None:
        if self.peer_idle_ttl_s <= 0:
            return
        now = time.time()
        stale = [
            pid for pid, t in self._threads.items()
            if (now - t.last_touch) > self.peer_idle_ttl_s
        ]
        for pid in stale:
            del self._threads[pid]
        if stale:
            self._persist_locked()

    def _evict_oldest_locked(self) -> None:
        if not self._threads:
            return
        oldest_pid = min(self._threads.items(), key=lambda kv: kv[1].last_touch)[0]
        del self._threads[oldest_pid]

    # ─────────────────────────────────────────────────────────────────
    # Persistence
    # ─────────────────────────────────────────────────────────────────

    # On-disk persistence format version.
    #   v1: turns with {role, text, timestamp, meta}
    #   v2: turns additionally carry {facts} (backward-compatible read)
    PERSIST_VERSION = 2

    def _persist_locked(self) -> None:
        if not self.persist_path:
            return
        try:
            os.makedirs(os.path.dirname(self.persist_path) or ".", exist_ok=True)
            payload = {
                "version": self.PERSIST_VERSION,
                "saved_at": time.time(),
                "threads": [t.to_dict() for t in self._threads.values()],
            }
            tmp = self.persist_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            os.replace(tmp, self.persist_path)
        except Exception as e:
            logger.debug("ConversationMemory: persist failed: %s", e)

    def _load(self) -> None:
        if not self.persist_path or not os.path.exists(self.persist_path):
            return
        with open(self.persist_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        threads = payload.get("threads", []) or []
        with self._lock:
            self._threads.clear()
            for t in threads:
                thread = Thread.from_dict(t)
                if thread.peer_id:
                    self._threads[thread.peer_id] = thread


# ─────────────────────────────────────────────────────────────────────────────
# Module-level singleton
# ─────────────────────────────────────────────────────────────────────────────


_memory_singleton: Optional[ConversationMemory] = None
_memory_lock = threading.Lock()


def get_conversation_memory() -> ConversationMemory:
    global _memory_singleton
    with _memory_lock:
        if _memory_singleton is None:
            _memory_singleton = ConversationMemory()
        return _memory_singleton


def reset_conversation_memory() -> None:
    global _memory_singleton
    with _memory_lock:
        _memory_singleton = None


__all__ = [
    "ConversationMemory",
    "Turn",
    "Thread",
    "get_conversation_memory",
    "reset_conversation_memory",
]
