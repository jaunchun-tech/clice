"""Clice Kanban Board — 3-Column Visual Task Board (To Do | In Progress | Done)."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, ListItem, ListView, Select, Static

from clice.core.config import load_json, save_json

DEFAULT_BOARD: dict[str, list[dict[str, str]]] = {
    "todo": [
        {"title": "Build custom Clice plugin", "tag": "HIGH"},
        {"title": "Export presentation to .pptx", "tag": "MED"},
    ],
    "doing": [
        {"title": "Test GitHub Marketplace auto-pull", "tag": "HIGH"},
    ],
    "done": [
        {"title": "Install Clice Office & Dev Suite", "tag": "LOW"},
    ],
}


class KanbanApp(Vertical):
    """Trello/Jira-style 3-column Kanban board persisted to ~/.clice/data/kanban.json."""

    def __init__(self) -> None:
        super().__init__()
        self.board: dict[str, list[dict[str, str]]] = load_json("kanban.json", DEFAULT_BOARD)
        self.active_col = "todo"

    def compose(self) -> ComposeResult:
        with Horizontal(classes="toolbar"):
            yield Static("[b #f59e0b]\\[KB] Clice Kanban Board[/b #f59e0b]", classes="app-title")
            yield Input(placeholder="New card title...", id="kb-input")
            yield Select([("HIGH", "HIGH"), ("MED", "MED"), ("LOW", "LOW")], value="MED", id="kb-tag")
            yield Button("+ Add Card", variant="success", id="kb-add")
            yield Button("◀ Move Left", id="kb-left")
            yield Button("Move Right ▶", variant="primary", id="kb-right")
            yield Button("Delete", variant="error", id="kb-del")

        with Horizontal(id="docs-split"):
            with Vertical(classes="metric-box"):
                yield Static("[b #ef4444]● TO DO[/b #ef4444]")
                yield ListView(id="kb-todo")
            with Vertical(classes="metric-box"):
                yield Static("[b #eab308]● IN PROGRESS[/b #eab308]")
                yield ListView(id="kb-doing")
            with Vertical(classes="metric-box"):
                yield Static("[b #22c55e]● DONE[/b #22c55e]")
                yield ListView(id="kb-done")

        yield Static("Select a card and click Move Left / Move Right • Auto-saved to ~/.clice/data/kanban.json", id="kb-status", classes="status-strip")

    def on_mount(self) -> None:
        self._render_board()
        self.query_one("#kb-todo", ListView).focus()

    def _save(self) -> None:
        save_json("kanban.json", self.board)

    def _render_board(self) -> None:
        tag_colors = {"HIGH": "#ef4444", "MED": "#eab308", "LOW": "#22c55e"}
        for col in ("todo", "doing", "done"):
            lv = self.query_one(f"#kb-{col}", ListView)
            lv.clear()
            for card in self.board.get(col, []):
                c = tag_colors.get(card.get("tag", "MED"), "#94a3b8")
                lv.append(ListItem(Static(f"[b {c}]\\[{card.get('tag', 'MED')}][/b {c}] {card.get('title', '')}")))

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.list_view.id and event.list_view.id.startswith("kb-"):
            self.active_col = event.list_view.id[3:]

    def _move_card(self, direction: int) -> None:
        cols = ["todo", "doing", "done"]
        cur_idx = cols.index(self.active_col)
        dst_idx = cur_idx + direction
        if not (0 <= dst_idx < len(cols)):
            return
        lv = self.query_one(f"#kb-{self.active_col}", ListView)
        row = lv.index
        if row is None or not (0 <= row < len(self.board[self.active_col])):
            return
        card = self.board[self.active_col].pop(row)
        self.board[cols[dst_idx]].append(card)
        self.active_col = cols[dst_idx]
        self._save()
        self._render_board()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "kb-add":
            title = self.query_one("#kb-input", Input).value.strip()
            if not title:
                return
            tag = str(self.query_one("#kb-tag", Select).value or "MED")
            self.board["todo"].append({"title": title, "tag": tag})
            self.query_one("#kb-input", Input).value = ""
            self._save()
            self._render_board()
        elif bid == "kb-left":
            self._move_card(-1)
        elif bid == "kb-right":
            self._move_card(1)
        elif bid == "kb-del":
            lv = self.query_one(f"#kb-{self.active_col}", ListView)
            row = lv.index
            if row is not None and 0 <= row < len(self.board[self.active_col]):
                self.board[self.active_col].pop(row)
                self._save()
                self._render_board()
