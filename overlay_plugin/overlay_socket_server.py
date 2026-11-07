"""Threaded JSON-over-TCP broadcaster used by the EDMC Modern Overlay plugin."""
from __future__ import annotations

import asyncio
import json
import queue
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Set, Tuple


LogFunc = Callable[[str], None]
IngestFunc = Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]

# plugin_stop runs on EDMC's shutdown thread. The worker is a daemon, so a
# client that does not finish closing must not keep the window up.
_STOP_JOIN_SECONDS = 0.5
_CLOSE_WAIT_SECONDS = 0.3


@dataclass
class SocketBroadcaster:
    """Runs a background TCP server that streams JSON lines to clients."""

    host: str = "127.0.0.1"
    port: int = 0
    log: LogFunc = lambda _msg: None  # noqa: E731 - simple default noop logger
    ingest_callback: Optional[IngestFunc] = None
    log_debug: Optional[LogFunc] = None
    connection_log_interval: float = 0.0
    _loop: Optional[asyncio.AbstractEventLoop] = field(default=None, init=False)
    _thread: Optional[threading.Thread] = field(default=None, init=False)
    _stop_event: threading.Event = field(default_factory=threading.Event, init=False)
    _ready_event: threading.Event = field(default_factory=threading.Event, init=False)
    _queue: "queue.Queue[Optional[str]]" = field(default_factory=queue.Queue, init=False)
    _clients: Set[Tuple[asyncio.StreamReader, asyncio.StreamWriter]] = field(default_factory=set, init=False)
    _server: Optional[asyncio.AbstractServer] = field(default=None, init=False)
    _start_error: Optional[BaseException] = field(default=None, init=False)
    _connection_log_counts: Dict[str, int] = field(default_factory=dict, init=False)
    _connection_log_timer: Optional[asyncio.TimerHandle] = field(default=None, init=False)
    _last_connection_peer: Optional[Any] = field(default=None, init=False)

    def start(self) -> bool:
        """Start the broadcast server on a background thread.

        Returns ``True`` when the listener becomes ready, ``False`` otherwise.
        """
        if self._thread and self._thread.is_alive():
            return True

        self._stop_event.clear()
        self._ready_event.clear()
        self._start_error = None
        self._thread = threading.Thread(target=self._run, name="EDMCOverlay-Server", daemon=True)
        self._thread.start()
        if not self._ready_event.wait(timeout=5.0):
            self.log("Broadcast server did not signal readiness within 5s; shutting down")
            self.stop()
            return False

        if self._start_error is not None:
            self.log(f"Broadcast server failed to start: {self._start_error}")
            self.stop()
            return False

        return True

    def stop(self) -> None:
        """Stop the server and release resources.

        Aborts connected clients instead of waiting for them to hang up.
        Leaving ``async with server`` waits until every handler finishes, and
        those handlers block in ``readline()`` until the socket closes, so the
        old 5s + 2s join ran before any client was closed.
        """
        self._stop_event.set()
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass
        loop = self._loop
        if loop is not None and loop.is_running():
            try:
                loop.call_soon_threadsafe(self._abort_clients)
            except RuntimeError:
                pass
        worker = self._thread
        if worker is not None and worker.is_alive() and worker is not threading.current_thread():
            worker.join(timeout=_STOP_JOIN_SECONDS)
            if worker.is_alive():
                self.log(
                    "Broadcast server thread still running after %.1fs; leaving the daemon thread behind"
                    % _STOP_JOIN_SECONDS
                )
                return
        self._loop = None
        self._thread = None
        self._server = None
        self._clients.clear()

    def publish(self, payload: Dict[str, Any]) -> None:
        """Queue a payload to broadcast to all connected clients."""
        if self._stop_event.is_set():
            return
        try:
            message = json.dumps(payload)
        except (TypeError, ValueError) as exc:
            self.log(f"Failed to encode payload to JSON: {exc}")
            return
        self._queue.put_nowait(message)

    # Internal helpers -----------------------------------------------------

    def _run(self) -> None:
        if self._loop is not None:
            return

        loop = asyncio.new_event_loop()
        self._loop = loop
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._server_main())
        except Exception as exc:  # pragma: no cover - defensive
            self._start_error = exc
            self.log(f"Broadcast server loop terminated with error: {exc}")
        finally:
            self._ready_event.set()
            try:
                self._abort_clients()
            except Exception:
                pass
            pending = [task for task in asyncio.all_tasks(loop) if not task.done()]
            for task in pending:
                task.cancel()
            if pending:
                try:
                    loop.run_until_complete(
                        asyncio.wait_for(
                            asyncio.gather(*pending, return_exceptions=True),
                            timeout=_CLOSE_WAIT_SECONDS,
                        )
                    )
                except Exception:
                    pass
            try:
                loop.run_until_complete(
                    asyncio.wait_for(loop.shutdown_asyncgens(), timeout=_CLOSE_WAIT_SECONDS)
                )
            except Exception:
                pass
            try:
                loop.close()
            except Exception:
                pass

    async def _server_main(self) -> None:
        server = await asyncio.start_server(self._handle_client, self.host, self.port)
        self._server = server
        sockets = server.sockets or []
        if sockets:
            sock = sockets[0]
            self.port = sock.getsockname()[1]
        self.log(f"Broadcast server listening on {self.host}:{self.port}")
        self._ready_event.set()

        try:
            while not self._stop_event.is_set():
                try:
                    message = await self._loop.run_in_executor(None, self._queue.get)
                except Exception:  # pragma: no cover - defensive
                    await asyncio.sleep(0.1)
                    continue
                if message is None:
                    if self._stop_event.is_set():
                        break
                    continue
                if self._stop_event.is_set():
                    break
                await self._broadcast(message)
        finally:
            # Abort before waiting. Server.wait_closed() does not return while
            # a handler is still blocked in readline().
            self._abort_clients()
            try:
                await asyncio.wait_for(server.wait_closed(), timeout=_CLOSE_WAIT_SECONDS)
            except Exception:
                pass
            self._clients.clear()
            self._cancel_connection_log_timer()
            self._server = None

    def _abort_writer(self, writer: asyncio.StreamWriter) -> None:
        """Drop a client socket without waiting for a graceful close."""
        try:
            transport = writer.transport
        except Exception:
            transport = None
        try:
            if transport is not None:
                transport.abort()
            else:
                writer.close()
        except Exception:
            pass

    def _abort_clients(self) -> None:
        """Abort every client and stop accepting. Must run on the server loop."""
        for _reader, writer in list(self._clients):
            self._abort_writer(writer)
        server = self._server
        if server is not None:
            try:
                server.close()
            except Exception:
                pass
        self._cancel_connection_log_timer()

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        self._clients.add((reader, writer))
        self._queue_connection_log("connected", peer)
        try:
            while not self._stop_event.is_set():
                try:
                    line = await reader.readline()
                except Exception:
                    break
                if not line:
                    break
                if not self.ingest_callback:
                    continue
                try:
                    message = json.loads(line.decode("utf-8"))
                except json.JSONDecodeError:
                    continue
                response: Optional[Dict[str, Any]] = None
                try:
                    response = self.ingest_callback(message)
                except Exception as exc:
                    meta = message.get("meta", {}) if isinstance(message, dict) else {}
                    self.log(
                        "CLI payload handler raised error: %s (meta=%s)",
                        exc,
                        meta,
                    )
                    response = {"status": "error", "error": str(exc)}
                if response is not None:
                    try:
                        writer.write(json.dumps(response).encode("utf-8") + b"\n")
                        await writer.drain()
                    except Exception:
                        pass
                    # Keep the connection alive so the client can continue receiving broadcasts.
                    continue
        except Exception:
            pass
        finally:
            self._clients.discard((reader, writer))
            self._abort_writer(writer)
        self._queue_connection_log("disconnected", peer)

    async def _broadcast(self, message: str) -> None:
        if not self._clients:
            return
        stale = []
        payload = (message + "\n").encode("utf-8")
        for reader_writer in list(self._clients):
            _reader, writer = reader_writer
            try:
                writer.write(payload)
                await writer.drain()
            except Exception:
                stale.append(reader_writer)
        for reader_writer in stale:
            self._clients.discard(reader_writer)
            _reader, writer = reader_writer
            self._abort_writer(writer)

    def _queue_connection_log(self, action: str, peer: Any) -> None:
        log_fn = self.log_debug or self.log
        if self.connection_log_interval <= 0:
            log_fn(f"Client {action} ({len(self._clients)} active) {peer}")
            return
        self._connection_log_counts[action] = self._connection_log_counts.get(action, 0) + 1
        self._last_connection_peer = peer
        if self._connection_log_timer is None and self._loop is not None:
            self._connection_log_timer = self._loop.call_later(
                self.connection_log_interval,
                self._flush_connection_log,
            )

    def _flush_connection_log(self) -> None:
        counts = self._connection_log_counts
        self._connection_log_counts = {}
        self._connection_log_timer = None
        if not counts:
            return
        connected = counts.get("connected", 0)
        disconnected = counts.get("disconnected", 0)
        parts = []
        if connected:
            parts.append(f"+{connected}")
        if disconnected:
            parts.append(f"-{disconnected}")
        summary = " ".join(parts) if parts else "0"
        peer_info = f" last={self._last_connection_peer}" if self._last_connection_peer is not None else ""
        log_fn = self.log_debug or self.log
        log_fn(f"Client activity ({len(self._clients)} active) {summary}{peer_info}")

    def _cancel_connection_log_timer(self) -> None:
        if self._connection_log_timer is not None:
            self._connection_log_timer.cancel()
            self._connection_log_timer = None
        self._connection_log_counts.clear()
        self._last_connection_peer = None


# Backwards compatibility: existing code imports WebSocketBroadcaster
WebSocketBroadcaster = SocketBroadcaster
