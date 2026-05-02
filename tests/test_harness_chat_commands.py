from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

import pytest

import load
from tests.harness_bootstrap import create_harness, stop_plugin_runtime
from tests.overlay_adapter import OverlayCaptureAdapter

pytestmark = pytest.mark.harness


@pytest.fixture
def harness_runtime(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[tuple[object, Any, OverlayCaptureAdapter]]:
    def _start_lightweight(self: Any) -> str:
        self._running = True
        return load.PLUGIN_NAME

    def _stop_lightweight(self: Any) -> None:
        self._running = False

    adapter = OverlayCaptureAdapter()
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(load._PluginRuntime, "start", _start_lightweight)
    monkeypatch.setattr(load._PluginRuntime, "stop", _stop_lightweight)
    monkeypatch.setattr(load._PluginRuntime, "_resolve_payload_logs_dir", lambda _self: log_dir)
    monkeypatch.setattr(load, "send_overlay_message", adapter.send_overlay_payload)

    harness = create_harness(register_journal=True)
    runtime = load._plugin
    assert runtime is not None
    try:
        yield harness, runtime, adapter
    finally:
        stop_plugin_runtime()


def test_chat_commands_replay_through_harness(harness_runtime: tuple[object, Any, OverlayCaptureAdapter]) -> None:
    harness, runtime, adapter = harness_runtime

    launch_calls: list[str] = []
    group_set_calls: list[tuple[bool, tuple[str, ...] | None, str]] = []
    group_toggle_calls: list[tuple[tuple[str, ...] | None, str]] = []
    group_status_calls: list[str] = []
    status_overlay_calls: list[tuple[str, ...]] = []
    profile_cycle_calls: list[tuple[int, str]] = []
    profile_status_calls: list[str] = []
    handled: dict[str, bool] = {}

    def launch_overlay_controller() -> None:
        launch_calls.append("launch")

    def set_groups(enabled: bool, *, group_names: list[str] | None = None, source: str = "runtime") -> dict[str, object]:
        targets = tuple(group_names) if group_names is not None else None
        group_set_calls.append((bool(enabled), targets, str(source)))
        return {"changed": True}

    def toggle_groups(*, group_names: list[str] | None = None, source: str = "runtime") -> dict[str, object]:
        targets = tuple(group_names) if group_names is not None else None
        group_toggle_calls.append((targets, str(source)))
        return {"changed": True}

    def group_status_lines() -> list[str]:
        group_status_calls.append("status")
        return ["BGS-Tally Objectives: On", "Diagnostics: Off"]

    def send_group_status_overlay(lines: list[str]) -> None:
        status_overlay_calls.append(tuple(lines))

    def cycle_profile(direction: int, *, source: str = "manual") -> dict[str, object]:
        profile_cycle_calls.append((int(direction), str(source)))
        return {"current_profile": "Default", "profiles": ["Default", "Mining"]}

    def get_profile_status() -> dict[str, object]:
        profile_status_calls.append("profiles")
        return {"current_profile": "Default", "profiles": ["Default", "Mining"]}

    runtime.launch_overlay_controller = launch_overlay_controller
    runtime._set_plugin_groups_enabled = set_groups
    runtime._toggle_plugin_groups_enabled = toggle_groups
    runtime.get_plugin_group_status_lines = group_status_lines
    runtime.send_group_status_overlay = send_group_status_overlay
    runtime.cycle_profile = cycle_profile
    runtime.get_profile_status = get_profile_status

    prefix = runtime._command_helper_prefix or getattr(runtime._preferences, "controller_launch_command", "!ovr")
    runtime._command_helper = runtime._build_command_helper(prefix, previous_prefix=prefix)
    original_handle_entry = runtime._command_helper.handle_entry

    def tracking_handle_entry(entry: dict[str, object]) -> bool:
        result = bool(original_handle_entry(entry))
        message = entry.get("Message")
        if isinstance(message, str):
            handled[message] = result
        return result

    runtime._command_helper.handle_entry = tracking_handle_entry

    for sequence in ("chat_launch", "chat_help", "chat_toggle", "chat_group_actions", "chat_profiles"):
        harness.play_sequence(sequence)

    assert launch_calls
    assert (None, "chat_toggle") in group_toggle_calls
    assert (True, ("BGS-Tally Objectives",), "chat_on") in group_set_calls
    assert (False, ("BGS-Tally Objectives",), "chat_off") in group_set_calls
    assert (("BGS-Tally Objectives",), "chat_toggle") in group_toggle_calls
    assert group_status_calls
    assert status_overlay_calls
    assert (1, "chat") in profile_cycle_calls
    assert (-1, "chat") in profile_cycle_calls
    assert profile_status_calls

    # Fallback assertion requirement for non-callback path (`help`).
    assert handled.get("!ovr help") is True

    # Adapter path assertion ensures overlay messaging was exercised.
    assert adapter.raw_payloads
