"""
HNC IMPORT — hnc_import.py
===========================
File Upload & Import Engine.

Ingests raw financial data from any common UK banking/trading format
and normalises it into the HNC internal schema that every engine
can consume.

Supported import formats:
    BANK STATEMENTS:
        - Barclays CSV (DD/MM/YYYY, desc, amount)
        - HSBC CSV (Date, Type, Description, Paid out, Paid in, Balance)
        - Lloyds CSV (Transaction Date, Transaction Type, Description, Debit, Credit)
        - Natwest/RBS CSV (Date, Type, Description, Value, Balance)
        - Revolut CSV (Type, Product, Started Date, Completed Date, Description, Amount)
        - Starling CSV (Date, Counter Party, Reference, Type, Amount)
        - Monzo CSV (date, name, notes, amount, category)
        - Generic CSV (auto-detect columns)

    CRYPTO EXCHANGES:
        - Coinbase CSV (Timestamp, Type, Asset, Quantity, Spot Price, Subtotal, Total, Fees)
        - Binance CSV
        - Kraken CSV
        - Generic exchange CSV

    ACCOUNTING DATA:
        - Excel workbooks (.xlsx)
        - CSV expense lists
        - CSV invoice lists

Output: Normalised dicts ready for HNCQueen.process()

Aureon Creator / Aureon Research — April 2026
"""

from __future__ import annotations
import csv
import io
import logging
import re
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("hnc_import")


# ========================================================================
# NORMALISED TRANSACTION SCHEMA
# ========================================================================

@dataclass
class NormalisedTransaction:
    """The universal HNC transaction format."""
    date: str = ""                 # YYYY-MM-DD
    description: str = ""
    amount: float = 0.0            # Positive = money in, negative = money out
    direction: str = ""            # "in" or "out"
    type: str = ""                 # bacs, card, cash, dd, faster_payment, etc.
    counterparty: str = ""
    category: str = ""             # Auto-detected or manual
    reference: str = ""
    balance: float = 0.0
    source_file: str = ""
    source_line: int = 0
    raw_data: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "date": self.date,
            "description": self.description,
            "amount": abs(self.amount),
            "direction": self.direction,
            "type": self.type,
            "counterparty": self.counterparty,
            "category": self.category,
            "reference": self.reference,
            "balance": self.balance,
        }


@dataclass
class NormalisedCryptoTrade:
    """Universal crypto trade format."""
    date: str = ""
    asset: str = ""
    action: str = ""               # buy, sell, swap, etc.
    quantity: float = 0.0
    price_gbp: float = 0.0
    fee_gbp: float = 0.0
    exchange: str = ""
    notes: str = ""
    raw_data: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "date": self.date,
            "asset": self.asset,
            "action": self.action,
            "quantity": self.quantity,
            "price_gbp": self.price_gbp,
            "fee_gbp": self.fee_gbp,
            "exchange": self.exchange,
            "notes": self.notes,
        }


@dataclass
class ImportResult:
    """Result of a file import."""
    source_file: str = ""
    format_detected: str = ""
    rows_read: int = 0
    rows_imported: int = 0
    rows_skipped: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    transactions: List[NormalisedTransaction] = field(default_factory=list)
    crypto_trades: List[NormalisedCryptoTrade] = field(default_factory=list)
    date_range: Tuple[str, str] = ("", "")
    total_in: float = 0.0
    total_out: float = 0.0


# ========================================================================
# DATE PARSING
# ========================================================================

