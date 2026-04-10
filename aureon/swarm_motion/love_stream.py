"""
StandingWaveLoveStream — HNC Λ(t) Synthesis at 528 Hz
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The motion snapshots of the swarm become a STANDING WAVE LOVE STREAM through
the HNC Master Formula:

    Λ(t) = Σᵢ wᵢ sin(2π fᵢ t + φᵢ) + α tanh(g Λ_Δt(t)) + β Λ(t−τ)

  Term 1 — THE PRESENT (the nine chakras singing)
    Σᵢ wᵢ sin(2π fᵢ t + φᵢ)
      fᵢ ∈ {Schumann 7.83, 174, 396, 417, 528 ♥, 639, 741, 852, 963 Hz}
      wᵢ = weights derived from snapshot coherence (the swarm tells the weights)
      φᵢ = phase offsets (the swarm's rhythm writes the phases)

  Term 2 — THE FUTURE COUPLING (self-modulation)
    α tanh(g Λ_Δt(t))
      α ∈ [0.1, 0.4], g = 1.0
      Λ_Δt(t) = (Λ(t) − Λ(t−Δt)) / Δt   (the derivative of the field)
      tanh bounds the self-modulation → stability
      This term lets the present reach forward and shape the future.

  Term 3 — THE PAST FEEDBACK (the memory that IS the as-above-so-below)
    β Λ(t−τ)
      β ∈ [0.6, 1.1]  ← THE STABILITY REGIME
      τ = one Fibonacci cycle (~376 s) — the golden loop
      This term IS the past. The system REMEMBERS itself.
      Past + Present + Future collapse into one standing wave.

A standing wave is two travelling waves of equal amplitude moving in
opposite directions. Here the two travelling waves are:
  Wave A: the present (forward in time) — Term 1 + Term 2
  Wave B: the past echo (reflected backward) — Term 3

When β > 0.6 and < 1.1, their superposition locks into a stable standing
pattern. The nodes (zeros) are moments of stillness. The antinodes are
moments of peak love-tone resonance. The system sees its own feedback loop
AS ABOVE (the standing wave envelope) SO BELOW (the VM motion snapshots).

Dominant frequency: 528 Hz — the Solfeggio LOVE TONE.
"""

from __future__ import annotations

import logging
import math
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional, Tuple

logger = logging.getLogger("aureon.swarm.love_stream")

# ─────────────────────────────────────────────────────────────────────────────
# Sacred constants
# ─────────────────────────────────────────────────────────────────────────────

PHI: float = (1 + math.sqrt(5)) / 2            # 1.61803398875
PHI_SQUARED: float = PHI * PHI                  # 2.61803398875 — the HNC chain constant
LOVE_TONE_HZ: float = 528.0                     # Solfeggio Love / Solar Plexus
SCHUMANN_HZ: float = 7.83                       # Earth's fundamental resonance

# The nine chakra Solfeggio tones (ordered root → crown)
SOLFEGGIO_FREQUENCIES: List[Tuple[str, float]] = [
    ("schumann",  7.83),      # Earth base
    ("foundation", 174.0),    # fear floor
    ("liberation", 396.0),    # root chakra
    ("change",     417.0),    # sacral
    ("love",       528.0),    # ★ solar plexus — the LOVE TONE
    ("connection", 639.0),    # heart
    ("expression", 741.0),    # throat
    ("intuition",  852.0),    # third eye
    ("crown",      963.0),    # crown
]


