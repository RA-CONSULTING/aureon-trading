"""
AgentRunner — Conversation Loop + Tool Dispatch
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Manages the full conversation lifecycle for an Agent:
  - Multi-turn conversation with memory
  - Automatic tool dispatch
  - Message history management
  - Event callbacks for monitoring
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generator, List, Optional

from aureon.inhouse_ai.llm_adapter import LLMAdapter, LLMResponse, StreamChunk
from aureon.inhouse_ai.tool_registry import ToolRegistry

logger = logging.getLogger("aureon.inhouse_ai.runner")


@dataclass
class ConversationMessage:
    """A message in the conversation history."""

    role: str  # user | assistant | tool
    content: Any
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentRunner:
    """
    Manages the conversation loop for an agent.

    The runner maintains conversation state and handles:
      - Multi-turn conversation with automatic tool dispatch
      - Streaming with tool interleaving
      - Conversation history pruning
      - Event callbacks (on_message, on_tool_call, on_error)

    Usage:
        runner = AgentRunner(adapter, registry)
        runner.set_system("You are the Nexus agent...")

        # Single turn
        response = runner.turn("What's the market state?")

        # Continuous loop
        runner.loop(interval=60, task_fn=lambda: "Analyse current signals")
    """

    def __init__(
        self,
        adapter: LLMAdapter,
        tools: Optional[ToolRegistry] = None,
        system_prompt: str = "",
        max_turns: int = 8,
        max_history: int = 50,
    ):
        self.adapter = adapter
        self.tools = tools or ToolRegistry(include_builtins=True)
        self.system_prompt = system_prompt
        self.max_turns = max_turns
        self.max_history = max_history

        self._history: List[ConversationMessage] = []
        self._messages: List[Dict[str, Any]] = []
        self._running = False
        self._turn_count = 0

        # Callbacks
        self.on_message: Optional[Callable[[str, str], None]] = None
        self.on_tool_call: Optional[Callable[[str, Dict], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None

    def set_system(self, prompt: str):
        """Update the system prompt."""
        self.system_prompt = prompt

    def turn(self, message: str) -> str:
        """
        Execute a single conversational turn.

        Sends the message, handles any tool calls in an agentic loop,
        and returns the final text response.
        """
        # Add user message
        self._messages.append({"role": "user", "content": message})
        self._history.append(ConversationMessage(role="user", content=message))

        if self.on_message:
            self.on_message("user", message)

        tool_defs = self.tools.list_tools() if self.tools else None

        for turn_idx in range(self.max_turns):
            self._turn_count += 1

            response = self.adapter.prompt(
                messages=self._messages,
                system=self.system_prompt,
                tools=tool_defs,
                max_tokens=4096,
            )

            # Build assistant content
            if response.has_tool_calls:
                content = []
                if response.text:
                    content.append({"type": "text", "text": response.text})
                for tc in response.tool_calls:
                    content.append({
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.arguments,
                    })
                self._messages.append({"role": "assistant", "content": content})
            else:
                self._messages.append({"role": "assistant", "content": response.text})

            # No tool calls → final answer
            if not response.has_tool_calls:
                self._history.append(ConversationMessage(
                    role="assistant", content=response.text,
                ))
                if self.on_message:
                    self.on_message("assistant", response.text)
                self._prune_history()
                return response.text

            # Dispatch tool calls
            tool_results = []
            for tc in response.tool_calls:
                if self.on_tool_call:
                    self.on_tool_call(tc.name, tc.arguments)
                logger.info("Tool dispatch: %s(%s)", tc.name, tc.arguments)

                result_str = self.tools.execute(tc.name, tc.arguments)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": result_str,
                })

            self._messages.append({"role": "user", "content": tool_results})

        # Max turns hit
        fallback = response.text if response else "Max conversation turns reached."
        self._history.append(ConversationMessage(role="assistant", content=fallback))
        return fallback

    def stream_turn(self, message: str) -> Generator[StreamChunk, None, None]:
        """
        Stream a single turn.  Yields text chunks and tool call events.
        Note: tool dispatch still happens synchronously between stream segments.
        """
        self._messages.append({"role": "user", "content": message})
        tool_defs = self.tools.list_tools() if self.tools else None

        for turn_idx in range(self.max_turns):
            collected_text = ""
            collected_tool_calls = []

            for chunk in self.adapter.stream(
                messages=self._messages,
                system=self.system_prompt,
                tools=tool_defs,
                max_tokens=4096,
            ):
                if chunk.text:
                    collected_text += chunk.text
                    yield chunk

                if chunk.tool_call:
                    collected_tool_calls.append(chunk.tool_call)

                if chunk.done:
                    break

            # If no tool calls → done
            if not collected_tool_calls:
                self._messages.append({"role": "assistant", "content": collected_text})
                yield StreamChunk(done=True, stop_reason="end_turn")
                return

            # Build assistant content with tool calls
            content = []
            if collected_text:
                content.append({"type": "text", "text": collected_text})
            for tc in collected_tool_calls:
                content.append({
                    "type": "tool_use",
                    "id": tc.id,
                    "name": tc.name,
                    "input": tc.arguments,
                })
            self._messages.append({"role": "assistant", "content": content})

            # Dispatch tools
            tool_results = []
            for tc in collected_tool_calls:
                result_str = self.tools.execute(tc.name, tc.arguments)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": result_str,
                })
            self._messages.append({"role": "user", "content": tool_results})

        yield StreamChunk(done=True, stop_reason="max_turns")

    def loop(
        self,
        task_fn: Callable[[], str],
        interval: float = 60.0,
        max_iterations: Optional[int] = None,
        on_result: Optional[Callable[[str], None]] = None,
    ):
        """
        Run the agent in a continuous loop.

        Args:
            task_fn: Callable that returns the task/prompt for each iteration
            interval: Seconds between iterations
            max_iterations: Stop after N iterations (None = infinite)
            on_result: Callback with each iteration's result
        """
        self._running = True
        iteration = 0

        try:
            while self._running:
                if max_iterations and iteration >= max_iterations:
                    break

                iteration += 1
                task = task_fn()

                try:
                    result = self.turn(task)
                    if on_result:
                        on_result(result)
                except Exception as e:
                    logger.error("Loop iteration %d failed: %s", iteration, e)
                    if self.on_error:
                        self.on_error(e)

                if self._running and (max_iterations is None or iteration < max_iterations):
                    time.sleep(interval)
        finally:
            self._running = False

    def stop(self):
        """Stop the conversation loop."""
        self._running = False

    def clear_history(self):
        """Clear conversation history."""
        self._messages.clear()
        self._history.clear()
        self._turn_count = 0

    def _prune_history(self):
        """Keep history within max_history limit."""
        if len(self._messages) > self.max_history * 2:
            # Keep system-relevant first message and last N messages
            self._messages = self._messages[:1] + self._messages[-(self.max_history * 2 - 1):]

    def get_history(self) -> List[Dict[str, Any]]:
        """Return conversation history."""
        return [
            {
                "role": m.role,
                "content": m.content if isinstance(m.content, str) else str(m.content),
                "timestamp": m.timestamp,
            }
            for m in self._history
        ]

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "turn_count": self._turn_count,
            "message_count": len(self._messages),
            "history_count": len(self._history),
        }
