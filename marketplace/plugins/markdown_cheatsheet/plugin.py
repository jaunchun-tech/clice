"""Clice Marketplace Plugin: Markdown Cheatsheet & Live Sandbox."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Markdown, Static, TextArea

from clice.core.plugins import ClicePlugin

CHEATSHEET = """# Markdown Cheatsheet
## Formatting
- **Bold**: `**bold**`
- *Italic*: `*italic*`
- ~~Strikethrough~~: `~~strike~~`
- `Inline code`: `` `code` ``

## Lists & Tasks
- [x] Installed Markdown Cheatsheet plugin
- [ ] Try editing on the left to see live preview!

## Table
| Syntax | Result |
| --- | --- |
| `# H1` | Heading 1 |
| `> Quote` | Blockquote |
"""


class MarkdownCheatsheetWidget(Vertical):
    """Interactive Markdown syntax reference with live side-by-side sandbox."""

    def compose(self) -> ComposeResult:
        yield Static("[b #3b82f6]\\[M] Markdown Cheatsheet (Plugin)[/b #3b82f6]", classes="app-title")
        with Horizontal(id="docs-split"):
            yield TextArea(CHEATSHEET, language="markdown", id="mdcs-in")
            with VerticalScroll(id="docs-preview-scroll"):
                yield Markdown(CHEATSHEET, id="mdcs-out")

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if event.text_area.id == "mdcs-in":
            self.query_one("#mdcs-out", Markdown).update(event.text_area.text)


class MarkdownCheatsheetPlugin(ClicePlugin):
    id = "plugin_markdown_cheatsheet"
    name = "MD Cheatsheet"
    icon = "[M]"
    description = "Interactive Markdown reference and live side-by-side sandbox."
    version = "0.1.0"
    author = "Clice Marketplace"

    def create_widget(self) -> Vertical:
        return MarkdownCheatsheetWidget()
