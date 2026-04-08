#!/usr/bin/env python3
"""
Safe local voice-command bridge.

This bridge does not execute arbitrary actions directly. It accepts
transcripts from a microphone/STT layer or from a simulated inbox,
parses a small set of safe intents, and routes them into the repo's
existing review-gated queues:
- LocalTaskQueue
- SafeCodeControl
- SafeDesktopControl
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from aureon.autonomous.aureon_local_task_queue import LocalTask, LocalTaskQueue, build_default_task_queue
from aureon.autonomous.aureon_dynamic_voice_executor import DynamicVoiceExecutor
from aureon.autonomous.aureon_repo_explorer_service import RepoExplorerService, build_default_repo_explorer
from aureon.autonomous.aureon_safe_code_control import CodeProposal, SafeCodeControl, build_default_code_controller
from aureon.autonomous.aureon_safe_desktop_control import DesktopAction, SafeDesktopControl, build_default_controller
from aureon.autonomous.aureon_voice_intent_cognition import VoiceIntentCognition, build_default_voice_cognition

try:
    from aureon.core.aureon_thought_bus import Thought, get_thought_bus
    HAS_THOUGHT_BUS = True
except Exception:
    Thought = None  # type: ignore
    get_thought_bus = None  # type: ignore
    HAS_THOUGHT_BUS = False

try:
    import speech_recognition as sr  # type: ignore
    HAS_SPEECH_RECOGNITION = True
except Exception:
    sr = None  # type: ignore
    HAS_SPEECH_RECOGNITION = False


DEFAULT_STATE_PATH = Path("state/voice_command_bridge_state.json")
DEFAULT_INBOX_PATH = Path("state/voice_command_inbox.jsonl")


@dataclass
class VoiceCommand:
    text: str
    source: str = "voice"
    confidence: float = 1.0
    created_at: float = field(default_factory=time.time)


class VoiceCommandBridge:
    def __init__(
        self,
        task_queue: Optional[LocalTaskQueue] = None,
        code_control: Optional[SafeCodeControl] = None,
        desktop_control: Optional[SafeDesktopControl] = None,
        explorer: Optional[RepoExplorerService] = None,
        state_path: Optional[Path] = None,
        inbox_path: Optional[Path] = None,
    ) -> None:
        self.task_queue = task_queue or build_default_task_queue()
        self.code_control = code_control or build_default_code_controller()
        self.desktop_control = desktop_control or build_default_controller(dry_run=True)
        self.explorer = explorer or build_default_repo_explorer()
        self.cognition = build_default_voice_cognition()
        self.dynamic_executor = DynamicVoiceExecutor(task_queue=self.task_queue)
        self.state_path = Path(state_path or DEFAULT_STATE_PATH)
        self.inbox_path = Path(inbox_path or DEFAULT_INBOX_PATH)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.inbox_path.parent.mkdir(parents=True, exist_ok=True)

        self.enabled = True
        self.last_error = ""
        self.last_command = ""
        self.last_route = ""
        self.recent_commands: List[Dict[str, Any]] = []
        self.last_inbox_line = 0
        self.max_recent = 30
        self.thought_bus = get_thought_bus() if HAS_THOUGHT_BUS and get_thought_bus is not None else None
        self._persist()

    def submit_command(self, text: str, source: str = "voice", confidence: float = 1.0) -> Dict[str, Any]:
        cmd = VoiceCommand(text=text.strip(), source=source, confidence=float(confidence))
        if not cmd.text:
            return {"ok": False, "reason": "empty_command"}
        result = self._route_command(cmd)
        self._record(cmd, result)
        return result

    def append_inbox_command(self, text: str, source: str = "simulated", confidence: float = 1.0) -> None:
        entry = asdict(VoiceCommand(text=text.strip(), source=source, confidence=float(confidence)))
        with self.inbox_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")

    def process_inbox(self) -> Dict[str, int]:
        if not self.inbox_path.exists():
            return {"processed": 0}
        processed = 0
        with self.inbox_path.open("r", encoding="utf-8", errors="ignore") as handle:
            for idx, line in enumerate(handle, start=1):
                if idx <= self.last_inbox_line:
                    continue
                line = line.strip()
                if not line:
                    self.last_inbox_line = idx
                    continue
                try:
                    payload = json.loads(line)
                except Exception:
                    payload = {"text": line, "source": "inbox", "confidence": 1.0}
                self.submit_command(
                    text=str(payload.get("text") or ""),
                    source=str(payload.get("source") or "inbox"),
                    confidence=float(payload.get("confidence") or 1.0),
                )
                self.last_inbox_line = idx
                processed += 1
        self._persist()
        return {"processed": processed}

    def status(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "speech_recognition_available": HAS_SPEECH_RECOGNITION,
            "thought_bus_available": self.thought_bus is not None,
            "inbox_path": str(self.inbox_path),
            "last_inbox_line": self.last_inbox_line,
            "last_error": self.last_error,
            "last_command": self.last_command,
            "last_route": self.last_route,
            "recent_commands": self.recent_commands[-10:],
            "task_queue": self.task_queue.status(),
            "code_control": self.code_control.status(),
            "desktop_control": self.desktop_control.status(),
            "cognition": self.cognition.status(),
        }

    def _route_command(self, cmd: VoiceCommand) -> Dict[str, Any]:
        text = cmd.text.strip()
        self._publish("voice.transcript.raw", {
            "text": text,
            "source": cmd.source,
            "confidence": cmd.confidence,
            "created_at": cmd.created_at,
        })
        intent = self.cognition.infer_intent(text, source=cmd.source, confidence=cmd.confidence)
        result = self._execute_intent(intent, source=cmd.source)
        self.last_route = str(result.get("route") or intent.get("route") or "")
        return result

    def _execute_intent(self, intent: Dict[str, Any], source: str = "voice") -> Dict[str, Any]:
        action = str(intent.get("action") or "")
        route = str(intent.get("route") or "")
        transcript = str(intent.get("transcript") or "")

        if action == "emergency_stop":
            self.desktop_control.emergency_stop()
            return {"ok": True, "route": "desktop_emergency_stop"}
        if action == "arm_desktop_dry":
            self.desktop_control.arm_dry_run()
            return {"ok": True, "route": "arm_desktop_dry"}
        if action == "arm_desktop_live":
            self.desktop_control.arm_live()
            return {"ok": True, "route": "arm_desktop_live"}
        if action == "disarm_desktop":
            self.desktop_control.disarm()
            return {"ok": True, "route": "disarm_desktop"}
        if action == "approve_desktop":
            result = self.desktop_control.approve_next(confirm_token=self.desktop_control.confirmation_token)
            return {"ok": bool(result.ok), "route": "approve_desktop", "result": result.__dict__}
        if action == "clear_desktop_pending":
            self.desktop_control.clear_pending()
            return {"ok": True, "route": "clear_desktop_pending"}
        if action == "approve_code":
            result = self.code_control.approve_next(reviewer=f"voice:{source}")
            return {"ok": bool(result.get("ok")), "route": "approve_code", "result": result}
        if action == "reject_code":
            result = self.code_control.reject_next(reviewer=f"voice:{source}", reason="voice_rejected")
            return {"ok": bool(result.get("ok")), "route": "reject_code", "result": result}
        if action == "clear_code_pending":
            self.code_control.clear_pending()
            return {"ok": True, "route": "clear_code_pending"}
        if route == "meta_reflection":
            return {
                "ok": True,
                "route": "meta_reflection",
                "message": f"I think you mean: {intent.get('target') or transcript}",
                "context": dict(intent.get("params") or {}),
            }
        if route == "meta_help":
            return {
                "ok": True,
                "route": "meta_help",
                "message": "You can ask me to search files, inspect code, type text, press keys, move the mouse, click, or manage desktop safety modes.",
            }
        if route == "meta_clarify":
            return {
                "ok": False,
                "route": "meta_clarify",
                "reason": str((intent.get("params") or {}).get("question") or "clarification_required"),
            }
        if route == "repo_search":
            query = str(intent.get("target") or transcript)
            hits = self.explorer.search_text(query, limit=10)
            self.task_queue.enqueue(LocalTask(title=f"Voice search: {query}", message=f"Search requested by voice. Found {len(hits)} hits.", source=f"voice:{source}", kind="voice_search"))
            return {"ok": True, "route": "repo_search", "hits": hits[:5]}
        if route == "repo_inspect":
            target = str(intent.get("target") or "")
            info = self.explorer.inspect_file(target)
            self.task_queue.enqueue(LocalTask(title=f"Voice inspect: {target}", message="Inspect file requested by voice", target_files=[target], source=f"voice:{source}", kind="voice_inspect"))
            return {"ok": True, "route": "repo_inspect", "file": info}
        if route == "code_proposal":
            summary = str(intent.get("target") or transcript)
            proposal = self.code_control.propose(CodeProposal(kind="voice_code_task", title=f"Voice code request: {summary[:80]}", summary=summary, source=f"voice:{source}", metadata={"confidence": intent.get("confidence", 1.0)}))
            self.task_queue.enqueue(LocalTask(title=f"Voice code task: {summary[:80]}", message=summary, source=f"voice:{source}", kind="voice_code_task"))
            return {"ok": True, "route": "code_proposal", "proposal": proposal}
        if route.startswith("desktop_"):
            proposal = self.desktop_control.propose(DesktopAction(action=action, params=dict(intent.get("params") or {}), source=f"voice:{source}"))
            return {"ok": True, "route": route, "proposal": proposal}
        dynamic = self.dynamic_executor.execute(transcript=transcript, intent=intent, source=source)
        if dynamic.get("ok") or dynamic.get("route") == "dynamic_wiki_grounding":
            return dynamic
        self.task_queue.enqueue(LocalTask(title=f"Voice task: {transcript[:80]}", message=transcript, source=f"voice:{source}", kind="voice_task"))
        return {"ok": True, "route": "generic_task"}

    def _record(self, cmd: VoiceCommand, result: Dict[str, Any]) -> None:
        self.last_command = cmd.text
        item = {
            "text": cmd.text,
            "source": cmd.source,
            "confidence": cmd.confidence,
            "created_at": cmd.created_at,
            "result": result,
        }
        self.recent_commands.append(item)
        self.recent_commands = self.recent_commands[-self.max_recent:]
        self._persist()

    def _publish(self, topic: str, payload: Dict[str, Any]) -> None:
        if self.thought_bus is None or Thought is None:
            return
        try:
            self.thought_bus.publish(Thought(
                source="voice_command_bridge",
                topic=topic,
                payload=payload,
            ))
        except Exception as exc:
            self.last_error = str(exc)

    def _persist(self) -> None:
        self.state_path.write_text(json.dumps(self.status(), indent=2), encoding="utf-8")


def build_default_voice_bridge() -> VoiceCommandBridge:
    return VoiceCommandBridge()


if __name__ == "__main__":
    bridge = build_default_voice_bridge()
    bridge.append_inbox_command("search websocket reconnect", source="demo")
    bridge.process_inbox()
    print(json.dumps(bridge.status(), indent=2))
