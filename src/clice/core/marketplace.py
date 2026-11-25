"""GitHub Marketplace client for Clice (default repo: jaunchun-tech/clice-marketplace)."""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from clice.core.config import get_clice_home, get_plugins_dir

DEFAULT_MARKETPLACE_REPO = "jaunchun-tech/clice-marketplace"


@dataclass
class MarketplacePluginInfo:
    slug: str
    repo: str
    files_api_url: str


def _gh_get_json(url: str) -> object:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "clice-marketplace-client/0.1",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _gh_get_text(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "clice-marketplace-client/0.1"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read().decode("utf-8")


def list_marketplace_plugins(repo: str = DEFAULT_MARKETPLACE_REPO) -> list[MarketplacePluginInfo]:
    """List plugin folders under `plugins/` in a GitHub marketplace repository."""
    url = f"https://api.github.com/repos/{repo}/contents/plugins"
    data = _gh_get_json(url)
    if not isinstance(data, list):
        return []
    out: list[MarketplacePluginInfo] = []
    for item in data:
        if isinstance(item, dict) and item.get("type") == "dir":
            slug = str(item.get("name", ""))
            if slug and not slug.startswith("."):
                out.append(
                    MarketplacePluginInfo(
                        slug=slug,
                        repo=repo,
                        files_api_url=str(item.get("url", "")),
                    )
                )
    return out


def fetch_marketplace_readme(slug: str, repo: str = DEFAULT_MARKETPLACE_REPO) -> str:
    """Fetch `readme/<slug>/README.md` from the GitHub marketplace repo."""
    for branch in ("main", "master"):
        raw_url = f"https://raw.githubusercontent.com/{repo}/{branch}/readme/{slug}/README.md"
        try:
            return _gh_get_text(raw_url)
        except Exception:
            continue
    return f"# {slug}\n\n_No `readme/{slug}/README.md` found in `{repo}`._"


def install_marketplace_plugin(slug: str, repo: str = DEFAULT_MARKETPLACE_REPO) -> Path:
    """Download all files from `plugins/<slug>/` into `~/.clice/plugins/<slug>/` and its README."""
    url = f"https://api.github.com/repos/{repo}/contents/plugins/{slug}"
    items = _gh_get_json(url)
    if not isinstance(items, list):
        raise RuntimeError(f"Could not list files for plugin '{slug}' in {repo}")

    dest_dir = get_plugins_dir() / slug
    dest_dir.mkdir(parents=True, exist_ok=True)

    for item in items:
        if isinstance(item, dict) and item.get("type") == "file" and item.get("download_url"):
            fname = str(item["name"])
            content = _gh_get_text(str(item["download_url"]))
            (dest_dir / fname).write_text(content, encoding="utf-8")

    # Also save README locally so it works offline!
    readme_text = fetch_marketplace_readme(slug, repo=repo)
    readme_dir = get_clice_home() / "readme" / slug
    readme_dir.mkdir(parents=True, exist_ok=True)
    (readme_dir / "README.md").write_text(readme_text, encoding="utf-8")
    return dest_dir
