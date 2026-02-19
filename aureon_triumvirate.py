#!/usr/bin/env python3
"""
AUREON TRIUMVIRATE - Three-Pillar Freeway Consensus Engine
=====================================================
"Three minds, one truth. All must agree. The Queen has final say."

The Triumvirate is the governance system for the Aureon trading ecosystem.
All three pillars must independently vote PASS for any action to proceed
(freeway consensus - all lanes must be clear). However, the Queen holds
absolute veto power because she has the most systems connected to her
(11+ subsystems: Temporal Dialer, Harmonic Chain Master, Probability
Nexus, ThoughtBus, Elephant Memory, Queen Neuron, etc.).

FREEWAY CONSENSUS RULES:
  1. All 3 pillars must independently vote PASS for an action to proceed
  2. If ANY pillar votes BLOCK, the action is blocked
  3. The Queen has ABSOLUTE VETO - she can override King+Seer agreement
  4. The King has FINANCIAL VETO - BANKRUPT halts everything
  5. The Seer has COSMIC VETO - BLIND blocks new entries

CONTROL HANDOFF:
  The active controller shifts based on domain:
  - Queen leads: trade execution, position management, entries/exits
  - King leads:  profit-taking decisions, financial health, tax events
  - Seer leads:  risk adjustment, regime detection, cosmic alignment

DATA FLOW (Freeway - all data flows freely between all 3):
  Queen <-> King:  P&L data, cost basis, position values
  Queen <-> Seer:  coherence scores, risk modifiers, vision grades
  King  <-> Seer:  financial health, portfolio snapshots, prophecy

Gary Leckey | February 2026
"""

import time
import logging
from enum import Enum
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# TRIUMVIRATE CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

# Queen's connected systems (why she has veto - most systems report to her)
QUEEN_CONNECTED_SYSTEMS = [
    "temporal_dialer", "temporal_ladder", "timeline_oracle",
    "harmonic_chain_master", "global_harmonic_field",
    "harmonic_signal_chain", "harmonic_fusion",
    "probability_nexus", "elephant_memory",
    "queen_neuron", "thought_bus",
]

# Minimum thresholds for each pillar to independently PASS
QUEEN_PASS_THRESHOLD = 0.45      # Queen confidence must exceed this
KING_PASS_GRADES = ["SOVEREIGN", "PROSPEROUS", "STABLE"]  # King must be healthy
SEER_PASS_GRADES = ["DIVINE_CLARITY", "CLEAR_SIGHT", "PARTIAL_VISION"]  # Seer must see

# Queen veto threshold - below this she blocks regardless
QUEEN_VETO_THRESHOLD = 0.30


class PillarRole(Enum):
    """Which pillar currently has control authority."""
    QUEEN = "QUEEN"   # Trading cognition - entries, exits, position management
    KING = "KING"     # Financial truth - profit-taking, health, tax
    SEER = "SEER"     # Cosmic coherence - risk adjustment, regime detection


class ConsensusAction(Enum):
    """Possible consensus outcomes."""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"
    HALT = "HALT"


class VoteResult(Enum):
    """A pillar's individual vote."""
    PASS = "PASS"
    BLOCK = "BLOCK"
    ABSTAIN = "ABSTAIN"
    VETO = "VETO"  # Only Queen can issue this


# ═══════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class PillarVote:
    """A single pillar's vote with reasoning."""
    pillar: str
    vote: str             # PASS / BLOCK / ABSTAIN / VETO
    score: float          # Numeric confidence/health/vision score
    grade: str            # Human-readable grade
    reason: str           # Why this vote was cast
    data: Dict[str, Any] = field(default_factory=dict)  # Analytical data shared freely
    connected_systems: int = 0  # Number of systems reporting to this pillar


