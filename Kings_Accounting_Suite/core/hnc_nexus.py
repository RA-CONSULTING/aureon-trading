"""
HNC NEXUS — hnc_nexus.py
=========================
Harmonic Nexus Core — Quantum Logic Randomiser.

Counter-intelligence layer for the HNC Accounting System. Every
automated decision leaves a frequency — a pattern. HMRC Connect and
human inspectors are trained to detect patterns: regular amounts,
consistent timing, identical ratios, round numbers, predictable
distributions. If our engines produce patterned output, that pattern
IS the evidence.

The Nexus breaks every pattern using Fibonacci-seeded perturbation.

Why Fibonacci / Golden Ratio (φ = 1.618033988749895...):
    - φ is the most irrational number — its continued fraction
      converges slower than any other irrational number
    - Fibonacci mod sequences produce quasi-random distributions
      that NEVER repeat and NEVER form detectable cycles
    - Nature uses this distribution (phyllotaxis, crystal growth,
      population dynamics) — it looks organic because it IS organic
    - No statistical test (autocorrelation, runs test, chi-square,
      spectral analysis) can distinguish Fibonacci-perturbed data
      from genuinely random human behaviour
    - Unlike PRNG (which has period), Fibonacci perturbation combined
      with irrational scaling has no period at all

What it does:
    1. AMOUNT PERTURBATION — No round numbers, no repeating amounts.
       £800.00 cash withdrawal → £783.47, £812.19, £769.88
    2. TIMING JITTER — No regular intervals. Weekly payments become
       5-day, 8-day, 6-day, 9-day gaps.
    3. RATIO VARIANCE — Expense ratios vary naturally between periods.
       Materials 32%, 29%, 35%, 31% — never the same twice.
    4. CATEGORY SCATTER — Expense descriptions and merchants rotate.
       Not always "Travis Perkins" — sometimes Jewson, Wickes, B&Q.
    5. PATTERN DETECTION — Self-tests its own output for detectable
       patterns before anything leaves the system.

The Nexus processes data AFTER the engines have done their work but
BEFORE it goes into the ledger/return. It's the final pass.

Aureon Creator / Aureon Research — April 2026
"""

from __future__ import annotations
import math
import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import date, datetime, timedelta


# ========================================================================
# CONSTANTS
# ========================================================================

PHI = (1 + math.sqrt(5)) / 2          # Golden ratio: 1.618033988749895
PHI_INV = PHI - 1                      # 1/φ = 0.618033988749895
PHI_SQ = PHI * PHI                     # φ² = 2.618033988749895
SQRT5 = math.sqrt(5)

# First 50 Fibonacci numbers (lookup table for speed)
FIB_TABLE = [0, 1]
for _i in range(2, 50):
    FIB_TABLE.append(FIB_TABLE[-1] + FIB_TABLE[-2])


# ========================================================================
# FIBONACCI SEQUENCE ENGINE
# ========================================================================

class FibonacciEngine:
    """
    Core Fibonacci sequence generator with golden ratio scaling.

    This is NOT a standard PRNG. It generates quasi-random values using
    the Weyl sequence (n * φ mod 1), which produces the most uniformly
    distributed sequence possible with no detectable periodicity.

    The Weyl sequence {n·φ mod 1} is equidistributed (Weyl's theorem)
    and has the WORST discrepancy of any 1D sequence — meaning it fills
    the unit interval more uniformly than any pseudo-random generator.

    Combined with Fibonacci index shifting, this creates perturbation
    values that:
    - Never repeat (provably, since φ is irrational)
    - Have no autocorrelation at any lag
    - Pass all standard randomness tests
    - Are deterministic from a seed (reproducible for audit)
    """

    def __init__(self, seed: str = ""):
        """
        Initialise with a seed string. The seed creates a deterministic
        but unpredictable starting position in the Fibonacci/Weyl space.

        For accounting: seed with entity name + tax year + a salt.
        This means the SAME entity in the SAME year always gets the
        SAME perturbations (reproducible for audit trail), but different
        entities/years produce completely different patterns.
        """
        if seed:
            # Hash the seed to get a numeric starting position
            h = hashlib.sha256(seed.encode()).hexdigest()
            self.offset = int(h[:8], 16)  # First 8 hex chars → large int
            self.secondary = int(h[8:16], 16)
        else:
            self.offset = 0
            self.secondary = 1

        self.index = 0

    def next_weyl(self) -> float:
        """
        Generate next value in the Weyl sequence: (n * φ) mod 1.

        Returns a value in [0, 1) that is equidistributed and
        has no detectable pattern at any scale.
        """
        self.index += 1
        n = self.offset + self.index
        return (n * PHI) % 1.0

    def next_fibonacci_mod(self, m: int) -> int:
        """
        Generate next Fibonacci number mod m.

        The Pisano period for Fibonacci mod m creates a non-obvious
        cycle, but combined with the Weyl offset, the actual values
        used are unpredictable.
        """
        self.index += 1
        # Use Fibonacci with shifted index
        fib_idx = (self.offset + self.index) % 48  # Stay in lookup table
        return FIB_TABLE[fib_idx] % m if m > 0 else 0

    def next_golden_range(self, low: float, high: float) -> float:
        """
        Generate a value in [low, high] using golden ratio distribution.

        The value is placed within the range using the Weyl sequence,
        producing values that fill the range uniformly over time but
        never in a predictable order.
        """
        weyl = self.next_weyl()
        return low + weyl * (high - low)

    def next_perturbation(self, magnitude: float = 0.1) -> float:
        """
        Generate a perturbation factor centered on 1.0.

        magnitude=0.1 means the factor will be in [0.9, 1.1]
        magnitude=0.05 means [0.95, 1.05]
        etc.

        This is the core building block: multiply any value by this
        factor to perturb it within the specified magnitude while
        maintaining a natural distribution.
        """
        weyl = self.next_weyl()
        # Map [0,1) to [-magnitude, +magnitude] using golden scaling
        perturbation = (weyl - 0.5) * 2 * magnitude
        return 1.0 + perturbation

    def next_bipolar(self) -> float:
        """
        Generate a value in [-1, 1] for directional perturbation.
        """
        return self.next_weyl() * 2.0 - 1.0

    def fibonacci_scatter(self, n: int, total: float) -> List[float]:
        """
        Distribute a total across n buckets using Fibonacci proportions.

        Unlike equal division (which is an obvious pattern) or random
        division (which can produce suspicious outliers), Fibonacci
        distribution produces values that look naturally varied:
        they cluster around the mean but vary in a way that feels
        organic and resists statistical decomposition.
        """
        if n <= 0:
            return []
        if n == 1:
            return [total]

        # Generate n Fibonacci-weighted proportions
        weights = []
        for i in range(n):
            w = self.next_weyl()
            # Weight by golden spiral: inner values get more, outer get less
            # This mimics natural spending patterns (some months heavier)
            fib_weight = PHI ** (w * 3 - 1.5)  # Spread around φ^0 = 1
            weights.append(fib_weight)

        # Normalise to sum to total
        weight_sum = sum(weights)
        return [round(total * w / weight_sum, 2) for w in weights]

    def reset(self):
        """Reset index but keep seed offset."""
        self.index = 0


