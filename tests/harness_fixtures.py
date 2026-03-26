from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import pytest

import load
from tests.harness_bootstrap import create_harness, stop_plugin_runtime
from tests.overlay_adapter import OverlayCaptureAdapter


def _apply_lightweight_runtime(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
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


@contextmanager
def harness_runtime_context(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    register_journal: bool = True,
    capture_overlay: bool = False,
) -> Iterator[tuple[object, Any, OverlayCaptureAdapter | None]]:
    _apply_lightweight_runtime(monkeypatch, tmp_path)

    try:
        harness = create_harness(register_journal=register_journal)
    except RuntimeError as exc:
        if "semantic_version" in str(exc):
            pytest.skip(str(exc))
        raise

    runtime = load._plugin
    assert runtime is not None

    adapter: OverlayCaptureAdapter | None = None
    if capture_overlay:
        adapter = OverlayCaptureAdapter()
        runtime.broadcaster.publish = adapter.send_overlay_payload

    try:
        yield harness, runtime, adapter
    finally:
        stop_plugin_runtime()
