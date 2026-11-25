"""GUI-like TCSS styling and theme list for Clice."""

AVAILABLE_THEMES = [
    "tokyo-night",
    "textual-dark",
    "nord",
    "dracula",
    "gruvbox",
    "catppuccin-mocha",
    "textual-light",
]

CLICE_CSS = """
Screen {
    layout: vertical;
    background: $surface;
}

/* Top GUI-like Ribbon / Title Bar */
#top-bar {
    height: 3;
    dock: top;
    background: $panel;
    border-bottom: solid $primary;
    padding: 0 1;
    align: left middle;
}

#brand-badge {
    width: auto;
    padding: 0 2;
    background: $primary;
    color: $text;
    text-style: bold;
    content-align: center middle;
    height: 1;
    margin-right: 1;
}

#top-cwd {
    width: 1fr;
    color: $text-muted;
    content-align: left middle;
    height: 1;
    padding: 0 1;
}

#top-actions {
    width: auto;
    height: 3;
    align: right middle;
}

#top-actions Button {
    min-width: 10;
    height: 1;
    margin: 0 0 0 1;
    border: none;
}

/* Main Desktop Shell: Left Dock + Workspace */
#main-shell {
    height: 1fr;
    width: 1fr;
}

#sidebar {
    width: 24;
    background: $panel;
    border-right: solid $primary-darken-2;
    padding: 1 1;
    overflow-y: auto;
}

.sidebar-section {
    color: $accent;
    text-style: bold;
    margin: 1 0 0 1;
    height: 1;
}

.nav-btn {
    width: 100%;
    height: 3;
    content-align: left middle;
    margin: 0 0 0 0;
    background: transparent;
    border: none;
    color: $text;
    padding: 0 1;
}

.nav-btn:hover {
    background: $boost;
}

.nav-btn.-active {
    background: $primary;
    color: $text;
    text-style: bold;
}

#workspace {
    width: 1fr;
    height: 1fr;
    padding: 1 2;
    overflow-y: auto;
}

/* Common App Chrome */
.app-header {
    height: 3;
    background: $panel;
    border: round $primary-darken-1;
    padding: 0 2;
    margin-bottom: 1;
    align: left middle;
}

.app-title {
    text-style: bold;
    color: $text;
    width: auto;
    margin-right: 2;
}

.toolbar {
    height: 3;
    margin-bottom: 1;
    align: left middle;
}

.toolbar Button {
    margin-right: 1;
    min-width: 8;
}

.toolbar Input {
    margin-right: 1;
}

.status-strip {
    height: 1;
    background: $panel;
    color: $text-muted;
    padding: 0 1;
    dock: bottom;
}

/* Home Dashboard Tiles */
#home-banner {
    height: auto;
    padding: 1 2;
    margin-bottom: 1;
    background: $primary-darken-2;
    border: tall $primary;
}

#home-grid {
    layout: grid;
    grid-size: 3;
    grid-gutter: 1 2;
    height: auto;
    margin-bottom: 1;
}

.app-card {
    height: 7;
    padding: 1 2;
    border: round $primary;
    background: $panel;
}

.app-card:hover {
    background: $boost;
    border: round $accent;
}

.card-excel { border: round #22c55e; }
.card-word { border: round #3b82f6; }
.card-ppt { border: round #f97316; }
.card-files { border: round #eab308; }
.card-dev { border: round #a855f7; }
.card-calc { border: round #06b6d4; }
.card-notes { border: round #ec4899; }
.card-cal { border: round #14b8a6; }
.card-sys { border: round #ef4444; }
.card-plugins { border: round #8b5cf6; }

/* Sheets (Excel) */
#sheets-formula-bar {
    height: 3;
    margin-bottom: 1;
    align: left middle;
}

#sheets-cell-badge {
    width: 10;
    height: 3;
    content-align: center middle;
    background: #166534;
    color: white;
    text-style: bold;
    margin-right: 1;
}

#sheets-table {
    height: 1fr;
    border: round #22c55e;
}

/* Docs (Word) */
#docs-split {
    height: 1fr;
}

#docs-editor {
    width: 1fr;
    height: 1fr;
    border: round #3b82f6;
    margin-right: 1;
}

#docs-preview-scroll {
    width: 1fr;
    height: 1fr;
    border: round $primary-darken-1;
    padding: 1 2;
    background: $panel;
}

/* Slides (PowerPoint) */
#slides-split {
    height: 1fr;
}

#slides-list {
    width: 26;
    height: 1fr;
    border: round #f97316;
    margin-right: 1;
}

#slides-editor-pane {
    width: 1fr;
    height: 1fr;
    margin-right: 1;
}

#slides-preview-pane {
    width: 1fr;
    height: 1fr;
    border: double #f97316;
    background: $panel;
    padding: 2 3;
}

/* Presentation Fullscreen Modal */
#present-screen {
    background: #0f172a;
    align: center middle;
    padding: 2 4;
}

#present-card {
    width: 90%;
    height: 85%;
    border: double #f97316;
    background: #1e293b;
    padding: 2 4;
}

#present-title {
    text-style: bold;
    color: #fb923c;
    content-align: center middle;
    height: 3;
    border-bottom: solid #f97316;
    margin-bottom: 1;
}

#present-body {
    height: 1fr;
    padding: 1 2;
}

#present-footer {
    height: 2;
    color: #94a3b8;
    content-align: center middle;
}

/* Files */
#files-table {
    height: 1fr;
    border: round #eab308;
}

/* Calculator */
#calc-display {
    height: 4;
    border: round #06b6d4;
    background: $panel;
    content-align: right middle;
    padding: 0 2;
    text-style: bold;
    margin-bottom: 1;
}

#calc-keypad {
    layout: grid;
    grid-size: 5;
    grid-gutter: 1 1;
    height: auto;
    width: 50;
}

#calc-keypad Button {
    width: 100%;
    height: 3;
}

/* SysMon */
.metric-box {
    height: auto;
    border: round $primary-darken-1;
    background: $panel;
    padding: 1 2;
    margin-bottom: 1;
}

/* DevTools */
#dev-tabs {
    height: 1fr;
}

.code-area {
    height: 1fr;
    border: round #a855f7;
}

/* Main Menu App Rectangles (Arrow + Click Navigable) */
#home-grid-tiles {
    layout: grid;
    grid-size: 3;
    grid-gutter: 1 2;
    height: auto;
    margin-bottom: 1;
}

.app-tile {
    height: 8;
    padding: 1 2;
    border: round $primary-darken-1;
    background: $panel;
}

.app-tile:hover {
    background: $boost;
    border: heavy $accent;
}

.app-tile:focus {
    background: $primary-darken-2;
    border: double $accent;
}

.tile-excel { border: round #22c55e; }
.tile-excel:focus { border: double #4ade80; background: #052e16; }
.tile-word { border: round #3b82f6; }
.tile-word:focus { border: double #60a5fa; background: #172554; }
.tile-ppt { border: round #f97316; }
.tile-ppt:focus { border: double #fb923c; background: #431407; }
.tile-files { border: round #eab308; }
.tile-files:focus { border: double #facc15; background: #422006; }
.tile-dev { border: round #a855f7; }
.tile-dev:focus { border: double #c084fc; background: #3b0764; }
.tile-calc { border: round #06b6d4; }
.tile-calc:focus { border: double #22d3ee; background: #083344; }
.tile-notes { border: round #ec4899; }
.tile-notes:focus { border: double #f472b6; background: #500724; }
.tile-cal { border: round #14b8a6; }
.tile-cal:focus { border: double #2dd4bf; background: #042f2e; }
.tile-sys { border: round #ef4444; }
.tile-sys:focus { border: double #f87171; background: #450a0a; }
.tile-plugins { border: round #8b5cf6; }
.tile-plugins:focus { border: double #a78bfa; background: #2e1065; }

/* Office-Style Top Ribbon */
.ribbon-container {
    height: auto;
    background: $panel;
    border: round $primary-darken-1;
    padding: 0 1;
    margin-bottom: 1;
}

.ribbon-tabs {
    height: 3;
    border-bottom: solid $primary-darken-2;
    align: left middle;
}

.ribbon-tabs Button {
    min-width: 10;
    height: 3;
    margin-right: 1;
    background: transparent;
    border: none;
}

.ribbon-tabs Button.-active-tab {
    background: $primary;
    text-style: bold;
}

.ribbon-tools {
    height: 3;
    padding: 0 0;
    align: left middle;
}

.ribbon-tools Button {
    min-width: 8;
    height: 3;
    margin-right: 1;
}

.find-bar {
    height: 3;
    margin-bottom: 1;
    align: left middle;
}

.find-bar Input {
    width: 1fr;
    margin-right: 1;
}

/* Modal File Picker */
FilePickerModal {
    align: center middle;
}

#file-picker-dialog {
    width: 80%;
    height: 80%;
    background: $surface;
    border: double $accent;
    padding: 1 2;
}

#fp-header {
    height: 2;
    border-bottom: solid $primary;
    margin-bottom: 1;
}

#fp-cwd {
    height: 1;
    color: $accent;
    margin-bottom: 1;
}

#fp-table {
    height: 1fr;
    border: round $primary-darken-1;
    margin-bottom: 1;
}

#fp-footer {
    height: 3;
    align: left middle;
}

#fp-filename {
    width: 1fr;
    margin-right: 1;
}
"""
