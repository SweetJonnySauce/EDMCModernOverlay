from __future__ import annotations

import logging

import load
from overlay_plugin import hotkeys
from overlay_plugin import preferences as prefs


class _SharedLaunchRuntime:
    def __init__(self) -> None:
        self.launch_sources: list[str] = []

    def send_test_message(self, text: str, x: int | None = None, y: int | None = None) -> None:  # pragma: no cover - unused
        return

    def launch_overlay_controller(self, *, source: load.LaunchSource = "chat") -> None:
        self.launch_sources.append(source)

    def cycle_payload_next(self) -> None:  # pragma: no cover - unused
        raise RuntimeError("unused")

    def cycle_payload_prev(self) -> None:  # pragma: no cover - unused
        raise RuntimeError("unused")


def test_chat_settings_hotkey_paths_route_to_expected_launch_modes() -> None:
    runtime = _SharedLaunchRuntime()

    # Chat command path.
    helper = load._PluginRuntime._build_command_helper(runtime, "!overlay")
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay"}) is True
    assert runtime.launch_sources == ["chat"]

    # Settings button path.
    panel = object.__new__(prefs.PreferencesPanel)
    panel._launch_controller = lambda: runtime.launch_overlay_controller(source="settings")
    panel._on_launch_controller()
    assert runtime.launch_sources == ["chat", "settings"]

    # Hotkey launch path.
    manager = hotkeys.HotkeysManager(
        is_running=lambda: True,
        get_payload_opacity=lambda: 100,
        toggle_payload_opacity=lambda: None,
        launch_controller=lambda: runtime.launch_overlay_controller(source="hotkey"),
        logger=logging.getLogger("test-launch-entrypoint-parity"),
        plugin_name="EDMCModernOverlay",
    )
    manager._launch_controller_callback()
    assert runtime.launch_sources == ["chat", "settings", "hotkey"]
