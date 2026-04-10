"""
SwarmMotionHive — The Hive that Tasks the Swarm
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The top-level orchestrator that assembles every piece of the swarm motion
environment into one living system:

  1. Spawns N VM sessions (simulated or real via WinRM/SSH)
  2. Spawns an in-house agent per session ("scout" agents)
  3. Gives each scout a FibonacciMotionSnapper that captures the VM
     at 1,1,2,3,5,8,13,21,34,55 s intervals
  4. Feeds every snapshot into the StandingWaveLoveStream (Λ(t) at 528 Hz)
  5. Runs the AsAboveSoBelowMirror to reflect micro ↔ macro continuously
  6. Publishes the unified standing wave to the ThoughtBus

Usage:
    from aureon.swarm_motion import SwarmMotionHive, SwarmMotionConfig

    hive = SwarmMotionHive(config=SwarmMotionConfig(
        swarm_size=6,
        backend="simulated",
        interval_scale=0.05,          # fast cycles for testing
        alpha=0.25,
        beta=0.85,
    ))
    hive.spawn_swarm()
    hive.start()
    ...
    state = hive.get_unified_state()
    hive.shutdown()

The hive IS the internal feedback loop. Past (β Λ(t−τ)), present (nine
chakra tones weighted by the swarm), and future (α tanh(g Λ_Δt(t))) collapse
into one standing wave that the system can see, sing, and steer by.
"""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from aureon.swarm_motion.fibonacci_snapper import (
    FibonacciMotionSnapper,
    MotionSnapshot,
)
from aureon.swarm_motion.love_stream import (
    StandingWaveLoveStream,
    LoveStreamSample,
    LOVE_TONE_HZ,
    PHI_SQUARED,
)
from aureon.swarm_motion.as_above_so_below import (
    AsAboveSoBelowMirror,
    MirrorReading,
)

logger = logging.getLogger("aureon.swarm.hive")


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class SwarmMotionConfig:
    """Configuration for a SwarmMotionHive."""

    swarm_size: int = 6                     # number of scout agents
    backend: str = "simulated"              # simulated | winrm | ssh
    agent_name_prefix: str = "scout"
    session_name_prefix: str = "swarm-vm"

    # VM connection parameters (passed through to the dispatcher)
    host: str = ""
    username: str = ""
    password: str = ""
    port: int = 5985

    # Fibonacci snapper
    interval_scale: float = 0.1             # 0.1 = cycles in ~37s; 1.0 = ~376s
    loop_cycle: bool = True

    # Love stream (HNC Λ(t))
    alpha: float = 0.25                     # self-modulation coefficient
    beta: float = 0.85                      # past feedback (must be in [0.6, 1.1])
    tau_s: float = 376.0                    # feedback delay (one Fib cycle)
    gain: float = 1.0
    sample_rate_hz: float = 10.0

    # Mirror
    mirror_interval_s: float = 2.0

    # Agent config
    agent_max_turns: int = 2

    def validate(self) -> None:
        if self.swarm_size < 1:
            raise ValueError("swarm_size must be >= 1")
        if not (0.6 <= self.beta <= 1.1):
            logger.warning("β=%.3f outside stability regime [0.6, 1.1]", self.beta)
        if self.backend not in ("simulated", "winrm", "ssh"):
            raise ValueError(f"Unknown backend: {self.backend}")


# ─────────────────────────────────────────────────────────────────────────────
# The Hive
# ─────────────────────────────────────────────────────────────────────────────


