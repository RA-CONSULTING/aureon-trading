#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   AUTONOMOUS TRADING ORCHESTRATOR                                            ║
║                                                                              ║
║   The central nervous system of the autonomous trading loop.                ║
║   Every cycle flows through here. Every trade is gated here.               ║
║                                                                              ║
║   CYCLE SYNC (called every loop iteration)                                  ║
║     1. Update all multiverse shadow rides with latest prices                ║
║     2. Sync learning bridge → Seer, Lyra, ThoughtBus                       ║
║     3. Refresh quick gate flags (Seer + Lyra) every 10 s                   ║
║                                                                              ║
║   PRE-TRADE GATE (called before any shadow is promoted to real capital)     ║
║     1. Seer gate      — BLIND vision = no trade                             ║
║     2. Lyra gate      — SILENCE resonance = no trade                       ║
║     3. Conviction gate — persistent BUCKING in shadow = caution            ║
║     4. Quadrumvirate  — all 4 pillars must vote PASS (TTL-cached)          ║
║        Queen (veto), King (finance), Seer (cosmos), Lyra (emotion)         ║
║     5. Size modifier  — Seer risk × Lyra position multiplier applied       ║
║                                                                              ║
║   STATUS REPORT (printed every 30 cycles alongside print_status())         ║
║     Seer grade, Lyra grade, consensus result, sizing modifier,              ║
║     multiverse scout energy, herd coherence, next stallion                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import time
import logging
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

# ── Tuning constants ──────────────────────────────────────────────────────────
CONSENSUS_TTL        = 120   # seconds between full Quadrumvirate calls (expensive)
QUICK_GATE_INTERVAL  =  10   # seconds between lightweight Seer/Lyra checks
MARGIN_LEVEL_TTL     =  30   # seconds between margin level refreshes


