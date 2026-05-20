#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   STALLION MULTIVERSE — PARALLEL SHADOW RIDE INTELLIGENCE                   ║
║                                                                              ║
║   The Apache did not chase one horse blindly.                               ║
║   He studied the entire herd — reading which stallions                      ║
║   were tiring, which were still wild, which he would                        ║
║   rope next when the current ride was done.                                 ║
║                                                                              ║
║   REAL RIDE LIMIT: 1 hour. Then rotate to the next stallion.               ║
║                                                                              ║
║   SHADOW RIDES (up to 10 concurrent):                                       ║
║                                                                              ║
║   LEARNING shadows — map phase transitions and timing patterns.             ║
║     Each shadow records every phase change, its duration, and               ║
║     final outcome. This feeds the algorithm's learning loop.                ║
║                                                                              ║
║   SCOUTING shadows — pre-select the next stallion to ride.                 ║
║     Ranked by readiness score. The top scout becomes the next               ║
║     real ride when the current hour expires.                                ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from aureon.core.aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    from aureon.utils.stallion_tracker import classify_phase, StallionPhase
    _STALLION_AVAILABLE = True
except ImportError:
    _STALLION_AVAILABLE = False
    classify_phase = None

try:
    from aureon.trading.dynamic_take_profit import DynamicTakeProfit, DTP_CONFIG
    _DTP_AVAILABLE = True
