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
GNOME_SHELL_HELPER_CAPABILITIES = ("hello", "health", "version", "protocol", "capabilities")
GNOME_SHELL_HELPER_REQUIRED_CAPABILITIES = GNOME_SHELL_HELPER_CAPABILITIES
GNOME_SHELL_HELPER_HEALTH_STALE_SECONDS = 10.0
HELPER_KIND = HelperKind.GNOME_SHELL_EXTENSION
HELPER_PROTOCOL = 1
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


def _coerce_health_payload(raw_health: object) -> Mapping[str, object]:
    raw = raw_health
    if isinstance(raw, (tuple, list)) and len(raw) == 1:
        raw = raw[0]
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise HelperBoundaryError("helper health payload is not valid JSON") from exc
        raw = parsed
    if not isinstance(raw, Mapping):
        raise HelperBoundaryError("helper health payload must be a mapping or JSON object string")
    return raw


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
