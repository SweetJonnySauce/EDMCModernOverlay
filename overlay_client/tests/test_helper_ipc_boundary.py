from pathlib import Path

import pytest

from overlay_client.backend import (
    GNOME_SHELL_ALLOWED_EVENTS,
    HELPER_PROTOCOL_VERSION,
    BackendInstance,
    HelperBoundaryConfig,
    HelperBoundaryError,
    HelperEndpointConfig,
    HelperKind,
    HelperMessageType,
    HelperTransport,
    build_gnome_shell_helper_boundary,
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


def _gnome_boundary() -> HelperBoundaryConfig:
    return build_gnome_shell_helper_boundary("session-token")


def test_validate_helper_boundary_accepts_unix_socket_inside_runtime_dir(tmp_path: Path) -> None:
    boundary = validate_helper_boundary(_unix_boundary(tmp_path), runtime_dir=str(tmp_path))

    assert boundary.backend_instance is BackendInstance.KWIN_WAYLAND
    assert boundary.helper_kind is HelperKind.KWIN_SCRIPT
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
    boundary = validate_helper_boundary(_gnome_boundary())

    assert boundary.backend_instance is BackendInstance.GNOME_SHELL_WAYLAND
    assert boundary.helper_kind is HelperKind.GNOME_SHELL_EXTENSION
    assert boundary.endpoint.transport is HelperTransport.SESSION_DBUS
    assert boundary.endpoint.service_name == "org.edmc.EDMCModernOverlay"
    assert boundary.allowed_events == GNOME_SHELL_ALLOWED_EVENTS


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


def test_parse_helper_message_accepts_gnome_session_dbus_event() -> None:
    boundary = validate_helper_boundary(_gnome_boundary())

    message = parse_helper_message(
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
        },
        boundary=boundary,
    )

    assert message.message_type is HelperMessageType.EVENT
    assert message.event == "active_window_changed"
    assert message.payload["identifier"] == "stable:123"


def test_parse_helper_message_accepts_gnome_presentation_state_event() -> None:
    boundary = validate_helper_boundary(_gnome_boundary())

    message = parse_helper_message(
        {
            "type": "event",
            "helper_kind": "gnome_shell_extension",
            "protocol_version": HELPER_PROTOCOL_VERSION,
            "session_token": "session-token",
            "event": "presentation_state_changed",
            "payload": {
                "target_found": True,
                "target_identifier": "stable:14",
                "overlay_found": True,
                "overlay_identifier": "stable:77",
                "overlay_is_above": True,
                "promotion_applied": True,
                "overlay_input_passthrough_requested": True,
                "overlay_input_passthrough_applied": True,
                "overlay_actor_reactive": False,
            },
        },
        boundary=boundary,
    )

    assert message.message_type is HelperMessageType.EVENT
    assert message.event == "presentation_state_changed"
    assert message.payload["overlay_identifier"] == "stable:77"
    assert message.payload["overlay_input_passthrough_applied"] is True


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
