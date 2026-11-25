"""Cross-platform configuration and persistent storage for Clice."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def get_clice_home() -> Path:
    """Return the cross-platform Clice config/data directory (~/.clice)."""
    home = Path.home() / ".clice"
    home.mkdir(parents=True, exist_ok=True)
    return home


def get_plugins_dir() -> Path:
    """Return the user plugins directory (~/.clice/plugins)."""
    pdir = get_clice_home() / "plugins"
    pdir.mkdir(parents=True, exist_ok=True)
    return pdir


def get_data_file(name: str) -> Path:
    """Return path to a JSON data file inside ~/.clice/data."""
    ddir = get_clice_home() / "data"
    ddir.mkdir(parents=True, exist_ok=True)
    return ddir / name


def load_json(name: str, default: Any) -> Any:
    """Load JSON data from ~/.clice/data/<name>, returning default on error."""
    path = get_data_file(name)
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(name: str, data: Any) -> None:
    """Save JSON data to ~/.clice/data/<name>."""
    path = get_data_file(name)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def add_recent_file(file_path: str | Path, app_id: str) -> None:
    """Record a recently opened/saved file."""
    recents: list[dict[str, str]] = load_json("recent_files.json", [])
    resolved = str(Path(file_path).resolve())
    recents = [r for r in recents if r.get("path") != resolved]
    recents.insert(0, {"path": resolved, "app": app_id, "name": Path(resolved).name})
    save_json("recent_files.json", recents[:20])


def get_recent_files() -> list[dict[str, str]]:
    """Return list of recent files."""
    return load_json("recent_files.json", [])
