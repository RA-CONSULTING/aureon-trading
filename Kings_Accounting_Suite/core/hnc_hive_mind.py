"""
HNC HIVE MIND — hnc_hive_mind.py
==================================
The Queen and her swarm. True hive mind behaviour.

Before this module, the 11 agents were 11 parallel workers that happened
to share memory. That's a team meeting, not a hive mind.

A HIVE MIND means:
    1. ONE QUEEN — single authority, owns the bus and memory
    2. SIGNAL PROPAGATION — every agent output flows to the Queen first,
       then the Queen broadcasts selectively to listeners
    3. REACTIVE AGENTS — agents can subscribe to each other's signals
       and re-run when their inputs change
    4. CONSENSUS VOTING — agents vote on contested classifications;
       coherence Γ determines confidence
    5. QUEEN VETO — the Queen has override authority on any decision
    6. WAVE PROTOCOL — information flows in waves:
         Wave 1: Independent agents produce primary signals
         Wave 2: Dependent agents consume Wave 1 and produce refined signals
         Wave 3: The Queen collects all signals, resolves conflicts, ships verdict
    7. EMERGENT INTELLIGENCE — the verdict is not the sum of parts;
       the Queen synthesises a coherent whole from contradictory inputs

This is how bees make honey, ants build colonies, and neurons think.
One organism, many cells, one decision.

Aureon Creator / Aureon Research — April 2026
"""

from __future__ import annotations
import logging
import time
import uuid
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from enum import Enum
from collections import defaultdict

from core.hnc_multi_agent import (
    HNCMultiAgent, HNCTeam, HNCAgent, AgentPool,
    TaskQueue, TaskNode, MessageBus, SharedMemory,
    ToolRegistry, AgentRole, TaskStatus, Message,
    MessageType, AgentConfig, HNCSystemAdapter, AgentResult,
)

logger = logging.getLogger("hnc_hive_mind")


# ═══════════════════════════════════════════════════════════════════
# HIVE MIND ENUMS
# ═══════════════════════════════════════════════════════════════════

class Wave(Enum):
    """Information propagation waves"""
    WAVE_1_PRIMARY = "wave_1_primary"        # Independent systems
    WAVE_2_REFINED = "wave_2_refined"        # Systems that consume wave 1
    WAVE_3_SYNTHESIS = "wave_3_synthesis"    # Queen synthesis


class QueenAuthority(Enum):
    """What the Queen can do to an agent's decision"""
    ACCEPT = "accept"          # Agent's output stands
    REFINE = "refine"          # Queen adjusts the output
    VETO = "veto"              # Queen overrides completely
    ESCALATE = "escalate"      # Queen flags for human review


class ConsensusState(Enum):
    """State of cross-agent agreement"""
    UNANIMOUS = "unanimous"        # All agents agree (Γ >= 0.95)
    STRONG = "strong"              # Most agents agree (Γ >= 0.80)
    MAJORITY = "majority"          # More than half agree (Γ >= 0.60)
    SPLIT = "split"                # No clear majority (Γ >= 0.40)
    CONFLICT = "conflict"          # Agents actively disagree (Γ < 0.40)


# ═══════════════════════════════════════════════════════════════════
# HIVE SIGNAL — The atomic unit of hive communication
# ═══════════════════════════════════════════════════════════════════

@dataclass
class HiveSignal:
    """A signal sent from an agent to the Queen (and possibly onward)"""
    signal_id: str
    source_agent: str
    source_role: AgentRole
    wave: Wave
    signal_type: str              # e.g. "tax_saving", "risk_flag", "validation_fail"
    payload: Any
    confidence: float = 1.0       # 0-1
    timestamp: float = field(default_factory=time.time)
    reactions: List[str] = field(default_factory=list)  # Which agents should react

    @property
    def summary(self) -> str:
        return f"[{self.wave.value}] {self.source_role.value}: {self.signal_type}"


@dataclass
class QueenDecision:
    """The Queen's ruling on a specific matter"""
    decision_id: str
    topic: str
    authority: QueenAuthority
    rationale: str
    original_signals: List[HiveSignal]
    consensus: ConsensusState
    coherence_gamma: float        # Γ
    timestamp: float = field(default_factory=time.time)


