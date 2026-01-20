from __future__ import annotations

import base64
import fcntl
import json
import os
import threading
import time
import uuid
from dataclasses import dataclass, asdict, field
from typing import Any, Callable, Deque, Dict, List, Optional
from collections import deque

Json = Dict[str, Any]


def _now() -> float:
    return time.time()


@dataclass
class Thought:
    """
    A unified JSON envelope for *every* internal message.
    This is how different parts of the system "think" and communicate.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    ts: float = field(default_factory=_now)

    source: str = "unknown"
    topic: str = "thought"  # e.g. market.snapshot, miner.signal, risk.approval, execution.order

    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: Optional[str] = None

    payload: Json = field(default_factory=dict)
    meta: Json = field(default_factory=dict)
    payload_encoding: str = "json"
    binary_payload_b64: Optional[str] = None

    def to_json(self) -> Json:
        return asdict(self)


Subscriber = Callable[[Thought], None]


class ThoughtBus:
    def __init__(self, max_memory: int = 5000, persist_path: Optional[str] = None):
        self._lock = threading.RLock()
        self._subs: Dict[str, List[Subscriber]] = {}
        self._memory: Deque[Thought] = deque(maxlen=max_memory)
        self._persist_path = persist_path

        if self._persist_path:
            os.makedirs(os.path.dirname(self._persist_path) or ".", exist_ok=True)
            
        # 🐳 Auto-wire Whale Sonar for every ThoughtBus instance
        # This ensures every subsystem (Queen, Scanner, Feed) has sonar capabilities.
        try:
            from mycelium_whale_sonar import ensure_sonar
            try:
                ensure_sonar(self)
            except Exception:
                # E.g. circular import or missing dependency during startup; proceed anyway.
                pass
        except ImportError:
            # Mycelium sonar module might not be present in all environments
            pass

    def think(self, message: str, topic: str = "thought", priority: str = "normal", metadata: Dict = None) -> Thought:
        """Convenience method to publish a thought"""
        payload = {"message": message, "priority": priority}
        if metadata:
            payload.update(metadata)
            
        thought = Thought(
            source="thought_bus_think",
            topic=topic,
            payload=payload
        )
        return self.publish(thought)

    def subscribe(self, topic: str, handler: Subscriber) -> None:
        """
        topic supports:
          - exact match: "miner.signal"
          - prefix match with "*": "miner.*"
          - global: "*"
        """
        with self._lock:
            self._subs.setdefault(topic, []).append(handler)

    def publish(self, thought: Thought) -> Thought:
        with self._lock:
            self._memory.append(thought)
            self._persist(thought)
            handlers = self._match_handlers(thought.topic)

        for h in handlers:
            try:
                h(thought)
            except Exception as e:
                err = Thought(
                    source="thought_bus",
                    topic="system.error",
                    trace_id=thought.trace_id,
                    parent_id=thought.id,
                    payload={"error": str(e), "while_handling_topic": thought.topic},
                )
                with self._lock:
                    self._memory.append(err)
                    self._persist(err)

        return thought

    def get_recent(self, limit: int = 100) -> List[Json]:
        """Return recent thoughts for monitoring/telemetry use."""
        with self._lock:
            recent = list(self._memory)[-max(1, int(limit)) :]
        return [t.to_json() for t in recent]

    def publish_binary(
        self,
        *,
        source: str,
        topic: str,
        binary_payload: bytes,
        payload: Optional[Json] = None,
        meta: Optional[Json] = None,
    ) -> Thought:
        encoded = base64.b64encode(binary_payload).decode("ascii")
        thought = Thought(
            source=source,
            topic=topic,
            payload=payload or {},
            meta=meta or {},
            payload_encoding="binary",
            binary_payload_b64=encoded,
        )
        return self.publish(thought)

    def recall(self, topic_prefix: Optional[str] = None, limit: int = 100) -> List[Json]:
        with self._lock:
            items = list(self._memory)
        if topic_prefix:
            items = [t for t in items if t.topic.startswith(topic_prefix)]
        return [t.to_json() for t in items[-limit:]]

    def load_history_to_memory(self, jsonl_path: Optional[str] = None, topic_prefix: Optional[str] = None) -> int:
        """Hydrate the in-memory ring buffer from a persisted JSONL log.

        Unlike `replay()`, this does NOT call `publish()` and does NOT re-persist.
        It is safe to use at startup to restore context without triggering handlers
        or creating duplicate log lines.
        """
        path = jsonl_path or self._persist_path
        if not path or not os.path.exists(path):
            return 0

        loaded = 0
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    t = Thought(**data)
                    if topic_prefix and not t.topic.startswith(topic_prefix):
                        continue
                    with self._lock:
                        self._memory.append(t)
                    loaded += 1
        except Exception:
            return loaded

        return loaded

    def replay(self, jsonl_path: Optional[str] = None, topic_prefix: Optional[str] = None) -> int:
        path = jsonl_path or self._persist_path
        if not path or not os.path.exists(path):
            return 0

        count = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                t = Thought(**data)
                if topic_prefix and not t.topic.startswith(topic_prefix):
                    continue
                self.publish(t)
                count += 1
        return count

    def _persist(self, thought: Thought) -> None:
        """Persist thought to JSONL with file locking for crash safety."""
        if not self._persist_path:
            return
        try:
            with open(self._persist_path, "a", encoding="utf-8") as f:
                # Acquire exclusive lock to prevent concurrent writes
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    f.write(json.dumps(thought.to_json(), ensure_ascii=False) + "\n")
                    f.flush()
                    os.fsync(f.fileno())  # Ensure data hits disk
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except (OSError, IOError) as e:
            # Log but don't crash on persistence failure
            pass

    def _match_handlers(self, topic: str) -> List[Subscriber]:
        with self._lock:
            handlers: List[Subscriber] = []
            for key, subs in self._subs.items():
                if key == "*":
                    handlers.extend(subs)
                elif key.endswith("*"):
                    prefix = key[:-1]
                    if topic.startswith(prefix):
                        handlers.extend(subs)
                else:
                    if key == topic:
                        handlers.extend(subs)
            return handlers


# ═══════════════════════════════════════════════════════════════
# GLOBAL SINGLETON & COMPATIBILITY
# ═══════════════════════════════════════════════════════════════

_thought_bus_instance: Optional[ThoughtBus] = None

def get_thought_bus(persist_path: Optional[str] = None) -> ThoughtBus:
    """Get or create the global ThoughtBus instance."""
    global _thought_bus_instance
    if _thought_bus_instance is None:
        _thought_bus_instance = ThoughtBus(
            persist_path=persist_path or "thoughts.jsonl"
        )
    return _thought_bus_instance

# Alias for compatibility - ThoughtSignal is just Thought
ThoughtSignal = Thought
