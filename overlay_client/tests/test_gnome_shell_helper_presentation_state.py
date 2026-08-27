import json

import pytest

from overlay_client.backend import (
    GNOME_SHELL_HELPER_CAPABILITIES,
    GNOME_SHELL_HELPER_COORDINATE_SPACE,
    GNOME_SHELL_HELPER_RECT_REASON_FRAME_FALLBACK_CLAMPED,
    GNOME_SHELL_HELPER_RECT_REASON_FRAME_FALLBACK_OUTSIDE_MONITOR,
    GNOME_SHELL_HELPER_RECT_SOURCE_CONTENT,
    GNOME_SHELL_HELPER_RECT_SOURCE_FRAME_FALLBACK,
    HELPER_KIND,
    HELPER_PROTOCOL,
    HELPER_VERSION,
    HelperDbusServiceMissing,
    HelperPresentationAction,
    HelperPresentationRequest,
    HelperPresentationState,
    HelperRasterFrameRequest,
    HelperRect,
    HelperTargetState,
    build_gnome_shell_helper_presentation_request,
    probe_gnome_shell_helper_presentation,
    validate_gnome_shell_helper_health_payload,
    validate_gnome_shell_helper_presentation_payload,
    validate_gnome_shell_helper_target_payload,
)


def _health_status(**overrides: object):
    payload: dict[str, object] = {
        "status": "healthy",
        "helper_kind": HELPER_KIND.value,
        "helper_version": HELPER_VERSION,
        "helper_protocol": HELPER_PROTOCOL,
        "capabilities": list(GNOME_SHELL_HELPER_CAPABILITIES),
    }
    payload.update(overrides)
    return validate_gnome_shell_helper_health_payload(
        payload,
        observed_at_monotonic=100.0,
        now_monotonic=100.0,
    )


def _target_window(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "targetToken": "meta:21",
        "title": "Elite - Dangerous (CLIENT)",
        "wmClass": "steam_app_359320",
        "wmClassInstance": "steam_app_359320",
        "appId": "steam_app_359320",
        "appName": "steam_app_359320",
        "pid": 9135,
        "windowType": 0,
        "frameRect": {"x": 1080, "y": 216, "width": 1280, "height": 997},
        "bufferRect": {"x": 1066, "y": 204, "width": 1308, "height": 1026},
        "contentRect": {"x": 1080, "y": 253, "width": 1280, "height": 960},
        "decorationInsets": {"left": 0, "top": 37, "right": 0, "bottom": 0},
        "monitor": 0,
        "outputName": "DP-2",
        "monitorRect": {"x": 0, "y": 0, "width": 3440, "height": 1440},
        "monitorScale": 1.0,
        "hasFocus": True,
        "showingOnWorkspace": True,
        "minimized": False,
        "fullscreen": False,
        "workspace": "0",
    }
    payload.update(overrides)
    return payload


def _target_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
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
        "target": _target_window(),
    }
    payload.update(overrides)
    return payload


def _target_status(**overrides: object):
    return validate_gnome_shell_helper_target_payload(
        _target_payload(**overrides),
        health_status=_health_status(),
        observed_at_monotonic=200.0,
        now_monotonic=200.0,
    )


def _presentation_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "status": "presentation_applied",
        "helper_kind": HELPER_KIND.value,
        "helper_version": HELPER_VERSION,
        "helper_protocol": HELPER_PROTOCOL,
        "coordinate_space": GNOME_SHELL_HELPER_COORDINATE_SPACE,
        "action": "attach",
        "target_token": "meta:21",
        "overlay_token": "overlay:1",
        "requested_rect": {"x": 1080, "y": 253, "width": 1280, "height": 960},
        "applied_rect": {"x": 1080, "y": 253, "width": 1280, "height": 960},
        "renderer": "pyqt",
        "placement": True,
        "chrome_free": True,
        "stacking": True,
        "click_through": True,
        "focus_safe": True,
        "standalone_mode": False,
        "unsupported_features": [],
        "degrade_reasons": [],
        "sequence": 4,
        "generated_at_monotonic_us": 123500,
        "generated_at_unix_ms": 1800000000500,
    }
    payload.update(overrides)
    return payload


