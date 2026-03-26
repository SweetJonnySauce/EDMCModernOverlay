from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

import pytest

import load
from tests.harness_fixtures import harness_runtime_context

pytestmark = pytest.mark.harness


@pytest.fixture
def harness_runtime(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[tuple[object, Any]]:
    with harness_runtime_context(monkeypatch, tmp_path, register_journal=False, capture_overlay=False) as (
        harness,
        runtime,
        _adapter,
    ):
        yield harness, runtime


def test_hook_functions_forward_to_runtime_handlers(harness_runtime: tuple[object, Any]) -> None:
    _harness, runtime = harness_runtime
    journal_calls: list[dict[str, Any]] = []
    dashboard_calls: list[dict[str, Any]] = []

    def _handle_journal(cmdr, system, station, entry, state):
        journal_calls.append(
            {
                "cmdr": cmdr,
                "system": system,
                "station": station,
                "entry": dict(entry),
                "state": dict(state or {}),
            }
        )

    def _handle_dashboard(entry):
        dashboard_calls.append(dict(entry))

    runtime.handle_journal = _handle_journal
    runtime.handle_dashboard_entry = _handle_dashboard

    load.journal_entry(
        cmdr="HookCmdr",
        is_beta=False,
        system="Sol",
        station="Galileo",
        entry={"event": "Docked"},
        state={"ShipID": 42},
    )
    load.dashboard_entry(cmdr="HookCmdr", is_beta=False, entry={"Flags": 1, "ShipID": 42})

    assert journal_calls == [
        {
            "cmdr": "HookCmdr",
            "system": "Sol",
            "station": "Galileo",
            "entry": {"event": "Docked"},
            "state": {"ShipID": 42},
        }
    ]
    assert dashboard_calls == [{"Flags": 1, "ShipID": 42}]


def test_plugin_stop_clears_globals_and_hooks_become_noop(harness_runtime: tuple[object, Any]) -> None:
    _harness, _runtime = harness_runtime
    load.plugin_stop()

    assert load._plugin is None
    assert load._preferences is None
    assert load._prefs_panel is None

    load.journal_entry(
        cmdr="HookCmdr",
        is_beta=False,
        system="Sol",
        station="Galileo",
        entry={"event": "Docked"},
        state={"ShipID": 42},
    )
    load.dashboard_entry(cmdr="HookCmdr", is_beta=False, entry={"Flags": 1, "ShipID": 42})
