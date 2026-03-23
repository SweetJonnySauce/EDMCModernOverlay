from __future__ import annotations

import load
from overlay_plugin import preferences as prefs


def test_preferences_tab_order_contract() -> None:
    assert prefs._preferences_tab_order() == ("Overlay", "Controller", "Profiles", "Experimental")


def test_controller_tab_control_order_contract() -> None:
    assert prefs._controller_tab_control_order() == (
        "launch_controller",
        "launch_command",
        "toggle_argument",
    )


def test_launch_controller_handler_delegates_to_callback() -> None:
    panel = object.__new__(prefs.PreferencesPanel)
    called: list[str] = []

    def _callback() -> None:
        called.append("launch")

    panel._launch_controller = _callback

    panel._on_launch_controller()

    assert called == ["launch"]


def test_launch_controller_handler_swallow_exceptions() -> None:
    panel = object.__new__(prefs.PreferencesPanel)

    def _boom() -> None:
        raise RuntimeError("boom")

    panel._launch_controller = _boom

    panel._on_launch_controller()


def test_plugin_prefs_wires_launch_controller_callback(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class _DummyPrefs:
        controller_launch_command = "!ovr"
        dev_mode = False

    class _DummyPlugin:
        _payload_logging_enabled = False

        def __init__(self) -> None:
            self.launch_sources: list[str] = []

        def launch_overlay_controller(self, *, source: load.LaunchSource = "chat") -> None:
            self.launch_sources.append(source)

        def get_version_status(self):
            return None

        def get_troubleshooting_panel_state(self):
            return load.TroubleshootingPanelState()

        def __getattr__(self, _name: str):
            return lambda *args, **kwargs: None

    class _FakePanel:
        def __init__(self, *args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs
            self.frame = object()

    plugin = _DummyPlugin()

    monkeypatch.setattr(load, "_prefs_panel", None)
    monkeypatch.setattr(load, "_preferences", _DummyPrefs())
    monkeypatch.setattr(load, "_plugin", plugin)
    monkeypatch.setattr(load, "PreferencesPanel", _FakePanel)

    frame = load.plugin_prefs(parent=None, cmdr="CMDR", is_beta=False)

    assert frame is load._prefs_panel.frame
    launch_callback = captured["kwargs"]["launch_controller_callback"]
    launch_callback()
    assert plugin.launch_sources == ["settings"]
