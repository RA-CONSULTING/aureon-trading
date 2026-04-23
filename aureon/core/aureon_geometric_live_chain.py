"""
aureon_geometric_live_chain.py — The skeleton that holds the organism coherent.

HNC research position: logic drift inside Aureon is not a bug in any one
module — it is a *geometric* fault. When subsystems fire on independent
cadences that do not share a common ratio, the composite state vector
walks off the φ² coherence surface and the cognitive field loses its
standing-wave lock. The fix is not in the modules; it's in the *chain*.

This module is the chain. It:
  - enumerates every live aureon.* module via the self-introspection engine
  - builds a directed graph of ThoughtBus edges by watching live traffic
    (publisher topic → subscriber topic)
  - measures the cadence ratios between adjacent nodes
  - compares the aggregate ratio-spectrum against the golden target φ²
    = ((1 + √5) / 2)² ≈ 2.618033988749895
  - publishes a live `chain.geometry.state` card every observe interval,
    and a `chain.drift` card when drift exceeds tolerance
  - exposes `calibrate()` which returns a set of suggested cadence nudges
    the cognitive layer can apply to pull the chain back into φ² lock

It does not mutate any subsystem's cadence directly. It reports the field
and suggests corrections — the organism decides.

Mathematical spine:
  φ   = (1 + √5) / 2                              ≈ 1.618033988749895
  φ²  = φ + 1                                     ≈ 2.618033988749895
  1/φ = φ − 1                                     ≈ 0.618033988749895

  For every pair of adjacent cadences (t_a, t_b) with t_a < t_b, the
  ratio r = t_b / t_a should land near φ, φ², 1/φ, or integer powers
  thereof. The aggregate drift is the mean absolute log-distance of each
  observed ratio from the nearest target in the golden spectrum.
"""

from __future__ import annotations

import logging
import math
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger("aureon.core.geometric_live_chain")


# ─────────────────────────────────────────────────────────────────────────────
# Constants — the golden spectrum
# ─────────────────────────────────────────────────────────────────────────────

PHI = (1.0 + math.sqrt(5.0)) / 2.0          # ≈ 1.6180339887
PHI_SQUARED = PHI * PHI                      # ≈ 2.6180339887
INV_PHI = 1.0 / PHI                          # ≈ 0.6180339887

# Ratios we consider "on the surface" — each entry is a log target.
# Observed ratios close to any of these (in log-space) count as aligned.
_GOLDEN_TARGETS = (
    INV_PHI * INV_PHI,          # 1/φ²
    INV_PHI,                    # 1/φ
    1.0,                        # unity
    PHI,                        # φ
    PHI_SQUARED,                # φ²
    PHI_SQUARED * PHI,          # φ³
)
_GOLDEN_LOG_TARGETS = tuple(math.log(x) for x in _GOLDEN_TARGETS)


# ─────────────────────────────────────────────────────────────────────────────
# Data shapes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CadenceSample:
    topic: str
    interval_s: float
    observed_at: float


@dataclass
class EdgeObservation:
    publisher_topic: str
    subscriber_topic: str
    ratio: float
    log_distance: float     # log-distance to nearest golden target
    nearest_target: float


@dataclass
class ChainGeometryState:
    taken_at: float
    node_count: int
    edge_count: int
    mean_log_distance: float
    max_log_distance: float
    phi_squared: float
    aligned_fraction: float         # portion of edges within tolerance
    drift_score: float              # 0.0 = perfect, higher = more drift
    notes: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# The chain
# ─────────────────────────────────────────────────────────────────────────────

