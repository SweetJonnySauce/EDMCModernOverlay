from pathlib import Path

import pytest

from overlay_client.backend import (
    HELPER_PROTOCOL_VERSION,
    BackendInstance,
    HelperBoundaryConfig,
    HelperBoundaryError,
    HelperEndpointConfig,
    HelperKind,
    HelperMessageType,
    HelperTransport,
    parse_helper_message,
    validate_helper_boundary,
)


def _unix_boundary(runtime_dir: Path) -> HelperBoundaryConfig:
    return HelperBoundaryConfig(
        backend_instance=BackendInstance.KWIN_WAYLAND,
        helper_kind=HelperKind.KWIN_SCRIPT,
        endpoint=HelperEndpointConfig(
            transport=HelperTransport.UNIX_SOCKET,
            address=str(runtime_dir / "edmc-modern-overlay-helper.sock"),
        ),
        session_token="session-token",
        allowed_events=frozenset({"window_geometry_changed", "active_window_changed"}),
    )


def test_validate_helper_boundary_accepts_unix_socket_inside_runtime_dir(tmp_path: Path) -> None:
    boundary = validate_helper_boundary(_unix_boundary(tmp_path), runtime_dir=str(tmp_path))

    assert boundary.endpoint.transport is HelperTransport.UNIX_SOCKET
    assert boundary.endpoint.address == str(tmp_path / "edmc-modern-overlay-helper.sock")
    assert boundary.allowed_events == frozenset({"window_geometry_changed", "active_window_changed"})
    assert boundary.protocol_version == HELPER_PROTOCOL_VERSION


def test_validate_helper_boundary_rejects_unix_socket_outside_runtime_dir(tmp_path: Path) -> None:
    boundary = HelperBoundaryConfig(
        backend_instance=BackendInstance.KWIN_WAYLAND,
        helper_kind=HelperKind.KWIN_SCRIPT,
        endpoint=HelperEndpointConfig(
            transport=HelperTransport.UNIX_SOCKET,
            address="/tmp/edmc-modern-overlay-helper.sock",
        ),
        session_token="session-token",
        allowed_events=frozenset({"window_geometry_changed"}),
    )

    with pytest.raises(HelperBoundaryError, match="session runtime directory"):
        validate_helper_boundary(boundary, runtime_dir=str(tmp_path))


def test_validate_helper_boundary_accepts_session_dbus_endpoint() -> None:
    boundary = validate_helper_boundary(
        HelperBoundaryConfig(
            backend_instance=BackendInstance.GNOME_SHELL_WAYLAND,
            helper_kind=HelperKind.GNOME_SHELL_EXTENSION,
            endpoint=HelperEndpointConfig(
                transport=HelperTransport.SESSION_DBUS,
                service_name="org.edmc.ModernOverlay",
                object_path="/org/edmc/ModernOverlay",
                interface_name="org.edmc.ModernOverlay.Helper",
            ),
            session_token="session-token",
            allowed_events=frozenset({"window_geometry_changed"}),
        )
    )

    assert boundary.endpoint.transport is HelperTransport.SESSION_DBUS
    assert boundary.endpoint.service_name == "org.edmc.ModernOverlay"


def test_parse_helper_message_accepts_valid_hello_message(tmp_path: Path) -> None:
    boundary = validate_helper_boundary(_unix_boundary(tmp_path), runtime_dir=str(tmp_path))

    message = parse_helper_message(
        {
            "type": "hello",
            "helper_kind": "kwin_script",
            "protocol_version": HELPER_PROTOCOL_VERSION,
            "session_token": "session-token",
            "helper_version": "1.2.3",
            "payload": {"approved": True},
        },
        boundary=boundary,
    )

    assert message.message_type is HelperMessageType.HELLO
    assert message.helper_version == "1.2.3"
    assert message.payload == {"approved": True}


def test_parse_helper_message_accepts_allowed_event(tmp_path: Path) -> None:
    boundary = validate_helper_boundary(_unix_boundary(tmp_path), runtime_dir=str(tmp_path))

    message = parse_helper_message(
        {
            "type": "event",
            "helper_kind": "kwin_script",
            "protocol_version": HELPER_PROTOCOL_VERSION,
            "session_token": "session-token",
            "event": "window_geometry_changed",
            "payload": {"x": 10, "y": 20},
        },
        boundary=boundary,
    )

    assert message.message_type is HelperMessageType.EVENT
    assert message.event == "window_geometry_changed"
    assert message.payload == {"x": 10, "y": 20}


@pytest.mark.parametrize(
    ("payload", "match"),
    [
        (
            {
                "type": "event",
                "helper_kind": "kwin_script",
                "protocol_version": 99,
                "session_token": "session-token",
                "event": "window_geometry_changed",
                "payload": {},
            },
            "protocol_version",
        ),
        (
            {
                "type": "event",
                "helper_kind": "kwin_script",
                "protocol_version": HELPER_PROTOCOL_VERSION,
                "session_token": "wrong-token",
                "event": "window_geometry_changed",
                "payload": {},
            },
            "session_token",
        ),
        (
            {
                "type": "event",
                "helper_kind": "kwin_script",
                "protocol_version": HELPER_PROTOCOL_VERSION,
                "session_token": "session-token",
                "event": "delete_everything",
                "payload": {},
            },
            "not allowed",
        ),
    ],
)
def test_parse_helper_message_fails_closed_for_invalid_messages(
    tmp_path: Path,
    payload: dict[str, object],
    match: str,
) -> None:
    boundary = validate_helper_boundary(_unix_boundary(tmp_path), runtime_dir=str(tmp_path))

    with pytest.raises(HelperBoundaryError, match=match):
        parse_helper_message(payload, boundary=boundary)
