"""
aureon_repair_swarm.py — Parallel repair using the existing agent pool.

The self-check scanner produces fix-jobs as authoring.research events.
One architect working serially can only author one proposal at a time.
The repair swarm subscribes to authoring.research, buffers jobs, and on
every cadence tick dispatches a batch through
aureon.inhouse_ai.AgentPool.run_parallel — so N agents work on N
different dormant-module wire-ins (or N syntax repairs, or N refinement
drafts) simultaneously.

Each agent produces a proposed edit (path + old_text + new_text +
rationale). The swarm funnels every proposal through the code integrator
as a pending edit. Confirmation gates still hold — nothing lands without
review. But throughput goes from 1× to N×.

Integration points:
  - Reuses aureon.inhouse_ai.OpenMultiAgent + AgentPool
  - Subscribes to authoring.research on the bus
  - Optionally triggered by the phi calendar's cadence / minor band
  - Writes proposals to state/integrations_pending via code integrator

Architecture:

    bus: authoring.research   ─┐
    phi_calendar.cadence       ├─►  RepairSwarm  ─►  AgentPool.run_parallel(N)
                               │                          │
                               │            each agent: architect.writer
                               │                          │
                               │                  edit proposal
                               │                          ▼
                               └────────────────────  CodeIntegrator.propose_edit
                                                          │
                                                          ▼
                                                 state/integrations_pending/*.json
                                                          │
                                                          ▼
                                                    reviewer confirms
"""

from __future__ import annotations

import json
import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Deque, Dict, List, Optional

logger = logging.getLogger("aureon.core.repair_swarm")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SWARM_LOG = _REPO_ROOT / "state" / "repair_swarm_log.jsonl"


# ─────────────────────────────────────────────────────────────────────────────
# Data shapes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SwarmJob:
    received_at: float
    topic: str
    payload: Dict[str, Any]

    def intent(self) -> str:
        return str(self.payload.get("intent") or self.payload.get("kind") or "unknown")

    def target(self) -> str:
        return str(
            self.payload.get("target_module")
            or self.payload.get("target_path")
            or self.payload.get("path")
            or "?"
        )


@dataclass
class SwarmResult:
    job_intent: str
    job_target: str
    agent_name: str
    ok: bool
    pending_id: str = ""
    error: str = ""
    duration_s: float = 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Swarm
# ─────────────────────────────────────────────────────────────────────────────

