from __future__ import annotations

from pathlib import Path

from overlay_client.backend import (
    HelperPresentationAction,
    HelperPresentationRequest,
    HelperRect,
    validate_gnome_shell_helper_health_payload,
    validate_gnome_shell_helper_target_payload,
)
from overlay_client.backend.helper_ipc import (
    GNOME_SHELL_HELPER_CAPABILITIES,
    GNOME_SHELL_HELPER_COORDINATE_SPACE,
    HELPER_KIND,
    HELPER_PROTOCOL,
    HELPER_VERSION,
)
from overlay_client.backend.shell_raster_frame import (
    SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS,
    SHELL_RASTER_FRAME_TRANSPORT_PNG_PATH,
    SHELL_RASTER_FRAME_VERSION,
    SHELL_RASTER_STATIC_FRAME_INSET_PX,
    build_static_shell_raster_frame_request,
    ensure_shell_raster_cache_dir,
    shell_raster_cache_dir,
    shell_raster_frame_version,
    shell_raster_session_id,
    validate_shell_raster_frame_path,
)


def _health_status():
    return validate_gnome_shell_helper_health_payload(
        {
            "status": "healthy",
            "helper_kind": HELPER_KIND.value,
            "helper_version": HELPER_VERSION,
            "helper_protocol": HELPER_PROTOCOL,
            "capabilities": list(GNOME_SHELL_HELPER_CAPABILITIES),
        },
        observed_at_monotonic=100.0,
        now_monotonic=100.0,
    )


def _target_status(**target_overrides: object):
    target: dict[str, object] = {
        "targetToken": "meta:21",
        "title": "Elite - Dangerous (CLIENT)",
        "wmClass": "steam_app_359320",
        "wmClassInstance": "steam_app_359320",
        "appId": "steam_app_359320",
        "appName": "steam_app_359320",
        "pid": 9135,
        "windowType": 0,
        "frameRect": {"x": 0, "y": 0, "width": 3440, "height": 1440},
        "bufferRect": {"x": 0, "y": 0, "width": 3440, "height": 1440},
        "contentRect": {"x": 0, "y": 0, "width": 3440, "height": 1440},
        "decorationInsets": {"left": 0, "top": 0, "right": 0, "bottom": 0},
        "monitor": 0,
        "outputName": "DP-2",
        "monitorRect": {"x": 0, "y": 0, "width": 3440, "height": 1440},
        "monitorScale": 1.0,
        "hasFocus": True,
        "showingOnWorkspace": True,
        "minimized": False,
        "fullscreen": True,
        "workspace": "0",
    }
    target.update(target_overrides)
    return validate_gnome_shell_helper_target_payload(
        {
            "status": "target_found",
            "helper_kind": HELPER_KIND.value,
            "helper_version": HELPER_VERSION,
            "helper_protocol": HELPER_PROTOCOL,
            "coordinate_space": GNOME_SHELL_HELPER_COORDINATE_SPACE,
            "sequence": 3,
            "generated_at_monotonic_us": 123456,
            "generated_at_unix_ms": 1800000000000,
            "candidate_count": 1,
            "launcher_count": 0,
            "target": target,
        },
        health_status=_health_status(),
        observed_at_monotonic=200.0,
        now_monotonic=200.0,
    )


def _presentation_request() -> HelperPresentationRequest:
    return HelperPresentationRequest(
        action=HelperPresentationAction.ATTACH,
        target_token="meta:21",
        content_rect=HelperRect(0, 0, 3440, 1440),
    )


def _png_writer(path: Path, width: int, height: int) -> None:
    assert width == 3440 - (SHELL_RASTER_STATIC_FRAME_INSET_PX * 2)
    assert height == 1440 - (SHELL_RASTER_STATIC_FRAME_INSET_PX * 2)
    path.write_bytes(b"\x89PNG\r\n\x1a\nphase12-test")


def test_shell_raster_cache_prefers_xdg_runtime_dir(tmp_path: Path) -> None:
    cache_dir = shell_raster_cache_dir({"XDG_RUNTIME_DIR": str(tmp_path)})

    assert cache_dir == tmp_path / "EDMCModernOverlay" / "shell-raster"
    ensured = ensure_shell_raster_cache_dir(cache_dir)
    assert ensured.exists()
    assert oct(ensured.stat().st_mode & 0o777) == "0o700"


