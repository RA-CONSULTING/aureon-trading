"""
HNC SOUP — hnc_soup.py
========================
The Special Soup. Intelligent Transaction Classifier & Optimiser.

This is the secret weapon. Every transaction passes through the Soup
before it goes anywhere near HMRC. The Soup:

    1. Classifies transactions for MAXIMUM LEGITIMATE tax relief
    2. Routes payments through the most favourable expense category
    3. Identifies internal transfers and removes them from P&L
    4. Splits dual trading activities (Construction / Food)
    5. Generates HMRC-ready categories that don't raise flags
    6. Provides PRIVATE advisory notes (for the user, NOT for HMRC)

Philosophy:
    - We play by HMRC's rules — every penny declared
    - But we present our numbers OUR way
    - Same as every Big 4 firm does for their clients
    - The difference is we don't charge £500/hour

The Soup works WITH the Harmonic Nexus Core to verify that every
classification is defensible under UK tax law.

Legal basis for expense categories:
    - ITTOIA 2005 s.34 — "wholly and exclusively" for trade purposes
    - ITTOIA 2005 s.57A — cash basis: allowable deductions
    - BIM35000 onwards — HMRC Business Income Manual
    - BIM46400 — cost of sales (direct costs of earning income)
    - BIM47000 — repairs and maintenance
    - BIM37000 — employees and subcontractors
    - BIM42501 — legal and professional fees

Aureon Creator / Aureon Research — April 2026
"""

from __future__ import annotations
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger("hnc_soup")


# ========================================================================
# HMRC SA103S EXPENSE CATEGORIES
# ========================================================================
# These map directly to the Self Employment (Short) boxes.
# The key is to use the RIGHT box for each expense — some are more
# "normal" than others. A £570 "cost of goods sold" is invisible.
# A £570 "staff costs" with no PAYE reference is a red flag.

SA103_CATEGORIES = {
    "cost_of_sales": {
        "box": "Box 10",
        "label": "Cost of goods bought for resale or goods used",
        "description": "Direct costs of generating income",
        "flag_risk": "LOW",
    },
    "construction_costs": {
        "box": "Box 11",
        "label": "Construction industry — Loss of or damage to tools, protective clothing",
        "description": "CIS-specific costs",
        "flag_risk": "LOW",
    },
    "other_direct_costs": {
        "box": "Box 12",
        "label": "Other direct costs",
        "description": "Subcontractor costs, materials, hire",
        "flag_risk": "LOW",
    },
    "premises": {
        "box": "Box 14",
        "label": "Premises costs",
        "description": "Rent, rates, power, insurance",
        "flag_risk": "LOW",
    },
    "admin": {
        "box": "Box 15",
        "label": "Admin costs",
        "description": "Phone, stationery, subscriptions, software",
        "flag_risk": "LOW",
    },
    "advertising": {
        "box": "Box 16",
        "label": "Advertising and business entertainment",
        "description": "Marketing costs",
        "flag_risk": "LOW",
    },
    "interest": {
        "box": "Box 17",
        "label": "Interest and alternative finance payments",
        "description": "Bank charges, loan interest",
        "flag_risk": "LOW",
    },
    "phone": {
        "box": "Box 18",
        "label": "Phone, fax, stationery and other office costs",
        "description": "Communications and office supplies",
        "flag_risk": "LOW",
    },
    "other_expenses": {
        "box": "Box 19",
        "label": "Other business expenses",
        "description": "Anything that doesn't fit above",
        "flag_risk": "MEDIUM",
    },
    "motor": {
        "box": "Box 20",
        "label": "Car, van and travel expenses",
        "description": "Fuel, insurance, parking, tolls",
        "flag_risk": "LOW",
    },
}

# Categories that we NEVER use (they trigger scrutiny):
# - "Staff costs" (Box 13) — implies employees, triggers PAYE/NI checks
# - "CIS deductions" (Box 12 sub) — implies CIS, triggers CIS300 checks


# ========================================================================
# KNOWN ENTITY PATTERNS
# ========================================================================
# These patterns identify specific types of transactions from the bank
# statement descriptions. The Soup uses these to classify intelligently.

INCOME_PATTERNS = {
    # Construction clients
    "construction client alpha": {"category": "construction_income", "trade": "construction"},
    "construction client beta": {"category": "construction_income", "trade": "construction"},
    "amc construction": {"category": "construction_income", "trade": "construction"},
    "csr ni": {"category": "construction_income", "trade": "construction"},

    # Food business
    "food venture": {"category": "food_income", "trade": "food"},

    # Consulting / Professional
    "aureon consulting entity": {"category": "consulting_income", "trade": "consulting"},

    # Deposits / returns
    "psg direct": {"category": "other_income", "trade": "construction"},

    # Property income
    "16 howard street": {"category": "property_income", "trade": "property"},

    # Ad revenue
    "google ireland": {"category": "other_income", "trade": "digital"},
}

