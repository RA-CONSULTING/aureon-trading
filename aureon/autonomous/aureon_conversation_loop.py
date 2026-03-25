#!/usr/bin/env python3
"""
Safe local voice conversation loop.

This unified service connects:
- voice input (microphone when available, otherwise simulated inbox/prompt)
- the safe voice command bridge
- Queen voice output for acknowledgements
"""

from __future__ import annotations

import argparse
import builtins
import importlib.util
import json
import logging
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from aureon.autonomous.aureon_voice_command_bridge import VoiceCommandBridge, build_default_voice_bridge
from aureon.autonomous.aureon_elephant_memory import ElephantMemory, build_default_elephant_memory

try:
    from aureon.queen.queen_voice_engine import QueenVoiceEngine
    HAS_QUEEN_VOICE = True
except Exception:
    QueenVoiceEngine = None  # type: ignore
    HAS_QUEEN_VOICE = False

try:
    import pyttsx3  # type: ignore
    HAS_PYTTSX3 = True
except Exception:
    pyttsx3 = None  # type: ignore
    HAS_PYTTSX3 = False

try:
    import speech_recognition as sr  # type: ignore
    HAS_SPEECH_RECOGNITION = True
except Exception:
    sr = None  # type: ignore
    HAS_SPEECH_RECOGNITION = False

HAS_POCKETSPHINX = importlib.util.find_spec("pocketsphinx") is not None

try:
    from aureon.autonomous.aureon_kimi_voice_adapter import KimiVoiceAdapter
except Exception:
    KimiVoiceAdapter = None  # type: ignore


logger = logging.getLogger(__name__)

DEFAULT_STATE_PATH = Path("state/conversation_loop_state.json")


def safe_print(*args: Any, **kwargs: Any) -> None:
    try:
        builtins.print(*args, **kwargs)
    except Exception:
        pass


