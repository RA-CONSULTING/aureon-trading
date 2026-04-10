"""
Primitives — the safe callables that skills can use
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Every self-written skill runs in a sandboxed exec context where the only
callables available are:

  • VM control primitives      (screenshot, click, type_text, hotkey, …)
  • Local agent primitives     (execute_shell via the SafeDesktopControl stub)
  • Skill library primitives   (call_skill — invoke another skill by name)
  • Math + time + random utils (deterministic, safe standard library)
  • Logging primitive          (emit_event)

Nothing else. No `open()` writes, no imports, no eval/exec, no __import__,
no network calls beyond what the VM control layer exposes.

The safe globals dict is assembled by `get_safe_globals(executor)` and
passed into exec() by the SkillExecutor.
"""

from __future__ import annotations

import json
import logging
import math
import random
import time
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("aureon.code_architect.primitives")


# ─────────────────────────────────────────────────────────────────────────────
# VM primitive factory
# ─────────────────────────────────────────────────────────────────────────────


def _vm_primitive_factory(dispatcher: Any, action: str) -> Callable:
    """Build a primitive that routes into the VM dispatcher."""

    def primitive(**kwargs) -> Dict[str, Any]:
        session_id = kwargs.pop("session_id", None)
        return dispatcher.dispatch(
            action_name=action,
            params=dict(kwargs),
            session_id=session_id,
            source="code_architect:skill",
        )

    primitive.__name__ = f"vm_{action}"
    return primitive


VM_ACTION_NAMES: List[str] = [
    "screenshot",
    "mouse_move",
    "left_click",
    "right_click",
    "middle_click",
    "double_click",
    "triple_click",
    "left_click_drag",
    "scroll",
    "type_text",
    "press_key",
    "hotkey",
    "get_cursor_position",
    "get_screen_size",
    "list_windows",
    "get_active_window",
    "focus_window",
    "wait",
    "execute_shell",
    "execute_powershell",
]


# ─────────────────────────────────────────────────────────────────────────────
# Non-VM primitives
# ─────────────────────────────────────────────────────────────────────────────


def _emit_event_factory(thought_bus: Any, source: str = "skill") -> Callable:
    def emit_event(topic: str, payload: Any = None) -> Dict[str, Any]:
        if not thought_bus:
            return {"ok": False, "error": "no_thought_bus"}
        try:
            from aureon.core.aureon_thought_bus import Thought
            thought_bus.publish(Thought(
                source=source,
                topic=str(topic),
                payload=payload if isinstance(payload, dict) else {"value": payload},
            ))
            return {"ok": True, "topic": topic}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    return emit_event


def _call_skill_factory(executor: Any) -> Callable:
    """
    Returns the `call_skill(name, **kwargs)` primitive so a compound skill
    can invoke lower-level skills.
    """

    def call_skill(name: str, **kwargs) -> Dict[str, Any]:
        if not executor:
            return {"ok": False, "error": "no_executor"}
        try:
            result = executor.execute_by_name(
                skill_name=str(name),
                params=kwargs,
                _depth=1,
            )
            return {
                "ok": result.ok,
                "skill": name,
                "duration_s": result.duration_s,
                "return_value": result.return_value,
                "error": result.error,
            }
        except Exception as e:
            return {"ok": False, "skill": name, "error": str(e)}

    return call_skill


def _safe_sleep(seconds: float) -> Dict[str, Any]:
    """Sleep, capped at 30 seconds for safety."""
    seconds = max(0.0, min(float(seconds), 30.0))
    time.sleep(seconds)
    return {"ok": True, "waited_s": seconds}


def _safe_log(message: str, level: str = "info") -> Dict[str, Any]:
    """Emit a log line from within a skill."""
    level_lower = str(level).lower()
    fn = getattr(logger, level_lower, logger.info)
    fn("[skill] %s", message)
    return {"ok": True}


# ─────────────────────────────────────────────────────────────────────────────
# Assembly
# ─────────────────────────────────────────────────────────────────────────────


PRIMITIVE_NAMES: List[str] = [
    # VM
    *[f"vm_{a}" for a in VM_ACTION_NAMES],
    # Utilities
    "emit_event",
    "call_skill",
    "safe_sleep",
    "safe_log",
    # Math / std
    "math",
    "random",
    "json",
    # Helpers
    "time_now",
]


def get_primitives(
    dispatcher: Any = None,
    thought_bus: Any = None,
    executor: Any = None,
) -> Dict[str, Any]:
    """
    Build the full primitives dict.

    Args:
        dispatcher: VMControlDispatcher (optional) — enables vm_* primitives
        thought_bus: ThoughtBus (optional) — enables emit_event
        executor: SkillExecutor (optional) — enables call_skill
    """
    primitives: Dict[str, Any] = {}

    # VM primitives
    if dispatcher is not None:
        for action in VM_ACTION_NAMES:
            primitives[f"vm_{action}"] = _vm_primitive_factory(dispatcher, action)

    # Event emitter
    primitives["emit_event"] = _emit_event_factory(thought_bus, source="skill")

    # Skill-calls-skill
    primitives["call_skill"] = _call_skill_factory(executor)

    # Safe utils
    primitives["safe_sleep"] = _safe_sleep
    primitives["safe_log"] = _safe_log
    primitives["time_now"] = lambda: time.time()

    # Standard-library-but-safe namespaces (read-only access)
    primitives["math"] = math
    primitives["random"] = random
    primitives["json"] = json

    return primitives


# ─────────────────────────────────────────────────────────────────────────────
# Safe globals for exec()
# ─────────────────────────────────────────────────────────────────────────────


# A minimal __builtins__ dict — no open(), no __import__, no exec, no eval
SAFE_BUILTINS: Dict[str, Any] = {
    # Types
    "bool": bool,
    "int": int,
    "float": float,
    "str": str,
    "bytes": bytes,
    "list": list,
    "tuple": tuple,
    "dict": dict,
    "set": set,
    "frozenset": frozenset,
    # Iteration
    "len": len,
    "range": range,
    "enumerate": enumerate,
    "zip": zip,
    "map": map,
    "filter": filter,
    "reversed": reversed,
    "sorted": sorted,
    "all": all,
    "any": any,
    "sum": sum,
    "min": min,
    "max": max,
    "abs": abs,
    "round": round,
    # Introspection (read-only)
    "isinstance": isinstance,
    "issubclass": issubclass,
    "hasattr": hasattr,
    "getattr": getattr,           # we'll reject dunder access at AST level
    "type": type,
    # Output (harmless)
    "print": print,
    "repr": repr,
    # None/True/False are keywords, not builtins
}


def get_safe_globals(
    dispatcher: Any = None,
    thought_bus: Any = None,
    executor: Any = None,
) -> Dict[str, Any]:
    """
    Return the globals dict to pass to exec() when running a skill.

    This dict contains:
      • SAFE_BUILTINS in __builtins__
      • All primitives
      • Nothing else.
    """
    primitives = get_primitives(
        dispatcher=dispatcher,
        thought_bus=thought_bus,
        executor=executor,
    )
    globals_dict: Dict[str, Any] = {
        "__builtins__": SAFE_BUILTINS,
        **primitives,
    }
    return globals_dict
