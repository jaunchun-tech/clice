"""Clice Command Runner — Run shell commands & save reusable dev snippets."""

from __future__ import annotations

import subprocess
from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, ListItem, ListView, Static, TextArea

from clice.core.config import load_json, save_json

DEFAULT_SNIPPETS = [
    "git status -sb",
    "git log -n 10 --oneline",
    "python3 --version",
    "ls -la",
]


class CommandRunnerApp(Vertical):
    """Cross-platform shell command runner with saved favorite dev snippets."""

    def __init__(self) -> None:
        super().__init__()
        self.snippets: list[str] = load_json("cmd_snippets.json", DEFAULT_SNIPPETS)

    def compose(self) -> ComposeResult:
        with Horizontal(classes="toolbar"):
            yield Static("[b #22d3ee]\\[$] Clice Command Runner[/b #22d3ee]", classes="app-title")
            yield Input(value="git status -sb", placeholder="Shell command to run...", id="cmd-input")
            yield Button("▶ Run (Enter)", variant="success", id="cmd-run")
            yield Button("+ Save Snippet", variant="primary", id="cmd-save")

        with Horizontal(id="slides-split"):
            with Vertical(id="slides-list"):
                yield Static("[b]Saved Snippets[/b]")
                yield ListView(id="cmd-snippets")
            yield TextArea("Output will appear here...", id="cmd-output", classes="code-area")

        yield Static(f"CWD: {Path.cwd()}  •  Press Enter to run command", id="cmd-status", classes="status-strip")

    def on_mount(self) -> None:
        self._render_snippets()
        self.query_one("#cmd-input", Input).focus()

    def _render_snippets(self) -> None:
        lv = self.query_one("#cmd-snippets", ListView)
        lv.clear()
        for s in self.snippets:
            lv.append(ListItem(Static(f"$ {s}")))

    def _run_cmd(self, cmd: str) -> None:
        cmd = cmd.strip()
        if not cmd:
            return
        self.query_one("#cmd-status", Static).update(f"Running: {cmd} ...")
        self._exec_bg(cmd)

    @work(thread=True)
    def _exec_bg(self, cmd: str) -> None:
        try:
            proc = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=Path.cwd(),
                timeout=30,
            )
            out = (proc.stdout or "") + (("\n--- STDERR ---\n" + proc.stderr) if proc.stderr else "")
            self.app.call_from_thread(self._show_output, cmd, proc.returncode, out or "(no output)")
        except Exception as exc:
            self.app.call_from_thread(self._show_output, cmd, -1, f"Error: {exc}")

    def _show_output(self, cmd: str, rc: int, output: str) -> None:
        self.query_one("#cmd-output", TextArea).text = output
        self.query_one("#cmd-status", Static).update(f"Exit code {rc}  •  $ {cmd}")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "cmd-input":
            self._run_cmd(event.value)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "cmd-snippets" and event.list_view.index is not None:
            idx = event.list_view.index
            if 0 <= idx < len(self.snippets):
                cmd = self.snippets[idx]
                self.query_one("#cmd-input", Input).value = cmd
                self._run_cmd(cmd)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "cmd-run":
            self._run_cmd(self.query_one("#cmd-input", Input).value)
        elif bid == "cmd-save":
            cmd = self.query_one("#cmd-input", Input).value.strip()
            if cmd and cmd not in self.snippets:
                self.snippets.insert(0, cmd)
                save_json("cmd_snippets.json", self.snippets)
                self._render_snippets()
                self.notify(f"Saved snippet: {cmd}", timeout=2)
