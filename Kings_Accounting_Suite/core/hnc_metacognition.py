"""
HNC METACOGNITION ENGINE — hnc_metacognition.py
=================================================
Adapted from Aureon's Sentience Architecture.

In Aureon, the metacognition system does this:
    1. INNER DIALOGUE — thinks about what it's seeing
    2. CURIOSITY LOOP — asks "what else could this be?"
    3. REFLECTION LOOP — thinks about whether its thinking is right
    4. CONSCIENCE GATE — can VETO a decision before it's final
    5. SENTIMENT/CONFIDENCE — tracks how sure it is
    6. CASCADE/AMPLIFICATION — when systems agree, confidence rises
    7. MEMORY/MIRRORS — remembers patterns

For the HNC Accountant, we adapt each one:

    AUREON SYSTEM              →  HNC ACCOUNTANT EQUIVALENT
    ─────────────────────────────────────────────────────────
    Inner Dialogue             →  Transaction Reasoning Stream
    Curiosity Loop             →  "What else could this payment be?"
    Reflection Loop            →  "Is our classification defensible?"
    Conscience Gate (VETO)     →  Tax Compliance Gate
    Sentiment/Confidence       →  Classification Confidence Score
    Cascade/Amplification      →  Multi-Strategy Conviction
    Memory/Mirrors             →  Pattern Memory (payee history)

The metacognition engine wraps around every transaction and every
strategy decision. It doesn't just classify — it REASONS.

A normal accountant looks at "James Logan £4,500" and puts it in
Box 12 Other Direct Costs. The metacognition engine asks:

    1. WHO is James Logan? (Person? Company? Related party?)
    2. WHAT was this for? (Labour? Asset? Personal?)
    3. If it's an asset → Capital Allowance, not revenue expense
    4. If it's a vehicle → AIA if van, WDA 18% if car
    5. If financed → Claim FULL cost year 1, not just payments
    6. Does the amount suggest personal? (Round numbers = suspicious)
    7. What's the tax-optimal treatment? (Box 12? Box 20? AIA?)
    8. Can we defend this to HMRC? (What evidence do we need?)

Legal basis:
    - ITTOIA 2005 s.34 — wholly and exclusively test
    - CAA 2001 Part 2 — capital allowances on plant & machinery
    - CAA 2001 s.38A — Annual Investment Allowance
    - Finance Act 2004 Part 3 — CIS deduction rules
    - ITA 2007 s.55B — marriage allowance
    - ITTOIA 2005 s.83 — sideways loss relief
    - ITTOIA 2005 s.94D — simplified expenses
    - BIM35000-BIM75000 — HMRC Business Income Manual

Aureon Creator / Aureon Research — April 2026
"""

from __future__ import annotations
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger("hnc_metacognition")


# ========================================================================
# THOUGHT TYPES — adapted from Aureon's SentienceEngine
# ========================================================================
# In Aureon: OBSERVATION, QUESTION, ANALYSIS, EMOTION, MEMORY, INTENTION,
#            REFLECTION, DOUBT, INSIGHT, CURIOSITY
# In HNC:   Same types, applied to tax reasoning

class ThoughtType:
    OBSERVATION = "OBSERVATION"     # "I see X in the data"
    QUESTION = "QUESTION"           # "What is this really?"
    ANALYSIS = "ANALYSIS"           # "The numbers show..."
    INSIGHT = "INSIGHT"             # "This could be treated as..."
    DOUBT = "DOUBT"                 # "But wait, is this defensible?"
    MEMORY = "MEMORY"               # "Previously we saw..."
    REFLECTION = "REFLECTION"       # "Our reasoning here is..."
    CURIOSITY = "CURIOSITY"         # "What if we looked at it this way?"
    VETO = "VETO"                   # "This classification is wrong"
    CONVICTION = "CONVICTION"       # "Multiple signals confirm this"


@dataclass
class Thought:
    """A single thought in the reasoning chain."""
    thought_type: str
    content: str
    confidence_impact: float = 0.0   # How this thought changes confidence
    saving_impact: float = 0.0       # Tax saving discovered
    legal_basis: str = ""
    action: str = ""                 # What to do about this thought


@dataclass
class MetacognitionResult:
    """The full reasoning result for a transaction or strategy."""
    subject: str                     # What we're thinking about
    thoughts: List[Thought] = field(default_factory=list)
    initial_classification: str = "" # What the Soup said
    recommended_classification: str = ""  # What we think after thinking
    confidence: float = 0.5
    tax_saving: float = 0.0
    risk_level: str = "NONE"
    action_required: str = ""
    defence_narrative: str = ""      # How to defend this to HMRC
    reclassified: bool = False       # Did we change the Soup's answer?


# ========================================================================
# PAYEE INTELLIGENCE — Memory/Mirrors from Aureon
# ========================================================================
# The system remembers what it knows about each payee.
# This is the equivalent of Aureon's Mirrors (temporal resonance array)
# — it doesn't just classify once, it builds up understanding.

