"""
aureon_phi_calendar.py — The organism's sense of time.

HNC staging of consciousness: the organism is not one clock, it is many
nested clocks ticking at φ-ratio intervals. Short bands handle reactive
work (drift correction, quick scans). Long bands handle strategic work
(day-level planning, week-level retrospectives). Together they give the
big picture — the wheel of existence — and let the organism know which
band is the right one to work in right now.

Bands (each publishes `calendar.tick.<band>` on its own cadence):

    pulse   ~  1.0 s       reactive   — single heartbeat
    breath  ~  φ   s       reactive   — one inhale
    beat    ~  φ²  s       reactive
    phrase  ~  φ³  s       tactical
    passage ~  φ⁵  s       tactical   — short phrase of thought
    cadence ~  φ⁷  s (~29s) cognitive — one coherent sequence
    minor   ~  φ⁹  s (~76s) cognitive
    major   ~  φ¹¹ s (~3m)  strategic — one deliberation arc
    hour    ~  1 h          strategic
    day     ~  24 h         developmental
    week    ~  7 d          developmental — retrospective window
    moon    ~  28 d         evolutionary
    season  ~  91 d         evolutionary

Per-band subscribers can register via `on(band, fn)`. Per-band state
includes: last_fired_at, count, latest_events (bounded ring). A single
`snapshot()` call returns current position across all bands — the
organism's big-picture view.

The calendar runs one background thread. Every ~1s it walks the bands
and fires any whose boundary was crossed. Bands are daemon by default.
"""

from __future__ import annotations

import json
import logging
import math
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple

logger = logging.getLogger("aureon.core.phi_calendar")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CALENDAR_LOG = _REPO_ROOT / "state" / "phi_calendar_log.jsonl"

PHI = (1.0 + math.sqrt(5.0)) / 2.0

# φⁿ from 0..11, then absolute durations for day-scale and up.
BAND_SECONDS: Dict[str, float] = {
    "pulse":   1.0,
    "breath":  PHI,                  # 1.618 s
    "beat":    PHI ** 2,             # 2.618 s
    "phrase":  PHI ** 3,             # 4.236 s
    "passage": PHI ** 5,             # 11.09 s
    "cadence": PHI ** 7,             # 29.03 s
    "minor":   PHI ** 9,             # 76.01 s
    "major":   PHI ** 11,            # 199.01 s (~3m 19s)
    "hour":    3600.0,
    "day":     86400.0,
    "week":    7.0 * 86400.0,
    "moon":    28.0 * 86400.0,
    "season":  91.0 * 86400.0,
}

BAND_STAGE: Dict[str, str] = {
    "pulse":   "reactive",
    "breath":  "reactive",
    "beat":    "reactive",
    "phrase":  "tactical",
    "passage": "tactical",
    "cadence": "cognitive",
    "minor":   "cognitive",
    "major":   "strategic",
    "hour":    "strategic",
    "day":     "developmental",
    "week":    "developmental",
    "moon":    "evolutionary",
    "season":  "evolutionary",
}


@dataclass
class BandState:
    name: str
    period_s: float
    stage: str
    started_at: float
    last_fired_at: float = 0.0
    count: int = 0
    events: Deque[Dict[str, Any]] = field(default_factory=lambda: deque(maxlen=16))
    subscribers: List[Callable[[str, Dict[str, Any]], None]] = field(default_factory=list)


