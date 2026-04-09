"""
AgentPool — Semaphore-Controlled Parallel Agent Execution
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Manages concurrent execution of multiple agents with:
  - Semaphore-based concurrency control
  - runParallel() for batch agent execution
  - Result aggregation and error handling
"""

from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from aureon.inhouse_ai.agent import Agent

logger = logging.getLogger("aureon.inhouse_ai.pool")


@dataclass
class AgentResult:
    """Result from a single agent execution."""

    agent_name: str
    result: str = ""
    error: Optional[str] = None
    duration_s: float = 0.0
    success: bool = True


class AgentPool:
    """
    Semaphore-controlled parallel agent execution pool.

    Manages multiple agents, controls concurrency via a semaphore,
    and provides runParallel() for batch execution.

    Usage:
        pool = AgentPool(max_concurrent=4)
        pool.add(nexus_agent)
        pool.add(omega_agent)
        pool.add(piano_agent)

        results = pool.run_parallel("Analyse the current market state")
    """

    def __init__(self, max_concurrent: int = 4):
        self.max_concurrent = max_concurrent
        self._semaphore = threading.Semaphore(max_concurrent)
        self._agents: Dict[str, Agent] = {}
        self._executor: Optional[ThreadPoolExecutor] = None
        self._results: Dict[str, AgentResult] = {}
        self._lock = threading.Lock()

    def add(self, agent: Agent) -> None:
        """Add an agent to the pool."""
        self._agents[agent.name] = agent
        logger.debug("Agent added to pool: %s", agent.name)

    def remove(self, name: str) -> Optional[Agent]:
        """Remove an agent from the pool."""
        return self._agents.pop(name, None)

    def get(self, name: str) -> Optional[Agent]:
        return self._agents.get(name)

    @property
    def agent_names(self) -> List[str]:
        return list(self._agents.keys())

    @property
    def size(self) -> int:
        return len(self._agents)

    def _run_single(self, agent: Agent, task: str, context: Optional[Dict] = None) -> AgentResult:
        """Run a single agent with semaphore control."""
        start = time.time()
        self._semaphore.acquire()
        try:
            result_text = agent.run(task, context=context)
            duration = time.time() - start
            return AgentResult(
                agent_name=agent.name,
                result=result_text,
                duration_s=duration,
                success=True,
            )
        except Exception as e:
            duration = time.time() - start
            logger.error("Agent %s failed: %s", agent.name, e)
            return AgentResult(
                agent_name=agent.name,
                error=str(e),
                duration_s=duration,
                success=False,
            )
        finally:
            self._semaphore.release()

    def run_parallel(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        agents: Optional[List[str]] = None,
        timeout: float = 120.0,
    ) -> List[AgentResult]:
        """
        Run multiple agents in parallel on the same task.

        Args:
            task: The task/prompt for all agents
            context: Shared context dict
            agents: Specific agent names to run (None = all)
            timeout: Max time to wait for all agents

        Returns:
            List of AgentResult, one per agent.
        """
        target_agents = []
        if agents:
            for name in agents:
                a = self._agents.get(name)
                if a:
                    target_agents.append(a)
                else:
                    logger.warning("Agent '%s' not found in pool", name)
        else:
            target_agents = list(self._agents.values())

        if not target_agents:
            return []

        results: List[AgentResult] = []

        with ThreadPoolExecutor(max_workers=min(len(target_agents), self.max_concurrent)) as executor:
            futures: Dict[Future, str] = {}
            for agent in target_agents:
                future = executor.submit(self._run_single, agent, task, context)
                futures[future] = agent.name

            for future in as_completed(futures, timeout=timeout):
                agent_name = futures[future]
                try:
                    result = future.result(timeout=5)
                    results.append(result)
                except Exception as e:
                    results.append(AgentResult(
                        agent_name=agent_name,
                        error=str(e),
                        success=False,
                    ))

        # Store results
        with self._lock:
            for r in results:
                self._results[r.agent_name] = r

        return results

    def run_sequential(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        agents: Optional[List[str]] = None,
    ) -> List[AgentResult]:
        """Run agents one by one (useful for dependency chains)."""
        target_agents = []
        if agents:
            for name in agents:
                a = self._agents.get(name)
                if a:
                    target_agents.append(a)
        else:
            target_agents = list(self._agents.values())

        results = []
        for agent in target_agents:
            result = self._run_single(agent, task, context)
            results.append(result)
            with self._lock:
                self._results[result.agent_name] = result

        return results

    def get_results(self) -> Dict[str, AgentResult]:
        """Return the last results for all agents."""
        with self._lock:
            return dict(self._results)

    def get_status(self) -> Dict[str, Any]:
        """Return pool status."""
        with self._lock:
            agent_statuses = {}
            for name, agent in self._agents.items():
                agent_statuses[name] = agent.get_status()

            return {
                "pool_size": self.size,
                "max_concurrent": self.max_concurrent,
                "agents": agent_statuses,
                "last_results": {
                    name: {"success": r.success, "duration_s": r.duration_s}
                    for name, r in self._results.items()
                },
            }

    def shutdown(self):
        """Shutdown the pool."""
        for agent in self._agents.values():
            if agent.is_running:
                agent.reset()
        self._agents.clear()
        self._results.clear()