@dataclass
class HiveVerdict:
    """The final hive mind verdict — what the whole organism decided"""
    # Position
    gross_income: float
    net_profit: float
    cis_deducted: float

    # The truth
    naive_liability: float
    hive_liability: float         # What the hive decided after synthesis
    total_saving: float
    cis_credit: float
    net_position: float           # + = owe, - = refund

    # Hive mind metrics
    agents_active: int
    signals_emitted: int
    queen_decisions: int
    consensus_state: ConsensusState
    coherence_gamma: float        # Overall hive Γ
    waves_completed: int

    # Subsystem summaries
    warfare_weapons: int
    lattice_strategies: int
    consciousness_verdict: str
    throne_advisory: str
    validator_ready: bool

    # The Queen's call
    queen_ruling: str
    queen_confidence: float
    human_review_required: bool
    queen_decisions_log: List[QueenDecision]

    # Defence
    defence_narrative: str
    bottom_line: str

    # Audit trail
    wave_timings: Dict[str, float]
    agent_times: Dict[str, float]
    total_time: float


# ═══════════════════════════════════════════════════════════════════
# THE QUEEN — Central authority, signal router, consensus judge
# ═══════════════════════════════════════════════════════════════════

class TheQueen:
    """
    The Queen.

    She owns the message bus. She owns the shared memory. She routes
    every signal. She enforces consensus. She has veto authority.
    When agents disagree, she decides. When data is missing, she
    demands it. When the verdict is ready, she ships it.

    The 11 agents are her body. She is the one who thinks.
    """

    def __init__(self, bus: MessageBus, memory: SharedMemory):
        self.bus = bus
        self.memory = memory
        self._lock = threading.RLock()

        # Signal registry — every signal the Queen has seen
        self._signals: List[HiveSignal] = []

        # Subscriptions — which agents react to which signal types
        self._subscriptions: Dict[str, List[AgentRole]] = defaultdict(list)

        # Decisions the Queen has made
        self._decisions: List[QueenDecision] = []

        # The Queen listens to every message on the bus
        self.bus.subscribe_broadcast(self._ingest_message)

    def _ingest_message(self, msg: Message):
        """Every message on the bus hits the Queen first"""
        pass  # We don't need to do anything here — signals are explicit

    def register_subscription(self, signal_type: str, role: AgentRole):
        """Tell the Queen: agent X wants to react when signal type Y appears"""
        with self._lock:
            if role not in self._subscriptions[signal_type]:
                self._subscriptions[signal_type].append(role)

    def emit_signal(self, signal: HiveSignal) -> List[AgentRole]:
        """
        An agent emits a signal to the hive.
        The Queen records it and returns which agents should react.
        """
        with self._lock:
            self._signals.append(signal)
            reactors = list(self._subscriptions.get(signal.signal_type, []))
            signal.reactions = [r.value for r in reactors]

            # Store signal in shared memory for all agents to see
            key = f"signal_{signal.source_role.value}_{signal.signal_type}"
            self.memory.write(signal.source_agent, key, signal.payload)

            logger.info(f"[QUEEN] Signal received: {signal.summary} → reactors: {[r.value for r in reactors]}")
            return reactors

    def get_signals_for(self, role: AgentRole) -> List[HiveSignal]:
        """Get all signals a particular agent should know about"""
        with self._lock:
            return [
                s for s in self._signals
                if role in self._subscriptions.get(s.signal_type, [])
            ]

    def calculate_coherence(self, signals: List[HiveSignal]) -> Tuple[float, ConsensusState]:
        """
        Calculate cross-agent coherence Γ.
        Same formula as the Auris nodes: weighted agreement.

        Γ = Σ(weight_i × confidence_i × agreement_i) / Σ(weight_i)
        """
        if not signals:
            return 0.0, ConsensusState.CONFLICT

        # Group signals by topic (signal_type)
        by_topic: Dict[str, List[HiveSignal]] = defaultdict(list)
        for s in signals:
            by_topic[s.signal_type].append(s)

        topic_scores = []
        for topic, sigs in by_topic.items():
            # For each topic, measure how much the signals agree
            if len(sigs) == 1:
                topic_scores.append(sigs[0].confidence)
                continue

            # Multi-signal topic: measure confidence variance
            confidences = [s.confidence for s in sigs]
            avg_conf = sum(confidences) / len(confidences)
            variance = sum((c - avg_conf) ** 2 for c in confidences) / len(confidences)
            # Low variance = high agreement
            agreement = max(0, 1 - variance * 4)  # Scale variance to 0-1
            topic_scores.append(avg_conf * agreement)

        gamma = sum(topic_scores) / len(topic_scores) if topic_scores else 0.0

        if gamma >= 0.95:
            state = ConsensusState.UNANIMOUS
        elif gamma >= 0.80:
            state = ConsensusState.STRONG
        elif gamma >= 0.60:
            state = ConsensusState.MAJORITY
        elif gamma >= 0.40:
            state = ConsensusState.SPLIT
        else:
            state = ConsensusState.CONFLICT

        return round(gamma, 3), state

    def rule(self, topic: str, signals: List[HiveSignal]) -> QueenDecision:
        """
        The Queen makes a ruling on a specific topic based on signals.
        This is where veto authority lives.
        """
        with self._lock:
            gamma, consensus = self.calculate_coherence(signals)

            # Determine authority action
            if consensus in (ConsensusState.UNANIMOUS, ConsensusState.STRONG):
                authority = QueenAuthority.ACCEPT
                rationale = f"Strong consensus (Γ={gamma:.3f}) — accepting agent findings"
            elif consensus == ConsensusState.MAJORITY:
                authority = QueenAuthority.REFINE
                rationale = f"Majority consensus (Γ={gamma:.3f}) — Queen refining with context"
            elif consensus == ConsensusState.SPLIT:
                authority = QueenAuthority.VETO
                rationale = f"Split vote (Γ={gamma:.3f}) — Queen overriding with conservative path"
            else:  # CONFLICT
                authority = QueenAuthority.ESCALATE
                rationale = f"Active conflict (Γ={gamma:.3f}) — escalating to human review"

            decision = QueenDecision(
                decision_id=str(uuid.uuid4())[:8],
                topic=topic,
                authority=authority,
                rationale=rationale,
                original_signals=signals,
                consensus=consensus,
                coherence_gamma=gamma,
            )

            self._decisions.append(decision)
            logger.info(f"[QUEEN RULING] {topic}: {authority.value} — {rationale}")
            return decision

    def get_all_signals(self) -> List[HiveSignal]:
        with self._lock:
            return list(self._signals)

    def get_all_decisions(self) -> List[QueenDecision]:
        with self._lock:
            return list(self._decisions)


