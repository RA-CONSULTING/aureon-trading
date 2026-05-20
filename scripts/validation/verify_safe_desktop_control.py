#!/usr/bin/env python3
"""Verify the constrained local desktop controller."""

from __future__ import annotations

import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from aureon.autonomous.aureon_safe_desktop_control import DesktopAction, build_default_controller
from aureon.autonomous.aureon_queen_desktop_bridge import build_default_bridge
from aureon.autonomous.aureon_safe_code_control import build_default_code_controller, CodeProposal
from aureon.autonomous.aureon_queen_code_bridge import build_default_code_bridge
from aureon.autonomous.aureon_repo_explorer_service import build_default_repo_explorer
from aureon.autonomous.aureon_local_task_queue import build_default_task_queue, LocalTask
from aureon.autonomous.aureon_repo_task_bridge import build_default_repo_task_bridge
from aureon.autonomous.aureon_voice_command_bridge import build_default_voice_bridge
from aureon.autonomous.aureon_conversation_loop import build_default_conversation_loop
from aureon.autonomous.aureon_voice_intent_cognition import build_default_voice_cognition
from aureon.autonomous.aureon_elephant_memory import build_default_elephant_memory


def main() -> int:
    ctl = build_default_controller(dry_run=True)
    ctl.arm()

    result = ctl.execute(DesktopAction(action="move_mouse", params={"x": 100, "y": 100}))
    payload = {
        "status": ctl.status(),
        "test_result": {
            "ok": result.ok,
            "action": result.action,
            "reason": result.reason,
            "dry_run": result.dry_run,
        },
        "bridge_status": build_default_bridge(dry_run=True).status(),
    }
    code_ctl = build_default_code_controller()
    code_ctl.propose(CodeProposal(kind="code_task", title="Example task", summary="Review bridge wiring", target_files=["aureon/autonomous/aureon_queen_code_bridge.py"]))
    payload["code_control_status"] = code_ctl.status()
    payload["code_bridge_status"] = build_default_code_bridge().status()
    explorer = build_default_repo_explorer()
    queue = build_default_task_queue()
    queue.enqueue(LocalTask(title="Example operator task", message="Review unified runner", target_files=["aureon/exchanges/unified_market_trader.py"]))
    bridge = build_default_repo_task_bridge()
    voice_bridge = build_default_voice_bridge()
    voice_bridge.submit_command("search ThoughtBus")
    voice_bridge.submit_command("suggest code add dashboard view for voice queue")
    payload["voice_cognition_status"] = build_default_voice_cognition().infer_intent("move mouse to 100, 120", source="verify")
    conversation = build_default_conversation_loop(speak_enabled=False)
    payload["conversation_status"] = conversation.handle_text("inspect aureon/autonomous/aureon_voice_command_bridge.py", source="verify")
    payload["elephant_memory_status"] = build_default_elephant_memory().status()
    payload["repo_explorer_status"] = {
        "sample_files": explorer.list_files(limit=10),
        "todo_hits": explorer.search_text("TODO", limit=5),
    }
    payload["task_queue_status"] = queue.status()
    payload["repo_task_bridge_status"] = bridge.status()
    payload["voice_bridge_status"] = voice_bridge.status()
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
