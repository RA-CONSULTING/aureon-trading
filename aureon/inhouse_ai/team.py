"""
Team — Agent Group with Shared Infrastructure
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A Team bundles agents with shared coordination infrastructure:
  - AgentConfig[]  : agent definitions
  - MessageBus     : inter-agent messaging (wraps ThoughtBus)
  - TaskQueue      : dependency-aware task scheduling
  - SharedMemory   : key-value store for shared state
"""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from aureon.inhouse_ai.llm_adapter import LLMAdapter
from aureon.inhouse_ai.agent import Agent, AgentConfig
from aureon.inhouse_ai.agent_pool import AgentPool
from aureon.inhouse_ai.task_queue import TaskQueue, Task, TaskStatus
from aureon.inhouse_ai.tool_registry import ToolRegistry

logger = logging.getLogger("aureon.inhouse_ai.team")


# ─────────────────────────────────────────────────────────────────────────────
# MessageBus — inter-agent messaging
# ─────────────────────────────────────────────────────────────────────────────


class MessageBus:
    """
    Inter-agent message bus.  Wraps the ThoughtBus when available,
    falls back to an in-memory pub/sub.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._messages: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

        # Try to wire the ThoughtBus
        self._thought_bus = None
        try:
            from aureon.core.aureon_thought_bus import ThoughtBus
            self._thought_bus = ThoughtBus()
            logger.info("MessageBus wired to ThoughtBus")
        except Exception:
            logger.info("MessageBus using in-memory transport (ThoughtBus not available)")

    def publish(self, topic: str, payload: Dict[str, Any], source: str = "team"):
        """Publish a message to a topic."""
        message = {
            "id": str(uuid.uuid4()),
            "topic": topic,
            "payload": payload,
            "source": source,
            "timestamp": time.time(),
        }

        with self._lock:
            self._messages.append(message)

            # Notify in-memory subscribers
            for sub in self._subscribers.get(topic, []):
                try:
                    sub(message)
                except Exception as e:
                    logger.error("Subscriber error on topic '%s': %s", topic, e)

            # Also publish to ThoughtBus if available
            if self._thought_bus:
                try:
                    from aureon.core.aureon_thought_bus import Thought
                    self._thought_bus.publish(Thought(
                        source=source,
                        topic=f"team.{topic}",
                        payload=payload,
                    ))
                except Exception as e:
                    logger.debug("ThoughtBus publish failed: %s", e)

    def subscribe(self, topic: str, callback: Callable[[Dict[str, Any]], None]):
        """Subscribe to a topic."""
        with self._lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = []
            self._subscribers[topic].append(callback)

    def get_messages(self, topic: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent messages, optionally filtered by topic."""
        with self._lock:
            msgs = self._messages
            if topic:
                msgs = [m for m in msgs if m["topic"] == topic]
            return msgs[-limit:]

    def clear(self):
        with self._lock:
            self._messages.clear()
            self._subscribers.clear()


# ─────────────────────────────────────────────────────────────────────────────
# SharedMemory — key-value store for shared state
# ─────────────────────────────────────────────────────────────────────────────


class SharedMemory:
    """Thread-safe key-value store for sharing state between agents."""

    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._history: List[Dict[str, Any]] = []

    def set(self, key: str, value: Any, source: str = ""):
        with self._lock:
            old = self._store.get(key)
            self._store[key] = value
            self._history.append({
                "action": "set",
                "key": key,
                "old_value": old,
                "new_value": value,
                "source": source,
                "timestamp": time.time(),
            })

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._store.get(key, default)

    def delete(self, key: str):
        with self._lock:
            self._store.pop(key, None)

    def keys(self) -> List[str]:
        with self._lock:
            return list(self._store.keys())

    def snapshot(self) -> Dict[str, Any]:
        """Return a copy of the entire store."""
        with self._lock:
            return dict(self._store)

    def clear(self):
        with self._lock:
            self._store.clear()
            self._history.clear()


# ─────────────────────────────────────────────────────────────────────────────
# Team
# ─────────────────────────────────────────────────────────────────────────────


