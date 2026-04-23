"""
aureon_cognitive_authoring_loop.py — Consciousness + Architect, running as a pair.

The Consciousness module (aureon.core.aureon_consciousness_module) observes
everything on the ThoughtBus. The Code Architect (aureon.code_architect)
turns observed patterns into validated Python skills the organism can
execute. Separately they are dormant. Together they are the organism's
self-authoring loop.

This module is a launcher — nothing else in the tree has to change for the
pair to come online. Call `launch_authoring_loop()` at boot (or run this
file as __main__) and the loop starts.

Cycle per tick (default ~1 Hz):
  1. Consciousness keeps absorbing ThoughtBus traffic (it runs its own logic
     subscribed to the bus — we just keep the reference alive).
  2. Architect's ObservationEngine collects vm/user action patterns.
  3. Every `observe_interval_s` seconds, architect.observe_and_propose()
     turns pending patterns into validated, stored skills.
  4. Every authored skill is published to the bus as `authoring.skill.new`
     so Consciousness (and anything else subscribed) can react.
  5. Requests on topic `authoring.request` are handled:
         { "kind": "compound", "name": "...", "deps": [...] }
         { "kind": "workflow", "name": "...", "tasks": [...] }
         { "kind": "role",     "name": "...", "workflows": [...] }
         { "kind": "execute",  "name": "..." }
     This is the ingress you feed requirements through — the architect
     authors Python code on the other side.

Nothing here calls exec on unvalidated code — SkillValidator + SkillExecutor
own that. This file just wires the two subsystems into one heartbeat.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("aureon.core.cognitive_authoring_loop")


# ─────────────────────────────────────────────────────────────────────────────
# Lazy / fail-soft imports so this module can exist even if parts are missing.
# ─────────────────────────────────────────────────────────────────────────────

try:
    from aureon.core.aureon_thought_bus import get_thought_bus, Thought
    _HAS_BUS = True
except Exception:  # pragma: no cover
    get_thought_bus = None  # type: ignore[assignment]
    Thought = None  # type: ignore[assignment,misc]
    _HAS_BUS = False

try:
    from aureon.core.aureon_consciousness_module import ConsciousnessModule
    _HAS_CONSCIOUSNESS = True
except Exception:  # pragma: no cover
    ConsciousnessModule = None  # type: ignore[assignment,misc]
    _HAS_CONSCIOUSNESS = False

try:
    from aureon.code_architect import get_code_architect, CodeArchitect
    _HAS_ARCHITECT = True
except Exception:  # pragma: no cover
    get_code_architect = None  # type: ignore[assignment]
    CodeArchitect = None  # type: ignore[assignment,misc]
    _HAS_ARCHITECT = False

try:
    from aureon.core.aureon_self_introspection import get_self_introspection
    _HAS_INTRO = True
except Exception:  # pragma: no cover
    get_self_introspection = None  # type: ignore[assignment]
    _HAS_INTRO = False


# ─────────────────────────────────────────────────────────────────────────────
# Status dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class LoopStatus:
    running: bool = False
    started_at: float = 0.0
    ticks: int = 0
    skills_authored: int = 0
    skills_executed: int = 0
    errors: int = 0
    last_error: str = ""
    last_skill: str = ""
    last_tick_at: float = 0.0
    consciousness_alive: bool = False
    architect_alive: bool = False


# ─────────────────────────────────────────────────────────────────────────────
# The loop
# ─────────────────────────────────────────────────────────────────────────────

class CognitiveAuthoringLoop:
    """
    The pair — Consciousness observing, Architect authoring, on one heartbeat.

    Never blocks on a single slow subsystem. Every call is wrapped in
    try/except; a failure increments `errors` and is recorded in `last_error`
    but the loop keeps beating.
    """

    def __init__(
        self,
        observe_interval_s: float = 5.0,
        tick_interval_s: float = 1.0,
        bootstrap_atomics: bool = True,
    ) -> None:
        self.observe_interval_s = max(0.5, float(observe_interval_s))
        self.tick_interval_s = max(0.1, float(tick_interval_s))
        self.bootstrap_atomics = bool(bootstrap_atomics)

        self.bus: Any = None
        self.consciousness: Any = None
        self.architect: Any = None
        self.introspection: Any = None

        self.status = LoopStatus()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._last_observe_at = 0.0
        self._request_handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}

        self._install_default_handlers()

    # ------------------------------------------------------------------
    # Wiring
    # ------------------------------------------------------------------
    def _wire(self) -> None:
        if _HAS_BUS and self.bus is None:
            try:
                self.bus = get_thought_bus()
            except Exception as e:
                logger.debug("bus unavailable: %s", e)

        if _HAS_CONSCIOUSNESS and self.consciousness is None:
            try:
                self.consciousness = ConsciousnessModule(bus=self.bus)
                self.status.consciousness_alive = True
                logger.info("consciousness: online")
            except Exception as e:
                self.status.consciousness_alive = False
                self._record_error(f"consciousness init: {e}")

        if _HAS_ARCHITECT and self.architect is None:
            try:
                self.architect = get_code_architect()
                self.status.architect_alive = True
                logger.info("architect: online")
                if self.bootstrap_atomics:
                    try:
                        self.architect.bootstrap_atomics()
                    except Exception as e:
                        self._record_error(f"bootstrap_atomics: {e}")
            except Exception as e:
                self.status.architect_alive = False
                self._record_error(f"architect init: {e}")

        if _HAS_INTRO and self.introspection is None:
            try:
                self.introspection = get_self_introspection()
            except Exception as e:
                logger.debug("introspection unavailable: %s", e)

        if self.bus is not None:
            try:
                self.bus.subscribe("authoring.request", self._on_request)
            except Exception as e:
                self._record_error(f"bus subscribe: {e}")

    # ------------------------------------------------------------------
    # Run / stop
    # ------------------------------------------------------------------
    def start(self) -> None:
        with self._lock:
            if self.status.running:
                return
            self._wire()
            self._stop.clear()
            self.status.running = True
            self.status.started_at = time.time()
            self._thread = threading.Thread(
                target=self._run,
                name="aureon-authoring-loop",
                daemon=True,
            )
            self._thread.start()
            logger.info("cognitive authoring loop: started")

    def stop(self, timeout: float = 3.0) -> None:
        with self._lock:
            self.status.running = False
            self._stop.set()
            t = self._thread
        if t is not None:
            t.join(timeout=timeout)

    def is_alive(self) -> bool:
        t = self._thread
        return bool(t is not None and t.is_alive())

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def _run(self) -> None:
        while not self._stop.is_set():
            tick_started = time.time()
            self.status.ticks += 1
            self.status.last_tick_at = tick_started

            # Architect: every observe_interval_s, pull patterns → skills.
            if (self.architect is not None
                    and tick_started - self._last_observe_at >= self.observe_interval_s):
                self._last_observe_at = tick_started
                try:
                    new_skills = self.architect.observe_and_propose()
                    for skill in new_skills or []:
                        self._announce_skill(skill)
                except Exception as e:
                    self._record_error(f"observe_and_propose: {e}")

            # Publish a lightweight heartbeat so observers can see we're alive.
            if self.bus is not None and self.status.ticks % 10 == 0:
                try:
                    self.bus.publish(
                        "authoring.heartbeat",
                        {
                            "ticks": self.status.ticks,
                            "skills_authored": self.status.skills_authored,
                            "skills_executed": self.status.skills_executed,
                            "errors": self.status.errors,
                        },
                        source="authoring_loop",
                    )
                except Exception:
                    pass

            # Sleep, but stay responsive to stop().
            self._stop.wait(self.tick_interval_s)

    # ------------------------------------------------------------------
    # Request handling
    # ------------------------------------------------------------------
    def _install_default_handlers(self) -> None:
        self._request_handlers["compound"] = self._handle_compound
        self._request_handlers["task"] = self._handle_task
        self._request_handlers["workflow"] = self._handle_workflow
        self._request_handlers["role"] = self._handle_role
        self._request_handlers["execute"] = self._handle_execute
        self._request_handlers["bootstrap"] = self._handle_bootstrap
        self._request_handlers["status"] = self._handle_status

    def register_handler(
        self,
        kind: str,
        fn: Callable[[Dict[str, Any]], Any],
    ) -> None:
        """Register a custom handler for an authoring.request kind."""
        self._request_handlers[str(kind)] = fn

    def submit(self, request: Dict[str, Any]) -> Any:
        """
        Direct in-process request API. Returns whatever the handler returns.
        This is the simpler surface for code that already holds the loop
        reference; bus-level callers use `authoring.request` instead.
        """
        return self._dispatch(request)

    def _on_request(self, thought: Any) -> None:
        try:
            payload = getattr(thought, "payload", None) or {}
            if not isinstance(payload, dict):
                return
            self._dispatch(payload)
        except Exception as e:
            self._record_error(f"on_request: {e}")

    def _dispatch(self, payload: Dict[str, Any]) -> Any:
        kind = str(payload.get("kind", "")).strip().lower()
        handler = self._request_handlers.get(kind)
        if handler is None:
            self._record_error(f"unknown kind: {kind}")
            return {"ok": False, "error": f"unknown kind: {kind}"}
        try:
            return handler(payload)
        except Exception as e:
            self._record_error(f"handler {kind}: {e}")
            return {"ok": False, "error": str(e)}

    # --- Handlers -----------------------------------------------------
    def _handle_compound(self, p: Dict[str, Any]) -> Dict[str, Any]:
        if self.architect is None:
            return {"ok": False, "error": "architect not wired"}
        skill = self.architect.teach_compound(
            name=str(p.get("name") or ""),
            dependency_skill_names=list(p.get("deps") or []),
            description=str(p.get("description") or ""),
        )
        if skill:
            self._announce_skill(skill)
            return {"ok": True, "skill": skill.name}
        return {"ok": False, "error": "validation failed"}

    def _handle_task(self, p: Dict[str, Any]) -> Dict[str, Any]:
        if self.architect is None:
            return {"ok": False, "error": "architect not wired"}
        skill = self.architect.build_task(
            name=str(p.get("name") or ""),
            dependency_skill_names=list(p.get("deps") or []),
            description=str(p.get("description") or ""),
        )
        if skill:
            self._announce_skill(skill)
            return {"ok": True, "skill": skill.name}
        return {"ok": False, "error": "validation failed"}

    def _handle_workflow(self, p: Dict[str, Any]) -> Dict[str, Any]:
        if self.architect is None:
            return {"ok": False, "error": "architect not wired"}
        skill = self.architect.build_workflow(
            name=str(p.get("name") or ""),
            task_skill_names=list(p.get("tasks") or []),
            description=str(p.get("description") or ""),
        )
        if skill:
            self._announce_skill(skill)
            return {"ok": True, "skill": skill.name}
        return {"ok": False, "error": "validation failed"}

    def _handle_role(self, p: Dict[str, Any]) -> Dict[str, Any]:
        if self.architect is None:
            return {"ok": False, "error": "architect not wired"}
        skill = self.architect.build_role(
            name=str(p.get("name") or ""),
            workflow_skill_names=list(p.get("workflows") or []),
            description=str(p.get("description") or ""),
        )
        if skill:
            self._announce_skill(skill)
            return {"ok": True, "skill": skill.name}
        return {"ok": False, "error": "validation failed"}

    def _handle_execute(self, p: Dict[str, Any]) -> Dict[str, Any]:
        if self.architect is None:
            return {"ok": False, "error": "architect not wired"}
        name = str(p.get("name") or "")
        if not name:
            return {"ok": False, "error": "name required"}
        try:
            result = self.architect.execute_skill(name)
        except Exception as e:
            return {"ok": False, "error": str(e)}
        self.status.skills_executed += 1
        ok = bool(getattr(result, "ok", False))
        err = getattr(result, "error", None)
        return {"ok": ok, "skill": name, "error": err}

    def _handle_bootstrap(self, p: Dict[str, Any]) -> Dict[str, Any]:
        if self.architect is None:
            return {"ok": False, "error": "architect not wired"}
        overwrite = bool(p.get("overwrite", False))
        skills = self.architect.bootstrap_atomics(overwrite=overwrite)
        return {"ok": True, "count": len(skills)}

    def _handle_status(self, p: Dict[str, Any]) -> Dict[str, Any]:
        return {"ok": True, "status": self.get_status()}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _announce_skill(self, skill: Any) -> None:
        self.status.skills_authored += 1
        self.status.last_skill = getattr(skill, "name", "")
        if self.bus is None:
            return
        try:
            self.bus.publish(
                "authoring.skill.new",
                {
                    "name": getattr(skill, "name", ""),
                    "level": str(getattr(skill, "level", "")),
                    "status": str(getattr(skill, "status", "")),
                    "category": getattr(skill, "category", ""),
                    "queen_verdict": getattr(skill, "queen_verdict", ""),
                    "pillar_score": getattr(skill, "pillar_alignment_score", 0.0),
                },
                source="authoring_loop",
            )
        except Exception:
            pass

    def _record_error(self, msg: str) -> None:
        self.status.errors += 1
        self.status.last_error = msg
        logger.warning(msg)

    def get_status(self) -> Dict[str, Any]:
        s = self.status
        return {
            "running": s.running,
            "started_at": s.started_at,
            "ticks": s.ticks,
            "skills_authored": s.skills_authored,
            "skills_executed": s.skills_executed,
            "errors": s.errors,
            "last_error": s.last_error,
            "last_skill": s.last_skill,
            "last_tick_at": s.last_tick_at,
            "consciousness_alive": s.consciousness_alive,
            "architect_alive": s.architect_alive,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Singleton launcher
# ─────────────────────────────────────────────────────────────────────────────

_instance: Optional[CognitiveAuthoringLoop] = None
_instance_lock = threading.Lock()


def get_authoring_loop() -> CognitiveAuthoringLoop:
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = CognitiveAuthoringLoop()
        return _instance


def launch_authoring_loop(
    observe_interval_s: float = 5.0,
    tick_interval_s: float = 1.0,
    bootstrap_atomics: bool = True,
) -> CognitiveAuthoringLoop:
    """
    Convenience entry point. Creates-or-reuses the singleton and starts it.
    Safe to call multiple times; second call is a no-op if already running.
    """
    loop = get_authoring_loop()
    loop.observe_interval_s = max(0.5, float(observe_interval_s))
    loop.tick_interval_s = max(0.1, float(tick_interval_s))
    loop.bootstrap_atomics = bool(bootstrap_atomics)
    loop.start()
    return loop


# ─────────────────────────────────────────────────────────────────────────────
# __main__ — run the pair from the command line
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import json
    import sys as _sys

    parser = argparse.ArgumentParser(description="Run the Aureon cognitive authoring loop.")
    parser.add_argument("--observe-interval", type=float, default=5.0)
    parser.add_argument("--tick-interval", type=float, default=1.0)
    parser.add_argument("--no-bootstrap", action="store_true")
    parser.add_argument("--runtime-seconds", type=float, default=0.0,
                        help="Stop after N seconds; 0 = run until interrupted.")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s :: %(message)s",
    )

    loop = launch_authoring_loop(
        observe_interval_s=args.observe_interval,
        tick_interval_s=args.tick_interval,
        bootstrap_atomics=not args.no_bootstrap,
    )

    t0 = time.time()
    try:
        while loop.is_alive():
            time.sleep(1.0)
            if args.runtime_seconds and (time.time() - t0) >= args.runtime_seconds:
                break
    except KeyboardInterrupt:
        pass
    finally:
        loop.stop()
        print(json.dumps(loop.get_status(), indent=2, default=str), file=_sys.stdout)
