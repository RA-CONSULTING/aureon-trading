"""
Shared signal brain for Aureon.

Goal:
- Put the miner-style selectivity / amplification in one place so BOTH:
  - the miner (simulation)
  - the ecosystem (real trading)
use the same logic.

This is intentionally framework-agnostic: you pass in feature dicts and it returns
a decision object (or None).
"""

from __future__ import annotations
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

from dataclasses import dataclass
from typing import Dict, Optional, Sequence
import time
import math
import numpy as np
from aureon_memory_core import memory  # 🧠 MEMORY CORE INTEGRATION

@dataclass(frozen=True)
class BrainParams:
    cascade_factor: float = 10.0         # CASCADE amplification
    gamma_threshold: float = 0.20        # Γ threshold (confidence/coherence)
    psi_percentile: float = 96.3         # top 3.7% == 96.3 percentile cutoff
    min_hold_seconds: int = 50 * 60      # 50 minutes
    kt_target: float = 4.24              # κt target (optional gate)


@dataclass
class BrainDecision:
    symbol: str
    side: str                    # "buy" or "sell"
    score: float                 # cascaded score
    coherence: float             # Γ-like measure
    raw_score: float             # before cascade
    timestamp: float


class AureonBrain:
    def __init__(self, params: Optional[BrainParams] = None):
        self.p = params or BrainParams()

    def cascade(self, base_score: float) -> float:
        """
        Apply CASCADE amplification.
        If in a SURGE WINDOW, amplification is doubled.
        """
        factor = float(self.p.cascade_factor)
        if memory.is_surge_window_active():
            factor *= 2.0  # 🌊 SURGE BOOST
        return float(base_score) * factor

    def coherence(self, features: Dict[str, float]) -> float:
        """
        Replace this with your miner's real coherence / HNC / QVEE coherence measure
        if you have it. For now, we compute a bounded 0..1 confidence proxy.

        Expected keys you can provide in `features` (optional):
          - "rsi" (0..100)
          - "momentum" (any scale)
          - "volatility" (stdev/atr; positive)
          - "trend_strength" (0..1)
        """
        rsi = float(features.get("rsi", 50.0))
        momentum = float(features.get("momentum", 0.0))
        vol = float(features.get("volatility", 1.0))
        trend = float(features.get("trend_strength", 0.5))

        # Momentum signal-to-noise:
        snr = abs(momentum) / max(vol, 1e-9)
        snr_component = 1.0 - math.exp(-snr)          # 0..1

        # RSI distance from neutral 50:
        rsi_component = min(abs(rsi - 50.0) / 50.0, 1.0)  # 0..1

        # Trend already 0..1
        trend_component = max(0.0, min(trend, 1.0))

        coh = 0.45 * snr_component + 0.35 * trend_component + 0.20 * rsi_component
        return float(max(0.0, min(coh, 1.0)))

    def psi_gate(self, candidate_scores: Sequence[float], my_score: float) -> bool:
        if not candidate_scores:
            return True
        cutoff = float(np.percentile(np.asarray(candidate_scores, dtype=float), self.p.psi_percentile))
        return float(my_score) >= cutoff

    def kt_gate(self, cascaded_score: float, coherence: float) -> bool:
        expected = float(cascaded_score) * float(coherence)
        return expected >= float(self.p.kt_target)

    def decide(
        self,
        symbol: str,
        base_score: float,
        features: Dict[str, float],
        population_scores: Sequence[float],
        now: Optional[float] = None,
    ) -> Optional[BrainDecision]:
        now = time.time() if now is None else float(now)

        raw = float(base_score)
        casc = self.cascade(raw)
        coh = self.coherence(features)

        if coh < self.p.gamma_threshold:
            return None
        if not self.psi_gate(population_scores, casc):
            return None
        if self.p.kt_target is not None and not self.kt_gate(casc, coh):
            return None

        side = "buy" if casc > 0 else "sell"
        return BrainDecision(
            symbol=symbol,
            side=side,
            score=casc,
            coherence=coh,
            raw_score=raw,
            timestamp=now,
        )

    def can_exit(self, entry_timestamp: float, now: Optional[float] = None) -> bool:
        now = time.time() if now is None else float(now)
        return (now - float(entry_timestamp)) >= float(self.p.min_hold_seconds)
