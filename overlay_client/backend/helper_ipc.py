"""Pure helper-boundary models and validation for compositor-native helper IPC."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Mapping

from .contracts import BackendInstance, HelperKind

try:
    from version import __version__ as MODERN_OVERLAY_VERSION
except Exception:  # pragma: no cover - defensive fallback for unusual import contexts
    MODERN_OVERLAY_VERSION = ""

GNOME_SHELL_HELPER_UUID = "edmc-modern-overlay-helper@edmcmodernoverlay.github.io"
GNOME_SHELL_HELPER_SHELL_VERSIONS = ("46", "47", "48", "49", "50")
GNOME_SHELL_HELPER_DBUS_SERVICE = "org.edmc.ModernOverlay.Helper"
GNOME_SHELL_HELPER_DBUS_OBJECT_PATH = "/org/edmc/ModernOverlay/Helper"
GNOME_SHELL_HELPER_DBUS_INTERFACE = "org.edmc.ModernOverlay.Helper"
GNOME_SHELL_HELPER_DBUS_HELLO_METHOD = "Hello"
GNOME_SHELL_HELPER_DBUS_HEALTH_METHOD = "GetHealth"
GNOME_SHELL_HELPER_DBUS_TARGET_METHOD = "GetTargetState"
GNOME_SHELL_HELPER_DBUS_PRESENTATION_METHOD = "ApplyPresentation"
GNOME_SHELL_HELPER_CAPABILITIES = (
    "hello",
    "health",
    "version",
    "protocol",
    "capabilities",
    "target_state",
    "presentation_state",
)
GNOME_SHELL_HELPER_REQUIRED_CAPABILITIES = GNOME_SHELL_HELPER_CAPABILITIES
GNOME_SHELL_HELPER_HEALTH_STALE_SECONDS = 10.0
GNOME_SHELL_HELPER_TARGET_STALE_SECONDS = 2.0
GNOME_SHELL_HELPER_PRESENTATION_STALE_SECONDS = 2.0
GNOME_SHELL_HELPER_COORDINATE_SPACE = "gnome_shell_global_logical"
HELPER_KIND = HelperKind.GNOME_SHELL_EXTENSION
HELPER_PROTOCOL = 3
HELPER_VERSION = MODERN_OVERLAY_VERSION
HELPER_PROTOCOL_VERSION = HELPER_PROTOCOL


class HelperTransport(str, Enum):
    """Local-only transport families allowed for helper communication."""

    UNIX_SOCKET = "unix_socket"
    SESSION_DBUS = "session_dbus"


class HelperMessageType(str, Enum):
    """Minimal helper-to-client message categories."""

    HELLO = "hello"
    EVENT = "event"


class HelperHealthState(str, Enum):
    """Fail-closed health states for helper DBus validation."""

    HEALTHY = "healthy"
    MISSING_SERVICE = "missing_service"
    DBUS_UNREACHABLE = "dbus_unreachable"
    MALFORMED_PAYLOAD = "malformed_payload"
    HELPER_KIND_MISMATCH = "helper_kind_mismatch"
    VERSION_INCOMPATIBLE = "version_incompatible"
    PROTOCOL_INCOMPATIBLE = "protocol_incompatible"
    CAPABILITY_MISSING = "capability_missing"
    STALE = "stale"
    INACTIVE = "inactive"
    ERROR = "error"


class HelperTargetState(str, Enum):
    """Fail-closed target discovery states from the GNOME Shell helper."""

    FOUND = "target_found"
    NOT_FOUND = "target_not_found"
    LAUNCHER_ONLY = "launcher_only"
    AMBIGUOUS = "target_ambiguous"
    STALE = "target_stale"
    MALFORMED_PAYLOAD = "malformed_payload"
    HELPER_UNHEALTHY = "helper_unhealthy"
    GEOMETRY_INCOMPLETE = "geometry_incomplete"


class HelperPresentationAction(str, Enum):
    """Narrow presentation actions accepted by the GNOME Shell helper."""

    ATTACH = "attach"
    HIDE = "hide"
    DEGRADE = "degrade"


class HelperPresentationState(str, Enum):
    """Fail-closed presentation states from the GNOME Shell helper."""

    APPLIED = "presentation_applied"
    HIDDEN = "presentation_hidden"
    DEGRADED = "presentation_degraded"
    UNSUPPORTED = "presentation_unsupported"
    STALE = "presentation_stale"
    MALFORMED_PAYLOAD = "malformed_payload"
    HELPER_UNHEALTHY = "helper_unhealthy"
    TARGET_UNAVAILABLE = "target_unavailable"
    TARGET_HIDDEN = "target_hidden"


class HelperBoundaryError(ValueError):
    """Raised when helper-boundary configuration or messages fail validation."""


class HelperDbusProbeError(RuntimeError):
    """Raised by DBus probe callers when helper health cannot be fetched."""


class HelperDbusServiceMissing(HelperDbusProbeError):
    """Raised when the expected helper DBus service is not owned."""


class HelperDbusUnreachable(HelperDbusProbeError):
    """Raised when the session bus or helper service cannot be reached."""


@dataclass(frozen=True, slots=True)
class HelperHealthStatus:
    """Validated health snapshot for a helper-owned DBus endpoint."""

    state: HelperHealthState
    helper_kind: HelperKind = HELPER_KIND
    helper_version: str = ""
    expected_version: str = HELPER_VERSION
    helper_protocol: int | None = None
    expected_protocol: int = HELPER_PROTOCOL
    capabilities: tuple[str, ...] = field(default_factory=tuple)
    missing_capabilities: tuple[str, ...] = field(default_factory=tuple)
    observed_at_monotonic: float = 0.0
    stale_after_seconds: float = GNOME_SHELL_HELPER_HEALTH_STALE_SECONDS
    detail: str = ""
    raw_status: str = ""

    @property
    def healthy(self) -> bool:
        return self.state is HelperHealthState.HEALTHY

    def is_stale(self, now_monotonic: float) -> bool:
        if self.observed_at_monotonic <= 0:
            return False
        return (float(now_monotonic) - self.observed_at_monotonic) > self.stale_after_seconds

    def to_payload(self) -> dict[str, object]:
        return {
            "state": self.state.value,
            "healthy": self.healthy,
            "helper_kind": self.helper_kind.value,
            "helper_version": self.helper_version,
            "expected_version": self.expected_version,
            "helper_protocol": self.helper_protocol,
            "expected_protocol": self.expected_protocol,
            "capabilities": list(self.capabilities),
            "missing_capabilities": list(self.missing_capabilities),
            "observed_at_monotonic": self.observed_at_monotonic,
            "stale_after_seconds": self.stale_after_seconds,
            "detail": self.detail,
            "raw_status": self.raw_status,
        }


@dataclass(frozen=True, slots=True)
class HelperRect:
    """Rectangle in the helper's named coordinate space."""

    x: int
    y: int
    width: int
    height: int

    @property
    def valid(self) -> bool:
        return self.width > 0 and self.height > 0

    def to_payload(self) -> dict[str, int]:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }


@dataclass(frozen=True, slots=True)
class HelperDecorationInsets:
    """Insets from frame rect to content rect in Shell logical coordinates."""

    left: int = 0
    top: int = 0
    right: int = 0
    bottom: int = 0

    def to_payload(self) -> dict[str, int]:
        return {
            "left": self.left,
            "top": self.top,
            "right": self.right,
            "bottom": self.bottom,
        }