def parse_date(d: str) -> str:
    """Parse various UK/US date formats into YYYY-MM-DD."""
    if not d or not d.strip():
        return ""

    d = d.strip().strip('"').strip("'")

    # Already ISO
    if re.match(r'^\d{4}-\d{2}-\d{2}', d):
        return d[:10]

    formats = [
        "%d/%m/%Y",        # UK: 15/01/2026
        "%d-%m-%Y",        # UK: 15-01-2026
        "%d %b %Y",        # UK: 15 Jan 2026
        "%d %B %Y",        # UK: 15 January 2026
        "%d/%m/%y",        # UK short: 15/01/26
        "%Y-%m-%dT%H:%M",  # ISO with time
        "%d/%m/%Y %H:%M",  # UK with time
        "%m/%d/%Y",        # US: 01/15/2026
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(d[:len(d)], fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Last resort: try dateutil if available
    try:
        from dateutil.parser import parse as dateparse
        dt = dateparse(d, dayfirst=True)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return d


def parse_amount(val: str) -> float:
    """Parse UK currency amounts."""
    if not val or not str(val).strip():
        return 0.0
    s = str(val).strip().strip('"').strip("'")
    s = s.replace("£", "").replace(",", "").replace(" ", "")
    s = s.replace("GBP", "").strip()

    # Handle (brackets) = negative
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]

    try:
        return float(s)
    except ValueError:
        return 0.0


def detect_transaction_type(desc: str) -> str:
    """Guess payment type from description."""
    d = desc.lower()
    if any(k in d for k in ["direct debit", "d/d", "ddr"]):
        return "dd"
    if any(k in d for k in ["standing order", "s/o"]):
        return "standing_order"
    if any(k in d for k in ["faster payment", "fp-", "fps"]):
        return "faster_payment"
    if any(k in d for k in ["bacs", "credit", "salary"]):
        return "bacs"
    if any(k in d for k in ["card", "visa", "mastercard", "contactless", "pos"]):
        return "card"
    if any(k in d for k in ["cash", "atm", "withdrawal"]):
        return "cash"
    if any(k in d for k in ["chq", "cheque"]):
        return "cheque"
    if any(k in d for k in ["transfer", "tfr"]):
        return "transfer"
    return "other"


# ========================================================================
# BANK FORMAT DETECTORS
# ========================================================================

def detect_bank_format(headers: List[str]) -> str:
    """Detect which bank format a CSV is from."""
    h = [c.strip().lower() for c in headers]

    # Barclays: Number, Date, Account, Amount, Subcategory, Memo
    if "subcategory" in h and "memo" in h:
        return "barclays"

    # HSBC: Date, Type, Description, Paid out, Paid in, Balance
    if "paid out" in h and "paid in" in h:
        return "hsbc"

    # Lloyds: Transaction Date, Transaction Type, Sort Code, Account Number, Transaction Description, Debit Amount, Credit Amount, Balance
    if "transaction date" in h and "debit amount" in h:
        return "lloyds"

    # Natwest/RBS: Date, Type, Description, Value, Balance, Account Name, Account Number
    if "value" in h and "account name" in h:
        return "natwest"

    # Revolut: Type, Product, Started Date, Completed Date, Description, Amount, Fee, Currency
    if "started date" in h and "completed date" in h:
        return "revolut"

    # Fintech Card (Starling Business, Tide, etc.): Date, Card, Type, Description, Credit, Debit, Balance, Category
    # Detect BEFORE starling/monzo — has "card" + "category" + separate credit/debit
    if "card" in h and "category" in h and "credit" in h and "debit" in h:
        return "fintech_card"

    # Starling: Date, Counter Party, Reference, Type, Amount (GBP), Balance (GBP)
    if "counter party" in h:
        return "starling"

    # Monzo: id, created, amount, currency, local_amount, local_currency, category, name, notes
    if "category" in h and "local_amount" in h:
        return "monzo"

    # Coinbase: Timestamp, Transaction Type, Asset, Quantity Transacted, Spot Price at Transaction, Subtotal, Total (inclusive of fees and/or spread), Fees and/or Spread, Notes
    if "quantity transacted" in h or "spot price" in h:
        return "coinbase"

    # Binance
    if "operation" in h and "coin" in h:
        return "binance"

    # Generic: look for date + amount columns
    if any(k in h for k in ["date", "transaction date"]):
        return "generic"

    return "unknown"


# ========================================================================
# BANK IMPORTERS
# ========================================================================

def import_barclays(rows: List[Dict], source: str = "") -> List[NormalisedTransaction]:
    """Import Barclays CSV format."""
    txns = []
    for i, row in enumerate(rows):
        amount = parse_amount(row.get("Amount", "0"))
        txn = NormalisedTransaction(
            date=parse_date(row.get("Date", "")),
            description=row.get("Memo", row.get("Subcategory", "")),
            amount=amount,
            direction="in" if amount > 0 else "out",
            type=detect_transaction_type(row.get("Subcategory", "")),
            counterparty=row.get("Memo", "")[:50],
            source_file=source,
            source_line=i + 2,
            raw_data=dict(row),
        )
        txns.append(txn)
    return txns


def import_hsbc(rows: List[Dict], source: str = "") -> List[NormalisedTransaction]:
    """Import HSBC CSV format."""
    txns = []
    for i, row in enumerate(rows):
        paid_in = parse_amount(row.get("Paid In", row.get("Paid in", "0")))
        paid_out = parse_amount(row.get("Paid Out", row.get("Paid out", "0")))
        amount = paid_in if paid_in > 0 else -paid_out

        txn = NormalisedTransaction(
            date=parse_date(row.get("Date", "")),
            description=row.get("Description", ""),
            amount=amount,
            direction="in" if amount > 0 else "out",
            type=row.get("Type", "").lower() or detect_transaction_type(
                row.get("Description", "")),
            counterparty=row.get("Description", "")[:50],
            balance=parse_amount(row.get("Balance", "0")),
            source_file=source,
            source_line=i + 2,
            raw_data=dict(row),
        )
        txns.append(txn)
    return txns


def import_lloyds(rows: List[Dict], source: str = "") -> List[NormalisedTransaction]:
    """Import Lloyds Banking Group CSV format."""
    txns = []
    for i, row in enumerate(rows):
        debit = parse_amount(row.get("Debit Amount", "0"))
        credit = parse_amount(row.get("Credit Amount", "0"))
        amount = credit if credit > 0 else -debit

        txn = NormalisedTransaction(
            date=parse_date(row.get("Transaction Date", "")),
            description=row.get("Transaction Description", ""),
            amount=amount,
            direction="in" if amount > 0 else "out",
            type=row.get("Transaction Type", "").lower(),
            counterparty=row.get("Transaction Description", "")[:50],
            balance=parse_amount(row.get("Balance", "0")),
            source_file=source,
            source_line=i + 2,
            raw_data=dict(row),
        )
        txns.append(txn)
    return txns


def import_natwest(rows: List[Dict], source: str = "") -> List[NormalisedTransaction]:
    """Import Natwest/RBS CSV format."""
    txns = []
    for i, row in enumerate(rows):
        amount = parse_amount(row.get("Value", "0"))
        txn = NormalisedTransaction(
            date=parse_date(row.get("Date", "")),
            description=row.get("Description", ""),
            amount=amount,
            direction="in" if amount > 0 else "out",
            type=row.get("Type", "").lower(),
            counterparty=row.get("Description", "")[:50],
            balance=parse_amount(row.get("Balance", "0")),
            source_file=source,
            source_line=i + 2,
            raw_data=dict(row),
        )
        txns.append(txn)
    return txns


def import_revolut(rows: List[Dict], source: str = "") -> List[NormalisedTransaction]:
    """Import Revolut CSV format."""
    txns = []
    for i, row in enumerate(rows):
        amount = parse_amount(row.get("Amount", "0"))
        txn = NormalisedTransaction(
            date=parse_date(row.get("Completed Date",
                                     row.get("Started Date", ""))),
            description=row.get("Description", ""),
            amount=amount,
            direction="in" if amount > 0 else "out",
            type=row.get("Type", "").lower(),
            counterparty=row.get("Description", "")[:50],
            source_file=source,
            source_line=i + 2,
            raw_data=dict(row),
        )
        txns.append(txn)
    return txns


def import_fintech_card(rows: List[Dict], source: str = "") -> List[NormalisedTransaction]:
    """
    Import fintech card CSV format.
    Headers: Date, Card, Type, Description, Credit, Debit, Balance, Category
    Used by: Starling Business, Tide, and similar UK fintech accounts.
    Amounts have £ prefix, debits are negative (e.g. -£50.00).
    Dates: DD MMM YYYY (e.g. "28 Feb 2026").
    """
    txns = []
    for i, row in enumerate(rows):
        credit = parse_amount(row.get("Credit", "0"))
        debit = parse_amount(row.get("Debit", "0"))

        # Debit column comes as negative (e.g. -50.00 after parsing -£50.00)
        # Credit column is positive
        if credit > 0:
            amount = credit
            direction = "in"
        elif debit != 0:
            amount = debit  # already negative from parse_amount
            direction = "out"
        else:
            amount = 0.0
            direction = "in"

        desc = row.get("Description", "").strip()
        txn_type_raw = row.get("Type", "").strip().lower()
        category = row.get("Category", "").strip()

        # Map Type column to our types
        if txn_type_raw == "debit":
            txn_type = detect_transaction_type(desc)
        elif txn_type_raw == "credit":
            txn_type = "bacs"
        else:
            txn_type = txn_type_raw or detect_transaction_type(desc)

        txn = NormalisedTransaction(
            date=parse_date(row.get("Date", "")),
            description=desc,
            amount=amount,
            direction=direction,
            type=txn_type,
            counterparty=desc[:50],
            category=category,
            balance=parse_amount(row.get("Balance", "0")),
            source_file=source,
            source_line=i + 2,
            raw_data=dict(row),
        )
        txns.append(txn)
    return txns


def import_starling(rows: List[Dict], source: str = "") -> List[NormalisedTransaction]:
    """Import Starling Bank CSV format."""
    txns = []
    for i, row in enumerate(rows):
        amount = parse_amount(row.get("Amount (GBP)", row.get("Amount", "0")))
        txn = NormalisedTransaction(
            date=parse_date(row.get("Date", "")),
            description=row.get("Reference", ""),
            amount=amount,
            direction="in" if amount > 0 else "out",
            type=row.get("Type", "").lower(),
            counterparty=row.get("Counter Party", ""),
            balance=parse_amount(row.get("Balance (GBP)",
                                         row.get("Balance", "0"))),
            source_file=source,
            source_line=i + 2,
            raw_data=dict(row),
        )
        txns.append(txn)
    return txns


def import_monzo(rows: List[Dict], source: str = "") -> List[NormalisedTransaction]:
    """Import Monzo CSV format."""
    txns = []
    for i, row in enumerate(rows):
        amount = parse_amount(row.get("amount", row.get("Amount", "0")))
        txn = NormalisedTransaction(
            date=parse_date(row.get("created", row.get("Date", ""))),
            description=row.get("notes", row.get("name", "")),
            amount=amount,
            direction="in" if amount > 0 else "out",
            type=detect_transaction_type(row.get("name", "")),
            counterparty=row.get("name", ""),
            category=row.get("category", ""),
            source_file=source,
            source_line=i + 2,
            raw_data=dict(row),
        )
        txns.append(txn)
    return txns


def import_generic(rows: List[Dict], source: str = "") -> List[NormalisedTransaction]:
    """Import generic CSV — auto-detect column meanings."""
    txns = []
    headers = list(rows[0].keys()) if rows else []
    h_lower = [h.lower() for h in headers]

    # Find date column
    date_col = None
    for h in headers:
        if h.lower() in ("date", "transaction date", "txn date", "posted date"):
            date_col = h
            break

    # Find amount column(s)
    amount_col = None
    debit_col = None
    credit_col = None
    for h in headers:
        hl = h.lower()
        if hl in ("amount", "value", "sum"):
            amount_col = h
        elif hl in ("debit", "debit amount", "paid out", "money out"):
            debit_col = h
        elif hl in ("credit", "credit amount", "paid in", "money in"):
            credit_col = h

    # Find description column
    desc_col = None
    for h in headers:
        if h.lower() in ("description", "memo", "narrative", "details",
                          "transaction description", "name"):
            desc_col = h
            break

    for i, row in enumerate(rows):
        if amount_col:
            amount = parse_amount(row.get(amount_col, "0"))
        elif debit_col or credit_col:
            debit = parse_amount(row.get(debit_col, "0")) if debit_col else 0
            credit = parse_amount(row.get(credit_col, "0")) if credit_col else 0
            amount = credit if credit > 0 else -debit
        else:
            continue

        txn = NormalisedTransaction(
            date=parse_date(row.get(date_col, "")) if date_col else "",
            description=row.get(desc_col, "") if desc_col else "",
            amount=amount,
            direction="in" if amount > 0 else "out",
            type=detect_transaction_type(row.get(desc_col, "") if desc_col else ""),
            source_file=source,
            source_line=i + 2,
            raw_data=dict(row),
        )
        txns.append(txn)

    return txns


# ========================================================================
# CRYPTO IMPORTERS
# ========================================================================

def import_coinbase(rows: List[Dict], source: str = "") -> List[NormalisedCryptoTrade]:
    """Import Coinbase CSV export."""
    trades = []
    for row in rows:
        action_raw = row.get("Transaction Type", row.get("Type", "")).lower()
        action_map = {
            "buy": "buy", "sell": "sell", "send": "transfer_out",
            "receive": "transfer_in", "convert": "swap",
            "staking reward": "staking", "reward": "staking",
        }
        action = action_map.get(action_raw, action_raw)

        trade = NormalisedCryptoTrade(
            date=parse_date(row.get("Timestamp", row.get("Date", ""))),
            asset=row.get("Asset", row.get("Currency", "")),
            action=action,
            quantity=parse_amount(row.get("Quantity Transacted",
                                          row.get("Quantity", "0"))),
            price_gbp=parse_amount(row.get("Total (inclusive of fees and/or spread)",
                                            row.get("Subtotal", "0"))),
            fee_gbp=parse_amount(row.get("Fees and/or Spread",
                                          row.get("Fees", "0"))),
            exchange="Coinbase",
            notes=row.get("Notes", ""),
            raw_data=dict(row),
        )
        trades.append(trade)
    return trades


def import_binance(rows: List[Dict], source: str = "") -> List[NormalisedCryptoTrade]:
    """Import Binance CSV export."""
    trades = []
    for row in rows:
        operation = row.get("Operation", row.get("Type", "")).lower()
        action_map = {
            "buy": "buy", "sell": "sell", "deposit": "transfer_in",
            "withdraw": "transfer_out", "staking rewards": "staking",
            "distribution": "airdrop",
        }
        action = action_map.get(operation, operation)

        trade = NormalisedCryptoTrade(
            date=parse_date(row.get("UTC_Time", row.get("Date", ""))),
            asset=row.get("Coin", row.get("Asset", "")),
            action=action,
            quantity=parse_amount(row.get("Change", row.get("Amount", "0"))),
            price_gbp=parse_amount(row.get("Realized_Amount_For_Primary_Asset",
                                            row.get("Total", "0"))),
            fee_gbp=parse_amount(row.get("Fee", "0")),
            exchange="Binance",
            raw_data=dict(row),
        )
        trades.append(trade)
    return trades


# ========================================================================
# MASTER IMPORT ENGINE
# ========================================================================

class HNCImportEngine:
    """
    Master file import engine.

    Reads CSV/Excel files, auto-detects format, normalises data.

    Usage:
        importer = HNCImportEngine()
        result = importer.import_file("bank_statement.csv")
        # result.transactions → list of normalised bank transactions
        # result.crypto_trades → list of normalised crypto trades
    """

    def __init__(self):
        self.results: List[ImportResult] = []

    def import_file(self, filepath: str, force_format: str = "") -> ImportResult:
        """Import a single file. Auto-detects format unless forced."""
        result = ImportResult(source_file=filepath)
        path = Path(filepath)

        if not path.exists():
            result.errors.append(f"File not found: {filepath}")
            return result

        suffix = path.suffix.lower()

        try:
            if suffix == ".csv":
                result = self._import_csv(filepath, force_format)
            elif suffix in (".xlsx", ".xls"):
                result = self._import_excel(filepath, force_format)
            elif suffix == ".tsv":
                result = self._import_csv(filepath, force_format, delimiter="\t")
            else:
                result.errors.append(f"Unsupported file type: {suffix}")
        except Exception as e:
            result.errors.append(f"Import error: {str(e)}")

        self.results.append(result)
        return result

    def import_csv_string(self, csv_text: str, filename: str = "upload.csv",
                           force_format: str = "") -> ImportResult:
        """Import from a CSV string (for web uploads). Handles UTF-16 artefacts."""
        # Strip null bytes (UTF-16 artefacts if raw bytes were decoded loosely)
        clean = csv_text.replace("\x00", "")

        reader = csv.DictReader(io.StringIO(clean))
        rows = list(reader)
        headers = reader.fieldnames or []

        # Clean header names
        headers = [h.strip() for h in headers]
        cleaned_rows = []
        for row in rows:
            cleaned = {k.strip(): v.strip() if isinstance(v, str) else v
                       for k, v in row.items()}
            cleaned_rows.append(cleaned)

        fmt = force_format or detect_bank_format(headers)
        result = self._process_rows(cleaned_rows, headers, fmt, filename)
        self.results.append(result)
        return result

    def _import_csv(self, filepath: str, force_format: str = "",
                     delimiter: str = ",") -> ImportResult:
        """Read and import a CSV file. Handles UTF-8, UTF-8-BOM, and UTF-16."""
        # Try multiple encodings — some bank exports use UTF-16
        raw = None
        for enc in ("utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "latin-1"):
            try:
                with open(filepath, "r", encoding=enc) as f:
                    raw = f.read()
                break
            except (UnicodeDecodeError, UnicodeError):
                continue

        if raw is None:
            result = ImportResult(source_file=filepath)
            result.errors.append("Could not decode file with any known encoding")
            return result

        # Strip null bytes that sometimes survive UTF-16 decode
        raw = raw.replace("\x00", "")

        # Parse CSV from the decoded string
        sio = io.StringIO(raw)
        try:
            dialect = csv.Sniffer().sniff(sio.read(4096))
            sio.seek(0)
            reader = csv.DictReader(sio, dialect=dialect)
        except csv.Error:
            sio.seek(0)
            reader = csv.DictReader(sio, delimiter=delimiter)

        rows = list(reader)
        headers = reader.fieldnames or []

        # Clean header names (strip whitespace from UTF-16 artefacts)
        headers = [h.strip() for h in headers]
        cleaned_rows = []
        for row in rows:
            cleaned = {k.strip(): v.strip() if isinstance(v, str) else v
                       for k, v in row.items()}
            cleaned_rows.append(cleaned)

        fmt = force_format or detect_bank_format(headers)
        return self._process_rows(cleaned_rows, headers, fmt, filepath)

    def _import_excel(self, filepath: str, force_format: str = "") -> ImportResult:
        """Read and import an Excel file."""
        try:
            import pandas as pd
        except ImportError:
            result = ImportResult(source_file=filepath)
            result.errors.append("pandas not installed — cannot read Excel files")
            return result

        df = pd.read_excel(filepath)
        headers = list(df.columns)
        rows = df.to_dict("records")

        # Clean NaN values
        for row in rows:
            for k, v in row.items():
                if pd.isna(v):
                    row[k] = ""

        fmt = force_format or detect_bank_format(headers)
        return self._process_rows(rows, headers, fmt, filepath)

    def _process_rows(self, rows: List[Dict], headers: List[str],
                       fmt: str, source: str) -> ImportResult:
        """Process rows using the detected format."""
        result = ImportResult(
            source_file=source,
            format_detected=fmt,
            rows_read=len(rows),
        )

        # Route to correct importer
        importers = {
            "barclays": import_barclays,
            "hsbc": import_hsbc,
            "lloyds": import_lloyds,
            "natwest": import_natwest,
            "revolut": import_revolut,
            "fintech_card": import_fintech_card,
            "starling": import_starling,
            "monzo": import_monzo,
            "generic": import_generic,
        }

        crypto_importers = {
            "coinbase": import_coinbase,
            "binance": import_binance,
        }

        if fmt in crypto_importers:
            trades = crypto_importers[fmt](rows, source)
            result.crypto_trades = trades
            result.rows_imported = len(trades)
        elif fmt in importers:
            txns = importers[fmt](rows, source)
            result.transactions = txns
            result.rows_imported = len(txns)
        elif fmt == "unknown":
            result.warnings.append(
                "Could not detect bank format. Trying generic importer.")
            txns = import_generic(rows, source)
            result.transactions = txns
            result.rows_imported = len(txns)
            result.format_detected = "generic (fallback)"
        else:
            result.errors.append(f"Unsupported format: {fmt}")
            return result

        result.rows_skipped = result.rows_read - result.rows_imported

        # Calculate totals and date range
        if result.transactions:
            dates = [t.date for t in result.transactions if t.date]
            if dates:
                result.date_range = (min(dates), max(dates))
            result.total_in = sum(t.amount for t in result.transactions if t.amount > 0)
            result.total_out = sum(abs(t.amount) for t in result.transactions if t.amount < 0)

        return result

    def get_bank_transactions(self) -> List[Dict]:
        """Get all imported bank transactions as dicts for HNCQueen."""
        all_txns = []
        for r in self.results:
            for t in r.transactions:
                all_txns.append(t.to_dict())
        return all_txns

    def get_crypto_trades(self) -> List[Dict]:
        """Get all imported crypto trades as dicts for HNCQueen."""
        all_trades = []
        for r in self.results:
            for t in r.crypto_trades:
                all_trades.append(t.to_dict())
        return all_trades

    def print_import_summary(self, result: ImportResult = None) -> str:
        """Print import summary."""
        results = [result] if result else self.results
        lines = [
            "=" * 60,
            "  HNC IMPORT — File Import Summary",
            "=" * 60,
        ]

        for r in results:
            lines.append(f"\n  File: {r.source_file}")
            lines.append(f"  Format: {r.format_detected}")
            lines.append(f"  Rows read: {r.rows_read}")
            lines.append(f"  Imported: {r.rows_imported}")
            lines.append(f"  Skipped: {r.rows_skipped}")
            if r.date_range[0]:
                lines.append(f"  Date range: {r.date_range[0]} to {r.date_range[1]}")
            if r.total_in:
                lines.append(f"  Total in:  £{r.total_in:>12,.2f}")
                lines.append(f"  Total out: £{r.total_out:>12,.2f}")
            if r.crypto_trades:
                lines.append(f"  Crypto trades: {len(r.crypto_trades)}")
            if r.errors:
                for e in r.errors:
                    lines.append(f"  [ERROR] {e}")
            if r.warnings:
                for w in r.warnings:
                    lines.append(f"  [WARN] {w}")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)


# ========================================================================
# TEST
# ========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("HNC IMPORT — File Import Engine Test")
    print("=" * 60)

    importer = HNCImportEngine()

    # ---- Test 1: HSBC format ----
    print("\n--- TEST 1: HSBC CSV ---")
    hsbc_csv = """Date,Type,Description,Paid out,Paid in,Balance
15/01/2026,DD,SIMPLY BUSINESS INSURANCE,150.00,,22350.00
18/01/2026,VIS,TRAVIS PERKINS,4500.00,,17850.00
20/01/2026,BAC,MRS JONES,,8500.00,26350.00
25/01/2026,VIS,SHELL,45.50,,26304.50
28/01/2026,BAC,MR DAVIES,,6200.00,32504.50
01/02/2026,ATM,CASH WITHDRAWAL,300.00,,32204.50"""

    result = importer.import_csv_string(hsbc_csv, "john_hsbc_jan.csv")
    print(importer.print_import_summary(result))

    for t in result.transactions:
        d = t.to_dict()
        print(f"  {d['date']}  {d['direction']:>3}  £{d['amount']:>10,.2f}  {d['description'][:30]}")

    # ---- Test 2: Coinbase format ----
    print("\n--- TEST 2: Coinbase CSV ---")
    coinbase_csv = """Timestamp,Transaction Type,Asset,Quantity Transacted,Spot Price at Transaction,Subtotal,Total (inclusive of fees and/or spread),Fees and/or Spread,Notes
2026-01-09T10:30:00Z,Buy,BTC,0.015,33000.00,495.00,500.00,5.00,
2026-02-20T14:15:00Z,Buy,BTC,0.010,34500.00,345.00,350.00,5.00,
2026-03-15T09:00:00Z,Sell,BTC,0.020,36000.00,720.00,715.00,5.00,"""

    result2 = importer.import_csv_string(coinbase_csv, "john_coinbase.csv")
    print(importer.print_import_summary(result2))

    for t in result2.crypto_trades:
        d = t.to_dict()
        print(f"  {d['date']}  {d['action']:>4}  {d['quantity']:.6f} {d['asset']}  "
              f"£{d['price_gbp']:>8,.2f}  fee £{d['fee_gbp']:.2f}")

    # ---- Test 3: Lloyds format ----
    print("\n--- TEST 3: Lloyds CSV ---")
    lloyds_csv = """Transaction Date,Transaction Type,Sort Code,Account Number,Transaction Description,Debit Amount,Credit Amount,Balance
15/01/2026,DPC,12-34-56,12345678,SHELL FUEL,45.50,,26304.50
20/01/2026,BGC,12-34-56,12345678,MRS JONES KITCHEN,,8500.00,34804.50
25/01/2026,DPC,12-34-56,12345678,TRAVIS PERKINS,2800.00,,32004.50"""

    result3 = importer.import_csv_string(lloyds_csv, "john_lloyds.csv")
    print(importer.print_import_summary(result3))

    # ---- Test 4: Generic CSV ----
    print("\n--- TEST 4: Generic CSV ---")
    generic_csv = """Date,Description,Amount
2026-01-15,Mrs Jones Kitchen,8500.00
2026-01-18,Travis Perkins,-4500.00
2026-01-20,Screwfix tools,-350.00
2026-01-28,Mr Davies Bathroom,6200.00"""

    result4 = importer.import_csv_string(generic_csv, "unknown_bank.csv")
    print(importer.print_import_summary(result4))

    # ---- Test 5: Get combined output for Queen ----
    print("\n--- TEST 5: Combined Output ---")
    bank_txns = importer.get_bank_transactions()
    crypto_trades = importer.get_crypto_trades()
    print(f"  Total bank transactions: {len(bank_txns)}")
    print(f"  Total crypto trades:     {len(crypto_trades)}")
    print(f"  Ready for HNCQueen.process()")

    print("\n" + "=" * 60)
    print("Import engine verified. Every format normalised.")
    print("=" * 60)