@dataclass
class TriumvirateConsensus:
    """The final consensus of the three pillars."""
    timestamp: float
    action: str                    # ConsensusAction value
    passed: bool                   # Did all 3 pillars agree?
    queen_vetoed: bool             # Did Queen exercise veto?
    active_controller: str         # Who has control right now
    alignment_score: float         # 0.0 to 1.0 how aligned the three are
    queen_vote: PillarVote = None
    king_vote: PillarVote = None
    seer_vote: PillarVote = None
    reason: str = ""               # Human-readable explanation
    data_exchange: Dict[str, Any] = field(default_factory=dict)  # Shared analytical data


@dataclass
class ControlHandoff:
    """Records when control shifts between pillars."""
    timestamp: float
    from_pillar: str
    to_pillar: str
    reason: str
    context: Dict[str, Any] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════
# PILLAR EVALUATORS - Each pillar votes independently
# ═══════════════════════════════════════════════════════════════════════════

class QueenEvaluator:
    """
    Evaluates the Queen's vote. The Queen has the most systems connected
    (11+ subsystems) and therefore holds ABSOLUTE VETO power.
    She evaluates: coherence, harmonic integrity, quantum signals,
    probability nexus validation, profit gates.
    """

    def evaluate(self, queen_confidence: float,
                 queen_data: Dict[str, Any] = None) -> PillarVote:
        """
        The Queen votes based on her trading cognition.

        Args:
            queen_confidence: 0.0-1.0 from Queen's perception systems
            queen_data: Additional data from Queen's 11+ subsystems

        Returns:
            PillarVote with PASS, BLOCK, or VETO
        """
        data = queen_data or {}

        # Extract subsystem data the Queen shares freely
        shared_data = {
            "coherence": data.get("coherence", queen_confidence),
            "harmonic_integrity": data.get("harmonic_integrity", 0.0),
            "quantum_omega": data.get("quantum_omega", 0.0),
            "lambda_stability": data.get("lambda_stability", 1.0),
            "probability_nexus": data.get("probability_nexus", 0.0),
            "profit_gate_active": data.get("profit_gate_active", True),
            "direction": data.get("direction", "NEUTRAL"),
            "decision_score": data.get("decision_score", 0.0),
            "emotional_state": data.get("emotional_state", "VIGILANT"),
            "subsystem_count": len(QUEEN_CONNECTED_SYSTEMS),
        }

        # Queen's vote logic
        if queen_confidence < QUEEN_VETO_THRESHOLD:
            return PillarVote(
                pillar="QUEEN",
                vote=VoteResult.VETO.value,
                score=queen_confidence,
                grade="SOVEREIGN_VETO",
                reason=f"Queen exercises VETO - confidence {queen_confidence:.2f} below {QUEEN_VETO_THRESHOLD}",
                data=shared_data,
                connected_systems=len(QUEEN_CONNECTED_SYSTEMS),
            )

        if queen_confidence < QUEEN_PASS_THRESHOLD:
            return PillarVote(
                pillar="QUEEN",
                vote=VoteResult.BLOCK.value,
                score=queen_confidence,
                grade="INSUFFICIENT",
                reason=f"Queen BLOCKS - confidence {queen_confidence:.2f} below threshold {QUEEN_PASS_THRESHOLD}",
                data=shared_data,
                connected_systems=len(QUEEN_CONNECTED_SYSTEMS),
            )

        # Check subsystem health if provided
        systems_online = data.get("systems_online", len(QUEEN_CONNECTED_SYSTEMS))
        systems_required = data.get("systems_required", 4)
        if systems_online < systems_required:
            return PillarVote(
                pillar="QUEEN",
                vote=VoteResult.BLOCK.value,
                score=queen_confidence,
                grade="SYSTEMS_DOWN",
                reason=f"Queen BLOCKS - only {systems_online}/{systems_required} required systems online",
                data=shared_data,
                connected_systems=systems_online,
            )

        # Grade the Queen's confidence
        if queen_confidence >= 0.85:
            grade = "SUPREME"
        elif queen_confidence >= 0.70:
            grade = "COMMANDING"
        elif queen_confidence >= 0.55:
            grade = "STEADY"
        else:
            grade = "CAUTIOUS"

        return PillarVote(
            pillar="QUEEN",
            vote=VoteResult.PASS.value,
            score=queen_confidence,
            grade=grade,
            reason=f"Queen PASSES - confidence {queen_confidence:.2f}, grade {grade}",
            data=shared_data,
            connected_systems=len(QUEEN_CONNECTED_SYSTEMS),
        )


