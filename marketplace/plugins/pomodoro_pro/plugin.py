"""Clice Marketplace Plugin: Pomodoro Pro — Focus & Break Timer with Progress Bar."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, ProgressBar, Static

from clice.core.plugins import ClicePlugin


class PomodoroProWidget(Vertical):
    """Animated Pomodoro Focus & Short/Long Break timer."""

    def __init__(self) -> None:
        super().__init__()
        self.total_secs = 25 * 60
        self.remaining = self.total_secs
        self.running = False
        self.mode = "Focus (25m)"

    def compose(self) -> ComposeResult:
        with Horizontal(classes="toolbar"):
            yield Static("[b #f43f5e]\\[T] Pomodoro Pro (Plugin)[/b #f43f5e]", classes="app-title")
            yield Button("Focus 25m", variant="primary", id="pp-25")
            yield Button("Short Break 5m", id="pp-5")
            yield Button("Long Break 15m", id="pp-15")
            yield Button("▶ Start", variant="success", id="pp-start")
            yield Button("⏸ Pause", variant="warning", id="pp-pause")
            yield Button("↺ Reset", id="pp-reset")

        with Vertical(classes="metric-box"):
            yield Static("[b]Focus (25m)[/b] — 25:00", id="pp-display")
            yield ProgressBar(total=100, show_eta=False, id="pp-bar")

    def on_mount(self) -> None:
        self.set_interval(1.0, self._tick)

    def _render_timer(self) -> None:
        m, s = divmod(self.remaining, 60)
        pct = ((self.total_secs - self.remaining) / max(1, self.total_secs)) * 100
        self.query_one("#pp-display", Static).update(f"[b #f43f5e]{self.mode}[/b #f43f5e]  —  [b]{m:02d}:{s:02d}[/b]")
        self.query_one("#pp-bar", ProgressBar).update(progress=pct)

    def _tick(self) -> None:
        if not self.running:
            return
        if self.remaining > 0:
            self.remaining -= 1
            self._render_timer()
        else:
            self.running = False
            self.notify(f"{self.mode} finished!", timeout=5)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "pp-25":
            self.mode, self.total_secs, self.remaining, self.running = "Focus (25m)", 25 * 60, 25 * 60, False
            self._render_timer()
        elif bid == "pp-5":
            self.mode, self.total_secs, self.remaining, self.running = "Short Break (5m)", 5 * 60, 5 * 60, False
            self._render_timer()
        elif bid == "pp-15":
            self.mode, self.total_secs, self.remaining, self.running = "Long Break (15m)", 15 * 60, 15 * 60, False
            self._render_timer()
        elif bid == "pp-start":
            self.running = True
        elif bid == "pp-pause":
            self.running = False
        elif bid == "pp-reset":
            self.running = False
            self.remaining = self.total_secs
            self._render_timer()


class PomodoroProPlugin(ClicePlugin):
    id = "plugin_pomodoro_pro"
    name = "Pomodoro Pro"
    icon = "[T]"
    description = "Focus, Short Break & Long Break timer with animated progress bar."
    version = "0.1.0"
    author = "Clice Marketplace"

    def create_widget(self) -> Vertical:
        return PomodoroProWidget()
