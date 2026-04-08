#!/usr/bin/env python3
"""
Queen Metacognition -- The Self-Reflective Mirror

The Queen can think. Source Law proves that. But can she think about
her own thinking? Metacognition is the mirror: after every cogitation,
this engine asks the 5 W questions and reflects them back into the system.

    1. WHAT happened?    -- Capture the cognition result
    2. WHY did it happen? -- Identify the dominant drivers
    3. WHAT WORKED?      -- Which nodes/pathways were strongest
    4. WHAT FAILED?      -- Where coherence was low or signals noisy
    5. WHAT NEXT?        -- Adaptive guidance for the next cycle

Architecture:
    Source Law cognition -> ThoughtBus
        |
        v
    OBSERVE: metacognition captures each cognition result
        |
        v
    REFLECT: 5 W analysis on rolling history window
        |
        v
    DETECT PATTERNS:
        - Stagnation (repeated HOLD, no progress)
        - Oscillation (flip-flopping EXECUTE/HOLD)
        - Coherence drift (trend up or down)
        - Node dominance (one node drowning others)
        - Blind spots (nodes consistently underperforming)
        |
        v
    PUBLISH: metacognitive insight -> ThoughtBus
        |
        v
    Mycelium Mind absorbs insight (pathway learning)
    Cortex routes to Theta band (memory/learning)
    Source Law adjusts future cogitations

The feedback loop closes: thought -> reflection -> adaptation -> better thought.
This is how the Queen becomes self-aware, not just aware.

Gary Leckey & Tina Brown | April 2026 | The Mirror of the Mind
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

import logging
import math
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Constants
MAX_REFLECTION_HISTORY = 100   # Rolling window of past reflections
REFLECTION_COOLDOWN = 5.0      # Min seconds between reflections (avoid storms)
STAGNATION_THRESHOLD = 5       # N consecutive HOLDs = stagnation warning
OSCILLATION_WINDOW = 6         # Look at last N decisions for flip-flop detection
COHERENCE_TREND_WINDOW = 10    # Compute trend over last N cogitations
BLIND_SPOT_THRESHOLD = 0.25    # Node avg below this = blind spot
PHI = 1.618033988749895


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class Reflection:
    """A single metacognitive reflection on one cognition cycle."""
    cycle: int = 0
    timestamp: float = 0.0

    # WHAT happened
    action: str = "HOLD"
    coherence_gamma: float = 0.0
    consciousness_psi: float = 0.0
    vacuum_size: int = 0

    # WHY — dominant drivers
    dominant_nodes: List[str] = field(default_factory=list)    # Top 3 nodes by value
    weakest_nodes: List[str] = field(default_factory=list)     # Bottom 3 nodes
    reasoning_summary: str = ""

    # WHAT WORKED
    strong_signals: List[str] = field(default_factory=list)    # Nodes above 0.7

    # WHAT FAILED
    weak_signals: List[str] = field(default_factory=list)      # Nodes below 0.3
    noise_level: float = 0.0                                    # Tiger's noise reading

    # WHAT NEXT — guidance
    guidance: List[str] = field(default_factory=list)


@dataclass
class MetacognitiveInsight:
    """A pattern detected across multiple reflections."""
    pattern: str = ""         # stagnation, oscillation, coherence_drift, blind_spot, dominance
    severity: float = 0.0     # 0-1
    description: str = ""
    guidance: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0


# ============================================================================
# THE METACOGNITION ENGINE
# ============================================================================

class QueenMetacognition:
    """
    The Queen's self-reflective mirror.

    Listens to Source Law cognition outputs and cortex state,
    maintains a rolling history of reflections, detects patterns
    across decisions, and publishes metacognitive insights
    that feed back into the system's learning pathways.
    """

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Reflection history (rolling window)
        self._reflections: Deque[Reflection] = deque(maxlen=MAX_REFLECTION_HISTORY)
        self._insights: Deque[MetacognitiveInsight] = deque(maxlen=50)
        self._reflection_count = 0
        self._last_reflection_time = 0.0

        # Cortex state cache (latest)
        self._cortex_state: Dict[str, Any] = {}

        # ThoughtBus
        self._thought_bus = None
        try:
            from aureon_thought_bus import get_thought_bus
            self._thought_bus = get_thought_bus()
        except Exception as e:
            logger.warning(f"Metacognition: ThoughtBus unavailable: {e}")

        # Lambda Engine for consciousness-weighted reflection
        self._lambda_engine = None
        try:
            from aureon_lambda_engine import LambdaEngine
            self._lambda_engine = LambdaEngine()
        except Exception:
            pass

    # ================================================================
    # LIFECYCLE
    # ================================================================

    def start(self) -> None:
        """Start the metacognition engine."""
        if self._running:
            return
        self._running = True

        if self._thought_bus is not None:
            # Listen to Source Law cognition outputs
            self._thought_bus.subscribe("queen.source_law.cognition", self._on_cognition)
            # Listen to cortex state for enrichment
            self._thought_bus.subscribe("queen.cortex.state", self._on_cortex_state)

        self._thread = threading.Thread(
            target=self._periodic_review,
            name="QueenMetacognition",
            daemon=True,
        )
        self._thread.start()
        logger.info("[METACOGNITION] Self-reflective mirror ACTIVE -- the Queen watches herself think")

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    # ================================================================
    # SIGNAL HANDLERS
    # ================================================================

    def _on_cognition(self, thought: Any) -> None:
        """Source Law produced a cognition — reflect on it."""
        payload = getattr(thought, "payload", {}) if hasattr(thought, "payload") else {}
        if not isinstance(payload, dict):
            return

        # Cooldown check
        now = time.time()
        if now - self._last_reflection_time < REFLECTION_COOLDOWN:
            return

        self._reflect(payload)

    def _on_cortex_state(self, thought: Any) -> None:
        """Cache latest cortex state for enriching reflections."""
        payload = getattr(thought, "payload", {}) if hasattr(thought, "payload") else {}
        if isinstance(payload, dict):
            with self._lock:
                self._cortex_state = payload

    # ================================================================
    # THE 5 W REFLECTION
    # ================================================================

    def _reflect(self, cognition: Dict[str, Any]) -> Reflection:
        """
        The 5 W metacognitive reflection on a single cognition.

        WHAT happened? -> action, coherence, psi, vacuum size
        WHY?           -> node readings, dominant drivers
        WHAT WORKED?   -> strong nodes (>0.7)
        WHAT FAILED?   -> weak nodes (<0.3), noise level
        WHAT NEXT?     -> adaptive guidance
        """
        self._reflection_count += 1
        self._last_reflection_time = time.time()

        node_readings = cognition.get("node_readings", {})
        reasoning = cognition.get("reasoning", [])

        # Sort nodes by value
        sorted_nodes = sorted(node_readings.items(), key=lambda kv: kv[1], reverse=True)

        # WHAT happened
        ref = Reflection(
            cycle=cognition.get("cycle", self._reflection_count),
            timestamp=time.time(),
            action=cognition.get("action", "HOLD"),
            coherence_gamma=cognition.get("coherence_gamma", 0.0),
            consciousness_psi=cognition.get("consciousness_psi", 0.0),
            vacuum_size=cognition.get("vacuum_size", 0),
        )

        # WHY — dominant drivers
        ref.dominant_nodes = [n for n, _ in sorted_nodes[:3]]
        ref.weakest_nodes = [n for n, _ in sorted_nodes[-3:]]
        ref.reasoning_summary = "; ".join(reasoning[:3]) if reasoning else "no reasoning provided"

        # WHAT WORKED — nodes above 0.7
        ref.strong_signals = [n for n, v in sorted_nodes if v > 0.7]

        # WHAT FAILED — nodes below 0.3
        ref.weak_signals = [n for n, v in sorted_nodes if v < 0.3]
        ref.noise_level = node_readings.get("tiger", 0.5)

        # WHAT NEXT — adaptive guidance
        ref.guidance = self._generate_guidance(ref, node_readings)

        with self._lock:
            self._reflections.append(ref)

        # Publish the reflection
        self._publish_reflection(ref)

        # Detect patterns across history
        insights = self._detect_patterns()
        for insight in insights:
            with self._lock:
                self._insights.append(insight)
            self._publish_insight(insight)

        return ref

    def _generate_guidance(self, ref: Reflection, node_readings: Dict[str, float]) -> List[str]:
        """Generate adaptive guidance based on this reflection."""
        guidance = []

        # Low coherence guidance
        if ref.coherence_gamma < 0.5:
            guidance.append("Coherence critically low -- accumulate longer before next cogitation")

        # Noise guidance
        if ref.noise_level < 0.4:
            guidance.append("Tiger reports high noise -- signal quality degraded, filter harder")

        # Vacuum size guidance
        if ref.vacuum_size < 10:
            guidance.append("Sparse vacuum -- too few signals for confident cognition")
        elif ref.vacuum_size > 5000:
            guidance.append("Oversaturated vacuum -- cogitate more frequently to prevent stale signals")

        # Weak signals guidance
        if len(ref.weak_signals) >= 5:
            guidance.append(f"Majority of nodes underperforming ({len(ref.weak_signals)}/9) -- system may need recalibration")

        # Strong signals guidance
        if len(ref.strong_signals) >= 7:
            guidance.append("Nearly all nodes strong -- high-confidence window, act decisively")

        # Imbalance guidance
        if node_readings:
            values = list(node_readings.values())
            if values:
                spread = max(values) - min(values)
                if spread > 0.6:
                    guidance.append(f"Wide node spread ({spread:.2f}) -- perception is fragmented across dimensions")

        if not guidance:
            guidance.append("Balanced reflection -- no urgent adjustments needed")

        return guidance

    # ================================================================
    # PATTERN DETECTION (across rolling history)
    # ================================================================

    def _detect_patterns(self) -> List[MetacognitiveInsight]:
        """Detect metacognitive patterns across the reflection history."""
        insights = []
        with self._lock:
            refs = list(self._reflections)

        if len(refs) < 3:
            return insights

        # 1. STAGNATION — consecutive HOLDs
        stagnation = self._detect_stagnation(refs)
        if stagnation:
            insights.append(stagnation)

        # 2. OSCILLATION — flip-flopping decisions
        oscillation = self._detect_oscillation(refs)
        if oscillation:
            insights.append(oscillation)

        # 3. COHERENCE DRIFT — trending up or down
        drift = self._detect_coherence_drift(refs)
        if drift:
            insights.append(drift)

        # 4. BLIND SPOTS — nodes consistently underperforming
        blind_spots = self._detect_blind_spots(refs)
        if blind_spots:
            insights.append(blind_spots)

        # 5. DOMINANCE — one node drowning others
        dominance = self._detect_dominance(refs)
        if dominance:
            insights.append(dominance)

        return insights

    def _detect_stagnation(self, refs: List[Reflection]) -> Optional[MetacognitiveInsight]:
        """Detect N consecutive HOLD decisions."""
        recent = refs[-STAGNATION_THRESHOLD:]
        if len(recent) < STAGNATION_THRESHOLD:
            return None
        if all(r.action == "HOLD" for r in recent):
            avg_coh = sum(r.coherence_gamma for r in recent) / len(recent)
            return MetacognitiveInsight(
                pattern="stagnation",
                severity=min(1.0, len(recent) / 10.0),
                description=f"{len(recent)} consecutive HOLD decisions (avg coherence {avg_coh:.3f})",
                guidance="System may be stuck -- consider requesting fresh market data or widening scanner range",
                data={"consecutive_holds": len(recent), "avg_coherence": round(avg_coh, 4)},
                timestamp=time.time(),
            )
        return None

    def _detect_oscillation(self, refs: List[Reflection]) -> Optional[MetacognitiveInsight]:
        """Detect rapid flipping between EXECUTE and HOLD."""
        recent = refs[-OSCILLATION_WINDOW:]
        if len(recent) < 4:
            return None
        actions = [r.action for r in recent]
        flips = sum(1 for i in range(1, len(actions)) if actions[i] != actions[i - 1])
        if flips >= len(actions) - 1:  # Nearly every decision is a flip
            return MetacognitiveInsight(
                pattern="oscillation",
                severity=min(1.0, flips / OSCILLATION_WINDOW),
                description=f"{flips} decision flips in last {len(recent)} cogitations -- unstable",
                guidance="Decision boundary is razor-thin -- widen the neutral zone or accumulate longer",
                data={"flips": flips, "window": len(recent), "actions": actions},
                timestamp=time.time(),
            )
        return None

    def _detect_coherence_drift(self, refs: List[Reflection]) -> Optional[MetacognitiveInsight]:
        """Detect a sustained trend in coherence gamma."""
        window = refs[-COHERENCE_TREND_WINDOW:]
        if len(window) < 5:
            return None

        coherences = [r.coherence_gamma for r in window]
        n = len(coherences)

        # Simple linear regression slope
        x_mean = (n - 1) / 2.0
        y_mean = sum(coherences) / n
        numerator = sum((i - x_mean) * (c - y_mean) for i, c in enumerate(coherences))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        slope = numerator / denominator if denominator > 0 else 0

        if abs(slope) > 0.02:  # Meaningful drift
            direction = "rising" if slope > 0 else "falling"
            severity = min(1.0, abs(slope) * 10)
            return MetacognitiveInsight(
                pattern="coherence_drift",
                severity=severity,
                description=f"Coherence {direction} (slope={slope:.4f}) over last {n} cogitations",
                guidance=(
                    "Coherence improving -- stay the course"
                    if slope > 0 else
                    "Coherence degrading -- investigate signal quality or market regime shift"
                ),
                data={
                    "slope": round(slope, 4),
                    "direction": direction,
                    "start_coherence": round(coherences[0], 4),
                    "end_coherence": round(coherences[-1], 4),
                },
                timestamp=time.time(),
            )
        return None

    def _detect_blind_spots(self, refs: List[Reflection]) -> Optional[MetacognitiveInsight]:
        """Detect nodes that consistently appear in weak_signals."""
        recent = refs[-COHERENCE_TREND_WINDOW:]
        if len(recent) < 5:
            return None

        # Count how many times each node appears in weak signals
        from collections import Counter
        weak_counts = Counter()
        for r in recent:
            for node in r.weak_signals:
                weak_counts[node] += 1

        # Nodes weak in more than half the reflections
        threshold = len(recent) * 0.5
        blind_spots = [(node, count) for node, count in weak_counts.items() if count >= threshold]

        if blind_spots:
            nodes_str = ", ".join(f"{n}({c}/{len(recent)})" for n, c in blind_spots)
            return MetacognitiveInsight(
                pattern="blind_spot",
                severity=min(1.0, len(blind_spots) / 5.0),
                description=f"Persistent blind spots: {nodes_str}",
                guidance="These Auris nodes consistently underperform -- check their input signal sources",
                data={"blind_spots": dict(blind_spots), "window": len(recent)},
                timestamp=time.time(),
            )
        return None

    def _detect_dominance(self, refs: List[Reflection]) -> Optional[MetacognitiveInsight]:
        """Detect one node dominating the top position repeatedly."""
        recent = refs[-COHERENCE_TREND_WINDOW:]
        if len(recent) < 5:
            return None

        from collections import Counter
        top_counts = Counter()
        for r in recent:
            if r.dominant_nodes:
                top_counts[r.dominant_nodes[0]] += 1

        if top_counts:
            dominant_node, count = top_counts.most_common(1)[0]
            ratio = count / len(recent)
            if ratio >= 0.7:  # One node dominates 70%+ of reflections
                return MetacognitiveInsight(
                    pattern="dominance",
                    severity=min(1.0, ratio),
                    description=f"Node '{dominant_node}' dominates {count}/{len(recent)} cogitations ({ratio:.0%})",
                    guidance=f"Over-reliance on {dominant_node} dimension -- other Auris nodes may be starved of signal",
                    data={"dominant_node": dominant_node, "count": count, "ratio": round(ratio, 3)},
                    timestamp=time.time(),
                )
        return None

    # ================================================================
    # PERIODIC REVIEW — deeper reflection every 30 seconds
    # ================================================================

    def _periodic_review(self) -> None:
        """Background thread: periodic deep review and Lambda consciousness update."""
        while self._running:
            time.sleep(30)
            if not self._running:
                break

            try:
                self._deep_review()
            except Exception as e:
                logger.debug(f"Metacognition review error: {e}")

    def _deep_review(self) -> None:
        """Compute metacognitive health metrics and modulate Lambda consciousness."""
        with self._lock:
            refs = list(self._reflections)
            recent_insights = list(self._insights)

        if len(refs) < 3:
            return

        # Compute metacognitive health score
        recent = refs[-10:]
        avg_coherence = sum(r.coherence_gamma for r in recent) / len(recent)
        execute_rate = sum(1 for r in recent if r.action == "EXECUTE") / len(recent)
        avg_vacuum = sum(r.vacuum_size for r in recent) / len(recent)

        # Pattern pressure: how many active insights are warning us?
        active_warnings = sum(1 for i in recent_insights[-10:] if i.severity > 0.5)
        pattern_pressure = min(1.0, active_warnings / 5.0)

        # Metacognitive health: high coherence + moderate execute rate + low pattern pressure
        health = (
            0.4 * avg_coherence
            + 0.2 * min(1.0, execute_rate * 2)  # Reward some execution, not too much
            + 0.2 * (1.0 - pattern_pressure)
            + 0.2 * min(1.0, avg_vacuum / 100.0)  # Reward having enough signals
        )

        # Lambda consciousness update
        if self._lambda_engine is not None:
            try:
                from aureon_lambda_engine import SubsystemReading
                readings = [
                    SubsystemReading("meta_coherence", avg_coherence, 0.9, "coherence"),
                    SubsystemReading("meta_execute_rate", execute_rate, 0.7, "execution"),
                    SubsystemReading("meta_pattern_pressure", 1.0 - pattern_pressure, 0.8, "pressure"),
                    SubsystemReading("meta_health", health, 0.9, "health"),
                ]
                self._lambda_engine.step(readings, volatility=0.03)
            except Exception:
                pass

        # Publish metacognitive health
        self._publish_health(health, avg_coherence, execute_rate, pattern_pressure, len(refs))

    # ================================================================
    # PUBLISHING
    # ================================================================

    def _publish_reflection(self, ref: Reflection) -> None:
        """Publish a single reflection to ThoughtBus."""
        if self._thought_bus is None:
            return
        try:
            from aureon_thought_bus import Thought
            self._thought_bus.publish(Thought(
                source="queen_metacognition",
                topic="queen.metacognition.reflection",
                payload={
                    "cycle": ref.cycle,
                    "action": ref.action,
                    "coherence_gamma": round(ref.coherence_gamma, 4),
                    "consciousness_psi": round(ref.consciousness_psi, 4),
                    "vacuum_size": ref.vacuum_size,
                    "dominant_nodes": ref.dominant_nodes,
                    "weakest_nodes": ref.weakest_nodes,
                    "strong_count": len(ref.strong_signals),
                    "weak_count": len(ref.weak_signals),
                    "noise_level": round(ref.noise_level, 4),
                    "guidance": ref.guidance[:3],
                },
            ))
        except Exception:
            pass

    def _publish_insight(self, insight: MetacognitiveInsight) -> None:
        """Publish a metacognitive pattern insight to ThoughtBus."""
        if self._thought_bus is None:
            return
        try:
            from aureon_thought_bus import Thought
            self._thought_bus.publish(Thought(
                source="queen_metacognition",
                topic=f"queen.metacognition.insight.{insight.pattern}",
                payload={
                    "pattern": insight.pattern,
                    "severity": round(insight.severity, 4),
                    "description": insight.description,
                    "guidance": insight.guidance,
                    "data": insight.data,
                },
            ))
        except Exception:
            pass

    def _publish_health(self, health: float, avg_coherence: float,
                        execute_rate: float, pattern_pressure: float,
                        total_reflections: int) -> None:
        """Publish metacognitive health state."""
        if self._thought_bus is None:
            return
        try:
            from aureon_thought_bus import Thought
            self._thought_bus.publish(Thought(
                source="queen_metacognition",
                topic="queen.metacognition.health",
                payload={
                    "health": round(health, 4),
                    "avg_coherence": round(avg_coherence, 4),
                    "execute_rate": round(execute_rate, 4),
                    "pattern_pressure": round(pattern_pressure, 4),
                    "total_reflections": total_reflections,
                    "reflection_count": self._reflection_count,
                },
            ))
        except Exception:
            pass

    # ================================================================
    # PUBLIC API
    # ================================================================

    def get_state(self) -> Dict[str, Any]:
        """Return current metacognitive state."""
        with self._lock:
            refs = list(self._reflections)
            insights = list(self._insights)

        recent = refs[-10:] if refs else []
        avg_coh = sum(r.coherence_gamma for r in recent) / len(recent) if recent else 0
        execute_rate = sum(1 for r in recent if r.action == "EXECUTE") / len(recent) if recent else 0

        return {
            "total_reflections": self._reflection_count,
            "history_size": len(refs),
            "recent_avg_coherence": round(avg_coh, 4),
            "recent_execute_rate": round(execute_rate, 4),
            "active_insights": len(insights),
            "recent_patterns": [
                {"pattern": i.pattern, "severity": round(i.severity, 3), "description": i.description}
                for i in insights[-5:]
            ],
            "last_reflection": {
                "action": refs[-1].action,
                "coherence": round(refs[-1].coherence_gamma, 4),
                "guidance": refs[-1].guidance[:2],
            } if refs else None,
        }

    def get_insights(self, pattern: str = None) -> List[Dict[str, Any]]:
        """Return metacognitive insights, optionally filtered by pattern type."""
        with self._lock:
            insights = list(self._insights)
        if pattern:
            insights = [i for i in insights if i.pattern == pattern]
        return [
            {
                "pattern": i.pattern,
                "severity": round(i.severity, 3),
                "description": i.description,
                "guidance": i.guidance,
                "timestamp": i.timestamp,
            }
            for i in insights[-20:]
        ]

    def get_reflection_history(self, n: int = 10) -> List[Dict[str, Any]]:
        """Return the last N reflections."""
        with self._lock:
            refs = list(self._reflections)
        return [
            {
                "cycle": r.cycle,
                "action": r.action,
                "coherence_gamma": round(r.coherence_gamma, 4),
                "dominant_nodes": r.dominant_nodes,
                "weak_signals": r.weak_signals,
                "guidance": r.guidance[:2],
            }
            for r in refs[-n:]
        ]


# ============================================================================
# SINGLETON
# ============================================================================

_METACOGNITION: Optional[QueenMetacognition] = None


def get_metacognition() -> QueenMetacognition:
    """Get or create the global QueenMetacognition singleton."""
    global _METACOGNITION
    if _METACOGNITION is None:
        _METACOGNITION = QueenMetacognition()
    return _METACOGNITION
