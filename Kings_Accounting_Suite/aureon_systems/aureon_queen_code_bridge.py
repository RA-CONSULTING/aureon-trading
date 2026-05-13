#!/usr/bin/env python3
"""
Bridge queen architect / ThoughtBus signals into the safe code proposal queue.
"""

from __future__ import annotations

import json
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

from aureon.autonomous.aureon_safe_code_control import CodeProposal, SafeCodeControl, build_default_code_controller

try:
    from aureon.core.aureon_thought_bus import get_thought_bus
    HAS_THOUGHT_BUS = True
except Exception:
    get_thought_bus = None  # type: ignore
    HAS_THOUGHT_BUS = False

try:
    from aureon.queen.queen_code_architect import QueenCodeArchitect
    HAS_CODE_ARCHITECT = True
except Exception:
    QueenCodeArchitect = None  # type: ignore
    HAS_CODE_ARCHITECT = False


DEFAULT_BRIDGE_STATE = Path("state/queen_code_bridge_state.json")


@dataclass
class CodeBridgeRule:
    topic: str
    kind: str
    enabled: bool = True


class QueenCodeBridge:
    def __init__(self, controller: Optional[SafeCodeControl] = None, state_path: Optional[Path] = None) -> None:
        self.controller = controller or build_default_code_controller()
        self.state_path = Path(state_path or DEFAULT_BRIDGE_STATE)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

        self.enabled = True
        self.last_error = ""
        self.recent_events: List[Dict[str, Any]] = []
        self.rules: List[CodeBridgeRule] = [
            CodeBridgeRule(topic="queen.code.*", kind="code_task"),
            CodeBridgeRule(topic="decisions.code.*", kind="code_task"),
            CodeBridgeRule(topic="system.patch.*", kind="patch_proposal"),
        ]
        self.architect = QueenCodeArchitect(repo_path=_REPO_ROOT) if HAS_CODE_ARCHITECT and QueenCodeArchitect is not None else None
        self.thought_bus = get_thought_bus(os.path.join(_REPO_ROOT, "state", "queen_code_bridge_thoughts.jsonl")) if HAS_THOUGHT_BUS and get_thought_bus is not None else None
        self._subscribe()
        self._persist()

    def _subscribe(self) -> None:
        if self.thought_bus is None:
            return
        for pattern in {"queen.code.*", "decisions.code.*", "system.patch.*"}:
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
            self.recent_events.append({
                "topic": topic,
                "source": str(getattr(thought, "source", "") or ""),
                "ts": float(getattr(thought, "ts", time.time()) or time.time()),
            })
            self.recent_events = self.recent_events[-25:]

            rule = self._match_rule(topic)
            if rule is None:
                self._persist()
                return

            proposal = CodeProposal(
                kind=rule.kind,
                title=str(payload.get("title") or topic),
                summary=str(payload.get("summary") or payload.get("message") or ""),
                target_files=list(payload.get("target_files") or []),
                patch_text=str(payload.get("patch_text") or ""),
                metadata=dict(payload),
                source=f"thought:{topic}",
            )
            self.controller.propose(proposal)
            self._persist()
        except Exception as e:
            self.last_error = str(e)
            self._persist()

    def propose_edit(self, file_path: str, old_snippet: str, new_snippet: str, title: str = "") -> Dict[str, Any]:
        if self.architect is None:
            return {"ok": False, "reason": "architect_unavailable"}
        result = self.architect.propose_edit(file_path, old_snippet, new_snippet)
        if not result.get("valid"):
            return {"ok": False, "reason": result.get("reason", "invalid_edit")}
        proposal = CodeProposal(
            kind="patch_proposal",
            title=title or f"Edit {file_path}",
            summary=str(result.get("reason") or "proposed edit"),
            target_files=[file_path],
            patch_text=str(result.get("diff") or ""),
            metadata={"file_path": file_path},
            source="queen_code_architect",
        )
        self.controller.propose(proposal)
        self._persist()
        return {"ok": True, "proposal": proposal.title}

    def status(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "last_error": self.last_error,
            "architect_available": self.architect is not None,
            "rules": [asdict(rule) for rule in self.rules],
            "recent_events": self.recent_events[-10:],
            "controller": self.controller.status(),
        }

    def _match_rule(self, topic: str) -> Optional[CodeBridgeRule]:
        for rule in self.rules:
            if rule.topic.endswith("*"):
                if topic.startswith(rule.topic[:-1]):
                    return rule
            elif rule.topic == topic:
                return rule
        return None

    def _persist(self) -> None:
        self.state_path.write_text(json.dumps(self.status(), indent=2), encoding="utf-8")


def build_default_code_bridge() -> QueenCodeBridge:
    return QueenCodeBridge()


if __name__ == "__main__":
    bridge = build_default_code_bridge()
    print(json.dumps(bridge.status(), indent=2))
