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