class AutonomousOrchestrator:
    """
    Wires ALL Queen's systems into one coherent pre-trade gate and
    per-cycle intelligence update.

    Usage
    -----
    # In trader __init__:
    self.orchestrator = AutonomousOrchestrator(self)

    # Top of every trading cycle:
    self.orchestrator.cycle_sync()

    # Before promoting a validated shadow to real capital:
    approved, reason, sizing = self.orchestrator.gate_pre_trade(pair, side)
    if not approved:
        logger.info(f"Trade blocked: {reason}")
        return None

    # In print_status():
    for line in self.orchestrator.status_report():
        print(line)
    """

    def __init__(self, trader):
        self.trader = trader

        # Cached consensus state
        self._consensus:        Optional[Dict] = None
        self._consensus_time:   float = 0.0

        # Cached quick gate flags
        self._seer_ok:          bool  = True
        self._lyra_ok:          bool  = True
        self._seer_grade:       str   = 'UNKNOWN'
        self._lyra_grade:       str   = 'UNKNOWN'
        self._quick_gate_time:  float = 0.0

        # Cached margin level (updated from trade balance on cycle_sync)
        self._margin_level:     float = 0.0
        self._margin_level_time: float = 0.0

        # Trade gate counters (for status display)
        self._gates_passed:     int = 0
        self._gates_blocked:    int = 0
        self._last_block_reason: str = ''

    # ── Per-cycle sync ────────────────────────────────────────────────────────

    def cycle_sync(self) -> None:
        """
        Called at the TOP of every trading cycle.
        Updates all intelligence systems with the latest market state.
        Does NOT make expensive API calls on every iteration — uses TTLs.
        """
        now = time.time()

        # 1. Refresh margin level (every 30s)
        if now - self._margin_level_time >= MARGIN_LEVEL_TTL:
            self._margin_level = self._fetch_margin_level()
            self._margin_level_time = now

        # 2. Build price map from trader's margin_pairs (no API call needed)
        price_map = self._build_price_map()

        # 3. Update multiverse shadow rides
        if getattr(self.trader, 'multiverse', None) is not None:
            try:
                self.trader.multiverse.update(price_map, self._margin_level)
            except Exception as e:
                logger.debug(f"[Orchestrator] Multiverse update error: {e}")

        # 4. Sync learning bridge → Seer, Lyra, ThoughtBus
        if getattr(self.trader, 'learning_bridge', None) is not None:
            try:
                self.trader.learning_bridge.sync()
            except Exception as e:
                logger.debug(f"[Orchestrator] Learning bridge sync error: {e}")

        # 5. Refresh quick gates (every 10s — lightweight, no heavy APIs)
        if now - self._quick_gate_time >= QUICK_GATE_INTERVAL:
            self._refresh_quick_gates()
            self._quick_gate_time = now

    # ── Pre-trade gate ────────────────────────────────────────────────────────

    def gate_pre_trade(
        self,
        pair:      str,
        side:      str,
        trade_val: float = 0.0,
    ) -> Tuple[bool, str, float]:
        """
        Full pre-trade intelligence gate.

        Returns
        -------
        approved       : bool  — True = all pillars aligned, deploy capital
        reason         : str   — human-readable explanation
        sizing_modifier: float — Seer_risk × Lyra_position_multiplier
                                 (apply to position sizing)
        """
        reasons   = []
        sizing_modifier = 1.0

        # ── 1. Seer quick gate ────────────────────────────────────────────
        if not self._seer_ok:
            self._gates_blocked += 1
            reason = f"Seer BLIND (grade={self._seer_grade}) — cosmic conditions unfavorable"
            self._last_block_reason = reason
            logger.info(f"[Orchestrator] Gate BLOCKED: {reason}")
            return False, reason, 1.0

        # ── 2. Lyra quick gate ────────────────────────────────────────────
        if not self._lyra_ok:
            self._gates_blocked += 1
            reason = f"Lyra SILENCE (grade={self._lyra_grade}) — emotional resonance too low"
            self._last_block_reason = reason
            logger.info(f"[Orchestrator] Gate BLOCKED: {reason}")
            return False, reason, 1.0

        # ── 3. Multiverse conviction / learning gate ──────────────────────
        bridge = getattr(self.trader, 'learning_bridge', None)
        if bridge is not None:
            try:
                ctx        = bridge.get_pre_trade_context(pair)
                conviction = ctx.get('conviction', 0.5)
                rec        = ctx.get('recommendation', 'HOLD')
                phase      = ctx.get('phase', 'UNKNOWN')

                if rec == 'AVOID':
                    self._gates_blocked += 1
                    reason = (
                        f"Learning bridge AVOID: {pair} phase={phase} "
                        f"conviction={conviction:.2f} (BUCKING 45+ min)"
                    )
                    self._last_block_reason = reason
                    logger.info(f"[Orchestrator] Gate BLOCKED: {reason}")
                    return False, reason, 1.0

                if conviction >= 0.70:
                    reasons.append(f"conviction={conviction:.2f}({rec})")
                elif conviction >= 0.55:
                    reasons.append(f"conviction={conviction:.2f}(neutral)")
                else:
                    reasons.append(f"conviction={conviction:.2f}(LOW)")
            except Exception as e:
                logger.debug(f"[Orchestrator] Conviction check error: {e}")

        # ── 4. Quadrumvirate consensus (TTL-cached, expensive) ────────────
        consensus = self._get_consensus()
        if consensus is not None:
            if not consensus.get('passed', True):
                queen_veto = consensus.get('queen_vetoed', False)
                prefix     = "Queen VETO" if queen_veto else "Quadrumvirate"
                cons_reason = consensus.get('reason', 'unknown')
                self._gates_blocked += 1
                reason = f"{prefix}: consensus FAILED — {cons_reason}"
                self._last_block_reason = reason
                logger.info(f"[Orchestrator] Gate BLOCKED: {reason}")
                return False, reason, 1.0

            # Extract sizing modifiers from consensus data
            seer_risk  = consensus.get('risk_modifier', 1.0)
            lyra_mult  = consensus.get('position_multiplier', 1.0)
            sizing_modifier = seer_risk * lyra_mult

            # Count aligned pillars for log context
            pillars    = consensus.get('pillars', {})
            n_aligned  = sum(
                1 for d in pillars.values()
                if d.get('vote') in ('APPROVE', 'GO', True, 'PASS')
            )
            alignment  = consensus.get('alignment_score', 0)
            cons_action = consensus.get('consensus_action', '?')
            reasons.append(
                f"consensus={n_aligned}/4 pillars | "
                f"action={cons_action} | "
                f"alignment={alignment:.2f} | "
                f"sizing={sizing_modifier:.2f}x"
            )

            # Seer margin conviction
            margin_conviction = consensus.get('margin_conviction')
            if margin_conviction is not None:
                reasons.append(f"margin_conviction={margin_conviction:.2f}")

        # ── 5. Multiverse scout alignment bonus ───────────────────────────
        mv = getattr(self.trader, 'multiverse', None)
        if mv is not None:
            next_stallion = mv.get_next_stallion()
            if next_stallion and next_stallion == pair:
                reasons.append("SCOUT:NOMINATED")
            remaining = mv.time_remaining_secs()
            if remaining < 300:  # < 5 min left
                reasons.append(f"rotation_in={int(remaining)}s")

        # ── All gates passed ──────────────────────────────────────────────
        self._gates_passed += 1
        final_reason = " | ".join(reasons) if reasons else "all gates clear"
        logger.info(
            f"[Orchestrator] Gate APPROVED: {pair} {side.upper()} — {final_reason}"
        )
        return True, final_reason, sizing_modifier

    # ── Status display ────────────────────────────────────────────────────────

    def status_report(self) -> List[str]:
        """Printable status lines for all autonomous intelligence systems."""
        lines = []
        total = self._gates_passed + self._gates_blocked
        pass_rate = (self._gates_passed / total * 100) if total else 0

        # Seer + Lyra quick gate
        seer_icon = '+' if self._seer_ok else 'BLIND'
        lyra_icon = '+' if self._lyra_ok else 'SILENCE'
        lines.append(
            f"  [ORCHESTRATOR] Seer={seer_icon}({self._seer_grade}) | "
            f"Lyra={lyra_icon}({self._lyra_grade}) | "
            f"Gates: {self._gates_passed} passed / {self._gates_blocked} blocked "
            f"({pass_rate:.0f}% pass)"
        )

        # Quadrumvirate consensus
        if self._consensus:
            c   = self._consensus
            age = int(time.time() - self._consensus_time)
            lines.append(
                f"  [QUADRUMVIRATE] {'PASS' if c.get('passed') else 'FAIL'} | "
                f"action={c.get('consensus_action','?')} | "
                f"alignment={c.get('alignment_score',0):.2f} | "
                f"sizing={c.get('combined_sizing_modifier',1.0):.2f}x | "
                f"age={age}s"
            )
            pillars = c.get('pillars', {})
            votes   = ' | '.join(
                f"{name}:{data.get('vote','?')}"
                for name, data in pillars.items()
            )
            if votes:
                lines.append(f"  [QUADRUMVIRATE] Votes: {votes}")
        else:
            lines.append("  [QUADRUMVIRATE] Not yet consulted this session")

        # Last block reason
        if self._last_block_reason:
            lines.append(f"  [ORCHESTRATOR] Last block: {self._last_block_reason}")

        return lines

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _build_price_map(self) -> Dict[str, float]:
        """Extract latest prices from trader's margin_pairs (no API call)."""
        price_map = {}
        margin_pairs = getattr(self.trader, 'margin_pairs', {})
        for pair, info in margin_pairs.items():
            price = getattr(info, 'last_price', 0)
            if price and price > 0:
                price_map[pair] = float(price)
        # Also try market data cache
        market = getattr(self.trader, 'market', None)
        if market and hasattr(market, 'prices'):
            for sym, price in (market.prices or {}).items():
                if price and price > 0:
                    price_map[sym] = float(price)
        return price_map

    def _fetch_margin_level(self) -> float:
        """Fetch current margin level from trade balance (cached by TTL)."""
        try:
            tb = self.trader.client.get_trade_balance()
            return float(tb.get('margin_level', 0) or 0)
        except Exception:
            return self._margin_level   # return last known

    def _refresh_quick_gates(self) -> None:
        """
        Lightweight Seer and Lyra gate checks.
        Does NOT call the full consensus — just the fast should_trade() gate.
        """
        try:
            from aureon_seer_integration import seer_should_trade, seer_get_vision
            self._seer_ok    = seer_should_trade()
            vision           = seer_get_vision() or {}
            self._seer_grade = vision.get('grade', 'UNKNOWN')
        except Exception:
            self._seer_ok    = True
            self._seer_grade = 'UNAVAILABLE'

        try:
            from aureon_lyra_integration import lyra_should_trade, lyra_get_resonance
            self._lyra_ok    = lyra_should_trade()
            resonance        = lyra_get_resonance() or {}
            self._lyra_grade = resonance.get('grade', 'UNKNOWN')
        except Exception:
            self._lyra_ok    = True
            self._lyra_grade = 'UNAVAILABLE'

        logger.debug(
            f"[Orchestrator] Quick gates: "
            f"Seer={self._seer_grade}({'OK' if self._seer_ok else 'BLOCKED'}) "
            f"Lyra={self._lyra_grade}({'OK' if self._lyra_ok else 'BLOCKED'})"
        )

    def _get_consensus(self) -> Optional[Dict]:
        """
        Get the Quadrumvirate four-pillar consensus.
        Cached for CONSENSUS_TTL seconds — the full call is expensive
        (touches Seer's 5 Oracles, Lyra's 6 Chambers, Queen, King).
        """
        now = time.time()
        if (self._consensus is not None and
                now - self._consensus_time < CONSENSUS_TTL):
            return self._consensus

        try:
            from aureon_seer_integration import get_triumvirate_consensus
            logger.info("[Orchestrator] Running full Quadrumvirate consensus...")
            result = get_triumvirate_consensus()
            if result:
                self._consensus      = result
                self._consensus_time = now
                logger.info(
                    f"[Quadrumvirate] passed={result.get('passed')} | "
                    f"action={result.get('consensus_action')} | "
                    f"alignment={result.get('alignment_score', 0):.2f} | "
                    f"sizing={result.get('combined_sizing_modifier', 1.0):.2f}x"
                )
        except Exception as e:
            logger.debug(f"[Orchestrator] Consensus unavailable: {e}")
            # Don't wipe the cached result on error — use stale data
        return self._consensus
