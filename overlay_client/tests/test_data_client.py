import asyncio
import logging
import os
from pathlib import Path

import pytest
from PyQt6.QtWidgets import QApplication

from overlay_client import data_client as data_client_module
from overlay_client.data_client import OverlayDataClient


@pytest.fixture(scope="module")
def qt_app():
    # Force Qt to run headless for CI/CLI test runs.
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_send_cli_payload_queues_when_loop_absent(qt_app):
    client = OverlayDataClient(Path("dummy_port.json"))
    assert client.send_cli_payload({"foo": "bar"}) is True
    assert client._pending.qsize() == 1  # type: ignore[attr-defined]


def test_send_cli_payload_overflow_returns_false(qt_app):
    client = OverlayDataClient(Path("dummy_port.json"))
    # Fill pending queue
    for _ in range(client._pending.maxsize):  # type: ignore[attr-defined]
        assert client.send_cli_payload({"x": 1})
    assert client.send_cli_payload({"overflow": True}) is False


def test_send_cli_payload_uses_running_loop(qt_app):
    class EagerLoop:
        def __init__(self) -> None:
            self.calls = []

        def call_soon_threadsafe(self, fn, *args, **kwargs):
            self.calls.append((fn, args, kwargs))
            return fn(*args, **kwargs)

    class RecordingQueue:
        def __init__(self) -> None:
            self.items = []

        def put_nowait(self, payload):
            self.items.append(payload)

    client = OverlayDataClient(Path("dummy_port.json"))
    loop = EagerLoop()
    outgoing = RecordingQueue()
    client._loop = loop  # type: ignore[attr-defined]
    client._outgoing = outgoing  # type: ignore[attr-defined]

    assert client.send_cli_payload({"hello": "world"}) is True
    assert outgoing.items == [{"hello": "world"}]
    # Pending queue should remain empty when loop/outgoing are available.
    assert client._pending.qsize() == 0  # type: ignore[attr-defined]


def test_send_cli_payload_logs_loop_failure(monkeypatch, qt_app):
    class FailingLoop:
        def call_soon_threadsafe(self, fn, *args, **kwargs):
            raise RuntimeError("loop closed")

    class DummyQueue:
        def put_nowait(self, payload):
            return None

    client = OverlayDataClient(Path("dummy_port.json"))
    client._loop = FailingLoop()  # type: ignore[attr-defined]
    client._outgoing = DummyQueue()  # type: ignore[attr-defined]

    logger = logging.getLogger("EDMC.ModernOverlay.Client.DataClient")
    records = []

    class _Capture(logging.Handler):
        def emit(self, record):
            records.append(record)

    handler = _Capture()
    logger.addHandler(handler)
    try:
        assert client.send_cli_payload({"hello": "world"}) is True
    finally:
        logger.removeHandler(handler)

    assert client._pending.qsize() == 1  # type: ignore[attr-defined]
    assert any("Failed to enqueue CLI payload" in record.getMessage() for record in records)


def test_flush_outgoing_logs_write_failure(qt_app):
    class BrokenWriter:
        def write(self, data):
            raise ConnectionError("boom")

        async def drain(self):
            return None

    async def _run():
        queue_ref: asyncio.Queue = asyncio.Queue()
        await queue_ref.put({"foo": "bar"})
        await queue_ref.put(None)

        client = OverlayDataClient(Path("dummy_port.json"))

        logger = logging.getLogger("EDMC.ModernOverlay.Client.DataClient")
        records = []

        class _Capture(logging.Handler):
            def emit(self, record):
                records.append(record)

        handler = _Capture()
        logger.addHandler(handler)
        try:
            await client._flush_outgoing(BrokenWriter(), queue_ref)
        finally:
            logger.removeHandler(handler)
        return records

    log_records = asyncio.run(_run())

    assert any("Failed to write outgoing payload" in record.getMessage() for record in log_records)


def test_run_requests_shutdown_after_server_unavailable_timeout(monkeypatch, qt_app, tmp_path):
    port_file = tmp_path / "port.json"
    port_file.write_text('{"port": 12345}', encoding="utf-8")
    monkeypatch.setattr(data_client_module, "SERVER_UNAVAILABLE_TIMEOUT_SECONDS", 0.03)

    async def fail_to_connect(host, port):
        raise ConnectionRefusedError("server is down")

    monkeypatch.setattr(data_client_module.asyncio, "open_connection", fail_to_connect)
    client = OverlayDataClient(port_file)
    shutdown_requests = []
    client.shutdown_requested.connect(lambda: shutdown_requests.append(True))
    logger = logging.getLogger("EDMC.ModernOverlay.Client.DataClient")
    log_messages = []

    class CaptureHandler(logging.Handler):
        def emit(self, record):
            log_messages.append(record.getMessage())

    handler = CaptureHandler()
    logger.addHandler(handler)
    try:
        asyncio.run(client._run())
    finally:
        logger.removeHandler(handler)

    assert shutdown_requests == [True]
    assert any("Connect failed to 127.0.0.1:12345" in message for message in log_messages)
    assert any("Retry 1; shutdown in" in message for message in log_messages)


def test_run_does_not_time_out_a_live_quiet_connection(monkeypatch, qt_app, tmp_path):
    port_file = tmp_path / "port.json"
    port_file.write_text('{"port": 12345}', encoding="utf-8")
    monkeypatch.setattr(data_client_module, "SERVER_UNAVAILABLE_TIMEOUT_SECONDS", 0.01)

    class QuietReader:
        async def readline(self):
            await asyncio.sleep(0.02)
            client._stop_event.set()  # type: ignore[attr-defined]
            return b'{"heartbeat-free": true}\n'

    class QuietWriter:
        def write(self, data):
            return None

        async def drain(self):
            return None

        def close(self):
            return None

        async def wait_closed(self):
            return None

    async def connect(host, port):
        return QuietReader(), QuietWriter()

    monkeypatch.setattr(data_client_module.asyncio, "open_connection", connect)
    client = OverlayDataClient(port_file)
    shutdown_requests = []
    client.shutdown_requested.connect(lambda: shutdown_requests.append(True))

    asyncio.run(client._run())

    assert shutdown_requests == []
