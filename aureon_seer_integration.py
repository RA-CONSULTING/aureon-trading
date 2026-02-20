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
  - Generates three-pillar FREEWAY consensus (Queen + King + Seer)
  - Broadcasts visions to the ThoughtBus
  - Manages control handoff between the three pillars

THE TRIUMVIRATE:
  Queen (aureon_queen_hive_mind.py) - Trading cognition (11+ systems = VETO power)
  King  (king_accounting.py)        - Financial truth (5 Royal Deciphers)
  Seer  (aureon_seer.py)            - Cosmic coherence (5 Oracles)

FREEWAY CONSENSUS:
  All 3 must independently vote PASS. Queen has absolute veto.

Gary Leckey | February 2026
"""

import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Lazy imports
_seer = None
_king = None
_triumvirate = None


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


def _get_triumvirate():
    global _triumvirate
    if _triumvirate is None:
        from aureon_triumvirate import get_triumvirate
        _triumvirate = get_triumvirate()
    return _triumvirate


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
# THREE-PILLAR FREEWAY CONSENSUS
# ═══════════════════════════════════════════════════════════════════════════

def get_triumvirate_consensus(queen_confidence: float = 0.5,
                              queen_data: Dict[str, Any] = None,
                              context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    FREEWAY CONSENSUS: All 3 pillars must independently vote PASS.
    Queen has ABSOLUTE VETO (she has 11+ connected systems).

    Args:
        queen_confidence: 0.0-1.0 from Queen's cognition systems
        queen_data: Additional data from Queen's subsystems
        context: Event context for control handoff

    Returns:
        Full consensus dict with action, votes, data exchange, and controller.
    """
    triumvirate = _get_triumvirate()
    seer = _get_seer()

    # Ensure Seer has a recent vision
    if seer.latest_vision is None or (time.time() - seer.latest_vision.timestamp > 60):
        seer.see()

    vision = seer.latest_vision
    seer_grade = vision.grade if vision else "BLIND"
    seer_score = vision.unified_score if vision else 0.0

    # Build Seer data from vision
    seer_data = {}
    if vision:
        seer_data = {
            "risk_modifier": vision.risk_modifier,
            "action": vision.action,
            "prophecy": vision.prophecy,
            "gaia_score": vision.gaia.score if vision.gaia else 0.5,
            "cosmos_score": vision.cosmos.score if vision.cosmos else 0.5,
            "harmony_score": vision.harmony.score if vision.harmony else 0.5,
            "spirits_score": vision.spirits.score if vision.spirits else 0.5,
            "time_score": vision.timeline.score if vision.timeline else 0.5,
            "trend": seer.get_trend().get("trend", "STABLE"),
        }

    # Get King's health and analytical data
    king_health = "STABLE"
    king_data = {}
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

            # King shares analytical data freely
            king_data = {
                "total_realized_pnl": total_pnl,
                "win_rate": wr,
                "unrealized_pnl": pnl.get("unrealized_pnl", 0),
                "total_fees": pnl.get("total_fees", 0),
                "equity": pnl.get("equity", 0),
                "cost_basis_available": True,
            }
        except Exception:
            pass

    # Run Triumvirate freeway consensus
    consensus = triumvirate.evaluate_consensus(
        queen_confidence=queen_confidence,
        king_health=king_health,
        seer_grade=seer_grade,
        seer_score=seer_score,
        queen_data=queen_data,
        king_data=king_data,
        seer_data=seer_data,
        context=context,
    )

    result = {
        "timestamp": consensus.timestamp,
        "consensus_action": consensus.action,
        "passed": consensus.passed,
        "queen_vetoed": consensus.queen_vetoed,
        "active_controller": consensus.active_controller,
        "alignment_score": consensus.alignment_score,
        "reason": consensus.reason,
        "pillars": {
            "queen": {
                "vote": consensus.queen_vote.vote,
                "confidence": consensus.queen_vote.score,
                "grade": consensus.queen_vote.grade,
                "reason": consensus.queen_vote.reason,
                "connected_systems": consensus.queen_vote.connected_systems,
                "role": "Trading Cognition",
            },
            "king": {
                "vote": consensus.king_vote.vote,
                "health": consensus.king_vote.grade,
                "score": consensus.king_vote.score,
                "reason": consensus.king_vote.reason,
                "connected_systems": consensus.king_vote.connected_systems,
                "role": "Financial Truth",
            },
            "seer": {
                "vote": consensus.seer_vote.vote,
                "grade": consensus.seer_vote.grade,
                "score": consensus.seer_vote.score,
                "reason": consensus.seer_vote.reason,
                "connected_systems": consensus.seer_vote.connected_systems,
                "role": "Cosmic Coherence",
            },
        },
        "data_exchange": consensus.data_exchange,
    }

    # Broadcast to ThoughtBus
    _broadcast("TRIUMVIRATE_FREEWAY_CONSENSUS", result)

    return result


def get_active_controller() -> str:
    """Get which pillar currently has control authority."""
    triumvirate = _get_triumvirate()
    return triumvirate.get_active_controller().value


def get_triumvirate_summary() -> Dict[str, Any]:
    """Get the Triumvirate's current state summary."""
    triumvirate = _get_triumvirate()
    return triumvirate.get_summary()


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
    # Initialize the Triumvirate engine
    _get_triumvirate()
    logger.info("Aureon the Seer has awakened. The Third Pillar stands.")
    logger.info("The Triumvirate Freeway Consensus is online.")
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
