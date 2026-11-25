"""Clice Calendar & Pomodoro Focus Timer."""

from __future__ import annotations

import calendar
from datetime import date

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Static

from clice.core.config import load_json, save_json


class CalendarApp(Vertical):
    """Interactive Monthly Calendar with Day Events & Pomodoro Focus Timer."""

    def __init__(self) -> None:
        super().__init__()
        today = date.today()
        self.year = today.year
        self.month = today.month
        self.events: dict[str, list[str]] = load_json("calendar_events.json", {})
        self.pomo_seconds = 25 * 60
        self.pomo_running = False

    def compose(self) -> ComposeResult:
        with Horizontal(classes="toolbar"):
            yield Static("[b #14b8a6]📅 Clice Calendar & Focus[/b #14b8a6]", classes="app-title")
            yield Button("◀ Prev Month", id="cal-prev")
            yield Button("Today", variant="primary", id="cal-today")
            yield Button("Next Month ▶", id="cal-next")

        with Horizontal():
            with Vertical(classes="metric-box"):
                yield Static("", id="cal-month-view")
                with Horizontal(classes="toolbar"):
                    yield Input(placeholder="YYYY-MM-DD", value=date.today().isoformat(), id="cal-date")
                    yield Input(placeholder="Event description...", id="cal-event-text")
                    yield Button("+ Add Event", variant="success", id="cal-add-event")
                yield Static("", id="cal-events-list")

            with Vertical(classes="metric-box"):
                yield Static("[b #14b8a6]⏱️ Pomodoro Focus Timer[/b #14b8a6]\n")
                yield Static("[b]25:00[/b]", id="pomo-display")
                with Horizontal(classes="toolbar"):
                    yield Button("▶ Start", variant="success", id="pomo-start")
                    yield Button("⏸ Pause", variant="warning", id="pomo-pause")
                    yield Button("↺ Reset", id="pomo-reset")
                yield Static("[dim]Stay focused for 25 minutes, then take a 5-minute break![/dim]")

    def on_mount(self) -> None:
        self._render_calendar()
        self._render_events()
        self.set_interval(1.0, self._tick_pomodoro)

    def _render_calendar(self) -> None:
        cal_str = calendar.month(self.year, self.month)
        self.query_one("#cal-month-view", Static).update(f"[b #14b8a6]{cal_str}[/b #14b8a6]")

    def _render_events(self) -> None:
        lines = ["[b]📌 Upcoming Events[/b]"]
        if not self.events:
            lines.append("[dim]No events yet. Add one above![/dim]")
        else:
            for d in sorted(self.events.keys())[:10]:
                for ev in self.events[d]:
                    lines.append(f"  • [cyan]{d}[/cyan]: {ev}")
        self.query_one("#cal-events-list", Static).update("\n".join(lines))

    def _tick_pomodoro(self) -> None:
        if not self.pomo_running:
            return
        if self.pomo_seconds > 0:
            self.pomo_seconds -= 1
        else:
            self.pomo_running = False
        mins, secs = divmod(self.pomo_seconds, 60)
        self.query_one("#pomo-display", Static).update(f"[b]{mins:02d}:{secs:02d}[/b]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "cal-prev":
            if self.month == 1:
                self.month = 12
                self.year -= 1
            else:
                self.month -= 1
            self._render_calendar()
        elif bid == "cal-next":
            if self.month == 12:
                self.month = 1
                self.year += 1
            else:
                self.month += 1
            self._render_calendar()
        elif bid == "cal-today":
            today = date.today()
            self.year, self.month = today.year, today.month
            self._render_calendar()
        elif bid == "cal-add-event":
            d = self.query_one("#cal-date", Input).value.strip()
            txt = self.query_one("#cal-event-text", Input).value.strip()
            if d and txt:
                self.events.setdefault(d, []).append(txt)
                save_json("calendar_events.json", self.events)
                self.query_one("#cal-event-text", Input).value = ""
                self._render_events()
        elif bid == "pomo-start":
            self.pomo_running = True
        elif bid == "pomo-pause":
            self.pomo_running = False
        elif bid == "pomo-reset":
            self.pomo_running = False
            self.pomo_seconds = 25 * 60
            self.query_one("#pomo-display", Static).update("[b]25:00[/b]")
