#!/usr/bin/env python3
"""
AUREON THE SEER - Ecosystem Integration
=====================================================
"The Seer stands between the Queen and the King,
 whispering what reality truly looks like."

Wires Aureon the Seer into the Aureon trading ecosystem:
  - Feeds live market data to the Seer's Oracles
  - Provides the Seer's vision to the Queen for trading decisions
  - Provides the Seer's vision to the King for risk assessment
  - Generates three-pillar consensus (Queen + King + Seer)
  - Broadcasts visions to the ThoughtBus

THE TRIUMVIRATE:
  Queen (aureon_queen_hive_mind.py) - Trading cognition
  King  (king_accounting.py)        - Financial truth
  Seer  (aureon_seer.py)            - Cosmic coherence

Gary Leckey | February 2026
"""

import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Lazy imports
_seer = None
_king = None


def _get_seer():
    global _seer
    if _seer is None:
        from aureon_seer import get_seer
        _seer = get_seer()
    return _seer


def _get_king():
    global _king
    if _king is None:
        try:
            from king_accounting import get_king
            _king = get_king()
        except ImportError:
            _king = None
    return _king


# ═══════════════════════════════════════════════════════════════════════════
# ECOSYSTEM HOOKS - Called by the trading engine
# ═══════════════════════════════════════════════════════════════════════════

def seer_update_context(positions: Dict = None,
                        ticker_cache: Dict = None,
                        market_data: Dict = None,
                        trade_history: list = None):
    """
    Feed live data to the Seer. Call this every cycle from the ecosystem.
    """
    seer = _get_seer()
    seer.update_context(
        positions=positions,
        ticker_cache=ticker_cache,
        market_data=market_data,
        trade_history=trade_history,
    )


def seer_get_vision() -> Dict[str, Any]:
    """
    Get the Seer's latest vision. If no recent vision exists, take a new reading.
    Returns a dict with score, grade, action, risk_modifier, prophecy.
    """
    seer = _get_seer()
    if seer.latest_vision is None or (time.time() - seer.latest_vision.timestamp > 60):
        seer.see()
    return seer.get_vision_summary()


def seer_get_risk_modifier() -> float:
    """
    Get the Seer's risk modifier for position sizing.
    >1.0 = increase size, <1.0 = decrease size.
    """
    seer = _get_seer()
    if seer.latest_vision:
        return seer.latest_vision.risk_modifier
    return 1.0


def seer_should_trade() -> bool:
    """
    Quick check: should the Queen trade right now?
    Returns False if the Seer's vision is FOG or BLIND.
    """
    seer = _get_seer()
    if seer.latest_vision is None:
        return True  # No vision yet, don't block
    return seer.latest_vision.grade not in ["BLIND"]


# ═══════════════════════════════════════════════════════════════════════════
# THREE-PILLAR CONSENSUS
# ═══════════════════════════════════════════════════════════════════════════

def get_triumvirate_consensus(queen_confidence: float = 0.5) -> Dict[str, Any]:
    """
    Get consensus between all three pillars:
      - The Queen's confidence (passed in from her cognition systems)
      - The King's financial health (queried from his accounting)
      - The Seer's cosmic coherence (from his oracles)

    Returns a consensus dict with action and alignment score.
    """
    seer = _get_seer()

    # Get King's health
    king_health = "STABLE"
    king = _get_king()
    if king:
        try:
            pnl = king.treasury.omega.get_summary()
            wr = pnl.get("win_rate", 50)
            total_pnl = pnl.get("total_realized_pnl", 0)

            if total_pnl > 0 and wr >= 55:
                king_health = "PROSPEROUS"
            elif total_pnl > 0 and wr >= 50:
                king_health = "STABLE"
            elif total_pnl > 0:
                king_health = "STABLE"
            elif total_pnl > -50:
                king_health = "STRAINED"
            else:
                king_health = "BANKRUPT"
        except Exception:
            pass

    # Get Seer's consensus
    consensus = seer.get_consensus(queen_confidence, king_health)

    result = {
        "timestamp": time.time(),
        "consensus_action": consensus.consensus_action,
        "alignment_score": consensus.alignment_score,
        "pillars": {
            "queen": {
                "confidence": queen_confidence,
                "role": "Trading Cognition",
            },
            "king": {
                "health": king_health,
                "role": "Financial Truth",
            },
            "seer": {
                "grade": consensus.seer_grade,
                "role": "Cosmic Coherence",
            },
        },
    }

    # Broadcast to ThoughtBus
    _broadcast("TRIUMVIRATE_CONSENSUS", result)

    return result


# ═══════════════════════════════════════════════════════════════════════════
# STARTUP
# ═══════════════════════════════════════════════════════════════════════════

def start_seer():
    """
    Start Aureon the Seer's autonomous monitoring.
    Call this from the main trading engine startup.
    """
    seer = _get_seer()
    seer.start_autonomous()
    logger.info("Aureon the Seer has awakened. The Third Pillar stands.")
    return seer


def stop_seer():
    """Stop the Seer's autonomous monitoring."""
    seer = _get_seer()
    seer.stop_autonomous()


def print_seer_report():
    """Print the Seer's vision report to stdout."""
    seer = _get_seer()
    if seer.latest_vision is None:
        seer.see()
    print("\n" + seer.generate_report())


# ═══════════════════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _broadcast(event_type: str, data: Dict):
    """Broadcast to ThoughtBus if available."""
    try:
        from aureon_mind_thought_action_hub import ThoughtBus
        bus = ThoughtBus.get_instance() if hasattr(ThoughtBus, "get_instance") else None
        if bus and hasattr(bus, "emit"):
            bus.emit({
                "source": "AureonTheSeer",
                "event": f"SEER_{event_type}",
                "data": data,
                "timestamp": time.time(),
            })
    except (ImportError, Exception):
        pass
