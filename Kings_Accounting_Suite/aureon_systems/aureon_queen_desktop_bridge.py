#!/usr/bin/env python3
"""
Bridge queen/thought-bus events into the safe desktop controller.

This bridge does not grant unrestricted autonomous control.
It converts selected thoughts into queued desktop action proposals
that still require the SafeDesktopControl safeguards.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from aureon.autonomous.aureon_safe_desktop_control import DesktopAction, SafeDesktopControl, build_default_controller

try:
    from aureon.core.aureon_thought_bus import Thought, get_thought_bus
    HAS_THOUGHT_BUS = True
except Exception:
    Thought = None  # type: ignore
    get_thought_bus = None  # type: ignore
    HAS_THOUGHT_BUS = False

logger = logging.getLogger(__name__)

DEFAULT_BRIDGE_STATE = Path(os.getenv("AUREON_QUEEN_DESKTOP_BRIDGE_STATE", "state/queen_desktop_bridge_state.json"))


@dataclass
class BridgeRule:
    topic: str
    action: str
    enabled: bool = True
    static_params: Dict[str, Any] = field(default_factory=dict)


class QueenDesktopBridge:
    def __init__(
        self,
        controller: Optional[SafeDesktopControl] = None,
        state_path: Optional[Path] = None,
    ) -> None:
        self.controller = controller or build_default_controller(dry_run=True)
        self.state_path = Path(state_path or DEFAULT_BRIDGE_STATE)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

        self.enabled = True
        self.rules: List[BridgeRule] = [
            BridgeRule(topic="queen.signal", action="press_key", static_params={"key": "f8"}),
            BridgeRule(topic="queen.voice", action="press_key", static_params={"key": "f9"}),
            BridgeRule(topic="decisions.trading", action="press_key", static_params={"key": "f6"}),
            BridgeRule(topic="system.alert", action="press_key", static_params={"key": "f10"}),
        ]
        self.recent_events: List[Dict[str, Any]] = []
        self.last_error = ""

        self.thought_bus = get_thought_bus(os.path.join(_REPO_ROOT, "state", "queen_desktop_bridge_thoughts.jsonl")) if HAS_THOUGHT_BUS and get_thought_bus is not None else None
        self._subscribe()
        self._persist_state()

    def _subscribe(self) -> None:
        if self.thought_bus is None:
            return
        for pattern in {"queen.*", "decisions.*", "system.alert", "emergency.*"}:
            try:
                self.thought_bus.subscribe(pattern, self._handle_thought)
            except Exception as e:
                self.last_error = str(e)

    def _handle_thought(self, thought: Any) -> None:
        if not self.enabled:
            return
        try:
            topic = str(getattr(thought, "topic", "") or "")
            payload = dict(getattr(thought, "payload", {}) or {})
            event = {
                "topic": topic,
                "source": str(getattr(thought, "source", "") or ""),
                "ts": float(getattr(thought, "ts", time.time()) or time.time()),
            }
            self.recent_events.append(event)
            self.recent_events = self.recent_events[-25:]

            if topic.startswith("emergency."):
                self.controller.emergency_stop()
                self._persist_state()
                return

            rule = self._match_rule(topic)
            if rule is None or not rule.enabled:
                self._persist_state()
                return

            params = dict(rule.static_params)
            params.update(self._extract_params(topic, payload))
            proposal = DesktopAction(
                action=rule.action,
                params=params,
                source=f"thought:{topic}",
            )
            self.controller.propose(proposal)
            self._persist_state()
        except Exception as e:
            self.last_error = str(e)
            self._persist_state()

    def _match_rule(self, topic: str) -> Optional[BridgeRule]:
        for rule in self.rules:
            if rule.topic.endswith("*"):
                if topic.startswith(rule.topic[:-1]):
                    return rule
            elif rule.topic == topic:
                return rule
        return None

    def _extract_params(self, topic: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if topic == "decisions.trading":
            side = str(payload.get("decision_type") or payload.get("side") or "").upper()
            if side == "BUY":
                return {"key": "f6"}
            if side == "SELL":
                return {"key": "f7"}
        if topic.startswith("system.alert"):
            return {"key": "f10"}
        return {}

    def status(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "last_error": self.last_error,
            "rules": [asdict(rule) for rule in self.rules],
            "recent_events": self.recent_events[-10:],
            "controller": self.controller.status(),
        }

    def _persist_state(self) -> None:
        try:
            self.state_path.write_text(json.dumps(self.status(), indent=2), encoding="utf-8")
        except Exception as e:
            logger.debug(f"Could not persist queen desktop bridge state: {e}")


def build_default_bridge(dry_run: bool = True) -> QueenDesktopBridge:
    controller = build_default_controller(dry_run=dry_run)
    return QueenDesktopBridge(controller=controller)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    bridge = build_default_bridge(dry_run=True)
    print(json.dumps(bridge.status(), indent=2))