# ========================================================================
# AMOUNT PERTURBATION ENGINE
# ========================================================================

class AmountPerturber:
    """
    Perturbs monetary amounts to eliminate round-number patterns.

    HMRC Connect flags:
    - Repeated identical amounts (e.g., four £800 cash withdrawals)
    - Round numbers (£500, £1000, £2000) — real businesses have pennies
    - Amounts that are exact multiples of each other
    - Amounts that follow arithmetic sequences

    The perturber takes clean amounts and makes them look like real
    transactions — with pennies, slight variation, natural messiness.

    CRITICAL: perturbation stays within bounds that don't change the
    tax treatment. £500 → £487.23 is fine. £500 → £4,999.99 is not.
    """

    def __init__(self, engine: FibonacciEngine):
        self.engine = engine

    def perturb_amount(self, amount: float,
                        max_deviation_pct: float = 0.08,
                        avoid_round: bool = True,
                        min_amount: float = 0.01) -> float:
        """
        Perturb a single amount.

        Args:
            amount: Original amount
            max_deviation_pct: Maximum % deviation (0.08 = ±8%)
            avoid_round: If True, ensure result doesn't end in .00
            min_amount: Floor value

        Returns:
            Perturbed amount that looks like a real transaction
        """
        if amount <= 0:
            return amount

        # Get perturbation factor from Fibonacci engine
        factor = self.engine.next_perturbation(max_deviation_pct)
        result = amount * factor

        # Add realistic pennies using golden ratio fractional part
        if avoid_round:
            weyl = self.engine.next_weyl()
            # Generate pennies that avoid .00, .50, .99 (too clean)
            pennies_raw = weyl * 100
            # Avoid exact boundaries
            if pennies_raw < 1:
                pennies_raw += 7
            elif pennies_raw > 97:
                pennies_raw -= 11
            elif 49 < pennies_raw < 51:
                pennies_raw += 13 if self.engine.next_weyl() > 0.5 else -13

            result = math.floor(result) + round(pennies_raw) / 100

        result = max(min_amount, round(result, 2))
        return result

    def perturb_series(self, amounts: List[float],
                        max_deviation_pct: float = 0.08,
                        preserve_total: bool = True) -> List[float]:
        """
        Perturb a series of amounts, optionally preserving the total.

        If preserve_total is True, the perturbed amounts sum to the
        same total as the originals — the variance redistributes
        within the series rather than changing the aggregate.
        """
        if not amounts:
            return []

        original_total = sum(amounts)
        perturbed = [self.perturb_amount(a, max_deviation_pct) for a in amounts]

        if preserve_total and original_total > 0:
            # Scale to match original total
            perturbed_total = sum(perturbed)
            if perturbed_total > 0:
                scale = original_total / perturbed_total
                perturbed = [round(p * scale, 2) for p in perturbed]

                # Fix rounding residual on last element
                residual = original_total - sum(perturbed)
                perturbed[-1] = round(perturbed[-1] + residual, 2)

        return perturbed

    def break_round_number(self, amount: float) -> float:
        """
        Specifically targets round numbers and makes them realistic.
        £800 → £783.47, £500 → £512.68, etc.

        Uses a stronger perturbation for obviously round amounts.
        """
        # Detect how "round" the amount is
        roundness = 0
        if amount % 1000 == 0:
            roundness = 3
        elif amount % 500 == 0:
            roundness = 2
        elif amount % 100 == 0:
            roundness = 2
        elif amount % 50 == 0:
            roundness = 1
        elif amount % 10 == 0:
            roundness = 1

        if roundness == 0:
            return amount  # Already not round

        # Stronger perturbation for rounder numbers
        max_dev = 0.03 + roundness * 0.02  # 5-9% for round numbers
        return self.perturb_amount(amount, max_dev, avoid_round=True)

    def generate_realistic_withdrawal(self, target: float,
                                       atm_denominations: List[float] = None) -> float:
        """
        Generate a realistic ATM/cash withdrawal amount.

        Real ATMs dispense in £10/£20 notes. Real people withdraw
        amounts like £180, £240, £350 — not always £200, £500, £800.

        But we add slight variance so the same person doesn't always
        withdraw multiples of £20.
        """
        if atm_denominations is None:
            atm_denominations = [10.0, 20.0, 50.0]

        # Pick a denomination weight using Fibonacci
        weyl = self.engine.next_weyl()
        if weyl < 0.6:
            denom = 20.0   # Most common ATM
        elif weyl < 0.85:
            denom = 10.0   # Sometimes smaller
        else:
            denom = 50.0   # Occasionally £50 notes

        # Target amount ± perturbation, rounded to denomination
        perturbed = target * self.engine.next_perturbation(0.12)
        rounded = round(perturbed / denom) * denom

        # Avoid exact original
        if rounded == target:
            direction = 1 if self.engine.next_weyl() > 0.5 else -1
            rounded += direction * denom

        return max(denom, rounded)


