"""Clice SysMon — Cross-platform Live System Monitor (CPU, RAM, Disk, Processes)."""

from __future__ import annotations

import platform
from pathlib import Path

import psutil
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, ProgressBar, Static


class SysMonApp(Vertical):
    """Live cross-platform System Monitor powered by psutil."""

    def compose(self) -> ComposeResult:
        with Horizontal(classes="toolbar"):
            yield Static("[b #ef4444]🖥️ Clice System Monitor[/b #ef4444]", classes="app-title")
            yield Static(f"[dim]{platform.system()} {platform.release()} ({platform.machine()})[/dim]")
            yield Button("↻ Refresh", variant="primary", id="sys-refresh")

        with Vertical(classes="metric-box"):
            yield Static("CPU Usage: 0%", id="cpu-label")
            yield ProgressBar(total=100, show_eta=False, id="cpu-bar")
            yield Static("RAM Usage: 0%", id="ram-label")
            yield ProgressBar(total=100, show_eta=False, id="ram-bar")
            yield Static("Disk Usage: 0%", id="disk-label")
            yield ProgressBar(total=100, show_eta=False, id="disk-bar")

        yield Static("[b]Top Processes (by Memory %)[/b]")
        yield DataTable(id="sys-procs")

    def on_mount(self) -> None:
        self._refresh_stats()
        self.set_interval(2.0, self._refresh_stats)

    def _refresh_stats(self) -> None:
        cpu = psutil.cpu_percent(interval=None)
        vm = psutil.virtual_memory()
        disk = psutil.disk_usage(str(Path.home().anchor or "/"))

        self.query_one("#cpu-label", Static).update(
            f"[b]CPU Usage:[/b] {cpu:.1f}%  ({psutil.cpu_count(logical=True)} logical cores)"
        )
        self.query_one("#cpu-bar", ProgressBar).update(progress=cpu)

        used_gb = vm.used / (1024**3)
        total_gb = vm.total / (1024**3)
        self.query_one("#ram-label", Static).update(
            f"[b]RAM Usage:[/b] {vm.percent:.1f}%  ({used_gb:.1f} GB / {total_gb:.1f} GB)"
        )
        self.query_one("#ram-bar", ProgressBar).update(progress=vm.percent)

        d_used = disk.used / (1024**3)
        d_total = disk.total / (1024**3)
        self.query_one("#disk-label", Static).update(
            f"[b]Disk Usage:[/b] {disk.percent:.1f}%  ({d_used:.1f} GB / {d_total:.1f} GB)"
        )
        self.query_one("#disk-bar", ProgressBar).update(progress=disk.percent)

        table = self.query_one("#sys-procs", DataTable)
        table.clear(columns=True)
        table.add_columns("PID", "Name", "CPU %", "MEM %", "Status")
        procs = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "status"]):
            try:
                info = p.info
                procs.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        procs.sort(key=lambda x: x.get("memory_percent") or 0.0, reverse=True)
        for info in procs[:15]:
            table.add_row(
                str(info.get("pid", "")),
                str(info.get("name", ""))[:28],
                f"{info.get('cpu_percent') or 0.0:.1f}",
                f"{info.get('memory_percent') or 0.0:.1f}",
                str(info.get("status", "")),
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "sys-refresh":
            self._refresh_stats()