def test_shell_raster_path_validation_rejects_outside_and_accepts_cache_png(tmp_path: Path) -> None:
    cache_dir = ensure_shell_raster_cache_dir(tmp_path / "runtime" / "EDMCModernOverlay" / "shell-raster")
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"\x89PNG\r\n\x1a\n")
    inside = cache_dir / "frame.png"
    inside.write_bytes(b"\x89PNG\r\n\x1a\n")

    assert validate_shell_raster_frame_path(outside, cache_dir=cache_dir)[0] is False
    assert validate_shell_raster_frame_path(inside, cache_dir=cache_dir) == (True, "")


def test_static_shell_raster_request_is_borderless_fullscreen_only(tmp_path: Path) -> None:
    request = _presentation_request()

    eligible = build_static_shell_raster_frame_request(
        _target_status(),
        request,
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        writer=_png_writer,
        session_id="test-session",
    )
    windowed = build_static_shell_raster_frame_request(
        _target_status(fullscreen=False),
        request,
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        writer=_png_writer,
    )
    not_full_monitor = build_static_shell_raster_frame_request(
        _target_status(contentRect={"x": 0, "y": 29, "width": 3440, "height": 1411}),
        request,
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        writer=_png_writer,
    )

    assert eligible.eligible is True
    assert eligible.request is not None
    assert eligible.request.action == "update"
    assert eligible.request.target_rect == HelperRect(0, 0, 3440, 1440)
    assert eligible.request.frame_rect == HelperRect(10, 10, 3420, 1420)
    assert eligible.request.stale_timeout_ms == SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS
    assert eligible.request.allow_unfocused_target is False
    assert eligible.request.diagnostics is None
    assert eligible.request.frame_version.startswith(f"{SHELL_RASTER_FRAME_VERSION}:test-session:")
    assert windowed.reason == "target_not_fullscreen"
    assert not_full_monitor.reason == "target_not_borderless_full_monitor"


def test_static_shell_raster_request_debug_metrics_and_cache_reuse(tmp_path: Path) -> None:
    calls = 0

    def writer(path: Path, width: int, height: int) -> None:
        nonlocal calls
        calls += 1
        _png_writer(path, width, height)

    first = build_static_shell_raster_frame_request(
        _target_status(),
        _presentation_request(),
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        writer=writer,
        session_id="test-session",
        include_diagnostics=True,
    )
    second = build_static_shell_raster_frame_request(
        _target_status(),
        _presentation_request(),
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        writer=writer,
        session_id="test-session",
        include_diagnostics=True,
    )

    assert calls == 1
    assert first.request is not None
    assert second.request is not None
    assert first.request.signature() == second.request.signature()
    assert first.request.diagnostics is not None
    assert second.request.diagnostics is not None
    assert first.request.diagnostics["transport"] == SHELL_RASTER_FRAME_TRANSPORT_PNG_PATH
    assert first.request.diagnostics["cache_hit"] is False
    assert second.request.diagnostics["cache_hit"] is True
    assert second.request.diagnostics["encode_ms"] == 0.0
    assert second.request.diagnostics["checksum_ms"] == 0.0

    payload = second.request.to_payload()
    assert payload["shell_raster_frame_diagnostics"] == dict(second.request.diagnostics)


def test_shell_raster_frame_version_includes_session_and_sanitized_digest() -> None:
    version = shell_raster_frame_version("abc123456789xxxx", session_id="test/session:1")

    assert version == f"{SHELL_RASTER_FRAME_VERSION}:test-session-1:abc123456789"
    assert shell_raster_session_id()


def test_static_shell_raster_request_rejects_hidden_degrade_and_frame_fallback(
    tmp_path: Path,
) -> None:
    hidden = build_static_shell_raster_frame_request(
        _target_status(minimized=True),
        _presentation_request(),
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        writer=_png_writer,
    )
    degrade = build_static_shell_raster_frame_request(
        _target_status(),
        HelperPresentationRequest(action=HelperPresentationAction.DEGRADE),
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        writer=_png_writer,
    )
    fallback = build_static_shell_raster_frame_request(
        _target_status(),
        HelperPresentationRequest(
            action=HelperPresentationAction.ATTACH,
            target_token="meta:21",
            content_rect=HelperRect(0, 0, 3440, 1440),
            rect_source="frame_rect_fallback",
        ),
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        writer=_png_writer,
    )

    assert hidden.reason == "target_minimized"
    assert degrade.reason == "not_attach_action"
    assert fallback.reason == "not_content_rect_source"
