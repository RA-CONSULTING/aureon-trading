#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   AUTONOMOUS TRADING ORCHESTRATOR                                            ║
║                                                                              ║
║   The central nervous system of the autonomous trading loop.                ║
║   Every cycle flows through here. Every trade is gated here.               ║
║                                                                              ║
║   UNIFIED POSITION REGISTRY (spot + margin work in unity)                   ║
║     - Both spot and margin register active positions here                    ║
║     - gate_pre_trade checks for cross-system conflicts                      ║
║     - A spot BUY on BTC while margin SHORT BTC is open = CONFLICT           ║
║     - Total exposure per asset is tracked across both systems               ║
║                                                                              ║
║   CYCLE SYNC (called every loop iteration)                                  ║
║     1. Update all multiverse shadow rides with latest prices                ║
║     2. Sync learning bridge → Seer, Lyra, ThoughtBus                       ║
║     3. Refresh quick gate flags (Seer + Lyra) every 10 s                   ║
║                                                                              ║
║   PRE-TRADE DYNAMIC DOORS (sizing, not blocking)                           ║
║     0. Cross-system conflict — ONLY hard block (self-hedging)              ║
║     1. Seer door      — grade → sizing factor (0.15x–1.2x)                ║
║     2. Lyra door      — grade → sizing factor (0.15x–1.2x)                ║
║     3. Conviction door — learning bridge → sizing factor (0.15x–1.3x)     ║
║     4. Quadrumvirate  — consensus → sizing factor (Queen VETO = 0.1x)     ║
║     5. Scout bonus    — multiverse nomination (informational)              ║
║     Final sizing = product of all factors, clamped [0.10, 2.0]             ║
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
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

# ── Queen battle-readiness integration (fail-safe import) ─────────────────────
try:
    from aureon.queen.queen_warrior_path import QueenWarriorPath
    _QUEEN_WARRIOR: Optional[QueenWarriorPath] = None
    def _get_queen_warrior() -> Optional[QueenWarriorPath]:
        global _QUEEN_WARRIOR
        if _QUEEN_WARRIOR is None:
            _QUEEN_WARRIOR = QueenWarriorPath()
        return _QUEEN_WARRIOR
except Exception:
    def _get_queen_warrior():  # type: ignore[misc]
        return None

# ── Tuning constants ──────────────────────────────────────────────────────────
CONSENSUS_TTL        = 120   # seconds between full Quadrumvirate calls (expensive)
QUICK_GATE_INTERVAL  =  10   # seconds between lightweight Seer/Lyra checks
MARGIN_LEVEL_TTL     =  30   # seconds between margin level refreshes

# ── Kraken pair prefix/suffix stripping for base asset extraction ─────────────
# Kraken uses prefixes like X/Z and suffixes like USD/ZUSD for their pairs.
# We need to normalize to a base asset (BTC, ETH, etc.) for cross-system matching.
_KRAKEN_QUOTE_SUFFIXES = ('ZUSD', 'USD', 'ZEUR', 'EUR', 'ZGBP', 'GBP', 'USDT')
_KRAKEN_BASE_PREFIXES  = {'XX': '', 'X': '', 'Z': ''}  # XXBT->XBT, XETH->ETH
_KRAKEN_BASE_MAP       = {'XBT': 'BTC', 'XXBT': 'BTC'}  # Kraken calls BTC "XBT"


def normalize_base_asset(pair: str) -> str:
    """
    Extract the base asset from any pair format used across exchanges.

    Examples:
        'XXBTZUSD'  -> 'BTC'   (Kraken margin)
        'XETHZUSD'  -> 'ETH'   (Kraken margin)
        'BTCUSD'    -> 'BTC'   (Alpaca/spot)
        'ETHUSD'    -> 'ETH'   (Alpaca/spot)
        'AAVEUSD'   -> 'AAVE'  (Alpaca/spot)
        'BTC/USD'   -> 'BTC'   (slash format)
        'SOLUSD'    -> 'SOL'
    """
    pair = pair.upper().replace('/', '')

    # Strip quote currency (longest match first)
    base = pair
    for suffix in sorted(_KRAKEN_QUOTE_SUFFIXES, key=len, reverse=True):
        if base.endswith(suffix) and len(base) > len(suffix):
            base = base[:-len(suffix)]
            break

    # Kraken XBT -> BTC
    if base in _KRAKEN_BASE_MAP:
        return _KRAKEN_BASE_MAP[base]

    # Strip Kraken X/XX prefix (XETH -> ETH, but keep AAVE as AAVE)
    if len(base) >= 4 and base.startswith('XX'):
        base = base[2:]
    elif len(base) >= 4 and base.startswith('X') and base[1:] not in ('RP',):
        # X prefix only stripped if result is >= 3 chars (XETH->ETH, not XRP->RP)
        candidate = base[1:]
        if len(candidate) >= 3:
            base = candidate

    return base


