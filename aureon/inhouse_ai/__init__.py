"""
Aureon In-House AI Framework
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Fully sovereign multi-agent orchestration — no external AI dependencies.
Replaces Anthropic, OpenAI, and Copilot with in-house alternatives:

  LLMAdapter layer:
    - AureonLocalAdapter   : connects to self-hosted models (Ollama, vLLM, llama.cpp, HF TGI)
    - AureonBrainAdapter   : uses the existing AureonBrain intelligence as reasoning backend
    - AureonHybridAdapter  : chains local LLM + AureonBrain for best-of-both

  Multi-Agent framework (matching the OpenMultiAgent architecture):
    - OpenMultiAgent       : top-level orchestrator
    - Team                 : agent group with shared bus, queue, memory
    - AgentPool            : semaphore-controlled parallel execution
    - TaskQueue            : dependency graph with auto-unblock + cascade failure
    - Agent                : run(), prompt(), stream()
    - AgentRunner          : conversation loop + tool dispatch
    - ToolRegistry         : defineTool() + 5 built-in tools

Gary Leckey / Aureon Institute — 2025/2026
"""

from aureon.inhouse_ai.llm_adapter import (
    LLMAdapter,
    AureonLocalAdapter,
    AureonBrainAdapter,
    AureonHybridAdapter,
    LLMResponse,
    StreamChunk,
)
from aureon.inhouse_ai.tool_registry import ToolRegistry, ToolDefinition
from aureon.inhouse_ai.agent import Agent, AgentConfig
from aureon.inhouse_ai.agent_runner import AgentRunner
from aureon.inhouse_ai.agent_pool import AgentPool
from aureon.inhouse_ai.task_queue import TaskQueue, Task, TaskStatus
from aureon.inhouse_ai.team import Team
from aureon.inhouse_ai.orchestrator import OpenMultiAgent

__all__ = [
    # LLM adapters
    "LLMAdapter",
    "AureonLocalAdapter",
    "AureonBrainAdapter",
    "AureonHybridAdapter",
    "LLMResponse",
    "StreamChunk",
    # Tools
    "ToolRegistry",
    "ToolDefinition",
    # Agent
    "Agent",
    "AgentConfig",
    "AgentRunner",
    "AgentPool",
    # Task management
    "TaskQueue",
    "Task",
    "TaskStatus",
    # Coordination
    "Team",
    "OpenMultiAgent",
]
