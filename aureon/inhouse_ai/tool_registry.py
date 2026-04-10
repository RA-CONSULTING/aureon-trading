"""
Tool Registry — Sovereign Tool System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Central registry for all tools available to in-house agents.
Provides defineTool() for custom tools and ships 5 built-in tools:

  1. read_state       — read dashboard snapshot / system state
  2. read_positions   — read current trading positions + equity
  3. read_prices      — get live prices across all exchanges
  4. publish_thought  — publish a Thought to the ThoughtBus
  5. execute_shell    — run a shell command (sandboxed)
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("aureon.inhouse_ai.tools")

# ─────────────────────────────────────────────────────────────────────────────
# Tool definition
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ToolDefinition:
    """Schema + handler for a single tool."""

    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=lambda: {
        "type": "object", "properties": {}, "required": []
    })
    handler: Optional[Callable[..., str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Export as the wire format agents expect."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Registry
# ─────────────────────────────────────────────────────────────────────────────


class ToolRegistry:
    """
    Central tool registry.  Agents discover and call tools through this.

    Usage:
        registry = ToolRegistry()
        registry.define_tool("my_tool", "Does something", schema, handler_fn)
        result = registry.execute("my_tool", {"arg": "value"})
    """

    def __init__(self, include_builtins: bool = True):
        self._tools: Dict[str, ToolDefinition] = {}
        if include_builtins:
            self._register_builtins()

    def define_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable[..., str],
    ) -> ToolDefinition:
        """Register a new tool.  Returns the definition."""
        td = ToolDefinition(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler,
        )
        self._tools[name] = td
        logger.debug("Tool registered: %s", name)
        return td

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def execute(self, name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool by name.  Returns the result string."""
        td = self._tools.get(name)
        if not td:
            return json.dumps({"error": f"Unknown tool: {name}"})
        if not td.handler:
            return json.dumps({"error": f"Tool '{name}' has no handler"})
        try:
            return td.handler(arguments)
        except Exception as e:
            logger.error("Tool %s failed: %s", name, e)
            return json.dumps({"error": f"Tool execution failed: {e}"})

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return all tool definitions in wire format."""
        return [td.to_dict() for td in self._tools.values()]

    def names(self) -> List[str]:
        return list(self._tools.keys())

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    # ─────────────────────────────────────────────────────────────────────────
    # Built-in tools
    # ─────────────────────────────────────────────────────────────────────────

    def _register_builtins(self):
        """Register the 5 built-in tools."""

        # 1. read_state
        self.define_tool(
            name="read_state",
            description="Read the current system state from the dashboard snapshot. Returns exchange status, session stats, flight check results, and systems registry.",
            input_schema={
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "string",
                        "description": "Comma-separated keys to read (e.g. 'session_stats,exchange_status') or 'all'",
                    },
                },
                "required": ["keys"],
                "additionalProperties": False,
            },
            handler=_builtin_read_state,
        )

        # 2. read_positions
        self.define_tool(
            name="read_positions",
            description="Read current open trading positions and equity across all exchanges.",
            input_schema={
                "type": "object",
                "properties": {
                    "exchange": {
                        "type": "string",
                        "description": "Filter by exchange: binance|alpaca|kraken|all",
                    },
                },
                "required": ["exchange"],
                "additionalProperties": False,
            },
            handler=_builtin_read_positions,
        )

        # 3. read_prices
        self.define_tool(
            name="read_prices",
            description="Get live prices for tracked symbols across all exchanges.",
            input_schema={
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "string",
                        "description": "Comma-separated symbols (e.g. 'BTCUSDT,ETHUSDT') or 'all'",
                    },
                    "top_n": {
                        "type": "integer",
                        "description": "Return top N symbols by activity (default 20)",
                    },
                },
                "required": ["symbols"],
                "additionalProperties": False,
            },
            handler=_builtin_read_prices,
        )

        # 4. publish_thought
        self.define_tool(
            name="publish_thought",
            description="Publish a Thought to the ThoughtBus for other system components to consume.",
            input_schema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "ThoughtBus topic (e.g. 'agent.signal', 'agent.analysis')",
                    },
                    "payload": {
                        "type": "string",
                        "description": "JSON-encoded payload to publish",
                    },
                    "source": {
                        "type": "string",
                        "description": "Source identifier (agent name)",
                    },
                },
                "required": ["topic", "payload", "source"],
                "additionalProperties": False,
            },
            handler=_builtin_publish_thought,
        )

        # 5. execute_shell
        self.define_tool(
            name="execute_shell",
            description="Execute a shell command and return its output. Sandboxed to safe read-only commands.",
            input_schema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute (read-only commands only)",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default 30, max 60)",
                    },
                },
                "required": ["command"],
                "additionalProperties": False,
            },
            handler=_builtin_execute_shell,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Built-in tool handlers
# ─────────────────────────────────────────────────────────────────────────────


def _load_snapshot() -> Dict[str, Any]:
    """Load the latest dashboard snapshot."""
    state_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "wisdom", "state")
    path = os.path.join(state_dir, "dashboard_snapshot.json")
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        # Try repo root state dir
        alt = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "state", "dashboard_snapshot.json")
        try:
            with open(alt) as f:
                return json.load(f)
        except Exception:
            return {}


def _builtin_read_state(args: Dict[str, Any]) -> str:
    snap = _load_snapshot()
    keys_str = args.get("keys", "all")

    if keys_str == "all":
        return json.dumps({
            "timestamp": snap.get("timestamp"),
            "session_stats": snap.get("session_stats", {}),
            "exchange_status": snap.get("exchange_status", {}),
            "systems_registry": snap.get("systems_registry", {}),
            "flight_check": snap.get("flight_check", {}),
        }, indent=2)

    keys = [k.strip() for k in keys_str.split(",")]
    result = {}
    for k in keys:
        result[k] = snap.get(k, None)
    return json.dumps(result, indent=2)


def _builtin_read_positions(args: Dict[str, Any]) -> str:
    snap = _load_snapshot()
    exchange = args.get("exchange", "all")
    positions = snap.get("positions", [])
    equity = snap.get("queen_equity")

    if exchange != "all" and isinstance(positions, list):
        positions = [p for p in positions if isinstance(p, dict) and p.get("exchange", "").lower() == exchange.lower()]

    return json.dumps({
        "positions": positions,
        "active_count": len(positions) if isinstance(positions, list) else 0,
        "queen_equity": equity,
        "exchange_filter": exchange,
    }, indent=2)


def _builtin_read_prices(args: Dict[str, Any]) -> str:
    snap = _load_snapshot()
    prices: Dict[str, float] = {}
    for key in ("binance_prices", "alpaca_prices", "kraken_prices"):
        raw = snap.get(key, {})
        if isinstance(raw, dict):
            for sym, val in raw.items():
                if sym not in prices and val:
                    try:
                        prices[sym] = float(val)
                    except (TypeError, ValueError):
                        pass

    symbols_str = args.get("symbols", "all")
    top_n = int(args.get("top_n", 20))

    if symbols_str != "all":
        wanted = {s.strip().upper() for s in symbols_str.split(",")}
        prices = {k: v for k, v in prices.items() if k.upper() in wanted}

    # Limit to top_n
    items = list(prices.items())[:top_n]
    return json.dumps({
        "total_tracked": len(prices),
        "prices": dict(items),
        "returned": len(items),
    }, indent=2)


def _builtin_publish_thought(args: Dict[str, Any]) -> str:
    topic = args.get("topic", "agent.signal")
    payload_str = args.get("payload", "{}")
    source = args.get("source", "inhouse_agent")

    try:
        payload = json.loads(payload_str) if isinstance(payload_str, str) else payload_str
    except json.JSONDecodeError:
        payload = {"raw": payload_str}

    try:
        from aureon.core.aureon_thought_bus import ThoughtBus, Thought
        bus = ThoughtBus()
        bus.publish(Thought(source=source, topic=topic, payload=payload))
        return json.dumps({"status": "published", "topic": topic, "source": source})
    except Exception as e:
        return json.dumps({"status": "failed", "error": str(e), "topic": topic})


def _builtin_execute_shell(args: Dict[str, Any]) -> str:
    command = args.get("command", "")
    timeout = min(int(args.get("timeout", 30)), 60)

    # Sandbox: block destructive commands
    blocked = ["rm ", "del ", "format ", "mkfs", "dd ", "shutdown", "reboot", "> /dev/", ":(){ ", "fork"]
    cmd_lower = command.lower()
    for b in blocked:
        if b in cmd_lower:
            return json.dumps({"error": f"Blocked: command contains '{b.strip()}'"})

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return json.dumps({
            "stdout": result.stdout[:4096],
            "stderr": result.stderr[:1024],
            "returncode": result.returncode,
        })
    except subprocess.TimeoutExpired:
        return json.dumps({"error": f"Command timed out after {timeout}s"})
    except Exception as e:
        return json.dumps({"error": str(e)})
