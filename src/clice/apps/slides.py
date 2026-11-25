"""Clice Slides — Feature-Rich Terminal PowerPoint with Office Ribbon, File Picker, Themes & Present Mode."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, ListItem, ListView, Markdown, Static, TextArea

from clice.core.config import add_recent_file
from clice.core.file_picker import FilePickerModal
from clice.core.io_office import SlideData, load_presentation, save_presentation

SLIDE_THEMES: dict[str, tuple[str, str]] = {
    "Midnight Orange": ("#fb923c", "#0f172a"),
    "Ocean Blue": ("#38bdf8", "#0c192c"),
    "Emerald Dark": ("#4ade80", "#052e16"),
    "Royal Purple": ("#c084fc", "#1e1033"),
    "Slate Gold": ("#facc15", "#1c1917"),
}


class PresentScreen(Screen[None]):
    """Full-screen PowerPoint-style Presentation Mode with Theme Support."""

    BINDINGS = [
        Binding("right,space,enter,n,down", "next_slide", "Next Slide"),
        Binding("left,p,up,backspace", "prev_slide", "Prev Slide"),
        Binding("escape,q", "exit_present", "Exit Present Mode"),
    ]

    def __init__(self, slides: list[SlideData], start_index: int = 0, theme_name: str = "Midnight Orange") -> None:
        super().__init__()
        self.slides = slides
        self.index = max(0, min(start_index, len(slides) - 1))
        self.theme_name = theme_name

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
        accent, _ = SLIDE_THEMES.get(self.theme_name, ("#fb923c", "#0f172a"))
        self.query_one("#present-title", Static).update(f"[b {accent}][P]  {s.title}[/b {accent}]")
        self.query_one("#present-body", Markdown).update(s.body or "_(empty slide)_")
        note_hint = f"  •  Notes: {s.notes[:45]}" if s.notes else ""
        self.query_one("#present-footer", Static).update(
            f"Slide {self.index + 1} / {len(self.slides)}  •  Theme: {self.theme_name}{note_hint}  •  ←/→ Space  •  Esc Exit"
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
    """PowerPoint-style editor with Office Ribbon, real File Picker, Slide Themes, and Present Mode."""

    BINDINGS = [
        Binding("ctrl+m", "add_slide", "New Slide"),
        Binding("alt+p", "present_mode", "Present"),
        Binding("ctrl+s", "save_deck", "Save"),
        Binding("ctrl+o", "open_picker", "Open"),
        Binding("alt+up", "prev_slide", "Prev Slide"),
        Binding("alt+down", "next_slide", "Next Slide"),
    ]

    def __init__(self, initial_file: Path | None = None) -> None:
        super().__init__()
        self.current_file: Path | None = initial_file
        self.theme_name = "Midnight Orange"
        self.slides: list[SlideData] = [
            SlideData(
                title="Untitled Presentation",
                body="- Use **File → Open (`Ctrl+O`)** to open any `.pptx`, `.md`, or `.json` deck\n- Press **`Ctrl+M`** to add slides, **`Alt+P`** for Present Mode\n- Switch themes in the **Design** tab!",
                notes="Welcome slide.",
            ),
        ]
        self.current_index = 0
        if initial_file and initial_file.exists():
            try:
                self.slides = load_presentation(initial_file)
            except Exception:
                pass

    def compose(self) -> ComposeResult:
        # Office-Style Top Ribbon
        with Vertical(classes="ribbon-container"):
            with Horizontal(classes="ribbon-tabs"):
                yield Static("[b #f97316][P] Clice Slides[/b #f97316]", classes="app-title")
                yield Button("File", id="ptab-file")
                yield Button("Slides", id="ptab-slides", classes="-active-tab")
                yield Button("Insert", id="ptab-insert")
                yield Button("Design", id="ptab-design")
                yield Button("Present", id="ptab-present")
                yield Static("", id="slides-file-label")

            with Horizontal(classes="ribbon-tools", id="pbar-file"):
                yield Button("New Deck", id="slides-new")
                yield Button("Open... (^O)", variant="primary", id="slides-open")
                yield Button("Save (^S)", variant="success", id="slides-save")
                yield Button("Save As...", id="slides-save-as")

            with Horizontal(classes="ribbon-tools", id="pbar-slides"):
                yield Button("+ New Slide (^M)", variant="success", id="slides-add")
                yield Button("Duplicate", id="slides-dup")
                yield Button("Move Up", id="slides-up")
                yield Button("Move Down", id="slides-down")
                yield Button("Delete", variant="error", id="slides-del")

            with Horizontal(classes="ribbon-tools", id="pbar-insert"):
                yield Button("Bullets", id="pins-bullets")
                yield Button("Table", id="pins-table")
                yield Button("Code Block", id="pins-code")
                yield Button("Quote", id="pins-quote")
                yield Button("Checklist", id="pins-check")

            with Horizontal(classes="ribbon-tools", id="pbar-design"):
                for tname in SLIDE_THEMES:
                    tid = "ptheme-" + tname.lower().replace(" ", "-")
                    yield Button(tname, id=tid, name=tname)

            with Horizontal(classes="ribbon-tools", id="pbar-present"):
                yield Button("▶ Present from Start", variant="warning", id="slides-present-start")
                yield Button("▶ Present Current (Alt+P)", variant="success", id="slides-present")

        with Horizontal(id="slides-split"):
            yield ListView(id="slides-list")
            with Vertical(id="slides-editor-pane"):
                yield Static("[b]Slide Title[/b]")
                yield Input(id="slide-title-input", placeholder="Slide title...")
                yield Static("[b]Slide Content (Markdown)[/b]")
                yield TextArea("", language="markdown", id="slide-body-input")
                yield Static("[b]Speaker Notes[/b]")
                yield Input(id="slide-notes-input", placeholder="Optional speaker notes...")
            with Vertical(id="slides-preview-pane"):
                yield Static("", id="slide-preview-title")
                yield Markdown("", id="slide-preview-body")

        yield Static("", id="slides-status", classes="status-strip")

    def on_mount(self) -> None:
        self._switch_ribbon("slides")
        self._refresh_list()
        self._load_slide_into_editor(0)
        self.query_one("#slides-list", ListView).focus()

    def _switch_ribbon(self, tab: str) -> None:
        for name in ("file", "slides", "insert", "design", "present"):
            bar = self.query_one(f"#pbar-{name}", Horizontal)
            btn = self.query_one(f"#ptab-{name}", Button)
            bar.display = name == tab
            if name == tab:
                btn.add_class("-active-tab")
            else:
                btn.remove_class("-active-tab")

    def _update_status(self, msg: str = "") -> None:
        fname = self.current_file.name if self.current_file else "Untitled.pptx"
        self.query_one("#slides-file-label", Static).update(f"  [b #fb923c]{fname}[/b #fb923c]")
        prefix = f"{msg}  •  " if msg else ""
        self.query_one("#slides-status", Static).update(
            f"{prefix}Slide {self.current_index + 1}/{len(self.slides)}  •  Theme: {self.theme_name}  •  ^M New  •  Alt+P Present  •  ^O Open  •  ^S Save"
        )

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
        self.query_one("#slide-notes-input", Input).value = s.notes
        self._update_preview()
        self._update_status()

    def _update_preview(self) -> None:
        s = self.slides[self.current_index]
        accent, _ = SLIDE_THEMES.get(self.theme_name, ("#fb923c", "#0f172a"))
        self.query_one("#slide-preview-title", Static).update(f"[b {accent}]{s.title}[/b {accent}]\n")
        self.query_one("#slide-preview-body", Markdown).update(s.body or "_(empty)_")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "slides-list" and event.list_view.index is not None:
            self._load_slide_into_editor(event.list_view.index)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "slide-title-input":
            self.slides[self.current_index].title = event.value
            self._update_preview()
        elif event.input.id == "slide-notes-input":
            self.slides[self.current_index].notes = event.value

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if event.text_area.id == "slide-body-input":
            self.slides[self.current_index].body = event.text_area.text
            self._update_preview()

    def action_add_slide(self) -> None:
        self.slides.append(SlideData(title=f"Slide {len(self.slides) + 1}", body="- New bullet point"))
        self._refresh_list()
        self._load_slide_into_editor(len(self.slides) - 1)
        self._update_status(f"Added Slide {len(self.slides)}")

    def action_prev_slide(self) -> None:
        if self.current_index > 0:
            self._load_slide_into_editor(self.current_index - 1)

    def action_next_slide(self) -> None:
        if self.current_index < len(self.slides) - 1:
            self._load_slide_into_editor(self.current_index + 1)

    def action_present_mode(self) -> None:
        self.app.push_screen(PresentScreen(self.slides, self.current_index, self.theme_name))

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
                title="Open Presentation (.pptx, .md, .json)",
                start_dir=self.current_file.parent if self.current_file else Path.cwd(),
                extensions=(".pptx", ".md", ".json"),
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
                title="Save Presentation As (.pptx, .md, .json)",
                start_dir=self.current_file.parent if self.current_file else Path.cwd(),
                extensions=(".pptx", ".md", ".json"),
                default_name=self.current_file.name if self.current_file else "deck.pptx",
            ),
            _on_picked,
        )

    def _save_to(self, path: Path) -> None:
        try:
            save_presentation(path, self.slides)
            self.current_file = path
            add_recent_file(path, "slides")
            self._update_status(f"Saved {path.name}")
            self.notify(f"Saved {len(self.slides)} slides to {path.name}", timeout=2)
        except Exception as exc:
            self.notify(f"Save error: {exc}", severity="error")

    def action_save_deck(self) -> None:
        if self.current_file is None:
            self._open_save_as()
        else:
            self._save_to(self.current_file)

    def open_file(self, path: Path) -> None:
        self.slides = load_presentation(path)
        self.current_file = path
        self._refresh_list()
        self._load_slide_into_editor(0)
        add_recent_file(path, "slides")
        self.notify(f"Opened {path.name} ({len(self.slides)} slides)", timeout=2)

    def _insert_body(self, snippet: str) -> None:
        ed = self.query_one("#slide-body-input", TextArea)
        ed.insert(snippet)
        self.slides[self.current_index].body = ed.text
        self._update_preview()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid.startswith("ptab-"):
            self._switch_ribbon(bid[5:])
        elif bid.startswith("ptheme-"):
            self.theme_name = event.button.name or "Midnight Orange"
            self._update_preview()
            self._update_status(f"Theme → {self.theme_name}")
        elif bid == "slides-new":
            self.current_file = None
            self.slides = [SlideData(title="Slide 1", body="- Start here")]
            self._refresh_list()
            self._load_slide_into_editor(0)
        elif bid == "slides-open":
            self.action_open_picker()
        elif bid == "slides-save":
            self.action_save_deck()
        elif bid == "slides-save-as":
            self._open_save_as()
        elif bid == "slides-add":
            self.action_add_slide()
        elif bid == "slides-dup":
            cur = self.slides[self.current_index]
            self.slides.insert(
                self.current_index + 1,
                SlideData(title=f"{cur.title} (Copy)", body=cur.body, notes=cur.notes),
            )
            self._refresh_list()
            self._load_slide_into_editor(self.current_index + 1)
        elif bid == "slides-up" and self.current_index > 0:
            i = self.current_index
            self.slides[i - 1], self.slides[i] = self.slides[i], self.slides[i - 1]
            self._refresh_list()
            self._load_slide_into_editor(i - 1)
        elif bid == "slides-down" and self.current_index < len(self.slides) - 1:
            i = self.current_index
            self.slides[i + 1], self.slides[i] = self.slides[i], self.slides[i + 1]
            self._refresh_list()
            self._load_slide_into_editor(i + 1)
        elif bid == "slides-del":
            if len(self.slides) <= 1:
                self._update_status("Cannot delete the last slide")
                return
            self.slides.pop(self.current_index)
            self._refresh_list()
            self._load_slide_into_editor(max(0, self.current_index - 1))
        elif bid == "slides-present":
            self.action_present_mode()
        elif bid == "slides-present-start":
            self.app.push_screen(PresentScreen(self.slides, 0, self.theme_name))
        elif bid == "pins-bullets":
            self._insert_body("\n- Point 1\n- Point 2\n")
        elif bid == "pins-table":
            self._insert_body("\n| Metric | Value |\n| --- | --- |\n| Speed | Fast |\n")
        elif bid == "pins-code":
            self._insert_body("\n```python\nprint('Hello Clice!')\n```\n")
        elif bid == "pins-quote":
            self._insert_body("\n> Key takeaway quote\n")
        elif bid == "pins-check":
            self._insert_body("\n- [x] Done\n- [ ] Next step\n")
