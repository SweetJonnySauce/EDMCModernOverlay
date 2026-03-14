## Does the plug in follow EDMC guidelines for good plugin development?
Yes, and they are re-validated with each major change to functionality. The following best practices are checked for:

- Implements the documented EDMC hooks (`plugin_start3`, `plugin_stop`, `plugin_prefs`, `prefs_changed`, `journal_entry`); `plugin_app` explicitly returns `None`, so the Tk main thread stays idle.
- Long-running work stays off the Tk thread. `WebSocketBroadcaster` runs on a daemon thread with its own asyncio loop, `OverlayWatchdog` supervises the client on another daemon thread, and `plugin_stop()` stops both and removes `port.json`.
- Plugin-owned timers are guarded by `_config_timer_lock`, keeping rebroadcast scheduling thread-safe across shutdowns and restarts.
- Plugin state lives inside this directory. `Preferences` reads and writes `overlay_settings.json`, while developer-only toggles (payload mirroring, tracing, stdout/stderr capture) live in `debug.json` and are only honoured in dev builds.
- Logging integrates with EDMC’s logger via `_EDMCLogHandler`; optional payload mirroring and stdout/stderr capture are controlled via `debug.json` and still emit additional detail only when EDMC logging is set to DEBUG.
- The overlay client launches with the dedicated `overlay_client/.venv` interpreter (or an override via `EDMC_OVERLAY_PYTHON`), keeping EDMC’s bundled Python environment untouched.
- Other plugins publish safely through `overlay_plugin.overlay_api.send_overlay_message`, which validates payload structure and size before handing messages to the broadcaster.
- Platform-aware paths handle Windows-specific interpreter names and window flags while keeping Linux/macOS support intact.