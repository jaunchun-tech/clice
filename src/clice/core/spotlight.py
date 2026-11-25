"""Clice Spotlight (Ctrl+K) — Raycast/VS Code-style instant app & recent-file launcher."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, ListItem, ListView, Static

from clice.core.config import get_recent_files


class SpotlightModal(ModalScreen[tuple[str, str] | None]):
    """Press Ctrl+K from anywhere to search & jump to any app, plugin, or recent file."""

    BINDINGS = [
        Binding("escape", "cancel", "Close"),
    ]

    def __init__(self, entries: list[tuple[str, str, str]]) -> None:
        """entries: list of (kind, target, display_label)."""
        super().__init__()
        self.all_entries = entries
        self.filtered: list[tuple[str, str, str]] = list(entries)

    def compose(self) -> ComposeResult:
        with Vertical(id="spotlight-dialog"):
            yield Static("[b #38bdf8]◆ Clice Spotlight[/b #38bdf8]  [dim](Type to filter • ↑↓ Select • Enter Go • Esc Close)[/dim]", id="sp-header")
            yield Input(placeholder="Jump to app, plugin, or recent file...", id="sp-input")
            yield ListView(id="sp-list")

    def on_mount(self) -> None:
        self._render_list("")
        self.query_one("#sp-input", Input).focus()

    def _render_list(self, query: str) -> None:
        q = query.strip().lower()
        self.filtered = [e for e in self.all_entries if not q or q in e[2].lower() or q in e[1].lower()]
        lv = self.query_one("#sp-list", ListView)
        lv.clear()
        for kind, _, label in self.filtered[:18]:
            tag = "[cyan]APP[/cyan]" if kind == "app" else "[green]FILE[/green]"
            lv.append(ListItem(Static(f" {tag}  {label}")))
        if self.filtered:
            lv.index = 0

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "sp-input":
            self._render_list(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "sp-input" and self.filtered:
            lv = self.query_one("#sp-list", ListView)
            idx = lv.index if lv.index is not None and 0 <= lv.index < len(self.filtered) else 0
            kind, target, _ = self.filtered[idx]
            self.dismiss((kind, target))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "sp-list" and event.list_view.index is not None:
            idx = event.list_view.index
            if 0 <= idx < len(self.filtered):
                kind, target, _ = self.filtered[idx]
                self.dismiss((kind, target))


def build_spotlight_entries(nav_items: list[tuple[str, str]]) -> list[tuple[str, str, str]]:
    """Combine apps/plugins and recent files for Spotlight."""
    entries: list[tuple[str, str, str]] = [("app", app_id, label) for app_id, label in nav_items]
    for rec in get_recent_files()[:10]:
        p = rec.get("path", "")
        if p and Path(p).exists():
            entries.append(("file", p, f"{rec.get('name', p)}  [dim]{p}[/dim]"))
    return entries