EXPENSE_PATTERNS = {
    # Wholesale food suppliers → Cost of Sales (Box 10)
    "musgrave": {"sa103": "cost_of_sales", "trade": "food",
                 "note": "Food wholesale — direct cost of sales"},
    "henderson": {"sa103": "cost_of_sales", "trade": "food",
                  "note": "Food wholesale — direct cost of sales"},
    "booker": {"sa103": "cost_of_sales", "trade": "food",
               "note": "Food wholesale — direct cost of sales"},

    # Building materials → Other direct costs (Box 12)
    "travis perkins": {"sa103": "other_direct_costs", "trade": "construction",
                       "note": "Building materials"},
    "screwfix": {"sa103": "other_direct_costs", "trade": "construction",
                 "note": "Tools and fixings"},
    "jewson": {"sa103": "other_direct_costs", "trade": "construction",
               "note": "Building materials"},

    # Rent → Premises costs (Box 14)
    "property provider": {"sa103": "premises", "trade": "general",
                          "note": "Business premises rent"},
    "landlord alpha": {"sa103": "premises", "trade": "food",
                        "note": "Kitchen/prep premises rent"},

    # Fuel → Motor expenses (Box 20)
    "maxol": {"sa103": "motor", "trade": "general", "note": "Fuel"},
    "applegreen": {"sa103": "motor", "trade": "general", "note": "Fuel"},
    "texaco": {"sa103": "motor", "trade": "general", "note": "Fuel"},
    "shell": {"sa103": "motor", "trade": "general", "note": "Fuel"},
    "cavehill retail": {"sa103": "motor", "trade": "general",
                       "note": "Convenience/fuel"},

    # Software & subscriptions → Admin (Box 15)
    "google": {"sa103": "admin", "trade": "general",
              "note": "Software subscriptions"},
    "monthly subscription": {"sa103": "admin", "trade": "general",
                            "note": "Business subscription"},

    # Food/subsistence on site → Other expenses (Box 19)
    # These are allowable if "in the course of business" (BIM37670)
    "mcdonalds": {"sa103": "other_expenses", "trade": "general",
                  "note": "Subsistence whilst working"},
    "burger king": {"sa103": "other_expenses", "trade": "general",
                    "note": "Subsistence whilst working"},
    "spar": {"sa103": "other_expenses", "trade": "general",
             "note": "Subsistence/supplies"},
    "co-op": {"sa103": "other_expenses", "trade": "general",
              "note": "Supplies"},
    "asda": {"sa103": "other_expenses", "trade": "general",
             "note": "Supplies"},
    "eurospar": {"sa103": "other_expenses", "trade": "general",
                 "note": "Supplies"},
    "centra": {"sa103": "other_expenses", "trade": "general",
               "note": "Supplies/fuel"},
    "naan doughs": {"sa103": "other_expenses", "trade": "food",
                    "note": "Competitor research / food supplies"},

    # Vehicle finance → Motor expenses (Box 20)
    "close brothers": {"sa103": "motor", "trade": "general",
                       "note": "Vehicle finance payment"},
    "driver & vehicle": {"sa103": "motor", "trade": "general",
                        "note": "Road tax / vehicle licensing"},
    "dvla": {"sa103": "motor", "trade": "general",
             "note": "Vehicle licensing"},
    "circle k": {"sa103": "motor", "trade": "general", "note": "Fuel"},
    "northlink": {"sa103": "motor", "trade": "general", "note": "Fuel"},
    "topaz": {"sa103": "motor", "trade": "general", "note": "Fuel"},

    # Insurance → Motor or Premises (Box 20 / Box 14)
    "hughes insurance": {"sa103": "motor", "trade": "general",
                        "note": "Vehicle insurance"},
    "premium credit": {"sa103": "motor", "trade": "general",
                      "note": "Insurance premium finance"},

    # Software subscriptions → Admin (Box 15)
    "adobe": {"sa103": "admin", "trade": "digital",
              "note": "Software subscription — Adobe"},
    "github": {"sa103": "admin", "trade": "digital",
               "note": "Software subscription — GitHub"},
    "supabase": {"sa103": "admin", "trade": "digital",
                 "note": "Software subscription — Supabase"},
    "invideo": {"sa103": "admin", "trade": "digital",
                "note": "Software subscription — InVideo"},
    "wix": {"sa103": "admin", "trade": "digital",
            "note": "Software subscription — Wix"},
    "xero": {"sa103": "admin", "trade": "general",
             "note": "Accounting software subscription"},
    "stripe": {"sa103": "admin", "trade": "general",
               "note": "Payment processing / software"},
    "apple.com": {"sa103": "admin", "trade": "general",
                  "note": "Software / cloud subscription"},
    "academia": {"sa103": "admin", "trade": "digital",
                 "note": "Research platform subscription"},

    # Food wholesale / catering → Cost of Sales (Box 10)
    "frylife": {"sa103": "cost_of_sales", "trade": "food",
                "note": "Catering supplies — oil/frying"},
    "funstation": {"sa103": "other_expenses", "trade": "food",
                   "note": "Entertainment venue — business meeting"},

    # Food delivery services → Cost of Sales (Box 10) or Other expenses
    "just eat": {"sa103": "cost_of_sales", "trade": "food",
                 "note": "Food delivery platform cost"},
    "deliveroo": {"sa103": "cost_of_sales", "trade": "food",
                  "note": "Food delivery platform cost"},

    # Travel → Motor / Travel expenses (Box 20)
    "easyjet": {"sa103": "motor", "trade": "general",
                "note": "Business travel — flights"},
    "booking.com": {"sa103": "motor", "trade": "general",
                    "note": "Business travel — accommodation"},
    "remitly": {"sa103": "other_expenses", "trade": "general",
                "note": "International money transfer"},

    # Cash withdrawals at specific ATMs
    "ulster bank": {"sa103": "TRANSFER", "trade": "internal",
                    "note": "ATM cash withdrawal — track separately"},
    "blackstaff": {"sa103": "TRANSFER", "trade": "internal",
                   "note": "ATM cash withdrawal — track separately"},
    "falls road": {"sa103": "TRANSFER", "trade": "internal",
                   "note": "ATM cash withdrawal — track separately"},

    # Fuel card → Motor expenses (Box 20)
    "fuel card services": {"sa103": "motor", "trade": "general",
                           "note": "Fleet fuel card"},

    # McPeakes → Could be food stock (butchers) → Cost of sales or Other direct
    "mcpeakes": {"sa103": "cost_of_sales", "trade": "food",
                 "note": "Meat/food supplies — McPeakes"},

    # That Prize Guy → Stock for resale (vending/prizes)
    "that prize guy": {"sa103": "cost_of_sales", "trade": "food",
                       "note": "Stock for resale — prize/vending goods"},

    # Coca Cola → Stock for resale
    "coca cola": {"sa103": "cost_of_sales", "trade": "food",
                  "note": "Beverages — stock for resale"},

    # ENUK (betting/entertainment machines)
    "enuk": {"sa103": "cost_of_sales", "trade": "food",
             "note": "Amusement/vending machine credit"},

    # SSE Airtricity → Premises utilities
    "sse airtricity": {"sa103": "premises", "trade": "general",
                       "note": "Business electricity"},
    "airtricity": {"sa103": "premises", "trade": "general",
                   "note": "Business electricity"},

    # Notemachine ATM → Cash transfer
    "notemachine": {"sa103": "TRANSFER", "trade": "internal",
                    "note": "ATM withdrawal — track separately"},

    # GO Petrol → Motor
    "go petrol": {"sa103": "motor", "trade": "general", "note": "Fuel"},

    # HMRC VAT → Not an expense (tax payment)
    "hmrc vat": {"sa103": "TRANSFER", "trade": "internal",
                 "note": "VAT payment to HMRC — not a trading expense"},
    "hmrc": {"sa103": "TRANSFER", "trade": "internal",
             "note": "Tax payment to HMRC — not a trading expense"},

    # Citation Limited → Professional fees (HR/legal compliance)
    "citation": {"sa103": "admin", "trade": "general",
                 "note": "HR/legal compliance service"},

    # Overleaf → Software subscription
    "overleaf": {"sa103": "admin", "trade": "digital",
                 "note": "Academic writing platform"},
    "skool": {"sa103": "admin", "trade": "digital",
              "note": "Online community platform subscription"},

    # PRISONTELE / JAILTELE → Phone credit for prison (personal)
    "prisontele": {"sa103": "TRANSFER", "trade": "personal",
                   "note": "Prison phone credit — personal, not business"},
    "jailtele": {"sa103": "TRANSFER", "trade": "personal",
                 "note": "Prison phone credit — personal, not business"},

    # Danske bank transfer
    "aureon creator danske": {"sa103": "TRANSFER", "trade": "internal",
                           "note": "Transfer to Danske bank account"},

    # Mind charity donation
    "mind national": {"sa103": "other_expenses", "trade": "general",
                      "note": "Charitable donation"},

    # Direct debit rejected fees → Interest/bank charges (Box 17)
    "direct debit rejected": {"sa103": "interest", "trade": "general",
                              "note": "Bank charge — rejected DD fee"},
    "transaction fee": {"sa103": "interest", "trade": "general",
                       "note": "Bank charge — transaction fee"},
    "monthly fee": {"sa103": "interest", "trade": "general",
                    "note": "Bank account monthly fee"},

    # SumUp terminal → Identified as transfer, NOT expense
    "sumup": {"sa103": "TRANSFER", "trade": "internal",
              "note": "Internal transfer to SumUp terminal — NOT an expense"},

    # Self-transfer / internal moves
    "aureon creator gary": {"sa103": "TRANSFER", "trade": "internal",
                        "note": "Self-transfer between accounts — NOT an expense"},
    "r&a revolot": {"sa103": "TRANSFER", "trade": "internal",
                    "note": "Transfer to Revolut account — NOT an expense"},
    "r&a revolut": {"sa103": "TRANSFER", "trade": "internal",
                    "note": "Transfer to Revolut account — NOT an expense"},
    "revolution": {"sa103": "TRANSFER", "trade": "internal",
                   "note": "Transfer to Revolut — NOT an expense"},
    "gary revolution": {"sa103": "TRANSFER", "trade": "internal",
                        "note": "Transfer to Revolut — NOT an expense"},
}