@dataclass
class RegisteredPosition:
    """A position registered by either the spot or margin trading system."""
    system:     str    # 'spot' or 'margin'
    pair:       str    # original pair string (e.g. 'BTCUSD' or 'XXBTZUSD')
    base_asset: str    # normalized (e.g. 'BTC')
    side:       str    # 'long' or 'short' (spot buys are always 'long')
    value_usd:  float  # notional value of the position
    exchange:   str    # 'kraken', 'alpaca', 'binance', 'capital'
    reg_time:   float = field(default_factory=time.time)


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

        # ── Unified Position Registry ────────────────────────────────────────
        # Tracks ALL active positions from both spot and margin systems.
        # Key = unique position id (e.g. "spot:BTCUSD" or "margin:XXBTZUSD:long")
        self._positions: Dict[str, RegisteredPosition] = {}

    # ── Position Registry (spot + margin unity) ──────────────────────────────

    def register_position(
        self,
        system:    str,
        pair:      str,
        side:      str,
        value_usd: float = 0.0,
        exchange:  str   = 'kraken',
    ) -> None:
        """
        Register an active position so both spot and margin systems are aware.

        Parameters
        ----------
        system    : 'spot' or 'margin'
        pair      : original pair string (e.g. 'BTCUSD', 'XXBTZUSD')
        side      : 'long', 'short', or 'buy'/'sell' (normalized to long/short)
        value_usd : notional USD value of the position
        exchange  : exchange name
        """
        norm_side = 'long' if side.lower() in ('long', 'buy') else 'short'
        base = normalize_base_asset(pair)
        pos_id = f"{system}:{pair}:{norm_side}"

        self._positions[pos_id] = RegisteredPosition(
            system=system,
            pair=pair,
            base_asset=base,
            side=norm_side,
            value_usd=value_usd,
            exchange=exchange,
        )
        logger.info(
            f"[Orchestrator] Position REGISTERED: {pos_id} "
            f"(base={base}, ${value_usd:.2f})"
        )

    def deregister_position(
        self,
        system: str,
        pair:   str,
        side:   str = '',
    ) -> None:
        """
        Remove a position when it's closed.

        If side is empty, removes all positions matching system+pair.
        """
        if side:
            norm_side = 'long' if side.lower() in ('long', 'buy') else 'short'
            pos_id = f"{system}:{pair}:{norm_side}"
            removed = self._positions.pop(pos_id, None)
            if removed:
                logger.info(f"[Orchestrator] Position DEREGISTERED: {pos_id}")
        else:
            # Remove all sides for this system+pair
            to_remove = [
                k for k in self._positions
                if k.startswith(f"{system}:{pair}:")
            ]
            for k in to_remove:
                self._positions.pop(k, None)
                logger.info(f"[Orchestrator] Position DEREGISTERED: {k}")

    def get_positions_for_asset(self, base_asset: str) -> List[RegisteredPosition]:
        """Get all registered positions (spot + margin) for a given base asset."""
        base = base_asset.upper()
        if base in _KRAKEN_BASE_MAP:
            base = _KRAKEN_BASE_MAP[base]
        return [p for p in self._positions.values() if p.base_asset == base]

    def get_cross_system_conflicts(
        self, pair: str, side: str
    ) -> List[RegisteredPosition]:
        """
        Find positions in the OTHER system that conflict directionally.

        A conflict = same asset, opposite direction, different system.
        e.g. spot LONG BTC conflicts with margin SHORT BTC.
        """
        base = normalize_base_asset(pair)
        norm_side = 'long' if side.lower() in ('long', 'buy') else 'short'
        opposite = 'short' if norm_side == 'long' else 'long'

        conflicts = []
        for pos in self._positions.values():
            if pos.base_asset == base and pos.side == opposite:
                conflicts.append(pos)
        return conflicts

    def get_total_exposure_usd(self, base_asset: str) -> float:
        """Total USD exposure for a base asset across all systems."""
        return sum(p.value_usd for p in self.get_positions_for_asset(base_asset))

    def get_all_positions(self) -> Dict[str, RegisteredPosition]:
        """Return a copy of the full position registry."""
        return dict(self._positions)

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
        Full pre-trade intelligence gate — DYNAMIC DOORS model.

        Instead of hard-blocking trades, each pillar contributes a sizing
        factor (0.1–1.3).  The final sizing_modifier is the product of all
        factors, clamped to [0.10, 2.0].  The Queen controls the weight of
        every trade — nothing is binary except cross-system conflict.

        Returns
        -------
        approved       : bool  — False ONLY for cross-system conflict
        reason         : str   — human-readable explanation
        sizing_modifier: float — product of all dynamic door factors
                                 (apply to position sizing)
        """
        reasons: List[str] = []
        sizing_modifier = 1.0

        # ── 0. Cross-system conflict gate (ONLY hard block) ──────────────
        # Spot and margin must work in unity: buying spot BTC while a margin
        # SHORT BTC is open (or vice versa) creates a self-hedging conflict
        # that wastes capital and fees.
        conflicts = self.get_cross_system_conflicts(pair, side)
        if conflicts:
            base = normalize_base_asset(pair)
            conflict_desc = ', '.join(
                f"{c.system} {c.side.upper()} {c.pair} (${c.value_usd:.2f})"
                for c in conflicts
            )
            self._gates_blocked += 1
            reason = (
                f"CROSS-SYSTEM CONFLICT: {base} — proposed {side.upper()} "
                f"conflicts with active {conflict_desc}. "
                f"Spot and margin must move in the same direction."
            )
            self._last_block_reason = reason
            logger.warning(f"[Orchestrator] Gate BLOCKED: {reason}")
            return False, reason, 1.0

        # Check total exposure per asset — warn if doubling up in same direction
        base = normalize_base_asset(pair)
        existing = self.get_positions_for_asset(base)
        if existing:
            total_exposure = sum(p.value_usd for p in existing)
            systems = set(p.system for p in existing)
            if len(systems) >= 1 and trade_val > 0:
                reasons.append(
                    f"cross-exposure={base}:${total_exposure:.2f}+"
                    f"${trade_val:.2f}({','.join(systems)})"
                )

        # ── 1. Seer dynamic door ─────────────────────────────────────────
        # Grade → sizing factor (never blocks, just adjusts weight)
        _SEER_SIZING = {
            "DIVINE_CLARITY": 1.2, "CLEAR_SIGHT": 1.0,
            "PARTIAL_VISION": 0.7, "FOG": 0.4, "BLIND": 0.15,
        }
        seer_factor = _SEER_SIZING.get(str(self._seer_grade), 1.0 if self._seer_ok else 0.15)
        sizing_modifier *= seer_factor
        reasons.append(f"seer={self._seer_grade}({seer_factor:.2f}x)")

        # ── 2. Lyra dynamic door ─────────────────────────────────────────
        _LYRA_SIZING = {
            "DIVINE_HARMONY": 1.2, "CLEAR_RESONANCE": 1.0,
            "PARTIAL_HARMONY": 0.7, "DISSONANCE": 0.4, "SILENCE": 0.15,
        }
        lyra_factor = _LYRA_SIZING.get(str(self._lyra_grade), 1.0 if self._lyra_ok else 0.15)
        sizing_modifier *= lyra_factor
        reasons.append(f"lyra={self._lyra_grade}({lyra_factor:.2f}x)")

        # ── 3. Multiverse conviction / learning door ─────────────────────
        conviction_factor = 1.0
        bridge = getattr(self.trader, 'learning_bridge', None)
        if bridge is not None:
            try:
                ctx        = bridge.get_pre_trade_context(pair)
                conviction = ctx.get('conviction', 0.5)
                rec        = ctx.get('recommendation', 'HOLD')
                phase      = ctx.get('phase', 'UNKNOWN')

                if rec == 'AVOID':
                    conviction_factor = 0.15
                elif conviction >= 0.85:
                    conviction_factor = 1.3
                elif conviction >= 0.70:
                    conviction_factor = 1.0
                elif conviction >= 0.55:
                    conviction_factor = 0.7
                elif conviction >= 0.40:
                    conviction_factor = 0.4
                else:
                    conviction_factor = 0.15

                sizing_modifier *= conviction_factor
                reasons.append(
                    f"conviction={conviction:.2f}({rec},{conviction_factor:.2f}x)"
                )
            except Exception as e:
                logger.debug(f"[Orchestrator] Conviction check error: {e}")

        # ── 4. Quadrumvirate consensus door (TTL-cached) ─────────────────
        consensus = self._get_consensus()
        if consensus is not None:
            # Extract sizing modifiers from consensus data
            seer_risk  = consensus.get('risk_modifier', 1.0)
            lyra_mult  = consensus.get('position_multiplier', 1.0)
            consensus_sizing = seer_risk * lyra_mult

            if not consensus.get('passed', True):
                queen_veto = consensus.get('queen_vetoed', False)
                # Queen VETO → 0.1x, other consensus fail → alignment-based
                alignment = max(0.10, float(consensus.get('alignment_score', 0) or 0))
                if queen_veto:
                    consensus_sizing *= 0.10
                    reasons.append(f"queen_veto(0.10x)")
                else:
                    consensus_sizing *= alignment
                    cons_reason = consensus.get('reason', 'unknown')
                    reasons.append(f"consensus_low({alignment:.2f}x,{cons_reason})")
            else:
                # Count aligned pillars for log context
                pillars    = consensus.get('pillars', {})
                n_aligned  = sum(
                    1 for d in pillars.values()
                    if d.get('vote') in ('APPROVE', 'GO', True, 'PASS')
                )
                alignment  = consensus.get('alignment_score', 0)
                cons_action = consensus.get('consensus_action', '?')
                reasons.append(
                    f"consensus={n_aligned}/4 | "
                    f"action={cons_action} | "
                    f"alignment={alignment:.2f}"
                )

            sizing_modifier *= max(0.10, consensus_sizing)

            # Seer margin conviction
            margin_conviction = consensus.get('margin_conviction')
            if margin_conviction is not None:
                reasons.append(f"margin_conviction={margin_conviction:.2f}")

        # ── 5. Multiverse scout alignment bonus ──────────────────────────
        mv = getattr(self.trader, 'multiverse', None)
        if mv is not None:
            next_stallion = mv.get_next_stallion()
            if next_stallion and next_stallion == pair:
                reasons.append("SCOUT:NOMINATED")
            remaining = mv.time_remaining_secs()
            if remaining < 300:  # < 5 min left
                reasons.append(f"rotation_in={int(remaining)}s")

        # ── 6. Queen battle readiness (dynamic weight) ───────────────────
        queen_warrior = _get_queen_warrior()
        if queen_warrior is not None:
            try:
                tactical = queen_warrior.assess_tactical_situation(
                    symbol=pair,
                    price=0.0,
                    price_change_pct=0.0,
                    volume=0.0,
                    market_context={},
                )
                br = getattr(tactical, 'battle_readiness', 0.5)
                # Map 0-1 readiness → 0.15x–1.5x sizing
                queen_factor = max(0.15, min(1.5, float(br) * 2.0))
                sizing_modifier *= queen_factor
                reasons.append(f"queen_readiness={br:.2f}({queen_factor:.2f}x)")
            except Exception as e:
                logger.debug(f"[Orchestrator] Queen warrior check: {e}")

        # ── Clamp final sizing to safe range ─────────────────────────────
        sizing_modifier = max(0.10, min(2.0, sizing_modifier))

        # ── All doors evaluated ──────────────────────────────────────────
        self._gates_passed += 1
        reasons.append(f"final_sizing={sizing_modifier:.2f}x")
        final_reason = " | ".join(reasons) if reasons else "all doors clear"
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

        # Unified position registry
        if self._positions:
            spot_count   = sum(1 for p in self._positions.values() if p.system == 'spot')
            margin_count = sum(1 for p in self._positions.values() if p.system == 'margin')
            total_val    = sum(p.value_usd for p in self._positions.values())
            # Group by base asset to show cross-system exposure
            asset_map: Dict[str, List[str]] = {}
            for p in self._positions.values():
                asset_map.setdefault(p.base_asset, []).append(
                    f"{p.system[0].upper()}:{p.side[0].upper()}"
                )
            exposure_str = ' '.join(
                f"{asset}[{'+'.join(dirs)}]" for asset, dirs in asset_map.items()
            )
            lines.append(
                f"  [POSITIONS] spot={spot_count} margin={margin_count} "
                f"total=${total_val:.2f} | {exposure_str}"
            )
        else:
            lines.append("  [POSITIONS] No active positions registered")

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