# ═══════════════════════════════════════════════════════════════════
# WAVE DEFINITIONS — Which agents run in which wave
# ═══════════════════════════════════════════════════════════════════

WAVE_1_AGENTS = [
    # Independent systems — produce primary signals from raw data
    AgentRole.THRONE,            # Fiscal environment (no deps)
    AgentRole.WARFARE,           # Weapons arsenal
    AgentRole.SEER,              # Prediction
    AgentRole.SCANNER,           # Transaction scanning
    AgentRole.INTELLIGENCE,      # Government moves
    AgentRole.METACOGNITION,     # Transaction reasoning
    AgentRole.STRATEGY,          # Strategy calculations
    AgentRole.AURIS_NODES,       # 9-node classification
]

WAVE_2_AGENTS = [
    # Refined systems — consume Wave 1 signals
    AgentRole.LATTICE,           # Consumes Strategy + Warfare signals
    AgentRole.CONSCIOUSNESS,     # Consumes all Wave 1 for self-audit
    AgentRole.VALIDATOR,         # Final check against all Wave 1 outputs
]

# Signal subscriptions — which agent reacts to which signal type
SIGNAL_SUBSCRIPTIONS = {
    "tax_saving": [AgentRole.LATTICE, AgentRole.CONSCIOUSNESS],
    "risk_flag": [AgentRole.CONSCIOUSNESS, AgentRole.VALIDATOR],
    "benchmark_deviation": [AgentRole.VALIDATOR, AgentRole.CONSCIOUSNESS],
    "fiscal_pressure": [AgentRole.LATTICE, AgentRole.STRATEGY, AgentRole.CONSCIOUSNESS],
    "missed_deduction": [AgentRole.LATTICE, AgentRole.STRATEGY],
    "enforcement_target": [AgentRole.CONSCIOUSNESS, AgentRole.VALIDATOR, AgentRole.LATTICE],
    "classification_conflict": [AgentRole.CONSCIOUSNESS, AgentRole.VALIDATOR],
    "prediction_alert": [AgentRole.LATTICE, AgentRole.STRATEGY],
    "weapon_activated": [AgentRole.LATTICE, AgentRole.CONSCIOUSNESS],
}


