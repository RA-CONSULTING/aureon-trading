#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   STALLION TRACKER — APACHE WAVE-RIDING PHASE INTELLIGENCE                  ║
║                                                                              ║
║   The Apache on the Great Plains never rushed the wild stallion.            ║
║   He studied the animal, felt every phase of the fight, and knew            ║
║   exactly when it was beginning to tire.  That knowledge IS the edge.       ║
║                                                                              ║
║   PHASES OF THE BREAK:                                                       ║
║                                                                              ║
║   1. ROPING      — Rope is thrown. Position just opened.                    ║
║                    Establishing grip, early seconds of the ride.            ║
║                                                                              ║
║   2. BUCKING     — The stallion fights back.                                ║
║                    Price moving against us. Hold tight. Never let go.       ║
║                    The 250% margin is our endurance — we can outlast it.    ║
║                                                                              ║
║   3. CIRCLING    — The stallion circles, tests our grip.                    ║
║                    Price oscillating near entry. It hasn't submitted        ║
║                    but the fight is no longer escalating. Patience.         ║
║                                                                              ║
║   4. TIRING      — First signs of fatigue.                                  ║
║                    Price has crossed back above entry (long) or below       ║
║                    entry (short). Gross profit is positive but fees         ║
║                    not yet covered. The tide is turning.                    ║
║                                                                              ║
║   5. SUBMITTING  — The stallion begins to yield.                            ║
║                    Net profit after all fees is positive and growing.       ║
║                    Tighten the grip. The Dead Man's Switch is arming.       ║
║                                                                              ║
║   6. BREAKING    — The moment of surrender.                                 ║
║                    Net profit cleared £15. Dead Man's Switch has            ║
║                    FIRED. Floor is LOCKED. Cannot lose from here.          ║
║                                                                              ║
║   7. TAMED       — Fully broken. Ratchet locked in.                         ║
║                    DTP floor has moved UP beyond the initial lock.          ║
║                    Every new peak ratchets the floor higher.                ║
║                    The stallion is ours. Close when the floor is hit.       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
from enum import Enum
from dataclasses import dataclass
from typing import Optional

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

class StallionPhase(Enum):
    ROPING     = "ROPING"
    BUCKING    = "BUCKING"
    CIRCLING   = "CIRCLING"
    TIRING     = "TIRING"
    SUBMITTING = "SUBMITTING"
    BREAKING   = "BREAKING"
    TAMED      = "TAMED"


# How long (seconds) before we leave the initial ROPING window
ROPING_WINDOW_SECS = 30

# Price move within this band (%) from entry = CIRCLING (not yet committing)
CIRCLING_BAND_PCT = 0.10