def test_build_presentation_request_uses_target_content_rect_and_pyqt_renderer() -> None:
    target = _target_status()

    request = build_gnome_shell_helper_presentation_request(target)

    assert request.action is HelperPresentationAction.ATTACH
    assert request.target_token == "meta:21"
    assert request.renderer == "pyqt"
    assert request.content_rect == HelperRect(x=1080, y=253, width=1280, height=960)
    assert request.rect_source == GNOME_SHELL_HELPER_RECT_SOURCE_CONTENT
    assert request.standalone_mode is False
    assert request.require_chrome_free is True
    assert request.require_click_through is True
    assert request.to_payload()["click_through_expected"] is True


def test_build_presentation_request_hides_when_target_is_not_on_workspace() -> None:
    target = _target_status(target=_target_window(showingOnWorkspace=False))

    request = build_gnome_shell_helper_presentation_request(target)

    assert request.action is HelperPresentationAction.HIDE
    assert request.degrade_reasons == ("target_hidden",)


def test_build_presentation_request_uses_frame_rect_fallback_when_content_rect_is_missing() -> None:
    target_window = _target_window(contentRect=None, decorationInsets=None)
    target = _target_status(target=target_window)

    request = build_gnome_shell_helper_presentation_request(target)

    assert request.action is HelperPresentationAction.ATTACH
    assert request.content_rect == HelperRect(x=1080, y=216, width=1280, height=997)
    assert request.rect_source == GNOME_SHELL_HELPER_RECT_SOURCE_FRAME_FALLBACK
    assert request.degrade_reasons == (GNOME_SHELL_HELPER_RECT_SOURCE_FRAME_FALLBACK,)


def test_build_presentation_request_keeps_content_rect_preferred_even_outside_monitor() -> None:
    target = _target_status(
        target=_target_window(
            contentRect={"x": 1080, "y": 253, "width": 1280, "height": 1600},
            monitorRect={"x": 0, "y": 0, "width": 3440, "height": 1440},
        )
    )

    request = build_gnome_shell_helper_presentation_request(target)

    assert request.action is HelperPresentationAction.ATTACH
    assert request.content_rect == HelperRect(x=1080, y=253, width=1280, height=1600)
    assert request.rect_source == GNOME_SHELL_HELPER_RECT_SOURCE_CONTENT
    assert request.degrade_reasons == ()


def test_build_presentation_request_clamps_frame_rect_fallback_to_monitor_bounds() -> None:
    target = _target_status(
        target=_target_window(
            frameRect={"x": 760, "y": 29, "width": 1920, "height": 1477},
            bufferRect={"x": 746, "y": 17, "width": 1948, "height": 1506},
            contentRect=None,
            decorationInsets=None,
            monitorRect={"x": 0, "y": 0, "width": 3440, "height": 1440},
        )
    )

    request = build_gnome_shell_helper_presentation_request(target)

    assert request.action is HelperPresentationAction.ATTACH
    assert request.content_rect == HelperRect(x=760, y=29, width=1920, height=1411)
    assert request.rect_source == GNOME_SHELL_HELPER_RECT_SOURCE_FRAME_FALLBACK
    assert request.degrade_reasons == (
        GNOME_SHELL_HELPER_RECT_SOURCE_FRAME_FALLBACK,
        GNOME_SHELL_HELPER_RECT_REASON_FRAME_FALLBACK_CLAMPED,
    )


def test_build_presentation_request_clamps_frame_rect_fallback_on_non_primary_monitor() -> None:
    target = _target_status(
        target=_target_window(
            frameRect={"x": 3600, "y": 29, "width": 1920, "height": 1477},
            bufferRect={"x": 3586, "y": 17, "width": 1948, "height": 1506},
            contentRect=None,
            decorationInsets=None,
            monitor=1,
            outputName="HDMI-1",
            monitorRect={"x": 3440, "y": 0, "width": 3440, "height": 1440},
        )
    )

    request = build_gnome_shell_helper_presentation_request(target)

    assert request.action is HelperPresentationAction.ATTACH
    assert request.content_rect == HelperRect(x=3600, y=29, width=1920, height=1411)
    assert request.rect_source == GNOME_SHELL_HELPER_RECT_SOURCE_FRAME_FALLBACK
    assert request.degrade_reasons == (
        GNOME_SHELL_HELPER_RECT_SOURCE_FRAME_FALLBACK,
        GNOME_SHELL_HELPER_RECT_REASON_FRAME_FALLBACK_CLAMPED,
    )


