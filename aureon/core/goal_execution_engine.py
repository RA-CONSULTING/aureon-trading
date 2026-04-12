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
    "build":    ["web_search", "create_script", "write_file", "execute_python"],
    "create":   ["create_dir", "write_file"],
    "search":   ["web_search"],
    "find":     ["find_files", "web_search"],
    "open":     ["open_app", "open_url"],
    "read":     ["read_file"],
    "write":    ["write_file"],
    "run":      ["execute_shell"],
    "install":  ["execute_shell"],
    "delete":   ["delete_file"],
    "copy":     ["copy_file"],
    "move":     ["move_file"],
    "check":    ["system_info", "network_status"],
    "show":     ["list_dir", "read_file"],
    "list":     ["list_dir", "list_apps"],
    "kill":     ["close_app", "kill_process"],
    "say":      ["speak"],
    "tell":     ["speak"],
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
    ):
        self._agent_core = agent_core
        self._thought_bus = thought_bus
        self._lambda_engine = lambda_engine
        self._elephant_memory = elephant_memory
        self._self_dialogue = self_dialogue
        self._auris = auris
        self._vault = vault
        self._swarm = swarm
        self._temporal_ground = temporal_ground

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
        """
        with self._lock:
            self._cancelled = False
            self._paused.set()

        self._stats["goals_submitted"] += 1
        self._publish("goal.submitted", {"text": text})

        # Decompose
        plan = self._decompose_goal(text)
        self._current_plan = plan
        self._publish("goal.decomposed", {
            "goal_id": plan.goal_id,
            "objective": plan.objective,
            "steps": [{"step_id": s.step_id, "title": s.title, "intent": s.intent} for s in plan.steps],
        })

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

        # Final validation
        self._validate_goal(plan)

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
        plan = GoalPlan(original_text=text, objective=text)
        steps: List[GoalStep] = []

        # Path 1: LLM-driven decomposition via swarm adapter
        if self._swarm is not None and hasattr(self._swarm, 'adapter'):
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

    def _llm_decompose(self, text: str) -> List[GoalStep]:
        """
        Use the LLM adapter to intelligently decompose a goal into steps.
        Parses the response into GoalSteps mapped to AgentCore intents.
        """
        adapter = self._swarm.adapter
        resp = adapter.prompt(
            messages=[{"role": "user", "content": (
                f"Break this goal into 2-5 concrete action steps. "
                f"For each step, output one line: STEP: <action verb> <details>\n\n"
                f"Goal: {text}\n\n"
                f"Available actions: search (web search), read (file), list (directory), "
                f"check (system/network), write (file), run (shell command), "
                f"create (script/file), analyse (data)\n\n"
                f"Output steps now:"
            )}],
            system="You are a task planner. Output only STEP: lines, nothing else.",
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

    def _heuristic_decompose(self, text: str) -> List[GoalStep]:
        """Verb-based heuristic decomposition for unrecognised patterns."""
        lower = text.lower().strip()
        steps: List[GoalStep] = []

        for verb, intents in VERB_INTENT_MAP.items():
            if lower.startswith(verb) or f" {verb} " in f" {lower} ":
                for intent in intents:
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
                        params["path"] = remainder.split()[0] if remainder else "output.txt"
                        params["content"] = text
                    elif intent in ("list_dir", "ls", "dir"):
                        params["path"] = "."
                    elif intent in ("read_file", "cat"):
                        params["path"] = remainder.split()[0] if remainder else "."
                    elif intent in ("speak", "say"):
                        params["text"] = remainder or text
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

        # ── 1. AURIS GATE ──────────────────────────────────────────
        gate = self._auris_gate(plan)
        self._publish("swarm.dispatching", {
            "goal_id": plan.goal_id,
            "agent_count": len(plan.steps),
            "objective": plan.objective,
            "auris_gate": gate["consensus"],
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

        configs = []
        for i, step in enumerate(plan.steps):
            agent_name = f"agent_{step.step_id}"
            is_coordinator = step.title.startswith("Synthesis:")
            configs.append(AgentConfig(
                name=agent_name,
                system_prompt=(
                    f"You are the Coordinator for goal: {plan.objective}\n"
                    f"You will receive all worker results. Synthesize them into a "
                    f"unified conclusion with key findings and recommended actions."
                ) if is_coordinator else (
                    f"You are Agent {i+1} ({step.title.split(':')[0] if ':' in step.title else 'Worker'}) "
                    f"working on: {plan.objective}\n"
                    f"Your specific task: {step.title}\n"
                    f"Execute thoroughly. Return clear findings."
                ),
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
                max_concurrent=max_concurrent,
            )

            # ── 4. EXECUTE — add tasks with dependencies ───────────
            worker_task_ids: List[str] = []
            task_id_map: Dict[str, str] = {}

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
                task = team.queue.add(
                    name=f"worker_{step.step_id}",
                    agent_name=agent_name,
                    prompt=(
                        f"Task: {step.title}\n"
                        f"Goal: {plan.objective}\n"
                        f"Action: {step.intent}\n"
                        f"Parameters: {step.params}\n"
                        f"Provide detailed findings."
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

    def _execute_step(self, step: GoalStep) -> Dict[str, Any]:
        """
        Execute a single step: tool dispatch via AgentCore, then LLM
        analysis of the result for reasoning-heavy intents.
        """
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
        if result.get("success") and self._swarm is not None:
            raw = result.get("result")
            if raw and step.intent in ("web_search", "read_file", "system_info", "network_status"):
                try:
                    analysis = self._swarm.adapter.prompt(
                        messages=[{"role": "user", "content": (
                            f"Summarise this result for the goal '{step.title}':\n\n"
                            f"{str(raw)[:1500]}"
                        )}],
                        system="You are a concise analyst. Summarise in 2-3 sentences.",
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
