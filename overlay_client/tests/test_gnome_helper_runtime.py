import json
import logging

import pytest

from overlay_client.backend import (
    HELPER_PROTOCOL_VERSION,
    GnomeShellHelperIpcBackend,
    GnomeShellHelperRuntime,
    HelperBoundaryError,
    HelperKind,
    HelperMessageType,
)
from overlay_client.backend.gnome_helper_runtime import create_gnome_shell_helper_tracker


class _SignalSubscription:
    def __init__(self, signal, callback):
        self._signal = signal
        self._callback = callback

    def disconnect(self):
        if self._callback in self._signal.callbacks:
            self._signal.callbacks.remove(self._callback)


class _Signal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)
        return _SignalSubscription(self, callback)

    def emit(self, payload):
        for callback in list(self.callbacks):
            callback(payload)


class _Proxy:
    def __init__(self, *, hello_response):
        self._hello_response = hello_response
        self.Event = _Signal()
        self.called_tokens = []

    def Hello(self, session_token):
        self.called_tokens.append(session_token)
        return self._hello_response


class _Bus:
    def __init__(self, proxy):
        self._proxy = proxy
        self.calls = []

    def get(self, service_name, object_path):
        self.calls.append((service_name, object_path))
        return self._proxy


def _logger():
    return logging.getLogger("test.gnome_helper_runtime")


def test_gnome_helper_runtime_starts_with_validated_hello_message():
    proxy = _Proxy(hello_response=("gnome_shell_extension", HELPER_PROTOCOL_VERSION, "stage2.3"))
    bus = _Bus(proxy)
    runtime = GnomeShellHelperRuntime(
        session_token="session-token",
        logger=_logger(),
        bus_factory=lambda: bus,
    )

    hello = runtime.start()

    assert hello.message_type is HelperMessageType.HELLO
    assert hello.helper_kind is HelperKind.GNOME_SHELL_EXTENSION
    assert hello.protocol_version == HELPER_PROTOCOL_VERSION
    assert hello.helper_version == "stage2.3"
    assert bus.calls == [("org.edmc.EDMCModernOverlay", "/org/edmc/EDMCModernOverlay")]
    assert proxy.called_tokens == ["session-token"]
    assert runtime.hello_message == hello
    assert runtime.boundary.endpoint.interface_name == "org.edmc.EDMCModernOverlay.Helper"


def test_gnome_helper_runtime_queues_validated_helper_events():
    proxy = _Proxy(hello_response=("gnome_shell_extension", HELPER_PROTOCOL_VERSION, "stage2.3"))
    runtime = GnomeShellHelperRuntime(
        session_token="session-token",
        logger=_logger(),
        bus_factory=lambda: _Bus(proxy),
    )
    runtime.start()

    proxy.Event.emit(
        json.dumps(
            {
                "type": "event",
                "helper_kind": "gnome_shell_extension",
                "protocol_version": HELPER_PROTOCOL_VERSION,
                "session_token": "session-token",
                "event": "active_window_changed",
                "payload": {
                    "matched": True,
                    "identifier": "stable:123",
                    "title": "Elite - Dangerous",
                    "wm_class": "",
                    "is_foreground": True,
                    "is_visible": True,
                },
            }
        )
    )

    events = runtime.drain_events()

    assert len(events) == 1
    assert events[0].message_type is HelperMessageType.EVENT
    assert events[0].event == "active_window_changed"
    assert events[0].payload["identifier"] == "stable:123"
    assert runtime.drain_events() == ()


def test_gnome_helper_runtime_accepts_presentation_state_events():
    proxy = _Proxy(hello_response=("gnome_shell_extension", HELPER_PROTOCOL_VERSION, "stage5.4"))
    runtime = GnomeShellHelperRuntime(
        session_token="session-token",
        logger=_logger(),
        bus_factory=lambda: _Bus(proxy),
    )
    runtime.start()

    proxy.Event.emit(
        json.dumps(
            {
                "type": "event",
                "helper_kind": "gnome_shell_extension",
                "protocol_version": HELPER_PROTOCOL_VERSION,
                "session_token": "session-token",
                "event": "presentation_state_changed",
                "payload": {
                    "target_found": True,
                    "target_identifier": "stable:14",
                    "target_is_foreground": True,
                    "overlay_found": True,
                    "overlay_identifier": "stable:77",
                    "overlay_is_above": True,
                    "promotion_applied": True,
                    "overlay_input_passthrough_requested": True,
                    "overlay_input_passthrough_applied": True,
                    "overlay_actor_reactive": False,
                    "shell_chrome_hidden": True,
                    "panel_hidden": True,
                    "dock_hidden": True,
                },
            }
        )
    )

    events = runtime.drain_events()

    assert len(events) == 1
    assert events[0].message_type is HelperMessageType.EVENT
    assert events[0].event == "presentation_state_changed"
    assert events[0].payload["promotion_applied"] is True
    assert events[0].payload["overlay_input_passthrough_applied"] is True
    assert events[0].payload["shell_chrome_hidden"] is True