def test_build_presentation_request_degrades_when_frame_fallback_misses_monitor() -> None:
    target = _target_status(
        target=_target_window(
            frameRect={"x": 3600, "y": 100, "width": 200, "height": 200},
            bufferRect={"x": 3600, "y": 100, "width": 200, "height": 200},
            contentRect=None,
            decorationInsets=None,
            monitorRect={"x": 0, "y": 0, "width": 3440, "height": 1440},
        )
    )

    request = build_gnome_shell_helper_presentation_request(target)

    assert request.action is HelperPresentationAction.DEGRADE
    assert request.content_rect is None
    assert request.rect_source == GNOME_SHELL_HELPER_RECT_SOURCE_FRAME_FALLBACK
    assert request.degrade_reasons == (
        GNOME_SHELL_HELPER_RECT_SOURCE_FRAME_FALLBACK,
        GNOME_SHELL_HELPER_RECT_REASON_FRAME_FALLBACK_OUTSIDE_MONITOR,
    )


def test_build_presentation_request_uses_frame_rect_fallback_when_monitor_rect_is_missing() -> None:
    target_window = _target_window(contentRect=None, decorationInsets=None)
    target_window.pop("monitorRect")
    target = _target_status(target=target_window)

    request = build_gnome_shell_helper_presentation_request(target)

    assert request.action is HelperPresentationAction.ATTACH
    assert request.content_rect == HelperRect(x=1080, y=216, width=1280, height=997)
    assert request.rect_source == GNOME_SHELL_HELPER_RECT_SOURCE_FRAME_FALLBACK
    assert request.degrade_reasons == (GNOME_SHELL_HELPER_RECT_SOURCE_FRAME_FALLBACK,)


def test_build_presentation_request_degrades_when_target_is_not_found() -> None:
    target = validate_gnome_shell_helper_target_payload(
        _target_payload(status="target_not_found", target=None, candidate_count=0),
        health_status=_health_status(),
        observed_at_monotonic=200.0,
        now_monotonic=200.0,
    )

    request = build_gnome_shell_helper_presentation_request(target)

    assert target.state is HelperTargetState.NOT_FOUND
    assert request.action is HelperPresentationAction.DEGRADE
    assert request.degrade_reasons == ("target_not_found",)


def test_validate_presentation_accepts_applied_state_only_when_all_gates_pass() -> None:
    target = _target_status()
    request = build_gnome_shell_helper_presentation_request(target)

    status = validate_gnome_shell_helper_presentation_payload(
        (json.dumps(_presentation_payload()),),
        health_status=_health_status(),
        target_status=target,
        request=request,
        observed_at_monotonic=210.0,
        now_monotonic=210.0,
    )

    assert status.state is HelperPresentationState.APPLIED
    assert status.applied is True
    assert status.rect_match is True
    assert status.rect_delta == (0, 0, 0, 0)
    assert status.true_overlay_ready is True
    assert status.pyqt_renderer_preserved is True


@pytest.mark.parametrize(
    ("override", "reason"),
    [
        ({"chrome_free": False}, "chrome_free_unproven"),
        ({"stacking": False}, "stacking_unproven"),
        ({"click_through": False}, "click_through_unproven"),
        ({"focus_safe": False}, "focus_safe_unproven"),
        ({"renderer": "gnome_shell"}, "renderer_changed"),
        ({"standalone_mode": True}, "standalone_mode_enabled"),
        ({"applied_rect": None}, "placement_unproven"),
        ({"applied_rect": {"x": 1084, "y": 253, "width": 1280, "height": 960}}, "applied_rect_mismatch"),
    ],
)
def test_validate_presentation_degrades_when_required_gate_is_unproven(
    override: dict[str, object],
    reason: str,
) -> None:
    target = _target_status()
    request = build_gnome_shell_helper_presentation_request(target)

    status = validate_gnome_shell_helper_presentation_payload(
        _presentation_payload(**override),
        health_status=_health_status(),
        target_status=target,
        request=request,
        observed_at_monotonic=210.0,
        now_monotonic=210.0,
    )

    assert status.state is HelperPresentationState.DEGRADED
    assert status.true_overlay_ready is False
    assert reason in status.degrade_reasons


def test_validate_presentation_accepts_applied_rect_within_tolerance() -> None:
    target = _target_status()
    request = build_gnome_shell_helper_presentation_request(target)

    status = validate_gnome_shell_helper_presentation_payload(
        _presentation_payload(applied_rect={"x": 1082, "y": 251, "width": 1281, "height": 958}),
        health_status=_health_status(),
        target_status=target,
        request=request,
        observed_at_monotonic=210.0,
        now_monotonic=210.0,
    )

    assert status.state is HelperPresentationState.APPLIED
    assert status.rect_match is True
    assert status.rect_delta == (2, -2, 1, -2)
    assert status.true_overlay_ready is True


