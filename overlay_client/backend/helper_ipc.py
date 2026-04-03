"""Pure helper-boundary models and validation for compositor-native helper IPC."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Mapping

from .contracts import BackendInstance, HelperKind

HELPER_PROTOCOL_VERSION = 1


class HelperTransport(str, Enum):
    """Local-only transport families allowed for helper communication."""

    UNIX_SOCKET = "unix_socket"
    SESSION_DBUS = "session_dbus"


class HelperMessageType(str, Enum):
    """Minimal helper-to-client message categories."""

    HELLO = "hello"
    EVENT = "event"


class HelperBoundaryError(ValueError):
    """Raised when helper-boundary configuration or messages fail validation."""


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
