from __future__ import annotations

import os
import shutil
import time
from pathlib import Path
from typing import Any, Iterator

import pytest

import load
from overlay_plugin.profile_state import OverlayProfileStore
from tests.harness_bootstrap import create_harness, stop_plugin_runtime

pytestmark = pytest.mark.harness

PROFILE_LIFECYCLE_PAUSE_SECONDS = max(0.0, float(os.environ.get("HARNESS_PROFILE_LIFECYCLE_PAUSE_SECONDS", "3")))


class _GroupStateStub:
    def sync_profiles(self, *, profiles: list[str], current_profile: str) -> None:
        return

    def create_profile(self, profile_name: str) -> None:
        return

    def rename_profile(self, old_name: str, new_name: str) -> None:
        return

    def delete_profile(self, profile_name: str) -> None:
        return


class _ControlsStub:
    def state_snapshot(self) -> dict[str, bool]:
        return {}


@pytest.fixture
def harness_runtime(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[tuple[object, Any, Path]]:
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

    config_dir = Path(__file__).parent / "config"
    config_user_path = config_dir / "overlay_groupings.user.json"
    root_user_path = Path(__file__).resolve().parents[1] / "overlay_groupings.user.json"
    if not config_user_path.exists() and root_user_path.exists():
        shutil.copy(root_user_path, config_user_path)

    original_bytes = config_user_path.read_bytes() if config_user_path.exists() else None

    runtime._groupings_user_path = config_user_path
    runtime._profile_store = OverlayProfileStore(user_path=config_user_path, logger=load.LOGGER)
    runtime._plugin_group_state = _GroupStateStub()
    runtime._plugin_group_controls = _ControlsStub()
    runtime._publish_payload = lambda payload: None
    runtime._send_overlay_config = lambda *args, **kwargs: None

    try:
        yield harness, runtime, config_user_path
    finally:
        if original_bytes is None:
            try:
                config_user_path.unlink()
            except FileNotFoundError:
                pass
        else:
            config_user_path.write_bytes(original_bytes)
        stop_plugin_runtime()


def _status_profiles(status: dict[str, Any]) -> list[str]:
    raw_profiles = status.get("profiles")
    if not isinstance(raw_profiles, list):
        return []
    return [str(item) for item in raw_profiles]


def _pause_after_mutation(step: str) -> None:
    if PROFILE_LIFECYCLE_PAUSE_SECONDS <= 0:
        return
    time.sleep(PROFILE_LIFECYCLE_PAUSE_SECONDS)


def _fire_dashboard_entry(harness: object, entry: dict[str, Any]) -> None:
    load.dashboard_entry(
        cmdr=str(getattr(harness, "commander", "TestHarnessCmdr")),
        is_beta=bool(getattr(harness, "is_beta", False)),
        entry=entry,
    )


def test_profile_lifecycle_round_trip_uses_config_fixture_store(
    harness_runtime: tuple[object, Any, Path]
) -> None:
    harness, runtime, config_user_path = harness_runtime

    create_name = "Harness Lifecycle Create"
    renamed_name = "Harness Lifecycle Renamed"
    ship_id = 93

    initial_status = runtime.get_profile_status()
    initial_profiles = _status_profiles(initial_status)
    for candidate in (create_name, renamed_name):
        if candidate in initial_profiles:
            runtime.delete_profile(candidate)

    harness.play_sequence("profile_ship_seed")
    harness.play_sequence("profile_shipyard_swap_seed")
    seeded_status = runtime.get_profile_status()
    ships = seeded_status.get("ships")
    assert isinstance(ships, list)
    assert any(int(item.get("ship_id", 0)) == ship_id for item in ships if isinstance(item, dict))

    created = runtime.create_profile(create_name)
    _pause_after_mutation("create")
    created_profiles = _status_profiles(created)
    assert create_name in created_profiles
    assert config_user_path.exists()

    renamed = runtime.rename_profile(create_name, renamed_name)
    _pause_after_mutation("rename")
    renamed_profiles = _status_profiles(renamed)
    assert renamed_name in renamed_profiles
    assert create_name not in renamed_profiles

    moved = runtime.reorder_profile(renamed_name, 0)
    _pause_after_mutation("reorder")
    moved_profiles = _status_profiles(moved)
    assert moved_profiles
    assert moved_profiles[0] == renamed_name

    ruled = runtime.set_profile_rules(renamed_name, [{"context": "InMainShip", "ship_id": ship_id}])
    _pause_after_mutation("set_rules")
    rules = ruled.get("rules")
    assert isinstance(rules, dict)
    assert rules.get(renamed_name) == [{"context": "InMainShip", "ship_id": ship_id}]

    runtime.set_current_profile("Default", source="manual")
    _pause_after_mutation("set_current_default")
    assert runtime.get_profile_status()["current_profile"] == "Default"

    _fire_dashboard_entry(
        harness,
        {
            "Flags": int(load._FLAG_IN_MAIN_SHIP),
            "ShipID": ship_id,
        },
    )
    _pause_after_mutation("auto_select_by_ship")
    assert runtime.get_profile_status()["current_profile"] == renamed_name

    deleted = runtime.delete_profile(renamed_name)
    _pause_after_mutation("delete")
    deleted_profiles = _status_profiles(deleted)
    assert renamed_name not in deleted_profiles

    persisted_status = OverlayProfileStore(user_path=config_user_path, logger=load.LOGGER).status()
    persisted_profiles = _status_profiles(persisted_status)
    assert renamed_name not in persisted_profiles


def test_profile_lifecycle_can_set_created_profile_active(
    harness_runtime: tuple[object, Any, Path]
) -> None:
    _harness, runtime, config_user_path = harness_runtime

    profile_name = "Harness Lifecycle Active"
    baseline = runtime.get_profile_status()
    baseline_profiles = _status_profiles(baseline)
    if profile_name in baseline_profiles:
        runtime.delete_profile(profile_name)

    created = runtime.create_profile(profile_name)
    _pause_after_mutation("create_for_active")
    assert profile_name in _status_profiles(created)

    activated = runtime.set_current_profile(profile_name, source="manual")
    _pause_after_mutation("set_created_active")
    assert str(activated.get("current_profile")) == profile_name
    assert str(activated.get("manual_profile")) == profile_name

    persisted_active = OverlayProfileStore(user_path=config_user_path, logger=load.LOGGER).status()
    assert str(persisted_active.get("current_profile")) == profile_name
    assert str(persisted_active.get("manual_profile")) == profile_name

    deleted = runtime.delete_profile(profile_name)
    _pause_after_mutation("delete_after_active")
    assert profile_name not in _status_profiles(deleted)