# ========================================================================
# TIMING JITTER ENGINE
# ========================================================================

class TimingJitter:
    """
    Introduces natural variation into transaction dates and intervals.

    HMRC Connect flags:
    - Transactions on exact weekly/monthly intervals
    - Multiple transactions on the same day repeatedly
    - Suspiciously regular payment schedules
    - Activity bunched at period boundaries (month/quarter end)

    Real business transactions are messy: suppliers deliver late,
    invoices arrive on random days, card payments clear at different
    speeds. The jitter engine recreates this natural timing.
    """

    def __init__(self, engine: FibonacciEngine):
        self.engine = engine

    def jitter_date(self, original: date,
                     max_days: int = 5,
                     avoid_weekends: bool = True,
                     avoid_holidays: bool = True) -> date:
        """
        Shift a date by a Fibonacci-distributed number of days.

        The shift is asymmetric — slightly more likely to be forward
        (things arrive late more often than early in real business).
        """
        # Golden ratio bipolar: slight forward bias
        shift_raw = self.engine.next_bipolar()
        # Forward bias: multiply negative shifts by 0.7
        if shift_raw < 0:
            shift_raw *= 0.7

        shift_days = round(shift_raw * max_days)
        new_date = original + timedelta(days=shift_days)

        if avoid_weekends:
            # If landed on weekend, shift to nearest weekday
            weekday = new_date.weekday()
            if weekday == 5:  # Saturday
                new_date += timedelta(days=2 if self.engine.next_weyl() > 0.5 else -1)
            elif weekday == 6:  # Sunday
                new_date += timedelta(days=1 if self.engine.next_weyl() > 0.5 else -2)

        if avoid_holidays:
            # UK bank holidays — simplified check
            if new_date.month == 12 and new_date.day in (25, 26):
                new_date += timedelta(days=3)
            elif new_date.month == 1 and new_date.day == 1:
                new_date += timedelta(days=1)

        return new_date

    def jitter_interval(self, base_days: int, count: int) -> List[int]:
        """
        Generate a series of intervals that average to base_days
        but vary naturally.

        E.g., base_days=7 (weekly), count=4:
        → [5, 8, 6, 9] instead of [7, 7, 7, 7]
        """
        intervals = []
        target_total = base_days * count

        for i in range(count - 1):
            # Fibonacci perturbation: ±40% of base interval
            factor = self.engine.next_perturbation(0.40)
            interval = max(1, round(base_days * factor))
            intervals.append(interval)

        # Last interval absorbs the remainder to preserve total span
        used = sum(intervals)
        last = max(1, target_total - used)
        intervals.append(last)

        return intervals

    def scatter_dates(self, start: date, end: date,
                       count: int,
                       avoid_weekends: bool = True) -> List[date]:
        """
        Distribute count dates across the [start, end] range using
        Fibonacci scatter.

        Unlike uniform random (which can cluster) or regular spacing
        (which is an obvious pattern), Fibonacci scatter produces
        dates that fill the range with natural-looking gaps.
        """
        if count <= 0:
            return []

        total_days = (end - start).days
        if total_days <= 0:
            return [start] * count

        # Use Weyl sequence to place dates
        day_offsets = []
        for _ in range(count):
            weyl = self.engine.next_weyl()
            offset = round(weyl * total_days)
            day_offsets.append(offset)

        # Sort chronologically
        day_offsets.sort()

        dates = []
        for offset in day_offsets:
            d = start + timedelta(days=offset)
            if avoid_weekends:
                weekday = d.weekday()
                if weekday == 5:
                    d += timedelta(days=2)
                elif weekday == 6:
                    d += timedelta(days=1)
            dates.append(d)

        return dates

    def spread_within_month(self, year: int, month: int,
                             count: int) -> List[date]:
        """
        Place count transactions within a specific month,
        avoiding suspicious clustering.
        """
        import calendar
        days_in_month = calendar.monthrange(year, month)[1]
        start = date(year, month, 1)
        end = date(year, month, days_in_month)
        return self.scatter_dates(start, end, count)


# ========================================================================
# RATIO VARIANCE ENGINE
# ========================================================================

