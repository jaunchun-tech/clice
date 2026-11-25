"""Clice Docs — Feature-Rich Terminal Word Processor with Office Ribbon, Find/Replace & Native .md/.docx."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Input, Markdown, Static, TextArea

from clice.core.config import add_recent_file
from clice.core.file_picker import FilePickerModal
from clice.core.io_office import load_document, save_document

DEFAULT_DOC = """# Untitled Document

Start writing in **native Markdown** or open any `.md`, `.docx`, or `.txt` file using **File → Open (`Ctrl+O`)**!

## Features in the Top Ribbon
- **File**: New, Open File Browser, Save (`Ctrl+S`), Save As
- **Format**: Headings (`H1`–`H3`), **Bold**, *Italic*, ~~Strike~~, Blockquote, Code, Divider
- **Insert**: Tables, Checklists, Bullet & Numbered Lists, Links, Date/Time
- **Tools**: Find & Replace (`Ctrl+F`), Toggle Live Preview
"""


class DocsApp(Vertical):
    """Word processor with Office-style Ribbon, Find & Replace, File Picker, and native .md/.docx."""

    BINDINGS = [
        Binding("ctrl+s", "save_doc", "Save"),
        Binding("ctrl+o", "open_picker", "Open"),
        Binding("ctrl+f", "toggle_find", "Find/Replace"),
        Binding("ctrl+i", "fmt_italic", "Italic"),
        Binding("ctrl+k", "fmt_code", "Code"),
        Binding("ctrl+1", "fmt_h1", "H1"),
        Binding("ctrl+2", "fmt_h2", "H2"),
    ]

    def __init__(self, initial_file: Path | None = None) -> None:
        super().__init__()
        self.current_file: Path | None = initial_file
        self._active_ribbon = "format"
        self._show_preview = True
        self._show_find = False
        if initial_file and initial_file.exists():
            try:
                self.initial_text = load_document(initial_file)
            except Exception:
                self.initial_text = DEFAULT_DOC
        else:
            self.initial_text = DEFAULT_DOC

    def compose(self) -> ComposeResult:
        # Office-Style Top Ribbon
        with Vertical(classes="ribbon-container"):
            with Horizontal(classes="ribbon-tabs"):
                yield Static("[b #3b82f6][W] Clice Docs[/b #3b82f6]", classes="app-title")
                yield Button("File", id="rtab-file")
                yield Button("Format", id="rtab-format", classes="-active-tab")
                yield Button("Insert", id="rtab-insert")
                yield Button("Tools", id="rtab-tools")
                yield Static(
                    f"[dim]{self.current_file.name if self.current_file else 'Untitled.md'}[/dim]",
                    id="docs-file-label",
                )

            with Horizontal(classes="ribbon-tools", id="rbar-file"):
                yield Button("New", id="doc-new")
                yield Button("Open... (^O)", variant="primary", id="doc-open")
                yield Button("Save (^S)", variant="success", id="doc-save")
                yield Button("Save As...", id="doc-save-as")

            with Horizontal(classes="ribbon-tools", id="rbar-format"):
                yield Button("H1", id="fmt-h1")
                yield Button("H2", id="fmt-h2")
                yield Button("H3", id="fmt-h3")
                yield Button("Bold", id="fmt-bold")
                yield Button("Italic", id="fmt-italic")
                yield Button("Strike", id="fmt-strike")
                yield Button("Quote", id="fmt-quote")
                yield Button("`Code`", id="fmt-inline-code")
                yield Button("Code Block", id="fmt-code")
                yield Button("HR ---", id="fmt-hr")

            with Horizontal(classes="ribbon-tools", id="rbar-insert"):
                yield Button("Table", id="ins-table")
                yield Button("Checklist", id="ins-check")
                yield Button("Bullets", id="ins-bullets")
                yield Button("Numbered", id="ins-num")
                yield Button("Link", id="ins-link")
                yield Button("Date/Time", id="ins-date")

            with Horizontal(classes="ribbon-tools", id="rbar-tools"):
                yield Button("Find & Replace (^F)", variant="primary", id="tool-find")
                yield Button("Toggle Preview", id="tool-preview")
                yield Button("UPPERCASE", id="tool-upper")
                yield Button("Word Stats", id="tool-stats")

        # Optional Find & Replace Bar
        with Horizontal(classes="find-bar", id="docs-find-bar"):
            yield Input(placeholder="Find text...", id="docs-find-in")
            yield Input(placeholder="Replace with...", id="docs-replace-in")
            yield Button("Replace All", variant="warning", id="docs-replace-all")
            yield Button("Close", id="docs-find-close")

        with Horizontal(id="docs-split"):
            yield TextArea(self.initial_text, language="markdown", id="docs-editor")
            with VerticalScroll(id="docs-preview-scroll"):
                yield Markdown(self.initial_text, id="docs-preview")

        yield Static("", id="docs-status", classes="status-strip")

    def on_mount(self) -> None:
        self._switch_ribbon("format")
        self.query_one("#docs-find-bar", Horizontal).display = False
        self._update_stats()
        self.query_one("#docs-editor", TextArea).focus()

    def _switch_ribbon(self, tab: str) -> None:
        self._active_ribbon = tab
        for name in ("file", "format", "insert", "tools"):
            bar = self.query_one(f"#rbar-{name}", Horizontal)
            btn = self.query_one(f"#rtab-{name}", Button)
            bar.display = name == tab
            if name == tab:
                btn.add_class("-active-tab")
            else:
                btn.remove_class("-active-tab")

    def _update_stats(self) -> None:
        text = self.query_one("#docs-editor", TextArea).text
        words = len(text.split())
        chars = len(text)
        lines = len(text.splitlines()) or 1
        paras = len([p for p in text.split("\n\n") if p.strip()])
        mins = max(1, round(words / 200)) if words else 0
        fname = self.current_file.name if self.current_file else "Untitled.md"
        self.query_one("#docs-file-label", Static).update(f"  [b cyan]{fname}[/b cyan]")
        self.query_one("#docs-status", Static).update(
            f"{fname}  •  Words: {words}  •  Chars: {chars}  •  Paras: {paras}  •  Lines: {lines}  •  Read: ~{mins}m  •  ^S Save  ^O Open  ^F Find"
        )

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if event.text_area.id == "docs-editor":
            self.query_one("#docs-preview", Markdown).update(event.text_area.text)
            self._update_stats()

    def open_file(self, path: Path) -> None:
        content = load_document(path)
        self.current_file = path
        editor = self.query_one("#docs-editor", TextArea)
        editor.text = content
        self.query_one("#docs-preview", Markdown).update(content)
        self._update_stats()
        add_recent_file(path, "docs")
        self.notify(f"Opened {path.name}", timeout=2)
        editor.focus()

    def _insert_snippet(self, snippet: str) -> None:
        editor = self.query_one("#docs-editor", TextArea)
        editor.insert(snippet)
        self.query_one("#docs-preview", Markdown).update(editor.text)
        self._update_stats()
        editor.focus()

    def action_open_picker(self) -> None:
        def _on_picked(path: Path | None) -> None:
            if path is not None:
                try:
                    self.open_file(path)
                except Exception as exc:
                    self.notify(f"Open error: {exc}", severity="error")

        self.app.push_screen(
            FilePickerModal(
                mode="open",
                title="Open Document (.md, .docx, .txt)",
                start_dir=self.current_file.parent if self.current_file else Path.cwd(),
                extensions=(".md", ".docx", ".txt"),
            ),
            _on_picked,
        )

    def _open_save_as(self) -> None:
        def _on_picked(path: Path | None) -> None:
            if path is not None:
                self._save_to(path)

        self.app.push_screen(
            FilePickerModal(
                mode="save",
                title="Save Document As (.md, .docx, .txt)",
                start_dir=self.current_file.parent if self.current_file else Path.cwd(),
                extensions=(".md", ".docx", ".txt"),
                default_name=self.current_file.name if self.current_file else "document.md",
            ),
            _on_picked,
        )

    def _save_to(self, path: Path) -> None:
        try:
            text = self.query_one("#docs-editor", TextArea).text
            save_document(path, text)
            self.current_file = path
            add_recent_file(path, "docs")
            self._update_stats()
            self.notify(f"Saved {path.name}", timeout=2)
        except Exception as exc:
            self.notify(f"Save error: {exc}", severity="error")

    def action_save_doc(self) -> None:
        if self.current_file is None:
            self._open_save_as()
        else:
            self._save_to(self.current_file)

    def action_toggle_find(self) -> None:
        self._show_find = not self._show_find
        bar = self.query_one("#docs-find-bar", Horizontal)
        bar.display = self._show_find
        if self._show_find:
            self.query_one("#docs-find-in", Input).focus()
        else:
            self.query_one("#docs-editor", TextArea).focus()

    def action_fmt_h1(self) -> None:
        self._insert_snippet("\n# Heading 1\n")

    def action_fmt_h2(self) -> None:
        self._insert_snippet("\n## Heading 2\n")

    def action_fmt_italic(self) -> None:
        self._insert_snippet("*italic text*")

    def action_fmt_code(self) -> None:
        self._insert_snippet("\n```python\nprint('Hello Clice!')\n```\n")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid.startswith("rtab-"):
            self._switch_ribbon(bid[5:])
        elif bid == "doc-new":
            self.current_file = None
            self.query_one("#docs-editor", TextArea).text = "# New Document\n\n"
            self._update_stats()
        elif bid == "doc-open":
            self.action_open_picker()
        elif bid == "doc-save":
            self.action_save_doc()
        elif bid == "doc-save-as":
            self._open_save_as()
        elif bid == "fmt-h1":
            self.action_fmt_h1()
        elif bid == "fmt-h2":
            self.action_fmt_h2()
        elif bid == "fmt-h3":
            self._insert_snippet("\n### Heading 3\n")
        elif bid == "fmt-bold":
            self._insert_snippet("**bold text**")
        elif bid == "fmt-italic":
            self.action_fmt_italic()
        elif bid == "fmt-strike":
            self._insert_snippet("~~strikethrough~~")
        elif bid == "fmt-quote":
            self._insert_snippet("\n> Blockquote text\n")
        elif bid == "fmt-inline-code":
            self._insert_snippet("`code`")
        elif bid == "fmt-code":
            self.action_fmt_code()
        elif bid == "fmt-hr":
            self._insert_snippet("\n---\n")
        elif bid == "ins-table":
            self._insert_snippet("\n| Column 1 | Column 2 | Column 3 |\n| --- | --- | --- |\n| Cell 1 | Cell 2 | Cell 3 |\n")
        elif bid == "ins-check":
            self._insert_snippet("\n- [ ] Task 1\n- [ ] Task 2\n")
        elif bid == "ins-bullets":
            self._insert_snippet("\n- Item 1\n- Item 2\n")
        elif bid == "ins-num":
            self._insert_snippet("\n1. First\n2. Second\n")
        elif bid == "ins-link":
            self._insert_snippet("[Link Text](https://example.com)")
        elif bid == "ins-date":
            self._insert_snippet(datetime.now().strftime("%Y-%m-%d %H:%M"))
        elif bid == "tool-find":
            self.action_toggle_find()
        elif bid == "tool-preview":
            self._show_preview = not self._show_preview
            self.query_one("#docs-preview-scroll", VerticalScroll).display = self._show_preview
        elif bid == "tool-upper":
            ed = self.query_one("#docs-editor", TextArea)
            ed.text = ed.text.upper()
        elif bid == "tool-stats":
            self.notify(str(self.query_one("#docs-status", Static).render()), timeout=4)
        elif bid == "docs-replace-all":
            needle = self.query_one("#docs-find-in", Input).value
            repl = self.query_one("#docs-replace-in", Input).value
            if needle:
                ed = self.query_one("#docs-editor", TextArea)
                count = ed.text.count(needle)
                ed.text = ed.text.replace(needle, repl)
                self.notify(f"Replaced {count} occurrence(s)", timeout=2)
        elif bid == "docs-find-close":
            self.action_toggle_find()
