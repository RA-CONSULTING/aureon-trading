#!/usr/bin/env python3
"""
MAXIMUM STRESS TEST — Aureon In-House AI Framework
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hammers every component of the in-house AI framework + Queen AI Bridge
under extreme concurrent load to verify:

  1. LLM adapter throughput        (1000 concurrent prompts)
  2. Tool registry race conditions (10000 tool calls across threads)
  3. Agent parallel execution      (50 agents x 20 tasks each)
  4. AgentPool saturation          (pool size 8 vs 100 concurrent jobs)
  5. TaskQueue DAG resolution      (500-task dependency graph)
  6. TaskQueue cascade failure     (100-task chain with upstream failure)
  7. Message bus throughput        (50000 messages, 20 subscribers)
  8. SharedMemory contention       (10000 concurrent set/get operations)
  9. Team orchestration            (5 teams x 10 agents running in parallel)
 10. OpenMultiAgent full-stack     (everything at once)
 11. Queen AI Bridge integration   (1000 enhance_thought calls)
 12. Sustained load soak test      (60 seconds continuous fire)

Usage:
    python tests/stress/stress_test_inhouse_ai.py
    python tests/stress/stress_test_inhouse_ai.py --quick
    python tests/stress/stress_test_inhouse_ai.py --soak 120
"""

from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Ensure repo root on path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Suppress noisy logging during stress test
import logging
logging.basicConfig(level=logging.ERROR, format="%(levelname)s %(name)s %(message)s")

from aureon.inhouse_ai import (
    OpenMultiAgent,
    AgentConfig,
    Agent,
    AgentPool,
    TaskQueue,
    Task,
    TaskStatus,
    Team,
    ToolRegistry,
    AureonBrainAdapter,
    AureonLocalAdapter,
    AureonHybridAdapter,
    LLMResponse,
)
from aureon.inhouse_ai.team import MessageBus, SharedMemory


