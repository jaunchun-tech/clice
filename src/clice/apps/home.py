"""Home Dashboard / Keyboard-First App Launcher for Clice."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import ListItem, ListView, Static

from clice import __version__
from clice.core.config import get_recent_files

LAUNCHER_APPS: list[tuple[str, str, str, str, str]] = [
    ("sheets", "[b #22c55e][X][/b #22c55e]", "Clice Sheets", "Excel • Formulas (=SUM, =AVG, =IF) • .xlsx & .csv", "F2"),
    ("docs", "[b #3b82f6][W][/b #3b82f6]", "Clice Docs", "Word • Live Preview • Ctrl+B/I/S • .docx & .md", "F3"),
    ("slides", "[b #f97316][P][/b #f97316]", "Clice Slides", "PowerPoint • F5 Present Mode • Ctrl+M New • .pptx", "F4"),
    ("files", "[b #eab308][F][/b #eab308]", "File Explorer", "Arrow Nav • Easy cd • mkdir (M) • touch (N)", "F5"),
    ("devtools", "[b #a855f7][<>][/b #a855f7]", "Coding Utils", "JSON • Regex • Base64/URL • Hash/UUID/JWT • Code", "F6"),
    ("calc", "[b #06b6d4][=][/b #06b6d4]", "Calculator", "Scientific • History • HEX/DEC/OCT/BIN", "F7"),
    ("notes", "[b #ec4899][✓][/b #ec4899]", "Notes & Tasks", "To-Do Manager • Priorities • Quick Notes", "F8"),
    ("calendar", "[b #14b8a6][#][/b #14b8a6]", "Calendar & Focus", "Month View • Events • Pomodoro Timer", "F9"),
    ("sysmon", "[b #ef4444][~][/b #ef4444]", "System Monitor", "Live CPU • RAM • Disk • Top Processes", ""),
    ("plugins", "[b #8b5cf6][+][/b #8b5cf6]", "Plugins & Marketplace", "Browse plugins/ & readme/ • Scaffold • Reload", ""),
]


class HomeApp(Vertical):
    """Keyboard-first Clice Launcher & Recent Files Dashboard."""

    def compose(self) -> ComposeResult:
        yield Static(
            f"[b]◆ CLICE v{__version__}[/b]  —  Keyboard-First Terminal Office & Developer Suite\n"
            "[dim]Use ↑ / ↓ and Enter to launch an app  •  F1–F9 quick switch  •  Ctrl+B sidebar  •  Ctrl+T theme  •  Ctrl+P palette[/dim]",
            id="home-banner",
        )
        yield ListView(id="home-launcher")

        recents = get_recent_files()
        if recents:
            lines = ["[b]▸ Recent Files[/b]"]
            for item in recents[:5]:
                lines.append(f"  • [{item.get('app', 'file')}] {item.get('name')}  [dim]{item.get('path')}[/dim]")
            yield Static("\n".join(lines), classes="metric-box")
        else:
            yield Static(
                f"[b]▸ Working Directory:[/b] [cyan]{Path.cwd()}[/cyan]\n"
                "[dim]Tip: Press F5 for File Explorer, or run `clice --shell-init fish|bash|zsh|powershell` for `clice-cd`![/dim]",
                classes="metric-box",
            )

    def on_mount(self) -> None:
        lv = self.query_one("#home-launcher", ListView)
        for _, icon, title, desc, key in LAUNCHER_APPS:
            k_hint = f"[b cyan]{key:>2}[/b cyan]" if key else "  "
            lv.append(ListItem(Static(f" {k_hint}  {icon}  [b]{title:<22}[/b]  [dim]{desc}[/dim]")))
        lv.focus()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "home-launcher" and event.list_view.index is not None:
            idx = event.list_view.index
            if 0 <= idx < len(LAUNCHER_APPS):
                self.app.switch_app(LAUNCHER_APPS[idx][0])  # type: ignore[attr-defined]