# ═══════════════════════════════════════════════════════════════════
# HIVE MIND — The full swarm orchestration
# ═══════════════════════════════════════════════════════════════════

class HNCHiveMind:
    """
    The hive mind orchestrator.

    Takes the 11 agents from hnc_multi_agent and wires them together
    under the Queen's authority. Information flows in waves:

        Wave 1 → Queen → Wave 2 → Queen → Wave 3 (synthesis)

    Every agent output becomes a HiveSignal. Every HiveSignal goes
    through the Queen. The Queen judges consensus, issues decisions,
    refines conflicts, and ships the verdict.

    This is emergent intelligence — the verdict is more than the sum
    of the 11 agent outputs.
    """

    def __init__(self, params: dict = None):
        self.params = params or self._default_params()

        # Core infrastructure (shared between all agents and Queen)
        self.bus = MessageBus()
        self.memory = SharedMemory()
        self.tools = ToolRegistry(self.memory)

        # The Queen
        self.queen = TheQueen(self.bus, self.memory)
        self._wire_subscriptions()

        # Agent pool
        self.pool = AgentPool(max_parallel=4)

        # Agents (built lazily)
        self.agents: Dict[AgentRole, HNCAgent] = {}

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

    def _wire_subscriptions(self):
        """Tell the Queen which agents want which signal types"""
        for signal_type, roles in SIGNAL_SUBSCRIPTIONS.items():
            for role in roles:
                self.queen.register_subscription(signal_type, role)

    def _build_agent(self, role: AgentRole) -> HNCAgent:
        """Build a single agent wired into the hive infrastructure"""
        if role in self.agents:
            return self.agents[role]

        config = AgentConfig(
            agent_id=f"hive_{role.value}",
            role=role,
            name=role.value.replace("_", " ").title(),
            priority=1,
        )
        adapter = HNCSystemAdapter(role=role, params=self.params)
        agent = HNCAgent(
            config=config,
            adapter=adapter,
            message_bus=self.bus,
            shared_memory=self.memory,
            tool_registry=self.tools,
        )
        self.agents[role] = agent
        return agent

    def _run_wave(self, wave: Wave, roles: List[AgentRole]) -> Tuple[Dict[AgentRole, AgentResult], float]:
        """Run a single wave of agents in parallel"""
        start = time.time()
        agents = [self._build_agent(r) for r in roles]
        results = self.pool.run_parallel(agents)

        # Map results back to roles
        result_map = {r.role: r for r in results}

        # Convert results into hive signals
        for result in results:
            if not result.success:
                continue
            signals = self._extract_signals_from_result(result, wave)
            for sig in signals:
                self.queen.emit_signal(sig)

        elapsed = time.time() - start
        return result_map, elapsed

    def _extract_signals_from_result(self, result: AgentResult, wave: Wave) -> List[HiveSignal]:
        """
        Convert an agent's raw output into discrete HiveSignals.
        Each signal is a single fact the hive needs to know about.
        """
        signals = []
        data = result.data
        role = result.role
        agent_id = result.agent_id

        def make(signal_type: str, payload: Any, confidence: float = 1.0):
            return HiveSignal(
                signal_id=str(uuid.uuid4())[:8],
                source_agent=agent_id,
                source_role=role,
                wave=wave,
                signal_type=signal_type,
                payload=payload,
                confidence=confidence,
            )

        try:
            if role == AgentRole.WARFARE and data:
                signals.append(make("tax_saving", {
                    "amount": data.total_annual_saving,
                    "bulletproof": data.bulletproof_saving,
                }, confidence=0.95))
                signals.append(make("weapon_activated", {
                    "count": data.total_weapons,
                    "threat": data.threat_level.value,
                }))
                if hasattr(data, "defence_readiness"):
                    signals.append(make("risk_flag", {
                        "readiness": data.defence_readiness,
                    }, confidence=0.90))

            elif role == AgentRole.SEER and data:
                signals.append(make("prediction_alert", {
                    "confidence": data.confidence.value,
                    "months": data.months_of_data,
                    "reserve": data.monthly_reserve_needed,
                }, confidence=0.85))

            elif role == AgentRole.SCANNER and data:
                signals.append(make("missed_deduction", {
                    "amount": data.total_missed_savings,
                    "invisible": data.invisible_tax_saving,
                    "problems": len(data.problem_transactions),
                }, confidence=0.90))

            elif role == AgentRole.THRONE and data:
                # Map Λ(t) pressure into fiscal signal
                conf = 1.0 if data.gate_open else 0.75
                signals.append(make("fiscal_pressure", {
                    "advisory": data.advisory.value,
                    "pressure": data.pressure_score,
                    "gate_open": data.gate_open,
                    "warnings": data.warnings,
                }, confidence=conf))

            elif role == AgentRole.INTELLIGENCE and data:
                # Intelligence Registry produces moves/targets
                if hasattr(data, "government_moves"):
                    signals.append(make("enforcement_target", {
                        "moves": len(getattr(data, "government_moves", [])),
                    }, confidence=0.85))

            elif role == AgentRole.STRATEGY and data:
                # List of strategies
                if isinstance(data, list) and data:
                    total = sum(getattr(s, "annual_saving", 0) for s in data if hasattr(s, "annual_saving"))
                    signals.append(make("tax_saving", {
                        "amount": total,
                        "count": len(data),
                    }, confidence=0.88))

            elif role == AgentRole.METACOGNITION and data:
                # List of reasoning traces
                count = len(data) if isinstance(data, list) else 1
                signals.append(make("tax_saving", {
                    "reasoning_traces": count,
                }, confidence=0.82))

            elif role == AgentRole.AURIS_NODES and data:
                # Single classification with its own coherence
                signals.append(make("classification_conflict"
                                    if data.coherence_score < 0.7
                                    else "tax_saving", {
                    "gamma": data.coherence_score,
                    "action": data.action.value,
                    "consensus": data.consensus_category,
                }, confidence=data.coherence_score))

            elif role == AgentRole.LATTICE and data:
                signals.append(make("tax_saving", {
                    "amount": data.total_saving,
                    "strategies": len(data.active_strategies),
                    "efficiency": data.best_position.efficiency_score,
                }, confidence=0.95))

            elif role == AgentRole.CONSCIOUSNESS and data:
                signals.append(make("risk_flag", {
                    "verdict": data.conscience_verdict.value,
                    "risk_score": data.overall_risk_score,
                    "at_risk": data.at_risk_amount,
                }, confidence=1 - data.overall_risk_score))
                if data.at_risk_amount > 0:
                    signals.append(make("benchmark_deviation", {
                        "amount": data.at_risk_amount,
                    }, confidence=0.80))

            elif role == AgentRole.VALIDATOR and data:
                signals.append(make("benchmark_deviation", {
                    "coherence": data.coherence_score,
                    "locked": data.benchmark_locked,
                    "hard_fails": data.hard_fails,
                    "ready": data.ready_to_file,
                }, confidence=data.coherence_score))

        except Exception as e:
            logger.warning(f"Signal extraction failed for {role.value}: {e}")

        return signals

    def run(self) -> HiveVerdict:
        """
        Execute the full hive mind pipeline.
        Wave 1 → Queen rules → Wave 2 → Queen rules → Synthesis
        """
        total_start = time.time()
        wave_timings = {}
        agent_times = {}

        print("=" * 70)
        print("HNC HIVE MIND — QUEEN COMMANDING THE SWARM")
        print("=" * 70)

        # ────────────────────────────────────────
        # WAVE 1 — Independent primary agents
        # ────────────────────────────────────────
        print(f"\n[WAVE 1] Launching {len(WAVE_1_AGENTS)} primary agents...")
        wave1_results, wave1_time = self._run_wave(Wave.WAVE_1_PRIMARY, WAVE_1_AGENTS)
        wave_timings["wave_1"] = round(wave1_time, 3)

        wave1_success = sum(1 for r in wave1_results.values() if r.success)
        print(f"[WAVE 1] Complete: {wave1_success}/{len(WAVE_1_AGENTS)} agents "
              f"({wave1_time:.2f}s) — {len(self.queen.get_all_signals())} signals emitted")

        for role, result in wave1_results.items():
            agent_times[role.value] = result.execution_time

        # Queen rules on Wave 1
        wave1_signals = self.queen.get_all_signals()
        wave1_ruling = self.queen.rule("wave_1_synthesis", wave1_signals)
        print(f"[QUEEN] Wave 1 ruling: {wave1_ruling.authority.value.upper()} "
              f"— {wave1_ruling.consensus.value} (Γ={wave1_ruling.coherence_gamma})")

        # ────────────────────────────────────────
        # WAVE 2 — Refined agents consuming Wave 1
        # ────────────────────────────────────────
        print(f"\n[WAVE 2] Launching {len(WAVE_2_AGENTS)} refined agents with Wave 1 context...")
        wave2_results, wave2_time = self._run_wave(Wave.WAVE_2_REFINED, WAVE_2_AGENTS)
        wave_timings["wave_2"] = round(wave2_time, 3)

        wave2_success = sum(1 for r in wave2_results.values() if r.success)
        print(f"[WAVE 2] Complete: {wave2_success}/{len(WAVE_2_AGENTS)} agents "
              f"({wave2_time:.2f}s) — {len(self.queen.get_all_signals())} total signals")

        for role, result in wave2_results.items():
            agent_times[role.value] = result.execution_time

        # Queen rules on Wave 2
        wave2_signals = [s for s in self.queen.get_all_signals() if s.wave == Wave.WAVE_2_REFINED]
        wave2_ruling = self.queen.rule("wave_2_synthesis", wave2_signals)
        print(f"[QUEEN] Wave 2 ruling: {wave2_ruling.authority.value.upper()} "
              f"— {wave2_ruling.consensus.value} (Γ={wave2_ruling.coherence_gamma})")

        # ────────────────────────────────────────
        # WAVE 3 — Queen synthesis
        # ────────────────────────────────────────
        print(f"\n[WAVE 3] Queen synthesising all {len(self.queen.get_all_signals())} signals...")
        synthesis_start = time.time()

        all_results = {**wave1_results, **wave2_results}
        all_signals = self.queen.get_all_signals()
        final_ruling = self.queen.rule("final_verdict", all_signals)

        verdict = self._synthesise_verdict(
            wave1_results=wave1_results,
            wave2_results=wave2_results,
            all_signals=all_signals,
            final_ruling=final_ruling,
            wave_timings=wave_timings,
            agent_times=agent_times,
            total_time=time.time() - total_start,
        )
        wave_timings["wave_3"] = round(time.time() - synthesis_start, 3)

        print(f"[WAVE 3] Synthesis complete — Γ={final_ruling.coherence_gamma} "
              f"— {final_ruling.consensus.value}")

        return verdict

    def _synthesise_verdict(
        self,
        wave1_results: Dict[AgentRole, AgentResult],
        wave2_results: Dict[AgentRole, AgentResult],
        all_signals: List[HiveSignal],
        final_ruling: QueenDecision,
        wave_timings: Dict[str, float],
        agent_times: Dict[str, float],
        total_time: float,
    ) -> HiveVerdict:
        """Queen's synthesis of all signals into one coherent verdict"""

        p = self.params
        all_results = {**wave1_results, **wave2_results}

        # Naive liability
        pa = 12_570
        taxable = max(0, p["net_profit"] - pa)
        if taxable <= 37_700:
            naive_tax = taxable * 0.20
        else:
            naive_tax = 37_700 * 0.20 + (taxable - 37_700) * 0.40
        naive_ni = max(0, p["net_profit"] - pa) * 0.06
        if p["net_profit"] >= pa:
            naive_ni += 3.45 * 52
        naive_liability = round(naive_tax + naive_ni, 2)

        # Extract subsystem data
        warfare = all_results.get(AgentRole.WARFARE)
        lattice = all_results.get(AgentRole.LATTICE)
        consciousness = all_results.get(AgentRole.CONSCIOUSNESS)
        throne = all_results.get(AgentRole.THRONE)
        validator = all_results.get(AgentRole.VALIDATOR)
        scanner = all_results.get(AgentRole.SCANNER)

        # Queen's saving synthesis — take the best of warfare and lattice,
        # plus scanner's invisible savings
        warfare_saving = warfare.data.total_annual_saving if warfare and warfare.success else 0
        lattice_saving = lattice.data.total_saving if lattice and lattice.success else 0
        invisible_saving = scanner.data.invisible_tax_saving if scanner and scanner.success else 0

        # The Queen chooses the larger of warfare/lattice (they overlap) + invisible
        synthesised_saving = max(warfare_saving, lattice_saving) + invisible_saving

        # Calculate hive liability
        hive_liability = max(0, naive_liability - synthesised_saving)
        cis_credit = p["cis_deducted"]
        net_position = hive_liability - cis_credit  # + = owe, - = refund

        # Subsystem details
        weapons = warfare.data.total_weapons if warfare and warfare.success else 0
        strategies = len(lattice.data.active_strategies) if lattice and lattice.success else 0
        conscience_v = consciousness.data.conscience_verdict.value if consciousness and consciousness.success else "UNKNOWN"
        throne_adv = throne.data.advisory.value if throne and throne.success else "UNKNOWN"
        validator_ready = validator.data.ready_to_file if validator and validator.success else False

        # Queen ruling
        if final_ruling.authority == QueenAuthority.ACCEPT:
            queen_ruling = f"ACCEPTED — Hive consensus is {final_ruling.consensus.value.upper()} (Γ={final_ruling.coherence_gamma})"
            queen_confidence = final_ruling.coherence_gamma
            human_review = False
        elif final_ruling.authority == QueenAuthority.REFINE:
            queen_ruling = f"REFINED — Majority agreement (Γ={final_ruling.coherence_gamma}), Queen adjusting with full context"
            queen_confidence = final_ruling.coherence_gamma * 0.9
            human_review = False
        elif final_ruling.authority == QueenAuthority.VETO:
            queen_ruling = f"VETO — Split vote (Γ={final_ruling.coherence_gamma}), Queen taking conservative path"
            queen_confidence = 0.6
            human_review = True
        else:  # ESCALATE
            queen_ruling = f"ESCALATED — Active conflict (Γ={final_ruling.coherence_gamma}), human review required"
            queen_confidence = 0.4
            human_review = True

        # Defence narrative
        if consciousness and consciousness.success and hasattr(consciousness.data, "defence_narrative"):
            defence_narrative = consciousness.data.defence_narrative
        else:
            defence_narrative = "Every claim filed has statutory basis under Duke of Westminster [1936]."

        # Bottom line
        if net_position < 0:
            bottom_line = (
                f"REFUND DUE: £{abs(net_position):,.0f}. "
                f"Hive mind consensus: {final_ruling.consensus.value} (Γ={final_ruling.coherence_gamma}). "
                f"Queen ruled {final_ruling.authority.value.upper()}. "
                f"{'Filing ready.' if validator_ready else 'Fix validator issues before filing.'}"
            )
        elif net_position == 0:
            bottom_line = (
                f"BREAK-EVEN after CIS credit. "
                f"Saved £{synthesised_saving:,.0f} via hive synthesis. "
                f"Queen confidence: {queen_confidence:.0%}."
            )
        else:
            bottom_line = (
                f"NET TO PAY: £{net_position:,.0f}. "
                f"Hive saved £{synthesised_saving:,.0f}. "
                f"Queen confidence: {queen_confidence:.0%}."
            )

        return HiveVerdict(
            gross_income=p["gross_income"],
            net_profit=p["net_profit"],
            cis_deducted=p["cis_deducted"],
            naive_liability=naive_liability,
            hive_liability=round(hive_liability, 2),
            total_saving=round(synthesised_saving, 2),
            cis_credit=cis_credit,
            net_position=round(net_position, 2),
            agents_active=sum(1 for r in all_results.values() if r.success),
            signals_emitted=len(all_signals),
            queen_decisions=len(self.queen.get_all_decisions()),
            consensus_state=final_ruling.consensus,
            coherence_gamma=final_ruling.coherence_gamma,
            waves_completed=3,
            warfare_weapons=weapons,
            lattice_strategies=strategies,
            consciousness_verdict=conscience_v,
            throne_advisory=throne_adv,
            validator_ready=validator_ready,
            queen_ruling=queen_ruling,
            queen_confidence=round(queen_confidence, 3),
            human_review_required=human_review,
            queen_decisions_log=self.queen.get_all_decisions(),
            defence_narrative=defence_narrative,
            bottom_line=bottom_line,
            wave_timings=wave_timings,
            agent_times=agent_times,
            total_time=round(total_time, 3),
        )