@dataclass(frozen=True, slots=True)
class HelperTargetWindow:
    """Validated GNOME helper target window snapshot."""

    target_token: str
    title: str
    wm_class: str = ""
    wm_class_instance: str = ""
    app_id: str = ""
    app_name: str = ""
    pid: int | None = None
    window_type: int | None = None
    frame_rect: HelperRect | None = None
    buffer_rect: HelperRect | None = None
    content_rect: HelperRect | None = None
    decoration_insets: HelperDecorationInsets | None = None
    monitor: int | None = None
    output_name: str = ""
    monitor_scale: float | None = None
    has_focus: bool = False
    showing_on_workspace: bool = False
    minimized: bool = False
    fullscreen: bool = False
    workspace: str = ""

    def to_payload(self) -> dict[str, object]:
        return {
            "target_token": self.target_token,
            "title": self.title,
            "wm_class": self.wm_class,
            "wm_class_instance": self.wm_class_instance,
            "app_id": self.app_id,
            "app_name": self.app_name,
            "pid": self.pid,
            "window_type": self.window_type,
            "frame_rect": self.frame_rect.to_payload() if self.frame_rect is not None else None,
            "buffer_rect": self.buffer_rect.to_payload() if self.buffer_rect is not None else None,
            "content_rect": self.content_rect.to_payload() if self.content_rect is not None else None,
            "decoration_insets": (
                self.decoration_insets.to_payload() if self.decoration_insets is not None else None
            ),
            "monitor": self.monitor,
            "output_name": self.output_name,
            "monitor_scale": self.monitor_scale,
            "has_focus": self.has_focus,
            "showing_on_workspace": self.showing_on_workspace,
            "minimized": self.minimized,
            "fullscreen": self.fullscreen,
            "workspace": self.workspace,
        }


@dataclass(frozen=True, slots=True)
class HelperTargetStatus:
    """Validated target-state result from the GNOME Shell helper."""

    state: HelperTargetState
    target: HelperTargetWindow | None = None
    helper_kind: HelperKind = HELPER_KIND
    helper_version: str = ""
    helper_protocol: int | None = None
    coordinate_space: str = GNOME_SHELL_HELPER_COORDINATE_SPACE
    sequence: int = 0
    generated_at_monotonic_us: int = 0
    generated_at_unix_ms: int = 0
    observed_at_monotonic: float = 0.0
    stale_after_seconds: float = GNOME_SHELL_HELPER_TARGET_STALE_SECONDS
    candidate_count: int = 0
    launcher_count: int = 0
    detail: str = ""

    @property
    def found(self) -> bool:
        return self.state is HelperTargetState.FOUND and self.target is not None

    def is_stale(self, now_monotonic: float) -> bool:
        if self.observed_at_monotonic <= 0:
            return False
        return (float(now_monotonic) - self.observed_at_monotonic) > self.stale_after_seconds

    def to_payload(self) -> dict[str, object]:
        return {
            "state": self.state.value,
            "found": self.found,
            "helper_kind": self.helper_kind.value,
            "helper_version": self.helper_version,
            "helper_protocol": self.helper_protocol,
            "coordinate_space": self.coordinate_space,
            "sequence": self.sequence,
            "generated_at_monotonic_us": self.generated_at_monotonic_us,
            "generated_at_unix_ms": self.generated_at_unix_ms,
            "observed_at_monotonic": self.observed_at_monotonic,
            "stale_after_seconds": self.stale_after_seconds,
            "candidate_count": self.candidate_count,
            "launcher_count": self.launcher_count,
            "detail": self.detail,
            "target": self.target.to_payload() if self.target is not None else None,
        }


@dataclass(frozen=True, slots=True)
class HelperPresentationRequest:
    """Client request for Shell-mediated presentation of the PyQt overlay."""

    action: HelperPresentationAction
    target_token: str = ""
    coordinate_space: str = GNOME_SHELL_HELPER_COORDINATE_SPACE
    content_rect: HelperRect | None = None
    renderer: str = "pyqt"
    standalone_mode: bool = False
    overlay_title: str = "EDMC Modern Overlay"
    overlay_wm_class: str = "EDMCModernOverlay"
    require_placement: bool = True
    require_chrome_free: bool = True
    require_stacking: bool = True
    require_click_through: bool = True
    require_focus_safe: bool = True
    degrade_reasons: tuple[str, ...] = field(default_factory=tuple)

    def to_payload(self) -> dict[str, object]:
        return {
            "action": self.action.value,
            "target_token": self.target_token,
            "coordinate_space": self.coordinate_space,
            "content_rect": self.content_rect.to_payload() if self.content_rect is not None else None,
            "renderer": self.renderer,
            "standalone_mode": self.standalone_mode,
            "overlay_title": self.overlay_title,
            "overlay_wm_class": self.overlay_wm_class,
            "click_through_expected": self.require_click_through,
            "focus_safe_expected": self.require_focus_safe,
            "required_gates": {
                "placement": self.require_placement,
                "chrome_free": self.require_chrome_free,
                "stacking": self.require_stacking,
                "click_through": self.require_click_through,
                "focus_safe": self.require_focus_safe,
            },
            "degrade_reasons": list(self.degrade_reasons),
        }


