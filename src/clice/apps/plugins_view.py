"""Clice Plugins & Marketplace Manager — Browse plugins/, preview readme/<name>/README.md, scaffold."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, DataTable, Input, Markdown, Static

from clice.core.config import get_plugins_dir
from clice.core.plugins import PluginRegistry, create_plugin_template


class PluginsViewApp(Vertical):
    """Keyboard-first Plugin Manager with live readme/<plugin>/README.md preview."""

    BINDINGS = [
        Binding("r", "reload_plugins", "Reload"),
        Binding("enter", "launch_selected", "Launch Plugin"),
    ]

    def __init__(self, registry: PluginRegistry) -> None:
        super().__init__()
        self.registry = registry

    def compose(self) -> ComposeResult:
        with Horizontal(classes="toolbar"):
            yield Static("[b #8b5cf6][+] Clice Plugins & Marketplace[/b #8b5cf6]", classes="app-title")
            yield Input(placeholder="New plugin name (creates plugins/<name>/ + readme/<name>/)...", id="plugin-new-name")
            yield Button("+ Create Plugin", variant="success", id="plugin-create")
            yield Button("Reload (R)", variant="primary", id="plugin-reload")

        yield Static(
            f"[b]Layout:[/b] [cyan]./plugins/<name>/plugin.py[/cyan]  +  [cyan]./readme/<name>/README.md[/cyan]  "
            f"(also [cyan]{get_plugins_dir()}[/cyan])\n"
            "[dim]Use ↑ / ↓ to inspect a plugin's README, press Enter to launch it![/dim]",
            classes="metric-box",
        )

        with Horizontal(id="docs-split"):
            yield DataTable(id="plugins-table", cursor_type="row")
            with VerticalScroll(id="docs-preview-scroll"):
                yield Markdown("_Select a plugin to view its README.md_", id="plugin-readme-view")

        yield Static("", id="plugins-status", classes="status-strip")

    def on_mount(self) -> None:
        self._refresh_table()
        self.query_one("#plugins-table", DataTable).focus()

    def _refresh_table(self) -> None:
        table = self.query_one("#plugins-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Icon", "Name", "Version", "Author")
        for lp in self.registry.loaded:
            p = lp.plugin
            table.add_row(p.icon, p.name, p.version, p.author)

        if self.registry.loaded:
            self.query_one("#plugin-readme-view", Markdown).update(self.registry.loaded[0].read_readme())
        else:
            self.query_one("#plugin-readme-view", Markdown).update("_No plugins installed yet._")

        err_msg = f"  •  {len(self.registry.errors)} error(s)" if self.registry.errors else ""
        self.query_one("#plugins-status", Static).update(
            f"Loaded {len(self.registry.loaded)} plugin(s){err_msg}  •  ↑/↓ Preview README  •  Enter Launch  •  R Reload"
        )

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.data_table.id == "plugins-table":
            idx = event.cursor_row
            if 0 <= idx < len(self.registry.loaded):
                self.query_one("#plugin-readme-view", Markdown).update(
                    self.registry.loaded[idx].read_readme()
                )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id == "plugins-table":
            self.action_launch_selected()

    def action_launch_selected(self) -> None:
        table = self.query_one("#plugins-table", DataTable)
        idx = table.cursor_row
        if idx is not None and 0 <= idx < len(self.registry.loaded):
            plugin_id = self.registry.loaded[idx].plugin.id
            self.app.switch_app(plugin_id)  # type: ignore[attr-defined]

    def action_reload_plugins(self) -> None:
        if hasattr(self.app, "reload_plugins"):
            self.app.reload_plugins()  # type: ignore[attr-defined]
        self._refresh_table()
        self.query_one("#plugins-status", Static).update("Reloaded plugins!")

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
            status.update(f"Created & loaded: {path}")
        elif bid == "plugin-reload":
            self.action_reload_plugins()
