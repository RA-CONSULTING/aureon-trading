"""
HNC GATEWAY — hnc_gateway.py
==============================
The Streamlined User Interface Orchestrator.

This is the "one button" module. John fills in his details,
uploads his bank CSV, and the Gateway runs the entire pipeline:

    1. IMPORT   — Parse bank CSV / crypto export
    2. PROCESS  — Queen pipeline (categorise, ledger, VAT, tax)
    3. GENERATE — PDF reports & Excel workbooks
    4. FILE     — Submit to HMRC via MTD API (with user confirmation)

The Gateway stores user profiles, remembers settings between sessions,
and presents a clear step-by-step flow.

This module is designed to be called from any frontend:
    - Flask/Django web app
    - Desktop GUI (Tkinter/PyQt)
    - CLI interface
    - REST API endpoint

Aureon Creator / Aureon Research — April 2026
"""

from __future__ import annotations
import json
import logging
import os
import time
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("hnc_gateway")


# =========================================================================
# USER PROFILE
# =========================================================================

@dataclass
class UserProfile:
    """
    Everything we need to know about the user to file their returns.
    John fills this in once — we remember it.
    """
    # Personal
    full_name: str = ""
    trading_as: str = ""           # "Smith Builders"
    nino: str = ""                 # National Insurance Number
    utr: str = ""                  # Unique Taxpayer Reference

    # Business
    business_type: str = "sole_trader"   # sole_trader, partnership, limited
    trade_sector: str = "construction"   # construction, plumbing, electrical, general
    trade_description: str = ""          # "General building contractor"

    # Tax
    tax_year: str = "2025/26"
    accounting_year_end: str = "2026-04-05"  # Usually 5 April for sole traders
    # Optional custom accounting period (for company year-ends, bespoke periods, etc.)
    # If set, reporting outputs should prefer this over the tax year label.
    accounting_period_start: str = ""  # YYYY-MM-DD
    accounting_period_end: str = ""    # YYYY-MM-DD

    # VAT
    vat_registered: bool = False
    vrn: str = ""                  # VAT Registration Number
    vat_scheme: str = "flat_rate"  # flat_rate, standard, cash_accounting
    flat_rate_percentage: float = 9.5   # For construction
    vat_threshold_check: bool = True

    # CIS
    cis_registered: bool = True
    cis_deduction_rate: float = 0.20    # 20% standard, 30% unverified

    # HMRC API
    hmrc_client_id: str = ""
    hmrc_client_secret: str = ""
    hmrc_business_id: str = ""
    hmrc_environment: str = "sandbox"

    # Address (for invoices)
    address_line1: str = ""
    address_line2: str = ""
    city: str = ""
    county: str = ""
    postcode: str = ""

    # Bank details (for invoices)
    bank_name: str = ""
    sort_code: str = ""
    account_number: str = ""

    # Contact
    email: str = ""
    phone: str = ""

    def save(self, filepath: str):
        """Save profile to JSON file."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> Optional[UserProfile]:
        try:
            with open(filepath) as f:
                data = json.load(f)
            return cls(**{k: v for k, v in data.items()
                         if k in cls.__dataclass_fields__})
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def validate(self) -> List[str]:
        """Check all required fields are filled."""
        issues = []
        if not self.full_name:
            issues.append("Full name is required")
        if not self.nino:
            issues.append("National Insurance Number (NINO) is required")
        if not self.utr:
            issues.append("Unique Taxpayer Reference (UTR) is required")
        if self.vat_registered and not self.vrn:
            issues.append("VAT Registration Number (VRN) required if VAT registered")
        if not self.trade_sector:
            issues.append("Trade sector is required")
        return issues

    @property
    def entity_display(self) -> str:
        if self.trading_as:
            return f"{self.full_name} t/a {self.trading_as}"
        return self.full_name

    @staticmethod
    def _fmt_uk_date(iso_yyyy_mm_dd: str) -> str:
        """
        Format ISO date (YYYY-MM-DD) as UK-style 'D Month YYYY'.
        Falls back to the raw input string if parsing fails.
        """
        try:
            d = datetime.strptime(iso_yyyy_mm_dd, "%Y-%m-%d").date()
        except Exception:
            return iso_yyyy_mm_dd
        return f"{d.day} {d.strftime('%B %Y')}"

    @property
    def reporting_period_label(self) -> str:
        """
        Human-readable period label used on PDFs and exports.
        Defaults to tax year unless a custom accounting period is provided.
        """
        if self.accounting_period_start and self.accounting_period_end:
            return f"{self._fmt_uk_date(self.accounting_period_start)} to {self._fmt_uk_date(self.accounting_period_end)}"
        return f"Tax Year {self.tax_year}"

    @property
    def reporting_period_end_label(self) -> str:
        """
        Single-date label for TB 'as at' style outputs.
        """
        if self.accounting_period_end:
            return self._fmt_uk_date(self.accounting_period_end)
        # Preserve existing behaviour for sole-trader tax-year outputs.
        return f"5 April {int(self.tax_year[:4])+1}"


# =========================================================================
# PIPELINE RESULT
# =========================================================================

@dataclass
class GatewayResult:
    """Complete result of a gateway run."""
    # Status
    status: str = "pending"           # pending, processing, completed, failed
    started_at: str = ""
    completed_at: str = ""
    error: str = ""

    # Stage results
    import_summary: Dict = field(default_factory=dict)
    pipeline_summary: Dict = field(default_factory=dict)
    tax_summary: Dict = field(default_factory=dict)
    vat_summary: Dict = field(default_factory=dict)

    # Generated documents
    documents: List[Dict] = field(default_factory=list)

    # HMRC filing
    hmrc_filing: Dict = field(default_factory=dict)

    # Warnings & actions needed
    warnings: List[str] = field(default_factory=list)
    actions_required: List[str] = field(default_factory=list)


# =========================================================================
# THE GATEWAY
# =========================================================================

class HNCGateway:
    """
    The main entry point. John's one-stop shop.

    Usage:
        gateway = HNCGateway(profile)
        result = gateway.run(csv_files=["bank.csv"], crypto_files=["coinbase.csv"])
        # result.documents has all PDFs and XLSXs
        # result.hmrc_filing has what was submitted to HMRC
    """

    def __init__(self, profile: UserProfile,
                 output_dir: str = "./output",
                 data_dir: str = "./data"):
        self.profile = profile
        self.output_dir = output_dir
        self.data_dir = data_dir

        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(data_dir, exist_ok=True)

        self._result = GatewayResult()

    def run(self,
            csv_files: List[str] = None,
            csv_strings: List[Tuple[str, str]] = None,
            crypto_files: List[str] = None,
            crypto_strings: List[Tuple[str, str]] = None,
            skip_hmrc: bool = True,
            generate_documents: bool = True,
            ) -> GatewayResult:
        """
        Run the complete pipeline.

        csv_files: list of bank CSV file paths
        csv_strings: list of (csv_text, filename) tuples for web uploads
        crypto_files: list of crypto exchange CSV file paths
        crypto_strings: list of (csv_text, filename) tuples
        skip_hmrc: if True, don't file to HMRC (default for safety)
        generate_documents: if True, generate PDFs and XLSXs
        """
        self._result = GatewayResult(
            started_at=datetime.now().isoformat(),
            status="processing",
        )

        try:
            # Validate profile
            issues = self.profile.validate()
            if issues:
                self._result.warnings.extend(issues)
                # Non-fatal for document generation, fatal for HMRC filing

            # ---- STAGE 1: IMPORT ----
            self._stage_import(csv_files, csv_strings,
                               crypto_files, crypto_strings)

            # ---- STAGE 2: PROCESS ----
            self._stage_process()

            # ---- STAGE 3: GENERATE ----
            if generate_documents:
                self._stage_generate()

            # ---- STAGE 4: FILE (optional) ----
            if not skip_hmrc and not issues:
                self._stage_file()
            elif not skip_hmrc and issues:
                self._result.actions_required.append(
                    "Cannot file to HMRC — profile incomplete: " +
                    ", ".join(issues)
                )

            self._result.status = "completed"
            self._result.completed_at = datetime.now().isoformat()

        except Exception as e:
            self._result.status = "failed"
            self._result.error = str(e)
            logger.error(f"Gateway failed: {e}", exc_info=True)

        return self._result

    # -----------------------------------------------------------------
    # STAGE 1: IMPORT
    # -----------------------------------------------------------------

    def _stage_import(self, csv_files, csv_strings,
                       crypto_files, crypto_strings):
        """Import all uploaded files."""
        from core.hnc_import import HNCImportEngine

        self._importer = HNCImportEngine()

        # File imports
        for fp in (csv_files or []):
            self._importer.import_file(fp)

        # String imports (web uploads)
        for csv_text, filename in (csv_strings or []):
            self._importer.import_csv_string(csv_text, filename)

        # Crypto file imports
        for fp in (crypto_files or []):
            self._importer.import_file(fp)

        # Crypto string imports
        for csv_text, filename in (crypto_strings or []):
            self._importer.import_csv_string(csv_text, filename)

        # Get normalised data
        self._bank_txns = self._importer.get_bank_transactions()
        self._crypto_trades = self._importer.get_crypto_trades()

        # Separate income / expenses
        self._income = [t for t in self._bank_txns
                        if t.get("direction") == "in"]
        self._expenses = [t for t in self._bank_txns
                          if t.get("direction") == "out"]
        self._total_income = sum(t.get("amount", 0) for t in self._income)
        self._total_expenses = sum(t.get("amount", 0) for t in self._expenses)

        self._result.import_summary = {
            "bank_transactions": len(self._bank_txns),
            "crypto_trades": len(self._crypto_trades),
            "income_records": len(self._income),
            "expense_records": len(self._expenses),
            "total_income": self._total_income,
            "total_expenses": self._total_expenses,
            "files_imported": len(self._importer.results),
            "errors": sum(len(r.errors) for r in self._importer.results),
        }

        logger.info(f"Import complete: {len(self._bank_txns)} bank, "
                     f"{len(self._crypto_trades)} crypto")

    # -----------------------------------------------------------------
    # STAGE 2: PROCESS
    # -----------------------------------------------------------------

    def _stage_process(self):
        """Run the Queen pipeline."""
        from core.hnc_queen import HNCQueen

        queen = HNCQueen(
            entity_name=self.profile.entity_display,
            entity_type=self.profile.business_type,
            trade_sector=self.profile.trade_sector,
            tax_year=self.profile.tax_year,
            vat_scheme=self.profile.vat_scheme if self.profile.vat_registered
                        else "not_registered",
            vat_registered=self.profile.vat_registered,
        )

        # Determine VAT quarter from current date
        now = datetime.now()
        q_map = {1: "Q3", 2: "Q3", 3: "Q3", 4: "Q4", 5: "Q4", 6: "Q4",
                 7: "Q1", 8: "Q1", 9: "Q1", 10: "Q2", 11: "Q2", 12: "Q2"}
        year = self.profile.tax_year.split("/")[0]
        quarter = f"{year}-{q_map.get(now.month, 'Q1')}"

        self._pipeline_result = queen.process(
            bank_transactions=self._bank_txns,
            income_records=self._income,
            expense_records=self._expenses,
            gross_turnover=self._total_income,
            allowable_expenses=self._total_expenses,
            trading_profit=max(0, self._total_income - self._total_expenses),
            vat_quarter=quarter,
        )

        # Extract summaries
        self._result.pipeline_summary = {
            "status": self._pipeline_result.status,
            "total_income": self._pipeline_result.total_income,
            "total_expenses": self._pipeline_result.total_expenses,
            "trading_profit": self._pipeline_result.trading_profit,
            "stages_completed": len(self._pipeline_result.stages),
        }

        # Tax computation
        tax = self._pipeline_result.tax_computation
        if tax and isinstance(tax, dict):
            self._result.tax_summary = tax
        else:
            self._result.tax_summary = {
                "income_tax": 0,
                "nic2": 0,
                "nic4": 0,
                "total_tax": 0,
                "note": "Tax computation from pipeline — check details",
            }

        # VAT
        vat = self._pipeline_result.vat_return
        if vat and isinstance(vat, dict):
            self._result.vat_summary = vat
        else:
            self._result.vat_summary = {}

        # Smart warnings
        if self._total_income > 85000 and not self.profile.vat_registered:
            self._result.warnings.append(
                f"WARNING: Turnover £{self._total_income:,.2f} exceeds "
                f"£85,000 VAT registration threshold — you may need to "
                f"register for VAT"
            )

        if self._pipeline_result.trading_profit > 50270:
            self._result.warnings.append(
                "Higher rate taxpayer — consider pension contributions "
                "to reduce tax liability"
            )

        logger.info(f"Pipeline complete: profit £{self._pipeline_result.trading_profit:,.2f}")

    # -----------------------------------------------------------------
    # STAGE 3: GENERATE DOCUMENTS
    # -----------------------------------------------------------------

    def _stage_generate(self):
        """Generate all PDF and Excel documents."""
        from core.hnc_export import HNCExportEngine
        from dataclasses import dataclass as dc, field as dc_field

        # Simple report line class for building reports
        @dc
        class RL:
            label: str = ""
            amount: float = 0.0
            indent: int = 0
            is_total: bool = False
            is_subtotal: bool = False

        @dc
        class RD:
            period: str = ""
            lines: list = dc_field(default_factory=list)
            totals: dict = dc_field(default_factory=dict)
            notes: list = dc_field(default_factory=list)

        exporter = HNCExportEngine(self.output_dir, self.profile.entity_display)

        profit = self._pipeline_result.trading_profit

        # --- PDF 1: P&L ---
        pnl = RD(
            period=self.profile.reporting_period_label,
            lines=[
                RL("TURNOVER", self._total_income),
                RL("Less: Cost of Sales & Expenses",
                   -self._total_expenses),
                RL("NET PROFIT", profit, 0, True),
            ],
            notes=["Prepared under FRS 102 Section 1A."],
        )
        exporter.export_pnl(pnl)

        # --- PDF 2: Tax Summary ---
        tax_d = self._result.tax_summary
        tax_export = {
            "tax_year": self.profile.tax_year,
            "turnover": self._total_income,
            "total_expenses": self._total_expenses,
            "net_profit": profit,
            "income_tax": tax_d.get("income_tax", 0),
            "nic2": tax_d.get("nic2", 0),
            "nic4": tax_d.get("nic4", 0),
            "total_tax": tax_d.get("total_tax", 0),
        }
        exporter.export_tax_summary(tax_export)

        # --- PDF 3: VAT Return (if registered) ---
        if self.profile.vat_registered and self._result.vat_summary:
            exporter.export_vat_return(self._result.vat_summary)

        # --- PDF 4: CGT Summary (if crypto trades) ---
        if self._crypto_trades:
            try:
                from core.hnc_cost_basis import HNCCostBasisEngine
                cgt_engine = HNCCostBasisEngine(
                    tax_year=self.profile.tax_year
                )
                for trade in self._crypto_trades:
                    cgt_engine.add_trade(trade)
                cgt_result = cgt_engine.compute()
                if isinstance(cgt_result, dict):
                    exporter.export_cgt_summary(cgt_result)
            except Exception as e:
                logger.warning(f"CGT computation skipped: {e}")

        # --- XLSX 1: Management Accounts ---
        monthly = self._build_monthly_projection()
        exporter.export_management_accounts(monthly)

        # --- XLSX 2: General Ledger ---
        journal = self._build_journal_entries()
        exporter.export_ledger(journal)

        # --- XLSX 3: Trial Balance ---
        accounts = self._build_trial_balance()
        exporter.export_trial_balance(accounts,
                                      self.profile.reporting_period_end_label)

        self._result.documents = exporter.generated
        logger.info(f"Generated {len(exporter.generated)} documents")

    def _build_monthly_projection(self) -> List[Dict]:
        """Build 12-month management accounts from actual data."""
        months = ["Apr", "May", "Jun", "Jul", "Aug", "Sep",
                  "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
        seasonal = [0.7, 0.9, 1.1, 1.2, 1.15, 1.1,
                    1.0, 0.85, 0.6, 0.75, 0.85, 1.0]

        # Group actuals by month
        monthly_income = {}
        monthly_expenses = {}
        for t in self._income:
            d = t.get("date", "")
            if len(d) >= 7:
                m = d[5:7]  # MM from YYYY-MM-DD
                monthly_income[m] = monthly_income.get(m, 0) + t.get("amount", 0)
        for t in self._expenses:
            d = t.get("date", "")
            if len(d) >= 7:
                m = d[5:7]
                monthly_expenses[m] = monthly_expenses.get(m, 0) + t.get("amount", 0)

        # Fill in projected months where no actuals
        avg_income = self._total_income / max(1, len(monthly_income))
        avg_expenses = self._total_expenses / max(1, len(monthly_expenses))

        result = []
        month_nums = ["04", "05", "06", "07", "08", "09",
                      "10", "11", "12", "01", "02", "03"]
        for i, (name, m_num) in enumerate(zip(months, month_nums)):
            if m_num in monthly_income:
                rev = monthly_income[m_num]
            else:
                rev = round(avg_income * seasonal[i], 2)

            if m_num in monthly_expenses:
                exp = monthly_expenses[m_num]
            else:
                exp = round(avg_expenses * seasonal[i], 2)

            result.append({
                "month": name,
                "turnover": rev,
                "expenses": {"operating": exp},
            })
        return result

    def _build_journal_entries(self) -> List[Dict]:
        """Convert bank transactions to journal entries."""
        journal = []
        for t in self._bank_txns:
            amt = t.get("amount", 0)
            direction = t.get("direction", "out")
            journal.append({
                "date": t.get("date", ""),
                "account": "1200 - Bank",
                "description": t.get("description", ""),
                "reference": t.get("reference", ""),
                "debit": amt if direction == "in" else 0,
                "credit": amt if direction == "out" else 0,
            })
        return journal

    def _build_trial_balance(self) -> List[Dict]:
        """Build trial balance from pipeline totals."""
        return [
            {"account_code": "1200", "account_name": "Bank Current Account",
             "debit": self._total_income - self._total_expenses, "credit": 0},
            {"account_code": "4000", "account_name": "Sales / Turnover",
             "debit": 0, "credit": self._total_income},
            {"account_code": "5000", "account_name": "Cost of Sales",
             "debit": self._total_expenses * 0.6, "credit": 0},
            {"account_code": "6000", "account_name": "Administrative Expenses",
             "debit": self._total_expenses * 0.4, "credit": 0},
        ]

    # -----------------------------------------------------------------
    # STAGE 4: FILE TO HMRC
    # -----------------------------------------------------------------

    def _stage_file(self):
        """Submit to HMRC via MTD API."""
        from core.hnc_hmrc_api import (
            HMRCConfig, HMRCApiClient, HMRCFilingWorkflow
        )

        config = HMRCConfig(
            environment=self.profile.hmrc_environment,
            client_id=self.profile.hmrc_client_id,
            client_secret=self.profile.hmrc_client_secret,
            token_file=os.path.join(self.data_dir, "hmrc_token.json"),
        )

        client = HMRCApiClient(config)

        # Convert tax year format: "2025/26" -> "2025-26"
        ty = self.profile.tax_year.replace("/", "-")

        workflow = HMRCFilingWorkflow(
            api_client=client,
            nino=self.profile.nino,
            business_id=self.profile.hmrc_business_id,
            vrn=self.profile.vrn,
            tax_year=ty,
        )

        # Auto-discover business if needed
        if not self.profile.hmrc_business_id:
            biz = workflow.discover_business()
            if "action_required" in biz:
                self._result.actions_required.append(
                    "Multiple businesses found — please select one: " +
                    json.dumps(biz["businesses"])
                )
                return
            if "error" in biz:
                self._result.warnings.append(biz["error"])
                return

        self._result.hmrc_filing = {
            "workflow_status": workflow.get_workflow_status(),
            "note": "HMRC filing prepared — awaiting user confirmation "
                    "before submission. Call gateway.confirm_filing() "
                    "to submit.",
        }

        # Store workflow for later confirmation
        self._workflow = workflow
        self._result.actions_required.append(
            "Review generated documents and confirm HMRC filing"
        )

    def confirm_filing(self, period_start: str, period_end: str,
                       file_vat: bool = False,
                       vat_period_key: str = "") -> Dict:
        """
        User has reviewed — submit to HMRC.

        Call this AFTER run() and AFTER user reviews the documents.
        """
        if not hasattr(self, "_workflow"):
            return {"error": "No filing workflow available — run() first"}

        results = {}

        # Submit quarterly update
        try:
            qr = self._workflow.submit_quarterly_update(
                self._pipeline_result,
                period_start=period_start,
                period_end=period_end,
                consolidated=(self._total_income < 90000),
            )
            results["quarterly_update"] = qr
        except Exception as e:
            results["quarterly_update_error"] = str(e)

        # Trigger calculation
        try:
            calc = self._workflow.trigger_tax_calc()
            results["calculation_triggered"] = calc
        except Exception as e:
            results["calculation_error"] = str(e)

        # VAT return
        if file_vat and self.profile.vat_registered and vat_period_key:
            try:
                vr = self._workflow.submit_vat_return(
                    self._result.vat_summary,
                    period_key=vat_period_key,
                )
                results["vat_return"] = vr
            except Exception as e:
                results["vat_return_error"] = str(e)

        return results

    # -----------------------------------------------------------------
    # CONVENIENCE METHODS
    # -----------------------------------------------------------------

    def get_result_summary(self) -> str:
        """Human-readable summary of the gateway run."""
        r = self._result
        lines = [
            "=" * 60,
            "THE HNC ACCOUNTANT — PROCESSING COMPLETE",
            "=" * 60,
            f"Client:     {self.profile.entity_display}",
            f"Tax Year:   {self.profile.tax_year}",
            f"Status:     {r.status.upper()}",
            "",
            "IMPORT",
            f"  Bank transactions: {r.import_summary.get('bank_transactions', 0)}",
            f"  Crypto trades:     {r.import_summary.get('crypto_trades', 0)}",
            f"  Total income:      £{r.import_summary.get('total_income', 0):,.2f}",
            f"  Total expenses:    £{r.import_summary.get('total_expenses', 0):,.2f}",
            "",
            "PIPELINE",
            f"  Trading profit:    £{r.pipeline_summary.get('trading_profit', 0):,.2f}",
            f"  Stages completed:  {r.pipeline_summary.get('stages_completed', 0)}",
            "",
            "TAX",
            f"  Income Tax:        £{r.tax_summary.get('income_tax', 0):,.2f}",
            f"  NIC Class 2:       £{r.tax_summary.get('nic2', 0):,.2f}",
            f"  NIC Class 4:       £{r.tax_summary.get('nic4', 0):,.2f}",
            f"  Total Tax Due:     £{r.tax_summary.get('total_tax', 0):,.2f}",
            "",
            f"DOCUMENTS GENERATED: {len(r.documents)}",
        ]
        for i, doc in enumerate(r.documents, 1):
            lines.append(f"  {i}. {doc.get('type', '')} — {doc.get('path', '')}")

        if r.warnings:
            lines.append("")
            lines.append("WARNINGS:")
            for w in r.warnings:
                lines.append(f"  ! {w}")

        if r.actions_required:
            lines.append("")
            lines.append("ACTIONS REQUIRED:")
            for a in r.actions_required:
                lines.append(f"  > {a}")

        if r.error:
            lines.append("")
            lines.append(f"ERROR: {r.error}")

        lines.append("=" * 60)
        return "\n".join(lines)


# =========================================================================
# QUICK START HELPER
# =========================================================================

def quick_start(name: str, nino: str, utr: str,
                bank_csv: str, filename: str = "bank.csv",
                output_dir: str = "./output",
                **kwargs) -> GatewayResult:
    """
    Quickest possible way to process accounts.

    quick_start(
        name="John Smith",
        nino="QQ123456C",
        utr="1234567890",
        bank_csv=open("hsbc.csv").read(),
    )
    """
    profile = UserProfile(
        full_name=name,
        nino=nino,
        utr=utr,
        **{k: v for k, v in kwargs.items()
           if k in UserProfile.__dataclass_fields__},
    )

    gateway = HNCGateway(profile, output_dir=output_dir)
    return gateway.run(
        csv_strings=[(bank_csv, filename)],
        skip_hmrc=True,
    )


# =========================================================================
# STANDALONE TEST
# =========================================================================

if __name__ == "__main__":
    import tempfile

    print("=" * 60)
    print("HNC GATEWAY — FULL INTEGRATION TEST")
    print("=" * 60)

    # ---- Test 1: User Profile ----
    print("\n--- Test 1: User Profile ---")
    profile = UserProfile(
        full_name="John Smith",
        trading_as="Smith Builders",
        nino="QQ123456C",
        utr="1234567890",
        trade_sector="construction",
        tax_year="2025/26",
        vat_registered=True,
        vrn="123456789",
        vat_scheme="flat_rate",
        cis_registered=True,
    )
    issues = profile.validate()
    assert len(issues) == 0, f"Profile validation failed: {issues}"
    print(f"  Entity: {profile.entity_display}")
    print(f"  NINO: {profile.nino}")
    print(f"  VAT: {profile.vrn}")
    print("  ✓ Profile valid")

    # ---- Test 2: Profile Persistence ----
    print("\n--- Test 2: Profile Save/Load ---")
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        profile.save(f.name)
        loaded = UserProfile.load(f.name)
        assert loaded.full_name == profile.full_name
        assert loaded.nino == profile.nino
        os.unlink(f.name)
    print("  ✓ Profile round-trip")

    # ---- Test 3: Full Gateway Run ----
    print("\n--- Test 3: Full Gateway Run ---")

    hsbc_csv = """Date,Type,Description,Paid Out,Paid In,Balance
