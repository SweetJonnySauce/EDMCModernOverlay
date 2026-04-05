from __future__ import annotations

import load


class _StubPrefs:
    def __init__(self):
        self.overlay_opacity = 0.75
        self.show_connection_status = True
        self.debug_overlay_corner = "SE"
        self.client_log_retention = load.DEFAULT_CLIENT_LOG_RETENTION
        self.gridlines_enabled = False
        self.gridline_spacing = 100
        self.force_render = False
        self.manual_backend_override = ""
        self.title_bar_enabled = False
        self.title_bar_height = 0
        self.show_debug_overlay = False
        self.physical_clamp_enabled = True
        self.physical_clamp_overrides = {"DisplayPort-2": 1.0}
        self.min_font_point = 6.0
        self.max_font_point = 18.0
        self.legacy_font_step = 2
        self.cycle_payload_ids = False
        self.copy_payload_id_on_cycle = False
        self.scale_mode = "fit"
        self.nudge_overflow_payloads = False
        self.payload_nudge_gutter = 30
        self.payload_log_delay_seconds = 0.25
        self.status_message_gutter = 0

    def status_bottom_margin(self) -> int:
        return int(self.status_message_gutter)

    def save(self) -> None:  # pragma: no cover - stubbed persistence
        return


class _StubGroupState:
    def __init__(self, states):
        self._states = dict(states)

    def state_snapshot(self):
        return dict(self._states)


def test_overlay_config_includes_physical_clamp_flag(monkeypatch):
    runtime = object.__new__(load._PluginRuntime)
    runtime._preferences = _StubPrefs()
    runtime._log_retention_override = None
    runtime._last_config = {}
    runtime._plugin_group_state = _StubGroupState({"BGS-Tally Objectives": False})
    runtime._platform_context_payload = lambda: {"platform": "stub"}
    runtime._load_payload_debug_config = lambda: None
    runtime._schedule_config_rebroadcasts = lambda: None

    published = []
    runtime._publish_payload = lambda payload: published.append(payload)

    runtime._send_overlay_config()

    assert published, "Overlay config payload was not published"
    payload = published[0]
    assert payload["physical_clamp_enabled"] is True
    assert runtime._last_config.get("physical_clamp_enabled") is True
    assert payload["physical_clamp_overrides"] == {"DisplayPort-2": 1.0}
    assert runtime._last_config.get("physical_clamp_overrides") == {"DisplayPort-2": 1.0}
    assert payload["legacy_font_step"] == 2
    assert payload["plugin_group_states"] == {"BGS-Tally Objectives": False}
    assert payload["plugin_group_state_default_on"] is True


def test_overlay_config_defaults_keep_clamp_off(monkeypatch):
    runtime = object.__new__(load._PluginRuntime)
    runtime._preferences = _StubPrefs()
    runtime._preferences.physical_clamp_enabled = False
    runtime._preferences.physical_clamp_overrides = {}
    runtime._log_retention_override = None
    runtime._last_config = {}
    runtime._plugin_group_state = _StubGroupState({})
    runtime._platform_context_payload = lambda: {"platform": "stub"}
    runtime._load_payload_debug_config = lambda: None
    runtime._schedule_config_rebroadcasts = lambda: None

    published = []
    runtime._publish_payload = lambda payload: published.append(payload)

    runtime._send_overlay_config()

    payload = published[0]
    assert payload["physical_clamp_enabled"] is False
    assert payload["physical_clamp_overrides"] == {}
    assert runtime._last_config.get("physical_clamp_enabled") is False
    assert runtime._last_config.get("physical_clamp_overrides") == {}


def test_platform_context_payload_includes_shadow_backend_status(monkeypatch):
    runtime = object.__new__(load._PluginRuntime)
    runtime._preferences = _StubPrefs()
    runtime._flatpak_context = {}

    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "KDE")
    monkeypatch.delenv("QT_QPA_PLATFORM", raising=False)

    context = runtime._platform_context_payload()

    assert context["session_type"] == "wayland"
    assert context["compositor"] == "kwin"
    assert context["manual_backend_override"] == ""
    shadow = context["shadow_backend_status"]
    assert shadow["shadow_mode"] is True
    assert shadow["selected_backend"] == {
        "family": "native_wayland",
        "instance": "kwin_wayland",
    }
    assert shadow["report"]["family"] == "native_wayland"
    assert shadow["report"]["instance"] == "kwin_wayland"
    assert shadow["report"]["classification"] == "true_overlay"
    assert shadow["report"]["summary"].startswith(
        "family=native_wayland instance=kwin_wayland classification=true_overlay"
    )
    assert shadow["probe"]["qt_platform_name"] == "wayland"


def test_platform_context_payload_carries_manual_backend_override(monkeypatch):
    runtime = object.__new__(load._PluginRuntime)
    runtime._preferences = _StubPrefs()
    runtime._preferences.manual_backend_override = "xwayland_compat"
    runtime._flatpak_context = {}

    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "KDE")
    monkeypatch.delenv("QT_QPA_PLATFORM", raising=False)

    context = runtime._platform_context_payload()

    assert context["manual_backend_override"] == "xwayland_compat"
    assert context["shadow_backend_status"]["manual_override"] == "xwayland_compat"
    assert context["shadow_backend_status"]["classification"] == "degraded_overlay"
    assert "fallback_reason" not in context["shadow_backend_status"]
    assert context["shadow_backend_status"]["report"]["classification"] == "degraded_overlay"
    assert context["shadow_backend_status"]["probe"]["qt_platform_name"] == "xcb"
