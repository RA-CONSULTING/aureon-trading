#!/usr/bin/env python3
"""
Voice transcript to structured intent adapter for ThoughtBus-driven routing.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from aureon.autonomous.aureon_elephant_memory import ElephantMemory, build_default_elephant_memory
from aureon.autonomous.aureon_harmonic_human_interpreter import HarmonicHumanInterpreter

try:
    from aureon.core.aureon_thought_bus import Thought, get_thought_bus
    HAS_THOUGHT_BUS = True
except Exception:
    Thought = None  # type: ignore
    get_thought_bus = None  # type: ignore
    HAS_THOUGHT_BUS = False


DEFAULT_STATE_PATH = Path("state/voice_intent_cognition_state.json")


@dataclass
class VoiceIntent:
    intent_type: str
    action: str
    route: str
    transcript: str
    confidence: float = 1.0
    target: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


class VoiceIntentCognition:
    def __init__(self, state_path: Optional[Path] = None, memory: Optional[ElephantMemory] = None) -> None:
        self.state_path = Path(state_path or DEFAULT_STATE_PATH)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.last_error = ""
        self.last_intent: Dict[str, Any] = {}
        self.recent_intents: List[Dict[str, Any]] = []
        self.max_recent = 30
        self.memory = memory or build_default_elephant_memory()
        self.pending_clarification: Dict[str, Any] = {}
        self.harmonic_interpreter = HarmonicHumanInterpreter()
        self.thought_bus = get_thought_bus() if HAS_THOUGHT_BUS and get_thought_bus is not None else None
        if self.thought_bus is not None:
            try:
                self.thought_bus.subscribe("voice.transcript.raw", self._handle_transcript)
            except Exception as exc:
                self.last_error = str(exc)
        self._persist()

    def infer_intent(self, transcript: str, source: str = "voice", confidence: float = 1.0) -> Dict[str, Any]:
        text = transcript.strip()
        lower = text.lower()
        normalized = self._normalize_transcript(text)
        context = self._build_context()
        harmonic = self.harmonic_interpreter.interpret(text)
        intent = VoiceIntent(
            intent_type="task",
            action="queue_task",
            route="generic_task",
            transcript=text,
            confidence=min(1.0, max(0.0, float(confidence) * (0.85 + (harmonic.coherence * 0.15)))),
            params={"harmonic": harmonic.to_dict()},
        )

        if self.pending_clarification:
            resumed = self._resolve_clarification(text, lower, confidence, context)
            if resumed is not None:
                return self._finalize_intent(resumed, source)

        if normalized in {"stop listening", "emergency stop", "stop now"}:
            intent.intent_type = "desktop_control"
            intent.action = "emergency_stop"
            intent.route = "desktop_emergency_stop"
        elif normalized in {"arm desktop dry run", "arm desktop dry", "enable desktop dry run"}:
            intent.intent_type = "desktop_control"
            intent.action = "arm_desktop_dry"
            intent.route = "arm_desktop_dry"
        elif normalized in {"arm desktop live", "enable live desktop", "enable desktop live mode"}:
            intent.intent_type = "desktop_control"
            intent.action = "arm_desktop_live"
            intent.route = "arm_desktop_live"
        elif normalized in {"disarm desktop", "disable desktop control"}:
            intent.intent_type = "desktop_control"
            intent.action = "disarm_desktop"
            intent.route = "disarm_desktop"
        elif normalized in {"approve next desktop action", "approve desktop action"}:
            intent.intent_type = "desktop_control"
            intent.action = "approve_desktop"
            intent.route = "approve_desktop"
        elif normalized in {"clear desktop actions", "clear pending desktop actions"}:
            intent.intent_type = "desktop_control"
            intent.action = "clear_desktop_pending"
            intent.route = "clear_desktop_pending"
        elif normalized in {"approve next code proposal", "approve code proposal"}:
            intent.intent_type = "code_control"
            intent.action = "approve_code"
            intent.route = "approve_code"
        elif normalized in {"reject next code proposal", "reject code proposal"}:
            intent.intent_type = "code_control"
            intent.action = "reject_code"
            intent.route = "reject_code"
        elif normalized in {"clear code proposals", "clear pending code proposals"}:
            intent.intent_type = "code_control"
            intent.action = "clear_code_pending"
            intent.route = "clear_code_pending"
        else:
            meta = self._infer_meta_intent(text, lower, context)
            if meta is not None:
                meta.params.setdefault("harmonic", harmonic.to_dict())
                return self._finalize_intent(meta, source)

            advanced = self._infer_advanced_kimi_intent(normalized, text)
            if advanced is not None:
                advanced.params.setdefault("harmonic", harmonic.to_dict())
                return self._finalize_intent(advanced, source)

            match = re.match(r"^(search|find|look for|show me)\s+(.+)$", normalized, re.IGNORECASE)
            if match:
                intent.intent_type = "repo"
                intent.action = "search"
                intent.target = match.group(2).strip()
                intent.route = "repo_search"
            match = re.match(r"^(inspect|open file|read|open)\s+(.+)$", normalized, re.IGNORECASE) if intent.action == "queue_task" else None
            if match:
                intent.intent_type = "repo"
                intent.action = "inspect"
                intent.target = match.group(2).strip().replace("\\", "/")
                intent.route = "repo_inspect"
            match = re.match(r"^(suggest code|improve|refactor|fix|change|update)\s+(.+)$", normalized, re.IGNORECASE) if intent.action == "queue_task" else None
            if match:
                intent.intent_type = "code"
                intent.action = "propose_code"
                intent.target = match.group(2).strip()
                intent.route = "code_proposal"
            match = re.match(r"^(type|enter|write)\s+(.+)$", normalized, re.IGNORECASE) if intent.action == "queue_task" else None
            if match:
                intent.intent_type = "desktop"
                intent.action = "type_text"
                intent.params = {"text": match.group(2).strip()}
                intent.route = "desktop_type_proposal"
            match = re.match(r"^(press|hit|tap)\s+(key\s+)?([A-Za-z0-9_+-]+)$", normalized, re.IGNORECASE) if intent.action == "queue_task" else None
            if match:
                intent.intent_type = "desktop"
                intent.action = "press_key"
                intent.params = {"key": match.group(3).strip().lower()}
                intent.route = "desktop_key_proposal"
            match = re.match(r"^(move mouse|move cursor|go to)\s+(to\s+)?(\d+)\s*[,\s]\s*(\d+)$", normalized, re.IGNORECASE) if intent.action == "queue_task" else None
            if match:
                intent.intent_type = "desktop"
                intent.action = "move_mouse"
                intent.params = {"x": int(match.group(3)), "y": int(match.group(4))}
                intent.route = "desktop_move_proposal"
            match = re.match(r"^(left click|click)\s+(at\s+)?(\d+)\s*[,\s]\s*(\d+)$", normalized, re.IGNORECASE) if intent.action == "queue_task" else None
            if match:
                intent.intent_type = "desktop"
                intent.action = "left_click"
                intent.params = {"x": int(match.group(3)), "y": int(match.group(4))}
                intent.route = "desktop_click_proposal"
            match = re.match(r"^(right click)\s+(at\s+)?(\d+)\s*[,\s]\s*(\d+)$", normalized, re.IGNORECASE) if intent.action == "queue_task" else None
            if match:
                intent.intent_type = "desktop"
                intent.action = "right_click"
                intent.params = {"x": int(match.group(3)), "y": int(match.group(4))}
                intent.route = "desktop_click_proposal"
            match = re.match(r"^(double click)\s+(at\s+)?(\d+)\s*[,\s]\s*(\d+)$", normalized, re.IGNORECASE) if intent.action == "queue_task" else None
            if match:
                intent.intent_type = "desktop"
                intent.action = "double_click"
                intent.params = {"x": int(match.group(3)), "y": int(match.group(4))}
                intent.route = "desktop_click_proposal"
            if lower in {"left click", "click", "click there", "click it"} and intent.action == "queue_task":
                intent.intent_type = "desktop"
                intent.action = "left_click"
                intent.route = "desktop_click_proposal"
            if lower in {"right click", "right click there", "right click it"} and intent.action == "queue_task":
                intent.intent_type = "desktop"
                intent.action = "right_click"
                intent.route = "desktop_click_proposal"
            if lower == "double click" and intent.action == "queue_task":
                intent.intent_type = "desktop"
                intent.action = "double_click"
                intent.route = "desktop_click_proposal"
            match = re.match(r"^(press|hit|use)\s+hotkey\s+(.+)$", normalized, re.IGNORECASE) if intent.action == "queue_task" else None
            if match:
                keys = [part.strip().lower() for part in re.split(r"\s*\+\s*|\s+", match.group(2).strip()) if part.strip()]
                if keys:
                    intent.intent_type = "desktop"
                    intent.action = "hotkey"
                    intent.params = {"keys": keys}
                    intent.route = "desktop_key_proposal"
            if intent.action == "queue_task" and harmonic.coherence <= 0.55:
                self.pending_clarification = {
                    "reason": "low_harmonic_coherence",
                    "options": [],
                    "prompt": "harmonic_clarification",
                }
                intent.intent_type = "meta"
                intent.action = "clarify_harmonic_intent"
                intent.route = "meta_clarify"
                intent.params = {
                    "question": "Your command is not clear enough yet. Say the exact action, file, key, or coordinates.",
                    "harmonic": harmonic.to_dict(),
                }
        return self._finalize_intent(intent, source)

    def _normalize_transcript(self, transcript: str) -> str:
        text = (transcript or "").strip()
        text = re.sub(r"^(please|hey queen|queen|aureon|okay aureon|can you|could you|would you)\s+", "", text, flags=re.IGNORECASE)
        return text.strip().lower()

    def status(self) -> Dict[str, Any]:
        return {
            "last_error": self.last_error,
            "pending_clarification": self.pending_clarification,
            "last_harmonic": self.last_intent.get("params", {}).get("harmonic", {}),
            "last_intent": self.last_intent,
            "recent_intents": self.recent_intents[-10:],
        }

    def _build_context(self) -> Dict[str, Any]:
        transcripts = self.memory.recent_transcripts(limit=5)
        intents = self.memory.recent_intents(limit=5)
        last_transcript = transcripts[-1]["text"] if transcripts else ""
        last_intent = intents[-1]["payload"] if intents else {}
        return {
            "last_transcript": last_transcript,
            "last_intent": last_intent,
            "objective": self.memory.current_objective,
            "current_step": self.memory.current_step() or {},
        }

    def _infer_meta_intent(self, text: str, lower: str, context: Dict[str, Any]) -> Optional[VoiceIntent]:
        if lower in {"what did you hear", "repeat that", "what do you understand", "what do you think i mean"}:
            return VoiceIntent(
                intent_type="meta",
                action="reflect_context",
                route="meta_reflection",
                transcript=text,
                target=context.get("last_transcript") or context.get("objective") or "",
                params={"context": context},
                confidence=0.85,
            )
        if lower in {"help me", "what can you do", "show commands"}:
            return VoiceIntent(
                intent_type="meta",
                action="help",
                route="meta_help",
                transcript=text,
                params={"context": context},
                confidence=0.9,
            )
        if lower in {"do that", "open that", "click that", "use that", "run that", "do it", "open it"}:
            last_intent = dict(context.get("last_intent") or {})
            if last_intent:
                resumed = VoiceIntent(
                    intent_type=str(last_intent.get("intent_type") or "task"),
                    action=str(last_intent.get("action") or "queue_task"),
                    route=str(last_intent.get("route") or "generic_task"),
                    transcript=text,
                    confidence=0.75,
                    target=str(last_intent.get("target") or ""),
                    params=dict(last_intent.get("params") or {}),
                )
                return resumed
        if re.match(r"^(first|second|third|number one|number two|number three)$", lower):
            choice_map = {
                "first": 1, "number one": 1,
                "second": 2, "number two": 2,
                "third": 3, "number three": 3,
            }
            if self.pending_clarification:
                resumed = self._intent_from_choice(choice_map[lower])
                if resumed is not None:
                    return resumed
        if lower.startswith(("open ", "inspect ", "search ", "type ", "press ", "click ", "move ")):
            return None
        if any(token in lower for token in {"this", "that", "it", "there"}) and not context.get("last_intent"):
            self.pending_clarification = {
                "reason": "missing_reference",
                "options": [],
                "prompt": "reference_ambiguous",
            }
            return VoiceIntent(
                intent_type="meta",
                action="clarify_reference",
                route="meta_clarify",
                transcript=text,
                confidence=0.4,
                params={"question": "I need a clearer target. Say the file, action, or coordinates."},
            )
        return None

    def _infer_advanced_kimi_intent(self, normalized: str, original: str) -> Optional[VoiceIntent]:
        code_match = re.match(r"^(write|create|generate)\s+(.+)$", normalized, re.IGNORECASE)
        if code_match and any(token in normalized for token in ["function", "class", "code", "skill", "script"]):
            return VoiceIntent(
                intent_type="code",
                action="propose_code",
                route="code_proposal",
                transcript=original,
                target=code_match.group(2).strip(),
                confidence=0.9,
            )

        search_match = re.match(r"^(search|google|look up|research|find information about)\s+(.+)$", normalized, re.IGNORECASE)
        if search_match:
            return VoiceIntent(
                intent_type="repo",
                action="search",
                route="repo_search",
                transcript=original,
                target=search_match.group(2).strip(),
                confidence=0.88,
            )

        news_match = re.match(r"^(search news|latest news|news about)\s+(.+)$", normalized, re.IGNORECASE)
        if news_match:
            return VoiceIntent(
                intent_type="task",
                action="queue_task",
                route="generic_task",
                transcript=original,
                target=news_match.group(2).strip(),
                params={"external_skill": "news_search"},
                confidence=0.82,
            )

        stock_match = re.match(r"^(get|show|what is)\s+(.+?)\s+(stock price|price)$", normalized, re.IGNORECASE)
        if stock_match:
            ticker = stock_match.group(2).strip().upper()
            return VoiceIntent(
                intent_type="task",
                action="queue_task",
                route="generic_task",
                transcript=original,
                target=ticker,
                params={"external_skill": "stock_price", "ticker": ticker},
                confidence=0.84,
            )

        crypto_match = re.match(r"^(get|show|what is)\s+(.+?)\s+(crypto price|price)$", normalized, re.IGNORECASE)
        if crypto_match:
            symbol = crypto_match.group(2).strip().upper()
            return VoiceIntent(
                intent_type="task",
                action="queue_task",
                route="generic_task",
                transcript=original,
                target=symbol,
                params={"external_skill": "crypto_price", "symbol": symbol},
                confidence=0.84,
            )

        papers_match = re.match(r"^(search papers|find papers|research papers)\s+(?:about|on\s+)?(.+)$", normalized, re.IGNORECASE)
        if papers_match:
            return VoiceIntent(
                intent_type="task",
                action="queue_task",
                route="generic_task",
                transcript=original,
                target=papers_match.group(2).strip(),
                params={"external_skill": "paper_search"},
                confidence=0.82,
            )

        return None

    def _resolve_clarification(self, text: str, lower: str, confidence: float, context: Dict[str, Any]) -> Optional[VoiceIntent]:
        if not self.pending_clarification:
            return None
        if self.pending_clarification.get("reason") == "missing_reference":
            self.pending_clarification = {}
            return VoiceIntent(
                intent_type="task",
                action="queue_task",
                route="generic_task",
                transcript=text,
                confidence=confidence,
                target=context.get("objective") or "",
            )
        return None

    def _intent_from_choice(self, choice: int) -> Optional[VoiceIntent]:
        options = list(self.pending_clarification.get("options") or [])
        if choice <= 0 or choice > len(options):
            return None
        selected = dict(options[choice - 1] or {})
        self.pending_clarification = {}
        return VoiceIntent(
            intent_type=str(selected.get("intent_type") or "task"),
            action=str(selected.get("action") or "queue_task"),
            route=str(selected.get("route") or "generic_task"),
            transcript=str(selected.get("transcript") or ""),
            confidence=float(selected.get("confidence") or 0.7),
            target=str(selected.get("target") or ""),
            params=dict(selected.get("params") or {}),
        )

    def _finalize_intent(self, intent: VoiceIntent, source: str) -> Dict[str, Any]:
        payload = asdict(intent)
        self.last_intent = payload
        self.recent_intents.append(payload)
        self.recent_intents = self.recent_intents[-self.max_recent:]
        self._publish_intent(payload, source)
        self._persist()
        return payload

    def _handle_transcript(self, thought: Any) -> None:
        try:
            payload = dict(getattr(thought, "payload", {}) or {})
            self.infer_intent(
                transcript=str(payload.get("text") or ""),
                source=str(payload.get("source") or "voice"),
                confidence=float(payload.get("confidence") or 1.0),
            )
        except Exception as exc:
            self.last_error = str(exc)
            self._persist()

    def _publish_intent(self, payload: Dict[str, Any], source: str) -> None:
        if self.thought_bus is None or Thought is None:
            return
        try:
            self.thought_bus.publish(Thought(
                source=f"voice_intent_cognition:{source}",
                topic="voice.intent.structured",
                payload=payload,
            ))
        except Exception as exc:
            self.last_error = str(exc)

    def _persist(self) -> None:
        self.state_path.write_text(json.dumps(self.status(), indent=2), encoding="utf-8")


def build_default_voice_cognition() -> VoiceIntentCognition:
    return VoiceIntentCognition()
