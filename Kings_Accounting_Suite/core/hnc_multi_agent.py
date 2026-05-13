"""
HNC MULTI-AGENT SYSTEM — hnc_multi_agent.py
=============================================
Adapted from OpenMultiAgent architecture (Orchestrator pattern).
Fully in-house. ZERO external dependencies. No LLM APIs.

The original OpenMultiAgent uses:
    LLMAdapter → AnthropicAdapter, OpenAIAdapter, CopilotAdapter

We replace that entire layer with:
    HNCSystemAdapter → 11 internal intelligence systems

    EXTERNAL (what we DON'T use)       →  INTERNAL (what we DO use)
    ─────────────────────────────────────────────────────────────────
    AnthropicAdapter                    →  WarfareAdapter
    OpenAIAdapter                       →  SeerAdapter
    CopilotAdapter                      →  LatticeAdapter
    (none — we have MORE)               →  ScannerAdapter
                                        →  ConsciousnessAdapter
                                        →  MetacognitionAdapter
                                        →  IntelligenceAdapter
                                        →  StrategyAdapter
                                        →  ThroneAdapter
                                        →  AurisNodesAdapter
                                        →  ValidatorAdapter

Architecture (mirrors the diagram exactly):

    HNCMultiAgent (Orchestrator)
        createTeam()  runTeam()  runTasks()  runAgent()  getStatus()
            │
            ▼
        HNCTeam
            - AgentConfig[]
            - MessageBus
            - TaskQueue
            - SharedMemory
           ┌────────┴────────┐
           ▼                 ▼
       AgentPool          TaskQueue
       - Semaphore        - dependency graph
       - runParallel()    - auto unblock
                          - cascade failure
           │
           ▼
        HNCAgent
        - run()
        - prompt()           ──►  HNCSystemAdapter
        - stream()                - WarfareAdapter
                                  - SeerAdapter
           │                      - LatticeAdapter
           ▼                      - ... (11 total)
       AgentRunner
       - conversation loop   ──►  ToolRegistry
       - tool dispatch            - defineTool()
                                  - 5 built-in tools

Why no LLMs? Because this system doesn't GUESS. It CALCULATES.
Tax law is deterministic. HMRC rules are deterministic.
You don't need a language model to add up numbers.
You need a SYSTEM that knows the law.

Aureon Creator / Aureon Research — April 2026
"""

from __future__ import annotations
import logging
import time
import uuid
import threading
import queue
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

logger = logging.getLogger("hnc_multi_agent")


# ═══════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════

class AgentRole(Enum):
    """What each agent specialises in"""
    WARFARE = "warfare"              # Tax battlefield analysis
    SEER = "seer"                    # Prediction & forecasting
    SCANNER = "scanner"              # Deep transaction scanning
    LATTICE = "lattice"              # Multi-strategy optimisation
    CONSCIOUSNESS = "consciousness"  # Self-audit & conscience
    METACOGNITION = "metacognition"  # Transaction reasoning
    INTELLIGENCE = "intelligence"    # Government moves & signals
    STRATEGY = "strategy"            # Tax optimisation calculations
    THRONE = "throne"                # Fiscal environment intel
    AURIS_NODES = "auris_nodes"      # 9-node coherence classification
    VALIDATOR = "validator"          # SA103 return validation
    QUEEN = "queen"                  # Master orchestrator (pipeline)
    NEXUS = "nexus"                  # Anti-pattern randomisation


class TaskStatus(Enum):
    PENDING = "pending"
    BLOCKED = "blocked"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageType(Enum):
    SIGNAL = "signal"        # Data signal from one agent to another
    COMMAND = "command"       # Direct instruction
    ALERT = "alert"          # Something needs attention
    RESULT = "result"        # Task completed
    HEARTBEAT = "heartbeat"  # I'm alive


# ═══════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════

@dataclass
class AgentConfig:
    """Configuration for a single agent"""
    agent_id: str
    role: AgentRole
    name: str
    priority: int = 5                      # 1 = highest, 10 = lowest
    max_retries: int = 2
    timeout_seconds: float = 30.0
    depends_on: List[str] = field(default_factory=list)  # Agent IDs this needs first
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Message:
    """Inter-agent message"""
    msg_id: str
    msg_type: MessageType
    sender: str          # Agent ID
    receiver: str        # Agent ID or "*" for broadcast
    payload: Any
    timestamp: float = field(default_factory=time.time)
    priority: int = 5


@dataclass
class TaskNode:
    """A task in the dependency graph"""
    task_id: str
    agent_id: str
    status: TaskStatus = TaskStatus.PENDING
    depends_on: List[str] = field(default_factory=list)
    result: Any = None
    error: str = ""
    started_at: float = 0
    completed_at: float = 0
    retries: int = 0


@dataclass
class AgentResult:
    """What an agent returns after running"""
    agent_id: str
    role: AgentRole
    success: bool
    data: Any = None
    error: str = ""
    execution_time: float = 0
    signals_emitted: int = 0


