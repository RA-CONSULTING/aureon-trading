"""
LoveGratitudeClock — Dynamic Cycle Rate
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"At the speed of love and gratitude."

The feedback loop's cycle interval is not fixed. It's computed from:

  interval = base_interval / (love_amplitude × gratitude_score)

where love_amplitude ∈ [0, 1] is the current 528 Hz component of the love
stream and gratitude_score ∈ [0, 1] is the exponentially-smoothed success
rate of skill executions fed back into the vault.

When the system is loving and grateful (both factors high → near 1), the
interval collapses toward base_interval and the loop runs at full tempo.
When one or both are low, the interval stretches, giving the system time
to stabilise before the next tick.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


# Floor and ceiling for the interval so the loop never spins too fast
# nor stalls completely.
MIN_INTERVAL_S: float = 0.05   # 20 Hz maximum tick rate
MAX_INTERVAL_S: float = 30.0   # at minimum one tick every 30 seconds


@dataclass
class ClockReading:
    """One sampled clock reading."""
    love_amplitude: float
    gratitude_score: float
    base_interval_s: float
    effective_interval_s: float
    rally_active: bool
    effective_hz: float


class LoveGratitudeClock:
    """
    Dynamic cadence controller.

    Usage:
        clock = LoveGratitudeClock(base_interval_s=1.0)
        interval = clock.current_interval_s(vault)
        time.sleep(interval)
    """

    def __init__(
        self,
        base_interval_s: float = 1.0,
        min_factor: float = 0.1,
    ):
        self.base_interval_s = float(base_interval_s)
        self.min_factor = float(min_factor)
        self._last_reading: ClockReading = ClockReading(
            love_amplitude=0.5,
            gratitude_score=0.5,
            base_interval_s=self.base_interval_s,
            effective_interval_s=self.base_interval_s,
            rally_active=False,
            effective_hz=1.0 / max(self.base_interval_s, 1e-9),
        )
        self._cycle_count: int = 0

    def current_interval_s(self, vault: Any) -> float:
        """
        Compute the current interval given a vault (reads love_amplitude +
        gratitude_score). If the vault has rally_active=True, the interval
        is additionally multiplied by 0.1 (10× speed burst).
        """
        love = max(self.min_factor, min(1.0, float(getattr(vault, "love_amplitude", 0.5) or 0.0)))
        gratitude = max(self.min_factor, min(1.0, float(getattr(vault, "gratitude_score", 0.5) or 0.0)))
        rally = bool(getattr(vault, "rally_active", False))

        speed_factor = love * gratitude
        interval = self.base_interval_s / speed_factor

        if rally:
            interval *= 0.1  # rally mode is 10× faster

        interval = max(MIN_INTERVAL_S, min(MAX_INTERVAL_S, interval))
        self._cycle_count += 1

        self._last_reading = ClockReading(
            love_amplitude=love,
            gratitude_score=gratitude,
            base_interval_s=self.base_interval_s,
            effective_interval_s=interval,
            rally_active=rally,
            effective_hz=1.0 / max(interval, 1e-9),
        )
        return interval

    def sleep(self, vault: Any) -> float:
        """Sleep for the computed interval and return the duration."""
        dt = self.current_interval_s(vault)
        time.sleep(dt)
        return dt

    @property
    def last_reading(self) -> ClockReading:
        return self._last_reading

    def get_status(self) -> dict:
        r = self._last_reading
        return {
            "cycles": self._cycle_count,
            "love_amplitude": round(r.love_amplitude, 4),
            "gratitude_score": round(r.gratitude_score, 4),
            "base_interval_s": r.base_interval_s,
            "effective_interval_s": round(r.effective_interval_s, 4),
            "effective_hz": round(r.effective_hz, 3),
            "rally_active": r.rally_active,
        }