def test_validate_presentation_keeps_normal_path_diagnostics_observational() -> None:
    target = _target_status()
    default_request = build_gnome_shell_helper_presentation_request(target)
    request = build_gnome_shell_helper_presentation_request(
        target,
        include_presentation_diagnostics=True,
    )
    diagnostics = {
        "schema": 1,
        "requestedRect": {"x": 1080, "y": 253, "width": 1280, "height": 960},
        "target": {"monitor": 0},
        "placement": {"moveResizeAction": "move_to_monitor_then_resize"},
        "before": {"monitor": 1},
        "after": {"monitor": 0},
    }

    status = validate_gnome_shell_helper_presentation_payload(
        _presentation_payload(
            applied_rect={"x": 3440, "y": 253, "width": 1280, "height": 960},
            presentation_diagnostics=diagnostics,
        ),
        health_status=_health_status(),
        target_status=target,
        request=request,
        observed_at_monotonic=210.0,
        now_monotonic=210.0,
    )

    assert "include_presentation_diagnostics" not in default_request.to_payload()
    assert request.to_payload()["include_presentation_diagnostics"] is True
    assert status.presentation_diagnostics == diagnostics
    assert status.rect_match is False
    assert status.state is HelperPresentationState.DEGRADED
    assert status.true_overlay_ready is False
    assert "applied_rect_mismatch" in status.degrade_reasons


def test_validate_presentation_accepts_shell_raster_renderer_when_requested() -> None:
    target = _target_status(
        target=_target_window(
            frameRect={"x": 0, "y": 0, "width": 3440, "height": 1440},
            bufferRect={"x": 0, "y": 0, "width": 3440, "height": 1440},
            contentRect={"x": 0, "y": 0, "width": 3440, "height": 1440},
            decorationInsets={"left": 0, "top": 0, "right": 0, "bottom": 0},
            monitorRect={"x": 0, "y": 0, "width": 3440, "height": 1440},
            fullscreen=True,
        )
    )
    frame_rect = HelperRect(24, 24, 520, 128)
    request = HelperPresentationRequest(
        action=HelperPresentationAction.ATTACH,
        target_token="meta:21",
        content_rect=HelperRect(0, 0, 3440, 1440),
        renderer="gnome_shell_raster_frame",
        shell_raster_frame=HelperRasterFrameRequest(
            action="update",
            frame_version="v1",
            target_token="meta:21",
            target_rect=HelperRect(0, 0, 3440, 1440),
            frame_rect=frame_rect,
            scale=1.0,
            image_path="/run/user/1000/EDMCModernOverlay/shell-raster/frame.png",
            checksum="abc123",
            byte_size=128,
            stale_timeout_ms=5000,
            allow_unfocused_target=True,
        ),
    )
    request_payload = request.to_payload()
    assert request_payload["allow_unfocused_target"] is True

    status = validate_gnome_shell_helper_presentation_payload(
        _presentation_payload(
            requested_rect={"x": 0, "y": 0, "width": 3440, "height": 1440},
            applied_rect=frame_rect.to_payload(),
            renderer="gnome_shell_raster_frame",
            shell_raster_frame={
                "frame_version": "v1",
                "frame_rect": frame_rect.to_payload(),
                "frame_dimensions": {"x": 0, "y": 0, "width": 520, "height": 128},
                "cleanup_action": "",
                "allow_unfocused_target": True,
            },
        ),
        health_status=_health_status(),
        target_status=target,
        request=request,
        observed_at_monotonic=210.0,
        now_monotonic=210.0,
    )

    assert status.state is HelperPresentationState.APPLIED
    assert status.pyqt_renderer_preserved is True
    assert status.requested_rect == HelperRect(0, 0, 3440, 1440)
    assert status.applied_rect == frame_rect
    assert status.rect_match is True
    assert status.rect_delta == (0, 0, 0, 0)
    assert status.true_overlay_ready is False
    assert status.shell_raster_frame is not None
    assert status.shell_raster_frame["allow_unfocused_target"] is True
    assert status.frame_version == "v1"
    assert status.frame_rect == frame_rect
    assert status.frame_dimensions == HelperRect(0, 0, 520, 128)