def test_gnome_helper_runtime_rejects_invalid_events_fail_closed():
    proxy = _Proxy(hello_response=("gnome_shell_extension", HELPER_PROTOCOL_VERSION, "stage2.3"))
    runtime = GnomeShellHelperRuntime(
        session_token="session-token",
        logger=_logger(),
        bus_factory=lambda: _Bus(proxy),
    )
    runtime.start()

    proxy.Event.emit(
        json.dumps(
            {
                "type": "event",
                "helper_kind": "gnome_shell_extension",
                "protocol_version": HELPER_PROTOCOL_VERSION,
                "session_token": "wrong-token",
                "event": "active_window_changed",
                "payload": {},
            }
        )
    )

    assert runtime.drain_events() == ()
    assert isinstance(runtime.last_error, HelperBoundaryError)
    assert "session_token" in str(runtime.last_error)


def test_gnome_helper_runtime_rejects_invalid_hello_response():
    proxy = _Proxy(hello_response=("wrong_helper", HELPER_PROTOCOL_VERSION, "stage2.3"))
    runtime = GnomeShellHelperRuntime(
        session_token="session-token",
        logger=_logger(),
        bus_factory=lambda: _Bus(proxy),
    )

    with pytest.raises(HelperBoundaryError, match="helper_kind"):
        runtime.start()


def test_gnome_shell_helper_backend_creates_runtime():
    backend = GnomeShellHelperIpcBackend(bus_factory=lambda: _Bus(_Proxy(hello_response=("gnome_shell_extension", 1, "v"))))
    runtime = backend.create_runtime(session_token="session-token", logger=_logger())

    assert isinstance(runtime, GnomeShellHelperRuntime)
    assert runtime.boundary.session_token == "session-token"


def test_gnome_helper_tracker_translates_geometry_events_into_window_state():
    proxy = _Proxy(hello_response=("gnome_shell_extension", HELPER_PROTOCOL_VERSION, "stage2.3"))
    backend = GnomeShellHelperIpcBackend(bus_factory=lambda: _Bus(proxy))
    tracker = create_gnome_shell_helper_tracker(
        _logger(),
        helper_backend=backend,
        monitor_provider=lambda: [("screen-a", 0, 0, 2560, 1440)],
    )

    assert tracker.poll() is None

    proxy.Event.emit(
        json.dumps(
            {
                "type": "event",
                "helper_kind": "gnome_shell_extension",
                "protocol_version": HELPER_PROTOCOL_VERSION,
                "session_token": next(iter(proxy.called_tokens)),
                "event": "window_geometry_changed",
                "payload": {
                    "identifier": "stable:123",
                    "title": "Elite - Dangerous",
                    "wm_class": "",
                    "is_foreground": True,
                    "is_visible": True,
                    "x": 10,
                    "y": 20,
                    "width": 1280,
                    "height": 720,
                },
            }
        )
    )

    state = tracker.poll()

    assert state is not None
    assert state.identifier == "stable:123"
    assert state.x == 10
    assert state.y == 20
    assert state.width == 1280
    assert state.height == 720
    assert state.global_x == 10
    assert state.global_y == 20


def test_gnome_helper_tracker_preserves_state_when_focus_moves_away_from_matched_window():
    proxy = _Proxy(hello_response=("gnome_shell_extension", HELPER_PROTOCOL_VERSION, "stage3.4"))
    backend = GnomeShellHelperIpcBackend(bus_factory=lambda: _Bus(proxy))
    tracker = create_gnome_shell_helper_tracker(_logger(), helper_backend=backend)

    tracker.poll()
    session_token = next(iter(proxy.called_tokens))

    proxy.Event.emit(
        json.dumps(
            {
                "type": "event",
                "helper_kind": "gnome_shell_extension",
                "protocol_version": HELPER_PROTOCOL_VERSION,
                "session_token": session_token,
                "event": "window_geometry_changed",
                "payload": {
                    "identifier": "stable:123",
                    "title": "Elite - Dangerous",
                    "wm_class": "",
                    "is_foreground": True,
                    "is_visible": True,
                    "x": 10,
                    "y": 20,
                    "width": 1280,
                    "height": 720,
                },
            }
        )
    )
    initial_state = tracker.poll()

    assert initial_state is not None
    assert initial_state.identifier == "stable:123"
    assert initial_state.is_foreground is True

    proxy.Event.emit(
        json.dumps(
            {
                "type": "event",
                "helper_kind": "gnome_shell_extension",
                "protocol_version": HELPER_PROTOCOL_VERSION,
                "session_token": session_token,
                "event": "active_window_changed",
                "payload": {
                    "matched": True,
                    "identifier": "stable:123",
                    "title": "Elite - Dangerous",
                    "wm_class": "",
                    "is_foreground": False,
                    "is_visible": True,
                },
            }
        )
    )

    state = tracker.poll()

    assert state is not None
    assert state.identifier == "stable:123"
    assert state.is_foreground is False
    assert state.is_visible is True
    assert state.width == 1280
    assert state.height == 720


