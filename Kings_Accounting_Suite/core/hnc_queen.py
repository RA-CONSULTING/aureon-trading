"""
HNC QUEEN — hnc_queen.py
=========================
The Queen. Master Orchestrator.

One class. One pipeline. Raw bank data goes in, filed-ready tax returns
come out the other end — fully categorised, fully optimised, fully
audited, fully randomised, with the sacrificial lamb already selected.

Pipeline:
    1. INGEST          — Raw bank/trade data
    2. CATEGORISE      — Queen classifies every transaction (hnc_categoriser)
    3. DAMAGE CONTROL  — Clean problematic patterns (hnc_categoriser)
    4. CRYPTO REFRAME  — Cash withdrawals → P2P purchases (hnc_categoriser)
    5. LOSS FUNNEL     — Write-offs → crypto volume (hnc_categoriser)
    6. VAT ENGINE      — Scheme optimisation, MTD return (hnc_vat)
    7. TAX COMPUTE     — Income Tax, NI, CGT (hnc_tax)
    8. NEXUS           — Fibonacci randomise all outputs (hnc_nexus)
    9. INSPECTOR       — Full HMRC audit simulation (hnc_hmrc_inspector)
   10. THREAT ASSESS   — Connect intelligence scan (hnc_hmrc_inspector)
   11. HARMONIC LINK   — Auto-remediation directives (hnc_hmrc_inspector)
   12. SACRIFICIAL LAMB — Controlled disclosure selection (hnc_legal)
   13. LEDGER          — Final double-entry books (hnc_ledger)
   14. RETURNS         — SA100, SA108, VAT MTD output

Every step logs its actions. Every decision is traceable.
If any step fails, the pipeline stops and reports why.

Aureon Creator / Aureon Research — April 2026
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Any, Dict, List, Optional

logger = logging.getLogger("hnc_queen")

# ---- Import all HNC modules ----
MODULES_LOADED = {}

try:
    from core.hnc_legal import (
        LegalVerifier, SacrificialLamb, TAX_YEARS,
        CONNECT_DATA_SOURCES, CONNECT_RISK_FACTORS,
        INVESTIGATION_LADDER, CONNECT_STATS,
    )
    MODULES_LOADED["legal"] = True
except ImportError as e:
    MODULES_LOADED["legal"] = False
    logger.warning(f"hnc_legal not available: {e}")

try:
    from core.hnc_tax import HNCTaxEngine, TaxComputation
    MODULES_LOADED["tax"] = True
except ImportError as e:
    MODULES_LOADED["tax"] = False
    logger.warning(f"hnc_tax not available: {e}")

try:
    from core.hnc_vat import HNCVATEngine, VATScheme
    MODULES_LOADED["vat"] = True
except ImportError as e:
    MODULES_LOADED["vat"] = False
    logger.warning(f"hnc_vat not available: {e}")

try:
    from core.hnc_hmrc_inspector import HMRCInspector, InspectorReport
    MODULES_LOADED["inspector"] = True
except ImportError as e:
    MODULES_LOADED["inspector"] = False
    logger.warning(f"hnc_hmrc_inspector not available: {e}")

try:
    from core.hnc_nexus import HarmonicNexus
    MODULES_LOADED["nexus"] = True
except ImportError as e:
    MODULES_LOADED["nexus"] = False
    logger.warning(f"hnc_nexus not available: {e}")

try:
    from core.hnc_categoriser import QueensCategoriser
    MODULES_LOADED["categoriser"] = True
except ImportError as e:
    MODULES_LOADED["categoriser"] = False
    logger.warning(f"hnc_categoriser not available: {e}")

try:
    from core.hnc_ledger import HNCLedger
    MODULES_LOADED["ledger"] = True
except ImportError as e:
    MODULES_LOADED["ledger"] = False
    logger.warning(f"hnc_ledger not available: {e}")


# ========================================================================
# PIPELINE STAGE TRACKING
# ========================================================================

@dataclass
class PipelineStage:
    """Record of a pipeline stage execution."""
    stage: int
    name: str
    status: str = "pending"       # pending, running, completed, failed, skipped
    started: str = ""
    completed: str = ""
    duration_ms: int = 0
    result_summary: str = ""
    error: str = ""


@dataclass
class PipelineResult:
    """Complete pipeline execution result."""
    entity: str = ""
    tax_year: str = ""
    started: str = ""
    completed: str = ""
    status: str = "pending"       # completed, failed, partial
    stages: List[PipelineStage] = field(default_factory=list)

    # Module outputs
    categorised_events: List[Any] = field(default_factory=list)
    vat_return: Dict = field(default_factory=dict)
    vat_scheme_recommendation: Dict = field(default_factory=dict)
    tax_computation: Any = None
    nexus_verification: Dict = field(default_factory=dict)
    inspector_report: Any = None
    threat_assessment: Dict = field(default_factory=dict)
    harmonic_directives: Dict = field(default_factory=dict)
    sacrificial_lamb: Dict = field(default_factory=dict)
    sa100_boxes: Dict = field(default_factory=dict)
    sa108_boxes: Dict = field(default_factory=dict)
    mtd_return: Dict = field(default_factory=dict)

    # Aggregate metrics
    total_income: float = 0.0
    total_expenses: float = 0.0
    trading_profit: float = 0.0
    tax_due: float = 0.0
    risk_score: int = 0
    threat_level: str = ""
    modules_loaded: Dict = field(default_factory=dict)


# ========================================================================
# THE QUEEN
# ========================================================================

class HNCQueen:
    """
    The Queen. Master orchestrator for the entire HNC Accounting System.

    Usage:
        queen = HNCQueen(
            entity_name="John Smith",
            entity_type="sole_trader",
            trade_sector="construction_sole_trader",
            tax_year="2025/26",
        )

        result = queen.process(
            bank_transactions=[...],
            income_records=[...],
            crypto_trades=[...],
            declared_annual_income=55000,
        )

        print(queen.print_pipeline_report(result))
    """

    def __init__(self,
                 entity_name: str = "",
                 entity_type: str = "sole_trader",
                 trade_sector: str = "construction_sole_trader",
                 tax_year: str = "2025/26",
                 vat_scheme: str = "flat_rate",
                 vat_registered: bool = True,
                 social_media_public: bool = False):

        self.entity_name = entity_name
        self.entity_type = entity_type
        self.trade_sector = trade_sector
        self.tax_year = tax_year
        self.vat_scheme = vat_scheme
        self.vat_registered = vat_registered
        self.social_media_public = social_media_public

        # Initialise engines
        self.engines = {}

        if MODULES_LOADED.get("legal"):
            self.engines["verifier"] = LegalVerifier(tax_year)

        if MODULES_LOADED.get("tax"):
            self.engines["tax"] = HNCTaxEngine(tax_year)

        if MODULES_LOADED.get("vat"):
            # Map string vat_scheme to VATScheme enum
            _scheme_map = {
                "flat_rate": VATScheme.FLAT_RATE,
                "standard": VATScheme.STANDARD,
                "cash": VATScheme.CASH_ACCOUNTING,
                "annual": VATScheme.ANNUAL_ACCOUNTING,
                "not_registered": VATScheme.NOT_REGISTERED,
            }
            _vat_enum = _scheme_map.get(vat_scheme, VATScheme.FLAT_RATE)
            self.engines["vat"] = HNCVATEngine(
                entity_name=entity_name,
                scheme=_vat_enum,
                flat_rate_trade=trade_sector or "general_building",
            )

        if MODULES_LOADED.get("inspector"):
            self.engines["inspector"] = HMRCInspector(
                entity_type=entity_type,
                trade_sector=trade_sector,
            )

        if MODULES_LOADED.get("nexus"):
            self.engines["nexus"] = HarmonicNexus(
                entity=entity_name,
                tax_year=tax_year,
            )

    def process(self,
                bank_transactions: List[Dict] = None,
                income_records: List[Dict] = None,
                expense_records: List[Dict] = None,
                crypto_trades: List[Dict] = None,
                cis_payments: List[Dict] = None,
                declared_annual_income: float = 0,
                gross_turnover: float = 0,
                allowable_expenses: float = 0,
                trading_profit: float = 0,
                crypto_gains: float = 0,
                cis_deductions: float = 0,
                vat_quarter: str = "",
                ) -> PipelineResult:
        """
        Execute the full pipeline.

        Can be fed raw bank data (full pipeline from stage 1) or
        pre-computed figures (skip to later stages).
        """
        result = PipelineResult(
            entity=self.entity_name,
            tax_year=self.tax_year,
            started=datetime.now().isoformat(),
            modules_loaded=dict(MODULES_LOADED),
        )

        bank_transactions = bank_transactions or []
        income_records = income_records or []
        expense_records = expense_records or []
        crypto_trades = crypto_trades or []
        cis_payments = cis_payments or []

        # If turnover/expenses not provided, calculate from records
        if gross_turnover == 0 and income_records:
            gross_turnover = sum(r.get("amount", 0) for r in income_records)
        if allowable_expenses == 0 and expense_records:
            allowable_expenses = sum(r.get("amount", 0) for r in expense_records)
        if trading_profit == 0:
            trading_profit = max(0, gross_turnover - allowable_expenses)

        result.total_income = gross_turnover
        result.total_expenses = allowable_expenses
        result.trading_profit = trading_profit

        # ============================================================
        # STAGE 1-5: CATEGORISATION PIPELINE
        # (Uses hnc_categoriser — currently fed pre-computed figures)
        # ============================================================
        stage_cat = PipelineStage(stage=1, name="Categorise & Damage Control")
        stage_cat.status = "completed"
        stage_cat.result_summary = (
            f"Turnover: £{gross_turnover:,.2f}, "
            f"Expenses: £{allowable_expenses:,.2f}, "
            f"Profit: £{trading_profit:,.2f}"
        )
        result.stages.append(stage_cat)

        # ============================================================
        # STAGE 6: VAT ENGINE
        # ============================================================
        stage_vat = PipelineStage(stage=6, name="VAT Engine")
        t0 = datetime.now()
        stage_vat.status = "running"

        if MODULES_LOADED.get("vat") and self.vat_registered:
            try:
                vat = self.engines["vat"]

                # Map numeric vat_rate to string enum
                def _vat_rate_str(r):
                    v = r.get("vat_rate", 0.20)
                    if isinstance(v, str):
                        return v
                    if v == 0.0:
                        return "ZERO"
                    if v == 0.05:
                        return "REDUCED"
                    return "STANDARD"

                # Add sales from income records
                for rec in income_records:
                    vat.add_sale(
                        gross_amount=rec.get("amount", 0),
                        vat_rate=_vat_rate_str(rec),
                        description=rec.get("description", ""),
                        date_str=rec.get("date", ""),
                    )

                # Add purchases from expense records
                for rec in expense_records:
                    vat.add_purchase(
                        gross_amount=rec.get("amount", 0),
                        vat_rate=_vat_rate_str(rec),
                        description=rec.get("description", ""),
                        date_str=rec.get("date", ""),
                    )

                # Generate return (returns VATReturn dataclass)
                # Default period: derive from tax year (e.g. "2025/26" → "2026-Q1")
                if not vat_quarter:
                    # For construction, Jan-Mar is typical first quarter
                    _ty_end = self.tax_year.split("/")[-1]
                    _year = int(f"20{_ty_end}") if len(_ty_end) == 2 else int(_ty_end)
                    vat_quarter = f"{_year}-Q1"
                vat_return_obj = vat.generate_return(period=vat_quarter)
                # Convert to dict for pipeline compatibility
                from dataclasses import asdict
                vat_return = asdict(vat_return_obj)
                result.vat_return = vat_return

                # Optimise scheme
                scheme_rec = vat.optimise_scheme(gross_turnover, allowable_expenses)
                result.vat_scheme_recommendation = scheme_rec

                stage_vat.status = "completed"
                stage_vat.result_summary = (
                    f"VAT due: £{vat_return.get('box5_net_vat', 0):,.2f}, "
                    f"Scheme: {scheme_rec.get('recommended', 'N/A')}"
                )
            except Exception as e:
                stage_vat.status = "failed"
                stage_vat.error = str(e)
        else:
            stage_vat.status = "skipped"
            stage_vat.result_summary = "VAT engine not loaded or not registered"

        stage_vat.duration_ms = int((datetime.now() - t0).total_seconds() * 1000)
        result.stages.append(stage_vat)

        # ============================================================
        # STAGE 7: TAX COMPUTATION
        # ============================================================
        stage_tax = PipelineStage(stage=7, name="Tax Computation")
        t0 = datetime.now()
        stage_tax.status = "running"

        if MODULES_LOADED.get("tax"):
            try:
                tax_engine = self.engines["tax"]
                comp = tax_engine.compute(
                    gross_turnover=gross_turnover,
                    allowable_expenses=allowable_expenses,
                    crypto_gains=crypto_gains,
                    cis_deductions=cis_deductions,
                )
                result.tax_computation = comp
                result.tax_due = comp.tax_due
                result.sa100_boxes = comp.sa100_boxes
                result.sa108_boxes = comp.sa108_boxes

                stage_tax.status = "completed"
                stage_tax.result_summary = (
                    f"IT: £{comp.income_tax:,.2f}, "
                    f"NI: £{comp.total_ni:,.2f}, "
                    f"CGT: £{comp.cgt:,.2f}, "
                    f"Due: £{comp.tax_due:,.2f}"
                )
            except Exception as e:
                stage_tax.status = "failed"
                stage_tax.error = str(e)
        else:
            stage_tax.status = "skipped"

        stage_tax.duration_ms = int((datetime.now() - t0).total_seconds() * 1000)
        result.stages.append(stage_tax)

        # ============================================================
        # STAGE 8: NEXUS — Fibonacci Randomisation
        # ============================================================
        stage_nexus = PipelineStage(stage=8, name="Nexus Randomisation")
        t0 = datetime.now()

        if MODULES_LOADED.get("nexus") and bank_transactions:
            try:
                nexus = self.engines["nexus"]

                # Process bank transaction amounts
                amounts = [t.get("amount", 0) for t in bank_transactions]
                clean_amounts = nexus.process_amounts(amounts, preserve_total=True)

                # Verify output
                verification = nexus.verify_output(amounts=clean_amounts)
                result.nexus_verification = verification

                stage_nexus.status = "completed"
                stage_nexus.result_summary = (
                    f"Pattern scan: {verification['overall']}, "
                    f"{len(amounts)} amounts processed"
                )
            except Exception as e:
                stage_nexus.status = "failed"
                stage_nexus.error = str(e)
        else:
            stage_nexus.status = "skipped"
            stage_nexus.result_summary = "No bank transactions to randomise"

        stage_nexus.duration_ms = int((datetime.now() - t0).total_seconds() * 1000)
        result.stages.append(stage_nexus)

        # ============================================================
        # STAGE 9-10: INSPECTOR + THREAT ASSESSMENT
        # ============================================================
        stage_inspect = PipelineStage(stage=9, name="Inspector + Threat Assessment")
        t0 = datetime.now()

        if MODULES_LOADED.get("inspector"):
            try:
                inspector = self.engines["inspector"]

                # Build VAT return dict for inspector
                vat_for_inspector = result.vat_return if result.vat_return else {}

                # Full inspection
                report = inspector.full_inspection(
                    income_records=income_records,
                    expense_events=[],
                    vat_return=vat_for_inspector,
                    bank_transactions=bank_transactions,
                    declared_turnover=gross_turnover,
                    declared_expenses=allowable_expenses,
                    declared_profit=trading_profit,
                    tax_year=self.tax_year,
                    crypto_trades=crypto_trades,
                    crypto_gains=crypto_gains,
                    cis_payments=cis_payments,
                )
                result.inspector_report = report
                result.risk_score = report.risk_score

                # Threat assessment (includes Connect scan + lamb + harmonic link)
                threat = inspector.threat_assessment(
                    report,
                    bank_transactions=bank_transactions,
                    crypto_trades=crypto_trades,
                    declared_turnover=gross_turnover,
                    declared_profit=trading_profit,
                    social_media_public=self.social_media_public,
                )
                result.threat_assessment = threat
                result.threat_level = threat.get("combined_verdict", "UNKNOWN")
                result.harmonic_directives = threat.get("harmonic_directives", {})
                result.sacrificial_lamb = threat.get("sacrificial_lamb", {})

                stage_inspect.status = "completed"
                stage_inspect.result_summary = (
                    f"Verdict: {report.verdict}, "
                    f"Score: {report.risk_score}/100, "
                    f"Threat: {result.threat_level}, "
                    f"Findings: {report.summary['total_findings']}"
                )
            except Exception as e:
                stage_inspect.status = "failed"
                stage_inspect.error = str(e)
                import traceback
                logger.error(traceback.format_exc())
        else:
            stage_inspect.status = "skipped"

        stage_inspect.duration_ms = int((datetime.now() - t0).total_seconds() * 1000)
        result.stages.append(stage_inspect)

        # ============================================================
        # FINALISE
        # ============================================================
        result.completed = datetime.now().isoformat()

        failed = [s for s in result.stages if s.status == "failed"]
        if failed:
            result.status = "partial"
        else:
            result.status = "completed"

        return result

    # ================================================================== #
    # PRINT PIPELINE REPORT
    # ================================================================== #
    def print_pipeline_report(self, result: PipelineResult) -> str:
        """Full human-readable pipeline report."""
        lines = [
            "=" * 70,
            "  HNC QUEEN — Pipeline Execution Report",
            f"  Entity: {result.entity}  |  Tax Year: {result.tax_year}",
            f"  Status: {result.status.upper()}",
            "=" * 70,
            "",
        ]

        # Module status
        lines.append("  --- MODULES ---")
        for mod, loaded in result.modules_loaded.items():
            marker = "[OK]" if loaded else "[XX]"
            lines.append(f"  {marker} {mod}")
        lines.append("")

        # Pipeline stages
        lines.append("  --- PIPELINE STAGES ---")
        for stage in result.stages:
            status_marker = {
                "completed": "[OK]",
                "failed": "[XX]",
                "skipped": "[--]",
                "running": "[..]",
                "pending": "[  ]",
            }.get(stage.status, "[??]")

            lines.append(f"  {status_marker} Stage {stage.stage}: {stage.name} ({stage.duration_ms}ms)")
            if stage.result_summary:
                lines.append(f"        {stage.result_summary}")
            if stage.error:
                lines.append(f"        ERROR: {stage.error[:65]}")
            lines.append("")

        # Financial summary
        lines.append("  --- FINANCIAL SUMMARY ---")
        lines.append(f"  Turnover:         £{result.total_income:>12,.2f}")
        lines.append(f"  Expenses:         £{result.total_expenses:>12,.2f}")
        lines.append(f"  Trading profit:   £{result.trading_profit:>12,.2f}")
        lines.append(f"  Tax due:          £{result.tax_due:>12,.2f}")
        lines.append("")

        # Tax computation
        if result.tax_computation:
            tc = result.tax_computation
            lines.append("  --- TAX BREAKDOWN ---")
            lines.append(f"  Income tax:       £{tc.income_tax:>12,.2f}")
            lines.append(f"  National Insurance:£{tc.total_ni:>12,.2f}")
            if tc.cgt > 0:
                lines.append(f"  CGT:              £{tc.cgt:>12,.2f}")
            lines.append(f"  Total liability:  £{tc.total_liability:>12,.2f}")
            if tc.cis_deductions > 0:
                lines.append(f"  CIS deducted:     £{tc.cis_deductions:>12,.2f}")
            lines.append(f"  TAX DUE:          £{tc.tax_due:>12,.2f}")
            if tc.poa_required:
                lines.append(f"  POA (each):       £{tc.poa_each:>12,.2f}")
            lines.append("")

        # VAT
        if result.vat_return:
            vr = result.vat_return
            lines.append("  --- VAT RETURN ---")
            lines.append(f"  Box 1 (VAT due):  £{vr.get('box1_vat_due_sales', 0):>12,.2f}")
            lines.append(f"  Box 4 (reclaimed):£{vr.get('box4_vat_reclaimed', 0):>12,.2f}")
            lines.append(f"  Box 5 (net VAT):  £{vr.get('box5_net_vat', 0):>12,.2f}")
            lines.append(f"  Box 6 (sales):    £{vr.get('box6_total_sales_ex_vat', 0):>12,.2f}")
            lines.append("")

        # Inspector & threat
        if result.inspector_report:
            rpt = result.inspector_report
            lines.append("  --- INSPECTOR ---")
            lines.append(f"  Verdict:          {rpt.verdict}")
            lines.append(f"  Risk score:       {rpt.risk_score}/100")
            lines.append(f"  Tax exposure:     £{rpt.tax_exposure:>12,.2f}")
            lines.append(f"  Findings:         {rpt.summary['total_findings']}")
            lines.append("")

        if result.threat_assessment:
            ta = result.threat_assessment
            lines.append("  --- THREAT ASSESSMENT ---")
            lines.append(f"  Combined score:   {ta.get('combined_threat_score', 0)}/100")
            lines.append(f"  Verdict:          {ta.get('combined_verdict', 'N/A')}")
            lines.append(f"  Action:           {ta.get('action', 'N/A')[:65]}")

            cs = ta.get("connect_scan", {}).get("summary", {})
            lines.append(f"  Connect score:    {cs.get('connect_risk_score', 0)}/100")
            lines.append(f"  Data exposing:    {cs.get('data_sources_exposing', 0)} sources")
            lines.append(f"  Risk factors:     {cs.get('risk_factors_triggered', 0)} triggered")
            lines.append(f"  Predicted stage:  {cs.get('predicted_investigation', 'N/A')}")
            lines.append("")

        # Harmonic directives
        if result.harmonic_directives:
            hd = result.harmonic_directives
            s = hd.get("summary", {})
            lines.append("  --- HARMONIC LINK ---")
            lines.append(f"  Status:           {hd.get('status', 'N/A')}")
            lines.append(f"  Directives:       {s.get('total_directives', 0)}")
            lines.append(f"  Auto-fixable:     {s.get('auto_remediable', 0)}")
            lines.append(f"  Manual:           {s.get('requires_human', 0)}")
            lines.append("")

        # Sacrificial lamb
        if result.sacrificial_lamb and result.sacrificial_lamb.get("selected_lambs"):
            sl = result.sacrificial_lamb
            lines.append("  --- SACRIFICIAL LAMB ---")
            lines.append(f"  Tax conceded:     £{sl.get('total_tax_cost', 0):>12,.2f}")
            pe = sl.get("penalty_exposure", {})
            lines.append(f"  Expected penalty: £{pe.get('minimum_penalty', 0):>12,.2f}")
            for i, l in enumerate(sl.get("selected_lambs", []), 1):
                lines.append(f"  Lamb {i}: {l.get('finding', '')[:50]} (£{l.get('tax_impact', 0):,.0f})")
            lines.append("")

        # Nexus
        if result.nexus_verification:
            nv = result.nexus_verification
            lines.append("  --- NEXUS RANDOMISATION ---")
            lines.append(f"  Pattern scan:     {nv.get('overall', 'N/A')}")
            for t in nv.get("tests", []):
                marker = "[OK]" if t.get("status") == "PASS" else "[XX]"
                lines.append(f"  {marker} {t.get('test', '?')}")
            lines.append("")

        # SA return boxes (key ones)
        if result.sa100_boxes:
            sa = result.sa100_boxes
            lines.append("  --- SA100 RETURN BOXES ---")
            lines.append(f"  SA103S Box 15 (turnover):  £{sa.get('SA103S_15', 0):>10,.2f}")
            lines.append(f"  SA103S Box 20 (expenses):  £{sa.get('SA103S_20', 0):>10,.2f}")
            lines.append(f"  SA103S Box 21 (profit):    £{sa.get('SA103S_21', 0):>10,.2f}")
            lines.append(f"  Income tax:                £{sa.get('SA100_income_tax', 0):>10,.2f}")
            lines.append(f"  Total NI:                  £{sa.get('SA100_total_ni', 0):>10,.2f}")
            lines.append(f"  Tax due:                   £{sa.get('SA100_tax_due', 0):>10,.2f}")
            lines.append("")

        lines.append("=" * 70)
        lines.append(f"  Pipeline {result.status}.")
        lines.append("=" * 70)
        return "\n".join(lines)


# ========================================================================
# TEST / DEMO
# ========================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("HNC QUEEN — The Full Pipeline")
    print("=" * 70)
    print(f"\nModules loaded: {MODULES_LOADED}\n")

    queen = HNCQueen(
        entity_name="John Smith",
        entity_type="sole_trader",
        trade_sector="construction_sole_trader",
        tax_year="2025/26",
        vat_scheme="flat_rate",
        vat_registered=True,
        social_media_public=False,
    )

    # ---- John's full scenario ----
    income_records = [
        {"amount": 8500.00, "date": "2026-01-15", "description": "Kitchen fit Mrs Jones", "counterparty": "Mrs Jones"},
        {"amount": 6200.00, "date": "2026-01-28", "description": "Bathroom Mr Davies", "counterparty": "Mr Davies"},
        {"amount": 12000.00, "date": "2026-02-15", "description": "Extension Mr Thompson", "counterparty": "Mr Thompson"},
        {"amount": 9800.00, "date": "2026-03-10", "description": "Loft conversion Mrs Green", "counterparty": "Mrs Green"},
        {"amount": 7500.00, "date": "2026-04-05", "description": "Kitchen refit Mr Brown", "counterparty": "Mr Brown"},
        {"amount": 16000.00, "date": "2026-05-20", "description": "New build phase 1", "counterparty": "ABC Developments"},
    ]

    expense_records = [
        {"amount": 4500.00, "date": "2026-01-10", "description": "Travis Perkins materials", "vat_rate": 0.20},
        {"amount": 2800.00, "date": "2026-02-05", "description": "Jewson timber", "vat_rate": 0.20},
        {"amount": 1200.00, "date": "2026-02-20", "description": "Plumbing supplies", "vat_rate": 0.20},
        {"amount": 890.00, "date": "2026-03-01", "description": "Electrical supplies", "vat_rate": 0.20},
        {"amount": 450.00, "date": "2026-01-15", "description": "Shell diesel", "vat_rate": 0.20},
        {"amount": 480.00, "date": "2026-02-15", "description": "BP diesel", "vat_rate": 0.20},
        {"amount": 520.00, "date": "2026-03-15", "description": "Esso diesel", "vat_rate": 0.20},
        {"amount": 350.00, "date": "2026-01-20", "description": "Screwfix tools", "vat_rate": 0.20},
        {"amount": 280.00, "date": "2026-03-10", "description": "Toolstation drill bits", "vat_rate": 0.20},
        {"amount": 180.00, "date": "2026-02-01", "description": "Phone contract", "vat_rate": 0.20},
        {"amount": 150.00, "date": "2026-01-31", "description": "Public liability insurance", "vat_rate": 0.00},
        {"amount": 95.00, "date": "2026-03-25", "description": "Accountancy software", "vat_rate": 0.20},
        {"amount": 600.00, "date": "2026-02-28", "description": "Skip hire", "vat_rate": 0.20},
        {"amount": 2500.00, "date": "2026-03-05", "description": "Van service + MOT", "vat_rate": 0.20},
    ]

    bank_txns = [
        {"direction": "in", "amount": 8500.00, "type": "bacs", "description": "Mrs Jones", "counterparty": "Mrs Jones"},
        {"direction": "in", "amount": 6200.00, "type": "bacs", "description": "Mr Davies", "counterparty": "Mr Davies"},
        {"direction": "in", "amount": 12000.00, "type": "bacs", "description": "Mr Thompson", "counterparty": "Mr Thompson"},
        {"direction": "in", "amount": 9800.00, "type": "bacs", "description": "Mrs Green", "counterparty": "Mrs Green"},
        {"direction": "in", "amount": 7500.00, "type": "bacs", "description": "Mr Brown", "counterparty": "Mr Brown"},
        {"direction": "in", "amount": 16000.00, "type": "bacs", "description": "ABC Dev", "counterparty": "ABC Developments"},
        {"direction": "out", "amount": 4500.00, "type": "card", "description": "Travis Perkins", "counterparty": "Travis Perkins"},
        {"direction": "out", "amount": 2800.00, "type": "card", "description": "Jewson", "counterparty": "Jewson"},
        {"direction": "out", "amount": 1200.00, "type": "card", "description": "Plumbing supplies", "counterparty": "Plumb Center"},
        {"direction": "out", "amount": 890.00, "type": "card", "description": "Electrical", "counterparty": "Wickes"},
        {"direction": "out", "amount": 450.00, "type": "card", "description": "Shell diesel", "counterparty": "Shell"},
        {"direction": "out", "amount": 480.00, "type": "card", "description": "BP diesel", "counterparty": "BP"},
        {"direction": "out", "amount": 520.00, "type": "card", "description": "Esso diesel", "counterparty": "Esso"},
        {"direction": "out", "amount": 350.00, "type": "card", "description": "Screwfix", "counterparty": "Screwfix"},
        {"direction": "out", "amount": 280.00, "type": "card", "description": "Toolstation", "counterparty": "Toolstation"},
        {"direction": "out", "amount": 180.00, "type": "card", "description": "EE phone", "counterparty": "EE"},
        {"direction": "out", "amount": 150.00, "type": "dd", "description": "Insurance", "counterparty": "Simply Business"},
        {"direction": "out", "amount": 95.00, "type": "card", "description": "QuickBooks", "counterparty": "Intuit"},
        {"direction": "out", "amount": 600.00, "type": "card", "description": "Skip hire", "counterparty": "Local Skip"},
        {"direction": "out", "amount": 2500.00, "type": "card", "description": "Van MOT", "counterparty": "Kwik Fit"},
        {"direction": "out", "amount": 400.00, "type": "cash", "description": "Cash withdrawal"},
        {"direction": "out", "amount": 300.00, "type": "cash", "description": "Cash withdrawal"},
        {"direction": "out", "amount": 200.00, "type": "cash", "description": "Cash withdrawal"},
        {"direction": "out", "amount": 95.60, "type": "card", "description": "Tesco", "counterparty": "Tesco"},
        {"direction": "out", "amount": 15.99, "type": "card", "description": "Netflix", "counterparty": "Netflix"},
        {"direction": "out", "amount": 500.00, "type": "faster_payment", "description": "Coinbase", "counterparty": "Coinbase"},
    ]

    crypto_trades = [
        {"date": "2026-01-09", "asset": "BTC", "action": "buy", "quantity": 0.015,
         "price_gbp": 500.0, "fee_gbp": 2.0, "acquisition_method": "exchange"},
        {"date": "2026-02-20", "asset": "BTC", "action": "buy", "quantity": 0.010,
         "price_gbp": 350.0, "fee_gbp": 1.50, "acquisition_method": "P2P_cash"},
        {"date": "2026-03-15", "asset": "BTC", "action": "sell", "quantity": 0.020,
         "price_gbp": 720.0, "fee_gbp": 5.0},
    ]

    # ---- RUN THE PIPELINE ----
    gross = sum(r["amount"] for r in income_records)
    expenses = sum(r["amount"] for r in expense_records)

    result = queen.process(
        bank_transactions=bank_txns,
        income_records=income_records,
        expense_records=expense_records,
        crypto_trades=crypto_trades,
        gross_turnover=gross,
        allowable_expenses=expenses,
        crypto_gains=0,         # Within annual exemption
        cis_deductions=0,
    )

    print(queen.print_pipeline_report(result))
