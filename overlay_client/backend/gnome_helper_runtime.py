"""Client-owned GNOME helper runtime seam for handshake and event intake."""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from .contracts import BackendInstance, HelperKind
from .helper_ipc import (
    HelperBoundaryConfig,
    HelperBoundaryError,
    HelperMessage,
    HelperMessageType,
    build_gnome_shell_helper_boundary,
    parse_helper_message,
)
from overlay_client.window_tracking_support import (
    MonitorProvider,
    WindowState,
    WindowTracker,
    augment_state_with_monitors,
    invoke_monitor_provider,
)

SessionBusFactory = Callable[[], Any]


@dataclass(frozen=True, slots=True)
class GnomeShellHelperIpcBackend:
    """GNOME helper backend that can create runtime sessions on demand."""

    backend_instance: BackendInstance = BackendInstance.GNOME_SHELL_WAYLAND
    helper_kind: HelperKind = HelperKind.GNOME_SHELL_EXTENSION
    bus_factory: SessionBusFactory | None = None

    def create_runtime(self, *, session_token: str, logger: logging.Logger) -> "GnomeShellHelperRuntime":
        return GnomeShellHelperRuntime(
            session_token=session_token,
            logger=logger,
            bus_factory=self.bus_factory,
        )


@dataclass(slots=True)
class GnomeShellHelperRuntime:
    """Runtime GNOME helper session that performs handshake and queues validated events."""

    session_token: str
    logger: logging.Logger
    bus_factory: SessionBusFactory | None = None
    boundary: HelperBoundaryConfig = field(init=False)
    hello_message: HelperMessage | None = field(init=False, default=None)
    last_error: Exception | None = field(init=False, default=None)
    _bus: Any = field(init=False, default=None, repr=False)
    _proxy: Any = field(init=False, default=None, repr=False)
    _event_subscription: Any = field(init=False, default=None, repr=False)
    _event_queue: list[HelperMessage] = field(init=False, default_factory=list, repr=False)

    def __post_init__(self) -> None:
        self.boundary = build_gnome_shell_helper_boundary(self.session_token)

    def start(self) -> HelperMessage:
        """Connect to the GNOME helper, perform handshake, and subscribe to helper events."""

        if self.hello_message is not None:
            return self.hello_message

        bus = self._session_bus()
        proxy = bus.get(
            self.boundary.endpoint.service_name,
            self.boundary.endpoint.object_path,
        )
        try:
            hello_response = proxy.Hello(self.boundary.session_token)
        except Exception as exc:
            raise HelperBoundaryError(f"GNOME helper Hello call failed: {exc}") from exc
        try:
            helper_kind, protocol_version, helper_version = hello_response
        except (TypeError, ValueError) as exc:
            raise HelperBoundaryError("GNOME helper Hello returned an invalid payload.") from exc
        hello_message = parse_helper_message(
            {
                "type": "hello",
                "helper_kind": helper_kind,
                "protocol_version": protocol_version,
                "session_token": self.boundary.session_token,
                "helper_version": helper_version,
                "payload": {},
            },
            boundary=self.boundary,
        )
        subscription = self._subscribe_to_events(proxy)

        self._bus = bus
        self._proxy = proxy
        self._event_subscription = subscription
        self.hello_message = hello_message
        self.last_error = None
        return hello_message

    def stop(self) -> None:
        """Stop the helper runtime and release event subscriptions."""

        if self._event_subscription is not None:
            disconnect = getattr(self._event_subscription, "disconnect", None)
            unsubscribe = getattr(self._event_subscription, "unsubscribe", None)
            try:
                if callable(disconnect):
                    disconnect()
                elif callable(unsubscribe):
                    unsubscribe()
                elif callable(self._event_subscription):
                    self._event_subscription()
            except Exception as exc:  # pragma: no cover - defensive cleanup
                self.logger.debug("Failed to disconnect GNOME helper event subscription: %s", exc)
        self._event_subscription = None
        self._proxy = None
        self._bus = None
        self._event_queue.clear()
        self.hello_message = None
        self.last_error = None

    def drain_events(self) -> tuple[HelperMessage, ...]:
        """Return queued validated helper events and clear the queue."""

        events = tuple(self._event_queue)
        self._event_queue.clear()
        return events

    def _session_bus(self):
        if self.bus_factory is not None:
            return self.bus_factory()

        try:
            from pydbus import SessionBus  # type: ignore
        except Exception as exc:  # pragma: no cover - dependency/runtime guard
            raise HelperBoundaryError(f"pydbus is required for GNOME helper runtime: {exc}") from exc
        return SessionBus()

    def _subscribe_to_events(self, proxy):
        signal = getattr(proxy, "Event", None)
        if signal is not None and hasattr(signal, "connect"):
            return signal.connect(self._on_event_signal)
        connect_to_signal = getattr(proxy, "connect_to_signal", None)
        if callable(connect_to_signal):
            return connect_to_signal("Event", self._on_event_signal)
        raise HelperBoundaryError("GNOME helper does not expose a subscribable Event signal.")

    def _on_event_signal(self, *args) -> None:
        if not args:
            self.last_error = HelperBoundaryError("GNOME helper Event signal did not include message_json.")
            self.logger.debug("GNOME helper Event signal missing payload")
            return

        try:
            raw_message = json.loads(str(args[0]))
            message = parse_helper_message(raw_message, boundary=self.boundary)
        except (TypeError, ValueError, HelperBoundaryError) as exc:
            self.last_error = exc
            self.logger.debug("GNOME helper event rejected: %s", exc)
            return

        self.last_error = None
        self._event_queue.append(message)