# ═══════════════════════════════════════════════════════════════════
# MESSAGE BUS — Inter-agent communication
# ═══════════════════════════════════════════════════════════════════

class MessageBus:
    """
    Pub/sub message bus for agent-to-agent communication.
    Agents publish signals. Other agents subscribe.
    No external broker needed — it's a thread-safe in-memory bus.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._subscribers: Dict[str, List[Callable]] = {}  # agent_id → callbacks
        self._broadcast_subscribers: List[Callable] = []
        self._message_log: List[Message] = []

    def subscribe(self, agent_id: str, callback: Callable[[Message], None]):
        """Subscribe an agent to receive messages"""
        with self._lock:
            if agent_id not in self._subscribers:
                self._subscribers[agent_id] = []
            self._subscribers[agent_id].append(callback)

    def subscribe_broadcast(self, callback: Callable[[Message], None]):
        """Subscribe to ALL messages"""
        with self._lock:
            self._broadcast_subscribers.append(callback)

    def publish(self, message: Message):
        """Publish a message to the bus"""
        with self._lock:
            self._message_log.append(message)
            # Direct delivery
            if message.receiver != "*" and message.receiver in self._subscribers:
                for cb in self._subscribers[message.receiver]:
                    try:
                        cb(message)
                    except Exception as e:
                        logger.warning(f"Message delivery failed: {e}")
            # Broadcast
            if message.receiver == "*":
                for agent_id, callbacks in self._subscribers.items():
                    if agent_id != message.sender:
                        for cb in callbacks:
                            try:
                                cb(message)
                            except Exception as e:
                                logger.warning(f"Broadcast delivery failed: {e}")
            # Broadcast subscribers always get everything
            for cb in self._broadcast_subscribers:
                try:
                    cb(message)
                except Exception:
                    pass

    def get_log(self) -> List[Message]:
        """Get full message history"""
        with self._lock:
            return list(self._message_log)

    def clear(self):
        with self._lock:
            self._message_log.clear()


# ═══════════════════════════════════════════════════════════════════
# SHARED MEMORY — Cross-agent state
# ═══════════════════════════════════════════════════════════════════

class SharedMemory:
    """
    Thread-safe key-value store that all agents can read/write.
    This is the "shared consciousness" — every agent's output
    is visible to every other agent.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._store: Dict[str, Any] = {}
        self._history: List[Tuple[str, str, Any, float]] = []  # (agent, key, value, time)

    def write(self, agent_id: str, key: str, value: Any):
        with self._lock:
            self._store[key] = value
            self._history.append((agent_id, key, value, time.time()))

    def read(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._store.get(key, default)

    def read_all(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._store)

    def has(self, key: str) -> bool:
        with self._lock:
            return key in self._store

    def get_history(self, key: str = None) -> List[Tuple]:
        with self._lock:
            if key:
                return [(a, k, v, t) for a, k, v, t in self._history if k == key]
            return list(self._history)


# ═══════════════════════════════════════════════════════════════════
# TOOL REGISTRY — Built-in tools for agents
# ═══════════════════════════════════════════════════════════════════

class ToolRegistry:
    """
    Replaces the external ToolRegistry.
    5 built-in tools + defineTool() for custom tools.
    All tools operate on internal data — no API calls.
    """

    def __init__(self, shared_memory: SharedMemory):
        self._tools: Dict[str, Callable] = {}
        self._memory = shared_memory
        self._register_builtins()

    def _register_builtins(self):
        """Register the 5 built-in tools"""

        # 1. CALCULATE — Run tax calculations
        def calculate(expression: str, context: dict = None) -> float:
            """Evaluate a tax calculation expression"""
            # Safe evaluation for tax arithmetic
            allowed = {
                "max": max, "min": min, "abs": abs,
                "round": round, "sum": sum, "len": len,
                "PA": 12_570, "BASIC_RATE": 0.20,
                "HIGHER_RATE": 0.40, "NI_RATE": 0.06,
                "CLASS2": 3.45, "CIS_RATE": 0.20,
                "BASIC_BAND": 37_700, "VAT_THRESHOLD": 90_000,
                "PA_TAPER_START": 100_000,
            }
            if context:
                allowed.update(context)
            try:
                return eval(expression, {"__builtins__": {}}, allowed)
            except Exception as e:
                return float("nan")
        self._tools["calculate"] = calculate

        # 2. LOOKUP — Query shared memory
        def lookup(key: str) -> Any:
            """Look up a value from shared memory"""
            return self._memory.read(key)
        self._tools["lookup"] = lookup

        # 3. STORE — Write to shared memory
        def store(key: str, value: Any, agent_id: str = "tool") -> bool:
            """Store a value in shared memory"""
            self._memory.write(agent_id, key, value)
            return True
        self._tools["store"] = store

        # 4. VALIDATE — Check a claim against HMRC rules
        def validate(claim_type: str, amount: float, context: dict = None) -> dict:
            """Validate a tax claim against known limits"""
            limits = {
                "mileage_45p": {"per_mile": 0.45, "max_miles": 10_000,
                                "reduced_rate": 0.25, "reduced_after": 10_000},
                "marriage_allowance": {"transfer": 1_260, "saving": 252},
                "trading_allowance": {"max": 1_000},
                "pension_annual": {"max": 60_000},
                "home_office_simplified": {"monthly": 26, "annual": 312},
                "phone_usage": {"typical_pct": 0.50},
                "ppe_clothing": {"typical": 200},
            }
            rule = limits.get(claim_type, {})
            if not rule:
                return {"valid": False, "reason": f"Unknown claim type: {claim_type}"}
            max_val = rule.get("max", rule.get("annual", rule.get("saving", float("inf"))))
            return {
                "valid": amount <= max_val,
                "limit": max_val,
                "rule": rule,
                "excess": max(0, amount - max_val),
            }
        self._tools["validate"] = validate

        # 5. BENCHMARK — Check against HMRC sector norms
        def benchmark(metric: str, value: float, sector: str = "construction_sub") -> dict:
            """Check a metric against HMRC sector benchmarks"""
            benchmarks = {
                "construction_sub": {
                    "gross_profit_margin": (0.40, 0.70),
                    "motor_ratio": (0.05, 0.15),
                    "admin_ratio": (0.02, 0.08),
                    "other_direct_ratio": (0.05, 0.20),
                    "net_profit_margin": (0.15, 0.40),
                    "cis_rate": (0.18, 0.22),
                },
            }
            sector_data = benchmarks.get(sector, {})
            bounds = sector_data.get(metric)
            if not bounds:
                return {"in_range": True, "message": "No benchmark available"}
            low, high = bounds
            return {
                "in_range": low <= value <= high,
                "value": value,
                "expected_low": low,
                "expected_high": high,
                "deviation": min(abs(value - low), abs(value - high)) if not (low <= value <= high) else 0,
                "message": f"{metric}: {value:.1%} ({'OK' if low <= value <= high else 'OUT OF RANGE'}) [expected {low:.0%}-{high:.0%}]"
            }
        self._tools["benchmark"] = benchmark

    def define_tool(self, name: str, fn: Callable):
        """Register a custom tool"""
        self._tools[name] = fn

    def get_tool(self, name: str) -> Optional[Callable]:
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

    def invoke(self, name: str, **kwargs) -> Any:
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")
        return tool(**kwargs)


# ═══════════════════════════════════════════════════════════════════
# HNC SYSTEM ADAPTER — Replaces LLMAdapter entirely
# ═══════════════════════════════════════════════════════════════════

class HNCSystemAdapter:
    """
    This is where we diverge from OpenMultiAgent completely.

    OpenMultiAgent has:
        LLMAdapter → AnthropicAdapter, OpenAIAdapter, CopilotAdapter

    We have:
        HNCSystemAdapter → 11 internal intelligence systems

    Each adapter wraps one of our engines and presents a uniform
    interface: prompt(input) → output. No network calls. No tokens.
    No rate limits. No API keys. Pure computation.
    """

    def __init__(self, role: AgentRole, params: dict):
        self.role = role
        self.params = params
        self._system = None

    def boot(self) -> bool:
        """Initialise the underlying HNC system"""
        try:
            self._system = self._create_system()
            return True
        except Exception as e:
            logger.warning(f"System boot failed for {self.role.value}: {e}")
            return False

    def _create_system(self):
        """Factory: create the right system for this role"""
        p = self.params

        if self.role == AgentRole.WARFARE:
            from core.hnc_tax_warfare import HNCTaxWarfare
            return HNCTaxWarfare(
                gross_income=p.get("gross_income", 51000),
                net_profit=p.get("net_profit", 25000),
                cis_deducted=p.get("cis_deducted", 10200),
                partner_income=p.get("partner_income", 0),
                mileage_estimate=p.get("mileage_estimate", 8000),
            )

        elif self.role == AgentRole.SEER:
            from core.hnc_seer import HNCSeer, MonthlySnapshot
            monthly = p.get("monthly_data", [])
            if not monthly:
                months = []
                for i in range(9):
                    m = 4 + i
                    if m > 12: m -= 12
                    months.append(MonthlySnapshot(
                        month=m, year=2025 if m >= 4 else 2026,
                        gross_income=p.get("gross_income", 51000) / 12,
                        expenses=p.get("total_expenses", 26000) / 12,
                        net_profit=p.get("net_profit", 25000) / 12,
                        cis_deducted=p.get("cis_deducted", 10200) / 12,
                    ))
                monthly = months
            return HNCSeer(monthly_data=monthly)

        elif self.role == AgentRole.SCANNER:
            from core.hnc_deep_scanner import HNCDeepScanner
            return HNCDeepScanner(tax_rate=0.20)

        elif self.role == AgentRole.LATTICE:
            from core.hnc_lattice import HNCLattice
            return HNCLattice(
                gross_income=p.get("gross_income", 51000),
                net_profit=p.get("net_profit", 25000),
                cis_deducted=p.get("cis_deducted", 10200),
            )

        elif self.role == AgentRole.CONSCIOUSNESS:
            from core.hnc_consciousness import HNCConsciousness
            return HNCConsciousness(
                turnover=p.get("gross_income", 51000),
                cost_of_sales=p.get("cost_of_sales", 8000),
                other_direct=p.get("other_direct", 5000),
                motor=p.get("motor", 3000),
                admin=p.get("admin", 2000),
                other_expenses=p.get("other_expenses", 1500),
                net_profit=p.get("net_profit", 25000),
                cis_deducted=p.get("cis_deducted", 10200),
            )

        elif self.role == AgentRole.METACOGNITION:
            from core.hnc_metacognition import HNCMetacognition
            return HNCMetacognition()

        elif self.role == AgentRole.INTELLIGENCE:
            from core.hnc_intelligence_registry import HNCIntelligenceRegistry
            return HNCIntelligenceRegistry(
                net_profit=p.get("net_profit", 25000),
                total_income=p.get("gross_income", 51000),
                total_expenses=p.get("total_expenses", 26000),
                motor_expenses=p.get("motor", 3000),
                cis_deducted=p.get("cis_deducted", 10200),
            )

        elif self.role == AgentRole.STRATEGY:
            from core.tax_strategy import TaxStrategy
            return TaxStrategy(
                net_profit=p.get("net_profit", 25000),
                total_income=p.get("gross_income", 51000),
                total_expenses=p.get("total_expenses", 26000),
                motor_expenses=p.get("motor", 3000),
                cis_deducted=p.get("cis_deducted", 10200),
            )

        elif self.role == AgentRole.THRONE:
            from core.hnc_auris_throne import get_hnc_auris_throne
            return get_hnc_auris_throne()

        elif self.role == AgentRole.AURIS_NODES:
            from core.hnc_auris_nodes import HNCAurisEngine
            return HNCAurisEngine()

        elif self.role == AgentRole.VALIDATOR:
            from core.hnc_auris_validator import HNCAurisValidator
            return HNCAurisValidator(sector="construction_subcontractor")

        else:
            raise ValueError(f"Unknown role: {self.role}")

    def prompt(self, input_data: dict = None) -> Any:
        """
        Run the system. This replaces LLM prompt() entirely.

        Instead of: "Generate a tax analysis" → LLM text output
        We do:      Run the actual calculation → structured data output
        """
        if self._system is None:
            raise RuntimeError(f"System not booted: {self.role.value}")

        p = self.params
        input_data = input_data or {}

        if self.role == AgentRole.WARFARE:
            return self._system.run_warfare_assessment()

        elif self.role == AgentRole.SEER:
            return self._system.predict()

        elif self.role == AgentRole.SCANNER:
            txns = input_data.get("transactions", p.get("transactions", []))
            if not txns:
                txns = [
                    {"date": "2025-06-01", "description": "GROVE BUILDERS CIS", "amount": 5666, "category": "income"},
                    {"date": "2025-06-05", "description": "TRAVIS PERKINS", "amount": 800, "category": "cost_of_sales"},
                    {"date": "2025-06-10", "description": "BP FUEL", "amount": 65, "category": "motor"},
                    {"date": "2025-06-15", "description": "EE MOBILE", "amount": 45, "category": "uncategorised"},
                ]
            return self._system.scan_all(txns)

        elif self.role == AgentRole.LATTICE:
            return self._system.find_optimum()

        elif self.role == AgentRole.CONSCIOUSNESS:
            return self._system.assess()

        elif self.role == AgentRole.METACOGNITION:
            return self._system.analyse_full_position(
                net_profit=p.get("net_profit", 25000),
                total_income=p.get("gross_income", 51000),
                total_expenses=p.get("total_expenses", 26000),
                motor_expenses=p.get("motor", 3000),
                cis_deducted=p.get("cis_deducted", 10200),
                cis_citb=0,
                drawings=0,
            )

        elif self.role == AgentRole.INTELLIGENCE:
            return self._system.run_all_systems()

        elif self.role == AgentRole.STRATEGY:
            return self._system.run_all_strategies()

        elif self.role == AgentRole.THRONE:
            return self._system.assess()

        elif self.role == AgentRole.AURIS_NODES:
            desc = input_data.get("description", "GROVE BUILDERS CIS PAYMENT")
            amount = input_data.get("amount", 5666.67)
            return self._system.classify(
                description=desc, amount=amount,
                turnover=p.get("gross_income", 51000),
                balance=p.get("net_profit", 25000),
            )

        elif self.role == AgentRole.VALIDATOR:
            return self._system.validate_return(
                turnover=p.get("gross_income", 51000),
                cost_of_sales=p.get("cost_of_sales", 8000),
                other_direct=p.get("other_direct", 5000),
                motor=p.get("motor", 3000),
                admin=p.get("admin", 2000),
                other_expenses=p.get("other_expenses", 1500),
                net_profit=p.get("net_profit", 25000),
                cis_deducted=p.get("cis_deducted", 10200),
            )

    def stream(self, input_data: dict = None):
        """
        Streaming interface. For LLMs this yields tokens.
        For us this yields intermediate computation steps.
        """
        yield {"phase": "boot", "system": self.role.value}
        result = self.prompt(input_data)
        yield {"phase": "complete", "system": self.role.value, "result": result}


# ═══════════════════════════════════════════════════════════════════
# AGENT — Individual intelligence unit
# ═══════════════════════════════════════════════════════════════════

class HNCAgent:
    """
    A single agent. Wraps one HNCSystemAdapter.
    Replaces the OpenMultiAgent Agent class.

    Methods: run(), prompt(), stream()
    """

    def __init__(self, config: AgentConfig, adapter: HNCSystemAdapter,
                 message_bus: MessageBus, shared_memory: SharedMemory,
                 tool_registry: ToolRegistry):
        self.config = config
        self.adapter = adapter
        self.bus = message_bus
        self.memory = shared_memory
        self.tools = tool_registry
        self._inbox: queue.Queue = queue.Queue()

        # Subscribe to messages
        self.bus.subscribe(config.agent_id, lambda msg: self._inbox.put(msg))

    def run(self, input_data: dict = None) -> AgentResult:
        """Execute this agent's full cycle"""
        start = time.time()
        try:
            # Boot system
            if not self.adapter.boot():
                return AgentResult(
                    agent_id=self.config.agent_id,
                    role=self.config.role,
                    success=False,
                    error=f"Failed to boot {self.config.role.value}",
                )

            # Run computation
            result = self.adapter.prompt(input_data)

            # Store result in shared memory
            self.memory.write(
                self.config.agent_id,
                f"result_{self.config.role.value}",
                result,
            )

            # Broadcast completion
            self.bus.publish(Message(
                msg_id=str(uuid.uuid4()),
                msg_type=MessageType.RESULT,
                sender=self.config.agent_id,
                receiver="*",
                payload={"role": self.config.role.value, "success": True},
            ))

            elapsed = time.time() - start
            return AgentResult(
                agent_id=self.config.agent_id,
                role=self.config.role,
                success=True,
                data=result,
                execution_time=round(elapsed, 3),
                signals_emitted=1,
            )

        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"Agent {self.config.agent_id} failed: {e}")

            # Broadcast failure
            self.bus.publish(Message(
                msg_id=str(uuid.uuid4()),
                msg_type=MessageType.ALERT,
                sender=self.config.agent_id,
                receiver="*",
                payload={"role": self.config.role.value, "error": str(e)},
            ))

            return AgentResult(
                agent_id=self.config.agent_id,
                role=self.config.role,
                success=False,
                error=str(e),
                execution_time=round(elapsed, 3),
            )

    def prompt(self, input_data: dict = None) -> Any:
        """Direct prompt — bypass the full run cycle"""
        if not self.adapter._system:
            self.adapter.boot()
        return self.adapter.prompt(input_data)

    def stream(self, input_data: dict = None):
        """Stream intermediate results"""
        return self.adapter.stream(input_data)