# One-liner descriptions for each phase
PHASE_DESCRIPTION = {
    StallionPhase.ROPING:     "Just mounted — establishing grip",
    StallionPhase.BUCKING:    "Fighting hard — hold on, the 250% margin is our endurance",
    StallionPhase.CIRCLING:   "Circling and testing — patience, it will tire",
    StallionPhase.TIRING:     "Showing fatigue — price turning our way",
    StallionPhase.SUBMITTING: "Submitting — net profit building, Dead Man arming",
    StallionPhase.BREAKING:   "BREAKING — floor locked, Dead Man fired, cannot lose",
    StallionPhase.TAMED:      "TAMED — profit ratcheted, riding to maximum yield",
}


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE SNAPSHOT
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class StallionSnapshot:
    phase: StallionPhase
    description: str
    hold_seconds: float
    net_pnl: float
    favourable_pct: float      # price move % in our direction (+ve = good)
    dtp_activated: bool
    dtp_floor_gbp: float
    dtp_peak_gbp: float
    dtp_ratchets: int
    wave_capacity_pct: float   # % adverse move before danger zone (from MarginWaveRider)

    def one_line(self) -> str:
        """Compact single-line summary for log output."""
        phase_str = self.phase.value
        dtp_str = ""
        if self.dtp_activated:
            dtp_str = (
                f" | floor=£{self.dtp_floor_gbp:.2f}"
                f" peak=£{self.dtp_peak_gbp:.2f}"
                f" ratchets={self.dtp_ratchets}"
            )
        wave_str = f" | wave_cap={self.wave_capacity_pct:.1f}%" if self.wave_capacity_pct > 0 else ""
        return (
            f"[{phase_str}] net=${self.net_pnl:+.4f} "
            f"move={self.favourable_pct:+.3f}%"
            f"{dtp_str}{wave_str}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# CORE CLASSIFIER
# ═══════════════════════════════════════════════════════════════════════════════

def classify_phase(
    hold_seconds: float,
    entry_price: float,
    current_price: float,
    net_pnl: float,
    trade_side: str,
    dtp_activated: bool = False,
    dtp_trigger_count: int = 0,
    dtp_floor_gbp: float = 0.0,
    dtp_peak_gbp: float = 0.0,
    margin_level: float = 0.0,
    leverage: float = 5.0,
) -> StallionSnapshot:
    """
    Classify the current phase of a margin trade.

    Parameters
    ----------
    hold_seconds:       seconds since position was opened
    entry_price:        price at which the position was opened
    current_price:      latest market price
    net_pnl:            net profit/loss in USD after ALL fees + rollover
    trade_side:         "buy" (long) or "sell" (short)
    dtp_activated:      True if the Dead Man's Switch has fired
    dtp_trigger_count:  number of times the DTP floor was ratcheted upward
    dtp_floor_gbp:      current DTP floor in GBP
    dtp_peak_gbp:       highest net profit seen since DTP activation, in GBP
    margin_level:       current Kraken margin level % (0 if not available)
    leverage:           leverage multiplier (used for wave capacity calc)

    Returns
    -------
    StallionSnapshot with phase, description, and all supporting data
    """
    # Normalise: positive favourable_pct means price moved in our favour
    if entry_price > 0:
        raw_pct = (current_price - entry_price) / entry_price * 100.0
    else:
        raw_pct = 0.0

    favourable_pct = raw_pct if trade_side.lower() == "buy" else -raw_pct

    # Wave capacity (how far price can move against us before danger zone)
    wave_cap = 0.0
    if margin_level > 0 and leverage > 0:
        danger = 110.0
        wave_cap = max(0.0, (margin_level - danger) / (leverage * 100.0) * 100.0)

    # ── PHASE CLASSIFICATION (priority order) ──────────────────────────────

    # Phase 6-7: DTP has fired
    if dtp_activated:
        if dtp_trigger_count > 0:
            phase = StallionPhase.TAMED
        else:
            phase = StallionPhase.BREAKING

    # Phase 1: Very recent entry
    elif hold_seconds < ROPING_WINDOW_SECS:
        phase = StallionPhase.ROPING

    # Phase 5: Net positive — building toward / past activation
    elif net_pnl > 0:
        phase = StallionPhase.SUBMITTING

    # Phase 4: Gross positive (price on our side) but fees not yet covered
    elif favourable_pct > 0:
        phase = StallionPhase.TIRING

    # Phase 3: Price barely moved — testing our patience
    elif abs(favourable_pct) < CIRCLING_BAND_PCT:
        phase = StallionPhase.CIRCLING

    # Phase 2: Price actively against us
    else:
        phase = StallionPhase.BUCKING

    return StallionSnapshot(
        phase=phase,
        description=PHASE_DESCRIPTION[phase],
        hold_seconds=hold_seconds,
        net_pnl=net_pnl,
        favourable_pct=favourable_pct,
        dtp_activated=dtp_activated,
        dtp_floor_gbp=dtp_floor_gbp,
        dtp_peak_gbp=dtp_peak_gbp,
        dtp_ratchets=dtp_trigger_count,
        wave_capacity_pct=wave_cap,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# STANDALONE DEMO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║        STALLION TRACKER — PHASE CLASSIFIER DEMO                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

Simulating a BTC/USD LONG position through all 7 phases:
""")

    ENTRY = 65_000.0
    VOLUME = 500.0 / ENTRY     # $500 position

    # (hold_secs, current_price, net_pnl_usd, dtp_activated, dtp_triggers, dtp_floor, dtp_peak)
    scenarios = [
        (5,   65_000,  -1.30, False, 0, 0.0,  0.0,  "Just entered"),
        (120, 64_500,  -5.20, False, 0, 0.0,  0.0,  "Price dropped hard"),
        (600, 64_980,  -1.50, False, 0, 0.0,  0.0,  "Circling near entry"),
        (900, 65_200,   0.40, False, 0, 0.0,  0.0,  "Price turned our way"),
        (1800,65_500,   3.80, False, 0, 0.0,  0.0,  "Net profit building"),
        (2400,66_200,  19.20, True,  0, 15.0, 19.2, "£15 floor locked in"),
        (3000,67_000,  34.50, True,  3, 33.8, 34.5, "Floor ratcheted 3 times"),
    ]

    width = 16
    print(f"{'Hold':>8}  {'Price':>8}  {'Net P&L':>9}  {'Phase':<12}  Description")
    print("─" * 80)
    for hold, price, pnl, dtp_on, ratchets, floor, peak, label in scenarios:
        snap = classify_phase(
            hold_seconds=hold,
            entry_price=ENTRY,
            current_price=price,
            net_pnl=pnl,
            trade_side="buy",
            dtp_activated=dtp_on,
            dtp_trigger_count=ratchets,
            dtp_floor_gbp=floor,
            dtp_peak_gbp=peak,
            margin_level=300.0,
            leverage=5.0,
        )
        print(
            f"  {hold:>5}s  ${price:>8,}  ${pnl:>+8.2f}  "
            f"{snap.phase.value:<12}  {snap.description[:45]}"
        )
    print("─" * 80)
    print("\nOne-line status examples:")
    for hold, price, pnl, dtp_on, ratchets, floor, peak, label in scenarios[-3:]:
        snap = classify_phase(hold, ENTRY, price, pnl, "buy",
                              dtp_on, ratchets, floor, peak, 300.0, 5.0)
        print(f"  {snap.one_line()}")
