# Clice Plugin & Marketplace Documentation

Clice supports both **local plugins** (`~/.clice/plugins/`) and **GitHub Marketplace plugins** (default repo: [`jaunchun-tech/clice-marketplace`](https://github.com/jaunchun-tech/clice-marketplace)).

## Folder Structure

```text
clice-marketplace/
├── plugins/
│   └── <plugin_slug>/
│       └── plugin.py          # Subclass of ClicePlugin
└── readme/
    └── <plugin_slug>/
        ├── README.md          # Shown live in Clice's Plugins & Marketplace tab
        └── ...                # Optional assets
```

## Plugin API (`ClicePlugin`)

Every plugin must define a subclass of `clice.core.plugins.ClicePlugin`:

| Attribute / Method | Description |
| --- | --- |
| `id: str` | Unique plugin ID (e.g. `"plugin_my_tool"`) |
| `name: str` | Display name in Sidebar, Main Menu, and Spotlight |
| `icon: str` | Crisp 2–3 char badge (e.g. `"[M]"`, `"[G]"`) |
| `description: str` | Short description shown on the Main Menu rectangle |
| `version: str` | SemVer string (e.g. `"0.1.0"`) |
| `author: str` | Author name or GitHub handle |
| `create_widget(self) -> Widget` | Returns the Textual `Widget` rendered when opened |

## Testing Locally

```bash
clice --plugins-dir marketplace/plugins
```

See `marketplace/plugins/` for 4 complete example plugins (`git_quick`, `pomodoro_pro`, `port_scanner`, `markdown_cheatsheet`) ready to push to `jaunchun-tech/clice-marketplace`.
