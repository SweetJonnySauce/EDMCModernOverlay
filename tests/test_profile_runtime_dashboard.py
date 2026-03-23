from __future__ import annotations

import load
from overlay_plugin.command_overlay_groups import COMMAND_PROFILE_STATUS_ID_PREFIX
from overlay_plugin.profile_runtime import (
    PROFILE_STATUS_MESSAGE_COLOR,
    PROFILE_STATUS_MESSAGE_SIZE,
    PROFILE_STATUS_MESSAGE_X,
    PROFILE_STATUS_MESSAGE_Y,
)


class _StaticMatchStore:
    def __init__(self, value: str | None) -> None:
        self.value = value

    def match_profile(self, *, active_contexts, ship_id):
        return self.value


class _MutableStatusStore:
    def __init__(self) -> None:
        self._status = {
            "profiles": ["PvE", "Default"],
            "current_profile": "Default",
            "manual_profile": "Default",
            "rules": {"Default": [], "PvE": []},
            "ships": [],
            "fleet_updated_at": "",
        }

    def status(self):
        return dict(self._status)

    def set_current_profile(self, profile_name: str, *, source: str = "manual"):
        self._status["current_profile"] = str(profile_name)
        if str(source or "").casefold() in {"manual", "settings", "hotkey", "chat", "controller"}:
            self._status["manual_profile"] = str(profile_name)
        return dict(self._status)


def test_decode_dashboard_contexts_supports_all_rule_tokens() -> None:
    entry = {
        "Flags": int(load._FLAG_IN_MAIN_SHIP | load._FLAG_IN_SRV | load._FLAG_IN_FIGHTER | load._FLAG_IN_WING),
        "Flags2": int(load._FLAG2_ON_FOOT | load._FLAG2_IN_TAXI | load._FLAG2_IN_MULTICREW),
    }

    contexts = load._PluginRuntime._decode_dashboard_contexts(entry)

    assert contexts == {
        "InMainShip",
        "InSRV",
        "InFighter",
        "OnFoot",
        "InWing",
        "InTaxi",
        "InMulticrew",
    }


def test_handle_dashboard_entry_updates_runtime_snapshot_and_triggers_rules() -> None:
    runtime = object.__new__(load._PluginRuntime)
    runtime._profile_active_contexts = set()
    runtime._profile_ship_id = None
    runtime._profile_dashboard_ready = False
    triggered: list[str] = []
    runtime._apply_profile_runtime_rules = lambda: triggered.append("run")

    load._PluginRuntime.handle_dashboard_entry(
        runtime,
        {
            "Flags": int(load._FLAG_IN_MAIN_SHIP),
            "Flags2": int(load._FLAG2_IN_TAXI),
            "ShipID": 42,
        },
    )

    assert runtime._profile_active_contexts == {"InMainShip", "InTaxi"}
    assert runtime._profile_ship_id == 42
    assert runtime._profile_dashboard_ready is True
    assert triggered == ["run"]


def test_profile_runtime_rules_switch_only_on_transition() -> None:
    runtime = object.__new__(load._PluginRuntime)
    runtime._profile_store = _StaticMatchStore("Mining")
    runtime._profile_dashboard_ready = True
    runtime._profile_active_contexts = {"OnFoot"}
    runtime._profile_ship_id = 77
    runtime._profile_last_matched_profile = None

    switch_calls: list[tuple[str, str]] = []

    def _set_current_profile(name: str, *, source: str = "manual"):
        switch_calls.append((name, source))
        return {"current_profile": name}

    runtime.set_current_profile = _set_current_profile
    runtime.get_profile_status = lambda: {"current_profile": "Default"}

    load._PluginRuntime._apply_profile_runtime_rules(runtime)
    runtime.get_profile_status = lambda: {"current_profile": "Mining"}
    load._PluginRuntime._apply_profile_runtime_rules(runtime)

    assert switch_calls == [("Mining", "auto_rule")]


