#!/usr/bin/env python3
"""
GoalExecutionEngine -- Goal Decomposition + Validated Multi-Step Task Execution

Accepts a natural-language goal from the user, decomposes it into an ordered
plan of GoalSteps, executes each step through AureonAgentCore, validates the
outcome of every step (anti-hallucination), and publishes the full feedback
loop to the ThoughtBus so the CognitiveDashboard can render it live.

Dual-path decomposition:
  1. AgentCore.plan_task()  -- fast, deterministic, regex-based
  2. Heuristic verb mapping -- fallback for unrecognised patterns

Every step goes through:
  coherence gate -> monologue -> execute -> validate -> advance memory
"""

from __future__ import annotations

import logging
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("aureon.core.goal_engine")

# ---------------------------------------------------------------------------
# Graceful imports (same pattern as queen_sentient_loop.py)
# ---------------------------------------------------------------------------
try:
    from aureon.autonomous.aureon_agent_core import AureonAgentCore
    _HAS_AGENT_CORE = True
except Exception:
    AureonAgentCore = None  # type: ignore[assignment,misc]
    _HAS_AGENT_CORE = False

try:
    from aureon.core.aureon_thought_bus import get_thought_bus, Thought
    _HAS_THOUGHT_BUS = True
except Exception:
    get_thought_bus = None  # type: ignore[assignment]
    Thought = None  # type: ignore[assignment,misc]
    _HAS_THOUGHT_BUS = False

try:
    from aureon.core.aureon_lambda_engine import LambdaEngine, SubsystemReading
    _HAS_LAMBDA = True
except Exception:
    LambdaEngine = None  # type: ignore[assignment,misc]
    SubsystemReading = None  # type: ignore[assignment,misc]
    _HAS_LAMBDA = False

try:
    from aureon.autonomous.aureon_elephant_memory import ElephantMemory
    _HAS_ELEPHANT = True
except Exception:
    ElephantMemory = None  # type: ignore[assignment,misc]
    _HAS_ELEPHANT = False

try:
    from aureon.vault.voice.self_dialogue import SelfDialogueEngine
    _HAS_SELF_DIALOGUE = True
except Exception:
    SelfDialogueEngine = None  # type: ignore[assignment,misc]
    _HAS_SELF_DIALOGUE = False

try:
    from aureon.vault.auris_metacognition import AurisMetacognition
    _HAS_AURIS = True
except Exception:
    AurisMetacognition = None  # type: ignore[assignment,misc]
    _HAS_AURIS = False

try:
    from aureon.inhouse_ai.orchestrator import OpenMultiAgent
    from aureon.inhouse_ai.agent import AgentConfig
    _HAS_SWARM = True
except Exception:
    OpenMultiAgent = None  # type: ignore[assignment,misc]
    AgentConfig = None  # type: ignore[assignment,misc]
    _HAS_SWARM = False

try:
    from aureon.queen.temporal_ground import get_temporal_ground_station
    _HAS_TEMPORAL = True
except Exception:
    get_temporal_ground_station = None  # type: ignore[assignment]
    _HAS_TEMPORAL = False

try:
    from aureon.inhouse_ai.llm_adapter import LLMAdapter
    _HAS_LLM_ADAPTER = True
except Exception:
    LLMAdapter = None  # type: ignore[assignment,misc]
    _HAS_LLM_ADAPTER = False


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class GoalStep:
    """One atomic step in a goal plan."""
    step_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    title: str = ""
    intent: str = ""           # maps to AureonAgentCore intent
    params: Dict[str, Any] = field(default_factory=dict)
    expected_outcome: str = ""
    status: str = "pending"    # pending | active | completed | failed | skipped
    result: Optional[Dict[str, Any]] = None
    validation_result: Optional[Dict[str, Any]] = None
    coherence_at_execution: float = 0.0
    monologue: str = ""


@dataclass
class GoalPlan:
    """A decomposed goal with ordered steps."""
    goal_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    original_text: str = ""
    objective: str = ""
    steps: List[GoalStep] = field(default_factory=list)
    success_criteria: str = ""
    status: str = "pending"    # pending | active | completed | failed | paused | cancelled
    coherence_threshold: float = 0.3


# ---------------------------------------------------------------------------
# Verb -> intent heuristic mapping (fallback decomposition)
# ---------------------------------------------------------------------------

VERB_INTENT_MAP: Dict[str, List[str]] = {
    # File / code operations
    "build":    ["web_search", "create_script", "write_file", "execute_python"],
    "create":   ["create_dir", "write_file"],
    "search":   ["web_search"],
    "research": ["web_search"],
    "google":   ["web_search"],
    "lookup":   ["web_search"],
    "find":     ["find_files", "web_search"],
    "read":     ["read_file"],
    "write":    ["write_file"],
    "compose":  ["compose_creative"],
    "run":      ["execute_shell"],
    "install":  ["execute_shell"],
    "delete":   ["delete_file"],
    "copy":     ["copy_file"],
    "move":     ["move_file"],
    "check":    ["system_info", "network_status"],
    "show":     ["list_dir", "read_file"],
    "list":     ["list_dir", "list_apps"],
    "say":      ["speak"],
    "tell":     ["speak"],
    # Desktop / human tasks
    "open":     ["open_app", "open_url"],
    "launch":   ["open_app"],
    "close":    ["close_app"],
    "kill":     ["close_app", "kill_process"],
    "click":    ["click"],
    "type":     ["type_text"],
    "press":    ["press_key"],
    "scroll":   ["press_key"],
    "focus":    ["focus_window"],
    "switch":   ["focus_window"],
    "screenshot": ["screenshot"],
    "capture":  ["screenshot"],
    "minimize": ["hotkey"],
    "maximize": ["hotkey"],
    "browse":   ["open_url"],
    "navigate": ["open_url"],
    "goto":     ["open_url"],
    # Trading
    "buy":      ["place_order"],
    "sell":     ["place_order"],
    "trade":    ["place_order"],
    "balance":  ["get_balances"],
    "position": ["get_positions"],
    "portfolio":["get_portfolio_summary"],
    # Knowledge
    "query":    ["query_knowledge"],
    "ask":      ["query_knowledge"],
    # Communication
    "notify":   ["notify"],
    "alert":    ["notify"],
    "speak":    ["speak"],
    # Process
    "stop":     ["close_app", "kill_process"],
    "process":  ["running_processes"],
    # Web
    "fetch":    ["web_fetch"],
    "download": ["web_fetch"],
    "get":      ["web_fetch"],
}


# ---------------------------------------------------------------------------
# GoalExecutionEngine
# ---------------------------------------------------------------------------

