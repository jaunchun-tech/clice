"""Clice SQLite Studio — Terminal Database IDE (browse tables, run SQL, export CSV)."""

from __future__ import annotations

import csv
import sqlite3
import time
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Input, ListItem, ListView, Static, TextArea

from clice.core.file_picker import FilePickerModal


class SqlStudioApp(Vertical):
    """Interactive SQLite IDE with schema browser, SQL editor, results grid, and CSV export."""

    BINDINGS = [
        Binding("ctrl+enter,f9", "run_query", "Run SQL"),
        Binding("ctrl+o", "open_db", "Open DB"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.db_path: Path | None = None
        self.conn: sqlite3.Connection = sqlite3.connect(":memory:")
        self._seed_demo_db()
        self._tables: list[str] = []
        self._last_cols: list[str] = []
        self._last_rows: list[tuple[object, ...]] = []

    def _seed_demo_db(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, role TEXT, active INTEGER)"
        )
        cur.executemany(
            "INSERT INTO users (name, role, active) VALUES (?, ?, ?)",
            [
                ("Alice", "Admin", 1),
                ("Bob", "Developer", 1),
                ("Charlie", "Designer", 1),
                ("Diana", "Manager", 0),
            ],
        )
        cur.execute(
            "CREATE TABLE projects (id INTEGER PRIMARY KEY, title TEXT, owner_id INTEGER, stars INTEGER)"
        )
        cur.executemany(
            "INSERT INTO projects (title, owner_id, stars) VALUES (?, ?, ?)",
            [
                ("Clice Office", 1, 420),
                ("Clice Marketplace", 2, 185),
                ("Terminal Themes", 3, 96),
            ],
        )
        self.conn.commit()

    def compose(self) -> ComposeResult:
        with Horizontal(classes="toolbar"):
            yield Static("[b #38bdf8]\\[DB] Clice SQLite Studio[/b #38bdf8]", classes="app-title")
            yield Static("[dim]:memory: (demo)[/dim]", id="sql-db-label")
            yield Button("Open .db (^O)", id="sql-open")
            yield Button("▶ Run SQL (^Enter)", variant="success", id="sql-run")
            yield Button("Export CSV", variant="primary", id="sql-export")

        with Horizontal(id="slides-split"):
            with Vertical(id="slides-list"):
                yield Static("[b]Tables[/b]")
                yield ListView(id="sql-tables")
            with Vertical():
                yield TextArea(
                    "SELECT u.name, u.role, p.title AS project, p.stars\n"
                    "FROM users u\n"
                    "LEFT JOIN projects p ON u.id = p.owner_id\n"
                    "ORDER BY p.stars DESC;",
                    language="sql",
                    id="sql-editor",
                    classes="code-area",
                )
                yield DataTable(id="sql-results", cursor_type="row")

        yield Static("Ready • Press Ctrl+Enter to run query • Click a table to preview", id="sql-status", classes="status-strip")

    def on_mount(self) -> None:
        self._refresh_tables()
        self.action_run_query()
        self.query_one("#sql-editor", TextArea).focus()

    def _refresh_tables(self) -> None:
        cur = self.conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        self._tables = [r[0] for r in cur.fetchall()]
        lv = self.query_one("#sql-tables", ListView)
        lv.clear()
        for t in self._tables:
            lv.append(ListItem(Static(f"▸ {t}")))

    def action_run_query(self) -> None:
        sql = self.query_one("#sql-editor", TextArea).text.strip()
        status = self.query_one("#sql-status", Static)
        table = self.query_one("#sql-results", DataTable)
        if not sql:
            return
        t0 = time.perf_counter()
        try:
            cur = self.conn.cursor()
            cur.execute(sql)
            elapsed = (time.perf_counter() - t0) * 1000
            if cur.description:
                cols = [d[0] for d in cur.description]
                rows = cur.fetchall()
                self._last_cols = cols
                self._last_rows = rows
                table.clear(columns=True)
                table.add_columns(*cols)
                for row in rows[:500]:
                    table.add_row(*["" if v is None else str(v) for v in row])
                status.update(f"✅ {len(rows)} row(s) in {elapsed:.1f} ms")
            else:
                self.conn.commit()
                self._refresh_tables()
                status.update(f"✅ Executed ({cur.rowcount} affected) in {elapsed:.1f} ms")
        except Exception as exc:
            status.update(f"❌ SQL Error: {exc}")

    def action_open_db(self) -> None:
        def _on_picked(path: Path | None) -> None:
            if path is not None:
                try:
                    self.conn.close()
                    self.conn = sqlite3.connect(str(path))
                    self.db_path = path
                    self.query_one("#sql-db-label", Static).update(f"[b cyan]{path.name}[/b cyan]")
                    self._refresh_tables()
                    self.notify(f"Opened DB: {path.name}", timeout=2)
                except Exception as exc:
                    self.notify(f"DB error: {exc}", severity="error")

        self.app.push_screen(
            FilePickerModal(
                mode="open",
                title="Open SQLite Database (.db, .sqlite, .sqlite3)",
                extensions=(".db", ".sqlite", ".sqlite3"),
            ),
            _on_picked,
        )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "sql-tables" and event.list_view.index is not None:
            idx = event.list_view.index
            if 0 <= idx < len(self._tables):
                tname = self._tables[idx]
                self.query_one("#sql-editor", TextArea).text = f"SELECT * FROM {tname} LIMIT 100;"
                self.action_run_query()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "sql-run":
            self.action_run_query()
        elif bid == "sql-open":
            self.action_open_db()
        elif bid == "sql-export":
            if not self._last_cols:
                self.notify("Run a SELECT query first", severity="warning")
                return
            out = Path.cwd() / "query_export.csv"
            with out.open("w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(self._last_cols)
                w.writerows(self._last_rows)
            self.notify(f"Exported {len(self._last_rows)} rows → {out.name}", timeout=3)