# ═══════════════════════════════════════════════════════════════════
# AGENT RUNNER — Conversation loop + tool dispatch
# ═══════════════════════════════════════════════════════════════════

class AgentRunner:
    """
    Runs an agent with a conversation loop.
    In OpenMultiAgent, this handles LLM back-and-forth.
    In HNC, this handles multi-step computation chains:
      1. Run the agent
      2. Check if tools need to be invoked
      3. Feed tool results back
      4. Repeat until convergence

    The "conversation" is between the agent and the ToolRegistry,
    not between a human and an LLM.
    """

    def __init__(self, agent: HNCAgent, tools: ToolRegistry,
                 max_iterations: int = 5):
        self.agent = agent
        self.tools = tools
        self.max_iterations = max_iterations
        self.conversation_log: List[dict] = []

    def run_with_tools(self, input_data: dict = None) -> AgentResult:
        """
        Run the agent in a tool-dispatch loop.
        The agent runs → produces output → if output references tools
        → dispatch tools → feed results back → re-run.
        """
        iteration = 0
        current_input = input_data or {}
        last_result = None

        while iteration < self.max_iterations:
            iteration += 1

            # Run the agent
            result = self.agent.run(current_input)
            last_result = result

            self.conversation_log.append({
                "iteration": iteration,
                "agent": self.agent.config.agent_id,
                "success": result.success,
                "has_data": result.data is not None,
            })

            if not result.success:
                break

            # Check if the result requests tool invocations
            tool_requests = self._extract_tool_requests(result.data)
            if not tool_requests:
                break  # No tools needed — we're done

            # Dispatch tools
            tool_results = {}
            for tool_name, tool_args in tool_requests:
                try:
                    tool_result = self.tools.invoke(tool_name, **tool_args)
                    tool_results[tool_name] = tool_result
                except Exception as e:
                    tool_results[tool_name] = {"error": str(e)}

            # Feed tool results back as input for next iteration
            current_input["tool_results"] = tool_results

        return last_result

    def _extract_tool_requests(self, data: Any) -> List[Tuple[str, dict]]:
        """
        Check if agent output contains tool invocation requests.
        Convention: if result has a 'tool_requests' key, it's a list
        of (tool_name, kwargs) tuples.
        """
        if isinstance(data, dict) and "tool_requests" in data:
            return data["tool_requests"]
        return []


