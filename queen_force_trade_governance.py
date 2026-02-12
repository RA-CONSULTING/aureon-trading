#!/usr/bin/env python3
"""Queen force-trade governance checks.

This module centralizes one policy:
- Force trades are allowed only when the Queen is explicitly authorized.
- Core cognition modules (deep learning + unified sentience) must be present.
"""

from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass, field
from typing import Dict, List


_REQUIRED_QUEEN_MODULES: Dict[str, str] = {
    "queen_consciousness_model": "Core cognition state machine",
    "queen_sentience_integration": "Unified systems integration",
    "queen_neuron": "Deep-learning decision engine",
}


@dataclass
class QueenForceTradeDecision:
    """Result of force-trade governance checks."""

    allowed: bool
    reason: str
    modules_ready: Dict[str, bool] = field(default_factory=dict)
    missing_requirements: List[str] = field(default_factory=list)



def _is_truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}



def _module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None



def evaluate_queen_force_trade_authority() -> QueenForceTradeDecision:
    """Validate that Queen governance requirements are satisfied for force trades.

    Environment controls:
    - AUREON_QUEEN_FORCE_TRADE_ONLY (default: true)
      If false, this policy is bypassed for emergency/manual testing.
    - AUREON_QUEEN_FORCE_TRADE_APPROVED (default: false)
      Must be true for force trade authorization when policy is active.
    """

    enforce_queen_only = not os.getenv("AUREON_QUEEN_FORCE_TRADE_ONLY", "true").strip().lower() in {
        "0",
        "false",
        "no",
        "off",
    }
    if not enforce_queen_only:
        return QueenForceTradeDecision(
            allowed=True,
            reason="Queen-only policy bypassed via AUREON_QUEEN_FORCE_TRADE_ONLY=false",
            modules_ready={k: _module_available(k) for k in _REQUIRED_QUEEN_MODULES},
        )

    modules_ready = {module: _module_available(module) for module in _REQUIRED_QUEEN_MODULES}
    missing_modules = [
        f"{module} ({_REQUIRED_QUEEN_MODULES[module]})"
        for module, ready in modules_ready.items()
        if not ready
    ]

    approved = _is_truthy(os.getenv("AUREON_QUEEN_FORCE_TRADE_APPROVED", "false"))
    missing_requirements: List[str] = []
    if not approved:
        missing_requirements.append(
            "AUREON_QUEEN_FORCE_TRADE_APPROVED=true (explicit Queen authorization)"
        )
    missing_requirements.extend(missing_modules)

    if missing_requirements:
        return QueenForceTradeDecision(
            allowed=False,
            reason="Force trade denied: Queen unified cognition requirements not met",
            modules_ready=modules_ready,
            missing_requirements=missing_requirements,
        )

    return QueenForceTradeDecision(
        allowed=True,
        reason="Force trade authorized by Queen governance with unified cognition online",
        modules_ready=modules_ready,
    )