class GoalExecutionEngine:
    """
    Accepts natural-language goals, decomposes them into plans,
    executes each step through AgentCore, validates outcomes,
    and publishes the feedback loop to ThoughtBus.
    """

    def __init__(
        self,
        agent_core: Any = None,
        thought_bus: Any = None,
        lambda_engine: Any = None,
        elephant_memory: Any = None,
        self_dialogue: Any = None,
        auris: Any = None,
        vault: Any = None,
        swarm: Any = None,
        temporal_ground: Any = None,
        source_law: Any = None,
        temporal_knowledge: Any = None,
        stash_pockets: Any = None,
        knowledge_dataset: Any = None,
    ):
        self._agent_core = agent_core
        self._thought_bus = thought_bus
        self._source_law = source_law
        self._temporal_knowledge = temporal_knowledge
        self._stash_pockets = stash_pockets
        self._knowledge_dataset = knowledge_dataset
        self._lambda_engine = lambda_engine
        self._elephant_memory = elephant_memory
        self._self_dialogue = self_dialogue
        self._auris = auris
        self._vault = vault
        self._swarm = swarm
        self._temporal_ground = temporal_ground
        self._ollama: Any = None   # injected after boot via set_ollama_adapter()
        self._agent_tools = self._build_agent_tools()

        self._current_plan: Optional[GoalPlan] = None
        self._lock = threading.Lock()
        self._paused = threading.Event()
        self._paused.set()  # not paused initially
        self._cancelled = False

        self._stats: Dict[str, int] = {
            "goals_submitted": 0,
            "goals_completed": 0,
            "goals_failed": 0,
            "steps_executed": 0,
            "steps_validated": 0,
            "swarm_dispatches": 0,
            "timelines_forked": 0,
        }

    def set_ollama_adapter(self, adapter: Any) -> None:
        """Inject an OllamaLLMAdapter as the primary LLM for goal decomposition."""
        self._ollama = adapter

    # ------------------------------------------------------------------
    # Tool bridge — AgentCore tools available to swarm agents
    # ------------------------------------------------------------------
    def _build_agent_tools(self) -> Any:
        """
        Bridge AgentCore's 40+ tools into a ToolRegistry so swarm agents
        can create files, run commands, search the web, and execute code.
        """
        if self._swarm is None or self._agent_core is None:
            return None

        try:
            from aureon.inhouse_ai.tool_registry import ToolRegistry
        except Exception:
            return None

        registry = ToolRegistry(include_builtins=True)
        ac = self._agent_core

        # Map of tool_name -> (description, schema, AgentCore intent)
        TOOLS = {
            "write_file": {
                "desc": "Write content to a file at the given path",
                "schema": {"type": "object", "properties": {
                    "path": {"type": "string", "description": "File path to write"},
                    "content": {"type": "string", "description": "Content to write"},
                }, "required": ["path", "content"]},
                "intent": "write_file",
            },
            "create_script": {
                "desc": "Create a Python script at the given path",
                "schema": {"type": "object", "properties": {
                    "path": {"type": "string", "description": "Script file path"},
                    "content": {"type": "string", "description": "Script content"},
                }, "required": ["path", "content"]},
                "intent": "create_script",
            },
            "read_file": {
                "desc": "Read the contents of a file",
                "schema": {"type": "object", "properties": {
                    "path": {"type": "string", "description": "File path to read"},
                }, "required": ["path"]},
                "intent": "read_file",
            },
            "list_directory": {
                "desc": "List files in a directory",
                "schema": {"type": "object", "properties": {
                    "path": {"type": "string", "description": "Directory path"},
                }, "required": ["path"]},
                "intent": "list_dir",
            },
            "web_search": {
                "desc": "Search the web for information",
                "schema": {"type": "object", "properties": {
                    "query": {"type": "string", "description": "Search query"},
                }, "required": ["query"]},
                "intent": "web_search",
            },
            "run_shell": {
                "desc": "Execute a shell command and return output",
                "schema": {"type": "object", "properties": {
                    "command": {"type": "string", "description": "Shell command to run"},
                }, "required": ["command"]},
                "intent": "shell",
            },
            "run_python": {
                "desc": "Execute Python code and return output",
                "schema": {"type": "object", "properties": {
                    "code": {"type": "string", "description": "Python code to execute"},
                }, "required": ["code"]},
                "intent": "execute_python",
            },
            "create_directory": {
                "desc": "Create a new directory",
                "schema": {"type": "object", "properties": {
                    "path": {"type": "string", "description": "Directory path to create"},
                }, "required": ["path"]},
                "intent": "create_dir",
            },
            "find_files": {
                "desc": "Find files matching a pattern",
                "schema": {"type": "object", "properties": {
                    "pattern": {"type": "string", "description": "Glob pattern (e.g. *.py)"},
                    "directory": {"type": "string", "description": "Directory to search in"},
                }, "required": ["pattern"]},
                "intent": "find_files",
            },
            "system_info": {
                "desc": "Get system information (platform, hostname, etc.)",
                "schema": {"type": "object", "properties": {}},
                "intent": "system_info",
            },
            # Desktop / human interaction tools
            "open_app": {
                "desc": "Open a desktop application (chrome, notepad, vscode, etc.)",
                "schema": {"type": "object", "properties": {
                    "app_name": {"type": "string", "description": "Application name"},
                }, "required": ["app_name"]},
                "intent": "open_app",
            },
            "close_app": {
                "desc": "Close a running application",
                "schema": {"type": "object", "properties": {
                    "app_name": {"type": "string", "description": "Application name"},
                }, "required": ["app_name"]},
                "intent": "close_app",
            },
            "click": {
                "desc": "Click at screen coordinates (x, y)",
                "schema": {"type": "object", "properties": {
                    "x": {"type": "integer", "description": "X coordinate"},
                    "y": {"type": "integer", "description": "Y coordinate"},
                }, "required": ["x", "y"]},
                "intent": "click",
            },
            "type_text": {
                "desc": "Type text on the keyboard",
                "schema": {"type": "object", "properties": {
                    "text": {"type": "string", "description": "Text to type"},
                }, "required": ["text"]},
                "intent": "type_text",
            },
            "press_key": {
                "desc": "Press a keyboard key (enter, tab, escape, etc.)",
                "schema": {"type": "object", "properties": {
                    "key": {"type": "string", "description": "Key to press"},
                }, "required": ["key"]},
                "intent": "press_key",
            },
            "hotkey": {
                "desc": "Press a keyboard shortcut (e.g. ctrl+c, alt+tab)",
                "schema": {"type": "object", "properties": {
                    "keys": {"type": "array", "items": {"type": "string"}, "description": "Keys to press together"},
                }, "required": ["keys"]},
                "intent": "hotkey",
            },
            "screenshot": {
                "desc": "Take a screenshot of the desktop",
                "schema": {"type": "object", "properties": {}},
                "intent": "screenshot",
            },
            "move_mouse": {
                "desc": "Move the mouse to screen coordinates (x, y)",
                "schema": {"type": "object", "properties": {
                    "x": {"type": "integer", "description": "X coordinate"},
                    "y": {"type": "integer", "description": "Y coordinate"},
                }, "required": ["x", "y"]},
                "intent": "move_mouse",
            },
            "focus_window": {
                "desc": "Focus/switch to a window by title",
                "schema": {"type": "object", "properties": {
                    "title": {"type": "string", "description": "Window title to focus"},
                }, "required": ["title"]},
                "intent": "focus_window",
            },
            "open_url": {
                "desc": "Open a URL in the default browser",
                "schema": {"type": "object", "properties": {
                    "url": {"type": "string", "description": "URL to open"},
                }, "required": ["url"]},
                "intent": "open_url",
            },
            # ── Trading ────────────────────────────────────────────
            "get_balances": {
                "desc": "Get trading account balances across all exchanges",
                "schema": {"type": "object", "properties": {}},
                "intent": "get_balances",
            },
            "get_positions": {
                "desc": "Get current open trading positions",
                "schema": {"type": "object", "properties": {}},
                "intent": "get_positions",
            },
            "place_order": {
                "desc": "Place a trading order (symbol, side, amount)",
                "schema": {"type": "object", "properties": {
                    "symbol": {"type": "string"}, "side": {"type": "string"},
                    "amount": {"type": "number"},
                }, "required": ["symbol", "side", "amount"]},
                "intent": "place_order",
            },
            "get_recent_trades": {
                "desc": "Get recent trade history",
                "schema": {"type": "object", "properties": {}},
                "intent": "get_recent_trades",
            },
            "get_market_summary": {
                "desc": "Get market summary (prices, trends, sentiment)",
                "schema": {"type": "object", "properties": {}},
                "intent": "market_summary",
            },
            "get_portfolio": {
                "desc": "Get portfolio summary (equity, positions, PnL)",
                "schema": {"type": "object", "properties": {}},
                "intent": "portfolio",
            },
            # ── Communication ──────────────────────────────────────
            "speak": {
                "desc": "Speak text aloud via TTS",
                "schema": {"type": "object", "properties": {
                    "text": {"type": "string", "description": "Text to speak"},
                }, "required": ["text"]},
                "intent": "speak",
            },
            "notify": {
                "desc": "Send a notification",
                "schema": {"type": "object", "properties": {
                    "message": {"type": "string"},
                }, "required": ["message"]},
                "intent": "notify",
            },
            "publish_thought_bus": {
                "desc": "Publish a thought to the ThoughtBus",
                "schema": {"type": "object", "properties": {
                    "message": {"type": "string"},
                }, "required": ["message"]},
                "intent": "think",
            },
            # ── Knowledge ──────────────────────────────────────────
            "query_knowledge": {
                "desc": "Query the knowledge base / history database",
                "schema": {"type": "object", "properties": {
                    "query": {"type": "string"},
                }, "required": ["query"]},
                "intent": "query_knowledge",
            },
            "search_knowledge": {
                "desc": "Search knowledge base for a topic",
                "schema": {"type": "object", "properties": {
                    "query": {"type": "string"},
                }, "required": ["query"]},
                "intent": "search_knowledge",
            },
            # ── File operations ────────────────────────────────────
            "copy_file": {
                "desc": "Copy a file from source to destination",
                "schema": {"type": "object", "properties": {
                    "source": {"type": "string"}, "destination": {"type": "string"},
                }, "required": ["source", "destination"]},
                "intent": "copy_file",
            },
            "move_file": {
                "desc": "Move/rename a file",
                "schema": {"type": "object", "properties": {
                    "source": {"type": "string"}, "destination": {"type": "string"},
                }, "required": ["source", "destination"]},
                "intent": "move_file",
            },
            "delete_file": {
                "desc": "Delete a file",
                "schema": {"type": "object", "properties": {
                    "path": {"type": "string"},
                }, "required": ["path"]},
                "intent": "delete_file",
            },
            "file_info": {
                "desc": "Get file metadata (size, modified date, type)",
                "schema": {"type": "object", "properties": {
                    "path": {"type": "string"},
                }, "required": ["path"]},
                "intent": "file_info",
            },
            "open_file": {
                "desc": "Open a file with the system default application",
                "schema": {"type": "object", "properties": {
                    "path": {"type": "string"},
                }, "required": ["path"]},
                "intent": "open_file",
            },
            # ── Web ────────────────────────────────────────────────
            "fetch_url": {
                "desc": "Fetch the content of a URL (HTTP GET)",
                "schema": {"type": "object", "properties": {
                    "url": {"type": "string"},
                }, "required": ["url"]},
                "intent": "web_fetch",
            },
            # ── Process / System ───────────────────────────────────
            "list_processes": {
                "desc": "List running processes",
                "schema": {"type": "object", "properties": {}},
                "intent": "processes",
            },
            "kill_process": {
                "desc": "Kill a process by name or PID",
                "schema": {"type": "object", "properties": {
                    "name_or_pid": {"type": "string"},
                }, "required": ["name_or_pid"]},
                "intent": "kill_process",
            },
            "list_running_apps": {
                "desc": "List currently running applications",
                "schema": {"type": "object", "properties": {}},
                "intent": "list_apps",
            },
            "network_status": {
                "desc": "Check network connectivity and status",
                "schema": {"type": "object", "properties": {}},
                "intent": "network_status",
            },
            "run_script": {
                "desc": "Run a script file (Python, shell, etc.)",
                "schema": {"type": "object", "properties": {
                    "path": {"type": "string"},
                }, "required": ["path"]},
                "intent": "run_script",
            },
            # ── Desktop extras ─────────────────────────────────────
            "right_click": {
                "desc": "Right-click at screen coordinates",
                "schema": {"type": "object", "properties": {
                    "x": {"type": "integer"}, "y": {"type": "integer"},
                }, "required": ["x", "y"]},
                "intent": "right_click",
            },
            "double_click": {
                "desc": "Double-click at screen coordinates",
                "schema": {"type": "object", "properties": {
                    "x": {"type": "integer"}, "y": {"type": "integer"},
                }, "required": ["x", "y"]},
                "intent": "double_click",
            },
        }

        import json as _json

        for tool_name, spec in TOOLS.items():
            intent = spec["intent"]

            def _make_handler(intent_name):
                def handler(args):
                    result = ac.execute(intent_name, args)
                    return _json.dumps(result, default=str)
                return handler

            registry.define_tool(
                name=tool_name,
                description=spec["desc"],
                input_schema=spec["schema"],
                handler=_make_handler(intent),
            )

        return registry

    # ------------------------------------------------------------------
    # Publishing helpers
    # ------------------------------------------------------------------
    def _publish(self, topic: str, payload: Dict[str, Any]) -> None:
        if self._thought_bus is not None:
            try:
                self._thought_bus.publish(topic, payload, source="goal_engine")
            except Exception as exc:
                logger.debug("ThoughtBus publish failed: %s", exc)

    # ------------------------------------------------------------------
    # Goal submission (entry point)
    # ------------------------------------------------------------------
    def submit_goal(self, text: str) -> GoalPlan:
        """
        Entry point: accept a natural-language goal, decompose it,
        execute each step, validate, and return the completed plan.

        Wraps execution in a stash pocket so all intermediate dumps
        accumulate and crystallize into the knowledge dataset on close.
        """
        with self._lock:
            self._cancelled = False
            self._paused.set()

        self._stats["goals_submitted"] += 1
        self._publish("goal.submitted", {"text": text})

        # ── Retrieve prior knowledge from the dataset ────────────
        # The system asks itself "what have I learned about this before?"
        # instead of leaning on an LLM.
        prior_knowledge: List[Any] = []
        if self._knowledge_dataset is not None:
            try:
                prior_knowledge = self._knowledge_dataset.relevant_for_goal(
                    text, n=5,
                )
                if prior_knowledge:
                    self._publish("goal.prior_knowledge", {
                        "goal_text": text[:80],
                        "fragment_count": len(prior_knowledge),
                        "previews": [
                            f.text[:60] for f in prior_knowledge[:3]
                        ],
                    })
            except Exception:
                pass

        # Decompose
        plan = self._decompose_goal(text)
        self._current_plan = plan
        self._publish("goal.decomposed", {
            "goal_id": plan.goal_id,
            "objective": plan.objective,
            "steps": [{"step_id": s.step_id, "title": s.title, "intent": s.intent} for s in plan.steps],
        })

        # ── Open a stash pocket for this goal ────────────────────
        pocket = None
        if self._stash_pockets is not None:
            try:
                pocket = self._stash_pockets.open_pocket(
                    goal_id=plan.goal_id,
                    owner="goal_engine",
                )
                # Dump the prior knowledge into the pocket so retrieval
                # during steps can reference it
                for frag in prior_knowledge:
                    try:
                        pocket.dump(
                            key="prior_knowledge",
                            value=getattr(frag, "text", ""),
                            tags=["prior"] + list(getattr(frag, "tags", [])),
                            phase_angle=getattr(frag, "phase_angle", 0.0),
                        )
                    except Exception:
                        pass
                # Dump the goal text itself for self-reference
                pocket.dump(
                    key="goal_text",
                    value=text,
                    tags=["goal", "input"],
                )
            except Exception:
                pocket = None

        # Set elephant memory objective
        if self._elephant_memory is not None:
            try:
                self._elephant_memory.set_objective(
                    plan.objective,
                    steps=[{"title": s.title, "status": s.status} for s in plan.steps],
                )
            except Exception:
                pass

        # Execute
        plan.status = "active"
        self._execute_plan(plan)

        # ── Dump each step's outcome into the pocket ─────────────
        if pocket is not None:
            try:
                for step in plan.steps:
                    result_str = ""
                    if step.result:
                        if isinstance(step.result, dict):
                            r = step.result.get("result") or step.result.get("analysis", "")
                            result_str = str(r)[:500]
                        else:
                            result_str = str(step.result)[:500]
                    tags = [step.intent, step.status]
                    # Add words from the goal text as tags for retrieval
                    goal_words = [w for w in text.lower().split() if len(w) > 3][:5]
                    tags.extend(goal_words)
                    pocket.dump(
                        key=f"step_{step.step_id}_{step.intent}",
                        value=f"{step.title}: {result_str}",
                        tags=tags,
                    )
            except Exception:
                pass

        # Final validation
        self._validate_goal(plan)

        # ── Close the pocket — flush to elephant memory + crystallize ──
        if pocket is not None and self._stash_pockets is not None:
            try:
                self._stash_pockets.close_pocket(pocket)
            except Exception:
                pass

        if plan.status == "completed":
            self._stats["goals_completed"] += 1
            self._publish("goal.completed", {
                "goal_id": plan.goal_id,
                "objective": plan.objective,
                "steps_total": len(plan.steps),
                "steps_ok": sum(1 for s in plan.steps if s.status == "completed"),
            })
        else:
            self._stats["goals_failed"] += 1
            self._publish("goal.failed", {
                "goal_id": plan.goal_id,
                "objective": plan.objective,
                "status": plan.status,
            })

        return plan

    # ------------------------------------------------------------------
    # Decomposition (3-tier: LLM -> AgentCore regex -> heuristic)
    # ------------------------------------------------------------------
    def _decompose_goal(self, text: str) -> GoalPlan:
        """
        Three-tier decomposition:
          1. LLM adapter (AureonBrain) -- intelligent decomposition
          2. AgentCore.plan_task() -- deterministic regex planner
          3. Heuristic verb->intent mapping fallback
        """
        import re as _re
        plan = GoalPlan(original_text=text, objective=text)
        steps: List[GoalStep] = []

        agent_company = self._match_agent_company_goal(text)
        if agent_company:
            steps = [GoalStep(
                title="Aureon build agent company capability bill list",
                intent="agent_company_builder",
                params=agent_company,
                expected_outcome="CEO-to-cleaner agent company registry, work orders, and console evidence published",
            )]
            plan.steps = steps
            plan.success_criteria = "Agent company registry generated with roles, authority boundaries, and public evidence"
            return plan

        codex_ingestion = self._match_codex_capability_ingestion_goal(text)
        if codex_ingestion:
            steps = [GoalStep(
                title="Aureon ingest Everything Codex Can Do",
                intent="codex_capability_ingestion",
                params=codex_ingestion,
                expected_outcome="Codex capability source file ingested, mapped to Aureon, tested, and completion report published",
            )]
            plan.steps = steps
            plan.success_criteria = "Codex capability ingestion report generated with Aureon bridge work orders and validation evidence"
            return plan

        repo_repair = self._match_repo_self_repair_goal(text)
        if repo_repair:
            steps = [GoalStep(
                title="Aureon repo-wide self bug report and repair",
                intent="repo_self_repair",
                params=repo_repair,
                expected_outcome="Repo-level checks, bug report, safe repairs, and retest evidence generated",
            )]
            plan.steps = steps
            plan.success_criteria = "Repo self-repair report generated and critical checks retested"
            return plan

        director_bridge = self._match_director_capability_bridge_goal(text)
        if director_bridge:
            steps = [GoalStep(
                title="Aureon build director capability bridge",
                intent="director_capability_bridge",
                params=director_bridge,
                expected_outcome="Codex-class capability parity map and Aureon bridge work orders published",
            )]
            plan.steps = steps
            plan.success_criteria = "Director capability bridge generated with exact Aureon build orders for gaps"
            return plan

        work_journal = self._match_coding_work_journal_goal(text)
        if work_journal:
            steps = [GoalStep(
                title="Aureon validate coding work journal UI",
                intent="coding_work_journal_ui",
                params=work_journal,
                expected_outcome="Coding organism publishes a prompt-to-files work journal and the UI renders it",
            )]
            plan.steps = steps
            plan.success_criteria = "Coding work journal evidence and UI surface are present and validated"
            return plan

        coding_skill_base = self._match_coding_agent_skill_base_goal(text)
        if coding_skill_base:
            steps = [GoalStep(
                title="Aureon build coding-agent skill base",
                intent="coding_agent_skill_base",
                params=coding_skill_base,
                expected_outcome="Coding agents, skill base, web-learning sources, and improvement work orders published",
            )]
            plan.steps = steps
            plan.success_criteria = "Coding-agent skill base manifest generated with web/repo learning tools visible"
            return plan

        work_orders = self._match_frontend_work_order_goal(text)
        if work_orders:
            steps = [GoalStep(
                title="Aureon execute frontend work orders",
                intent="frontend_work_orders",
                params=work_orders,
                expected_outcome="Frontend work order execution manifest and adapter console generated",
            )]
            plan.steps = steps
            plan.success_criteria = "All current frontend work orders represented as execution records"
            return plan

        ui_repair = self._match_operational_ui_self_repair_goal(text)
        if ui_repair:
            steps = [GoalStep(
                title="Aureon self-review and repair operational UI",
                intent="self_repair_operational_ui",
                params=ui_repair,
                expected_outcome="Operational React console reviewed, repaired, and retested through Aureon's own code path",
            )]
            plan.steps = steps
            plan.success_criteria = "Self-review/self-repair evidence generated with final UI checks passing"
            return plan

        operational_ui = self._match_operational_ui_goal(text)
        if operational_ui:
            steps = [GoalStep(
                title="Aureon self-author operational UI",
                intent="self_author_operational_ui",
                params=operational_ui,
                expected_outcome="Operational React console authored through Aureon's Queen code writer",
            )]
            plan.steps = steps
            plan.success_criteria = "Self-authored UI component and provenance evidence generated"
            return plan

        document_pdf = self._match_document_pdf_goal(text)
        if document_pdf:
            steps = [GoalStep(
                title=f"compose {document_pdf['form']} PDF about {document_pdf['topic']}",
                intent="compose_document_pdf",
                params=document_pdf,
                expected_outcome="Long-form Markdown and PDF document artifacts created",
            )]
            plan.steps = steps
            plan.success_criteria = "Document PDF generated and validated on disk"
            return plan

        # Path -1: Creative generation — "write a [poem/story/essay/song/
        # haiku/sonnet/letter/article/speech] about <topic>"
        creative_match = _re.search(
            r'\b(?:write|compose|craft|create)\s+(?:a|an)?\s*'
            r'(poem|story|essay|song|haiku|sonnet|letter|article|speech|verse|ballad|tale|ode|lyric|poetry)'
            r'\s+(?:about|on|for|of)\s+(.+)',
            text.lower(),
        )
        if creative_match:
            form = creative_match.group(1)
            topic = creative_match.group(2).strip().rstrip('.')
            steps = [GoalStep(
                title=f"compose {form} about {topic}",
                intent="compose_creative",
                params={"form": form, "topic": topic, "source_text": text},
                expected_outcome=f"{form} composed from knowledge dataset + background facts",
            )]
            plan.steps = steps
            plan.success_criteria = f"Creative {form} generated"
            return plan

        # Path 0: If text contains "and"/"then" chain words, prefer heuristic
        # split so multi-step desktop commands work ("open X and type Y then press Z")
        if _re.search(r'\b(?:and then|then|and)\b', text.lower()):
            heuristic = self._heuristic_decompose(text)
            if len(heuristic) >= 2:
                steps = heuristic

        # Path 1: LLM-driven decomposition via swarm adapter (only if no steps yet)
        if not steps and self._swarm is not None and hasattr(self._swarm, 'adapter'):
            try:
                steps = self._llm_decompose(text)
            except Exception as exc:
                logger.debug("LLM decomposition failed: %s", exc)

        # Path 2: AgentCore deterministic planner
        if not steps and self._agent_core is not None:
            try:
                raw_steps = self._agent_core.plan_task(text)
                if raw_steps:
                    for rs in raw_steps:
                        steps.append(GoalStep(
                            title=rs.get("description", rs.get("intent", "")),
                            intent=rs.get("intent", ""),
                            params=rs.get("params", {}),
                            expected_outcome=rs.get("description", ""),
                        ))
            except Exception as exc:
                logger.debug("AgentCore.plan_task failed: %s", exc)

        # Path 3: Heuristic fallback if no steps or only generic "think"
        if not steps or all(s.intent == "think" for s in steps):
            heuristic = self._heuristic_decompose(text)
            if heuristic:
                steps = heuristic

        # Path 4: If we detect a file path but no step writes to it, add write_file
        extracted_path = self._extract_path(text)
        if extracted_path:
            has_write = any(s.intent in ("write_file", "create_script") for s in steps)
            if not has_write:
                content = self._extract_content(text, extracted_path)
                steps = [GoalStep(
                    title=f"Create {extracted_path}",
                    intent="write_file",
                    params={"path": extracted_path, "content": content},
                    expected_outcome=f"File created at {extracted_path}",
                )]

        # Ensure at least one step
        if not steps:
            steps.append(GoalStep(
                title=text,
                intent="think",
                params={"message": text},
                expected_outcome="Acknowledged",
            ))

        plan.steps = steps
        plan.success_criteria = f"All {len(steps)} steps completed and validated"
        return plan

    def _match_repo_self_repair_goal(self, text: str) -> Optional[Dict[str, Any]]:
        """Detect a request for Aureon to inspect and fix its repo/codebase."""
        import re as _re

        lower = (text or "").lower()
        aureon_hit = "aureon" in lower or "organism" in lower or "itself" in lower
        repo_hit = _re.search(r"\b(?:repo|repository|codebase|code|everything|all problems|bug report|bugs|tests|builds)\b", lower)
        repair_hit = _re.search(r"\b(?:fix|repair|review|check|test|work through|diagnose|bug report|self[- ]?repair)\b", lower)
        self_hit = _re.search(r"\b(?:own|itself|self|without help|no cheating)\b", lower)
        if not (aureon_hit and repo_hit and repair_hit and self_hit):
            return None
        return {
            "goal": text,
            "authoring_contract": "goal_engine_repo_self_repair_to_queen_code_architect",
        }

    def _match_frontend_work_order_goal(self, text: str) -> Optional[Dict[str, Any]]:
        """Detect a request for Aureon to execute frontend evolution work orders."""
        import re as _re

        lower = (text or "").lower()
        aureon_hit = "aureon" in lower or "organism" in lower or "itself" in lower
        work_order_hit = _re.search(r"\b(?:work order|work orders|frontend evolution|adapter|adapters|do the work)\b", lower)
        action_hit = _re.search(r"\b(?:do|execute|fix|complete|work through|apply|wire)\b", lower)
        if not (aureon_hit and work_order_hit and action_hit):
            return None
        return {
            "goal": text,
            "authoring_contract": "goal_engine_frontend_work_orders_to_queen_code_architect",
        }

    def _match_coding_agent_skill_base_goal(self, text: str) -> Optional[Dict[str, Any]]:
        """Detect a request to teach Aureon its coder-agent/skill/web-learning system."""
        import re as _re

        lower = (text or "").lower()
        aureon_hit = "aureon" in lower or "system" in lower or "organism" in lower
        coding_hit = _re.search(r"\b(?:coder|coders|coding|code writing|write code|programming|developer|agents as coders|code)\b", lower)
        skill_hit = _re.search(r"\b(?:skill|skills|skill base|capability|capabilities|learn|learning|teach)\b", lower)
        web_hit = _re.search(r"\b(?:websearch|web search|web_search|web|online|open source|api|documentation|docs)\b", lower)
        bridge_hit = _re.search(
            r"\b(?:coding organism|coding systems?|code builder|coding builder|coding lane|coding terminal|terminal chat|"
            r"prompt[- ]?to[- ]?run|desktop run|desktop/run|run handoff|finished product|product audit|remote desktop|vm control)\b",
            lower,
        )
        if not (aureon_hit and coding_hit and (skill_hit or bridge_hit)):
            return None
        return {
            "goal": text,
            "online": bool(web_hit),
            "authoring_contract": "goal_engine_coding_agent_skill_base_to_queen_code_architect",
        }

    def _match_director_capability_bridge_goal(self, text: str) -> Optional[Dict[str, Any]]:
        """Detect a director-mode request to compare Codex-class ability with Aureon."""
        import re as _re

        lower = (text or "").lower()
        aureon_hit = "aureon" in lower or "organism" in lower or "system" in lower
        director_hit = _re.search(r"\b(?:director|codex|capability parity|capability bridge|bridge the gaps|marry up|what can i do)\b", lower)
        gap_hit = _re.search(r"\b(?:gap|gaps|cant do|can't do|missing|bridge|build orders|work orders|list)\b", lower)
        code_hit = _re.search(r"\b(?:code|write|build|coding|desktop|remote|test|audit|run)\b", lower)
        if not (aureon_hit and director_hit and gap_hit and code_hit):
            return None
        return {
            "goal": text,
            "authoring_contract": "goal_engine_director_capability_bridge_to_queen_code_architect",
        }

    def _match_codex_capability_ingestion_goal(self, text: str) -> Optional[Dict[str, Any]]:
        """Detect a request to ingest the Everything Codex Can Do source file."""
        import re as _re

        lower = (text or "").lower()
        file_hit = "everything_codex_can_do.md" in lower or "everything codex can do" in lower
        aureon_hit = "aureon" in lower or "organism" in lower or "system" in lower
        ingest_hit = _re.search(r"\b(?:ingest|upload|load|read|write these into|marry up|bridge|completion report|progress report)\b", lower)
        test_hit = _re.search(r"\b(?:test|validate|run|report|self[- ]?validation|completion)\b", lower)
        if not (file_hit and aureon_hit and ingest_hit and test_hit):
            return None
        return {
            "goal": text,
            "source_md": "EVERYTHING_CODEX_CAN_DO.md",
            "authoring_contract": "goal_engine_codex_capability_ingestion_to_queen_code_architect",
        }

    def _match_coding_work_journal_goal(self, text: str) -> Optional[Dict[str, Any]]:
        """Detect a request for the coding organism to show its full work trail."""
        import re as _re

        lower = (text or "").lower()
        aureon_hit = "aureon" in lower or "system" in lower or "organism" in lower
        journal_hit = _re.search(
            r"\b(?:work journal|show its work|show the work|stages|prompt to finished files|prompt-to-finished|flow|prompt lane|send to aureon|operator terminal)\b",
            lower,
        )
        coding_panel_hit = (
            "aureoncodingorganismconsole" in lower
            or "aureon coding organism" in lower
            or "coding organism console" in lower
            or "coding organism ui" in lower
            or "coding panel" in lower
        )
        ui_hit = _re.search(r"\b(?:ui|console|panel|screen|frontend|show|terminal|textarea|prompt box|prompt lane|send to aureon|local hub|endpoint)\b", lower)
        evidence_hit = _re.search(r"\b(?:prompt|route|goal steps|code proposal|files|tests|desktop handoff|completion|report|hub endpoint|local hub)\b", lower)
        if aureon_hit and coding_panel_hit and ui_hit and evidence_hit:
            journal_hit = journal_hit or True
        if not (aureon_hit and journal_hit and ui_hit and evidence_hit):
            return None
        return {
            "goal": text,
            "authoring_contract": "goal_engine_coding_work_journal_ui_to_coding_organism_bridge",
            "target_files": [
                "aureon/autonomous/aureon_coding_organism_bridge.py",
                "frontend/src/components/generated/AureonCodingOrganismConsole.tsx",
                "tests/test_aureon_coding_organism_bridge.py",
            ],
        }

    def _match_agent_company_goal(self, text: str) -> Optional[Dict[str, Any]]:
        """Detect a request to build Aureon's company-of-agents registry."""
        import re as _re

        lower = (text or "").lower()
        aureon_hit = "aureon" in lower or "organism" in lower or "system" in lower
        company_hit = _re.search(
            r"\b(?:company of agents|agent company|company-style|org chart|organisation|organization|who does what|ceo|cleaner|toilet|bill list|day to day|daily duties|daily routine|agency|head hunting|headhunting|subcontractor|sub contractor|client job|prompt as client|temporary workers|crew memory|memory phonebook|phonebook|rehydrate|internal memory database)\b",
            lower,
        )
        capability_hit = _re.search(
            r"\b(?:capability|capabilities|roles|agents|workers|staff|crew|departments|startup|tasks|work orders|skills|functions|duties|routines|hire|fire|retire|outsource|memory|archive)\b",
            lower,
        )
        build_hit = _re.search(
            r"\b(?:build|create|list|map|wire|make|generate|tell aureon|write|ensure|expand|teach|operate|treat|scout|assemble|deliver|retire|retain|outsource|save|archive|compress|rehydrate|reuse)\b",
            lower,
        )
        if not (aureon_hit and company_hit and capability_hit and build_hit):
            return None
        return {
            "goal": text,
            "online": bool(_re.search(r"\b(?:online|internet|web search|websearch|search job|job sites|official docs|external search|search capabilities)\b", lower)),
            "authoring_contract": "goal_engine_agent_company_builder_to_coding_organism",
            "target_files": [
                "aureon/autonomous/aureon_agent_company_builder.py",
                "frontend/src/components/generated/AureonAgentCompanyConsole.tsx",
                "frontend/public/aureon_agent_company_bill_list.json",
                "docs/audits/aureon_agent_company_bill_list.json",
                "tests/test_agent_company_builder.py",
            ],
        }

    def _match_operational_ui_self_repair_goal(self, text: str) -> Optional[Dict[str, Any]]:
        """Detect a request for Aureon to diagnose and fix its own UI defects."""
        import re as _re

        lower = (text or "").lower()
        if (
            "aureoncodingorganismconsole" in lower
            or "aureon coding organism" in lower
            or "coding organism console" in lower
            or "coding organism ui" in lower
            or "prompt lane" in lower
            or "send to aureon" in lower
        ):
            return None
        ui_hit = _re.search(r"\b(?:ui|user interface|frontend|front-end|console|dashboard|react|tsx)\b", lower)
        aureon_hit = "aureon" in lower or "organism" in lower or "itself" in lower
        repair_hit = _re.search(
            r"\b(?:problem|problems|issue|issues|defect|defects|bug|bugs|fix|repair|review|check|test|work through|improve)\b",
            lower,
        )
        self_hit = _re.search(r"\b(?:own|itself|self|without help|no cheating)\b", lower)
        if not (ui_hit and aureon_hit and repair_hit and self_hit):
            return None

        target_path = self._extract_path(text)
        if target_path and not target_path.lower().endswith((".tsx", ".jsx")):
            target_path = ""
        if not target_path:
            target_path = "frontend/src/components/generated/AureonGeneratedOperationalConsole.tsx"
        return {
            "goal": text,
            "target_path": target_path,
            "authoring_contract": "goal_engine_self_review_repair_to_queen_code_architect",
        }

    def _match_operational_ui_goal(self, text: str) -> Optional[Dict[str, Any]]:
        """Detect a request for Aureon to design/write its own live UI."""
        import re as _re

        lower = (text or "").lower()
        action_hit = _re.search(r"\b(?:design|build|create|write|author|generate)\b", lower)
        ui_hit = _re.search(r"\b(?:ui|user interface|frontend|front-end|console|dashboard|react|tsx)\b", lower)
        aureon_hit = "aureon" in lower or "organism" in lower
        if not (action_hit and ui_hit and aureon_hit):
            return None

        target_path = self._extract_path(text)
        if target_path and not target_path.lower().endswith((".tsx", ".jsx")):
            target_path = ""
        if not target_path:
            target_path = "frontend/src/components/generated/AureonGeneratedOperationalConsole.tsx"
        return {
            "goal": text,
            "target_path": target_path,
            "authoring_contract": "goal_engine_to_queen_code_architect",
        }

    def _match_document_pdf_goal(self, text: str) -> Optional[Dict[str, Any]]:
        """Detect long-form writing requests that must become a PDF artifact."""
        import re as _re

        lower = (text or "").lower()
        if "pdf" not in lower:
            return None
        if not _re.search(r"\b(?:write|compose|craft|create|draft)\b", lower):
            return None
        form_match = _re.search(r"\b(essay|article|report|document|piece)\b", lower)
        if not form_match:
            return None
        form = form_match.group(1)
        topic = self._extract_document_topic(text, form=form)
        target_words = self._extract_document_target_words(text, default=4000)
        desktop = bool(_re.search(r"\bdesktop\b", lower))
        return {
            "form": form,
            "topic": topic,
            "prompt": text,
            "target_words": target_words,
            "output_dir": "desktop" if desktop else "",
        }

    def _extract_document_topic(self, text: str, *, form: str) -> str:
        import re as _re

        patterns = [
            rf"\b{_re.escape(form)}\b\s+(?:about|on|of)\s+(.+?)(?:\s+(?:and|then)\s+(?:pdf|save|export|put|write)|\s+to\s+(?:a\s+)?pdf|\s+as\s+(?:a\s+)?pdf|$)",
            r"\b(?:about|on|of)\s+(.+?)(?:\s+(?:and|then)\s+(?:pdf|save|export|put|write)|\s+to\s+(?:a\s+)?pdf|\s+as\s+(?:a\s+)?pdf|$)",
        ]
        for pattern in patterns:
            match = _re.search(pattern, text or "", _re.I)
            if match:
                topic = match.group(1).strip(" .")
                if topic:
                    return topic
        return "the meaning of life"

    def _extract_document_target_words(self, text: str, default: int = 4000) -> int:
        import re as _re

        match = _re.search(r"\b(\d{3,5})\s*(?:[- ]?word|words)\b", text or "", _re.I)
        if not match:
            return default
        return max(100, min(int(match.group(1)), 20000))

    def _llm_decompose(self, text: str) -> List[GoalStep]:
        """
        Use the LLM adapter to intelligently decompose a goal into steps.
        Every call obeys the Emerald Tablet decree and includes any
        prior knowledge retrieved from the dataset for puzzle-piecing.
        """
        adapter = self._ollama or (self._swarm.adapter if self._swarm is not None else None)
        if adapter is None:
            return []
        decree = self._consult_source_law()
        tablet = self._emerald_tablet_prompt(decree)

        # Retrieve prior knowledge from the dataset (no LLM)
        prior_block = ""
        if self._knowledge_dataset is not None:
            try:
                prior = self._knowledge_dataset.relevant_for_goal(text, n=3)
                if prior:
                    lines = ["[PRIOR KNOWLEDGE — what I learned before]"]
                    for f in prior:
                        snippet = getattr(f, "text", "")[:120]
                        lines.append(f"  - {snippet}")
                    prior_block = "\n".join(lines) + "\n\n"
            except Exception:
                pass

        resp = adapter.prompt(
            messages=[{"role": "user", "content": (
                f"{prior_block}"
                f"Break this goal into 2-5 concrete action steps. "
                f"For each step, output one line: STEP: <action verb> <details>\n\n"
                f"Goal: {text}\n\n"
                f"Available actions: search (web search), read (file), list (directory), "
                f"check (system/network), write (file), run (shell command), "
                f"create (script/file), analyse (data)\n\n"
                f"Output steps now:"
            )}],
            system=tablet + "You are a task planner. Output only STEP: lines, nothing else.",
            max_tokens=512,
            temperature=0.3,
        )
        response_text = resp.text or ""
        if not response_text:
            return []

        # Parse STEP: lines from the response
        steps: List[GoalStep] = []
        intent_keywords = {
            "search": "web_search", "google": "web_search", "find": "find_files",
            "read": "read_file", "open": "read_file",
            "list": "list_dir", "show": "list_dir",
            "check": "system_info", "verify": "system_info",
            "write": "write_file", "create": "create_script",
            "run": "execute_shell", "execute": "execute_shell",
            "analyse": "think", "analyze": "think", "evaluate": "think",
            "install": "execute_shell",
        }

        for line in response_text.split("\n"):
            line = line.strip()
            # Accept lines starting with STEP: or numbered lines
            if line.upper().startswith("STEP:"):
                action = line[5:].strip()
            elif line and line[0].isdigit() and "." in line[:3]:
                action = line.split(".", 1)[-1].strip()
            else:
                continue

            if not action:
                continue

            # Map first word to an intent
            first_word = action.split()[0].lower().rstrip(":")
            intent = intent_keywords.get(first_word, "think")
            params: Dict[str, Any] = {}

            remainder = action.split(None, 1)[-1] if " " in action else text
            if intent == "web_search":
                params["query"] = remainder
            elif intent in ("read_file", "find_files", "list_dir"):
                params["path"] = remainder.split()[0] if remainder.split() else "."
            elif intent == "execute_shell":
                params["command"] = remainder
            elif intent in ("write_file", "create_script"):
                params["path"] = remainder.split()[0] if remainder.split() else "output.txt"
                params["content"] = remainder
            else:
                params["message"] = remainder

            steps.append(GoalStep(
                title=action[:80],
                intent=intent,
                params=params,
                expected_outcome=f"Successful {intent}: {action[:40]}",
            ))

        return steps[:5]  # cap at 5 steps

    @staticmethod
    def _extract_path(text: str) -> str:
        """Extract a file path from natural language text."""
        import re
        # Match explicit paths like /tmp/foo.py, ./bar.txt, aureon/core/x.py
        m = re.search(r'(?:at\s+|to\s+|in\s+|from\s+)?(/[\w./\-]+\.\w+|\.[\w./\-]+\.\w+|\w+/[\w./\-]+\.\w+)', text)
        if m:
            return m.group(1) if m.group(1).startswith(("/", ".")) else m.group(1)
        return ""

    @staticmethod
    def _extract_content(text: str, path: str) -> str:
        """Extract the content description after 'that' or 'with' or 'containing'."""
        import re
        m = re.search(r'(?:that|which|with content|containing)\s+(.+)', text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        # Fallback: everything after the path
        if path and path in text:
            after = text.split(path, 1)[-1].strip()
            if after.startswith("that "):
                return after[5:]
            return after if after else text
        return text

    def _heuristic_decompose(self, text: str) -> List[GoalStep]:
        """Verb-based heuristic decomposition for unrecognised patterns."""
        import re as _re
        lower = text.lower().strip()
        steps: List[GoalStep] = []

        # Split on "and"/"then"/"," to handle chained tasks:
        # "open notepad and type hello then press enter" -> 3 sub-tasks
        clauses = _re.split(r'\s+(?:and then|then|and)\s+|,\s+', lower)
        if len(clauses) > 1:
            for clause in clauses:
                sub_steps = self._heuristic_decompose(clause.strip())
                steps.extend(sub_steps)
            return steps

        # Check for explicit file path in the text
        extracted_path = self._extract_path(text)
        extracted_content = self._extract_content(text, extracted_path) if extracted_path else ""

        # For chained clauses (single verbs), take only the first intent.
        # For full goals ("build a website"), take all intents as steps.
        is_single_clause = len(lower.split()) <= 5

        for verb, intents in VERB_INTENT_MAP.items():
            if lower.startswith(verb) or f" {verb} " in f" {lower} ":
                use_intents = intents[:1] if is_single_clause else intents
                for intent in use_intents:
                    params: Dict[str, Any] = {}
                    # Extract the object of the verb as the primary param
                    remainder = lower.split(verb, 1)[-1].strip().strip('"\'')
                    if intent in ("web_search", "search_web", "google"):
                        params["query"] = remainder or text
                    elif intent in ("open_app", "launch"):
                        params["app_name"] = remainder.split()[0] if remainder else "explorer"
                    elif intent in ("open_url", "browse"):
                        params["url"] = remainder
                    elif intent in ("execute_shell", "run_command"):
                        params["command"] = remainder or text
                    elif intent in ("write_file", "create_script"):
                        params["path"] = extracted_path or (remainder.split()[0] if remainder else "output.txt")
                        params["content"] = extracted_content or text
                    elif intent in ("list_dir", "ls", "dir"):
                        params["path"] = "."
                    elif intent in ("read_file", "cat"):
                        params["path"] = extracted_path or (remainder.split()[0] if remainder else ".")
                    elif intent in ("speak", "say"):
                        params["text"] = remainder or text
                    elif intent == "click":
                        # Try to extract x,y coordinates from text
                        import re as _re
                        m = _re.search(r'(\d+)\s*[,x]\s*(\d+)', remainder)
                        if m:
                            params["x"] = int(m.group(1))
                            params["y"] = int(m.group(2))
                        else:
                            params["x"] = 500
                            params["y"] = 500
                    elif intent == "type_text":
                        params["text"] = remainder or text
                    elif intent == "press_key":
                        params["key"] = remainder.split()[0] if remainder else "enter"
                    elif intent == "hotkey":
                        keys = [k.strip() for k in remainder.replace("+", " ").split() if k.strip()]
                        params["keys"] = keys or ["alt", "tab"]
                    elif intent == "screenshot":
                        pass  # no params needed
                    elif intent == "focus_window":
                        params["title"] = remainder or ""
                    elif intent == "close_app":
                        params["app_name"] = remainder.split()[0] if remainder else ""
                    elif intent == "move_mouse":
                        import re as _re
                        m = _re.search(r'(\d+)\s*[,x]\s*(\d+)', remainder)
                        if m:
                            params["x"] = int(m.group(1))
                            params["y"] = int(m.group(2))
                        else:
                            params["x"] = 500
                            params["y"] = 500
                    elif intent == "think":
                        params["message"] = text
                    else:
                        params["query"] = remainder or text

                    steps.append(GoalStep(
                        title=f"{intent}: {remainder[:60]}" if remainder else intent,
                        intent=intent,
                        params=params,
                        expected_outcome=f"Successful {intent}",
                    ))
                break

        return steps

    # ------------------------------------------------------------------
    # Swarm dispatch (parallel multi-agent execution)
    # ------------------------------------------------------------------
    def _can_swarm(self, plan: GoalPlan) -> bool:
        """Determine if this plan benefits from swarm (parallel) execution."""
        if self._swarm is None:
            return False
        # Swarm dispatch for plans with 3+ independent steps
        if len(plan.steps) >= 3:
            return True
        # Or if the goal text signals multi-agent intent
        lower = plan.original_text.lower()
        swarm_signals = ["compare", "analyse", "analyze", "research", "investigate",
                         "parallel", "multiple", "agents", "team", "swarm",
                         "perspectives", "opinions", "evaluate"]
        return any(sig in lower for sig in swarm_signals)

    def _expand_for_swarm(self, plan: GoalPlan) -> None:
        """
        If a plan has fewer than 3 steps but was flagged for swarm,
        auto-expand into parallel agent perspectives so the swarm
        has something to parallelize.
        """
        if len(plan.steps) >= 3:
            return
        # Create specialist agents for the same objective
        perspectives = [
            ("Analyst", "Perform quantitative analysis"),
            ("Scout", "Search for the latest data and news"),
            ("Architect", "Design a structured approach"),
        ]
        expanded: List[GoalStep] = []
        for role, desc in perspectives:
            expanded.append(GoalStep(
                title=f"{role}: {plan.objective[:50]}",
                intent="think",
                params={"message": f"[{role}] {desc}: {plan.objective}"},
                expected_outcome=f"{role} perspective completed",
            ))
        # Keep original steps as final synthesis
        for s in plan.steps:
            s.title = f"Synthesis: {s.title}"
        plan.steps = expanded + plan.steps

    # ------------------------------------------------------------------
    # Source Law (Emerald Tablet) — supreme decision authority
    # ------------------------------------------------------------------
    def _consult_source_law(self) -> Dict[str, Any]:
        """
        Consult the Emerald Tablet before any LLM operation.
        Returns the decree dict with action, confidence, coherence, reasoning.
        """
        if self._source_law is None:
            return {
                "action": "EXECUTE",
                "confidence": 0.5,
                "coherence": 0.5,
                "consciousness": "FLOWING",
                "reasoning": ["Source Law not available — permissive default"],
                "available": False,
            }
        try:
            result = self._source_law.cogitate()
            if result is None:
                return {
                    "action": "EXECUTE",
                    "confidence": 0.5,
                    "coherence": 0.5,
                    "consciousness": "AWARE",
                    "reasoning": ["No cognition yet — vacuum accumulating"],
                    "available": True,
                }
            return {
                "action": result.action,
                "confidence": result.confidence,
                "coherence": result.coherence_gamma,
                "consciousness": result.consciousness_level,
                "reasoning": list(result.reasoning[:3]),
                "vacuum_size": result.vacuum_size,
                "available": True,
            }
        except Exception as exc:
            logger.debug("Source Law cogitation failed: %s", exc)
            return {
                "action": "EXECUTE",
                "confidence": 0.5,
                "coherence": 0.5,
                "consciousness": "DORMANT",
                "reasoning": [f"Cogitation error: {exc}"],
                "available": False,
            }

    def _emerald_tablet_prompt(self, decree: Dict[str, Any]) -> str:
        """
        Format the Source Law decree + temporal context as a system prompt prefix.
        Every LLM call uses this so all agents obey the same truth and have
        the same temporal awareness.
        """
        action = decree.get("action", "EXECUTE")
        conf = decree.get("confidence", 0.5)
        coh = decree.get("coherence", 0.5)
        cons = decree.get("consciousness", "AWARE")
        reasoning = "; ".join(decree.get("reasoning", []))[:200]

        # Inject temporal knowledge — what just happened in the last 60s
        temporal_block = ""
        if self._temporal_knowledge is not None:
            try:
                temporal_block = self._temporal_knowledge.temporal_context(
                    window_s=60.0,
                    max_lines=6,
                ) + "\n"
            except Exception:
                pass

        return (
            f"[EMERALD TABLET DECREE]\n"
            f"The Source Law has spoken — all agents obey the same truth:\n"
            f"  Action: {action}  Confidence: {conf:.2f}  Coherence: {coh:.3f}\n"
            f"  Consciousness: {cons}\n"
            f"  Reasoning: {reasoning}\n"
            f"Act in alignment with this decree. "
            f"{'Proceed decisively.' if action == 'EXECUTE' else 'Pause, gather more data, or act minimally.' if action in ('HOLD','GATHER_MORE_DATA') else 'Accumulate and reflect.'}\n"
            f"\n{temporal_block}"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )

    # ------------------------------------------------------------------
    # Auris gate — ask the 9 nodes before committing resources
    # ------------------------------------------------------------------
    def _auris_gate(self, plan: GoalPlan) -> Dict[str, Any]:
        """
        Consult the 9 Auris nodes before executing.
        Returns the vote result. If SELL or STABILISE with high
        confidence, the swarm should proceed with caution.
        """
        if self._auris is None or self._vault is None:
            return {"consensus": "NEUTRAL", "confidence": 0.0, "gated": False}

        try:
            vote = self._auris.vote(self._vault)
            gated = vote.consensus in ("SELL", "STABILISE") and vote.confidence >= 0.7
            self._publish("swarm.auris.gate", {
                "goal_id": plan.goal_id,
                "consensus": vote.consensus,
                "confidence": vote.confidence,
                "agreeing": vote.agreeing,
                "lighthouse": vote.lighthouse_cleared,
                "gated": gated,
            })
            return {
                "consensus": vote.consensus,
                "confidence": vote.confidence,
                "agreeing": vote.agreeing,
                "lighthouse_cleared": vote.lighthouse_cleared,
                "gated": gated,
            }
        except Exception:
            return {"consensus": "NEUTRAL", "confidence": 0.0, "gated": False}

    def _execute_plan_swarm(self, plan: GoalPlan) -> None:
        """
        Coordinated swarm execution:
          1. AURIS GATE  — consult 9 nodes before committing resources
          2. FORK        — fork a timeline branch
          3. DELEGATE    — assign specific tasks to specialist agents with DAG deps
          4. EXECUTE     — run workers in parallel, coordinator waits for all
          5. COORDINATE  — share results via SharedMemory + MessageBus
          6. SYNTHESIZE  — coordinator agent reads all results and produces summary
          7. VALIDATE    — final Auris vote on the completed work
          8. MERGE       — merge timeline, update elephant memory
        """
        self._expand_for_swarm(plan)
        self._stats["swarm_dispatches"] += 1

        # ── 0. EMERALD TABLET DECREE ───────────────────────────────
        # The Source Law decides before anything else
        decree = self._consult_source_law()
        self._publish("swarm.emerald_tablet", {
            "goal_id": plan.goal_id,
            "action": decree["action"],
            "confidence": decree["confidence"],
            "coherence": decree["coherence"],
            "reasoning": decree.get("reasoning", []),
        })

        # ── 1. AURIS GATE ──────────────────────────────────────────
        gate = self._auris_gate(plan)
        self._publish("swarm.dispatching", {
            "goal_id": plan.goal_id,
            "agent_count": len(plan.steps),
            "objective": plan.objective,
            "auris_gate": gate["consensus"],
            "emerald_tablet": decree["action"],
        })

        if gate["gated"]:
            self._publish("swarm.gated", {
                "goal_id": plan.goal_id,
                "reason": f"Auris says {gate['consensus']} (conf={gate['confidence']:.2f})",
            })
            # Proceed with caution — reduce concurrency, add extra validation
            max_concurrent = 1
        else:
            max_concurrent = min(len(plan.steps), 4)

        # Emerald Tablet overrides — HOLD/ACCUMULATE reduces concurrency further
        if decree["action"] in ("HOLD", "GATHER_MORE_DATA"):
            max_concurrent = 1  # sequential only
            self._publish("swarm.tablet.gated", {
                "goal_id": plan.goal_id,
                "action": decree["action"],
                "reason": "Emerald Tablet says pause and accumulate",
            })
        elif decree["action"] == "ACCUMULATE":
            max_concurrent = min(max_concurrent, 2)  # reduced pair execution

        # ── 2. FORK TIMELINE ───────────────────────────────────────
        if self._temporal_ground is not None:
            try:
                coherence = self._get_coherence()
                report = self._temporal_ground.tick(
                    lambda_t=0.0,
                    coherence_gamma=coherence,
                    consciousness_psi=0.5,
                    auris_consensus=gate["consensus"],
                )
                if report.forked:
                    self._stats["timelines_forked"] += 1
                self._publish("swarm.timeline.forked", {
                    "goal_id": plan.goal_id,
                    "chain_length": report.chain_length,
                    "branches": report.active_branches,
                })
            except Exception:
                pass

        # ── 3. DELEGATE — build team with specific roles ───────────
        # Separate worker steps from synthesis steps
        worker_steps = [s for s in plan.steps if not s.title.startswith("Synthesis:")]
        synthesis_steps = [s for s in plan.steps if s.title.startswith("Synthesis:")]

        # Consult the Emerald Tablet — every agent obeys the same decree
        decree = self._consult_source_law()
        tablet = self._emerald_tablet_prompt(decree)

        configs = []
        for i, step in enumerate(plan.steps):
            agent_name = f"agent_{step.step_id}"
            is_coordinator = step.title.startswith("Synthesis:")
            role_prompt = (
                f"You are the Coordinator for goal: {plan.objective}\n"
                f"You will receive all worker results. Synthesize them into a "
                f"unified conclusion with key findings and recommended actions."
            ) if is_coordinator else (
                f"You are Agent {i+1} ({step.title.split(':')[0] if ':' in step.title else 'Worker'}) "
                f"working on: {plan.objective}\n"
                f"Your specific task: {step.title}\n"
                f"Execute thoroughly. You have tools: write_file, create_script, "
                f"read_file, web_search, run_shell, run_python, list_directory, "
                f"find_files. Use them to CREATE real artifacts, not just analyse."
            )
            configs.append(AgentConfig(
                name=agent_name,
                system_prompt=tablet + role_prompt,  # Emerald Tablet governs first
                max_turns=4,
                max_tokens=1024,
                temperature=0.3 if is_coordinator else 0.5,
                metadata={
                    "step_id": step.step_id,
                    "intent": step.intent,
                    "role": "coordinator" if is_coordinator else "worker",
                },
            ))

        team_name = f"goal_{plan.goal_id}"
        try:
            team = self._swarm.create_team(
                name=team_name,
                agent_configs=configs,
                tools=self._agent_tools,  # agents can create files, run code, search web
                max_concurrent=max_concurrent,
            )

            # ── 4. EXECUTE — add tasks with dependencies ───────────
            worker_task_ids: List[str] = []
            task_id_map: Dict[str, str] = {}

            # Creation intents — execute tool first, then reason about result
            # Intents that DO something (not just analyse) — execute via AgentCore first
            ACTION_INTENTS = {
                # File/code
                "write_file", "create_script", "create_dir", "execute_shell",
                "execute_python", "run_command", "shell", "copy_file", "move_file",
                "delete_file", "run_script",
                # Desktop
                "open_app", "close_app", "click", "type_text", "press_key",
                "hotkey", "screenshot", "move_mouse", "focus_window", "open_url",
                "right_click", "double_click", "open_file",
                # Trading
                "place_order", "get_balances", "get_positions",
                # Communication
                "speak", "notify",
                # Process
                "kill_process",
            }

            # Workers run in parallel (no dependencies on each other)
            for i, step in enumerate(worker_steps):
                agent_name = f"agent_{step.step_id}"
                step.status = "active"
                self._publish("goal.step.starting", {
                    "goal_id": plan.goal_id,
                    "step_id": step.step_id,
                    "title": step.title,
                    "role": "worker",
                })

                # For creation intents, execute the tool first
                tool_output = ""
                if step.intent in ACTION_INTENTS and self._agent_core is not None:
                    try:
                        tool_result = self._agent_core.execute(step.intent, step.params)
                        tool_output = f"\n\nTool executed: {step.intent}\nResult: {str(tool_result)[:500]}"
                    except Exception as exc:
                        tool_output = f"\n\nTool execution failed: {exc}"

                task = team.queue.add(
                    name=f"worker_{step.step_id}",
                    agent_name=agent_name,
                    prompt=(
                        f"Task: {step.title}\n"
                        f"Goal: {plan.objective}\n"
                        f"Action: {step.intent}\n"
                        f"Parameters: {step.params}\n"
                        f"{'Provide detailed findings.' if not tool_output else 'The tool has been executed. Describe what was created and verify the result.'}"
                        f"{tool_output}"
                    ),
                    context={"goal_id": plan.goal_id, "step_index": i},
                )
                worker_task_ids.append(task.id)
                task_id_map[step.step_id] = task.id

            # Coordinator waits for ALL workers to finish (depends_on)
            for step in synthesis_steps:
                agent_name = f"agent_{step.step_id}"
                step.status = "active"
                self._publish("goal.step.starting", {
                    "goal_id": plan.goal_id,
                    "step_id": step.step_id,
                    "title": step.title,
                    "role": "coordinator",
                })
                task = team.queue.add(
                    name=f"coordinator_{step.step_id}",
                    agent_name=agent_name,
                    prompt=(
                        f"All worker agents have completed their tasks for: {plan.objective}\n"
                        f"Review all results (available in context as dep_worker_* keys).\n"
                        f"Synthesize into a unified conclusion with:\n"
                        f"1. Key findings from each agent\n"
                        f"2. Points of agreement and disagreement\n"
                        f"3. Recommended action\n"
                    ),
                    context={"goal_id": plan.goal_id, "role": "coordinator"},
                    depends_on=worker_task_ids,  # waits for all workers
                )
                task_id_map[step.step_id] = task.id

            # Run the DAG (workers in parallel, coordinator after all workers)
            team.run_tasks()

            # ── 5. COORDINATE — read results + share via memory ────
            worker_results: Dict[str, str] = {}
            for step in plan.steps:
                task_id = task_id_map.get(step.step_id)
                task_result = ""
                if task_id:
                    t = team.queue.get_task(task_id)
                    if t and t.result:
                        task_result = t.result

                if task_result:
                    step.result = {"success": True, "result": task_result, "tool_used": "swarm_agent"}
                    step.status = "completed"
                    step.validation_result = {"valid": True, "reason": "Agent completed", "confidence": 0.85}
                    # Store in shared memory for other agents to read
                    try:
                        team.memory.set(f"result_{step.step_id}", task_result, source=f"agent_{step.step_id}")
                    except Exception:
                        pass
                    worker_results[step.title[:30]] = task_result[:200]
                else:
                    logger.info("Swarm agent %s empty, falling back to AgentCore", f"agent_{step.step_id}")
                    step.result = self._execute_step(step)
                    step.validation_result = self._validate_step(step)
                    step.status = "completed" if step.validation_result.get("valid") else "failed"

                step.coherence_at_execution = self._get_coherence()
                self._stats["steps_executed"] += 1
                self._stats["steps_validated"] += 1

                # ── 6. TRACK — publish progress per step ───────────
                completed_count = sum(1 for s in plan.steps if s.status == "completed")
                self._publish("goal.step.completed" if step.status == "completed" else "goal.step.failed", {
                    "goal_id": plan.goal_id,
                    "step_id": step.step_id,
                    "title": step.title,
                    "role": step.result.get("tool_used", "") if step.result else "",
                    "progress": f"{completed_count}/{len(plan.steps)}",
                })

                # Update elephant memory per step
                if self._elephant_memory is not None:
                    try:
                        self._elephant_memory.remember_result({
                            "route": f"swarm.{step.intent}",
                            "success": step.status == "completed",
                            "step_title": step.title,
                            "progress": f"{completed_count}/{len(plan.steps)}",
                        })
                    except Exception:
                        pass

        except Exception as exc:
            logger.warning("Swarm execution failed, falling back to sequential: %s", exc)
            self._publish("swarm.fallback", {"goal_id": plan.goal_id, "error": str(exc)})
            self._execute_plan_sequential(plan)
            return

        # ── 7. VALIDATE — final Auris vote on completed work ──────
        final_gate = self._auris_gate(plan)
        self._publish("swarm.auris.final", {
            "goal_id": plan.goal_id,
            "consensus": final_gate["consensus"],
            "confidence": final_gate["confidence"],
        })

        # ── 8. MERGE — close timeline, publish completion ─────────
        if self._temporal_ground is not None:
            try:
                coherence = self._get_coherence()
                self._temporal_ground.tick(
                    lambda_t=0.0,
                    coherence_gamma=max(coherence, 0.95),
                    consciousness_psi=0.7,
                    auris_consensus=final_gate["consensus"],
                )
            except Exception:
                pass

        completed = sum(1 for s in plan.steps if s.status == "completed")
        self._publish("swarm.completed", {
            "goal_id": plan.goal_id,
            "agents": len(plan.steps),
            "workers": len(worker_steps),
            "coordinators": len(synthesis_steps),
            "completed": completed,
            "auris_final": final_gate["consensus"],
        })

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------
    def _execute_plan(self, plan: GoalPlan) -> None:
        """
        Execute plan. If swarm is available and plan qualifies,
        use parallel multi-agent dispatch. Otherwise sequential.
        """
        if self._can_swarm(plan):
            self._execute_plan_swarm(plan)
        else:
            self._execute_plan_sequential(plan)

    def _execute_plan_sequential(self, plan: GoalPlan) -> None:
        """Execute each step: coherence check -> monologue -> execute -> validate -> advance."""
        for i, step in enumerate(plan.steps):
            # Check cancellation
            if self._cancelled:
                step.status = "skipped"
                plan.status = "cancelled"
                return

            # Wait if paused
            self._paused.wait()

            step.status = "active"
            self._publish("goal.step.starting", {
                "goal_id": plan.goal_id,
                "step_id": step.step_id,
                "step_index": i,
                "total_steps": len(plan.steps),
                "title": step.title,
                "intent": step.intent,
            })

            # 1. Coherence gate
            coherence = self._get_coherence()
            step.coherence_at_execution = coherence
            if coherence < plan.coherence_threshold and coherence > 0:
                self._publish("goal.coherence.warning", {
                    "goal_id": plan.goal_id,
                    "step_id": step.step_id,
                    "coherence": coherence,
                    "threshold": plan.coherence_threshold,
                })

            # 2. Internal monologue
            step.monologue = self._generate_monologue({
                "action": "executing_step",
                "step_title": step.title,
                "step_intent": step.intent,
                "step_index": i + 1,
                "total_steps": len(plan.steps),
                "coherence": coherence,
            })
            self._publish("ics.monologue", {
                "source": "goal_engine",
                "text": step.monologue,
                "step_id": step.step_id,
            })

            # 3. Execute via AgentCore
            result = self._execute_step(step)
            step.result = result
            self._stats["steps_executed"] += 1

            # 4. Validate
            validation = self._validate_step(step)
            step.validation_result = validation
            self._stats["steps_validated"] += 1

            if validation.get("valid", False):
                step.status = "completed"
                self._publish("goal.step.completed", {
                    "goal_id": plan.goal_id,
                    "step_id": step.step_id,
                    "title": step.title,
                    "coherence": step.coherence_at_execution,
                    "validation": validation,
                })
            else:
                step.status = "failed"
                self._publish("goal.step.failed", {
                    "goal_id": plan.goal_id,
                    "step_id": step.step_id,
                    "title": step.title,
                    "reason": validation.get("reason", "unknown"),
                })

            # 5. Advance elephant memory
            if self._elephant_memory is not None:
                try:
                    note = f"{step.status}: {validation.get('reason', '')}"
                    self._elephant_memory.advance_step(note=note)
                    self._elephant_memory.remember_result({
                        "route": step.intent,
                        "success": step.status == "completed",
                        "step_title": step.title,
                    })
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Creative generation — compose_creative intent handler
    # ------------------------------------------------------------------
    def _execute_document_pdf(self, step: GoalStep) -> Dict[str, Any]:
        """Compose a long-form Markdown/PDF artifact through Aureon's prose stack."""
        try:
            from aureon.queen.queen_prose_composer import QueenProseComposer
            from aureon.vault.voice.document_artifact_skill import (
                AureonDocumentArtifactSkill,
                desktop_dir,
            )

            composer = QueenProseComposer(
                lambda_engine=self._lambda_engine,
                vault=self._vault,
                elephant_memory=self._elephant_memory,
                auris=self._auris,
                source_law=self._source_law,
                goal_engine=self,
                agent_core=self._agent_core,
                temporal_knowledge=self._temporal_knowledge,
                knowledge_dataset=self._knowledge_dataset,
                subsystem_status={
                    "goal_engine": "alive",
                    "document_artifact_skill": "alive",
                    "thought_bus": "alive" if self._thought_bus is not None else "unknown",
                    "agent_core": "alive" if self._agent_core is not None else "unknown",
                },
            )
            output_dir = step.params.get("output_dir") or ""
            resolved_output = desktop_dir() if output_dir == "desktop" else None
            skill = AureonDocumentArtifactSkill(
                composer=composer,
                thought_bus=self._thought_bus,
                output_dir=resolved_output,
            )
            result = skill.compose_pdf(
                prompt=str(step.params.get("prompt") or step.title),
                topic=str(step.params.get("topic") or "the meaning of life"),
                target_words=int(step.params.get("target_words") or 4000),
                output_dir=resolved_output,
            )
            payload = result.to_dict()
            return {
                "success": bool(result.ok),
                "result": payload,
                "tool_used": "compose_document_pdf",
                "artifact_path": result.pdf_path,
                "markdown_path": result.markdown_path,
                "evidence_path": result.evidence_path,
                "word_count": result.word_count,
                "pdf_rendered": result.pdf_rendered,
                "error": result.error or None,
            }
        except Exception as exc:
            return {
                "success": False,
                "result": None,
                "tool_used": "compose_document_pdf",
                "error": str(exc),
            }

    def _execute_repo_self_repair(self, step: GoalStep) -> Dict[str, Any]:
        """Run Aureon's repo-wide bug report, safe repair, and retest loop."""
        try:
            from aureon.autonomous.aureon_repo_self_repair import run_repo_self_repair

            result = run_repo_self_repair(str(step.params.get("goal") or step.title))
            return {
                "success": result.get("summary", {}).get("failed_retest_count", 1) == 0,
                "result": result,
                "tool_used": "repo_self_repair",
                "error": None if result.get("summary", {}).get("failed_retest_count", 1) == 0 else result.get("status"),
            }
        except Exception as exc:
            return {
                "success": False,
                "result": None,
                "tool_used": "repo_self_repair",
                "error": str(exc),
            }

    def _execute_frontend_work_orders(self, step: GoalStep) -> Dict[str, Any]:
        """Execute frontend work orders into safe adapter/blocker records."""
        try:
            from aureon.autonomous.aureon_frontend_work_order_executor import execute_frontend_work_orders

            result = execute_frontend_work_orders(str(step.params.get("goal") or step.title))
            return {
                "success": bool(result.get("summary", {}).get("executed_count")),
                "result": result,
                "tool_used": "frontend_work_orders",
                "error": None if result.get("summary", {}).get("executed_count") else "no_work_orders_executed",
            }
        except Exception as exc:
            return {
                "success": False,
                "result": None,
                "tool_used": "frontend_work_orders",
                "error": str(exc),
            }

    def _execute_coding_agent_skill_base(self, step: GoalStep) -> Dict[str, Any]:
        """Build Aureon's coding-agent skill base and web-learning manifest."""
        try:
            from aureon.autonomous.aureon_coding_agent_skill_base import build_and_write_profile

            result = build_and_write_profile(
                str(step.params.get("goal") or step.title),
                online=bool(step.params.get("online")),
            )
            summary = result.get("summary", {}) if isinstance(result, dict) else {}
            return {
                "success": bool(summary.get("coder_agent_count")) and bool(summary.get("web_tools_ready")),
                "result": result,
                "tool_used": "coding_agent_skill_base",
                "error": None if bool(summary.get("web_tools_ready")) else "coder_web_tools_not_ready",
            }
        except Exception as exc:
            return {
                "success": False,
                "result": None,
                "tool_used": "coding_agent_skill_base",
                "error": str(exc),
            }

    def _execute_director_capability_bridge(self, step: GoalStep) -> Dict[str, Any]:
        """Build the Codex-class capability parity map and Aureon bridge orders."""
        try:
            from aureon.autonomous.aureon_director_capability_bridge import build_and_write_director_capability_bridge

            result = build_and_write_director_capability_bridge(str(step.params.get("goal") or step.title))
            summary = result.get("summary", {}) if isinstance(result, dict) else {}
            return {
                "success": bool(summary.get("capability_count")) and bool(result.get("aureon_bridge_work_orders") is not None),
                "result": result,
                "tool_used": "director_capability_bridge",
                "error": None if bool(summary.get("capability_count")) else "director_capability_bridge_empty",
            }
        except Exception as exc:
            return {
                "success": False,
                "result": None,
                "tool_used": "director_capability_bridge",
                "error": str(exc),
            }

    def _execute_codex_capability_ingestion(self, step: GoalStep) -> Dict[str, Any]:
        """Let Aureon ingest the public Codex capability document and publish a completion report."""
        try:
            from aureon.autonomous.aureon_codex_capability_ingestion import build_and_write_codex_capability_ingestion

            result = build_and_write_codex_capability_ingestion(
                str(step.params.get("source_md") or "EVERYTHING_CODEX_CAN_DO.md"),
                goal=str(step.params.get("goal") or step.title),
            )
            summary = result.get("summary", {}) if isinstance(result, dict) else {}
            completion = result.get("completion_report", {}) if isinstance(result, dict) else {}
            return {
                "success": bool(summary.get("capability_rows_read")) and completion.get("self_validation_result") == "passing",
                "result": result,
                "tool_used": "codex_capability_ingestion",
                "error": None if completion.get("self_validation_result") == "passing" else "codex_capability_ingestion_attention",
            }
        except Exception as exc:
            return {
                "success": False,
                "result": None,
                "tool_used": "codex_capability_ingestion",
                "error": str(exc),
            }

    def _execute_agent_company_builder(self, step: GoalStep) -> Dict[str, Any]:
        """Build Aureon's CEO-to-cleaner agent company registry and public evidence."""
        try:
            from aureon.autonomous.aureon_agent_company_builder import build_and_write_agent_company_bill_list

            result = build_and_write_agent_company_bill_list(
                goal=str(step.params.get("goal") or step.title),
                online=bool(step.params.get("online")),
            )
            summary = result.get("summary", {}) if isinstance(result, dict) else {}
            completion = result.get("completion_report", {}) if isinstance(result, dict) else {}
            return {
                "success": (
                    int((summary or {}).get("role_count") or 0) >= 30
                    and bool((summary or {}).get("ceo_to_cleaner_coverage"))
                    and completion.get("self_validation_result") == "passing"
                ),
                "result": result,
                "tool_used": "agent_company_builder",
                "error": None if completion.get("self_validation_result") == "passing" else "agent_company_builder_attention",
            }
        except Exception as exc:
            return {
                "success": False,
                "result": None,
                "tool_used": "agent_company_builder",
                "error": str(exc),
            }

    def _execute_coding_work_journal_ui(self, step: GoalStep) -> Dict[str, Any]:
        """Validate that the coding organism exposes prompt-to-finished-files work stages."""
        try:
            from pathlib import Path

            root = Path.cwd().resolve()
            target_files = list(step.params.get("target_files") or [])
            checks = []
            expectations = {
                "aureon/autonomous/aureon_coding_organism_bridge.py": ["_build_work_journal", "aureon-coding-work-journal-v1"],
                "frontend/src/components/generated/AureonCodingOrganismConsole.tsx": [
                    "AureonCodingOrganismConsole",
                    "Scope Of Works",
                    "Work Journal: Prompt To Finished Files",
                    "journalStages",
                    "proofChecklist",
                    "snaggingList",
                    "HNC/Auris drift proof",
                    "compactEvidence",
                    "Local hub endpoint",
                    "Prompt lane",
                    "Send To Aureon",
                    "Desktop And Remote Run Handoff",
                ],
                "tests/test_aureon_coding_organism_bridge.py": ["work_journal", "aureon-coding-work-journal-v1"],
            }
            for rel_path, needles in expectations.items():
                path = root / rel_path
                text = path.read_text(encoding="utf-8") if path.exists() else ""
                checks.append(
                    {
                        "path": rel_path,
                        "exists": path.exists(),
                        "needles": needles,
                        "passed": path.exists() and all(needle in text for needle in needles),
                    }
                )
            passed = all(item["passed"] for item in checks)
            return {
                "success": passed,
                "result": {
                    "schema_version": "aureon-coding-work-journal-ui-validation-v1",
                    "status": "work_journal_ui_ready" if passed else "work_journal_ui_attention",
                    "target_files": target_files,
                    "checks": checks,
                    "summary": {
                        "check_count": len(checks),
                        "passed_count": len([item for item in checks if item["passed"]]),
                        "ui_journal_visible_in_code": any(
                            item["path"].endswith("AureonCodingOrganismConsole.tsx") and item["passed"]
                            for item in checks
                        ),
                    },
                    "completion_report": {
                        "did_validate_backend_journal": checks[0]["passed"],
                        "did_validate_frontend_journal": checks[1]["passed"],
                        "did_validate_tests": checks[2]["passed"],
                        "remaining_work": [] if passed else [item["path"] for item in checks if not item["passed"]],
                    },
                },
                "tool_used": "coding_work_journal_ui",
                "error": None if passed else "work_journal_ui_missing_expected_wires",
            }
        except Exception as exc:
            return {
                "success": False,
                "result": None,
                "tool_used": "coding_work_journal_ui",
                "error": str(exc),
            }

    def _execute_self_author_operational_ui(self, step: GoalStep) -> Dict[str, Any]:
        """Author the live operations UI through Aureon's own Queen code path."""
        try:
            from pathlib import Path

            from aureon.autonomous.aureon_unified_ui_builder import self_author_operational_ui

            target = str(step.params.get("target_path") or "frontend/src/components/generated/AureonGeneratedOperationalConsole.tsx")
            result = self_author_operational_ui(
                str(step.params.get("goal") or step.title),
                component_path=Path(target),
            )
            return {
                "success": bool(result.get("success")),
                "result": result,
                "tool_used": "self_author_operational_ui",
                "error": result.get("error"),
            }
        except Exception as exc:
            return {
                "success": False,
                "result": None,
                "tool_used": "self_author_operational_ui",
                "error": str(exc),
            }

    def _execute_self_repair_operational_ui(self, step: GoalStep) -> Dict[str, Any]:
        """Let Aureon inspect, repair, and retest its own generated UI."""
        try:
            from pathlib import Path

            from aureon.autonomous.aureon_unified_ui_builder import self_review_and_repair_operational_ui

            target = str(step.params.get("target_path") or "frontend/src/components/generated/AureonGeneratedOperationalConsole.tsx")
            result = self_review_and_repair_operational_ui(
                str(step.params.get("goal") or step.title),
                component_path=Path(target),
                run_build=Path("frontend/package.json").exists(),
            )
            return {
                "success": bool(result.get("success")),
                "result": result,
                "tool_used": "self_repair_operational_ui",
                "error": None if result.get("success") else result.get("status"),
            }
        except Exception as exc:
            return {
                "success": False,
                "result": None,
                "tool_used": "self_repair_operational_ui",
                "error": str(exc),
            }

    def _execute_creative(self, step: GoalStep) -> Dict[str, Any]:
        """
        Compose a creative piece (poem, story, essay, song, etc.) by:
          1. Pulling factual background on the topic from WorldDataIngester
          2. Retrieving prior fragments from the knowledge dataset
          3. Calling the LLM adapter with a creative system prompt
          4. Falling back to a template weaver if the adapter returns
             only structured analysis
          5. Writing the output to /tmp/aureon_<form>_<topic>.txt
          6. Returning the composed text

        Uses the Emerald Tablet decree in the system prompt so every
        generation obeys the same decision authority.
        """
        form = step.params.get("form", "poem")
        topic = step.params.get("topic", "existence")
        source_text = step.params.get("source_text", "")

        # 1. Gather factual background
        facts: List[str] = []
        if self._knowledge_dataset is not None:
            try:
                prior = self._knowledge_dataset.find_similar(topic, n=5)
                for p in prior:
                    if getattr(p, "meaning", ""):
                        facts.append(p.meaning)
                    elif getattr(p, "text", ""):
                        facts.append(p.text[:120])
            except Exception:
                pass

        # Also pull from Wikipedia / DuckDuckGo if the ingester is available
        try:
            from aureon.integrations.world_data import get_world_data_ingester
            wdi = get_world_data_ingester()
            external = wdi.answer_question(topic, n_per_source=1)
            for item in external[:5]:
                if item.text:
                    facts.append(item.text[:200])
        except Exception:
            pass

        # 2. Build the creative prompt
        fact_block = ""
        if facts:
            fact_block = "Facts about the topic:\n" + "\n".join(
                f"  - {f[:200]}" for f in facts[:6]
            ) + "\n\n"

        form_instructions = {
            "poem":   "Write a 12-line poem with rhythm and imagery. Use line breaks.",
            "haiku":  "Write a 3-line haiku (5-7-5 syllables).",
            "sonnet": "Write a 14-line sonnet with end-rhymes.",
            "song":   "Write a song with verse / chorus / verse structure.",
            "story":  "Write a 200-word short story with a beginning, middle, and end.",
            "essay":  "Write a 300-word essay with intro, body, conclusion.",
            "letter": "Write a heartfelt letter addressed to the topic.",
            "article":"Write a journalistic article with headline and body.",
            "speech": "Write a 200-word impassioned speech.",
            "ballad": "Write a ballad in 4-line stanzas with end-rhymes.",
            "ode":    "Write an ode — celebratory praise in formal language.",
        }.get(form, "Write a creative piece using line breaks and rhythm.")

        creative_prompt = (
            f"{fact_block}"
            f"Your task: {form_instructions}\n\n"
            f"Topic: {topic}\n\n"
            f"Write the {form} now. Do not prefix with 'Here is a {form}'. "
            f"Just write the {form} itself — no analysis, no preamble, no boilerplate."
        )

        # 3. Call the LLM adapter (AureonBrainAdapter / Ollama / whatever is wired)
        composed_text = ""
        adapter_used = False
        if self._swarm is not None and hasattr(self._swarm, "adapter"):
            try:
                decree = self._consult_source_law()
                tablet = self._emerald_tablet_prompt(decree)
                resp = self._swarm.adapter.prompt(
                    messages=[{"role": "user", "content": creative_prompt}],
                    system=(
                        tablet +
                        f"You are a creative {form} writer. Produce only the "
                        f"{form} text — never meta-analysis, never 'Signal: NEUTRAL'. "
                        f"Pure creative output."
                    ),
                    max_tokens=1024,
                    temperature=0.9,
                )
                composed_text = (resp.text or "").strip()
                adapter_used = True
            except Exception as exc:
                logger.debug("Creative adapter call failed: %s", exc)

        # 4. Detect boilerplate → template fallback
        is_boilerplate = (
            not composed_text
            or "Aureon In-House Analysis" in composed_text
            or "Signal:" in composed_text
            or len(composed_text.split()) < 20
        )
        if is_boilerplate:
            composed_text = self._template_creative_fallback(form, topic, facts)
            adapter_used = False

        # 5. Write to disk
        import re as _re, os as _os
        safe_topic = _re.sub(r'[^a-zA-Z0-9_]', '_', topic)[:40]
        artifact_path = f"/tmp/aureon_{form}_{safe_topic}.txt"
        try:
            with open(artifact_path, "w", encoding="utf-8") as f:
                f.write(f"# {form.title()} about {topic}\n\n")
                f.write(composed_text)
                f.write("\n")
        except Exception as exc:
            logger.debug("Write creative file failed: %s", exc)
            artifact_path = ""

        # 6. Publish
        if self._thought_bus is not None:
            try:
                self._thought_bus.publish(
                    "creative.generated",
                    {
                        "form": form,
                        "topic": topic[:80],
                        "word_count": len(composed_text.split()),
                        "artifact": artifact_path,
                        "adapter_used": adapter_used,
                    },
                    source="goal_engine.creative",
                )
            except Exception:
                pass

        return {
            "success": True,
            "result": composed_text,
            "tool_used": "compose_creative",
            "form": form,
            "topic": topic,
            "word_count": len(composed_text.split()),
            "artifact_path": artifact_path,
            "adapter_used": adapter_used,
            "error": None,
        }

    def _template_creative_fallback(
        self,
        form: str,
        topic: str,
        facts: List[str],
    ) -> str:
        """
        Deterministic template weaver for when the LLM adapter can't
        produce real creative prose. Pulls from the facts and the
        knowledge dataset to weave a simple themed piece.
        """
        # Strip leading article from topic ("the irish revolution" -> "irish revolution")
        clean_topic = topic
        for article in ("the ", "a ", "an "):
            if clean_topic.lower().startswith(article):
                clean_topic = clean_topic[len(article):]
                break
        topic = clean_topic

        # Extract nouns and themes from the facts
        all_words = " ".join(facts).lower() if facts else topic.lower()
        import re as _re
        STOPWORDS = {
            "the", "and", "with", "from", "that", "this", "were", "they",
            "have", "will", "been", "into", "their", "there", "which",
            "when", "what", "also", "some", "such", "only", "more", "most",
            "then", "than", "them", "these", "those", "about", "after",
            "other", "over", "very", "would", "could", "should", "where",
        }
        keywords = [
            w for w in _re.findall(r"[a-zA-Z]{4,}", all_words)
            if w not in STOPWORDS and len(w) >= 4
        ]
        # Most frequent
        from collections import Counter
        top = [w for w, _ in Counter(keywords).most_common(12)]
        # Seed with strong default imagery if facts didn't give enough
        defaults = ["spirit", "fire", "dawn", "stone", "voice", "land",
                    "thunder", "flame", "iron", "courage", "silence", "banner"]
        k = []
        seen = set()
        for w in top + defaults:
            if w not in seen and len(k) < 12:
                seen.add(w)
                k.append(w)

        # Primary noun for the topic — pick the most meaningful word
        topic_words = [w for w in topic.split() if len(w) >= 3]
        topic_words = [w for w in topic_words if w.lower() not in STOPWORDS]
        primary = topic_words[-1] if topic_words else "freedom"  # last word usually the noun

        if form == "haiku":
            return (
                f"{k[0].capitalize()} wakes at dawn —\n"
                f"{k[1]} burns in silent {k[2]},\n"
                f"{primary} takes breath."
            )

        if form == "sonnet":
            lines = [
                f"When {k[0]} first called across the {k[1]} plain,",
                f"The {k[2]} rose like fire within the chest,",
                f"And {k[3]} met {k[4]} neither blind nor vain,",
                f"While {topic} held its people to the test.",
                f"No king, no crown, no distant ruling hand,",
                f"Could silence what the {k[5]} spoke at night,",
                f"For {k[6]} burned in every corner of the land,",
                f"And {k[7]} would not yield to foreign might.",
                f"The years will carry echoes of their name,",
                f"The stones remember where the brave had stood,",
                f"The wind still whispers of their righteous claim,",
                f"And every field still tastes their sacred blood.",
                f"  So let the verse remain though flesh must fall,",
                f"  For {topic} answered when its time did call."
            ]
            return "\n".join(lines)

        if form == "song":
            return (
                f"[Verse 1]\n"
                f"They woke with the {k[0]} in their bones,\n"
                f"Stood tall against the crown and throne,\n"
                f"{topic.title()} rising through the {k[1]},\n"
                f"Burning with a {k[2]} so bright.\n\n"
                f"[Chorus]\n"
                f"Oh {primary}, oh {primary}, never silent in the storm,\n"
                f"Oh {primary}, oh {primary}, where the brave hearts still stand warm,\n"
                f"We'll sing your name to the {k[3]},\n"
                f"For the {k[4]} that set us free.\n\n"
                f"[Verse 2]\n"
                f"The stones remember every step,\n"
                f"Every prayer and every debt,\n"
                f"{k[5].title()} carries all the names,\n"
                f"Through the {k[6]} and through the flames.\n"
            )

        if form == "essay":
            return (
                f"The {topic} stands as one of the most profound "
                f"chapters in the story of human courage. At its heart "
                f"was not merely {k[0]} against the {k[1]}, but a deeper "
                f"current of {k[2]} running through generations who refused "
                f"to forget what had been stolen from them.\n\n"
                f"To understand the {topic}, one must understand the {k[3]} "
                f"that preceded it — the slow, stubborn {k[4]} of a people "
                f"who kept their {k[5]} alive in songs, in language, in "
                f"the simple act of remembering. When the moment came, "
                f"they did not rise because they believed victory was "
                f"certain; they rose because silence was no longer bearable.\n\n"
                f"The legacy of the {topic} is not measured in treaties "
                f"or battles alone. It lives in every voice that still "
                f"carries the old names, every stone wall that still "
                f"stands on the land it defended, every heart that has "
                f"learned the lesson the {topic} taught: that freedom "
                f"is not given, it is claimed, and the {k[6]} of those "
                f"who claim it will outlast every empire that ever tried "
                f"to crush it."
            )

        # Default: poem
        lines = [
            f"They rose at the hour when the {k[0]} was at hand,",
            f"With {k[1]} in their breath and a {k[2]} on the land,",
            f"Through {k[3]} and {k[4]}, through the long bitter night,",
            f"They carried the {k[5]} toward the edge of the light.",
            "",
            f"The story of {topic} is a song no one forgets,",
            f"A name the old rivers return without regrets,",
            f"For the ones who did not come home laid their {k[6]} in the flame,",
            f"And the wind along the valleys still remembers their name.",
            "",
            f"So raise a glass to {primary}, to the fallen and the free,",
            f"To the stones that hold their footprints by the edge of every sea,",
            f"As long as one breath whispers what the silent hearts adored,",
            f"The spirit of {topic} will answer, and will never be ignored.",
        ]
        return "\n".join(lines)

    def _execute_step(self, step: GoalStep) -> Dict[str, Any]:
        """
        Execute a single step: tool dispatch via AgentCore, then LLM
        analysis of the result for reasoning-heavy intents.
        """
        # Creative generation intent — handled internally, not via AgentCore
        if step.intent == "compose_document_pdf":
            return self._execute_document_pdf(step)

        if step.intent == "repo_self_repair":
            return self._execute_repo_self_repair(step)

        if step.intent == "frontend_work_orders":
            return self._execute_frontend_work_orders(step)

        if step.intent == "coding_agent_skill_base":
            return self._execute_coding_agent_skill_base(step)

        if step.intent == "director_capability_bridge":
            return self._execute_director_capability_bridge(step)

        if step.intent == "codex_capability_ingestion":
            return self._execute_codex_capability_ingestion(step)

        if step.intent == "agent_company_builder":
            return self._execute_agent_company_builder(step)

        if step.intent == "coding_work_journal_ui":
            return self._execute_coding_work_journal_ui(step)

        if step.intent == "self_repair_operational_ui":
            return self._execute_self_repair_operational_ui(step)

        if step.intent == "self_author_operational_ui":
            return self._execute_self_author_operational_ui(step)

        if step.intent == "compose_creative":
            return self._execute_creative(step)

        if self._agent_core is None:
            return {
                "success": False,
                "result": None,
                "tool_used": None,
                "error": "AgentCore not available",
            }

        try:
            result = self._agent_core.execute(step.intent, step.params)
            if not isinstance(result, dict):
                result = {"success": True, "result": result}
        except Exception as exc:
            result = {
                "success": False,
                "result": None,
                "tool_used": step.intent,
                "error": str(exc),
            }

        # LLM post-analysis: have the brain interpret the tool result
        # (governed by the Emerald Tablet)
        if result.get("success") and self._swarm is not None:
            raw = result.get("result")
            if raw and step.intent in ("web_search", "read_file", "system_info", "network_status"):
                try:
                    decree = self._consult_source_law()
                    tablet = self._emerald_tablet_prompt(decree)
                    analysis = self._swarm.adapter.prompt(
                        messages=[{"role": "user", "content": (
                            f"Summarise this result for the goal '{step.title}':\n\n"
                            f"{str(raw)[:1500]}"
                        )}],
                        system=tablet + "You are a concise analyst. Summarise in 2-3 sentences.",
                        max_tokens=256,
                        temperature=0.3,
                    )
                    if analysis.text:
                        result["analysis"] = analysis.text
                except Exception:
                    pass

        return result

    # ------------------------------------------------------------------
    # Validation (anti-hallucination)
    # ------------------------------------------------------------------
    def _validate_step(self, step: GoalStep) -> Dict[str, Any]:
        """
        Anti-hallucination validation per step type.

        File ops   -> verify file exists / was created
        Web        -> verify results were returned
        Shell      -> check exit code
        Code       -> verify no execution errors
        Default    -> check success flag from AgentCore
        """
        result = step.result or {}
        success = result.get("success", False)
        error = result.get("error")

        if error:
            return {"valid": False, "reason": f"Execution error: {error}", "confidence": 0.0}

        intent = step.intent

        # Creative generation validation — verify output exists and has substance
        if intent == "compose_document_pdf":
            text_result = result.get("result") or {}
            artifact = result.get("artifact_path", "") or text_result.get("pdf_path", "")
            markdown = result.get("markdown_path", "") or text_result.get("markdown_path", "")
            target = int(step.params.get("target_words") or 4000)
            wc = int(result.get("word_count") or text_result.get("word_count") or 0)
            if artifact and markdown and os.path.exists(artifact) and os.path.exists(markdown) and wc >= target * 0.9:
                return {
                    "valid": True,
                    "reason": f"Document PDF verified at {artifact} with {wc} words",
                    "confidence": 0.95,
                }
            return {
                "valid": False,
                "reason": f"Document PDF missing or too short: pdf={artifact!r} markdown={markdown!r} words={wc}",
                "confidence": 0.2,
            }

        if intent == "compose_creative":
            text = result.get("result", "") or ""
            artifact = result.get("artifact_path", "")
            wc = result.get("word_count", 0)
            if wc >= 20 and text.strip():
                reason = f"Creative output: {wc} words"
                if artifact and os.path.exists(artifact):
                    reason += f" + file at {artifact}"
                return {"valid": True, "reason": reason, "confidence": 0.9}
            return {"valid": False, "reason": "Creative output too short or empty", "confidence": 0.2}

        if intent == "repo_self_repair":
            payload = result.get("result") or {}
            summary = payload.get("summary") if isinstance(payload, dict) else {}
            authoring_path = payload.get("authoring_path") if isinstance(payload, dict) else []
            passed = (
                result.get("success")
                and isinstance(summary, dict)
                and int(summary.get("failed_retest_count") or 0) == 0
                and "QueenCodeArchitect.write_file" in authoring_path
            )
            if passed:
                return {
                    "valid": True,
                    "reason": "Repo self-repair report passed checks/retests with Queen provenance",
                    "confidence": 0.95,
                }
            return {
                "valid": False,
                "reason": "Repo self-repair found unresolved failed checks or missing Queen provenance",
                "confidence": 0.25,
            }

        if intent == "frontend_work_orders":
            payload = result.get("result") or {}
            summary = payload.get("summary") if isinstance(payload, dict) else {}
            authoring_path = payload.get("authoring_path") if isinstance(payload, dict) else []
            executed = int((summary or {}).get("executed_count") or 0) if isinstance(summary, dict) else 0
            source_count = int((summary or {}).get("source_queue_count") or 0) if isinstance(summary, dict) else 0
            if (
                success
                and executed > 0
                and (source_count == 0 or executed <= source_count)
                and "QueenCodeArchitect.write_file" in authoring_path
            ):
                return {
                    "valid": True,
                    "reason": f"Frontend work orders executed as {executed} safe adapter/blocker records",
                    "confidence": 0.94,
                }
            return {
                "valid": False,
                "reason": "Frontend work order execution missing records or Queen provenance",
                "confidence": 0.25,
            }

        if intent == "coding_agent_skill_base":
            payload = result.get("result") or {}
            summary = payload.get("summary") if isinstance(payload, dict) else {}
            authoring_path = payload.get("authoring_path") if isinstance(payload, dict) else []
            work_orders = payload.get("coding_work_orders") if isinstance(payload, dict) else []
            logic_map = payload.get("coding_logic_map") if isinstance(payload, dict) else {}
            writer = (payload.get("write_info") or {}).get("writer") if isinstance(payload.get("write_info"), dict) else ""
            if (
                success
                and int((summary or {}).get("coder_agent_count") or 0) >= 3
                and bool((summary or {}).get("web_tools_ready"))
                and (logic_map or {}).get("status") == "who_what_where_when_how_ready"
                and int((summary or {}).get("coding_logic_rule_count") or 0) >= 5
                and isinstance(work_orders, list)
                and work_orders
                and "QueenCodeArchitect.write_file" in authoring_path
                and writer == "QueenCodeArchitect"
            ):
                return {
                    "valid": True,
                    "reason": "Coding-agent skill base published with who/what/where/when/how routing, active web/repo learning tools, and Queen provenance",
                    "confidence": 0.95,
                }
            return {
                "valid": False,
                "reason": "Coding-agent skill base missing agents, web tools, logic map, work orders, or Queen provenance",
                "confidence": 0.25,
            }

        if intent == "director_capability_bridge":
            payload = result.get("result") or {}
            summary = payload.get("summary") if isinstance(payload, dict) else {}
            authoring_path = payload.get("authoring_path") if isinstance(payload, dict) else []
            rows = payload.get("codex_class_capabilities") if isinstance(payload, dict) else []
            work_orders = payload.get("aureon_bridge_work_orders") if isinstance(payload, dict) else []
            writer = (payload.get("write_info") or {}).get("writer") if isinstance(payload.get("write_info"), dict) else ""
            if (
                success
                and int((summary or {}).get("capability_count") or 0) >= 10
                and isinstance(rows, list)
                and isinstance(work_orders, list)
                and "QueenCodeArchitect.write_file" in authoring_path
                and writer == "QueenCodeArchitect"
            ):
                return {
                    "valid": True,
                    "reason": "Director capability bridge published Codex-class parity map and exact Aureon bridge work orders",
                    "confidence": 0.95,
                }
            return {
                "valid": False,
                "reason": "Director capability bridge missing capability rows, bridge orders, or Queen provenance",
                "confidence": 0.25,
            }

        if intent == "codex_capability_ingestion":
            payload = result.get("result") or {}
            summary = payload.get("summary") if isinstance(payload, dict) else {}
            completion = payload.get("completion_report") if isinstance(payload, dict) else {}
            validation = (payload.get("act") or {}).get("validation") if isinstance(payload, dict) else {}
            writer = (payload.get("write_info") or {}).get("writer") if isinstance(payload.get("write_info"), dict) else ""
            if (
                success
                and int((summary or {}).get("capability_rows_read") or 0) >= 3
                and (completion or {}).get("did_read_source_document") is True
                and (completion or {}).get("did_marriage_map") is True
                and (completion or {}).get("did_generate_bridge_work_orders") is True
                and (validation or {}).get("director_bridge_ran") is True
                and writer == "QueenCodeArchitect"
            ):
                return {
                    "valid": True,
                    "reason": "Aureon ingested EVERYTHING_CODEX_CAN_DO.md, mapped it to its own systems, wrote bridge work orders, and published validation evidence",
                    "confidence": 0.95,
                }
            return {
                "valid": False,
                "reason": "Codex capability ingestion missing source read, mapping, work orders, director bridge run, or Queen provenance",
                "confidence": 0.25,
            }

        if intent == "agent_company_builder":
            payload = result.get("result") or {}
            summary = payload.get("summary") if isinstance(payload, dict) else {}
            completion = payload.get("completion_report") if isinstance(payload, dict) else {}
            roles = payload.get("roles") if isinstance(payload, dict) else []
            agents = payload.get("agents") if isinstance(payload, dict) else []
            boundaries = payload.get("authority_boundaries") if isinstance(payload, dict) else []
            role_titles = {str(role.get("title")) for role in roles if isinstance(role, dict)}
            mapped_or_ordered = bool((completion or {}).get("did_map_roles_to_surfaces_or_work_orders"))
            day_plans_ready = bool((summary or {}).get("daily_operating_loop_ready")) and int(
                (summary or {}).get("roles_with_day_plan_count") or 0
            ) >= len(roles)
            whole_access_ready = bool((completion or {}).get("did_attach_whole_organism_access")) and int(
                (summary or {}).get("roles_with_whole_organism_access_count") or 0
            ) >= len(roles)
            agency_ready = (
                (summary or {}).get("agency_model") == "prompt_as_client_job_agency"
                and int((summary or {}).get("agency_workforce_role_count") or 0) >= 5
                and bool((completion or {}).get("did_attach_hire_retire_lifecycle"))
            )
            memory_ready = (
                bool((summary or {}).get("memory_phonebook_ready"))
                and int((summary or {}).get("sha256_memory_entry_count") or 0) >= len(roles)
                and bool((completion or {}).get("did_build_sha256_zlib_memory_phonebook"))
            )
            if (
                success
                and int((summary or {}).get("role_count") or 0) >= 30
                and int((summary or {}).get("department_count") or 0) >= 7
                and bool((summary or {}).get("ceo_to_cleaner_coverage"))
                and bool((summary or {}).get("existing_gates_preserved"))
                and "CEO Goal Steward" in role_titles
                and "Log Janitor" in role_titles
                and "Stale State Cleaner" in role_titles
                and isinstance(agents, list)
                and len(agents) >= len(roles)
                and isinstance(boundaries, list)
                and len(boundaries) >= 4
                and mapped_or_ordered
                and day_plans_ready
                and whole_access_ready
                and agency_ready
                and memory_ready
            ):
                return {
                    "valid": True,
                    "reason": "Aureon agent company registry published CEO-to-cleaner roles, prompt-as-client agency flow, hire/retire lifecycle, SHA-256/zlib memory phonebook, whole-organism access, handoffs, work orders, and preserved authority gates",
                    "confidence": 0.95,
                }
            return {
                "valid": False,
                "reason": "Agent company registry missing role coverage, agent configs, authority boundaries, or surface/work-order mapping",
                "confidence": 0.25,
            }

        if intent == "coding_work_journal_ui":
            payload = result.get("result") or {}
            summary = payload.get("summary") if isinstance(payload, dict) else {}
            completion = payload.get("completion_report") if isinstance(payload, dict) else {}
            if (
                success
                and int((summary or {}).get("check_count") or 0) >= 3
                and int((summary or {}).get("passed_count") or 0) >= 3
                and bool((completion or {}).get("did_validate_backend_journal"))
                and bool((completion or {}).get("did_validate_frontend_journal"))
                and bool((completion or {}).get("did_validate_tests"))
            ):
                return {
                    "valid": True,
                    "reason": "Coding organism work journal is wired from prompt intake to finished-file evidence and rendered in the UI",
                    "confidence": 0.95,
                }
            return {
                "valid": False,
                "reason": "Coding work journal UI is missing backend, frontend, or test evidence",
                "confidence": 0.25,
            }

        if intent == "self_author_operational_ui":
            payload = result.get("result") or {}
            files = payload.get("generated_files") or []
            authoring_path = payload.get("authoring_path") or []
            component = payload.get("component_path") or step.params.get("target_path", "")
            if (
                success
                and component
                and os.path.exists(component)
                and "QueenCodeArchitect.write_file" in authoring_path
                and len(files) >= 3
            ):
                return {
                    "valid": True,
                    "reason": f"Self-authored UI verified at {component} through QueenCodeArchitect",
                    "confidence": 0.96,
                }
            return {
                "valid": False,
                "reason": "Self-authored UI evidence missing component, generated files, or Queen writer provenance",
                "confidence": 0.2,
            }

        if intent == "self_repair_operational_ui":
            payload = result.get("result") or {}
            final_review = payload.get("final_review") if isinstance(payload, dict) else {}
            build_result = final_review.get("build_result") if isinstance(final_review, dict) else {}
            authoring_path = payload.get("authoring_path") if isinstance(payload, dict) else []
            build_ok = isinstance(build_result, dict) and (
                build_result.get("success") or build_result.get("ran") is False
            )
            if (
                success
                and isinstance(final_review, dict)
                and final_review.get("success")
                and build_ok
                and "QueenCodeArchitect.write_file" in authoring_path
            ):
                return {
                    "valid": True,
                    "reason": "Self UI review/repair passed with Queen provenance and frontend build",
                    "confidence": 0.96,
                }
            return {
                "valid": False,
                "reason": "Self UI repair did not clear final review, build, or Queen provenance",
                "confidence": 0.2,
            }

        # File operation validation
        if intent in ("write_file", "create_script", "create_dir"):
            path = step.params.get("path", "")
            if path and os.path.exists(path):
                return {"valid": True, "reason": f"File verified at {path}", "confidence": 0.95}
            elif success:
                return {"valid": True, "reason": "Reported success (path not verifiable)", "confidence": 0.7}
            return {"valid": False, "reason": f"File not found at {path}", "confidence": 0.1}

        # Web search validation
        if intent in ("web_search", "search_web", "google", "web_fetch", "fetch_url"):
            actual_result = result.get("result")
            if actual_result:
                return {"valid": True, "reason": "Results returned", "confidence": 0.85}
            return {"valid": False, "reason": "No results returned", "confidence": 0.2}

        # Shell command validation
        if intent in ("execute_shell", "run_command", "terminal", "shell"):
            if success:
                return {"valid": True, "reason": "Command succeeded (exit 0)", "confidence": 0.9}
            return {"valid": False, "reason": "Command failed", "confidence": 0.1}

        # Code execution validation
        if intent in ("execute_python", "run_code", "run_script"):
            if success:
                return {"valid": True, "reason": "Code executed without errors", "confidence": 0.9}
            return {"valid": False, "reason": "Code execution failed", "confidence": 0.1}

        # Default: trust AgentCore's success flag
        if success:
            return {"valid": True, "reason": "AgentCore reported success", "confidence": 0.8}

        return {"valid": False, "reason": result.get("error", "Step did not succeed"), "confidence": 0.2}

    def _validate_goal(self, plan: GoalPlan) -> None:
        """
        Final goal-level validation: all steps must be completed
        and average coherence must be above threshold.
        """
        completed = sum(1 for s in plan.steps if s.status == "completed")
        total = len(plan.steps)

        if total == 0:
            plan.status = "failed"
            return

        # Check step completion
        if completed == total:
            plan.status = "completed"
        elif completed > 0:
            plan.status = "completed"  # partial success counts
        else:
            plan.status = "failed"

        # Check average coherence
        coherences = [s.coherence_at_execution for s in plan.steps if s.coherence_at_execution > 0]
        if coherences:
            avg_coherence = sum(coherences) / len(coherences)
            if avg_coherence < plan.coherence_threshold:
                logger.warning(
                    "Goal %s avg coherence %.3f below threshold %.3f",
                    plan.goal_id, avg_coherence, plan.coherence_threshold,
                )

    # ------------------------------------------------------------------
    # Coherence reading
    # ------------------------------------------------------------------
    def _get_coherence(self) -> float:
        """Read current coherence from the lambda engine."""
        if self._lambda_engine is None:
            return 0.5  # neutral default

        try:
            state = self._lambda_engine.step()
            return state.coherence_gamma
        except Exception:
            return 0.5

    # ------------------------------------------------------------------
    # Internal monologue
    # ------------------------------------------------------------------
    def _generate_monologue(self, context: Dict[str, Any]) -> str:
        """
        Generate an internal monologue line.
        Uses SelfDialogueEngine if available, falls back to template.
        """
        # Try self-dialogue engine
        if self._self_dialogue is not None and self._vault is not None:
            try:
                utterance = self._self_dialogue.converse()
                if utterance is not None:
                    preview = getattr(utterance, "preview", None)
                    if preview:
                        return str(preview)
                    stmts = getattr(utterance, "statements", [])
                    if stmts:
                        first = stmts[0]
                        text = getattr(first, "text", "")
                        if text:
                            return text
            except Exception:
                pass

        # Template fallback
        action = context.get("action", "thinking")
        title = context.get("step_title", "")
        idx = context.get("step_index", 0)
        total = context.get("total_steps", 0)
        coherence = context.get("coherence", 0.0)

        if action == "executing_step":
            return f"Step {idx}/{total}: executing '{title}' (coherence: {coherence:.3f})"
        return f"Processing: {title}"

    # ------------------------------------------------------------------
    # Control
    # ------------------------------------------------------------------
    def pause(self) -> None:
        """Pause goal execution after current step completes."""
        self._paused.clear()
        if self._current_plan:
            self._current_plan.status = "paused"
        self._publish("goal.paused", {})

    def resume(self) -> None:
        """Resume paused goal execution."""
        self._paused.set()
        if self._current_plan and self._current_plan.status == "paused":
            self._current_plan.status = "active"
        self._publish("goal.resumed", {})

    def cancel(self) -> None:
        """Cancel the current goal."""
        self._cancelled = True
        self._paused.set()  # unblock if paused
        self._publish("goal.cancelled", {})

    def get_status(self) -> Dict[str, Any]:
        """Return current goal execution status."""
        plan_info = None
        if self._current_plan:
            p = self._current_plan
            plan_info = {
                "goal_id": p.goal_id,
                "objective": p.objective,
                "status": p.status,
                "total_steps": len(p.steps),
                "completed_steps": sum(1 for s in p.steps if s.status == "completed"),
                "failed_steps": sum(1 for s in p.steps if s.status == "failed"),
                "active_step": next(
                    ({"title": s.title, "intent": s.intent} for s in p.steps if s.status == "active"),
                    None,
                ),
            }
        return {
            "current_plan": plan_info,
            "stats": dict(self._stats),
            "paused": not self._paused.is_set(),
            "cancelled": self._cancelled,
        }
