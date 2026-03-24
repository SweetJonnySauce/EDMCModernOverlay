from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

import pytest

import load
from overlay_plugin.profile_state import OverlayProfileStore
from tests.harness_bootstrap import create_harness, stop_plugin_runtime

pytestmark = pytest.mark.harness


@pytest.fixture
def harness_runtime(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[tuple[object, Any, list[dict[str, Any]]]]:
    def _start_lightweight(self: Any) -> str:
        self._running = True
        return load.PLUGIN_NAME

    def _stop_lightweight(self: Any) -> None:
        self._running = False

    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(load._PluginRuntime, "start", _start_lightweight)
    monkeypatch.setattr(load._PluginRuntime, "stop", _stop_lightweight)
    monkeypatch.setattr(load._PluginRuntime, "_resolve_payload_logs_dir", lambda _self: log_dir)

    harness = create_harness(register_journal=True)
    runtime = load._plugin
    assert runtime is not None

    profile_store_path = tmp_path / "overlay_groupings.user.json"
    runtime._profile_store = OverlayProfileStore(user_path=profile_store_path, logger=load.LOGGER)

    class _GroupStateStub:
        def sync_profiles(self, *, profiles: list[str], current_profile: str) -> None:
            return

    class _ControlsStub:
        def state_snapshot(self) -> dict[str, bool]:
            return {}

    runtime._plugin_group_state = _GroupStateStub()
    runtime._plugin_group_controls = _ControlsStub()

    published: list[dict[str, Any]] = []
    runtime._publish_payload = lambda payload: published.append(dict(payload))
    runtime._send_overlay_config = lambda: None

    try:
        yield harness, runtime, published
    finally:
        stop_plugin_runtime()


def _fire_dashboard_entry(harness: object, entry: dict[str, Any]) -> None:
    load.dashboard_entry(
        cmdr=str(getattr(harness, "commander", "TestHarnessCmdr")),
        is_beta=bool(getattr(harness, "is_beta", False)),
        entry=entry,
    )


def test_dashboard_onfoot_rule_switches_profile(harness_runtime: tuple[object, Any, list[dict[str, Any]]]) -> None:
    harness, runtime, published = harness_runtime
    profile_name = "On Foot"
    runtime.create_profile(profile_name)
    runtime.set_profile_rules(profile_name, [{"context": "OnFoot"}])
    runtime.set_current_profile("Default", source="manual")

    _fire_dashboard_entry(
        harness,
        {
            "Flags2": int(load._FLAG2_ON_FOOT),
            "ShipID": 9,
        },
    )

    status = runtime.get_profile_status()
    assert status["current_profile"] == profile_name
    assert runtime._profile_active_contexts == {"OnFoot"}
    assert runtime._profile_ship_id == 9
    assert runtime._profile_dashboard_ready is True
    assert any(
        payload.get("event") == "OverlayProfileChanged"
        and payload.get("source") == "auto_rule"
        and payload.get("current_profile") == profile_name
        for payload in published
    )


def test_dashboard_profile_rules_are_transition_only(harness_runtime: tuple[object, Any, list[dict[str, Any]]]) -> None:
    harness, runtime, _published = harness_runtime
    profile_name = "On Foot"
    runtime.create_profile(profile_name)
    runtime.set_profile_rules(profile_name, [{"context": "OnFoot"}])
    runtime.set_current_profile("Default", source="manual")

    calls: list[tuple[str, str]] = []
    original_set_current_profile = runtime.set_current_profile

    def _tracking_set_current_profile(profile_name: str, *, source: str = "manual") -> dict[str, Any]:
        calls.append((str(profile_name), str(source)))
        return original_set_current_profile(profile_name, source=source)

    runtime.set_current_profile = _tracking_set_current_profile

    onfoot_entry = {"Flags2": int(load._FLAG2_ON_FOOT), "ShipID": 12}
    _fire_dashboard_entry(harness, onfoot_entry)
    _fire_dashboard_entry(harness, onfoot_entry)

    auto_calls = [call for call in calls if call[1] == "auto_rule"]
    assert auto_calls == [(profile_name, "auto_rule")]


def test_dashboard_ship_specific_main_ship_rule(harness_runtime: tuple[object, Any, list[dict[str, Any]]]) -> None:
    harness, runtime, _published = harness_runtime
    runtime.create_profile("Cargo")
    runtime.set_profile_rules("Cargo", [{"context": "InMainShip", "ship_id": 42}])
    runtime.set_current_profile("Default", source="manual")

    _fire_dashboard_entry(
        harness,
        {
            "Flags": int(load._FLAG_IN_MAIN_SHIP),
            "ShipID": 99,
        },
    )
    assert runtime.get_profile_status()["current_profile"] == "Default"

    _fire_dashboard_entry(
        harness,
        {
            "Flags": int(load._FLAG_IN_MAIN_SHIP),
            "ShipID": 42,
        },
    )
    assert runtime.get_profile_status()["current_profile"] == "Cargo"


def test_dashboard_falls_back_to_default_when_custom_rule_no_longer_matches(
    harness_runtime: tuple[object, Any, list[dict[str, Any]]]
) -> None:
    harness, runtime, _published = harness_runtime
    profile_name = "On Foot"
    runtime.create_profile(profile_name)
    runtime.set_profile_rules(profile_name, [{"context": "OnFoot"}])
    runtime.set_current_profile("Default", source="manual")

    _fire_dashboard_entry(harness, {"Flags2": int(load._FLAG2_ON_FOOT), "ShipID": 7})
    assert runtime.get_profile_status()["current_profile"] == profile_name

    _fire_dashboard_entry(harness, {"Flags": int(load._FLAG_IN_MAIN_SHIP), "ShipID": 7})
    assert runtime.get_profile_status()["current_profile"] == "Default"
