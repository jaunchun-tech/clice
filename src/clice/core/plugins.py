"""Extensible local plugin system for Clice.

Drop any `.py` file into `~/.clice/plugins/` (or `./plugins/`) defining a subclass
of `ClicePlugin` (or a top-level `PLUGIN` instance) and Clice will automatically
discover and mount it as a first-class app in the sidebar and launcher.
"""

from __future__ import annotations

import importlib.util
import inspect
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from textual.widget import Widget

from clice.core.config import get_plugins_dir


class ClicePlugin:
    """Base class for all Clice plugins."""

    id: str = "custom_plugin"
    name: str = "Custom Plugin"
    icon: str = "🧩"
    description: str = "A custom Clice plugin."
    version: str = "0.1.0"
    author: str = "Unknown"
    category: str = "Plugins"

    def create_widget(self) -> Widget:
        """Return the Textual Widget to render when this plugin app is opened."""
        raise NotImplementedError("Plugins must implement create_widget()")


@dataclass
class LoadedPlugin:
    plugin: ClicePlugin
    source_path: Path
    error: str | None = None


@dataclass
class PluginRegistry:
    loaded: list[LoadedPlugin] = field(default_factory=list)
    errors: list[tuple[Path, str]] = field(default_factory=list)

    def discover(self, extra_dirs: list[Path] | None = None) -> None:
        """Discover and load plugins from ~/.clice/plugins, ./plugins, and extra_dirs."""
        self.loaded.clear()
        self.errors.clear()

        search_dirs: list[Path] = [get_plugins_dir(), Path.cwd() / "plugins"]
        if extra_dirs:
            search_dirs.extend(extra_dirs)

        seen_paths: set[Path] = set()
        seen_ids: set[str] = set()

        for directory in search_dirs:
            if not directory.exists() or not directory.is_dir():
                continue
            for py_file in sorted(directory.glob("*.py")):
                if py_file.name.startswith("_"):
                    continue
                resolved = py_file.resolve()
                if resolved in seen_paths:
                    continue
                seen_paths.add(resolved)
                self._load_file(resolved, seen_ids)

    def _load_file(self, path: Path, seen_ids: set[str]) -> None:
        module_name = f"clice_user_plugin_{path.stem}_{abs(hash(str(path))) % 100000}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                self.errors.append((path, "Could not create module spec"))
                return
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            candidates: list[ClicePlugin] = []
            if hasattr(module, "PLUGIN") and isinstance(module.PLUGIN, ClicePlugin):
                candidates.append(module.PLUGIN)
            else:
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, ClicePlugin) and obj is not ClicePlugin:
                        candidates.append(obj())

            if not candidates:
                self.errors.append((path, "No ClicePlugin subclass or PLUGIN instance found"))
                return

            for plugin in candidates:
                if plugin.id in seen_ids:
                    continue
                seen_ids.add(plugin.id)
                self.loaded.append(LoadedPlugin(plugin=plugin, source_path=path))
        except Exception as exc:
            self.errors.append((path, f"{type(exc).__name__}: {exc}"))


PLUGIN_TEMPLATE = '''"""Example Clice Plugin — {name}."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Input, Label, Static

from clice.core.plugins import ClicePlugin


class {class_name}Widget(Vertical):
    """Main UI for the {name} plugin."""

    def compose(self) -> ComposeResult:
        yield Static("🧩 {name} Plugin", classes="app-title")
        yield Label("Edit this file to build your own Clice app!")
        yield Input(placeholder="Type something...", id="plugin-input")
        yield Button("Run Action", variant="primary", id="plugin-btn")
        yield Static("", id="plugin-output")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "plugin-btn":
            val = self.query_one("#plugin-input", Input).value
            self.query_one("#plugin-output", Static).update(f"You entered: {{val or '(empty)'}}")


class {class_name}Plugin(ClicePlugin):
    id = "{plugin_id}"
    name = "{name}"
    icon = "🧩"
    description = "Custom plugin created with Clice."
    version = "0.1.0"
    author = "You"

    def create_widget(self) -> Vertical:
        return {class_name}Widget()
'''


def create_plugin_template(name: str, target_dir: Path | None = None) -> Path:
    """Scaffold a new ready-to-run plugin file in ~/.clice/plugins."""
    clean = "".join(ch if ch.isalnum() else "_" for ch in name.strip()).strip("_").lower()
    if not clean:
        clean = "my_plugin"
    class_name = "".join(part.capitalize() for part in clean.split("_")) or "MyPlugin"
    dest_dir = target_dir or get_plugins_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / f"{clean}.py"
    content = PLUGIN_TEMPLATE.format(
        name=name.strip() or "My Plugin",
        class_name=class_name,
        plugin_id=f"plugin_{clean}",
    )
    path.write_text(content, encoding="utf-8")
    return path