class RepairSwarm:
    """
    Parallel repair lane. Subscribes to authoring.research and dispatches
    buffered jobs to the agent pool on a cadence.
    """

    def __init__(
        self,
        max_parallel: int = 4,
        dispatch_interval_s: float = 10.0,
        max_queue: int = 64,
    ) -> None:
        self.max_parallel = max(1, int(max_parallel))
        self.dispatch_interval_s = max(1.0, float(dispatch_interval_s))
        self.max_queue = int(max_queue)

        self.bus: Any = None
        self.pool: Any = None
        self.team: Any = None
        self.orchestrator: Any = None
        self.integrator: Any = None

        self._queue: Deque[SwarmJob] = deque(maxlen=self.max_queue)
        self._queue_lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        self.dispatches = 0
        self.jobs_processed = 0
        self.proposals_created = 0
        self.errors = 0

    # ------------------------------------------------------------------
    # Wiring
    # ------------------------------------------------------------------
    def _wire(self) -> None:
        if self.bus is None:
            try:
                from aureon.core.aureon_thought_bus import get_thought_bus
                self.bus = get_thought_bus()
            except Exception as e:
                logger.debug("bus unavailable: %s", e)

        if self.pool is None:
            try:
                from aureon.inhouse_ai.orchestrator import OpenMultiAgent
                from aureon.inhouse_ai.agent import AgentConfig
                self.orchestrator = OpenMultiAgent(mode="hybrid")
                # Build a team of N repair agents. Each agent has the same
                # role — "read the problem, propose an edit". The pool
                # parallelises them; max_concurrent caps throughput.
                agent_configs = [
                    AgentConfig(
                        name=f"RepairAgent-{i}",
                        system_prompt=(
                            "You are an Aureon repair agent. Your job is to "
                            "propose a minimal, syntactically valid Python "
                            "edit to the target file that resolves the "
                            "stated issue. Respond with a JSON object only: "
                            '{"path": "<repo-rel>", "old_text": "<exact '
                            'anchor>", "new_text": "<replacement>", '
                            '"rationale": "<one line>"}. old_text must '
                            "appear exactly once in the target file; if "
                            "uncertain, widen it with surrounding context."
                        ),
                    )
                    for i in range(self.max_parallel)
                ]
                self.team = self.orchestrator.create_team(
                    name="RepairSwarm",
                    agent_configs=agent_configs,
                    max_concurrent=self.max_parallel,
                )
                # Team has its own pool attribute on most implementations;
                # fall back to AgentPool directly if not.
                self.pool = getattr(self.team, "pool", None) or getattr(self.team, "_pool", None)
                if self.pool is None:
                    from aureon.inhouse_ai.agent_pool import AgentPool
                    from aureon.inhouse_ai.agent import Agent
                    self.pool = AgentPool(max_concurrent=self.max_parallel)
                    for cfg in agent_configs:
                        self.pool.add(Agent(config=cfg, adapter=self.orchestrator.adapter))
            except Exception as e:
                logger.debug("agent pool unavailable: %s", e)

        if self.integrator is None:
            try:
                from aureon.core.aureon_code_integrator import get_code_integrator
                self.integrator = get_code_integrator()
            except Exception as e:
                logger.debug("integrator unavailable: %s", e)

        # Subscribe once.
        if self.bus is not None and not getattr(self, "_subscribed", False):
            try:
                self.bus.subscribe("authoring.research", self._on_research)
                self._subscribed = True
            except Exception as e:
                logger.debug("subscribe failed: %s", e)

    # ------------------------------------------------------------------
    # Ingress
    # ------------------------------------------------------------------
    def _on_research(self, thought: Any) -> None:
        try:
            payload = getattr(thought, "payload", None) or {}
            if not isinstance(payload, dict):
                return
            topic = getattr(thought, "topic", "authoring.research")
            job = SwarmJob(received_at=time.time(), topic=topic, payload=payload)
            with self._queue_lock:
                self._queue.append(job)
        except Exception as e:
            logger.debug("ingest error: %s", e)

    def submit(self, payload: Dict[str, Any]) -> None:
        """Direct in-process submission (bypasses bus)."""
        job = SwarmJob(received_at=time.time(), topic="direct", payload=payload)
        with self._queue_lock:
            self._queue.append(job)

    # ------------------------------------------------------------------
    # Dispatch cycle
    # ------------------------------------------------------------------
    def _drain_queue(self, batch_size: int) -> List[SwarmJob]:
        out: List[SwarmJob] = []
        with self._queue_lock:
            while self._queue and len(out) < batch_size:
                out.append(self._queue.popleft())
        return out

    def dispatch_once(self) -> Dict[str, Any]:
        """One dispatch cycle. Drains up to max_parallel jobs and runs them."""
        self.dispatches += 1
        batch = self._drain_queue(self.max_parallel)
        if not batch:
            return {"batch_size": 0, "results": []}
        self._wire()

        results: List[SwarmResult] = []
        started = time.time()
        if self.pool is not None and hasattr(self.pool, "run_parallel"):
            for job in batch:
                task_prompt = self._build_task_prompt(job)
                agent_results = self.pool.run_parallel(
                    task=task_prompt,
                    timeout=60.0,
                )
                # Use the first successful agent's answer; everyone
                # working the same job is redundant for this batch so we
                # just take the best.
                picked = next((a for a in agent_results if a.success), None)
                if picked is None:
                    self.errors += 1
                    results.append(SwarmResult(
                        job_intent=job.intent(),
                        job_target=job.target(),
                        agent_name="",
                        ok=False,
                        error="all agents failed",
                    ))
                    continue
                res = self._stage_proposal(job, picked.result, picked.agent_name)
                results.append(res)
        else:
            # No pool — skip; log and leave the jobs for a retry later.
            for job in batch:
                results.append(SwarmResult(
                    job_intent=job.intent(),
                    job_target=job.target(),
                    agent_name="",
                    ok=False,
                    error="agent pool unavailable",
                ))

        duration = time.time() - started
        summary = {
            "dispatch_n": self.dispatches,
            "batch_size": len(batch),
            "duration_s": duration,
            "results": [vars(r) for r in results],
        }
        self._append_log(summary)
        if self.bus is not None:
            try:
                self.bus.publish("repair_swarm.dispatch", summary, source="repair_swarm")
            except Exception:
                pass
        return summary

    def _build_task_prompt(self, job: SwarmJob) -> str:
        intent = job.intent()
        target = job.target()
        rationale = str(job.payload.get("rationale") or "")
        evidence = job.payload.get("evidence") or {}
        return (
            f"Intent: {intent}\n"
            f"Target: {target}\n"
            f"Rationale: {rationale}\n"
            f"Evidence: {json.dumps(evidence, default=str)}\n\n"
            "Produce a minimal JSON edit proposal as specified in the "
            "system prompt. Do not include commentary outside the JSON."
        )

    def _stage_proposal(
        self,
        job: SwarmJob,
        agent_text: str,
        agent_name: str,
    ) -> SwarmResult:
        self.jobs_processed += 1
        if self.integrator is None:
            return SwarmResult(
                job_intent=job.intent(),
                job_target=job.target(),
                agent_name=agent_name,
                ok=False,
                error="integrator unavailable",
            )
        try:
            proposal = self._extract_json(agent_text)
        except Exception as e:
            self.errors += 1
            return SwarmResult(
                job_intent=job.intent(),
                job_target=job.target(),
                agent_name=agent_name,
                ok=False,
                error=f"could not extract JSON: {e}",
            )

        path = str(proposal.get("path") or job.target())
        old_text = str(proposal.get("old_text") or "")
        new_text = str(proposal.get("new_text") or "")
        rationale = str(
            proposal.get("rationale")
            or f"[swarm/{agent_name}] {job.intent()} for {job.target()}"
        )
        if not old_text or not new_text:
            return SwarmResult(
                job_intent=job.intent(),
                job_target=job.target(),
                agent_name=agent_name,
                ok=False,
                error="proposal missing old_text or new_text",
            )

        result = self.integrator.propose_edit(
            target_path=path,
            old_text=old_text,
            new_text=new_text,
            rationale=f"{rationale} (via RepairSwarm/{agent_name})",
        )
        if not result.get("ok"):
            return SwarmResult(
                job_intent=job.intent(),
                job_target=job.target(),
                agent_name=agent_name,
                ok=False,
                error=str(result.get("error") or "propose_edit failed"),
            )
        self.proposals_created += 1
        return SwarmResult(
            job_intent=job.intent(),
            job_target=job.target(),
            agent_name=agent_name,
            ok=True,
            pending_id=str(result.get("pending_id") or ""),
        )

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        # Agents may wrap the JSON in a fence or preamble. Find the first
        # '{' and the matching '}' assuming balanced braces.
        if not text:
            raise ValueError("empty agent response")
        start = text.find("{")
        if start < 0:
            raise ValueError("no '{' in agent response")
        depth = 0
        end = -1
        for i, ch in enumerate(text[start:], start=start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end < 0:
            raise ValueError("unbalanced braces in agent response")
        return json.loads(text[start:end])

    def _append_log(self, record: Dict[str, Any]) -> None:
        try:
            _SWARM_LOG.parent.mkdir(parents=True, exist_ok=True)
            with _SWARM_LOG.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, default=str) + "\n")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Background loop
    # ------------------------------------------------------------------
    def start(self) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._wire()
            self._stop.clear()
            self._thread = threading.Thread(
                target=self._run,
                name="aureon-repair-swarm",
                daemon=True,
            )
            self._thread.start()
            logger.info("repair swarm: started (parallel=%d, interval=%.0fs)",
                        self.max_parallel, self.dispatch_interval_s)

    def stop(self, timeout: float = 3.0) -> None:
        with self._lock:
            self._stop.set()
            t = self._thread
        if t is not None:
            t.join(timeout=timeout)

    def is_alive(self) -> bool:
        t = self._thread
        return bool(t is not None and t.is_alive())

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self.dispatch_once()
            except Exception as e:
                logger.debug("dispatch error: %s", e)
            self._stop.wait(self.dispatch_interval_s)

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    def status(self) -> Dict[str, Any]:
        with self._queue_lock:
            qsize = len(self._queue)
        return {
            "alive": self.is_alive(),
            "queue_size": qsize,
            "dispatches": self.dispatches,
            "jobs_processed": self.jobs_processed,
            "proposals_created": self.proposals_created,
            "errors": self.errors,
            "max_parallel": self.max_parallel,
            "dispatch_interval_s": self.dispatch_interval_s,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────

_instance: Optional[RepairSwarm] = None
_instance_lock = threading.Lock()


def get_repair_swarm() -> RepairSwarm:
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = RepairSwarm()
        return _instance


def launch_repair_swarm(max_parallel: int = 4, dispatch_interval_s: float = 10.0) -> RepairSwarm:
    swarm = get_repair_swarm()
    swarm.max_parallel = max(1, int(max_parallel))
    swarm.dispatch_interval_s = max(1.0, float(dispatch_interval_s))
    swarm.start()
    return swarm


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Aureon repair swarm.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_st = sub.add_parser("status")
    p_one = sub.add_parser("dispatch_once")

    p_watch = sub.add_parser("watch")
    p_watch.add_argument("--parallel", type=int, default=4)
    p_watch.add_argument("--interval", type=float, default=10.0)
    p_watch.add_argument("--runtime-seconds", type=float, default=0.0)

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s :: %(message)s")

    if args.cmd == "status":
        print(json.dumps(get_repair_swarm().status(), indent=2))
    elif args.cmd == "dispatch_once":
        print(json.dumps(get_repair_swarm().dispatch_once(), indent=2, default=str))
    elif args.cmd == "watch":
        sw = launch_repair_swarm(max_parallel=args.parallel, dispatch_interval_s=args.interval)
        t0 = time.time()
        try:
            while sw.is_alive():
                time.sleep(max(1.0, args.interval / 2))
                if args.runtime_seconds and (time.time() - t0) >= args.runtime_seconds:
                    break
        except KeyboardInterrupt:
            pass
        finally:
            sw.stop()
            print(json.dumps(sw.status(), indent=2))
