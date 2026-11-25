"""Main Clice Textual Desktop Shell — Keyboard-First Navigation, Crisp Icons, Themes & Plugins."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, ListItem, ListView, Static

from clice import __version__
from clice.apps.calc import CalcApp
from clice.apps.calendar_app import CalendarApp
from clice.apps.devtools import DevToolsApp
from clice.apps.diff_viewer import DiffViewerApp
from clice.apps.docs import DocsApp
from clice.apps.files import FilesApp
from clice.apps.home import HomeApp
from clice.apps.http_client import HttpClientApp
from clice.apps.kanban import KanbanApp
from clice.apps.notes import NotesApp
from clice.apps.plugins_view import PluginsViewApp
from clice.apps.secrets_tool import SecretsToolApp
from clice.apps.sheets import SheetsApp
from clice.apps.slides import SlidesApp
from clice.apps.sql_studio import SqlStudioApp
from clice.apps.sysmon import SysMonApp
from clice.apps.terminal_runner import CommandRunnerApp
from clice.core.config import load_json, save_json
from clice.core.help_modal import HelpModal
from clice.core.intro import IntroSplashScreen
from clice.core.plugins import PluginRegistry
from clice.core.spotlight import SpotlightModal, build_spotlight_entries
from clice.theme import AVAILABLE_THEMES, CLICE_CSS

BUILTIN_NAV: list[tuple[str, str, str, str]] = [
    ("home", "[b #38bdf8]\\[H][/b #38bdf8]", "Home", "F1"),
    ("sheets", "[b #22c55e]\\[X][/b #22c55e]", "Sheets (Excel)", "F2"),
    ("docs", "[b #3b82f6]\\[W][/b #3b82f6]", "Docs (Word)", "F3"),
    ("slides", "[b #f97316]\\[P][/b #f97316]", "Slides (PPT)", "F4"),
    ("files", "[b #eab308]\\[F][/b #eab308]", "Files & cd", "F5"),
    ("devtools", "[b #a855f7]\\[<>][/b #a855f7]", "Coding Utils", "F6"),
    ("calc", "[b #06b6d4]\\[=][/b #06b6d4]", "Calculator", "F7"),
    ("notes", "[b #ec4899]\\[✓][/b #ec4899]", "Notes & Tasks", "F8"),
    ("calendar", "[b #14b8a6]\\[#][/b #14b8a6]", "Calendar", "F9"),
    ("kanban", "[b #f59e0b]\\[KB][/b #f59e0b]", "Kanban Board", ""),
    ("sql", "[b #38bdf8]\\[DB][/b #38bdf8]", "SQLite Studio", ""),
    ("http", "[b #10b981]\\[API][/b #10b981]", "HTTP Client", ""),
    ("runner", "[b #22d3ee]\\[$][/b #22d3ee]", "Cmd Runner", ""),
    ("diff", "[b #f43f5e]\\[≠][/b #f43f5e]", "Diff Viewer", ""),
    ("secrets", "[b #a78bfa]\\[*][/b #a78bfa]", "Secrets", ""),
    ("sysmon", "[b #ef4444]\\[~][/b #ef4444]", "SysMon", ""),
    ("plugins", "[b #8b5cf6]\\[+][/b #8b5cf6]", "Plugins", ""),
]


class CliceApp(App[str | None]):
    """Clice — Keyboard-First, Colorful GUI-like Terminal Office Suite & Dev Multitool."""

    TITLE = f"Clice v{__version__}"
    SUB_TITLE = "Keyboard-First Terminal Office & Dev Suite"
    CSS = CLICE_CSS

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+k", "open_spotlight", "Spotlight"),
        Binding("ctrl+b", "focus_sidebar", "Sidebar"),
        Binding("ctrl+backslash", "toggle_sidebar", "Hide Bar"),
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
        Binding("f10", "open_help", "Help"),
    ]

    def __init__(
        self,
        initial_app: str = "home",
        initial_file: Path | None = None,
        extra_plugin_dirs: list[Path] | None = None,
        cd_file: Path | None = None,
        show_intro: bool = True,
    ) -> None:
        super().__init__()
        self.initial_app = initial_app
        self.initial_file = initial_file
        self.extra_plugin_dirs = extra_plugin_dirs or []
        self.cd_file = cd_file
        self.show_intro = show_intro
        self.current_app_id = initial_app
        self._theme_idx = 0
        self._nav_ids: list[str] = []
        self.plugin_registry = PluginRegistry()
        self.plugin_registry.discover(self.extra_plugin_dirs)

    def compose(self) -> ComposeResult:
        with Horizontal(id="top-bar"):
            yield Static(f"◆ CLICE v{__version__}", id="brand-badge")
            yield Static(f"▸ {Path.cwd()}", id="top-cwd")
            yield Static(datetime.now().strftime("%H:%M"), id="top-clock")
            with Horizontal(id="top-actions"):
                yield Button("Search (^K)", variant="primary", id="top-spotlight")
                yield Button("Help (F10)", id="top-help")
                yield Button("Theme (^T)", id="top-theme")
                yield Button("Quit (^Q)", variant="error", id="top-quit")

        with Horizontal(id="main-shell"):
            with Vertical(id="sidebar"):
                yield Static("APPS (↑↓ Enter)", classes="sidebar-section")
                yield ListView(id="sidebar-list")
            yield Vertical(id="workspace")

        yield Footer()

    def on_mount(self) -> None:
        saved = load_json("settings.json", {})
        saved_theme = saved.get("theme")
        if saved_theme in AVAILABLE_THEMES:
            self._theme_idx = AVAILABLE_THEMES.index(saved_theme)
        self.theme = AVAILABLE_THEMES[self._theme_idx]
        self._populate_sidebar()
        self.set_interval(30.0, self._tick_clock)
        if self.initial_file and self.initial_file.exists():
            self.open_file_in_appropriate_app(self.initial_file)
        else:
            self.switch_app(self.initial_app)
        if self.show_intro:
            self.push_screen(IntroSplashScreen())

    def _tick_clock(self) -> None:
        self.query_one("#top-clock", Static).update(datetime.now().strftime("%H:%M"))

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
        elif app_id == "kanban":
            widget = KanbanApp()
        elif app_id == "sql":
            widget = SqlStudioApp()
        elif app_id == "http":
            widget = HttpClientApp()
        elif app_id == "runner":
            widget = CommandRunnerApp()
        elif app_id == "diff":
            widget = DiffViewerApp()
        elif app_id == "secrets":
            widget = SecretsToolApp()
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

        widget.styles.opacity = 0.0
        workspace.mount(widget)
        widget.styles.animate("opacity", value=1.0, duration=0.22, easing="out_cubic")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "sidebar-list" and event.list_view.index is not None:
            idx = event.list_view.index
            if 0 <= idx < len(self._nav_ids):
                self.switch_app(self._nav_ids[idx])

    def action_focus_sidebar(self) -> None:
        sidebar = self.query_one("#sidebar", Vertical)
        sidebar.display = True
        self.query_one("#sidebar-list", ListView).focus()

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one("#sidebar", Vertical)
        sidebar.display = not sidebar.display

    def action_open_help(self) -> None:
        self.push_screen(HelpModal())

    def action_open_spotlight(self) -> None:
        nav_items = [(app_id, label) for app_id, _, label, _ in BUILTIN_NAV]
        for lp in self.plugin_registry.loaded:
            nav_items.append((lp.plugin.id, f"{lp.plugin.name} (Plugin)"))
        entries = build_spotlight_entries(nav_items)

        def _on_pick(res: tuple[str, str] | None) -> None:
            if res is None:
                return
            kind, target = res
            if kind == "app":
                self.switch_app(target)
            elif kind == "file":
                self.open_file_in_appropriate_app(Path(target))

        self.push_screen(SpotlightModal(entries), _on_pick)

    def action_go_app(self, app_id: str) -> None:
        self.switch_app(app_id)

    def action_cycle_theme(self) -> None:
        self._theme_idx = (self._theme_idx + 1) % len(AVAILABLE_THEMES)
        self.theme = AVAILABLE_THEMES[self._theme_idx]
        save_json("settings.json", {"theme": self.theme})
        self.notify(f"Theme: {self.theme} (saved)", timeout=2)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid == "top-theme":
            self.action_cycle_theme()
        elif bid == "top-spotlight":
            self.action_open_spotlight()
        elif bid == "top-help":
            self.action_open_help()
        elif bid == "top-quit":
            self.exit()
