"""Clice Plugins & GitHub Marketplace Manager (default: jaunchun-tech/clice-marketplace)."""

from __future__ import annotations

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, DataTable, Input, Markdown, Static, TabbedContent, TabPane

from clice.core.config import get_plugins_dir
from clice.core.marketplace import (
    DEFAULT_MARKETPLACE_REPO,
    MarketplacePluginInfo,
    fetch_marketplace_readme,
    install_marketplace_plugin,
    list_marketplace_plugins,
)
from clice.core.plugins import PluginRegistry, create_plugin_template


class PluginsViewApp(Vertical):
    """Manage local plugins and browse/install from GitHub Marketplace (jaunchun-tech/clice-marketplace)."""

    BINDINGS = [
        Binding("r", "reload_plugins", "Reload"),
        Binding("enter", "launch_selected", "Launch Plugin"),
    ]

    def __init__(self, registry: PluginRegistry) -> None:
        super().__init__()
        self.registry = registry
        self._remote_plugins: list[MarketplacePluginInfo] = []

    def compose(self) -> ComposeResult:
        with Horizontal(classes="toolbar"):
            yield Static("[b #8b5cf6][+] Clice Plugins & Marketplace[/b #8b5cf6]", classes="app-title")
            yield Static(f"[dim]Local dir: {get_plugins_dir()}[/dim]")

        with TabbedContent(id="plugins-tabs"):
            with TabPane("Installed Plugins", id="ptab-installed"):
                with Horizontal(classes="toolbar"):
                    yield Input(placeholder="New plugin name (scaffolds plugins/<name>/ + readme/<name>/)...", id="plugin-new-name")
                    yield Button("+ Create Template", variant="success", id="plugin-create")
                    yield Button("Reload (R)", variant="primary", id="plugin-reload")
                    yield Button("Launch (Enter)", id="plugin-launch")

                with Horizontal(id="docs-split"):
                    yield DataTable(id="plugins-table", cursor_type="row")
                    with VerticalScroll(id="docs-preview-scroll"):
                        yield Markdown("_Select a plugin to view its README.md_", id="plugin-readme-view")

            with TabPane("GitHub Marketplace", id="ptab-marketplace"):
                with Horizontal(classes="toolbar"):
                    yield Input(
                        value=DEFAULT_MARKETPLACE_REPO,
                        placeholder="GitHub repo (owner/repo)...",
                        id="mkt-repo-input",
                    )
                    yield Button("Fetch Marketplace", variant="primary", id="mkt-fetch")
                    yield Button("Install Selected", variant="success", id="mkt-install")

                with Horizontal(id="docs-split"):
                    yield DataTable(id="mkt-table", cursor_type="row")
                    with VerticalScroll(id="docs-preview-scroll"):
                        yield Markdown(
                            f"# Clice GitHub Marketplace\n\n"
                            f"Default repo: **`{DEFAULT_MARKETPLACE_REPO}`**\n\n"
                            "Click **Fetch Marketplace** to browse plugins from `plugins/<slug>/` "
                            "and preview `readme/<slug>/README.md`!",
                            id="mkt-readme-view",
                        )

        yield Static("", id="plugins-status", classes="status-strip")

    def on_mount(self) -> None:
        self._refresh_installed()
        self.query_one("#plugins-table", DataTable).focus()
        # Automatically pull latest plugins from GitHub Marketplace in background
        self._auto_pull_marketplace(DEFAULT_MARKETPLACE_REPO)

    @work(thread=True)
    def _auto_pull_marketplace(self, repo: str) -> None:
        try:
            plugins = list_marketplace_plugins(repo)
            first_md = ""
            if plugins:
                first_md = fetch_marketplace_readme(plugins[0].slug, repo=plugins[0].repo)
            self.app.call_from_thread(self._apply_marketplace_results, repo, plugins, first_md, None)
        except Exception as exc:
            self.app.call_from_thread(self._apply_marketplace_results, repo, [], "", str(exc))

    def _apply_marketplace_results(
        self,
        repo: str,
        plugins: list[MarketplacePluginInfo],
        first_md: str,
        error: str | None,
    ) -> None:
        status = self.query_one("#plugins-status", Static)
        if error:
            status.update(f"Marketplace auto-pull ({repo}): {error}")
            return
        self._remote_plugins = plugins
        table = self.query_one("#mkt-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Plugin Slug", "Repository", "Status")
        installed_dirs = {p.name for p in get_plugins_dir().iterdir() if p.is_dir()} if get_plugins_dir().exists() else set()
        for info in self._remote_plugins:
            st = "Installed" if info.slug in installed_dirs else "Available"
            table.add_row(info.slug, info.repo, st)
        if first_md:
            self.query_one("#mkt-readme-view", Markdown).update(first_md)
        status.update(f"Auto-pulled {len(plugins)} plugin(s) from {repo}")

    def _refresh_installed(self) -> None:
        table = self.query_one("#plugins-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Icon", "Name", "Version", "Author")
        for lp in self.registry.loaded:
            p = lp.plugin
            table.add_row(p.icon, p.name, p.version, p.author)

        if self.registry.loaded:
            self.query_one("#plugin-readme-view", Markdown).update(self.registry.loaded[0].read_readme())
        else:
            self.query_one("#plugin-readme-view", Markdown).update(
                "_No plugins installed yet. Switch to the **GitHub Marketplace** tab to install from "
                f"`{DEFAULT_MARKETPLACE_REPO}` or create a local template above!_"
            )

        err_msg = f"  •  {len(self.registry.errors)} error(s)" if self.registry.errors else ""
        self.query_one("#plugins-status", Static).update(
            f"Installed: {len(self.registry.loaded)} plugin(s){err_msg}  •  ↑/↓ Preview README  •  Enter Launch  •  R Reload"
        )

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.data_table.id == "plugins-table":
            idx = event.cursor_row
            if 0 <= idx < len(self.registry.loaded):
                self.query_one("#plugin-readme-view", Markdown).update(
                    self.registry.loaded[idx].read_readme()
                )
        elif event.data_table.id == "mkt-table":
            idx = event.cursor_row
            if 0 <= idx < len(self._remote_plugins):
                info = self._remote_plugins[idx]
                try:
                    md = fetch_marketplace_readme(info.slug, repo=info.repo)
                except Exception as exc:
                    md = f"_Could not fetch README: {exc}_"
                self.query_one("#mkt-readme-view", Markdown).update(md)

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
        self._refresh_installed()
        self.query_one("#plugins-status", Static).update("Reloaded plugins!")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        status = self.query_one("#plugins-status", Static)

        if bid == "plugin-create":
            name = self.query_one("#plugin-new-name", Input).value.strip()
            if not name:
                status.update("Enter a plugin name first")
                return
            path = create_plugin_template(name, target_dir=get_plugins_dir())
            self.query_one("#plugin-new-name", Input).value = ""
            if hasattr(self.app, "reload_plugins"):
                self.app.reload_plugins()  # type: ignore[attr-defined]
            self._refresh_installed()
            status.update(f"Created & loaded: {path}")
        elif bid == "plugin-reload":
            self.action_reload_plugins()
        elif bid == "plugin-launch":
            self.action_launch_selected()
        elif bid == "mkt-fetch":
            repo = self.query_one("#mkt-repo-input", Input).value.strip() or DEFAULT_MARKETPLACE_REPO
            status.update(f"Fetching marketplace from {repo}...")
            try:
                self._remote_plugins = list_marketplace_plugins(repo)
                table = self.query_one("#mkt-table", DataTable)
                table.clear(columns=True)
                table.add_columns("Plugin Slug", "Repository")
                for info in self._remote_plugins:
                    table.add_row(info.slug, info.repo)
                if self._remote_plugins:
                    first = self._remote_plugins[0]
                    self.query_one("#mkt-readme-view", Markdown).update(
                        fetch_marketplace_readme(first.slug, repo=first.repo)
                    )
                    status.update(f"Found {len(self._remote_plugins)} plugin(s) in {repo}")
                else:
                    status.update(f"No plugin folders found under plugins/ in {repo}")
            except Exception as exc:
                status.update(f"Marketplace fetch error: {exc}")
        elif bid == "mkt-install":
            table = self.query_one("#mkt-table", DataTable)
            idx = table.cursor_row
            if idx is None or not (0 <= idx < len(self._remote_plugins)):
                status.update("Select a marketplace plugin first")
                return
            info = self._remote_plugins[idx]
            try:
                dest = install_marketplace_plugin(info.slug, repo=info.repo)
                if hasattr(self.app, "reload_plugins"):
                    self.app.reload_plugins()  # type: ignore[attr-defined]
                self._refresh_installed()
                status.update(f"Installed '{info.slug}' to {dest}!")
                self.notify(f"Installed plugin: {info.slug}", timeout=3)
            except Exception as exc:
                status.update(f"Install error: {exc}")
