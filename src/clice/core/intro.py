"""Animated Intro Splash Screen for Clice."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.events import Click, Key
from textual.screen import ModalScreen
from textual.widgets import ProgressBar, Static

from clice import __version__

CLICE_LOGO = """[b #38bdf8] ██████╗██╗     ██╗ ██████╗███████╗[/b #38bdf8]
[b #60a5fa]██╔════╝██║     ██║██╔════╝██╔════╝[/b #60a5fa]
[b #818cf8]██║     ██║     ██║██║     █████╗  [/b #818cf8]
[b #a78bfa]██║     ██║     ██║██║     ██╔══╝  [/b #a78bfa]
[b #c084fc]╚██████╗███████╗██║╚██████╗███████╗[/b #c084fc]
[b #e879f9] ╚═════╝╚══════╝╚═╝ ╚═════╝╚══════╝[/b #e879f9]"""

STEPS = [
    (20, "Initializing Terminal Desktop Shell..."),
    (45, "Loading Office Suite (Sheets • Docs • Slides)..."),
    (70, "Mounting Developer & System Multitools..."),
    (90, "Connecting Plugin & GitHub Marketplace Engine..."),
    (100, "Ready! Welcome to Clice."),
]


class IntroSplashScreen(ModalScreen[None]):
    """Animated gradient logo splash screen — auto-closes in ~1.2s or on any key/click."""

    BINDINGS = [
        Binding("escape,enter,space", "skip_intro", "Skip"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._step = 0

    def compose(self) -> ComposeResult:
        with Vertical(id="intro-card"):
            yield Static(CLICE_LOGO, id="intro-logo")
            yield Static(
                f"[b]v{__version__}[/b]  •  [dim]Terminal Office Suite & Developer Desktop[/dim]",
                id="intro-sub",
            )
            yield ProgressBar(total=100, show_eta=False, id="intro-bar")
            yield Static("Starting Clice...", id="intro-status")
            yield Static("[dim]Press any key or click to skip[/dim]", id="intro-hint")

    def on_mount(self) -> None:
        card = self.query_one("#intro-card", Vertical)
        card.styles.opacity = 0.0
        card.styles.animate("opacity", value=1.0, duration=0.25, easing="out_cubic")
        self.set_interval(0.22, self._advance)

    def _advance(self) -> None:
        if self._step < len(STEPS):
            pct, msg = STEPS[self._step]
            self.query_one("#intro-bar", ProgressBar).update(progress=pct)
            self.query_one("#intro-status", Static).update(f"[cyan]{msg}[/cyan]")
            self._step += 1
        else:
            self.dismiss(None)

    def action_skip_intro(self) -> None:
        self.dismiss(None)

    def on_key(self, event: Key) -> None:
        self.dismiss(None)

    def on_click(self, event: Click) -> None:
        self.dismiss(None)