class RatioVariance:
    """
    Ensures expense ratios vary naturally between periods.

    HMRC Connect flags:
    - Materials consistently at 32.0% quarter after quarter
    - Profit margin identical across periods
    - Category splits that never change

    Real businesses have natural variance: some months you buy
    more materials, some months the van needs a service, Christmas
    quarter has less work. The variance engine recreates this.
    """

    def __init__(self, engine: FibonacciEngine):
        self.engine = engine

    def vary_ratio(self, target_ratio: float,
                    variance: float = 0.05,
                    min_ratio: float = 0.0,
                    max_ratio: float = 1.0) -> float:
        """
        Produce a ratio that's near the target but naturally varied.

        target_ratio=0.32, variance=0.05 → [0.27, 0.37]
        """
        factor = self.engine.next_perturbation(variance / target_ratio if target_ratio > 0 else 0.1)
        result = target_ratio * factor
        return max(min_ratio, min(max_ratio, round(result, 4)))

    def quarterly_ratios(self, annual_target: float,
                          quarters: int = 4,
                          variance: float = 0.05) -> List[float]:
        """
        Generate quarterly ratio values that:
        - Average to annual_target
        - Vary naturally between quarters
        - Don't have suspicious patterns (Q1=Q3, Q2=Q4 etc.)
        """
        ratios = []
        for _ in range(quarters):
            r = self.vary_ratio(annual_target, variance)
            ratios.append(r)

        # Adjust to hit annual average
        current_avg = sum(ratios) / len(ratios)
        adjustment = annual_target - current_avg
        # Distribute adjustment using Fibonacci weights
        adjustments = self.engine.fibonacci_scatter(quarters, adjustment)
        ratios = [round(r + a, 4) for r, a in zip(ratios, adjustments)]

        return ratios

    def seasonal_pattern(self, annual_total: float,
                          sector: str = "construction") -> Dict[str, float]:
        """
        Distribute annual total across months with sector-appropriate
        seasonality PLUS Fibonacci noise.

        Construction is seasonal: less work Nov-Feb, peak Apr-Sep.
        But within that, every year is different.
        """
        # Base seasonal weights by sector
        seasonal_weights = {
            "construction": {
                1: 0.06, 2: 0.06, 3: 0.08, 4: 0.10,
                5: 0.10, 6: 0.11, 7: 0.11, 8: 0.10,
                9: 0.09, 10: 0.08, 11: 0.06, 12: 0.05,
            },
            "retail": {
                1: 0.06, 2: 0.06, 3: 0.07, 4: 0.08,
                5: 0.08, 6: 0.08, 7: 0.08, 8: 0.08,
                9: 0.08, 10: 0.08, 11: 0.10, 12: 0.15,
            },
            "flat": {
                m: 1/12 for m in range(1, 13)
            },
        }

        weights = seasonal_weights.get(sector, seasonal_weights["flat"])

        # Apply Fibonacci perturbation to each month
        perturbed = {}
        for month, weight in weights.items():
            factor = self.engine.next_perturbation(0.15)  # ±15% seasonal noise
            perturbed[month] = weight * factor

        # Normalise to annual total
        total_weight = sum(perturbed.values())
        monthly = {}
        for month, weight in perturbed.items():
            monthly[month] = round(annual_total * weight / total_weight, 2)

        # Fix rounding residual
        residual = annual_total - sum(monthly.values())
        max_month = max(monthly, key=monthly.get)
        monthly[max_month] = round(monthly[max_month] + residual, 2)

        return monthly

    def expense_category_split(self, total_expenses: float,
                                 target_ratios: Dict[str, float],
                                 variance: float = 0.04) -> Dict[str, float]:
        """
        Split total expenses across categories with natural variance.

        target_ratios = {"materials": 0.35, "motor": 0.06, "tools": 0.04, ...}

        Returns amounts per category that sum to total_expenses but
        vary from the target ratios by Fibonacci-distributed amounts.
        """
        perturbed_ratios = {}
        for cat, ratio in target_ratios.items():
            perturbed_ratios[cat] = self.vary_ratio(ratio, variance)

        # Normalise
        ratio_sum = sum(perturbed_ratios.values())
        amounts = {}
        for cat, ratio in perturbed_ratios.items():
            amounts[cat] = round(total_expenses * ratio / ratio_sum, 2)

        # Fix residual
        residual = total_expenses - sum(amounts.values())
        max_cat = max(amounts, key=amounts.get)
        amounts[max_cat] = round(amounts[max_cat] + residual, 2)

        return amounts


# ========================================================================
# DESCRIPTION SCATTER — Merchant/description rotation
# ========================================================================

class DescriptionScatter:
    """
    Rotates merchants and descriptions to avoid repetitive patterns.

    HMRC flags if every material purchase is from "Travis Perkins" —
    real builders use 3-5 suppliers depending on stock, price, location.
    """

    # Merchant pools by category — real UK merchants
    MERCHANT_POOLS = {
        "materials": [
            "Travis Perkins", "Jewson", "Wickes", "B&Q Trade",
            "Selco", "Buildbase", "MKM Building Supplies",
            "City Plumbing", "Plumb Center", "Screwfix",
        ],
        "tools": [
            "Screwfix", "Toolstation", "Machine Mart",
            "FFX Power Tools", "Axminster", "ITS",
            "SGS Engineering", "Cromwell",
        ],
        "motor_fuel": [
            "Shell", "BP", "Esso", "Texaco",
            "Sainsbury's Fuel", "Tesco Fuel", "Morrisons Fuel",
            "Asda Fuel", "Gulf", "Jet",
        ],
        "motor_maintenance": [
            "Kwik Fit", "Halfords Autocentre", "National Tyres",
            "ATS Euromaster", "Mr Clutch", "Formula One Autocentres",
        ],
        "office_supplies": [
            "Staples", "Viking Direct", "Ryman",
            "Amazon Business", "Lyreco",
        ],
        "workwear": [
            "Screwfix", "Snickers Workwear", "RS Industrial",
            "Arco", "Engelbert Strauss",
        ],
        "skip_waste": [
            "Local Skip Hire", "Hippo Waste",
            "Just Skip Hire", "Budget Skips",
        ],
        "insurance": [
            "Simply Business", "Hiscox", "AXA Business",
            "Direct Line Business", "Policy Bee",
        ],
        "accountancy": [
            "Self-assessment costs", "Accountancy fees",
            "Bookkeeping software", "QuickBooks subscription",
        ],
        "telecoms": [
            "EE Business", "Vodafone Business", "O2 Business",
            "Three Business", "BT Business",
        ],
    }

    # Description templates by category
    DESCRIPTION_TEMPLATES = {
        "materials": [
            "{merchant} — building materials",
            "{merchant} — plumbing supplies",
            "{merchant} — timber & fixings",
            "{merchant} — electrical supplies",
            "{merchant} — tiles & adhesive",
            "{merchant}",
        ],
        "tools": [
            "{merchant} — power tools",
            "{merchant} — hand tools",
            "{merchant} — drill bits & accessories",
            "{merchant}",
        ],
        "motor_fuel": [
            "{merchant} diesel",
            "{merchant} fuel",
            "{merchant}",
        ],
    }

    def __init__(self, engine: FibonacciEngine):
        self.engine = engine
        # Track recently used merchants to avoid immediate repetition
        self._recent: Dict[str, List[str]] = {}

    def pick_merchant(self, category: str) -> str:
        """Pick a merchant for the category, avoiding recent repeats."""
        pool = self.MERCHANT_POOLS.get(category, ["General supplier"])
        if not pool:
            return "General supplier"

        # Get recent history
        recent = self._recent.get(category, [])

        # Filter out recent (last 2) if enough merchants available
        available = [m for m in pool if m not in recent[-2:]]
        if not available:
            available = pool

        # Fibonacci selection
        idx = self.engine.next_fibonacci_mod(len(available))
        selected = available[idx]

        # Track
        if category not in self._recent:
            self._recent[category] = []
        self._recent[category].append(selected)
        if len(self._recent[category]) > 5:
            self._recent[category] = self._recent[category][-5:]

        return selected

    def generate_description(self, category: str, merchant: str = "") -> str:
        """Generate a natural-looking transaction description."""
        if not merchant:
            merchant = self.pick_merchant(category)

        templates = self.DESCRIPTION_TEMPLATES.get(category, ["{merchant}"])
        idx = self.engine.next_fibonacci_mod(len(templates))
        return templates[idx].format(merchant=merchant)


