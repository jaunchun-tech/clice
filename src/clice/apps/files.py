"""Clice Files — Cross-platform File Explorer with easy cd, mkdir, touch, and app launch."""

from __future__ import annotations

import os
import shutil
from datetime import datetime
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Input, Static


def _fmt_size(num_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if num_bytes < 1024:
            return f"{num_bytes:.0f} {unit}" if unit == "B" else f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024  # type: ignore[assignment]
    return f"{num_bytes:.1f} PB"


class FilesApp(Vertical):
    """File Explorer with easy cd, mkdir, touch, delete, and direct Open-in-Clice."""

    def __init__(self, start_dir: Path | None = None) -> None:
        super().__init__()
        self.current_dir: Path = (start_dir or Path.cwd()).resolve()
        self._entries: list[Path] = []

    def compose(self) -> ComposeResult:
        with Horizontal(classes="toolbar"):
            yield Static("[b #eab308]📁 Clice Files[/b #eab308]", classes="app-title")
            yield Input(value=str(self.current_dir), placeholder="Enter path to cd...", id="files-cd-input")
            yield Button("Go / cd", variant="primary", id="files-go")
            yield Button("⬆ Up", id="files-up")
            yield Button("🏠 Home", id="files-home")
            yield Button("📌 CD & Exit", variant="success", id="files-cd-exit")

        with Horizontal(classes="toolbar"):
            yield Input(placeholder="New file or folder name...", id="files-new-name")
            yield Button("+ New Dir (mkdir)", variant="success", id="files-mkdir")
            yield Button("+ New File (touch)", variant="primary", id="files-touch")
            yield Button("Open Selected", id="files-open-sel")
            yield Button("Delete Selected", variant="error", id="files-del-sel")

        yield DataTable(id="files-table", cursor_type="row")
        yield Static("Select a folder and press Enter to cd, or select a file to open it in Clice.", id="files-status", classes="status-strip")

    def on_mount(self) -> None:
        self._refresh_listing()

    def _refresh_listing(self) -> None:
        table = self.query_one("#files-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Type", "Name", "Size", "Modified")

        self.query_one("#files-cd-input", Input).value = str(self.current_dir)
        try:
            os.chdir(self.current_dir)
        except Exception:
            pass

        if hasattr(self.app, "update_cwd_display"):
            self.app.update_cwd_display(self.current_dir)  # type: ignore[attr-defined]

        self._entries = []
        try:
            items = sorted(
                self.current_dir.iterdir(),
                key=lambda p: (not p.is_dir(), p.name.lower()),
            )
        except PermissionError:
            self.query_one("#files-status", Static).update(f"Permission denied: {self.current_dir}")
            return

        for p in items:
            self._entries.append(p)
            try:
                stat = p.stat()
                size_str = "<DIR>" if p.is_dir() else _fmt_size(stat.st_size)
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            except OSError:
                size_str = "?"
                mtime = "?"
            icon = "📁" if p.is_dir() else "📄"
            table.add_row(icon, p.name, size_str, mtime)

        self.query_one("#files-status", Static).update(
            f"{self.current_dir}  •  {len(self._entries)} items"
        )

    def _get_selected_entry(self) -> Path | None:
        table = self.query_one("#files-table", DataTable)
        if table.cursor_row is None or table.cursor_row < 0 or table.cursor_row >= len(self._entries):
            return None
        return self._entries[table.cursor_row]

    def _open_entry(self, entry: Path) -> None:
        if entry.is_dir():
            self.current_dir = entry.resolve()
            self._refresh_listing()
            return
        if hasattr(self.app, "open_file_in_appropriate_app"):
            self.app.open_file_in_appropriate_app(entry)  # type: ignore[attr-defined]

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id == "files-table":
            entry = self._get_selected_entry()
            if entry is not None:
                self._open_entry(entry)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "files-cd-input":
            self._cd_to(event.value)

    def _cd_to(self, raw: str) -> None:
        target = Path(raw.strip()).expanduser()
        if not target.is_absolute():
            target = (self.current_dir / target).resolve()
        if target.exists() and target.is_dir():
            self.current_dir = target
            self._refresh_listing()
        else:
            self.query_one("#files-status", Static).update(f"Directory not found: {target}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        status = self.query_one("#files-status", Static)

        if bid == "files-go":
            self._cd_to(self.query_one("#files-cd-input", Input).value)
        elif bid == "files-up":
            self.current_dir = self.current_dir.parent
            self._refresh_listing()
        elif bid == "files-home":
            self.current_dir = Path.home()
            self._refresh_listing()
        elif bid == "files-cd-exit":
            if hasattr(self.app, "exit_with_cd"):
                self.app.exit_with_cd(self.current_dir)  # type: ignore[attr-defined]
            else:
                self.app.exit(str(self.current_dir))
        elif bid == "files-mkdir":
            name = self.query_one("#files-new-name", Input).value.strip()
            if not name:
                status.update("Enter a directory name first")
                return
            try:
                new_dir = self.current_dir / name
                new_dir.mkdir(parents=True, exist_ok=True)
                self.query_one("#files-new-name", Input).value = ""
                self._refresh_listing()
                status.update(f"Created directory: {new_dir.name}")
            except Exception as exc:
                status.update(f"mkdir error: {exc}")
        elif bid == "files-touch":
            name = self.query_one("#files-new-name", Input).value.strip()
            if not name:
                status.update("Enter a file name first")
                return
            try:
                new_file = self.current_dir / name
                new_file.parent.mkdir(parents=True, exist_ok=True)
                new_file.touch(exist_ok=True)
                self.query_one("#files-new-name", Input).value = ""
                self._refresh_listing()
                status.update(f"Created file: {new_file.name}")
            except Exception as exc:
                status.update(f"touch error: {exc}")
        elif bid == "files-open-sel":
            entry = self._get_selected_entry()
            if entry is not None:
                self._open_entry(entry)
        elif bid == "files-del-sel":
            entry = self._get_selected_entry()
            if entry is None:
                status.update("No item selected")
                return
            try:
                if entry.is_dir():
                    shutil.rmtree(entry)
                else:
                    entry.unlink()
                self._refresh_listing()
                status.update(f"Deleted: {entry.name}")
            except Exception as exc:
                status.update(f"Delete error: {exc}")