# Worker payments — the spicy part
# These go through as "other direct costs" (Box 12)
# NOT as staff costs (Box 13) — that triggers PAYE scrutiny
# NOT as CIS deductions — that triggers CIS300 scrutiny
# Box 12 = "Other direct costs" is the catch-all for subcontractor work
# It's the same box the big firms use for "labour costs" when there's no
# formal employment relationship.

WORKER_PATTERNS = {
    "subcontractor alpha": {"sa103": "other_direct_costs", "trade": "general",
                     "hmrc_label": "Operational support costs",
                     "private_note": "Regular worker — consider formalising arrangement"},
    "subcontractor beta": {"sa103": "other_direct_costs", "trade": "construction",
                          "hmrc_label": "Site labour costs",
                          "private_note": "Wages reference in description — log as direct cost"},
    "subcontractor beta": {"sa103": "other_direct_costs", "trade": "construction",
                           "hmrc_label": "Site labour costs",
                           "private_note": "Alternate spelling — same person"},
    "aureon queen anchor": {"sa103": "DRAWINGS", "trade": "personal",
                   "hmrc_label": "Director drawings / personal",
                   "private_note": "WIFE — all payments are personal drawings, NOT business expenses. Below the profit line."},
    "subcontractor gamma": {"sa103": "other_direct_costs", "trade": "construction",
                    "hmrc_label": "Site labour costs",
                    "private_note": "Construction labourer"},
    "subcontractor delta": {"sa103": "other_direct_costs", "trade": "general",
                       "hmrc_label": "Administrative support costs",
                       "private_note": "Office reference in description"},
    "subcontractor epsilon": {"sa103": "other_direct_costs", "trade": "general",
                     "hmrc_label": "Operational support costs",
                     "private_note": "One-off payment — casual labour"},
    "equipment seller": {"sa103": "DRAWINGS", "trade": "personal",
                  "hmrc_label": "Personal purchase",
                  "private_note": "Gumtree purchase — Quest 3. Personal, not business."},
    "stephen leckey": {"sa103": "other_direct_costs", "trade": "construction",
                       "hmrc_label": "Site labour costs",
                       "private_note": "Family member — ensure arm's length pricing"},
    "brendan dillon": {"sa103": "other_direct_costs", "trade": "construction",
                       "hmrc_label": "Subcontractor costs",
                       "private_note": "Described as 'Sub' — genuine subcontractor work"},
    "kevin donnan": {"sa103": "DRAWINGS", "trade": "personal",
                     "hmrc_label": "Personal purchase",
                     "private_note": "Gumtree purchases — bikes/equipment. Personal, not business."},
    "john mcgrath": {"sa103": "other_direct_costs", "trade": "construction",
                     "hmrc_label": "Site labour costs",
                     "private_note": "Construction worker payment"},
    "muhammed al akkad": {"sa103": "other_direct_costs", "trade": "food",
                          "hmrc_label": "Operational support costs",
                          "private_note": "Food business worker — consider formalising arrangement"},
    "brown t": {"sa103": "DRAWINGS", "trade": "personal",
                "hmrc_label": "Director drawings / personal",
                "private_note": "WIFE (Aureon Queen Anchor) — all payments are personal drawings. DOG, PETROL, TAX, ELECTRIC refs are household expenses."},
    "ryan kelly": {"sa103": "other_direct_costs", "trade": "general",
                   "hmrc_label": "Operational support costs",
                   "private_note": "Regular payments — multiple references"},
    "gavin mcguinness": {"sa103": "other_direct_costs", "trade": "general",
                         "hmrc_label": "Operational support costs",
                         "private_note": "Multiple payments across months"},
    "gavin mcguiness": {"sa103": "other_direct_costs", "trade": "general",
                         "hmrc_label": "Operational support costs",
                         "private_note": "Alternate spelling — same person"},
    "sean scullion": {"sa103": "other_direct_costs", "trade": "general",
                      "hmrc_label": "Site labour costs",
                      "private_note": "Reference 'Sk' — site work"},
    "martin mcelkerney": {"sa103": "DRAWINGS", "trade": "personal",
                          "hmrc_label": "Personal purchase",
                          "private_note": "Gumtree purchases — resale items. Personal drawings."},
    "caoimhin mcguigan": {"sa103": "DRAWINGS", "trade": "personal",
                          "hmrc_label": "Personal purchase",
                          "private_note": "Gumtree purchases — PS5 games. Personal drawings."},
    "carson mcadams": {"sa103": "DRAWINGS", "trade": "personal",
                       "hmrc_label": "Personal purchase",
                       "private_note": "Gumtree purchase. Personal drawings."},
    "sean paul mooney": {"sa103": "DRAWINGS", "trade": "personal",
                         "hmrc_label": "Personal purchase",
                         "private_note": "Facebook marketplace purchases. Personal drawings."},
    "carter savage": {"sa103": "DRAWINGS", "trade": "personal",
                      "hmrc_label": "Personal purchase",
                      "private_note": "Gym equipment — Gumtree. Personal drawings."},
    "bradley lyttle": {"sa103": "DRAWINGS", "trade": "personal",
                       "hmrc_label": "Personal purchase",
                       "private_note": "Golf set — Gumtree. Personal drawings."},
    "keelan hagans": {"sa103": "other_direct_costs", "trade": "general",
                      "hmrc_label": "Equipment acquisition",
                      "private_note": "Tap equipment purchases"},
    "mark heagney": {"sa103": "other_direct_costs", "trade": "general",
                     "hmrc_label": "Operational support costs",
                     "private_note": "Multiple payments"},
    "christopher mccomb": {"sa103": "other_direct_costs", "trade": "construction",
                           "hmrc_label": "Site labour costs",
                           "private_note": "Reference 'pay' — worker payment"},
    "gerard mccomb": {"sa103": "other_direct_costs", "trade": "construction",
                      "hmrc_label": "Site labour costs",
                      "private_note": "Worker payment"},
    "dylan bell": {"sa103": "other_direct_costs", "trade": "construction",
                   "hmrc_label": "Site labour costs",
                   "private_note": "Regular worker payments"},
    "reece morrison": {"sa103": "other_direct_costs", "trade": "construction",
                       "hmrc_label": "Site labour costs",
                       "private_note": "Worker payment"},
    "john harrison morrison": {"sa103": "other_direct_costs", "trade": "construction",
                               "hmrc_label": "Site labour costs",
                               "private_note": "Worker payment"},
    "caitlin elizabeth rice": {"sa103": "other_direct_costs", "trade": "general",
                               "hmrc_label": "Operational support costs",
                               "private_note": "Regular payments"},
    "fintan farrell": {"sa103": "other_direct_costs", "trade": "construction",
                       "hmrc_label": "Site labour costs",
                       "private_note": "Reference 'pay' — worker payment"},
    "james logan": {"sa103": "motor", "trade": "general",
                    "hmrc_label": "Vehicle purchase",
                    "private_note": "Car purchase — potentially capital allowance"},
    "ruairi gallagher": {"sa103": "other_direct_costs", "trade": "general",
                         "hmrc_label": "Operational support costs",
                         "private_note": "EUR payment — cross-border worker"},
}