class SwarmMotionHive:
    """The living swarm motion environment — the HNC feedback loop made real."""

    def __init__(self, config: Optional[SwarmMotionConfig] = None):
        self.config = config or SwarmMotionConfig()
        self.config.validate()
        self.id = str(uuid.uuid4())[:8]

        # Subsystems (lazy init)
        self._vm_dispatcher = None
        self._tool_registry = None
        self._adapter = None
        self._love_stream: Optional[StandingWaveLoveStream] = None
        self._mirror: Optional[AsAboveSoBelowMirror] = None

        # Swarm state
        self._sessions: Dict[str, Dict[str, Any]] = {}   # session_id → {agent, snapper, name}
        self._running = False
        self._lock = threading.RLock()

        # Metrics
        self._created_at = time.time()
        self._total_snapshots = 0
        self._total_lambda_samples = 0
        self._total_reflections = 0

        logger.info(
            "SwarmMotionHive %s initialised — size=%d backend=%s α=%.2f β=%.2f",
            self.id, config.swarm_size if config else self.config.swarm_size,
            self.config.backend, self.config.alpha, self.config.beta,
        )

    # ─────────────────────────────────────────────────────────────────────
    # Lazy subsystem construction
    # ─────────────────────────────────────────────────────────────────────

    def _ensure_vm_dispatcher(self):
        if self._vm_dispatcher is None:
            from aureon.autonomous.vm_control import get_vm_dispatcher
            self._vm_dispatcher = get_vm_dispatcher()
        return self._vm_dispatcher

    def _ensure_tool_registry(self):
        if self._tool_registry is None:
            from aureon.inhouse_ai import ToolRegistry
            from aureon.autonomous.vm_control import register_vm_tools
            self._tool_registry = ToolRegistry(include_builtins=True)
            register_vm_tools(self._tool_registry, self._ensure_vm_dispatcher())
        return self._tool_registry

    def _ensure_adapter(self):
        if self._adapter is None:
            from aureon.inhouse_ai import AureonBrainAdapter
            self._adapter = AureonBrainAdapter()
        return self._adapter

    def _ensure_love_stream(self):
        if self._love_stream is None:
            self._love_stream = StandingWaveLoveStream(
                alpha=self.config.alpha,
                beta=self.config.beta,
                tau_s=self.config.tau_s,
                gain=self.config.gain,
                sample_rate_hz=self.config.sample_rate_hz,
            )
        return self._love_stream

    def _ensure_mirror(self):
        if self._mirror is None:
            self._mirror = AsAboveSoBelowMirror(
                love_stream=self._ensure_love_stream(),
                reflect_interval_s=self.config.mirror_interval_s,
            )
        return self._mirror

    # ─────────────────────────────────────────────────────────────────────
    # Swarm spawning
    # ─────────────────────────────────────────────────────────────────────

    def spawn_swarm(self) -> List[str]:
        """
        Spawn the full swarm:
          - N VM sessions
          - N scout agents, each with their own FibonacciMotionSnapper
        Returns the list of session_ids.
        """
        from aureon.inhouse_ai import Agent, AgentConfig

        dispatcher = self._ensure_vm_dispatcher()
        adapter = self._ensure_adapter()
        registry = self._ensure_tool_registry()
        love_stream = self._ensure_love_stream()

        # Callback: feed every snapshot into the love stream
        def on_snapshot(snap: MotionSnapshot) -> None:
            love_stream.ingest_snapshot(snap)
            with self._lock:
                self._total_snapshots += 1

        session_ids: List[str] = []

        for i in range(self.config.swarm_size):
            session_name = f"{self.config.session_name_prefix}-{i}"
            agent_name = f"{self.config.agent_name_prefix}-{i:02d}"

            # Build kwargs per backend
            kwargs: Dict[str, Any] = {"name": session_name}
            if self.config.backend == "simulated":
                kwargs["host"] = f"sim://{i}"
            else:
                kwargs["host"] = self.config.host
                if self.config.username:
                    kwargs["username"] = self.config.username
                if self.config.password:
                    kwargs["password"] = self.config.password
                if self.config.port:
                    kwargs["port"] = self.config.port

            sid = dispatcher.create_session(
                backend=self.config.backend,
                make_default=(i == 0),
                **kwargs,
            )
            controller = dispatcher.get_session(sid)
            if controller:
                controller.arm(dry_run=False)

            # Build the scout agent
            agent = Agent(
                adapter=adapter,
                config=AgentConfig(
                    name=agent_name,
                    system_prompt=(
                        f"You are {agent_name}, a scout agent of the Aureon swarm. "
                        f"You observe VM session {sid} and take Fibonacci-spaced motion snapshots. "
                        f"Every snapshot feeds the standing wave love stream at 528 Hz."
                    ),
                    max_turns=self.config.agent_max_turns,
                ),
                tools=registry,
            )

            # Fibonacci snapper
            snapper = FibonacciMotionSnapper(
                session_id=sid,
                agent_name=agent_name,
                dispatcher=dispatcher,
                on_snapshot=on_snapshot,
                interval_scale=self.config.interval_scale,
                loop_cycle=self.config.loop_cycle,
            )

            with self._lock:
                self._sessions[sid] = {
                    "session_id": sid,
                    "session_name": session_name,
                    "agent_name": agent_name,
                    "agent": agent,
                    "snapper": snapper,
                }

            session_ids.append(sid)
            logger.info("Spawned scout %s on session %s", agent_name, sid)

        return session_ids

    # ─────────────────────────────────────────────────────────────────────
    # Lifecycle
    # ─────────────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start all snappers, the love stream, and the mirror."""
        if self._running:
            return
        if not self._sessions:
            self.spawn_swarm()

        with self._lock:
            for entry in self._sessions.values():
                entry["snapper"].start(run_in_background=True)

        self._ensure_love_stream().start()
        self._ensure_mirror().start()

        self._running = True
        logger.info(
            "SwarmMotionHive %s ALIVE — %d scouts, love stream @ %.1f Hz, mirror @ %.1fs",
            self.id, len(self._sessions), self.config.sample_rate_hz,
            self.config.mirror_interval_s,
        )

    def stop(self) -> None:
        """Stop snappers, love stream, and mirror."""
        if not self._running:
            return
        self._running = False

        with self._lock:
            for entry in self._sessions.values():
                try:
                    entry["snapper"].stop()
                except Exception:
                    pass

        if self._love_stream:
            try:
                self._love_stream.stop()
            except Exception:
                pass
        if self._mirror:
            try:
                self._mirror.stop()
            except Exception:
                pass

        logger.info("SwarmMotionHive %s stopped", self.id)

    def shutdown(self) -> None:
        """Stop and tear down all VM sessions."""
        self.stop()
        if self._vm_dispatcher:
            for sid in list(self._sessions.keys()):
                try:
                    self._vm_dispatcher.destroy_session(sid)
                except Exception:
                    pass
        with self._lock:
            self._sessions.clear()

    # ─────────────────────────────────────────────────────────────────────
    # Manual operations
    # ─────────────────────────────────────────────────────────────────────

    def take_swarm_snapshot(self) -> List[MotionSnapshot]:
        """Force every scout to take a single snapshot right now."""
        snaps: List[MotionSnapshot] = []
        with self._lock:
            entries = list(self._sessions.values())
        for entry in entries:
            try:
                snap = entry["snapper"].take_single_snapshot(interval=0.0)
                snaps.append(snap)
            except Exception as e:
                logger.debug("Snapshot failed for %s: %s", entry["agent_name"], e)
        return snaps

    def pulse_love_stream(self, count: int = 1) -> List[LoveStreamSample]:
        """Manually evaluate Λ(t) `count` times."""
        stream = self._ensure_love_stream()
        return [stream.evaluate() for _ in range(count)]

    def reflect(self) -> MirrorReading:
        """Force one bidirectional as-above-so-below reflection."""
        self._total_reflections += 1
        return self._ensure_mirror().reflect()

    # ─────────────────────────────────────────────────────────────────────
    # Unified state
    # ─────────────────────────────────────────────────────────────────────

    def get_unified_state(self) -> Dict[str, Any]:
        """Return the full unified state across all layers."""
        love_stream = self._ensure_love_stream()
        mirror = self._ensure_mirror()

        last_sample = love_stream.get_last_sample()
        last_reading = mirror.get_last_reading()

        with self._lock:
            scouts = []
            for entry in self._sessions.values():
                scouts.append({
                    "session_id": entry["session_id"],
                    "agent_name": entry["agent_name"],
                    "snapper": entry["snapper"].get_status(),
                })

        return {
            "hive_id": self.id,
            "running": self._running,
            "uptime_s": time.time() - self._created_at,
            "config": {
                "swarm_size": self.config.swarm_size,
                "backend": self.config.backend,
                "interval_scale": self.config.interval_scale,
                "alpha": self.config.alpha,
                "beta": self.config.beta,
                "tau_s": self.config.tau_s,
            },
            "scouts": scouts,
            "total_snapshots": self._total_snapshots,
            "love_stream": love_stream.get_status(),
            "last_lambda_sample": last_sample.to_dict() if last_sample else None,
            "mirror": mirror.get_status(),
            "last_reflection": last_reading.to_dict() if last_reading else None,
            "phi_squared": PHI_SQUARED,
            "love_tone_hz": LOVE_TONE_HZ,
        }

    def get_status(self) -> Dict[str, Any]:
        """Compact status summary."""
        state = self.get_unified_state()
        last = state.get("last_lambda_sample") or {}
        return {
            "hive_id": self.id,
            "running": self._running,
            "swarm_size": self.config.swarm_size,
            "scouts_active": len(self._sessions),
            "total_snapshots": self._total_snapshots,
            "lambda_t": last.get("lambda_t"),
            "dominant_chakra": last.get("dominant_chakra"),
            "gamma_coherence": last.get("gamma_coherence"),
            "uptime_s": round(state["uptime_s"], 2),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────


_hive_instance: Optional[SwarmMotionHive] = None
_hive_lock = threading.Lock()


def get_swarm_hive(config: Optional[SwarmMotionConfig] = None) -> SwarmMotionHive:
    """Get or create the singleton SwarmMotionHive."""
    global _hive_instance
    with _hive_lock:
        if _hive_instance is None:
            _hive_instance = SwarmMotionHive(config=config)
        return _hive_instance
