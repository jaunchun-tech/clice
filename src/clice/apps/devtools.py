"""Clice DevTools — Coding Utilities & Code Scratchpad for programmers."""

from __future__ import annotations

import base64
import colorsys
import hashlib
import json
import re
import urllib.parse
import uuid
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Static, TabbedContent, TabPane, TextArea


class DevToolsApp(Vertical):
    """All-in-one developer utility belt: JSON, Regex, Base64/URL, Hash/UUID/JWT, Color, Code Pad."""

    def __init__(self, initial_file: Path | None = None) -> None:
        super().__init__()
        self.initial_file = initial_file

    def compose(self) -> ComposeResult:
        with Horizontal(classes="toolbar"):
            yield Static("[b #a855f7]💻 Clice Coding Utils[/b #a855f7]", classes="app-title")
            yield Static("[dim]JSON • Regex • Base64/URL • Hash/UUID/JWT • Colors • Code Scratchpad[/dim]")

        with TabbedContent(id="dev-tabs"):
            # Tab 1: JSON Formatter
            with TabPane("JSON", id="tab-json"):
                with Horizontal(classes="toolbar"):
                    yield Button("Format (Pretty)", variant="primary", id="json-pretty")
                    yield Button("Minify", id="json-minify")
                    yield Button("Validate", variant="success", id="json-validate")
                yield TextArea('{"name": "clice", "version": 1, "awesome": true}', language="json", id="json-area", classes="code-area")
                yield Static("Ready", id="json-status", classes="status-strip")

            # Tab 2: Regex Tester
            with TabPane("Regex", id="tab-regex"):
                with Horizontal(classes="toolbar"):
                    yield Input(value=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", placeholder="Regex pattern...", id="regex-pattern")
                    yield Button("Test Regex", variant="primary", id="regex-run")
                yield TextArea("Contact us at dev@clice.io or hello@example.com!", id="regex-text", classes="code-area")
                yield Static("Click 'Test Regex' to see matches.", id="regex-output", classes="metric-box")

            # Tab 3: Base64 & URL
            with TabPane("Base64 / URL", id="tab-codec"):
                with Horizontal(classes="toolbar"):
                    yield Button("B64 Encode", variant="primary", id="b64-enc")
                    yield Button("B64 Decode", id="b64-dec")
                    yield Button("URL Encode", variant="success", id="url-enc")
                    yield Button("URL Decode", id="url-dec")
                yield TextArea("Hello Clice Developer!", id="codec-in", classes="code-area")
                yield TextArea("", id="codec-out", classes="code-area")

            # Tab 4: Hash / UUID / JWT
            with TabPane("Hash / UUID / JWT", id="tab-hash"):
                with Horizontal(classes="toolbar"):
                    yield Input(value="clice", placeholder="Text to hash or JWT to decode...", id="hash-input")
                    yield Button("Hash Text", variant="primary", id="hash-run")
                    yield Button("New UUID4", variant="success", id="uuid-gen")
                    yield Button("Decode JWT", variant="warning", id="jwt-dec")
                yield Static("Enter text and click Hash, or generate a UUID4.", id="hash-output", classes="metric-box")

            # Tab 5: Color Converter
            with TabPane("Colors", id="tab-color"):
                with Horizontal(classes="toolbar"):
                    yield Input(value="#3b82f6", placeholder="HEX color (e.g. #3b82f6)", id="color-input")
                    yield Button("Convert", variant="primary", id="color-run")
                yield Static("Enter a HEX color to convert to RGB and HSL.", id="color-output", classes="metric-box")

            # Tab 6: Code Scratchpad
            with TabPane("Code Pad", id="tab-code"):
                with Horizontal(classes="toolbar"):
                    yield Input(
                        value=str(self.initial_file) if self.initial_file else "scratch.py",
                        placeholder="File path to open/save...",
                        id="code-path",
                    )
                    yield Button("Open", id="code-open")
                    yield Button("Save", variant="success", id="code-save")
                initial_code = "# Clice Code Scratchpad\nprint('Hello from Clice!')\n"
                if self.initial_file and self.initial_file.exists():
                    try:
                        initial_code = self.initial_file.read_text(encoding="utf-8")
                    except Exception:
                        pass
                yield TextArea(initial_code, language="python", id="code-editor", classes="code-area")
                yield Static("Ready", id="code-status", classes="status-strip")

    def open_code_file(self, path: Path) -> None:
        content = path.read_text(encoding="utf-8")
        self.query_one("#code-path", Input).value = str(path)
        self.query_one("#code-editor", TextArea).text = content
        self.query_one("#dev-tabs", TabbedContent).active = "tab-code"
        self.query_one("#code-status", Static).update(f"Opened {path}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id

        # JSON
        if bid in ("json-pretty", "json-minify", "json-validate"):
            area = self.query_one("#json-area", TextArea)
            status = self.query_one("#json-status", Static)
            try:
                parsed = json.loads(area.text)
                if bid == "json-pretty":
                    area.text = json.dumps(parsed, indent=2, ensure_ascii=False)
                    status.update("✅ Valid JSON — formatted")
                elif bid == "json-minify":
                    area.text = json.dumps(parsed, separators=(",", ":"), ensure_ascii=False)
                    status.update("✅ Valid JSON — minified")
                else:
                    status.update("✅ Valid JSON!")
            except Exception as exc:
                status.update(f"❌ JSON Error: {exc}")

        # Regex
        elif bid == "regex-run":
            pat = self.query_one("#regex-pattern", Input).value
            text = self.query_one("#regex-text", TextArea).text
            out = self.query_one("#regex-output", Static)
            try:
                matches = list(re.finditer(pat, text))
                if not matches:
                    out.update("No matches found.")
                else:
                    lines = [f"[b green]Found {len(matches)} match(es):[/b green]"]
                    for i, m in enumerate(matches[:20], start=1):
                        lines.append(f"  {i}. `{m.group(0)}` (span {m.start()}..{m.end()})")
                    out.update("\n".join(lines))
            except re.error as exc:
                out.update(f"[red]Regex error: {exc}[/red]")

        # Base64 / URL
        elif bid in ("b64-enc", "b64-dec", "url-enc", "url-dec"):
            src = self.query_one("#codec-in", TextArea).text
            dst = self.query_one("#codec-out", TextArea)
            try:
                if bid == "b64-enc":
                    dst.text = base64.b64encode(src.encode("utf-8")).decode("ascii")
                elif bid == "b64-dec":
                    dst.text = base64.b64decode(src.strip()).decode("utf-8")
                elif bid == "url-enc":
                    dst.text = urllib.parse.quote(src, safe="")
                elif bid == "url-dec":
                    dst.text = urllib.parse.unquote(src)
            except Exception as exc:
                dst.text = f"Error: {exc}"

        # Hash / UUID / JWT
        elif bid == "hash-run":
            raw = self.query_one("#hash-input", Input).value.encode("utf-8")
            out = self.query_one("#hash-output", Static)
            out.update(
                f"[b]MD5:[/b]    {hashlib.md5(raw).hexdigest()}\n"
                f"[b]SHA1:[/b]   {hashlib.sha1(raw).hexdigest()}\n"
                f"[b]SHA256:[/b] {hashlib.sha256(raw).hexdigest()}\n"
                f"[b]SHA512:[/b] {hashlib.sha512(raw).hexdigest()[:64]}..."
            )
        elif bid == "uuid-gen":
            u = str(uuid.uuid4())
            self.query_one("#hash-output", Static).update(f"[b green]UUID v4:[/b green] {u}")
        elif bid == "jwt-dec":
            token = self.query_one("#hash-input", Input).value.strip()
            out = self.query_one("#hash-output", Static)
            try:
                parts = token.split(".")
                if len(parts) < 2:
                    raise ValueError("JWT must have at least 2 dot-separated parts")

                def _b64url(s: str) -> str:
                    pad = "=" * (-len(s) % 4)
                    return base64.urlsafe_b64decode(s + pad).decode("utf-8")

                header = json.dumps(json.loads(_b64url(parts[0])), indent=2)
                payload = json.dumps(json.loads(_b64url(parts[1])), indent=2)
                out.update(f"[b]Header:[/b]\n{header}\n\n[b]Payload:[/b]\n{payload}")
            except Exception as exc:
                out.update(f"[red]JWT decode error: {exc}[/red]")

        # Color
        elif bid == "color-run":
            hx = self.query_one("#color-input", Input).value.strip().lstrip("#")
            out = self.query_one("#color-output", Static)
            try:
                if len(hx) != 6:
                    raise ValueError("Use 6-digit HEX like #3b82f6")
                r, g, b = int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)
                h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
                out.update(
                    f"[on #{hx}]      PREVIEW      [/on #{hx}]\n\n"
                    f"[b]HEX:[/b] #{hx.upper()}\n"
                    f"[b]RGB:[/b] rgb({r}, {g}, {b})\n"
                    f"[b]HSL:[/b] hsl({round(h * 360)}, {round(s * 100)}%, {round(l * 100)}%)"
                )
            except Exception as exc:
                out.update(f"[red]Color error: {exc}[/red]")

        # Code Pad
        elif bid == "code-open":
            raw = self.query_one("#code-path", Input).value.strip()
            status = self.query_one("#code-status", Static)
            try:
                p = Path(raw).expanduser()
                self.query_one("#code-editor", TextArea).text = p.read_text(encoding="utf-8")
                status.update(f"Opened {p}")
            except Exception as exc:
                status.update(f"Open error: {exc}")
        elif bid == "code-save":
            raw = self.query_one("#code-path", Input).value.strip()
            status = self.query_one("#code-status", Static)
            try:
                p = Path(raw).expanduser()
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(self.query_one("#code-editor", TextArea).text, encoding="utf-8")
                status.update(f"Saved {p}")
            except Exception as exc:
                status.update(f"Save error: {exc}")
