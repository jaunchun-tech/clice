"""Main Clice Textual Desktop Shell — Keyboard-First Navigation, Crisp Icons, Themes & Plugins."""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, ListItem, ListView, Static

from clice import __version__
from clice.apps.calc import CalcApp
from clice.apps.calendar_app import CalendarApp
from clice.apps.devtools import DevToolsApp
from clice.apps.docs import DocsApp
from clice.apps.files import FilesApp
from clice.apps.home import HomeApp
from clice.apps.notes import NotesApp
from clice.apps.plugins_view import PluginsViewApp
from clice.apps.sheets import SheetsApp
from clice.apps.slides import SlidesApp
from clice.apps.sysmon import SysMonApp
from clice.core.plugins import PluginRegistry
from clice.theme import AVAILABLE_THEMES, CLICE_CSS

BUILTIN_NAV: list[tuple[str, str, str, str]] = [
    ("home", "[b #38bdf8][H][/b #38bdf8]", "Home", "F1"),
    ("sheets", "[b #22c55e][X][/b #22c55e]", "Sheets (Excel)", "F2"),
    ("docs", "[b #3b82f6][W][/b #3b82f6]", "Docs (Word)", "F3"),
    ("slides", "[b #f97316][P][/b #f97316]", "Slides (PPT)", "F4"),
    ("files", "[b #eab308][F][/b #eab308]", "Files & cd", "F5"),
    ("devtools", "[b #a855f7][<>][/b #a855f7]", "Coding Utils", "F6"),
    ("calc", "[b #06b6d4][=][/b #06b6d4]", "Calculator", "F7"),
    ("notes", "[b #ec4899][✓][/b #ec4899]", "Notes & Tasks", "F8"),
    ("calendar", "[b #14b8a6][#][/b #14b8a6]", "Calendar", "F9"),
    ("sysmon", "[b #ef4444][~][/b #ef4444]", "SysMon", ""),
    ("plugins", "[b #8b5cf6][+][/b #8b5cf6]", "Plugins", ""),
]


