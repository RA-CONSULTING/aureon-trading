"""
_goal_claims — shared in-process registry of who is handling a goal.

The persona layer has two consumers of ``goal.submit.request``:

  1. GoalDispatchBridge — gates via conscience, hands off to the
     existing GoalExecutionEngine (AgentCore tools).
  2. GoalSkillAligner → SkillExecutorBridge — when a learned pattern
     exists, republishes ``goal.submit.request.aligned`` and runs the
     skill chain directly via CodeArchitect.

Without coordination both paths would fire for the same goal_id.
This registry lets either side "claim" a goal_id so the other can
skip. Claims are in-process only — mesh-remote claims don't propagate,
which is correct because both consumers run in the same process.

Subscription order is assumed: the aligner subscribes to
``goal.submit.request`` BEFORE GoalDispatchBridge does, so the aligner
runs first and (when a pattern matches) publishes
``goal.submit.request.aligned`` synchronously. The SkillExecutorBridge
claims the goal_id inside that inner publish, and GDB — running next
in the outer ``goal.submit.request`` handler list — sees the claim and
skips.

Gary Leckey · Aureon Institute — April 2026
"""

from __future__ import annotations

import threading
from typing import Dict, Optional


class GoalClaims:
    """Module-level singleton by intent. Thread-safe."""

    _lock = threading.Lock()
    _claimed: Dict[str, str] = {}

    @classmethod
    def claim(cls, goal_id: str, claimer: str) -> bool:
        """Return True when claim succeeds; False when already claimed."""
        if not goal_id:
            return False
        with cls._lock:
            if goal_id in cls._claimed:
                return False
            cls._claimed[goal_id] = claimer
            return True

    @classmethod
    def is_claimed(cls, goal_id: str) -> bool:
        if not goal_id:
            return False
        with cls._lock:
            return goal_id in cls._claimed

    @classmethod
    def who(cls, goal_id: str) -> Optional[str]:
        with cls._lock:
            return cls._claimed.get(goal_id)

    @classmethod
    def release(cls, goal_id: str) -> None:
        with cls._lock:
            cls._claimed.pop(goal_id, None)

    @classmethod
    def clear(cls) -> None:
        with cls._lock:
            cls._claimed.clear()


__all__ = ["GoalClaims"]
