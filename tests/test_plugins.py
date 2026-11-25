"""Tests for the Clice local plugin system."""

from pathlib import Path

from clice.core.plugins import PluginRegistry, create_plugin_template


def test_create_and_discover_plugin(tmp_path: Path):
    created = create_plugin_template("Demo Tool", target_dir=tmp_path)
    assert created.exists()

    reg = PluginRegistry()
    reg.discover(extra_dirs=[tmp_path])
    ids = [lp.plugin.id for lp in reg.loaded]
    assert "plugin_demo_tool" in ids


def test_discover_example_git_plugin():
    examples_dir = Path(__file__).resolve().parent.parent / "examples" / "plugins"
    reg = PluginRegistry()
    reg.discover(extra_dirs=[examples_dir])
    ids = [lp.plugin.id for lp in reg.loaded]
    assert "plugin_git_quick" in ids
