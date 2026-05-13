"""
MAXIMUM STRESS TEST — Multi-Agent System
==========================================
15 extreme scenarios. Every edge case. Every breaking point.
If it survives this, it survives HMRC.

Scenarios:
  1. Gary's real position (baseline)
  2. Zero income (brand new business, nothing earned)
  3. Loss-making year (expenses > income)
  4. Higher rate taxpayer (£80k)
  5. PA taper zone (£105k — the 60% trap)
  6. Micro business (under trading allowance)
  7. VAT threshold boundary (£89,999)
  8. CIS overpayment (CIS > total liability by miles)
  9. Massive turnover (£500k construction firm)
  10. Minimum viable (£1 income, £0 expenses)
  11. All expenses in one category (motor only)
  12. Negative net profit with huge CIS
  13. Partner with income (marriage allowance test)
  14. Extreme mileage (50,000 miles)
  15. Zero CIS (not construction — pure self-employed)
  16. Concurrent team runs (parallel stress)
  17. Single agent isolation test
  18. Cascade failure test (deliberately break one system)
  19. Message bus flood test
  20. Shared memory contention test

Aureon Creator / Aureon Research — April 2026
"""

import sys
import os
import time
import threading
import traceback
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from core.hnc_multi_agent import (
    HNCMultiAgent, HNCTeam, HNCAgent, AgentPool,
    TaskQueue, TaskNode, MessageBus, SharedMemory,
    ToolRegistry, AgentRole, TaskStatus, Message,
    MessageType, AgentConfig, HNCSystemAdapter,
)


# ═══════════════════════════════════════════════════════════════════
# TEST HARNESS
# ═══════════════════════════════════════════════════════════════════

class StressTestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.agents_ok = 0
        self.agents_fail = 0
        self.errors = []
        self.time_taken = 0
        self.details = {}

    def __repr__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.name} — {self.agents_ok}/{self.agents_ok + self.agents_fail} agents ({self.time_taken:.2f}s)"


def run_scenario(name: str, params: dict, expect_all_pass: bool = True,
                 expected_agents: int = 11) -> StressTestResult:
    """Run a single scenario through the full multi-agent system"""
    result = StressTestResult(name)
    start = time.time()

    try:
        orchestrator = HNCMultiAgent(params=params)
        team = orchestrator.createTeam(name.lower().replace(" ", "_"))
        agent_results = orchestrator.runTeam(name.lower().replace(" ", "_"))

        result.agents_ok = sum(1 for r in agent_results.values() if r.success)
        result.agents_fail = sum(1 for r in agent_results.values() if not r.success)

        # Collect errors
        for aid, r in agent_results.items():
            if not r.success:
                result.errors.append(f"  {r.role.value}: {r.error}")

        # Check shared memory got populated
        memory_keys = list(team.shared_memory.read_all().keys())
        result.details["memory_keys"] = len(memory_keys)
        result.details["messages"] = len(team.message_bus.get_log())

        if expect_all_pass:
            result.passed = (result.agents_ok == expected_agents and result.agents_fail == 0)
        else:
            # For scenarios where we expect some failures
            result.passed = True

    except Exception as e:
        result.errors.append(f"  CRASH: {e}")
        result.passed = False
        traceback.print_exc()

    result.time_taken = time.time() - start
    return result


# ═══════════════════════════════════════════════════════════════════
# SCENARIOS
# ═══════════════════════════════════════════════════════════════════

