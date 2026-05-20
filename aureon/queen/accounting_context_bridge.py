"""
AccountingContextBridge - wire accounting artifacts into Queen + Vault context.
===========================================================================

The accounting system writes useful artifacts (filing packs, gateway summaries,
exchange archive coverage, year CSVs), but Queen prompt grounding historically
did not read them directly.

This bridge provides one cached, structured snapshot that can be:

1) read by MeaningResolver for accounting/tax prompts, and
2) ingested into the Vault as compact cards so other subsystems can reuse it.

No external dependencies; pure stdlib.
"""

from __future__ import annotations

import csv
import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("aureon.queen.accounting_context_bridge")


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


class AccountingContextBridge:
    """Load + cache accounting context and optionally mirror it into Vault."""

    def __init__(self, repo_root: Optional[str] = None):
        self.repo_root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[2]
        self._lock = threading.RLock()
        self._cached_context: Dict[str, Any] = {}
        self._cached_signature: Tuple[Tuple[str, float, int], ...] = tuple()
        self._last_vault_signature: str = ""

    def _paths(self) -> Dict[str, Path]:
        return {
            "filing_pack": self.repo_root / "Kings_Accounting_Suite" / "output" / "final" / "hmrc_filing_pack_2024_2025.json",
            "gateway_summary": self.repo_root / "Kings_Accounting_Suite" / "output" / "gateway" / "filling_prep_summary_2024_2025.json",
            "exchange_coverage": self.repo_root / "data" / "exchange_account_archives" / "latest" / "coverage_report.json",
            "year_2024_25_csv": self.repo_root / "uploads" / "Statement_06_Apr_2024_05_Apr_2025.csv",
            "year_2025_26_csv": self.repo_root / "uploads" / "Statement_06_Apr_2025_05_Apr_2026.csv",
            "full_period_csv": self.repo_root / "uploads" / "Statement_31_Aug_2024_10_Apr_2026.csv",
        }

    @staticmethod
    def _signature_for(paths: Dict[str, Path]) -> Tuple[Tuple[str, float, int], ...]:
        parts: List[Tuple[str, float, int]] = []
        for key, path in sorted(paths.items()):
            if not path.exists():
                parts.append((key, -1.0, -1))
                continue
            st = path.stat()
            parts.append((key, float(st.st_mtime), int(st.st_size)))
        return tuple(parts)

    @staticmethod
    def _read_json(path: Path) -> Dict[str, Any]:
        try:
            if not path.exists():
                return {}
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.debug("accounting bridge json read failed %s: %s", path, e)
            return {}

    @staticmethod
    def _csv_rows(path: Path) -> int:
        try:
            if not path.exists():
                return 0
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.reader(f)
                # header + rows
                n = sum(1 for _ in reader)
            return max(0, n - 1)
        except Exception as e:
            logger.debug("accounting bridge csv read failed %s: %s", path, e)
            return 0

    @staticmethod
    def _extract_year_metrics(year_blob: Dict[str, Any]) -> Dict[str, Any]:
        boxes = year_blob.get("sa103_boxes") or {}
        turnover = _to_float(boxes.get("9"))
        allowable = _to_float(boxes.get("21"))
        if allowable <= 0.0:
            allowable = sum(
                _to_float(boxes.get(str(i)))
                for i in (10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20)
            )
        profit = _to_float(boxes.get("22"))
        if abs(profit) < 1e-9 and turnover > 0.0:
            profit = turnover - allowable
        filing_deadlines = year_blob.get("filing_deadlines") or {}
        return {
            "turnover": round(turnover, 2),
            "allowable_expenses": round(allowable, 2),
            "net_profit": round(profit, 2),
            "filing_deadlines": filing_deadlines,
        }

    @staticmethod
    def _build_prompt_lines(context: Dict[str, Any]) -> List[str]:
        lines: List[str] = []
        generated = context.get("generated_at")
        if generated:
            lines.append(f"Accounting snapshot: {generated}")
        years = context.get("tax_years") or {}
        for year in ("2024/25", "2025/26"):
            data = years.get(year) or {}
            if not data:
                continue
            lines.append(
                f"{year}: turnover GBP {data.get('turnover', 0):,.2f}, "
                f"expenses GBP {data.get('allowable_expenses', 0):,.2f}, "
                f"net GBP {data.get('net_profit', 0):,.2f}, "
                f"rows={data.get('bank_rows', 0)}"
            )
        venue = context.get("exchange_venues") or {}
        if venue:
            chunks: List[str] = []
            for name in sorted(venue.keys()):
                v = venue.get(name) or {}
                chunks.append(
                    f"{name}:{int(v.get('trade_count', 0))}t/{int(v.get('symbol_count', 0))}s"
                )
            lines.append("Exchange coverage: " + ", ".join(chunks))
        submit = context.get("submission_status") or {}
        if submit:
            done = bool(submit.get("hmrc_api_submitted"))
            reason = str(submit.get("reason", "")).strip()
            if reason:
                lines.append(f"HMRC submitted={done}; {reason}")
            else:
                lines.append(f"HMRC submitted={done}")
        return lines

    def load_context(self, force: bool = False) -> Dict[str, Any]:
        with self._lock:
            paths = self._paths()
            signature = self._signature_for(paths)
            if not force and self._cached_context and signature == self._cached_signature:
                return dict(self._cached_context)

            filing_pack = self._read_json(paths["filing_pack"])
            gateway_summary = self._read_json(paths["gateway_summary"])
            exchange_coverage = self._read_json(paths["exchange_coverage"])

            years_out: Dict[str, Dict[str, Any]] = {}
            for year in ("2024/25", "2025/26"):
                year_blob = (filing_pack.get("tax_years") or {}).get(year) or {}
                metrics = self._extract_year_metrics(year_blob) if year_blob else {
                    "turnover": 0.0,
                    "allowable_expenses": 0.0,
                    "net_profit": 0.0,
                    "filing_deadlines": {},
                }
                gw = (gateway_summary.get(year) or {})
                import_summary = gw.get("import_summary") or {}
                metrics["bank_rows"] = int(import_summary.get("bank_transactions", 0))
                metrics["gateway_status"] = gw.get("status", "")
                metrics["gateway_warnings"] = list(gw.get("warnings") or [])
                years_out[year] = metrics

            context: Dict[str, Any] = {
                "generated_at": filing_pack.get("generated_at") or exchange_coverage.get("generated_at_utc") or "",
                "repo_root": str(self.repo_root),
                "tax_years": years_out,
                "exchange_venues": (exchange_coverage.get("venue_summary") or {}),
                "submission_status": filing_pack.get("submission_status") or {},
                "source_files": {k: str(v) for k, v in paths.items() if v.exists()},
                "csv_rows": {
                    "2024/25": self._csv_rows(paths["year_2024_25_csv"]),
                    "2025/26": self._csv_rows(paths["year_2025_26_csv"]),
                    "full_period": self._csv_rows(paths["full_period_csv"]),
                },
            }
            context["prompt_lines"] = self._build_prompt_lines(context)

            self._cached_context = context
            self._cached_signature = signature
            return dict(context)

    @staticmethod
    def render_for_prompt(context: Dict[str, Any], max_chars: int = 420) -> str:
        lines = list(context.get("prompt_lines") or [])
        if not lines:
            return ""
        text = "Accounting context (vault + filing artifacts):\n" + "\n".join(f"  - {ln}" for ln in lines)
        if len(text) > max_chars:
            text = text[: max_chars - 3].rstrip() + "..."
        return text

    def ingest_to_vault(self, vault: Any, *, force: bool = False) -> int:
        if vault is None or not hasattr(vault, "ingest"):
            return 0
        context = self.load_context(force=force)
        if not context:
            return 0

        signature_payload = {
            "generated_at": context.get("generated_at"),
            "tax_years": context.get("tax_years"),
            "exchange_venues": context.get("exchange_venues"),
            "submission_status": context.get("submission_status"),
        }
        signature = json.dumps(signature_payload, sort_keys=True, separators=(",", ":"))
        if not force and signature == self._last_vault_signature:
            return 0

        ingested = 0
        try:
            vault.ingest(
                topic="accounting.context.summary",
                category="accounting_summary",
                payload={
                    "generated_at": context.get("generated_at"),
                    "prompt_lines": context.get("prompt_lines"),
                    "submission_status": context.get("submission_status"),
                    "csv_rows": context.get("csv_rows"),
                    "source_files": context.get("source_files"),
                },
            )
            ingested += 1
            for year, data in (context.get("tax_years") or {}).items():
                vault.ingest(
                    topic=f"accounting.tax_year.{year.replace('/', '-')}",
                    category="accounting_year",
                    payload={"tax_year": year, **data},
                )
                ingested += 1
            for venue, data in (context.get("exchange_venues") or {}).items():
                vault.ingest(
                    topic=f"accounting.exchange.{venue}",
                    category="exchange_archive",
                    payload={"venue": venue, **(data or {})},
                )
                ingested += 1
            self._last_vault_signature = signature
        except Exception as e:
            logger.debug("accounting bridge ingest_to_vault failed: %s", e)
        return ingested


_bridge_singleton: Optional[AccountingContextBridge] = None
_bridge_lock = threading.Lock()


def get_accounting_context_bridge() -> AccountingContextBridge:
    global _bridge_singleton
    with _bridge_lock:
        if _bridge_singleton is None:
            _bridge_singleton = AccountingContextBridge()
        return _bridge_singleton


def reset_accounting_context_bridge() -> None:
    global _bridge_singleton
    with _bridge_lock:
        _bridge_singleton = None


__all__ = [
    "AccountingContextBridge",
    "get_accounting_context_bridge",
    "reset_accounting_context_bridge",
]
