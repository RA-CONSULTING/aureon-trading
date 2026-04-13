"""
aureon/queen/temporal_knowledge.py

TemporalKnowledgeBase — gives agents a sense of TIME.

What it does:
  Subscribes to the ThoughtBus and indexes every event with timestamp,
  topic, and payload. Provides time-window queries, pattern detection,
  recency tracking, causal chain inference, and temporal statistics.

The output of this knowledge base feeds INTO every agent's system prompt
so that when an LLM agent decides what to do, it can see:
  - what happened in the last N seconds/minutes/hours
  - which topics fired most often
  - whether a topic is bursting (suddenly active) or quiet
  - when this exact action was last attempted
  - the causal chain of recent events

This is how agents acquire temporal knowledge — not just "I have memory"
but "I know what happened, when, in what order, and how often."

Architecture:
  - Ring buffer of TemporalEvent records (timestamp, topic, source, payload_summary)
  - Topic index: topic -> deque of timestamps (for recency + rate queries)
  - Causal chains: parent_id -> child events (when ThoughtBus carries lineage)
  - Pattern detector: rolling 60s window of topic frequencies
  - Burst detector: topic rate > 3x baseline = bursting

Singleton pattern matches the rest of the queen layer.
"""

from __future__ import annotations

import math
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional, Tuple


@dataclass
class TemporalEvent:
    """One event in the temporal index."""
    timestamp: float
    topic: str
    source: str
    payload_summary: str = ""
    trace_id: str = ""
    parent_id: Optional[str] = None
    event_id: str = ""


@dataclass
class TopicStats:
    """Rolling statistics for one topic."""
    topic: str
    total_count: int = 0
    last_seen: float = 0.0
    first_seen: float = 0.0
    rate_per_min: float = 0.0
    bursting: bool = False  # rate > 3x baseline


