from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pytest

from overlay_client.backend.pressure_ab import WORK_COUNTER_KEYS, build_work_snapshot
from tests.harness_fixtures import harness_runtime_context

pytestmark = pytest.mark.harness


@pytest.fixture
def runtime_for_pressure_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Iterator[object]:
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "GNOME")
    with harness_runtime_context(monkeypatch, tmp_path, register_journal=False, capture_overlay=False) as (
        _harness,
        runtime,
        _adapter,
    ):
        yield runtime


def _snapshot(value: int = 0) -> dict[str, object]:
    return build_work_snapshot(
        origin_id="f" * 32,
        captured_at_ns=100,
        counters={key: value for key in WORK_COUNTER_KEYS},
    )


def test_pressure_snapshot_cli_roundtrip_resolves_matching_response(
    runtime_for_pressure_snapshot: object,
) -> None:
    runtime = runtime_for_pressure_snapshot
    published: list[dict[str, object]] = []

    def _publish(payload: dict[str, object]) -> None:
        published.append(dict(payload))
        if payload.get("event") != "OverlayClientPressureSnapshotRequest":
            return
        runtime._handle_cli_payload(
            {
                "cli": "client_runtime_pressure_snapshot",
                "request_id": payload["request_id"],
                "snapshot": _snapshot(2),
            }
        )

    runtime.broadcaster.publish = _publish

    response = runtime._handle_cli_payload({"cli": "pressure_snapshot"})

    assert published[-1]["event"] == "OverlayClientPressureSnapshotRequest"
    assert response == {"status": "ok", "snapshot": _snapshot(2)}
    assert runtime._pending_client_pressure_snapshot_requests == {}


def test_pressure_snapshot_timeout_is_bounded_and_clears_pending_state(
    runtime_for_pressure_snapshot: object,
) -> None:
    runtime = runtime_for_pressure_snapshot
    runtime.broadcaster.publish = lambda _payload: None
    runtime._pressure_snapshot_timeout_seconds = 0.0

    response = runtime._handle_cli_payload({"cli": "pressure_snapshot"})

    assert response == {"status": "unavailable", "reason": "client_snapshot_timeout"}
    assert runtime._pending_client_pressure_snapshot_requests == {}


def test_pressure_snapshot_rejects_malformed_client_response(
    runtime_for_pressure_snapshot: object,
) -> None:
    runtime = runtime_for_pressure_snapshot

    response = runtime._handle_cli_payload(
        {
            "cli": "client_runtime_pressure_snapshot",
            "request_id": "missing",
            "snapshot": {"private_title": "forbidden"},
        }
    )

    assert response["status"] == "error"
    assert "invalid pressure snapshot" in response["error"]