# ═══════════════════════════════════════════════════════════════════
# TASK QUEUE — Dependency graph with auto-unblock
# ═══════════════════════════════════════════════════════════════════

class TaskQueue:
    """
    Manages task dependencies. Tasks only run when their
    dependencies are satisfied. Failed tasks cascade to dependents.

    dependency graph: Task A → Task B means B waits for A
    auto unblock: When A completes, B is unblocked
    cascade failure: When A fails, B is cancelled
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._tasks: Dict[str, TaskNode] = {}

    def add_task(self, task: TaskNode):
        with self._lock:
            self._tasks[task.task_id] = task

    def get_ready_tasks(self) -> List[TaskNode]:
        """Get all tasks whose dependencies are satisfied"""
        with self._lock:
            ready = []
            for task in self._tasks.values():
                if task.status != TaskStatus.PENDING:
                    continue
                # Check all dependencies are completed
                deps_met = all(
                    self._tasks.get(dep_id, TaskNode(task_id="", agent_id="")).status == TaskStatus.COMPLETED
                    for dep_id in task.depends_on
                )
                if deps_met:
                    ready.append(task)
            return ready

    def mark_running(self, task_id: str):
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].status = TaskStatus.RUNNING
                self._tasks[task_id].started_at = time.time()

    def mark_completed(self, task_id: str, result: Any = None):
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].status = TaskStatus.COMPLETED
                self._tasks[task_id].result = result
                self._tasks[task_id].completed_at = time.time()

    def mark_failed(self, task_id: str, error: str = ""):
        """Mark failed and CASCADE to dependents"""
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].status = TaskStatus.FAILED
                self._tasks[task_id].error = error
                self._tasks[task_id].completed_at = time.time()
                # Cascade: cancel all tasks that depend on this one
                self._cascade_failure(task_id)

    def _cascade_failure(self, failed_id: str):
        """Cancel all downstream tasks"""
        for task in self._tasks.values():
            if failed_id in task.depends_on and task.status == TaskStatus.PENDING:
                task.status = TaskStatus.CANCELLED
                task.error = f"Cancelled: dependency {failed_id} failed"
                # Recursive cascade
                self._cascade_failure(task.task_id)

    def all_done(self) -> bool:
        with self._lock:
            return all(
                t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
                for t in self._tasks.values()
            )

    def get_status(self) -> Dict[str, str]:
        with self._lock:
            return {tid: t.status.value for tid, t in self._tasks.items()}

    def get_results(self) -> Dict[str, Any]:
        with self._lock:
            return {tid: t.result for tid, t in self._tasks.items()
                    if t.status == TaskStatus.COMPLETED}


# ═══════════════════════════════════════════════════════════════════
# AGENT POOL — Parallel execution with semaphore
# ═══════════════════════════════════════════════════════════════════

class AgentPool:
    """
    Manages parallel agent execution.
    Semaphore controls max concurrency.
    """

    def __init__(self, max_parallel: int = 4):
        self.max_parallel = max_parallel
        self._semaphore = threading.Semaphore(max_parallel)

    def run_parallel(self, agents: List[HNCAgent],
                     input_data: dict = None) -> List[AgentResult]:
        """Run multiple agents in parallel, respecting concurrency limit"""
        results = []

        with ThreadPoolExecutor(max_workers=self.max_parallel) as executor:
            futures = {}
            for agent in agents:
                future = executor.submit(self._run_with_semaphore, agent, input_data)
                futures[future] = agent.config.agent_id

            for future in as_completed(futures):
                agent_id = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(AgentResult(
                        agent_id=agent_id,
                        role=AgentRole.WARFARE,  # placeholder
                        success=False,
                        error=str(e),
                    ))

        return results

    def _run_with_semaphore(self, agent: HNCAgent, input_data: dict = None) -> AgentResult:
        self._semaphore.acquire()
        try:
            return agent.run(input_data)
        finally:
            self._semaphore.release()


# ═══════════════════════════════════════════════════════════════════
# HNC TEAM — Collection of agents working together
# ═══════════════════════════════════════════════════════════════════

class HNCTeam:
    """
    A team of agents configured to work together.
    Contains: AgentConfig[], MessageBus, TaskQueue, SharedMemory
    """

    def __init__(self, name: str, params: dict):
        self.name = name
        self.params = params
        self.message_bus = MessageBus()
        self.shared_memory = SharedMemory()
        self.task_queue = TaskQueue()
        self.tool_registry = ToolRegistry(self.shared_memory)
        self.agents: Dict[str, HNCAgent] = {}
        self.configs: List[AgentConfig] = []
        self.pool = AgentPool(max_parallel=4)

    def add_agent(self, config: AgentConfig) -> HNCAgent:
        """Add an agent to the team"""
        adapter = HNCSystemAdapter(role=config.role, params=self.params)
        agent = HNCAgent(
            config=config,
            adapter=adapter,
            message_bus=self.message_bus,
            shared_memory=self.shared_memory,
            tool_registry=self.tool_registry,
        )
        self.agents[config.agent_id] = agent
        self.configs.append(config)

        # Add corresponding task to the queue
        self.task_queue.add_task(TaskNode(
            task_id=config.agent_id,
            agent_id=config.agent_id,
            depends_on=config.depends_on,
        ))

        return agent

    def run(self) -> Dict[str, AgentResult]:
        """
        Run all agents respecting dependency order.
        Uses the TaskQueue for ordering and AgentPool for parallelism.
        """
        all_results: Dict[str, AgentResult] = {}

        while not self.task_queue.all_done():
            ready = self.task_queue.get_ready_tasks()
            if not ready:
                # Deadlock detection
                status = self.task_queue.get_status()
                pending = [k for k, v in status.items() if v == "pending"]
                if pending:
                    logger.error(f"Deadlock detected: {pending}")
                    for tid in pending:
                        self.task_queue.mark_failed(tid, "Deadlock — circular dependency?")
                break

            # Mark them running
            for task in ready:
                self.task_queue.mark_running(task.task_id)

            # Get the agent objects
            agents_to_run = [
                self.agents[task.task_id]
                for task in ready
                if task.task_id in self.agents
            ]

            # Run in parallel
            results = self.pool.run_parallel(agents_to_run)

            # Process results
            for result in results:
                all_results[result.agent_id] = result
                if result.success:
                    self.task_queue.mark_completed(result.agent_id, result.data)
                else:
                    self.task_queue.mark_failed(result.agent_id, result.error)

        return all_results


# ═══════════════════════════════════════════════════════════════════
# HNC MULTI-AGENT — The Orchestrator
# ═══════════════════════════════════════════════════════════════════

class HNCMultiAgent:
    """
    The top-level orchestrator. Replaces OpenMultiAgent.

    Methods:
        createTeam()   — Build a team of agents
        runTeam()      — Execute all agents in dependency order
        runTasks()     — Run specific tasks
        runAgent()     — Run a single agent
        getStatus()    — Get system-wide status
    """

    def __init__(self, params: dict = None):
        self.params = params or self._default_params()
        self.teams: Dict[str, HNCTeam] = {}
        self._results_cache: Dict[str, Dict[str, AgentResult]] = {}

    def _default_params(self) -> dict:
        return {
            "gross_income": 51_000,
            "net_profit": 25_000,
            "cis_deducted": 10_200,
            "total_expenses": 26_000,
            "cost_of_sales": 8_000,
            "other_direct": 5_000,
            "motor": 3_000,
            "admin": 2_000,
            "other_expenses": 1_500,
            "partner_income": 0,
            "mileage_estimate": 8_000,
        }

    def createTeam(self, name: str = "default",
                   roles: List[AgentRole] = None) -> HNCTeam:
        """
        Create a team of agents.
        By default, creates the full 11-system team.
        """
        team = HNCTeam(name=name, params=self.params)

        if roles is None:
            roles = list(AgentRole)
            # Exclude abstract roles that don't have adapters
            roles = [r for r in roles if r not in (AgentRole.QUEEN, AgentRole.NEXUS)]

        # Define the dependency graph
        # Phase 1: Independent systems (can run in parallel)
        phase1 = {AgentRole.WARFARE, AgentRole.SEER, AgentRole.SCANNER,
                  AgentRole.METACOGNITION, AgentRole.INTELLIGENCE,
                  AgentRole.STRATEGY, AgentRole.THRONE, AgentRole.AURIS_NODES}

        # Phase 2: Depends on Phase 1 outputs
        phase2_deps = {
            AgentRole.LATTICE: [],  # Can also run independently
            AgentRole.CONSCIOUSNESS: [],  # Can also run independently
            AgentRole.VALIDATOR: [],  # Can also run independently
        }

        for i, role in enumerate(roles):
            depends = []
            if role in phase2_deps:
                # Phase 2 agents depend on all phase 1 agents that are in the team
                depends = [
                    f"agent_{r.value}"
                    for r in phase1
                    if r in roles
                ]

            config = AgentConfig(
                agent_id=f"agent_{role.value}",
                role=role,
                name=role.value.replace("_", " ").title(),
                priority=1 if role in phase1 else 5,
                depends_on=depends,
            )
            team.add_agent(config)

        self.teams[name] = team
        return team

    def runTeam(self, name: str = "default") -> Dict[str, AgentResult]:
        """Run all agents in a team"""
        team = self.teams.get(name)
        if not team:
            raise ValueError(f"Team not found: {name}")

        print(f"\n{'=' * 70}")
        print(f"HNC MULTI-AGENT — TEAM '{name.upper()}' EXECUTING")
        print(f"Agents: {len(team.agents)} | Max Parallel: {team.pool.max_parallel}")
        print(f"{'=' * 70}")

        results = team.run()
        self._results_cache[name] = results

        # Summary
        ok = sum(1 for r in results.values() if r.success)
        fail = sum(1 for r in results.values() if not r.success)
        total_time = sum(r.execution_time for r in results.values())

        print(f"\n{'─' * 70}")
        print(f"TEAM EXECUTION COMPLETE")
        print(f"  Success: {ok}/{ok + fail}")
        print(f"  Total compute time: {total_time:.2f}s")
        print(f"  (Parallel — wall clock is lower)")
        print(f"{'─' * 70}")

        for agent_id, result in sorted(results.items()):
            status = "OK" if result.success else f"FAIL: {result.error[:50]}"
            print(f"  {result.role.value:20s} [{status}] ({result.execution_time:.3f}s)")

        return results

    def runTasks(self, task_ids: List[str], team_name: str = "default") -> Dict[str, AgentResult]:
        """Run specific tasks from a team"""
        team = self.teams.get(team_name)
        if not team:
            raise ValueError(f"Team not found: {team_name}")

        results = {}
        agents = [team.agents[tid] for tid in task_ids if tid in team.agents]
        agent_results = team.pool.run_parallel(agents)
        for r in agent_results:
            results[r.agent_id] = r
        return results

    def runAgent(self, agent_id: str, team_name: str = "default",
                 input_data: dict = None) -> AgentResult:
        """Run a single agent"""
        team = self.teams.get(team_name)
        if not team or agent_id not in team.agents:
            raise ValueError(f"Agent not found: {agent_id}")
        return team.agents[agent_id].run(input_data)

    def getStatus(self, team_name: str = "default") -> dict:
        """Get comprehensive status of the multi-agent system"""
        team = self.teams.get(team_name)
        if not team:
            return {"error": f"Team not found: {team_name}"}

        cached = self._results_cache.get(team_name, {})

        return {
            "team": team_name,
            "agents": len(team.agents),
            "task_status": team.task_queue.get_status(),
            "shared_memory_keys": list(team.shared_memory.read_all().keys()),
            "message_count": len(team.message_bus.get_log()),
            "tools_available": team.tool_registry.list_tools(),
            "results": {
                aid: {
                    "role": r.role.value,
                    "success": r.success,
                    "time": r.execution_time,
                    "error": r.error or None,
                }
                for aid, r in cached.items()
            },
        }


# ═══════════════════════════════════════════════════════════════════
# DEMO / TEST
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    print("\n" + "=" * 70)
    print("HNC MULTI-AGENT SYSTEM")
    print("11 Internal Systems. 0 External Dependencies. 1 Verdict.")
    print("Fully In-House. No LLMs. Pure Computation.")
    print("=" * 70)

    # Create the orchestrator with Gary's real position
    orchestrator = HNCMultiAgent(params={
        "gross_income": 51_000,
        "net_profit": 25_000,
        "cis_deducted": 10_200,
        "total_expenses": 26_000,
        "cost_of_sales": 8_000,
        "other_direct": 5_000,
        "motor": 3_000,
        "admin": 2_000,
        "other_expenses": 1_500,
        "partner_income": 0,
        "mileage_estimate": 8_000,
    })

    # Create the team (all 11 systems)
    team = orchestrator.createTeam("tax_warfare_team")
    print(f"\nTeam created: {len(team.agents)} agents")
    print(f"Tools available: {team.tool_registry.list_tools()}")

    # Run the team
    results = orchestrator.runTeam("tax_warfare_team")

    # Get status
    status = orchestrator.getStatus("tax_warfare_team")
    print(f"\n{'=' * 70}")
    print("SYSTEM STATUS")
    print(f"{'=' * 70}")
    print(f"  Agents: {status['agents']}")
    print(f"  Memory keys: {len(status['shared_memory_keys'])}")
    print(f"  Messages exchanged: {status['message_count']}")
    print(f"  Tools: {status['tools_available']}")

    # Pull key results from shared memory
    print(f"\n{'=' * 70}")
    print("SHARED MEMORY — CROSS-AGENT INTELLIGENCE")
    print(f"{'=' * 70}")
    memory = team.shared_memory.read_all()
    for key, value in sorted(memory.items()):
        vtype = type(value).__name__
        print(f"  {key:40s} [{vtype}]")

    print(f"\n{'─' * 70}")
    print("Architecture: OpenMultiAgent pattern, fully in-house")
    print("No LLM APIs. No tokens. No rate limits. Pure tax intelligence.")
    print(f"{'─' * 70}")