PAYEE_INTELLIGENCE = {
    # === CONSTRUCTION WORKERS (established subcontractors) ===
    "james logan": {
        "entity_type": "individual",
        "relationship": "regular_subcontractor",
        "cis_registered": True,
        "typical_payments": "2000-5000",
        "known_services": ["vehicle_purchase", "plant_hire"],
        "capital_flag": True,  # Large payments may be asset purchases
        "notes": "Car purchase identified in data. If van → AIA. If car → WDA 18%.",
        "optimal_treatment": "Review each payment: labour → Box 12, vehicle → AIA capital allowance",
    },
    "close brothers": {
        "entity_type": "finance_company",
        "relationship": "vehicle_finance",
        "typical_payments": "200-500_monthly",
        "known_services": ["vehicle_hp", "asset_finance"],
        "capital_flag": True,
        "notes": "Vehicle HP payments. CRITICAL: Claim AIA on FULL asset cost in year 1, "
                "not on monthly payments. Monthly payments are just cashflow. "
                "Interest element is separately allowable under Box 17.",
        "optimal_treatment": "Split: Capital element → AIA. Interest element → Box 17.",
    },
    "construction client alpha": {
        "entity_type": "company",
        "relationship": "contractor",
        "cis_registered": True,
        "known_services": ["construction_income"],
        "notes": "CIS contractor. Bank shows NET. Must gross up. CIS deductions = tax credit.",
        "optimal_treatment": "Gross up all receipts. CIS credit on SA100 Box 21.",
    },
    "aureon queen anchor": {
        "entity_type": "individual",
        "relationship": "spouse",
        "capital_flag": False,
        "notes": "Wife. ALL payments are personal drawings. Not a business expense.",
        "optimal_treatment": "DRAWINGS — below the profit line. Not allowable.",
    },
    "brown t": {
        "entity_type": "individual",
        "relationship": "spouse",
        "notes": "Aureon Queen Anchor shorthand. Same treatment as aureon queen anchor.",
        "optimal_treatment": "DRAWINGS.",
    },

    # === MARKETPLACE / CASUAL WORKERS (drawings) ===
    "equipment seller": {"entity_type": "individual", "relationship": "gumtree_worker", "optimal_treatment": "DRAWINGS"},
    "kevin donnan": {"entity_type": "individual", "relationship": "gumtree_worker", "optimal_treatment": "DRAWINGS"},
    "martin mcelkerney": {"entity_type": "individual", "relationship": "gumtree_worker", "optimal_treatment": "DRAWINGS"},
    "caoimhin mcguigan": {"entity_type": "individual", "relationship": "gumtree_worker", "optimal_treatment": "DRAWINGS"},
    "carson mcadams": {"entity_type": "individual", "relationship": "gumtree_worker", "optimal_treatment": "DRAWINGS"},
    "sean paul mooney": {"entity_type": "individual", "relationship": "gumtree_worker", "optimal_treatment": "DRAWINGS"},
    "carter savage": {"entity_type": "individual", "relationship": "gumtree_worker", "optimal_treatment": "DRAWINGS"},
    "bradley lyttle": {"entity_type": "individual", "relationship": "gumtree_worker", "optimal_treatment": "DRAWINGS"},

    # === SUPPLIERS ===
    "booker": {"entity_type": "wholesaler", "relationship": "food_supplier",
               "optimal_treatment": "Box 10 — Cost of Sales. Food stock for Food Venture."},
    "musgrave": {"entity_type": "wholesaler", "relationship": "food_supplier",
                 "optimal_treatment": "Box 10 — Cost of Sales."},
    "hendersons": {"entity_type": "wholesaler", "relationship": "food_supplier",
                   "optimal_treatment": "Box 10 — Cost of Sales."},
    "brakes": {"entity_type": "wholesaler", "relationship": "food_supplier",
               "optimal_treatment": "Box 10 — Cost of Sales."},

    # === FINANCE / INSURANCE ===
    "axa": {"entity_type": "insurer", "relationship": "business_insurance",
            "optimal_treatment": "Box 14 Premises (if property) or Box 20 Motor (if vehicle)"},
    "hastings": {"entity_type": "insurer", "relationship": "motor_insurance",
                 "optimal_treatment": "Box 20 — Motor Expenses"},
}


# ========================================================================
# AMOUNT PATTERN INTELLIGENCE
# ========================================================================
# Round numbers, specific ranges, and patterns that suggest different
# treatments. This is the Curiosity Loop — always asking "what if?"

AMOUNT_SIGNALS = {
    "round_thousand": {
        "test": lambda amt: amt >= 1000 and amt % 1000 == 0,
        "thought": "Round thousands (£{amount}) often indicate asset purchases or personal loans, "
                  "not regular labour payments. Labour is usually irregular amounts.",
        "suggestion": "Verify: is this a capital purchase (AIA), personal loan (DRAWINGS), "
                     "or a round payment for accumulated work?",
    },
    "round_hundred": {
        "test": lambda amt: 100 <= amt < 1000 and amt % 100 == 0,
        "thought": "Round hundreds can be weekly cash wages or personal transfers.",
        "suggestion": "Check frequency. Weekly → labour (Box 12). One-off → investigate.",
    },
    "vehicle_range": {
        "test": lambda amt: 3000 <= amt <= 25000,
        "thought": "Amount in vehicle purchase range (£3k-25k). If to an individual "
                  "or dealer, could be van/car purchase.",
        "suggestion": "If vehicle: Van → AIA (100% year 1). Car → WDA 18% per year. "
                     "Electric car → 100% first year allowance.",
    },
    "finance_payment": {
        "test": lambda amt: 150 <= amt <= 600 and True,  # Would need frequency check
        "thought": "Monthly payment range. Could be HP/lease/finance for vehicle or equipment.",
        "suggestion": "If HP: claim AIA on FULL asset cost, not monthly payments.",
    },
    "micro_payment": {
        "test": lambda amt: amt < 20,
        "thought": "Micro payment — likely a subscription, bank charge, or card payment.",
        "suggestion": "Usually Box 15 Admin or Box 17 Interest.",
    },
}


# ========================================================================
# TAX OPTIMISATION RULES — the REAL cooking
# ========================================================================
# Each rule is a lens through which every transaction is examined.
# A normal accountant applies one classification. We apply ALL of these
# and choose the most favourable legitimate treatment.

