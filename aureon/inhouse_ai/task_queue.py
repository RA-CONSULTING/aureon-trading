"""
TaskQueue — Dependency Graph + Auto Unblock + Cascade Failure
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DAG-based task scheduler for multi-agent workflows:
  - dependency graph : tasks declare which other tasks they depend on
  - auto unblock     : when a dependency completes, blocked tasks are unblocked
  - cascade failure  : when a task fails, all downstream tasks are failed too
"""

from __future__ import annotations

import enum
import logging
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger("aureon.inhouse_ai.taskqueue")


class TaskStatus(enum.Enum):
    PENDING = "pending"
    BLOCKED = "blocked"      # waiting on dependencies
    READY = "ready"          # all deps met, ready to run
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """A unit of work in the task queue."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    agent_name: str = ""           # which agent should handle this
    prompt: str = ""               # the task prompt
    context: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)  # task IDs this depends on
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_s(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


class TaskQueue:
    """
    DAG-based task queue with dependency resolution.

    Usage:
        q = TaskQueue()

        # Add tasks with dependencies
        t1 = q.add("fetch_data", agent_name="DataAgent", prompt="Fetch market data")
        t2 = q.add("analyse", agent_name="NexusAgent", prompt="Analyse data",
                    depends_on=[t1.id])
        t3 = q.add("decide", agent_name="OmegaAgent", prompt="Make decision",
                    depends_on=[t2.id])

        # Process ready tasks
        ready = q.get_ready()  # returns [t1] initially
        q.complete(t1.id, "data fetched")  # auto-unblocks t2
        ready = q.get_ready()  # returns [t2] now
    """

    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._dependents: Dict[str, Set[str]] = defaultdict(set)  # task_id → downstream task_ids
        self._lock = threading.Lock()

    def add(
        self,
        name: str,
        agent_name: str = "",
        prompt: str = "",
        context: Optional[Dict[str, Any]] = None,
        depends_on: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Task:
        """Add a task to the queue."""
        deps = depends_on or []

        # Validate dependencies exist
        with self._lock:
            for dep_id in deps:
                if dep_id not in self._tasks:
                    raise ValueError(f"Dependency task '{dep_id}' not found")

            task = Task(
                name=name,
                agent_name=agent_name,
                prompt=prompt,
                context=context or {},
                depends_on=deps,
                metadata=metadata or {},
            )

            # Set initial status based on dependencies
            if deps:
                all_complete = all(
                    self._tasks[d].status == TaskStatus.COMPLETED for d in deps
                )
                task.status = TaskStatus.READY if all_complete else TaskStatus.BLOCKED
            else:
                task.status = TaskStatus.READY

            self._tasks[task.id] = task

            # Register as dependent of each dependency
            for dep_id in deps:
                self._dependents[dep_id].add(task.id)

            logger.debug("Task added: %s (%s) — status=%s", name, task.id[:8], task.status.value)
            return task

    def get_ready(self) -> List[Task]:
        """Return all tasks that are ready to run."""
        with self._lock:
            return [t for t in self._tasks.values() if t.status == TaskStatus.READY]

    def get_blocked(self) -> List[Task]:
        """Return all blocked tasks."""
        with self._lock:
            return [t for t in self._tasks.values() if t.status == TaskStatus.BLOCKED]

    def start(self, task_id: str):
        """Mark a task as running."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task and task.status == TaskStatus.READY:
                task.status = TaskStatus.RUNNING
                task.started_at = time.time()

    def complete(self, task_id: str, result: str = ""):
        """
        Mark a task as completed. Automatically unblocks downstream tasks.
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return

            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = time.time()

            # Auto-unblock dependents
            self._unblock_dependents(task_id)

    def fail(self, task_id: str, error: str = ""):
        """
        Mark a task as failed. Cascade-fails all downstream tasks.
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return

            task.status = TaskStatus.FAILED
            task.error = error
            task.completed_at = time.time()

            # Cascade failure to all downstream tasks
            self._cascade_failure(task_id, error)

    def cancel(self, task_id: str):
        """Cancel a task and its dependents."""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task or task.status in (TaskStatus.COMPLETED, TaskStatus.RUNNING):
                return

            task.status = TaskStatus.CANCELLED
            task.completed_at = time.time()

            # Cancel dependents too
            for dep_id in self._dependents.get(task_id, set()):
                dep_task = self._tasks.get(dep_id)
                if dep_task and dep_task.status in (TaskStatus.PENDING, TaskStatus.BLOCKED, TaskStatus.READY):
                    dep_task.status = TaskStatus.CANCELLED
                    dep_task.completed_at = time.time()

    def _unblock_dependents(self, completed_id: str):
        """Check if any blocked tasks can now be unblocked (lock must be held)."""
        for dep_id in self._dependents.get(completed_id, set()):
            task = self._tasks.get(dep_id)
            if not task or task.status != TaskStatus.BLOCKED:
                continue

            # Check if ALL dependencies are now complete
            all_complete = all(
                self._tasks[d].status == TaskStatus.COMPLETED
                for d in task.depends_on
                if d in self._tasks
            )
            if all_complete:
                task.status = TaskStatus.READY
                logger.info("Task unblocked: %s (%s)", task.name, task.id[:8])

    def _cascade_failure(self, failed_id: str, error: str):
        """Recursively fail all downstream tasks (lock must be held)."""
        for dep_id in self._dependents.get(failed_id, set()):
            task = self._tasks.get(dep_id)
            if not task or task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                continue

            task.status = TaskStatus.FAILED
            task.error = f"Cascade failure: upstream task '{failed_id[:8]}' failed — {error}"
            task.completed_at = time.time()
            logger.warning("Cascade failure: %s (%s)", task.name, task.id[:8])

            # Continue cascading
            self._cascade_failure(dep_id, error)

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def all_tasks(self) -> List[Task]:
        return list(self._tasks.values())

    def is_complete(self) -> bool:
        """True if all tasks are in a terminal state."""
        return all(
            t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
            for t in self._tasks.values()
        )

    def summary(self) -> Dict[str, int]:
        """Count tasks by status."""
        counts: Dict[str, int] = {}
        for t in self._tasks.values():
            key = t.status.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    def get_status(self) -> Dict[str, Any]:
        """Full queue status."""
        return {
            "total": len(self._tasks),
            "summary": self.summary(),
            "complete": self.is_complete(),
            "tasks": [
                {
                    "id": t.id[:8],
                    "name": t.name,
                    "agent": t.agent_name,
                    "status": t.status.value,
                    "depends_on": [d[:8] for d in t.depends_on],
                    "duration_s": t.duration_s,
                }
                for t in self._tasks.values()
            ],
        }

    def clear(self):
        """Clear all tasks."""
        with self._lock:
            self._tasks.clear()
            self._dependents.clear()

    def __len__(self) -> int:
        return len(self._tasks)
