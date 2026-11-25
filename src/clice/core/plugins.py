"""Extensible local & marketplace-ready plugin system for Clice.

Supports two layouts in `~/.clice/plugins/`, `./plugins/`, and `--plugins-dir`:
1. Folder-based (Marketplace layout):
   - `plugins/<plugin_name>/plugin.py` (or `__init__.py` or `<plugin_name>.py`)
   - Matching docs/assets in `readme/<plugin_name>/README.md`
2. Single-file layout:
   - `plugins/<plugin_name>.py`
"""

from __future__ import annotations

import importlib.util
import inspect
from dataclasses import dataclass, field
from pathlib import Path

from textual.widget import Widget

from clice.core.config import get_plugins_dir


class ClicePlugin:
    """Base class for all Clice plugins."""

    id: str = "custom_plugin"
    name: str = "Custom Plugin"
    icon: str = "[+]"
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
    readme_path: Path | None = None
    error: str | None = None

    def read_readme(self) -> str:
        if self.readme_path and self.readme_path.exists():
            try:
                return self.readme_path.read_text(encoding="utf-8")
            except Exception:
                pass
        return (
            f"# {self.plugin.name}\n\n"
            f"{self.plugin.description}\n\n"
            f"- **ID:** `{self.plugin.id}`\n"
            f"- **Version:** `{self.plugin.version}`\n"
            f"- **Author:** {self.plugin.author}\n"
            f"- **Source:** `{self.source_path}`\n"
        )


def _find_readme_for_plugin(plugin_dir: Path, slug: str) -> Path | None:
    """Look for readme/<slug>/README.md next to the plugins/ directory or inside plugin_dir."""
    candidates = [
        plugin_dir.parent / "readme" / slug / "README.md",
        plugin_dir.parent.parent / "readme" / slug / "README.md",
        Path.cwd() / "readme" / slug / "README.md",
        plugin_dir / "README.md",
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            return c.resolve()
    return None


@dataclass
class PluginRegistry:
    loaded: list[LoadedPlugin] = field(default_factory=list)
    errors: list[tuple[Path, str]] = field(default_factory=list)

    def discover(self, extra_dirs: list[Path] | None = None) -> None:
        """Discover and load plugins from ~/.clice/plugins, ./plugins, and extra_dirs."""
        self.loaded.clear()
        self.errors.clear()

        search_dirs: list[Path] = [Path.cwd() / "plugins", get_plugins_dir()]
        if extra_dirs:
            search_dirs.extend(extra_dirs)

        seen_paths: set[Path] = set()
        seen_ids: set[str] = set()

        for directory in search_dirs:
            if not directory.exists() or not directory.is_dir():
                continue

            # 1. Folder-based plugins: plugins/<slug>/plugin.py | __init__.py | <slug>.py
            for sub in sorted(directory.iterdir()):
                if sub.is_dir() and not sub.name.startswith(("_", ".")):
                    entry = None
                    for fname in ("plugin.py", f"{sub.name}.py", "__init__.py"):
                        cand = sub / fname
                        if cand.exists() and cand.is_file():
                            entry = cand.resolve()
                            break
                    if entry is None:
                        py_files = [p for p in sorted(sub.glob("*.py")) if not p.name.startswith("_")]
                        if py_files:
                            entry = py_files[0].resolve()
                    if entry and entry not in seen_paths:
                        seen_paths.add(entry)
                        readme = _find_readme_for_plugin(sub, sub.name)
                        self._load_file(entry, seen_ids, readme_path=readme)

            # 2. Single-file plugins: plugins/<slug>.py
            for py_file in sorted(directory.glob("*.py")):
                if py_file.name.startswith("_"):
                    continue
                resolved = py_file.resolve()
                if resolved in seen_paths:
                    continue
                seen_paths.add(resolved)
                readme = _find_readme_for_plugin(directory, py_file.stem)
                self._load_file(resolved, seen_ids, readme_path=readme)

    def _load_file(
        self,
        path: Path,
        seen_ids: set[str],
        readme_path: Path | None = None,
    ) -> None:
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
                self.loaded.append(
                    LoadedPlugin(plugin=plugin, source_path=path, readme_path=readme_path)
                )
        except Exception as exc:
            self.errors.append((path, f"{type(exc).__name__}: {exc}"))


PLUGIN_TEMPLATE = '''"""Clice Plugin — {name}."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Input, Label, Static

from clice.core.plugins import ClicePlugin


class {class_name}Widget(Vertical):
    """Main UI for the {name} plugin."""

    def compose(self) -> ComposeResult:
        yield Static("[+] {name} Plugin", classes="app-title")
        yield Label("Edit this file to build your own Clice app! Press Enter to run.")
        yield Input(placeholder="Type something and press Enter...", id="plugin-input")
        yield Button("Run Action", variant="primary", id="plugin-btn")
        yield Static("", id="plugin-output")

    def on_mount(self) -> None:
        self.query_one("#plugin-input", Input).focus()

    def _run(self) -> None:
        val = self.query_one("#plugin-input", Input).value
        self.query_one("#plugin-output", Static).update(f"You entered: {{val or '(empty)'}}")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "plugin-input":
            self._run()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "plugin-btn":
            self._run()


class {class_name}Plugin(ClicePlugin):
    id = "{plugin_id}"
    name = "{name}"
    icon = "[+]"
    description = "Custom plugin created with Clice."
    version = "0.1.0"
    author = "You"

    def create_widget(self) -> Vertical:
        return {class_name}Widget()
'''

README_TEMPLATE = """# {name}

Custom plugin for **Clice**.

## Structure
- Plugin code: `plugins/{slug}/plugin.py`
- Documentation & assets: `readme/{slug}/README.md`

## Usage
Open **Clice** and select **{name}** from the sidebar or press `Ctrl+P` to launch it.
"""


def create_plugin_template(
    name: str,
    target_dir: Path | None = None,
    readme_root: Path | None = None,
) -> Path:
    """Scaffold a new marketplace-layout plugin (`plugins/<slug>/plugin.py` + `readme/<slug>/README.md`)."""
    clean = "".join(ch if ch.isalnum() else "_" for ch in name.strip()).strip("_").lower()
    if not clean:
        clean = "my_plugin"
    class_name = "".join(part.capitalize() for part in clean.split("_")) or "MyPlugin"

    plugins_root = target_dir or (Path.cwd() / "plugins")
    plugin_folder = plugins_root / clean
    plugin_folder.mkdir(parents=True, exist_ok=True)
    plugin_path = plugin_folder / "plugin.py"

    content = PLUGIN_TEMPLATE.format(
        name=name.strip() or "My Plugin",
        class_name=class_name,
        plugin_id=f"plugin_{clean}",
    )
    plugin_path.write_text(content, encoding="utf-8")

    r_root = readme_root or (plugins_root.parent / "readme")
    readme_folder = r_root / clean
    readme_folder.mkdir(parents=True, exist_ok=True)
    (readme_folder / "README.md").write_text(
        README_TEMPLATE.format(name=name.strip() or "My Plugin", slug=clean),
        encoding="utf-8",
    )
    return plugin_path
