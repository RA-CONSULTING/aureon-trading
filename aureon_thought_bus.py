from __future__ import annotations

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

    def recall(self, topic_prefix: Optional[str] = None, limit: int = 100) -> List[Json]:
        with self._lock:
            items = list(self._memory)
        if topic_prefix:
            items = [t for t in items if t.topic.startswith(topic_prefix)]
        return [t.to_json() for t in items[-limit:]]

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
        if not self._persist_path:
            return
        with open(self._persist_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(thought.to_json(), ensure_ascii=False) + "\n")

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