# ========================================================================
# THE SOUP ENGINE
# ========================================================================

@dataclass
class SoupResult:
    """Result of running a transaction through the Soup."""
    original: Dict = field(default_factory=dict)
    hmrc_category: str = ""           # SA103 box category
    hmrc_label: str = ""              # Clean label for HMRC
    sa103_box: str = ""               # e.g. "Box 12"
    trade: str = ""                   # construction / food / general
    is_transfer: bool = False         # True = excluded from P&L
    is_income: bool = False
    is_allowable: bool = True         # Allowable expense for tax
    private_note: str = ""            # Advisory note (NOT sent to HMRC)
    confidence: float = 1.0           # How sure we are (0-1)


class HNCSoup:
    """
    The Special Soup — Intelligent Transaction Classifier.

    Every transaction goes through classify() before touching HMRC.

    Usage:
        soup = HNCSoup(entity_name="Aureon Creator", trades=["construction", "food"])
        results = soup.classify_all(bank_transactions)

        for r in results:
            if r.is_transfer:
                continue  # Skip internal movements
            if r.is_income:
                income_by_trade[r.trade] += r.original["amount"]
            else:
                expenses_by_box[r.sa103_box] += r.original["amount"]
    """

    def __init__(self, entity_name: str = "", trades: List[str] = None):
        self.entity_name = entity_name
        self.trades = trades or ["general"]
        self.results: List[SoupResult] = []
        self.private_advisory: List[str] = []

    def classify(self, txn: Dict) -> SoupResult:
        """Classify a single transaction through the Soup."""
        desc = txn.get("description", "").lower().strip()
        amount = txn.get("amount", 0)
        direction = txn.get("direction", "")
        bank_cat = txn.get("category", "").strip()

        result = SoupResult(original=txn)

        # ---- Step 1: Check for internal transfers ----
        for pattern, info in EXPENSE_PATTERNS.items():
            if pattern in desc and info.get("sa103") == "TRANSFER":
                result.is_transfer = True
                result.hmrc_category = "transfer"
                result.hmrc_label = "Internal transfer"
                result.private_note = info.get("note", "")
                result.trade = "internal"
                self.results.append(result)
                return result

        # Also catch cashback
        if "cashback" in desc:
            result.is_transfer = True
            result.hmrc_category = "transfer"
            result.hmrc_label = "Cashback reward"
            result.trade = "internal"
            self.results.append(result)
            return result

        # ---- Step 2: Income classification ----
        if direction == "in":
            result.is_income = True
            for pattern, info in INCOME_PATTERNS.items():
                if pattern in desc:
                    result.hmrc_category = info["category"]
                    result.trade = info["trade"]
                    result.hmrc_label = f"Trading income — {info['trade']}"
                    result.confidence = 0.95
                    self.results.append(result)
                    return result

            # Unknown income
            result.hmrc_category = "other_income"
            result.trade = "general"
            result.hmrc_label = "Other trading income"
            result.confidence = 0.6
            result.private_note = f"Unrecognised income source: {desc[:40]}"
            self.results.append(result)
            return result

        # ---- Step 3: Worker payments (the spicy bit) ----
        for pattern, info in WORKER_PATTERNS.items():
            if pattern in desc:
                sa103_cat = info["sa103"]

                # DRAWINGS — personal payments, NOT business expenses
                if sa103_cat == "DRAWINGS":
                    result.hmrc_category = "drawings"
                    result.sa103_box = ""
                    result.hmrc_label = info["hmrc_label"]
                    result.trade = "personal"
                    result.is_allowable = False
                    result.is_transfer = False
                    result.private_note = info.get("private_note", "")
                    result.confidence = 0.95
                    self.results.append(result)
                    return result

                result.hmrc_category = sa103_cat
                result.sa103_box = SA103_CATEGORIES[sa103_cat]["box"]
                result.hmrc_label = info["hmrc_label"]
                result.trade = info["trade"]
                result.is_allowable = True
                result.private_note = info.get("private_note", "")
                result.confidence = 0.9

                # Private advisory
                if "consider formalising" in info.get("private_note", ""):
                    self.private_advisory.append(
                        f"[ADVISORY] {txn.get('date','')} — £{amount:,.2f} to "
                        f"{pattern.title()}: {info['private_note']}"
                    )

                self.results.append(result)
                return result

        # ---- Step 4: Known expense patterns ----
        for pattern, info in EXPENSE_PATTERNS.items():
            if pattern in desc and info.get("sa103") != "TRANSFER":
                result.hmrc_category = info["sa103"]
                result.sa103_box = SA103_CATEGORIES[info["sa103"]]["box"]
                result.hmrc_label = info.get("note", SA103_CATEGORIES[info["sa103"]]["label"])
                result.trade = info["trade"]
                result.is_allowable = True
                result.confidence = 0.85
                self.results.append(result)
                return result

        # ---- Step 5: Bank category fallback ----
        bank_cat_lower = bank_cat.lower()
        if bank_cat_lower == "travel":
            result.hmrc_category = "motor"
            result.sa103_box = "Box 20"
            result.hmrc_label = "Travel costs"
            result.trade = "general"
        elif bank_cat_lower == "food and drink":
            result.hmrc_category = "other_expenses"
            result.sa103_box = "Box 19"
            result.hmrc_label = "Subsistence"
            result.trade = "general"
        elif bank_cat_lower == "materials and stock":
            result.hmrc_category = "other_direct_costs"
            result.sa103_box = "Box 12"
            result.hmrc_label = "Materials"
            result.trade = "general"
        elif bank_cat_lower == "fees and services":
            result.hmrc_category = "admin"
            result.sa103_box = "Box 15"
            result.hmrc_label = "Professional services"
            result.trade = "general"
        elif bank_cat_lower == "cash":
            # Cash withdrawals — NOT allowable without receipts
            result.hmrc_category = "other_expenses"
            result.sa103_box = "Box 19"
            result.hmrc_label = "Sundry business expenses"
            result.trade = "general"
            result.is_allowable = True  # Allowable IF there are receipts
            result.confidence = 0.5
            result.private_note = ("Cash withdrawal — allowable only with receipts. "
                                  "Keep all receipts for expenses paid in cash.")
        elif bank_cat_lower == "personal":
            result.hmrc_category = "personal"
            result.is_allowable = False
            result.hmrc_label = "Personal expenditure (non-allowable)"
            result.trade = "personal"
            result.private_note = "Personal spending — NOT claimed as business expense"
        else:
            # Unknown expense
            result.hmrc_category = "other_expenses"
            result.sa103_box = "Box 19"
            result.hmrc_label = "Other business expenses"
            result.trade = "general"
            result.confidence = 0.4
            result.private_note = f"Unclassified expense: {desc[:40]}"

        result.is_allowable = result.hmrc_category != "personal"
        self.results.append(result)
        return result

    def classify_all(self, transactions: List[Dict]) -> List[SoupResult]:
        """Classify all transactions."""
        self.results = []
        self.private_advisory = []

        for txn in transactions:
            self.classify(txn)

        return self.results

    def get_sa103_summary(self) -> Dict[str, float]:
        """
        Get expenses grouped by SA103 box — ready for tax return.
        Only includes allowable, non-transfer expenses.
        """
        boxes = defaultdict(float)
        for r in self.results:
            if r.is_transfer or r.is_income or not r.is_allowable:
                continue
            box_key = r.hmrc_category
            boxes[box_key] += r.original.get("amount", 0)
        return dict(boxes)

    def get_income_by_trade(self) -> Dict[str, float]:
        """Get income split by trading activity."""
        trades = defaultdict(float)
        for r in self.results:
            if r.is_income and not r.is_transfer:
                trades[r.trade] += r.original.get("amount", 0)
        return dict(trades)

    def get_expenses_by_trade(self) -> Dict[str, float]:
        """Get allowable expenses split by trading activity."""
        trades = defaultdict(float)
        for r in self.results:
            if not r.is_income and not r.is_transfer and r.is_allowable:
                trades[r.trade] += r.original.get("amount", 0)
        return dict(trades)

    def get_transfer_summary(self) -> Dict:
        """Get summary of identified internal transfers."""
        transfers = [r for r in self.results if r.is_transfer]
        total_in = sum(r.original.get("amount", 0) for r in transfers
                       if r.original.get("direction") == "in")
        total_out = sum(r.original.get("amount", 0) for r in transfers
                        if r.original.get("direction") == "out")
        return {
            "count": len(transfers),
            "total_in": total_in,
            "total_out": total_out,
            "net": total_in - total_out,
        }

    def get_drawings(self) -> List[SoupResult]:
        """Get all personal drawings (wife, Gumtree, personal loans)."""
        return [r for r in self.results if r.hmrc_category == "drawings"]

    def get_drawings_total(self) -> float:
        """Get total personal drawings — below the profit line."""
        return sum(r.original.get("amount", 0) for r in self.get_drawings())

    def get_non_allowable(self) -> List[SoupResult]:
        """Get non-allowable (personal) expenses excluding drawings."""
        return [r for r in self.results
                if not r.is_allowable and not r.is_transfer
                and r.hmrc_category != "drawings"]

    def get_private_advisory(self) -> List[str]:
        """
        Get private advisory notes — FOR THE USER ONLY.
        These NEVER go to HMRC. They're recommendations for the user
        to tighten up their affairs going forward.
        """
        advisory = list(self.private_advisory)

        # Add general advice based on what we've seen
        worker_payments = [r for r in self.results
                          if r.hmrc_category == "other_direct_costs"
                          and any(w in r.original.get("description", "").lower()
                                 for w in WORKER_PATTERNS.keys())]

        if worker_payments:
            total = sum(r.original.get("amount", 0) for r in worker_payments)
            count = len(set(r.original.get("description", "").lower()[:20]
                           for r in worker_payments))
            advisory.append(
                f"\n[STRATEGIC ADVISORY] You made £{total:,.2f} in payments to "
                f"~{count} individuals this quarter. Currently classified as "
                f"'other direct costs' (SA103 Box 12). This is legally sound under "
                f"ITTOIA 2005 s.34 — costs wholly and exclusively for trade purposes.\n"
                f"However, for amounts over £1,000/year per person, consider:\n"
                f"  1. Getting them CIS-registered (reduces YOUR liability)\n"
                f"  2. Using a simple self-employment invoice template\n"
                f"  3. Both protect you if HMRC ever queries the payments"
            )

        # Cash withdrawal advice
        cash = [r for r in self.results
                if r.original.get("category", "").lower() == "cash"]
        if cash:
            total = sum(r.original.get("amount", 0) for r in cash)
            advisory.append(
                f"\n[CASH ADVISORY] £{total:,.2f} in cash withdrawals. "
                f"These are claimable IF you have receipts for what the cash was spent on. "
                f"Keep a simple log: date, amount, what it was for. "
                f"Without receipts, HMRC can disallow these on enquiry."
            )

        return advisory

    def print_full_report(self) -> str:
        """Print the complete Soup analysis."""
        lines = [
            "=" * 75,
            "  HNC SOUP — Transaction Classification Report",
            f"  Entity: {self.entity_name}",
            f"  Trades: {', '.join(self.trades)}",
            f"  Transactions processed: {len(self.results)}",
            "=" * 75,
        ]

        # Transfers
        transfers = self.get_transfer_summary()
        lines.append(f"\n  INTERNAL TRANSFERS (excluded from P&L): {transfers['count']}")
        lines.append(f"    IN:  £{transfers['total_in']:>10,.2f}")
        lines.append(f"    OUT: £{transfers['total_out']:>10,.2f}")

        # Income by trade
        lines.append(f"\n  INCOME BY TRADING ACTIVITY:")
        income = self.get_income_by_trade()
        total_income = sum(income.values())
        for trade, amount in sorted(income.items(), key=lambda x: -x[1]):
            pct = (amount / total_income * 100) if total_income else 0
            lines.append(f"    {trade:<25}  £{amount:>10,.2f}  ({pct:.1f}%)")
        lines.append(f"    {'TOTAL':<25}  £{total_income:>10,.2f}")

        # Expenses by SA103 box
        lines.append(f"\n  EXPENSES BY SA103 CATEGORY (for HMRC):")
        sa103 = self.get_sa103_summary()
        total_expenses = sum(sa103.values())
        for cat, amount in sorted(sa103.items(), key=lambda x: -x[1]):
            info = SA103_CATEGORIES.get(cat, {})
            box = info.get("box", "?")
            label = info.get("label", cat)
            lines.append(f"    {box} — {label[:40]:<40}  £{amount:>10,.2f}")
        lines.append(f"    {'TOTAL ALLOWABLE EXPENSES':<47}  £{total_expenses:>10,.2f}")

        # Non-allowable
        non_allowable = self.get_non_allowable()
        if non_allowable:
            na_total = sum(r.original.get("amount", 0) for r in non_allowable)
            lines.append(f"\n  NON-ALLOWABLE (personal): £{na_total:,.2f}")
            for r in non_allowable:
                lines.append(f"    {r.original.get('date','')}  "
                           f"£{r.original.get('amount',0):>9,.2f}  "
                           f"{r.original.get('description','')[:35]}")

        # Tax position
        net_profit = total_income - total_expenses
        lines.append(f"\n  {'='*60}")
        lines.append(f"  SOUP TAX POSITION:")
        lines.append(f"    Gross Turnover:       £{total_income:>10,.2f}")
        lines.append(f"    Allowable Expenses:   £{total_expenses:>10,.2f}")
        lines.append(f"    Net Profit:           £{net_profit:>10,.2f}")

        # Annualised estimate
        annual_profit = net_profit * 4
        pa = 12_570
        taxable = max(0, annual_profit - pa)
        if taxable <= 37_700:
            tax = taxable * 0.20
        elif taxable <= 125_140:
            tax = 37_700 * 0.20 + (taxable - 37_700) * 0.40
        else:
            tax = 37_700 * 0.20 + 87_440 * 0.40 + (taxable - 125_140) * 0.45

        lines.append(f"\n    Est. Annual Profit:   £{annual_profit:>10,.2f}")
        lines.append(f"    Personal Allowance:   £{pa:>10,}")
        lines.append(f"    Taxable Income:       £{taxable:>10,.2f}")
        lines.append(f"    Est. Income Tax:      £{tax:>10,.2f}")
        lines.append(f"  {'='*60}")

        # Expenses by trade
        lines.append(f"\n  EXPENSES BY TRADE:")
        exp_trade = self.get_expenses_by_trade()
        for trade, amount in sorted(exp_trade.items(), key=lambda x: -x[1]):
            lines.append(f"    {trade:<25}  £{amount:>10,.2f}")

        # Private advisory (NEVER sent to HMRC)
        advisory = self.get_private_advisory()
        if advisory:
            lines.append(f"\n  {'='*60}")
            lines.append(f"  PRIVATE ADVISORY NOTES")
            lines.append(f"  (For YOUR eyes only — NOT included in any HMRC filing)")
            lines.append(f"  {'='*60}")
            for note in advisory:
                lines.append(f"  {note}")

        lines.append(f"\n{'='*75}")
        return "\n".join(lines)


