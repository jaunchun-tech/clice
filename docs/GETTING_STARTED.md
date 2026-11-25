# Getting Started with Clice

**Clice** is a cross-platform (macOS, Linux, Windows), keyboard-first, GUI-like terminal office suite & developer multitool built with Python and Textual.

## Installation

Requires **Python 3.10+**.

### Linux / macOS (Bash or Zsh)
```bash
git clone https://github.com/jaunchun-tech/clice.git
cd clice
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
clice
```

### Linux / macOS (Fish shell)
```fish
git clone https://github.com/jaunchun-tech/clice.git
cd clice
python3 -m venv .venv
source .venv/bin/activate.fish
pip install -e .
clice
```

### Windows (PowerShell)
```powershell
git clone https://github.com/jaunchun-tech/clice.git
cd clice
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
clice
```

## Easy Terminal `cd` (`clice-cd`)

Add the shell wrapper for your shell:
- **Bash**: `eval "$(clice --shell-init bash)"`
- **Zsh**: `eval "$(clice --shell-init zsh)"`
- **Fish**: `clice --shell-init fish | source`
- **PowerShell**: `clice --shell-init powershell | Invoke-Expression`

Then run `clice-cd`, navigate to any directory in **Files (`F5`)**, and press **`C`** (CD & Exit) to change your terminal's working directory!