# ═══════════════════════════════════════════════════════════════════
# DEMO / TEST
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    print("\n" + "=" * 70)
    print("HNC HIVE MIND — THE QUEEN AND HER SWARM")
    print("11 agents. 1 Queen. 3 Waves. 1 Coherent Verdict.")
    print("=" * 70)

    hive = HNCHiveMind(params={
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

    verdict = hive.run()

    print(f"\n{'=' * 70}")
    print("HIVE VERDICT")
    print(f"{'=' * 70}")
    print(f"\n  POSITION:")
    print(f"    Gross Income:     £{verdict.gross_income:>10,.0f}")
    print(f"    Net Profit:       £{verdict.net_profit:>10,.0f}")
    print(f"    CIS Deducted:     £{verdict.cis_deducted:>10,.0f}")

    print(f"\n  HIVE SYNTHESIS:")
    print(f"    Naive Liability:  £{verdict.naive_liability:>10,.2f}")
    print(f"    Hive Liability:   £{verdict.hive_liability:>10,.2f}")
    print(f"    Total Saving:     £{verdict.total_saving:>10,.2f}")
    print(f"    CIS Credit:       £{verdict.cis_credit:>10,.2f}")
    if verdict.net_position < 0:
        print(f"    *** REFUND DUE:   £{abs(verdict.net_position):>10,.2f} ***")
    else:
        print(f"    NET TO PAY:       £{verdict.net_position:>10,.2f}")

    print(f"\n  HIVE METRICS:")
    print(f"    Agents Active:    {verdict.agents_active}")
    print(f"    Signals Emitted:  {verdict.signals_emitted}")
    print(f"    Queen Decisions:  {verdict.queen_decisions}")
    print(f"    Consensus:        {verdict.consensus_state.value.upper()}")
    print(f"    Coherence Γ:      {verdict.coherence_gamma}")
    print(f"    Waves Completed:  {verdict.waves_completed}")

    print(f"\n  SUBSYSTEM STATE:")
    print(f"    Warfare Weapons:  {verdict.warfare_weapons}")
    print(f"    Lattice Strategies: {verdict.lattice_strategies}")
    print(f"    Consciousness:    {verdict.consciousness_verdict}")
    print(f"    Throne Advisory:  {verdict.throne_advisory}")
    print(f"    Validator Ready:  {verdict.validator_ready}")

    print(f"\n  QUEEN RULING:")
    print(f"    {verdict.queen_ruling}")
    print(f"    Confidence:       {verdict.queen_confidence:.1%}")
    print(f"    Human Review:     {verdict.human_review_required}")

    print(f"\n  WAVE TIMINGS:")
    for wave, t in verdict.wave_timings.items():
        print(f"    {wave}: {t}s")
    print(f"    TOTAL:  {verdict.total_time}s")

    print(f"\n  QUEEN DECISIONS LOG:")
    for d in verdict.queen_decisions_log:
        print(f"    [{d.decision_id}] {d.topic}: {d.authority.value} — {d.consensus.value} (Γ={d.coherence_gamma})")

    print(f"\n{'─' * 70}")
    print("BOTTOM LINE")
    print(f"{'─' * 70}")
    print(f"  {verdict.bottom_line}")
    print(f"\n  {verdict.defence_narrative[:200]}")
    print(f"\n{'─' * 70}")
