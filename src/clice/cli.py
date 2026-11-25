"""CLI entry point for Clice (supports --app, --open, --cd-file, --shell-init, --plugins-dir)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from clice import __version__

SHELL_INIT_SNIPPETS = {
    "bash": """# Add to ~/.bashrc: eval "$(clice --shell-init bash)"
clice-cd() {
    local tmpfile
    tmpfile="$(mktemp)"
    clice --cd-file "$tmpfile" "$@"
    if [ -s "$tmpfile" ]; then
        cd "$(cat "$tmpfile")" || true
    fi
    rm -f "$tmpfile"
}
""",
    "zsh": """# Add to ~/.zshrc: eval "$(clice --shell-init zsh)"
clice-cd() {
    local tmpfile
    tmpfile="$(mktemp)"
    clice --cd-file "$tmpfile" "$@"
    if [ -s "$tmpfile" ]; then
        cd "$(cat "$tmpfile")" || true
    fi
    rm -f "$tmpfile"
}
""",
    "fish": """# Add to ~/.config/fish/config.fish: clice --shell-init fish | source
function clice-cd
    set tmpfile (mktemp)
    clice --cd-file $tmpfile $argv
    if test -s $tmpfile
        cd (cat $tmpfile)
    end
    rm -f $tmpfile
end
""",
    "powershell": """# Add to $PROFILE: clice --shell-init powershell | Invoke-Expression
function clice-cd {
    $tmpfile = [System.IO.Path]::GetTempFileName()
    clice --cd-file $tmpfile @args
    if ((Test-Path $tmpfile) -and ((Get-Item $tmpfile).Length -gt 0)) {
        Set-Location (Get-Content $tmpfile -Raw).Trim()
    }
    Remove-Item $tmpfile -ErrorAction SilentlyContinue
}
""",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="clice",
        description="Clice — Colorful GUI-like Terminal Office Suite & Developer Multitool",
    )
    parser.add_argument("file", nargs="?", help="Optional file to open directly in Clice")
    parser.add_argument(
        "--app",
        default="home",
        choices=["home", "sheets", "docs", "slides", "files", "devtools", "calc", "notes", "calendar", "sysmon", "plugins"],
        help="Start directly in a specific Clice app",
    )
    parser.add_argument(
        "--plugins-dir",
        type=Path,
        action="append",
        default=[],
        help="Additional directory to load Clice plugins from",
    )
    parser.add_argument(
        "--cd-file",
        type=Path,
        default=None,
        help="Write the chosen directory to this file on 'CD & Exit' (used by clice-cd shell wrapper)",
    )
    parser.add_argument(
        "--shell-init",
        choices=["bash", "zsh", "fish", "powershell"],
        default=None,
        help="Print shell integration snippet for easy terminal `cd` via `clice-cd`",
    )
    parser.add_argument(
        "--no-intro",
        action="store_true",
        help="Skip the animated intro splash screen on startup",
    )
    parser.add_argument("-v", "--version", action="version", version=f"clice {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.shell_init:
        print(SHELL_INIT_SNIPPETS[args.shell_init])
        return 0

    from clice.app import CliceApp

    initial_file = Path(args.file).expanduser().resolve() if args.file else None
    app = CliceApp(
        initial_app=args.app,
        initial_file=initial_file,
        extra_plugin_dirs=args.plugins_dir,
        cd_file=args.cd_file,
        show_intro=not args.no_intro,
    )
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