def test_validate_presentation_degrades_frame_rect_fallback_even_when_applied_rect_matches() -> None:
    target = _target_status(target=_target_window(contentRect=None, decorationInsets=None))
    request = build_gnome_shell_helper_presentation_request(target)

    status = validate_gnome_shell_helper_presentation_payload(
        _presentation_payload(
            requested_rect={"x": 1080, "y": 216, "width": 1280, "height": 997},
            applied_rect={"x": 1080, "y": 216, "width": 1280, "height": 997},
        ),
        health_status=_health_status(),
        target_status=target,
        request=request,
        observed_at_monotonic=210.0,
        now_monotonic=210.0,
    )

    assert status.state is HelperPresentationState.DEGRADED
    assert status.rect_source == GNOME_SHELL_HELPER_RECT_SOURCE_FRAME_FALLBACK
    assert status.rect_match is True
    assert GNOME_SHELL_HELPER_RECT_SOURCE_FRAME_FALLBACK in status.degrade_reasons
    assert status.true_overlay_ready is False


def test_validate_presentation_reports_unsupported_and_target_unavailable() -> None:
    missing_target = validate_gnome_shell_helper_target_payload(
        _target_payload(status="target_not_found", target=None, candidate_count=0),
        health_status=_health_status(),
        observed_at_monotonic=200.0,
        now_monotonic=200.0,
    )
    attach_request = HelperPresentationRequest(
        action=HelperPresentationAction.ATTACH,
        target_token="meta:missing",
        content_rect=HelperRect(0, 0, 100, 100),
    )

    unavailable = validate_gnome_shell_helper_presentation_payload(
        _presentation_payload(status="presentation_unsupported", unsupported_features=["make_above"]),
        health_status=_health_status(),
        target_status=missing_target,
        request=attach_request,
        observed_at_monotonic=210.0,
        now_monotonic=210.0,
    )

    assert unavailable.state is HelperPresentationState.TARGET_UNAVAILABLE
    assert unavailable.true_overlay_ready is False

    target = _target_status()
    unsupported = validate_gnome_shell_helper_presentation_payload(
        _presentation_payload(status="presentation_unsupported", unsupported_features=["make_above"]),
        health_status=_health_status(),
        target_status=target,
        request=build_gnome_shell_helper_presentation_request(target),
        observed_at_monotonic=210.0,
        now_monotonic=210.0,
    )

    assert unsupported.state is HelperPresentationState.UNSUPPORTED
    assert unsupported.unsupported_features == ("make_above",)
    assert unsupported.true_overlay_ready is False


def test_validate_presentation_fails_closed_for_unhealthy_stale_and_malformed_payloads() -> None:
    target = _target_status()
    request = build_gnome_shell_helper_presentation_request(target)

    unhealthy = validate_gnome_shell_helper_presentation_payload(
        _presentation_payload(),
        health_status=_health_status(status="inactive"),
        target_status=target,
        request=request,
        observed_at_monotonic=210.0,
        now_monotonic=210.0,
    )
    stale = validate_gnome_shell_helper_presentation_payload(
        _presentation_payload(),
        health_status=_health_status(),
        target_status=target,
        request=request,
        observed_at_monotonic=210.0,
        now_monotonic=213.0,
        stale_after_seconds=2.0,
    )
    malformed = validate_gnome_shell_helper_presentation_payload(
        "not-json",
        health_status=_health_status(),
        target_status=target,
        request=request,
        observed_at_monotonic=210.0,
        now_monotonic=210.0,
    )

    assert unhealthy.state is HelperPresentationState.HELPER_UNHEALTHY
    assert unhealthy.true_overlay_ready is False
    assert stale.state is HelperPresentationState.STALE
    assert stale.is_stale(213.0) is True
    assert stale.true_overlay_ready is False
    assert malformed.state is HelperPresentationState.MALFORMED_PAYLOAD
    assert malformed.true_overlay_ready is False


def test_probe_presentation_maps_missing_service_to_unhealthy() -> None:
    target = _target_status()
    request = build_gnome_shell_helper_presentation_request(target)

    def fetch_presentation(_request: HelperPresentationRequest) -> object:
        raise HelperDbusServiceMissing("service not owned")

    status = probe_gnome_shell_helper_presentation(
        fetch_presentation,
        health_status=_health_status(),
        target_status=target,
        request=request,
        clock=lambda: 210.0,
    )

    assert status.state is HelperPresentationState.HELPER_UNHEALTHY
    assert status.true_overlay_ready is False
    assert "missing_service" in status.degrade_reasons