class KingEvaluator:
    """
    Evaluates the King's vote. The King sees financial truth -
    P&L, cost basis, portfolio health, tax implications.
    He shares all analytical data freely with Queen and Seer.
    """

    HEALTH_SCORES = {
        "SOVEREIGN": 0.90,
        "PROSPEROUS": 0.75,
        "STABLE": 0.55,
        "STRAINED": 0.35,
        "BANKRUPT": 0.10,
    }

    def evaluate(self, king_health: str,
                 king_data: Dict[str, Any] = None) -> PillarVote:
        """
        The King votes based on financial health.

        Args:
            king_health: SOVEREIGN/PROSPEROUS/STABLE/STRAINED/BANKRUPT
            king_data: Analytical data from King's 5 Royal Deciphers

        Returns:
            PillarVote with PASS or BLOCK
        """
        data = king_data or {}
        score = self.HEALTH_SCORES.get(king_health, 0.5)

        # King shares all analytical data freely
        shared_data = {
            "health_grade": king_health,
            "health_score": score,
            "total_realized_pnl": data.get("total_realized_pnl", 0.0),
            "unrealized_pnl": data.get("unrealized_pnl", 0.0),
            "win_rate": data.get("win_rate", 50.0),
            "drawdown_pct": data.get("drawdown_pct", 0.0),
            "max_drawdown_pct": data.get("max_drawdown_pct", 0.0),
            "total_fees": data.get("total_fees", 0.0),
            "equity": data.get("equity", 0.0),
            "cost_basis_available": data.get("cost_basis_available", False),
            "tax_liability": data.get("tax_liability", 0.0),
            "audit_alerts": data.get("audit_alerts", []),
        }

        # King's vote logic
        if king_health == "BANKRUPT":
            return PillarVote(
                pillar="KING",
                vote=VoteResult.BLOCK.value,
                score=score,
                grade="BANKRUPT",
                reason="King BLOCKS - treasury is BANKRUPT, all trading must halt",
                data=shared_data,
                connected_systems=5,  # 5 Royal Deciphers
            )

        if king_health == "STRAINED":
            return PillarVote(
                pillar="KING",
                vote=VoteResult.BLOCK.value,
                score=score,
                grade="STRAINED",
                reason="King BLOCKS - treasury is STRAINED, reduce exposure",
                data=shared_data,
                connected_systems=5,
            )

        # Check for critical audit alerts
        critical_alerts = [a for a in data.get("audit_alerts", [])
                          if isinstance(a, dict) and a.get("severity") == "CRITICAL"]
        if critical_alerts:
            return PillarVote(
                pillar="KING",
                vote=VoteResult.BLOCK.value,
                score=score,
                grade="AUDIT_CRITICAL",
                reason=f"King BLOCKS - {len(critical_alerts)} CRITICAL audit alert(s)",
                data=shared_data,
                connected_systems=5,
            )

        return PillarVote(
            pillar="KING",
            vote=VoteResult.PASS.value,
            score=score,
            grade=king_health,
            reason=f"King PASSES - treasury is {king_health} (score {score:.2f})",
            data=shared_data,
            connected_systems=5,
        )


