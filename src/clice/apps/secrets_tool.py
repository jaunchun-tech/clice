"""Clice Secrets & Password Generator — Cryptographic passwords, passphrases & API keys."""

from __future__ import annotations

import math
import secrets
import string

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Static

WORDS = [
    "atlas", "beacon", "cipher", "delta", "ember", "falcon", "glacier", "harbor",
    "ivory", "jasper", "kinetic", "lantern", "matrix", "nebula", "orbit", "prism",
    "quartz", "raven", "solstice", "titan", "umbra", "vertex", "whisper", "zenith",
]


class SecretsToolApp(Vertical):
    """Cryptographically secure password, passphrase, and API token generator."""

    def compose(self) -> ComposeResult:
        with Horizontal(classes="toolbar"):
            yield Static("[b #a78bfa]\\[*] Clice Secrets & Passwords[/b #a78bfa]", classes="app-title")
            yield Input(value="24", placeholder="Length (e.g. 24)", id="sec-len")
            yield Button("Generate Password", variant="success", id="sec-pwd")
            yield Button("Passphrase (5 words)", variant="primary", id="sec-phrase")
            yield Button("API Key (hex)", variant="warning", id="sec-hex")
            yield Button("URL Token", id="sec-url")

        yield Static("", id="sec-output", classes="metric-box")
        yield Static("Uses Python `secrets` (CSPRNG) — safe for production credentials.", classes="status-strip")

    def on_mount(self) -> None:
        self._gen_password()

    def _get_len(self) -> int:
        try:
            return max(8, min(128, int(self.query_one("#sec-len", Input).value.strip())))
        except ValueError:
            return 24

    def _gen_password(self) -> None:
        length = self._get_len()
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*-_=+"
        pw = "".join(secrets.choice(alphabet) for _ in range(length))
        entropy = length * math.log2(len(alphabet))
        strength = "[b green]VERY STRONG[/b green]" if entropy >= 100 else ("[b yellow]STRONG[/b yellow]" if entropy >= 64 else "[b red]MODERATE[/b red]")
        self.query_one("#sec-output", Static).update(
            f"[b]Generated Password ({length} chars):[/b]\n\n"
            f"[b cyan]{pw}[/b cyan]\n\n"
            f"Entropy: [b]{entropy:.1f} bits[/b]  •  Strength: {strength}"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        out = self.query_one("#sec-output", Static)
        if bid == "sec-pwd":
            self._gen_password()
        elif bid == "sec-phrase":
            phrase = "-".join(secrets.choice(WORDS) for _ in range(5)) + f"-{secrets.randbelow(900) + 100}"
            out.update(f"[b]Diceware-Style Passphrase:[/b]\n\n[b green]{phrase}[/b green]")
        elif bid == "sec-hex":
            tok = secrets.token_hex(32)
            out.update(f"[b]256-bit Hex API Secret:[/b]\n\n[b yellow]{tok}[/b yellow]")
        elif bid == "sec-url":
            tok = secrets.token_urlsafe(32)
            out.update(f"[b]URL-Safe Bearer Token:[/b]\n\n[b magenta]{tok}[/b magenta]")