class PhiCalendar:
    """
    Nested phi-ratio time bands. The organism's multi-scale clock.
    """

    def __init__(self) -> None:
        self.bus: Any = None
        self.bands: Dict[str, BandState] = {}
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        now = time.time()
        for name, period in BAND_SECONDS.items():
            self.bands[name] = BandState(
                name=name,
                period_s=float(period),
                stage=BAND_STAGE.get(name, "reactive"),
                started_at=now,
                last_fired_at=0.0,
            )

    # ------------------------------------------------------------------
    # Wiring
    # ------------------------------------------------------------------
    def _wire_bus(self) -> None:
        if self.bus is not None:
            return
        try:
            from aureon.core.aureon_thought_bus import get_thought_bus
            self.bus = get_thought_bus()
        except Exception as e:
            logger.debug("bus unavailable: %s", e)

    def on(self, band: str, fn: Callable[[str, Dict[str, Any]], None]) -> None:
        """Register a callback fired when `band` ticks. fn(band, event_dict)."""
        b = self.bands.get(band)
        if b is None:
            raise ValueError(f"unknown band {band}; choose from {list(self.bands)}")
        with self._lock:
            b.subscribers.append(fn)

    # ------------------------------------------------------------------
    # Fire loop
    # ------------------------------------------------------------------
    def start(self) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._wire_bus()
            self._stop.clear()
            self._thread = threading.Thread(
                target=self._run,
                name="aureon-phi-calendar",
                daemon=True,
            )
            self._thread.start()
            logger.info("phi calendar: started (%d bands)", len(self.bands))

    def stop(self, timeout: float = 3.0) -> None:
        with self._lock:
            self._stop.set()
            t = self._thread
        if t is not None:
            t.join(timeout=timeout)

    def is_alive(self) -> bool:
        t = self._thread
        return bool(t is not None and t.is_alive())

    def _run(self) -> None:
        # Base sleep = half the shortest band, so we never miss a pulse.
        base = max(0.25, min(b.period_s for b in self.bands.values()) / 2.0)
        while not self._stop.is_set():
            now = time.time()
            for b in self.bands.values():
                # Fire if at least one full period has elapsed since the
                # last fire (or since start, for the very first fire).
                ref = b.last_fired_at or b.started_at
                if now - ref >= b.period_s:
                    self._fire(b, now)
            self._stop.wait(base)

    def _fire(self, band: BandState, now: float) -> None:
        band.count += 1
        band.last_fired_at = now
        event = {
            "band": band.name,
            "stage": band.stage,
            "period_s": band.period_s,
            "count": band.count,
            "fired_at": now,
        }
        band.events.append(event)

        # Fan out.
        if self.bus is not None:
            try:
                self.bus.publish(f"calendar.tick.{band.name}", event, source="phi_calendar")
            except Exception:
                pass
        for fn in list(band.subscribers):
            try:
                fn(band.name, event)
            except Exception as e:
                logger.debug("subscriber %s failed on %s: %s", fn, band.name, e)

        # Persist long-band ticks only (pulse/breath/beat happen too
        # often to justify disk). Everything cadence+ goes to the log.
        if band.period_s >= BAND_SECONDS["cadence"] - 0.01:
            try:
                _CALENDAR_LOG.parent.mkdir(parents=True, exist_ok=True)
                with _CALENDAR_LOG.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(event, default=str) + "\n")
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Snapshot — big picture
    # ------------------------------------------------------------------
    def snapshot(self) -> Dict[str, Any]:
        now = time.time()
        rows: List[Dict[str, Any]] = []
        for b in self.bands.values():
            ref = b.last_fired_at or b.started_at
            next_in = max(0.0, b.period_s - (now - ref))
            last_ago = (now - b.last_fired_at) if b.last_fired_at else None
            rows.append({
                "band": b.name,
                "stage": b.stage,
                "period_s": b.period_s,
                "count": b.count,
                "last_fired_ago_s": last_ago,
                "next_in_s": next_in,
            })
        return {
            "taken_at": now,
            "bands": rows,
        }

    def recent(self, band: str, limit: int = 8) -> List[Dict[str, Any]]:
        b = self.bands.get(band)
        if b is None:
            return []
        events = list(b.events)[-limit:]
        return events


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────

_instance: Optional[PhiCalendar] = None
_instance_lock = threading.Lock()


def get_phi_calendar() -> PhiCalendar:
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = PhiCalendar()
        return _instance


def launch_phi_calendar() -> PhiCalendar:
    cal = get_phi_calendar()
    cal.start()
    return cal


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Aureon phi calendar.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_show = sub.add_parser("snapshot", help="Print the current big-picture snapshot")

    p_watch = sub.add_parser("watch", help="Run the calendar and print snapshots")
    p_watch.add_argument("--runtime-seconds", type=float, default=30.0)
    p_watch.add_argument("--snapshot-every", type=float, default=5.0)

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s :: %(message)s")

    if args.cmd == "snapshot":
        cal = get_phi_calendar()
        # Force one fire of every band that would be due now.
        cal._wire_bus()
        print(json.dumps(cal.snapshot(), indent=2, default=str))
    elif args.cmd == "watch":
        cal = launch_phi_calendar()
        t0 = time.time()
        try:
            while cal.is_alive():
                time.sleep(args.snapshot_every)
                print(json.dumps(cal.snapshot(), indent=2, default=str))
                if args.runtime_seconds and (time.time() - t0) >= args.runtime_seconds:
                    break
        except KeyboardInterrupt:
            pass
        finally:
            cal.stop()
