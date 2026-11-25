"""Clice Notes & Tasks — Persistent To-Do Manager & Quick Scratchpad Notes."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Input, Select, Static, TextArea

from clice.core.config import load_json, save_json


class NotesApp(Vertical):
    """Persistent To-Do list + Quick Markdown Notes."""

    def __init__(self) -> None:
        super().__init__()
        self.tasks: list[dict[str, str | bool]] = load_json(
            "tasks.json",
            [
                {"title": "Try Clice Sheets formulas", "priority": "High", "done": False},
                {"title": "Create a presentation in Clice Slides", "priority": "Medium", "done": False},
            ],
        )
        self.note_text: str = load_json("quick_note.json", {"text": "# Quick Notes\n\nWrite anything here — saved automatically!"}).get("text", "")

    def compose(self) -> ComposeResult:
        with Horizontal(classes="toolbar"):
            yield Static("[b #ec4899]✅ Clice Notes & Tasks[/b #ec4899]", classes="app-title")
            yield Input(placeholder="New task title...", id="task-input")
            yield Select(
                [("High", "High"), ("Medium", "Medium"), ("Low", "Low")],
                value="Medium",
                id="task-priority",
            )
            yield Button("+ Add Task", variant="primary", id="task-add")
            yield Button("Toggle Done", variant="success", id="task-toggle")
            yield Button("Delete", variant="error", id="task-del")

        with Horizontal():
            with Vertical():
                yield Static("[b]📋 Tasks[/b]")
                yield DataTable(id="tasks-table", cursor_type="row")
            with Vertical():
                with Horizontal(classes="toolbar"):
                    yield Static("[b]🗒️ Quick Notes[/b]")
                    yield Button("Save Note", variant="primary", id="note-save")
                yield TextArea(self.note_text, language="markdown", id="note-area", classes="code-area")

        yield Static("Tasks & notes are saved automatically to ~/.clice/data/", id="notes-status", classes="status-strip")

    def on_mount(self) -> None:
        self._refresh_tasks()

    def _refresh_tasks(self) -> None:
        table = self.query_one("#tasks-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Done", "Priority", "Task")
        for t in self.tasks:
            mark = "✅" if t.get("done") else "⬜"
            table.add_row(mark, str(t.get("priority", "Medium")), str(t.get("title", "")))

    def _save_tasks(self) -> None:
        save_json("tasks.json", self.tasks)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        status = self.query_one("#notes-status", Static)
        table = self.query_one("#tasks-table", DataTable)

        if bid == "task-add":
            title = self.query_one("#task-input", Input).value.strip()
            if not title:
                status.update("Enter a task title first")
                return
            prio = str(self.query_one("#task-priority", Select).value or "Medium")
            self.tasks.append({"title": title, "priority": prio, "done": False})
            self.query_one("#task-input", Input).value = ""
            self._save_tasks()
            self._refresh_tasks()
            status.update(f"Added task: {title}")
        elif bid == "task-toggle":
            idx = table.cursor_row
            if idx is not None and 0 <= idx < len(self.tasks):
                self.tasks[idx]["done"] = not bool(self.tasks[idx].get("done"))
                self._save_tasks()
                self._refresh_tasks()
                status.update("Toggled task status")
        elif bid == "task-del":
            idx = table.cursor_row
            if idx is not None and 0 <= idx < len(self.tasks):
                removed = self.tasks.pop(idx)
                self._save_tasks()
                self._refresh_tasks()
                status.update(f"Deleted task: {removed.get('title')}")
        elif bid == "note-save":
            text = self.query_one("#note-area", TextArea).text
            save_json("quick_note.json", {"text": text})
            status.update("Saved quick note!")
