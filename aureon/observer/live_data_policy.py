"""Centralised gate for simulation / fallback data paths in production.

The system has historically had a number of "fall back to simulated
data when the live source fails" code paths — Schumann resonance
bridge, space-weather bridge, market-data fetchers, etc. Those
fallbacks were silent: a consumer reading the data structure couldn't
tell whether the values were live or synthetic. In production trading,
that's the wrong behaviour — we want loud failure when live data is
unavailable so we don't trade on stale fixtures.

This module exposes a single env-controlled gate:

    simulation_fallback_allowed() -> bool

When the env var is unset OR set to a falsy value, the gate returns
False — production posture. Live data sources should raise / return
None when their fetch fails rather than substituting synthetic values.

When the env var is set to a truthy value, the gate returns True —
dev / test / backtest posture. Existing simulation paths fire as
before.

Why a separate module rather than inlining ``os.environ.get`` at each
site: every fallback path needs the same gate, and bundling them
gives us one place to change the policy + one place to add an audit
log of every time a fallback would have fired.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

ENV_ALLOW_SIM_FALLBACK = "AUREON_ALLOW_SIM_FALLBACK"
_TRUTHY = ("1", "true", "yes", "on", "y", "t")


def simulation_fallback_allowed() -> bool:
    """True iff AUREON_ALLOW_SIM_FALLBACK is set truthy. Default False.

    Production deployments leave this unset → no simulation fallback
    fires → live data sources fail loudly when unavailable. Dev /
    backtest / unit-test deployments can set ``AUREON_ALLOW_SIM_FALLBACK=1``
    to restore the old simulation-on-failure behaviour.
    """
    raw = os.environ.get(ENV_ALLOW_SIM_FALLBACK, "").strip().lower()
    return raw in _TRUTHY


def log_blocked_fallback(source: str, reason: str = "live_unavailable") -> None:
    """Emit a structured log when a simulation fallback was blocked.

    Surfaces in operator logs as a clear "live data missing" event
    rather than silently degrading. Optional — callers can call this
    before returning None / raising to make the failure auditable.
    """
    logger.warning(
        "[live-data] %s fallback BLOCKED (env=%s=off) — reason=%s",
        source, ENV_ALLOW_SIM_FALLBACK, reason,
    )


def fallback_marker(source: str, when: Optional[float] = None) -> dict:
    """Return a small audit dict for tagging a reading as fallback-derived.

    Modules that DO honour the simulation fallback (because the env
    var is set, or because the fallback is meaningfully different
    from raw fakery — e.g. cached data with a known TTL) can attach
    this marker to their reading so downstream consumers can detect.
    """
    return {
        "source": source,
        "is_live": False,
        "fallback_used_at": float(when) if when is not None else time.time(),
    }
