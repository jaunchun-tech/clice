"""Clice Plugins Manager — Discover, reload, and scaffold local plugins."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Input, Static

from clice.core.config import get_plugins_dir
from clice.core.plugins import PluginRegistry, create_plugin_template


class PluginsViewApp(Vertical):
    """Manage local Clice plugins and scaffold new ones."""

    def __init__(self, registry: PluginRegistry) -> None:
        super().__init__()
        self.registry = registry

    def compose(self) -> ComposeResult:
        with Horizontal(classes="toolbar"):
            yield Static("[b #8b5cf6]🧩 Clice Plugins[/b #8b5cf6]", classes="app-title")
            yield Input(placeholder="New plugin name (e.g. Git Helper)...", id="plugin-new-name")
            yield Button("+ Create Plugin Template", variant="success", id="plugin-create")
            yield Button("↻ Reload Plugins", variant="primary", id="plugin-reload")

        yield Static(
            f"[b]Plugin Directories:[/b] [cyan]{get_plugins_dir()}[/cyan]  and  [cyan]./plugins[/cyan]\n"
            "[dim]Drop any .py file defining a `ClicePlugin` subclass in either folder and click Reload! "
            "Loaded plugins appear automatically in the left sidebar.[/dim]",
            classes="metric-box",
        )

        yield DataTable(id="plugins-table", cursor_type="row")
        yield Static("", id="plugins-status", classes="status-strip")

    def on_mount(self) -> None:
        self._refresh_table()

    def _refresh_table(self) -> None:
        table = self.query_one("#plugins-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Icon", "Name", "ID", "Version", "Author", "Source")
        for lp in self.registry.loaded:
            p = lp.plugin
            table.add_row(p.icon, p.name, p.id, p.version, p.author, str(lp.source_path))

        err_msg = ""
        if self.registry.errors:
            err_msg = f"  •  {len(self.registry.errors)} load error(s)"
        self.query_one("#plugins-status", Static).update(
            f"Loaded {len(self.registry.loaded)} plugin(s){err_msg}"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        status = self.query_one("#plugins-status", Static)
        if bid == "plugin-create":
            name = self.query_one("#plugin-new-name", Input).value.strip()
            if not name:
                status.update("Enter a plugin name first")
                return
            path = create_plugin_template(name)
            self.query_one("#plugin-new-name", Input).value = ""
            if hasattr(self.app, "reload_plugins"):
                self.app.reload_plugins()  # type: ignore[attr-defined]
            self._refresh_table()
            status.update(f"Created & loaded plugin: {path}")
        elif bid == "plugin-reload":
            if hasattr(self.app, "reload_plugins"):
                self.app.reload_plugins()  # type: ignore[attr-defined]
            self._refresh_table()
            status.update("Reloaded plugins!")
