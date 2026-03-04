```
EDMCModernOverlay/
|-- README.md                       # Install & usage guide
|-- RELEASE_NOTES.md                # Release changelog
|-- LICENSE                         # Project licensing
|-- .gitignore                      # Ignore rules (see note on respecting them)
|-- EDMCModernOverlay.code-workspace  # Optional VS Code workspace definition
|-- .codex/
|   `-- agents.md                   # Codex CLI agent metadata
|-- .github/
|   `-- workflows/                  # CI/release pipelines
|-- .vscode/
|   |-- launch.json                 # Recommended debug configuration
|   `-- settings.json               # Workspace settings
|-- docs/
|   |-- FAQ.md                      # Expanded setup and troubleshooting notes
|   |-- developer.md                # Development tips and versioning details
|   |-- troubleshooting.md          # Debugging playbook
|   `-- (more renderer/layout docs)
|-- extras/                         # Installer assets (fonts, icons)
|-- requirements/
|   `-- dev.txt                     # Dev/test tooling dependencies
|-- schemas/
|   `-- overlay_groupings.schema.json  # Overlay groupings schema
|-- scripts/                        # Installer/build helpers
|-- utils/                          # Developer utilities and debug collectors
|-- tests/                          # Pytest + integration fixtures
|-- __init__.py                     # Package marker for EDMC imports
|-- load.py                         # EDMC entry hook copied into the plugins dir
|-- edmcoverlay.py                  # Legacy shim module (`import edmcoverlay`)
|-- EDMCOverlay/                    # Package form of the legacy shim
|   |-- __init__.py
|   `-- edmcoverlay.py
|-- overlay_plugin/                 # Runtime that runs inside EDMC
|   |-- overlay_api.py              # Helper API for other plugins
|   |-- overlay_socket_server.py    # JSON-over-TCP broadcaster
|   |-- overlay_watchdog.py         # Subprocess supervisor for the client
|   `-- preferences.py              # myNotebook-backed settings panel
|-- overlay_client/                 # Stand-alone PyQt6 overlay process
|   |-- overlay_client.py           # Main window and socket bridge
|   |-- client_config.py            # Bootstrap defaults and OverlayConfig parsing
|   |-- platform_integration.py     # Window stacking/input helpers per platform
|   |-- render_surface.py           # Rendering pipeline and caching
|   |-- requirements/
|   |   |-- base.txt                # Core client requirements (PyQt6, etc.)
|   |   `-- wayland.txt             # Wayland/KDE helpers installed on Wayland
|   `-- fonts/
|       |-- README.txt
|       |-- preferred_fonts.txt     # Optional case-insensitive priority list
|       `-- emoji_fallbacks.txt     # Emoji fallback font list
|-- overlay_controller/             # Layout/placement UI
|   |-- overlay_controller.py       # Main controller entry
|   |-- controller/                 # Controller state and actions
|   |-- services/                   # Plugin bridge + cache services
|   |-- widgets/                    # UI widgets
|   `-- preview/                    # Preview renderer
|-- group_cache.py                  # Placement cache helpers
|-- prefix_entries.py               # Plugin prefix registration helpers
|-- version.py                      # Central version metadata for releases
|-- pyproject.toml                  # Tooling configuration
|-- Makefile                        # Convenience build targets
|-- conftest.py                     # Pytest configuration
|-- overlay_groupings.json          # Shipped plugin group defaults
|-- overlay_groupings.user.json     # User overrides (not in git)
|-- overlay_group_cache.json        # Placement cache (runtime)
|-- overlay_settings.json           # Preferences persisted by the plugin
|-- debug.json                      # Debug toggles (dev builds)
|-- dev_settings.json               # Dev-only flags
`-- port.json                       # Runtime port + log level
```