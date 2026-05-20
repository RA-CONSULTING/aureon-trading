"""
HNC AURIS VALIDATOR — hnc_auris_validator.py
==============================================
Adapted from Aureon's validator_auris.py (155 lines).

In Aureon, the Auris Validator is a streaming metric processor that
validates Schumann harmonic signals in real-time. It scores coherence,
detects lock states, and checks prime alignment.

For the HNC Accountant, the Validator does the same for tax returns:
    - Validates every line of the SA103 against benchmarks
    - Checks internal consistency (do the numbers add up?)
    - Detects anomalies that would trigger HMRC review
    - Scores overall return quality (like Schumann coherence)
    - Produces a pass/fail for each validation check

AUREON VALIDATOR              →  HNC TAX VALIDATOR
──────────────────────────────────────────────────
tanh_softclip()              →  Soft threshold (gradual flag, not binary)
bandpass_env()               →  Acceptable range check
coh_score()                  →  Return coherence score
schumann_lock()              →  Benchmark lock (within HMRC norms)
prime_alignment()            →  Cross-reference alignment
ten_nine_one_concordance()   →  Box concordance (SA103 boxes consistent)

Aureon Creator / Aureon Research — April 2026
"""

from __future__ import annotations
import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger("hnc_auris_validator")

PHI = (1 + math.sqrt(5)) / 2


# ═══════════════════════════════════════════════════════════════════
# VALIDATION RESULTS
# ═══════════════════════════════════════════════════════════════════

class ValidationResult(Enum):
    """Result of a validation check"""
    PASS = "PASS"              # Within acceptable range
    SOFT_FAIL = "SOFT_FAIL"    # Marginal — worth checking
    HARD_FAIL = "HARD_FAIL"    # Outside acceptable range — must fix
    ANOMALY = "ANOMALY"        # Unexpected pattern — investigate


@dataclass
class ValidationCheck:
    """A single validation check result"""
    check_name: str
    area: str                  # SA103 box or section
    result: ValidationResult
    value: float               # The actual value
    expected_range: Tuple[float, float]  # Acceptable range
    score: float               # 0-1 quality score
    message: str


@dataclass
class ReturnValidation:
    """Complete validation of a tax return"""
    total_checks: int
    passed: int
    soft_fails: int
    hard_fails: int
    anomalies: int
    coherence_score: float      # Overall return quality (0-1)
    benchmark_locked: bool      # All ratios within HMRC norms?
    checks: List[ValidationCheck]
    summary: str
    ready_to_file: bool


# ═══════════════════════════════════════════════════════════════════
# VALIDATION FUNCTIONS — Adapted from Auris
# ═══════════════════════════════════════════════════════════════════

def tanh_softclip(value: float, threshold: float, steepness: float = 5.0) -> float:
    """
    Soft threshold function — adapted from Auris tanh_softclip.
    Returns 0 at threshold, approaches 1 as value exceeds threshold.
    Gives gradual warnings instead of binary pass/fail.
    """
    return math.tanh(steepness * (value - threshold) / threshold) if threshold != 0 else 0


def bandpass_check(value: float, low: float, high: float) -> Tuple[float, ValidationResult]:
    """
    Check if value is within acceptable range.
    Adapted from Auris bandpass_env.
    Returns (score, result) where score is 0-1.
    """
    if low <= value <= high:
        # Within range — score based on distance from centre
        mid = (low + high) / 2
        span = (high - low) / 2
        if span > 0:
            score = 1 - abs(value - mid) / span * 0.3  # Never below 0.7 if in range
        else:
            score = 1.0
        return score, ValidationResult.PASS

    # Outside range
    if value < low:
        distance = (low - value) / low if low > 0 else abs(value)
    else:
        distance = (value - high) / high if high > 0 else abs(value)

    if distance < 0.15:
        return 0.6, ValidationResult.SOFT_FAIL
    return 0.3, ValidationResult.HARD_FAIL


