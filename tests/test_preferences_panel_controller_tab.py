from __future__ import annotations

import load
from overlay_plugin import preferences as prefs


class _StatusVar:
    def __init__(self) -> None:
        self.value = ""

    def set(self, value: str) -> None:
        self.value = str(value)

    def get(self) -> str:
        return self.value


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


class _FakeCombo:
    def __init__(self) -> None:
        self.values: tuple[str, ...] = ()

    def configure(self, **kwargs) -> None:
        values = kwargs.get("values")
        if isinstance(values, tuple):
            self.values = values
        elif isinstance(values, list):
            self.values = tuple(str(value) for value in values)


class _FakeLabel:
    def __init__(self) -> None:
        self.foreground = ""

    def configure(self, **kwargs) -> None:
        if "foreground" in kwargs:
            self.foreground = str(kwargs["foreground"])


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
            self.manual_backend_override_values: list[str] = []

        def launch_overlay_controller(self, *, source: load.LaunchSource = "chat") -> None:
            self.launch_sources.append(source)

        def get_version_status(self):
            return None

        def get_troubleshooting_panel_state(self):
            return load.TroubleshootingPanelState()

        def set_manual_backend_override_preference(self, value: str) -> None:
            self.manual_backend_override_values.append(value)

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
    override_callback = captured["kwargs"]["set_manual_backend_override_callback"]
    override_callback("xwayland_compat")
    assert plugin.launch_sources == ["settings"]
    assert plugin.manual_backend_override_values == ["xwayland_compat"]


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


def test_backend_status_refresh_updates_summary_and_warning() -> None:
    panel = object.__new__(prefs.PreferencesPanel)
    panel._status_var = _StatusVar()
    panel._backend_status_var = _StatusVar()
    panel._backend_warning_var = _StatusVar()
    panel._backend_warning_label = _FakeLabel()
    panel._preferences = type("_Prefs", (), {"manual_backend_override": ""})()
    panel._var_manual_backend_override = _StatusVar()
    panel._backend_override_combo = _FakeCombo()
    panel._backend_status_snapshot = {}
    panel._backend_status_callback = lambda: {
        "status": "ok",
        "backend_status": {
            "selected_backend": {"family": "xwayland_compat", "instance": "xwayland_compat"},
            "classification": "degraded_overlay",
            "fallback_from": {"family": "native_wayland", "instance": "kwin_wayland"},
            "fallback_reason": "xwayland_compat_only",
            "shadow_mode": True,
            "helper_states": [],
            "review_required": False,
            "review_reasons": [],
        },
    }

    changed = panel._maybe_refresh_backend_status_from_callback(silent=True)

    assert changed is True
    assert panel._backend_status_var.value == (
        "Backend: XWayland compatibility | Mode: Degraded overlay | Source: Plugin hint"
    )
    assert panel._backend_warning_var.value == (
        "Warning: Some overlay guarantees are reduced in this mode.; "
        "Using XWayland compatibility mode because a native Wayland path is not active."
    )
    assert panel._backend_warning_label.foreground == prefs.BACKEND_NOTICE_WARNING_COLOR
    assert panel._backend_override_combo.values == ("auto", "xwayland_compat")


def test_backend_status_refresh_prefers_client_runtime_source() -> None:
    panel = object.__new__(prefs.PreferencesPanel)
    panel._status_var = _StatusVar()
    panel._backend_status_var = _StatusVar()
    panel._backend_warning_var = _StatusVar()
    panel._backend_warning_label = _FakeLabel()
    panel._preferences = type("_Prefs", (), {"manual_backend_override": ""})()
    panel._var_manual_backend_override = _StatusVar()
    panel._backend_override_combo = _FakeCombo()
    panel._backend_status_snapshot = {}
    panel._backend_status_callback = lambda: {
        "status": "ok",
        "backend_status": {
            "selected_backend": {"family": "native_wayland", "instance": "kwin_wayland"},
            "classification": "true_overlay",
            "shadow_mode": False,
            "helper_states": [],
            "review_required": False,
            "review_reasons": [],
        },
    }

    changed = panel._maybe_refresh_backend_status_from_callback(silent=True)

    assert changed is True
    assert panel._backend_status_var.value == (
        "Backend: KWin Wayland | Mode: True overlay | Source: Live runtime"
    )
    assert panel._backend_warning_var.value == ""
    assert panel._backend_warning_label.foreground == prefs.BACKEND_NOTICE_WARNING_COLOR