SCENARIOS = [
    # 1. BASELINE — Gary's real position
    ("1. Gary Baseline (£51k CIS subbie)", {
        "gross_income": 51_000, "net_profit": 25_000, "cis_deducted": 10_200,
        "total_expenses": 26_000, "cost_of_sales": 8_000, "other_direct": 5_000,
        "motor": 3_000, "admin": 2_000, "other_expenses": 1_500,
        "partner_income": 0, "mileage_estimate": 8_000,
    }),

    # 2. ZERO INCOME — brand new business
    ("2. Zero Income (new business)", {
        "gross_income": 0, "net_profit": 0, "cis_deducted": 0,
        "total_expenses": 0, "cost_of_sales": 0, "other_direct": 0,
        "motor": 0, "admin": 0, "other_expenses": 0,
        "partner_income": 0, "mileage_estimate": 0,
    }),

    # 3. LOSS YEAR — expenses exceed income
    ("3. Loss Year (£30k turnover, £35k expenses)", {
        "gross_income": 30_000, "net_profit": -5_000, "cis_deducted": 6_000,
        "total_expenses": 35_000, "cost_of_sales": 15_000, "other_direct": 8_000,
        "motor": 5_000, "admin": 4_000, "other_expenses": 3_000,
        "partner_income": 0, "mileage_estimate": 12_000,
    }),

    # 4. HIGHER RATE — £80k net profit
    ("4. Higher Rate (£80k net profit)", {
        "gross_income": 120_000, "net_profit": 80_000, "cis_deducted": 24_000,
        "total_expenses": 40_000, "cost_of_sales": 18_000, "other_direct": 8_000,
        "motor": 5_000, "admin": 4_000, "other_expenses": 5_000,
        "partner_income": 0, "mileage_estimate": 15_000,
    }),

    # 5. PA TAPER ZONE — the 60% effective rate trap
    ("5. PA Taper Zone (£105k — 60% trap)", {
        "gross_income": 150_000, "net_profit": 105_000, "cis_deducted": 30_000,
        "total_expenses": 45_000, "cost_of_sales": 20_000, "other_direct": 10_000,
        "motor": 6_000, "admin": 4_000, "other_expenses": 5_000,
        "partner_income": 0, "mileage_estimate": 18_000,
    }),

    # 6. MICRO BUSINESS — under trading allowance (£1,000)
    ("6. Micro Business (£800 turnover)", {
        "gross_income": 800, "net_profit": 600, "cis_deducted": 160,
        "total_expenses": 200, "cost_of_sales": 100, "other_direct": 50,
        "motor": 30, "admin": 10, "other_expenses": 10,
        "partner_income": 0, "mileage_estimate": 500,
    }),

    # 7. VAT BOUNDARY — just under threshold
    ("7. VAT Boundary (£89,999 turnover)", {
        "gross_income": 89_999, "net_profit": 45_000, "cis_deducted": 18_000,
        "total_expenses": 44_999, "cost_of_sales": 20_000, "other_direct": 10_000,
        "motor": 6_000, "admin": 4_000, "other_expenses": 4_999,
        "partner_income": 0, "mileage_estimate": 12_000,
    }),

    # 8. CIS OVERPAYMENT — massive refund due
    ("8. CIS Overpayment (£20k CIS on £30k profit)", {
        "gross_income": 60_000, "net_profit": 30_000, "cis_deducted": 20_000,
        "total_expenses": 30_000, "cost_of_sales": 12_000, "other_direct": 6_000,
        "motor": 4_000, "admin": 3_000, "other_expenses": 5_000,
        "partner_income": 0, "mileage_estimate": 10_000,
    }),

    # 9. MASSIVE TURNOVER — £500k construction firm
    ("9. Massive Turnover (£500k firm)", {
        "gross_income": 500_000, "net_profit": 150_000, "cis_deducted": 100_000,
        "total_expenses": 350_000, "cost_of_sales": 200_000, "other_direct": 60_000,
        "motor": 30_000, "admin": 25_000, "other_expenses": 35_000,
        "partner_income": 30_000, "mileage_estimate": 40_000,
    }),

    # 10. MINIMUM VIABLE — £1 income
    ("10. Minimum Viable (£1 income)", {
        "gross_income": 1, "net_profit": 1, "cis_deducted": 0,
        "total_expenses": 0, "cost_of_sales": 0, "other_direct": 0,
        "motor": 0, "admin": 0, "other_expenses": 0,
        "partner_income": 0, "mileage_estimate": 0,
    }),

    # 11. ALL MOTOR — every expense is vehicle costs
    ("11. All Motor Expenses (£15k motor only)", {
        "gross_income": 40_000, "net_profit": 25_000, "cis_deducted": 8_000,
        "total_expenses": 15_000, "cost_of_sales": 0, "other_direct": 0,
        "motor": 15_000, "admin": 0, "other_expenses": 0,
        "partner_income": 0, "mileage_estimate": 25_000,
    }),

    # 12. NEGATIVE PROFIT + HUGE CIS
    ("12. Deep Loss + Huge CIS (£-20k profit, £15k CIS)", {
        "gross_income": 40_000, "net_profit": -20_000, "cis_deducted": 15_000,
        "total_expenses": 60_000, "cost_of_sales": 30_000, "other_direct": 12_000,
        "motor": 8_000, "admin": 5_000, "other_expenses": 5_000,
        "partner_income": 0, "mileage_estimate": 15_000,
    }),

    # 13. PARTNER INCOME — marriage allowance trigger
    ("13. Partner Income (spouse £8k, marriage allowance)", {
        "gross_income": 51_000, "net_profit": 25_000, "cis_deducted": 10_200,
        "total_expenses": 26_000, "cost_of_sales": 8_000, "other_direct": 5_000,
        "motor": 3_000, "admin": 2_000, "other_expenses": 1_500,
        "partner_income": 8_000, "mileage_estimate": 8_000,
    }),

    # 14. EXTREME MILEAGE — 50,000 miles
    ("14. Extreme Mileage (50k miles)", {
        "gross_income": 70_000, "net_profit": 35_000, "cis_deducted": 14_000,
        "total_expenses": 35_000, "cost_of_sales": 12_000, "other_direct": 8_000,
        "motor": 8_000, "admin": 3_000, "other_expenses": 4_000,
        "partner_income": 0, "mileage_estimate": 50_000,
    }),

    # 15. ZERO CIS — pure self-employed, no construction
    ("15. Zero CIS (pure self-employed)", {
        "gross_income": 45_000, "net_profit": 30_000, "cis_deducted": 0,
        "total_expenses": 15_000, "cost_of_sales": 5_000, "other_direct": 3_000,
        "motor": 3_000, "admin": 2_000, "other_expenses": 2_000,
        "partner_income": 0, "mileage_estimate": 10_000,
    }),
]


