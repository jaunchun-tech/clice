"""Clice Marketplace Plugin: Port Scanner — Check common local dev ports."""

from __future__ import annotations

import socket

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Input, Static

from clice.core.plugins import ClicePlugin

COMMON_PORTS = [
    (80, "HTTP"),
    (443, "HTTPS"),
    (3000, "Node / React / Next.js"),
    (5173, "Vite"),
    (5432, "PostgreSQL"),
    (6379, "Redis"),
    (8000, "FastAPI / Django"),
    (8080, "HTTP Alt"),
    (27017, "MongoDB"),
]


class PortScannerWidget(Vertical):
    """Checks whether common local development ports are open on localhost."""

    def compose(self) -> ComposeResult:
        with Horizontal(classes="toolbar"):
            yield Static("[b #06b6d4]\\[P] Port Checker (Plugin)[/b #06b6d4]", classes="app-title")
            yield Input(value="127.0.0.1", placeholder="Host (default 127.0.0.1)", id="ps-host")
            yield Button("▶ Scan Common Ports", variant="primary", id="ps-scan")
        yield DataTable(id="ps-table")

    def on_mount(self) -> None:
        self._scan()

    def _scan(self) -> None:
        host = self.query_one("#ps-host", Input).value.strip() or "127.0.0.1"
        table = self.query_one("#ps-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Port", "Service", "Status")
        for port, label in COMMON_PORTS:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.15)
                is_open = s.connect_ex((host, port)) == 0
            status = "OPEN" if is_open else "closed"
            table.add_row(str(port), label, status)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ps-scan":
            self._scan()


class PortScannerPlugin(ClicePlugin):
    id = "plugin_port_scanner"
    name = "Port Checker"
    icon = "[P]"
    description = "Inspect common local dev server ports (3000, 5173, 5432, 8000, etc.)."
    version = "0.1.0"
    author = "Clice Marketplace"

    def create_widget(self) -> Vertical:
        return PortScannerWidget()