def coherence_score(checks: List[ValidationCheck]) -> float:
    """
    Overall return coherence — adapted from Auris coh_score.
    Weighted average of all check scores.
    """
    if not checks:
        return 0.0

    total_weight = 0
    weighted_score = 0
    for check in checks:
        # Weight by importance: hard fails matter more
        weight = {
            ValidationResult.PASS: 1.0,
            ValidationResult.SOFT_FAIL: 1.5,
            ValidationResult.HARD_FAIL: 2.0,
            ValidationResult.ANOMALY: 1.8,
        }.get(check.result, 1.0)
        weighted_score += check.score * weight
        total_weight += weight

    return weighted_score / total_weight if total_weight > 0 else 0


def benchmark_lock(checks: List[ValidationCheck]) -> bool:
    """
    Are all checks within HMRC benchmarks?
    Adapted from Auris schumann_lock.
    """
    return all(c.result in (ValidationResult.PASS, ValidationResult.SOFT_FAIL) for c in checks)


# ═══════════════════════════════════════════════════════════════════
# THE VALIDATOR ENGINE
# ═══════════════════════════════════════════════════════════════════

class HNCAurisValidator:
    """
    Tax Return Validation Engine.
    Adapted from Auris Validator — streaming metric processor
    turned into SA103 return validator.
    """

    def __init__(self, sector: str = "construction_subcontractor"):
        self.sector = sector
        # HMRC sector benchmarks (construction subcontractor)
        self.benchmarks = {
            "gross_profit_margin": (0.40, 0.70),
            "net_profit_margin": (0.20, 0.50),
            "materials_pct": (0.10, 0.35),
            "motor_pct": (0.03, 0.15),
            "admin_pct": (0.01, 0.08),
            "other_direct_pct": (0.03, 0.20),
            "cis_rate": (0.18, 0.22),  # Should be ~20%
        }

    def validate_return(
        self,
        turnover: float,
        cost_of_sales: float = 0,
        construction: float = 0,
        other_direct: float = 0,
        motor: float = 0,
        premises: float = 0,
        admin: float = 0,
        interest: float = 0,
        other_finance: float = 0,
        depreciation: float = 0,
        other_expenses: float = 0,
        net_profit: float = 0,
        cis_deducted: float = 0,
    ) -> ReturnValidation:
        """Validate a complete SA103 return."""

        checks: List[ValidationCheck] = []
        total_expenses = (cost_of_sales + construction + other_direct + motor +
                         premises + admin + interest + other_finance +
                         depreciation + other_expenses)

        if turnover <= 0:
            return ReturnValidation(
                total_checks=0, passed=0, soft_fails=0, hard_fails=0,
                anomalies=0, coherence_score=0, benchmark_locked=False,
                checks=[], summary="No turnover — cannot validate.",
                ready_to_file=False,
            )

        # ── CHECK 1: Turnover ≥ Total Income declared ──
        checks.append(self._check_arithmetic(turnover, total_expenses, net_profit))

        # ── CHECK 2: Gross Profit Margin ──
        gp_margin = (turnover - cost_of_sales) / turnover
        score, result = bandpass_check(gp_margin, *self.benchmarks["gross_profit_margin"])
        checks.append(ValidationCheck(
            check_name="Gross Profit Margin",
            area="Overall",
            result=result,
            value=gp_margin,
            expected_range=self.benchmarks["gross_profit_margin"],
            score=score,
            message=f"GP margin {gp_margin:.1%} (expected {self.benchmarks['gross_profit_margin'][0]:.0%}-{self.benchmarks['gross_profit_margin'][1]:.0%})"
        ))

        # ── CHECK 3: Net Profit Margin ──
        np_margin = net_profit / turnover
        score, result = bandpass_check(np_margin, *self.benchmarks["net_profit_margin"])
        checks.append(ValidationCheck(
            check_name="Net Profit Margin",
            area="Box 29",
            result=result,
            value=np_margin,
            expected_range=self.benchmarks["net_profit_margin"],
            score=score,
            message=f"NP margin {np_margin:.1%} (expected {self.benchmarks['net_profit_margin'][0]:.0%}-{self.benchmarks['net_profit_margin'][1]:.0%})"
        ))

        # ── CHECK 4: Motor Expenses Ratio ──
        if motor > 0:
            motor_pct = motor / turnover
            score, result = bandpass_check(motor_pct, *self.benchmarks["motor_pct"])
            checks.append(ValidationCheck(
                check_name="Motor Expenses Ratio",
                area="Box 13",
                result=result,
                value=motor_pct,
                expected_range=self.benchmarks["motor_pct"],
                score=score,
                message=f"Motor {motor_pct:.1%} of turnover (benchmark {self.benchmarks['motor_pct'][0]:.0%}-{self.benchmarks['motor_pct'][1]:.0%})"
            ))

        # ── CHECK 5: Admin Ratio ──
        if admin > 0:
            admin_pct = admin / turnover
            score, result = bandpass_check(admin_pct, *self.benchmarks["admin_pct"])
            checks.append(ValidationCheck(
                check_name="Admin Expenses Ratio",
                area="Box 15",
                result=result,
                value=admin_pct,
                expected_range=self.benchmarks["admin_pct"],
                score=score,
                message=f"Admin {admin_pct:.1%} of turnover"
            ))

        # ── CHECK 6: Other Direct Costs Ratio ──
        if other_direct > 0:
            od_pct = other_direct / turnover
            score, result = bandpass_check(od_pct, *self.benchmarks["other_direct_pct"])
            checks.append(ValidationCheck(
                check_name="Other Direct Costs Ratio",
                area="Box 12",
                result=result,
                value=od_pct,
                expected_range=self.benchmarks["other_direct_pct"],
                score=score,
                message=f"Other direct {od_pct:.1%} of turnover"
            ))

        # ── CHECK 7: CIS Deduction Rate ──
        if cis_deducted > 0:
            cis_rate = cis_deducted / turnover
            score, result = bandpass_check(cis_rate, *self.benchmarks["cis_rate"])
            checks.append(ValidationCheck(
                check_name="CIS Deduction Rate",
                area="CIS",
                result=result,
                value=cis_rate,
                expected_range=self.benchmarks["cis_rate"],
                score=score,
                message=f"CIS rate {cis_rate:.1%} (expected ~20%)"
            ))

        # ── CHECK 8: Depreciation Add-Back ──
        if depreciation > 0:
            checks.append(ValidationCheck(
                check_name="Depreciation Disallowable",
                area="Box 20",
                result=ValidationResult.SOFT_FAIL,
                value=depreciation,
                expected_range=(0, 0),
                score=0.7,
                message=f"Depreciation £{depreciation:,.0f} — must be added back (Box 20 is disallowable)"
            ))

        # ── CHECK 9: Round Number Detection (Anomaly) ──
        expense_boxes = [cost_of_sales, other_direct, motor, admin, other_expenses]
        round_count = sum(1 for e in expense_boxes if e > 0 and e % 100 == 0)
        if round_count >= 3:
            soft_score = max(0.4, 1 - round_count * 0.15)
            checks.append(ValidationCheck(
                check_name="Round Number Anomaly",
                area="Multiple Boxes",
                result=ValidationResult.ANOMALY,
                value=round_count,
                expected_range=(0, 2),
                score=soft_score,
                message=f"{round_count} boxes have exact round numbers — HMRC may view as estimates"
            ))

        # ── CHECK 10: Zero Boxes Check ──
        zero_boxes = sum(1 for e in expense_boxes if e == 0)
        if zero_boxes >= 4:
            checks.append(ValidationCheck(
                check_name="Empty Categories Warning",
                area="SA103",
                result=ValidationResult.SOFT_FAIL,
                value=zero_boxes,
                expected_range=(0, 3),
                score=0.65,
                message=f"{zero_boxes}/5 expense categories are zero — unusual for active business"
            ))

        # ── COMPUTE FINAL SCORES ──
        coh = coherence_score(checks)
        locked = benchmark_lock(checks)

        passed = sum(1 for c in checks if c.result == ValidationResult.PASS)
        soft_fails = sum(1 for c in checks if c.result == ValidationResult.SOFT_FAIL)
        hard_fails = sum(1 for c in checks if c.result == ValidationResult.HARD_FAIL)
        anomalies = sum(1 for c in checks if c.result == ValidationResult.ANOMALY)

        ready = hard_fails == 0 and coh >= 0.70

        summary = (
            f"Validated {len(checks)} checks. "
            f"Passed: {passed}, Soft fails: {soft_fails}, Hard fails: {hard_fails}, Anomalies: {anomalies}. "
            f"Coherence: {coh:.1%}. Benchmark locked: {'YES' if locked else 'NO'}. "
            f"Ready to file: {'YES' if ready else 'NO — fix hard fails first'}."
        )

        return ReturnValidation(
            total_checks=len(checks),
            passed=passed,
            soft_fails=soft_fails,
            hard_fails=hard_fails,
            anomalies=anomalies,
            coherence_score=round(coh, 3),
            benchmark_locked=locked,
            checks=checks,
            summary=summary,
            ready_to_file=ready,
        )

    def _check_arithmetic(self, turnover: float, expenses: float, net_profit: float) -> ValidationCheck:
        """Check that turnover - expenses = net profit."""
        expected = turnover - expenses
        diff = abs(expected - net_profit)

        if diff < 1:
            return ValidationCheck(
                check_name="Arithmetic Check",
                area="SA103 Summary",
                result=ValidationResult.PASS,
                value=diff,
                expected_range=(0, 1),
                score=1.0,
                message="Turnover - Expenses = Net Profit ✓"
            )
        elif diff < 100:
            return ValidationCheck(
                check_name="Arithmetic Check",
                area="SA103 Summary",
                result=ValidationResult.SOFT_FAIL,
                value=diff,
                expected_range=(0, 1),
                score=0.7,
                message=f"Rounding difference: £{diff:.2f} (expected £{expected:,.2f}, got £{net_profit:,.2f})"
            )
        else:
            return ValidationCheck(
                check_name="Arithmetic Check",
                area="SA103 Summary",
                result=ValidationResult.HARD_FAIL,
                value=diff,
                expected_range=(0, 1),
                score=0.2,
                message=f"MISMATCH: Turnover £{turnover:,.0f} - Expenses £{expenses:,.0f} = £{expected:,.0f}, but Net Profit = £{net_profit:,.0f}"
            )


