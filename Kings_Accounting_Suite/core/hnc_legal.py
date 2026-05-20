"""
HNC LEGAL SUITE — hnc_legal.py
===============================
The Law Library.

A structured, machine-queryable dataset of UK tax law that every engine
in the HNC system can verify itself against. No guessing, no assumptions —
every rule, threshold, penalty, and power is cited to its source statute
and HMRC guidance reference.

This is NOT legal advice. This is a structured representation of publicly
available UK legislation and HMRC published guidance for the purpose of
automated compliance verification.

Sources:
    - legislation.gov.uk (primary and secondary legislation)
    - gov.uk/hmrc-internal-manuals (HMRC published guidance)
    - gov.uk/government/publications (HMRC policy papers, CC-FS notices)

Modules:
    1. STATUTES — Primary and secondary legislation references
    2. HMRC_MANUALS — Published HMRC guidance manual references
    3. THRESHOLDS — Tax year-specific rates, bands, allowances
    4. PENALTIES — FA 2007 Sch 24, FA 2009 Sch 55/56 penalty regimes
    5. ENQUIRY_POWERS — TMA 1970 Part V investigation powers
    6. DISCLOSURE — Routes for voluntary disclosure and correction
    7. CASE_LAW — Key tribunal and court decisions
    8. SECTOR_BENCHMARKS — HMRC internal sector norms
    9. VERIFICATION — Methods for engines to check their own compliance
   10. SACRIFICIAL_LAMB — Controlled disclosure engine

Aureon Creator / Aureon Research — April 2026
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from datetime import date, datetime


# ========================================================================
# 1. STATUTE REFERENCES
# ========================================================================

@dataclass
class StatuteRef:
    """A reference to a specific provision of UK law."""
    act: str                    # Short name e.g. "TMA 1970"
    full_title: str             # Full title
    section: str                # Section/Schedule reference
    description: str            # What it provides
    url: str                    # legislation.gov.uk URL
    category: str               # income_tax, cgt, vat, penalties, etc.
    notes: str = ""             # Additional context


# ---- Taxes Management Act 1970 ----
STATUTES: Dict[str, StatuteRef] = {

    # ===== TMA 1970 — Taxes Management Act =====
    "TMA_s7": StatuteRef(
        act="TMA 1970",
        full_title="Taxes Management Act 1970",
        section="s.7",
        description="Obligation to notify HMRC of chargeability to income tax or capital gains tax",
        url="https://www.legislation.gov.uk/ukpga/1970/9/section/7",
        category="obligations",
        notes="Must notify by 5 October following the tax year. Failure: penalty under FA 2008 Sch 41",
    ),
    "TMA_s8": StatuteRef(
        act="TMA 1970",
        full_title="Taxes Management Act 1970",
        section="s.8",
        description="Personal return (self assessment). HMRC may issue notice requiring SA return",
        url="https://www.legislation.gov.uk/ukpga/1970/9/section/8",
        category="obligations",
    ),
    "TMA_s9A": StatuteRef(
        act="TMA 1970",
        full_title="Taxes Management Act 1970",
        section="s.9A",
        description="HMRC power to enquire into a personal tax return",
        url="https://www.legislation.gov.uk/ukpga/1970/9/section/9A",
        category="enquiry_powers",
        notes="Enquiry window: 12 months from filing date. Random or risk-based selection.",
    ),
    "TMA_s9ZA": StatuteRef(
        act="TMA 1970",
        full_title="Taxes Management Act 1970",
        section="s.9ZA",
        description="Taxpayer amendment of self assessment return within 12 months of filing deadline",
        url="https://www.legislation.gov.uk/ukpga/1970/9/section/9ZA",
        category="amendments",
        notes="Key for sacrificial lamb — voluntary amendment before HMRC asks",
    ),
    "TMA_s12B": StatuteRef(
        act="TMA 1970",
        full_title="Taxes Management Act 1970",
        section="s.12B",
        description="Duty to keep and preserve records",
        url="https://www.legislation.gov.uk/ukpga/1970/9/section/12B",
        category="record_keeping",
        notes="Self-employed: 5 years from 31 January following the tax year. Others: 22 months. Penalty up to £3,000 for failure.",
    ),
    "TMA_s19A": StatuteRef(
        act="TMA 1970",
        full_title="Taxes Management Act 1970",
        section="s.19A",
        description="Power to call for documents during enquiry (information notice)",
        url="https://www.legislation.gov.uk/ukpga/1970/9/section/19A",
        category="enquiry_powers",
        notes="HMRC can request any document reasonably required for checking the return",
    ),
    "TMA_s28A": StatuteRef(
        act="TMA 1970",
        full_title="Taxes Management Act 1970",
        section="s.28A",
        description="Completion of enquiry — closure notice",
        url="https://www.legislation.gov.uk/ukpga/1970/9/section/28A",
        category="enquiry_powers",
        notes="HMRC must issue closure notice when enquiry complete. Taxpayer can apply to tribunal to compel closure.",
    ),
    "TMA_s29": StatuteRef(
        act="TMA 1970",
        full_title="Taxes Management Act 1970",
        section="s.29",
        description="Discovery assessment — HMRC assessment outside enquiry window",
        url="https://www.legislation.gov.uk/ukpga/1970/9/section/29",
        category="enquiry_powers",
        notes="Requires loss of tax + careless/deliberate behaviour or information not made available. 4 years (careless) or 20 years (deliberate).",
    ),
    "TMA_s34": StatuteRef(
        act="TMA 1970",
        full_title="Taxes Management Act 1970",
        section="s.34",
        description="Ordinary time limit for assessments — 4 years from end of tax year",
        url="https://www.legislation.gov.uk/ukpga/1970/9/section/34",
        category="time_limits",
    ),
    "TMA_s36": StatuteRef(
        act="TMA 1970",
        full_title="Taxes Management Act 1970",
        section="s.36",
        description="Extended time limit — 6 years (careless) or 20 years (deliberate)",
        url="https://www.legislation.gov.uk/ukpga/1970/9/section/36",
        category="time_limits",
        notes="Careless: 6 years. Deliberate: 20 years. Deliberate + concealed: 20 years but higher penalties.",
    ),
    "TMA_s59B": StatuteRef(
        act="TMA 1970",
        full_title="Taxes Management Act 1970",
        section="s.59B",
        description="Payments on account — two instalments of income tax",
        url="https://www.legislation.gov.uk/ukpga/1970/9/section/59B",
        category="payment",
        notes="31 January and 31 July. Each = 50% of previous year's liability. Balancing payment 31 January following.",
    ),

    # ===== ITTOIA 2005 — Income Tax (Trading and Other Income) Act =====
    "ITTOIA_s5": StatuteRef(
        act="ITTOIA 2005",
        full_title="Income Tax (Trading and Other Income) Act 2005",
        section="s.5",
        description="Charge to tax on trade profits",
        url="https://www.legislation.gov.uk/ukpga/2005/5/section/5",
        category="income_tax",
    ),
    "ITTOIA_s25": StatuteRef(
        act="ITTOIA 2005",
        full_title="Income Tax (Trading and Other Income) Act 2005",
        section="s.25",
        description="Cash basis for small businesses (turnover under £150,000)",
        url="https://www.legislation.gov.uk/ukpga/2005/5/section/25",
        category="income_tax",
        notes="Default basis from April 2024 for eligible businesses. Opt out for accruals basis.",
    ),
    "ITTOIA_s34": StatuteRef(
        act="ITTOIA 2005",
        full_title="Income Tax (Trading and Other Income) Act 2005",
        section="s.34",
        description="Wholly and exclusively test — expenses must be incurred wholly and exclusively for trade purposes",
        url="https://www.legislation.gov.uk/ukpga/2005/5/section/34",
        category="expenses",
        notes="The foundational test for ALL business expense claims. Dual purpose expenditure must be apportioned where identifiable part is for trade.",
    ),
    "ITTOIA_s57A": StatuteRef(
        act="ITTOIA 2005",
        full_title="Income Tax (Trading and Other Income) Act 2005",
        section="s.57A",
        description="Simplified expenses — flat rate deductions for use of home, vehicles, living at business premises",
        url="https://www.legislation.gov.uk/ukpga/2005/5/section/57A",
        category="expenses",
        notes="Optional simplified calculation. Home office: £10/£18/£26 per month by hours. Vehicle: 45p first 10k, 25p thereafter.",
    ),
    "ITTOIA_s66": StatuteRef(
        act="ITTOIA 2005",
        full_title="Income Tax (Trading and Other Income) Act 2005",
        section="s.66",
        description="Cessation of trade — final year accounting rules",
        url="https://www.legislation.gov.uk/ukpga/2005/5/section/66",
        category="income_tax",
    ),

    # ===== TCGA 1992 — Taxation of Chargeable Gains Act =====
    "TCGA_s1": StatuteRef(
        act="TCGA 1992",
        full_title="Taxation of Chargeable Gains Act 1992",
        section="s.1",
        description="The charge to capital gains tax",
        url="https://www.legislation.gov.uk/ukpga/1992/12/section/1",
        category="cgt",
    ),
    "TCGA_s3": StatuteRef(
        act="TCGA 1992",
        full_title="Taxation of Chargeable Gains Act 1992",
        section="s.3",
        description="Annual exempt amount for individuals (AEA)",
        url="https://www.legislation.gov.uk/ukpga/1992/12/section/3",
        category="cgt",
        notes="2025/26: £3,000. Still must report disposals over 4x AEA (£12,000) or total proceeds > £50,000.",
    ),
    "TCGA_s21": StatuteRef(
        act="TCGA 1992",
        full_title="Taxation of Chargeable Gains Act 1992",
        section="s.21",
        description="Assets and disposals — meaning of asset for CGT purposes",
        url="https://www.legislation.gov.uk/ukpga/1992/12/section/21",
        category="cgt",
        notes="Cryptoassets are assets for CGT purposes per HMRC Cryptoassets Manual CRYPTO10100.",
    ),
    "TCGA_s104": StatuteRef(
        act="TCGA 1992",
        full_title="Taxation of Chargeable Gains Act 1992",
        section="s.104",
        description="Section 104 holding — share pooling (pooled cost basis)",
        url="https://www.legislation.gov.uk/ukpga/1992/12/section/104",
        category="cgt",
        notes="Same asset, same class → pooled. Applied to crypto. Order: same-day → 30-day → s.104 pool.",
    ),
    "TCGA_s105": StatuteRef(
        act="TCGA 1992",
        full_title="Taxation of Chargeable Gains Act 1992",
        section="s.105",
        description="Disposal from section 104 holding — cost basis calculation",
        url="https://www.legislation.gov.uk/ukpga/1992/12/section/105",
        category="cgt",
        notes="Proportionate cost: (disposed quantity / total pool quantity) * total pool cost",
    ),
    "TCGA_s106A": StatuteRef(
        act="TCGA 1992",
        full_title="Taxation of Chargeable Gains Act 1992",
        section="s.106A",
        description="Bed and breakfasting rule — 30-day reacquisition rule",
        url="https://www.legislation.gov.uk/ukpga/1992/12/section/106A",
        category="cgt",
        notes="Disposal + reacquisition within 30 days: matched to reacquisition cost, not pool. Anti-avoidance for artificial losses.",
    ),
    "TCGA_s251": StatuteRef(
        act="TCGA 1992",
        full_title="Taxation of Chargeable Gains Act 1992",
        section="s.251",
        description="Debts — disposal of debts is not a disposal for CGT (general rule)",
        url="https://www.legislation.gov.uk/ukpga/1992/12/section/251",
        category="cgt",
        notes="GBP/fiat is not an asset for CGT. Converting crypto to GBP = disposal of crypto.",
    ),

    # ===== ITA 2007 — Income Tax Act =====
    "ITA_s6": StatuteRef(
        act="ITA 2007",
        full_title="Income Tax Act 2007",
        section="s.6",
        description="Income tax rates — basic, higher, additional",
        url="https://www.legislation.gov.uk/ukpga/2007/3/section/6",
        category="income_tax",
    ),
    "ITA_s23": StatuteRef(
        act="ITA 2007",
        full_title="Income Tax Act 2007",
        section="s.23",
        description="Steps in calculating income tax liability",
        url="https://www.legislation.gov.uk/ukpga/2007/3/section/23",
        category="income_tax",
    ),

    # ===== VATA 1994 — Value Added Tax Act =====
    "VATA_s1": StatuteRef(
        act="VATA 1994",
        full_title="Value Added Tax Act 1994",
        section="s.1",
        description="Value added tax charged on supply of goods and services",
        url="https://www.legislation.gov.uk/ukpga/1994/23/section/1",
        category="vat",
    ),
    "VATA_s4": StatuteRef(
        act="VATA 1994",
        full_title="Value Added Tax Act 1994",
        section="s.4",
        description="Taxable supply made in the UK — scope of VAT",
        url="https://www.legislation.gov.uk/ukpga/1994/23/section/4",
        category="vat",
    ),
    "VATA_s25": StatuteRef(
        act="VATA 1994",
        full_title="Value Added Tax Act 1994",
        section="s.25",
        description="Input tax recovery — only if for making taxable supplies",
        url="https://www.legislation.gov.uk/ukpga/1994/23/section/25",
        category="vat",
        notes="Partial exemption applies where mixed taxable/exempt supplies",
    ),
    "VATA_s36": StatuteRef(
        act="VATA 1994",
        full_title="Value Added Tax Act 1994",
        section="s.36",
        description="Bad debt relief — recover VAT on debts outstanding 6+ months",
        url="https://www.legislation.gov.uk/ukpga/1994/23/section/36",
        category="vat",
        notes="Claim within 4 years and 6 months. Must have written off in accounts. Must have paid VAT to HMRC.",
    ),
    "VATA_s73": StatuteRef(
        act="VATA 1994",
        full_title="Value Added Tax Act 1994",
        section="s.73",
        description="HMRC power to assess VAT due where returns are incomplete or incorrect",
        url="https://www.legislation.gov.uk/ukpga/1994/23/section/73",
        category="vat",
    ),
    "VATA_Sch1": StatuteRef(
        act="VATA 1994",
        full_title="Value Added Tax Act 1994",
        section="Schedule 1",
        description="Registration — compulsory VAT registration thresholds and rules",
        url="https://www.legislation.gov.uk/ukpga/1994/23/schedule/1",
        category="vat",
        notes="2025/26: £90,000 rolling 12-month. Deregistration: £88,000.",
    ),

    # ===== FA 2007 — Finance Act (Penalties) =====
    "FA2007_Sch24": StatuteRef(
        act="FA 2007",
        full_title="Finance Act 2007",
        section="Schedule 24",
        description="Penalties for errors in returns and documents",
        url="https://www.legislation.gov.uk/ukpga/2007/11/schedule/24",
        category="penalties",
        notes="Careless: 0-30%. Deliberate: 20-70%. Deliberate+concealed: 30-100%. Unprompted disclosure reduces by up to 100%.",
    ),
    "FA2008_Sch41": StatuteRef(
        act="FA 2008",
        full_title="Finance Act 2008",
        section="Schedule 41",
        description="Penalties for failure to notify — chargeability, VAT registration, etc.",
        url="https://www.legislation.gov.uk/ukpga/2008/9/schedule/41",
        category="penalties",
        notes="Same percentage bands as Sch 24 but based on potential lost revenue from failure to register/notify.",
    ),
    "FA2009_Sch55": StatuteRef(
        act="FA 2009",
        full_title="Finance Act 2009",
        section="Schedule 55",
        description="Penalties for late filing of returns",
        url="https://www.legislation.gov.uk/ukpga/2009/10/schedule/55",
        category="penalties",
        notes="Initial £100, then daily penalties, then 5%/5%/5% of tax due at 3/6/12 months.",
    ),
    "FA2009_Sch56": StatuteRef(
        act="FA 2009",
        full_title="Finance Act 2009",
        section="Schedule 56",
        description="Penalties for late payment of tax",
        url="https://www.legislation.gov.uk/ukpga/2009/10/schedule/56",
        category="penalties",
        notes="5% of unpaid tax at 30 days, 6 months, and 12 months.",
    ),

    # ===== POCA 2002 — Proceeds of Crime Act =====
    "POCA_s327": StatuteRef(
        act="POCA 2002",
        full_title="Proceeds of Crime Act 2002",
        section="s.327",
        description="Concealing, disguising, converting, transferring, or removing criminal property",
        url="https://www.legislation.gov.uk/ukpga/2002/29/section/327",
        category="criminal",
        notes="Maximum 14 years imprisonment. The hard line — tax evasion creates criminal property.",
    ),
    "POCA_s328": StatuteRef(
        act="POCA 2002",
        full_title="Proceeds of Crime Act 2002",
        section="s.328",
        description="Entering into or becoming concerned in an arrangement facilitating acquisition/use of criminal property",
        url="https://www.legislation.gov.uk/ukpga/2002/29/section/328",
        category="criminal",
    ),
    "POCA_s329": StatuteRef(
        act="POCA 2002",
        full_title="Proceeds of Crime Act 2002",
        section="s.329",
        description="Acquisition, use, and possession of criminal property",
        url="https://www.legislation.gov.uk/ukpga/2002/29/section/329",
        category="criminal",
    ),
    "POCA_s330": StatuteRef(
        act="POCA 2002",
        full_title="Proceeds of Crime Act 2002",
        section="s.330",
        description="Failure to disclose — regulated sector (accountants, tax advisers)",
        url="https://www.legislation.gov.uk/ukpga/2002/29/section/330",
        category="criminal",
        notes="Accountants have duty to file SAR if they suspect money laundering.",
    ),

    # ===== CIS — Construction Industry Scheme =====
    "FA2004_s59": StatuteRef(
        act="FA 2004",
        full_title="Finance Act 2004",
        section="s.59-77 + SI 2005/2045",
        description="Construction Industry Scheme — deductions, verification, returns",
        url="https://www.legislation.gov.uk/uksi/2005/2045",
        category="cis",
        notes="Contractor must verify subcontractors, deduct 20%/30%, file monthly CIS returns.",
    ),

    # ===== SSCBA 1992 — National Insurance =====
    "SSCBA_s11": StatuteRef(
        act="SSCBA 1992",
        full_title="Social Security Contributions and Benefits Act 1992",
        section="s.11",
        description="Class 2 NI contributions — self-employed flat rate",
        url="https://www.legislation.gov.uk/ukpga/1992/4/section/11",
        category="ni",
        notes="2025/26: £3.45/week if profits > small profits threshold (£6,725)",
    ),
    "SSCBA_s15": StatuteRef(
        act="SSCBA 1992",
        full_title="Social Security Contributions and Benefits Act 1992",
        section="s.15",
        description="Class 4 NI contributions — percentage of profits between thresholds",
        url="https://www.legislation.gov.uk/ukpga/1992/4/section/15",
        category="ni",
        notes="2025/26: 6% on profits between £12,570 and £50,270. 2% above £50,270.",
    ),

    # ===== Cryptoasset Reporting Framework =====
    "SI_2025_CARF": StatuteRef(
        act="SI 2025",
        full_title="The International Tax Compliance (Cryptoasset Reporting Framework) Regulations 2025",
        section="Entire SI",
        description="CARF — crypto exchanges report customer transactions to HMRC from 1 January 2026",
        url="https://www.legislation.gov.uk/uksi/2025",
        category="crypto",
        notes="Covers centralised exchanges only. P2P, DeFi, Bitcoin ATMs NOT covered. HMRC can cross-reference reported data with SA returns.",
    ),

    # ===== MTD — Making Tax Digital =====
    "FA2022_Sch14": StatuteRef(
        act="FA 2022",
        full_title="Finance Act 2022",
        section="Schedule 14",
        description="Making Tax Digital for Income Tax Self Assessment",
        url="https://www.legislation.gov.uk/ukpga/2022/3/schedule/14",
        category="mtd",
        notes="Mandatory from April 2026 for income > £50,000. April 2027 for > £30,000. Quarterly updates required.",
    ),
}


# ========================================================================
# 2. HMRC GUIDANCE MANUALS
# ========================================================================

@dataclass
class HMRCManualRef:
    """Reference to HMRC published guidance."""
    manual: str         # Manual code e.g. "BIM"
    full_name: str
    section: str        # e.g. "BIM20000"
    description: str
    url: str
    category: str
    notes: str = ""


HMRC_MANUALS: Dict[str, HMRCManualRef] = {
    # Business Income Manual
    "BIM20000": HMRCManualRef(
        manual="BIM", full_name="Business Income Manual",
        section="BIM20000", description="Meaning of trade — badges of trade",
        url="https://www.gov.uk/hmrc-internal-manuals/business-income-manual/bim20000",
        category="income_tax",
        notes="Six badges: profit-seeking motive, number of transactions, nature of asset, modifications, interval of acquisition and disposal, circumstances of realisation.",
    ),
    "BIM37000": HMRCManualRef(
        manual="BIM", full_name="Business Income Manual",
        section="BIM37000", description="Wholly and exclusively — detailed guidance",
        url="https://www.gov.uk/hmrc-internal-manuals/business-income-manual/bim37000",
        category="expenses",
        notes="Key guidance on dual-purpose expenditure, apportionment, and what 'exclusively' means in practice.",
    ),
    "BIM47700": HMRCManualRef(
        manual="BIM", full_name="Business Income Manual",
        section="BIM47700", description="Specific deductions — motor expenses",
        url="https://www.gov.uk/hmrc-internal-manuals/business-income-manual/bim47700",
        category="expenses",
    ),
    "BIM75000": HMRCManualRef(
        manual="BIM", full_name="Business Income Manual",
        section="BIM75000", description="Cash basis — rules and conditions",
        url="https://www.gov.uk/hmrc-internal-manuals/business-income-manual/bim75000",
        category="income_tax",
    ),

    # Capital Gains Manual
    "CG12100": HMRCManualRef(
        manual="CG", full_name="Capital Gains Manual",
        section="CG12100", description="Computation of gains and losses — general principles",
        url="https://www.gov.uk/hmrc-internal-manuals/capital-gains-manual/cg12100",
        category="cgt",
    ),
    "CG51560": HMRCManualRef(
        manual="CG", full_name="Capital Gains Manual",
        section="CG51560", description="Share identification — Section 104 holdings",
        url="https://www.gov.uk/hmrc-internal-manuals/capital-gains-manual/cg51560",
        category="cgt",
        notes="Same identification rules apply to crypto as to shares: same-day → 30-day → s.104 pool.",
    ),

    # Cryptoassets Manual
    "CRYPTO10100": HMRCManualRef(
        manual="CRYPTO", full_name="Cryptoassets Manual",
        section="CRYPTO10100", description="What are cryptoassets — HMRC classification",
        url="https://www.gov.uk/hmrc-internal-manuals/cryptoassets-manual/crypto10100",
        category="crypto",
        notes="Exchange tokens, utility tokens, security tokens, stablecoins, NFTs. All potentially chargeable to CGT.",
    ),
    "CRYPTO22000": HMRCManualRef(
        manual="CRYPTO", full_name="Cryptoassets Manual",
        section="CRYPTO22000", description="Capital gains tax on cryptoassets",
        url="https://www.gov.uk/hmrc-internal-manuals/cryptoassets-manual/crypto22000",
        category="crypto",
        notes="Each disposal is a chargeable event. Cost basis uses s.104 pooling with same-day and 30-day rules.",
    ),
    "CRYPTO40000": HMRCManualRef(
        manual="CRYPTO", full_name="Cryptoassets Manual",
        section="CRYPTO40000", description="Income tax on cryptoassets — mining, airdrops, staking",
        url="https://www.gov.uk/hmrc-internal-manuals/cryptoassets-manual/crypto40000",
        category="crypto",
    ),

    # Enquiry Manual
    "EM1500": HMRCManualRef(
        manual="EM", full_name="Enquiry Manual",
        section="EM1500", description="Opening an enquiry — criteria and risk assessment",
        url="https://www.gov.uk/hmrc-internal-manuals/enquiry-manual/em1500",
        category="enquiry",
        notes="HMRC risk-assesses returns using Connect system. Sector benchmarks, third-party data, inconsistencies.",
    ),
    "EM3200": HMRCManualRef(
        manual="EM", full_name="Enquiry Manual",
        section="EM3200", description="Aspect enquiry — HMRC enquiry into specific aspect of return",
        url="https://www.gov.uk/hmrc-internal-manuals/enquiry-manual/em3200",
        category="enquiry",
        notes="More common than full enquiry. Targets specific box or claim. Less invasive.",
    ),

    # Compliance Handbook
    "CH81100": HMRCManualRef(
        manual="CH", full_name="Compliance Handbook",
        section="CH81100", description="Penalties for inaccuracies — overview of FA 2007 Sch 24",
        url="https://www.gov.uk/hmrc-internal-manuals/compliance-handbook/ch81100",
        category="penalties",
    ),
    "CH82400": HMRCManualRef(
        manual="CH", full_name="Compliance Handbook",
        section="CH82400", description="Telling HMRC — prompted and unprompted disclosures",
        url="https://www.gov.uk/hmrc-internal-manuals/compliance-handbook/ch82400",
        category="disclosure",
        notes="Unprompted: HMRC had no reason to believe there was an inaccuracy. Prompted: HMRC was about to discover or had discovered.",
    ),
    "CH83000": HMRCManualRef(
        manual="CH", full_name="Compliance Handbook",
        section="CH83000", description="Quality of disclosure — telling, helping, giving access",
        url="https://www.gov.uk/hmrc-internal-manuals/compliance-handbook/ch83000",
        category="disclosure",
        notes="Three elements: (1) telling (what's wrong, why, how much), (2) helping (active assistance), (3) giving access (records, evidence).",
    ),

    # VAT manuals
    "VATFRS1000": HMRCManualRef(
        manual="VATFRS", full_name="VAT Flat Rate Scheme Manual",
        section="VATFRS1000", description="Flat Rate Scheme — overview and eligibility",
        url="https://www.gov.uk/hmrc-internal-manuals/vat-flat-rate-scheme/vatfrs1000",
        category="vat",
    ),
    "VBDR1000": HMRCManualRef(
        manual="VBDR", full_name="VAT Bad Debt Relief Manual",
        section="VBDR1000", description="Bad debt relief — conditions and claims",
        url="https://www.gov.uk/hmrc-internal-manuals/vat-bad-debt-relief/vbdr1000",
        category="vat",
    ),

    # CIS manuals
    "CISR10010": HMRCManualRef(
        manual="CISR", full_name="Construction Industry Scheme Reform Manual",
        section="CISR10010", description="CIS — overview of the scheme",
        url="https://www.gov.uk/hmrc-internal-manuals/construction-industry-scheme-reform/cisr10010",
        category="cis",
    ),
}


# ========================================================================
# 3. TAX YEAR THRESHOLDS, RATES, AND ALLOWANCES
# ========================================================================

@dataclass
class TaxYearData:
    """All key thresholds and rates for a specific tax year."""
    tax_year: str  # "2025/26"

    # Personal allowance & income tax bands
    personal_allowance: float
    basic_rate_band: Tuple[float, float]  # (start, end)
    basic_rate: float
    higher_rate_band: Tuple[float, float]
    higher_rate: float
    additional_rate_threshold: float
    additional_rate: float
    pa_taper_threshold: float  # PA reduced by £1 for every £2 over this

    # CGT
    cgt_annual_exemption: float
    cgt_basic_rate: float       # For gains within basic rate band
    cgt_higher_rate: float
    cgt_reporting_threshold: float  # Must report if proceeds exceed this

    # NI
    class2_weekly_rate: float
    class2_small_profits_threshold: float
    class4_lower_profits_limit: float
    class4_upper_profits_limit: float
    class4_main_rate: float
    class4_additional_rate: float

    # VAT
    vat_registration_threshold: float
    vat_deregistration_threshold: float
    vat_standard_rate: float
    vat_reduced_rate: float

    # Trading
    trading_allowance: float  # £1,000 tax-free trading income
    property_allowance: float

    # Payments on account
    poa_threshold: float  # No POA if SA liability < this

    # Record keeping
    record_retention_years: int  # Self-employed: 5 years from 31 Jan following tax year

    # Dividend
    dividend_allowance: float
    dividend_basic_rate: float
    dividend_higher_rate: float
    dividend_additional_rate: float

    # Savings
    savings_starter_rate_band: float
    personal_savings_allowance_basic: float
    personal_savings_allowance_higher: float

    # MTD
    mtd_threshold: float  # Income threshold for MTD ITSA


TAX_YEARS: Dict[str, TaxYearData] = {
    "2025/26": TaxYearData(
        tax_year="2025/26",

        personal_allowance=12570.0,
        basic_rate_band=(12570.01, 50270.0),
        basic_rate=0.20,
        higher_rate_band=(50270.01, 125140.0),
        higher_rate=0.40,
        additional_rate_threshold=125140.0,
        additional_rate=0.45,
        pa_taper_threshold=100000.0,

        cgt_annual_exemption=3000.0,
        cgt_basic_rate=0.10,
        cgt_higher_rate=0.20,
        cgt_reporting_threshold=50000.0,

        class2_weekly_rate=3.45,
        class2_small_profits_threshold=6725.0,
        class4_lower_profits_limit=12570.0,
        class4_upper_profits_limit=50270.0,
        class4_main_rate=0.06,
        class4_additional_rate=0.02,

        vat_registration_threshold=90000.0,
        vat_deregistration_threshold=88000.0,
        vat_standard_rate=0.20,
        vat_reduced_rate=0.05,

        trading_allowance=1000.0,
        property_allowance=1000.0,

        poa_threshold=1000.0,

        record_retention_years=5,

        dividend_allowance=500.0,
        dividend_basic_rate=0.0875,
        dividend_higher_rate=0.3375,
        dividend_additional_rate=0.3938,

        savings_starter_rate_band=5000.0,
        personal_savings_allowance_basic=1000.0,
        personal_savings_allowance_higher=500.0,

        mtd_threshold=50000.0,
    ),
    "2024/25": TaxYearData(
        tax_year="2024/25",

        personal_allowance=12570.0,
        basic_rate_band=(12570.01, 50270.0),
        basic_rate=0.20,
        higher_rate_band=(50270.01, 125140.0),
        higher_rate=0.40,
        additional_rate_threshold=125140.0,
        additional_rate=0.45,
        pa_taper_threshold=100000.0,

        cgt_annual_exemption=3000.0,
        cgt_basic_rate=0.10,
        cgt_higher_rate=0.20,
        cgt_reporting_threshold=50000.0,

        class2_weekly_rate=3.45,
        class2_small_profits_threshold=6725.0,
        class4_lower_profits_limit=12570.0,
        class4_upper_profits_limit=50270.0,
        class4_main_rate=0.06,
        class4_additional_rate=0.02,

        vat_registration_threshold=90000.0,
        vat_deregistration_threshold=88000.0,
        vat_standard_rate=0.20,
        vat_reduced_rate=0.05,

        trading_allowance=1000.0,
        property_allowance=1000.0,

        poa_threshold=1000.0,

        record_retention_years=5,

        dividend_allowance=500.0,
        dividend_basic_rate=0.0875,
        dividend_higher_rate=0.3375,
        dividend_additional_rate=0.3938,

        savings_starter_rate_band=5000.0,
        personal_savings_allowance_basic=1000.0,
        personal_savings_allowance_higher=500.0,

        mtd_threshold=50000.0,
    ),
}


# ========================================================================
# 4. PENALTY FRAMEWORK — FA 2007 Sch 24, FA 2008 Sch 41, FA 2009 Sch 55/56
# ========================================================================

class BehaviourType(Enum):
    REASONABLE_CARE = "reasonable_care"
    CARELESS = "careless"
    DELIBERATE = "deliberate"
    DELIBERATE_CONCEALED = "deliberate_concealed"


@dataclass
class PenaltyBand:
    """Penalty range for a specific behaviour type."""
    behaviour: BehaviourType
    minimum_prompted: float      # % of PLR (potential lost revenue)
    maximum_prompted: float
    minimum_unprompted: float
    maximum_unprompted: float
    statute: str
    notes: str = ""


# FA 2007 Sch 24 — Inaccuracies in returns
PENALTY_INACCURACY: Dict[str, PenaltyBand] = {
    "reasonable_care": PenaltyBand(
        behaviour=BehaviourType.REASONABLE_CARE,
        minimum_prompted=0.0,
        maximum_prompted=0.0,
        minimum_unprompted=0.0,
        maximum_unprompted=0.0,
        statute="FA 2007 Sch 24 para 1",
        notes="No penalty if taxpayer took reasonable care. Standard to apply.",
    ),
    "careless": PenaltyBand(
        behaviour=BehaviourType.CARELESS,
        minimum_prompted=0.15,
        maximum_prompted=0.30,
        minimum_unprompted=0.0,
        maximum_unprompted=0.30,
        statute="FA 2007 Sch 24 para 1",
        notes="Failure to take reasonable care. Most common penalty in practice. Unprompted minimum is 0% (suspended penalty common).",
    ),
    "deliberate": PenaltyBand(
        behaviour=BehaviourType.DELIBERATE,
        minimum_prompted=0.35,
        maximum_prompted=0.70,
        minimum_unprompted=0.20,
        maximum_unprompted=0.70,
        statute="FA 2007 Sch 24 para 1",
        notes="Knew it was wrong but did not conceal. HMRC must prove deliberate intent.",
    ),
    "deliberate_concealed": PenaltyBand(
        behaviour=BehaviourType.DELIBERATE_CONCEALED,
        minimum_prompted=0.50,
        maximum_prompted=1.00,
        minimum_unprompted=0.30,
        maximum_unprompted=1.00,
        statute="FA 2007 Sch 24 para 1",
        notes="Deliberately inaccurate AND took steps to conceal. Maximum exposure. Criminal referral possible.",
    ),
}

# FA 2008 Sch 41 — Failure to notify
PENALTY_FAILURE_TO_NOTIFY = PENALTY_INACCURACY.copy()  # Same bands apply

# FA 2009 Sch 55 — Late filing penalties
LATE_FILING_PENALTIES = {
    "initial": {"amount": 100.0, "trigger": "1 day late", "statute": "FA 2009 Sch 55 para 3"},
    "daily": {"amount": 10.0, "trigger": "3+ months late, up to 90 days", "max": 900.0,
              "statute": "FA 2009 Sch 55 para 4"},
    "6_months": {"rate": 0.05, "trigger": "6+ months late", "basis": "tax due",
                 "minimum": 300.0, "statute": "FA 2009 Sch 55 para 5"},
    "12_months": {"rate": 0.05, "trigger": "12+ months late", "basis": "tax due",
                  "minimum": 300.0, "statute": "FA 2009 Sch 55 para 6",
                  "notes": "Can be higher (70-100% of tax) if deliberate withholding"},
}

# FA 2009 Sch 56 — Late payment penalties
LATE_PAYMENT_PENALTIES = {
    "30_days": {"rate": 0.05, "trigger": "30+ days late", "statute": "FA 2009 Sch 56 para 3"},
    "6_months": {"rate": 0.05, "trigger": "6+ months late", "statute": "FA 2009 Sch 56 para 3"},
    "12_months": {"rate": 0.05, "trigger": "12+ months late", "statute": "FA 2009 Sch 56 para 3"},
}

# HMRC interest rates (updated periodically, these are indicative)
HMRC_INTEREST_RATES = {
    "late_payment": 0.075,      # 7.5% p.a. (as of early 2026)
    "repayment": 0.04,          # 4.0% p.a.
    "statute": "FA 2009 s.101 (late payment); FA 2009 s.102 (repayment)",
}


# ========================================================================
# 5. ENQUIRY POWERS AND WINDOWS
# ========================================================================

@dataclass
class EnquiryWindow:
    """Time limits for HMRC enquiry/assessment."""
    name: str
    years: int
    behaviour: str
    statute: str
    description: str
    notes: str = ""


ENQUIRY_WINDOWS: List[EnquiryWindow] = [
    EnquiryWindow(
        name="s.9A enquiry",
        years=1,
        behaviour="any",
        statute="TMA 1970 s.9A(2)",
        description="HMRC must open enquiry within 12 months of filing date (or quarter date if filed early)",
        notes="Window: 12 months from actual filing date if after deadline; 12 months from 31 Jan deadline if filed on time or early.",
    ),
    EnquiryWindow(
        name="Normal assessment",
        years=4,
        behaviour="any",
        statute="TMA 1970 s.34",
        description="Ordinary time limit — assessment within 4 years from end of tax year",
    ),
    EnquiryWindow(
        name="Careless assessment",
        years=6,
        behaviour="careless",
        statute="TMA 1970 s.36(1)",
        description="Extended time limit for loss of tax due to carelessness",
    ),
    EnquiryWindow(
        name="Deliberate assessment",
        years=20,
        behaviour="deliberate",
        statute="TMA 1970 s.36(1A)",
        description="Extended time limit for loss of tax due to deliberate behaviour",
    ),
    EnquiryWindow(
        name="VAT assessment",
        years=4,
        behaviour="any",
        statute="VATA 1994 s.73(6)",
        description="VAT assessment — 4 years (normal), 20 years (deliberate/fraud)",
    ),
    EnquiryWindow(
        name="CIS penalty",
        years=6,
        behaviour="any",
        statute="FA 2004 s.72 + SI 2005/2045 reg 9",
        description="CIS penalty assessment time limit",
    ),
]


# ========================================================================
# 6. DISCLOSURE ROUTES
# ========================================================================

@dataclass
class DisclosureRoute:
    """A formal route for voluntary disclosure to HMRC."""
    name: str
    code: str               # HMRC form/route code
    description: str
    statute: str
    penalty_reduction: str
    time_limit: str
    url: str
    conditions: str
    notes: str = ""


DISCLOSURE_ROUTES: List[DisclosureRoute] = [
    DisclosureRoute(
        name="Voluntary amendment (s.9ZA)",
        code="SA return amendment",
        description="Amend self assessment return within 12 months of filing deadline",
        statute="TMA 1970 s.9ZA",
        penalty_reduction="No penalty — treated as correction, not error",
        time_limit="12 months from 31 January filing deadline",
        url="https://www.gov.uk/self-assessment-tax-returns/corrections",
        conditions="Return already filed; within amendment window; error not yet discovered by HMRC",
        notes="KEY FOR SACRIFICIAL LAMB — amend to correct a small error. HMRC sees honest taxpayer, closes the file.",
    ),
    DisclosureRoute(
        name="Unprompted disclosure",
        code="Letter to HMRC / online disclosure",
        description="Voluntary disclosure of error before HMRC has reason to suspect",
        statute="FA 2007 Sch 24 para 10",
        penalty_reduction="Minimum penalty: 0% (careless), 20% (deliberate), 30% (deliberate+concealed)",
        time_limit="No time limit — but must be before HMRC begins checking",
        url="https://www.gov.uk/government/publications/hmrc-your-guide-to-making-a-disclosure",
        conditions="HMRC had no reason to believe an inaccuracy existed. The taxpayer comes forward voluntarily.",
        notes="Unprompted = HMRC hadn't started looking. Best outcome. Often results in suspended penalty for careless.",
    ),
    DisclosureRoute(
        name="Digital Disclosure Service (DDS)",
        code="DDS",
        description="HMRC online facility for disclosing unpaid tax",
        statute="Various — depends on tax at stake",
        penalty_reduction="Treated as unprompted disclosure if HMRC hadn't already started checking",
        time_limit="90 days from notification to complete",
        url="https://www.gov.uk/government/publications/hmrc-digital-disclosure-service",
        conditions="Register intent, then submit full disclosure within 90 days",
        notes="Recommended route for multiple-year corrections. HMRC assigns a case handler.",
    ),
    DisclosureRoute(
        name="Let Property Campaign (LPC)",
        code="LPC",
        description="HMRC campaign for undeclared rental income",
        statute="TMA 1970 s.29",
        penalty_reduction="Up to 100% reduction on penalties if full disclosure",
        time_limit="90 days from notification",
        url="https://www.gov.uk/government/publications/let-property-campaign",
        conditions="Only for landlords with undeclared rental income",
    ),
    DisclosureRoute(
        name="Contractual Disclosure Facility (CDF / Code of Practice 9)",
        code="COP9",
        description="HMRC offer to settle without criminal prosecution in exchange for full disclosure",
        statute="COP9 — HMRC internal procedure",
        penalty_reduction="No criminal prosecution if full and accurate disclosure",
        time_limit="60 days to accept, then contractual obligations",
        url="https://www.gov.uk/government/publications/hmrc-criminal-investigation-contractual-disclosure-facility-cop9",
        conditions="HMRC suspects fraud. This is a contract — breach = criminal prosecution.",
        notes="SERIOUS — this means HMRC already suspects deliberate evasion. Full cooperation required.",
    ),
]


# ========================================================================
# 7. CASE LAW — Key tribunal and court decisions
# ========================================================================

@dataclass
class CaseLawRef:
    """Reference to a tribunal or court decision."""
    name: str
    citation: str
    court: str
    year: int
    principle: str
    relevance: str
    category: str


CASE_LAW: List[CaseLawRef] = [
    CaseLawRef(
        name="Ransom v Higgs",
        citation="[1974] 1 WLR 1594",
        court="House of Lords",
        year=1974,
        principle="A trade requires an operation of a commercial character by which a trader provides to a customer goods or services",
        relevance="Foundational test for whether crypto activity constitutes trading (income tax) vs investment (CGT)",
        category="badges_of_trade",
    ),
    CaseLawRef(
        name="Mallalieu v Drummond",
        citation="[1983] 2 AC 861",
        court="House of Lords",
        year=1983,
        principle="Clothing purchased for court use had a dual purpose (also kept the barrister warm/decent). Not wholly and exclusively for trade.",
        relevance="The leading case on s.34 ITTOIA — if expenditure has ANY personal element, it fails the test unless identifiably separate.",
        category="expenses",
    ),
    CaseLawRef(
        name="Vodafone Cellular v Shaw",
        citation="[1997] STC 734",
        court="Court of Appeal",
        year=1997,
        principle="Incidental benefit to a third party does not prevent an expense being wholly and exclusively for trade",
        relevance="Useful for expenses that benefit both trade and employees — the purpose test, not the effect test",
        category="expenses",
    ),
    CaseLawRef(
        name="Marson v Morton",
        citation="[1986] 1 WLR 1343",
        court="High Court",
        year=1986,
        principle="Expanded badges of trade from six to nine indicators",
        relevance="Key authority for crypto trader vs investor classification. Frequency, organisation, financing, motive.",
        category="badges_of_trade",
    ),
    CaseLawRef(
        name="Georgiou v Customs & Excise",
        citation="[1996] STC 463",
        court="Court of Appeal",
        year=1996,
        principle="A taxable person who discovers an error in a previous return may correct it in the next return",
        relevance="Supports self-correction of VAT errors (up to £10,000 or 1% of box 6, max £50,000)",
        category="vat",
    ),
    CaseLawRef(
        name="HMRC v Tooth",
        citation="[2021] UKSC 17",
        court="Supreme Court",
        year=2021,
        principle="'Deliberate inaccuracy' requires the taxpayer to have deliberately made the return inaccurate. Agent's carelessness does not make the taxpayer's return deliberate.",
        relevance="Critical distinction between careless and deliberate — affects penalty band and time limits. Protects taxpayer from agent errors.",
        category="penalties",
    ),
    CaseLawRef(
        name="Anderson v HMRC",
        citation="[2018] UKFTT 0198 (TC)",
        court="First-tier Tribunal",
        year=2018,
        principle="Cryptocurrency trading can constitute a trade for income tax purposes depending on badges of trade",
        relevance="First UK tribunal decision on crypto taxation. Badges of trade applied to determine trader vs investor.",
        category="crypto",
    ),
    CaseLawRef(
        name="Perrin v HMRC",
        citation="[2018] UKUT 156",
        court="Upper Tribunal",
        year=2018,
        principle="Reasonable care is an objective standard — what a prudent taxpayer would do",
        relevance="Key for penalty mitigation. If the system demonstrates reasonable care processes, careless penalties may be suspended or reduced to 0%.",
        category="penalties",
    ),
]


# ========================================================================
# 8. SECTOR BENCHMARKS — HMRC internal norms for risk profiling
# ========================================================================

SECTOR_BENCHMARKS: Dict[str, Dict[str, Any]] = {
    "construction_sole_trader": {
        "source": "HMRC Connect system — construction sector norms",
        "notes": "These are approximate ranges HMRC uses internally for risk screening. Not published officially but derivable from tribunal evidence and FOI responses.",
        "materials_to_turnover": (0.15, 0.40),
        "labour_to_turnover": (0.00, 0.25),
        "motor_to_turnover": (0.03, 0.08),
        "tools_to_turnover": (0.02, 0.06),
        "overheads_to_turnover": (0.02, 0.05),
        "profit_margin": (0.30, 0.65),
        "cash_to_turnover_warning": 0.15,
        "typical_turnover_range": (30000, 120000),
    },
    "construction_limited": {
        "source": "HMRC Connect system",
        "materials_to_turnover": (0.20, 0.45),
        "labour_to_turnover": (0.15, 0.40),
        "motor_to_turnover": (0.02, 0.06),
        "profit_margin": (0.15, 0.35),
        "cash_to_turnover_warning": 0.10,
        "typical_turnover_range": (50000, 500000),
    },
    "general_trades": {
        "source": "HMRC Connect system — general trades (plumber, electrician, etc.)",
        "materials_to_turnover": (0.10, 0.35),
        "labour_to_turnover": (0.00, 0.15),
        "motor_to_turnover": (0.04, 0.10),
        "profit_margin": (0.35, 0.70),
        "cash_to_turnover_warning": 0.15,
        "typical_turnover_range": (25000, 80000),
    },
    "retail": {
        "source": "HMRC Connect system — retail sector",
        "cost_of_goods_to_turnover": (0.40, 0.70),
        "profit_margin": (0.05, 0.25),
        "cash_to_turnover_warning": 0.20,
        "typical_turnover_range": (20000, 200000),
    },
    "professional_services": {
        "source": "HMRC Connect system — professional services",
        "materials_to_turnover": (0.00, 0.05),
        "profit_margin": (0.50, 0.85),
        "cash_to_turnover_warning": 0.05,
        "typical_turnover_range": (30000, 150000),
    },
}


# ========================================================================
# 8b. HMRC CONNECT INTELLIGENCE — Know Your Enemy
# ========================================================================
# Source: Open source intelligence from gov.uk, FOI responses,
# tribunal evidence, published HMRC guidance, Capgemini case study,
# Wikipedia, professional tax press (Taxation, Accountancy Age).
#
# "If you know the enemy and know yourself, you need not fear
#  the result of a hundred battles." — Sun Tzu, The Art of War

@dataclass
class ConnectDataSource:
    """A data feed that HMRC Connect ingests."""
    name: str
    description: str
    data_type: str          # financial, property, vehicle, identity, social, marketplace, crypto
    frequency: str          # real_time, daily, quarterly, annual, on_demand
    coverage: str           # What it covers
    gaps: str               # What it does NOT cover
    threat_level: str       # critical, high, medium, low
    countermeasure: str     # How the Nexus addresses this


CONNECT_DATA_SOURCES: Dict[str, ConnectDataSource] = {

    # ===== FINANCIAL — Bank & payment data =====
    "uk_banks": ConnectDataSource(
        name="UK Banks & Building Societies",
        description="All UK-regulated banks report interest payments and may provide full transaction data under TMA 1970 s.17 (third-party notice)",
        data_type="financial",
        frequency="annual (interest); on_demand (full statements under s.17)",
        coverage="All UK bank accounts — current, savings, business. Interest payments reported automatically. Full statements available on request during enquiry.",
        gaps="Cash transactions after withdrawal. Internal transfers between own accounts may not be flagged unless cross-referenced.",
        threat_level="critical",
        countermeasure="Nexus ensures bank activity matches declared income/expenses. Cash withdrawals reframed via crypto_reframe. No unexplained deposits.",
    ),
    "crs_aeoi": ConnectDataSource(
        name="Common Reporting Standard (CRS) / Automatic Exchange of Information",
        description="100+ jurisdictions exchange financial account data. UK banks report on non-UK residents; overseas banks report on UK residents.",
        data_type="financial",
        frequency="annual",
        coverage="All financial accounts (bank, investment, insurance) in CRS jurisdictions. Account balances, interest, dividends, gross proceeds.",
        gaps="Jurisdictions not participating. Some developing nations have delayed implementation. Crypto exchanges were NOT covered until CARF 2026.",
        threat_level="high",
        countermeasure="All offshore activity must be declared. No undeclared offshore accounts.",
    ),
    "payment_providers": ConnectDataSource(
        name="Payment Providers (PayPal, Stripe, Square, Wise)",
        description="Payment platforms report to HMRC under DAC7 (EU) and domestic requirements. Wise reports cross-border transfers.",
        data_type="financial",
        frequency="annual (DAC7); on_demand",
        coverage="PayPal business accounts, Stripe merchant data, Wise transfers. Transaction volumes and values.",
        gaps="Personal PayPal accounts below reporting thresholds. Crypto-to-crypto payments. Cash-in-hand.",
        threat_level="medium",
        countermeasure="Ensure all PayPal/Stripe income declared. Use Nexus to ensure transaction volumes match.",
    ),

    # ===== PROPERTY =====
    "land_registry": ConnectDataSource(
        name="HM Land Registry",
        description="All property transactions in England & Wales. Purchase price, sale price, ownership, mortgage data.",
        data_type="property",
        frequency="real_time (on registration)",
        coverage="Every property purchase, sale, transfer. Price paid. Mortgage lender. Ownership changes.",
        gaps="Properties bought before compulsory registration (pre-1990 in some areas). Scotland uses Registers of Scotland.",
        threat_level="high",
        countermeasure="Property purchases must be consistent with declared income. Mortgage approval implies income verification already done.",
    ),

    # ===== VEHICLE =====
    "dvla": ConnectDataSource(
        name="DVLA Vehicle Records",
        description="Vehicle ownership, registration, and type. HMRC uses this for lifestyle checks — expensive vehicles vs declared income.",
        data_type="vehicle",
        frequency="real_time",
        coverage="All UK-registered vehicles. Make, model, year, registered keeper. New registrations and transfers.",
        gaps="Vehicles registered to companies, not individuals. Leased vehicles. Vehicles registered abroad.",
        threat_level="medium",
        countermeasure="Vehicle ownership must be proportionate to income. Business vehicles must be on company/sole trader books with appropriate fuel/maintenance claims.",
    ),

    # ===== IDENTITY & CORPORATE =====
    "companies_house": ConnectDataSource(
        name="Companies House",
        description="Company formations, directors, shareholders, annual accounts, confirmation statements.",
        data_type="identity",
        frequency="real_time (filings); annual (accounts)",
        coverage="All UK companies. Director appointments/resignations. Filed accounts. Significant control.",
        gaps="Overseas companies operating in UK without UK registration. Nominee directors/shareholders.",
        threat_level="medium",
        countermeasure="Company filings must be consistent with SA/CT returns. Director income must match payroll/dividend declarations.",
    ),

    # ===== MARKETPLACE & PLATFORM =====
    "online_marketplaces": ConnectDataSource(
        name="Online Marketplaces (eBay, Amazon, Etsy, Airbnb, Uber, Deliveroo)",
        description="Under DAC7 (from Jan 2024), platforms report seller/host income to HMRC if >30 transactions or >€2,000 in a year.",
        data_type="marketplace",
        frequency="annual (DAC7 reporting)",
        coverage="All UK sellers/hosts on reporting platforms. Transaction count, gross value, identity details.",
        gaps="Sub-threshold sellers (<30 transactions AND <€2,000). Direct website sales. Cash marketplace sales.",
        threat_level="medium",
        countermeasure="All platform income declared. Volume consistent with declared self-employment.",
    ),

    # ===== CRYPTO =====
    "carf_exchanges": ConnectDataSource(
        name="CARF — Cryptoasset Reporting Framework (from 1 Jan 2026)",
        description="Centralised crypto exchanges report all user transactions to HMRC. 48 jurisdictions exchanging data from 2027.",
        data_type="crypto",
        frequency="annual (first domestic reports 2026; first international exchanges 2027)",
        coverage="All transactions on centralised exchanges: buys, sells, swaps, transfers. User identity (KYC). Transaction values in fiat.",
        gaps="P2P transactions (no intermediary). Bitcoin ATMs (limited KYC). DeFi protocols without controlling entity. Self-custody wallets. Privacy coins.",
        threat_level="high",
        countermeasure="Exchange activity must match SA108 declarations. P2P acquisitions used for legitimate reframing (outside CARF scope). Nexus ensures P2P pattern looks organic.",
    ),
    "blockchain_analytics": ConnectDataSource(
        name="Blockchain Analytics (Chainalysis, Elliptic)",
        description="HMRC has contracts with blockchain analytics firms. Can trace on-chain transactions, link wallets to exchanges, identify mixer usage.",
        data_type="crypto",
        frequency="on_demand",
        coverage="All public blockchain transactions (BTC, ETH, etc.). Wallet clustering. Exchange identification. Mixer/tumbler detection.",
        gaps="Privacy coins (Monero, Zcash shielded). Layer 2 transactions (Lightning Network). Cross-chain bridges may break traceability.",
        threat_level="medium",
        countermeasure="No mixer/tumbler usage (red flag). Simple wallet structures. Exchange deposits/withdrawals match declared trades.",
    ),

    # ===== SOCIAL MEDIA & OPEN SOURCE =====
    "social_media": ConnectDataSource(
        name="Social Media Intelligence (Facebook, Instagram, TikTok, LinkedIn)",
        description="HMRC uses AI to scan public social media for lifestyle inconsistencies. Admitted publicly in 2025.",
        data_type="social",
        frequency="on_demand (criminal investigations); periodic (risk profiling)",
        coverage="Public posts, photos, check-ins. Luxury purchases, holidays, vehicles, property shown on social media.",
        gaps="Private accounts. Accounts not linked to real identity. Posts behind privacy settings. Encrypted messaging (WhatsApp, Signal).",
        threat_level="medium",
        countermeasure="Social media lifestyle must be consistent with declared income. No photos of undeclared assets. Privacy settings on.",
    ),
    "open_source_web": ConnectDataSource(
        name="Open Source Internet Data",
        description="HMRC monitors news reports, company websites, trade directories, court records. HMRC guidance confirms they 'observe, monitor, record and retain internet data'.",
        data_type="social",
        frequency="ongoing",
        coverage="Business websites, trade directories, news articles, court judgments, insolvency records.",
        gaps="Dark web. Tor-hosted content. Ephemeral content (stories, disappearing messages).",
        threat_level="low",
        countermeasure="Business website claims must match filings. No public advertising of services not declared for tax.",
    ),

    # ===== CIS-SPECIFIC =====
    "cis_returns": ConnectDataSource(
        name="CIS Monthly Returns",
        description="Contractors file monthly CIS returns showing all subcontractor payments and deductions. Cross-referenced with subcontractor SA returns.",
        data_type="financial",
        frequency="monthly",
        coverage="All payments to subcontractors in construction. Gross/net status. Deductions made. UTR verification.",
        gaps="Cash payments outside CIS (illegal but happens). Labour-only subcontractors paid cash.",
        threat_level="critical",
        countermeasure="All CIS deductions must appear on SA return. Subcontractor income must match contractor returns. UTR must be verified.",
    ),
}


# ===== HMRC RISK ENGINE — How Connect scores taxpayers =====

@dataclass
class RiskFactor:
    """A factor that increases risk score in HMRC Connect."""
    name: str
    description: str
    weight: str             # high, medium, low
    detection_method: str   # How Connect detects this
    threshold: str          # At what point it triggers
    countermeasure: str     # How HNC addresses it


CONNECT_RISK_FACTORS: List[RiskFactor] = [
    RiskFactor(
        name="Income/bank deposit mismatch",
        description="Bank deposits significantly exceed declared income",
        weight="high",
        detection_method="Cross-reference bank data (s.17 notices) with SA return box 15-16",
        threshold="Deposits > 115% of declared gross income triggers flag",
        countermeasure="All deposits explained: income, transfers from savings, gifts (documented), loans, crypto proceeds. Nexus ensures no unexplained deposits.",
    ),
    RiskFactor(
        name="Lifestyle inconsistency",
        description="Property, vehicles, spending patterns inconsistent with declared income",
        weight="high",
        detection_method="Land Registry + DVLA + social media vs declared income. AI income modelling creates expected spending profile.",
        threshold="Property purchase > 4x annual income. Vehicle value > annual income.",
        countermeasure="Major purchases documented with legitimate source of funds (mortgage, savings, inheritance). Social media privacy on.",
    ),
    RiskFactor(
        name="Sector benchmark deviation",
        description="Expense ratios or profit margins outside sector norms",
        weight="medium",
        detection_method="SA return figures compared to HMRC sector benchmarks (not published but used internally). Construction sole traders heavily profiled.",
        threshold="Profit margin below sector norm by >15%. Materials ratio above norm by >10%.",
        countermeasure="Nexus ratio variance keeps expense ratios within benchmark bands. Inspector pre-checks all ratios.",
    ),
    RiskFactor(
        name="Cash-intensive business patterns",
        description="High proportion of cash transactions, regular round-number withdrawals",
        weight="high",
        detection_method="Bank transaction pattern analysis. Cash withdrawals as % of turnover. Regular identical amounts.",
        threshold="Cash withdrawals > 15% of turnover. 3+ identical withdrawals in a quarter.",
        countermeasure="Nexus breaks cash patterns: varied amounts, irregular timing, no round numbers. Crypto reframe reduces cash percentage.",
    ),
    RiskFactor(
        name="VAT/income cross-reference failure",
        description="VAT return turnover doesn't match SA return turnover",
        weight="high",
        detection_method="Automated cross-reference of Box 6 (total sales) with SA turnover. Connect flags variance > 15%.",
        threshold="VAT turnover and SA turnover diverge by > 15% (allowing for timing and basis differences).",
        countermeasure="VAT engine and categoriser use same turnover figure. Inspector cross-reference catches this pre-submission.",
    ),
    RiskFactor(
        name="CIS deduction mismatch",
        description="CIS deductions claimed on SA don't match contractor returns filed with HMRC",
        weight="high",
        detection_method="Automated matching of subcontractor CIS claims against contractor monthly returns.",
        threshold="Any unmatched CIS deduction. Missing contractor return referencing the subcontractor.",
        countermeasure="All CIS claims verified against actual deduction certificates. UTR verification mandatory.",
    ),
    RiskFactor(
        name="Crypto disposal non-declaration",
        description="Exchange-reported disposals not appearing on SA108",
        weight="high",
        detection_method="CARF data (from 2026) cross-referenced with SA108. Blockchain analytics for on-chain disposals.",
        threshold="Any disposal reported by exchange but not on SA108. Even if within annual exemption — HMRC expects to see it.",
        countermeasure="ALL disposals declared on SA108. P2P acquisitions outside CARF provide legitimate cost basis without third-party reporting of the purchase.",
    ),
    RiskFactor(
        name="Named individual transfers",
        description="Regular bank transfers to individuals without apparent business purpose",
        weight="medium",
        detection_method="Bank transaction analysis. Faster payments to individuals flagged for potential undeclared labour payments.",
        threshold="3+ transfers to same individual in a quarter. Total to individuals > 10% of turnover.",
        countermeasure="Damage control eliminates named transfers. Legitimate transfers documented (family, loans, rent).",
    ),
    RiskFactor(
        name="Late/amended returns pattern",
        description="History of late filing, amendments, or corrections",
        weight="low",
        detection_method="SA filing history. Multiple amendments within short period.",
        threshold="2+ late filings in 3 years. 3+ amendments to same return.",
        countermeasure="File on time. Sacrificial lamb uses single s.9ZA amendment (looks like honest correction, not pattern).",
    ),
    RiskFactor(
        name="Random selection",
        description="HMRC selects ~7% of enquiries randomly regardless of risk profile",
        weight="low",
        detection_method="Random number generator within Connect. No specific trigger.",
        threshold="N/A — random. Construction and cash businesses may have higher random selection weighting.",
        countermeasure="Books must be clean enough to survive random enquiry. Inspector AI simulates this exact scenario.",
    ),
    RiskFactor(
        name="Tip-offs and informants",
        description="HMRC receives anonymous tip-offs from public, ex-partners, competitors, disgruntled employees",
        weight="medium",
        detection_method="HMRC hotline, online reporting form, letters. Tax fraud reporting service.",
        threshold="Any specific allegation with enough detail to investigate.",
        countermeasure="Cannot prevent tip-offs. Defence is clean books that survive scrutiny. Sacrificial lamb demonstrates good faith.",
    ),
    RiskFactor(
        name="Social media lifestyle flags",
        description="AI-detected lifestyle inconsistency from public social media posts",
        weight="medium",
        detection_method="AI scraping of public Facebook, Instagram, TikTok. Image recognition for luxury goods, holidays, vehicles, property.",
        threshold="Visible lifestyle significantly exceeding declared after-tax income. Luxury purchases not explainable from declared income.",
        countermeasure="Social media privacy settings. No public posts showing undeclared lifestyle. This is outside HNC system scope — manual advice to client.",
    ),
]


# ===== HMRC INVESTIGATION ESCALATION LADDER =====

@dataclass
class InvestigationStage:
    """A stage in the HMRC investigation process."""
    stage: int
    name: str
    code: str               # COP reference or internal
    description: str
    trigger: str
    duration: str
    powers: str
    outcome: str
    threat_level: str
    countermeasure: str


INVESTIGATION_LADDER: List[InvestigationStage] = [
    InvestigationStage(
        stage=1,
        name="Compliance check letter",
        code="One-to-many letter / nudge",
        description="Automated letter asking taxpayer to check their return. Not an enquiry — no formal powers. Based on Connect risk flag.",
        trigger="Low-confidence Connect flag. Sector campaign. Third-party data mismatch below enquiry threshold.",
        duration="30 days to respond",
        powers="None — voluntary. But failure to respond increases risk score.",
        outcome="Either resolved (no action) or escalated to aspect enquiry.",
        threat_level="low",
        countermeasure="Respond promptly with accurate information. Sacrificial lamb amendment pre-empts this.",
    ),
    InvestigationStage(
        stage=2,
        name="Aspect enquiry",
        code="TMA 1970 s.9A (aspect)",
        description="Formal enquiry into ONE specific aspect of the return. Most common type — 70%+ of all enquiries.",
        trigger="Specific Connect flag: VAT mismatch, expense ratio outlier, CIS discrepancy, missing crypto declaration.",
        duration="6-12 months typically",
        powers="TMA s.19A information notices — can request documents related to the specific aspect only.",
        outcome="Closure notice with amendment (if tax due) + penalty (if careless/deliberate). Or no amendment if clean.",
        threat_level="medium",
        countermeasure="Inspector AI pre-checks every aspect. Books clean for specific queries. Documentation ready.",
    ),
    InvestigationStage(
        stage=3,
        name="Full enquiry",
        code="TMA 1970 s.9A (full)",
        description="Formal enquiry into ENTIRE return. All aspects open. Rare — less than 30% of enquiries.",
        trigger="Multiple Connect flags. High risk score (60+/100). Previous aspect enquiry found wider issues. Tip-off.",
        duration="12-18 months",
        powers="Full s.19A powers. Can request ALL records. Bank statements. Third-party notices to banks/suppliers.",
        outcome="Full amended assessment. Penalties. Possible referral to Fraud Investigation Service.",
        threat_level="high",
        countermeasure="Connect Four audit in inspector passes all four data sources. Harmonic link remediates cross-reference issues.",
    ),
    InvestigationStage(
        stage=4,
        name="COP8 — Civil investigation (non-fraud)",
        code="COP8",
        description="HMRC suspects significant tax loss through avoidance or complex arrangements. Not fraud — but serious. Specialist Investigations team.",
        trigger="Complex avoidance scheme detected. Offshore structures. Significant tax loss (£50,000+). COP8 letter issued.",
        duration="12-24 months",
        powers="Extended s.19A powers. Third-party notices. Offshore information requests via CRS/treaties.",
        outcome="Negotiated settlement. Back-tax + interest + penalties (typically 0-30% careless band).",
        threat_level="high",
        countermeasure="Avoid triggers: no complex avoidance, no offshore structures. Simple sole trader with clean books doesn't attract COP8.",
    ),
    InvestigationStage(
        stage=5,
        name="COP9 — Contractual Disclosure Facility (fraud suspected)",
        code="COP9",
        description="HMRC suspects FRAUD. Offers contract: full disclosure in exchange for no criminal prosecution. The Contractual Disclosure Facility.",
        trigger="Evidence of deliberate understatement/concealment. Informant evidence. Pattern of fraud across multiple years.",
        duration="60 days to accept CDF. Then 6-12 months for full disclosure.",
        powers="Full investigation powers. Can refer to Crown Prosecution Service if CDF refused or breached.",
        outcome="Full back-tax + interest + penalties (20-100%). OR criminal prosecution if CDF refused.",
        threat_level="critical",
        countermeasure="NEVER reach this stage. Everything before COP9 must work. If COP9 received, immediate professional legal advice required.",
    ),
    InvestigationStage(
        stage=6,
        name="Criminal investigation",
        code="HMRC Fraud Investigation Service (FIS)",
        description="Criminal prosecution under Fraud Act 2006 or POCA 2002. HMRC pursues only ~500-600 criminal cases per year.",
        trigger="CDF refused. Evidence of organised fraud. Revenue loss > £100,000. Political/public interest. Aggravating factors.",
        duration="12-36 months to trial",
        powers="Criminal investigation powers. PACE interviews. Search warrants. Asset freezing (POCA).",
        outcome="Criminal conviction. Prison sentence (up to 10 years fraud, 14 years POCA). Confiscation order. Lifetime criminal record.",
        threat_level="critical",
        countermeasure="The entire HNC system exists to ensure this NEVER happens. Reasonable care throughout. Voluntary disclosure of small errors (sacrificial lamb). No deliberate concealment.",
    ),
]


# ===== CONNECT SYSTEM STATISTICS =====

CONNECT_STATS = {
    "developer": "BAE Systems Applied Intelligence",
    "initial_cost": 45_000_000,  # £45m initial development
    "estimated_current_cost": 100_000_000,  # £80-100m with ongoing development
    "data_lines": 22_000_000_000,  # 22 billion lines of data
    "data_items_cross_matched": 1_000_000_000,  # 1 billion cross-matched items
    "taxpayers_flagged_annually": 500_000,  # 500,000 taxpayers flagged per year
    "revenue_generated_2024_25": 4_600_000_000,  # £4.6 billion additional revenue
    "investigations_connect_triggered_pct": 0.90,  # 90%+ of investigations triggered by Connect
    "random_selection_pct": 0.07,  # ~7% of enquiries are random
    "databases_available": 30,  # 30+ databases in Connect
    "operated_by": "Risk and Intelligence Service (RIS)",
    "source": "Capgemini case study, Wikipedia, HMRC FOI responses, professional press",
}


# ========================================================================
# 9. VERIFICATION ENGINE — Self-check for HNC engines
# ========================================================================

class LegalVerifier:
    """
    Verification engine that any HNC module can use to check its own
    compliance against the legal dataset.

    Usage:
        verifier = LegalVerifier("2025/26")
        result = verifier.check_expense(amount, category, turnover)
        result = verifier.check_penalty_exposure(tax_at_risk, behaviour)
        result = verifier.check_vat_status(turnover_12m)
    """

    def __init__(self, tax_year: str = "2025/26"):
        if tax_year not in TAX_YEARS:
            raise ValueError(f"Tax year {tax_year} not in dataset. Available: {list(TAX_YEARS.keys())}")
        self.tax_year = tax_year
        self.data = TAX_YEARS[tax_year]

    # ---- Income tax checks ----

    def calculate_income_tax(self, taxable_profit: float) -> Dict:
        """Calculate income tax on trading profit (sole trader)."""
        d = self.data
        tax = 0.0
        breakdown = []

        # Personal allowance (taper if over £100k)
        pa = d.personal_allowance
        if taxable_profit > d.pa_taper_threshold:
            excess = taxable_profit - d.pa_taper_threshold
            pa_reduction = min(pa, excess / 2)
            pa = pa - pa_reduction
            breakdown.append({
                "item": "Personal allowance taper",
                "statute": "ITA 2007 s.35",
                "detail": f"PA reduced from £{d.personal_allowance:,.0f} to £{pa:,.0f} (income over £{d.pa_taper_threshold:,.0f})",
            })

        taxable = max(0, taxable_profit - pa)

        # Basic rate
        basic_taxable = min(taxable, d.basic_rate_band[1] - d.personal_allowance)
        basic_tax = basic_taxable * d.basic_rate
        if basic_tax > 0:
            tax += basic_tax
            breakdown.append({
                "item": f"Basic rate ({d.basic_rate*100:.0f}%)",
                "statute": "ITA 2007 s.6",
                "on": basic_taxable,
                "tax": basic_tax,
            })

        # Higher rate
        if taxable > (d.basic_rate_band[1] - d.personal_allowance):
            higher_taxable = min(
                taxable - (d.basic_rate_band[1] - d.personal_allowance),
                d.additional_rate_threshold - d.basic_rate_band[1]
            )
            higher_tax = higher_taxable * d.higher_rate
            tax += higher_tax
            breakdown.append({
                "item": f"Higher rate ({d.higher_rate*100:.0f}%)",
                "statute": "ITA 2007 s.6",
                "on": higher_taxable,
                "tax": higher_tax,
            })

        # Additional rate
        if taxable > (d.additional_rate_threshold - pa):
            additional_taxable = taxable - (d.additional_rate_threshold - pa)
            additional_tax = additional_taxable * d.additional_rate
            tax += additional_tax
            breakdown.append({
                "item": f"Additional rate ({d.additional_rate*100:.0f}%)",
                "statute": "ITA 2007 s.6",
                "on": additional_taxable,
                "tax": additional_tax,
            })

        return {
            "taxable_profit": taxable_profit,
            "personal_allowance": pa,
            "taxable_income": taxable,
            "income_tax": round(tax, 2),
            "breakdown": breakdown,
            "statute": "ITA 2007 s.23",
        }

    def calculate_ni(self, taxable_profit: float) -> Dict:
        """Calculate Class 2 and Class 4 NI for self-employed."""
        d = self.data
        result = {"class2": 0.0, "class4": 0.0, "total": 0.0, "breakdown": []}

        # Class 2
        if taxable_profit > d.class2_small_profits_threshold:
            class2 = d.class2_weekly_rate * 52
            result["class2"] = round(class2, 2)
            result["breakdown"].append({
                "item": f"Class 2 NI (£{d.class2_weekly_rate}/week x 52)",
                "statute": "SSCBA 1992 s.11",
                "amount": round(class2, 2),
            })

        # Class 4
        if taxable_profit > d.class4_lower_profits_limit:
            main_band = min(taxable_profit, d.class4_upper_profits_limit) - d.class4_lower_profits_limit
            class4_main = main_band * d.class4_main_rate
            result["class4"] += class4_main
            result["breakdown"].append({
                "item": f"Class 4 NI main rate ({d.class4_main_rate*100:.0f}%)",
                "statute": "SSCBA 1992 s.15",
                "on": round(main_band, 2),
                "amount": round(class4_main, 2),
            })

            if taxable_profit > d.class4_upper_profits_limit:
                additional_band = taxable_profit - d.class4_upper_profits_limit
                class4_add = additional_band * d.class4_additional_rate
                result["class4"] += class4_add
                result["breakdown"].append({
                    "item": f"Class 4 NI additional ({d.class4_additional_rate*100:.0f}%)",
                    "statute": "SSCBA 1992 s.15",
                    "on": round(additional_band, 2),
                    "amount": round(class4_add, 2),
                })

        result["class4"] = round(result["class4"], 2)
        result["total"] = round(result["class2"] + result["class4"], 2)
        return result

    def calculate_cgt(self, gains: float, income: float = 0.0) -> Dict:
        """Calculate CGT on crypto/other gains."""
        d = self.data
        net_gain = gains - d.cgt_annual_exemption
        if net_gain <= 0:
            return {
                "gross_gains": gains,
                "annual_exemption": d.cgt_annual_exemption,
                "taxable_gain": 0.0,
                "cgt": 0.0,
                "note": "Within annual exemption — no CGT due",
                "statute": "TCGA 1992 s.3",
                "must_report": gains > d.cgt_reporting_threshold or (gains > 4 * d.cgt_annual_exemption),
            }

        # Determine rate based on income
        remaining_basic = max(0, d.basic_rate_band[1] - income)
        basic_gain = min(net_gain, remaining_basic)
        higher_gain = max(0, net_gain - remaining_basic)

        cgt = basic_gain * d.cgt_basic_rate + higher_gain * d.cgt_higher_rate

        return {
            "gross_gains": gains,
            "annual_exemption": d.cgt_annual_exemption,
            "taxable_gain": round(net_gain, 2),
            "basic_rate_portion": round(basic_gain, 2),
            "higher_rate_portion": round(higher_gain, 2),
            "cgt": round(cgt, 2),
            "statute": "TCGA 1992 s.1; ITA 2007 s.4",
            "must_report": True,
        }

    # ---- Expense verification ----

    def check_expense_ratio(self, category: str, amount: float,
                            turnover: float, sector: str = "construction_sole_trader") -> Dict:
        """Check if an expense ratio is within HMRC sector benchmarks."""
        if sector not in SECTOR_BENCHMARKS:
            return {"status": "UNKNOWN", "reason": f"No benchmark data for sector: {sector}"}

        benchmarks = SECTOR_BENCHMARKS[sector]
        ratio = amount / turnover if turnover > 0 else 0
        key = f"{category}_to_turnover"

        if key not in benchmarks:
            return {
                "status": "NO_BENCHMARK",
                "ratio": round(ratio, 4),
                "reason": f"No specific benchmark for '{category}' in {sector}",
            }

        low, high = benchmarks[key]
        if ratio < low:
            status = "BELOW_NORM"
            risk = "LOW"
            note = f"Below sector norm ({low*100:.0f}-{high*100:.0f}%). Not a problem unless suspiciously low."
        elif ratio <= high:
            status = "WITHIN_NORM"
            risk = "NONE"
            note = f"Within sector norm ({low*100:.0f}-{high*100:.0f}%). Clean."
        else:
            status = "ABOVE_NORM"
            risk = "MEDIUM" if ratio <= high * 1.5 else "HIGH"
            note = f"Above sector norm ({low*100:.0f}-{high*100:.0f}%). HMRC may query."

        return {
            "status": status,
            "risk": risk,
            "ratio": round(ratio, 4),
            "ratio_pct": f"{ratio*100:.1f}%",
            "benchmark_range": f"{low*100:.0f}-{high*100:.0f}%",
            "note": note,
        }

    def check_wholly_exclusively(self, description: str, has_personal_element: bool,
                                  apportioned: bool = False) -> Dict:
        """Check if expense passes the wholly and exclusively test."""
        result = {
            "statute": "ITTOIA 2005 s.34",
            "guidance": "BIM37000",
            "case_law": "Mallalieu v Drummond [1983]",
        }

        if not has_personal_element:
            result["status"] = "PASSES"
            result["note"] = "No personal element identified. Expense passes s.34 test."
        elif apportioned:
            result["status"] = "PASSES_APPORTIONED"
            result["note"] = "Dual-purpose but identifiable business portion apportioned. Acceptable per BIM37000."
        else:
            result["status"] = "FAILS"
            result["note"] = "Dual-purpose expenditure without apportionment. Fails wholly and exclusively test."
            result["action"] = "Apportion identifiable business element or disallow entirely."

        return result

    # ---- VAT checks ----

    def check_vat_status(self, turnover_12m: float) -> Dict:
        """Check VAT registration status based on rolling 12-month turnover."""
        d = self.data
        if turnover_12m > d.vat_registration_threshold:
            return {
                "status": "MUST_REGISTER",
                "turnover": turnover_12m,
                "threshold": d.vat_registration_threshold,
                "statute": "VATA 1994 Sch 1",
                "action": "Register within 30 days of exceeding threshold. Registration effective from first day of second month after threshold exceeded.",
            }
        elif turnover_12m > d.vat_registration_threshold * 0.90:
            return {
                "status": "APPROACHING",
                "turnover": turnover_12m,
                "threshold": d.vat_registration_threshold,
                "headroom": d.vat_registration_threshold - turnover_12m,
                "statute": "VATA 1994 Sch 1",
                "action": f"Within 10% of threshold. Monitor monthly. £{d.vat_registration_threshold - turnover_12m:,.0f} headroom.",
            }
        elif turnover_12m < d.vat_deregistration_threshold:
            return {
                "status": "CAN_DEREGISTER",
                "turnover": turnover_12m,
                "threshold": d.vat_deregistration_threshold,
                "statute": "VATA 1994 Sch 1 para 4",
                "action": "Turnover below deregistration threshold. Consider deregistering if VAT is net cost.",
            }
        else:
            return {
                "status": "REGISTERED_NORMAL",
                "turnover": turnover_12m,
                "threshold": d.vat_registration_threshold,
                "headroom": d.vat_registration_threshold - turnover_12m,
            }

    # ---- Penalty exposure ----

    def calculate_penalty_exposure(self, tax_at_risk: float,
                                    behaviour: str = "careless",
                                    disclosure: str = "unprompted") -> Dict:
        """Calculate penalty exposure for a given tax at risk."""
        if behaviour not in PENALTY_INACCURACY:
            return {"error": f"Unknown behaviour: {behaviour}"}

        band = PENALTY_INACCURACY[behaviour]

        if disclosure == "unprompted":
            min_pct = band.minimum_unprompted
            max_pct = band.maximum_unprompted
        else:
            min_pct = band.minimum_prompted
            max_pct = band.maximum_prompted

        return {
            "tax_at_risk": tax_at_risk,
            "behaviour": behaviour,
            "disclosure": disclosure,
            "penalty_range": (round(tax_at_risk * min_pct, 2), round(tax_at_risk * max_pct, 2)),
            "penalty_pct_range": (f"{min_pct*100:.0f}%", f"{max_pct*100:.0f}%"),
            "statute": band.statute,
            "notes": band.notes,
            "interest_1yr": round(tax_at_risk * HMRC_INTEREST_RATES["late_payment"], 2),
            "total_max_exposure": round(tax_at_risk + tax_at_risk * max_pct + tax_at_risk * HMRC_INTEREST_RATES["late_payment"], 2),
        }

    def check_enquiry_window(self, filing_date: date, behaviour: str = "any") -> Dict:
        """Check if HMRC can still open an enquiry."""
        today = date.today()
        results = []

        for window in ENQUIRY_WINDOWS:
            if behaviour != "any" and window.behaviour != "any" and window.behaviour != behaviour:
                continue

            if window.name == "s.9A enquiry":
                # 12 months from filing date
                deadline = date(filing_date.year + 1, filing_date.month, filing_date.day)
            else:
                # Years from end of tax year
                # Approximate: tax year ends 5 April
                tax_year_end = date(filing_date.year, 4, 5)
                deadline = date(tax_year_end.year + window.years, tax_year_end.month, tax_year_end.day)

            still_open = today < deadline
            results.append({
                "window": window.name,
                "years": window.years,
                "deadline": deadline.isoformat(),
                "open": still_open,
                "statute": window.statute,
                "description": window.description,
            })

        return {"filing_date": filing_date.isoformat(), "windows": results}

    # ---- Record keeping ----

    def check_record_retention(self, tax_year: str) -> Dict:
        """When can records for a tax year be destroyed?"""
        # Parse tax year e.g. "2025/26" → ends 5 April 2026
        start_year = int(tax_year.split("/")[0])
        tax_year_end = date(start_year + 1, 4, 5)
        filing_deadline = date(start_year + 2, 1, 31)
        retention_end = date(filing_deadline.year + self.data.record_retention_years,
                            filing_deadline.month, filing_deadline.day)

        return {
            "tax_year": tax_year,
            "tax_year_end": tax_year_end.isoformat(),
            "filing_deadline": filing_deadline.isoformat(),
            "retain_until": retention_end.isoformat(),
            "statute": "TMA 1970 s.12B",
            "penalty_for_failure": "Up to £3,000",
        }

    # ---- Statute lookup ----

    def get_statute(self, key: str) -> Optional[StatuteRef]:
        """Look up a statute by key."""
        return STATUTES.get(key)

    def get_manual(self, key: str) -> Optional[HMRCManualRef]:
        """Look up HMRC manual guidance by key."""
        return HMRC_MANUALS.get(key)

    def find_statutes(self, category: str) -> List[StatuteRef]:
        """Find all statutes in a category."""
        return [s for s in STATUTES.values() if s.category == category]

    def find_case_law(self, category: str) -> List[CaseLawRef]:
        """Find relevant case law by category."""
        return [c for c in CASE_LAW if c.category == category]


# ========================================================================
# 10. SACRIFICIAL LAMB ENGINE
# ========================================================================

class SacrificialLamb:
    """
    Controlled disclosure engine. The strategy: let HMRC find something
    small so they stop looking for something big.

    FA 2007 Sch 24 + TMA 1970 s.9ZA: if a taxpayer voluntarily corrects
    a small error before HMRC asks, it demonstrates reasonable care and
    good faith. HMRC sees an honest taxpayer making a genuine correction.

    The lamb must be:
    1. Real — it must be a genuine correction, not fabricated
    2. Small — £200-500 tax impact, enough to log but not to escalate
    3. Careless — behaviour classification must be 'careless' at worst
    4. Correctable — within s.9ZA amendment window
    5. Isolated — must not connect to or suggest a pattern of errors
    6. Plausible — the type of mistake any small trader might make

    What it does NOT do:
    - It does NOT fabricate errors (that's fraud — POCA s.327)
    - It does NOT create fake transactions
    - It does NOT manufacture evidence
    - It simply IDENTIFIES which real findings to leave unfixed
      and CORRECTS them via proper amendment channels
    """

    def __init__(self, verifier: LegalVerifier):
        self.verifier = verifier
        self.data = verifier.data

    def select_lambs(self, findings: List[Dict],
                      max_tax_cost: float = 500.0,
                      min_tax_cost: float = 100.0,
                      max_lambs: int = 2) -> Dict:
        """
        From a set of inspector findings, select the optimal sacrificial
        lambs — small, careless, correctable errors to leave visible.

        Args:
            findings: List of finding dicts from inspector
            max_tax_cost: Maximum tax impact of each lamb (£)
            min_tax_cost: Minimum tax impact to be worth flagging (£)
            max_lambs: Maximum number of lambs to select

        Returns:
            Dict with selected lambs, remediation plan, and analysis
        """
        candidates = []

        # Score each finding for lamb suitability
        for f in findings:
            score = self._score_candidate(f, max_tax_cost, min_tax_cost)
            if score["eligible"]:
                candidates.append({**f, **score})

        # Sort by suitability (higher = better lamb)
        candidates.sort(key=lambda c: c["suitability_score"], reverse=True)

        # Select top candidates
        selected = candidates[:max_lambs]

        # Calculate total tax cost
        total_tax_cost = sum(l.get("tax_impact", 0) for l in selected)

        # Build disclosure plan
        disclosure_plan = self._build_disclosure_plan(selected)

        # Everything NOT selected gets full remediation
        remediate = [f for f in findings
                     if f.get("finding", "") not in [s.get("finding", "") for s in selected]]

        return {
            "selected_lambs": selected,
            "total_tax_cost": round(total_tax_cost, 2),
            "penalty_exposure": self._calculate_lamb_penalty(total_tax_cost),
            "disclosure_plan": disclosure_plan,
            "findings_to_remediate": len(remediate),
            "findings_to_concede": len(selected),
            "strategy": self._describe_strategy(selected),
            "legal_basis": {
                "amendment": "TMA 1970 s.9ZA — voluntary amendment within 12 months",
                "penalty": "FA 2007 Sch 24 — careless + unprompted = 0% minimum penalty",
                "case_law": "Perrin v HMRC [2018] — reasonable care is objective standard",
                "guidance": "CH82400 — unprompted disclosure; CH83000 — quality of disclosure",
            },
        }

    def _score_candidate(self, finding: Dict,
                          max_tax: float, min_tax: float) -> Dict:
        """Score a finding for suitability as a sacrificial lamb."""
        score = 0.0
        reasons = []
        disqualifiers = []

        severity = finding.get("severity", "")
        tax_impact = finding.get("tax_impact", 0)
        category = finding.get("category", "")
        finding_text = finding.get("finding", "").lower()

        # ---- DISQUALIFIERS — never sacrifice these ----

        # Critical severity = too dangerous
        if severity == "CRITICAL":
            disqualifiers.append("Critical severity — would trigger deep investigation")
            return {"eligible": False, "disqualifiers": disqualifiers, "suitability_score": 0}

        # Anything criminal
        if any(word in finding_text for word in ["poca", "money laundering", "criminal", "fraud"]):
            disqualifiers.append("Criminal/POCA finding — cannot be a lamb")
            return {"eligible": False, "disqualifiers": disqualifiers, "suitability_score": 0}

        # Anything that connects to the wider architecture
        if any(word in finding_text for word in ["pattern", "systematic", "multiple years", "concealed"]):
            disqualifiers.append("Suggests pattern/systematic behaviour — would invite deeper enquiry")
            return {"eligible": False, "disqualifiers": disqualifiers, "suitability_score": 0}

        # Tax impact outside range
        if tax_impact > max_tax:
            disqualifiers.append(f"Tax impact £{tax_impact:,.0f} exceeds maximum £{max_tax:,.0f}")
            return {"eligible": False, "disqualifiers": disqualifiers, "suitability_score": 0}

        if tax_impact > 0 and tax_impact < min_tax:
            disqualifiers.append(f"Tax impact £{tax_impact:,.0f} below minimum £{min_tax:,.0f} — not worth flagging")
            return {"eligible": False, "disqualifiers": disqualifiers, "suitability_score": 0}

        # ---- SCORING — higher = better lamb ----

        # LOW severity = best
        if severity == "LOW":
            score += 30
            reasons.append("Low severity — minimal risk")
        elif severity == "MEDIUM":
            score += 15
            reasons.append("Medium severity — acceptable risk")
        elif severity == "HIGH":
            score += 5
            reasons.append("High severity — risky but possible if isolated")

        # Tax impact sweet spot: £200-400
        if 200 <= tax_impact <= 400:
            score += 25
            reasons.append(f"Tax impact £{tax_impact:,.0f} in sweet spot")
        elif 100 <= tax_impact < 200:
            score += 15
            reasons.append(f"Tax impact £{tax_impact:,.0f} — low end but workable")
        elif 400 < tax_impact <= 500:
            score += 10
            reasons.append(f"Tax impact £{tax_impact:,.0f} — upper end")

        # Category suitability
        common_mistakes = ["expenses", "vat", "timing"]
        if category in common_mistakes:
            score += 20
            reasons.append(f"Category '{category}' — common honest mistake for small traders")
        elif category == "income":
            score += 10
            reasons.append("Income finding — plausible if minor timing error")
        elif category in ["crypto", "bank"]:
            score += 5
            reasons.append(f"Category '{category}' — less common but not unusual")

        # Plausibility keywords — things HMRC would expect a small trader to get wrong
        plausible_errors = ["timing", "misclassif", "flat rate", "mileage",
                           "use of home", "small", "rounding", "period"]
        plausibility = sum(1 for kw in plausible_errors if kw in finding_text)
        score += plausibility * 5
        if plausibility > 0:
            reasons.append(f"Contains {plausibility} plausible-error keywords")

        # Isolation — finding should be standalone
        if "cross-reference" not in finding_text and "connect" not in finding_text:
            score += 10
            reasons.append("Isolated finding — doesn't connect to other issues")

        return {
            "eligible": True,
            "suitability_score": score,
            "reasons": reasons,
            "disqualifiers": [],
        }

    def _calculate_lamb_penalty(self, tax_cost: float) -> Dict:
        """Calculate penalty for the lamb — should be minimal or zero."""
        # Careless + unprompted disclosure = 0% minimum
        penalty = self.verifier.calculate_penalty_exposure(
            tax_at_risk=tax_cost,
            behaviour="careless",
            disclosure="unprompted",
        )
        return {
            "tax_conceded": tax_cost,
            "minimum_penalty": penalty["penalty_range"][0],
            "maximum_penalty": penalty["penalty_range"][1],
            "likely_outcome": "Suspended penalty or 0% — unprompted disclosure of careless error",
            "statute": "FA 2007 Sch 24 para 10",
            "total_worst_case": round(tax_cost + penalty["penalty_range"][1] + penalty["interest_1yr"], 2),
        }

    def _build_disclosure_plan(self, lambs: List[Dict]) -> List[Dict]:
        """Build a step-by-step disclosure plan for the lambs."""
        plan = []

        if not lambs:
            return [{"step": 1, "action": "No lambs selected — all findings remediated"}]

        plan.append({
            "step": 1,
            "action": "Prepare amended return",
            "detail": "File amended SA return under TMA 1970 s.9ZA within 12-month window",
            "statute": "TMA 1970 s.9ZA",
        })

        for i, lamb in enumerate(lambs):
            plan.append({
                "step": i + 2,
                "action": f"Correct: {lamb.get('finding', 'Unknown')[:60]}",
                "tax_impact": lamb.get("tax_impact", 0),
                "detail": "Include correction with brief explanation of the error",
            })

        plan.append({
            "step": len(lambs) + 2,
            "action": "Submit amendment with covering letter",
            "detail": "Letter states: 'During routine review of our records, we identified the following error(s) and wish to make a voluntary correction.' This establishes unprompted disclosure.",
            "statute": "CH82400 — unprompted disclosure",
        })

        plan.append({
            "step": len(lambs) + 3,
            "action": "Pay additional tax due",
            "detail": "Pay within 30 days of amendment to avoid late payment penalties",
            "statute": "FA 2009 Sch 56",
        })

        plan.append({
            "step": len(lambs) + 4,
            "action": "Retain full documentation",
            "detail": "Keep all working papers showing the error and correction process. This is your 'reasonable care' evidence.",
            "statute": "TMA 1970 s.12B; Perrin v HMRC [2018]",
        })

        return plan

    def _describe_strategy(self, lambs: List[Dict]) -> str:
        """Human-readable strategy description."""
        if not lambs:
            return "CLEAN SLATE — No suitable lambs found. All findings remediated."

        tax_total = sum(l.get("tax_impact", 0) for l in lambs)
        lamb_types = ", ".join(l.get("category", "unknown") for l in lambs)

        return (
            f"CONTROLLED DISCLOSURE — Voluntarily correct {len(lambs)} small finding(s) "
            f"({lamb_types}) totalling ~£{tax_total:,.0f} tax. Filed as s.9ZA amendment "
            f"with covering letter establishing unprompted disclosure. Expected outcome: "
            f"0% penalty (careless + unprompted), HMRC logs correction and moves on. "
            f"All remaining findings fully remediated before HMRC could discover them."
        )

    def print_lamb_report(self, result: Dict) -> str:
        """Human-readable sacrificial lamb report."""
        lines = [
            "=" * 70,
            "  SACRIFICIAL LAMB — Controlled Disclosure Report",
            "=" * 70,
            "",
            f"  Strategy:           {result['strategy'][:65]}",
            f"  Findings conceded:  {result['findings_to_concede']}",
            f"  Findings remediated: {result['findings_to_remediate']}",
            f"  Tax cost:           £{result['total_tax_cost']:,.2f}",
            "",
        ]

        pe = result["penalty_exposure"]
        lines.append(f"  Penalty range:      £{pe['minimum_penalty']:,.2f} — £{pe['maximum_penalty']:,.2f}")
        lines.append(f"  Likely outcome:     {pe['likely_outcome']}")
        lines.append(f"  Worst case total:   £{pe['total_worst_case']:,.2f}")
        lines.append("")

        if result["selected_lambs"]:
            lines.append("  --- SELECTED LAMBS ---")
            for i, lamb in enumerate(result["selected_lambs"], 1):
                lines.append(f"  {i}. {lamb.get('finding', 'Unknown')[:60]}")
                lines.append(f"     Severity:    {lamb.get('severity', 'N/A')}")
                lines.append(f"     Tax impact:  £{lamb.get('tax_impact', 0):,.2f}")
                lines.append(f"     Suitability: {lamb.get('suitability_score', 0)}/100")
                lines.append(f"     Reasons:     {'; '.join(lamb.get('reasons', []))}")
                lines.append("")

        lines.append("  --- DISCLOSURE PLAN ---")
        for step in result["disclosure_plan"]:
            statute = f" [{step.get('statute', '')}]" if step.get("statute") else ""
            lines.append(f"  Step {step['step']}: {step['action']}{statute}")
            if step.get("detail"):
                lines.append(f"           {step['detail'][:65]}")
            lines.append("")

        lines.append("  --- LEGAL BASIS ---")
        for key, val in result["legal_basis"].items():
            lines.append(f"  {key}: {val}")

        lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)


# ========================================================================
# TEST / DEMO
# ========================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("HNC LEGAL SUITE — The Law Library")
    print("Every rule, every rate, every statute. Verified.")
    print("=" * 70)

    verifier = LegalVerifier("2025/26")

    # ---- Income Tax Calculation ----
    print("\n--- INCOME TAX: John's construction profits £45,000 ---")
    it = verifier.calculate_income_tax(45000.0)
    print(f"  Taxable profit: £{it['taxable_profit']:,.2f}")
    print(f"  Personal allowance: £{it['personal_allowance']:,.2f}")
    print(f"  Taxable income: £{it['taxable_income']:,.2f}")
    print(f"  Income tax: £{it['income_tax']:,.2f}")
    for b in it["breakdown"]:
        if "tax" in b:
            print(f"    {b['item']}: £{b['on']:,.2f} → £{b['tax']:,.2f} [{b['statute']}]")

    # ---- NI Calculation ----
    print("\n--- NATIONAL INSURANCE: profits £45,000 ---")
    ni = verifier.calculate_ni(45000.0)
    print(f"  Class 2: £{ni['class2']:,.2f}")
    print(f"  Class 4: £{ni['class4']:,.2f}")
    print(f"  Total NI: £{ni['total']:,.2f}")
    for b in ni["breakdown"]:
        print(f"    {b['item']}: £{b['amount']:,.2f} [{b['statute']}]")

    # ---- CGT on crypto ----
    print("\n--- CGT: Crypto gains of £5,000 on income of £45,000 ---")
    cgt = verifier.calculate_cgt(5000.0, 45000.0)
    print(f"  Gross gains: £{cgt['gross_gains']:,.2f}")
    print(f"  Annual exemption: £{cgt['annual_exemption']:,.2f}")
    print(f"  Taxable gain: £{cgt['taxable_gain']:,.2f}")
    print(f"  CGT: £{cgt['cgt']:,.2f}")
    print(f"  Must report: {cgt['must_report']}")

    # ---- Expense ratio check ----
    print("\n--- EXPENSE CHECK: Materials £18,000 on turnover £60,000 ---")
    exp = verifier.check_expense_ratio("materials", 18000.0, 60000.0)
    print(f"  Status: {exp['status']}")
    print(f"  Ratio: {exp['ratio_pct']}")
    print(f"  Benchmark: {exp['benchmark_range']}")
    print(f"  Risk: {exp['risk']}")

    # ---- VAT status ----
    print("\n--- VAT: Rolling 12-month turnover £85,000 ---")
    vat = verifier.check_vat_status(85000.0)
    print(f"  Status: {vat['status']}")
    print(f"  Headroom: £{vat.get('headroom', 0):,.0f}")

    # ---- Penalty exposure ----
    print("\n--- PENALTY: £2,000 tax at risk, careless, unprompted ---")
    pen = verifier.calculate_penalty_exposure(2000.0, "careless", "unprompted")
    print(f"  Tax at risk: £{pen['tax_at_risk']:,.2f}")
    print(f"  Penalty range: {pen['penalty_pct_range'][0]} — {pen['penalty_pct_range'][1]}")
    print(f"  £: £{pen['penalty_range'][0]:,.2f} — £{pen['penalty_range'][1]:,.2f}")
    print(f"  Interest (1yr): £{pen['interest_1yr']:,.2f}")
    print(f"  Total max exposure: £{pen['total_max_exposure']:,.2f}")

    # ---- Statute lookup ----
    print("\n--- STATUTE LOOKUP ---")
    s = verifier.get_statute("TMA_s9ZA")
    if s:
        print(f"  {s.act} {s.section}: {s.description}")
        print(f"  URL: {s.url}")
        print(f"  Notes: {s.notes}")

    # ---- Record retention ----
    print("\n--- RECORD RETENTION: 2025/26 ---")
    rr = verifier.check_record_retention("2025/26")
    print(f"  Tax year: {rr['tax_year']}")
    print(f"  Retain until: {rr['retain_until']}")
    print(f"  Statute: {rr['statute']}")

    # ================================================================
    # SACRIFICIAL LAMB TEST
    # ================================================================
    print("\n\n" + "=" * 70)
    print("SACRIFICIAL LAMB — Controlled Disclosure Test")
    print("=" * 70)

    lamb = SacrificialLamb(verifier)

    # Simulate findings from the inspector
    test_findings = [
        {
            "finding": "Cash withdrawals (2,600) are 17.7% of declared turnover",
            "severity": "HIGH",
            "category": "bank",
            "tax_impact": 780.0,
        },
        {
            "finding": "1 crypto disposal with net gain of 23.89 not declared",
            "severity": "HIGH",
            "category": "crypto",
            "tax_impact": 0.0,  # Within annual exemption
        },
        {
            "finding": "Box 6 varies significantly from expected quarterly — timing mismatch",
            "severity": "MEDIUM",
            "category": "vat",
            "tax_impact": 0.0,
        },
        {
            "finding": "Transfers to 3 named individuals totalling 1,350",
            "severity": "MEDIUM",
            "category": "bank",
            "tax_impact": 405.0,
        },
        {
            "finding": "Flat rate scheme percentage may be incorrect for trade classification",
            "severity": "LOW",
            "category": "vat",
            "tax_impact": 280.0,
        },
        {
            "finding": "Mileage claim uses simplified rate but actual costs may be lower",
            "severity": "LOW",
            "category": "expenses",
            "tax_impact": 180.0,
        },
        {
            "finding": "Small timing misclassification — December invoice booked in January",
            "severity": "LOW",
            "category": "income",
            "tax_impact": 320.0,
        },
        {
            "finding": "Low turnover for construction sector",
            "severity": "LOW",
            "category": "income",
            "tax_impact": 0.0,
        },
    ]

    result = lamb.select_lambs(test_findings)
    print(lamb.print_lamb_report(result))

    # Summary
    print(f"\n  The system concedes £{result['total_tax_cost']:,.2f} in tax")
    print(f"  to protect {result['findings_to_remediate']} other findings from scrutiny")
    print(f"  Expected penalty: £{result['penalty_exposure']['minimum_penalty']:,.2f}")

    print("\n" + "=" * 70)
    print("Legal suite verified. The law library is open.")
    print("=" * 70)