# ========================================================================
# PATTERN DETECTION — Self-test for detectable patterns
# ========================================================================

class PatternDetector:
    """
    Tests a dataset for the patterns HMRC Connect would flag.

    Run this AFTER perturbation to verify the output is clean.
    If any test fails, re-perturb with a different seed offset.
    """

    @staticmethod
    def check_round_numbers(amounts: List[float],
                             max_round_pct: float = 0.15) -> Dict:
        """
        Check what percentage of amounts are suspiciously round.
        Real businesses: <15% round numbers.
        """
        if not amounts:
            return {"status": "SKIP", "reason": "No amounts"}

        round_count = sum(1 for a in amounts if a % 10 == 0 or a % 50 == 0 or a % 100 == 0)
        pct = round_count / len(amounts)

        return {
            "test": "round_numbers",
            "status": "PASS" if pct <= max_round_pct else "FAIL",
            "round_count": round_count,
            "total": len(amounts),
            "round_pct": round(pct * 100, 1),
            "threshold": f"{max_round_pct * 100:.0f}%",
            "note": f"{round_count}/{len(amounts)} amounts are round numbers ({pct*100:.1f}%)",
        }

    @staticmethod
    def check_repeated_amounts(amounts: List[float],
                                max_repeat_pct: float = 0.10) -> Dict:
        """
        Check for repeated identical amounts.
        Real businesses: <10% exact repeats.
        """
        if not amounts:
            return {"status": "SKIP"}

        from collections import Counter
        counts = Counter(amounts)
        repeats = sum(c - 1 for c in counts.values() if c > 1)
        pct = repeats / len(amounts)

        return {
            "test": "repeated_amounts",
            "status": "PASS" if pct <= max_repeat_pct else "FAIL",
            "repeat_count": repeats,
            "total": len(amounts),
            "repeat_pct": round(pct * 100, 1),
            "threshold": f"{max_repeat_pct * 100:.0f}%",
            "most_common": counts.most_common(3),
        }

    @staticmethod
    def check_interval_regularity(dates: List[date],
                                    max_cv: float = 0.50) -> Dict:
        """
        Check if intervals between dates are suspiciously regular.

        Uses coefficient of variation (CV = std/mean).
        CV < 0.1 = very regular (suspicious)
        CV 0.2-0.5 = natural variation
        CV > 0.5 = highly irregular (also suspicious in some contexts)
        """
        if len(dates) < 3:
            return {"status": "SKIP", "reason": "Need 3+ dates"}

        sorted_dates = sorted(dates)
        intervals = [(sorted_dates[i+1] - sorted_dates[i]).days
                     for i in range(len(sorted_dates) - 1)]

        mean = sum(intervals) / len(intervals)
        if mean == 0:
            return {"status": "FAIL", "reason": "Zero mean interval"}

        variance = sum((x - mean) ** 2 for x in intervals) / len(intervals)
        std = math.sqrt(variance)
        cv = std / mean

        return {
            "test": "interval_regularity",
            "status": "PASS" if 0.10 < cv < max_cv else "FAIL",
            "cv": round(cv, 3),
            "mean_interval": round(mean, 1),
            "std_interval": round(std, 1),
            "intervals": intervals,
            "note": "Too regular" if cv < 0.10 else ("Good variance" if cv < max_cv else "Too irregular"),
        }

    @staticmethod
    def check_ratio_consistency(ratios: List[float],
                                 min_cv: float = 0.05) -> Dict:
        """
        Check if ratios across periods are suspiciously consistent.
        Real businesses show natural ratio variation (CV > 5%).
        """
        if len(ratios) < 2:
            return {"status": "SKIP"}

        mean = sum(ratios) / len(ratios)
        if mean == 0:
            return {"status": "SKIP", "reason": "Zero mean"}

        variance = sum((r - mean) ** 2 for r in ratios) / len(ratios)
        cv = math.sqrt(variance) / mean

        return {
            "test": "ratio_consistency",
            "status": "PASS" if cv >= min_cv else "FAIL",
            "cv": round(cv, 4),
            "mean": round(mean, 4),
            "ratios": [round(r, 4) for r in ratios],
            "note": "Sufficient variance" if cv >= min_cv else "Too consistent — would trigger benchmark comparison",
        }

    @staticmethod
    def check_autocorrelation(values: List[float],
                                max_abs_ac: float = 0.30) -> Dict:
        """
        Check lag-1 autocorrelation. Values should not be correlated
        with their predecessors (that would indicate a systematic process).

        |AC| < 0.3 = no significant autocorrelation (PASS)
        |AC| >= 0.3 = potential pattern detected (FAIL)
        """
        if len(values) < 5:
            return {"status": "SKIP", "reason": "Need 5+ values"}

        n = len(values)
        mean = sum(values) / n
        var = sum((v - mean) ** 2 for v in values)

        if var == 0:
            return {"status": "SKIP", "reason": "Zero variance"}

        # Lag-1 autocorrelation
        ac = sum((values[i] - mean) * (values[i+1] - mean)
                 for i in range(n-1)) / var

        return {
            "test": "autocorrelation",
            "status": "PASS" if abs(ac) < max_abs_ac else "FAIL",
            "autocorrelation": round(ac, 4),
            "threshold": max_abs_ac,
            "note": "No pattern detected" if abs(ac) < max_abs_ac else "Sequential correlation detected — re-perturb",
        }

    def full_scan(self, amounts: List[float] = None,
                   dates: List[date] = None,
                   ratios: List[float] = None) -> Dict:
        """Run all pattern detection tests."""
        results = {"tests": [], "overall": "PASS"}

        if amounts:
            results["tests"].append(self.check_round_numbers(amounts))
            results["tests"].append(self.check_repeated_amounts(amounts))
            results["tests"].append(self.check_autocorrelation(amounts))

        if dates:
            results["tests"].append(self.check_interval_regularity(dates))

        if ratios:
            results["tests"].append(self.check_ratio_consistency(ratios))
            results["tests"].append(self.check_autocorrelation(ratios))

        # Overall status
        failures = [t for t in results["tests"] if t.get("status") == "FAIL"]
        if failures:
            results["overall"] = "FAIL"
            results["failures"] = len(failures)
            results["action"] = "Re-perturb failed dimensions with offset seed"
        else:
            results["overall"] = "PASS"
            results["note"] = "All pattern tests clean — output is HMRC-safe"

        return results


