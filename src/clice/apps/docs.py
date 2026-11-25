"""Clice Docs — Keyboard-First Terminal Word Processor with .docx/.md/.txt support."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Input, Markdown, Static, TextArea

from clice.core.config import add_recent_file
from clice.core.io_office import load_document, save_document

DEFAULT_DOC = """# Welcome to Clice Docs

Write rich documents right in your terminal with **live formatting preview** and real `.docx`, `.md`, and `.txt` support!

## Word-Standard Shortcuts
- `Ctrl+S` — Save document
- `Ctrl+O` — Open document
- `Ctrl+I` — Insert *italic*
- `Ctrl+K` — Insert code block
- `Ctrl+1` / `Ctrl+2` — Insert Heading 1 / Heading 2
"""


class DocsApp(Vertical):
    """Word processor with split-pane live preview, Word shortcuts, and .docx/.md/.txt I/O."""

    BINDINGS = [
        Binding("ctrl+s", "save_doc", "Save"),
        Binding("ctrl+o", "focus_path", "Open"),
        Binding("ctrl+i", "fmt_italic", "Italic"),
        Binding("ctrl+k", "fmt_code", "Code"),
        Binding("ctrl+1", "fmt_h1", "H1"),
        Binding("ctrl+2", "fmt_h2", "H2"),
    ]

    def __init__(self, initial_file: Path | None = None) -> None:
        super().__init__()
        self.current_file: Path | None = initial_file
        if initial_file and initial_file.exists():
            try:
                self.initial_text = load_document(initial_file)
            except Exception:
                self.initial_text = DEFAULT_DOC
        else:
            self.initial_text = DEFAULT_DOC

    def compose(self) -> ComposeResult:
        with Horizontal(classes="toolbar"):
            yield Static("[b #3b82f6][W] Clice Docs[/b #3b82f6]", classes="app-title")
            yield Input(
                value=str(self.current_file) if self.current_file else "document.docx",
                placeholder="Path (.docx, .md, .txt)",
                id="docs-path",
            )
            yield Button("Open (^O)", id="docs-open")
            yield Button("Save (^S)", variant="primary", id="docs-save")
            yield Button("H1", id="fmt-h1")
            yield Button("H2", id="fmt-h2")
            yield Button("Bold", id="fmt-bold")
            yield Button("Italic (^I)", id="fmt-italic")
            yield Button("List", id="fmt-list")
            yield Button("Code (^K)", id="fmt-code")

        with Horizontal(id="docs-split"):
            yield TextArea(self.initial_text, language="markdown", id="docs-editor")
            with VerticalScroll(id="docs-preview-scroll"):
                yield Markdown(self.initial_text, id="docs-preview")

        yield Static("", id="docs-status", classes="status-strip")

    def on_mount(self) -> None:
        self._update_stats()
        self.query_one("#docs-editor", TextArea).focus()

    def _update_stats(self) -> None:
        text = self.query_one("#docs-editor", TextArea).text
        words = len(text.split())
        chars = len(text)
        lines = len(text.splitlines()) or 1
        mins = max(1, round(words / 200)) if words else 0
        self.query_one("#docs-status", Static).update(
            f"Words: {words}  •  Chars: {chars}  •  Lines: {lines}  •  Read: ~{mins} min  •  Ctrl+S Save  •  Ctrl+O Open"
        )

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if event.text_area.id == "docs-editor":
            self.query_one("#docs-preview", Markdown).update(event.text_area.text)
            self._update_stats()

    def open_file(self, path: Path) -> None:
        content = load_document(path)
        self.current_file = path
        self.query_one("#docs-path", Input).value = str(path)
        editor = self.query_one("#docs-editor", TextArea)
        editor.text = content
        self.query_one("#docs-preview", Markdown).update(content)
        self._update_stats()
        add_recent_file(path, "docs")
        self.query_one("#docs-status", Static).update(f"Opened {path}")
        editor.focus()

    def _insert_snippet(self, snippet: str) -> None:
        editor = self.query_one("#docs-editor", TextArea)
        editor.insert(snippet)
        self.query_one("#docs-preview", Markdown).update(editor.text)
        self._update_stats()
        editor.focus()

    def action_fmt_h1(self) -> None:
        self._insert_snippet("\n# Heading 1\n")

    def action_fmt_h2(self) -> None:
        self._insert_snippet("\n## Heading 2\n")

    def action_fmt_italic(self) -> None:
        self._insert_snippet("*italic text*")

    def action_fmt_code(self) -> None:
        self._insert_snippet("\n```python\nprint('Hello Clice!')\n```\n")

    def action_focus_path(self) -> None:
        self.query_one("#docs-path", Input).focus()

    def action_save_doc(self) -> None:
        status = self.query_one("#docs-status", Static)
        raw = self.query_one("#docs-path", Input).value.strip()
        if not raw:
            status.update("Enter a file path (.docx, .md, .txt)")
            return
        try:
            p = Path(raw).expanduser()
            text = self.query_one("#docs-editor", TextArea).text
            save_document(p, text)
            self.current_file = p
            add_recent_file(p, "docs")
            status.update(f"Saved to {p}")
        except Exception as exc:
            status.update(f"Save error: {exc}")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "docs-path":
            try:
                self.open_file(Path(event.value.strip()).expanduser())
            except Exception as exc:
                self.query_one("#docs-status", Static).update(f"Open error: {exc}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        status = self.query_one("#docs-status", Static)
        if bid == "fmt-h1":
            self.action_fmt_h1()
        elif bid == "fmt-h2":
            self.action_fmt_h2()
        elif bid == "fmt-bold":
            self._insert_snippet("**bold text**")
        elif bid == "fmt-italic":
            self.action_fmt_italic()
        elif bid == "fmt-list":
            self._insert_snippet("\n- List item\n")
        elif bid == "fmt-code":
            self.action_fmt_code()
        elif bid == "docs-open":
            raw = self.query_one("#docs-path", Input).value.strip()
            if not raw:
                status.update("Enter a file path (.docx, .md, .txt)")
                return
            try:
                self.open_file(Path(raw).expanduser())
            except Exception as exc:
                status.update(f"Open error: {exc}")
        elif bid == "docs-save":
            self.action_save_doc()
