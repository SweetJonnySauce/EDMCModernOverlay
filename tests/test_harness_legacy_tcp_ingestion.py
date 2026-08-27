from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

import pytest

from tests.harness_fixtures import harness_runtime_context

pytestmark = pytest.mark.harness


@pytest.fixture
def runtime_with_external_capture(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Iterator[tuple[Any, list[dict[str, Any]]]]:
    with harness_runtime_context(monkeypatch, tmp_path, register_journal=False, capture_overlay=False) as (
        _harness,
        runtime,
        _adapter,
    ):
        published: list[dict[str, Any]] = []
        runtime._publish_external = lambda payload: published.append(dict(payload)) or True
        yield runtime, published


def test_legacy_tcp_valid_message_payload_publishes(runtime_with_external_capture: tuple[Any, list[dict[str, Any]]]) -> None:
    runtime, published = runtime_with_external_capture
    raw_payload = {"id": "legacy-msg-1", "text": "Hello", "x": 11, "y": 22, "ttl": 7}

    ok = runtime._handle_legacy_tcp_payload(raw_payload)

    assert ok is True
    assert published
    payload = published[-1]
    assert payload["event"] == "LegacyOverlay"
    assert payload["type"] == "message"
    assert payload["id"] == "legacy-msg-1"
    assert payload["text"] == "Hello"
    assert payload["legacy_raw"] == raw_payload
    assert "timestamp" in payload


def test_legacy_tcp_raw_circle_preserves_canonical_fields_through_publication(
    runtime_with_external_capture: tuple[Any, list[dict[str, Any]]]
) -> None:
    runtime, published = runtime_with_external_capture
    raw_payload = {
        "id": "legacy-circle-1",
        "shape": "circle",
        "color": "#80d0ff",
        "fill": "#1a1a1acc",
        "x": 100,
        "y": 200,
        "radius": 50,
        "thickness": 2,
        "ttl": 7,
        "plugin": "CirclePlugin",
    }

    # Runtime normalization preserves raw geometry; the client owns its validation.
    ok = runtime._handle_legacy_tcp_payload(raw_payload)

    assert ok is True
    assert len(published) == 1
    payload = published[0]
    assert payload["event"] == "LegacyOverlay"
    assert payload["type"] == "shape"
    assert payload["shape"] == "circle"
    assert payload["id"] == "legacy-circle-1"
    assert payload["color"] == "#80d0ff"
    assert payload["fill"] == "#1a1a1acc"
    assert payload["x"] == 100
    assert payload["y"] == 200
    assert payload["radius"] == 50
    assert payload["thickness"] == 2
    assert payload["ttl"] == 7
    assert payload["plugin"] == "CirclePlugin"
    assert payload["legacy_raw"] == raw_payload
    assert "timestamp" in payload


def test_legacy_tcp_raw_rectangle_preserves_explicit_thickness_through_publication(
    runtime_with_external_capture: tuple[Any, list[dict[str, Any]]]
) -> None:
    runtime, published = runtime_with_external_capture
    raw_payload = {
        "id": "legacy-rect-1",
        "shape": "rect",
        "x": 100,
        "y": 200,
        "w": 300,
        "h": 400,
        "thickness": 2,
        "ttl": 7,
    }

    assert runtime._handle_legacy_tcp_payload(raw_payload) is True
    assert published[0]["shape"] == "rect"
    assert published[0]["thickness"] == 2
    assert published[0]["legacy_raw"] == raw_payload


def test_legacy_tcp_invalid_vect_payload_is_dropped(
    runtime_with_external_capture: tuple[Any, list[dict[str, Any]]]
) -> None:
    runtime, published = runtime_with_external_capture
    raw_payload = {"id": "legacy-vect-1", "shape": "vect", "vector": [{"x": 10, "y": 10}], "ttl": 9}

    ok = runtime._handle_legacy_tcp_payload(raw_payload)

    assert ok is False
    assert published == []


def test_legacy_tcp_returns_false_when_runtime_stopped(
    runtime_with_external_capture: tuple[Any, list[dict[str, Any]]]
) -> None:
    runtime, published = runtime_with_external_capture
    runtime._running = False

    ok = runtime._handle_legacy_tcp_payload({"id": "legacy-msg-2", "text": "ignored"})

    assert ok is False
    assert published == []
