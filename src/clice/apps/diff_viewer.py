"""Clice Diff Viewer — Side-by-side text/code diff tool with colorized unified diff."""

from __future__ import annotations

import difflib

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Static, TextArea


class DiffViewerApp(Vertical):
    """Compare two blocks of text or code with colorized unified diff output."""

    def compose(self) -> ComposeResult:
        with Horizontal(classes="toolbar"):
            yield Static("[b #f43f5e]\\[≠] Clice Diff Viewer[/b #f43f5e]", classes="app-title")
            yield Button("▶ Compare Diff", variant="success", id="diff-run")
            yield Button("Swap A ↔ B", id="diff-swap")
            yield Button("Clear", variant="warning", id="diff-clear")

        with Horizontal(id="docs-split"):
            yield TextArea("def greet(name):\n    print('Hello ' + name)\n    return True\n", id="diff-left", classes="code-area")
            yield TextArea("def greet(name: str) -> bool:\n    print(f'Hello, {name}!')\n    return True\n", id="diff-right", classes="code-area")

        with VerticalScroll(classes="metric-box"):
            yield Static("Click 'Compare Diff' to see line-by-line differences.", id="diff-output")

    def on_mount(self) -> None:
        self._compute_diff()

    def _compute_diff(self) -> None:
        left = self.query_one("#diff-left", TextArea).text.splitlines()
        right = self.query_one("#diff-right", TextArea).text.splitlines()
        diff = list(difflib.unified_diff(left, right, fromfile="Original (A)", tofile="Modified (B)", lineterm=""))
        out = self.query_one("#diff-output", Static)
        if not diff:
            out.update("[b green]✅ Identical — No differences found![/b green]")
            return
        rendered: list[str] = []
        for line in diff:
            esc = line.replace("[", "\\[")
            if line.startswith("+++") or line.startswith("---"):
                rendered.append(f"[b cyan]{esc}[/b cyan]")
            elif line.startswith("@@"):
                rendered.append(f"[b magenta]{esc}[/b magenta]")
            elif line.startswith("+"):
                rendered.append(f"[green]{esc}[/green]")
            elif line.startswith("-"):
                rendered.append(f"[red]{esc}[/red]")
            else:
                rendered.append(f"[dim]{esc}[/dim]")
        out.update("\n".join(rendered))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "diff-run":
            self._compute_diff()
        elif bid == "diff-swap":
            l_ed = self.query_one("#diff-left", TextArea)
            r_ed = self.query_one("#diff-right", TextArea)
            l_ed.text, r_ed.text = r_ed.text, l_ed.text
            self._compute_diff()
        elif bid == "diff-clear":
            self.query_one("#diff-left", TextArea).text = ""
            self.query_one("#diff-right", TextArea).text = ""
            self._compute_diff()
