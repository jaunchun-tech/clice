"""Clice Keyboard Shortcuts & Help Modal (F10)."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Markdown, Static

HELP_MD = """# ◆ Clice Keyboard Shortcuts & Quick Guide

## Global Navigation
- **`Ctrl+K`** — Open **Spotlight** (instant search for any app, plugin, or recent file)
- **`Ctrl+B`** — Focus Left Sidebar (`↑`/`↓` + `Enter` to switch apps)
- **`Ctrl+\\`** — Toggle Sidebar (full-width focus mode!)
- **`Ctrl+T`** — Cycle Color Theme (saved automatically!)
- **`F1` – `F9`** — Jump directly to Home, Sheets, Docs, Slides, Files, DevTools, Calc, Notes, Calendar
- **`F10`** — Open this Help & Shortcuts modal
- **`Ctrl+P`** — Textual Command Palette
- **`Ctrl+Q`** — Quit Clice

## Office Suite Shortcuts
- **Sheets (Excel)**: `↑↓←→` move • `Enter`/`F2` edit cell • `Del` clear • `Ctrl+O` Open • `Ctrl+S` Save • `Ctrl+R`/`Ctrl+L` +Row/+Col
- **Docs (Word)**: `Ctrl+O` Open • `Ctrl+S` Save • `Ctrl+F` Find & Replace • `Ctrl+I` Italic • `Ctrl+K` Code • `Ctrl+1`/`2` Headings
- **Slides (PowerPoint)**: `Ctrl+O` Open • `Ctrl+S` Save • `Ctrl+M` New Slide • `Alt+P` Present Mode • `Alt+↑`/`↓` Switch Slides

## Developer & Workspace Tools
- **Files**: `↑↓` + `Enter` browse/open • `←`/`Backspace` Up • `H` Home • `M` mkdir • `N` touch • `Del` delete • `C` CD & Exit
- **SQLite Studio**: `Ctrl+Enter` Run SQL • `Ctrl+O` Open `.db`
- **HTTP Client**: `Ctrl+Enter` Send Request
- **Plugins & Marketplace**: Auto-pulls from `jaunchun-tech/clice-marketplace` • `Enter` Download & Install
"""


class HelpModal(ModalScreen[None]):
    """Clean, scrollable Keyboard Shortcuts & Help overlay."""

    BINDINGS = [
        Binding("escape,q,f10", "close_help", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="help-dialog"):
            yield Static("[b #38bdf8]◆ Clice Help & Shortcuts[/b #38bdf8]  [dim](Esc / Q to close)[/dim]", id="sp-header")
            with VerticalScroll(id="help-scroll"):
                yield Markdown(HELP_MD)
            yield Button("Close (Esc)", variant="primary", id="help-close")

    def action_close_help(self) -> None:
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "help-close":
            self.dismiss(None)
