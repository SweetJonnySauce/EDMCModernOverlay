from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pytest

import load
from tests.harness_bootstrap import create_harness, stop_plugin_runtime
from tests.overlay_adapter import OverlayCaptureAdapter

pytestmark = pytest.mark.harness


@pytest.fixture
def harness_runtime(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[tuple[object, object, OverlayCaptureAdapter]]:
    def _start_lightweight(self: object) -> str:
        self._running = True
        return load.PLUGIN_NAME

    def _stop_lightweight(self: object) -> None:
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


def test_harness_bootstrap_startup_smoke(harness_runtime: tuple[object, object, OverlayCaptureAdapter]) -> None:
    harness, runtime, _adapter = harness_runtime
    assert getattr(load, "_plugin", None) is runtime
    assert getattr(harness, "journal_handlers", [])
    assert callable(getattr(runtime, "handle_journal", None))


def test_harness_adapter_captures_overlay_message(harness_runtime: tuple[object, object, OverlayCaptureAdapter]) -> None:
    _harness, runtime, adapter = harness_runtime

    runtime.send_test_message("Harness adapter smoke", x=120, y=160)

    assert adapter.messages
    assert adapter.messages[-1]["text"] == "Harness adapter smoke"
    assert adapter.messages[-1]["x"] == 120
    assert adapter.messages[-1]["y"] == 160