def test_backend_status_refresh_shows_manual_override_as_info() -> None:
    panel = object.__new__(prefs.PreferencesPanel)
    panel._status_var = _StatusVar()
    panel._backend_status_var = _StatusVar()
    panel._backend_warning_var = _StatusVar()
    panel._backend_warning_label = _FakeLabel()
    panel._preferences = type("_Prefs", (), {"manual_backend_override": "native_x11"})()
    panel._var_manual_backend_override = _StatusVar()
    panel._backend_override_combo = _FakeCombo()
    panel._backend_status_snapshot = {}
    panel._backend_status_callback = lambda: {
        "status": "ok",
        "backend_status": {
            "selected_backend": {"family": "native_x11", "instance": "native_x11"},
            "classification": "true_overlay",
            "manual_override": "native_x11",
            "shadow_mode": False,
            "helper_states": [],
            "review_required": False,
            "review_reasons": [],
            "probe": {"operating_system": "linux", "session_type": "x11", "compositor": "none"},
        },
    }

    changed = panel._maybe_refresh_backend_status_from_callback(silent=True)

    assert changed is True
    assert panel._backend_warning_var.value == (
        "Info: Overlay backend is set to Native X11.; "
        "Set Overlay backend to Auto if you want the overlay to choose automatically."
    )
    assert panel._backend_warning_label.foreground == prefs.BACKEND_NOTICE_INFO_COLOR


def test_apply_manual_backend_override_persists_and_calls_callback() -> None:
    panel = object.__new__(prefs.PreferencesPanel)
    panel._status_var = _StatusVar()
    panel._preferences = type(
        "_Prefs",
        (),
        {
            "manual_backend_override": "",
            "save": lambda self: None,
        },
    )()
    panel._var_manual_backend_override = _StatusVar()
    panel._var_manual_backend_override.set("xwayland_compat")
    panel._backend_override_apply_in_progress = False
    applied: list[str] = []
    panel._set_manual_backend_override = lambda value: applied.append(value)

    panel._apply_manual_backend_override()

    assert panel._preferences.manual_backend_override == "xwayland_compat"
    assert applied == ["xwayland_compat"]
    assert (
        panel._status_var.value
        == "Overlay backend saved. Restart Overlay Client to apply. Current runtime backend remains unchanged until restart."
    )


def test_apply_manual_backend_override_clears_auto_value() -> None:
    panel = object.__new__(prefs.PreferencesPanel)
    panel._status_var = _StatusVar()
    panel._preferences = type(
        "_Prefs",
        (),
        {
            "manual_backend_override": "xwayland_compat",
            "save": lambda self: None,
        },
    )()
    panel._var_manual_backend_override = _StatusVar()
    panel._var_manual_backend_override.set("auto")
    panel._backend_override_apply_in_progress = False
    applied: list[str] = []
    panel._set_manual_backend_override = lambda value: applied.append(value)

    panel._apply_manual_backend_override()

    assert panel._preferences.manual_backend_override == ""
    assert applied == [""]
    assert (
        panel._status_var.value
        == "Overlay backend saved. Restart Overlay Client to apply. Current runtime backend remains unchanged until restart."
    )


def test_profile_state_monitor_starts_with_backend_status_callback_only() -> None:
    panel = object.__new__(prefs.PreferencesPanel)
    panel._frame = _FakeFrame()
    panel._status_var = _StatusVar()
    panel._profile_status_callback = None
    panel._backend_status_callback = lambda: {"status": "ok", "backend_status": {}}
    panel._profile_poll_interval_ms = 555
    panel._profile_poll_after_id = None
    panel._profile_table_editor = None

    panel._start_profile_state_monitor()

    assert panel._profile_poll_after_id == "after-1"
    assert panel._frame.after_calls[-1][0] == 555
