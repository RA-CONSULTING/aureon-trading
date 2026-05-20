"""
Build an accounts pack for an arbitrary accounting period by reusing the existing
HNC Gateway pipeline, then merge the generated PDFs into a single file and place
it on the user's Desktop.

This is intentionally small and non-invasive: it does not change core pipeline
logic, it only supplies a custom reporting period label (supported by the
gateway profile).

Usage (from repo root):
  .venv\\Scripts\\python.exe Kings_Accounting_Suite\\tools\\build_period_accounts_pack.py
"""

from __future__ import annotations

import os
import sys
import shutil
import argparse
import json
import re
from dataclasses import asdict
from datetime import datetime, date
from pathlib import Path
from typing import List, Sequence


KAS_DIR = Path(__file__).resolve().parents[1]  # Kings_Accounting_Suite/
REPO_ROOT = KAS_DIR.parents[0]
TOOLS_DIR = KAS_DIR / "tools"
sys.path.insert(0, str(KAS_DIR))
sys.path.insert(0, str(TOOLS_DIR))

from core.hnc_gateway import HNCGateway, UserProfile  # noqa: E402
from combined_bank_data import combine_bank_data_for_period  # noqa: E402

ENTITY_NAME = "R&A Consulting and Brokerage Services Ltd"
PACK_TITLE = "R&A Consulting and Brokerage Accounts Pack"
PACK_BASENAME = "ra_consulting_and_brokerage_accounts_pack"


def _parse_iso_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def _make_cover_pdf(
    out_path: Path,
    *,
    title: str,
    entity: str,
    period_label: str,
    included_paths: List[Path],
) -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(out_path), pagesize=A4)
    w, h = A4

    y = h - 20 * mm
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, y, title)
    y -= 10 * mm

    c.setFont("Helvetica", 11)
    c.drawString(20 * mm, y, f"Entity: {entity}")
    y -= 6 * mm
    c.drawString(20 * mm, y, f"Period: {period_label}")
    y -= 10 * mm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y, "Included documents:")
    y -= 7 * mm

    c.setFont("Helvetica", 10)
    for p in included_paths:
        if y < 20 * mm:
            c.showPage()
            y = h - 20 * mm
            c.setFont("Helvetica", 10)
        c.drawString(23 * mm, y, f"- {p.name}")
        y -= 5.5 * mm

    c.setFont("Helvetica", 9)
    y = 15 * mm
    c.drawString(20 * mm, y, "Note: Final-ready local pack generated from repository data; manual submission only.")

    c.showPage()
    c.save()


def _merge_pdfs(output_path: Path, pdfs: List[Path]) -> None:
    from pypdf import PdfReader, PdfWriter

    writer = PdfWriter()
    for p in pdfs:
        reader = PdfReader(str(p))
        for page in reader.pages:
            writer.add_page(page)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as f:
        writer.write(f)


def _pack_basename(entity_name: str) -> str:
    if entity_name == ENTITY_NAME:
        return PACK_BASENAME
    slug = re.sub(r"[^a-z0-9]+", "_", entity_name.lower()).strip("_")
    return f"{slug or 'company'}_accounts_pack"


def _desktop_dir() -> Path:
    userprofile = Path(os.environ.get("USERPROFILE") or str(Path.home()))
    for candidate in (userprofile / "OneDrive" / "Desktop", Path.home() / "OneDrive" / "Desktop", Path(os.path.expanduser("~/Desktop"))):
        if candidate.exists():
            return candidate
    return Path(os.path.expanduser("~/Desktop"))


