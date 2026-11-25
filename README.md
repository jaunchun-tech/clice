# ✨ Clice — Terminal Office Suite & Developer Multitool

**Clice** is a colorful, GUI-like terminal application (TUI) built with Python and [Textual](https://textual.textualize.io/). It brings **Microsoft Office-style apps** (Excel, Word, PowerPoint), a **File Explorer with easy `cd`**, **Coding & Developer Utilities**, **Productivity tools**, **System Monitor**, and a **local Plugin System** into one fast, cross-platform terminal workspace.

Works natively on **macOS**, **Linux**, and **Windows** (Windows Terminal, PowerShell, CMD, iTerm2, Kitty, Alacritty, etc.) with **full mouse support**, keyboard shortcuts, and 7 switchable color themes.

---

## 🚀 Built-in Apps

| App | Icon | What it does |
| --- | :---: | --- |
| **Clice Sheets** | 📊 | Excel-like spreadsheet grid with formula engine (`=SUM`, `=AVG`, `=MIN`, `=MAX`, `=COUNT`, `=IF`, `=ROUND`, `=SQRT`, cell ranges `A1:B5`) and real **`.xlsx` / `.csv`** open & save. |
| **Clice Docs** | 📝 | Word processor with side-by-side live Markdown preview, formatting toolbar (H1/H2/Bold/Italic/List/Code), word/character/reading-time stats, and real **`.docx` / `.md` / `.txt`** open & save. |
| **Clice Slides** | 📽️ | PowerPoint-style slide deck editor with slide list, live preview, **Full-Screen Present Mode** (`▶ Present`), and real **`.pptx` / `.json` / `.md`** open & save. |
| **Clice Files** | 📁 | Cross-platform File Explorer with **easy `cd`**, **`mkdir`**, **`touch`**, delete, and one-click opening of files directly in Sheets, Docs, Slides, or Code Pad. |
| **Coding Utils** | 💻 | All-in-one developer toolbox: **JSON** formatter/minifier/validator, **Regex** tester, **Base64 & URL** encoder/decoder, **MD5/SHA1/SHA256/SHA512** hasher, **UUID4** generator, **JWT** decoder, **HEX/RGB/HSL** color converter, and a **Code Scratchpad**. |
| **Calculator** | 🧮 | Scientific calculator with clickable GUI keypad, expression history, and a **Programmer Base Converter** (`DEC` / `HEX` / `OCT` / `BIN`). |
| **Notes & Tasks** | ✅ | Persistent To-Do manager with priorities & checkboxes + Quick Markdown Notes saved to `~/.clice/data/`. |
| **Calendar & Focus** | 📅 | Interactive monthly calendar with saved day events + built-in **Pomodoro 25:00 Focus Timer**. |
| **System Monitor** | 🖥️ | Live cross-platform CPU, RAM, Disk usage bars and Top Processes table. |
| **Plugins Manager** | 🧩 | Discover, reload, and scaffold custom local Clice plugins in one click. |

---

## 📦 Installation (macOS, Linux, Windows)

Requires **Python 3.10+**.

```bash
git clone https://github.com/jaunchun-tech/clice.git
cd clice
pip install -e .
```

Or install in a virtual environment:

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
```

---

## 🖥️ Usage

Launch Clice:

```bash
clice
```

Open a specific file directly in the matching app:

```bash
clice budget.xlsx
clice report.docx
clice presentation.pptx
clice script.py
```

Jump straight into a specific app:

```bash
clice --app sheets
clice --app docs
clice --app slides
clice --app files
clice --app devtools
```

Load plugins from an extra folder (e.g. the included Git Quick example plugin):

```bash
clice --plugins-dir examples/plugins
```

---

## 📌 Easy `cd` Shell Integration (`clice-cd`)

Because a child process cannot change its parent shell's working directory directly, Clice includes a built-in shell wrapper generator so clicking **📌 CD & Exit** in **Clice Files** actually `cd`s your terminal!

- **Bash** (`~/.bashrc`):
  ```bash
  eval "$(clice --shell-init bash)"
  ```
- **Zsh** (`~/.zshrc`):
  ```bash
  eval "$(clice --shell-init zsh)"
  ```
- **Fish** (`~/.config/fish/config.fish`):
  ```fish
  clice --shell-init fish | source
  ```
- **PowerShell** (`$PROFILE`):
  ```powershell
  clice --shell-init powershell | Invoke-Expression
  ```

Then run `clice-cd`, navigate to any folder in **Files**, and click **📌 CD & Exit**!

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| --- | --- |
| `F1` | Home Dashboard |
| `F2` | Clice Sheets (Excel) |
| `F3` | Clice Docs (Word) |
| `F4` | Clice Slides (PowerPoint) |
| `F5` | Clice Files & `cd` |
| `F6` | Coding Utils |
| `Ctrl+T` | Cycle Color Theme (`tokyo-night`, `textual-dark`, `nord`, `dracula`, `gruvbox`, `catppuccin-mocha`, `textual-light`) |
| `Ctrl+P` | Textual Command Palette |
| `Ctrl+Q` | Quit Clice |

In **Present Mode** (Clice Slides): `→` / `Space` / `Enter` for Next Slide, `←` for Previous Slide, `Esc` / `Q` to exit.

---

## 🧩 Writing Plugins

Clice automatically loads any `.py` file placed in:
- `~/.clice/plugins/` (user-global plugins)
- `./plugins/` (project-local plugins)
- Any directory passed via `--plugins-dir`

You can also click **+ Create Plugin Template** inside the **🧩 Plugins** app to generate a ready-to-edit plugin!

Minimal plugin example:

```python
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static
from clice.core.plugins import ClicePlugin

class HelloWidget(Vertical):
    def compose(self) -> ComposeResult:
        yield Static("👋 Hello from my custom Clice plugin!")

class HelloPlugin(ClicePlugin):
    id = "plugin_hello"
    name = "Hello"
    icon = "👋"
    description = "My first Clice plugin"
    version = "0.1.0"
    author = "You"

    def create_widget(self) -> Vertical:
        return HelloWidget()
```

See `examples/plugins/git_quick.py` for a full working example.

---

## 🧪 Running Tests

```bash
pip install -e ".[dev]"
pytest
```
