#!/usr/bin/env python3
"""
Bridge repo exploration findings into local task queue and safe code proposals.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from aureon.autonomous.aureon_local_task_queue import LocalTask, LocalTaskQueue, build_default_task_queue
from aureon.autonomous.aureon_repo_explorer_service import RepoExplorerService, build_default_repo_explorer
from aureon.autonomous.aureon_safe_code_control import CodeProposal, SafeCodeControl, build_default_code_controller


DEFAULT_STATE_PATH = Path("state/repo_task_bridge_state.json")


class RepoTaskBridge:
    def __init__(
        self,
        explorer: Optional[RepoExplorerService] = None,
        task_queue: Optional[LocalTaskQueue] = None,
        code_control: Optional[SafeCodeControl] = None,
        state_path: Optional[Path] = None,
    ) -> None:
        self.explorer = explorer or build_default_repo_explorer()
        self.task_queue = task_queue or build_default_task_queue()
        self.code_control = code_control or build_default_code_controller()
        self.state_path = Path(state_path or DEFAULT_STATE_PATH)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.last_run = 0.0
        self._persist()

    def generate_repo_suggestions(self, limit: int = 10) -> Dict[str, int]:
        suggestions = self.explorer.suggest_tasks(limit=limit)
        task_count = 0
        proposal_count = 0
        for item in suggestions:
            self.task_queue.enqueue(LocalTask(
                title=str(item.get("title") or "Repo task"),
                message=str(item.get("summary") or ""),
                target_files=list(item.get("target_files") or []),
                source=str(item.get("source") or "repo_explorer"),
                kind="suggestion",
            ))
            task_count += 1
            self.code_control.propose(CodeProposal(
                kind="code_task",
                title=str(item.get("title") or "Repo task"),
                summary=str(item.get("summary") or ""),
                target_files=list(item.get("target_files") or []),
                source="repo_task_bridge",
            ))
            proposal_count += 1
        self.last_run = __import__("time").time()
        self._persist()
        return {"tasks_added": task_count, "proposals_added": proposal_count}

    def status(self) -> Dict[str, object]:
        return {
            "last_run": self.last_run,
            "task_queue": self.task_queue.status(),
            "code_control": self.code_control.status(),
        }

    def _persist(self) -> None:
        self.state_path.write_text(json.dumps(self.status(), indent=2), encoding="utf-8")


def build_default_repo_task_bridge() -> RepoTaskBridge:
    return RepoTaskBridge()


if __name__ == "__main__":
    bridge = build_default_repo_task_bridge()
    print(json.dumps(bridge.generate_repo_suggestions(limit=5), indent=2))