@dataclass(frozen=True, slots=True)
class HelperPresentationStatus:
    """Validated presentation-state result from the GNOME Shell helper."""

    state: HelperPresentationState
    action: HelperPresentationAction = HelperPresentationAction.DEGRADE
    helper_kind: HelperKind = HELPER_KIND
    helper_version: str = ""
    helper_protocol: int | None = None
    coordinate_space: str = GNOME_SHELL_HELPER_COORDINATE_SPACE
    target_token: str = ""
    overlay_token: str = ""
    requested_rect: HelperRect | None = None
    applied_rect: HelperRect | None = None
    renderer: str = "pyqt"
    placement: bool = False
    chrome_free: bool = False
    stacking: bool = False
    click_through: bool = False
    focus_safe: bool = False
    standalone_mode: bool = False
    pyqt_renderer_preserved: bool = True
    unsupported_features: tuple[str, ...] = field(default_factory=tuple)
    degrade_reasons: tuple[str, ...] = field(default_factory=tuple)
    sequence: int = 0
    generated_at_monotonic_us: int = 0
    generated_at_unix_ms: int = 0
    observed_at_monotonic: float = 0.0
    stale_after_seconds: float = GNOME_SHELL_HELPER_PRESENTATION_STALE_SECONDS
    detail: str = ""

    @property
    def applied(self) -> bool:
        return self.state is HelperPresentationState.APPLIED

    @property
    def true_overlay_ready(self) -> bool:
        return (
            self.applied
            and self.action is HelperPresentationAction.ATTACH
            and self.placement
            and self.chrome_free
            and self.stacking
            and self.click_through
            and self.focus_safe
            and self.pyqt_renderer_preserved
            and not self.standalone_mode
            and not self.unsupported_features
            and not self.degrade_reasons
        )

    def is_stale(self, now_monotonic: float) -> bool:
        if self.observed_at_monotonic <= 0:
            return False
        return (float(now_monotonic) - self.observed_at_monotonic) > self.stale_after_seconds

    def to_payload(self) -> dict[str, object]:
        return {
            "state": self.state.value,
            "applied": self.applied,
            "true_overlay_ready": self.true_overlay_ready,
            "action": self.action.value,
            "helper_kind": self.helper_kind.value,
            "helper_version": self.helper_version,
            "helper_protocol": self.helper_protocol,
            "coordinate_space": self.coordinate_space,
            "target_token": self.target_token,
            "overlay_token": self.overlay_token,
            "requested_rect": self.requested_rect.to_payload() if self.requested_rect is not None else None,
            "applied_rect": self.applied_rect.to_payload() if self.applied_rect is not None else None,
            "renderer": self.renderer,
            "placement": self.placement,
            "chrome_free": self.chrome_free,
            "stacking": self.stacking,
            "click_through": self.click_through,
            "focus_safe": self.focus_safe,
            "standalone_mode": self.standalone_mode,
            "pyqt_renderer_preserved": self.pyqt_renderer_preserved,
            "unsupported_features": list(self.unsupported_features),
            "degrade_reasons": list(self.degrade_reasons),
            "sequence": self.sequence,
            "generated_at_monotonic_us": self.generated_at_monotonic_us,
            "generated_at_unix_ms": self.generated_at_unix_ms,
            "observed_at_monotonic": self.observed_at_monotonic,
            "stale_after_seconds": self.stale_after_seconds,
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class HelperEndpointConfig:
    """Endpoint details for a local helper boundary."""

    transport: HelperTransport
    address: str = ""
    service_name: str = ""
    object_path: str = ""
    interface_name: str = ""

    def to_payload(self) -> dict[str, str]:
        return {
            "transport": self.transport.value,
            "address": self.address,
            "service_name": self.service_name,
            "object_path": self.object_path,
            "interface_name": self.interface_name,
        }


@dataclass(frozen=True, slots=True)
class HelperBoundaryConfig:
    """Validated, client-owned boundary configuration for a compositor helper."""

    backend_instance: BackendInstance
    helper_kind: HelperKind
    endpoint: HelperEndpointConfig
    session_token: str
    allowed_events: frozenset[str] = field(default_factory=frozenset)
    protocol_version: int = HELPER_PROTOCOL_VERSION

    def to_payload(self) -> dict[str, object]:
        return {
            "backend_instance": self.backend_instance.value,
            "helper_kind": self.helper_kind.value,
            "endpoint": self.endpoint.to_payload(),
            "session_token": self.session_token,
            "allowed_events": sorted(self.allowed_events),
            "protocol_version": self.protocol_version,
        }


@dataclass(frozen=True, slots=True)
class HelperMessage:
    """Validated helper-to-client message payload."""

    message_type: HelperMessageType
    helper_kind: HelperKind
    protocol_version: int
    session_token: str
    event: str = ""
    helper_version: str = ""
    payload: dict[str, object] = field(default_factory=dict)

    def to_payload(self) -> dict[str, object]:
        return {
            "type": self.message_type.value,
            "helper_kind": self.helper_kind.value,
            "protocol_version": self.protocol_version,
            "session_token": self.session_token,
            "event": self.event,
            "helper_version": self.helper_version,
            "payload": dict(self.payload),
        }


def validate_helper_boundary(
    boundary: HelperBoundaryConfig,
    *,
    runtime_dir: str = "",
) -> HelperBoundaryConfig:
    """Validate a helper boundary and return a normalized copy."""

    token = str(boundary.session_token or "").strip()
    if not token:
        raise HelperBoundaryError("Helper boundary requires a non-empty session token.")
    if int(boundary.protocol_version) < 1:
        raise HelperBoundaryError("Helper boundary requires a positive protocol version.")

    allowed_events = frozenset(
        event.strip() for event in boundary.allowed_events if isinstance(event, str) and event.strip()
    )
    if not allowed_events:
        raise HelperBoundaryError("Helper boundary requires at least one allowed event.")

    endpoint = _validate_endpoint(boundary.endpoint, runtime_dir=runtime_dir)
    return HelperBoundaryConfig(
        backend_instance=boundary.backend_instance,
        helper_kind=boundary.helper_kind,
        endpoint=endpoint,
        session_token=token,
        allowed_events=allowed_events,
        protocol_version=int(boundary.protocol_version),
    )


def parse_helper_message(
    raw: Mapping[str, object],
    *,
    boundary: HelperBoundaryConfig,
) -> HelperMessage:
    """Validate and normalize a helper message for a specific boundary."""

    if not isinstance(raw, Mapping):
        raise HelperBoundaryError("Helper message must be a mapping.")
    try:
        message_type = HelperMessageType(str(raw.get("type") or "").strip().lower())
    except ValueError as exc:
        raise HelperBoundaryError("Helper message type is invalid.") from exc
    try:
        helper_kind = HelperKind(str(raw.get("helper_kind") or "").strip().lower())
    except ValueError as exc:
        raise HelperBoundaryError("Helper message helper_kind is invalid.") from exc
    if helper_kind is not boundary.helper_kind:
        raise HelperBoundaryError("Helper message helper_kind does not match boundary.")
    protocol_raw = raw.get("protocol_version")
    try:
        protocol_version = int(str(protocol_raw))
    except (TypeError, ValueError) as exc:
        raise HelperBoundaryError("Helper message protocol_version is invalid.") from exc
    if protocol_version != boundary.protocol_version:
        raise HelperBoundaryError("Helper message protocol_version does not match boundary.")
    session_token = str(raw.get("session_token") or "").strip()
    if session_token != boundary.session_token:
        raise HelperBoundaryError("Helper message session_token does not match boundary.")
    payload = raw.get("payload")
    if payload is None:
        payload_mapping: dict[str, object] = {}
    elif isinstance(payload, Mapping):
        payload_mapping = {str(key): value for key, value in payload.items()}
    else:
        raise HelperBoundaryError("Helper message payload must be a mapping.")

    event = str(raw.get("event") or "").strip()
    helper_version = str(raw.get("helper_version") or "").strip()
    if message_type is HelperMessageType.HELLO:
        if not helper_version:
            raise HelperBoundaryError("Helper hello message requires helper_version.")
        return HelperMessage(
            message_type=message_type,
            helper_kind=helper_kind,
            protocol_version=protocol_version,
            session_token=session_token,
            helper_version=helper_version,
            payload=payload_mapping,
        )
    if event not in boundary.allowed_events:
        raise HelperBoundaryError("Helper event is not allowed for this boundary.")
    return HelperMessage(
        message_type=message_type,
        helper_kind=helper_kind,
        protocol_version=protocol_version,
        session_token=session_token,
        event=event,
        payload=payload_mapping,
    )


def probe_gnome_shell_helper_health(
    fetch_health: Callable[[], object],
    *,
    clock: Callable[[], float] = time.monotonic,
    stale_after_seconds: float = GNOME_SHELL_HELPER_HEALTH_STALE_SECONDS,
) -> HelperHealthStatus:
    """Fetch and validate the GNOME Shell helper health payload.

    The DBus transport caller is injected so this boundary stays unit-testable and
    dependency-light. Transport errors map to explicit fail-closed health states.
    """

    try:
        raw_health = fetch_health()
    except HelperDbusServiceMissing as exc:
        return _helper_health_status(HelperHealthState.MISSING_SERVICE, detail=str(exc))
    except HelperDbusProbeError as exc:
        return _helper_health_status(HelperHealthState.DBUS_UNREACHABLE, detail=str(exc))
    except Exception as exc:  # pragma: no cover - defensive transport boundary
        return _helper_health_status(HelperHealthState.DBUS_UNREACHABLE, detail=exc.__class__.__name__)

    observed_at = float(clock())
    return validate_gnome_shell_helper_health_payload(
        raw_health,
        observed_at_monotonic=observed_at,
        now_monotonic=observed_at,
        stale_after_seconds=stale_after_seconds,
    )


def validate_gnome_shell_helper_health_payload(
    raw_health: object,
    *,
    observed_at_monotonic: float,
    now_monotonic: float | None = None,
    expected_kind: HelperKind = HELPER_KIND,
    expected_version: str = HELPER_VERSION,
    expected_protocol: int = HELPER_PROTOCOL,
    required_capabilities: tuple[str, ...] = GNOME_SHELL_HELPER_REQUIRED_CAPABILITIES,
    stale_after_seconds: float = GNOME_SHELL_HELPER_HEALTH_STALE_SECONDS,
) -> HelperHealthStatus:
    """Validate a GNOME Shell helper health payload and fail closed."""

    try:
        payload = _coerce_health_payload(raw_health)
    except HelperBoundaryError as exc:
        return _helper_health_status(HelperHealthState.MALFORMED_PAYLOAD, detail=str(exc))

    raw_status = _payload_text(payload, "status").lower()
    helper_kind_token = _payload_text(payload, "helper_kind").lower()
    if not raw_status or not helper_kind_token:
        return _helper_health_status(HelperHealthState.MALFORMED_PAYLOAD, detail="missing status or helper_kind")
    try:
        helper_kind = HelperKind(helper_kind_token)
    except ValueError:
        return _helper_health_status(
            HelperHealthState.HELPER_KIND_MISMATCH,
            detail=f"unexpected helper_kind={helper_kind_token}",
            raw_status=raw_status,
        )
    if helper_kind is not expected_kind:
        return _helper_health_status(
            HelperHealthState.HELPER_KIND_MISMATCH,
            helper_kind=helper_kind,
            detail=f"expected helper_kind={expected_kind.value}",
            raw_status=raw_status,
        )

    helper_version = _payload_text(payload, "helper_version")
    helper_protocol = _payload_int(payload, "helper_protocol")
    capabilities = _payload_capabilities(payload.get("capabilities"))

    if raw_status in {"inactive", "disabled"}:
        return _helper_health_status(
            HelperHealthState.INACTIVE,
            helper_version=helper_version,
            helper_protocol=helper_protocol,
            capabilities=capabilities,
            raw_status=raw_status,
        )
    if raw_status in {"error", "failed"}:
        return _helper_health_status(
            HelperHealthState.ERROR,
            helper_version=helper_version,
            helper_protocol=helper_protocol,
            capabilities=capabilities,
            detail=_payload_text(payload, "detail"),
            raw_status=raw_status,
        )
    if raw_status not in {"healthy", "active", "ok"}:
        return _helper_health_status(
            HelperHealthState.MALFORMED_PAYLOAD,
            detail=f"unexpected status={raw_status}",
            raw_status=raw_status,
        )

    if helper_protocol is None:
        return _helper_health_status(
            HelperHealthState.MALFORMED_PAYLOAD,
            helper_version=helper_version,
            detail="helper_protocol is missing or invalid",
            raw_status=raw_status,
        )
    if int(helper_protocol) != int(expected_protocol):
        return _helper_health_status(
            HelperHealthState.PROTOCOL_INCOMPATIBLE,
            helper_version=helper_version,
            helper_protocol=helper_protocol,
            detail=f"expected protocol={expected_protocol}",
            raw_status=raw_status,
        )
    if not helper_version or (expected_version and helper_version != expected_version):
        return _helper_health_status(
            HelperHealthState.VERSION_INCOMPATIBLE,
            helper_version=helper_version,
            helper_protocol=helper_protocol,
            capabilities=capabilities,
            detail=f"expected version={expected_version}",
            raw_status=raw_status,
        )

    required = tuple(str(capability).strip() for capability in required_capabilities if str(capability).strip())
    missing_capabilities = tuple(capability for capability in required if capability not in capabilities)
    if missing_capabilities:
        return _helper_health_status(
            HelperHealthState.CAPABILITY_MISSING,
            helper_version=helper_version,
            helper_protocol=helper_protocol,
            capabilities=capabilities,
            missing_capabilities=missing_capabilities,
            raw_status=raw_status,
        )

    observed_at = float(observed_at_monotonic)
    now = observed_at if now_monotonic is None else float(now_monotonic)
    if observed_at > 0 and (now - observed_at) > stale_after_seconds:
        return _helper_health_status(
            HelperHealthState.STALE,
            helper_version=helper_version,
            helper_protocol=helper_protocol,
            capabilities=capabilities,
            observed_at_monotonic=observed_at,
            stale_after_seconds=stale_after_seconds,
            raw_status=raw_status,
        )

    return _helper_health_status(
        HelperHealthState.HEALTHY,
        helper_version=helper_version,
        helper_protocol=helper_protocol,
        capabilities=capabilities,
        observed_at_monotonic=observed_at,
        stale_after_seconds=stale_after_seconds,
        raw_status=raw_status,
    )


def probe_gnome_shell_helper_target(
    fetch_target: Callable[[], object],
    *,
    health_status: HelperHealthStatus,
    clock: Callable[[], float] = time.monotonic,
    stale_after_seconds: float = GNOME_SHELL_HELPER_TARGET_STALE_SECONDS,
) -> HelperTargetStatus:
    """Fetch and validate the GNOME Shell helper target-state payload."""

    if not health_status.healthy:
        return _helper_target_status(
            HelperTargetState.HELPER_UNHEALTHY,
            helper_version=health_status.helper_version,
            helper_protocol=health_status.helper_protocol,
            detail=health_status.state.value,
        )
    try:
        raw_target = fetch_target()
    except HelperDbusServiceMissing as exc:
        return _helper_target_status(HelperTargetState.HELPER_UNHEALTHY, detail=str(exc))
    except HelperDbusProbeError as exc:
        return _helper_target_status(HelperTargetState.HELPER_UNHEALTHY, detail=str(exc))
    except Exception as exc:  # pragma: no cover - defensive transport boundary
        return _helper_target_status(HelperTargetState.HELPER_UNHEALTHY, detail=exc.__class__.__name__)

    observed_at = float(clock())
    return validate_gnome_shell_helper_target_payload(
        raw_target,
        health_status=health_status,
        observed_at_monotonic=observed_at,
        now_monotonic=observed_at,
        stale_after_seconds=stale_after_seconds,
    )


def validate_gnome_shell_helper_target_payload(
    raw_target: object,
    *,
    health_status: HelperHealthStatus,
    observed_at_monotonic: float,
    now_monotonic: float | None = None,
    expected_kind: HelperKind = HELPER_KIND,
    expected_protocol: int = HELPER_PROTOCOL,
    expected_coordinate_space: str = GNOME_SHELL_HELPER_COORDINATE_SPACE,
    stale_after_seconds: float = GNOME_SHELL_HELPER_TARGET_STALE_SECONDS,
) -> HelperTargetStatus:
    """Validate a GNOME Shell helper target-state payload and fail closed."""

    if not health_status.healthy:
        return _helper_target_status(
            HelperTargetState.HELPER_UNHEALTHY,
            helper_version=health_status.helper_version,
            helper_protocol=health_status.helper_protocol,
            detail=health_status.state.value,
        )

    try:
        payload = _coerce_json_mapping(raw_target, "helper target payload")
    except HelperBoundaryError as exc:
        return _helper_target_status(HelperTargetState.MALFORMED_PAYLOAD, detail=str(exc))

    state_token = _payload_text(payload, "status").lower() or _payload_text(payload, "state").lower()
    helper_kind_token = _payload_text(payload, "helper_kind").lower()
    if not state_token or not helper_kind_token:
        return _helper_target_status(HelperTargetState.MALFORMED_PAYLOAD, detail="missing status or helper_kind")
    try:
        helper_kind = HelperKind(helper_kind_token)
    except ValueError:
        return _helper_target_status(
            HelperTargetState.MALFORMED_PAYLOAD,
            detail=f"unexpected helper_kind={helper_kind_token}",
        )
    if helper_kind is not expected_kind:
        return _helper_target_status(
            HelperTargetState.MALFORMED_PAYLOAD,
            helper_kind=helper_kind,
            detail=f"expected helper_kind={expected_kind.value}",
        )

    helper_version = _payload_text(payload, "helper_version")
    helper_protocol = _payload_int(payload, "helper_protocol")
    if helper_protocol is None or int(helper_protocol) != int(expected_protocol):
        return _helper_target_status(
            HelperTargetState.MALFORMED_PAYLOAD,
            helper_version=helper_version,
            helper_protocol=helper_protocol,
            detail=f"expected protocol={expected_protocol}",
        )

    coordinate_space = _payload_text(payload, "coordinate_space")
    if coordinate_space != expected_coordinate_space:
        return _helper_target_status(
            HelperTargetState.GEOMETRY_INCOMPLETE,
            helper_version=helper_version,
            helper_protocol=helper_protocol,
            coordinate_space=coordinate_space,
            detail=f"expected coordinate_space={expected_coordinate_space}",
        )

    observed_at = float(observed_at_monotonic)
    now = observed_at if now_monotonic is None else float(now_monotonic)
    generated_at_monotonic_us = _payload_int(payload, "generated_at_monotonic_us") or 0
    generated_at_unix_ms = _payload_int(payload, "generated_at_unix_ms") or 0
    sequence = _payload_int(payload, "sequence") or 0
    candidate_count = _payload_int(payload, "candidate_count") or 0
    launcher_count = _payload_int(payload, "launcher_count") or 0
    if observed_at > 0 and (now - observed_at) > stale_after_seconds:
        return _helper_target_status(
            HelperTargetState.STALE,
            helper_version=helper_version,
            helper_protocol=helper_protocol,
            coordinate_space=coordinate_space,
            sequence=sequence,
            generated_at_monotonic_us=generated_at_monotonic_us,
            generated_at_unix_ms=generated_at_unix_ms,
            observed_at_monotonic=observed_at,
            stale_after_seconds=stale_after_seconds,
            candidate_count=candidate_count,
            launcher_count=launcher_count,
            detail="observation stale",
        )

    try:
        target_state = HelperTargetState(state_token)
    except ValueError:
        return _helper_target_status(
            HelperTargetState.MALFORMED_PAYLOAD,
            helper_version=helper_version,
            helper_protocol=helper_protocol,
            detail=f"unexpected target status={state_token}",
        )
    if target_state is not HelperTargetState.FOUND:
        return _helper_target_status(
            target_state,
            helper_version=helper_version,
            helper_protocol=helper_protocol,
            coordinate_space=coordinate_space,
            sequence=sequence,
            generated_at_monotonic_us=generated_at_monotonic_us,
            generated_at_unix_ms=generated_at_unix_ms,
            observed_at_monotonic=observed_at,
            stale_after_seconds=stale_after_seconds,
            candidate_count=candidate_count,
            launcher_count=launcher_count,
            detail=_payload_text(payload, "detail"),
        )

    raw_target_window = payload.get("target")
    if not isinstance(raw_target_window, Mapping):
        return _helper_target_status(
            HelperTargetState.MALFORMED_PAYLOAD,
            helper_version=helper_version,
            helper_protocol=helper_protocol,
            coordinate_space=coordinate_space,
            detail="target_found requires target mapping",
        )
    target_window, geometry_error = _parse_helper_target_window(raw_target_window)
    if geometry_error:
        return _helper_target_status(
            HelperTargetState.GEOMETRY_INCOMPLETE,
            helper_version=helper_version,
            helper_protocol=helper_protocol,
            coordinate_space=coordinate_space,
            sequence=sequence,
            generated_at_monotonic_us=generated_at_monotonic_us,
            generated_at_unix_ms=generated_at_unix_ms,
            observed_at_monotonic=observed_at,
            stale_after_seconds=stale_after_seconds,
            candidate_count=candidate_count,
            launcher_count=launcher_count,
            detail=geometry_error,
        )
    return _helper_target_status(
        HelperTargetState.FOUND,
        target=target_window,
        helper_version=helper_version,
        helper_protocol=helper_protocol,
        coordinate_space=coordinate_space,
        sequence=sequence,
        generated_at_monotonic_us=generated_at_monotonic_us,
        generated_at_unix_ms=generated_at_unix_ms,
        observed_at_monotonic=observed_at,
        stale_after_seconds=stale_after_seconds,
        candidate_count=candidate_count,
        launcher_count=launcher_count,
    )


def build_gnome_shell_helper_presentation_request(
    target_status: HelperTargetStatus,
    *,
    standalone_mode: bool = False,
    overlay_title: str = "EDMC Modern Overlay",
    overlay_wm_class: str = "EDMCModernOverlay",
) -> HelperPresentationRequest:
    """Build a narrow presentation request from validated helper target state."""

    if not target_status.found or target_status.target is None:
        return HelperPresentationRequest(
            action=HelperPresentationAction.DEGRADE,
            standalone_mode=bool(standalone_mode),
            overlay_title=overlay_title,
            overlay_wm_class=overlay_wm_class,
            degrade_reasons=(target_status.state.value,),
        )
    target = target_status.target
    if target.minimized or not target.showing_on_workspace:
        return HelperPresentationRequest(
            action=HelperPresentationAction.HIDE,
            target_token=target.target_token,
            content_rect=target.content_rect,
            standalone_mode=bool(standalone_mode),
            overlay_title=overlay_title,
            overlay_wm_class=overlay_wm_class,
            degrade_reasons=("target_hidden",),
        )
    return HelperPresentationRequest(
        action=HelperPresentationAction.ATTACH,
        target_token=target.target_token,
        content_rect=target.content_rect,
        standalone_mode=bool(standalone_mode),
        overlay_title=overlay_title,
        overlay_wm_class=overlay_wm_class,
    )


def probe_gnome_shell_helper_presentation(
    fetch_presentation: Callable[[HelperPresentationRequest], object],
    *,
    health_status: HelperHealthStatus,
    target_status: HelperTargetStatus,
    request: HelperPresentationRequest | None = None,
    clock: Callable[[], float] = time.monotonic,
    stale_after_seconds: float = GNOME_SHELL_HELPER_PRESENTATION_STALE_SECONDS,
) -> HelperPresentationStatus:
    """Fetch and validate helper presentation state for a target request."""

    presentation_request = request or build_gnome_shell_helper_presentation_request(target_status)
    if not health_status.healthy:
        return _helper_presentation_status(
            HelperPresentationState.HELPER_UNHEALTHY,
            action=presentation_request.action,
            helper_version=health_status.helper_version,
            helper_protocol=health_status.helper_protocol,
            target_token=presentation_request.target_token,
            requested_rect=presentation_request.content_rect,
            standalone_mode=presentation_request.standalone_mode,
            degrade_reasons=(health_status.state.value,),
            detail=health_status.state.value,
        )
    if presentation_request.action is HelperPresentationAction.ATTACH and not target_status.found:
        return _helper_presentation_status(
            HelperPresentationState.TARGET_UNAVAILABLE,
            action=presentation_request.action,
            helper_version=health_status.helper_version,
            helper_protocol=health_status.helper_protocol,
            target_token=presentation_request.target_token,
            requested_rect=presentation_request.content_rect,
            standalone_mode=presentation_request.standalone_mode,
            degrade_reasons=(target_status.state.value,),
            detail=target_status.state.value,
        )
    try:
        raw_presentation = fetch_presentation(presentation_request)
    except HelperDbusServiceMissing as exc:
        return _helper_presentation_status(
            HelperPresentationState.HELPER_UNHEALTHY,
            action=presentation_request.action,
            detail=str(exc),
            degrade_reasons=("missing_service",),
        )
    except HelperDbusProbeError as exc:
        return _helper_presentation_status(
            HelperPresentationState.HELPER_UNHEALTHY,
            action=presentation_request.action,
            detail=str(exc),
            degrade_reasons=("dbus_unreachable",),
        )
    except Exception as exc:  # pragma: no cover - defensive transport boundary
        return _helper_presentation_status(
            HelperPresentationState.HELPER_UNHEALTHY,
            action=presentation_request.action,
            detail=exc.__class__.__name__,
            degrade_reasons=("transport_error",),
        )

    observed_at = float(clock())
    return validate_gnome_shell_helper_presentation_payload(
        raw_presentation,
        health_status=health_status,
        target_status=target_status,
        request=presentation_request,
        observed_at_monotonic=observed_at,
        now_monotonic=observed_at,
        stale_after_seconds=stale_after_seconds,
    )


def validate_gnome_shell_helper_presentation_payload(
    raw_presentation: object,
    *,
    health_status: HelperHealthStatus,
    target_status: HelperTargetStatus,
    request: HelperPresentationRequest,
    observed_at_monotonic: float,
    now_monotonic: float | None = None,
    expected_kind: HelperKind = HELPER_KIND,
    expected_protocol: int = HELPER_PROTOCOL,
    expected_coordinate_space: str = GNOME_SHELL_HELPER_COORDINATE_SPACE,
    stale_after_seconds: float = GNOME_SHELL_HELPER_PRESENTATION_STALE_SECONDS,
) -> HelperPresentationStatus:
    """Validate a GNOME Shell helper presentation payload and fail closed."""

    if not health_status.healthy:
        return _helper_presentation_status(
            HelperPresentationState.HELPER_UNHEALTHY,
            action=request.action,
            helper_version=health_status.helper_version,
            helper_protocol=health_status.helper_protocol,
            target_token=request.target_token,
            requested_rect=request.content_rect,
            standalone_mode=request.standalone_mode,
            degrade_reasons=(health_status.state.value,),
            detail=health_status.state.value,
        )
    if request.action is HelperPresentationAction.ATTACH and not target_status.found:
        return _helper_presentation_status(
            HelperPresentationState.TARGET_UNAVAILABLE,
            action=request.action,
            helper_version=health_status.helper_version,
            helper_protocol=health_status.helper_protocol,
            target_token=request.target_token,
            requested_rect=request.content_rect,
            standalone_mode=request.standalone_mode,
            degrade_reasons=(target_status.state.value,),
            detail=target_status.state.value,
        )
    if request.action is HelperPresentationAction.HIDE:
        expected_target = request.target_token
    else:
        expected_target = target_status.target.target_token if target_status.target is not None else request.target_token

    try:
        payload = _coerce_json_mapping(raw_presentation, "helper presentation payload")
    except HelperBoundaryError as exc:
        return _helper_presentation_status(
            HelperPresentationState.MALFORMED_PAYLOAD,
            action=request.action,
            target_token=request.target_token,
            requested_rect=request.content_rect,
            standalone_mode=request.standalone_mode,
            detail=str(exc),
        )

    state_token = _payload_text(payload, "status").lower() or _payload_text(payload, "state").lower()
    helper_kind_token = _payload_text(payload, "helper_kind").lower()
    if not state_token or not helper_kind_token:
        return _helper_presentation_status(
            HelperPresentationState.MALFORMED_PAYLOAD,
            action=request.action,
            target_token=request.target_token,
            requested_rect=request.content_rect,
            standalone_mode=request.standalone_mode,
            detail="missing status or helper_kind",
        )
    try:
        helper_kind = HelperKind(helper_kind_token)
    except ValueError:
        return _helper_presentation_status(
            HelperPresentationState.MALFORMED_PAYLOAD,
            action=request.action,
            target_token=request.target_token,
            requested_rect=request.content_rect,
            standalone_mode=request.standalone_mode,
            detail=f"unexpected helper_kind={helper_kind_token}",
        )
    if helper_kind is not expected_kind:
        return _helper_presentation_status(
            HelperPresentationState.MALFORMED_PAYLOAD,
            action=request.action,
            helper_kind=helper_kind,
            target_token=request.target_token,
            requested_rect=request.content_rect,
            standalone_mode=request.standalone_mode,
            detail=f"expected helper_kind={expected_kind.value}",
        )

    helper_version = _payload_text(payload, "helper_version")
    helper_protocol = _payload_int(payload, "helper_protocol")
    if helper_protocol is None or int(helper_protocol) != int(expected_protocol):
        return _helper_presentation_status(
            HelperPresentationState.MALFORMED_PAYLOAD,
            action=request.action,
            helper_version=helper_version,
            helper_protocol=helper_protocol,
            target_token=request.target_token,
            requested_rect=request.content_rect,
            standalone_mode=request.standalone_mode,
            detail=f"expected protocol={expected_protocol}",
        )

    coordinate_space = _payload_text(payload, "coordinate_space")
    if coordinate_space != expected_coordinate_space:
        return _helper_presentation_status(
            HelperPresentationState.DEGRADED,
            action=request.action,
            helper_version=helper_version,
            helper_protocol=helper_protocol,
            coordinate_space=coordinate_space,
            target_token=request.target_token,
            requested_rect=request.content_rect,
            standalone_mode=request.standalone_mode,
            degrade_reasons=("coordinate_space_mismatch",),
            detail=f"expected coordinate_space={expected_coordinate_space}",
        )

    observed_at = float(observed_at_monotonic)
    now = observed_at if now_monotonic is None else float(now_monotonic)
    generated_at_monotonic_us = _payload_int(payload, "generated_at_monotonic_us") or 0
    generated_at_unix_ms = _payload_int(payload, "generated_at_unix_ms") or 0
    sequence = _payload_int(payload, "sequence") or 0
    if observed_at > 0 and (now - observed_at) > stale_after_seconds:
        return _helper_presentation_status(
            HelperPresentationState.STALE,
            action=request.action,
            helper_version=helper_version,
            helper_protocol=helper_protocol,
            coordinate_space=coordinate_space,
            target_token=_payload_text(payload, "target_token") or request.target_token,
            requested_rect=request.content_rect,
            standalone_mode=request.standalone_mode,
            sequence=sequence,
            generated_at_monotonic_us=generated_at_monotonic_us,
            generated_at_unix_ms=generated_at_unix_ms,
            observed_at_monotonic=observed_at,
            stale_after_seconds=stale_after_seconds,
            degrade_reasons=("presentation_stale",),
            detail="observation stale",
        )

    try:
        presentation_state = HelperPresentationState(state_token)
    except ValueError:
        return _helper_presentation_status(
            HelperPresentationState.MALFORMED_PAYLOAD,
            action=request.action,
            helper_version=helper_version,
            helper_protocol=helper_protocol,
            target_token=request.target_token,
            requested_rect=request.content_rect,
            standalone_mode=request.standalone_mode,
            detail=f"unexpected presentation status={state_token}",
        )

    action_token = _payload_text(payload, "action").lower() or request.action.value
    try:
        action = HelperPresentationAction(action_token)
    except ValueError:
        return _helper_presentation_status(
            HelperPresentationState.MALFORMED_PAYLOAD,
            action=request.action,
            helper_version=helper_version,
            helper_protocol=helper_protocol,
            target_token=request.target_token,
            requested_rect=request.content_rect,
            standalone_mode=request.standalone_mode,
            detail=f"unexpected presentation action={action_token}",
        )

    target_token = _payload_text(payload, "target_token",) or request.target_token
    if expected_target and target_token and target_token != expected_target:
        return _helper_presentation_status(
            HelperPresentationState.DEGRADED,
            action=action,
            helper_version=helper_version,
            helper_protocol=helper_protocol,
            coordinate_space=coordinate_space,
            target_token=target_token,
            requested_rect=request.content_rect,
            standalone_mode=request.standalone_mode,
            sequence=sequence,
            generated_at_monotonic_us=generated_at_monotonic_us,
            generated_at_unix_ms=generated_at_unix_ms,
            observed_at_monotonic=observed_at,
            stale_after_seconds=stale_after_seconds,
            degrade_reasons=("target_token_mismatch",),
            detail=f"expected target_token={expected_target}",
        )

    requested_rect = _payload_rect(payload.get("requestedRect", payload.get("requested_rect"))) or request.content_rect
    applied_rect = _payload_rect(payload.get("appliedRect", payload.get("applied_rect")))
    renderer = _payload_text(payload, "renderer") or request.renderer
    unsupported_features = _payload_string_tuple(payload.get("unsupported_features", payload.get("unsupportedFeatures")))
    degrade_reasons = _payload_string_tuple(payload.get("degrade_reasons", payload.get("degradeReasons")))
    placement = _mapping_bool(payload, "placement")
    chrome_free = _mapping_bool(payload, "chrome_free", "chromeFree")
    stacking = _mapping_bool(payload, "stacking")
    click_through = _mapping_bool(payload, "click_through", "clickThrough")
    focus_safe = _mapping_bool(payload, "focus_safe", "focusSafe")
    standalone_mode = _mapping_bool(payload, "standalone_mode", "standaloneMode") or request.standalone_mode
    pyqt_renderer_preserved = renderer == "pyqt"

    if presentation_state is HelperPresentationState.APPLIED:
        missing_gate_reasons = _missing_presentation_gate_reasons(
            request,
            placement=placement,
            chrome_free=chrome_free,
            stacking=stacking,
            click_through=click_through,
            focus_safe=focus_safe,
            renderer=renderer,
            standalone_mode=standalone_mode,
            applied_rect=applied_rect,
        )
        if action is not HelperPresentationAction.ATTACH:
            missing_gate_reasons += ("action_not_attach",)
        if missing_gate_reasons:
            return _helper_presentation_status(
                HelperPresentationState.DEGRADED,
                action=action,
                helper_version=helper_version,
                helper_protocol=helper_protocol,
                coordinate_space=coordinate_space,
                target_token=target_token,
                overlay_token=_payload_text(payload, "overlay_token",),
                requested_rect=requested_rect,
                applied_rect=applied_rect,
                renderer=renderer,
                placement=placement,
                chrome_free=chrome_free,
                stacking=stacking,
                click_through=click_through,
                focus_safe=focus_safe,
                standalone_mode=standalone_mode,
                pyqt_renderer_preserved=pyqt_renderer_preserved,
                unsupported_features=unsupported_features,
                degrade_reasons=tuple(dict.fromkeys(degrade_reasons + missing_gate_reasons)),
                sequence=sequence,
                generated_at_monotonic_us=generated_at_monotonic_us,
                generated_at_unix_ms=generated_at_unix_ms,
                observed_at_monotonic=observed_at,
                stale_after_seconds=stale_after_seconds,
                detail=_payload_text(payload, "detail"),
            )

    if presentation_state is HelperPresentationState.HIDDEN and action is not HelperPresentationAction.HIDE:
        return _helper_presentation_status(
            HelperPresentationState.TARGET_HIDDEN,
            action=action,
            helper_version=helper_version,
            helper_protocol=helper_protocol,
            coordinate_space=coordinate_space,
            target_token=target_token,
            requested_rect=requested_rect,
            standalone_mode=standalone_mode,
            degrade_reasons=("target_hidden",),
            detail=_payload_text(payload, "detail"),
        )

    return _helper_presentation_status(
        presentation_state,
        action=action,
        helper_version=helper_version,
        helper_protocol=helper_protocol,
        coordinate_space=coordinate_space,
        target_token=target_token,
        overlay_token=_payload_text(payload, "overlay_token",),
        requested_rect=requested_rect,
        applied_rect=applied_rect,
        renderer=renderer,
        placement=placement,
        chrome_free=chrome_free,
        stacking=stacking,
        click_through=click_through,
        focus_safe=focus_safe,
        standalone_mode=standalone_mode,
        pyqt_renderer_preserved=pyqt_renderer_preserved,
        unsupported_features=unsupported_features,
        degrade_reasons=degrade_reasons,
        sequence=sequence,
        generated_at_monotonic_us=generated_at_monotonic_us,
        generated_at_unix_ms=generated_at_unix_ms,
        observed_at_monotonic=observed_at,
        stale_after_seconds=stale_after_seconds,
        detail=_payload_text(payload, "detail"),
    )


def select_elite_dangerous_target(candidates: list[Mapping[str, object]]) -> dict[str, object]:
    """Select the Elite Dangerous client from Shell-visible window metadata."""

    client_candidates: list[tuple[int, Mapping[str, object]]] = []
    launcher_count = 0
    for raw_candidate in candidates:
        if not isinstance(raw_candidate, Mapping):
            continue
        if _is_launcher_candidate(raw_candidate):
            launcher_count += 1
            continue
        if not _is_elite_client_candidate(raw_candidate):
            continue
        client_candidates.append((_target_candidate_score(raw_candidate), raw_candidate))

    base: dict[str, object] = {
        "coordinate_space": GNOME_SHELL_HELPER_COORDINATE_SPACE,
        "candidate_count": len(client_candidates),
        "launcher_count": launcher_count,
    }
    if not client_candidates:
        base["status"] = HelperTargetState.LAUNCHER_ONLY.value if launcher_count else HelperTargetState.NOT_FOUND.value
        return base
    client_candidates.sort(key=lambda item: item[0], reverse=True)
    if len(client_candidates) > 1 and client_candidates[0][0] == client_candidates[1][0]:
        base["status"] = HelperTargetState.AMBIGUOUS.value
        return base
    base["status"] = HelperTargetState.FOUND.value
    base["target"] = dict(client_candidates[0][1])
    return base


def _validate_endpoint(endpoint: HelperEndpointConfig, *, runtime_dir: str) -> HelperEndpointConfig:
    if endpoint.transport is HelperTransport.UNIX_SOCKET:
        address = str(endpoint.address or "").strip()
        if not address:
            raise HelperBoundaryError("Unix-socket helper endpoint requires an address.")
        path = Path(address)
        if not path.is_absolute():
            raise HelperBoundaryError("Unix-socket helper endpoint must use an absolute path.")
        if runtime_dir:
            runtime_path = Path(runtime_dir).resolve(strict=False)
            socket_path = path.resolve(strict=False)
            try:
                socket_path.relative_to(runtime_path)
            except ValueError as exc:
                raise HelperBoundaryError("Unix-socket helper endpoint must stay inside the session runtime directory.") from exc
        return HelperEndpointConfig(
            transport=endpoint.transport,
            address=address,
        )

    service_name = str(endpoint.service_name or "").strip()
    object_path = str(endpoint.object_path or "").strip()
    interface_name = str(endpoint.interface_name or "").strip()
    if not service_name or "." not in service_name or " " in service_name:
        raise HelperBoundaryError("Session-DBus helper endpoint requires a valid service name.")
    if not object_path.startswith("/"):
        raise HelperBoundaryError("Session-DBus helper endpoint requires an absolute object path.")
    if not interface_name or "." not in interface_name or " " in interface_name:
        raise HelperBoundaryError("Session-DBus helper endpoint requires a valid interface name.")
    return HelperEndpointConfig(
        transport=endpoint.transport,
        service_name=service_name,
        object_path=object_path,
        interface_name=interface_name,
    )


def _helper_health_status(
    state: HelperHealthState,
    *,
    helper_kind: HelperKind = HELPER_KIND,
    helper_version: str = "",
    helper_protocol: int | None = None,
    capabilities: tuple[str, ...] = (),
    missing_capabilities: tuple[str, ...] = (),
    observed_at_monotonic: float = 0.0,
    stale_after_seconds: float = GNOME_SHELL_HELPER_HEALTH_STALE_SECONDS,
    detail: str = "",
    raw_status: str = "",
) -> HelperHealthStatus:
    return HelperHealthStatus(
        state=state,
        helper_kind=helper_kind,
        helper_version=helper_version,
        expected_version=HELPER_VERSION,
        helper_protocol=helper_protocol,
        expected_protocol=HELPER_PROTOCOL,
        capabilities=capabilities,
        missing_capabilities=missing_capabilities,
        observed_at_monotonic=observed_at_monotonic,
        stale_after_seconds=stale_after_seconds,
        detail=detail,
        raw_status=raw_status,
    )


def _helper_target_status(
    state: HelperTargetState,
    *,
    target: HelperTargetWindow | None = None,
    helper_kind: HelperKind = HELPER_KIND,
    helper_version: str = "",
    helper_protocol: int | None = None,
    coordinate_space: str = GNOME_SHELL_HELPER_COORDINATE_SPACE,
    sequence: int = 0,
    generated_at_monotonic_us: int = 0,
    generated_at_unix_ms: int = 0,
    observed_at_monotonic: float = 0.0,
    stale_after_seconds: float = GNOME_SHELL_HELPER_TARGET_STALE_SECONDS,
    candidate_count: int = 0,
    launcher_count: int = 0,
    detail: str = "",
) -> HelperTargetStatus:
    return HelperTargetStatus(
        state=state,
        target=target,
        helper_kind=helper_kind,
        helper_version=helper_version,
        helper_protocol=helper_protocol,
        coordinate_space=coordinate_space,
        sequence=sequence,
        generated_at_monotonic_us=generated_at_monotonic_us,
        generated_at_unix_ms=generated_at_unix_ms,
        observed_at_monotonic=observed_at_monotonic,
        stale_after_seconds=stale_after_seconds,
        candidate_count=candidate_count,
        launcher_count=launcher_count,
        detail=detail,
    )


def _helper_presentation_status(
    state: HelperPresentationState,
    *,
    action: HelperPresentationAction = HelperPresentationAction.DEGRADE,
    helper_kind: HelperKind = HELPER_KIND,
    helper_version: str = "",
    helper_protocol: int | None = None,
    coordinate_space: str = GNOME_SHELL_HELPER_COORDINATE_SPACE,
    target_token: str = "",
    overlay_token: str = "",
    requested_rect: HelperRect | None = None,
    applied_rect: HelperRect | None = None,
    renderer: str = "pyqt",
    placement: bool = False,
    chrome_free: bool = False,
    stacking: bool = False,
    click_through: bool = False,
    focus_safe: bool = False,
    standalone_mode: bool = False,
    pyqt_renderer_preserved: bool = True,
    unsupported_features: tuple[str, ...] = (),
    degrade_reasons: tuple[str, ...] = (),
    sequence: int = 0,
    generated_at_monotonic_us: int = 0,
    generated_at_unix_ms: int = 0,
    observed_at_monotonic: float = 0.0,
    stale_after_seconds: float = GNOME_SHELL_HELPER_PRESENTATION_STALE_SECONDS,
    detail: str = "",
) -> HelperPresentationStatus:
    return HelperPresentationStatus(
        state=state,
        action=action,
        helper_kind=helper_kind,
        helper_version=helper_version,
        helper_protocol=helper_protocol,
        coordinate_space=coordinate_space,
        target_token=target_token,
        overlay_token=overlay_token,
        requested_rect=requested_rect,
        applied_rect=applied_rect,
        renderer=renderer,
        placement=placement,
        chrome_free=chrome_free,
        stacking=stacking,
        click_through=click_through,
        focus_safe=focus_safe,
        standalone_mode=standalone_mode,
        pyqt_renderer_preserved=pyqt_renderer_preserved,
        unsupported_features=unsupported_features,
        degrade_reasons=degrade_reasons,
        sequence=sequence,
        generated_at_monotonic_us=generated_at_monotonic_us,
        generated_at_unix_ms=generated_at_unix_ms,
        observed_at_monotonic=observed_at_monotonic,
        stale_after_seconds=stale_after_seconds,
        detail=detail,
    )


def _parse_helper_target_window(payload: Mapping[str, object]) -> tuple[HelperTargetWindow | None, str]:
    target_token = _mapping_text(payload, "target_token", "targetToken")
    title = _mapping_text(payload, "title")
    if not target_token:
        return None, "target_token missing"
    if not _title_matches_elite_dangerous(title):
        return None, "target title does not match Elite Dangerous"

    frame_rect = _payload_rect(payload.get("frameRect", payload.get("frame_rect")))
    buffer_rect = _payload_rect(payload.get("bufferRect", payload.get("buffer_rect")))
    content_rect = _payload_rect(payload.get("contentRect", payload.get("content_rect")))
    decoration_insets = _payload_insets(payload.get("decorationInsets", payload.get("decoration_insets")))
    if frame_rect is None or not frame_rect.valid:
        return None, "frameRect missing or invalid"
    if buffer_rect is None or not buffer_rect.valid:
        return None, "bufferRect missing or invalid"
    if content_rect is None or not content_rect.valid:
        return None, "contentRect missing or invalid"
    if decoration_insets is None:
        return None, "decorationInsets missing or invalid"

    return (
        HelperTargetWindow(
            target_token=target_token,
            title=title,
            wm_class=_mapping_text(payload, "wmClass", "wm_class"),
            wm_class_instance=_mapping_text(payload, "wmClassInstance", "wm_class_instance"),
            app_id=_mapping_text(payload, "appId", "app_id"),
            app_name=_mapping_text(payload, "appName", "app_name"),
            pid=_mapping_int(payload, "pid"),
            window_type=_mapping_int(payload, "windowType", "window_type"),
            frame_rect=frame_rect,
            buffer_rect=buffer_rect,
            content_rect=content_rect,
            decoration_insets=decoration_insets,
            monitor=_mapping_int(payload, "monitor"),
            output_name=_mapping_text(payload, "outputName", "output_name"),
            monitor_scale=_mapping_float(payload, "monitorScale", "monitor_scale"),
            has_focus=_mapping_bool(payload, "hasFocus", "has_focus"),
            showing_on_workspace=_mapping_bool(payload, "showingOnWorkspace", "showing_on_workspace"),
            minimized=_mapping_bool(payload, "minimized"),
            fullscreen=_mapping_bool(payload, "fullscreen"),
            workspace=_mapping_text(payload, "workspace"),
        ),
        "",
    )


def _payload_rect(raw_rect: object) -> HelperRect | None:
    if not isinstance(raw_rect, Mapping):
        return None
    x = _mapping_int(raw_rect, "x")
    y = _mapping_int(raw_rect, "y")
    width = _mapping_int(raw_rect, "width")
    height = _mapping_int(raw_rect, "height")
    if x is None or y is None or width is None or height is None:
        return None
    return HelperRect(x=x, y=y, width=width, height=height)


def _payload_insets(raw_insets: object) -> HelperDecorationInsets | None:
    if not isinstance(raw_insets, Mapping):
        return None
    left = _mapping_int(raw_insets, "left")
    top = _mapping_int(raw_insets, "top")
    right = _mapping_int(raw_insets, "right")
    bottom = _mapping_int(raw_insets, "bottom")
    if left is None or top is None or right is None or bottom is None:
        return None
    return HelperDecorationInsets(left=left, top=top, right=right, bottom=bottom)


def _is_elite_client_candidate(candidate: Mapping[str, object]) -> bool:
    title = _mapping_text(candidate, "title")
    if not _title_matches_elite_dangerous(title):
        return False
    if _is_launcher_candidate(candidate):
        return False
    if _mapping_bool(candidate, "minimized"):
        return False
    rect = _payload_rect(candidate.get("frameRect", candidate.get("frame_rect")))
    return rect is not None and rect.valid


def _is_launcher_candidate(candidate: Mapping[str, object]) -> bool:
    title = _mapping_text(candidate, "title").lower()
    if any(token in title for token in ("launcher", "installer", "updater", "update")):
        return "elite" in title
    return False


def _title_matches_elite_dangerous(title: str) -> bool:
    lowered = title.strip().lower()
    return "elite" in lowered and "dangerous" in lowered


def _target_candidate_score(candidate: Mapping[str, object]) -> int:
    score = 100
    title = _mapping_text(candidate, "title").lower()
    wm_class = _mapping_text(candidate, "wmClass", "wm_class").lower()
    app_name = _mapping_text(candidate, "appName", "app_name").lower()
    app_id = _mapping_text(candidate, "appId", "app_id").lower()
    if "(client)" in title:
        score += 20
    if "steam_app_359320" in {wm_class, app_name, app_id}:
        score += 10
    if _mapping_bool(candidate, "showingOnWorkspace", "showing_on_workspace"):
        score += 10
    if _mapping_bool(candidate, "hasFocus", "has_focus"):
        score += 5
    if _mapping_int(candidate, "pid") is not None:
        score += 1
    return score


def _coerce_json_mapping(raw_value: object, label: str) -> Mapping[str, object]:
    raw = raw_value
    if isinstance(raw, (tuple, list)) and len(raw) == 1:
        raw = raw[0]
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise HelperBoundaryError(f"{label} is not valid JSON") from exc
        raw = parsed
    if not isinstance(raw, Mapping):
        raise HelperBoundaryError(f"{label} must be a mapping or JSON object string")
    return raw


def _coerce_health_payload(raw_health: object) -> Mapping[str, object]:
    return _coerce_json_mapping(raw_health, "helper health payload")


def _payload_text(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if value is None:
        return ""
    return str(value).strip()


def _payload_int(payload: Mapping[str, object], key: str) -> int | None:
    value = payload.get(key)
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _payload_capabilities(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple, set, frozenset)):
        return ()
    return tuple(sorted(str(item).strip() for item in value if str(item).strip()))


def _payload_string_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value.strip(),) if value.strip() else ()
    if not isinstance(value, (list, tuple, set, frozenset)):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())