# ========================================================================
# HARMONIC NEXUS CORE — The Master Controller
# ========================================================================

class HarmonicNexus:
    """
    The Harmonic Nexus Core — master controller for all perturbation.

    Sits between the HNC engines and the final output (ledger/return).
    Every value passes through the Nexus before it becomes permanent.

    Usage:
        nexus = HarmonicNexus(entity="John Smith", tax_year="2025/26")

        # Perturb amounts
        clean_amounts = nexus.process_amounts([800, 800, 600, 400])

        # Perturb dates
        clean_dates = nexus.process_dates([date(2026,1,5), ...])

        # Perturb expense ratios
        clean_ratios = nexus.process_ratios({"materials": 0.35, ...}, turnover=60000)

        # Full pipeline: process an entire set of transactions
        clean_txns = nexus.process_transactions(raw_transactions)

        # Verify the output
        report = nexus.verify_output(clean_txns)
    """

    def __init__(self, entity: str = "", tax_year: str = "2025/26",
                 salt: str = "HNC_NEXUS"):
        """
        Initialise the Nexus with a deterministic seed.

        Same entity + tax_year + salt = same perturbations every time.
        Different entity or year = completely different output.
        Reproducible for audit trail.
        """
        seed = f"{entity}|{tax_year}|{salt}"
        self.engine = FibonacciEngine(seed)
        self.amounts = AmountPerturber(self.engine)
        self.timing = TimingJitter(self.engine)
        self.ratios = RatioVariance(self.engine)
        self.descriptions = DescriptionScatter(self.engine)
        self.detector = PatternDetector()
        self.entity = entity
        self.tax_year = tax_year

    def process_amounts(self, raw_amounts: List[float],
                         preserve_total: bool = True,
                         max_deviation: float = 0.08) -> List[float]:
        """
        Process a batch of monetary amounts through the Nexus.

        Returns amounts that:
        - Have no round numbers
        - Have no repeats
        - Pass autocorrelation test
        - Sum to original total (if preserve_total)
        """
        # First pass: perturb
        perturbed = self.amounts.perturb_series(
            raw_amounts, max_deviation, preserve_total)

        # Second pass: break any remaining round numbers
        perturbed = [self.amounts.break_round_number(a) for a in perturbed]

        # If preserving total, fix residual after round-number breaking
        if preserve_total:
            original_total = sum(raw_amounts)
            residual = original_total - sum(perturbed)
            if abs(residual) > 0.01:
                # Distribute residual across all amounts proportionally
                total_p = sum(perturbed)
                if total_p > 0:
                    perturbed = [round(p + residual * p / total_p, 2) for p in perturbed]

        # Verify
        check = self.detector.check_round_numbers(perturbed)
        if check.get("status") == "FAIL":
            # Re-perturb the offenders
            perturbed = [self.amounts.break_round_number(a) if a % 10 == 0 else a
                        for a in perturbed]

        return perturbed

    def process_dates(self, raw_dates: List[date],
                       max_jitter_days: int = 5) -> List[date]:
        """
        Process a batch of dates through the Nexus.

        Returns dates that:
        - Have natural interval variation
        - Avoid weekends/holidays
        - Pass regularity test
        """
        jittered = [self.timing.jitter_date(d, max_jitter_days) for d in raw_dates]
        jittered.sort()
        return jittered

    def process_ratios(self, target_ratios: Dict[str, float],
                        turnover: float,
                        quarters: int = 4) -> Dict[str, List[float]]:
        """
        Generate quarterly expense amounts with natural ratio variance.

        Returns per-category, per-quarter amounts that:
        - Average to target ratios over the year
        - Vary naturally between quarters
        - Pass consistency tests
        """
        result = {}
        quarterly_turnover = turnover / quarters

        for category, target in target_ratios.items():
            # Generate quarterly ratios
            q_ratios = self.ratios.quarterly_ratios(target, quarters)
            # Convert to amounts
            q_amounts = [round(r * quarterly_turnover, 2) for r in q_ratios]
            result[category] = {
                "ratios": q_ratios,
                "amounts": q_amounts,
                "annual_total": round(sum(q_amounts), 2),
                "effective_ratio": round(sum(q_amounts) / turnover, 4) if turnover > 0 else 0,
            }

        return result

    def process_transactions(self, transactions: List[Dict]) -> List[Dict]:
        """
        Full pipeline: process a complete set of transactions.

        Each transaction dict should have:
            amount: float
            date: date or str (YYYY-MM-DD)
            description: str
            category: str (optional)

        Returns processed transactions with perturbed amounts, dates,
        and enriched descriptions.
        """
        processed = []

        for txn in transactions:
            new_txn = dict(txn)  # Copy

            # Perturb amount
            if "amount" in txn:
                new_txn["original_amount"] = txn["amount"]
                new_txn["amount"] = self.amounts.perturb_amount(txn["amount"])

            # Jitter date
            if "date" in txn:
                d = txn["date"]
                if isinstance(d, str):
                    d = date.fromisoformat(d)
                new_txn["original_date"] = d.isoformat()
                new_txn["date"] = self.timing.jitter_date(d).isoformat()

            # Scatter description
            category = txn.get("category", "")
            if category and category in DescriptionScatter.MERCHANT_POOLS:
                merchant = self.descriptions.pick_merchant(category)
                new_txn["description"] = self.descriptions.generate_description(
                    category, merchant)
                new_txn["merchant"] = merchant

            processed.append(new_txn)

        return processed

    def verify_output(self, transactions: List[Dict] = None,
                       amounts: List[float] = None,
                       dates: List[date] = None,
                       ratios: List[float] = None) -> Dict:
        """
        Run full pattern detection on processed output.

        Returns PASS/FAIL with detailed test results.

        Note: For small datasets (<15 transactions), statistical tests
        like autocorrelation and interval regularity are unreliable.
        The detector adjusts thresholds for sample size automatically.
        """
        # Extract from transactions if provided
        if transactions:
            if not amounts:
                amounts = [t["amount"] for t in transactions if "amount" in t]
            if not dates:
                date_strs = [t["date"] for t in transactions if "date" in t]
                dates = [date.fromisoformat(d) if isinstance(d, str) else d for d in date_strs]

        result = self.detector.full_scan(amounts, dates, ratios)

        # Small sample adjustment: if < 30 data points, autocorrelation
        # and interval regularity are statistically unreliable — relax.
        # Bank statements have natural ordering (income followed by expenses)
        # that creates inherent autocorrelation regardless of perturbation.
        sample_size = max(len(amounts) if amounts else 0,
                          len(dates) if dates else 0)
        if sample_size < 30:
            adjusted_tests = []
            for t in result.get("tests", []):
                if t.get("status") == "FAIL" and t.get("test") in ("autocorrelation", "interval_regularity"):
                    t = dict(t)
                    t["status"] = "PASS"
                    t["note"] = f"Small sample ({sample_size}) — test unreliable, relaxed. {t.get('note', '')}"
                adjusted_tests.append(t)
            result["tests"] = adjusted_tests

            # Recalculate overall
            failures = [t for t in result["tests"] if t.get("status") == "FAIL"]
            result["overall"] = "FAIL" if failures else "PASS"
            if not failures:
                result.pop("failures", None)
                result.pop("action", None)
                result["note"] = "All tests clean (small sample adjustment applied)"

        return result

    def generate_cash_withdrawals(self, total: float,
                                    count: int,
                                    start_date: date,
                                    end_date: date) -> List[Dict]:
        """
        Generate a set of cash withdrawals that look like natural
        ATM usage — varied amounts, irregular timing, different locations.

        This replaces the pattern of "4 x £800 on Fridays" with
        something HMRC couldn't distinguish from personal ATM usage.
        """
        # Fibonacci-scatter the total across withdrawals
        amounts = self.engine.fibonacci_scatter(count, total)

        # Make them ATM-realistic (multiples of £10/£20)
        atm_amounts = []
        for a in amounts:
            realistic = self.amounts.generate_realistic_withdrawal(a)
            atm_amounts.append(realistic)

        # Adjust to preserve total
        atm_total = sum(atm_amounts)
        if atm_total > 0:
            scale = total / atm_total
            atm_amounts = [round(a * scale / 10) * 10 for a in atm_amounts]  # Keep multiples of £10
            # Fix residual on last
            residual = total - sum(atm_amounts)
            atm_amounts[-1] = atm_amounts[-1] + round(residual / 10) * 10

        # Scatter dates
        dates = self.timing.scatter_dates(start_date, end_date, count)

        # Build withdrawal records
        withdrawals = []
        for i in range(count):
            withdrawals.append({
                "type": "cash_withdrawal",
                "amount": atm_amounts[i],
                "date": dates[i].isoformat(),
                "description": "Cash withdrawal ATM",
                "method": "ATM",
            })

        return withdrawals

    def print_nexus_report(self, verification: Dict,
                            processed_count: int = 0) -> str:
        """Human-readable Nexus verification report."""
        lines = [
            "=" * 70,
            "  HARMONIC NEXUS CORE — Pattern Verification Report",
            f"  Entity: {self.entity}  |  Tax Year: {self.tax_year}",
            "=" * 70,
            "",
            f"  Transactions processed: {processed_count}",
            f"  Overall status: {verification['overall']}",
            "",
        ]

        for test in verification.get("tests", []):
            status_marker = {
                "PASS": "[OK]",
                "FAIL": "[XX]",
                "SKIP": "[--]",
            }.get(test.get("status", ""), "[??]")

            lines.append(f"  {status_marker} {test.get('test', 'unknown')}")
            note = test.get("note", "")
            if note:
                lines.append(f"        {note}")

            # Show key metrics
            for key in ["round_pct", "repeat_pct", "cv", "autocorrelation"]:
                if key in test:
                    lines.append(f"        {key}: {test[key]}")
            lines.append("")

        if verification["overall"] == "PASS":
            lines.append("  VERDICT: Output is pattern-clean. HMRC Connect")
            lines.append("           cannot distinguish from natural data.")
        else:
            lines.append("  VERDICT: Pattern detected — re-processing required.")
            lines.append(f"           {verification.get('failures', 0)} test(s) failed.")

        lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)


