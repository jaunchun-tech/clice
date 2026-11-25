"""Round-trip tests for real Office formats (.xlsx, .docx, .pptx) and .csv/.md/.json."""

from pathlib import Path

from clice.core.io_office import (
    SlideData,
    load_document,
    load_presentation,
    load_spreadsheet,
    save_document,
    save_presentation,
    save_spreadsheet,
)


def test_xlsx_and_csv_roundtrip(tmp_path: Path):
    grid = [["Name", "Score"], ["Alice", "95"], ["Bob", "=B2-5"]]

    xlsx = tmp_path / "grades.xlsx"
    save_spreadsheet(xlsx, grid)
    loaded = load_spreadsheet(xlsx, min_rows=3, min_cols=2)
    assert loaded[0][:2] == ["Name", "Score"]
    assert loaded[1][:2] == ["Alice", "95"]
    assert loaded[2][:2] == ["Bob", "=B2-5"]

    csv_file = tmp_path / "grades.csv"
    save_spreadsheet(csv_file, grid)
    loaded_csv = load_spreadsheet(csv_file, min_rows=3, min_cols=2)
    assert loaded_csv[0][:2] == ["Name", "Score"]
    assert loaded_csv[2][:2] == ["Bob", "=B2-5"]


def test_docx_and_md_roundtrip(tmp_path: Path):
    content = "# Title\n\nHello Clice!\n- Bullet 1\n- Bullet 2"

    docx_file = tmp_path / "doc.docx"
    save_document(docx_file, content)
    loaded = load_document(docx_file)
    assert "# Title" in loaded
    assert "Hello Clice!" in loaded
    assert "- Bullet 1" in loaded

    md_file = tmp_path / "doc.md"
    save_document(md_file, content)
    assert load_document(md_file) == content


def test_pptx_and_json_roundtrip(tmp_path: Path):
    slides = [
        SlideData(title="Intro", body="Welcome to Clice", notes="Speaker note 1"),
        SlideData(title="Agenda", body="- Sheets\n- Docs\n- Slides"),
    ]

    pptx_file = tmp_path / "deck.pptx"
    save_presentation(pptx_file, slides)
    loaded = load_presentation(pptx_file)
    assert len(loaded) == 2
    assert loaded[0].title == "Intro"
    assert "Welcome to Clice" in loaded[0].body
    assert loaded[0].notes == "Speaker note 1"

    json_file = tmp_path / "deck.json"
    save_presentation(json_file, slides)
    loaded_json = load_presentation(json_file)
    assert len(loaded_json) == 2
    assert loaded_json[1].title == "Agenda"
