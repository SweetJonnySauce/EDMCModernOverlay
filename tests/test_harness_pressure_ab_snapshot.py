from __future__ import annotations

import json
import socket
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator

import pytest

import load
from overlay_client.backend.pressure_ab import WORK_COUNTER_KEYS, build_work_snapshot
from tests.harness_fixtures import harness_runtime_context

pytestmark = pytest.mark.harness

_REAL_RUNTIME_STOP = load._PluginRuntime.stop


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


@pytest.fixture
def socket_runtime_for_pressure_snapshot(
    runtime_for_pressure_snapshot: object,
) -> Iterator[Any]:
    runtime = runtime_for_pressure_snapshot
    runtime._pressure_snapshot_timeout_seconds = 0.4
    assert runtime.broadcaster.start() is True
    try:
        yield runtime
    finally:
        runtime.broadcaster.stop()


@contextmanager
def _socket_peer(runtime: Any, *, timeout: float = 2.0) -> Iterator[tuple[socket.socket, Any]]:
    connection = socket.create_connection((runtime.broadcaster.host, runtime.broadcaster.port), timeout=timeout)
    connection.settimeout(timeout)
    reader = connection.makefile("rb")
    try:
        yield connection, reader
    finally:
        reader.close()
        connection.close()


def _send(connection: socket.socket, payload: dict[str, object]) -> None:
    connection.sendall(json.dumps(payload, separators=(",", ":")).encode("utf-8") + b"\n")


def _read_matching(reader: Any, predicate: Callable[[dict[str, object]], bool]) -> dict[str, object]:
    for _ in range(32):
        line = reader.readline()
        if not line:
            raise AssertionError("socket closed before the expected payload arrived")
        payload = json.loads(line)
        if isinstance(payload, dict) and predicate(payload):
            return payload
    raise AssertionError("expected payload was not received within 32 socket messages")


def _read_status(reader: Any) -> dict[str, object]:
    return _read_matching(reader, lambda payload: "status" in payload)


def _register_snapshot_client(connection: socket.socket, reader: Any) -> None:
    _send(
        connection,
        {
            "cli": "client_runtime_pressure_snapshot",
            "request_id": "registration-probe",
            "snapshot": _snapshot(),
        },
    )
    assert _read_status(reader) == {"status": "ok"}


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


def test_pressure_snapshot_real_socket_roundtrip_keeps_transport_responsive(
    socket_runtime_for_pressure_snapshot: Any,
) -> None:
    runtime = socket_runtime_for_pressure_snapshot
    with _socket_peer(runtime) as (client, client_reader), _socket_peer(runtime) as (requester, requester_reader):
        _register_snapshot_client(client, client_reader)

        _send(requester, {"cli": "pressure_snapshot"})
        request = _read_matching(
            client_reader,
            lambda payload: payload.get("event") == "OverlayClientPressureSnapshotRequest",
        )
        _send(
            client,
            {
                "cli": "client_runtime_pressure_snapshot",
                "request_id": request["request_id"],
                "snapshot": _snapshot(2),
            },
        )

        assert _read_status(client_reader) == {"status": "ok"}
        assert _read_status(requester_reader) == {"status": "ok", "snapshot": _snapshot(2)}
        assert runtime._pending_client_pressure_snapshot_requests == {}


def test_pressure_snapshot_real_socket_requires_valid_correlated_response(
    socket_runtime_for_pressure_snapshot: Any,
) -> None:
    runtime = socket_runtime_for_pressure_snapshot
    runtime._pressure_snapshot_timeout_seconds = 1.0
    with _socket_peer(runtime) as (client, client_reader), _socket_peer(runtime) as (requester, requester_reader):
        _register_snapshot_client(client, client_reader)
        _send(requester, {"cli": "pressure_snapshot"})
        request = _read_matching(
            client_reader,
            lambda payload: payload.get("event") == "OverlayClientPressureSnapshotRequest",
        )
        request_id = str(request["request_id"])

        _send(
            client,
            {
                "cli": "client_runtime_pressure_snapshot",
                "request_id": "0" * 32,
                "snapshot": _snapshot(3),
            },
        )
        assert _read_status(client_reader) == {"status": "ok"}
        assert request_id in runtime._pending_client_pressure_snapshot_requests

        _send(
            client,
            {
                "cli": "client_runtime_pressure_snapshot",
                "request_id": request_id,
                "snapshot": {"private_title": "forbidden"},
            },
        )
        malformed = _read_status(client_reader)
        assert malformed["status"] == "error"
        assert "invalid pressure snapshot" in str(malformed["error"])
        assert request_id in runtime._pending_client_pressure_snapshot_requests

        _send(
            client,
            {
                "cli": "client_runtime_pressure_snapshot",
                "request_id": request_id,
                "snapshot": _snapshot(4),
            },
        )
        assert _read_status(client_reader) == {"status": "ok"}
        assert _read_status(requester_reader) == {"status": "ok", "snapshot": _snapshot(4)}
        assert runtime._pending_client_pressure_snapshot_requests == {}


def test_pressure_snapshot_real_socket_timeout_is_bounded_and_cleans_up(
    socket_runtime_for_pressure_snapshot: Any,
) -> None:
    runtime = socket_runtime_for_pressure_snapshot
    runtime._pressure_snapshot_timeout_seconds = 0.1
    with _socket_peer(runtime) as (requester, requester_reader):
        started = time.monotonic()
        _send(requester, {"cli": "pressure_snapshot"})
        response = _read_status(requester_reader)
        elapsed = time.monotonic() - started

    assert response == {"status": "unavailable", "reason": "client_snapshot_timeout"}
    assert elapsed < 0.75
    assert runtime._pending_client_pressure_snapshot_requests == {}


def test_pressure_snapshot_real_socket_shutdown_wakes_waiter_and_cleans_up(
    socket_runtime_for_pressure_snapshot: Any,
) -> None:
    runtime = socket_runtime_for_pressure_snapshot
    runtime._pressure_snapshot_timeout_seconds = 3.0
    with _socket_peer(runtime) as (client, client_reader), _socket_peer(runtime) as (requester, _requester_reader):
        _register_snapshot_client(client, client_reader)
        _send(requester, {"cli": "pressure_snapshot"})
        _read_matching(
            client_reader,
            lambda payload: payload.get("event") == "OverlayClientPressureSnapshotRequest",
        )

        started = time.monotonic()
        _REAL_RUNTIME_STOP(runtime)
        elapsed = time.monotonic() - started

    assert elapsed < 1.0
    assert runtime._pending_client_pressure_snapshot_requests == {}
    assert runtime.broadcaster._thread is None


def test_neighboring_cli_command_remains_on_socket_thread(
    socket_runtime_for_pressure_snapshot: Any,
) -> None:
    runtime = socket_runtime_for_pressure_snapshot
    callback_threads: list[threading.Thread] = []
    original_callback = runtime.broadcaster.ingest_callback

    def _record_thread(payload: dict[str, object]) -> dict[str, object] | None:
        callback_threads.append(threading.current_thread())
        assert original_callback is not None
        return original_callback(payload)

    runtime.broadcaster.ingest_callback = _record_thread
    with _socket_peer(runtime) as (connection, reader):
        _send(connection, {"cli": "does_not_exist"})
        response = _read_status(reader)

    assert response["status"] == "error"
    assert "Unsupported CLI command" in str(response["error"])
    assert callback_threads == [runtime.broadcaster._thread]
