"""
LLM Adapter Layer — In-House Sovereign AI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Replaces Anthropic / OpenAI / Copilot with fully in-house alternatives:

  AureonLocalAdapter   — self-hosted LLM via HTTP (Ollama, vLLM, llama.cpp, HF TGI)
  AureonBrainAdapter   — existing AureonBrain intelligence as reasoning engine
  AureonHybridAdapter  — local LLM + AureonBrain combined

All adapters implement the same LLMAdapter interface so agents are backend-agnostic.
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generator, List, Optional

logger = logging.getLogger("aureon.inhouse_ai.llm")

# ─────────────────────────────────────────────────────────────────────────────
# Response types
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ToolCall:
    """A tool invocation requested by the model."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    arguments: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Unified response from any adapter."""

    text: str = ""
    tool_calls: List[ToolCall] = field(default_factory=list)
    stop_reason: str = "end_turn"  # end_turn | tool_use | max_tokens
    usage: Dict[str, int] = field(default_factory=dict)
    model: str = ""
    raw: Any = None  # adapter-specific raw response

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


@dataclass
class StreamChunk:
    """A single chunk during streaming."""

    text: str = ""
    tool_call: Optional[ToolCall] = None
    done: bool = False
    stop_reason: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Base adapter
# ─────────────────────────────────────────────────────────────────────────────