except ImportError:
    _DTP_AVAILABLE = False
    DynamicTakeProfit = None
    DTP_CONFIG = {
        'activation_threshold': 15.0,
        'trailing_distance_pct': 0.02,
        'gbp_usd_rate': 1.27,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

MULTIVERSE_CONFIG = {
    # Hard limit on how long to hold one real position before rotating
    'real_ride_limit_secs': 3600,   # 1 hour

    # Maximum simultaneous shadow rides
    'max_shadows': 10,

    # How many of those shadows are reserved for learning vs scouting
    'learning_slots': 5,
    'scouting_slots': 5,

    # A scout must have run for at least this long before it can be
    # nominated as the next real ride — gives it time to show its character
    'min_scout_age_secs': 120,

    # Phase readiness scores for scout ranking (higher = closer to being tamed)
    'phase_scores': {
        'TAMED':      7,
        'BREAKING':   6,
        'SUBMITTING': 5,
        'TIRING':     4,
        'CIRCLING':   3,
        'ROPING':     2,
        'BUCKING':    1,
        'UNKNOWN':    0,
    },

    # Approximate round-trip taker fee used for shadow P&L estimates
    'shadow_fee_rate': 0.0026,
}


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class PhaseTransition:
    """Records a single phase change in a shadow ride for learning purposes."""
    timestamp:    float
    from_phase:   str
    to_phase:     str
    net_pnl:      float
    hold_seconds: float
    price:        float


@dataclass
class ShadowRide:
    """
    A paper/shadow position tracking a candidate pair without real capital.
    Updated every monitoring cycle via update_price().
    """
    pair:                 str
    entry_price:          float
    entry_time:           float   # unix timestamp when shadow was "entered"
    hypothetical_volume:  float   # paper size in base currency
    leverage:             int
    purpose:              str     # 'learning' or 'scouting'

    # Mutable state — refreshed each cycle
    current_price: float = 0.0
    gross_pnl:     float = 0.0
    net_pnl:       float = 0.0
    phase:         str   = 'ROPING'
    last_phase:    str   = 'ROPING'
    scout_score:   float = 0.0

    # DTP state (populated when DTP module is available)
    dtp:           object = field(default=None, repr=False)
    dtp_activated: bool   = False
    dtp_floor_gbp: float  = 0.0
    dtp_peak_gbp:  float  = 0.0
    dtp_ratchets:  int    = 0
    dtp_triggered: bool   = False

    # Learning data — phase transition log
    phase_transitions: List[PhaseTransition] = field(default_factory=list)

    def hold_seconds(self) -> float:
        return time.time() - self.entry_time

    def update_price(self, price: float) -> None:
        """Recompute P&L from a new market price and advance DTP state."""
        if price <= 0:
            return
        self.current_price = price
        fee_rate   = MULTIVERSE_CONFIG['shadow_fee_rate']
        self.gross_pnl = (price - self.entry_price) * self.hypothetical_volume
        open_fee   = self.entry_price * self.hypothetical_volume * (fee_rate / 2)
        close_fee  = price            * self.hypothetical_volume * (fee_rate / 2)
        self.net_pnl = self.gross_pnl - open_fee - close_fee

        if self.dtp is not None:
            try:
                triggered, _reason, state = self.dtp.update(self.net_pnl)
                self.dtp_triggered = triggered
                self.dtp_activated = state.activated
                self.dtp_floor_gbp = state.floor_gbp
                self.dtp_peak_gbp  = state.peak_profit_gbp
                self.dtp_ratchets  = state.trigger_count
            except Exception:
                pass

    def refresh_phase(self, margin_level: float = 0.0) -> str:
        """Classify current stallion phase and record any transition."""
        if not _STALLION_AVAILABLE or classify_phase is None:
            return self.phase
        try:
            snap = classify_phase(
                hold_seconds      = self.hold_seconds(),
                entry_price       = self.entry_price,
                current_price     = self.current_price,
                net_pnl           = self.net_pnl,
                trade_side        = 'buy',
                dtp_activated     = self.dtp_activated,
                dtp_trigger_count = self.dtp_ratchets,
                dtp_floor_gbp     = self.dtp_floor_gbp,
                dtp_peak_gbp      = self.dtp_peak_gbp,
                margin_level      = margin_level,
                leverage          = float(self.leverage),
            )
            new_phase = snap.phase.value
        except Exception:
            new_phase = self.phase

        if new_phase != self.last_phase:
            self.phase_transitions.append(PhaseTransition(
                timestamp    = time.time(),
                from_phase   = self.last_phase,
                to_phase     = new_phase,
                net_pnl      = self.net_pnl,
                hold_seconds = self.hold_seconds(),
                price        = self.current_price,
            ))
            self.last_phase = new_phase

        self.phase = new_phase
        return new_phase

    def compute_scout_score(self) -> float:
        """Rank this shadow as a next-stallion candidate (higher = better)."""
        base = MULTIVERSE_CONFIG['phase_scores'].get(self.phase, 0)

        # Bonus: DTP has already fired or activated
        dtp_bonus = 3 if self.dtp_triggered else (2 if self.dtp_activated else 0)

        # Bonus: positive net P&L, capped at +3
        profit_bonus = min(self.net_pnl / 5.0, 3.0) if self.net_pnl > 0 else 0.0

        # Penalty: still BUCKING/CIRCLING after 45 minutes — losing patience
        age_penalty = 2.0 if (
            self.hold_seconds() > 2700 and self.phase in ('BUCKING', 'CIRCLING')
        ) else 0.0

        self.scout_score = base + dtp_bonus + profit_bonus - age_penalty
        return self.scout_score

    def learning_summary(self) -> dict:
        """Extract a learning record for algorithm improvement."""
        return {
            'pair':          self.pair,
            'entry_price':   self.entry_price,
            'final_price':   self.current_price,
            'final_net_pnl': self.net_pnl,
            'final_phase':   self.phase,
            'hold_seconds':  self.hold_seconds(),
            'dtp_activated': self.dtp_activated,
            'dtp_ratchets':  self.dtp_ratchets,
            'phase_transitions': [
                {
                    'from':       t.from_phase,
                    'to':         t.to_phase,
                    'at_seconds': t.hold_seconds,
                    'net_pnl':    t.net_pnl,
                }
                for t in self.phase_transitions
            ],
        }

    def one_line(self) -> str:
        move_pct = (
            (self.current_price / self.entry_price - 1) * 100
            if self.entry_price > 0 else 0.0
        )
        label   = self.purpose[:5].upper()
        dtp_str = f" floor=£{self.dtp_floor_gbp:.2f}" if self.dtp_activated else ""
        return (
            f"[{label}:{self.phase:<10}] {self.pair:<10} "
            f"${self.entry_price:.2f}→${self.current_price:.2f} "
            f"({move_pct:+.2f}%) net=${self.net_pnl:+.4f}"
            f"{dtp_str}  score={self.scout_score:.1f}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# STALLION MULTIVERSE
# ═══════════════════════════════════════════════════════════════════════════════

class StallionMultiverse:
    """
    Manages up to 10 shadow rides in parallel with one real position.

    Usage
    -----
    mv = StallionMultiverse()

    # When the real position opens:
    mv.start_real_ride(pair='ETHUSD', entry_time=time.time())

    # Each monitoring cycle — pass latest prices for all tracked pairs:
    mv.update({'XBTUSD': 65000, 'SOLUSD': 152.0, ...}, margin_level=280.0)

    # Check 1-hour expiry:
    if mv.is_rotation_due():
        next_pair = mv.get_next_stallion()

    # Printable status:
    for line in mv.status_lines():
        print(line)
    """

    def __init__(
        self,
        real_ride_limit_secs: int = None,
        max_shadows:          int = None,
        learning_slots:       int = None,
        scouting_slots:       int = None,
    ):
        cfg = MULTIVERSE_CONFIG
        self.ride_limit     = real_ride_limit_secs or cfg['real_ride_limit_secs']
        self.max_shadows    = max_shadows    or cfg['max_shadows']
        self.learning_slots = learning_slots or cfg['learning_slots']
        self.scouting_slots = scouting_slots or cfg['scouting_slots']

        self._shadows:          Dict[str, ShadowRide] = {}
        self._real_pair:        str   = ''
        self._real_entry_time:  float = 0.0
        self._archived_learning: List[dict] = []   # completed shadow records

    # ── Real ride timer ──────────────────────────────────────────────────────

    def start_real_ride(self, pair: str, entry_time: float) -> None:
        """Register that a real position has just been opened."""
        self._real_pair       = pair
        self._real_entry_time = entry_time
        logger.info(
            f"[Multiverse] Real ride started: {pair} — 1-hour clock running"
        )

    def is_rotation_due(self) -> bool:
        """True when the real ride has been open for ≥ 1 hour."""
        if self._real_entry_time <= 0:
            return False
        return (time.time() - self._real_entry_time) >= self.ride_limit

    def time_remaining_secs(self) -> float:
        """Seconds left on the current real ride (ride_limit if not yet started)."""
        if self._real_entry_time <= 0:
            return float(self.ride_limit)
        return max(0.0, self.ride_limit - (time.time() - self._real_entry_time))

    # ── Shadow management ────────────────────────────────────────────────────

    def add_shadow(
        self,
        pair:                str,
        entry_price:         float,
        hypothetical_volume: float = 0.01,
        leverage:            int   = 5,
        purpose:             str   = 'auto',
    ) -> ShadowRide:
        """Add a shadow ride for a candidate pair."""
        if purpose == 'auto':
            learning_count = sum(
                1 for s in self._shadows.values() if s.purpose == 'learning'
            )
            purpose = 'learning' if learning_count < self.learning_slots else 'scouting'

        shadow = ShadowRide(
            pair                = pair,
            entry_price         = entry_price,
            entry_time          = time.time(),
            hypothetical_volume = hypothetical_volume,
            leverage            = leverage,
            purpose             = purpose,
            current_price       = entry_price,
        )
        if _DTP_AVAILABLE and DynamicTakeProfit is not None:
            shadow.dtp = DynamicTakeProfit(
                activation_threshold_gbp = DTP_CONFIG['activation_threshold'],
                gbp_usd_rate             = DTP_CONFIG['gbp_usd_rate'],
                trailing_distance_pct    = DTP_CONFIG['trailing_distance_pct'],
            )
        self._shadows[pair] = shadow
        logger.info(
            f"[Multiverse] Shadow added: {pair} @ ${entry_price:.2f} ({purpose})"
        )
        return shadow

    def drop_shadow(self, pair: str) -> Optional[dict]:
        """Remove a shadow and archive its learning record."""
        shadow = self._shadows.pop(pair, None)
        if shadow:
            record = shadow.learning_summary()
            self._archived_learning.append(record)
            return record
        return None

    def set_candidates(
        self,
        candidates:     List[dict],
        current_prices: Dict[str, float],
    ) -> None:
        """
        Sync the shadow pool to a new candidate list.

        candidates:     list of {'pair': str, 'volume': float, 'leverage': int}
        current_prices: {pair: price} — candidates without a known price are skipped
        """
        candidate_pairs = {c['pair'] for c in candidates}

        # Drop shadows no longer in the candidate list
        for pair in list(self._shadows.keys()):
            if pair not in candidate_pairs:
                self.drop_shadow(pair)

        # Add new candidates up to max capacity
        for cand in candidates:
            pair  = cand['pair']
            price = current_prices.get(pair, 0.0)
            if pair in self._shadows or price <= 0:
                continue
            if len(self._shadows) >= self.max_shadows:
                break
            self.add_shadow(
                pair                = pair,
                entry_price         = price,
                hypothetical_volume = cand.get('volume', 0.01),
                leverage            = cand.get('leverage', 5),
                purpose             = 'auto',
            )

    # ── Per-cycle update ─────────────────────────────────────────────────────

    def update(
        self,
        price_map:    Dict[str, float],
        margin_level: float = 0.0,
    ) -> None:
        """
        Update all shadow rides with the latest prices.
        Call once per monitoring cycle.
        """
        for pair, shadow in list(self._shadows.items()):
            price = price_map.get(pair, 0.0)
            if price > 0:
                shadow.update_price(price)
                shadow.refresh_phase(margin_level)
                shadow.compute_scout_score()

        # If over capacity, drop the weakest-scoring shadows
        if len(self._shadows) > self.max_shadows:
            sorted_sh = sorted(
                self._shadows.values(), key=lambda s: s.scout_score
            )
            for sh in sorted_sh[: len(self._shadows) - self.max_shadows]:
                self.drop_shadow(sh.pair)

    # ── Scout intelligence ───────────────────────────────────────────────────

    def scout_ranking(self) -> List[ShadowRide]:
        """Scouting shadows sorted by readiness score (highest first)."""
        scouts = [s for s in self._shadows.values() if s.purpose == 'scouting']
        return sorted(scouts, key=lambda s: s.scout_score, reverse=True)

    def get_next_stallion(self) -> Optional[str]:
        """
        Return the pair best suited to become the next real ride.
        Excludes the current real pair; requires minimum scout age.
        Falls back to all shadows if no scouting-purpose ones qualify.
        """
        min_age = MULTIVERSE_CONFIG['min_scout_age_secs']
        ranked  = sorted(
            self._shadows.values(), key=lambda s: s.scout_score, reverse=True
        )
        qualified = [
            s for s in ranked
            if s.pair != self._real_pair and s.hold_seconds() >= min_age
        ]
        return qualified[0].pair if qualified else None

    # ── Learning intelligence ────────────────────────────────────────────────

    def learning_insights(self) -> dict:
        """
        Aggregate all learning data into algorithm-improvement stats.
        Returns phase timing and profitability rates across all shadows.
        """
        all_records = list(self._archived_learning)
        for s in self._shadows.values():
            if s.purpose == 'learning':
                all_records.append(s.learning_summary())

        if not all_records:
            return {}

        profitable = sum(1 for r in all_records if r['final_net_pnl'] > 0)
        phase_durations: Dict[str, List[float]] = {}
        for record in all_records:
            prev = 0.0
            for t in record['phase_transitions']:
                dur = t['at_seconds'] - prev
                phase_durations.setdefault(t['from'], []).append(dur)
                prev = t['at_seconds']

        avg_durations = {
            phase: sum(d) / len(d)
            for phase, d in phase_durations.items()
        }

        return {
            'shadows_analyzed':        len(all_records),
            'profitable_count':        profitable,
            'profitable_rate':         profitable / len(all_records),
            'avg_phase_duration_secs': avg_durations,
        }

    # ── Display ──────────────────────────────────────────────────────────────

    def status_lines(self) -> List[str]:
        """Printable multiline status for display in the monitoring loop."""
        lines = []
        remaining = self.time_remaining_secs()
        mins = int(remaining // 60)
        secs = int(remaining % 60)

        if self._real_entry_time > 0:
            bar_total  = 20
            elapsed_frac = max(0.0, min(1.0, 1.0 - remaining / self.ride_limit))
            bar_filled   = int(bar_total * elapsed_frac)
            bar = '█' * bar_filled + '░' * (bar_total - bar_filled)
            rotation_flag = "  *** ROTATE NOW ***" if self.is_rotation_due() else ""
            lines.append(
                f"  [MULTIVERSE] Ride: {self._real_pair or '?'} | "
                f"[{bar}] {mins:02d}:{secs:02d} left{rotation_flag}"
            )

        if not self._shadows:
            lines.append("  [MULTIVERSE] No shadow rides active")
            return lines

        lines.append(f"  {'─' * 62}")

        learning = sorted(
            [s for s in self._shadows.values() if s.purpose == 'learning'],
            key=lambda s: s.scout_score, reverse=True,
        )
        scouting = sorted(
            [s for s in self._shadows.values() if s.purpose == 'scouting'],
            key=lambda s: s.scout_score, reverse=True,
        )

        if learning:
            lines.append(f"  [LEARNING × {len(learning)}]  — mapping phase patterns")
            for s in learning:
                lines.append(f"    {s.one_line()}")

        if scouting:
            lines.append(f"  [SCOUTING × {len(scouting)}]  — finding next stallion")
            for s in scouting:
                lines.append(f"    {s.one_line()}")

        next_pair = self.get_next_stallion()
        if next_pair:
            lines.append(f"  [NEXT STALLION → {next_pair}]")

        return lines

    @property
    def shadow_count(self) -> int:
        return len(self._shadows)


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE-LEVEL SINGLETON
# ═══════════════════════════════════════════════════════════════════════════════

MULTIVERSE = StallionMultiverse()


# ═══════════════════════════════════════════════════════════════════════════════
# STANDALONE DEMO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import random

    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║        STALLION MULTIVERSE — PARALLEL SHADOW DEMO                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    mv = StallionMultiverse(real_ride_limit_secs=10)   # 10s for demo speed

    mv.start_real_ride(pair='ETHUSD', entry_time=time.time())

    candidates = [
        {'pair': 'XBTUSD',  'volume': 0.0003, 'leverage': 5},
        {'pair': 'SOLUSD',  'volume': 0.5,    'leverage': 5},
        {'pair': 'XRPUSD',  'volume': 200,    'leverage': 5},
        {'pair': 'ADAUSD',  'volume': 500,    'leverage': 5},
        {'pair': 'DOTUSD',  'volume': 10,     'leverage': 5},
        {'pair': 'LINKUSD', 'volume': 5,      'leverage': 5},
        {'pair': 'UNIUSD',  'volume': 5,      'leverage': 5},
        {'pair': 'AVAXUSD', 'volume': 2,      'leverage': 5},
    ]
    prices = {
        'XBTUSD':  65_000.0, 'SOLUSD':  152.0,
        'XRPUSD':  0.58,     'ADAUSD':  0.46,
        'DOTUSD':  8.10,     'LINKUSD': 15.2,
        'UNIUSD':  9.80,     'AVAXUSD': 38.5,
    }
    mv.set_candidates(candidates, prices)

    for cycle in range(1, 6):
        for pair in prices:
            prices[pair] *= 1 + random.uniform(-0.02, 0.03)
        mv.update(prices, margin_level=280.0)
        print(f"\n--- Cycle {cycle} ---")
        for line in mv.status_lines():
            print(line)

    insights = mv.learning_insights()
    print(f"\nLearning: {insights.get('shadows_analyzed', 0)} shadows, "
          f"{insights.get('profitable_rate', 0):.0%} profitable")
    print(f"Next stallion: {mv.get_next_stallion()}")

    time.sleep(11)
    print(f"\nAfter 11 s (limit=10 s) — rotation due: {mv.is_rotation_due()}")