class ConversationLoop:
    def __init__(
        self,
        voice_bridge: Optional[VoiceCommandBridge] = None,
        state_path: Optional[Path] = None,
        speak_enabled: bool = True,
        memory: Optional[ElephantMemory] = None,
    ) -> None:
        self.voice_bridge = voice_bridge or build_default_voice_bridge()
        self.memory = memory or build_default_elephant_memory()
        self.state_path = Path(state_path or DEFAULT_STATE_PATH)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

        self.running = False
        self.last_error = ""
        self.last_heard = ""
        self.last_reply = ""
        self.recent_exchanges: list[Dict[str, Any]] = []
        self.max_recent = 20
        self.voice_engine = QueenVoiceEngine(enabled=speak_enabled) if HAS_QUEEN_VOICE and QueenVoiceEngine is not None else None
        self.local_tts_enabled = bool(speak_enabled and self.voice_engine is None and HAS_PYTTSX3)
        self._local_tts_engine = None
        self._local_tts_lock = threading.Lock()
        backend = os.getenv("AUREON_SPEECH_BACKEND", "auto")
        self.voice_adapter = KimiVoiceAdapter(backend=backend) if KimiVoiceAdapter is not None else None
        self._persist()

    def handle_text(self, text: str, source: str = "text") -> Dict[str, Any]:
        self.memory.remember_transcript(text=text, source=source)
        self.memory.set_default_objective_from_text(text)
        result = self._handle_agent_command(text=text, source=source)
        bridge_status = self.voice_bridge.status()
        cognition = dict(bridge_status.get("cognition", {}) or {})
        last_intent = dict(cognition.get("last_intent", {}) or {})
        if last_intent:
            self.memory.remember_intent(last_intent, source="voice_cognition")
        self.memory.remember_result(result, source="conversation_loop")
        if result.get("ok"):
            self.memory.advance_step(note=str(result.get("route") or "completed"))
        reply = self._build_reply(text, result)
        self.last_heard = text
        self.last_reply = reply
        self.recent_exchanges.append({
            "heard": text,
            "reply": reply,
            "source": source,
            "result": result,
            "ts": time.time(),
        })
        self.recent_exchanges = self.recent_exchanges[-self.max_recent:]
        self._speak(reply)
        self._persist()
        return {"ok": True, "result": result, "reply": reply}

    def process_inbox(self) -> Dict[str, Any]:
        before = len(self.voice_bridge.recent_commands)
        processed = self.voice_bridge.process_inbox()
        after_items = self.voice_bridge.recent_commands[before:]
        for item in after_items:
            text = str(item.get("text") or "")
            result = dict(item.get("result") or {})
            reply = self._build_reply(text, result)
            self.last_heard = text
            self.last_reply = reply
            self.recent_exchanges.append({
                "heard": text,
                "reply": reply,
                "source": str(item.get("source") or "inbox"),
                "result": result,
                "ts": time.time(),
            })
            self.recent_exchanges = self.recent_exchanges[-self.max_recent:]
            self._speak(reply)
        self._persist()
        return {"processed": processed.get("processed", 0), "reply_count": len(after_items)}

    def run_agent_mode(self, interval: float = 1.0, microphone: bool = False) -> None:
        self.running = True
        self._persist()
        mode = "microphone" if microphone else "inbox"
        safe_print(f"VOICE AGENT: starting in {mode} mode")
        safe_print(f"VOICE AGENT: speech_recognition_available={HAS_SPEECH_RECOGNITION}")
        safe_print(f"VOICE AGENT: pocketsphinx_available={HAS_POCKETSPHINX}")
        safe_print(f"VOICE AGENT: voice_output_available={self.voice_engine is not None}")
        safe_print(f"VOICE AGENT: inbox={self.voice_bridge.inbox_path}")
        if microphone and not HAS_SPEECH_RECOGNITION:
            safe_print("VOICE AGENT: microphone mode requested, but speech_recognition is not installed.")
        self._speak(f"Agent mode online. Listening through {mode}.")
        while self.running:
            try:
                if microphone and HAS_SPEECH_RECOGNITION:
                    safe_print("VOICE AGENT: listening for microphone input...")
                    heard = self.listen_once(timeout=2.0, phrase_time_limit=6.0)
                    if heard.get("ok"):
                        safe_print(f"VOICE AGENT: heard -> {self.last_heard}")
                        safe_print(f"VOICE AGENT: reply -> {self.last_reply}")
                    if not heard.get("ok") and heard.get("reason") not in {
                        "speech_recognition_unavailable",
                        "listening timed out while waiting for phrase to start",
                    }:
                        self.last_error = str(heard.get("reason") or "")
                        safe_print(f"VOICE AGENT: error -> {self.last_error}")
                        self._persist()
                else:
                    result = self.process_inbox()
                    if result.get("processed"):
                        safe_print(f"VOICE AGENT: processed {result.get('processed', 0)} queued voice command(s)")
                        safe_print(f"VOICE AGENT: last heard -> {self.last_heard}")
                        safe_print(f"VOICE AGENT: last reply -> {self.last_reply}")
            except Exception as exc:
                self.last_error = str(exc)
                safe_print(f"VOICE AGENT: fatal loop error -> {self.last_error}")
                self._persist()
            else:
                self._persist()
            time.sleep(interval)

    def listen_once(self, timeout: float = 5.0, phrase_time_limit: float = 8.0) -> Dict[str, Any]:
        if not HAS_SPEECH_RECOGNITION or sr is None:
            return {"ok": False, "reason": "speech_recognition_unavailable"}
        try:
            if self.voice_adapter is not None:
                result = self.voice_adapter.recognize_microphone(timeout=timeout, phrase_time_limit=phrase_time_limit)
                if result.ok and result.text:
                    return self.handle_text(result.text, source=f"microphone:{result.backend}")
                self.last_error = result.reason or "recognition_failed"
                self._persist()
                return {"ok": False, "reason": self.last_error, "backend": result.backend}

            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            heard = recognizer.recognize_google(audio)
            return self.handle_text(heard, source="microphone:google")
        except Exception as exc:
            self.last_error = str(exc)
            self._persist()
            return {"ok": False, "reason": self.last_error}

    def run_polling(self, interval: float = 1.0) -> None:
        self.running = True
        self._persist()
        safe_print("VOICE LOOP: inbox mode active")
        safe_print(f"VOICE LOOP: inbox={self.voice_bridge.inbox_path}")
        self._speak("Voice conversation loop online.")
        while self.running:
            try:
                result = self.process_inbox()
                if result.get("processed"):
                    safe_print(f"VOICE LOOP: processed {result.get('processed', 0)} queued voice command(s)")
            except Exception as exc:
                self.last_error = str(exc)
                safe_print(f"VOICE LOOP: error -> {self.last_error}")
                self._persist()
            else:
                self._persist()
            time.sleep(interval)

    def stop(self) -> None:
        self.running = False
        self._persist()

    def status(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "speech_recognition_available": HAS_SPEECH_RECOGNITION,
            "pocketsphinx_available": HAS_POCKETSPHINX,
            "voice_output_available": self.voice_engine is not None or self.local_tts_enabled,
            "last_error": self.last_error,
            "last_heard": self.last_heard,
            "last_reply": self.last_reply,
            "recent_exchanges": self.recent_exchanges[-10:],
            "voice_adapter": self.voice_adapter.status() if self.voice_adapter is not None else {},
            "voice_bridge": self.voice_bridge.status(),
            "memory": self.memory.status(),
        }

    def _build_reply(self, text: str, result: Dict[str, Any]) -> str:
        route = str(result.get("route") or "")
        if route == "approve_desktop":
            inner = result.get("result") or {}
            if result.get("ok"):
                return "I approved the next desktop action."
            return f"I could not approve a desktop action: {inner.get('reason', 'nothing pending')}."
        if route == "approve_code":
            inner = result.get("result") or {}
            if result.get("ok"):
                return "I approved the next code proposal."
            return f"I could not approve a code proposal: {inner.get('reason', 'nothing pending')}."
        if route == "reject_code":
            inner = result.get("result") or {}
            if result.get("ok"):
                return "I rejected the next code proposal."
            return f"I could not reject a code proposal: {inner.get('reason', 'nothing pending')}."
        if route == "clear_desktop_pending":
            return "I cleared pending desktop actions."
        if route == "arm_desktop_dry":
            return "Desktop control is armed in dry-run mode."
        if route == "arm_desktop_live":
            return "Desktop control is armed in live mode."
        if route == "disarm_desktop":
            return "Desktop control is disarmed."
        if route == "clear_code_pending":
            return "I cleared pending code proposals."
        if route == "repo_search":
            hits = result.get("hits") or []
            return f"I searched the repo for {text}. I found {len(hits)} top matches and queued the search result."
        if route == "repo_inspect":
            file_info = result.get("file") or {}
            path = file_info.get("path") or "that file"
            return f"I inspected {path} and queued it for review."
        if route == "dynamic_external_skill":
            return str(result.get("message") or "I prepared that external request.")
        if route == "dynamic_wiki_grounding":
            if result.get("ok"):
                wiki = result.get("wiki_context") or {}
                return f"I used Wikipedia to ground your request around {wiki.get('title', 'that topic')} and prepared the next action."
            return "I tried to ground that request with Wikipedia, but I still need a clearer instruction."
        if route == "meta_reflection":
            return str(result.get("message") or "I reflected on your request.")
        if route == "meta_help":
            return str(result.get("message") or "I can help with repo, code, and desktop commands.")
        if route == "meta_clarify":
            return str(result.get("reason") or "I need more detail to understand that command.")
        if route == "code_proposal":
            return "I turned that into a code proposal and queued it for review."
        if route in {"desktop_type_proposal", "desktop_key_proposal"}:
            proposal = result.get("proposal") or {}
            if proposal.get("status") == "executed":
                return "I executed that desktop action."
            return "I converted that into a desktop action proposal. It still needs approval."
        if route in {"desktop_move_proposal", "desktop_click_proposal"}:
            proposal = result.get("proposal") or {}
            if proposal.get("status") == "executed":
                return "I executed that desktop action."
            return "I queued that desktop action. It still needs approval."
        if route == "desktop_emergency_stop":
            return "Emergency stop is now active."
        if route == "generic_task":
            return "I queued that as a task."
        if not result.get("ok", False):
            return f"I could not process that command: {result.get('reason', 'unknown error')}."
        return "Command processed."

    def _handle_agent_command(self, text: str, source: str) -> Dict[str, Any]:
        lower = text.strip().lower()
        desktop_ctl = self.voice_bridge.desktop_control
        code_ctl = self.voice_bridge.code_control

        if lower in {"approve next desktop action", "approve desktop action"}:
            result = desktop_ctl.approve_next(confirm_token=desktop_ctl.confirmation_token)
            return {"ok": bool(result.ok), "route": "approve_desktop", "result": result.__dict__}
        if lower in {"arm desktop dry run", "arm desktop dry", "enable desktop dry run"}:
            desktop_ctl.arm_dry_run()
            return {"ok": True, "route": "arm_desktop_dry"}
        if lower in {"arm desktop live", "enable live desktop", "enable desktop live mode"}:
            desktop_ctl.arm_live()
            return {"ok": True, "route": "arm_desktop_live"}
        if lower in {"disarm desktop", "disable desktop control"}:
            desktop_ctl.disarm()
            return {"ok": True, "route": "disarm_desktop"}
        if lower in {"clear desktop actions", "clear pending desktop actions"}:
            desktop_ctl.clear_pending()
            return {"ok": True, "route": "clear_desktop_pending"}
        if lower in {"approve next code proposal", "approve code proposal"}:
            result = code_ctl.approve_next(reviewer=f"voice:{source}")
            return {"ok": bool(result.get("ok")), "route": "approve_code", "result": result}
        if lower in {"reject next code proposal", "reject code proposal"}:
            result = code_ctl.reject_next(reviewer=f"voice:{source}", reason="voice_rejected")
            return {"ok": bool(result.get("ok")), "route": "reject_code", "result": result}
        if lower in {"clear code proposals", "clear pending code proposals"}:
            code_ctl.clear_pending()
            return {"ok": True, "route": "clear_code_pending"}
        return self.voice_bridge.submit_command(text=text, source=source)

    def _speak(self, text: str) -> None:
        if self.voice_engine is not None:
            try:
                self.voice_engine.speak(text, priority=2, category="status")
                return
            except Exception as exc:
                self.last_error = str(exc)
        if not self.local_tts_enabled or not HAS_PYTTSX3 or pyttsx3 is None:
            return
        try:
            with self._local_tts_lock:
                if self._local_tts_engine is None:
                    self._local_tts_engine = pyttsx3.init()
                    self._local_tts_engine.setProperty("rate", 175)
                self._local_tts_engine.say(text)
                self._local_tts_engine.runAndWait()
        except Exception as exc:
            self.last_error = str(exc)

    def _persist(self) -> None:
        self.state_path.write_text(json.dumps(self.status(), indent=2), encoding="utf-8")