def test_gnome_helper_tracker_clears_state_when_helper_reports_no_match():
    proxy = _Proxy(hello_response=("gnome_shell_extension", HELPER_PROTOCOL_VERSION, "stage2.3"))
    backend = GnomeShellHelperIpcBackend(bus_factory=lambda: _Bus(proxy))
    tracker = create_gnome_shell_helper_tracker(_logger(), helper_backend=backend)

    tracker.poll()
    session_token = next(iter(proxy.called_tokens))

    proxy.Event.emit(
        json.dumps(
            {
                "type": "event",
                "helper_kind": "gnome_shell_extension",
                "protocol_version": HELPER_PROTOCOL_VERSION,
                "session_token": session_token,
                "event": "window_geometry_changed",
                "payload": {
                    "identifier": "stable:123",
                    "title": "Elite - Dangerous",
                    "wm_class": "",
                    "is_foreground": True,
                    "is_visible": True,
                    "x": 10,
                    "y": 20,
                    "width": 1280,
                    "height": 720,
                },
            }
        )
    )
    assert tracker.poll() is not None

    proxy.Event.emit(
        json.dumps(
            {
                "type": "event",
                "helper_kind": "gnome_shell_extension",
                "protocol_version": HELPER_PROTOCOL_VERSION,
                "session_token": session_token,
                "event": "active_window_changed",
                "payload": {
                    "matched": False,
                    "identifier": "",
                    "title": "",
                    "wm_class": "",
                    "is_foreground": False,
                    "is_visible": False,
                },
            }
        )
    )

    assert tracker.poll() is None


def test_gnome_helper_tracker_logs_presentation_state_without_clearing_window_state(caplog):
    proxy = _Proxy(hello_response=("gnome_shell_extension", HELPER_PROTOCOL_VERSION, "stage5.4"))
    backend = GnomeShellHelperIpcBackend(bus_factory=lambda: _Bus(proxy))
    tracker = create_gnome_shell_helper_tracker(_logger(), helper_backend=backend)

    tracker.poll()
    session_token = next(iter(proxy.called_tokens))

    proxy.Event.emit(
        json.dumps(
            {
                "type": "event",
                "helper_kind": "gnome_shell_extension",
                "protocol_version": HELPER_PROTOCOL_VERSION,
                "session_token": session_token,
                "event": "window_geometry_changed",
                "payload": {
                    "identifier": "stable:123",
                    "title": "Elite - Dangerous",
                    "wm_class": "",
                    "is_foreground": True,
                    "is_visible": True,
                    "x": 10,
                    "y": 20,
                    "width": 1280,
                    "height": 720,
                },
            }
        )
    )
    initial_state = tracker.poll()

    assert initial_state is not None

    with caplog.at_level(logging.DEBUG, logger="test.gnome_helper_runtime"):
        proxy.Event.emit(
            json.dumps(
                {
                    "type": "event",
                    "helper_kind": "gnome_shell_extension",
                    "protocol_version": HELPER_PROTOCOL_VERSION,
                    "session_token": session_token,
                    "event": "presentation_state_changed",
                    "payload": {
                        "target_found": True,
                        "target_identifier": "stable:123",
                        "target_is_foreground": True,
                        "overlay_found": True,
                        "overlay_identifier": "stable:77",
                        "overlay_is_above": True,
                        "promotion_applied": True,
                        "overlay_input_passthrough_requested": True,
                        "overlay_input_passthrough_applied": True,
                        "overlay_actor_reactive": False,
                        "shell_chrome_hidden": True,
                        "panel_hidden": True,
                        "dock_hidden": True,
                    },
                }
            )
        )
        state = tracker.poll()

    assert state is not None
    assert state.identifier == "stable:123"
    assert "GNOME helper presentation state" in caplog.text
    assert "passthrough_applied=True" in caplog.text
    assert "shell_chrome_hidden=True" in caplog.text