def build_period_accounts_pack(
    *,
    company_name: str = ENTITY_NAME,
    period_start: str = "2024-05-01",
    period_end: str = "2025-04-30",
    raw_data_roots: Sequence[str | Path] | None = None,
    include_default_roots: bool = True,
    output_dir: str | Path | None = None,
) -> dict:
    start_iso = period_start
    end_iso = period_end

    out_dir = Path(output_dir) if output_dir else (
        REPO_ROOT / "Kings_Accounting_Suite" / "output" / "gateway" / f"{start_iso}_to_{end_iso}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    combined = combine_bank_data_for_period(
        REPO_ROOT,
        start_iso,
        end_iso,
        raw_roots=raw_data_roots,
        include_default_roots=include_default_roots,
    )
    rows = combined.rows
    filtered_csv = combined.to_standard_csv()
    filtered_filename = f"Combined_Bank_Transactions_{start_iso}_{end_iso}.csv"
    combined_csv_path = out_dir / f"combined_bank_transactions_{start_iso}_to_{end_iso}.csv"
    combined_csv_path.write_text(combined.to_full_csv(), encoding="utf-8")

    # Company profile: keep minimal fields so gateway runs; HMRC submission is skipped.
    profile = UserProfile(
        full_name=company_name,
        trading_as="",
        business_type="limited",
        trade_sector="brokerage",
        trade_description="Consulting and brokerage services",
        tax_year="2024/25",
        accounting_year_end=end_iso,
        accounting_period_start=start_iso,
        accounting_period_end=end_iso,
    )

    gateway = HNCGateway(profile, output_dir=str(out_dir))
    result = gateway.run(
        csv_strings=[(filtered_csv, filtered_filename)],
        skip_hmrc=True,
        generate_documents=True,
    )
    if result.status != "completed":
        raise RuntimeError(f"Gateway failed: {result.error}")

    # Find the generated PDFs in this output dir.
    pnl_pdf = out_dir / "pnl.pdf"
    tax_pdf = out_dir / "tax_summary.pdf"
    if not pnl_pdf.exists() or not tax_pdf.exists():
        raise FileNotFoundError(f"Missing expected PDFs: {pnl_pdf} / {tax_pdf}")

    cover_pdf = out_dir / "cover.pdf"
    period_label = profile.reporting_period_label
    _make_cover_pdf(
        cover_pdf,
        title=PACK_TITLE if company_name == ENTITY_NAME else f"{company_name} Accounts Pack",
        entity=profile.entity_display,
        period_label=period_label,
        included_paths=[pnl_pdf, tax_pdf],
    )

    merged_pdf = out_dir / f"{_pack_basename(company_name)}_{start_iso}_to_{end_iso}.pdf"
    _merge_pdfs(merged_pdf, [cover_pdf, pnl_pdf, tax_pdf])

    # Copy final PDF to Desktop.
    desktop = _desktop_dir()
    desktop.mkdir(parents=True, exist_ok=True)
    dest = desktop / merged_pdf.name
    if dest.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = desktop / f"{merged_pdf.stem}_{ts}{merged_pdf.suffix}"
    desktop_target = str(dest)
    try:
        shutil.copyfile(merged_pdf, dest)
    except PermissionError:
        desktop_target = ""

    # Also write a tiny machine-readable manifest next to the PDF in the repo.
    manifest = {
        "period_start": start_iso,
        "period_end": end_iso,
        "entity": profile.entity_display,
        "output_dir": str(out_dir),
        "generated_documents": result.documents,
        "merged_pdf": str(merged_pdf),
        "desktop_pdf": desktop_target,
        "rows_in_period": len(rows),
        "combined_bank_data": combined.to_summary(combined_csv_path),
        "raw_data_roots": [str(path) for path in raw_data_roots or []],
        "include_default_roots": include_default_roots,
        "profile": {k: v for k, v in asdict(profile).items() if k not in ("hmrc_client_secret",)},
    }
    (out_dir / "period_pack_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a final-ready accounts pack for a company period.")
    parser.add_argument("--company-name", default=ENTITY_NAME)
    parser.add_argument("--period-start", default="2024-05-01")
    parser.add_argument("--period-end", default="2025-04-30")
    parser.add_argument("--raw-data-dir", action="append", default=[])
    parser.add_argument("--no-default-roots", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = build_period_accounts_pack(
        company_name=args.company_name,
        period_start=args.period_start,
        period_end=args.period_end,
        raw_data_roots=args.raw_data_dir,
        include_default_roots=not args.no_default_roots,
    )
    dest = manifest.get("desktop_pdf") or manifest.get("merged_pdf")
    print(str(dest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
