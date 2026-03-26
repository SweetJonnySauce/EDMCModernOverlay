from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

import pytest

import load
from tests.harness_fixtures import harness_runtime_context

pytestmark = pytest.mark.harness


class _FakePanel:
    last_instance: "_FakePanel | None" = None
    last_kwargs: dict[str, object] = {}

    def __init__(self, *args, **kwargs):
        self.frame = object()
        self.apply_calls = 0
        _FakePanel.last_instance = self
        _FakePanel.last_kwargs = dict(kwargs)

    def apply(self) -> None:
        self.apply_calls += 1


@pytest.fixture
def harness_runtime(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[tuple[object, Any]]:
    with harness_runtime_context(monkeypatch, tmp_path, register_journal=False, capture_overlay=False) as (
        harness,
        runtime,
        _adapter,
    ):
        yield harness, runtime


def test_plugin_prefs_launch_callback_and_prefs_changed_round_trip(
    harness_runtime: tuple[object, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _harness, runtime = harness_runtime
    monkeypatch.setattr(load, "PreferencesPanel", _FakePanel)

    launch_sources: list[str] = []
    runtime.launch_overlay_controller = lambda *, source="chat": launch_sources.append(str(source))
    updated: list[str] = []
    runtime.on_preferences_updated = lambda: updated.append("updated")

    frame = load.plugin_prefs(parent=None, cmdr="TestCmdr", is_beta=False)

    assert frame is not None
    callback = _FakePanel.last_kwargs["launch_controller_callback"]
    assert callable(callback)
    callback()
    assert launch_sources == ["settings"]

    load.prefs_changed(cmdr="TestCmdr", is_beta=False)
    assert _FakePanel.last_instance is not None
    assert _FakePanel.last_instance.apply_calls == 1
    assert updated == ["updated"]


def test_prefs_changed_noop_without_panel(harness_runtime: tuple[object, Any]) -> None:
    _harness, _runtime = harness_runtime
    load._prefs_panel = None
    load.prefs_changed(cmdr="TestCmdr", is_beta=False)
