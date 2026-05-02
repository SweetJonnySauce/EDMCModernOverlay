from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

import pytest

import load
from tests.harness_bootstrap import create_harness, stop_plugin_runtime
from tests.overlay_adapter import OverlayCaptureAdapter
from tests.payload_log_fixtures import load_payloads_from_log, sample_payload_logs

pytestmark = pytest.mark.harness


@pytest.fixture
def harness_runtime(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[tuple[Any, Any, OverlayCaptureAdapter]]:
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

    try:
        harness = create_harness(register_journal=True)
    except RuntimeError as exc:
        if "semantic_version" in str(exc):
            pytest.skip(str(exc))
        raise
    runtime = load._plugin
    assert runtime is not None

    adapter = OverlayCaptureAdapter()
    runtime.broadcaster.publish = adapter.send_overlay_payload

    try:
        yield harness, runtime, adapter
    finally:
        stop_plugin_runtime()


def test_harness_can_replay_payload_store_fixtures_into_overlay_adapter(
    harness_runtime: tuple[Any, Any, OverlayCaptureAdapter]
) -> None:
    _harness, runtime, adapter = harness_runtime
    logs = list(sample_payload_logs())
    replay_log = next(path for path in logs if path.name == "landingpad.log")
    payloads = load_payloads_from_log(replay_log, ttl_override=6, max_payloads=30)
    assert payloads

    for payload in payloads:
        runtime._publish_payload(payload)

    assert len(adapter.raw_payloads) == len(payloads)
    assert adapter.shapes
    assert all(int(payload.get("ttl")) == 6 for payload in adapter.raw_payloads if "ttl" in payload)
