from __future__ import annotations

import load
from overlay_plugin import preferences as prefs


class _StatusVar:
    def __init__(self) -> None:
        self.value = ""

    def set(self, value: str) -> None:
        self.value = str(value)


class _FakeFrame:
    def __init__(self) -> None:
        self.after_calls: list[tuple[int, object]] = []
        self.cancelled: list[object] = []
        self._next_id = 0
        self._exists = True

    def winfo_exists(self) -> bool:
        return self._exists

    def after(self, delay_ms: int, callback):
        self._next_id += 1
        token = f"after-{self._next_id}"
        self.after_calls.append((int(delay_ms), callback))
        return token

    def after_cancel(self, token: object) -> None:
        self.cancelled.append(token)

    def bind(self, *_args, **_kwargs):
        return "bind-id"


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


def test_profile_status_refresh_only_syncs_on_change() -> None:
    panel = object.__new__(prefs.PreferencesPanel)
    panel._status_var = _StatusVar()
    panel._profile_table = None
    panel._profile_state_snapshot = {
        "profiles": ["PvE", "Default"],
        "current_profile": "PvE",
        "manual_profile": "PvE",
        "rules": {"PvE": [], "Default": []},
        "ships": [],
        "fleet_updated_at": "",
    }
    sync_calls: list[str] = []
    panel._sync_profile_widgets = lambda: sync_calls.append("sync")
    panel._profile_status_callback = lambda: {
        "profiles": ["PvE", "Default"],
        "current_profile": "PvE",
        "manual_profile": "PvE",
        "rules": {"PvE": [], "Default": []},
        "ships": [],
        "fleet_updated_at": "",
    }

    changed = panel._maybe_refresh_profile_state_from_callback(silent=True)

    assert changed is False
    assert sync_calls == []

    panel._profile_status_callback = lambda: {
        "profiles": ["PvE", "Default"],
        "current_profile": "Default",
        "manual_profile": "PvE",
        "rules": {"PvE": [], "Default": []},
        "ships": [],
        "fleet_updated_at": "",
    }
    changed = panel._maybe_refresh_profile_state_from_callback(silent=True)

    assert changed is True
    assert sync_calls == []


def test_profile_status_silent_refresh_updates_table_only_not_rule_widgets() -> None:
    panel = object.__new__(prefs.PreferencesPanel)
    panel._status_var = _StatusVar()
    panel._profile_state_snapshot = {}
    panel._profile_status_callback = lambda: {
        "profiles": ["PvE", "Default"],
        "current_profile": "PvE",
        "manual_profile": "PvE",
        "rules": {"PvE": [], "Default": []},
        "ships": [],
        "fleet_updated_at": "",
    }
    panel._sync_profile_widgets = lambda: (_ for _ in ()).throw(AssertionError("full sync should not run"))
    table_sync_calls: list[object] = []
    panel._sync_profile_table_from_status = lambda status: table_sync_calls.append(status)

    changed = panel._maybe_refresh_profile_state_from_callback(silent=True)

    assert changed is True
    assert len(table_sync_calls) == 1


def test_profile_state_monitor_poll_skips_refresh_while_inline_edit_active() -> None:
    panel = object.__new__(prefs.PreferencesPanel)
    panel._frame = _FakeFrame()
    panel._status_var = _StatusVar()
    panel._profile_poll_interval_ms = 321
    panel._profile_poll_after_id = "after-existing"
    panel._profile_table_editor = object()
    panel._profile_status_callback = lambda: {
        "profiles": ["PvE", "Default"],
        "current_profile": "PvE",
        "manual_profile": "PvE",
        "rules": {"PvE": [], "Default": []},
        "ships": [],
        "fleet_updated_at": "",
    }
    panel._profile_state_snapshot = {}
    sync_calls: list[str] = []
    panel._sync_profile_widgets = lambda: sync_calls.append("sync")

    panel._poll_profile_state_monitor()

    assert sync_calls == []
    assert panel._frame.after_calls
    assert panel._frame.after_calls[-1][0] == 321


def test_profile_state_monitor_start_and_stop_manage_after_id() -> None:
    panel = object.__new__(prefs.PreferencesPanel)
    panel._frame = _FakeFrame()
    panel._status_var = _StatusVar()
    panel._profile_status_callback = lambda: {}
    panel._profile_poll_interval_ms = 777
    panel._profile_poll_after_id = None
    panel._profile_table_editor = None
    panel._profile_state_snapshot = {}
    panel._sync_profile_widgets = lambda: None

    panel._start_profile_state_monitor()

    assert panel._profile_poll_after_id == "after-1"
    assert panel._frame.after_calls[-1][0] == 777

    panel._stop_profile_state_monitor()

    assert panel._profile_poll_after_id is None
    assert panel._frame.cancelled == ["after-1"]