# ─────────────────────────────────────────────────────────────────────────────
# Test result tracking
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class TestResult:
    name: str
    passed: bool = False
    duration_s: float = 0.0
    operations: int = 0
    throughput_ops_s: float = 0.0
    errors: int = 0
    details: Dict[str, Any] = field(default_factory=dict)
    exception: Optional[str] = None

    def report(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        icon = "[OK]" if self.passed else "[XX]"
        line = (
            f"{icon} {status:4s}  {self.name:42s}  "
            f"{self.operations:>7d} ops  "
            f"{self.duration_s:>7.2f}s  "
            f"{self.throughput_ops_s:>10.1f} ops/s  "
            f"errors={self.errors}"
        )
        if self.details:
            extras = "  ".join(f"{k}={v}" for k, v in self.details.items())
            line += f"\n        {extras}"
        if self.exception:
            line += f"\n        EXCEPTION: {self.exception}"
        return line


class StressTestRunner:
    """Executes stress tests and collects results."""

    def __init__(self, quick: bool = False):
        self.quick = quick
        self.results: List[TestResult] = []
        self.scale = 0.1 if quick else 1.0

    def scaled(self, n: int) -> int:
        return max(1, int(n * self.scale))

    def run(self, name: str, fn):
        """Run a single test with timing + error capture."""
        print(f"  Running: {name}...", flush=True)
        start = time.time()
        result = TestResult(name=name)
        try:
            details = fn() or {}
            result.duration_s = time.time() - start
            result.passed = True
            if isinstance(details, dict):
                result.operations = details.pop("operations", 0)
                result.errors = details.pop("errors", 0)
                result.details = details
                if result.duration_s > 0:
                    result.throughput_ops_s = result.operations / result.duration_s
        except Exception as e:
            result.duration_s = time.time() - start
            result.passed = False
            result.exception = f"{type(e).__name__}: {e}"
            traceback.print_exc()
        self.results.append(result)
        return result

    def summary(self):
        print("\n" + "=" * 100)
        print("  MAXIMUM STRESS TEST RESULTS")
        print("=" * 100)
        for r in self.results:
            print(r.report())
        print("=" * 100)
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        total_ops = sum(r.operations for r in self.results)
        total_time = sum(r.duration_s for r in self.results)
        total_errors = sum(r.errors for r in self.results)
        print(
            f"  TOTAL: {passed}/{total} tests passed  |  "
            f"{total_ops:,} operations  |  "
            f"{total_time:.2f}s total  |  "
            f"{total_errors} errors"
        )
        print("=" * 100)
        return passed == total


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: LLM adapter throughput
# ─────────────────────────────────────────────────────────────────────────────


def test_llm_adapter_throughput(runner: StressTestRunner):
    """Fire 1000 concurrent prompts at the Brain adapter."""
    n_prompts = runner.scaled(1000)
    adapter = AureonBrainAdapter()

    errors = 0
    errors_lock = threading.Lock()
    latencies = []
    latencies_lock = threading.Lock()

    def fire_prompt(i: int):
        nonlocal errors
        try:
            t0 = time.time()
            response = adapter.prompt(
                messages=[{"role": "user", "content": f"analyse BTCUSDT signal {i}"}],
                system="You are a market analyst",
                max_tokens=256,
            )
            dt = time.time() - t0
            with latencies_lock:
                latencies.append(dt)
            if not response.text:
                with errors_lock:
                    errors += 1
        except Exception:
            with errors_lock:
                errors += 1

    with ThreadPoolExecutor(max_workers=32) as executor:
        futures = [executor.submit(fire_prompt, i) for i in range(n_prompts)]
        for f in as_completed(futures):
            pass

    return {
        "operations": n_prompts,
        "errors": errors,
        "p50_latency_ms": round(statistics.median(latencies) * 1000, 2) if latencies else 0,
        "p99_latency_ms": round(sorted(latencies)[int(len(latencies) * 0.99)] * 1000, 2) if len(latencies) > 1 else 0,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: Tool registry race conditions
# ─────────────────────────────────────────────────────────────────────────────


def test_tool_registry_race(runner: StressTestRunner):
    """10000 concurrent tool calls across threads."""
    n_calls = runner.scaled(10000)
    registry = ToolRegistry(include_builtins=True)

    # Register a custom counter tool
    counter = {"value": 0}
    counter_lock = threading.Lock()

    def counter_handler(args):
        with counter_lock:
            counter["value"] += 1
            return json.dumps({"value": counter["value"]})

    registry.define_tool(
        name="counter",
        description="Increments a counter",
        input_schema={"type": "object", "properties": {}, "required": []},
        handler=counter_handler,
    )

    errors = 0
    errors_lock = threading.Lock()

    def hammer(i: int):
        nonlocal errors
        try:
            tool_name = random.choice(["counter", "read_state", "read_prices", "read_positions"])
            args = {"keys": "all"} if tool_name == "read_state" else \
                   {"symbols": "BTCUSDT", "top_n": 5} if tool_name == "read_prices" else \
                   {"exchange": "all"} if tool_name == "read_positions" else \
                   {}
            result = registry.execute(tool_name, args)
            if not result:
                with errors_lock:
                    errors += 1
        except Exception:
            with errors_lock:
                errors += 1

    with ThreadPoolExecutor(max_workers=64) as executor:
        futures = [executor.submit(hammer, i) for i in range(n_calls)]
        for f in as_completed(futures):
            pass

    return {
        "operations": n_calls,
        "errors": errors,
        "counter_final": counter["value"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: Agent parallel execution
# ─────────────────────────────────────────────────────────────────────────────


def test_agent_parallel_execution(runner: StressTestRunner):
    """50 agents running 20 tasks each in parallel."""
    n_agents = runner.scaled(50)
    n_tasks_per_agent = runner.scaled(20)
    adapter = AureonBrainAdapter()

    agents = [
        Agent(
            adapter=adapter,
            config=AgentConfig(
                name=f"StressAgent-{i}",
                system_prompt=f"You are stress agent {i}",
                max_turns=2,
            ),
        )
        for i in range(n_agents)
    ]

    total_ops = n_agents * n_tasks_per_agent
    errors = 0
    errors_lock = threading.Lock()

    def run_agent_tasks(agent: Agent):
        nonlocal errors
        for j in range(n_tasks_per_agent):
            try:
                result = agent.run(f"task {j} for {agent.name}")
                if not result:
                    with errors_lock:
                        errors += 1
            except Exception:
                with errors_lock:
                    errors += 1

    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(run_agent_tasks, a) for a in agents]
        for f in as_completed(futures):
            pass

    return {
        "operations": total_ops,
        "errors": errors,
        "agents": n_agents,
        "tasks_per_agent": n_tasks_per_agent,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: AgentPool saturation
# ─────────────────────────────────────────────────────────────────────────────


def test_agent_pool_saturation(runner: StressTestRunner):
    """AgentPool with size 8 vs 100 jobs."""
    pool_size = 8
    n_jobs = runner.scaled(100)
    adapter = AureonBrainAdapter()

    pool = AgentPool(max_concurrent=pool_size)
    for i in range(n_jobs):
        pool.add(Agent(
            adapter=adapter,
            config=AgentConfig(name=f"Worker-{i}", max_turns=1),
        ))

    results = pool.run_parallel("Compute signal for BTCUSDT", timeout=60)
    errors = sum(1 for r in results if not r.success)

    return {
        "operations": len(results),
        "errors": errors,
        "pool_size": pool_size,
        "successful": sum(1 for r in results if r.success),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: TaskQueue DAG resolution
# ─────────────────────────────────────────────────────────────────────────────


def test_task_queue_dag(runner: StressTestRunner):
    """Build a 500-task DAG and resolve dependencies."""
    n_tasks = runner.scaled(500)
    queue = TaskQueue()

    # Build a complex DAG: tasks chain in groups of 5
    task_ids = []
    for i in range(n_tasks):
        depends_on = []
        if i >= 5:
            # Each task depends on the task 5 slots back (mostly linear)
            depends_on.append(task_ids[i - 5])
        if i >= 10 and i % 3 == 0:
            # Every 3rd task also depends on one 10 slots back
            depends_on.append(task_ids[i - 10])

        task = queue.add(
            name=f"task_{i}",
            agent_name=f"agent_{i % 10}",
            prompt=f"task prompt {i}",
            depends_on=depends_on,
        )
        task_ids.append(task.id)

    # Process the queue
    resolved = 0
    max_iterations = n_tasks * 2
    while not queue.is_complete() and resolved < max_iterations:
        ready = queue.get_ready()
        if not ready:
            break
        for task in ready:
            queue.start(task.id)
            queue.complete(task.id, f"result_{task.name}")
            resolved += 1

    summary = queue.summary()
    return {
        "operations": resolved,
        "errors": summary.get("failed", 0) + summary.get("cancelled", 0),
        "tasks_total": n_tasks,
        "completed": summary.get("completed", 0),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Test 6: TaskQueue cascade failure
# ─────────────────────────────────────────────────────────────────────────────


def test_task_queue_cascade_failure(runner: StressTestRunner):
    """100-task chain with upstream failure — verify cascade."""
    n_tasks = max(runner.scaled(100), 20)  # Need at least 20 for fail-at-10 logic
    queue = TaskQueue()

    task_ids = []
    for i in range(n_tasks):
        depends_on = [task_ids[i - 1]] if i > 0 else []
        task = queue.add(
            name=f"chain_{i}",
            agent_name="chain_agent",
            prompt=f"step {i}",
            depends_on=depends_on,
        )
        task_ids.append(task.id)

    # Complete the first 10, then fail task 10 — expect cascade to 90 others
    for i in range(10):
        queue.start(task_ids[i])
        queue.complete(task_ids[i], "ok")

    queue.fail(task_ids[10], "intentional test failure")

    summary = queue.summary()
    cascade_count = summary.get("failed", 0)
    expected_failures = n_tasks - 10  # task 10 fails + all downstream

    details = {
        "operations": n_tasks,
        "errors": 0 if cascade_count == expected_failures else 1,
        "cascade_count": cascade_count,
        "expected": expected_failures,
        "completed": summary.get("completed", 0),
    }

    if cascade_count != expected_failures:
        raise AssertionError(
            f"Cascade failure broken: got {cascade_count} failed, expected {expected_failures}"
        )

    return details


# ─────────────────────────────────────────────────────────────────────────────
# Test 7: Message bus throughput
# ─────────────────────────────────────────────────────────────────────────────


def test_message_bus_throughput(runner: StressTestRunner):
    """50000 messages with 20 subscribers."""
    n_messages = runner.scaled(50000)
    n_subscribers = 20

    bus = MessageBus()
    received: Dict[int, int] = {i: 0 for i in range(n_subscribers)}
    received_lock = threading.Lock()

    def make_handler(sub_id: int):
        def handler(msg):
            with received_lock:
                received[sub_id] += 1
        return handler

    for i in range(n_subscribers):
        bus.subscribe("stress.topic", make_handler(i))

    def publisher(idx: int):
        bus.publish("stress.topic", {"msg": idx}, source="stress")

    with ThreadPoolExecutor(max_workers=32) as executor:
        futures = [executor.submit(publisher, i) for i in range(n_messages)]
        for f in as_completed(futures):
            pass

    total_received = sum(received.values())
    expected = n_messages * n_subscribers

    return {
        "operations": n_messages,
        "errors": 0 if total_received == expected else 1,
        "total_delivered": total_received,
        "expected": expected,
        "subscribers": n_subscribers,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Test 8: SharedMemory contention
# ─────────────────────────────────────────────────────────────────────────────


def test_shared_memory_contention(runner: StressTestRunner):
    """10000 concurrent set/get operations on SharedMemory."""
    n_ops = runner.scaled(10000)
    memory = SharedMemory()
    errors = 0
    errors_lock = threading.Lock()

    def hammer(i: int):
        nonlocal errors
        try:
            key = f"key_{i % 100}"
            if i % 2 == 0:
                memory.set(key, {"val": i, "ts": time.time()}, source=f"worker_{i}")
            else:
                memory.get(key, default={})
        except Exception:
            with errors_lock:
                errors += 1

    with ThreadPoolExecutor(max_workers=64) as executor:
        futures = [executor.submit(hammer, i) for i in range(n_ops)]
        for f in as_completed(futures):
            pass

    return {
        "operations": n_ops,
        "errors": errors,
        "keys_stored": len(memory.keys()),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Test 9: Team orchestration
# ─────────────────────────────────────────────────────────────────────────────


def test_team_orchestration(runner: StressTestRunner):
    """5 teams x 10 agents running in parallel."""
    n_teams = runner.scaled(5)
    n_agents_per_team = runner.scaled(10)
    adapter = AureonBrainAdapter()

    teams = []
    for t in range(n_teams):
        configs = [
            AgentConfig(name=f"Team{t}-Agent{a}", max_turns=1)
            for a in range(n_agents_per_team)
        ]
        team = Team(
            name=f"StressTeam-{t}",
            adapter=adapter,
            agent_configs=configs,
            max_concurrent=4,
        )
        teams.append(team)

    total_ops = 0
    errors = 0

    def run_team(team: Team):
        nonlocal total_ops, errors
        results = team.run_all("Analyse market state", parallel=True)
        total_ops += len(results)
        for r in results.values():
            if r.startswith("[ERROR]"):
                errors += 1

    with ThreadPoolExecutor(max_workers=n_teams) as executor:
        futures = [executor.submit(run_team, t) for t in teams]
        for f in as_completed(futures):
            pass

    return {
        "operations": total_ops,
        "errors": errors,
        "teams": n_teams,
        "agents_per_team": n_agents_per_team,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Test 10: OpenMultiAgent full-stack
# ─────────────────────────────────────────────────────────────────────────────


def test_open_multi_agent_full_stack(runner: StressTestRunner):
    """End-to-end orchestrator with teams + tasks + parallel agents."""
    oma = OpenMultiAgent(mode="brain")

    # Create 3 teams with 5 agents each
    for t in range(3):
        configs = [
            AgentConfig(name=f"Stack-T{t}-A{a}", max_turns=1)
            for a in range(5)
        ]
        oma.create_team(
            name=f"StackTeam-{t}",
            agent_configs=configs,
            max_concurrent=4,
        )

    total_ops = 0
    errors = 0

    # Run each team on a task
    for team_name in oma.list_teams():
        results = oma.run_team(team_name, "Compute signal")
        total_ops += len(results)
        for r in results.values():
            if r.startswith("[ERROR]"):
                errors += 1

    # Run standalone agents
    for i in range(runner.scaled(20)):
        try:
            oma.run_agent(
                name=f"Standalone-{i}",
                task=f"Check signal {i}",
                system_prompt="You are a signal checker.",
            )
            total_ops += 1
        except Exception:
            errors += 1

    # Build a task DAG in the first team
    first_team = oma.get_team("StackTeam-0")
    t1 = first_team.queue.add("fetch", agent_name="Stack-T0-A0", prompt="fetch")
    t2 = first_team.queue.add("analyse", agent_name="Stack-T0-A1", prompt="analyse", depends_on=[t1.id])
    t3 = first_team.queue.add("decide", agent_name="Stack-T0-A2", prompt="decide", depends_on=[t2.id])

    oma.run_tasks("StackTeam-0")
    total_ops += len(first_team.queue)

    # Get system-wide status
    status = oma.get_status()
    oma.shutdown()

    return {
        "operations": total_ops,
        "errors": errors,
        "teams": status["team_count"],
        "standalone": status["standalone_agent_count"],
        "tools": len(status["tools_registered"]),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Test 11: Queen AI Bridge integration
# ─────────────────────────────────────────────────────────────────────────────


def test_queen_ai_bridge_integration(runner: StressTestRunner):
    """1000 calls to enhance_thought + synthesise_insight + reflect."""
    n_calls = runner.scaled(1000)

    from aureon.queen.queen_inhouse_ai_bridge import QueenAIBridge
    bridge = QueenAIBridge()
    bridge.start()

    if not bridge.is_alive:
        raise RuntimeError("Queen AI Bridge adapter failed to initialise")

    errors = 0
    errors_lock = threading.Lock()

    def hammer(i: int):
        nonlocal errors
        try:
            op = i % 4
            if op == 0:
                result = bridge.enhance_thought(
                    "UPDATE",
                    perception={"significant_moves": [{"symbol": "BTCUSDT"}], "recent_bars": [1, 2, 3]},
                    emotion={"mood": "focused", "urgency": 0.6, "excitement": 0.4},
                )
            elif op == 1:
                insight = bridge.synthesise_insight(
                    market_data={"symbol": "BTCUSDT", "price": 100000 + i},
                    system_signals=[{"source": "scanner", "signal": "BUY"}],
                )
                result = insight.text
            elif op == 2:
                result = bridge.reflect([
                    {"action": "BUY", "confidence": 0.8},
                    {"action": "HOLD", "confidence": 0.5},
                    {"action": "BUY", "confidence": 0.9},
                ])
            else:
                result = bridge.reason(f"What is the state of signal {i}?")

            if not result:
                with errors_lock:
                    errors += 1
        except Exception:
            with errors_lock:
                errors += 1

    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(hammer, i) for i in range(n_calls)]
        for f in as_completed(futures):
            pass

    status = bridge.get_status()
    bridge.stop()

    return {
        "operations": n_calls,
        "errors": errors,
        "insights_generated": status["insights_generated"],
        "thoughts_enhanced": status["thoughts_enhanced"],
        "bridge_errors": status["errors"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Test 12: Sustained load soak test
# ─────────────────────────────────────────────────────────────────────────────


def test_sustained_soak(runner: StressTestRunner, duration_s: float = 10.0):
    """Continuous load for N seconds across all subsystems."""
    oma = OpenMultiAgent(mode="brain")
    oma.create_team(
        name="SoakTeam",
        agent_configs=[
            AgentConfig(name=f"Soak-{i}", max_turns=1) for i in range(6)
        ],
        max_concurrent=4,
    )

    total_ops = 0
    errors = 0
    stop_flag = threading.Event()
    counter_lock = threading.Lock()

    def worker():
        nonlocal total_ops, errors
        local_ops = 0
        local_errors = 0
        while not stop_flag.is_set():
            try:
                results = oma.run_team("SoakTeam", f"Soak cycle {local_ops}")
                local_ops += len(results)
                for r in results.values():
                    if r.startswith("[ERROR]"):
                        local_errors += 1
            except Exception:
                local_errors += 1
            local_ops += 1
        with counter_lock:
            total_ops += local_ops
            errors += local_errors

    n_workers = 4
    threads = [threading.Thread(target=worker, daemon=True) for _ in range(n_workers)]
    for t in threads:
        t.start()

    time.sleep(duration_s)
    stop_flag.set()

    for t in threads:
        t.join(timeout=30)

    oma.shutdown()

    return {
        "operations": total_ops,
        "errors": errors,
        "duration_s": duration_s,
        "workers": n_workers,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main runner
# ─────────────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Aureon In-House AI maximum stress test")
    parser.add_argument("--quick", action="store_true", help="Run at 10% scale for quick verification")
    parser.add_argument("--soak", type=float, default=10.0, help="Soak test duration seconds (default 10)")
    parser.add_argument("--skip-soak", action="store_true", help="Skip the soak test")
    args = parser.parse_args()

    print("=" * 100)
    print("  AUREON IN-HOUSE AI — MAXIMUM STRESS TEST")
    print("  " + ("QUICK MODE (10% scale)" if args.quick else "FULL SCALE"))
    print("=" * 100 + "\n")

    runner = StressTestRunner(quick=args.quick)

    print("\n[Test Suite]")
    runner.run("1. LLM adapter throughput",          lambda: test_llm_adapter_throughput(runner))
    runner.run("2. Tool registry race conditions",   lambda: test_tool_registry_race(runner))
    runner.run("3. Agent parallel execution",        lambda: test_agent_parallel_execution(runner))
    runner.run("4. AgentPool saturation",            lambda: test_agent_pool_saturation(runner))
    runner.run("5. TaskQueue DAG resolution",        lambda: test_task_queue_dag(runner))
    runner.run("6. TaskQueue cascade failure",       lambda: test_task_queue_cascade_failure(runner))
    runner.run("7. Message bus throughput",          lambda: test_message_bus_throughput(runner))
    runner.run("8. SharedMemory contention",         lambda: test_shared_memory_contention(runner))
    runner.run("9. Team orchestration",              lambda: test_team_orchestration(runner))
    runner.run("10. OpenMultiAgent full-stack",      lambda: test_open_multi_agent_full_stack(runner))
    runner.run("11. Queen AI Bridge integration",    lambda: test_queen_ai_bridge_integration(runner))

    if not args.skip_soak:
        runner.run(
            f"12. Sustained soak test ({args.soak}s)",
            lambda: test_sustained_soak(runner, duration_s=args.soak),
        )

    all_passed = runner.summary()
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
