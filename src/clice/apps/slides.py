"""Clice Slides — Keyboard-First Terminal PowerPoint with Present Mode & .pptx support."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, ListItem, ListView, Markdown, Static, TextArea

from clice.core.config import add_recent_file
from clice.core.io_office import SlideData, load_presentation, save_presentation


class PresentScreen(Screen[None]):
    """Full-screen PowerPoint-style Presentation Mode."""

    BINDINGS = [
        Binding("right,space,enter,n,down", "next_slide", "Next Slide"),
        Binding("left,p,up,backspace", "prev_slide", "Prev Slide"),
        Binding("escape,q", "exit_present", "Exit Present Mode"),
    ]

    def __init__(self, slides: list[SlideData], start_index: int = 0) -> None:
        super().__init__()
        self.slides = slides
        self.index = max(0, min(start_index, len(slides) - 1))

    def compose(self) -> ComposeResult:
        with Vertical(id="present-screen"):
            with Vertical(id="present-card"):
                yield Static("", id="present-title")
                yield Markdown("", id="present-body")
                yield Static("", id="present-footer")

    def on_mount(self) -> None:
        self._render_slide()

    def _render_slide(self) -> None:
        s = self.slides[self.index]
        self.query_one("#present-title", Static).update(f"[P]  {s.title}")
        self.query_one("#present-body", Markdown).update(s.body or "_(empty slide)_")
        self.query_one("#present-footer", Static).update(
            f"Slide {self.index + 1} / {len(self.slides)}   •   "
            "← / → or Space to navigate   •   Esc / Q to exit"
        )

    def action_next_slide(self) -> None:
        if self.index < len(self.slides) - 1:
            self.index += 1
            self._render_slide()

    def action_prev_slide(self) -> None:
        if self.index > 0:
            self.index -= 1
            self._render_slide()

    def action_exit_present(self) -> None:
        self.app.pop_screen()


class SlidesApp(Vertical):
    """Presentation editor with PowerPoint shortcuts (Ctrl+M new slide, Alt+P present, Ctrl+S save)."""

    BINDINGS = [
        Binding("ctrl+m", "add_slide", "New Slide"),
        Binding("alt+p", "present_mode", "Present"),
        Binding("ctrl+s", "save_deck", "Save"),
        Binding("alt+up", "prev_slide", "Prev Slide"),
        Binding("alt+down", "next_slide", "Next Slide"),
    ]

    def __init__(self, initial_file: Path | None = None) -> None:
        super().__init__()
        self.current_file: Path | None = initial_file
        self.slides: list[SlideData] = [
            SlideData(
                title="Welcome to Clice Slides",
                body="- Build presentations right in your terminal\n- Export to real Microsoft PowerPoint (`.pptx`)\n- Press **Alt+P** (or click Present) for full-screen slideshow!",
                notes="Introduce Clice Slides.",
            ),
            SlideData(
                title="PowerPoint Shortcuts",
                body="- `Ctrl+M` — Add a new slide\n- `Alt+P` — Launch Present Mode\n- `Alt+Up` / `Alt+Down` — Switch slides\n- `Ctrl+S` — Save `.pptx` / `.json` / `.md`",
                notes="Highlight keyboard-first workflow.",
            ),
        ]
        self.current_index = 0
        if initial_file and initial_file.exists():
            try:
                self.slides = load_presentation(initial_file)
            except Exception:
                pass

    def compose(self) -> ComposeResult:
        with Horizontal(classes="toolbar"):
            yield Static("[b #f97316][P] Clice Slides[/b #f97316]", classes="app-title")
            yield Input(
                value=str(self.current_file) if self.current_file else "deck.pptx",
                placeholder="Path (.pptx, .json, .md)",
                id="slides-path",
            )
            yield Button("Open", id="slides-open")
            yield Button("Save (^S)", variant="primary", id="slides-save")
            yield Button("+ Slide (^M)", variant="success", id="slides-add")
            yield Button("- Slide", variant="error", id="slides-del")
            yield Button("▶ Present (Alt+P)", variant="warning", id="slides-present")

        with Horizontal(id="slides-split"):
            yield ListView(id="slides-list")
            with Vertical(id="slides-editor-pane"):
                yield Static("[b]Slide Title[/b]")
                yield Input(id="slide-title-input", placeholder="Slide title...")
                yield Static("[b]Slide Content (Markdown)[/b]")
                yield TextArea("", language="markdown", id="slide-body-input")
            with Vertical(id="slides-preview-pane"):
                yield Static("", id="slide-preview-title")
                yield Markdown("", id="slide-preview-body")

        yield Static(
            "Ctrl+M: New Slide  •  Alt+P: Present Mode  •  Alt+↑/↓: Switch Slides  •  Ctrl+S: Save",
            id="slides-status",
            classes="status-strip",
        )

    def on_mount(self) -> None:
        self._refresh_list()
        self._load_slide_into_editor(0)
        self.query_one("#slides-list", ListView).focus()

    def _refresh_list(self) -> None:
        lv = self.query_one("#slides-list", ListView)
        lv.clear()
        for idx, s in enumerate(self.slides):
            lv.append(ListItem(Static(f"{idx + 1}. {s.title[:20]}")))

    def _load_slide_into_editor(self, idx: int) -> None:
        self.current_index = max(0, min(idx, len(self.slides) - 1))
        s = self.slides[self.current_index]
        self.query_one("#slide-title-input", Input).value = s.title
        self.query_one("#slide-body-input", TextArea).text = s.body
        self._update_preview()

    def _update_preview(self) -> None:
        s = self.slides[self.current_index]
        self.query_one("#slide-preview-title", Static).update(f"[b #fb923c]{s.title}[/b #fb923c]\n")
        self.query_one("#slide-preview-body", Markdown).update(s.body or "_(empty)_")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "slides-list" and event.list_view.index is not None:
            self._load_slide_into_editor(event.list_view.index)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "slide-title-input":
            self.slides[self.current_index].title = event.value
            self._update_preview()

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if event.text_area.id == "slide-body-input":
            self.slides[self.current_index].body = event.text_area.text
            self._update_preview()

    def action_add_slide(self) -> None:
        self.slides.append(SlideData(title=f"Slide {len(self.slides) + 1}", body="- New bullet point"))
        self._refresh_list()
        self._load_slide_into_editor(len(self.slides) - 1)
        self.query_one("#slides-status", Static).update(f"Added Slide {len(self.slides)}")

    def action_prev_slide(self) -> None:
        if self.current_index > 0:
            self._load_slide_into_editor(self.current_index - 1)

    def action_next_slide(self) -> None:
        if self.current_index < len(self.slides) - 1:
            self._load_slide_into_editor(self.current_index + 1)

    def action_present_mode(self) -> None:
        self.app.push_screen(PresentScreen(self.slides, self.current_index))

    def action_save_deck(self) -> None:
        status = self.query_one("#slides-status", Static)
        raw = self.query_one("#slides-path", Input).value.strip()
        if not raw:
            status.update("Enter a file path (.pptx, .json, .md)")
            return
        try:
            p = Path(raw).expanduser()
            save_presentation(p, self.slides)
            self.current_file = p
            add_recent_file(p, "slides")
            status.update(f"Saved {len(self.slides)} slides to {p}")
        except Exception as exc:
            status.update(f"Save error: {exc}")

    def open_file(self, path: Path) -> None:
        self.slides = load_presentation(path)
        self.current_file = path
        self.query_one("#slides-path", Input).value = str(path)
        self._refresh_list()
        self._load_slide_into_editor(0)
        add_recent_file(path, "slides")
        self.query_one("#slides-status", Static).update(f"Opened {path} ({len(self.slides)} slides)")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        status = self.query_one("#slides-status", Static)
        if bid == "slides-add":
            self.action_add_slide()
        elif bid == "slides-del":
            if len(self.slides) <= 1:
                status.update("Cannot delete the last slide")
                return
            self.slides.pop(self.current_index)
            self._refresh_list()
            self._load_slide_into_editor(max(0, self.current_index - 1))
            status.update("Deleted slide")
        elif bid == "slides-present":
            self.action_present_mode()
        elif bid == "slides-open":
            raw = self.query_one("#slides-path", Input).value.strip()
            if not raw:
                status.update("Enter a file path (.pptx, .json, .md)")
                return
            try:
                self.open_file(Path(raw).expanduser())
            except Exception as exc:
                status.update(f"Open error: {exc}")
        elif bid == "slides-save":
            self.action_save_deck()
