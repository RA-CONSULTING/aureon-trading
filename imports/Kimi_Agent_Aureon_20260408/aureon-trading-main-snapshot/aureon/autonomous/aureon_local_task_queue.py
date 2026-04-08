#!/usr/bin/env python3
"""
Local operator task/chat queue for repo exploration and code suggestions.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_STATE_PATH = Path("state/local_task_queue_state.json")


@dataclass
class LocalTask:
    title: str
    message: str = ""
    target_files: List[str] = field(default_factory=list)
    source: str = "operator"
    kind: str = "task"
    created_at: float = field(default_factory=time.time)
    status: str = "queued"


class LocalTaskQueue:
    def __init__(self, state_path: Optional[Path] = None) -> None:
        self.state_path = Path(state_path or DEFAULT_STATE_PATH)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.tasks: List[Dict[str, Any]] = []
        self.recent_completed: List[Dict[str, Any]] = []
        self.max_tasks = 100
        self.max_recent = 25
        self._persist()

    def enqueue(self, task: LocalTask) -> Dict[str, Any]:
        item = asdict(task)
        self.tasks.append(item)
        self.tasks = self.tasks[-self.max_tasks:]
        self._persist()
        return item

    def next_task(self) -> Optional[Dict[str, Any]]:
        for task in self.tasks:
            if task.get("status") == "queued":
                task["status"] = "active"
                self._persist()
                return task
        return None

    def complete_next(self, note: str = "") -> Optional[Dict[str, Any]]:
        for idx, task in enumerate(self.tasks):
            if task.get("status") in {"queued", "active"}:
                task["status"] = "completed"
                task["completed_at"] = time.time()
                task["note"] = note
                self.recent_completed.append(task)
                self.recent_completed = self.recent_completed[-self.max_recent:]
                finished = self.tasks.pop(idx)
                self._persist()
                return finished
        return None

    def status(self) -> Dict[str, Any]:
        queued = [t for t in self.tasks if t.get("status") == "queued"]
        active = [t for t in self.tasks if t.get("status") == "active"]
        return {
            "queued_count": len(queued),
            "active_count": len(active),
            "tasks": self.tasks[-15:],
            "recent_completed": self.recent_completed[-10:],
        }

    def _persist(self) -> None:
        self.state_path.write_text(json.dumps(self.status(), indent=2), encoding="utf-8")


def build_default_task_queue() -> LocalTaskQueue:
    return LocalTaskQueue()


if __name__ == "__main__":
    queue = build_default_task_queue()
    print(json.dumps(queue.status(), indent=2))