@dataclass(slots=True)
class GnomeShellHelperTracker:
    """WindowTracker backed by the validated GNOME helper runtime event stream."""

    logger: logging.Logger
    helper_backend: GnomeShellHelperIpcBackend
    title_hint: str = "elite - dangerous"
    monitor_provider: MonitorProvider | None = None
    _runtime: GnomeShellHelperRuntime | None = field(init=False, default=None, repr=False)
    _state: WindowState | None = field(init=False, default=None, repr=False)
    _warned_startup: bool = field(init=False, default=False, repr=False)

    def poll(self) -> WindowState | None:
        runtime = self._ensure_runtime()
        if runtime is None:
            return None

        for event in runtime.drain_events():
            self._apply_event(event)
        return self._state

    def set_monitor_provider(self, provider: MonitorProvider | None) -> None:
        self.monitor_provider = provider

    def _ensure_runtime(self) -> GnomeShellHelperRuntime | None:
        if self._runtime is not None:
            return self._runtime

        runtime = self.helper_backend.create_runtime(
            session_token=uuid.uuid4().hex,
            logger=self.logger,
        )
        try:
            runtime.start()
        except Exception as exc:
            if not self._warned_startup:
                self.logger.warning("GNOME helper runtime unavailable: %s", exc)
                self._warned_startup = True
            runtime.stop()
            return None
        self._runtime = runtime
        self._warned_startup = False
        return runtime

    def _apply_event(self, event: HelperMessage) -> None:
        if event.message_type is not HelperMessageType.EVENT:
            return

        if event.event == "presentation_state_changed":
            self.logger.debug(
                "GNOME helper presentation state: overlay_found=%s target_found=%s target_foreground=%s overlay_above=%s promotion_applied=%s passthrough_requested=%s passthrough_applied=%s actor_reactive=%s shell_chrome_hidden=%s panel_hidden=%s dock_hidden=%s",
                bool(event.payload.get("overlay_found")),
                bool(event.payload.get("target_found")),
                bool(event.payload.get("target_is_foreground")),
                bool(event.payload.get("overlay_is_above")),
                bool(event.payload.get("promotion_applied")),
                bool(event.payload.get("overlay_input_passthrough_requested")),
                bool(event.payload.get("overlay_input_passthrough_applied")),
                event.payload.get("overlay_actor_reactive"),
                bool(event.payload.get("shell_chrome_hidden")),
                bool(event.payload.get("panel_hidden")),
                bool(event.payload.get("dock_hidden")),
            )
            return

        if event.event == "active_window_changed":
            matched = bool(event.payload.get("matched"))
            if not matched:
                self._state = None
                return
            if self._state is not None and self._state.identifier == str(event.payload.get("identifier") or ""):
                self._state = WindowState(
                    x=self._state.x,
                    y=self._state.y,
                    width=self._state.width,
                    height=self._state.height,
                    is_foreground=bool(event.payload.get("is_foreground", self._state.is_foreground)),
                    is_visible=bool(event.payload.get("is_visible", self._state.is_visible)),
                    identifier=self._state.identifier,
                    global_x=self._state.global_x,
                    global_y=self._state.global_y,
                )
            return

        if event.event == "window_geometry_changed":
            state = self._state_from_geometry_event(event)
            if state is not None:
                self._state = state

    def _state_from_geometry_event(self, event: HelperMessage) -> WindowState | None:
        try:
            x = _payload_int(event.payload, "x")
            y = _payload_int(event.payload, "y")
            width = _payload_int(event.payload, "width")
            height = _payload_int(event.payload, "height")
        except (TypeError, ValueError):
            self.logger.debug("GNOME helper geometry event carried invalid coordinates: %s", event.payload)
            return None

        identifier = str(event.payload.get("identifier") or "").strip()
        base_state = WindowState(
            x=x,
            y=y,
            width=max(width, 0),
            height=max(height, 0),
            is_foreground=bool(event.payload.get("is_foreground", True)),
            is_visible=bool(event.payload.get("is_visible", width > 0 and height > 0)),
            identifier=identifier,
            global_x=x,
            global_y=y,
        )
        monitors = invoke_monitor_provider(self.monitor_provider, self.logger)
        return augment_state_with_monitors(
            base_state,
            monitors,
            self.logger,
            absolute_geometry=(x, y, width, height),
        )


def create_gnome_shell_helper_tracker(
    logger: logging.Logger,
    *,
    helper_backend: GnomeShellHelperIpcBackend | None = None,
    title_hint: str = "elite - dangerous",
    monitor_provider: MonitorProvider | None = None,
) -> WindowTracker:
    """Return the GNOME helper-backed tracker used by the helper-enabled bundle."""

    return GnomeShellHelperTracker(
        logger=logger,
        helper_backend=helper_backend or GnomeShellHelperIpcBackend(),
        title_hint=title_hint,
        monitor_provider=monitor_provider,
    )


def _payload_int(payload: dict[str, object], key: str) -> int:
    value = payload.get(key, 0)
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        return int(value)
    raise TypeError(f"{key} must be numeric")