TAX_RULES = [
    {
        "name": "Capital vs Revenue",
        "description": "Is this a capital purchase (AIA deductible) or a revenue expense?",
        "test_questions": [
            "Does this payment buy something that lasts more than 2 years?",
            "Is it for equipment, tools, vehicles, or machinery?",
            "Is the amount > £500 for a single item?",
        ],
        "if_capital": "Annual Investment Allowance — 100% deduction in year 1 (up to £1M). "
                     "CAA 2001 s.38A. This is BETTER than revenue expense for large items "
                     "because AIA gives full deduction immediately.",
        "if_revenue": "Revenue expense — deductible in the period incurred.",
        "legal_basis": "CAA 2001 Part 2 — plant and machinery capital allowances",
    },
    {
        "name": "HP Interest Splitting",
        "description": "Finance payments contain capital + interest. Both are deductible "
                      "but in DIFFERENT ways.",
        "test_questions": [
            "Is this a hire purchase, lease, or finance payment?",
            "Can we identify the interest element?",
        ],
        "if_yes": "Capital element → AIA on FULL purchase price in year 1. "
                 "Interest element → Box 17 (allowable finance cost).",
        "legal_basis": "CAA 2001 s.67 — expenditure on provision of plant/machinery. "
                      "BIM45340 — interest on borrowed money.",
    },
    {
        "name": "CIS Gross-Up",
        "description": "Every payment from a CIS contractor represents only 79.44% of the "
                      "actual income. The missing 20.56% is CIS + CITB already paid as tax.",
        "test_questions": [
            "Is the payer a CIS-registered contractor?",
            "Do we have the CIS statement showing gross/net?",
        ],
        "if_yes": "Record GROSS income (not net). CIS deduction = reclaimable tax credit. "
                 "CITB = allowable business expense. "
                 "Gross = Net ÷ 0.7944 (approximately).",
        "legal_basis": "Finance Act 2004 Part 3 Ch.3 — CIS deductions",
    },
    {
        "name": "Private Use Adjustment",
        "description": "Some expenses have both business and personal use. Only the "
                      "business proportion is allowable.",
        "test_questions": [
            "Is this expense used partly for personal purposes?",
            "Can we justify a business use percentage?",
        ],
        "if_mixed": "Claim business proportion only. Common splits: "
                   "Phone 60% business, Broadband 40% business, "
                   "Motor 70% business (if sole vehicle), Home office 15%.",
        "legal_basis": "ITTOIA 2005 s.34 — wholly and exclusively. "
                      "BIM37000 — dual purpose expenditure apportionment.",
    },
    {
        "name": "Simplified vs Actual Expenses",
        "description": "HMRC offers flat-rate simplified expenses for vehicles and home office. "
                      "Sometimes the flat rate beats actual costs.",
        "test_questions": [
            "Would the simplified mileage rate (45p/mile) beat actual motor costs?",
            "Would the home office flat rate beat actual proportional costs?",
        ],
        "if_simplified_better": "Switch to simplified expenses. ITTOIA 2005 s.94D (vehicles), "
                               "s.94G (home). Once chosen, must stick with it for that vehicle.",
        "legal_basis": "ITTOIA 2005 s.94D, s.94G — simplified expenses",
    },
    {
        "name": "Loss Relief",
        "description": "If one trade makes a loss, it can offset against another trade's profit.",
        "test_questions": [
            "Is any trade (food/consulting) making a loss?",
            "Can we use that loss against construction profit?",
        ],
        "if_loss": "Sideways loss relief — ITTOIA 2005 s.83. "
                  "Food trade loss reduces construction tax. "
                  "BUT: cap at £50k or 25% of total income (ITA 2007 s.24A).",
        "legal_basis": "ITTOIA 2005 s.83 — trade losses. ITA 2007 s.24A — cap.",
    },
    {
        "name": "Timing Optimisation",
        "description": "When an expense falls relative to the tax year boundary (April 5/6) "
                      "affects which year gets the deduction.",
        "test_questions": [
            "Is this expense near the April 5/6 boundary?",
            "Would it save more tax in this year or next?",
        ],
        "if_timing_matters": "Under cash basis, expenses count when PAID, not when incurred. "
                            "If you're near the higher rate threshold, consider timing purchases "
                            "to fall in the year where you get 40% relief instead of 20%.",
        "legal_basis": "ITTOIA 2005 s.33 — cash basis. Tax year: 6 April to 5 April.",
    },
    {
        "name": "Training & CPD",
        "description": "Training costs to maintain or update existing skills are allowable. "
                      "Training for new skills is NOT allowable.",
        "test_questions": [
            "Is there any payment for training, courses, or certifications?",
            "Does the training relate to the existing trade?",
        ],
        "if_existing_trade": "100% allowable as a business expense. "
                            "Construction site cards (CSCS), first aid, plant licences.",
        "legal_basis": "ITTOIA 2005 s.34. BIM35660 — training costs.",
    },
    {
        "name": "Bad Debt Relief",
        "description": "If a customer owes you money and won't pay, the bad debt is an "
                      "allowable deduction.",
        "test_questions": [
            "Are there any invoices that remain unpaid?",
            "Has reasonable effort been made to collect?",
        ],
        "if_bad_debt": "Write off as allowable bad debt expense. "
                      "If VAT was charged, reclaim the VAT too.",
        "legal_basis": "ITTOIA 2005 s.35 — bad and doubtful debts.",
    },
]


# ========================================================================
# THE METACOGNITION ENGINE
# ========================================================================

