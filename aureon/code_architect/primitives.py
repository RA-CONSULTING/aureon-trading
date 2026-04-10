"""
Primitives — the safe callables that skills can use
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Every self-written skill runs in a sandboxed exec context where the only
callables available are:

  • VM control primitives      (screenshot, click, type_text, hotkey, …)
  • Local agent primitives     (execute_shell via the SafeDesktopControl stub)
  • Skill library primitives   (call_skill — invoke another skill by name)
  • Cognitive primitives       (ai_reason, consult_queen, consult_pillars,
                                 synthesise_insight, remember, recall)
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
from typing import Any, Callable, Dict, List

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
# Cognitive primitives — the building blocks of LLM-level capabilities
# ─────────────────────────────────────────────────────────────────────────────


def _ai_reason_factory() -> Callable:
    """
    ai_reason(query, context=None, max_tokens=512) — wraps the in-house
    AureonBrainAdapter.prompt() so skills can reason in-sandbox.

    The adapter is loaded lazily and cached at module level.
    """
    _state = {"adapter": None, "loaded": False}

    def _get_adapter():
        if _state["loaded"]:
            return _state["adapter"]
        _state["loaded"] = True
        try:
            from aureon.inhouse_ai.llm_adapter import AureonBrainAdapter
            _state["adapter"] = AureonBrainAdapter()
        except Exception:
            _state["adapter"] = None
        return _state["adapter"]

    def ai_reason(query: str, context: Any = None, max_tokens: int = 512) -> Dict[str, Any]:
        adapter = _get_adapter()
        if adapter is None:
            return {"ok": False, "error": "no_adapter", "text": ""}

        messages = [{"role": "user", "content": str(query)}]
        system = "You are the Aureon reasoning engine. Be precise and actionable."
        if context is not None:
            try:
                ctx_str = json.dumps(context, default=str)[:1200]
                system = f"{system}\nContext: {ctx_str}"
            except Exception:
                pass

        try:
            response = adapter.prompt(
                messages=messages,
                system=system,
                max_tokens=int(max_tokens),
            )
            return {
                "ok": True,
                "text": response.text,
                "stop_reason": response.stop_reason,
                "model": response.model,
            }
        except Exception as e:
            return {"ok": False, "error": str(e), "text": ""}

    return ai_reason


def _consult_queen_factory() -> Callable:
    """consult_queen(query, context=None) — calls QueenAIBridge.reason()."""
    _state = {"bridge": None, "loaded": False}

    def _get_bridge():
        if _state["loaded"]:
            return _state["bridge"]
        _state["loaded"] = True
        try:
            from aureon.queen.queen_inhouse_ai_bridge import get_queen_ai_bridge
            _state["bridge"] = get_queen_ai_bridge()
        except Exception:
            _state["bridge"] = None
        return _state["bridge"]

    def consult_queen(query: str, context: Any = None) -> Dict[str, Any]:
        bridge = _get_bridge()
        if bridge is None or not getattr(bridge, "is_alive", False):
            return {"ok": False, "error": "queen_unavailable", "text": ""}
        try:
            text = bridge.reason(query=str(query), context=context if isinstance(context, dict) else None)
            return {"ok": True, "text": text, "source": "queen"}
        except Exception as e:
            return {"ok": False, "error": str(e), "text": ""}

    return consult_queen


def _consult_pillars_factory() -> Callable:
    """consult_pillars(signals=None) — runs PillarAlignment.run_synthetic_cycle."""
    _state = {"alignment": None, "loaded": False}

    def _get_alignment():
        if _state["loaded"]:
            return _state["alignment"]
        _state["loaded"] = True
        try:
            from aureon.alignment.pillar_alignment import PillarAlignment, AlignmentConfig
            _state["alignment"] = PillarAlignment(AlignmentConfig(auto_load_pillars=False))
        except Exception:
            _state["alignment"] = None
        return _state["alignment"]

    def consult_pillars(signals: Any = None) -> Dict[str, Any]:
        alignment = _get_alignment()
        if alignment is None:
            return {"ok": False, "error": "alignment_unavailable"}
        try:
            result = alignment.run_synthetic_cycle(signals=signals if isinstance(signals, list) else None)
            return {
                "ok": True,
                "signal": result.consensus_signal,
                "confidence": result.consensus_confidence,
                "alignment_score": result.alignment_score,
                "lighthouse": result.lighthouse_cleared,
                "agreeing_pillars": result.agreeing_pillars,
                "total_pillars": result.total_pillars,
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    return consult_pillars


def _synthesise_insight_factory() -> Callable:
    """synthesise_insight(market_data, signals=None) — calls MinerAIBridge."""
    _state = {"bridge": None, "loaded": False}

    def _get_bridge():
        if _state["loaded"]:
            return _state["bridge"]
        _state["loaded"] = True
        try:
            from aureon.miner.miner_inhouse_ai_bridge import get_miner_ai_bridge
            _state["bridge"] = get_miner_ai_bridge()
        except Exception:
            _state["bridge"] = None
        return _state["bridge"]

    def synthesise_insight(market_data: Any = None, signals: Any = None) -> Dict[str, Any]:
        bridge = _get_bridge()
        if bridge is None or not getattr(bridge, "is_alive", False):
            return {"ok": False, "error": "miner_unavailable"}
        try:
            md = market_data if isinstance(market_data, dict) else {}
            sigs = signals if isinstance(signals, list) else None
            insight = bridge.synthesise_insight(market_data=md, system_signals=sigs)
            return {
                "ok": True,
                "signal": insight.signal,
                "confidence": insight.confidence,
                "coherence": insight.coherence,
                "reasoning": insight.reasoning[:300] if insight.reasoning else "",
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    return synthesise_insight


def _remember_factory(executor: Any) -> Callable:
    """remember(skill_name, key, value) — stores metadata on a stored skill."""

    def remember(skill_name: str, key: str, value: Any) -> Dict[str, Any]:
        if executor is None or getattr(executor, "library", None) is None:
            return {"ok": False, "error": "no_library"}
        lib = executor.library
        skill = lib.get(str(skill_name))
        if skill is None:
            return {"ok": False, "error": "skill_not_found"}
        if not hasattr(skill, "harmonic_signature") or skill.harmonic_signature is None:
            skill.harmonic_signature = {}
        # Store in tags or harmonic_signature as a side channel
        try:
            # Use a dedicated metadata map via tags — tag format: "mem:key=serialised"
            tag_prefix = f"mem:{key}="
            skill.tags = [t for t in (skill.tags or []) if not t.startswith(tag_prefix)]
            serialised = str(value)[:200]
            skill.tags.append(tag_prefix + serialised)
            return {"ok": True, "skill": skill_name, "key": key}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    return remember


def _recall_factory(executor: Any) -> Callable:
    """recall(skill_name, key) — retrieves metadata from a stored skill."""

    def recall(skill_name: str, key: str) -> Dict[str, Any]:
        if executor is None or getattr(executor, "library", None) is None:
            return {"ok": False, "error": "no_library"}
        lib = executor.library
        skill = lib.get(str(skill_name))
        if skill is None:
            return {"ok": False, "error": "skill_not_found"}
        tag_prefix = f"mem:{key}="
        for tag in skill.tags or []:
            if tag.startswith(tag_prefix):
                return {"ok": True, "value": tag[len(tag_prefix):]}
        return {"ok": False, "error": "key_not_found"}

    return recall


def _list_skills_factory(executor: Any) -> Callable:
    """list_skills(level=None) — returns the names of skills in the library."""

    def list_skills(level: Any = None) -> Dict[str, Any]:
        if executor is None or getattr(executor, "library", None) is None:
            return {"ok": False, "error": "no_library"}
        lib = executor.library
        try:
            if level is not None:
                from aureon.code_architect.skill import SkillLevel
                lvl = SkillLevel(int(level))
                names = [s.name for s in lib.by_level(lvl)]
            else:
                names = [s.name for s in lib.all()]
            return {"ok": True, "skills": names, "count": len(names)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    return list_skills


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
    # Cognitive — LLM-level building blocks
    "ai_reason",
    "consult_queen",
    "consult_pillars",
    "synthesise_insight",
    "remember",
    "recall",
    "list_skills",
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
        executor: SkillExecutor (optional) — enables call_skill + memory
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

    # Cognitive primitives — the building blocks of LLM capabilities
    primitives["ai_reason"] = _ai_reason_factory()
    primitives["consult_queen"] = _consult_queen_factory()
    primitives["consult_pillars"] = _consult_pillars_factory()
    primitives["synthesise_insight"] = _synthesise_insight_factory()
    primitives["remember"] = _remember_factory(executor)
    primitives["recall"] = _recall_factory(executor)
    primitives["list_skills"] = _list_skills_factory(executor)

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
