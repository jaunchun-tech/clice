"""Clice Sheets — Feature-Rich Terminal Excel with Office Ribbon, File Picker, Sort & Formulas."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Input, Static

from clice.core.config import add_recent_file
from clice.core.file_picker import FilePickerModal
from clice.core.formulas import evaluate_cell, index_to_col_letters
from clice.core.io_office import load_spreadsheet, save_spreadsheet


class SheetsApp(Vertical):
    """Excel-like spreadsheet with Office Ribbon, real File Picker, Sorting, and Formula Engine."""

    BINDINGS = [
        Binding("enter,f2", "edit_cell", "Edit Cell"),
        Binding("escape", "focus_grid", "Grid"),
        Binding("delete", "clear_cell", "Clear Cell"),
        Binding("ctrl+s", "save_sheet", "Save"),
        Binding("ctrl+o", "open_picker", "Open"),
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
        self.show_formulas = False
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
        # Office-Style Top Ribbon
        with Vertical(classes="ribbon-container"):
            with Horizontal(classes="ribbon-tabs"):
                yield Static("[b #22c55e][X] Clice Sheets[/b #22c55e]", classes="app-title")
                yield Button("File", id="xtab-file")
                yield Button("Formulas", id="xtab-formulas", classes="-active-tab")
                yield Button("Data", id="xtab-data")
                yield Button("View", id="xtab-view")
                yield Static("", id="sheets-file-label")

            with Horizontal(classes="ribbon-tools", id="xbar-file"):
                yield Button("New Blank", id="sheets-new")
                yield Button("Open... (^O)", variant="primary", id="sheets-open")
                yield Button("Save (^S)", variant="success", id="sheets-save")
                yield Button("Save As...", id="sheets-save-as")

            with Horizontal(classes="ribbon-tools", id="xbar-formulas"):
                yield Button("=SUM()", id="fn-sum")
                yield Button("=AVG()", id="fn-avg")
                yield Button("=MIN()", id="fn-min")
                yield Button("=MAX()", id="fn-max")
                yield Button("=COUNT()", id="fn-count")
                yield Button("=IF()", id="fn-if")
                yield Button("=ROUND()", id="fn-round")

            with Horizontal(classes="ribbon-tools", id="xbar-data"):
                yield Button("Sort A→Z", variant="primary", id="data-sort-asc")
                yield Button("Sort Z→A", id="data-sort-desc")
                yield Button("+Row (^R)", variant="success", id="sheets-add-row")
                yield Button("+Col (^L)", variant="success", id="sheets-add-col")
                yield Button("Del Row", variant="error", id="sheets-del-row")
                yield Button("Fill Down", id="sheets-fill-down")
                yield Button("Clear Cell", variant="warning", id="sheets-clear-cell")

            with Horizontal(classes="ribbon-tools", id="xbar-view"):
                yield Button("Toggle Formulas/Values", variant="primary", id="view-toggle-fx")
                yield Button("ASCII Bar Chart", variant="success", id="view-chart")
                yield Button("Auto-Sum Col", id="view-autosum")
                yield Button("Clear Sheet", variant="error", id="sheets-clear")

        with Horizontal(id="sheets-formula-bar"):
            yield Static("A1", id="sheets-cell-badge")
            yield Input(placeholder="Enter value or formula (=SUM(B2:B5), =A1*2)...", id="sheets-formula-input")
            yield Button("Apply", variant="primary", id="sheets-apply")

        yield DataTable(id="sheets-table", cursor_type="cell")
        yield Static("", id="sheets-status", classes="status-strip")

    def on_mount(self) -> None:
        self._switch_ribbon("formulas")
        self._rebuild_table()
        self._sync_formula_bar()
        self.query_one("#sheets-table", DataTable).focus()

    def _switch_ribbon(self, tab: str) -> None:
        for name in ("file", "formulas", "data", "view"):
            bar = self.query_one(f"#xbar-{name}", Horizontal)
            btn = self.query_one(f"#xtab-{name}", Button)
            bar.display = name == tab
            if name == tab:
                btn.add_class("-active-tab")
            else:
                btn.remove_class("-active-tab")

    def _col_summary(self) -> str:
        nums: list[float] = []
        for r in range(self.num_rows):
            val = evaluate_cell(self.grid[r][self.cursor_col], self.grid)
            try:
                nums.append(float(val))
            except ValueError:
                pass
        if not nums:
            return "Col Stats: (no numbers)"
        return f"Col {index_to_col_letters(self.cursor_col)} • Sum: {sum(nums):.4g} • Avg: {sum(nums)/len(nums):.4g} • Count: {len(nums)}"

    def _update_status(self, msg: str = "") -> None:
        fname = self.current_file.name if self.current_file else "Untitled.xlsx"
        self.query_one("#sheets-file-label", Static).update(f"  [b #4ade80]{fname}[/b #4ade80]")
        prefix = f"{msg}  •  " if msg else ""
        self.query_one("#sheets-status", Static).update(
            f"{prefix}{self._col_summary()}  •  Enter/F2 Edit  •  ^O Open  •  ^S Save"
        )

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
                raw = self.grid[r][c]
                rendered_row.append(raw if self.show_formulas else evaluate_cell(raw, self.grid))
            table.add_row(*rendered_row, key=str(r))

        try:
            table.move_cursor(row=self.cursor_row, column=self.cursor_col + 1)
        except Exception:
            pass
        self._update_status()

    def _sync_formula_bar(self) -> None:
        ref = f"{index_to_col_letters(self.cursor_col)}{self.cursor_row + 1}"
        self.query_one("#sheets-cell-badge", Static).update(ref)
        raw = self.grid[self.cursor_row][self.cursor_col]
        self.query_one("#sheets-formula-input", Input).value = raw
        self._update_status()

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

    def action_clear_cell(self) -> None:
        self.grid[self.cursor_row][self.cursor_col] = ""
        self._rebuild_table()
        self._sync_formula_bar()
        self.query_one("#sheets-table", DataTable).focus()

    def action_add_row(self) -> None:
        self.grid.append(["" for _ in range(self.num_cols)])
        self.num_rows += 1
        self._rebuild_table()
        self._update_status(f"Added row {self.num_rows}")

    def action_add_col(self) -> None:
        for row in self.grid:
            row.append("")
        self.num_cols += 1
        self._rebuild_table()
        self._update_status(f"Added col {index_to_col_letters(self.num_cols - 1)}")

    def action_open_picker(self) -> None:
        def _on_picked(path: Path | None) -> None:
            if path is not None:
                try:
                    self.open_file(path)
                except Exception as exc:
                    self.notify(f"Open error: {exc}", severity="error")

        self.app.push_screen(
            FilePickerModal(
                mode="open",
                title="Open Spreadsheet (.xlsx, .csv, .tsv)",
                start_dir=self.current_file.parent if self.current_file else Path.cwd(),
                extensions=(".xlsx", ".csv", ".tsv"),
            ),
            _on_picked,
        )

    def _open_save_as(self) -> None:
        def _on_picked(path: Path | None) -> None:
            if path is not None:
                self._save_to(path)

        self.app.push_screen(
            FilePickerModal(
                mode="save",
                title="Save Spreadsheet As (.xlsx, .csv)",
                start_dir=self.current_file.parent if self.current_file else Path.cwd(),
                extensions=(".xlsx", ".csv", ".tsv"),
                default_name=self.current_file.name if self.current_file else "sheet.xlsx",
            ),
            _on_picked,
        )

    def _save_to(self, path: Path) -> None:
        try:
            save_spreadsheet(path, self.grid)
            self.current_file = path
            add_recent_file(path, "sheets")
            self._update_status(f"Saved {path.name}")
            self.notify(f"Saved {path.name}", timeout=2)
        except Exception as exc:
            self.notify(f"Save error: {exc}", severity="error")

    def action_save_sheet(self) -> None:
        if self.current_file is None:
            self._open_save_as()
        else:
            self._save_to(self.current_file)

    def _apply_cell_edit(self) -> None:
        val = self.query_one("#sheets-formula-input", Input).value
        self.grid[self.cursor_row][self.cursor_col] = val
        self._rebuild_table()
        ref = f"{index_to_col_letters(self.cursor_col)}{self.cursor_row + 1}"
        computed = evaluate_cell(val, self.grid)
        self._update_status(f"{ref} → {computed}")
        self.query_one("#sheets-table", DataTable).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "sheets-formula-input":
            self._apply_cell_edit()

    def open_file(self, path: Path) -> None:
        self.grid = load_spreadsheet(path)
        self.num_rows = len(self.grid)
        self.num_cols = len(self.grid[0]) if self.grid else 10
        self.current_file = path
        self.cursor_row = 0
        self.cursor_col = 0
        self._rebuild_table()
        self._sync_formula_bar()
        add_recent_file(path, "sheets")
        self.notify(f"Opened {path.name}", timeout=2)
        self.query_one("#sheets-table", DataTable).focus()

    def _sort_column(self, reverse: bool = False) -> None:
        col = self.cursor_col
        header = self.grid[0]
        body = [r for r in self.grid[1:] if any(str(x).strip() for x in r)]
        empty = [r for r in self.grid[1:] if not any(str(x).strip() for x in r)]

        def _key(row: list[str]) -> tuple[int, float | str]:
            val = evaluate_cell(row[col], self.grid)
            try:
                return (0, float(val))
            except ValueError:
                return (1, val.lower())

        body.sort(key=_key, reverse=reverse)
        self.grid = [header] + body + empty
        self._rebuild_table()
        self._update_status(f"Sorted col {index_to_col_letters(col)} {'Z→A' if reverse else 'A→Z'}")

    def _insert_formula_template(self, template: str) -> None:
        inp = self.query_one("#sheets-formula-input", Input)
        inp.value = template
        inp.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        col_let = index_to_col_letters(self.cursor_col)
        if bid.startswith("xtab-"):
            self._switch_ribbon(bid[5:])
        elif bid == "sheets-apply":
            self._apply_cell_edit()
        elif bid == "sheets-new":
            self.current_file = None
            self.grid = [["" for _ in range(self.num_cols)] for _ in range(self.num_rows)]
            self._rebuild_table()
            self._sync_formula_bar()
        elif bid == "sheets-open":
            self.action_open_picker()
        elif bid == "sheets-save":
            self.action_save_sheet()
        elif bid == "sheets-save-as":
            self._open_save_as()
        elif bid == "fn-sum":
            self._insert_formula_template(f"=SUM({col_let}2:{col_let}{max(2, self.cursor_row)})")
        elif bid == "fn-avg":
            self._insert_formula_template(f"=AVG({col_let}2:{col_let}{max(2, self.cursor_row)})")
        elif bid == "fn-min":
            self._insert_formula_template(f"=MIN({col_let}2:{col_let}{max(2, self.cursor_row)})")
        elif bid == "fn-max":
            self._insert_formula_template(f"=MAX({col_let}2:{col_let}{max(2, self.cursor_row)})")
        elif bid == "fn-count":
            self._insert_formula_template(f"=COUNT({col_let}2:{col_let}{max(2, self.cursor_row)})")
        elif bid == "fn-if":
            self._insert_formula_template(f"=IF({col_let}2>0,'Yes','No')")
        elif bid == "fn-round":
            self._insert_formula_template(f"=ROUND({col_let}2, 2)")
        elif bid == "data-sort-asc":
            self._sort_column(reverse=False)
        elif bid == "data-sort-desc":
            self._sort_column(reverse=True)
        elif bid == "sheets-add-row":
            self.action_add_row()
        elif bid == "sheets-add-col":
            self.action_add_col()
        elif bid == "sheets-del-row":
            if self.num_rows > 1:
                self.grid.pop(self.cursor_row)
                self.num_rows -= 1
                self.cursor_row = min(self.cursor_row, self.num_rows - 1)
                self._rebuild_table()
                self._sync_formula_bar()
        elif bid == "sheets-fill-down":
            if self.cursor_row + 1 < self.num_rows:
                self.grid[self.cursor_row + 1][self.cursor_col] = self.grid[self.cursor_row][self.cursor_col]
                self._rebuild_table()
        elif bid == "sheets-clear-cell":
            self.action_clear_cell()
        elif bid == "view-toggle-fx":
            self.show_formulas = not self.show_formulas
            self._rebuild_table()
            self._update_status("Showing Formulas" if self.show_formulas else "Showing Values")
        elif bid == "view-chart":
            col = self.cursor_col
            vals: list[tuple[str, float]] = []
            for r in range(1, self.num_rows):
                raw_v = evaluate_cell(self.grid[r][col], self.grid)
                try:
                    num = float(raw_v)
                    label = self.grid[r][0] or f"Row {r + 1}"
                    vals.append((label[:12], num))
                except ValueError:
                    pass
            if not vals:
                self.notify("No numeric values in current column to chart", severity="warning")
            else:
                mx = max(abs(v) for _, v in vals) or 1.0
                bars = [f"{lbl:<12} | {'█' * max(1, int(abs(v) / mx * 20))} {v:g}" for lbl, v in vals[:10]]
                self.notify(f"Chart ({index_to_col_letters(col)}):\n" + "\n".join(bars), timeout=8)
        elif bid == "view-autosum":
            col_let = index_to_col_letters(self.cursor_col)
            self.grid[self.cursor_row][self.cursor_col] = f"=SUM({col_let}2:{col_let}{max(2, self.cursor_row)})"
            self._rebuild_table()
            self._sync_formula_bar()
        elif bid == "sheets-clear":
            self.grid = [["" for _ in range(self.num_cols)] for _ in range(self.num_rows)]
            self._rebuild_table()
            self._sync_formula_bar()
