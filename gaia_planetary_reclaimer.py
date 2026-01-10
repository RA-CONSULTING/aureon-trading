#!/usr/bin/env python3
"""
🌍🛰️ GAIA PLANETARY RECLAIMER
Central signal unifier for the Queen intelligence system.

This module is the primary convergence point for lattice, mycelium, HNC,
market pulse, and immune signals. All subsystems should feed signals here
so the Queen can act with unified coherence.
"""

from __future__ import annotations

import time
from typing import Dict, Optional, Any


class GaiaPlanetaryReclaimer:
    """Unifies subsystem signals into coherence and risk bias outputs."""

    def __init__(self) -> None:
        self.last_update = 0.0
        self.sources: Dict[str, Dict[str, Any]] = {}
        self.state: Dict[str, Any] = {
            "coherence": 0.5,
            "risk_bias": 0.0,
            "updated_at": time.time(),
            "sources": {},
        }

    def update_signal(
        self,
        source: str,
        coherence: Optional[float] = None,
        risk_bias: Optional[float] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update signal inputs from a subsystem."""
        data = {
            "timestamp": time.time(),
            "coherence": coherence,
            "risk_bias": risk_bias,
            "payload": payload or {},
        }
        self.sources[source] = data
        self._recalculate()

    def _recalculate(self) -> None:
        """Recalculate unified coherence/risk bias from all sources."""
        coherences = [s["coherence"] for s in self.sources.values() if s.get("coherence") is not None]
        biases = [s["risk_bias"] for s in self.sources.values() if s.get("risk_bias") is not None]

        if coherences:
            coherence = sum(coherences) / len(coherences)
        else:
            coherence = 0.5

        if biases:
            risk_bias = sum(biases) / len(biases)
        else:
            risk_bias = 0.0

        self.state = {
            "coherence": max(0.0, min(1.0, float(coherence))),
            "risk_bias": max(-0.5, min(0.5, float(risk_bias))),
            "updated_at": time.time(),
            "sources": {
                key: {
                    "coherence": value.get("coherence"),
                    "risk_bias": value.get("risk_bias"),
                    "timestamp": value.get("timestamp"),
                }
                for key, value in self.sources.items()
            },
        }
        self.last_update = self.state["updated_at"]

    def get_state(self) -> Dict[str, Any]:
        """Return the latest unified state."""
        return dict(self.state)

    def get_metrics(self) -> Dict[str, Any]:
        """Alias for state retrieval."""
        return self.get_state()
