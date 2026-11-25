"""Clice Sheets — Keyboard-First Terminal Excel with formulas & .xlsx/.csv support."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Input, Static

from clice.core.config import add_recent_file
from clice.core.formulas import evaluate_cell, index_to_col_letters
from clice.core.io_office import load_spreadsheet, save_spreadsheet


class SheetsApp(Vertical):
    """Spreadsheet app with Excel-standard keyboard shortcuts (Arrows, Enter/F2, Del, Ctrl+S)."""

    BINDINGS = [
        Binding("enter,f2", "edit_cell", "Edit Cell"),
        Binding("escape", "focus_grid", "Grid"),
        Binding("delete", "clear_cell", "Clear Cell"),
        Binding("ctrl+s", "save_sheet", "Save"),
        Binding("ctrl+o", "focus_path", "Open"),
        Binding("ctrl+r", "add_row", "+Row"),
        Binding("ctrl+l", "add_col", "+Col"),
    ]

    def __init__(self, initial_file: Path | None = None) -> None:
        super().__init__()
        self.current_file: Path | None = initial_file
        self.num_rows = 20
        self.num_cols = 10
        self.grid: list[list[str]] = [["" for _ in range(self.num_cols)] for _ in range(self.num_rows)]
        self.cursor_row = 0
        self.cursor_col = 0
        if initial_file and initial_file.exists():
            try:
                self.grid = load_spreadsheet(initial_file)
                self.num_rows = len(self.grid)
                self.num_cols = len(self.grid[0]) if self.grid else 10
            except Exception:
                self._seed_sample_data()
        else:
            self._seed_sample_data()

    def _seed_sample_data(self) -> None:
        sample = [
            ["Item", "Qty", "Price", "Total", "Status"],
            ["Laptop", "2", "1299", "=B2*C2", "=IF(D2>2000,'High','OK')"],
            ["Monitor", "3", "349", "=B3*C3", "=IF(D3>2000,'High','OK')"],
            ["Keyboard", "5", "129", "=B4*C4", "=IF(D4>2000,'High','OK')"],
            ["Mouse", "5", "69", "=B5*C5", "=IF(D5>2000,'High','OK')"],
            ["Grand Total", "=SUM(B2:B5)", "", "=SUM(D2:D5)", ""],
            ["Average", "=AVG(B2:B5)", "=AVG(C2:C5)", "=AVG(D2:D5)", ""],
        ]
        for r, row in enumerate(sample):
            for c, val in enumerate(row):
                self.grid[r][c] = val

    def compose(self) -> ComposeResult:
        with Horizontal(classes="toolbar"):
            yield Static("[b #22c55e][X] Clice Sheets[/b #22c55e]", classes="app-title")
            yield Input(
                value=str(self.current_file) if self.current_file else "budget.xlsx",
                placeholder="Path (.xlsx or .csv)",
                id="sheets-path",
            )
            yield Button("Open (^O)", variant="default", id="sheets-open")
            yield Button("Save (^S)", variant="success", id="sheets-save")
            yield Button("+Row (^R)", id="sheets-add-row")
            yield Button("+Col (^L)", id="sheets-add-col")
            yield Button("Clear", variant="warning", id="sheets-clear")

        with Horizontal(id="sheets-formula-bar"):
            yield Static("A1", id="sheets-cell-badge")
            yield Input(placeholder="Enter value or formula (=SUM(B2:B5), =A1*2)...", id="sheets-formula-input")
            yield Button("Apply", variant="primary", id="sheets-apply")

        yield DataTable(id="sheets-table", cursor_type="cell")
        yield Static(
            "Arrows: Move  •  Enter/F2: Edit Cell  •  Esc: Grid  •  Del: Clear  •  Ctrl+S: Save  •  Ctrl+R/+L: +Row/+Col",
            id="sheets-status",
            classes="status-strip",
        )

    def on_mount(self) -> None:
        self._rebuild_table()
        self._sync_formula_bar()
        self.query_one("#sheets-table", DataTable).focus()

    def _rebuild_table(self) -> None:
        table = self.query_one("#sheets-table", DataTable)
        table.clear(columns=True)
        table.add_column("#", key="row_idx", width=4)
        for c in range(self.num_cols):
            col_name = index_to_col_letters(c)
            table.add_column(col_name, key=col_name, width=14)

        for r in range(self.num_rows):
            rendered_row = [str(r + 1)]
            for c in range(self.num_cols):
                rendered_row.append(evaluate_cell(self.grid[r][c], self.grid))
            table.add_row(*rendered_row, key=str(r))

        try:
            table.move_cursor(row=self.cursor_row, column=self.cursor_col + 1)
        except Exception:
            pass

    def _sync_formula_bar(self) -> None:
        ref = f"{index_to_col_letters(self.cursor_col)}{self.cursor_row + 1}"
        self.query_one("#sheets-cell-badge", Static).update(ref)
        raw = self.grid[self.cursor_row][self.cursor_col]
        self.query_one("#sheets-formula-input", Input).value = raw

    def on_data_table_cell_highlighted(self, event: DataTable.CellHighlighted) -> None:
        row = event.coordinate.row
        col = event.coordinate.column - 1
        if col < 0:
            return
        if 0 <= row < self.num_rows and 0 <= col < self.num_cols:
            self.cursor_row = row
            self.cursor_col = col
            self._sync_formula_bar()

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        self.action_edit_cell()

    def action_edit_cell(self) -> None:
        self.query_one("#sheets-formula-input", Input).focus()

    def action_focus_grid(self) -> None:
        self.query_one("#sheets-table", DataTable).focus()

    def action_focus_path(self) -> None:
        self.query_one("#sheets-path", Input).focus()

    def action_clear_cell(self) -> None:
        self.grid[self.cursor_row][self.cursor_col] = ""
        self._rebuild_table()
        self._sync_formula_bar()
        self.query_one("#sheets-table", DataTable).focus()

    def action_add_row(self) -> None:
        self.grid.append(["" for _ in range(self.num_cols)])
        self.num_rows += 1
        self._rebuild_table()
        self.query_one("#sheets-status", Static).update(f"Added row {self.num_rows}")

    def action_add_col(self) -> None:
        for row in self.grid:
            row.append("")
        self.num_cols += 1
        self._rebuild_table()
        self.query_one("#sheets-status", Static).update(f"Added column {index_to_col_letters(self.num_cols - 1)}")

    def action_save_sheet(self) -> None:
        status = self.query_one("#sheets-status", Static)
        raw_path = self.query_one("#sheets-path", Input).value.strip()
        if not raw_path:
            status.update("Enter a file path (.xlsx or .csv)")
            return
        try:
            p = Path(raw_path).expanduser()
            save_spreadsheet(p, self.grid)
            self.current_file = p
            add_recent_file(p, "sheets")
            status.update(f"Saved to {p}")
        except Exception as exc:
            status.update(f"Save error: {exc}")

    def _apply_cell_edit(self) -> None:
        val = self.query_one("#sheets-formula-input", Input).value
        self.grid[self.cursor_row][self.cursor_col] = val
        self._rebuild_table()
        ref = f"{index_to_col_letters(self.cursor_col)}{self.cursor_row + 1}"
        computed = evaluate_cell(val, self.grid)
        self.query_one("#sheets-status", Static).update(f"Updated {ref} → {computed}")
        self.query_one("#sheets-table", DataTable).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "sheets-formula-input":
            self._apply_cell_edit()
        elif event.input.id == "sheets-path":
            try:
                self.open_file(Path(event.value.strip()).expanduser())
            except Exception as exc:
                self.query_one("#sheets-status", Static).update(f"Open error: {exc}")

    def open_file(self, path: Path) -> None:
        self.grid = load_spreadsheet(path)
        self.num_rows = len(self.grid)
        self.num_cols = len(self.grid[0]) if self.grid else 10
        self.current_file = path
        self.cursor_row = 0
        self.cursor_col = 0
        self.query_one("#sheets-path", Input).value = str(path)
        self._rebuild_table()
        self._sync_formula_bar()
        add_recent_file(path, "sheets")
        self.query_one("#sheets-status", Static).update(f"Opened {path}")
        self.query_one("#sheets-table", DataTable).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        status = self.query_one("#sheets-status", Static)
        if bid == "sheets-apply":
            self._apply_cell_edit()
        elif bid == "sheets-add-row":
            self.action_add_row()
        elif bid == "sheets-add-col":
            self.action_add_col()
        elif bid == "sheets-clear":
            self.grid = [["" for _ in range(self.num_cols)] for _ in range(self.num_rows)]
            self._rebuild_table()
            self._sync_formula_bar()
            status.update("Cleared spreadsheet")
        elif bid == "sheets-open":
            raw_path = self.query_one("#sheets-path", Input).value.strip()
            if not raw_path:
                status.update("Enter a file path (.xlsx or .csv)")
                return
            try:
                self.open_file(Path(raw_path).expanduser())
            except Exception as exc:
                status.update(f"Open error: {exc}")
        elif bid == "sheets-save":
            self.action_save_sheet()
