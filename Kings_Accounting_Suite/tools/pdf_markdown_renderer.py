"""Small Markdown-to-PDF renderer for accounting reports.

The accounting pack is generated as Markdown first. This module preserves the
human-readable structure in PDFs: headings, bullets, paragraphs, and pipe
tables become ReportLab flowables instead of being flattened into wrapped text.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Sequence


def render_markdown_pdf(path: str | Path, title: str, markdown_text: str | Sequence[str]) -> bool:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            KeepTogether,
            ListFlowable,
            ListItem,
            PageBreak,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except Exception:
        return False

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(markdown_text, str):
        lines = markdown_text.splitlines()
    else:
        lines = [str(line) for line in markdown_text]

    max_cols = max((len(split_table_row(line)) for line in lines if is_table_row(line)), default=0)
    pagesize = landscape(A4) if max_cols >= 5 else A4
    margin = 15 * mm
    doc = SimpleDocTemplate(
        str(output),
        pagesize=pagesize,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=18 * mm,
        bottomMargin=16 * mm,
        title=title,
    )

    width = doc.width
    styles = build_styles()
    story = []
    bullet_buffer: list[str] = []

    def flush_bullets() -> None:
        if not bullet_buffer:
            return
        items = [
            ListItem(Paragraph(markdown_inline(item), styles["Body"]), leftIndent=8, bulletColor=colors.HexColor("#30475E"))
            for item in bullet_buffer
        ]
        story.append(ListFlowable(items, bulletType="bullet", start="circle", leftIndent=12, bulletFontSize=6))
        story.append(Spacer(1, 3 * mm))
        bullet_buffer.clear()

    i = 0
    while i < len(lines):
        raw = lines[i].rstrip()
        stripped = raw.strip()
        if not stripped:
            flush_bullets()
            story.append(Spacer(1, 2 * mm))
            i += 1
            continue

        if is_table_row(stripped):
            flush_bullets()
            table_lines: list[str] = []
            while i < len(lines) and is_table_row(lines[i].strip()):
                table_lines.append(lines[i].strip())
                i += 1
            table = build_table(table_lines, width, styles, colors)
            if table is not None:
                story.append(table)
                story.append(Spacer(1, 4 * mm))
            continue

        if stripped.startswith("---PAGEBREAK---"):
            flush_bullets()
            story.append(PageBreak())
            i += 1
            continue

        if stripped.startswith("- "):
            bullet_buffer.append(stripped[2:].strip())
            i += 1
            continue

        flush_bullets()
        level = heading_level(stripped)
        if level:
            text = stripped[level + 1 :].strip()
            story.append(Paragraph(markdown_inline(text), styles[f"H{min(level, 3)}"]))
            story.append(Spacer(1, 2 * mm))
        else:
            story.append(Paragraph(markdown_inline(stripped), styles["Body"]))
            story.append(Spacer(1, 1.5 * mm))
        i += 1

    flush_bullets()
    if not story:
        story.append(Paragraph(markdown_inline(title), styles["H1"]))

    def on_page(canvas, doc_obj):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#5F6C7B"))
        canvas.drawString(doc_obj.leftMargin, 9 * mm, title[:95])
        canvas.drawRightString(doc_obj.pagesize[0] - doc_obj.rightMargin, 9 * mm, f"Page {doc_obj.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return True


def build_styles():
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

    base = getSampleStyleSheet()
    return {
        "H1": ParagraphStyle(
            "AccountingH1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=17,
            textColor=colors.HexColor("#17324D"),
            spaceAfter=4,
        ),
        "H2": ParagraphStyle(
            "AccountingH2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#1F4E5F"),
            spaceBefore=5,
            spaceAfter=3,
        ),
        "H3": ParagraphStyle(
            "AccountingH3",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=12,
            textColor=colors.HexColor("#30475E"),
            spaceBefore=4,
            spaceAfter=2,
        ),
        "Body": ParagraphStyle(
            "AccountingBody",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            alignment=TA_LEFT,
            wordWrap="CJK",
            splitLongWords=True,
        ),
        "TableCell": ParagraphStyle(
            "AccountingTableCell",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7,
            leading=8.4,
            wordWrap="CJK",
            splitLongWords=True,
        ),
        "TableHeader": ParagraphStyle(
            "AccountingTableHeader",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=8.4,
            textColor=colors.white,
            wordWrap="CJK",
            splitLongWords=True,
        ),
    }


def build_table(table_lines: list[str], available_width: float, styles: dict, colors_module):
    from reportlab.platypus import Paragraph, Table, TableStyle

    rows = [split_table_row(line) for line in table_lines]
    rows = [row for row in rows if row and not is_separator_row(row)]
    if not rows:
        return None
    col_count = max(len(row) for row in rows)
    normalised = [row + [""] * (col_count - len(row)) for row in rows]
    weighted = column_widths(normalised, available_width)
    table_data = []
    for row_index, row in enumerate(normalised):
        style = styles["TableHeader"] if row_index == 0 else styles["TableCell"]
        table_data.append([Paragraph(markdown_inline(cell), style) for cell in row])

    table = Table(table_data, colWidths=weighted, repeatRows=1 if len(table_data) > 1 else 0, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors_module.HexColor("#30475E")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors_module.white),
                ("GRID", (0, 0), (-1, -1), 0.35, colors_module.HexColor("#B8C2CC")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors_module.white, colors_module.HexColor("#F6F8FA")]),
            ]
        )
    )
    return table


def column_widths(rows: list[list[str]], available_width: float) -> list[float]:
    col_count = max(len(row) for row in rows)
    if col_count <= 0:
        return []
    scores: list[float] = []
    for index in range(col_count):
        values = [strip_markdown(row[index]) for row in rows if index < len(row)]
        max_len = max((len(value) for value in values), default=1)
        avg_len = sum(len(value) for value in values) / max(len(values), 1)
        scores.append(max(8.0, min(45.0, (max_len * 0.55) + (avg_len * 0.45))))
    total = sum(scores) or 1
    min_width = min(42.0, available_width / col_count)
    widths = [max(min_width, available_width * (score / total)) for score in scores]
    scale = available_width / sum(widths)
    return [width * scale for width in widths]


def is_table_row(line: str) -> bool:
    return line.startswith("|") and line.endswith("|") and line.count("|") >= 2


def split_table_row(line: str) -> list[str]:
    if not is_table_row(line):
        return []
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_separator_row(row: Sequence[str]) -> bool:
    return all(re.fullmatch(r":?-{2,}:?", cell.strip() or "---") for cell in row)


def heading_level(line: str) -> int:
    match = re.match(r"^(#{1,6})\s+", line)
    return len(match.group(1)) if match else 0


def markdown_inline(text: str) -> str:
    out = strip_markdown(text)
    out = html.escape(out)
    out = re.sub(r"`([^`]+)`", r"<font name=\"Courier\">\1</font>", out)
    return out.replace("&lt;br&gt;", "<br/>")


def strip_markdown(text: str) -> str:
    out = str(text).strip()
    out = out.replace("**", "")
    out = out.replace("__", "")
    out = out.replace("`", "")
    out = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", out)
    return out