class TemporalKnowledgeBase:
    """
    A time-indexed knowledge layer over the ThoughtBus.

    Usage:
        tkb = TemporalKnowledgeBase()
        tkb.subscribe_to(thought_bus)

        # Query
        recent = tkb.events_in_window(seconds=60)
        last_swarm = tkb.last_occurrence("swarm.completed")
        bursting = tkb.bursting_topics()
        summary = tkb.temporal_context()  # for agent prompts
    """

    def __init__(
        self,
        max_events: int = 5000,
        max_per_topic: int = 500,
        burst_threshold: float = 3.0,
        baseline_window_s: float = 300.0,  # 5 minutes baseline
    ):
        self._events: Deque[TemporalEvent] = deque(maxlen=max_events)
        self._topic_index: Dict[str, Deque[float]] = defaultdict(
            lambda: deque(maxlen=max_per_topic)
        )
        self._topic_stats: Dict[str, TopicStats] = {}
        self._causal_children: Dict[str, List[str]] = defaultdict(list)
        self._lock = threading.RLock()
        self._burst_threshold = burst_threshold
        self._baseline_window_s = baseline_window_s
        self._created_at = time.time()
        self._thought_bus: Any = None

    # ─────────────────────────────────────────────────────────────────────
    # ThoughtBus subscription
    # ─────────────────────────────────────────────────────────────────────
    def subscribe_to(self, thought_bus: Any) -> None:
        """Wire to a ThoughtBus to absorb every event."""
        self._thought_bus = thought_bus
        try:
            thought_bus.subscribe("*", self._on_event)
        except Exception:
            pass

    def _on_event(self, thought: Any) -> None:
        """Handle one ThoughtBus event."""
        try:
            ts = float(getattr(thought, "ts", time.time()) or time.time())
            topic = str(getattr(thought, "topic", "") or "")
            source = str(getattr(thought, "source", "") or "")
            event_id = str(getattr(thought, "id", "") or "")
            trace_id = str(getattr(thought, "trace_id", "") or "")
            parent_id = getattr(thought, "parent_id", None)
            payload = getattr(thought, "payload", {})

            # Avoid recursive feedback from temporal events themselves
            if topic.startswith("temporal."):
                return

            # Compact payload summary
            if isinstance(payload, dict):
                items = list(payload.items())[:3]
                summary = ", ".join(f"{k}={str(v)[:30]}" for k, v in items)
            else:
                summary = str(payload)[:80]

            event = TemporalEvent(
                timestamp=ts,
                topic=topic,
                source=source,
                payload_summary=summary,
                trace_id=trace_id,
                parent_id=parent_id,
                event_id=event_id,
            )

            with self._lock:
                self._events.append(event)
                self._topic_index[topic].append(ts)

                # Update stats
                stats = self._topic_stats.get(topic)
                if stats is None:
                    stats = TopicStats(
                        topic=topic,
                        first_seen=ts,
                    )
                    self._topic_stats[topic] = stats
                stats.total_count += 1
                stats.last_seen = ts

                # Causal chain
                if parent_id:
                    self._causal_children[parent_id].append(event_id)
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────────────
    # Time-window queries
    # ─────────────────────────────────────────────────────────────────────
    def events_in_window(
        self,
        seconds: float = 60.0,
        topic_prefix: Optional[str] = None,
    ) -> List[TemporalEvent]:
        """Return events from the last `seconds` seconds, optionally filtered."""
        cutoff = time.time() - seconds
        with self._lock:
            events = [e for e in self._events if e.timestamp >= cutoff]
        if topic_prefix:
            events = [e for e in events if e.topic.startswith(topic_prefix)]
        return events

    def last_occurrence(self, topic: str) -> Optional[float]:
        """Return timestamp of the last time this topic fired, or None."""
        with self._lock:
            stats = self._topic_stats.get(topic)
            if stats:
                return stats.last_seen
        return None

    def time_since(self, topic: str) -> Optional[float]:
        """Return seconds since this topic last fired, or None."""
        last = self.last_occurrence(topic)
        if last is None:
            return None
        return time.time() - last

    def topic_count(self, topic: str) -> int:
        """Return total number of times this topic has fired."""
        with self._lock:
            return self._topic_stats.get(topic, TopicStats(topic=topic)).total_count

    def topic_rate(self, topic: str, window_s: float = 60.0) -> float:
        """Return events-per-minute rate for this topic over the window."""
        cutoff = time.time() - window_s
        with self._lock:
            timestamps = self._topic_index.get(topic, deque())
            recent = [t for t in timestamps if t >= cutoff]
        if not recent:
            return 0.0
        return (len(recent) / window_s) * 60.0

    # ─────────────────────────────────────────────────────────────────────
    # Pattern detection
    # ─────────────────────────────────────────────────────────────────────
    def bursting_topics(self, window_s: float = 60.0) -> List[Tuple[str, float, float]]:
        """
        Return topics whose recent rate is > burst_threshold * baseline rate.
        Returns: list of (topic, recent_rate, baseline_rate).
        """
        bursting: List[Tuple[str, float, float]] = []
        now = time.time()
        with self._lock:
            for topic, ts_deque in self._topic_index.items():
                recent = [t for t in ts_deque if t >= now - window_s]
                baseline_window = [t for t in ts_deque if t >= now - self._baseline_window_s]
                if len(recent) < 3 or len(baseline_window) < 5:
                    continue
                recent_rate = (len(recent) / window_s) * 60.0
                baseline_rate = (len(baseline_window) / self._baseline_window_s) * 60.0
                if baseline_rate > 0 and recent_rate / baseline_rate > self._burst_threshold:
                    bursting.append((topic, round(recent_rate, 2), round(baseline_rate, 2)))
        bursting.sort(key=lambda x: -x[1])
        return bursting

    def hottest_topics(self, n: int = 10, window_s: float = 60.0) -> List[Tuple[str, int]]:
        """Return the n most-frequent topics in the recent window."""
        cutoff = time.time() - window_s
        counts: Dict[str, int] = defaultdict(int)
        with self._lock:
            for e in self._events:
                if e.timestamp >= cutoff:
                    counts[e.topic] += 1
        return sorted(counts.items(), key=lambda x: -x[1])[:n]

    def causal_chain(self, event_id: str, max_depth: int = 5) -> List[str]:
        """Walk the causal chain forward from an event id."""
        chain: List[str] = []
        with self._lock:
            current = [event_id]
            depth = 0
            while current and depth < max_depth:
                children = []
                for cid in current:
                    children.extend(self._causal_children.get(cid, []))
                chain.extend(children)
                current = children
                depth += 1
        return chain

    # ─────────────────────────────────────────────────────────────────────
    # Temporal context — formatted for agent prompts
    # ─────────────────────────────────────────────────────────────────────
    def temporal_context(self, window_s: float = 60.0, max_lines: int = 8) -> str:
        """
        Produce a compact temporal-context block to inject into an agent's
        system prompt. Tells the agent what just happened, what's bursting,
        and what's quiet.
        """
        with self._lock:
            total_events = len(self._events)
            uptime = time.time() - self._created_at

        recent = self.events_in_window(seconds=window_s)
        hot = self.hottest_topics(n=5, window_s=window_s)
        bursts = self.bursting_topics(window_s=window_s)

        lines = ["[TEMPORAL CONTEXT]"]
        lines.append(
            f"  Uptime: {uptime:.0f}s  Total events: {total_events}  "
            f"Recent ({window_s:.0f}s): {len(recent)}"
        )
        if hot:
            top_str = ", ".join(f"{t}({n})" for t, n in hot)
            lines.append(f"  Hot topics: {top_str}")
        if bursts:
            burst_str = ", ".join(f"{t}({recent_r:.0f}/min vs {base_r:.0f})"
                                   for t, recent_r, base_r in bursts[:3])
            lines.append(f"  Bursting: {burst_str}")
        if recent:
            # Show 3 most recent events
            tail = recent[-3:]
            for e in tail:
                age = time.time() - e.timestamp
                lines.append(f"  -{age:.1f}s  {e.topic}  {e.payload_summary[:50]}")
        return "\n".join(lines[:max_lines + 2])

    # ─────────────────────────────────────────────────────────────────────
    # Status snapshot
    # ─────────────────────────────────────────────────────────────────────
    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_events": len(self._events),
                "unique_topics": len(self._topic_stats),
                "uptime_s": round(time.time() - self._created_at, 1),
                "burst_threshold": self._burst_threshold,
                "max_events": self._events.maxlen,
            }


# ─────────────────────────────────────────────────────────────────────────────
# Singleton accessor
# ─────────────────────────────────────────────────────────────────────────────

_singleton: Optional[TemporalKnowledgeBase] = None
_singleton_lock = threading.Lock()


def get_temporal_knowledge() -> TemporalKnowledgeBase:
    """Return the global TemporalKnowledgeBase."""
    global _singleton
    with _singleton_lock:
        if _singleton is None:
            _singleton = TemporalKnowledgeBase()
        return _singleton


def reset_temporal_knowledge() -> None:
    global _singleton
    with _singleton_lock:
        _singleton = None