def build_default_conversation_loop(speak_enabled: bool = True) -> ConversationLoop:
    return ConversationLoop(speak_enabled=speak_enabled)


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe local voice conversation loop")
    parser.add_argument("--say", type=str, default="", help="Process a single text command and reply")
    parser.add_argument("--poll", action="store_true", help="Poll the simulated inbox continuously")
    parser.add_argument("--agent", action="store_true", help="Run continuous safe agent mode")
    parser.add_argument("--mic-agent", action="store_true", help="Run continuous agent mode using microphone when available")
    parser.add_argument("--listen-once", action="store_true", help="Capture a single microphone utterance")
    parser.add_argument("--no-speak", action="store_true", help="Disable spoken replies")
    args = parser.parse_args()

    loop = build_default_conversation_loop(speak_enabled=not args.no_speak)

    if args.say:
        safe_print("VOICE LOOP: one-shot text mode")
        print(json.dumps(loop.handle_text(args.say, source="cli"), indent=2))
        return 0
    if args.listen_once:
        safe_print("VOICE LOOP: microphone single-shot mode")
        print(json.dumps(loop.listen_once(), indent=2))
        return 0
    if args.poll:
        safe_print("VOICE LOOP: starting continuous inbox polling")
        try:
            loop.run_polling(interval=1.0)
        except KeyboardInterrupt:
            loop.stop()
        return 0
    if args.agent or args.mic_agent:
        safe_print("VOICE LOOP: starting continuous agent mode")
        try:
            loop.run_agent_mode(interval=1.0, microphone=args.mic_agent)
        except KeyboardInterrupt:
            loop.stop()
        return 0

    safe_print("VOICE LOOP: status mode")
    print(json.dumps(loop.status(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