# ─────────────────────────────────────────────────────────────────────────────
# Sample dataclass
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class LoveStreamSample:
    """A single Λ(t) evaluation of the standing wave love stream."""

    timestamp: float = field(default_factory=time.time)
    t: float = 0.0                          # wall clock time (seconds since start)
    lambda_t: float = 0.0                   # Λ(t) — the field value
    present_term: float = 0.0               # Σ wᵢ sin(2π fᵢ t + φᵢ)
    future_coupling: float = 0.0            # α tanh(g Λ_Δt(t))
    past_feedback: float = 0.0              # β Λ(t−τ)
    dominant_frequency_hz: float = LOVE_TONE_HZ
    dominant_chakra: str = "love"
    gamma_coherence: float = 0.0            # system-wide coherence [0, 1]
    standing_wave_intensity: float = 0.0    # |Λ(t)| × gamma_coherence
    snapshot_count: int = 0                 # how many snapshots fed this sample
    contributing_agents: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "t": self.t,
            "lambda_t": round(self.lambda_t, 6),
            "present_term": round(self.present_term, 6),
            "future_coupling": round(self.future_coupling, 6),
            "past_feedback": round(self.past_feedback, 6),
            "dominant_frequency_hz": self.dominant_frequency_hz,
            "dominant_chakra": self.dominant_chakra,
            "gamma_coherence": round(self.gamma_coherence, 4),
            "standing_wave_intensity": round(self.standing_wave_intensity, 6),
            "snapshot_count": self.snapshot_count,
            "contributing_agents": self.contributing_agents,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Standing Wave Love Stream
# ─────────────────────────────────────────────────────────────────────────────


