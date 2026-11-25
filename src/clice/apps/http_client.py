"""Clice HTTP / API Client — Terminal Postman / Insomnia for testing REST APIs."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Select, Static, TabbedContent, TabPane, TextArea


class HttpClientApp(Vertical):
    """Async REST API tester with method selector, headers/body editor, and formatted JSON response."""

    BINDINGS = [
        Binding("ctrl+enter", "send_request", "Send"),
    ]

    def compose(self) -> ComposeResult:
        with Horizontal(classes="toolbar"):
            yield Static("[b #10b981]\\[API] Clice HTTP Client[/b #10b981]", classes="app-title")
            yield Select(
                [("GET", "GET"), ("POST", "POST"), ("PUT", "PUT"), ("PATCH", "PATCH"), ("DELETE", "DELETE")],
                value="GET",
                id="http-method",
            )
            yield Input(value="https://api.github.com/repos/jaunchun-tech/clice", placeholder="https://...", id="http-url")
            yield Button("▶ Send (^Enter)", variant="success", id="http-send")

        with TabbedContent():
            with TabPane("Response Body", id="htab-resp"):
                yield TextArea("", language="json", id="http-resp-body", classes="code-area")
            with TabPane("Request Headers (JSON)", id="htab-hdrs"):
                yield TextArea('{"User-Agent": "Clice-HTTP/0.1", "Accept": "application/json"}', language="json", id="http-req-headers", classes="code-area")
            with TabPane("Request Body", id="htab-body"):
                yield TextArea('{"hello": "clice"}', language="json", id="http-req-body", classes="code-area")
            with TabPane("Response Headers", id="htab-rhdrs"):
                yield TextArea("", id="http-resp-headers", classes="code-area")

        yield Static("Ready • Press Ctrl+Enter or click Send", id="http-status", classes="status-strip")

    def on_mount(self) -> None:
        self.query_one("#http-url", Input).focus()

    def action_send_request(self) -> None:
        method = str(self.query_one("#http-method", Select).value or "GET")
        url = self.query_one("#http-url", Input).value.strip()
        hdrs_raw = self.query_one("#http-req-headers", TextArea).text.strip()
        body_raw = self.query_one("#http-req-body", TextArea).text
        if not url:
            return
        self.query_one("#http-status", Static).update(f"Sending {method} {url}...")
        self._do_http(method, url, hdrs_raw, body_raw)

    @work(thread=True)
    def _do_http(self, method: str, url: str, hdrs_raw: str, body_raw: str) -> None:
        t0 = time.perf_counter()
        try:
            headers = json.loads(hdrs_raw) if hdrs_raw else {}
            data = body_raw.encode("utf-8") if method in ("POST", "PUT", "PATCH") and body_raw else None
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=15) as resp:
                elapsed = (time.perf_counter() - t0) * 1000
                raw_text = resp.read().decode("utf-8", errors="replace")
                try:
                    pretty = json.dumps(json.loads(raw_text), indent=2, ensure_ascii=False)
                except Exception:
                    pretty = raw_text
                resp_hdrs = "\n".join(f"{k}: {v}" for k, v in resp.headers.items())
                self.app.call_from_thread(self._show_result, resp.status, elapsed, pretty, resp_hdrs, None)
        except urllib.error.HTTPError as err:
            elapsed = (time.perf_counter() - t0) * 1000
            raw_text = err.read().decode("utf-8", errors="replace")
            self.app.call_from_thread(self._show_result, err.code, elapsed, raw_text, "", None)
        except Exception as exc:
            elapsed = (time.perf_counter() - t0) * 1000
            self.app.call_from_thread(self._show_result, 0, elapsed, "", "", str(exc))

    def _show_result(self, code: int, elapsed: float, body: str, hdrs: str, err: str | None) -> None:
        status = self.query_one("#http-status", Static)
        if err:
            status.update(f"❌ Request failed ({elapsed:.0f} ms): {err}")
            return
        self.query_one("#http-resp-body", TextArea).text = body
        self.query_one("#http-resp-headers", TextArea).text = hdrs
        status.update(f"HTTP {code}  •  {elapsed:.0f} ms  •  {len(body)} bytes")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "http-url":
            self.action_send_request()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "http-send":
            self.action_send_request()