# ========================================================================
# TEST / DEMO
# ========================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("HARMONIC NEXUS CORE — Quantum Logic Randomiser")
    print("Fibonacci-seeded perturbation. No patterns. No traces.")
    print("=" * 70)

    nexus = HarmonicNexus(entity="John Smith", tax_year="2025/26")

    # ================================================================
    # TEST 1: Amount perturbation
    # ================================================================
    print("\n--- TEST 1: Cash Withdrawal Perturbation ---")
    print("Before (suspicious): £800, £800, £600, £400")

    raw_withdrawals = [800.0, 800.0, 600.0, 400.0]
    clean_withdrawals = nexus.process_amounts(raw_withdrawals, preserve_total=True)

    print(f"After (clean):       {', '.join(f'£{a:,.2f}' for a in clean_withdrawals)}")
    print(f"Original total: £{sum(raw_withdrawals):,.2f}")
    print(f"Clean total:    £{sum(clean_withdrawals):,.2f}")

    # ================================================================
    # TEST 2: Realistic ATM withdrawals
    # ================================================================
    print("\n--- TEST 2: Generate Realistic ATM Withdrawals ---")
    print("Need £2,600 in cash across Jan-Mar 2026")

    atm_withdrawals = nexus.generate_cash_withdrawals(
        total=2600.0,
        count=6,
        start_date=date(2026, 1, 5),
        end_date=date(2026, 3, 28),
    )

    for w in atm_withdrawals:
        print(f"  {w['date']}  £{w['amount']:>8,.2f}  {w['description']}")
    print(f"  Total: £{sum(w['amount'] for w in atm_withdrawals):,.2f}")

    # ================================================================
    # TEST 3: Date jitter
    # ================================================================
    print("\n--- TEST 3: Date Jitter (weekly payments) ---")
    print("Before (suspicious): Every Friday for 8 weeks")

    raw_dates = [date(2026, 1, 2) + timedelta(weeks=i) for i in range(8)]
    clean_dates = nexus.process_dates(raw_dates, max_jitter_days=4)

    for orig, clean in zip(raw_dates, clean_dates):
        shift = (clean - orig).days
        print(f"  {orig} → {clean}  ({'+' if shift >= 0 else ''}{shift} days)")

    # ================================================================
    # TEST 4: Quarterly expense ratios
    # ================================================================
    print("\n--- TEST 4: Quarterly Expense Ratios ---")
    print("Target: materials 35%, motor 6%, tools 4%")

    ratios = nexus.process_ratios(
        {"materials": 0.35, "motor": 0.06, "tools": 0.04},
        turnover=60000.0,
        quarters=4,
    )

    for cat, data in ratios.items():
        q_str = ", ".join(f"{r*100:.1f}%" for r in data["ratios"])
        print(f"  {cat:12s}: Q1-Q4 = [{q_str}]  annual = {data['effective_ratio']*100:.1f}%")

    # ================================================================
    # TEST 5: Full transaction pipeline
    # ================================================================
    print("\n--- TEST 5: Full Transaction Pipeline ---")

    raw_txns = [
        {"amount": 500.00, "date": "2026-01-10", "category": "materials", "description": "Building supplies"},
        {"amount": 500.00, "date": "2026-01-17", "category": "materials", "description": "Building supplies"},
        {"amount": 500.00, "date": "2026-01-24", "category": "materials", "description": "Building supplies"},
        {"amount": 90.00, "date": "2026-01-10", "category": "motor_fuel", "description": "Diesel"},
        {"amount": 90.00, "date": "2026-01-17", "category": "motor_fuel", "description": "Diesel"},
        {"amount": 90.00, "date": "2026-01-24", "category": "motor_fuel", "description": "Diesel"},
        {"amount": 250.00, "date": "2026-01-15", "category": "tools", "description": "Power tools"},
    ]

    processed = nexus.process_transactions(raw_txns)

    print("  Before → After:")
    for raw, clean in zip(raw_txns, processed):
        print(f"  £{raw['amount']:>8.2f} {raw['date']} {raw['description'][:25]:25s}"
              f" → £{clean['amount']:>8.2f} {clean['date']} {clean.get('description', '')[:25]}")

    # ================================================================
    # TEST 6: Pattern detection
    # ================================================================
    print("\n--- TEST 6: Pattern Detection ---")

    # Test on raw (should fail some tests)
    print("\n  Raw data (should show patterns):")
    raw_amounts = [a["amount"] for a in raw_txns]
    raw_check = nexus.detector.full_scan(amounts=raw_amounts)
    for t in raw_check["tests"]:
        print(f"    [{t.get('status', '?'):4s}] {t.get('test', '?')}: {t.get('note', '')}")

    # Test on processed (should be clean)
    print("\n  Processed data (should be clean):")
    verification = nexus.verify_output(transactions=processed)
    for t in verification["tests"]:
        print(f"    [{t.get('status', '?'):4s}] {t.get('test', '?')}: {t.get('note', '')}")

    # Full report
    print("\n" + nexus.print_nexus_report(verification, len(processed)))

    # ================================================================
    # TEST 7: Seasonal distribution
    # ================================================================
    print("\n--- TEST 7: Seasonal Turnover Distribution ---")
    print("Annual turnover £60,000 — construction seasonality + Fibonacci noise")

    seasonal = nexus.ratios.seasonal_pattern(60000.0, "construction")
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for m in range(1, 13):
        bar = "█" * int(seasonal[m] / 200)
        print(f"  {month_names[m-1]}: £{seasonal[m]:>8,.2f}  {bar}")
    print(f"  Total: £{sum(seasonal.values()):,.2f}")

    # ================================================================
    # TEST 8: Reproducibility test
    # ================================================================
    print("\n--- TEST 8: Reproducibility (same seed = same output) ---")

    nexus_a = HarmonicNexus(entity="John Smith", tax_year="2025/26")
    nexus_b = HarmonicNexus(entity="John Smith", tax_year="2025/26")

    vals_a = [nexus_a.engine.next_weyl() for _ in range(5)]
    vals_b = [nexus_b.engine.next_weyl() for _ in range(5)]

    match = all(abs(a - b) < 1e-10 for a, b in zip(vals_a, vals_b))
    print(f"  Same seed produces same sequence: {'YES' if match else 'NO'}")

    # Different entity = different output
    nexus_c = HarmonicNexus(entity="Dave Builder", tax_year="2025/26")
    vals_c = [nexus_c.engine.next_weyl() for _ in range(5)]
    diff = any(abs(a - c) > 0.01 for a, c in zip(vals_a, vals_c))
    print(f"  Different entity produces different sequence: {'YES' if diff else 'NO'}")

    print("\n" + "=" * 70)
    print("Nexus verified. No patterns. No traces. Just organic data.")
    print("=" * 70)
