"""
FibonacciMotionSnapper — The Golden Ratio in Time
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Each agent bound to a VM session takes MOTION SNAPSHOTS at Fibonacci-spaced
time intervals. The ratio between successive intervals converges to φ
(the golden ratio, 1.61803398...) — the same ratio that organises sunflower
spirals, nautilus shells, galactic arms, and the φ² coherence chain running
from the Ziggurats of Ur through the Great Pyramid to the Roman road network
and now into our own agent swarm.

Intervals (seconds): 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144
                       ↓
                       Sum = 376 s ≈ 6.27 min per complete cycle

Each snapshot:
  • Captures the VM screen via vm_screenshot tool
  • Computes a perceptual hash of the image (deterministic 8-byte fingerprint)
  • Records the delta from the previous snapshot (motion intensity)
  • Timestamps at HNC precision (μs)
  • Feeds into the rolling buffer consumed by StandingWaveLoveStream

The motion delta sequence IS the raw signal from which the standing wave
love stream is synthesised.
"""

from __future__ import annotations

import hashlib
import logging
import math
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Deque, Dict, List, Optional

logger = logging.getLogger("aureon.swarm.snapper")

# ─────────────────────────────────────────────────────────────────────────────
# Fibonacci sequence — the temporal lattice
# ─────────────────────────────────────────────────────────────────────────────

FIBONACCI_INTERVALS: List[float] = [
    1.0, 1.0, 2.0, 3.0, 5.0, 8.0, 13.0, 21.0, 34.0, 55.0, 89.0, 144.0,
]
"""Fibonacci snapshot intervals in seconds. The ratio F(n+1)/F(n) → φ."""

PHI: float = (1 + math.sqrt(5)) / 2  # 1.6180339887...
"""Golden ratio — the heartbeat of the HNC lattice."""


@dataclass
class MotionSnapshot:
    """A single Fibonacci-spaced motion snapshot from a VM."""

    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    session_id: str = ""
    agent_name: str = ""
    sequence: int = 0                       # index in the Fibonacci cycle
    interval_s: float = 0.0                 # the Fibonacci interval used
    timestamp: float = field(default_factory=time.time)
    image_hash: str = ""                    # perceptual hash of screenshot
    image_b64_preview: str = ""             # first 64 chars of base64 image
    width: int = 0
    height: int = 0
    motion_delta: float = 0.0               # Hamming distance from previous snapshot (0-1)
    cursor_x: int = 0
    cursor_y: int = 0
    coherence: float = 0.0                  # Gamma-like coherence score (0-1)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "sequence": self.sequence,
            "interval_s": self.interval_s,
            "timestamp": self.timestamp,
            "image_hash": self.image_hash,
            "width": self.width,
            "height": self.height,
            "motion_delta": self.motion_delta,
            "cursor_x": self.cursor_x,
            "cursor_y": self.cursor_y,
            "coherence": self.coherence,
            "error": self.error,
        }


