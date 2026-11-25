"""Reusable GUI-like Modal File Picker (Open / Save As) for Clice Office apps."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Input, Static


class FilePickerModal(ModalScreen[Path | None]):
    """Cross-platform modal file browser with arrow navigation, folder traversal, and Save As."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("backspace,left", "go_up", "Up (..)"),
    ]

    def __init__(
        self,
        mode: str = "open",
        title: str = "Open File",
        start_dir: Path | None = None,
        extensions: tuple[str, ...] = (),
        default_name: str = "",
    ) -> None:
        super().__init__()
        self.mode = mode  # "open" or "save"
        self.dialog_title = title
        self.current_dir = (start_dir or Path.cwd()).resolve()
        self.extensions = tuple(e.lower() for e in extensions)
        self.default_name = default_name
        self._entries: list[Path] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="file-picker-dialog"):
            yield Static(f"[b]{self.dialog_title}[/b]  [dim](Esc to cancel • ←/Backspace Up)[/dim]", id="fp-header")
            yield Static(f"▸ {self.current_dir}", id="fp-cwd")
            yield DataTable(id="fp-table", cursor_type="row")
            with Horizontal(id="fp-footer"):
                yield Input(
                    value=self.default_name,
                    placeholder="Filename (e.g. report.md, budget.xlsx, deck.pptx)...",
                    id="fp-filename",
                )
                yield Button("Up (←)", id="fp-up")
                yield Button("Save" if self.mode == "save" else "Open", variant="success", id="fp-confirm")
                yield Button("Cancel", variant="error", id="fp-cancel")

    def on_mount(self) -> None:
        self._refresh()
        if self.mode == "save":
            self.query_one("#fp-filename", Input).focus()
        else:
            self.query_one("#fp-table", DataTable).focus()

    def _refresh(self) -> None:
        table = self.query_one("#fp-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Type", "Name")
        self.query_one("#fp-cwd", Static).update(f"▸ {self.current_dir}")

        self._entries = []
        try:
            items = sorted(self.current_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            return

        for p in items:
            if p.name.startswith("."):
                continue
            if not p.is_dir() and self.extensions and p.suffix.lower() not in self.extensions:
                continue
            self._entries.append(p)
            table.add_row("[DIR]" if p.is_dir() else " file", p.name)

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_go_up(self) -> None:
        self.current_dir = self.current_dir.parent
        self._refresh()

    def _confirm(self) -> None:
        name = self.query_one("#fp-filename", Input).value.strip()
        if name:
            target = Path(name).expanduser()
            if not target.is_absolute():
                target = (self.current_dir / target).resolve()
            if target.is_dir():
                self.current_dir = target
                self.query_one("#fp-filename", Input).value = ""
                self._refresh()
                return
            self.dismiss(target)
            return

        table = self.query_one("#fp-table", DataTable)
        idx = table.cursor_row
        if idx is not None and 0 <= idx < len(self._entries):
            chosen = self._entries[idx]
            if chosen.is_dir():
                self.current_dir = chosen.resolve()
                self._refresh()
            else:
                self.dismiss(chosen.resolve())

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.data_table.id == "fp-table":
            idx = event.cursor_row
            if 0 <= idx < len(self._entries) and not self._entries[idx].is_dir():
                self.query_one("#fp-filename", Input).value = self._entries[idx].name

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id == "fp-table":
            idx = event.cursor_row
            if 0 <= idx < len(self._entries):
                chosen = self._entries[idx]
                if chosen.is_dir():
                    self.current_dir = chosen.resolve()
                    self._refresh()
                else:
                    self.dismiss(chosen.resolve())

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "fp-filename":
            self._confirm()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "fp-cancel":
            self.dismiss(None)
        elif event.button.id == "fp-up":
            self.action_go_up()
        elif event.button.id == "fp-confirm":
            self._confirm()