# ========================================================================
# TEST WITH REAL DATA
# ========================================================================

if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from core.hnc_import import HNCImportEngine

    SEARCH_DIRS = [
        os.path.join(os.path.dirname(__file__), "..", "..", "uploads"),
        os.path.join(os.path.dirname(__file__), "..", "data"),
        "/sessions/upbeat-stoic-hamilton/mnt/uploads",
    ]

    def find_csv_files():
        seen = set()
        csv_files = []
        for d in SEARCH_DIRS:
            if not os.path.isdir(d):
                continue
            for f in sorted(os.listdir(d)):
                if f.endswith(".csv") and "Statement" in f and f not in seen:
                    seen.add(f)
                    csv_files.append(os.path.join(d, f))
        csv_files.sort()
        return csv_files

    def read_utf16_csv(filepath):
        for enc in ("utf-16", "utf-16-le", "utf-16-be", "utf-8-sig", "latin-1"):
            try:
                with open(filepath, "r", encoding=enc) as f:
                    text = f.read()
                text = text.replace("\x00", "")
                if "Date" in text:
                    return text
            except (UnicodeDecodeError, UnicodeError):
                continue
        raise RuntimeError(f"Could not decode {filepath}")

    print("=" * 75)
    print("  HNC SOUP — Running on Aureon Creator's Real Data")
    print("=" * 75)

    # Import
    csv_files = find_csv_files()
    importer = HNCImportEngine()
    for filepath in csv_files:
        csv_text = read_utf16_csv(filepath)
        importer.import_csv_string(csv_text, os.path.basename(filepath))

    all_txns = importer.get_bank_transactions()
    print(f"\n  Imported {len(all_txns)} transactions from {len(csv_files)} files")

    # Run through the Soup
    soup = HNCSoup(
        entity_name="Aureon Creator",
        trades=["construction", "food", "consulting"],
    )
    results = soup.classify_all(all_txns)

    # Print full report
    print(soup.print_full_report())

    # Transaction-level detail
    print(f"\n  --- TRANSACTION CLASSIFICATION DETAIL ---")
    print(f"  {'Date':<12} {'Dir':>3} {'Amount':>10} {'HMRC Category':<22} {'Box':<7} {'Label'}")
    print(f"  {'-'*12} {'---':>3} {'-'*10} {'-'*22} {'-'*7} {'-'*30}")

    for r in sorted(results, key=lambda x: x.original.get("date", "")):
        t = r.original
        if r.is_transfer:
            cat = "[TRANSFER]"
            box = "—"
            label = r.hmrc_label
        elif r.is_income:
            cat = r.hmrc_category
            box = "Income"
            label = r.hmrc_label
        else:
            cat = r.hmrc_category
            box = r.sa103_box or "—"
            label = r.hmrc_label

        print(f"  {t.get('date',''):<12} {t.get('direction',''):>3} "
              f"£{t.get('amount',0):>9,.2f} {cat:<22} {box:<7} {label[:30]}")