10/04/2025,BP,TRAVIS PERKINS,2800.00,,23504.50
12/04/2025,BGC,MR DAVIES BATHROOM,,7440.00,30944.50
15/04/2025,BP,SHELL FUEL,85.50,,30859.00
18/04/2025,BP,SCREWFIX TOOLS,350.00,,30509.00
22/04/2025,BGC,MRS JONES KITCHEN,,8500.00,39009.00
25/04/2025,BP,RAC VAN INSURANCE,316.67,,38692.33
28/04/2025,BP,VODAFONE MOBILE,45.00,,38647.33
05/05/2025,BGC,MR PATEL EXTENSION,,12000.00,50647.33
08/05/2025,BP,JEWSON TIMBER,3200.00,,47447.33
15/05/2025,BGC,MRS KHAN BATHROOM,,6800.00,54067.33
20/05/2025,BP,TRAVIS PERKINS,1950.00,,52117.33"""

    with tempfile.TemporaryDirectory() as outdir:
        gateway = HNCGateway(profile, output_dir=outdir)
        result = gateway.run(
            csv_strings=[(hsbc_csv, "john_hsbc.csv")],
            skip_hmrc=True,
            generate_documents=True,
        )

        print(gateway.get_result_summary())

        assert result.status == "completed", f"Gateway failed: {result.error}"
        assert result.import_summary["bank_transactions"] > 0
        assert result.pipeline_summary["trading_profit"] > 0
        assert len(result.documents) >= 4  # P&L, Tax, MgmtAccts, Ledger, TB
        print(f"\n  ✓ Gateway completed successfully")
        print(f"  ✓ {len(result.documents)} documents generated")

    # ---- Test 4: Quick Start ----
    print("\n--- Test 4: Quick Start API ---")
    with tempfile.TemporaryDirectory() as outdir:
        result = quick_start(
            name="John Smith",
            nino="QQ123456C",
            utr="1234567890",
            bank_csv=hsbc_csv,
            output_dir=outdir,
            trading_as="Smith Builders",
            trade_sector="construction",
            vat_registered=True,
            vrn="123456789",
            vat_scheme="flat_rate",
        )
        assert result.status == "completed"
        print(f"  ✓ Quick start: {len(result.documents)} documents, "
              f"profit £{result.pipeline_summary.get('trading_profit', 0):,.2f}")

    print("\n" + "=" * 60)
    print("ALL GATEWAY TESTS PASSED")
    print("=" * 60)

    # Module count
    import glob
    modules = glob.glob("/sessions/upbeat-stoic-hamilton/mnt/Kings_Accounting_Suite/core/hnc_*.py")
    total_lines = 0
    for m in sorted(modules):
        with open(m) as f:
            lc = len(f.readlines())
            total_lines += lc
            print(f"  {Path(m).name:30s} {lc:>6,} lines")
    print(f"  {'TOTAL':30s} {total_lines:>6,} lines")
