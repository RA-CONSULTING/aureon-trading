#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   DYNAMIC TAKE PROFIT - DEAD MAN'S SWITCH SYSTEM                            ║
║                                                                              ║
║   HOW IT WORKS:                                                              ║
║   1. ACTIVATION: When net profit (after ALL fees) reaches £15,              ║
║      the dead man's switch fires - floor is LOCKED at £15.                  ║
║   2. FLOOR GUARANTEE: Once locked, the trade will NEVER close below         ║
║      the floor. No matter what, profit is protected.                        ║
║   3. TRAILING COUNTDOWN: As profit rises above the floor, a new             ║
║      dead man's switch is set 2% below each new peak.                       ║
║      Peak £20 → floor rises to £19.60. Peak £25 → floor £24.50.            ║
║   4. TRIGGER: When price drops so that net profit touches the floor         ║
║      → CLOSE immediately. Always exits in profit.                           ║
║                                                                              ║
║   The floor can only move UP, never down.                                   ║
║   Once activated, a loss is impossible.                                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import json
import os
import time as _time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

# ── Thought Bus integration (fail-safe) ──────────────────────────────────────
try:
    from aureon.core.aureon_thought_bus import Thought as _Thought
    _HAS_THOUGHT = True
except Exception:
    _Thought = None  # type: ignore
    _HAS_THOUGHT = False

# ═══════════════════════════════════════════════════════════════════════════════
# DEAD MAN'S SWITCH CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

DTP_CONFIG = {
    # Minimum net profit (after fees) to activate the dead man's switch.
    # Once this is hit the floor is LOCKED - the trade can never close below it.
    'activation_threshold': 1.27,           # £1 net profit — lock in any real profit
    'activation_currency': 'GBP',          # Display label for the threshold
    'trailing_distance_pct': 0.02,         # 2% trailing distance below peak profit
    # Conservative fallback fee rate if no live fee data is available.
    # Covers both entry and exit taker fees (round-trip) as a fraction.
    'fallback_fee_rate': 0.005,            # 0.50% round-trip (conservative)
    # GBP/USD exchange rate used to convert the £ threshold to USD for
    # internal calculations.  Update this via set_gbp_usd_rate() or by
    # injecting it into the position constructor.
    'gbp_usd_rate': 1.27,                  # £1 = $1.27 (update as needed)
}


def set_gbp_usd_rate(rate: float) -> None:
    """Update the live GBP/USD conversion rate used by all new DTP instances."""
    if rate > 0:
        DTP_CONFIG['gbp_usd_rate'] = rate


# ═══════════════════════════════════════════════════════════════════════════════
# DEAD MAN'S SWITCH STATE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class DeadManState:
    """Serialisable snapshot of the current dead man's switch state."""
    activated: bool = False
    floor_usd: float = 0.0          # Current locked profit floor in USD
    floor_gbp: float = 0.0          # Floor displayed in GBP
    peak_profit_usd: float = 0.0    # Highest net profit seen since activation
    peak_profit_gbp: float = 0.0
    activation_time: Optional[str] = None
    last_updated: Optional[str] = None
    trigger_count: int = 0          # How many times the floor was ratcheted up

    def to_dict(self) -> Dict:
        return asdict(self)


