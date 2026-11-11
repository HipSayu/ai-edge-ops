"""Turns a markdown-ish report body into a Word (.docx) file: '#' headings, '- ' lists, '| a | b |' tables, **bold**."""

import re
import uuid
from datetime import UTC, datetime
from pathlib import Path

from docx import Document
from docx.shared import Pt

_BOLD = re.compile(r"\*\*(.+?)\*\*")
_RULE = re.compile(r"[|\s:-]+")


def _runs(paragraph, text: str) -> None:
    """Adds text to a paragraph, turning **bold** spans into bold runs."""
    for i, part in enumerate(_BOLD.split(text)):
        if part:
            paragraph.add_run(part).bold = bool(i % 2)


def _table(document, lines: list[str]) -> None:
    rows = [[c.strip() for c in line.strip("|").split("|")] for line in lines if not _RULE.fullmatch(line)]
    width = max(len(r) for r in rows)
    table = document.add_table(rows=len(rows), cols=width, style="Table Grid")
    for r, row in enumerate(rows):
        for c in range(width):
            cell = table.cell(r, c).paragraphs[0]
            _runs(cell, row[c] if c < len(row) else "")
            if r == 0:
                for run in cell.runs:
                    run.bold = True


def render_body(document, markdown: str) -> None:
    table: list[str] = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("|"):
            table.append(stripped)
            continue
        if table:
            _table(document, table)
            table = []
        if stripped.startswith(("- ", "* ")):
            _runs(document.add_paragraph(style="List Bullet"), stripped[2:])
        elif stripped.startswith("#"):
            level = min(len(stripped) - len(stripped.lstrip("#")) + 1, 3)
            document.add_heading(stripped.lstrip("# "), level=level)
        elif stripped:
            _runs(document.add_paragraph(), stripped)
    if table:
        _table(document, table)


def save_report(folder: Path, title: str, body_markdown: str, author: str) -> str:
    """Writes the report and returns its id (the file name without .docx)."""
    folder.mkdir(parents=True, exist_ok=True)
    report_id = uuid.uuid4().hex[:12]
    document = Document()
    document.styles["Normal"].font.name = "Calibri"
    document.styles["Normal"].font.size = Pt(11)
    document.add_heading(title, level=0)
    stamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    document.add_paragraph().add_run(f"Lập lúc {stamp} bởi {author}").italic = True
    render_body(document, body_markdown)
    document.save(folder / f"{report_id}.docx")
    return report_id
