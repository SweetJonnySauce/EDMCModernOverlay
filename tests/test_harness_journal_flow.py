from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

import pytest

import load
from tests.harness_fixtures import harness_runtime_context

pytestmark = pytest.mark.harness


@pytest.fixture
def harness_runtime(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Iterator[tuple[object, Any, list[dict[str, Any]]]]:
    with harness_runtime_context(monkeypatch, tmp_path, register_journal=True, capture_overlay=False) as (
        harness,
        runtime,
        _adapter,
    ):
        published: list[dict[str, Any]] = []
        runtime._publish_payload = lambda payload: published.append(dict(payload))
        monkeypatch.setattr(load, "_game_running", lambda: True)
        monkeypatch.setattr(load, "_is_live_galaxy", lambda: True)
        yield harness, runtime, published


def test_journal_broadcast_event_updates_state_and_publishes_payload(
    harness_runtime: tuple[object, Any, list[dict[str, Any]]]
) -> None:
    harness, runtime, published = harness_runtime

    harness.fire_event(
        {
            "event": "Docked",
            "StarSystem": "Sol",
            "StationName": "Galileo",
        }
    )

    assert runtime._state["system"] == "Sol"
    assert runtime._state["station"] == "Galileo"
    assert runtime._state["docked"] is True
    assert published
    payload = published[-1]
    assert payload["event"] == "Docked"
    assert payload["system"] == "Sol"
    assert payload["station"] == "Galileo"
    assert payload["docked"] is True
    assert payload["raw"]["event"] == "Docked"


def test_journal_non_broadcast_event_updates_state_without_publish(
    harness_runtime: tuple[object, Any, list[dict[str, Any]]]
) -> None:
    _harness, runtime, published = harness_runtime
    runtime._state.update({"system": "Old System", "station": "", "docked": False})

    load.journal_entry(
        cmdr="Cmdr",
        is_beta=False,
        system="Lave",
        station="Lave Station",
        entry={"event": "Music", "MusicTrack": "DockingComputer"},
        state={},
    )

    assert runtime._state["system"] == "Old System"
    assert runtime._state["station"] == "Lave Station"
    assert published == []


def test_journal_live_galaxy_gate_resets_state_and_skips_publish(
    harness_runtime: tuple[object, Any, list[dict[str, Any]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness, runtime, published = harness_runtime
    runtime._state.update({"system": "Shinrarta Dezhra", "station": "Jameson Memorial", "docked": True})
    monkeypatch.setattr(load, "_is_live_galaxy", lambda: False)

    harness.fire_event({"event": "Docked", "StarSystem": "Sol", "StationName": "Galileo"})

    assert runtime._state["system"] == ""
    assert runtime._state["station"] == ""
    assert runtime._state["docked"] is False
    assert published == []


def test_journal_game_not_running_skips_processing(
    harness_runtime: tuple[object, Any, list[dict[str, Any]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness, runtime, published = harness_runtime
    runtime._state.update({"system": "Alioth", "station": "Turner", "docked": True})
    before = dict(runtime._state)
    monkeypatch.setattr(load, "_game_running", lambda: False)

    harness.fire_event({"event": "Undocked", "StarSystem": "Alioth"})

    assert runtime._state == before
    assert published == []