def _missing_presentation_gate_reasons(
    request: HelperPresentationRequest,
    *,
    placement: bool,
    chrome_free: bool,
    stacking: bool,
    click_through: bool,
    focus_safe: bool,
    renderer: str,
    standalone_mode: bool,
    applied_rect: HelperRect | None,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if request.require_placement and (not placement or applied_rect is None or not applied_rect.valid):
        reasons.append("placement_unproven")
    if request.require_chrome_free and not chrome_free:
        reasons.append("chrome_free_unproven")
    if request.require_stacking and not stacking:
        reasons.append("stacking_unproven")
    if request.require_click_through and not click_through:
        reasons.append("click_through_unproven")
    if request.require_focus_safe and not focus_safe:
        reasons.append("focus_safe_unproven")
    if renderer != "pyqt":
        reasons.append("renderer_changed")
    if standalone_mode:
        reasons.append("standalone_mode_enabled")
    return tuple(reasons)


def _mapping_text(payload: Mapping[str, object], *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if value is not None:
            return str(value).strip()
    return ""


def _mapping_int(payload: Mapping[str, object], *keys: str) -> int | None:
    for key in keys:
        value = payload.get(key)
        if value is None:
            continue
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return None
    return None


def _mapping_float(payload: Mapping[str, object], *keys: str) -> float | None:
    for key in keys:
        value = payload.get(key)
        if value is None:
            continue
        try:
            return float(str(value).strip())
        except (TypeError, ValueError):
            return None
    return None


def _mapping_bool(payload: Mapping[str, object], *keys: str) -> bool:
    for key in keys:
        value = payload.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)
    return False