# ═══════════════════════════════════════════════════════════════════
# INFRASTRUCTURE STRESS TESTS
# ═══════════════════════════════════════════════════════════════════

def test_message_bus_flood() -> StressTestResult:
    """Flood the message bus with 10,000 messages"""
    result = StressTestResult("16. Message Bus Flood (10k messages)")
    start = time.time()
    try:
        bus = MessageBus()
        received = {"count": 0}

        def counter(msg):
            received["count"] += 1

        bus.subscribe("listener", counter)

        for i in range(10_000):
            bus.publish(Message(
                msg_id=str(i),
                msg_type=MessageType.SIGNAL,
                sender="sender",
                receiver="listener",
                payload={"index": i},
            ))

        result.passed = (received["count"] == 10_000)
        result.details["messages_sent"] = 10_000
        result.details["messages_received"] = received["count"]
        result.agents_ok = 1 if result.passed else 0
        result.agents_fail = 0 if result.passed else 1
        if not result.passed:
            result.errors.append(f"  Expected 10000, got {received['count']}")
    except Exception as e:
        result.errors.append(f"  CRASH: {e}")
    result.time_taken = time.time() - start
    return result


def test_shared_memory_contention() -> StressTestResult:
    """Hammer shared memory from 20 threads simultaneously"""
    result = StressTestResult("17. Shared Memory Contention (20 threads)")
    start = time.time()
    try:
        mem = SharedMemory()
        errors = []
        threads_done = {"count": 0}

        def writer(thread_id: int):
            try:
                for i in range(1000):
                    mem.write(f"thread_{thread_id}", f"key_{thread_id}_{i}", i * thread_id)
                    val = mem.read(f"key_{thread_id}_{i}")
                    if val != i * thread_id:
                        errors.append(f"Thread {thread_id}: expected {i * thread_id}, got {val}")
                threads_done["count"] += 1
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")

        threads = [threading.Thread(target=writer, args=(t,)) for t in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        result.passed = (len(errors) == 0 and threads_done["count"] == 20)
        result.details["threads_completed"] = threads_done["count"]
        result.details["total_writes"] = 20_000
        result.details["memory_keys"] = len(mem.read_all())
        result.agents_ok = 1 if result.passed else 0
        result.agents_fail = 0 if result.passed else 1
        if errors:
            result.errors = errors[:5]
    except Exception as e:
        result.errors.append(f"  CRASH: {e}")
    result.time_taken = time.time() - start
    return result


def test_cascade_failure() -> StressTestResult:
    """Deliberately fail one agent, verify cascade"""
    result = StressTestResult("18. Cascade Failure (break warfare, check cascade)")
    start = time.time()
    try:
        tq = TaskQueue()
        tq.add_task(TaskNode(task_id="A", agent_id="A"))
        tq.add_task(TaskNode(task_id="B", agent_id="B", depends_on=["A"]))
        tq.add_task(TaskNode(task_id="C", agent_id="C", depends_on=["B"]))
        tq.add_task(TaskNode(task_id="D", agent_id="D", depends_on=["A"]))
        tq.add_task(TaskNode(task_id="E", agent_id="E"))  # Independent

        # A runs and fails
        tq.mark_running("A")
        tq.mark_failed("A", "Deliberate failure")

        # E should still be ready
        ready = tq.get_ready_tasks()

        status = tq.get_status()
        result.details = status

        # A=failed, B=cancelled (dep on A), C=cancelled (dep on B), D=cancelled (dep on A), E=pending/ready
        expected = {
            "A": "failed",
            "B": "cancelled",
            "C": "cancelled",
            "D": "cancelled",
            "E": "pending",
        }

        result.passed = (status == expected)
        result.agents_ok = sum(1 for v in status.values() if v in ("completed", "pending"))
        result.agents_fail = sum(1 for v in status.values() if v in ("failed", "cancelled"))
        if not result.passed:
            result.errors.append(f"  Expected {expected}")
            result.errors.append(f"  Got      {status}")

    except Exception as e:
        result.errors.append(f"  CRASH: {e}")
    result.time_taken = time.time() - start
    return result


def test_tool_registry() -> StressTestResult:
    """Stress test all 5 built-in tools"""
    result = StressTestResult("19. Tool Registry (all 5 built-in tools)")
    start = time.time()
    try:
        mem = SharedMemory()
        tools = ToolRegistry(mem)
        errors = []

        # 1. Calculate
        val = tools.invoke("calculate", expression="max(0, 25000 - PA) * BASIC_RATE")
        expected_tax = (25000 - 12570) * 0.20
        if abs(val - expected_tax) > 0.01:
            errors.append(f"  calculate: expected {expected_tax}, got {val}")

        # 2. Store + Lookup
        tools.invoke("store", key="test_val", value=42, agent_id="test")
        got = tools.invoke("lookup", key="test_val")
        if got != 42:
            errors.append(f"  store/lookup: expected 42, got {got}")

        # 3. Validate
        v = tools.invoke("validate", claim_type="mileage_45p", amount=5000)
        if not v["valid"]:
            errors.append(f"  validate: £5000 mileage should be valid")

        v2 = tools.invoke("validate", claim_type="trading_allowance", amount=1500)
        if v2["valid"]:
            errors.append(f"  validate: £1500 trading allowance should be invalid (limit £1000)")

        # 4. Benchmark
        b = tools.invoke("benchmark", metric="gross_profit_margin", value=0.50)
        if not b["in_range"]:
            errors.append(f"  benchmark: 50% GP margin should be in range")

        b2 = tools.invoke("benchmark", metric="gross_profit_margin", value=0.95)
        if b2["in_range"]:
            errors.append(f"  benchmark: 95% GP margin should be out of range")

        # 5. Unknown tool
        try:
            tools.invoke("nonexistent_tool")
            errors.append("  Should have raised ValueError for unknown tool")
        except ValueError:
            pass  # Expected

        # 6. Custom tool via defineTool
        tools.define_tool("double", lambda x: x * 2)
        d = tools.invoke("double", x=21)
        if d != 42:
            errors.append(f"  defineTool: expected 42, got {d}")

        result.passed = len(errors) == 0
        result.agents_ok = 6 - len(errors)
        result.agents_fail = len(errors)
        result.errors = errors

    except Exception as e:
        result.errors.append(f"  CRASH: {e}")
    result.time_taken = time.time() - start
    return result


def test_single_agent_isolation() -> StressTestResult:
    """Run each of the 11 agents completely alone"""
    result = StressTestResult("20. Single Agent Isolation (11 solo runs)")
    start = time.time()
    try:
        params = {
            "gross_income": 51_000, "net_profit": 25_000, "cis_deducted": 10_200,
            "total_expenses": 26_000, "cost_of_sales": 8_000, "other_direct": 5_000,
            "motor": 3_000, "admin": 2_000, "other_expenses": 1_500,
            "partner_income": 0, "mileage_estimate": 8_000,
        }

        roles_to_test = [r for r in AgentRole if r not in (AgentRole.QUEEN, AgentRole.NEXUS)]
        errors = []
        ok_count = 0

        for role in roles_to_test:
            try:
                orchestrator = HNCMultiAgent(params=params)
                team = orchestrator.createTeam(f"solo_{role.value}", roles=[role])
                results = orchestrator.runTeam(f"solo_{role.value}")
                agent_ok = all(r.success for r in results.values())
                if agent_ok:
                    ok_count += 1
                else:
                    for r in results.values():
                        if not r.success:
                            errors.append(f"  {role.value} solo FAIL: {r.error}")
            except Exception as e:
                errors.append(f"  {role.value} solo CRASH: {e}")

        result.agents_ok = ok_count
        result.agents_fail = len(roles_to_test) - ok_count
        result.passed = ok_count == len(roles_to_test)
        result.errors = errors

    except Exception as e:
        result.errors.append(f"  CRASH: {e}")
    result.time_taken = time.time() - start
    return result


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("HNC MULTI-AGENT — MAXIMUM STRESS TEST")
    print("20 Scenarios. Every Edge Case. Every Breaking Point.")
    print("=" * 70)

    all_results = []
    total_start = time.time()

    # Run 15 financial scenarios
    print(f"\n{'─' * 70}")
    print("PHASE 1: FINANCIAL SCENARIOS (15 positions)")
    print(f"{'─' * 70}")

    for name, params in SCENARIOS:
        print(f"\n  Running: {name}")
        r = run_scenario(name, params)
        all_results.append(r)
        status_icon = "✓" if r.passed else "✗"
        print(f"  {status_icon} {r}")
        if r.errors:
            for err in r.errors[:3]:
                print(f"    {err}")

    # Run infrastructure tests
    print(f"\n{'─' * 70}")
    print("PHASE 2: INFRASTRUCTURE STRESS TESTS")
    print(f"{'─' * 70}")

    infra_tests = [
        test_message_bus_flood,
        test_shared_memory_contention,
        test_cascade_failure,
        test_tool_registry,
        test_single_agent_isolation,
    ]

    for test_fn in infra_tests:
        print(f"\n  Running: {test_fn.__doc__}")
        r = test_fn()
        all_results.append(r)
        status_icon = "✓" if r.passed else "✗"
        print(f"  {status_icon} {r}")
        if r.errors:
            for err in r.errors[:3]:
                print(f"    {err}")

    # Final summary
    total_time = time.time() - total_start
    passed = sum(1 for r in all_results if r.passed)
    failed = sum(1 for r in all_results if not r.passed)
    total_agents = sum(r.agents_ok + r.agents_fail for r in all_results)
    total_agents_ok = sum(r.agents_ok for r in all_results)

    print(f"\n{'=' * 70}")
    print("STRESS TEST SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Scenarios:     {passed}/{passed + failed} passed")
    print(f"  Agent runs:    {total_agents_ok}/{total_agents} succeeded")
    print(f"  Total time:    {total_time:.1f}s")
    print(f"{'─' * 70}")

    if failed > 0:
        print("\n  FAILURES:")
        for r in all_results:
            if not r.passed:
                print(f"    ✗ {r.name}")
                for err in r.errors:
                    print(f"      {err}")
    else:
        print(f"\n  ALL {passed} SCENARIOS PASSED.")
        print(f"  {total_agents_ok} agent executions. Zero failures.")

    print(f"\n{'─' * 70}")
    print("No LLMs were harmed in the making of this test.")
    print(f"{'─' * 70}")

    # Exit code
    sys.exit(0 if failed == 0 else 1)