class Team:
    """
    A group of agents with shared infrastructure.

    Usage:
        adapter = AureonLocalAdapter()
        team = Team(
            name="PillarTeam",
            adapter=adapter,
            agent_configs=[
                AgentConfig(name="Nexus", system_prompt="..."),
                AgentConfig(name="Omega", system_prompt="..."),
            ],
        )

        # Run all agents on same task
        results = team.run_all("Analyse the market")

        # Use the task queue for dependency workflows
        t1 = team.queue.add("fetch", agent_name="Nexus", prompt="Get state")
        t2 = team.queue.add("analyse", agent_name="Omega", prompt="Analyse",
                            depends_on=[t1.id])
        team.run_tasks()
    """

    def __init__(
        self,
        name: str,
        adapter: LLMAdapter,
        agent_configs: Optional[List[AgentConfig]] = None,
        tools: Optional[ToolRegistry] = None,
        max_concurrent: int = 4,
    ):
        self.name = name
        self.id = str(uuid.uuid4())
        self.adapter = adapter
        self.tools = tools or ToolRegistry(include_builtins=True)

        # Infrastructure
        self.bus = MessageBus()
        self.queue = TaskQueue()
        self.memory = SharedMemory()
        self.pool = AgentPool(max_concurrent=max_concurrent)

        # Build agents from configs
        self._configs: List[AgentConfig] = agent_configs or []
        for cfg in self._configs:
            agent = Agent(adapter=self.adapter, config=cfg, tools=self.tools)
            self.pool.add(agent)

    def add_agent(self, config: AgentConfig) -> Agent:
        """Add a new agent to the team."""
        self._configs.append(config)
        agent = Agent(adapter=self.adapter, config=config, tools=self.tools)
        self.pool.add(agent)
        return agent

    def remove_agent(self, name: str):
        """Remove an agent from the team."""
        self._configs = [c for c in self._configs if c.name != name]
        self.pool.remove(name)

    def run_all(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        parallel: bool = True,
    ) -> Dict[str, str]:
        """
        Run all agents on the same task.

        Returns:
            Dict mapping agent_name → result string
        """
        # Share context in memory
        if context:
            self.memory.set("task_context", context, source="team")

        if parallel:
            results = self.pool.run_parallel(task, context=context)
        else:
            results = self.pool.run_sequential(task, context=context)

        # Publish results to bus
        result_map = {}
        for r in results:
            result_map[r.agent_name] = r.result if r.success else f"[ERROR] {r.error}"
            self.bus.publish(
                topic="agent.result",
                payload={
                    "agent": r.agent_name,
                    "success": r.success,
                    "result": r.result[:500] if r.result else None,
                    "error": r.error,
                    "duration_s": r.duration_s,
                },
                source=r.agent_name,
            )

        # Store aggregate in shared memory
        self.memory.set("last_results", result_map, source="team")

        return result_map

    def run_tasks(self) -> Dict[str, Any]:
        """
        Execute all tasks in the queue respecting dependencies.

        Processes the DAG: runs ready tasks, dispatches to the appropriate agent,
        completes/fails tasks, auto-unblocks dependents, cascade-fails on error.
        """
        iteration = 0
        max_iterations = len(self.queue) * 3  # safety limit

        while not self.queue.is_complete() and iteration < max_iterations:
            iteration += 1
            ready = self.queue.get_ready()

            if not ready:
                # Check if there are blocked tasks (possible deadlock)
                blocked = self.queue.get_blocked()
                if blocked:
                    logger.warning("Deadlock detected: %d blocked tasks, 0 ready", len(blocked))
                    break
                break

            # Run ready tasks in parallel
            for task in ready:
                self.queue.start(task.id)

                agent = self.pool.get(task.agent_name)
                if not agent:
                    self.queue.fail(task.id, f"Agent '{task.agent_name}' not found in pool")
                    continue

                try:
                    # Enrich context with shared memory + dependency results
                    enriched_context = dict(task.context)
                    for dep_id in task.depends_on:
                        dep_task = self.queue.get_task(dep_id)
                        if dep_task and dep_task.result:
                            enriched_context[f"dep_{dep_task.name}"] = dep_task.result

                    result = agent.run(task.prompt, context=enriched_context)
                    self.queue.complete(task.id, result)

                    self.bus.publish(
                        topic="task.completed",
                        payload={"task": task.name, "agent": task.agent_name},
                        source=task.agent_name,
                    )
                except Exception as e:
                    self.queue.fail(task.id, str(e))
                    self.bus.publish(
                        topic="task.failed",
                        payload={"task": task.name, "error": str(e)},
                        source=task.agent_name,
                    )

        return self.queue.get_status()

    def get_status(self) -> Dict[str, Any]:
        return {
            "team": self.name,
            "id": self.id[:8],
            "agents": self.pool.agent_names,
            "agent_count": self.pool.size,
            "queue": self.queue.summary(),
            "memory_keys": self.memory.keys(),
            "bus_messages": len(self.bus.get_messages()),
        }

    def shutdown(self):
        """Shutdown the team."""
        self.pool.shutdown()
        self.bus.clear()
        self.memory.clear()
        self.queue.clear()