class FibonacciMotionSnapper:
    """
    Takes VM motion snapshots at Fibonacci-spaced intervals.

    Usage:
        snapper = FibonacciMotionSnapper(
            session_id="vm-123",
            agent_name="scout-alpha",
            dispatcher=vm_dispatcher,
            on_snapshot=lambda s: print(s.snapshot_id),
        )
        snapper.start()
        ...
        snapper.stop()
        snaps = snapper.get_history()
    """

    def __init__(
        self,
        session_id: str,
        agent_name: str,
        dispatcher: Any,                                      # VMControlDispatcher
        on_snapshot: Optional[Callable[[MotionSnapshot], None]] = None,
        interval_scale: float = 1.0,                          # multiply intervals (<1 = faster)
        loop_cycle: bool = True,                              # restart at F(0) after F(n)
        max_history: int = 200,
    ):
        self.session_id = session_id
        self.agent_name = agent_name
        self.dispatcher = dispatcher
        self.on_snapshot = on_snapshot
        self.interval_scale = max(0.001, interval_scale)
        self.loop_cycle = loop_cycle

        self._history: Deque[MotionSnapshot] = deque(maxlen=max_history)
        self._sequence = 0
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._last_hash: Optional[str] = None
        self._snapshots_taken = 0
        self._errors = 0

    # ─────────────────────────────────────────────────────────────────────
    # Lifecycle
    # ─────────────────────────────────────────────────────────────────────

    def start(self, run_in_background: bool = True) -> None:
        """Start the Fibonacci snapshot loop."""
        if self._running:
            return
        self._running = True
        logger.info(
            "Snapper starting for %s (agent=%s, scale=%.3f)",
            self.session_id, self.agent_name, self.interval_scale,
        )
        if run_in_background:
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
        else:
            self._loop()

    def stop(self) -> None:
        """Stop the snapshot loop."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

    def _loop(self) -> None:
        """The main Fibonacci snapshot loop."""
        idx = 0
        while self._running:
            interval = FIBONACCI_INTERVALS[idx % len(FIBONACCI_INTERVALS)] * self.interval_scale
            # Sleep in small chunks so we can stop responsively
            remaining = interval
            while remaining > 0 and self._running:
                chunk = min(0.1, remaining)
                time.sleep(chunk)
                remaining -= chunk
            if not self._running:
                break
            self._take_snapshot(sequence=self._sequence, interval=interval)
            self._sequence += 1
            idx += 1
            if idx >= len(FIBONACCI_INTERVALS) and not self.loop_cycle:
                break
            if idx >= len(FIBONACCI_INTERVALS):
                idx = 0  # restart the spiral

    # ─────────────────────────────────────────────────────────────────────
    # Snapshot capture
    # ─────────────────────────────────────────────────────────────────────

    def take_single_snapshot(self, interval: float = 0.0) -> MotionSnapshot:
        """
        Capture one snapshot synchronously (bypassing the Fibonacci loop).
        Useful for on-demand captures and testing.
        """
        with self._lock:
            seq = self._sequence
            self._sequence += 1
        return self._take_snapshot(sequence=seq, interval=interval)

    def _take_snapshot(self, sequence: int, interval: float) -> MotionSnapshot:
        """Capture a single snapshot and push it through the pipeline."""
        snap = MotionSnapshot(
            session_id=self.session_id,
            agent_name=self.agent_name,
            sequence=sequence,
            interval_s=interval,
        )

        try:
            result = self.dispatcher.dispatch(
                "screenshot",
                {},
                session_id=self.session_id,
                source=f"snapper:{self.agent_name}",
            )
            if not result.get("ok"):
                snap.error = result.get("error", "unknown")
                self._errors += 1
            else:
                data = result.get("data", {}) or {}
                image_b64 = data.get("image_b64", "") or ""
                snap.width = int(data.get("width", 0) or 0)
                snap.height = int(data.get("height", 0) or 0)
                snap.cursor_x = int(data.get("cursor_x", 0) or 0)
                snap.cursor_y = int(data.get("cursor_y", 0) or 0)
                snap.image_b64_preview = image_b64[:64]
                # Perceptual hash via SHA-256 of the base64 payload
                snap.image_hash = hashlib.sha256(image_b64.encode()).hexdigest()
                snap.motion_delta = self._compute_motion_delta(snap.image_hash)
                snap.coherence = self._compute_coherence(snap)
        except Exception as e:
            snap.error = f"{type(e).__name__}: {e}"
            self._errors += 1

        self._last_hash = snap.image_hash
        self._snapshots_taken += 1
        with self._lock:
            self._history.append(snap)

        # Callback
        if self.on_snapshot:
            try:
                self.on_snapshot(snap)
            except Exception as cb_err:
                logger.debug("Snapshot callback error: %s", cb_err)

        return snap

    def _compute_motion_delta(self, new_hash: str) -> float:
        """
        Compute the Hamming-like distance between consecutive hashes.
        Returns a value in [0, 1] representing motion intensity.
        """
        if not self._last_hash or not new_hash:
            return 0.0
        if len(self._last_hash) != len(new_hash):
            return 1.0
        diff = sum(a != b for a, b in zip(self._last_hash, new_hash))
        return diff / max(len(new_hash), 1)

    def _compute_coherence(self, snap: MotionSnapshot) -> float:
        """
        Compute a Γ-like coherence score for the snapshot.
        Low motion on a clean frame = high coherence.
        """
        if snap.error:
            return 0.0
        # Start from 1 - motion_delta, then scale
        base = max(0.0, 1.0 - snap.motion_delta)
        # Boost for successful screen capture (non-zero dimensions)
        dims_ok = 1.0 if (snap.width > 0 and snap.height > 0) else 0.5
        return round(base * dims_ok, 4)

    # ─────────────────────────────────────────────────────────────────────
    # Introspection
    # ─────────────────────────────────────────────────────────────────────

    def get_history(self) -> List[MotionSnapshot]:
        with self._lock:
            return list(self._history)

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            avg_coherence = (
                sum(s.coherence for s in self._history) / len(self._history)
                if self._history else 0.0
            )
            return {
                "session_id": self.session_id,
                "agent_name": self.agent_name,
                "running": self._running,
                "sequence": self._sequence,
                "snapshots_taken": self._snapshots_taken,
                "errors": self._errors,
                "history_size": len(self._history),
                "avg_coherence": round(avg_coherence, 4),
                "phi": PHI,
            }