class SeerEvaluator:
    """
    Evaluates the Seer's vote. The Seer reads cosmic coherence through
    5 Oracles. He shares all vision data freely with Queen and King.
    """

    GRADE_SCORES = {
        "DIVINE_CLARITY": 0.92,
        "CLEAR_SIGHT": 0.77,
        "PARTIAL_VISION": 0.60,
        "FOG": 0.42,
        "BLIND": 0.15,
    }

    def evaluate(self, seer_grade: str, seer_score: float = 0.5,
                 seer_data: Dict[str, Any] = None) -> PillarVote:
        """
        The Seer votes based on cosmic coherence vision.

        Args:
            seer_grade: DIVINE_CLARITY/CLEAR_SIGHT/PARTIAL_VISION/FOG/BLIND
            seer_score: 0.0-1.0 unified score from All-Seeing Eye
            seer_data: Vision data from 5 Oracles

        Returns:
            PillarVote with PASS or BLOCK
        """
        data = seer_data or {}
        score = seer_score if seer_score > 0 else self.GRADE_SCORES.get(seer_grade, 0.5)

        # Seer shares all oracle data freely
        shared_data = {
            "vision_grade": seer_grade,
            "unified_score": score,
            "risk_modifier": data.get("risk_modifier", 1.0),
            "action_bias": data.get("action", "HOLD"),
            "prophecy": data.get("prophecy", ""),
            "gaia_score": data.get("gaia_score", 0.5),
            "cosmos_score": data.get("cosmos_score", 0.5),
            "harmony_score": data.get("harmony_score", 0.5),
            "spirits_score": data.get("spirits_score", 0.5),
            "time_score": data.get("time_score", 0.5),
            "trend": data.get("trend", "STABLE"),
        }

        # Seer's vote logic
        if seer_grade == "BLIND":
            return PillarVote(
                pillar="SEER",
                vote=VoteResult.BLOCK.value,
                score=score,
                grade="BLIND",
                reason="Seer BLOCKS - vision is BLIND, no coherence detected",
                data=shared_data,
                connected_systems=5,  # 5 Oracles
            )

        if seer_grade == "FOG":
            return PillarVote(
                pillar="SEER",
                vote=VoteResult.BLOCK.value,
                score=score,
                grade="FOG",
                reason="Seer BLOCKS - FOG clouds vision, reduce exposure",
                data=shared_data,
                connected_systems=5,
            )

        return PillarVote(
            pillar="SEER",
            vote=VoteResult.PASS.value,
            score=score,
            grade=seer_grade,
            reason=f"Seer PASSES - vision is {seer_grade} (score {score:.2f})",
            data=shared_data,
            connected_systems=5,
        )


