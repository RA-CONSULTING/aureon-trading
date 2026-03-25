#!/usr/bin/env python3
"""
Persistent conversation and task memory for the local Aureon agent flow.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_STATE_PATH = Path("state/queen_elephant_memory.json")


@dataclass
class MemoryEvent:
    kind: str
    text: str = ""
    source: str = "local"
    payload: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


class ElephantMemory:
    def __init__(self, state_path: Optional[Path] = None) -> None:
        self.state_path = Path(state_path or DEFAULT_STATE_PATH)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.current_objective = ""
        self.current_plan: List[Dict[str, Any]] = []
        self.active_step_index = 0
        self.recent_events: List[Dict[str, Any]] = []
        self.max_recent = 100
        self._load()
        self._persist()

    def remember_transcript(self, text: str, source: str = "voice", payload: Optional[Dict[str, Any]] = None) -> None:
        self._append(MemoryEvent(kind="transcript", text=text, source=source, payload=dict(payload or {})))

    def remember_intent(self, payload: Dict[str, Any], source: str = "cognition") -> None:
        self._append(MemoryEvent(kind="intent", text=str(payload.get("transcript") or ""), source=source, payload=dict(payload)))

    def remember_result(self, payload: Dict[str, Any], source: str = "executor") -> None:
        self._append(MemoryEvent(kind="result", text=str(payload.get("route") or ""), source=source, payload=dict(payload)))

    def recent_transcripts(self, limit: int = 5) -> List[Dict[str, Any]]:
        items = [event for event in self.recent_events if event.get("kind") == "transcript"]
        return items[-limit:]

    def recent_intents(self, limit: int = 5) -> List[Dict[str, Any]]:
        items = [event for event in self.recent_events if event.get("kind") == "intent"]
        return items[-limit:]

    def set_objective(self, objective: str, steps: Optional[List[Dict[str, Any]]] = None) -> None:
        self.current_objective = objective.strip()
        self.current_plan = list(steps or [])
        self.active_step_index = 0
        self._append(MemoryEvent(
            kind="objective",
            text=self.current_objective,
            source="planner",
            payload={"steps": self.current_plan, "active_step_index": self.active_step_index},
        ))

    def set_default_objective_from_text(self, text: str) -> None:
        lower = text.lower()
        if lower.startswith(("do ", "open ", "search ", "inspect ", "type ", "press ", "move ")):
            self.set_objective(text, steps=[{"title": text, "status": "pending"}])

    def advance_step(self, note: str = "") -> None:
        if 0 <= self.active_step_index < len(self.current_plan):
            self.current_plan[self.active_step_index]["status"] = "completed"
            if note:
                self.current_plan[self.active_step_index]["note"] = note
            self.active_step_index += 1
            if self.active_step_index < len(self.current_plan):
                self.current_plan[self.active_step_index].setdefault("status", "active")
        self._append(MemoryEvent(
            kind="plan_advance",
            source="planner",
            payload={"active_step_index": self.active_step_index, "plan": self.current_plan},
        ))

    def current_step(self) -> Optional[Dict[str, Any]]:
        if 0 <= self.active_step_index < len(self.current_plan):
            return self.current_plan[self.active_step_index]
        return None

    def status(self) -> Dict[str, Any]:
        return {
            "current_objective": self.current_objective,
            "current_plan": self.current_plan,
            "active_step_index": self.active_step_index,
            "current_step": self.current_step(),
            "recent_events": self.recent_events[-20:],
        }

    def _append(self, event: MemoryEvent) -> None:
        self.recent_events.append(asdict(event))
        self.recent_events = self.recent_events[-self.max_recent:]
        self._persist()

    def _load(self) -> None:
        if not self.state_path.exists():
            return
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            self.current_objective = str(data.get("current_objective") or "")
            self.current_plan = list(data.get("current_plan") or [])
            self.active_step_index = int(data.get("active_step_index") or 0)
            self.recent_events = list(data.get("recent_events") or [])[-self.max_recent:]
        except Exception:
            pass

    def _persist(self) -> None:
        self.state_path.write_text(json.dumps(self.status(), indent=2), encoding="utf-8")


def build_default_elephant_memory() -> ElephantMemory:
    return ElephantMemory()