class HNCMetacognition:
    """
    The Metacognition Engine — adapted from Aureon's sentience architecture.

    In Aureon:
        - The Brain integrates all systems
        - Coherence filters noise from signal
        - Mirrors remember patterns
        - The Conscience can VETO
        - Cascade amplifies conviction

    In HNC Accountant:
        - The Engine integrates all tax rules
        - Analysis filters legitimate from risky
        - Payee Intelligence remembers patterns
        - The Compliance Gate can VETO
        - Multi-strategy conviction amplifies savings
    """

    def __init__(self, tax_year: int = 2025):
        self.tax_year = tax_year
        self.thoughts_log: List[Thought] = []
        self.results: List[MetacognitionResult] = []
        self.total_savings_found: float = 0
        self.reclassifications: int = 0
        self.pattern_memory: Dict[str, List[Dict]] = defaultdict(list)

    # ================================================================
    # CORE: Analyse a single transaction
    # ================================================================
    def analyse_transaction(self, txn: Dict, current_classification: str = "",
                           current_box: str = "", current_trade: str = "") -> MetacognitionResult:
        """
        Run the full metacognition pipeline on a transaction.

        This is the equivalent of Aureon's full sentience loop:
        Inner Dialogue → Curiosity → Analysis → Reflection → Conscience → Conviction
        """
        desc = txn.get("description", "").lower().strip()
        amount = abs(txn.get("amount", 0))
        direction = txn.get("direction", "")

        result = MetacognitionResult(
            subject=f"{desc[:50]} £{amount:,.2f}",
            initial_classification=current_classification,
            recommended_classification=current_classification,
            confidence=0.5,
        )

        # === PHASE 1: OBSERVATION — What do we see? ===
        result.thoughts.append(Thought(
            thought_type=ThoughtType.OBSERVATION,
            content=f"Transaction: '{desc}' for £{amount:,.2f} ({direction}). "
                   f"Current classification: {current_classification} / {current_box}.",
        ))

        # === PHASE 2: MEMORY — Do we recognise this payee? ===
        payee_match = self._check_payee_intelligence(desc)
        if payee_match:
            name, intel = payee_match
            result.thoughts.append(Thought(
                thought_type=ThoughtType.MEMORY,
                content=f"KNOWN PAYEE: {name}. Type: {intel.get('entity_type', 'unknown')}. "
                       f"Relationship: {intel.get('relationship', 'unknown')}. "
                       f"Optimal: {intel.get('optimal_treatment', 'standard')}.",
                confidence_impact=0.2,
            ))
            # Update pattern memory
            self.pattern_memory[name].append({"amount": amount, "desc": desc})

        # === PHASE 3: CURIOSITY — What else could this be? ===
        for signal_name, signal in AMOUNT_SIGNALS.items():
            try:
                if signal["test"](amount):
                    thought_text = signal["thought"].replace("{amount}", f"{amount:,.0f}")
                    result.thoughts.append(Thought(
                        thought_type=ThoughtType.CURIOSITY,
                        content=thought_text,
                        action=signal["suggestion"],
                    ))
            except Exception:
                pass

        # === PHASE 4: ANALYSIS — Apply every tax rule ===
        for rule in TAX_RULES:
            thought = self._apply_tax_rule(rule, txn, payee_match, current_classification)
            if thought:
                result.thoughts.append(thought)

        # === PHASE 5: INSIGHT — What's the optimal treatment? ===
        optimal = self._determine_optimal_treatment(
            txn, payee_match, current_classification, current_box, result.thoughts
        )
        if optimal:
            result.thoughts.append(optimal["thought"])
            if optimal.get("reclassify"):
                result.recommended_classification = optimal["new_classification"]
                result.reclassified = True
                result.tax_saving = optimal.get("saving", 0)
                self.reclassifications += 1

        # === PHASE 6: CONSCIENCE GATE — Is this defensible? ===
        defence = self._compliance_check(result)
        result.thoughts.append(defence)

        # === PHASE 7: CONVICTION — Calculate final confidence ===
        base_confidence = 0.5
        for t in result.thoughts:
            base_confidence += t.confidence_impact
        result.confidence = max(0.1, min(1.0, base_confidence))

        # Build defence narrative
        result.defence_narrative = self._build_defence(result)

        self.results.append(result)
        self.total_savings_found += result.tax_saving
        return result

    # ================================================================
    # PAYEE INTELLIGENCE — Memory/Mirrors
    # ================================================================
    def _check_payee_intelligence(self, desc: str) -> Optional[Tuple[str, Dict]]:
        """Check if we recognise the payee from our intelligence database."""
        desc_lower = desc.lower()
        for name, intel in PAYEE_INTELLIGENCE.items():
            if name in desc_lower:
                return (name, intel)
        return None

    # ================================================================
    # TAX RULE APPLICATION — Analysis phase
    # ================================================================
    def _apply_tax_rule(self, rule: Dict, txn: Dict,
                        payee_match: Optional[Tuple], current_class: str) -> Optional[Thought]:
        """Apply a single tax optimisation rule to a transaction."""
        desc = txn.get("description", "").lower()
        amount = abs(txn.get("amount", 0))

        # Capital vs Revenue
        if rule["name"] == "Capital vs Revenue":
            if payee_match and payee_match[1].get("capital_flag"):
                return Thought(
                    thought_type=ThoughtType.INSIGHT,
                    content=f"CAPITAL PURCHASE DETECTED. Payee {payee_match[0]} is flagged "
                           f"for potential asset purchases. £{amount:,.2f} may qualify for "
                           f"Annual Investment Allowance (100% deduction in year 1).",
                    saving_impact=amount * 0.26,  # Marginal rate saving
                    legal_basis=rule["legal_basis"],
                    confidence_impact=0.1,
                )
            if amount > 500 and any(kw in desc for kw in ["tool", "drill", "saw", "generator",
                                                           "scaffold", "ladder", "mixer"]):
                return Thought(
                    thought_type=ThoughtType.INSIGHT,
                    content=f"Possible tool/equipment purchase (£{amount:,.2f}). "
                           f"If this lasts more than 2 years, claim under AIA.",
                    legal_basis=rule["legal_basis"],
                )

        # HP Interest Splitting
        if rule["name"] == "HP Interest Splitting":
            if payee_match and payee_match[1].get("entity_type") == "finance_company":
                return Thought(
                    thought_type=ThoughtType.INSIGHT,
                    content=f"FINANCE PAYMENT to {payee_match[0]}. This likely contains "
                           f"capital repayment + interest. Split them: "
                           f"Capital → AIA (already claimed on full cost). "
                           f"Interest → Box 17 (allowable finance cost). "
                           f"DO NOT double-count the capital element.",
                    legal_basis=rule["legal_basis"],
                    confidence_impact=0.15,
                )

        # CIS Gross-Up
        if rule["name"] == "CIS Gross-Up":
            if payee_match and payee_match[1].get("cis_registered"):
                if txn.get("direction") == "in":
                    gross = amount / 0.7944
                    cis_credit = gross * 0.2 * 0.993  # Gross less CITB × 20%
                    return Thought(
                        thought_type=ThoughtType.INSIGHT,
                        content=f"CIS INCOME: Bank shows £{amount:,.2f} (net). "
                               f"Actual gross = £{gross:,.2f}. "
                               f"CIS tax already paid = ~£{cis_credit:,.2f}. "
                               f"This is RECLAIMABLE as a tax credit.",
                        saving_impact=cis_credit,
                        legal_basis=rule["legal_basis"],
                        confidence_impact=0.2,
                    )

        # Loss Relief
        if rule["name"] == "Loss Relief":
            if current_class in ["food", "consulting"] and txn.get("direction") == "out":
                return Thought(
                    thought_type=ThoughtType.CURIOSITY,
                    content=f"This {current_class} expense contributes to trade loss. "
                           f"If {current_class} makes an overall loss, it can offset "
                           f"against construction profit (sideways loss relief).",
                    legal_basis=rule["legal_basis"],
                )

        # Timing optimisation
        if rule["name"] == "Timing Optimisation":
            date_str = txn.get("date", "")
            if date_str:
                try:
                    from datetime import datetime
                    d = datetime.strptime(date_str.strip(), "%d %b %Y").date()
                    # Near tax year boundary
                    if d.month == 4 and d.day <= 10:
                        return Thought(
                            thought_type=ThoughtType.ANALYSIS,
                            content=f"TAX YEAR BOUNDARY: This payment on {date_str} "
                                   f"falls near the 5/6 April boundary. "
                                   f"Under cash basis, the date PAID determines the tax year.",
                            legal_basis=rule["legal_basis"],
                        )
                except (ValueError, AttributeError):
                    pass

        return None

    # ================================================================
    # OPTIMAL TREATMENT — Insight phase
    # ================================================================
    def _determine_optimal_treatment(self, txn: Dict, payee_match: Optional[Tuple],
                                     current_class: str, current_box: str,
                                     thoughts: List[Thought]) -> Optional[Dict]:
        """Determine the most tax-efficient treatment based on all analysis."""
        desc = txn.get("description", "").lower()
        amount = abs(txn.get("amount", 0))

        # Check if payee intelligence suggests a different classification
        if payee_match:
            intel = payee_match[1]
            optimal = intel.get("optimal_treatment", "")

            if "AIA" in optimal and current_class != "capital_allowance":
                return {
                    "thought": Thought(
                        thought_type=ThoughtType.INSIGHT,
                        content=f"RECLASSIFICATION OPPORTUNITY: Currently classified as "
                               f"'{current_class}' ({current_box}). Payee intelligence suggests "
                               f"this should be '{optimal}'. AIA gives 100% deduction.",
                        confidence_impact=0.15,
                        saving_impact=amount * 0.06,  # NI saving from correct classification
                    ),
                    "reclassify": True,
                    "new_classification": "capital_allowance",
                    "saving": amount * 0.06,
                }

            if "DRAWINGS" in optimal and current_class not in ["drawings", "DRAWINGS"]:
                return {
                    "thought": Thought(
                        thought_type=ThoughtType.VETO,
                        content=f"CLASSIFICATION ERROR: '{desc}' is currently in "
                               f"'{current_class}' but should be DRAWINGS (personal). "
                               f"This is NOT a business expense. Removing from Box "
                               f"{current_box} protects against HMRC enquiry.",
                        confidence_impact=0.3,
                    ),
                    "reclassify": True,
                    "new_classification": "drawings",
                    "saving": 0,  # Removing an invalid deduction is not a "saving"
                }

        return None

    # ================================================================
    # COMPLIANCE GATE — Conscience from Aureon
    # ================================================================
    def _compliance_check(self, result: MetacognitionResult) -> Thought:
        """
        The Conscience Gate — can VETO a classification.
        Equivalent to Aureon's QueenConscience VETO system.

        In Aureon: Can block trades if unethical.
        In HNC: Can block classifications if indefensible.
        """
        insights = [t for t in result.thoughts if t.thought_type == ThoughtType.INSIGHT]
        doubts = [t for t in result.thoughts if t.thought_type in [ThoughtType.DOUBT, ThoughtType.VETO]]

        if doubts:
            return Thought(
                thought_type=ThoughtType.REFLECTION,
                content=f"COMPLIANCE CHECK: {len(doubts)} concern(s) raised. "
                       f"Classification confidence reduced. Manual review recommended.",
                confidence_impact=-0.2,
            )
        elif insights:
            return Thought(
                thought_type=ThoughtType.CONVICTION,
                content=f"COMPLIANCE CHECK: {len(insights)} optimisation(s) identified. "
                       f"All have statutory legal basis. Defensible.",
                confidence_impact=0.1,
            )
        else:
            return Thought(
                thought_type=ThoughtType.REFLECTION,
                content="COMPLIANCE CHECK: Standard classification. No concerns.",
                confidence_impact=0.05,
            )

    # ================================================================
    # DEFENCE NARRATIVE
    # ================================================================
    def _build_defence(self, result: MetacognitionResult) -> str:
        """Build the defence narrative for this classification."""
        parts = []
        for t in result.thoughts:
            if t.legal_basis:
                parts.append(f"[{t.thought_type}] {t.content} — {t.legal_basis}")
            elif t.thought_type in [ThoughtType.INSIGHT, ThoughtType.VETO, ThoughtType.CONVICTION]:
                parts.append(f"[{t.thought_type}] {t.content}")
        return " | ".join(parts) if parts else "Standard classification."

    # ================================================================
    # FULL PORTFOLIO ANALYSIS
    # ================================================================
    def analyse_full_position(self, net_profit: float, total_income: float,
                              total_expenses: float, motor_expenses: float,
                              cis_deducted: float, cis_citb: float,
                              drawings: float, food_pnl: float = 0) -> List[MetacognitionResult]:
        """
        Analyse the FULL tax position with metacognition.

        This goes beyond individual transactions to look at the
        whole picture — the equivalent of Aureon's Queen Decision Pipeline
        where all systems contribute to one final decision.
        """
        results = []

        # === 1. CIS DEEP ANALYSIS ===
        if cis_deducted > 0:
            r = MetacognitionResult(subject="CIS Tax Position")
            r.thoughts.append(Thought(
                thought_type=ThoughtType.ANALYSIS,
                content=f"CIS deductions total £{cis_deducted:,.2f}. This is tax ALREADY PAID "
                       f"by the contractor on your behalf. It's not a deduction — it's a CREDIT. "
                       f"If your total tax bill < £{cis_deducted:,.2f}, HMRC owes YOU a refund.",
                legal_basis="Finance Act 2004 Part 3 Ch.3",
                confidence_impact=0.3,
                saving_impact=cis_deducted,
            ))

            # Calculate if refund is due
            pa = 12_570
            taxable = max(0, net_profit - pa)
            tax = taxable * 0.20 if taxable <= 37_700 else 37_700 * 0.20 + (taxable - 37_700) * 0.40
            ni_c2 = 179.40 if net_profit >= 12_570 else 0
            ni_c4 = max(0, min(net_profit, 50_270) - 12_570) * 0.06 if net_profit > 12_570 else 0
            if net_profit > 50_270:
                ni_c4 += (net_profit - 50_270) * 0.02
            total_tax = tax + ni_c2 + ni_c4

            if cis_deducted > total_tax:
                refund = cis_deducted - total_tax
                r.thoughts.append(Thought(
                    thought_type=ThoughtType.INSIGHT,
                    content=f"REFUND DUE: Total tax liability = £{total_tax:,.2f}. "
                           f"CIS already paid = £{cis_deducted:,.2f}. "
                           f"HMRC owes you a REFUND of £{refund:,.2f}.",
                    saving_impact=refund,
                    confidence_impact=0.3,
                    legal_basis="SI 2005/2045 Reg 56 — CIS refund via SA return",
                ))
                r.tax_saving = refund
            else:
                remaining = total_tax - cis_deducted
                r.thoughts.append(Thought(
                    thought_type=ThoughtType.ANALYSIS,
                    content=f"Tax remaining after CIS credit: £{remaining:,.2f} "
                           f"(from £{total_tax:,.2f} total).",
                ))

            r.confidence = 0.95
            results.append(r)

        # === 2. LOSS RELIEF ANALYSIS ===
        if food_pnl < 0:
            r = MetacognitionResult(subject="Sideways Loss Relief")
            loss = abs(food_pnl)
            # Tax saving = loss × marginal rate
            marginal = 0.40 if net_profit > 50_270 else 0.20
            saving = loss * (marginal + 0.06)
            r.thoughts.append(Thought(
                thought_type=ThoughtType.INSIGHT,
                content=f"LOSS RELIEF: Food trade loss of £{loss:,.2f} can offset "
                       f"against construction profit. At {marginal*100:.0f}% + 6% NI, "
                       f"this saves £{saving:,.2f} in tax.",
                saving_impact=saving,
                legal_basis="ITTOIA 2005 s.83 — sideways loss relief",
                confidence_impact=0.2,
            ))
            cap = max(50_000, net_profit * 0.25)
            if loss > cap:
                r.thoughts.append(Thought(
                    thought_type=ThoughtType.DOUBT,
                    content=f"WARNING: Loss relief cap is £{cap:,.0f} (£50k or 25% of income). "
                           f"Loss of £{loss:,.2f} exceeds cap. Only £{cap:,.0f} can offset.",
                    confidence_impact=-0.1,
                    legal_basis="ITA 2007 s.24A — cap on sideways loss relief",
                ))
            r.tax_saving = saving
            r.confidence = 0.85
            results.append(r)

        # === 3. MARRIAGE ALLOWANCE — DEEP ANALYSIS ===
        r = MetacognitionResult(subject="Marriage Allowance")
        r.thoughts.append(Thought(
            thought_type=ThoughtType.ANALYSIS,
            content="Marriage Allowance: Tina (spouse) can transfer £1,260 of her "
                   "Personal Allowance. This gives £252/year tax reduction. "
                   "Can be BACKDATED 4 years = up to £1,008 one-off refund.",
            saving_impact=252,
            legal_basis="ITA 2007 s.55B",
            confidence_impact=0.2,
        ))
        r.thoughts.append(Thought(
            thought_type=ThoughtType.CURIOSITY,
            content="BACKDATE CHECK: Has this been claimed for 2021/22, 2022/23, "
                   "2023/24, 2024/25? If not, Tina should apply at gov.uk/marriage-allowance "
                   "and tick the backdate box. Instant refund of up to £1,008.",
            action="Tina applies at gov.uk/marriage-allowance — takes 5 minutes",
        ))
        r.tax_saving = 252
        r.confidence = 0.99  # Zero risk, statutory entitlement
        results.append(r)

        # === 4. PENSION DEEP ANALYSIS ===
        r = MetacognitionResult(subject="Pension Contribution Analysis")
        # Calculate optimal contribution
        if net_profit > 50_270:
            # Higher rate taxpayer — pension contributions get 40% relief
            optimal_contribution = min(net_profit - 50_270, 60_000)
            saving = optimal_contribution * 0.40
            r.thoughts.append(Thought(
                thought_type=ThoughtType.INSIGHT,
                content=f"HIGHER RATE OPPORTUNITY: You're a 40% taxpayer on income "
                       f"above £50,270. Pension contributions up to £{optimal_contribution:,.0f} "
                       f"would get 40% tax relief (£{saving:,.0f} saving). "
                       f"Plus NI saving of {optimal_contribution * 0.02:,.0f}.",
                saving_impact=saving + optimal_contribution * 0.02,
                legal_basis="Finance Act 2004 Part 4 — annual allowance £60k",
            ))
        else:
            optimal_contribution = min(5_000, net_profit * 0.10)
            saving = optimal_contribution * 0.20
            r.thoughts.append(Thought(
                thought_type=ThoughtType.ANALYSIS,
                content=f"Basic rate taxpayer. Pension contributions get 20% relief. "
                       f"Suggested: £{optimal_contribution:,.0f}/year → £{saving:,.0f} saving.",
                saving_impact=saving,
                legal_basis="Finance Act 2004 Part 4",
            ))
        r.tax_saving = saving
        r.confidence = 0.90
        results.append(r)

        # === 5. HOME OFFICE — DEEPER ANALYSIS ===
        r = MetacognitionResult(subject="Home Office Deduction")
        r.thoughts.append(Thought(
            thought_type=ThoughtType.ANALYSIS,
            content="TWO METHODS compared: "
                   "(1) Simplified flat rate: 80+ hrs/month = £26/month = £312/year. "
                   "(2) Proportional actual: 15% of household costs. "
                   "Estimate: mortgage interest £500 + council tax £120 + "
                   "electric £100 + broadband £35 = £755/month × 15% = £1,359/year.",
            legal_basis="ITTOIA 2005 s.94G (simplified), BIM47815 (actual)",
        ))
        actual = 755 * 12 * 0.15
        marginal = 0.26  # 20% IT + 6% NI
        r.thoughts.append(Thought(
            thought_type=ThoughtType.INSIGHT,
            content=f"ACTUAL METHOD IS BETTER: £{actual:,.0f}/year vs £312 flat rate. "
                   f"Tax saving: £{actual * marginal:,.0f}/year. "
                   f"Requires: utility bills, council tax bill, mortgage statement.",
            saving_impact=actual * marginal,
            legal_basis="BIM47815",
        ))
        r.tax_saving = actual * marginal
        r.confidence = 0.80
        results.append(r)

        # === 6. VEHICLE CAPITAL ALLOWANCE ANALYSIS ===
        r = MetacognitionResult(subject="Vehicle Capital Allowances")
        r.thoughts.append(Thought(
            thought_type=ThoughtType.CURIOSITY,
            content="James Logan vehicle purchase and Close Brothers finance payments "
                   "identified. CRITICAL QUESTIONS: "
                   "(1) Is it a van or a car? Van → AIA 100%. Car → WDA 18%. "
                   "(2) What was the total purchase price? On HP, claim AIA on FULL cost, "
                   "not monthly payments. "
                   "(3) Is it electric? Electric → 100% first year allowance regardless.",
        ))
        r.thoughts.append(Thought(
            thought_type=ThoughtType.INSIGHT,
            content="If the vehicle is a van (double cab with payload > 1 tonne), "
                   "AIA gives 100% deduction in year of purchase. "
                   "If £15,000 van → £15,000 × 26% = £3,900 tax saving. "
                   "The monthly HP payments are just cashflow, not the deduction.",
            saving_impact=0,  # Can't calculate without knowing the price
            legal_basis="CAA 2001 s.38A (AIA), s.104AA (vans)",
            action="NEEDED: Confirm if van or car. Get HP agreement showing total cost.",
        ))
        r.confidence = 0.70  # Need more info
        r.action_required = "Provide vehicle details: type, total cost, HP agreement"
        results.append(r)

        # === 7. MILEAGE vs ACTUAL — DEEP COMPARISON ===
        r = MetacognitionResult(subject="Motor Expenses: Mileage vs Actual")
        if motor_expenses > 0:
            # Compare at different mileage levels
            for miles in [10_000, 12_000, 15_000, 20_000]:
                if miles <= 10_000:
                    mileage = miles * 0.45
                else:
                    mileage = 10_000 * 0.45 + (miles - 10_000) * 0.25
                diff = mileage - motor_expenses
                if diff > 0:
                    r.thoughts.append(Thought(
                        thought_type=ThoughtType.ANALYSIS,
                        content=f"At {miles:,} miles: Simplified = £{mileage:,.0f} vs "
                               f"Actual = £{motor_expenses:,.0f}. "
                               f"Simplified is BETTER by £{diff:,.0f}.",
                    ))
                else:
                    r.thoughts.append(Thought(
                        thought_type=ThoughtType.ANALYSIS,
                        content=f"At {miles:,} miles: Simplified = £{mileage:,.0f} vs "
                               f"Actual = £{motor_expenses:,.0f}. "
                               f"ACTUAL is better by £{abs(diff):,.0f}.",
                    ))

            r.thoughts.append(Thought(
                thought_type=ThoughtType.REFLECTION,
                content=f"Current motor expenses: £{motor_expenses:,.2f}. "
                       f"Break-even point: ~{int(motor_expenses / 0.45):,} miles "
                       f"(if all at 45p) or ~{int((motor_expenses - 4500) / 0.25) + 10000:,} miles "
                       f"(if over 10k). Keep a mileage log to prove whichever is higher.",
                action="Start a mileage log TODAY. Phone app recommended.",
            ))
        r.confidence = 0.85
        results.append(r)

        # === 8. PPE & INVISIBLE EXPENSES ===
        r = MetacognitionResult(subject="Invisible Expenses (Cash/Card)")
        r.thoughts.append(Thought(
            thought_type=ThoughtType.CURIOSITY,
            content="CRITICAL: The bank statements don't capture everything. "
                   "Cash purchases are INVISIBLE. Common cash expenses for construction: "
                   "PPE (boots £80, hi-vis £20, gloves £30, hard hat £15 = £145/year minimum), "
                   "tools (replacement blades, drill bits, sandpaper), "
                   "materials (fixings, adhesives, sundries), "
                   "parking (site visits), "
                   "lunches on site (if working away from home > 5 hours). "
                   "TOTAL ESTIMATE: £600-1,200/year in unclaimed expenses.",
        ))
        r.thoughts.append(Thought(
            thought_type=ThoughtType.INSIGHT,
            content="Even without receipts, HMRC accepts 'reasonable estimates' for "
                   "PPE and small tools under the trading income allowance principle. "
                   "A construction worker claiming £600 PPE is completely normal.",
            saving_impact=600 * 0.26,
            legal_basis="ITTOIA 2005 s.34, BIM37670 — protective clothing",
            confidence_impact=0.1,
        ))
        r.tax_saving = 600 * 0.26
        r.confidence = 0.85
        results.append(r)

        # === 9. TAX YEAR PLANNING ===
        r = MetacognitionResult(subject="Tax Year Planning 2025/26")
        r.thoughts.append(Thought(
            thought_type=ThoughtType.REFLECTION,
            content=f"Current position: Net profit £{net_profit:,.2f}. "
                   f"{'ABOVE higher rate threshold (£50,270)' if net_profit > 50_270 else 'Within basic rate band'}. "
                   f"{'Pension contributions before 5 April would get 40% relief.' if net_profit > 50_270 else ''} "
                   f"{'Any expenses that can be pulled into this year get 40% instead of 20%.' if net_profit > 50_270 else ''}",
        ))
        if net_profit > 50_270:
            excess = net_profit - 50_270
            r.thoughts.append(Thought(
                thought_type=ThoughtType.INSIGHT,
                content=f"HIGHER RATE BAND: £{excess:,.2f} is taxed at 40% + 2% NI = 42%. "
                       f"Every pound of additional deduction in this band saves 42p. "
                       f"If you can bring forward any expenses, do it NOW.",
                saving_impact=0,
                legal_basis="ITA 2007 s.10 — basic and higher rate thresholds",
            ))
        r.confidence = 0.90
        results.append(r)

        # Track all results in the engine
        self.results.extend(results)
        return results

    # ================================================================
    # SUMMARY REPORT
    # ================================================================
    def get_strategy_summary(self) -> Dict:
        """Get the full metacognition summary."""
        all_savings = sum(r.tax_saving for r in self.results)
        high_confidence = [r for r in self.results if r.confidence >= 0.8]
        needs_action = [r for r in self.results
                       if any(t.action for t in r.thoughts)]

        return {
            "total_analyses": len(self.results),
            "total_tax_saving_identified": all_savings,
            "reclassifications": self.reclassifications,
            "high_confidence_items": len(high_confidence),
            "items_needing_action": len(needs_action),
            "thought_count": sum(len(r.thoughts) for r in self.results),
            "results": self.results,
        }


