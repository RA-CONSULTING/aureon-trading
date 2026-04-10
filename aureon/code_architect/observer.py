"""
ObservationEngine — watches the swarm motion environment for skill candidates
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Listens to motion snapshots from the swarm motion hive and the VM control
dispatcher's action history, detects recurring patterns, and surfaces them
as skill candidates for the writer.

A "pattern" is a recurring sequence of VM actions observed within a
temporal window. When the same sequence appears >= min_occurrences times,
it becomes an ObservedPattern eligible for code generation.

The engine can also be fed observations directly (for tests and for
end-user skill teaching where we record the user's own actions).
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
import uuid
from collections import Counter, deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional, Tuple

logger = logging.getLogger("aureon.code_architect.observer")


# ─────────────────────────────────────────────────────────────────────────────
# ObservedPattern
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ObservedPattern:
    """A pattern detected in the action stream — a skill candidate."""

    pattern_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    signature: str = ""                                  # hash of the action sequence
    action_sequence: List[Dict[str, Any]] = field(default_factory=list)
    occurrence_count: int = 0
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    coherence: float = 0.0                                # avg snapshot coherence
    suggested_name: str = ""
    suggested_description: str = ""
    contributing_sessions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "signature": self.signature,
            "action_sequence": self.action_sequence,
            "action_count": len(self.action_sequence),
            "occurrence_count": self.occurrence_count,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "coherence": round(self.coherence, 4),
            "suggested_name": self.suggested_name,
            "suggested_description": self.suggested_description,
            "contributing_sessions": self.contributing_sessions,
        }


# ─────────────────────────────────────────────────────────────────────────────
# ObservationEngine
# ─────────────────────────────────────────────────────────────────────────────


class ObservationEngine:
    """
    Tracks observed action sequences and surfaces recurring patterns.

    Usage:
        obs = ObservationEngine(window_size=5, min_occurrences=3)
        obs.record_action("vm_mouse_move", {"x": 500, "y": 300})
        obs.record_action("vm_left_click", {"x": 500, "y": 300})
        obs.record_action("vm_type_text", {"text": "hello"})
        ... (repeat)
        patterns = obs.get_pending_patterns()
    """

    def __init__(
        self,
        window_size: int = 3,                    # length of action sequences we track
        min_occurrences: int = 2,                # threshold before surfacing as pattern
        max_history: int = 2000,
        snap_coherence_default: float = 0.5,
    ):
        self.window_size = window_size
        self.min_occurrences = min_occurrences
        self.max_history = max_history
        self.snap_coherence_default = snap_coherence_default

        self._actions: Deque[Dict[str, Any]] = deque(maxlen=max_history)
        self._pattern_counts: Counter = Counter()
        self._pattern_sequences: Dict[str, List[Dict[str, Any]]] = {}
        self._pattern_metadata: Dict[str, Dict[str, Any]] = {}
        self._surfaced: set = set()
        self._pending_patterns: List[ObservedPattern] = []

        self._lock = threading.RLock()

        # Metrics
        self._total_actions_recorded = 0
        self._total_patterns_detected = 0
        self._recent_coherence: Deque[float] = deque(maxlen=50)

    # ─────────────────────────────────────────────────────────────────────
    # Recording
    # ─────────────────────────────────────────────────────────────────────

    def record_action(
        self,
        action: str,
        params: Optional[Dict[str, Any]] = None,
        session_id: str = "",
        coherence: Optional[float] = None,
    ) -> None:
        """Record a single VM action into the observation stream."""
        entry = {
            "action": str(action),
            "params": dict(params or {}),
            "session_id": session_id,
            "timestamp": time.time(),
            "coherence": float(coherence) if coherence is not None else self.snap_coherence_default,
        }

        with self._lock:
            self._actions.append(entry)
            self._total_actions_recorded += 1
            self._recent_coherence.append(entry["coherence"])
            self._update_patterns()

    def record_sequence(
        self,
        actions: List[Tuple[str, Dict[str, Any]]],
        session_id: str = "",
        coherence: float = 0.8,
    ) -> None:
        """Record a pre-formed sequence of actions atomically."""
        for action, params in actions:
            self.record_action(action, params, session_id=session_id, coherence=coherence)

    def record_from_dispatcher_history(self, dispatcher: Any, session_id: Optional[str] = None) -> int:
        """
        Pull recent action history from a VMControlDispatcher's sessions.
        Returns the number of new actions recorded.
        """
        count = 0
        try:
            sessions = dispatcher.list_sessions()
        except Exception:
            return 0

        for s in sessions:
            sid = s.get("session_id")
            if session_id and sid != session_id:
                continue
            controller = dispatcher.get_session(sid)
            if not controller:
                continue
            history = getattr(controller.session, "action_history", [])
            for result in history:
                try:
                    self.record_action(
                        action=result.action,
                        params=result.data,
                        session_id=sid,
                        coherence=0.85 if result.ok else 0.2,
                    )
                    count += 1
                except Exception:
                    pass
        return count

    def record_from_snapshot(self, snapshot: Any) -> None:
        """Record a MotionSnapshot as an 'observe' action."""
        if hasattr(snapshot, "to_dict"):
            data = snapshot.to_dict()
        else:
            data = dict(snapshot) if isinstance(snapshot, dict) else {}

        self.record_action(
            action="observe_snapshot",
            params={
                "image_hash": data.get("image_hash", "")[:16],
                "motion_delta": data.get("motion_delta", 0.0),
                "cursor_x": data.get("cursor_x", 0),
                "cursor_y": data.get("cursor_y", 0),
            },
            session_id=data.get("session_id", ""),
            coherence=data.get("coherence", 0.5),
        )

    # ─────────────────────────────────────────────────────────────────────
    # Pattern detection
    # ─────────────────────────────────────────────────────────────────────

    def _pattern_signature(self, actions: List[Dict[str, Any]]) -> str:
        """
        Compute a signature that groups equivalent action sequences.

        Only the action NAMES are hashed (not the specific params), so
        click(500,300)+type("hello") and click(100,200)+type("world")
        are treated as the same pattern.
        """
        names = "|".join(a["action"] for a in actions)
        return hashlib.sha1(names.encode()).hexdigest()[:12]

    def _update_patterns(self) -> None:
        """Scan the recent window for new pattern matches."""
        if len(self._actions) < self.window_size:
            return

        # Take the last `window_size` actions as a candidate sequence
        recent = list(self._actions)[-self.window_size:]
        signature = self._pattern_signature(recent)

        self._pattern_counts[signature] += 1
        if signature not in self._pattern_sequences:
            self._pattern_sequences[signature] = [dict(a) for a in recent]
            self._pattern_metadata[signature] = {
                "first_seen": time.time(),
                "sessions": set(),
            }

        self._pattern_metadata[signature]["last_seen"] = time.time()
        for a in recent:
            sid = a.get("session_id") or ""
            if sid:
                self._pattern_metadata[signature]["sessions"].add(sid)

        # Surface the pattern once it crosses the threshold
        count = self._pattern_counts[signature]
        if count >= self.min_occurrences and signature not in self._surfaced:
            self._surfaced.add(signature)
            self._create_pattern_record(signature)

    def _create_pattern_record(self, signature: str) -> None:
        sequence = self._pattern_sequences.get(signature, [])
        metadata = self._pattern_metadata.get(signature, {})
        count = self._pattern_counts[signature]

        # Compute mean coherence from the actions in the sequence
        if sequence:
            coherence = sum(a.get("coherence", 0) for a in sequence) / len(sequence)
        else:
            coherence = 0.0

        # Suggest a name from the action names
        action_names = [a["action"].replace("vm_", "").replace("_", " ") for a in sequence]
        suggested_name = "_".join(a.replace("vm_", "") for a in [x["action"] for x in sequence])
        if len(suggested_name) > 48:
            suggested_name = suggested_name[:48] + "_etc"
        suggested_description = f"Observed sequence: {' → '.join(action_names)}"

        pattern = ObservedPattern(
            signature=signature,
            action_sequence=sequence,
            occurrence_count=count,
            first_seen=metadata.get("first_seen", time.time()),
            last_seen=metadata.get("last_seen", time.time()),
            coherence=coherence,
            suggested_name=suggested_name,
            suggested_description=suggested_description,
            contributing_sessions=sorted(metadata.get("sessions", set())),
        )

        self._pending_patterns.append(pattern)
        self._total_patterns_detected += 1
        logger.info(
            "ObservedPattern: %s (count=%d, actions=%d)",
            suggested_name, count, len(sequence),
        )

    # ─────────────────────────────────────────────────────────────────────
    # Pattern retrieval
    # ─────────────────────────────────────────────────────────────────────

    def get_pending_patterns(self, clear: bool = True) -> List[ObservedPattern]:
        """Return all patterns that are ready for skill proposal."""
        with self._lock:
            patterns = list(self._pending_patterns)
            if clear:
                self._pending_patterns.clear()
        return patterns

    def get_all_patterns(self) -> List[ObservedPattern]:
        """Return all known patterns (surfaced or not), sorted by count."""
        with self._lock:
            patterns = []
            for sig, count in self._pattern_counts.items():
                sequence = self._pattern_sequences.get(sig, [])
                metadata = self._pattern_metadata.get(sig, {})
                coherence = (
                    sum(a.get("coherence", 0) for a in sequence) / len(sequence)
                    if sequence else 0.0
                )
                patterns.append(ObservedPattern(
                    signature=sig,
                    action_sequence=sequence,
                    occurrence_count=count,
                    first_seen=metadata.get("first_seen", 0),
                    last_seen=metadata.get("last_seen", 0),
                    coherence=coherence,
                    suggested_name="_".join(a["action"].replace("vm_", "") for a in sequence)[:48],
                    contributing_sessions=sorted(metadata.get("sessions", set())),
                ))
            patterns.sort(key=lambda p: p.occurrence_count, reverse=True)
            return patterns

    # ─────────────────────────────────────────────────────────────────────
    # Status
    # ─────────────────────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            avg_coherence = (
                sum(self._recent_coherence) / len(self._recent_coherence)
                if self._recent_coherence else 0.0
            )
            return {
                "window_size": self.window_size,
                "min_occurrences": self.min_occurrences,
                "actions_recorded": self._total_actions_recorded,
                "action_buffer": len(self._actions),
                "unique_patterns": len(self._pattern_counts),
                "surfaced_patterns": len(self._surfaced),
                "pending_patterns": len(self._pending_patterns),
                "total_patterns_detected": self._total_patterns_detected,
                "avg_recent_coherence": round(avg_coherence, 4),
            }

    def reset(self) -> None:
        with self._lock:
            self._actions.clear()
            self._pattern_counts.clear()
            self._pattern_sequences.clear()
            self._pattern_metadata.clear()
            self._surfaced.clear()
            self._pending_patterns.clear()
            self._total_actions_recorded = 0
            self._total_patterns_detected = 0
            self._recent_coherence.clear()