class LLMAdapter(ABC):
    """
    Abstract base for all LLM backends.
    Every adapter must implement prompt() and stream().
    """

    @abstractmethod
    def prompt(
        self,
        messages: List[Dict[str, Any]],
        system: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> LLMResponse:
        """Send a prompt and return the complete response."""

    @abstractmethod
    def stream(
        self,
        messages: List[Dict[str, Any]],
        system: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> Generator[StreamChunk, None, None]:
        """Stream response token-by-token."""

    def health_check(self) -> bool:
        """Return True if the backend is reachable."""
        return True


# ─────────────────────────────────────────────────────────────────────────────
# AureonLocalAdapter — self-hosted model server
# ─────────────────────────────────────────────────────────────────────────────


class AureonLocalAdapter(LLMAdapter):
    """
    Connects to a self-hosted LLM server via HTTP.

    Supported backends (all expose an OpenAI-compatible /v1/chat/completions):
      - Ollama        (default: http://localhost:11434/v1)
      - vLLM          (default: http://localhost:8000/v1)
      - llama.cpp     (default: http://localhost:8080/v1)
      - HuggingFace TGI (default: http://localhost:8080/v1)
      - LocalAI       (default: http://localhost:8080/v1)

    Environment variables:
      AUREON_LLM_BASE_URL   — override base URL
      AUREON_LLM_MODEL      — override model name
      AUREON_LLM_API_KEY    — optional API key for the local server
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.base_url = (
            base_url
            or os.environ.get("AUREON_LLM_BASE_URL", "http://localhost:11434/v1")
        ).rstrip("/")
        self.model = model or os.environ.get("AUREON_LLM_MODEL", "llama3")
        self.api_key = api_key or os.environ.get("AUREON_LLM_API_KEY", "")

        try:
            import requests

            self._session = requests.Session()
        except ImportError:
            self._session = None
            logger.warning("requests not installed — HTTP adapter degraded")

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _build_payload(
        self,
        messages: List[Dict[str, Any]],
        system: str,
        tools: Optional[List[Dict[str, Any]]],
        max_tokens: int,
        temperature: float,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Build an OpenAI-compatible chat completion payload."""
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            # Handle tool_result messages → assistant tool response format
            if isinstance(content, list):
                # Check if it's tool results
                tool_results = [
                    c for c in content if isinstance(c, dict) and c.get("type") == "tool_result"
                ]
                if tool_results:
                    for tr in tool_results:
                        full_messages.append({
                            "role": "tool",
                            "tool_call_id": tr.get("tool_use_id", ""),
                            "content": tr.get("content", ""),
                        })
                    continue

                # Extract text from content blocks
                text_parts = []
                for c in content:
                    if isinstance(c, dict):
                        if c.get("type") == "text":
                            text_parts.append(c.get("text", ""))
                        elif hasattr(c, "text"):
                            text_parts.append(c.text)
                    elif isinstance(c, str):
                        text_parts.append(c)
                    elif hasattr(c, "text"):
                        text_parts.append(c.text)
                content = "\n".join(text_parts) if text_parts else str(content)

            full_messages.append({"role": role, "content": content})

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": full_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
        }

        if tools:
            payload["tools"] = self._convert_tools(tools)

        return payload

    def _convert_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert Aureon tool defs to OpenAI function-calling format."""
        converted = []
        for t in tools:
            converted.append({
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("input_schema", {"type": "object", "properties": {}}),
                },
            })
        return converted

    def prompt(
        self,
        messages: List[Dict[str, Any]],
        system: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> LLMResponse:
        if not self._session:
            return LLMResponse(text="[ERROR] requests library not available", stop_reason="error")

        payload = self._build_payload(messages, system, tools, max_tokens, temperature)
        url = f"{self.base_url}/chat/completions"

        try:
            resp = self._session.post(url, json=payload, headers=self._headers(), timeout=120)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error("Local LLM request failed: %s", e)
            return LLMResponse(text=f"[ERROR] {e}", stop_reason="error")

        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})

        tool_calls = []
        for tc in message.get("tool_calls", []):
            func = tc.get("function", {})
            args = func.get("arguments", "{}")
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {"raw": args}
            tool_calls.append(ToolCall(
                id=tc.get("id", str(uuid.uuid4())),
                name=func.get("name", ""),
                arguments=args,
            ))

        stop_reason = "tool_use" if tool_calls else "end_turn"
        if choice.get("finish_reason") == "length":
            stop_reason = "max_tokens"

        return LLMResponse(
            text=message.get("content", "") or "",
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            usage=data.get("usage", {}),
            model=data.get("model", self.model),
            raw=data,
        )

    def stream(
        self,
        messages: List[Dict[str, Any]],
        system: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> Generator[StreamChunk, None, None]:
        if not self._session:
            yield StreamChunk(text="[ERROR] requests library not available", done=True)
            return

        payload = self._build_payload(messages, system, tools, max_tokens, temperature, stream=True)
        url = f"{self.base_url}/chat/completions"

        try:
            resp = self._session.post(
                url, json=payload, headers=self._headers(), stream=True, timeout=300
            )
            resp.raise_for_status()
        except Exception as e:
            logger.error("Local LLM stream failed: %s", e)
            yield StreamChunk(text=f"[ERROR] {e}", done=True)
            return

        pending_tool: Optional[Dict[str, Any]] = None

        for line in resp.iter_lines():
            if not line:
                continue
            decoded = line.decode("utf-8", errors="replace").strip()
            if not decoded.startswith("data: "):
                continue
            data_str = decoded[6:]
            if data_str == "[DONE]":
                if pending_tool:
                    args_str = pending_tool.get("arguments_buffer", "")
                    try:
                        args = json.loads(args_str)
                    except json.JSONDecodeError:
                        args = {"raw": args_str}
                    yield StreamChunk(
                        tool_call=ToolCall(
                            id=pending_tool.get("id", str(uuid.uuid4())),
                            name=pending_tool.get("name", ""),
                            arguments=args,
                        ),
                        done=False,
                    )
                yield StreamChunk(done=True, stop_reason="end_turn")
                return

            try:
                chunk_data = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            delta = chunk_data.get("choices", [{}])[0].get("delta", {})
            finish = chunk_data.get("choices", [{}])[0].get("finish_reason")

            # Handle tool call deltas
            if delta.get("tool_calls"):
                tc_delta = delta["tool_calls"][0]
                if tc_delta.get("function", {}).get("name"):
                    if pending_tool:
                        args_str = pending_tool.get("arguments_buffer", "")
                        try:
                            args = json.loads(args_str)
                        except json.JSONDecodeError:
                            args = {"raw": args_str}
                        yield StreamChunk(
                            tool_call=ToolCall(
                                id=pending_tool.get("id", str(uuid.uuid4())),
                                name=pending_tool.get("name", ""),
                                arguments=args,
                            ),
                        )
                    pending_tool = {
                        "id": tc_delta.get("id", str(uuid.uuid4())),
                        "name": tc_delta["function"]["name"],
                        "arguments_buffer": tc_delta.get("function", {}).get("arguments", ""),
                    }
                elif pending_tool:
                    pending_tool["arguments_buffer"] += tc_delta.get("function", {}).get("arguments", "")
                continue

            content = delta.get("content", "")
            if content:
                yield StreamChunk(text=content)

            if finish:
                if pending_tool:
                    args_str = pending_tool.get("arguments_buffer", "")
                    try:
                        args = json.loads(args_str)
                    except json.JSONDecodeError:
                        args = {"raw": args_str}
                    yield StreamChunk(
                        tool_call=ToolCall(
                            id=pending_tool.get("id", str(uuid.uuid4())),
                            name=pending_tool.get("name", ""),
                            arguments=args,
                        ),
                    )
                yield StreamChunk(done=True, stop_reason=finish)
                return

    def health_check(self) -> bool:
        if not self._session:
            return False
        try:
            resp = self._session.get(f"{self.base_url}/models", headers=self._headers(), timeout=5)
            return resp.status_code == 200
        except Exception:
            return False


# ─────────────────────────────────────────────────────────────────────────────
# AureonBrainAdapter — use existing AureonBrain as reasoning engine
# ─────────────────────────────────────────────────────────────────────────────


class AureonBrainAdapter(LLMAdapter):
    """
    Uses the existing AureonBrain intelligence layer as a reasoning backend.

    Instead of an external LLM, this adapter:
      1. Parses the user message to extract intent (symbol, action, context)
      2. Runs AureonBrain.decide() with market data
      3. Formats the Brain's BrainDecision as an LLM-like response

    This is the fully in-house, zero-external-dependency reasoning path.
    """

    def __init__(self):
        self._brain = None
        self._brain_loaded = False
        self._load_brain()

    def _load_brain(self):
        try:
            from aureon.intelligence.aureon_brain import AureonBrain
            self._brain = AureonBrain()
            self._brain_loaded = True
            logger.info("AureonBrain loaded as reasoning backend")
        except Exception as e:
            logger.warning("AureonBrain not available: %s — falling back to rule engine", e)
            self._brain_loaded = False

    def _extract_context(self, messages: List[Dict[str, Any]], system: str) -> Dict[str, Any]:
        """Extract actionable context from conversation messages."""
        context: Dict[str, Any] = {"system": system, "query": "", "symbols": [], "action": None}

        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, list):
                    parts = []
                    for c in content:
                        if isinstance(c, dict) and c.get("type") == "text":
                            parts.append(c["text"])
                        elif isinstance(c, str):
                            parts.append(c)
                    content = " ".join(parts)
                context["query"] = str(content)

        # Extract symbols mentioned
        text = context["query"].upper()
        common_symbols = [
            "BTCUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT", "ADAUSDT",
            "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT", "LINKUSDT",
        ]
        for sym in common_symbols:
            if sym in text or sym.replace("USDT", "") in text:
                context["symbols"].append(sym)

        # Detect action intent
        lower = context["query"].lower()
        if any(w in lower for w in ["buy", "long", "enter", "open"]):
            context["action"] = "BUY"
        elif any(w in lower for w in ["sell", "short", "exit", "close"]):
            context["action"] = "SELL"
        elif any(w in lower for w in ["analyse", "analyze", "signal", "status", "check"]):
            context["action"] = "ANALYSE"

        return context

    def _brain_reason(self, context: Dict[str, Any]) -> str:
        """Use AureonBrain to generate a reasoning response."""
        if not self._brain_loaded or not self._brain:
            return self._rule_engine_reason(context)

        try:
            # Build features dict for brain
            features = {
                "query": context.get("query", ""),
                "symbols": context.get("symbols", []),
                "action": context.get("action"),
                "timestamp": time.time(),
            }

            # If brain has a decide method, use it
            if hasattr(self._brain, "decide"):
                decision = self._brain.decide(features)
                if decision and hasattr(decision, "__dict__"):
                    return json.dumps({
                        "signal": getattr(decision, "signal", "NEUTRAL"),
                        "confidence": getattr(decision, "confidence", 0.5),
                        "coherence": getattr(decision, "coherence", 0.5),
                        "reasoning": getattr(decision, "reasoning", str(decision)),
                        "source": "AureonBrain",
                    }, indent=2)
                return str(decision)

            # Fallback to any available method
            if hasattr(self._brain, "analyse"):
                return str(self._brain.analyse(features))
            if hasattr(self._brain, "predict"):
                return str(self._brain.predict(features))

        except Exception as e:
            logger.warning("AureonBrain reasoning failed: %s", e)

        return self._rule_engine_reason(context)

    def _rule_engine_reason(self, context: Dict[str, Any]) -> str:
        """Deterministic rule-based reasoning when Brain is unavailable."""
        query = context.get("query", "")
        action = context.get("action", "ANALYSE")
        symbols = context.get("symbols", [])

        response_parts = []
        response_parts.append(f"Aureon In-House Analysis — {time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        response_parts.append(f"Query: {query}")

        if symbols:
            response_parts.append(f"Symbols detected: {', '.join(symbols)}")

        if action == "BUY":
            response_parts.append(
                "Signal: NEUTRAL — Requires live market data + coherence gate (Gamma > 0.945) "
                "before confirming BUY. Run through full pillar consensus."
            )
        elif action == "SELL":
            response_parts.append(
                "Signal: NEUTRAL — SELL signals require Auris 9-node consensus. "
                "Check stop-loss levels and current position state."
            )
        else:
            response_parts.append(
                "Signal: NEUTRAL — System is in analysis mode. "
                "All 6 pillar agents should be consulted for a full signal."
            )

        return "\n".join(response_parts)

    def prompt(
        self,
        messages: List[Dict[str, Any]],
        system: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> LLMResponse:
        context = self._extract_context(messages, system)
        response_text = self._brain_reason(context)

        # If tools are available and action is detected, generate tool calls
        tool_calls = []
        if tools and context.get("action"):
            for tool in tools:
                tool_name = tool.get("name", "")
                # Auto-invoke relevant tools based on context
                if context["action"] == "ANALYSE" and "read" in tool_name.lower():
                    tool_calls.append(ToolCall(
                        name=tool_name,
                        arguments=self._auto_tool_args(tool, context),
                    ))
                    break
                if context["action"] in ("BUY", "SELL") and "position" in tool_name.lower():
                    tool_calls.append(ToolCall(
                        name=tool_name,
                        arguments=self._auto_tool_args(tool, context),
                    ))
                    break

        return LLMResponse(
            text=response_text,
            tool_calls=tool_calls,
            stop_reason="tool_use" if tool_calls else "end_turn",
            model="aureon-brain-v1",
        )

    def _auto_tool_args(self, tool: Dict, context: Dict) -> Dict[str, Any]:
        """Generate sensible default arguments for a tool."""
        schema = tool.get("input_schema", {})
        props = schema.get("properties", {})
        args = {}
        for key, prop in props.items():
            ptype = prop.get("type", "string")
            if ptype == "string":
                if "symbol" in key.lower():
                    args[key] = context.get("symbols", ["BTCUSDT"])[0] if context.get("symbols") else "all"
                elif "exchange" in key.lower():
                    args[key] = "all"
                elif "format" in key.lower():
                    args[key] = "json"
                else:
                    args[key] = "default"
            elif ptype == "integer":
                args[key] = 10
            elif ptype == "number":
                args[key] = 0.945
            elif ptype == "boolean":
                args[key] = True
        return args

    def stream(
        self,
        messages: List[Dict[str, Any]],
        system: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> Generator[StreamChunk, None, None]:
        # Brain responses are fast — simulate streaming by chunking the response
        response = self.prompt(messages, system, tools, max_tokens, temperature, **kwargs)

        # Stream tool calls first
        for tc in response.tool_calls:
            yield StreamChunk(tool_call=tc)

        # Stream text in word-sized chunks
        words = response.text.split(" ")
        for i, word in enumerate(words):
            suffix = " " if i < len(words) - 1 else ""
            yield StreamChunk(text=word + suffix)

        yield StreamChunk(done=True, stop_reason=response.stop_reason)

    def health_check(self) -> bool:
        return self._brain_loaded


# ─────────────────────────────────────────────────────────────────────────────
# AureonHybridAdapter — local LLM + AureonBrain combined
# ─────────────────────────────────────────────────────────────────────────────


class AureonHybridAdapter(LLMAdapter):
    """
    Chains AureonLocalAdapter (for language generation) with AureonBrainAdapter
    (for market-specific reasoning). The Brain enriches the system prompt with
    live intelligence before the local LLM generates the final response.

    Fallback chain:
      1. Try local LLM with Brain-enriched context
      2. If local LLM is down → fall back to Brain-only
      3. If Brain is down → fall back to local LLM alone
      4. If both are down → rule engine
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.local = AureonLocalAdapter(base_url=base_url, model=model, api_key=api_key)
        self.brain = AureonBrainAdapter()

    def _enrich_system(self, system: str, messages: List[Dict[str, Any]]) -> str:
        """Prepend Brain intelligence to the system prompt."""
        if not self.brain.health_check():
            return system

        context = self.brain._extract_context(messages, system)
        brain_intel = self.brain._brain_reason(context)

        enriched = (
            f"{system}\n\n"
            f"── AUREON BRAIN INTELLIGENCE ──\n"
            f"{brain_intel}\n"
            f"── END BRAIN INTELLIGENCE ──"
        )
        return enriched

    def prompt(
        self,
        messages: List[Dict[str, Any]],
        system: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> LLMResponse:
        enriched_system = self._enrich_system(system, messages)

        # Try local LLM first
        if self.local.health_check():
            response = self.local.prompt(
                messages, enriched_system, tools, max_tokens, temperature, **kwargs
            )
            if response.stop_reason != "error":
                return response

        # Fallback to brain-only
        logger.info("Local LLM unavailable — falling back to AureonBrain")
        return self.brain.prompt(messages, system, tools, max_tokens, temperature, **kwargs)

    def stream(
        self,
        messages: List[Dict[str, Any]],
        system: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> Generator[StreamChunk, None, None]:
        enriched_system = self._enrich_system(system, messages)

        if self.local.health_check():
            yield from self.local.stream(
                messages, enriched_system, tools, max_tokens, temperature, **kwargs
            )
        else:
            yield from self.brain.stream(
                messages, system, tools, max_tokens, temperature, **kwargs
            )

    def health_check(self) -> bool:
        return self.local.health_check() or self.brain.health_check()