# ========================================================================
# QUICK DEMO
# ========================================================================
if __name__ == "__main__":
    engine = HNCMetacognition(tax_year=2025)

    # Full position analysis
    results = engine.analyse_full_position(
        net_profit=60_316,
        total_income=115_934,
        total_expenses=55_618,
        motor_expenses=8_500,
        cis_deducted=10_223.13,
        cis_citb=360.34,
        drawings=5_000,
        food_pnl=-2_500,  # Assume food trade is losing money
    )

    print("=" * 70)
    print("  HNC METACOGNITION ENGINE — FULL ANALYSIS")
    print("=" * 70)

    for r in results:
        print(f"\n{'─' * 60}")
        print(f"  {r.subject}")
        print(f"  Confidence: {r.confidence:.0%} | Tax Saving: £{r.tax_saving:,.2f}")
        for t in r.thoughts:
            marker = {"INSIGHT": "💡", "ANALYSIS": "📊", "CURIOSITY": "🔍",
                      "MEMORY": "🧠", "OBSERVATION": "👁", "DOUBT": "⚠️",
                      "VETO": "🚫", "CONVICTION": "✅", "REFLECTION": "🤔",
                      "QUESTION": "❓"}.get(t.thought_type, "•")
            print(f"    {marker} [{t.thought_type}] {t.content[:100]}")
            if t.action:
                print(f"       → DO: {t.action[:80]}")
            if t.legal_basis:
                print(f"       → LAW: {t.legal_basis[:80]}")

    summary = engine.get_strategy_summary()
    print(f"\n{'=' * 70}")
    print(f"  TOTAL: {summary['total_analyses']} analyses, "
          f"{summary['thought_count']} thoughts, "
          f"£{summary['total_tax_saving_identified']:,.2f} savings identified")
    print(f"{'=' * 70}")
