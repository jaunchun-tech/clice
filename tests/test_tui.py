"""End-to-end Textual Pilot TUI tests for CliceApp."""

from pathlib import Path

import pytest

from clice.app import CliceApp


@pytest.mark.asyncio
async def test_clice_switches_all_built_in_apps():
    app = CliceApp()
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert app.current_app_id == "home"

        for app_id in [
            "sheets",
            "docs",
            "slides",
            "files",
            "devtools",
            "calc",
            "notes",
            "calendar",
            "kanban",
            "sql",
            "http",
            "runner",
            "sysmon",
            "plugins",
            "home",
        ]:
            app.switch_app(app_id)
            await pilot.pause()
            assert app.current_app_id == app_id


@pytest.mark.asyncio
async def test_clice_theme_cycle_and_plugin_mount():
    examples_dir = Path(__file__).resolve().parent.parent / "examples" / "plugins"
    app = CliceApp(extra_plugin_dirs=[examples_dir])
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        first_theme = app.theme
        app.action_cycle_theme()
        await pilot.pause()
        assert app.theme != first_theme

        app.switch_app("plugin_git_quick")
        await pilot.pause()
        assert app.current_app_id == "plugin_git_quick"
