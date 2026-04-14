"""
RallyCoordinator — High-Frequency Burst Mode
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"High frequency rally system."

Normal operation: the feedback loop runs at the love+gratitude cadence
(typically 0.5–2 Hz). When the Auris consensus votes "RALLY" or the
Casimir drift force exceeds a threshold, the coordinator enters rally
mode for a bounded number of ticks, during which the clock runs 10×
faster.

Entering rally mode sets vault.rally_active = True, which the
LoveGratitudeClock reads and applies its 0.1× multiplier.

Exiting rally mode restores normal cadence.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger("aureon.vault.rally")


@dataclass
class RallyState:
    active: bool
    entered_at: Optional[float]
    ticks_remaining: int
    last_trigger_reason: str


class RallyCoordinator:
    """
    Decides when to enter and when to exit rally mode.

    Usage:
        rally = RallyCoordinator(burst_ticks=20, casimir_threshold=5.0)
        rally.update(vault, auris_result)
    """

    def __init__(
        self,
        burst_ticks: int = 20,
        casimir_threshold: float = 5.0,
    ):
        self.burst_ticks = int(burst_ticks)
        self.casimir_threshold = float(casimir_threshold)
        self._state: RallyState = RallyState(
            active=False,
            entered_at=None,
            ticks_remaining=0,
            last_trigger_reason="",
        )
        self._total_entries: int = 0
        self._total_exits: int = 0

    # ─────────────────────────────────────────────────────────────────────
    # Update
    # ─────────────────────────────────────────────────────────────────────

    def update(self, vault: Any, auris_result: Any = None) -> RallyState:
        """
        Check the vault + auris verdict and update rally state.
        Writes rally_active to vault so the clock can pick it up.
        """
        force = float(getattr(vault, "last_casimir_force", 0.0) or 0.0)
        consensus = "NEUTRAL"
        if auris_result is not None:
            consensus = str(getattr(auris_result, "consensus", "NEUTRAL") or "NEUTRAL")

        # Trigger conditions
        trigger = None
        if consensus == "RALLY":
            trigger = "auris-rally"
        elif force > self.casimir_threshold:
            trigger = f"casimir-spike({force:.2f})"

        if trigger and not self._state.active:
            self._enter(trigger)
        elif self._state.active:
            self._state.ticks_remaining -= 1
            if self._state.ticks_remaining <= 0:
                self._exit()
            elif trigger:
                # Refresh the burst window on continued pressure
                self._state.ticks_remaining = self.burst_ticks
                self._state.last_trigger_reason = trigger

        # Push state to the vault
        try:
            vault.rally_active = self._state.active
        except Exception:
            pass

        return self._state

    def _enter(self, reason: str) -> None:
        self._state.active = True
        self._state.entered_at = time.time()
        self._state.ticks_remaining = self.burst_ticks
        self._state.last_trigger_reason = reason
        self._total_entries += 1
        logger.debug("Rally ENTER: %s (ticks=%d)", reason, self.burst_ticks)

    def _exit(self) -> None:
        self._state.active = False
        self._state.entered_at = None
        self._state.ticks_remaining = 0
        self._total_exits += 1
        logger.debug("Rally EXIT")

    # ─────────────────────────────────────────────────────────────────────
    # Status
    # ─────────────────────────────────────────────────────────────────────

    @property
    def state(self) -> RallyState:
        return self._state

    @property
    def active(self) -> bool:
        return self._state.active

    def get_status(self) -> Dict[str, Any]:
        return {
            "active": self._state.active,
            "entered_at": self._state.entered_at,
            "ticks_remaining": self._state.ticks_remaining,
            "last_trigger_reason": self._state.last_trigger_reason,
            "total_entries": self._total_entries,
            "total_exits": self._total_exits,
            "burst_ticks": self.burst_ticks,
            "casimir_threshold": self.casimir_threshold,
        }
