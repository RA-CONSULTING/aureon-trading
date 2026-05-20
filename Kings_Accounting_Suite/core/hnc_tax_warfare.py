"""
HNC TAX WARFARE ENGINE — hnc_tax_warfare.py
=============================================
Adapted from Aureon's war_strategy.py (679 lines).

In Aureon, the War Strategy module identifies market manipulation,
hostile actors, and counter-strategies. It maps the battlefield,
identifies threats, and deploys counter-measures autonomously.

For the HNC Accountant, the SAME logic applies:
    - The BATTLEFIELD is the UK tax system
    - The ENEMY is fiscal drag, stealth taxes, hidden policy changes
    - The TARGETS are every deduction, relief, and allowance in legislation
    - The WEAPONS are legitimate planning techniques
    - The DEFENCE is HMRC-proof documentation

AUREON WAR STRATEGY          →  HNC TAX WARFARE
──────────────────────────────────────────────────
Threat Assessment            →  HMRC Enquiry Risk Assessment
Attack Vectors               →  Tax Saving Vectors (legal deductions)
Counter-Strategy             →  Optimisation Strategy
Battlefield Map              →  UK Tax Landscape Map
Kill List                    →  Savings Kill List (ranked by impact)
Defence Grid                 →  Documentation Defence Grid
War Chest                    →  Tax Reserve War Chest
Intel Network                →  Open Source Tax Intelligence

The philosophy: The government changes the rules every year.
Most people don't notice. We notice EVERYTHING.

Legal basis:
    - IRC v Duke of Westminster [1936] AC 1 — legitimate tax planning
    - Ramsay v IRC [1982] AC 300 — anti-avoidance boundary
    - HMRC's own manuals are published intelligence (BIM, CGM, PAYE, etc.)
    - Freedom of Information Act 2000 — HMRC statistics are public data
    - All optimisations use legislation as Parliament wrote it

Aureon Creator / Aureon Research — April 2026
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import date, datetime
from enum import Enum

logger = logging.getLogger("hnc_tax_warfare")


# ═══════════════════════════════════════════════════════════════════
# THREAT LEVELS — How aggressive is HMRC's current stance?
# ═══════════════════════════════════════════════════════════════════

class ThreatLevel(Enum):
    """Current HMRC enforcement posture"""
    GREEN = "GREEN"        # Low activity, routine checks only
    AMBER = "AMBER"        # Sector-targeted campaigns running
    RED = "RED"            # Active enquiry wave, aggressive posture
    BLACK = "BLACK"        # Emergency powers invoked (pandemic-style)


class WeaponType(Enum):
    """Categories of legitimate tax planning weapons"""
    ALLOWANCE = "ALLOWANCE"          # Personal allowances, thresholds
    DEDUCTION = "DEDUCTION"          # Business expenses, costs
    RELIEF = "RELIEF"                # Specific reliefs (pension, EIS, etc.)
    TIMING = "TIMING"                # Accelerate/defer income or costs
    STRUCTURAL = "STRUCTURAL"        # Business structure optimisation
    CREDIT = "CREDIT"                # Tax credits (CIS, R&D, etc.)
    EXEMPTION = "EXEMPTION"          # CGT annual exempt, ISA, etc.


class RiskLevel(Enum):
    """Risk of HMRC challenge"""
    BULLETPROOF = "BULLETPROOF"      # In the legislation, no grey area
    LOW = "LOW"                      # Standard practice, rarely challenged
    MEDIUM = "MEDIUM"                # May attract enquiry, defensible
    ELEVATED = "ELEVATED"            # Will be questioned, needs strong docs


# ═══════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════

@dataclass
class TaxWeapon:
    """A single legitimate tax planning technique"""
    name: str
    weapon_type: WeaponType
    description: str
    annual_saving: float           # Estimated annual tax saving
    legal_basis: str               # Legislation reference
    risk_level: RiskLevel
    auto_apply: bool               # Can be applied without user action
    evidence_required: List[str]   # What docs are needed
    hmrc_manual_ref: str = ""      # HMRC's own guidance
    action_required: str = ""      # What user needs to do
    conditions: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class BattlefieldSector:
    """A sector of the UK tax battlefield"""
    name: str
    description: str
    current_threat: ThreatLevel
    hmrc_focus_2025_26: str       # What HMRC is targeting this year
    our_exposure: float            # How much of our income is in this sector
    weapons_available: List[str]   # Names of weapons that apply
    intelligence_source: str       # Where we get our intel


@dataclass
class WarfareVerdict:
    """Complete warfare assessment"""
    total_weapons: int
    total_annual_saving: float
    bulletproof_saving: float      # Zero-risk savings
    low_risk_saving: float
    medium_risk_saving: float
    kill_list: List[TaxWeapon]     # Ranked by impact
    battlefield_assessment: str
    threat_level: ThreatLevel
    defence_readiness: float       # 0.0-1.0
    war_chest_reserve: float       # Recommended tax reserve
    action_items: List[str]
    intelligence_brief: str


# ═══════════════════════════════════════════════════════════════════
# UK TAX BATTLEFIELD MAP — 2025/26
# ═══════════════════════════════════════════════════════════════════

UK_BATTLEFIELD = {
    "income_tax": BattlefieldSector(
        name="Income Tax",
        description="Self-employment income via SA103",
        current_threat=ThreatLevel.AMBER,
        hmrc_focus_2025_26="Construction CIS subcontractors, cash businesses, online sellers",
        our_exposure=1.0,
        weapons_available=[
            "personal_allowance", "marriage_allowance", "pension_relief",
            "mileage_deduction", "home_office", "training_cpd",
            "ppe_clothing", "phone_broadband", "professional_subs",
            "loss_relief_offset", "simplified_expenses",
        ],
        intelligence_source="HMRC Annual Report, SA Filing Stats (published)",
    ),
    "national_insurance": BattlefieldSector(
        name="National Insurance",
        description="Class 2 + Class 4 NIC on self-employment profits",
        current_threat=ThreatLevel.GREEN,
        hmrc_focus_2025_26="NI cut to 6% Class 4 — government gave ground here",
        our_exposure=1.0,
        weapons_available=[
            "profit_reduction_all", "class2_threshold_check",
            "deferment_if_employed",
        ],
        intelligence_source="NIC Act 2015, Finance Act 2024 s.1",
    ),
    "cis_construction": BattlefieldSector(
        name="CIS Tax Credits",
        description="20% deducted at source from construction payments",
        current_threat=ThreatLevel.GREEN,
        hmrc_focus_2025_26="Gross payment status compliance checks",
        our_exposure=1.0,
        weapons_available=[
            "cis_credit_reclaim", "cis_refund_claim",
            "gross_payment_status_application",
        ],
        intelligence_source="Finance Act 2004 Part 3, CIS340",
    ),
    "capital_allowances": BattlefieldSector(
        name="Capital Allowances",
        description="AIA and WDA on plant/machinery/vehicles",
        current_threat=ThreatLevel.GREEN,
        hmrc_focus_2025_26="AIA still at £1m — use it",
        our_exposure=0.3,
        weapons_available=[
            "aia_full_deduction", "wda_18_main_pool",
            "wda_6_special_rate", "vehicle_capital_allowance",
        ],
        intelligence_source="CAA 2001, HMRC CA Manual",
    ),
    "vat": BattlefieldSector(
        name="VAT",
        description="Registration threshold £90k, flat rate, MTD",
        current_threat=ThreatLevel.AMBER,
        hmrc_focus_2025_26="MTD enforcement, flat rate scheme abuse detection",
        our_exposure=0.6,
        weapons_available=[
            "flat_rate_scheme", "voluntary_registration_input_recovery",
            "partial_exemption", "capital_goods_scheme",
        ],
        intelligence_source="VATA 1994, VAT Notice 733, MTD regulations",
    ),
    "capital_gains": BattlefieldSector(
        name="Capital Gains Tax",
        description="CGT on disposals — crypto, property, shares",
        current_threat=ThreatLevel.AMBER,
        hmrc_focus_2025_26="Crypto nudge letters, annual exempt cut to £3k",
        our_exposure=0.2,
        weapons_available=[
            "annual_exempt_amount", "bed_and_spouse", "loss_offset",
            "entrepreneurs_relief_if_qualifying", "gift_relief",
        ],
        intelligence_source="TCGA 1992, CG Manual, HMRC Cryptoasset Guidance",
    ),
}


# ═══════════════════════════════════════════════════════════════════
# WEAPONS ARSENAL — Every Legitimate Tax Planning Technique
# ═══════════════════════════════════════════════════════════════════

def build_weapons_arsenal(
    gross_income: float = 51_000,
    net_profit: float = 25_000,
    cis_deducted: float = 10_200,
    partner_income: float = 0,
    mileage_estimate: float = 8_000,
    has_vehicle_purchase: bool = False,
    vehicle_cost: float = 0,
    pension_contributions: float = 0,
    home_office_months: int = 12,
) -> List[TaxWeapon]:
    """
    Build the full weapons arsenal based on the taxpayer's position.
    Every weapon is grounded in legislation. No grey areas.
    """

    basic_rate_limit = 37_700
    personal_allowance = 12_570
    higher_rate = 0.40
    basic_rate = 0.20
    class4_rate = 0.06

    taxable_income = max(0, net_profit - personal_allowance)
    current_tax = 0
    if taxable_income <= basic_rate_limit:
        current_tax = taxable_income * basic_rate
    else:
        current_tax = basic_rate_limit * basic_rate + (taxable_income - basic_rate_limit) * higher_rate
    current_ni = max(0, net_profit - 12_570) * class4_rate

    weapons = []

    # ── WEAPON 1: CIS Tax Credit Reclaim ──
    if cis_deducted > 0:
        weapons.append(TaxWeapon(
            name="CIS Tax Credit Reclaim",
            weapon_type=WeaponType.CREDIT,
            description=(
                f"£{cis_deducted:,.0f} already deducted at source by contractor. "
                "This is NOT a deduction — it's tax ALREADY PAID. "
                "It comes straight off the bill. If CIS exceeds liability, HMRC refunds the excess."
            ),
            annual_saving=cis_deducted,
            legal_basis="Finance Act 2004 s.62, ITA 2007 s.59",
            risk_level=RiskLevel.BULLETPROOF,
            auto_apply=True,
            evidence_required=["CIS statements from contractor", "Monthly CIS returns"],
            hmrc_manual_ref="CISR15200",
            notes="CIS deductions are tax credits. They reduce the final bill pound for pound."
        ))

    # ── WEAPON 2: Marriage Allowance Transfer ──
    if partner_income <= personal_allowance:
        ma_saving = 1_260 * basic_rate  # £252
        weapons.append(TaxWeapon(
            name="Marriage Allowance Transfer",
            weapon_type=WeaponType.ALLOWANCE,
            description=(
                "Transfer £1,260 of spouse's unused Personal Allowance. "
                f"Saves £{ma_saving:,.0f}/year. Can backdate 4 years = £{ma_saving * 4:,.0f} total."
            ),
            annual_saving=ma_saving,
            legal_basis="ITA 2007 s.55B",
            risk_level=RiskLevel.BULLETPROOF,
            auto_apply=False,
            evidence_required=["Marriage certificate", "Spouse's income confirmation"],
            hmrc_manual_ref="EIM76200",
            conditions=["Spouse earns below Personal Allowance", "Claimant is basic rate taxpayer"],
            notes="Apply online at gov.uk. Takes 10 minutes. Can backdate to 2021/22."
        ))

    # ── WEAPON 3: Pension Relief (Nuclear Option) ──
    max_pension = min(net_profit, 60_000)  # Annual allowance
    pension_actual = min(pension_contributions, max_pension) if pension_contributions > 0 else 0
    # Suggest optimal pension contribution if not already contributing
    if pension_contributions == 0 and net_profit > personal_allowance:
        # Calculate how much to contribute to drop to basic rate
        if taxable_income > basic_rate_limit:
            optimal_pension = taxable_income - basic_rate_limit
            pension_saving = optimal_pension * higher_rate + optimal_pension * class4_rate
        else:
            optimal_pension = min(5_000, taxable_income)
            pension_saving = optimal_pension * basic_rate + optimal_pension * class4_rate
        weapons.append(TaxWeapon(
            name="Pension Relief — Drop a Tax Band",
            weapon_type=WeaponType.RELIEF,
            description=(
                f"Contribute £{optimal_pension:,.0f} to a SIPP/personal pension. "
                f"Reduces taxable income AND National Insurance. "
                f"Tax saving: £{pension_saving:,.0f}/year. Money is still yours — just tax-sheltered."
            ),
            annual_saving=pension_saving,
            legal_basis="Finance Act 2004 Part 4, ITEPA 2003 s.188",
            risk_level=RiskLevel.BULLETPROOF,
            auto_apply=False,
            evidence_required=["Pension contribution receipts", "SIPP annual statement"],
            hmrc_manual_ref="PTM044100",
            conditions=[f"Annual allowance: £60,000", "Must be registered pension scheme"],
            notes=(
                "The most powerful legal weapon in UK tax. "
                "£1 in pension saves up to 46p in tax+NI for higher rate taxpayers."
            ),
        ))
    elif pension_actual > 0:
        if taxable_income > basic_rate_limit:
            pension_saving = pension_actual * higher_rate + pension_actual * class4_rate
        else:
            pension_saving = pension_actual * basic_rate + pension_actual * class4_rate
        weapons.append(TaxWeapon(
            name="Pension Relief — Existing Contributions",
            weapon_type=WeaponType.RELIEF,
            description=f"£{pension_actual:,.0f} pension contributions reduce taxable income.",
            annual_saving=pension_saving,
            legal_basis="Finance Act 2004 Part 4",
            risk_level=RiskLevel.BULLETPROOF,
            auto_apply=True,
            evidence_required=["Pension contribution receipts"],
            hmrc_manual_ref="PTM044100",
        ))

    # ── WEAPON 4: Mileage Allowance ──
    if mileage_estimate > 0:
        first_10k = min(mileage_estimate, 10_000) * 0.45
        over_10k = max(0, mileage_estimate - 10_000) * 0.25
        mileage_deduction = first_10k + over_10k
        mileage_saving = mileage_deduction * basic_rate  # Conservative: basic rate
        weapons.append(TaxWeapon(
            name="Mileage Allowance (45p/25p)",
            weapon_type=WeaponType.DEDUCTION,
            description=(
                f"{mileage_estimate:,.0f} business miles @ HMRC approved rates. "
                f"Deduction: £{mileage_deduction:,.0f}. Tax saving: £{mileage_saving:,.0f}."
            ),
            annual_saving=mileage_saving,
            legal_basis="ITTOIA 2005 s.94D, HMRC Employment Income Manual EIM31240",
            risk_level=RiskLevel.LOW,
            auto_apply=False,
            evidence_required=["Mileage log (date, from, to, miles, purpose)", "Vehicle registration"],
            hmrc_manual_ref="BIM75005",
            conditions=["Cannot also claim actual vehicle costs", "Must keep mileage log"],
            notes="45p for first 10,000 miles, 25p thereafter. HMRC's own rates — they cannot argue."
        ))

    # ── WEAPON 5: Home Office Deduction ──
    if home_office_months > 0:
        # HMRC simplified rate: £6/week = £312/year (£26/month)
        simplified = home_office_months * 26
        # Or proportional actual costs (typically higher)
        estimated_actual = home_office_months * 80  # £80/month typical
        use_actual = estimated_actual > simplified
        home_saving = (estimated_actual if use_actual else simplified) * basic_rate
        weapons.append(TaxWeapon(
            name="Use of Home as Office",
            weapon_type=WeaponType.DEDUCTION,
            description=(
                f"{'Actual proportional costs' if use_actual else 'HMRC simplified rate'}: "
                f"£{estimated_actual if use_actual else simplified:,.0f}/year. "
                f"Tax saving: £{home_saving:,.0f}."
            ),
            annual_saving=home_saving,
            legal_basis="ITTOIA 2005 s.94G (simplified) or ITTOIA 2005 s.34 (actual)",
            risk_level=RiskLevel.BULLETPROOF if not use_actual else RiskLevel.LOW,
            auto_apply=True,
            evidence_required=(
                ["None — HMRC flat rate"] if not use_actual
                else ["Utility bills", "Mortgage/rent statement", "Floor plan with office measurement"]
            ),
            hmrc_manual_ref="BIM47820",
            notes="Simplified: no questions asked. Actual: higher but needs evidence."
        ))

    # ── WEAPON 6: Vehicle Capital Allowance (AIA) ──
    if has_vehicle_purchase and vehicle_cost > 0:
        # Van or commercial vehicle = 100% AIA
        # Car = WDA 18% or 6% depending on emissions
        aia_saving = vehicle_cost * basic_rate  # Simplified; could be higher rate
        weapons.append(TaxWeapon(
            name="Annual Investment Allowance (Vehicle)",
            weapon_type=WeaponType.DEDUCTION,
            description=(
                f"£{vehicle_cost:,.0f} vehicle purchase — 100% AIA if van/commercial. "
                f"Tax saving: £{aia_saving:,.0f} in year of purchase."
            ),
            annual_saving=aia_saving,
            legal_basis="CAA 2001 s.38A (AIA), s.104A (WDA)",
            risk_level=RiskLevel.LOW,
            auto_apply=False,
            evidence_required=[
                "Purchase invoice/HP agreement",
                "V5 registration document",
                "Evidence of business use percentage",
            ],
            hmrc_manual_ref="CA23000",
            conditions=["Van/commercial vehicle for 100% AIA", "Car = WDA only"],
        ))

    # ── WEAPON 7: PPE & Protective Clothing ──
    ppe_estimate = 250  # Conservative annual estimate for construction
    ppe_saving = ppe_estimate * basic_rate
    weapons.append(TaxWeapon(
        name="PPE & Protective Clothing",
        weapon_type=WeaponType.DEDUCTION,
        description=(
            f"Hi-vis, steel toe boots, hard hats, safety glasses — "
            f"£{ppe_estimate}/year. Tax saving: £{ppe_saving:,.0f}."
        ),
        annual_saving=ppe_saving,
        legal_basis="ITTOIA 2005 s.34, BIM37900",
        risk_level=RiskLevel.BULLETPROOF,
        auto_apply=True,
        evidence_required=["Receipts for PPE items"],
        hmrc_manual_ref="BIM37900",
        notes="Construction = obvious need. HMRC rarely challenges."
    ))

    # ── WEAPON 8: Phone & Broadband ──
    phone_estimate = 600  # £50/month typical
    phone_business_pct = 0.60
    phone_deduction = phone_estimate * phone_business_pct
    phone_saving = phone_deduction * basic_rate
    weapons.append(TaxWeapon(
        name="Phone & Broadband (Business Proportion)",
        weapon_type=WeaponType.DEDUCTION,
        description=(
            f"£{phone_estimate}/year total, {phone_business_pct:.0%} business use = "
            f"£{phone_deduction:,.0f} deduction. Saving: £{phone_saving:,.0f}."
        ),
        annual_saving=phone_saving,
        legal_basis="ITTOIA 2005 s.34",
        risk_level=RiskLevel.LOW,
        auto_apply=True,
        evidence_required=["Phone/broadband bills", "Reasonable business use estimate"],
        hmrc_manual_ref="BIM35000",
    ))

    # ── WEAPON 9: Training & CPD ──
    training_estimate = 500
    training_saving = training_estimate * basic_rate
    weapons.append(TaxWeapon(
        name="Training & CPD",
        weapon_type=WeaponType.DEDUCTION,
        description=(
            "CSCS card renewal, CITB courses, first aid, SMSTS — "
            f"£{training_estimate}/year. Saving: £{training_saving:,.0f}."
        ),
        annual_saving=training_saving,
        legal_basis="ITTOIA 2005 s.34, BIM35660",
        risk_level=RiskLevel.BULLETPROOF,
        auto_apply=True,
        evidence_required=["Course certificates", "Payment receipts"],
        hmrc_manual_ref="BIM35660",
        conditions=["Must maintain/update existing skills, not acquire new trade"],
    ))

    # ── WEAPON 10: Professional Subscriptions ──
    subs_estimate = 200
    subs_saving = subs_estimate * basic_rate
    weapons.append(TaxWeapon(
        name="Professional Subscriptions",
        weapon_type=WeaponType.DEDUCTION,
        description=(
            "CITB levy, FMB membership, trade body subscriptions — "
            f"£{subs_estimate}/year. Saving: £{subs_saving:,.0f}."
        ),
        annual_saving=subs_saving,
        legal_basis="ITTOIA 2005 s.34, ITA 2007 s.344",
        risk_level=RiskLevel.BULLETPROOF,
        auto_apply=True,
        evidence_required=["Subscription receipts/invoices"],
        hmrc_manual_ref="BIM42501",
    ))

    # ── WEAPON 11: Loss Relief Cross-Trade Offset ──
    # If Food Venture (food) makes a loss, offset against Grove (construction)
    weapons.append(TaxWeapon(
        name="Sideways Loss Relief (Dual Trade)",
        weapon_type=WeaponType.RELIEF,
        description=(
            "If the food trade (Food Venture) makes a loss, offset it against "
            "construction profits. Two trades = two chances."
        ),
        annual_saving=0,  # Depends on actual losses
        legal_basis="ITTOIA 2005 s.83, ITA 2007 s.64",
        risk_level=RiskLevel.LOW,
        auto_apply=True,
        evidence_required=["Separate P&L for each trade", "Evidence both are genuine trades"],
        hmrc_manual_ref="BIM85000",
        conditions=["Loss must be from a genuine commercial trade", "Claim within time limit"],
        notes="Powerful when one trade is loss-making. Food businesses often run tight."
    ))

    # ── WEAPON 12: Fiscal Drag Counter ──
    weapons.append(TaxWeapon(
        name="Fiscal Drag Counter-Strategy",
        weapon_type=WeaponType.TIMING,
        description=(
            "Personal Allowance frozen at £12,570 until 2028. "
            "Every year, inflation pushes more income into tax bands. "
            "Counter: maximise deductions NOW while allowance is eroding. "
            "Accelerate expenses into current year. Defer income if possible."
        ),
        annual_saving=0,  # Strategic, not directly calculable
        legal_basis="Income Tax Act 2007 — thresholds as set by Parliament",
        risk_level=RiskLevel.BULLETPROOF,
        auto_apply=False,
        evidence_required=[],
        notes="This is the government's biggest stealth tax. Fight it with timing."
    ))

    # ── WEAPON 13: Bad Debt Relief ──
    weapons.append(TaxWeapon(
        name="Bad Debt Relief",
        weapon_type=WeaponType.RELIEF,
        description=(
            "Any invoiced work that was never paid can be written off. "
            "Reduces taxable profits. Also recoverable for VAT if VAT-registered."
        ),
        annual_saving=0,  # Depends on actual bad debts
        legal_basis="ITTOIA 2005 s.35, VATA 1994 s.36",
        risk_level=RiskLevel.LOW,
        auto_apply=False,
        evidence_required=["Original invoice", "Evidence of chasing payment", "Write-off decision"],
        hmrc_manual_ref="BIM42700",
    ))

    # ── WEAPON 14: Simplified Expenses (Vehicles) ──
    if mileage_estimate > 0:
        # Compare simplified vs actual and tell user which wins
        weapons.append(TaxWeapon(
            name="Simplified vs Actual Cost Arbitrage",
            weapon_type=WeaponType.TIMING,
            description=(
                "HMRC allows two methods for vehicle costs. We calculate BOTH "
                "and use whichever gives the bigger deduction. Legal. "
                "Most accountants just pick one."
            ),
            annual_saving=0,  # Calculated at runtime by comparing both
            legal_basis="ITTOIA 2005 s.94D",
            risk_level=RiskLevel.BULLETPROOF,
            auto_apply=True,
            evidence_required=["Vehicle receipts OR mileage log (whichever method chosen)"],
            hmrc_manual_ref="BIM75005",
        ))

    # Sort by saving (highest first), then by risk (lowest first)
    risk_order = {RiskLevel.BULLETPROOF: 0, RiskLevel.LOW: 1, RiskLevel.MEDIUM: 2, RiskLevel.ELEVATED: 3}
    weapons.sort(key=lambda w: (-w.annual_saving, risk_order.get(w.risk_level, 9)))

    return weapons


# ═══════════════════════════════════════════════════════════════════
# GOVERNMENT MOVE TRACKER — What They Changed and Our Counter
# ═══════════════════════════════════════════════════════════════════

GOVERNMENT_MOVES_2024_26 = [
    {
        "move": "Froze Personal Allowance at £12,570 until 2028",
        "year": "2021 (extended 2024)",
        "stealth_cost": "£500-1,500/year depending on income growth",
        "our_counter": "Maximise deductions to keep taxable income below thresholds. Pension contributions.",
        "legislation": "Income Tax Act 2007 s.35",
    },
    {
        "move": "Cut CGT Annual Exempt Amount from £12,300 to £3,000",
        "year": "2023-2024",
        "stealth_cost": "£1,860 extra CGT/year at 20% on gains above £3k",
        "our_counter": "Use annual exempt, bed-and-spouse, loss harvesting. Time disposals across tax years.",
        "legislation": "TCGA 1992 s.3",
    },
    {
        "move": "Cut NI Class 4 from 9% to 6%",
        "year": "2024",
        "stealth_cost": "NONE — this is a rare government give-back",
        "our_counter": "Take the win. But note: they'll claw it back elsewhere.",
        "legislation": "National Insurance Contributions Act 2015 (as amended)",
    },
    {
        "move": "MTD for Income Tax from April 2026",
        "year": "2026",
        "stealth_cost": "Compliance cost + quarterly reporting burden",
        "our_counter": "Automate everything. This system IS the MTD solution. Every transaction already categorised.",
        "legislation": "Finance (No. 2) Act 2017",
    },
    {
        "move": "Dividend allowance cut to £500",
        "year": "2024",
        "stealth_cost": "Up to £1,350 extra tax for directors (£6k * 33.75% - £500 * 33.75%)",
        "our_counter": "Salary vs dividend mix optimisation for any future Ltd structure.",
        "legislation": "ITTOIA 2005 s.13A",
    },
    {
        "move": "Employer NI increase to 15% + threshold drop to £5k",
        "year": "2025",
        "stealth_cost": "Increases cost of employing staff; sole traders unaffected directly",
        "our_counter": "Stay sole trader or subcontractor where possible. If employing: use Employment Allowance.",
        "legislation": "National Insurance Contributions Act 2025",
    },
    {
        "move": "VAT threshold frozen at £90,000",
        "year": "2024-2026",
        "stealth_cost": "More businesses dragged into VAT net by inflation",
        "our_counter": "Monitor turnover carefully. Flat Rate Scheme if beneficial. Voluntary registration for input recovery.",
        "legislation": "VATA 1994 s.3, Sch 1",
    },
]


# ═══════════════════════════════════════════════════════════════════
# HMRC ENFORCEMENT INTELLIGENCE — What They're Actively Hunting
# ═══════════════════════════════════════════════════════════════════

HMRC_ENFORCEMENT_2025_26 = [
    {
        "target": "CIS Non-Compliance",
        "risk": "MEDIUM",
        "what_they_check": "Subcontractors claiming too many expenses vs CIS certificates shown",
        "our_defence": "Full CIS reconciliation. Every certificate matched. Every deduction documented.",
        "source": "HMRC Compliance Handbook CH402000",
    },
    {
        "target": "Cash Business Under-Reporting",
        "risk": "HIGH for cash-heavy businesses",
        "what_they_check": "Bank deposits vs declared income. Lifestyle inconsistencies.",
        "our_defence": "Full bank reconciliation. Every deposit traced. Food Venture food takings recorded.",
        "source": "HMRC Connect system, CH405000",
    },
    {
        "target": "Crypto Under-Reporting",
        "risk": "MEDIUM — nudge letter campaign active",
        "what_they_check": "Exchange data sharing (Coinbase, Binance), cross-referencing with SA returns",
        "our_defence": "Full cost basis tracking via King Accounting. Every trade documented.",
        "source": "HMRC Cryptoasset Manual CRYPTO01000",
    },
    {
        "target": "Expense Inflation",
        "risk": "MEDIUM for construction",
        "what_they_check": "Expense ratios vs sector benchmarks. Materials, motor, subcontractor costs.",
        "our_defence": "Stay within HMRC sector benchmarks. Nexus randomisation prevents patterns.",
        "source": "HMRC Business Income Manual BIM35000-BIM75000",
    },
    {
        "target": "Incorrect Loss Claims",
        "risk": "LOW unless repeated",
        "what_they_check": "Sideways loss claims, hobby businesses, losses without commercial basis",
        "our_defence": "Both trades are genuine commercial operations with evidence of profit motive.",
        "source": "ITA 2007 s.66, BIM85000",
    },
]


# ═══════════════════════════════════════════════════════════════════
# THE TAX WARFARE ENGINE
# ═══════════════════════════════════════════════════════════════════

class HNCTaxWarfare:
    """
    The War Strategy Engine.

    In Aureon: identifies market manipulation, plans counter-strategies,
    deploys autonomous trading counter-measures.

    In HNC: identifies government tax moves, plans counter-strategies,
    deploys autonomous tax optimisations.

    Same logic. Different battlefield. Same goal: protect the operator.
    """

    def __init__(
        self,
        gross_income: float = 51_000,
        net_profit: float = 25_000,
        cis_deducted: float = 10_200,
        partner_income: float = 0,
        mileage_estimate: float = 8_000,
        has_vehicle_purchase: bool = False,
        vehicle_cost: float = 0,
        pension_contributions: float = 0,
        home_office_months: int = 12,
    ):
        self.gross_income = gross_income
        self.net_profit = net_profit
        self.cis_deducted = cis_deducted
        self.partner_income = partner_income
        self.mileage_estimate = mileage_estimate
        self.has_vehicle_purchase = has_vehicle_purchase
        self.vehicle_cost = vehicle_cost
        self.pension_contributions = pension_contributions
        self.home_office_months = home_office_months

        # Build arsenal
        self.weapons = build_weapons_arsenal(
            gross_income=gross_income,
            net_profit=net_profit,
            cis_deducted=cis_deducted,
            partner_income=partner_income,
            mileage_estimate=mileage_estimate,
            has_vehicle_purchase=has_vehicle_purchase,
            vehicle_cost=vehicle_cost,
            pension_contributions=pension_contributions,
            home_office_months=home_office_months,
        )

    def assess_battlefield(self) -> ThreatLevel:
        """Assess overall HMRC threat level based on our profile."""
        threats = [s.current_threat for s in UK_BATTLEFIELD.values()]
        if ThreatLevel.RED in threats:
            return ThreatLevel.RED
        if ThreatLevel.AMBER in threats:
            return ThreatLevel.AMBER
        return ThreatLevel.GREEN

    def calculate_defence_readiness(self) -> float:
        """
        Score 0.0-1.0: how well-defended is our position?
        Based on evidence availability and risk profile.
        """
        if not self.weapons:
            return 0.0
        bulletproof_count = sum(1 for w in self.weapons if w.risk_level == RiskLevel.BULLETPROOF)
        total = len(self.weapons)
        auto_count = sum(1 for w in self.weapons if w.auto_apply)
        # Score = proportion bulletproof + bonus for auto-applicable
        score = (bulletproof_count / total) * 0.7 + (auto_count / total) * 0.3
        return round(min(1.0, score), 2)

    def calculate_war_chest(self) -> float:
        """
        How much tax reserve should be held?
        Conservative estimate accounting for ALL optimisations.
        """
        total_saving = sum(w.annual_saving for w in self.weapons)
        # Naive tax
        taxable = max(0, self.net_profit - 12_570)
        if taxable <= 37_700:
            naive_tax = taxable * 0.20
        else:
            naive_tax = 37_700 * 0.20 + (taxable - 37_700) * 0.40
        naive_ni = max(0, self.net_profit - 12_570) * 0.06

        optimised_tax = max(0, naive_tax + naive_ni - total_saving)
        # Reserve = optimised tax + 10% safety margin
        return round(optimised_tax * 1.10, 2)

    def run_warfare_assessment(self) -> WarfareVerdict:
        """
        Complete warfare assessment.
        Maps the battlefield, counts the weapons, produces the kill list.
        """
        total_saving = sum(w.annual_saving for w in self.weapons)
        bulletproof = sum(w.annual_saving for w in self.weapons if w.risk_level == RiskLevel.BULLETPROOF)
        low_risk = sum(w.annual_saving for w in self.weapons if w.risk_level == RiskLevel.LOW)
        medium_risk = sum(w.annual_saving for w in self.weapons if w.risk_level == RiskLevel.MEDIUM)

        threat = self.assess_battlefield()
        readiness = self.calculate_defence_readiness()
        war_chest = self.calculate_war_chest()

        # Action items: weapons that need user action
        actions = []
        for w in self.weapons:
            if not w.auto_apply and w.annual_saving > 0:
                actions.append(f"[£{w.annual_saving:,.0f}] {w.name}: {w.action_required or w.description[:80]}")

        # Intelligence brief
        govt_moves = len(GOVERNMENT_MOVES_2024_26)
        enforcement_targets = len(HMRC_ENFORCEMENT_2025_26)
        brief = (
            f"INTELLIGENCE BRIEF — Tax Year 2025/26\n"
            f"Government made {govt_moves} significant moves since 2024. "
            f"HMRC has {enforcement_targets} active enforcement targets. "
            f"Overall threat level: {threat.value}. "
            f"Our defence readiness: {readiness:.0%}. "
            f"Arsenal: {len(self.weapons)} weapons, £{total_saving:,.0f} total saving potential. "
            f"Recommended war chest reserve: £{war_chest:,.0f}."
        )

        # Battlefield assessment
        if total_saving > self.net_profit * 0.30:
            assessment = "DOMINANT — Tax position is heavily optimised. Well above average."
        elif total_saving > self.net_profit * 0.15:
            assessment = "STRONG — Good optimisation. Room for improvement in timing strategies."
        elif total_saving > self.net_profit * 0.05:
            assessment = "ADEQUATE — Basic reliefs claimed but missing advanced strategies."
        else:
            assessment = "EXPOSED — Minimal optimisation. Paying significantly more than necessary."

        return WarfareVerdict(
            total_weapons=len(self.weapons),
            total_annual_saving=total_saving,
            bulletproof_saving=bulletproof,
            low_risk_saving=low_risk,
            medium_risk_saving=medium_risk,
            kill_list=self.weapons,
            battlefield_assessment=assessment,
            threat_level=threat,
            defence_readiness=readiness,
            war_chest_reserve=war_chest,
            action_items=actions,
            intelligence_brief=brief,
        )

    def get_government_moves(self) -> List[dict]:
        """Return all tracked government policy changes."""
        return GOVERNMENT_MOVES_2024_26

    def get_enforcement_intel(self) -> List[dict]:
        """Return all current HMRC enforcement targets."""
        return HMRC_ENFORCEMENT_2025_26

    def get_battlefield_map(self) -> Dict[str, BattlefieldSector]:
        """Return the full battlefield map."""
        return UK_BATTLEFIELD


# ═══════════════════════════════════════════════════════════════════
# DEMO / TEST
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("HNC TAX WARFARE ENGINE — BATTLEFIELD ASSESSMENT")
    print("Adapted from Aureon War Strategy")
    print("=" * 70)

    warfare = HNCTaxWarfare(
        gross_income=51_000,
        net_profit=25_000,
        cis_deducted=10_200,
        partner_income=0,
        mileage_estimate=8_000,
    )

    verdict = warfare.run_warfare_assessment()

    print(f"\n{verdict.intelligence_brief}")
    print(f"\nBattlefield Assessment: {verdict.battlefield_assessment}")
    print(f"Threat Level: {verdict.threat_level.value}")
    print(f"Defence Readiness: {verdict.defence_readiness:.0%}")
    print(f"War Chest Reserve: £{verdict.war_chest_reserve:,.0f}")

    print(f"\n{'─' * 70}")
    print("KILL LIST — Ranked by Impact")
    print(f"{'─' * 70}")
    for i, w in enumerate(verdict.kill_list, 1):
        risk_badge = {
            RiskLevel.BULLETPROOF: "●",
            RiskLevel.LOW: "◐",
            RiskLevel.MEDIUM: "○",
            RiskLevel.ELEVATED: "◌",
        }.get(w.risk_level, "?")
        auto = "AUTO" if w.auto_apply else "ACTION"
        print(f"  {i:2}. {risk_badge} [{auto:6}] £{w.annual_saving:>8,.0f}  {w.name}")
        print(f"      Legal: {w.legal_basis}")

    print(f"\n{'─' * 70}")
    print("TOTAL SAVINGS BREAKDOWN")
    print(f"{'─' * 70}")
    print(f"  Bulletproof (zero risk):  £{verdict.bulletproof_saving:>8,.0f}")
    print(f"  Low risk:                 £{verdict.low_risk_saving:>8,.0f}")
    print(f"  Medium risk:              £{verdict.medium_risk_saving:>8,.0f}")
    print(f"  TOTAL:                    £{verdict.total_annual_saving:>8,.0f}")

    print(f"\n{'─' * 70}")
    print("GOVERNMENT MOVES — What They Did & Our Counter")
    print(f"{'─' * 70}")
    for move in warfare.get_government_moves():
        print(f"\n  MOVE: {move['move']}")
        print(f"  COST: {move['stealth_cost']}")
        print(f"  OUR COUNTER: {move['our_counter']}")

    print(f"\n{'─' * 70}")
    print("HMRC ENFORCEMENT TARGETS — What They're Hunting")
    print(f"{'─' * 70}")
    for target in warfare.get_enforcement_intel():
        print(f"\n  TARGET: {target['target']} [{target['risk']}]")
        print(f"  CHECKS: {target['what_they_check']}")
        print(f"  DEFENCE: {target['our_defence']}")
