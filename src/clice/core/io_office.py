"""Real Office (.xlsx, .docx, .pptx) and lightweight (.csv, .md, .txt, .json) I/O."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Spreadsheets (.xlsx, .csv)
# ---------------------------------------------------------------------------

def load_spreadsheet(path: Path, min_rows: int = 20, min_cols: int = 10) -> list[list[str]]:
    """Load a .xlsx or .csv file into a 2D list of strings."""
    suffix = path.suffix.lower()
    rows: list[list[str]] = []

    if suffix == ".xlsx":
        import openpyxl

        wb = openpyxl.load_workbook(path, data_only=False)
        ws = wb.active
        for row in ws.iter_rows(values_only=True):
            rows.append(["" if v is None else str(v) for v in row])
        wb.close()
    elif suffix in (".csv", ".tsv"):
        delimiter = "\t" if suffix == ".tsv" else ","
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f, delimiter=delimiter)
            rows = [list(r) for r in reader]
    else:
        raise ValueError(f"Unsupported spreadsheet format: {suffix}")

    max_cols = max([min_cols] + [len(r) for r in rows])
    num_rows = max(min_rows, len(rows))
    grid: list[list[str]] = []
    for r in range(num_rows):
        if r < len(rows):
            padded = rows[r] + [""] * (max_cols - len(rows[r]))
            grid.append(padded)
        else:
            grid.append([""] * max_cols)
    return grid


def save_spreadsheet(path: Path, grid: list[list[str]]) -> None:
    """Save a 2D list of strings to .xlsx or .csv."""
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()

    # Trim completely empty trailing rows/cols
    last_row = 0
    last_col = 0
    for r_idx, row in enumerate(grid):
        for c_idx, val in enumerate(row):
            if str(val).strip() != "":
                last_row = max(last_row, r_idx + 1)
                last_col = max(last_col, c_idx + 1)
    trimmed = [row[: max(1, last_col)] for row in grid[: max(1, last_row)]]

    if suffix == ".xlsx":
        import openpyxl

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        for r_idx, row in enumerate(trimmed, start=1):
            for c_idx, val in enumerate(row, start=1):
                if isinstance(val, str) and not val.startswith("="):
                    try:
                        num = float(val)
                        ws.cell(r_idx, c_idx, int(num) if num.is_integer() else num)
                        continue
                    except ValueError:
                        pass
                ws.cell(r_idx, c_idx, val)
        wb.save(path)
    elif suffix in (".csv", ".tsv"):
        delimiter = "\t" if suffix == ".tsv" else ","
        with path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerows(trimmed)
    else:
        raise ValueError(f"Unsupported spreadsheet format: {suffix}")


# ---------------------------------------------------------------------------
# Documents (.docx, .md, .txt)
# ---------------------------------------------------------------------------

def load_document(path: Path) -> str:
    """Load a .docx, .md, or .txt document into a Markdown-friendly string."""
    suffix = path.suffix.lower()
    if suffix == ".docx":
        from docx import Document

        doc = Document(str(path))
        lines: list[str] = []
        for para in doc.paragraphs:
            style_name = (para.style.name or "").lower() if para.style else ""
            text = para.text
            if style_name.startswith("heading 1"):
                lines.append(f"# {text}")
            elif style_name.startswith("heading 2"):
                lines.append(f"## {text}")
            elif style_name.startswith("heading 3"):
                lines.append(f"### {text}")
            elif "list bullet" in style_name:
                lines.append(f"- {text}")
            elif "list number" in style_name:
                lines.append(f"1. {text}")
            else:
                lines.append(text)
        return "\n".join(lines)
    return path.read_text(encoding="utf-8")


def save_document(path: Path, content: str) -> None:
    """Save text/markdown content to .docx, .md, or .txt."""
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix == ".docx":
        from docx import Document

        doc = Document()
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("### "):
                doc.add_heading(stripped[4:], level=3)
            elif stripped.startswith("## "):
                doc.add_heading(stripped[3:], level=2)
            elif stripped.startswith("# "):
                doc.add_heading(stripped[2:], level=1)
            elif stripped.startswith("- ") or stripped.startswith("* "):
                doc.add_paragraph(stripped[2:], style="List Bullet")
            else:
                doc.add_paragraph(line)
        doc.save(str(path))
    else:
        path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Presentations (.pptx, .json, .md)
# ---------------------------------------------------------------------------

@dataclass
class SlideData:
    title: str
    body: str
    notes: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"title": self.title, "body": self.body, "notes": self.notes}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SlideData":
        return cls(
            title=str(data.get("title", "Untitled Slide")),
            body=str(data.get("body", "")),
            notes=str(data.get("notes", "")),
        )


def load_presentation(path: Path) -> list[SlideData]:
    """Load a .pptx, .json, or .md slide deck."""
    suffix = path.suffix.lower()
    if suffix == ".pptx":
        from pptx import Presentation

        prs = Presentation(str(path))
        slides: list[SlideData] = []
        for idx, slide in enumerate(prs.slides, start=1):
            title = ""
            body_parts: list[str] = []
            if slide.shapes.title and slide.shapes.title.text:
                title = slide.shapes.title.text.strip()
            for shape in slide.shapes:
                if shape == slide.shapes.title:
                    continue
                if shape.has_text_frame:
                    txt = shape.text_frame.text.strip()
                    if txt:
                        body_parts.append(txt)
            notes = ""
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                notes = slide.notes_slide.notes_text_frame.text.strip()
            slides.append(
                SlideData(
                    title=title or f"Slide {idx}",
                    body="\n".join(body_parts),
                    notes=notes,
                )
            )
        return slides or [SlideData(title="Slide 1", body="")]
    elif suffix == ".json":
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            return [SlideData.from_dict(s) for s in raw]
        return [SlideData.from_dict(s) for s in raw.get("slides", [])]
    elif suffix == ".md":
        text = path.read_text(encoding="utf-8")
        chunks = [c.strip() for c in text.split("\n---\n") if c.strip()]
        slides = []
        for idx, chunk in enumerate(chunks, start=1):
            lines = chunk.splitlines()
            title = lines[0].lstrip("# ").strip() if lines else f"Slide {idx}"
            body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
            slides.append(SlideData(title=title, body=body))
        return slides or [SlideData(title="Slide 1", body="")]
    else:
        raise ValueError(f"Unsupported presentation format: {suffix}")


def save_presentation(path: Path, slides: list[SlideData]) -> None:
    """Save a slide deck to .pptx, .json, or .md."""
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix == ".pptx":
        from pptx import Presentation

        prs = Presentation()
        for idx, s in enumerate(slides):
            layout_idx = 0 if idx == 0 else 1
            layout = prs.slide_layouts[min(layout_idx, len(prs.slide_layouts) - 1)]
            slide = prs.slides.add_slide(layout)
            if slide.shapes.title:
                slide.shapes.title.text = s.title
            if len(slide.placeholders) > 1:
                slide.placeholders[1].text = s.body
            if s.notes:
                notes_slide = slide.notes_slide
                notes_slide.notes_text_frame.text = s.notes
        prs.save(str(path))
    elif suffix == ".json":
        payload = {"slides": [s.to_dict() for s in slides]}
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    elif suffix == ".md":
        parts = [f"# {s.title}\n\n{s.body}" for s in slides]
        path.write_text("\n\n---\n\n".join(parts), encoding="utf-8")
    else:
        raise ValueError(f"Unsupported presentation format: {suffix}")
