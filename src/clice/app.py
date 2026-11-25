"""Main Clice Textual Desktop Shell — Top Ribbon, Left App Dock, Workspace, Themes & Plugins."""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Static

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

NAV_SECTIONS: list[tuple[str, list[tuple[str, str]]]] = [
    (
        "OFFICE SUITE",
        [
            ("home", "🏠 Home"),
            ("sheets", "📊 Sheets (Excel)"),
            ("docs", "📝 Docs (Word)"),
            ("slides", "📽️ Slides (PPT)"),
        ],
    ),
    (
        "WORKSPACE & DEV",
        [
            ("files", "📁 Files & cd"),
            ("devtools", "💻 Coding Utils"),
            ("calc", "🧮 Calculator"),
            ("notes", "✅ Notes & Tasks"),
            ("calendar", "📅 Calendar"),
            ("sysmon", "🖥️ SysMon"),
        ],
    ),
    (
        "EXTENSIONS",
        [
            ("plugins", "🧩 Plugins"),
        ],
    ),
]


class CliceApp(App[str | None]):
    """Clice — Colorful GUI-like Terminal Office Suite & Developer Multitool."""

    TITLE = f"Clice v{__version__}"
    SUB_TITLE = "Terminal Office & Dev Suite"
    CSS = CLICE_CSS

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("f1", "go_app('home')", "Home"),
        Binding("f2", "go_app('sheets')", "Sheets"),
        Binding("f3", "go_app('docs')", "Docs"),
        Binding("f4", "go_app('slides')", "Slides"),
        Binding("f5", "go_app('files')", "Files"),
        Binding("f6", "go_app('devtools')", "DevTools"),
        Binding("ctrl+t", "cycle_theme", "Theme"),
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
        self.plugin_registry = PluginRegistry()
        self.plugin_registry.discover(self.extra_plugin_dirs)

    def compose(self) -> ComposeResult:
        with Horizontal(id="top-bar"):
            yield Static(f"✨ CLICE v{__version__}", id="brand-badge")
            yield Static(f"📂 {Path.cwd()}", id="top-cwd")
            with Horizontal(id="top-actions"):
                yield Button("🎨 Theme", id="top-theme")
                yield Button("🏠 Home", id="top-home")
                yield Button("✖ Quit", variant="error", id="top-quit")

        with Horizontal(id="main-shell"):
            with Vertical(id="sidebar"):
                for section_title, items in NAV_SECTIONS:
                    yield Static(section_title, classes="sidebar-section")
                    for app_id, label in items:
                        yield Button(label, id=f"nav-{app_id}", classes="nav-btn")
                yield Vertical(id="plugin-nav-container")

            yield Vertical(id="workspace")

        yield Footer()

    def on_mount(self) -> None:
        self.theme = AVAILABLE_THEMES[self._theme_idx]
        self._populate_plugin_nav()
        if self.initial_file and self.initial_file.exists():
            self.open_file_in_appropriate_app(self.initial_file)
        else:
            self.switch_app(self.initial_app)

    def _populate_plugin_nav(self) -> None:
        container = self.query_one("#plugin-nav-container", Vertical)
        container.remove_children()
        if self.plugin_registry.loaded:
            container.mount(Static("INSTALLED PLUGINS", classes="sidebar-section"))
            for lp in self.plugin_registry.loaded:
                p = lp.plugin
                container.mount(Button(f"{p.icon} {p.name}", id=f"nav-{p.id}", classes="nav-btn"))

    def reload_plugins(self) -> None:
        self.plugin_registry.discover(self.extra_plugin_dirs)
        self._populate_plugin_nav()

    def update_cwd_display(self, path: Path) -> None:
        self.query_one("#top-cwd", Static).update(f"📂 {path}")

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
        elif ext in (".pptx", ".json"):
            self.switch_app("slides" if ext == ".pptx" else "devtools", file_path=path)
        else:
            self.switch_app("devtools", file_path=path)

    def switch_app(self, app_id: str, file_path: Path | None = None) -> None:
        self.current_app_id = app_id

        # Highlight active sidebar button
        for btn in self.query(".nav-btn"):
            btn.remove_class("-active")
            if btn.id == f"nav-{app_id}":
                btn.add_class("-active")

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
        elif bid == "top-home":
            self.switch_app("home")
        elif bid == "top-quit":
            self.exit()
        elif bid.startswith("nav-"):
            self.switch_app(bid[4:])