# ═══════════════════════════════════════════════════════════════════════════════
# DYNAMIC TAKE PROFIT ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class DynamicTakeProfit:
    """
    Dead Man's Switch trailing take-profit system.

    The class operates in the ACCOUNT currency (USD internally) but displays
    thresholds in GBP as that is how the floor was specified.

    Usage
    -----
    dtp = DynamicTakeProfit(
        position_size_usd=500.0,     # notional value of the position
        entry_fee_usd=1.25,          # actual entry fee already paid
        fee_rate=0.0025,             # per-side taker rate for exit fee estimate
        gbp_usd_rate=1.27,           # live FX rate
    )

    On every price update:
        should_exit, reason, state = dtp.update(current_net_profit_usd)

    The caller is responsible for computing net_profit_usd.  Helper method
    calc_net_profit_usd() is provided for convenience.
    """

    def __init__(
        self,
        position_size_usd: float = 0.0,
        entry_fee_usd: float = 0.0,
        fee_rate: float = None,
        gbp_usd_rate: float = None,
        activation_threshold_gbp: float = None,
        trailing_distance_pct: float = None,
        thought_bus: Any = None,
    ):
        self.position_size_usd = position_size_usd
        self.entry_fee_usd = entry_fee_usd
        self.fee_rate = fee_rate if fee_rate is not None else DTP_CONFIG['fallback_fee_rate'] / 2
        self.gbp_usd_rate = gbp_usd_rate if gbp_usd_rate is not None else DTP_CONFIG['gbp_usd_rate']
        self.activation_threshold_gbp = (
            activation_threshold_gbp
            if activation_threshold_gbp is not None
            else DTP_CONFIG['activation_threshold']
        )
        self.trailing_distance_pct = (
            trailing_distance_pct
            if trailing_distance_pct is not None
            else DTP_CONFIG['trailing_distance_pct']
        )

        # Convert the GBP threshold to USD for internal comparisons
        self.activation_threshold_usd = self.activation_threshold_gbp * self.gbp_usd_rate

        self.state = DeadManState()

        # ── Thought Bus (optional, rate-limited) ─────────────────────────
        self._thought_bus = thought_bus
        self._last_publish_at: float = 0.0

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def calc_exit_fee_usd(self, current_price: float, quantity: float) -> float:
        """Estimate exit fee for a position that hasn't closed yet."""
        exit_value = quantity * current_price
        return exit_value * self.fee_rate

    def calc_net_profit_usd(
        self,
        entry_price: float,
        current_price: float,
        quantity: float,
        exit_fee_usd: float = None,
    ) -> float:
        """
        Calculate net profit in USD after entry + exit fees.

        Parameters
        ----------
        entry_price:   price the position was opened at
        current_price: current market price
        quantity:      number of units held
        exit_fee_usd:  if provided, uses this value; otherwise estimates from fee_rate
        """
        gross_pnl = (current_price - entry_price) * quantity
        if exit_fee_usd is None:
            exit_fee_usd = self.calc_exit_fee_usd(current_price, quantity)
        net_profit = gross_pnl - self.entry_fee_usd - exit_fee_usd
        return net_profit

    def to_gbp(self, usd_amount: float) -> float:
        """Convert USD amount to GBP for display."""
        if self.gbp_usd_rate <= 0:
            return usd_amount
        return usd_amount / self.gbp_usd_rate

    # ------------------------------------------------------------------
    # Thought Bus publishing (rate-limited)
    # ------------------------------------------------------------------

    def _publish_dtp_event(self, topic: str, payload: Dict[str, Any]) -> None:
        """Best-effort publish to Thought Bus. Max 1 event per 5 seconds."""
        if self._thought_bus is None or not _HAS_THOUGHT or _Thought is None:
            return
        now = _time.time()
        if now - self._last_publish_at < 5.0:
            return
        self._last_publish_at = now
        try:
            self._thought_bus.publish(_Thought(
                source="dynamic_take_profit",
                topic=topic,
                payload=payload,
                meta={"mode": "dtp"},
            ))
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Core update loop
    # ------------------------------------------------------------------

    def update(self, net_profit_usd: float) -> Tuple[bool, str, DeadManState]:
        """
        Feed the current net profit (after ALL fees, in USD) into the system.

        Returns
        -------
        (should_exit, reason, state)

        should_exit : bool
            True  → close the position NOW (dead man's switch triggered or
                     the position just hit the guaranteed profit floor)
            False → hold
        reason : str
            Human-readable description of the current state.
        state : DeadManState
            A snapshot of the current dead man's switch state.
        """
        now = datetime.now().isoformat()
        self.state.last_updated = now

        net_gbp = self.to_gbp(net_profit_usd)

        # ── PRE-ACTIVATION ─────────────────────────────────────────────
        if not self.state.activated:
            if net_profit_usd >= self.activation_threshold_usd:
                # ACTIVATION: lock in the floor
                self.state.activated = True
                self.state.floor_usd = self.activation_threshold_usd
                self.state.floor_gbp = self.activation_threshold_gbp
                self.state.peak_profit_usd = net_profit_usd
                self.state.peak_profit_gbp = net_gbp
                self.state.activation_time = now

                reason = (
                    f"DEAD MAN ACTIVATED: Net profit £{net_gbp:.2f} reached "
                    f"threshold £{self.activation_threshold_gbp:.2f}. "
                    f"Floor LOCKED at £{self.state.floor_gbp:.2f}. "
                    f"Countdown started - trailing 2% below peak."
                )
                self._publish_dtp_event("dtp.activated", {
                    "floor_gbp": self.state.floor_gbp,
                    "threshold_gbp": self.activation_threshold_gbp,
                    "net_profit_gbp": net_gbp,
                })
                return False, reason, self.state

            # Not yet activated - report progress toward activation
            pct_to_activation = (net_profit_usd / self.activation_threshold_usd * 100) if self.activation_threshold_usd > 0 else 0
            reason = (
                f"Waiting for activation: £{net_gbp:.2f} profit "
                f"({pct_to_activation:.1f}% of £{self.activation_threshold_gbp:.2f} threshold)"
            )
            return False, reason, self.state

        # ── POST-ACTIVATION: RATCHET UP THE FLOOR ─────────────────────
        if net_profit_usd > self.state.peak_profit_usd:
            # New peak reached - ratchet up the dead man's switch
            old_floor_gbp = self.state.floor_gbp
            self.state.peak_profit_usd = net_profit_usd
            self.state.peak_profit_gbp = net_gbp

            new_floor_usd = net_profit_usd * (1.0 - self.trailing_distance_pct)
            new_floor_gbp = self.to_gbp(new_floor_usd)

            # Floor can ONLY move up, never down
            if new_floor_usd > self.state.floor_usd:
                self.state.floor_usd = new_floor_usd
                self.state.floor_gbp = new_floor_gbp
                self.state.trigger_count += 1
                self._publish_dtp_event("dtp.floor_locked", {
                    "floor_gbp": new_floor_gbp,
                    "peak_gbp": self.state.peak_profit_gbp,
                    "ratchet_count": self.state.trigger_count,
                })

        # ── CHECK IF FLOOR IS HIT ──────────────────────────────────────
        if net_profit_usd <= self.state.floor_usd:
            reason = (
                f"DEAD MAN TRIGGERED: Net profit £{net_gbp:.2f} "
                f"hit floor £{self.state.floor_gbp:.2f}. "
                f"CLOSE NOW - locking in £{self.state.floor_gbp:.2f} profit. "
                f"(Peak was £{self.state.peak_profit_gbp:.2f})"
            )
            self._publish_dtp_event("dtp.triggered", {
                "floor_gbp": self.state.floor_gbp,
                "profit_gbp": net_gbp,
                "peak_gbp": self.state.peak_profit_gbp,
            })
            return True, reason, self.state

        # ── HOLDING: above the floor ───────────────────────────────────
        headroom_gbp = net_gbp - self.state.floor_gbp
        reason = (
            f"RUNNING: £{net_gbp:.2f} profit | "
            f"Floor: £{self.state.floor_gbp:.2f} | "
            f"Peak: £{self.state.peak_profit_gbp:.2f} | "
            f"Headroom: £{headroom_gbp:.2f} | "
            f"Ratchets: {self.state.trigger_count}"
        )
        return False, reason, self.state

    # ------------------------------------------------------------------
    # Convenience: full position update (price-based)
    # ------------------------------------------------------------------

    def update_from_price(
        self,
        entry_price: float,
        current_price: float,
        quantity: float,
        exit_fee_usd: float = None,
    ) -> Tuple[bool, str, DeadManState]:
        """
        Convenience wrapper: compute net profit from raw price data and call update().

        Parameters
        ----------
        entry_price:   position entry price
        current_price: latest market price
        quantity:      units held
        exit_fee_usd:  optional override for exit fee (uses fee_rate estimate if omitted)
        """
        net_profit_usd = self.calc_net_profit_usd(
            entry_price, current_price, quantity, exit_fee_usd
        )
        return self.update(net_profit_usd)

    # ------------------------------------------------------------------
    # Status / reporting
    # ------------------------------------------------------------------

    def get_status(self) -> Dict:
        """Return a full status dict for logging/display."""
        return {
            'activated': self.state.activated,
            'floor_gbp': round(self.state.floor_gbp, 4),
            'floor_usd': round(self.state.floor_usd, 4),
            'peak_profit_gbp': round(self.state.peak_profit_gbp, 4),
            'peak_profit_usd': round(self.state.peak_profit_usd, 4),
            'activation_threshold_gbp': self.activation_threshold_gbp,
            'activation_threshold_usd': round(self.activation_threshold_usd, 4),
            'trailing_distance_pct': self.trailing_distance_pct * 100,
            'trigger_count': self.state.trigger_count,
            'activation_time': self.state.activation_time,
            'last_updated': self.state.last_updated,
            'gbp_usd_rate': self.gbp_usd_rate,
        }

    def __repr__(self) -> str:
        if not self.state.activated:
            return (
                f"<DTP not_activated threshold=£{self.activation_threshold_gbp:.2f}>"
            )
        return (
            f"<DTP ACTIVE floor=£{self.state.floor_gbp:.2f} "
            f"peak=£{self.state.peak_profit_gbp:.2f} "
            f"ratchets={self.state.trigger_count}>"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# POSITION-LEVEL FACTORY
# ═══════════════════════════════════════════════════════════════════════════════

def create_dtp_for_position(
    entry_price: float,
    quantity: float,
    fee_rate: float = None,
    gbp_usd_rate: float = None,
    activation_threshold_gbp: float = None,
) -> DynamicTakeProfit:
    """
    Factory: build a DynamicTakeProfit instance for a newly opened position.

    The entry fee is computed immediately from the fee_rate so it is already
    baked into every subsequent net-profit calculation.

    Parameters
    ----------
    entry_price:              price at which the position was opened
    quantity:                 units bought
    fee_rate:                 per-side taker fee as a decimal (e.g. 0.0025 = 0.25%)
    gbp_usd_rate:             live GBP/USD FX rate
    activation_threshold_gbp: override the £15 default if desired
    """
    if fee_rate is None:
        fee_rate = DTP_CONFIG['fallback_fee_rate'] / 2   # per-side

    entry_value = entry_price * quantity
    entry_fee_usd = entry_value * fee_rate

    return DynamicTakeProfit(
        position_size_usd=entry_value,
        entry_fee_usd=entry_fee_usd,
        fee_rate=fee_rate,
        gbp_usd_rate=gbp_usd_rate,
        activation_threshold_gbp=activation_threshold_gbp,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# STANDALONE DEMO / TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║         DYNAMIC TAKE PROFIT - DEAD MAN'S SWITCH DEMO                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    # Simulate a $5,000 BTC position, taker fee 0.25%, GBP/USD = 1.27
    ENTRY = 67_000.0
    QTY = 5_000.0 / ENTRY   # ~0.0746 BTC
    FEE_RATE = 0.0025        # 0.25% per side
    GBP_USD = 1.27

    dtp = create_dtp_for_position(
        entry_price=ENTRY,
        quantity=QTY,
        fee_rate=FEE_RATE,
        gbp_usd_rate=GBP_USD,
        activation_threshold_gbp=15.0,
    )

    print(f"Position: {QTY:.6f} BTC @ ${ENTRY:,.0f}")
    print(f"Notional: ${QTY * ENTRY:,.2f}")
    print(f"Entry fee: ${dtp.entry_fee_usd:.4f}")
    print(f"Activation floor: £{dtp.activation_threshold_gbp:.2f} "
          f"(≈${dtp.activation_threshold_usd:.2f})")
    print(f"Trailing distance: {dtp.trailing_distance_pct * 100:.0f}% below peak\n")

    # Simulate price movement
    price_path = [
        67_000,   # entry
        67_100,   # small rise - not activated yet
        67_400,   # ~£8 profit
        67_800,   # ~£15+ profit → ACTIVATION
        68_000,   # ratchet up
        68_300,   # ratchet up again
        68_500,   # new peak
        68_200,   # dropping back toward floor
        68_000,   # further drop - floor hit?
        67_800,   # if not, continue falling
    ]

    print("─" * 72)
    print(f"{'Price':>10}  {'Net P&L £':>10}  {'Floor £':>10}  {'Status'}")
    print("─" * 72)

    for price in price_path:
        should_exit, reason, state = dtp.update_from_price(ENTRY, price, QTY)
        net_gbp = dtp.to_gbp(dtp.calc_net_profit_usd(ENTRY, price, QTY))
        floor_gbp = state.floor_gbp if state.activated else 0.0
        marker = "  << CLOSE" if should_exit else ""
        print(f"  ${price:>8,}  £{net_gbp:>9.2f}  £{floor_gbp:>9.2f}  {reason[:55]}{marker}")
        if should_exit:
            break

    print("─" * 72)
    print(f"\nFinal DTP Status: {dtp}")
    print(json.dumps(dtp.get_status(), indent=2))