class CliceApp(App[str | None]):
    """Clice — Keyboard-First, Colorful GUI-like Terminal Office Suite & Dev Multitool."""

    TITLE = f"Clice v{__version__}"
    SUB_TITLE = "Keyboard-First Terminal Office & Dev Suite"
    CSS = CLICE_CSS

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+b", "focus_sidebar", "Sidebar"),
        Binding("ctrl+t", "cycle_theme", "Theme"),
        Binding("f1", "go_app('home')", "Home"),
        Binding("f2", "go_app('sheets')", "Sheets"),
        Binding("f3", "go_app('docs')", "Docs"),
        Binding("f4", "go_app('slides')", "Slides"),
        Binding("f5", "go_app('files')", "Files"),
        Binding("f6", "go_app('devtools')", "Dev"),
        Binding("f7", "go_app('calc')", "Calc"),
        Binding("f8", "go_app('notes')", "Notes"),
        Binding("f9", "go_app('calendar')", "Cal"),
    ]

    def __init__(
        self,
        initial_app: str = "home",
        initial_file: Path | None = None,
        extra_plugin_dirs: list[Path] | None = None,
        cd_file: Path | None = None,
    ) -> None:
        super().__init__()
        self.initial_app = initial_app
        self.initial_file = initial_file
        self.extra_plugin_dirs = extra_plugin_dirs or []
        self.cd_file = cd_file
        self.current_app_id = initial_app
        self._theme_idx = 0
        self._nav_ids: list[str] = []
        self.plugin_registry = PluginRegistry()
        self.plugin_registry.discover(self.extra_plugin_dirs)

    def compose(self) -> ComposeResult:
        with Horizontal(id="top-bar"):
            yield Static(f"◆ CLICE v{__version__}", id="brand-badge")
            yield Static(f"▸ {Path.cwd()}", id="top-cwd")
            with Horizontal(id="top-actions"):
                yield Button("Sidebar (^B)", id="top-sidebar")
                yield Button("Theme (^T)", id="top-theme")
                yield Button("Quit (^Q)", variant="error", id="top-quit")

        with Horizontal(id="main-shell"):
            with Vertical(id="sidebar"):
                yield Static("APPS (↑↓ Enter)", classes="sidebar-section")
                yield ListView(id="sidebar-list")
            yield Vertical(id="workspace")

        yield Footer()

    def on_mount(self) -> None:
        self.theme = AVAILABLE_THEMES[self._theme_idx]
        self._populate_sidebar()
        if self.initial_file and self.initial_file.exists():
            self.open_file_in_appropriate_app(self.initial_file)
        else:
            self.switch_app(self.initial_app)

    def _populate_sidebar(self) -> None:
        lv = self.query_one("#sidebar-list", ListView)
        lv.clear()
        self._nav_ids = []

        for app_id, icon, label, key in BUILTIN_NAV:
            self._nav_ids.append(app_id)
            hint = f" [dim]{key}[/dim]" if key else ""
            lv.append(ListItem(Static(f"{icon} {label}{hint}")))

        for lp in self.plugin_registry.loaded:
            p = lp.plugin
            self._nav_ids.append(p.id)
            lv.append(ListItem(Static(f"[b #c084fc]{p.icon}[/b #c084fc] {p.name}")))

    def reload_plugins(self) -> None:
        self.plugin_registry.discover(self.extra_plugin_dirs)
        self._populate_sidebar()

    def update_cwd_display(self, path: Path) -> None:
        self.query_one("#top-cwd", Static).update(f"▸ {path}")

    def exit_with_cd(self, target_dir: Path) -> None:
        if self.cd_file is not None:
            try:
                self.cd_file.write_text(str(target_dir), encoding="utf-8")
            except Exception:
                pass
        self.exit(str(target_dir))

    def open_file_in_appropriate_app(self, path: Path) -> None:
        ext = path.suffix.lower()
        if ext in (".xlsx", ".csv", ".tsv"):
            self.switch_app("sheets", file_path=path)
        elif ext in (".docx", ".md", ".txt"):
            self.switch_app("docs", file_path=path)
        elif ext == ".pptx":
            self.switch_app("slides", file_path=path)
        else:
            self.switch_app("devtools", file_path=path)

    def switch_app(self, app_id: str, file_path: Path | None = None) -> None:
        self.current_app_id = app_id

        lv = self.query_one("#sidebar-list", ListView)
        if app_id in self._nav_ids:
            lv.index = self._nav_ids.index(app_id)

        workspace = self.query_one("#workspace", Vertical)
        workspace.remove_children()

        widget = None
        if app_id == "home":
            widget = HomeApp()
        elif app_id == "sheets":
            widget = SheetsApp(initial_file=file_path)
        elif app_id == "docs":
            widget = DocsApp(initial_file=file_path)
        elif app_id == "slides":
            widget = SlidesApp(initial_file=file_path)
        elif app_id == "files":
            widget = FilesApp()
        elif app_id == "devtools":
            widget = DevToolsApp(initial_file=file_path)
        elif app_id == "calc":
            widget = CalcApp()
        elif app_id == "notes":
            widget = NotesApp()
        elif app_id == "calendar":
            widget = CalendarApp()
        elif app_id == "sysmon":
            widget = SysMonApp()
        elif app_id == "plugins":
            widget = PluginsViewApp(self.plugin_registry)
        else:
            for lp in self.plugin_registry.loaded:
                if lp.plugin.id == app_id:
                    widget = lp.plugin.create_widget()
                    break

        if widget is None:
            widget = HomeApp()

        workspace.mount(widget)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "sidebar-list" and event.list_view.index is not None:
            idx = event.list_view.index
            if 0 <= idx < len(self._nav_ids):
                self.switch_app(self._nav_ids[idx])

    def action_focus_sidebar(self) -> None:
        self.query_one("#sidebar-list", ListView).focus()

    def action_go_app(self, app_id: str) -> None:
        self.switch_app(app_id)

    def action_cycle_theme(self) -> None:
        self._theme_idx = (self._theme_idx + 1) % len(AVAILABLE_THEMES)
        self.theme = AVAILABLE_THEMES[self._theme_idx]
        self.notify(f"Theme: {self.theme}", timeout=2)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid == "top-theme":
            self.action_cycle_theme()
        elif bid == "top-sidebar":
            self.action_focus_sidebar()
        elif bid == "top-quit":
            self.exit()