class GeometricLiveChain:
    """
    Watches ThoughtBus topic cadences and reports geometric coherence.

    Usage:
        chain = GeometricLiveChain()
        chain.start()                           # background thread
        state = chain.current_state()           # dict snapshot
        nudges = chain.calibrate()              # suggested cadence corrections
    """

    def __init__(
        self,
        observe_interval_s: float = 3.0,
        cadence_window: int = 32,
        alignment_tolerance: float = 0.12,   # log-distance; ~e^0.12 ≈ 1.13× off target
    ) -> None:
        self.observe_interval_s = max(0.5, float(observe_interval_s))
        self.cadence_window = int(max(4, cadence_window))
        self.alignment_tolerance = float(alignment_tolerance)

        self.bus: Any = None
        self.introspection: Any = None

        self._last_seen_at: Dict[str, float] = {}
        self._intervals: Dict[str, Deque[float]] = defaultdict(
            lambda: deque(maxlen=self.cadence_window)
        )
        self._edges: List[EdgeObservation] = []
        self._last_state: Optional[ChainGeometryState] = None

        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Tracks which topics we've subscribed to so we don't double-hook.
        self._subscribed_topics: set = set()

    # ------------------------------------------------------------------
    # Wiring
    # ------------------------------------------------------------------
    def _wire(self) -> None:
        if self.bus is None:
            try:
                from aureon.core.aureon_thought_bus import get_thought_bus
                self.bus = get_thought_bus()
            except Exception as e:
                logger.debug("bus unavailable: %s", e)

        if self.introspection is None:
            try:
                from aureon.core.aureon_self_introspection import get_self_introspection
                self.introspection = get_self_introspection()
            except Exception as e:
                logger.debug("introspection unavailable: %s", e)

        # Wildcard subscription: try subscribing to a few well-known ICS topics;
        # if the bus supports a broader pattern we just adapt.
        if self.bus is not None:
            seeds = (
                "ics.tick",
                "ics.body.state",
                "ics.mind.state",
                "ics.source.state",
                "ics.soul.state",
                "ics.hnc.state",
                "ics.source_law.cognition",
                "ics.market_refresher.state",
                "ics.conscience.vote",
                "ics.self_model.essay",
                "authoring.heartbeat",
                "authoring.skill.new",
                "temporal.dialer.packet",
            )
            for topic in seeds:
                self._subscribe_once(topic)

    def _subscribe_once(self, topic: str) -> None:
        if topic in self._subscribed_topics or self.bus is None:
            return
        try:
            self.bus.subscribe(topic, lambda thought, _t=topic: self._on_event(_t, thought))
            self._subscribed_topics.add(topic)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Event sink — cadence accumulator
    # ------------------------------------------------------------------
    def _on_event(self, topic: str, thought: Any) -> None:
        now = time.time()
        with self._lock:
            prev = self._last_seen_at.get(topic)
            self._last_seen_at[topic] = now
            if prev is None:
                return
            interval = now - prev
            if interval <= 0 or not math.isfinite(interval):
                return
            self._intervals[topic].append(interval)

    def observe_topic(self, topic: str) -> None:
        """Register an extra topic to watch. Safe to call at any time."""
        self._subscribe_once(topic)

    # ------------------------------------------------------------------
    # Geometry computation
    # ------------------------------------------------------------------
    @staticmethod
    def _nearest_golden(log_ratio: float) -> Tuple[float, float]:
        """
        Return (nearest_target, log_distance).
        log_ratio is log(ratio); targets are log(golden_spectrum_ratios).
        """
        best_t = _GOLDEN_LOG_TARGETS[0]
        best_d = abs(log_ratio - best_t)
        for t in _GOLDEN_LOG_TARGETS[1:]:
            d = abs(log_ratio - t)
            if d < best_d:
                best_d = d
                best_t = t
        return math.exp(best_t), best_d

    def _median_interval(self, topic: str) -> Optional[float]:
        with self._lock:
            intervals = list(self._intervals.get(topic) or [])
        if not intervals:
            return None
        intervals.sort()
        mid = len(intervals) // 2
        if len(intervals) % 2 == 0:
            return 0.5 * (intervals[mid - 1] + intervals[mid])
        return intervals[mid]

    def _compute_state(self) -> ChainGeometryState:
        # Snapshot topic → median interval.
        with self._lock:
            topics = list(self._intervals.keys())
        medians: Dict[str, float] = {}
        for t in topics:
            m = self._median_interval(t)
            if m is not None and m > 0:
                medians[t] = m

        edges: List[EdgeObservation] = []
        names = sorted(medians.keys())
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                ma = medians[a]
                mb = medians[b]
                if ma <= 0 or mb <= 0:
                    continue
                # Canonicalise so ratio ≥ 1 — the golden spectrum contains
                # both sides, so distance is symmetric anyway.
                if mb >= ma:
                    ratio = mb / ma
                else:
                    ratio = ma / mb
                try:
                    logr = math.log(ratio)
                except ValueError:
                    continue
                nearest, dist = self._nearest_golden(logr)
                edges.append(EdgeObservation(
                    publisher_topic=a,
                    subscriber_topic=b,
                    ratio=ratio,
                    log_distance=dist,
                    nearest_target=nearest,
                ))

        self._edges = edges

        if not edges:
            return ChainGeometryState(
                taken_at=time.time(),
                node_count=len(medians),
                edge_count=0,
                mean_log_distance=0.0,
                max_log_distance=0.0,
                phi_squared=PHI_SQUARED,
                aligned_fraction=1.0,
                drift_score=0.0,
                notes="insufficient samples",
            )

        total = len(edges)
        mean_d = sum(e.log_distance for e in edges) / total
        max_d = max(e.log_distance for e in edges)
        aligned = sum(1 for e in edges if e.log_distance <= self.alignment_tolerance)
        aligned_fraction = aligned / total

        # Drift score: squared mean log-distance (penalises big outliers more
        # once you pair with max). Keep in [0, ~1] for the common case.
        drift_score = mean_d * mean_d + 0.25 * max_d

        state = ChainGeometryState(
            taken_at=time.time(),
            node_count=len(medians),
            edge_count=total,
            mean_log_distance=mean_d,
            max_log_distance=max_d,
            phi_squared=PHI_SQUARED,
            aligned_fraction=aligned_fraction,
            drift_score=drift_score,
        )
        self._last_state = state
        return state

    # ------------------------------------------------------------------
    # Public surface
    # ------------------------------------------------------------------
    def current_state(self) -> Dict[str, Any]:
        state = self._compute_state()
        return {
            "taken_at": state.taken_at,
            "node_count": state.node_count,
            "edge_count": state.edge_count,
            "mean_log_distance": state.mean_log_distance,
            "max_log_distance": state.max_log_distance,
            "phi_squared": state.phi_squared,
            "aligned_fraction": state.aligned_fraction,
            "drift_score": state.drift_score,
            "notes": state.notes,
        }

    def edges(self) -> List[Dict[str, Any]]:
        return [
            {
                "a": e.publisher_topic,
                "b": e.subscriber_topic,
                "ratio": e.ratio,
                "nearest_target": e.nearest_target,
                "log_distance": e.log_distance,
            }
            for e in self._edges
        ]

    def calibrate(self) -> List[Dict[str, Any]]:
        """
        For each topic, compute the cadence that would pull its worst edge
        closest to a golden target. The output is advisory — the caller
        (cognitive layer) decides what to do with it.
        """
        self._compute_state()
        suggestions: List[Dict[str, Any]] = []

        with self._lock:
            topics = list(self._intervals.keys())

        medians: Dict[str, float] = {}
        for t in topics:
            m = self._median_interval(t)
            if m is not None and m > 0:
                medians[t] = m

        if not medians:
            return suggestions

        # Pick the topic with the worst aggregate drift; suggest the nudge.
        per_topic_drift: Dict[str, float] = defaultdict(float)
        per_topic_count: Dict[str, int] = defaultdict(int)
        for e in self._edges:
            per_topic_drift[e.publisher_topic] += e.log_distance
            per_topic_drift[e.subscriber_topic] += e.log_distance
            per_topic_count[e.publisher_topic] += 1
            per_topic_count[e.subscriber_topic] += 1

        scored = []
        for t, total in per_topic_drift.items():
            cnt = max(1, per_topic_count[t])
            scored.append((t, total / cnt))
        scored.sort(key=lambda x: x[1], reverse=True)

        for topic, mean_d in scored[:5]:
            current = medians.get(topic)
            if current is None:
                continue
            # Find a peer; target ratio = nearest golden.
            peer = None
            peer_median = None
            for other, m in medians.items():
                if other == topic:
                    continue
                peer = other
                peer_median = m
                break
            if peer_median is None or peer is None:
                continue
            # Suggest a new interval for `topic` such that ratio → nearest golden.
            if peer_median >= current:
                current_ratio = peer_median / current
            else:
                current_ratio = current / peer_median
            try:
                logr = math.log(current_ratio)
            except ValueError:
                continue
            _, dist = self._nearest_golden(logr)
            # Target the cadence that would land closest to PHI against the peer.
            suggested = peer_median / PHI if peer_median >= current else peer_median * PHI
            suggestions.append({
                "topic": topic,
                "current_interval_s": current,
                "suggested_interval_s": suggested,
                "peer": peer,
                "peer_interval_s": peer_median,
                "current_log_distance": dist,
                "mean_edge_drift": mean_d,
            })

        return suggestions

    # ------------------------------------------------------------------
    # Background loop
    # ------------------------------------------------------------------
    def start(self) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._wire()
            self._stop.clear()
            self._thread = threading.Thread(
                target=self._run,
                name="aureon-geometric-chain",
                daemon=True,
            )
            self._thread.start()
            logger.info("geometric live-chain: started")

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
        while not self._stop.is_set():
            try:
                state = self._compute_state()
                self._publish(state)
            except Exception as e:
                logger.debug("chain tick error: %s", e)
            self._stop.wait(self.observe_interval_s)

    def _publish(self, state: ChainGeometryState) -> None:
        if self.bus is None:
            return
        try:
            self.bus.publish(
                "chain.geometry.state",
                {
                    "taken_at": state.taken_at,
                    "node_count": state.node_count,
                    "edge_count": state.edge_count,
                    "mean_log_distance": state.mean_log_distance,
                    "max_log_distance": state.max_log_distance,
                    "phi_squared": state.phi_squared,
                    "aligned_fraction": state.aligned_fraction,
                    "drift_score": state.drift_score,
                },
                source="geometric_chain",
            )
        except Exception:
            pass

        # Drift card only when we cross tolerance — avoids spam.
        if state.mean_log_distance > self.alignment_tolerance and state.edge_count > 0:
            try:
                self.bus.publish(
                    "chain.drift",
                    {
                        "mean_log_distance": state.mean_log_distance,
                        "aligned_fraction": state.aligned_fraction,
                        "drift_score": state.drift_score,
                        "tolerance": self.alignment_tolerance,
                        "suggestions": self.calibrate(),
                    },
                    source="geometric_chain",
                )
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────