def test_set_current_profile_syncs_plugin_group_state_to_active_profile() -> None:
    runtime = object.__new__(load._PluginRuntime)
    runtime._profile_store = _MutableStatusStore()
    sync_calls: list[dict[str, object]] = []

    class _StubGroupState:
        def sync_profiles(self, *, profiles, current_profile):
            sync_calls.append({"profiles": list(profiles), "current_profile": current_profile})

    runtime._plugin_group_state = _StubGroupState()
    emitted: list[str] = []
    runtime._emit_profile_change_event = lambda *, source, matched_profile=None: emitted.append(source)

    status = load._PluginRuntime.set_current_profile(runtime, "PvE", source="manual")

    assert status["current_profile"] == "PvE"
    assert sync_calls
    assert sync_calls[-1]["profiles"] == ["PvE", "Default"]
    assert sync_calls[-1]["current_profile"] == "PvE"
    assert emitted == ["manual"]


def test_set_current_profile_clears_groups_that_turn_off_after_profile_switch() -> None:
    runtime = object.__new__(load._PluginRuntime)
    runtime._profile_store = _MutableStatusStore()
    emitted: list[str] = []
    runtime._emit_profile_change_event = lambda *, source, matched_profile=None: emitted.append(source)

    class _StubGroupState:
        def __init__(self) -> None:
            self.current_profile = "Default"
            self.by_profile = {
                "Default": {"Alpha": True},
                "PvE": {"Alpha": False},
            }

        def sync_profiles(self, *, profiles, current_profile):
            self.current_profile = str(current_profile)

        def state_snapshot(self):
            return dict(self.by_profile.get(self.current_profile, {}))

    group_state = _StubGroupState()
    runtime._plugin_group_state = group_state

    class _StubControls:
        def __init__(self, state) -> None:
            self._state = state

        def state_snapshot(self):
            return self._state.state_snapshot()

    runtime._plugin_group_controls = _StubControls(group_state)
    cleared: list[tuple[list[str], str]] = []
    runtime._publish_group_clear_event = lambda group_names, source: cleared.append((list(group_names), str(source)))

    status = load._PluginRuntime.set_current_profile(runtime, "PvE", source="manual")
    assert status["current_profile"] == "PvE"
    assert cleared == [(["Alpha"], "profile_switch:manual")]
    assert emitted == ["manual"]


def test_emit_profile_change_event_publishes_profile_status_overlay_message() -> None:
    runtime = object.__new__(load._PluginRuntime)
    runtime._profile_active_contexts = {"OnFoot"}
    runtime._profile_ship_id = 12
    published: list[dict[str, object]] = []
    runtime.get_profile_status = lambda: {"current_profile": "On Foot", "manual_profile": "Default"}
    runtime._publish_payload = lambda payload: published.append(dict(payload))
    sent_config: list[str] = []
    runtime._send_overlay_config = lambda: sent_config.append("sent")

    load._PluginRuntime._emit_profile_change_event(runtime, source="manual")

    message_payloads = [p for p in published if p.get("event") == "LegacyOverlay" and p.get("type") == "message"]
    assert message_payloads
    assert any(str(payload.get("id", "")).startswith(COMMAND_PROFILE_STATUS_ID_PREFIX) for payload in message_payloads)
    assert any(payload.get("text") == "Active Profile: On Foot" for payload in message_payloads)
    assert any(payload.get("color") == PROFILE_STATUS_MESSAGE_COLOR for payload in message_payloads)
    assert any(payload.get("size") == PROFILE_STATUS_MESSAGE_SIZE for payload in message_payloads)
    assert any(payload.get("x") == PROFILE_STATUS_MESSAGE_X for payload in message_payloads)
    assert any(payload.get("y") == PROFILE_STATUS_MESSAGE_Y for payload in message_payloads)
    assert sent_config == ["sent"]
