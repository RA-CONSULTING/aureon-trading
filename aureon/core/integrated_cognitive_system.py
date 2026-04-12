#!/usr/bin/env python3
"""
IntegratedCognitiveSystem -- The unified orchestrator that wires everything together.

Boots all cognitive subsystems in parallel, runs a unified cognitive tick at ~1Hz,
accepts user input, and routes goals to the GoalExecutionEngine.
"""

from __future__ import annotations

import logging
import sys
import threading
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("aureon.core.ics")

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

        # State
        self._running = False
        self._tick_thread: Optional[threading.Thread] = None
        self._boot_status: Dict[str, str] = {}
        self._tick_count = 0

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

        # Phase 3: Lambda Engine
        def boot_lambda():
            if not _HAS_LAMBDA:
                raise RuntimeError("import failed")
            self.lambda_engine = LambdaEngine()
        _boot_phase("lambda_engine", boot_lambda)

        # Phase 4: Queen Cortex
        def boot_cortex():
            if not _HAS_CORTEX:
                raise RuntimeError("import failed")
            self.cortex = get_cortex()
            self.cortex.start()
        _boot_phase("cortex", boot_cortex)

        # Phase 5: Self-Feedback Loop
        def boot_feedback():
            if not _HAS_FEEDBACK_LOOP:
                raise RuntimeError("import failed")
            self.feedback_loop = get_self_feedback_loop(vault=self.vault)
            self.feedback_loop.start()
        _boot_phase("feedback_loop", boot_feedback)

        # Phase 6: Sentient Loop
        def boot_sentient():
            if not _HAS_SENTIENT:
                raise RuntimeError("import failed")
            self.sentient_loop = QueenSentientLoop()
            self.sentient_loop.start()
        _boot_phase("sentient_loop", boot_sentient)

        # Phase 7: Agent Core
        def boot_agent():
            if not _HAS_AGENT_CORE:
                raise RuntimeError("import failed")
            self.agent_core = AureonAgentCore()
        _boot_phase("agent_core", boot_agent)

        # Phase 8: Action Bridge
        def boot_bridge():
            if not _HAS_ACTION_BRIDGE:
                raise RuntimeError("import failed")
            self.action_bridge = get_queen_action_bridge()
        _boot_phase("action_bridge", boot_bridge)

        # Phase 9: Being Model
        def boot_being():
            if not _HAS_BEING_MODEL:
                raise RuntimeError("import failed")
            self.being_model = get_being_model()
        _boot_phase("being_model", boot_being)

        # Phase 10: Elephant Memory
        def boot_elephant():
            if not _HAS_ELEPHANT:
                raise RuntimeError("import failed")
            self.elephant_memory = ElephantMemory()
        _boot_phase("elephant_memory", boot_elephant)

        # Phase 11: Goal Execution Engine (wired to all above)
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
            )
        _boot_phase("goal_engine", boot_goal_engine)

        # Phase 12: Dashboard
        def boot_dashboard():
            if not _HAS_DASHBOARD:
                raise RuntimeError("import failed")
            self.dashboard = CognitiveDashboard(thought_bus=self.thought_bus)
        _boot_phase("dashboard", boot_dashboard)

        # Phase 13: Auris Metacognition
        def boot_auris():
            if not _HAS_AURIS:
                raise RuntimeError("import failed")
            self.auris = AurisMetacognition()
        _boot_phase("auris", boot_auris)

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
                # Build readings from cortex bands
                readings = []
                if self.cortex is not None and _HAS_LAMBDA:
                    try:
                        cs = self.cortex.get_state()
                        for band_name in ("delta", "theta", "alpha", "beta", "gamma"):
                            band = cs.band(band_name)
                            readings.append(SubsystemReading(
                                name=band_name,
                                value=band.amplitude if hasattr(band, "amplitude") else 0.0,
                                confidence=band.coherence if hasattr(band, "coherence") else 0.5,
                                state="active",
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
    # Main run loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        """
        Main entry point. Boots subsystems, starts dashboard and tick thread,
        then blocks on stdin input loop.
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
        if self.dashboard is not None:
            self.dashboard.start()

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

        if self.lambda_engine is not None:
            try:
                self.lambda_engine.save_history()
            except Exception:
                pass

        if self._tick_thread is not None:
            self._tick_thread.join(timeout=3)

        print("  ICS shutdown complete.")