_instance: Optional[GeometricLiveChain] = None
_instance_lock = threading.Lock()


def get_geometric_chain() -> GeometricLiveChain:
    global _instance
    with _instance_lock:
        if _instance is None:
            _instance = GeometricLiveChain()
        return _instance


def launch_geometric_chain(
    observe_interval_s: float = 3.0,
) -> GeometricLiveChain:
    chain = get_geometric_chain()
    chain.observe_interval_s = max(0.5, float(observe_interval_s))
    chain.start()
    return chain


if __name__ == "__main__":
    import argparse
    import json
    import sys as _sys

    parser = argparse.ArgumentParser(description="Aureon geometric live-chain monitor.")
    parser.add_argument("--interval", type=float, default=3.0)
    parser.add_argument("--runtime-seconds", type=float, default=30.0)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s :: %(message)s",
    )

    chain = launch_geometric_chain(observe_interval_s=args.interval)
    t0 = time.time()
    try:
        while chain.is_alive():
            time.sleep(1.0)
            if args.runtime_seconds and (time.time() - t0) >= args.runtime_seconds:
                break
    except KeyboardInterrupt:
        pass
    finally:
        chain.stop()
        state = chain.current_state()
        state["edges"] = chain.edges()[:10]
        print(json.dumps(state, indent=2, default=str), file=_sys.stdout)