# ═══════════════════════════════════════════════════════════════════════════
# CONTROL HANDOFF ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class ControlHandoffEngine:
    """
    Determines which pillar should have active control based on the
    current context. Each pillar has domains where they lead.

    Queen leads: trade execution, entries, exits, position sizing
    King leads:  profit-taking, financial review, tax optimization
    Seer leads:  risk modulation, regime detection, cosmic events
    """

    def __init__(self):
        self._current_controller = PillarRole.QUEEN
        self._handoff_history: List[ControlHandoff] = []

    @property
    def current_controller(self) -> PillarRole:
        return self._current_controller

    def determine_controller(self, queen_vote: PillarVote,
                             king_vote: PillarVote,
                             seer_vote: PillarVote,
                             context: Dict[str, Any] = None) -> Tuple[PillarRole, Optional[ControlHandoff]]:
        """
        Determine which pillar should have active control.

        Returns:
            (new_controller, handoff_record_or_None)
        """
        ctx = context or {}
        previous = self._current_controller

        # RULE 1: Queen always has final authority - if she vetoes, she leads
        if queen_vote.vote == VoteResult.VETO.value:
            new = PillarRole.QUEEN
            reason = "Queen exercised VETO - assuming direct control"

        # RULE 2: King leads during financial distress
        elif king_vote.grade in ["BANKRUPT", "STRAINED", "AUDIT_CRITICAL"]:
            new = PillarRole.KING
            reason = f"King assumes control - financial status: {king_vote.grade}"

        # RULE 3: Seer leads during cosmic events / risk regime changes
        elif seer_vote.grade in ["BLIND", "FOG"]:
            new = PillarRole.SEER
            reason = f"Seer assumes control - vision: {seer_vote.grade}, managing risk"

        # RULE 4: King leads for profit-taking decisions
        elif ctx.get("event") == "PROFIT_TAKING":
            new = PillarRole.KING
            reason = "King leads profit-taking decision"

        # RULE 5: Seer leads for risk modulation
        elif ctx.get("event") == "RISK_ADJUSTMENT":
            new = PillarRole.SEER
            reason = "Seer leads risk adjustment"

        # RULE 6: Seer leads when cosmic vision has significant shift
        elif (seer_vote.data.get("trend") == "DECLINING" and
              seer_vote.score < 0.5):
            new = PillarRole.SEER
            reason = "Seer assumes control - declining cosmic alignment detected"

        # DEFAULT: Queen leads (she has the most systems)
        else:
            new = PillarRole.QUEEN
            reason = "Queen leads - default trading authority"

        # Record handoff if controller changed
        handoff = None
        if new != previous:
            handoff = ControlHandoff(
                timestamp=time.time(),
                from_pillar=previous.value,
                to_pillar=new.value,
                reason=reason,
                context=ctx,
            )
            self._handoff_history.append(handoff)
            logger.info(f"CONTROL HANDOFF: {previous.value} -> {new.value}: {reason}")

        self._current_controller = new
        return new, handoff

    def get_handoff_history(self) -> List[ControlHandoff]:
        return list(self._handoff_history)


# ═══════════════════════════════════════════════════════════════════════════
# THE TRIUMVIRATE ENGINE - Three-Way Freeway Consensus
# ═══════════════════════════════════════════════════════════════════════════

