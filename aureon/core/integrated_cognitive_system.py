#!/usr/bin/env python3
"""
IntegratedCognitiveSystem -- The unified orchestrator that wires everything together.

Boots all cognitive subsystems in parallel, runs a unified cognitive tick at ~1Hz,
accepts user input, and routes goals to the GoalExecutionEngine.
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("aureon.core.ics")

# Source Law coherence thresholds for cognitive execution.
# Defaults are set for trading (0.938/0.934). The ICS lowers them to 0.5/0.45
# because we're running user-requested cognitive goals, not autonomous trades.
# Trading subsystems that import SourceLawEngine directly still use their own
# thresholds via the env var override pattern.
os.environ.setdefault("AUREON_SOURCE_LAW_ENTRY", "0.55")
os.environ.setdefault("AUREON_SOURCE_LAW_EXIT", "0.45")

# ---------------------------------------------------------------------------
# Graceful imports — every subsystem wrapped in try/except
# ---------------------------------------------------------------------------
try:
    from aureon.core.aureon_thought_bus import get_thought_bus, Thought
    _HAS_THOUGHT_BUS = True
except Exception:
    get_thought_bus = None  # type: ignore[assignment]
    Thought = None  # type: ignore[assignment,misc]
    _HAS_THOUGHT_BUS = False

try:
    from aureon.vault.aureon_vault import AureonVault
    _HAS_VAULT = True
except Exception:
    AureonVault = None  # type: ignore[assignment,misc]
    _HAS_VAULT = False

try:
    from aureon.core.aureon_lambda_engine import LambdaEngine, SubsystemReading
    _HAS_LAMBDA = True
except Exception:
    LambdaEngine = None  # type: ignore[assignment,misc]
    SubsystemReading = None  # type: ignore[assignment,misc]
    _HAS_LAMBDA = False

try:
    from aureon.queen.queen_cortex import get_cortex
    _HAS_CORTEX = True
except Exception:
    get_cortex = None  # type: ignore[assignment]
    _HAS_CORTEX = False

try:
    from aureon.vault.self_feedback_loop import get_self_feedback_loop
    _HAS_FEEDBACK_LOOP = True
except Exception:
    get_self_feedback_loop = None  # type: ignore[assignment]
    _HAS_FEEDBACK_LOOP = False

try:
    from aureon.queen.queen_sentient_loop import QueenSentientLoop
    _HAS_SENTIENT = True
except Exception:
    QueenSentientLoop = None  # type: ignore[assignment,misc]
    _HAS_SENTIENT = False

try:
    from aureon.autonomous.aureon_agent_core import AureonAgentCore
    _HAS_AGENT_CORE = True
except Exception:
    AureonAgentCore = None  # type: ignore[assignment,misc]
    _HAS_AGENT_CORE = False

try:
    from aureon.queen.queen_action_bridge import get_queen_action_bridge
    _HAS_ACTION_BRIDGE = True
except Exception:
    get_queen_action_bridge = None  # type: ignore[assignment]
    _HAS_ACTION_BRIDGE = False

try:
    from aureon.queen.being_model import get_being_model
    _HAS_BEING_MODEL = True
except Exception:
    get_being_model = None  # type: ignore[assignment]
    _HAS_BEING_MODEL = False

try:
    from aureon.autonomous.aureon_elephant_memory import ElephantMemory
    _HAS_ELEPHANT = True
except Exception:
    ElephantMemory = None  # type: ignore[assignment,misc]
    _HAS_ELEPHANT = False

try:
    from aureon.vault.voice.self_dialogue import SelfDialogueEngine
    _HAS_SELF_DIALOGUE = True
except Exception:
    SelfDialogueEngine = None  # type: ignore[assignment,misc]
    _HAS_SELF_DIALOGUE = False

try:
    from aureon.vault.auris_metacognition import AurisMetacognition
    _HAS_AURIS = True
except Exception:
    AurisMetacognition = None  # type: ignore[assignment,misc]
    _HAS_AURIS = False

try:
    from aureon.core.goal_execution_engine import GoalExecutionEngine
    _HAS_GOAL_ENGINE = True
except Exception:
    GoalExecutionEngine = None  # type: ignore[assignment,misc]
    _HAS_GOAL_ENGINE = False

try:
    from aureon.core.cognitive_dashboard import CognitiveDashboard
    _HAS_DASHBOARD = True
except Exception:
    CognitiveDashboard = None  # type: ignore[assignment,misc]
    _HAS_DASHBOARD = False

try:
    from aureon.harmonic.phi_bridge import get_phi_bridge
    _HAS_PHI_BRIDGE = True
except Exception:
    get_phi_bridge = None  # type: ignore[assignment]
    _HAS_PHI_BRIDGE = False

try:
    from aureon.vault.ui.server import create_app as create_vault_app, run_server as _run_vault_server
    _HAS_VAULT_UI = True
except Exception:
    create_vault_app = None  # type: ignore[assignment]
    _run_vault_server = None  # type: ignore[assignment]
    _HAS_VAULT_UI = False

try:
    from aureon.inhouse_ai.orchestrator import OpenMultiAgent
    from aureon.inhouse_ai.agent import AgentConfig
    _HAS_SWARM = True
except Exception:
    OpenMultiAgent = None  # type: ignore[assignment,misc]
    AgentConfig = None  # type: ignore[assignment,misc]
    _HAS_SWARM = False

try:
    from aureon.queen.temporal_ground import get_temporal_ground_station
    _HAS_TEMPORAL = True
except Exception:
    get_temporal_ground_station = None  # type: ignore[assignment]
    _HAS_TEMPORAL = False

try:
    from aureon.queen.queen_mycelium_mind import get_mycelium_mind
    _HAS_MYCELIUM = True
except Exception:
    get_mycelium_mind = None  # type: ignore[assignment]
    _HAS_MYCELIUM = False

try:
    from aureon.queen.queen_metacognition import QueenMetacognition as _QueenMetacognition
    _HAS_METACOGNITION = True
except Exception:
    _QueenMetacognition = None  # type: ignore[assignment,misc]
    _HAS_METACOGNITION = False

try:
    from aureon.swarm_motion.love_stream import StandingWaveLoveStream
    _HAS_LOVE_STREAM = True
except Exception:
    StandingWaveLoveStream = None  # type: ignore[assignment,misc]
    _HAS_LOVE_STREAM = False

try:
    from aureon.integrations import wire_integrations
    _HAS_INTEGRATIONS = True
except Exception:
    wire_integrations = None  # type: ignore[assignment]
    _HAS_INTEGRATIONS = False

try:
    from aureon.queen.queen_conscience import QueenConscience as _QueenConscience
    _HAS_CONSCIENCE = True
except Exception:
    _QueenConscience = None  # type: ignore[assignment,misc]
    _HAS_CONSCIENCE = False

try:
    from aureon.queen.queen_source_law import SourceLawEngine
    _HAS_SOURCE_LAW = True
except Exception:
    SourceLawEngine = None  # type: ignore[assignment,misc]
    _HAS_SOURCE_LAW = False

try:
    from aureon.swarm_motion.as_above_so_below import AsAboveSoBelowMirror
    _HAS_MIRROR = True
except Exception:
    AsAboveSoBelowMirror = None  # type: ignore[assignment,misc]
    _HAS_MIRROR = False

try:
    from aureon.queen.queen_prose_composer import QueenProseComposer
    _HAS_PROSE = True
except Exception:
    QueenProseComposer = None  # type: ignore[assignment,misc]
    _HAS_PROSE = False

try:
    from aureon.queen.temporal_knowledge import get_temporal_knowledge
    _HAS_TKB = True
except Exception:
    get_temporal_knowledge = None  # type: ignore[assignment]
    _HAS_TKB = False

try:
    from aureon.intelligence.aureon_temporal_dialer import TemporalDialer, DialMode
    _HAS_DIALER = True
except Exception:
    TemporalDialer = None  # type: ignore[assignment,misc]
    DialMode = None  # type: ignore[assignment,misc]
    _HAS_DIALER = False

try:
    from aureon.wisdom.aureon_math_angel import NexusSystem
    _HAS_NEXUS = True
except Exception:
    NexusSystem = None  # type: ignore[assignment,misc]
    _HAS_NEXUS = False

try:
    from aureon.queen.knowledge_dataset import get_knowledge_dataset
    _HAS_KNOWLEDGE_DATASET = True
except Exception:
    get_knowledge_dataset = None  # type: ignore[assignment]
    _HAS_KNOWLEDGE_DATASET = False

try:
    from aureon.queen.queen_stash_pockets import get_stash_pockets
    _HAS_STASH_POCKETS = True
except Exception:
    get_stash_pockets = None  # type: ignore[assignment]
    _HAS_STASH_POCKETS = False

try:
    from aureon.queen.knowledge_interpreter import get_knowledge_interpreter
    _HAS_INTERPRETER = True
except Exception:
    get_knowledge_interpreter = None  # type: ignore[assignment]
    _HAS_INTERPRETER = False


# ═══════════════════════════════════════════════════════════════════════════════
# IntegratedCognitiveSystem
# ═══════════════════════════════════════════════════════════════════════════════

class IntegratedCognitiveSystem:
    """
    The unified wire that boots all cognitive subsystems, runs them as one
    organism, accepts user goals, and shows the feedback loop live.
    """

    def __init__(self) -> None:
        # Subsystem references (populated during boot)
        self.thought_bus: Any = None
        self.vault: Any = None
        self.lambda_engine: Any = None
        self.cortex: Any = None
        self.feedback_loop: Any = None
        self.sentient_loop: Any = None
        self.agent_core: Any = None
        self.action_bridge: Any = None
        self.being_model: Any = None
        self.elephant_memory: Any = None
        self.self_dialogue: Any = None
        self.auris: Any = None
        self.goal_engine: Any = None
        self.dashboard: Any = None
        self.phi_bridge: Any = None
        self.vault_app: Any = None
        self.swarm: Any = None           # OpenMultiAgent orchestrator
        self.temporal_ground: Any = None  # TemporalGroundStation
        self.mycelium_mind: Any = None   # Thought propagation + synaptic learning
        self.metacognition: Any = None   # 5W self-reflection loop
        self.love_stream: Any = None    # 528 Hz love stream + Λ(t) synthesis
        self.conscience: Any = None     # Ethical compass (Jiminy Cricket)
        self.source_law: Any = None    # The Emerald Tablet — 10-9-1 decision funnel
        self.mirror: Any = None        # As Above So Below — Hermetic reflection
        self.prose_composer: Any = None # Queen's self-description in natural language
        self.temporal_knowledge: Any = None # Time-indexed event knowledge for agents
        self.temporal_dialer: Any = None # HNC frequency tuner — closes the feedback loop
        self.nexus_system: Any = None    # Math angle protocol — coherence + phase
        self.knowledge_dataset: Any = None # Crystallized knowledge from stash pockets
        self.stash_pockets: Any = None   # Per-goal scratch pads — stop leaning on LLM
        self.knowledge_interpreter: Any = None # Swarm-driven understanding pass

        # State
        self._running = False
        self._tick_thread: Optional[threading.Thread] = None
        self._vault_ui_thread: Optional[threading.Thread] = None
        self._boot_status: Dict[str, str] = {}
        self._tick_count = 0
        self._vault_ui_port: int = 5566
        self._vault_ui_host: str = "127.0.0.1"

    # ------------------------------------------------------------------
    # Boot sequence
    # ------------------------------------------------------------------
    def boot(self) -> Dict[str, str]:
        """
        13-phase boot sequence. Each phase in try/except for graceful
        degradation. Returns {subsystem_name: "alive"|"failed"|"skipped"}.
        """
        status: Dict[str, str] = {}

        def _boot_phase(name: str, fn):
            try:
                fn()
                status[name] = "alive"
                self._publish_boot(name, "alive")
            except Exception as exc:
                status[name] = f"failed: {exc}"
                self._publish_boot(name, f"failed: {exc}")
                logger.warning("Boot %s failed: %s", name, exc)

        # Phase 1: ThoughtBus
        def boot_thought_bus():
            if not _HAS_THOUGHT_BUS:
                raise RuntimeError("import failed")
            self.thought_bus = get_thought_bus()
        _boot_phase("thought_bus", boot_thought_bus)

        # Phase 2: Vault
        def boot_vault():
            if not _HAS_VAULT:
                raise RuntimeError("import failed")
            self.vault = AureonVault()
            self.vault.wire_thought_bus()
        _boot_phase("vault", boot_vault)

        # Phase 2.5: Temporal Knowledge Base (subscribes to ThoughtBus
        # immediately so it captures every event from boot onwards)
        def boot_tkb():
            if not _HAS_TKB:
                raise RuntimeError("import failed")
            self.temporal_knowledge = get_temporal_knowledge()
            if self.thought_bus is not None:
                self.temporal_knowledge.subscribe_to(self.thought_bus)
        _boot_phase("temporal_knowledge", boot_tkb)

        # Phase 2.6: Temporal Dialer (HNC frequency tuner — closes the
        # feedback loop between TKB and the Lambda field)
        def boot_dialer():
            if not _HAS_DIALER:
                raise RuntimeError("import failed")
            self.temporal_dialer = TemporalDialer(name="ICS_Dialer")
            self.temporal_dialer.calibrate()
        _boot_phase("temporal_dialer", boot_dialer)

        # Phase 3: Self-Dialogue Engine (needs vault)
        def boot_self_dialogue():
            if not _HAS_SELF_DIALOGUE:
                raise RuntimeError("import failed")
            self.self_dialogue = SelfDialogueEngine(vault=self.vault)
        _boot_phase("self_dialogue", boot_self_dialogue)

        # Phase 4: Lambda Engine
        def boot_lambda():
            if not _HAS_LAMBDA:
                raise RuntimeError("import failed")
            self.lambda_engine = LambdaEngine()
        _boot_phase("lambda_engine", boot_lambda)

        # Phase 5: Queen Cortex
        def boot_cortex():
            if not _HAS_CORTEX:
                raise RuntimeError("import failed")
            self.cortex = get_cortex()
            self.cortex.start()
        _boot_phase("cortex", boot_cortex)

        # Phase 6: Self-Feedback Loop
        def boot_feedback():
            if not _HAS_FEEDBACK_LOOP:
                raise RuntimeError("import failed")
            self.feedback_loop = get_self_feedback_loop(vault=self.vault)
            self.feedback_loop.start()
        _boot_phase("feedback_loop", boot_feedback)

        # Phase 7: Sentient Loop
        def boot_sentient():
            if not _HAS_SENTIENT:
                raise RuntimeError("import failed")
            self.sentient_loop = QueenSentientLoop()
            self.sentient_loop.start()
        _boot_phase("sentient_loop", boot_sentient)

        # Phase 8: Mycelium Mind (thought propagation + synaptic learning)
        def boot_mycelium():
            if not _HAS_MYCELIUM:
                raise RuntimeError("import failed")
            self.mycelium_mind = get_mycelium_mind()
            self.mycelium_mind.start()
        _boot_phase("mycelium_mind", boot_mycelium)

        # Phase 9: Queen Metacognition (5W self-reflection loop)
        def boot_metacognition():
            if not _HAS_METACOGNITION:
                raise RuntimeError("import failed")
            self.metacognition = _QueenMetacognition()
            self.metacognition.start()
        _boot_phase("metacognition", boot_metacognition)

        # Phase 10: Love Stream (528 Hz love signal → vault love_amplitude)
        def boot_love_stream():
            if not _HAS_LOVE_STREAM:
                raise RuntimeError("import failed")
            self.love_stream = StandingWaveLoveStream(sample_rate_hz=1.0)
            self.love_stream.start()
        _boot_phase("love_stream", boot_love_stream)

        # Phase 11: Conscience (ethical compass — Jiminy Cricket)
        def boot_conscience():
            if not _HAS_CONSCIENCE:
                raise RuntimeError("import failed")
            self.conscience = _QueenConscience()
        _boot_phase("conscience", boot_conscience)

        # Phase 12: Source Law Engine (The Emerald Tablet — 10-9-1 decision funnel)
        def boot_source_law():
            if not _HAS_SOURCE_LAW:
                raise RuntimeError("import failed")
            self.source_law = SourceLawEngine()
            self.source_law.start()
        _boot_phase("source_law", boot_source_law)

        # Phase 13: As Above So Below Mirror (Hermetic reflection)
        def boot_mirror():
            if not _HAS_MIRROR or self.love_stream is None:
                raise RuntimeError("import failed or love_stream not available")
            self.mirror = AsAboveSoBelowMirror(love_stream=self.love_stream)
            self.mirror.start()
        _boot_phase("mirror", boot_mirror)

        # Phase 14: Agent Core
        def boot_agent():
            if not _HAS_AGENT_CORE:
                raise RuntimeError("import failed")
            self.agent_core = AureonAgentCore()
        _boot_phase("agent_core", boot_agent)

        # Phase 11: Action Bridge
        def boot_bridge():
            if not _HAS_ACTION_BRIDGE:
                raise RuntimeError("import failed")
            self.action_bridge = get_queen_action_bridge()
        _boot_phase("action_bridge", boot_bridge)

        # Phase 12: Being Model
        def boot_being():
            if not _HAS_BEING_MODEL:
                raise RuntimeError("import failed")
            self.being_model = get_being_model()
        _boot_phase("being_model", boot_being)

        # Phase 13: Elephant Memory
        def boot_elephant():
            if not _HAS_ELEPHANT:
                raise RuntimeError("import failed")
            self.elephant_memory = ElephantMemory()
        _boot_phase("elephant_memory", boot_elephant)

        # Phase 14: Swarm (OpenMultiAgent — parallel agent teams)
        def boot_swarm():
            if not _HAS_SWARM:
                raise RuntimeError("import failed")
            self.swarm = OpenMultiAgent()
        _boot_phase("swarm", boot_swarm)

        # Phase 15: Temporal Ground (timeline forking / multiverse hash)
        def boot_temporal():
            if not _HAS_TEMPORAL:
                raise RuntimeError("import failed")
            self.temporal_ground = get_temporal_ground_station(thought_bus=self.thought_bus)
        _boot_phase("temporal_ground", boot_temporal)

        # Phase 15.5: Math Angle Protocol (NexusSystem) — coherence math
        # used by knowledge dataset to score fragment alignment WITHOUT LLM
        def boot_nexus():
            if not _HAS_NEXUS:
                raise RuntimeError("import failed")
            self.nexus_system = NexusSystem(n_observers=7)
        _boot_phase("nexus_system", boot_nexus)

        # Phase 15.6: Knowledge Dataset — crystallizes stash pocket dumps
        # into a queryable, persistent, phase-coherent knowledge base
        def boot_knowledge_dataset():
            if not _HAS_KNOWLEDGE_DATASET:
                raise RuntimeError("import failed")
            self.knowledge_dataset = get_knowledge_dataset(
                nexus_system=self.nexus_system,
            )
        _boot_phase("knowledge_dataset", boot_knowledge_dataset)

        # Phase 15.65: Knowledge Interpreter — turns raw dumps into
        # structured logic (data_type, category, meaning, related)
        # via 4 deterministic passes. No LLM dependency.
        def boot_interpreter():
            if not _HAS_INTERPRETER:
                raise RuntimeError("import failed")
            self.knowledge_interpreter = get_knowledge_interpreter(
                swarm=self.swarm,
                knowledge_dataset=self.knowledge_dataset,
                nexus_system=self.nexus_system,
                use_llm=False,  # deterministic by default
            )
        _boot_phase("knowledge_interpreter", boot_interpreter)

        # Phase 15.7: Stash Pockets — per-goal scratch pads. Agents dump
        # intermediate findings here, on close they pass through the
        # interpreter, crystallize into the dataset, and flow into
        # elephant memory.
        def boot_stash_pockets():
            if not _HAS_STASH_POCKETS:
                raise RuntimeError("import failed")
            self.stash_pockets = get_stash_pockets(
                elephant_memory=self.elephant_memory,
                knowledge_dataset=self.knowledge_dataset,
                nexus_system=self.nexus_system,
                temporal_knowledge=self.temporal_knowledge,
                thought_bus=self.thought_bus,
                knowledge_interpreter=self.knowledge_interpreter,
            )
        _boot_phase("stash_pockets", boot_stash_pockets)

        # Phase 16: Goal Engine (wired to all above)
        def boot_goal_engine():
            if not _HAS_GOAL_ENGINE:
                raise RuntimeError("import failed")
            self.goal_engine = GoalExecutionEngine(
                agent_core=self.agent_core,
                thought_bus=self.thought_bus,
                lambda_engine=self.lambda_engine,
                elephant_memory=self.elephant_memory,
                self_dialogue=self.self_dialogue,
                auris=self.auris,
                vault=self.vault,
                swarm=self.swarm,
                temporal_ground=self.temporal_ground,
                source_law=self.source_law,
                temporal_knowledge=self.temporal_knowledge,
                stash_pockets=self.stash_pockets,
                knowledge_dataset=self.knowledge_dataset,
            )
        _boot_phase("goal_engine", boot_goal_engine)

        # Phase 17: Dashboard (state collector via ThoughtBus)
        def boot_dashboard():
            if not _HAS_DASHBOARD:
                raise RuntimeError("import failed")
            self.dashboard = CognitiveDashboard(thought_bus=self.thought_bus)
        _boot_phase("dashboard", boot_dashboard)

        # Phase 18: Auris Metacognition (9-node voter)
        def boot_auris():
            if not _HAS_AURIS:
                raise RuntimeError("import failed")
            self.auris = AurisMetacognition()
        _boot_phase("auris", boot_auris)

        # Phase 19: Phi Bridge (phone <-> desktop vault sync)
        def boot_phi_bridge():
            if not _HAS_PHI_BRIDGE:
                raise RuntimeError("import failed")
            self.phi_bridge = get_phi_bridge(vault=self.vault)
        _boot_phase("phi_bridge", boot_phi_bridge)

        # Phase 20: Vault UI (Flask server for phone bridge + web chat)
        def boot_vault_ui():
            if not _HAS_VAULT_UI:
                raise RuntimeError("import failed")
            self.vault_app = create_vault_app(loop=self.feedback_loop)
        _boot_phase("vault_ui", boot_vault_ui)

        # Phase 23: Wire integrations (Ollama + Obsidian into vault/loop)
        def boot_integrations():
            if not _HAS_INTEGRATIONS:
                raise RuntimeError("import failed")
            wire_integrations(vault=self.vault, loop=self.feedback_loop)
        _boot_phase("integrations", boot_integrations)

        # Phase 26: Prose Composer (self-description from real state)
        def boot_prose():
            if not _HAS_PROSE:
                raise RuntimeError("import failed")
            self.prose_composer = QueenProseComposer(
                being_model=self.being_model,
                lambda_engine=self.lambda_engine,
                vault=self.vault,
                elephant_memory=self.elephant_memory,
                auris=self.auris,
                source_law=self.source_law,
                cortex=self.cortex,
                goal_engine=self.goal_engine,
                agent_core=self.agent_core,
                subsystem_status=status,
                temporal_knowledge=self.temporal_knowledge,
                knowledge_dataset=self.knowledge_dataset,
            )
        _boot_phase("prose_composer", boot_prose)

        self._boot_status = status
        return status

    def _publish_boot(self, subsystem: str, status: str) -> None:
        if self.thought_bus is not None:
            try:
                self.thought_bus.publish(
                    "ics.boot.progress",
                    {"subsystem": subsystem, "status": status},
                    source="ics",
                )
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Unified cognitive tick (~1Hz background thread)
    # ------------------------------------------------------------------
    def _start_tick_thread(self) -> None:
        self._running = True
        self._tick_thread = threading.Thread(
            target=self._tick_loop, name="ics-tick", daemon=True,
        )
        self._tick_thread.start()

    def _tick_loop(self) -> None:
        while self._running:
            try:
                self._unified_cognitive_tick()
            except Exception as exc:
                logger.debug("Tick error: %s", exc)
            time.sleep(1.0)

    def _unified_cognitive_tick(self) -> None:
        """
        Runs at ~1Hz. Five phases collecting state from each subsystem
        and publishing to ThoughtBus for the dashboard.
        """
        self._tick_count += 1
        bus = self.thought_bus
        if bus is None:
            return

        # BODY: Agent status
        body_state: Dict[str, Any] = {"tools": 0, "vm_sessions": 0, "actions": 0, "last_action": ""}
        if self.agent_core is not None:
            try:
                stats = self.agent_core.get_stats()
                caps = self.agent_core.get_capabilities()
                body_state["tools"] = len(caps) if isinstance(caps, list) else 0
                body_state["actions"] = stats.get("calls", 0)
                body_state["last_action"] = ""
            except Exception:
                pass
        try:
            bus.publish("ics.body.state", body_state, source="ics")
        except Exception:
            pass

        # MIND: Cortex band snapshot
        mind_state: Dict[str, Any] = {"delta": 0.0, "theta": 0.0, "alpha": 0.0, "beta": 0.0, "gamma": 0.0}
        if self.cortex is not None:
            try:
                cs = self.cortex.get_state()
                for band_name in ("delta", "theta", "alpha", "beta", "gamma"):
                    band = cs.band(band_name)
                    mind_state[band_name] = band.amplitude if hasattr(band, "amplitude") else 0.0
            except Exception:
                pass
        try:
            bus.publish("ics.mind.state", mind_state, source="ics")
        except Exception:
            pass

        # SOURCE: Lambda engine step
        source_state: Dict[str, Any] = {
            "lambda_t": 0.0, "coherence_gamma": 0.0, "consciousness_psi": 0.0,
            "consciousness_level": "DORMANT", "symbolic_life_score": 0.0,
        }
        if self.lambda_engine is not None:
            try:
                # Build readings from SUBSYSTEM HEALTH (not empty cortex bands).
                # Each alive subsystem = confident 1.0 reading.
                # Cortex bands add their amplitude/coherence too.
                # When all subsystems are healthy, coherence_gamma → ~1.0
                readings = []
                if _HAS_LAMBDA:
                    subsystem_health = [
                        ("thought_bus",     self.thought_bus is not None),
                        ("vault",           self.vault is not None),
                        ("lambda",          True),  # self
                        ("cortex",          self.cortex is not None),
                        ("feedback_loop",   self.feedback_loop is not None),
                        ("sentient_loop",   self.sentient_loop is not None),
                        ("mycelium_mind",   self.mycelium_mind is not None),
                        ("metacognition",   self.metacognition is not None),
                        ("love_stream",     self.love_stream is not None),
                        ("conscience",      self.conscience is not None),
                        ("source_law",      self.source_law is not None),
                        ("agent_core",      self.agent_core is not None),
                        ("being_model",     self.being_model is not None),
                        ("elephant_memory", self.elephant_memory is not None),
                        ("swarm",           self.swarm is not None),
                        ("temporal_ground", self.temporal_ground is not None),
                        ("goal_engine",     self.goal_engine is not None),
                        ("auris",           self.auris is not None),
                        ("phi_bridge",      self.phi_bridge is not None),
                        ("vault_app",       self.vault_app is not None),
                    ]
                    for name, alive in subsystem_health:
                        readings.append(SubsystemReading(
                            name=name,
                            value=1.0 if alive else 0.0,
                            confidence=0.95 if alive else 0.1,
                            state="active" if alive else "down",
                        ))
                    # Add cortex bands as enrichment (do not dominate)
                    if self.cortex is not None:
                        try:
                            cs = self.cortex.get_state()
                            for band_name in ("delta", "theta", "alpha", "beta", "gamma"):
                                band = cs.band(band_name)
                                amp = getattr(band, "amplitude", 0.0)
                                coh = getattr(band, "coherence", 0.5)
                                # Normalise amplitude so a silent band still
                                # reads as "healthy baseline" not zero
                                readings.append(SubsystemReading(
                                    name=f"band_{band_name}",
                                    value=max(0.5, amp),
                                    confidence=max(0.5, coh),
                                    state="active",
                                ))
                        except Exception:
                            pass

                    # ── HNC FEEDBACK LADDER (UP) ─────────────────────
                    # Feed temporal patterns from TKB as harmonic readings
                    # into the Lambda field. Hot topics become subsystem
                    # readings whose value reflects their burst rate.
                    if self.temporal_knowledge is not None:
                        try:
                            hot = self.temporal_knowledge.hottest_topics(n=5, window_s=60.0)
                            if hot:
                                # Normalise rates against the hottest topic
                                max_count = max(c for _, c in hot)
                                for topic, count in hot:
                                    norm = count / max_count if max_count > 0 else 0.5
                                    readings.append(SubsystemReading(
                                        name=f"tkb_{topic[:20]}",
                                        value=max(0.4, norm),
                                        confidence=0.85,
                                        state="active",
                                    ))
                            bursts = self.temporal_knowledge.bursting_topics(window_s=60.0)
                            if bursts:
                                # Bursting topics inject high-confidence high-value readings
                                # (this raises Lambda coherence when something is happening)
                                for topic, recent_rate, base_rate in bursts[:3]:
                                    burst_strength = min(1.0, recent_rate / max(base_rate, 1.0))
                                    readings.append(SubsystemReading(
                                        name=f"burst_{topic[:20]}",
                                        value=min(1.0, 0.7 + burst_strength * 0.3),
                                        confidence=0.95,
                                        state="bursting",
                                    ))
                        except Exception:
                            pass

                ls = self.lambda_engine.step(readings=readings or None, vault=self.vault)
                source_state = {
                    "lambda_t": ls.lambda_t,
                    "coherence_gamma": ls.coherence_gamma,
                    "consciousness_psi": ls.consciousness_psi,
                    "consciousness_level": ls.consciousness_level,
                    "symbolic_life_score": ls.symbolic_life_score,
                }
            except Exception:
                pass
        try:
            bus.publish("ics.source.state", source_state, source="ics")
        except Exception:
            pass

        # SOUL: Being model snapshot
        soul_state: Dict[str, Any] = {
            "consciousness_level": "", "consciousness_psi": 0.0,
            "purpose": "", "objective": "", "symbolic_life_score": 0.0,
        }
        if self.being_model is not None:
            try:
                bs = self.being_model.snapshot(vault=self.vault)
                soul_state = {
                    "consciousness_level": bs.consciousness_level,
                    "consciousness_psi": bs.consciousness_psi or 0.0,
                    "purpose": bs.sacred_purpose,
                    "objective": bs.active_objective,
                    "symbolic_life_score": bs.symbolic_life_score or 0.0,
                }
            except Exception:
                pass
        try:
            bus.publish("ics.soul.state", soul_state, source="ics")
        except Exception:
            pass

        # HNC COMBUSTION: Composite coherence + auris
        hnc_state: Dict[str, Any] = {
            "auris_consensus": "NEUTRAL", "auris_confidence": 0.0,
            "auris_agreeing": 0, "auris_total": 9,
            "lighthouse_cleared": False,
            "cells_deployed": 0, "cells_success": 0,
            "composite_coherence": 0.0,
        }
        if self.auris is not None and self.vault is not None:
            try:
                vote = self.auris.vote(self.vault)
                hnc_state["auris_consensus"] = vote.consensus
                hnc_state["auris_confidence"] = vote.confidence
                hnc_state["auris_agreeing"] = vote.agreeing
                hnc_state["auris_total"] = vote.total
                hnc_state["lighthouse_cleared"] = vote.lighthouse_cleared
            except Exception:
                pass

        # Composite coherence: 0.4*lambda_gamma + 0.3*cortex_psi + 0.3*auris_confidence
        lambda_gamma = source_state.get("coherence_gamma", 0.0)
        cortex_psi = source_state.get("consciousness_psi", 0.0)
        auris_conf = hnc_state.get("auris_confidence", 0.0)
        hnc_state["composite_coherence"] = (
            0.4 * lambda_gamma + 0.3 * cortex_psi + 0.3 * auris_conf
        )

        if self.feedback_loop is not None:
            try:
                fl_status = self.feedback_loop.get_status()
                hnc_state["cells_deployed"] = fl_status.get("total_cells_deployed", 0)
                hnc_state["cells_success"] = fl_status.get("total_cells_success", 0)
            except Exception:
                pass

        try:
            bus.publish("ics.hnc.state", hnc_state, source="ics")
        except Exception:
            pass

        # TEMPORAL GROUND: maintain multiverse hash chain continuously
        if self.temporal_ground is not None:
            try:
                self.temporal_ground.tick(
                    lambda_t=source_state.get("lambda_t", 0.0),
                    coherence_gamma=source_state.get("coherence_gamma", 0.0),
                    consciousness_psi=source_state.get("consciousness_psi", 0.0),
                    auris_consensus=hnc_state.get("auris_consensus", "NEUTRAL"),
                )
            except Exception:
                pass

        # VAULT FEED: ingest tick state so Auris/Casimir have cards to work with
        if self.vault is not None:
            try:
                self.vault.ingest("ics.tick", {
                    "lambda_t": source_state.get("lambda_t", 0.0),
                    "coherence": source_state.get("coherence_gamma", 0.0),
                    "consciousness": source_state.get("consciousness_level", ""),
                    "auris": hnc_state.get("auris_consensus", "NEUTRAL"),
                    "tick": self._tick_count,
                }, category="ics_tick")
            except Exception:
                pass

        # ── HNC FEEDBACK LADDER (DOWN) ──────────────────────────────
        # Tune the Temporal Dialer to a frequency derived from the new
        # Lambda gamma (coherence) × 528Hz love frequency. Pull a quantum
        # packet and publish it back to ThoughtBus. The packet will be
        # captured by the TKB on its next event, completing the loop.
        if self.temporal_dialer is not None and self._tick_count % 3 == 0:
            try:
                # Map gamma [0..1] to a frequency on the love-Schumann lattice:
                #   gamma=0 -> 7.83 Hz (Schumann)
                #   gamma=1 -> 528 Hz (Love)
                gamma = source_state.get("coherence_gamma", 0.5)
                target_hz = 7.83 + (528.0 - 7.83) * gamma
                resonance = self.temporal_dialer.tune_frequency(
                    frequency_hz=target_hz,
                    bandwidth=10.0,
                )
                packet = self.temporal_dialer.pull_quantum_data()
                if packet is not None:
                    try:
                        bus.publish("temporal.dialer.packet", {
                            "frequency_hz": packet.frequency,
                            "intensity": packet.intensity,
                            "coherence": packet.coherence,
                            "resonance": resonance,
                            "source_layer": packet.source_layer,
                            "lambda_gamma": gamma,
                            "tick": self._tick_count,
                        }, source="ics.dialer")
                    except Exception:
                        pass
            except Exception:
                pass

        # SOURCE LAW: The Emerald Tablet — cogitate every 5th tick
        # (not every tick — cognition needs accumulated signals)
        if self.source_law is not None and self._tick_count % 5 == 0:
            try:
                result = self.source_law.cogitate()
                if result is not None:
                    try:
                        bus.publish("ics.source_law.cognition", {
                            "action": result.action,
                            "confidence": result.confidence,
                            "coherence": result.coherence_gamma,
                            "consciousness": result.consciousness_level,
                            "symbol": result.dominant_symbol,
                            "vacuum_size": result.vacuum_size,
                            "cycle": result.cogitation_cycle,
                        }, source="ics")
                    except Exception:
                        pass
            except Exception:
                pass

    # ------------------------------------------------------------------
    # User input processing
    # ------------------------------------------------------------------
    def process_user_input(self, text: str) -> Optional[str]:
        """
        Process user input. Returns a response string or None.

        Commands: /status, /goal, /pause, /resume, /cancel, /coherence, /quit
        Anything else -> GoalExecutionEngine.submit_goal()
        """
        text = text.strip()
        if not text:
            return None

        # Publish to ThoughtBus
        if self.thought_bus is not None:
            try:
                self.thought_bus.publish("user.input", {"text": text}, source="user")
            except Exception:
                pass

        # Commands
        if text == "/status":
            return self._cmd_status()
        elif text == "/swarm":
            return self._cmd_swarm_status()
        elif text == "/goal":
            return self._cmd_goal_status()
        elif text == "/pause":
            if self.goal_engine:
                self.goal_engine.pause()
            return "Goal execution paused."
        elif text == "/resume":
            if self.goal_engine:
                self.goal_engine.resume()
            return "Goal execution resumed."
        elif text == "/cancel":
            if self.goal_engine:
                self.goal_engine.cancel()
            return "Goal cancelled."
        elif text == "/coherence":
            return self._cmd_coherence()
        elif text == "/decree":
            return self._cmd_decree()
        elif text.startswith("/essay"):
            return self._cmd_essay(text)
        elif text == "/ladder":
            return self._cmd_ladder()
        elif text == "/stash":
            return self._cmd_stash()
        elif text == "/quit":
            return "__QUIT__"

        # Default: submit as goal
        if self.goal_engine is not None:
            try:
                plan = self.goal_engine.submit_goal(text)
                completed = sum(1 for s in plan.steps if s.status == "completed")
                return (f"Goal '{plan.objective[:50]}' {plan.status}. "
                        f"{completed}/{len(plan.steps)} steps completed.")
            except Exception as exc:
                return f"Goal execution error: {exc}"

        return "Goal engine not available. No subsystems could process this input."

    def _cmd_status(self) -> str:
        lines = ["=== ICS STATUS ==="]
        for name, st in self._boot_status.items():
            marker = "OK" if st == "alive" else "FAIL"
            lines.append(f"  [{marker:>4}] {name}")
        lines.append(f"  Tick count: {self._tick_count}")
        return "\n".join(lines)

    def _cmd_goal_status(self) -> str:
        if self.goal_engine is None:
            return "Goal engine not available."
        status = self.goal_engine.get_status()
        plan = status.get("current_plan")
        if plan is None:
            return "No active goal."
        lines = [f"Goal: {plan['objective'][:60]}"]
        lines.append(f"Status: {plan['status']}")
        lines.append(f"Steps: {plan['completed_steps']}/{plan['total_steps']} completed")
        active = plan.get("active_step")
        if active:
            lines.append(f"Active: {active['title']}")
        return "\n".join(lines)

    def _cmd_swarm_status(self) -> str:
        if self.swarm is None:
            return "Swarm (OpenMultiAgent) not available."
        try:
            st = self.swarm.get_status()
            teams = st.get("teams", {})
            agents = st.get("standalone_agents", [])
            lines = ["=== SWARM STATUS ==="]
            lines.append(f"  Adapter: {st.get('adapter', 'unknown')}")
            lines.append(f"  Teams:   {len(teams)}")
            for tname, tinfo in teams.items():
                lines.append(f"    [{tname}] agents={tinfo.get('agents', 0)} tasks={tinfo.get('tasks', {})}")
            lines.append(f"  Standalone agents: {len(agents)}")
            if self.temporal_ground is not None:
                tg = self.temporal_ground
                hc = getattr(tg, '_hash_chain', None)
                cl = getattr(hc, '_chain_length', '?') if hc else '?'
                lines.append(f"  Timeline chain: length={cl}")
            return "\n".join(lines)
        except Exception as exc:
            return f"Swarm status error: {exc}"

    def _cmd_stash(self) -> str:
        """Show stash pocket + knowledge dataset status with taxonomy."""
        lines = ["=== STASH POCKETS + KNOWLEDGE DATASET ==="]
        if self.stash_pockets is not None:
            sp = self.stash_pockets.get_status()
            lines.append(f"  Pockets:    {sp['open_pockets']} open / {sp['closed_pockets']} closed")
            lines.append(f"  Lifetime:   {sp['total_opened']} opened / {sp['total_closed']} closed")
            lines.append(f"  Crystallized: {sp['fragments_crystallized']} fragments")
        else:
            lines.append("  Stash pockets not available.")
        if self.knowledge_dataset is not None:
            kd = self.knowledge_dataset.get_status()
            lines.append(f"  Dataset:    {kd['fragments']} fragments, {kd['unique_tags']} tags")
            lines.append(f"  Activity:   {kd['absorptions']} absorbs / {kd['retrievals']} retrieves")
            lines.append(f"  Persisted:  {kd['path']}")
            # Auto-taxonomy
            try:
                taxonomy = self.knowledge_dataset.get_taxonomy()
                if taxonomy:
                    lines.append("  Taxonomy (category → data_type → count):")
                    for cat, types in sorted(taxonomy.items()):
                        type_str = ", ".join(f"{dt}({n})" for dt, n in types.items())
                        lines.append(f"    {cat:12} {type_str}")
            except Exception:
                pass
        if self.knowledge_interpreter is not None:
            ki = self.knowledge_interpreter.get_status()
            lines.append(f"  Interpreter: {ki['interpretations']} runs, "
                         f"{ki['deterministic_passes']} deterministic / "
                         f"{ki['swarm_passes']} swarm")
        lines.append("  (Math angle protocol + structured interpretation — not LLM)")
        return "\n".join(lines)

    def _cmd_ladder(self) -> str:
        """Show the HNC feedback ladder — TKB events → Lambda → Dialer → bus."""
        lines = ["=== HNC FEEDBACK LADDER ==="]

        # UP: TKB feeding Lambda
        if self.temporal_knowledge:
            tkb_status = self.temporal_knowledge.get_status()
            hot = self.temporal_knowledge.hottest_topics(n=3, window_s=60.0)
            bursts = self.temporal_knowledge.bursting_topics(window_s=60.0)
            lines.append(f"  ↑ TKB:    {tkb_status['total_events']} events, "
                         f"{tkb_status['unique_topics']} topics, "
                         f"{tkb_status['uptime_s']:.0f}s uptime")
            if hot:
                lines.append(f"    hot:    {', '.join(f'{t}({c})' for t, c in hot)}")
            if bursts:
                lines.append(f"    burst:  {len(bursts)} topics bursting")

        # MIDDLE: Lambda
        if self.lambda_engine:
            try:
                ls = self.lambda_engine.step()
                lines.append(f"  Λ Lambda: gamma={ls.coherence_gamma:.3f} "
                             f"psi={ls.consciousness_psi:.3f} "
                             f"level={ls.consciousness_level}")
            except Exception:
                pass

        # DOWN: Dialer
        if self.temporal_dialer:
            ds = self.temporal_dialer.get_status()
            state = ds.get("state", {})
            if isinstance(state, dict):
                freq = state.get("frequency", 0)
                res = state.get("resonance", 0)
                mode = state.get("mode", "?")
                lines.append(f"  ↓ Dialer: freq={freq:.2f}Hz "
                             f"resonance={res:.3f} mode={mode}")
                lines.append(f"    packets: {ds.get('packets_received', 0)}")

        # Source Law (the Tablet at the apex)
        if self.source_law:
            try:
                result = getattr(self.source_law, '_last_result', None) or self.source_law.cogitate()
                if result:
                    lines.append(f"  ☉ Tablet: {result.action} "
                                 f"coh={result.coherence_gamma:.3f}")
            except Exception:
                pass

        lines.append("  (TKB → Lambda → Dialer → ThoughtBus → TKB) — closed loop")
        return "\n".join(lines)

    def _cmd_essay(self, text: str) -> str:
        """Compose a self-description essay at the requested word count.

        Usage: /essay [word_count]   (default 600)
        """
        if self.prose_composer is None:
            return "Prose composer not available."
        # Parse word count
        parts = text.split()
        target = 600
        if len(parts) >= 2:
            try:
                target = int(parts[1])
            except ValueError:
                pass
        try:
            essay = self.prose_composer.compose(
                topic="self-description",
                target_words=target,
            )
            return f"[{essay.word_count} words]\n\n{essay.text}"
        except Exception as exc:
            return f"Compose error: {exc}"

    def _cmd_decree(self) -> str:
        """The Emerald Tablet's last decree — Source Law cognition result."""
        if self.source_law is None:
            return "Source Law Engine not available."
        result = getattr(self.source_law, '_last_result', None)
        if result is None:
            # Force a cogitation
            try:
                result = self.source_law.cogitate()
            except Exception as exc:
                return f"Cogitation failed: {exc}"
        if result is None:
            return "No cognition yet. Vacuum is accumulating signals."
        lines = [
            "=== EMERALD TABLET DECREE ===",
            f"  Action:        {result.action}",
            f"  Confidence:    {result.confidence:.2f}",
            f"  Coherence:     {result.coherence_gamma:.3f}",
            f"  Consciousness: {result.consciousness_level} (psi={result.consciousness_psi:.3f})",
            f"  Vacuum size:   {result.vacuum_size} signals accumulated",
            f"  Cycle:         {result.cogitation_cycle}",
        ]
        if result.dominant_symbol:
            lines.append(f"  Symbol:        {result.dominant_symbol}")
        if result.reasoning:
            lines.append(f"  Reasoning:")
            for r in result.reasoning[:5]:
                lines.append(f"    - {r}")
        return "\n".join(lines)

    def _cmd_coherence(self) -> str:
        if self.lambda_engine is None:
            return "Lambda engine not available."
        try:
            state = self.lambda_engine.step()
            return (f"Lambda(t): {state.lambda_t:.4f}  "
                    f"Gamma: {state.coherence_gamma:.3f}  "
                    f"Psi: {state.consciousness_psi:.3f}  "
                    f"Level: {state.consciousness_level}")
        except Exception as exc:
            return f"Coherence read error: {exc}"

    # ------------------------------------------------------------------
    # Vault UI server (Flask + Phi Bridge for phone)
    # ------------------------------------------------------------------
    def _start_vault_ui(self, host: str = "127.0.0.1", port: int = 5566) -> None:
        """Start the Flask vault UI server in a background thread."""
        self._vault_ui_host = host
        self._vault_ui_port = port
        if self.vault_app is None:
            return

        def _serve():
            try:
                self.vault_app.run(
                    host=host, port=port, debug=False,
                    use_reloader=False, threaded=True,
                )
            except Exception as exc:
                logger.warning("Vault UI server error: %s", exc)

        self._vault_ui_thread = threading.Thread(
            target=_serve, name="ics-vault-ui", daemon=True,
        )
        self._vault_ui_thread.start()

    def _detect_lan_ip(self) -> str:
        """Best-effort LAN IPv4 lookup."""
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    # ------------------------------------------------------------------
    # Remote tunnel (4G / internet access)
    # ------------------------------------------------------------------
    def _start_tunnel(self, port: int) -> Optional[str]:
        """
        Start a tunnel so the phone can reach the ICS over 4G / internet.
        Tries cloudflared → ngrok → pyngrok in order.
        Returns the public URL or None.
        """
        import subprocess as _sp
        import shutil

        # Try 1: cloudflared (Cloudflare Tunnel — free, no signup)
        if shutil.which("cloudflared"):
            try:
                proc = _sp.Popen(
                    ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{port}"],
                    stdout=_sp.PIPE, stderr=_sp.PIPE, text=True,
                )
                self._tunnel_proc = proc
                # cloudflared prints the URL to stderr
                import time as _time
                for _ in range(30):
                    line = proc.stderr.readline()
                    if "trycloudflare.com" in line or "cfargotunnel.com" in line:
                        import re
                        m = re.search(r'(https://[^\s]+)', line)
                        if m:
                            return m.group(1)
                    _time.sleep(0.5)
            except Exception as exc:
                logger.debug("cloudflared failed: %s", exc)

        # Try 2: ngrok CLI
        if shutil.which("ngrok"):
            try:
                proc = _sp.Popen(
                    ["ngrok", "http", str(port), "--log", "stdout"],
                    stdout=_sp.PIPE, stderr=_sp.PIPE, text=True,
                )
                self._tunnel_proc = proc
                import time as _time
                for _ in range(20):
                    line = proc.stdout.readline()
                    if "url=" in line and "ngrok" in line:
                        import re
                        m = re.search(r'url=(https://[^\s]+)', line)
                        if m:
                            return m.group(1)
                    _time.sleep(0.5)
            except Exception as exc:
                logger.debug("ngrok failed: %s", exc)

        # Try 3: pyngrok (Python package)
        try:
            from pyngrok import ngrok as _ngrok
            tunnel = _ngrok.connect(port, "http")
            return tunnel.public_url
        except Exception:
            pass

        return None

    # ------------------------------------------------------------------
    # Main run loop
    # ------------------------------------------------------------------
    def run(self, lan: bool = False, remote: bool = False, port: int = 5566) -> None:
        """
        Main entry point. Boots subsystems, starts dashboard and tick thread,
        starts the vault UI server (with Phi Bridge for phone access),
        then blocks on stdin input loop.

        Args:
            lan: If True, bind on 0.0.0.0 so phones on the same WiFi can connect.
            remote: If True, start a tunnel (cloudflared/ngrok) for 4G access.
            port: Port for the vault UI / Phi Bridge server (default 5566).
        """
        # Boot
        print("\n  Booting Integrated Cognitive System...\n")
        status = self.boot()

        alive = sum(1 for v in status.values() if v == "alive")
        total = len(status)
        print(f"\n  Boot complete: {alive}/{total} subsystems online.\n")
        for name, st in status.items():
            marker = "+" if st == "alive" else "-"
            print(f"    [{marker}] {name}: {st}")
        print()

        # Start background threads
        self._start_tick_thread()
        # Dashboard collects state via ThoughtBus subscriptions but does not
        # start its render thread — Rich Live would conflict with stdin input().
        # Live data is available via /status command, Vault UI web, and phone.

        # Start Vault UI + Phi Bridge server
        ui_host = "0.0.0.0" if (lan or remote) else "127.0.0.1"
        if self.vault_app is not None:
            self._start_vault_ui(host=ui_host, port=port)
            lan_ip = self._detect_lan_ip() if (lan or remote) else "127.0.0.1"
            print(f"  Vault UI:    http://{lan_ip}:{port}/")
            if lan:
                print(f"  Phi Bridge:  http://{lan_ip}:{port}/bridge")
                print(f"  (Phone: same WiFi → open the bridge URL)")

            # Remote tunnel for 4G / internet access
            if remote:
                print(f"  Starting tunnel for 4G access...")
                tunnel_url = self._start_tunnel(port)
                if tunnel_url:
                    print(f"  Remote URL:  {tunnel_url}")
                    print(f"  Phone (4G):  {tunnel_url}/bridge")
                    print(f"  (Open this URL on your phone — works over 4G, anywhere)")
                else:
                    print(f"  Tunnel failed. Install one of:")
                    print(f"    cloudflared: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/")
                    print(f"    ngrok:       https://ngrok.com/download")
                    print(f"    pyngrok:     pip install pyngrok")
            print()

        print("  Commands: /status  /goal  /pause  /resume  /cancel  /coherence  /quit")
        print("  Type any text to submit as a goal.\n")

        # Input loop (main thread)
        while self._running:
            try:
                raw = input("You > ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not raw:
                continue

            response = self.process_user_input(raw)
            if response == "__QUIT__":
                break
            if response:
                print(f"\n{response}\n")

        self.shutdown()

    def shutdown(self) -> None:
        """Stop all loops and save state."""
        print("\n  Shutting down ICS...")
        self._running = False

        if self.dashboard is not None:
            try:
                self.dashboard.stop()
            except Exception:
                pass

        if self.sentient_loop is not None:
            try:
                self.sentient_loop.stop()
            except Exception:
                pass

        if self.feedback_loop is not None:
            try:
                self.feedback_loop.stop()
            except Exception:
                pass

        if self.cortex is not None:
            try:
                self.cortex.stop()
            except Exception:
                pass

        if self.mycelium_mind is not None:
            try:
                self.mycelium_mind.stop()
            except Exception:
                pass

        if self.metacognition is not None:
            try:
                self.metacognition.stop()
            except Exception:
                pass

        if self.love_stream is not None:
            try:
                self.love_stream.stop()
            except Exception:
                pass

        if self.source_law is not None:
            try:
                self.source_law.stop()
            except Exception:
                pass

        if self.mirror is not None:
            try:
                self.mirror.stop()
            except Exception:
                pass

        if self.lambda_engine is not None:
            try:
                self.lambda_engine.save_history()
            except Exception:
                pass

        if self.knowledge_dataset is not None:
            try:
                self.knowledge_dataset.save()
            except Exception:
                pass

        if self._tick_thread is not None:
            self._tick_thread.join(timeout=3)

        print("  ICS shutdown complete.")