# ═══════════════════════════════════════════════════════════════════
# DEMO / TEST
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("HNC AURIS VALIDATOR — TAX RETURN VALIDATION")
    print("Adapted from Auris Validator (155 lines)")
    print("=" * 70)

    validator = HNCAurisValidator()

    # Gary's position
    result = validator.validate_return(
        turnover=51_000,
        cost_of_sales=8_000,
        other_direct=5_000,
        motor=3_000,
        admin=2_000,
        other_expenses=1_500,
        net_profit=31_500,  # 51000 - 19500
        cis_deducted=10_200,
    )

    print(f"\n{result.summary}")

    print(f"\n{'─' * 70}")
    print("VALIDATION CHECKS")
    print(f"{'─' * 70}")
    for check in result.checks:
        badge = {
            ValidationResult.PASS: "PASS",
            ValidationResult.SOFT_FAIL: "WARN",
            ValidationResult.HARD_FAIL: "FAIL",
            ValidationResult.ANOMALY: "ANOM",
        }.get(check.result, "?")
        print(f"  [{badge:4s}] {check.check_name:30s}  Score: {check.score:.2f}  {check.message}")

    print(f"\n  Coherence: {result.coherence_score:.1%}")
    print(f"  Benchmark Locked: {result.benchmark_locked}")
    print(f"  Ready to File: {result.ready_to_file}")
