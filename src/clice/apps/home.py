"""Home Dashboard / Main Menu — Grid of Clickable & Arrow-Navigable App Rectangles."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import psutil
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Horizontal, Vertical, VerticalScroll
from textual.events import Click
from textual.widgets import Button, Static

from clice import __version__
from clice.core.config import get_recent_files

GRID_COLS = 3

MAIN_MENU_APPS: list[tuple[str, str, str, str, str, str]] = [
    ("sheets", "[b #22c55e]\\[X][/b #22c55e]", "Clice Sheets", "Excel • Ribbon • Formulas • Sort\n.xlsx & .csv File Browser", "F2", "tile-excel"),
    ("docs", "[b #3b82f6]\\[W][/b #3b82f6]", "Clice Docs", "Word • Ribbon • Find/Replace\nNative .md, .docx & .txt", "F3", "tile-word"),
    ("slides", "[b #f97316]\\[P][/b #f97316]", "Clice Slides", "PowerPoint • Design • Present\n.pptx, .md & .json Decks", "F4", "tile-ppt"),
    ("files", "[b #eab308]\\[F][/b #eab308]", "File Explorer", "Easy cd • mkdir • touch • Open\nCross-Platform File System", "F5", "tile-files"),
    ("devtools", "[b #a855f7]\\[<>][/b #a855f7]", "Coding Utils", "JSON • Regex • Base64 • Hash\nUUID • JWT • Color • Code Pad", "F6", "tile-dev"),
    ("calc", "[b #06b6d4]\\[=][/b #06b6d4]", "Calculator", "Scientific • Expression History\nHEX / DEC / OCT / BIN", "F7", "tile-calc"),
    ("notes", "[b #ec4899]\\[✓][/b #ec4899]", "Notes & Tasks", "To-Do Manager • Priorities\nAuto-Saved Quick Notes", "F8", "tile-notes"),
    ("calendar", "[b #14b8a6]\\[#][/b #14b8a6]", "Calendar & Focus", "Interactive Month • Events\nPomodoro 25:00 Timer", "F9", "tile-cal"),
    ("kanban", "[b #f59e0b]\\[KB][/b #f59e0b]", "Kanban Board", "To Do • In Progress • Done\nPriority Tags & Auto-Save", "", "tile-files"),
    ("sql", "[b #38bdf8]\\[DB][/b #38bdf8]", "SQLite Studio", "Browse Tables • Run SQL\nExport Query Results to CSV", "", "tile-word"),
    ("http", "[b #10b981]\\[API][/b #10b981]", "HTTP / API Client", "GET/POST/PUT/DELETE • JSON\nHeaders & Response Inspector", "", "tile-excel"),
    ("runner", "[b #22d3ee]\\[$][/b #22d3ee]", "Command Runner", "Run Shell Commands Live\nSave Reusable Dev Snippets", "", "tile-calc"),
    ("diff", "[b #f43f5e]\\[≠][/b #f43f5e]", "Diff Viewer", "Side-by-Side Text/Code Diff\nColorized Unified Diff Output", "", "tile-notes"),
    ("secrets", "[b #a78bfa]\\[*][/b #a78bfa]", "Secrets & Passwords", "CSPRNG Passwords & Passphrases\nAPI Keys & Entropy Meter", "", "tile-dev"),
    ("sysmon", "[b #ef4444]\\[~][/b #ef4444]", "System Monitor", "Live CPU • RAM • Disk Bars\nTop Processes (psutil)", "", "tile-sys"),
    ("plugins", "[b #8b5cf6]\\[+][/b #8b5cf6]", "Plugins & Market", "GitHub Auto-Pull Marketplace\nLive README Preview & Install", "", "tile-plugins"),
]


class AppTile(Vertical):
    """A focusable, clickable, arrow-navigable app rectangle on the Main Menu."""

    can_focus = True

    BINDINGS = [
        Binding("enter,space", "launch", "Launch"),
    ]

    def __init__(
        self,
        app_id: str,
        icon: str,
        title: str,
        desc: str,
        shortcut: str,
        tile_class: str,
        tile_index: int,
    ) -> None:
        super().__init__(classes=f"app-tile {tile_class}", id=f"tile-{tile_index}")
        self.target_app_id = app_id
        self.tile_index = tile_index
        self._icon = icon
        self._title = title
        self._desc = desc
        self._shortcut = shortcut

    def compose(self) -> ComposeResult:
        badge = f"  [b cyan][{self._shortcut}][/b cyan]" if self._shortcut else ""
        yield Static(f"{self._icon}  [b]{self._title}[/b]{badge}")
        yield Static(f"[dim]{self._desc}[/dim]")

    def action_launch(self) -> None:
        self.app.switch_app(self.target_app_id)  # type: ignore[attr-defined]

    def on_click(self, event: Click) -> None:
        self.action_launch()


class HomeApp(VerticalScroll):
    """Main Menu with scrollable 3-column grid of clickable & arrow-navigable app rectangles."""

    BINDINGS = [
        Binding("left", "move_tile(-1)", "Left"),
        Binding("right", "move_tile(1)", "Right"),
        Binding("up", "move_tile(-3)", "Up"),
        Binding("down", "move_tile(3)", "Down"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._tile_count = 0

    def compose(self) -> ComposeResult:
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        now = datetime.now().strftime("%a %b %d  •  %H:%M")
        with Vertical(id="home-hero"):
            yield Static(
                f"[b #38bdf8]◆ CLICE DESKTOP[/b #38bdf8] [dim]v{__version__}[/dim]   "
                f"[b #a78bfa]│[/b #a78bfa]   [cyan]{now}[/cyan]   "
                f"[b #a78bfa]│[/b #a78bfa]   CPU [b #4ade80]{cpu:.0f}%[/b #4ade80]  RAM [b #fb923c]{ram:.0f}%[/b #fb923c]\n"
                f"[dim]📂 {Path.cwd()}   •   ← ↑ ↓ → Arrows + Enter (or Click) any app rectangle[/dim]"
            )
            with Horizontal(id="home-quick-actions"):
                yield Button("+ New Sheet", variant="success", id="qa-sheets")
                yield Button("+ New Doc", variant="primary", id="qa-docs")
                yield Button("+ New Slides", variant="warning", id="qa-slides")
                yield Button("Search (^K)", id="qa-spotlight")
                yield Button("Marketplace", id="qa-plugins")

        tiles: list[tuple[str, str, str, str, str, str]] = list(MAIN_MENU_APPS)
        if hasattr(self.app, "plugin_registry"):
            for lp in self.app.plugin_registry.loaded:  # type: ignore[attr-defined]
                p = lp.plugin
                tiles.append(
                    (
                        p.id,
                        f"[b #c084fc]{p.icon}[/b #c084fc]",
                        p.name,
                        f"{p.description[:52]}\nPlugin v{p.version} by {p.author}",
                        "",
                        "tile-plugins",
                    )
                )

        self._tile_count = len(tiles)
        with Grid(id="home-grid-tiles"):
            for idx, (app_id, icon, title, desc, shortcut, cls) in enumerate(tiles):
                yield AppTile(app_id, icon, title, desc, shortcut, cls, idx)

        recents = get_recent_files()
        if recents:
            lines = ["[b]▸ Recent Files[/b]"]
            for item in recents[:4]:
                lines.append(f"  • [{item.get('app', 'file')}] {item.get('name')}  [dim]{item.get('path')}[/dim]")
            yield Static("\n".join(lines), classes="metric-box")
        else:
            yield Static(
                f"[b]▸ Working Directory:[/b] [cyan]{Path.cwd()}[/cyan]",
                classes="metric-box",
            )

    def on_mount(self) -> None:
        if self._tile_count > 0:
            self.query_one("#tile-0", AppTile).focus()

    def action_move_tile(self, delta: int) -> None:
        focused = self.app.focused
        cur = focused.tile_index if isinstance(focused, AppTile) else 0
        nxt = max(0, min(self._tile_count - 1, cur + delta))
        tile = self.query_one(f"#tile-{nxt}", AppTile)
        tile.focus()
        tile.scroll_visible()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid == "qa-sheets":
            self.app.switch_app("sheets")  # type: ignore[attr-defined]
        elif bid == "qa-docs":
            self.app.switch_app("docs")  # type: ignore[attr-defined]
        elif bid == "qa-slides":
            self.app.switch_app("slides")  # type: ignore[attr-defined]
        elif bid == "qa-spotlight":
            self.app.action_open_spotlight()  # type: ignore[attr-defined]
        elif bid == "qa-plugins":
            self.app.switch_app("plugins")  # type: ignore[attr-defined]