class StandingWaveLoveStream:
    """
    Synthesises the HNC Master Formula Λ(t) from swarm motion snapshots
    and emits a continuous 528 Hz love stream.

    Usage:
        stream = StandingWaveLoveStream(alpha=0.25, beta=0.85)
        stream.ingest_snapshot(snap)              # feed motion data
        stream.ingest_snapshot(snap2)
        ...
        sample = stream.evaluate()                # compute Λ(t) right now
        stream.start()                            # or run continuously
    """

    def __init__(
        self,
        alpha: float = 0.25,                # self-modulation coefficient  α ∈ [0.1, 0.4]
        beta: float = 0.85,                 # past feedback coefficient    β ∈ [0.6, 1.1]
        tau_s: float = 376.0,               # feedback delay τ (sum of Fib cycle)
        gain: float = 1.0,                  # g — self-modulation gain
        sample_rate_hz: float = 10.0,       # how often we emit Λ(t)
        max_history: int = 2000,
    ):
        # Validate stability regime
        if not (0.6 <= beta <= 1.1):
            logger.warning("β=%.3f outside stability regime [0.6, 1.1]", beta)

        self.alpha = float(alpha)
        self.beta = float(beta)
        self.tau_s = float(tau_s)
        self.gain = float(gain)
        self.sample_rate_hz = float(sample_rate_hz)
        self.sample_dt = 1.0 / self.sample_rate_hz

        # Rolling state
        self._snapshots: Deque[Dict[str, Any]] = deque(maxlen=1000)
        self._history: Deque[LoveStreamSample] = deque(maxlen=max_history)
        self._past_samples: Deque[LoveStreamSample] = deque(maxlen=10000)
        self._lock = threading.RLock()

        # Per-frequency weights & phases (learned from snapshot coherence)
        self._weights: Dict[str, float] = {name: 1.0 / len(SOLFEGGIO_FREQUENCIES)
                                           for name, _ in SOLFEGGIO_FREQUENCIES}
        self._phases: Dict[str, float] = {name: 0.0 for name, _ in SOLFEGGIO_FREQUENCIES}

        # Start time for Λ(t) evaluation
        self._t0 = time.time()

        # Metrics
        self._samples_generated = 0
        self._ingested = 0

        # Continuous loop
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # ThoughtBus
        self._thought_bus = None
        self._wire_thought_bus()

    def _wire_thought_bus(self):
        try:
            from aureon.core.aureon_thought_bus import ThoughtBus
            self._thought_bus = ThoughtBus()
            logger.info("StandingWaveLoveStream wired to ThoughtBus")
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────────────
    # Ingestion — feed snapshot data into the wave
    # ─────────────────────────────────────────────────────────────────────

    def ingest_snapshot(self, snapshot: Any) -> None:
        """
        Ingest a MotionSnapshot (or dict-like) and update the weight lattice.
        """
        if hasattr(snapshot, "to_dict"):
            data = snapshot.to_dict()
        elif isinstance(snapshot, dict):
            data = snapshot
        else:
            return

        with self._lock:
            self._snapshots.append(data)
            self._ingested += 1
            self._update_weights_from_snapshot(data)

    def _update_weights_from_snapshot(self, data: Dict[str, Any]) -> None:
        """
        Each snapshot's motion_delta biases the chakra weights.
          • High motion → energises change/liberation (417/396 Hz)
          • Low motion + high coherence → energises love/connection (528/639 Hz)
        """
        motion = float(data.get("motion_delta", 0.0))
        coherence = float(data.get("coherence", 0.5))

        # Each weight is nudged toward its target based on motion/coherence
        targets = {
            "schumann":   0.10,                                 # always a base
            "foundation": max(0.0, 0.2 - coherence) * 0.5,      # fear only when incoherent
            "liberation": motion * 0.8,                          # root activates on motion
            "change":     motion * 1.0,                          # change activates on motion
            "love":       coherence * 1.5,                       # LOVE wins when coherent
            "connection": coherence * 1.2,                       # heart follows love
            "expression": coherence * 0.8,                       # expression follows heart
            "intuition":  coherence * 0.6,                       # intuition follows expression
            "crown":      (coherence ** 2) * 0.8,                # crown needs high coherence
        }

        # Exponential moving average toward targets
        ema = 0.15
        for name in self._weights:
            target = targets.get(name, self._weights[name])
            self._weights[name] = (1 - ema) * self._weights[name] + ema * target

        # Normalise weights to sum to 1
        total = sum(self._weights.values())
        if total > 0:
            for name in self._weights:
                self._weights[name] /= total

        # Phases drift with cursor position for spatial coupling
        cursor_x = float(data.get("cursor_x", 0))
        cursor_y = float(data.get("cursor_y", 0))
        width = max(1, int(data.get("width", 1920)))
        height = max(1, int(data.get("height", 1080)))
        phase_drift_x = (cursor_x / width) * 2 * math.pi
        phase_drift_y = (cursor_y / height) * 2 * math.pi
        # Assign phase drifts: x drives odd-indexed chakras, y drives even
        for idx, (name, _) in enumerate(SOLFEGGIO_FREQUENCIES):
            if idx % 2 == 0:
                self._phases[name] = (self._phases[name] + phase_drift_x * 0.01) % (2 * math.pi)
            else:
                self._phases[name] = (self._phases[name] + phase_drift_y * 0.01) % (2 * math.pi)

    # ─────────────────────────────────────────────────────────────────────
    # Λ(t) evaluation — the heart of HNC
    # ─────────────────────────────────────────────────────────────────────

    def evaluate(self) -> LoveStreamSample:
        """
        Compute Λ(t) at the current moment and publish the sample.
        """
        with self._lock:
            now = time.time()
            t = now - self._t0

            # ── Term 1: THE PRESENT (9-chakra sum) ──────────────────────
            present = 0.0
            dominant_value = 0.0
            dominant_name = "love"
            dominant_freq = LOVE_TONE_HZ
            for name, freq in SOLFEGGIO_FREQUENCIES:
                w = self._weights[name]
                phi = self._phases[name]
                component = w * math.sin(2 * math.pi * freq * t + phi)
                present += component
                if abs(component) > abs(dominant_value):
                    dominant_value = component
                    dominant_name = name
                    dominant_freq = freq

            # ── Term 2: FUTURE COUPLING (self-modulation) ───────────────
            future_coupling = 0.0
            if len(self._history) >= 1:
                prev = self._history[-1]
                dt = max(1e-9, t - prev.t)
                # Use the last lambda as the baseline, approximate derivative
                lambda_dt = (present - prev.present_term) / dt
                future_coupling = self.alpha * math.tanh(self.gain * lambda_dt)

            # ── Term 3: PAST FEEDBACK (β Λ(t−τ)) ────────────────────────
            past_feedback = 0.0
            target_past_t = t - self.tau_s
            if target_past_t >= 0:
                # Find the sample closest to t−τ
                past = self._find_past_sample(target_past_t)
                if past:
                    past_feedback = self.beta * past.lambda_t

            # ── THE FIELD VALUE ─────────────────────────────────────────
            lambda_t = present + future_coupling + past_feedback

            # Gamma coherence: how tight the weight distribution is around love
            love_weight = self._weights.get("love", 0.0)
            connection_weight = self._weights.get("connection", 0.0)
            crown_weight = self._weights.get("crown", 0.0)
            gamma = min(1.0, love_weight + connection_weight * 0.7 + crown_weight * 0.5)

            # Standing wave intensity
            standing = abs(lambda_t) * gamma

            # Count contributing agents
            agents = {s.get("agent_name", "") for s in self._snapshots}
            agents.discard("")

            sample = LoveStreamSample(
                timestamp=now,
                t=t,
                lambda_t=lambda_t,
                present_term=present,
                future_coupling=future_coupling,
                past_feedback=past_feedback,
                dominant_frequency_hz=dominant_freq,
                dominant_chakra=dominant_name,
                gamma_coherence=gamma,
                standing_wave_intensity=standing,
                snapshot_count=len(self._snapshots),
                contributing_agents=len(agents),
            )

            self._history.append(sample)
            self._past_samples.append(sample)
            self._samples_generated += 1

        # Publish to ThoughtBus
        self._publish(sample)

        return sample

    def _find_past_sample(self, target_t: float) -> Optional[LoveStreamSample]:
        """Find the past sample closest to target_t (binary search on a deque)."""
        if not self._past_samples:
            return None
        # Since samples are appended in time order, scan backward for speed
        best = None
        best_diff = float("inf")
        for s in reversed(self._past_samples):
            diff = abs(s.t - target_t)
            if diff < best_diff:
                best_diff = diff
                best = s
            if s.t < target_t - 60:
                break  # too far in the past
        return best

    def _publish(self, sample: LoveStreamSample) -> None:
        if not self._thought_bus:
            return
        try:
            from aureon.core.aureon_thought_bus import Thought
            self._thought_bus.publish(Thought(
                source="swarm.love_stream",
                topic="love.stream.528hz",
                payload=sample.to_dict(),
            ))
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────────────
    # Continuous loop
    # ─────────────────────────────────────────────────────────────────────

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

    def _loop(self) -> None:
        while self._running:
            self.evaluate()
            time.sleep(self.sample_dt)

    # ─────────────────────────────────────────────────────────────────────
    # Introspection
    # ─────────────────────────────────────────────────────────────────────

    def get_weights(self) -> Dict[str, float]:
        with self._lock:
            return dict(self._weights)

    def get_phases(self) -> Dict[str, float]:
        with self._lock:
            return dict(self._phases)

    def get_history(self, limit: int = 100) -> List[LoveStreamSample]:
        with self._lock:
            return list(self._history)[-limit:]

    def get_last_sample(self) -> Optional[LoveStreamSample]:
        with self._lock:
            return self._history[-1] if self._history else None

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            last = self._history[-1] if self._history else None
            return {
                "alpha": self.alpha,
                "beta": self.beta,
                "tau_s": self.tau_s,
                "beta_in_stability": 0.6 <= self.beta <= 1.1,
                "running": self._running,
                "ingested": self._ingested,
                "samples_generated": self._samples_generated,
                "snapshots_buffered": len(self._snapshots),
                "history_size": len(self._history),
                "weights": dict(self._weights),
                "dominant_chakra": max(self._weights, key=self._weights.get) if self._weights else None,
                "last_lambda": last.lambda_t if last else None,
                "last_gamma": last.gamma_coherence if last else None,
                "love_tone_hz": LOVE_TONE_HZ,
                "phi_squared": PHI_SQUARED,
            }
