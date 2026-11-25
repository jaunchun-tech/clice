"""Home Dashboard / App Launcher for Clice."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Grid, Vertical
from textual.widgets import Button, Static

from clice import __version__
from clice.core.config import get_recent_files


class AppCard(Vertical):
    """Clickable GUI-like app tile on the Home Dashboard."""

    def __init__(
        self,
        app_id: str,
        icon: str,
        title: str,
        subtitle: str,
        card_class: str,
    ) -> None:
        super().__init__(classes=f"app-card {card_class}")
        self.target_app_id = app_id
        self._icon = icon
        self._title = title
        self._subtitle = subtitle

    def compose(self) -> ComposeResult:
        yield Static(f"[b]{self._icon}  {self._title}[/b]")
        yield Static(f"[dim]{self._subtitle}[/dim]")
        yield Button("Open →", variant="primary", id=f"launch-{self.target_app_id}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == f"launch-{self.target_app_id}":
            self.app.switch_app(self.target_app_id)  # type: ignore[attr-defined]


class HomeApp(Vertical):
    """Clice Desktop Launcher & Recent Files Dashboard."""

    def compose(self) -> ComposeResult:
        yield Static(
            f"[b]✨ Welcome to CLICE v{__version__}[/b]  —  "
            "Your Colorful Terminal Office Suite & Developer Multitool\n"
            "[dim]Click any app below, use the left dock, or press Ctrl+P for the Command Palette • "
            "Press T to cycle themes[/dim]",
            id="home-banner",
        )
        with Grid(id="home-grid"):
            yield AppCard("sheets", "📊", "Clice Sheets", "Excel • Formulas • .xlsx & .csv", "card-excel")
            yield AppCard("docs", "📝", "Clice Docs", "Word • Live Preview • .docx & .md", "card-word")
            yield AppCard("slides", "📽️", "Clice Slides", "PowerPoint • Present Mode • .pptx", "card-ppt")
            yield AppCard("files", "📁", "File Explorer", "Easy cd • mkdir • touch • Open files", "card-files")
            yield AppCard("devtools", "💻", "Coding Utils", "JSON • Regex • Base64 • Hash • Code", "card-dev")
            yield AppCard("calc", "🧮", "Calculator", "Scientific • History • HEX/BIN/DEC", "card-calc")
            yield AppCard("notes", "✅", "Notes & Tasks", "To-Do Manager • Priorities • Notes", "card-notes")
            yield AppCard("calendar", "📅", "Calendar & Focus", "Month View • Events • Pomodoro", "card-cal")
            yield AppCard("sysmon", "🖥️", "System Monitor", "Live CPU • RAM • Disk • Processes", "card-sys")

        recents = get_recent_files()
        if recents:
            lines = ["[b]🕒 Recent Files[/b]"]
            for item in recents[:6]:
                lines.append(f"  • [{item.get('app', 'file')}] {item.get('name')}  [dim]{item.get('path')}[/dim]")
            yield Static("\n".join(lines), classes="metric-box")
        else:
            yield Static(
                f"[b]💡 Quick Tip[/b]  Working directory: [cyan]{Path.cwd()}[/cyan]\n"
                "[dim]Open File Explorer to navigate, create folders/files, or use `clice --shell-init` for easy terminal `cd`![/dim]",
                classes="metric-box",
            )
