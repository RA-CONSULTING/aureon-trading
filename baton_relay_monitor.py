#!/usr/bin/env python3
"""Relay-style validation monitor for ThoughtBus systems."""
from __future__ import annotations
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

import json
import threading
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional, Tuple

from aureon_thought_bus import Thought, get_thought_bus


DEFAULT_LOG_PATH = Path("state/baton_relay.jsonl")
DEFAULT_TIMEOUT_SECONDS = 15.0
DEFAULT_TICK_SECONDS = 2.0

STAGE_ORDER = ["intent", "plan", "execute", "confirm"]
STAGE_INDEX = {stage: idx for idx, stage in enumerate(STAGE_ORDER)}


def _now() -> float:
    return time.time()


def _normalize_system(source: str, topic: str) -> str:
    raw = f"{source} {topic}".lower()
    if "queen" in raw:
        return "queen"
    if "orca" in raw:
        return "orca"
    if "mycelium" in raw:
        return "mycelium"
    if "thought_bus" in raw or "thoughtbus" in raw:
        return "thought_bus"
    if "market" in raw or "feed" in raw:
        return "market_feed"
    if "execute" in raw or "execution" in raw or "order" in raw or "trade" in raw:
        return "execution"
    return "unknown"


def _detect_stage(topic: str, payload: Dict) -> Optional[str]:
    text = f"{topic} {payload or ''}".lower()
    if "intent" in text:
        return "intent"
    if "plan" in text or "prepare" in text:
        return "plan"
    if "execute" in text or "execution" in text or "order" in text or "trade" in text:
        return "execute"
    if "confirm" in text or "confirmed" in text or "complete" in text or "filled" in text:
        return "confirm"
    return None


@dataclass
class SystemState:
    system: str
    last_seen: float
    last_stage: Optional[str] = None
    last_stage_ts: Optional[float] = None
    stale: bool = False


class BatonRelayMonitor:
    """Validates process flow as a relay baton across systems."""

    def __init__(
        self,
        *,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        tick_seconds: float = DEFAULT_TICK_SECONDS,
        log_path: Path = DEFAULT_LOG_PATH,
    ) -> None:
        self.timeout_seconds = float(timeout_seconds)
        self.tick_seconds = float(tick_seconds)
        self.log_path = Path(log_path)
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._systems: Dict[str, SystemState] = {}
        self._last_event: Optional[Tuple[str, float]] = None

        self.bus = get_thought_bus(persist_path="logs/aureon_thoughts.jsonl")
        self.bus.subscribe("*", self._handle_thought)

        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            from aureon_queen_hive_mind import get_queen
            queen = get_queen()
            try:
                queen.enable_full_autonomous_control()
            except Exception:
                pass
        except Exception:
            pass

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run_loop, name="BatonRelayMonitor", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def _handle_thought(self, thought: Thought) -> None:
        system = _normalize_system(thought.source, thought.topic)
        stage = _detect_stage(thought.topic, thought.payload or {})
        ts = float(getattr(thought, "ts", _now()))

        with self._lock:
            state = self._systems.get(system)
            if not state:
                state = SystemState(system=system, last_seen=ts)
                self._systems[system] = state
            state.last_seen = ts
            state.stale = False

            if stage:
                prev_stage = state.last_stage
                if prev_stage and STAGE_INDEX.get(stage, -1) < STAGE_INDEX.get(prev_stage, -1):
                    self._log_event({
                        "type": "stage_out_of_order",
                        "system": system,
                        "stage": stage,
                        "previous_stage": prev_stage,
                        "ts": ts,
                        "topic": thought.topic,
                    })
                state.last_stage = stage
                state.last_stage_ts = ts
                self._log_event({
                    "type": "stage",
                    "system": system,
                    "stage": stage,
                    "ts": ts,
                    "topic": thought.topic,
                })

            if self._last_event:
                last_system, last_ts = self._last_event
                if last_system != system:
                    self._log_event({
                        "type": "handoff",
                        "from_system": last_system,
                        "to_system": system,
                        "elapsed": round(ts - last_ts, 3),
                        "ts": ts,
                        "topic": thought.topic,
                    })
            self._last_event = (system, ts)

    def _log_event(self, payload: Dict) -> None:
        payload.setdefault("ts", _now())
        try:
            with self.log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload) + "\n")
        except Exception:
            pass

    def _run_loop(self) -> None:
        while not self._stop.is_set():
            self._check_stale()
            time.sleep(self.tick_seconds)

    def _check_stale(self) -> None:
        now = _now()
        with self._lock:
            for system, state in self._systems.items():
                if state.stale:
                    continue
                if now - state.last_seen > self.timeout_seconds:
                    state.stale = True
                    self._log_event({
                        "type": "stale",
                        "system": system,
                        "last_seen": state.last_seen,
                        "timeout_seconds": self.timeout_seconds,
                        "ts": now,
                    })
                    try:
                        self.bus.publish(Thought(
                            source="baton_relay",
                            topic="system.reanchor",
                            payload={
                                "system": system,
                                "last_seen": state.last_seen,
                                "timeout_seconds": self.timeout_seconds,
                                "reason": "no heartbeat",
                            },
                        ))
                    except Exception:
                        pass

    def get_status(self) -> Dict[str, Dict]:
        with self._lock:
            return {k: asdict(v) for k, v in self._systems.items()}


def start_baton_monitor(
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    tick_seconds: float = DEFAULT_TICK_SECONDS,
    log_path: Path = DEFAULT_LOG_PATH,
) -> BatonRelayMonitor:
    monitor = BatonRelayMonitor(
        timeout_seconds=timeout_seconds,
        tick_seconds=tick_seconds,
        log_path=log_path,
    )
    monitor.start()
    return monitor


def main() -> None:
    monitor = start_baton_monitor()
    print("🏃 Baton Relay Monitor ACTIVE")
    print(f"   Log: {DEFAULT_LOG_PATH}")
    print(f"   Timeout: {DEFAULT_TIMEOUT_SECONDS}s | Tick: {DEFAULT_TICK_SECONDS}s")
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        monitor.stop()


if __name__ == "__main__":
    main()