class TriumvirateEngine:
    """
    The Triumvirate Engine enforces freeway consensus:
    ALL three pillars must independently vote PASS for any action.
    The Queen holds absolute veto (most systems connected = 11+).

    FREEWAY RULES:
      Lane 1 (Queen): Must PASS with confidence >= 0.45
      Lane 2 (King):  Must PASS with health in [SOVEREIGN, PROSPEROUS, STABLE]
      Lane 3 (Seer):  Must PASS with vision in [DIVINE_CLARITY, CLEAR_SIGHT, PARTIAL_VISION]

      ALL THREE LANES MUST BE CLEAR.
      Queen can VETO at any time (overrides all other votes).
    """

    def __init__(self):
        self.queen_eval = QueenEvaluator()
        self.king_eval = KingEvaluator()
        self.seer_eval = SeerEvaluator()
        self.handoff_engine = ControlHandoffEngine()
        self._consensus_history: List[TriumvirateConsensus] = []

    def evaluate_consensus(self,
                           queen_confidence: float,
                           king_health: str,
                           seer_grade: str,
                           seer_score: float = 0.5,
                           queen_data: Dict[str, Any] = None,
                           king_data: Dict[str, Any] = None,
                           seer_data: Dict[str, Any] = None,
                           context: Dict[str, Any] = None) -> TriumvirateConsensus:
        """
        Run full freeway consensus evaluation.

        All three pillars vote independently. All must PASS for consensus.
        Queen has absolute veto regardless of other votes.

        Args:
            queen_confidence: 0.0-1.0 from Queen's cognition systems
            king_health: SOVEREIGN/PROSPEROUS/STABLE/STRAINED/BANKRUPT
            seer_grade: DIVINE_CLARITY/CLEAR_SIGHT/PARTIAL_VISION/FOG/BLIND
            seer_score: 0.0-1.0 unified vision score
            queen_data: Queen's subsystem data (shared freely)
            king_data: King's analytical data (shared freely)
            seer_data: Seer's oracle data (shared freely)
            context: Additional context for control handoff

        Returns:
            TriumvirateConsensus with final action and all vote details
        """
        # ─── Phase 1: Each pillar votes independently ───
        queen_vote = self.queen_eval.evaluate(queen_confidence, queen_data)
        king_vote = self.king_eval.evaluate(king_health, king_data)
        seer_vote = self.seer_eval.evaluate(seer_grade, seer_score, seer_data)

        # ─── Phase 2: Free data exchange between all pillars ───
        data_exchange = self._exchange_data(queen_vote, king_vote, seer_vote)

        # ─── Phase 3: Determine active controller ───
        active_controller, handoff = self.handoff_engine.determine_controller(
            queen_vote, king_vote, seer_vote, context
        )

        # ─── Phase 4: Apply freeway consensus rules ───
        queen_vetoed = queen_vote.vote == VoteResult.VETO.value
        all_passed = (
            queen_vote.vote == VoteResult.PASS.value and
            king_vote.vote == VoteResult.PASS.value and
            seer_vote.vote == VoteResult.PASS.value
        )

        # Calculate alignment score (how closely the three agree)
        alignment = self._calculate_alignment(queen_vote, king_vote, seer_vote)

        # Determine final action
        action, reason = self._determine_action(
            queen_vote, king_vote, seer_vote,
            all_passed, queen_vetoed, alignment,
            active_controller
        )

        consensus = TriumvirateConsensus(
            timestamp=time.time(),
            action=action,
            passed=all_passed,
            queen_vetoed=queen_vetoed,
            active_controller=active_controller.value,
            alignment_score=alignment,
            queen_vote=queen_vote,
            king_vote=king_vote,
            seer_vote=seer_vote,
            reason=reason,
            data_exchange=data_exchange,
        )

        self._consensus_history.append(consensus)
        return consensus

    def _exchange_data(self, queen_vote: PillarVote,
                       king_vote: PillarVote,
                       seer_vote: PillarVote) -> Dict[str, Any]:
        """
        Free data exchange - all analytical data flows between all pillars.
        King and Seer need analytical data pulled free.
        """
        return {
            "queen_shares": queen_vote.data,
            "king_shares": king_vote.data,
            "seer_shares": seer_vote.data,
            "queen_systems_count": queen_vote.connected_systems,
            "king_systems_count": king_vote.connected_systems,
            "seer_systems_count": seer_vote.connected_systems,
            "total_systems": (
                queen_vote.connected_systems +
                king_vote.connected_systems +
                seer_vote.connected_systems
            ),
        }

    def _calculate_alignment(self, queen: PillarVote, king: PillarVote,
                             seer: PillarVote) -> float:
        """Calculate how aligned the three pillars are (0.0 to 1.0)."""
        scores = [queen.score, king.score, seer.score]
        avg = sum(scores) / 3.0
        # Variance-based alignment - low variance = high alignment
        variance = sum((s - avg) ** 2 for s in scores) / 3.0
        # Max possible variance is when one is 0 and others are 1: ~0.222
        alignment = max(0.0, 1.0 - (variance / 0.25))
        return round(alignment, 3)

    def _determine_action(self, queen: PillarVote, king: PillarVote,
                          seer: PillarVote, all_passed: bool,
                          queen_vetoed: bool, alignment: float,
                          controller: PillarRole) -> Tuple[str, str]:
        """
        Determine the final consensus action.

        FREEWAY RULE: All three must pass. Queen has absolute veto.
        """
        # ─── Queen VETO overrides everything ───
        if queen_vetoed:
            return ConsensusAction.HALT.value, (
                f"QUEEN VETO - {queen.reason}. "
                f"Queen has {queen.connected_systems} systems and absolute authority."
            )

        # ─── King BANKRUPT halts everything ───
        if king.grade == "BANKRUPT":
            return ConsensusAction.HALT.value, (
                f"KING HALT - Treasury is BANKRUPT. {king.reason}"
            )

        # ─── Freeway consensus: all must pass ───
        if not all_passed:
            # Identify which lanes are blocked
            blockers = []
            if queen.vote != VoteResult.PASS.value:
                blockers.append(f"Queen ({queen.grade})")
            if king.vote != VoteResult.PASS.value:
                blockers.append(f"King ({king.grade})")
            if seer.vote != VoteResult.PASS.value:
                blockers.append(f"Seer ({seer.grade})")

            # If King or Seer block, action depends on severity
            if king.grade == "STRAINED":
                return ConsensusAction.SELL.value, (
                    f"FREEWAY BLOCKED by {', '.join(blockers)}. "
                    f"King is STRAINED - reducing exposure."
                )
            if seer.grade == "BLIND":
                return ConsensusAction.HALT.value, (
                    f"FREEWAY BLOCKED by {', '.join(blockers)}. "
                    f"Seer is BLIND - no coherence detected."
                )
            if seer.grade == "FOG":
                return ConsensusAction.HOLD.value, (
                    f"FREEWAY BLOCKED by {', '.join(blockers)}. "
                    f"Seer sees FOG - holding positions."
                )

            return ConsensusAction.HOLD.value, (
                f"FREEWAY BLOCKED by {', '.join(blockers)}. "
                f"Consensus not reached - holding."
            )

        # ─── ALL THREE PASSED - Determine strength of consensus ───
        avg_score = (queen.score + king.score + seer.score) / 3.0
        min_score = min(queen.score, king.score, seer.score)

        if avg_score >= 0.80 and min_score >= 0.60 and alignment >= 0.85:
            action = ConsensusAction.STRONG_BUY.value
            reason = (
                f"FREEWAY CLEAR - STRONG consensus. "
                f"All pillars aligned (avg={avg_score:.2f}, alignment={alignment:.2f}). "
                f"Controller: {controller.value}"
            )
        elif avg_score >= 0.65 and min_score >= 0.50:
            action = ConsensusAction.BUY.value
            reason = (
                f"FREEWAY CLEAR - Good consensus. "
                f"All pillars agree (avg={avg_score:.2f}). "
                f"Controller: {controller.value}"
            )
        elif avg_score >= 0.50:
            action = ConsensusAction.HOLD.value
            reason = (
                f"FREEWAY CLEAR but cautious. "
                f"Average score {avg_score:.2f} suggests holding. "
                f"Controller: {controller.value}"
            )
        else:
            action = ConsensusAction.SELL.value
            reason = (
                f"FREEWAY CLEAR but weak. "
                f"Average score {avg_score:.2f} suggests reducing exposure. "
                f"Controller: {controller.value}"
            )

        return action, reason

    def get_active_controller(self) -> PillarRole:
        """Get the currently active controller."""
        return self.handoff_engine.current_controller

    def get_consensus_history(self) -> List[TriumvirateConsensus]:
        return list(self._consensus_history)

    def get_handoff_history(self) -> List[ControlHandoff]:
        return self.handoff_engine.get_handoff_history()

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the Triumvirate's state."""
        last = self._consensus_history[-1] if self._consensus_history else None
        return {
            "active_controller": self.handoff_engine.current_controller.value,
            "total_evaluations": len(self._consensus_history),
            "total_handoffs": len(self.handoff_engine.get_handoff_history()),
            "last_action": last.action if last else None,
            "last_passed": last.passed if last else None,
            "last_alignment": last.alignment_score if last else None,
            "queen_systems": len(QUEEN_CONNECTED_SYSTEMS),
        }


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════

_triumvirate_instance: Optional[TriumvirateEngine] = None


def get_triumvirate() -> TriumvirateEngine:
    """Get the singleton Triumvirate engine instance."""
    global _triumvirate_instance
    if _triumvirate_instance is None:
        _triumvirate_instance = TriumvirateEngine()
    return _triumvirate_instance
