from __future__ import annotations

from overlay_client.backend import (
    GNOME_SHELL_HELPER_CAPABILITIES,
    GNOME_SHELL_HELPER_COORDINATE_SPACE,
    GNOME_SHELL_HELPER_RECT_SOURCE_FRAME_FALLBACK,
    HELPER_KIND,
    HELPER_PROTOCOL,
    HELPER_VERSION,
    HelperPresentationRequest,
    HelperPresentationState,
)
from overlay_client.backend.bundles._gnome_shell_helper_presentation import run_gnome_shell_helper_presentation_cycle


def _health_payload() -> dict[str, object]:
    return {
        "status": "healthy",
        "helper_kind": HELPER_KIND.value,
        "helper_version": HELPER_VERSION,
        "helper_protocol": HELPER_PROTOCOL,
        "capabilities": list(GNOME_SHELL_HELPER_CAPABILITIES),
    }


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
        "monitorScale": 1.0,
        "hasFocus": True,
        "showingOnWorkspace": True,
        "minimized": False,
        "fullscreen": False,
        "workspace": "0",
    }
    payload.update(overrides)
    return payload


def _target_payload(target: dict[str, object] | None = None) -> dict[str, object]:
    return {
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
        "target": target or _target_window(),
    }


def _presentation_payload(request: HelperPresentationRequest, **overrides: object) -> dict[str, object]:
    rect = request.content_rect
    assert rect is not None
    payload: dict[str, object] = {
        "status": "presentation_applied",
        "helper_kind": HELPER_KIND.value,
        "helper_version": HELPER_VERSION,
        "helper_protocol": HELPER_PROTOCOL,
        "coordinate_space": GNOME_SHELL_HELPER_COORDINATE_SPACE,
        "action": request.action.value,
        "target_token": request.target_token,
        "overlay_token": "overlay:1",
        "requested_rect": rect.to_payload(),
        "applied_rect": rect.to_payload(),
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


def test_presentation_cycle_retries_once_when_applied_rect_readback_lags() -> None:
    calls: list[HelperPresentationRequest] = []

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        calls.append(request)
        if len(calls) == 1:
            return _presentation_payload(
                request,
                applied_rect={"x": 0, "y": 29, "width": 1280, "height": 960},
            )
        return _presentation_payload(request)

    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=_target_payload,
        fetch_presentation=fetch_presentation,
        clock=lambda: 100.0,
    )

    assert result.attempts == 2
    assert result.retry_reasons == ("applied_rect_mismatch",)
    assert result.presentation_status is not None
    assert result.presentation_status.state is HelperPresentationState.APPLIED
    assert result.presentation_status.rect_match is True
    assert result.presentation_ready is True
    assert len(calls) == 2


def test_presentation_cycle_does_not_retry_frame_rect_fallback_degrade() -> None:
    target = _target_window(contentRect=None, decorationInsets=None)
    calls: list[HelperPresentationRequest] = []

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        calls.append(request)
        return _presentation_payload(request)

    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(target),
        fetch_presentation=fetch_presentation,
        clock=lambda: 100.0,
    )

    assert result.attempts == 1
    assert result.retry_reasons == ()
    assert result.request is not None
    assert result.request.rect_source == GNOME_SHELL_HELPER_RECT_SOURCE_FRAME_FALLBACK
    assert result.presentation_status is not None
    assert result.presentation_status.state is HelperPresentationState.DEGRADED
    assert result.presentation_status.rect_match is True
    assert result.presentation_ready is False
    assert len(calls) == 1
