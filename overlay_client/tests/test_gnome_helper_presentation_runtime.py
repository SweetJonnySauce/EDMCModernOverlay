from __future__ import annotations

import sys
import types

import pytest

try:  # pragma: no cover - exercised when PyQt6 is present
    from PyQt6 import QtGui as _QtGui  # noqa: F401
except Exception:  # pragma: no cover - lightweight stub path
    if "PyQt6" not in sys.modules:
        sys.modules["PyQt6"] = types.ModuleType("PyQt6")
    qtgui = sys.modules.get("PyQt6.QtGui") or types.ModuleType("PyQt6.QtGui")
    qtgui.QGuiApplication = getattr(
        qtgui,
        "QGuiApplication",
        type(
            "QGuiApplication",
            (),
            {
                "platformName": staticmethod(lambda: "wayland"),
                "screens": staticmethod(lambda: []),
            },
        ),
    )
    qtgui.QWindow = getattr(qtgui, "QWindow", object)
    sys.modules["PyQt6.QtGui"] = qtgui

    qtwidgets = sys.modules.get("PyQt6.QtWidgets") or types.ModuleType("PyQt6.QtWidgets")
    qtwidgets.QWidget = getattr(qtwidgets, "QWidget", object)
    sys.modules["PyQt6.QtWidgets"] = qtwidgets

    qtcore = sys.modules.get("PyQt6.QtCore") or types.ModuleType("PyQt6.QtCore")
    qtcore.Qt = getattr(qtcore, "Qt", type("Qt", (), {}))
    sys.modules["PyQt6.QtCore"] = qtcore

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
from overlay_client.backend.bundles._gnome_shell_helper_presentation import (
    GnomeHelperPresentationRuntimeState,
    run_gnome_shell_helper_presentation_cycle,
)


class _Clock:
    def __init__(self, now: float = 100.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


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


def test_presentation_cycle_skips_fresh_matching_apply_for_same_signature() -> None:
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    presentation_calls: list[HelperPresentationRequest] = []

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        presentation_calls.append(request)
        return _presentation_payload(request)

    first = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=_target_payload,
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )
    clock.now += 0.5
    second = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=_target_payload,
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )

    assert first.attempts == 1
    assert second.attempts == 0
    assert second.presentation_skipped is True
    assert second.presentation_skip_reason == "fresh_matching_presentation"
    assert second.target_poll_skipped is False
    assert len(presentation_calls) == 1


def test_presentation_cycle_bypasses_skip_when_requested_rect_changes() -> None:
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    target_payloads = [
        _target_payload(),
        _target_payload(_target_window(contentRect={"x": 1200, "y": 300, "width": 1024, "height": 768})),
    ]
    presentation_calls: list[HelperPresentationRequest] = []

    def fetch_target() -> dict[str, object]:
        return target_payloads.pop(0)

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        presentation_calls.append(request)
        return _presentation_payload(request)

    run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=fetch_target,
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )
    clock.now += 0.5
    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=fetch_target,
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )

    assert result.presentation_skipped is False
    assert result.attempts == 1
    assert len(presentation_calls) == 2


def test_presentation_cycle_does_not_skip_after_applied_rect_mismatch() -> None:
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    presentation_calls: list[HelperPresentationRequest] = []

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        presentation_calls.append(request)
        if len(presentation_calls) == 1:
            return _presentation_payload(
                request,
                applied_rect={"x": 0, "y": 0, "width": 10, "height": 10},
            )
        return _presentation_payload(request)

    first = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=_target_payload,
        fetch_presentation=fetch_presentation,
        clock=clock,
        max_attempts=1,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )
    clock.now += 0.5
    second = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=_target_payload,
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )

    assert first.presentation_status is not None
    assert first.presentation_status.rect_match is False
    assert second.presentation_skipped is False
    assert len(presentation_calls) == 2


def test_presentation_cycle_focused_same_signature_skips_after_old_freshness_window() -> None:
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    target_calls = 0
    presentation_calls: list[HelperPresentationRequest] = []

    def fetch_target() -> dict[str, object]:
        nonlocal target_calls
        target_calls += 1
        return _target_payload()

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        presentation_calls.append(request)
        return _presentation_payload(request)

    run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=fetch_target,
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )
    clock.now += 12.0
    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=fetch_target,
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )

    assert result.presentation_skipped is True
    assert result.presentation_skip_reason == "fresh_matching_presentation"
    assert result.target_poll_skipped is False
    assert target_calls == 2
    assert len(presentation_calls) == 1


def test_presentation_cycle_suppressed_target_poll_throttles_without_timed_reapply() -> None:
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    target_calls = 0
    presentation_calls: list[HelperPresentationRequest] = []

    def fetch_target() -> dict[str, object]:
        nonlocal target_calls
        target_calls += 1
        return _target_payload(_target_window(hasFocus=False))

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        presentation_calls.append(request)
        return _presentation_payload(request)

    run_gnome_shell_helper_presentation_cycle(
        previous_surface_action="mapped_suppressed",
        fetch_health=_health_payload,
        fetch_target=fetch_target,
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )
    clock.now += 1.0
    throttled = run_gnome_shell_helper_presentation_cycle(
        previous_surface_action="mapped_suppressed",
        fetch_health=_health_payload,
        fetch_target=fetch_target,
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )
    clock.now += 0.6
    fresh_apply_skip = run_gnome_shell_helper_presentation_cycle(
        previous_surface_action="mapped_suppressed",
        fetch_health=_health_payload,
        fetch_target=fetch_target,
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )

    assert throttled.presentation_skipped is True
    assert throttled.presentation_skip_reason == "suppressed_poll_throttle"
    assert throttled.target_poll_skipped is True
    assert fresh_apply_skip.presentation_skipped is True
    assert fresh_apply_skip.presentation_skip_reason == "fresh_matching_presentation"
    assert fresh_apply_skip.target_poll_skipped is False
    assert target_calls == 2
    assert len(presentation_calls) == 1

    clock.now += 0.9
    after_old_suppressed_window = run_gnome_shell_helper_presentation_cycle(
        previous_surface_action="mapped_suppressed",
        fetch_health=_health_payload,
        fetch_target=fetch_target,
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )

    assert after_old_suppressed_window.presentation_skipped is True
    assert after_old_suppressed_window.presentation_skip_reason == "suppressed_poll_throttle"
    assert after_old_suppressed_window.target_poll_skipped is True
    assert target_calls == 2
    assert len(presentation_calls) == 1

    clock.now += 1.0
    after_next_poll_interval = run_gnome_shell_helper_presentation_cycle(
        previous_surface_action="mapped_suppressed",
        fetch_health=_health_payload,
        fetch_target=fetch_target,
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )

    assert after_next_poll_interval.presentation_skipped is True
    assert after_next_poll_interval.presentation_skip_reason == "fresh_matching_presentation"
    assert after_next_poll_interval.target_poll_skipped is False
    assert target_calls == 3
    assert len(presentation_calls) == 1


@pytest.mark.parametrize(
    ("target_overrides", "first_surface_action", "second_surface_action"),
    [
        ({"targetToken": "meta:22"}, "", ""),
        ({"monitorRect": {"x": 3440, "y": 0, "width": 3440, "height": 1440}}, "", ""),
        ({"hasFocus": False}, "", ""),
        ({"showingOnWorkspace": False}, "", ""),
        ({"minimized": True}, "", ""),
        ({"fullscreen": True}, "", ""),
        ({}, "", "mapped_suppressed"),
    ],
)
def test_presentation_cycle_hard_signature_changes_force_apply(
    target_overrides: dict[str, object],
    first_surface_action: str,
    second_surface_action: str,
) -> None:
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    target_payloads = [
        _target_payload(),
        _target_payload(_target_window(**target_overrides)),
    ]
    presentation_calls: list[HelperPresentationRequest] = []

    def fetch_target() -> dict[str, object]:
        return target_payloads.pop(0)

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        presentation_calls.append(request)
        return _presentation_payload(request)

    run_gnome_shell_helper_presentation_cycle(
        previous_surface_action=first_surface_action,
        fetch_health=_health_payload,
        fetch_target=fetch_target,
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )
    clock.now += 12.0
    result = run_gnome_shell_helper_presentation_cycle(
        previous_surface_action=second_surface_action,
        fetch_health=_health_payload,
        fetch_target=fetch_target,
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )

    assert result.presentation_skipped is False
    assert result.attempts == 1
    assert len(presentation_calls) == 2


def test_presentation_cycle_health_cache_hits_then_expires_with_bounded_jitter() -> None:
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    health_calls = 0
    presentation_calls: list[HelperPresentationRequest] = []

    def fetch_health() -> dict[str, object]:
        nonlocal health_calls
        health_calls += 1
        return _health_payload()

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        presentation_calls.append(request)
        return _presentation_payload(request)

    run_gnome_shell_helper_presentation_cycle(
        fetch_health=fetch_health,
        fetch_target=_target_payload,
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 99.0,
    )
    assert state.health_cache_expires_at == 105.5
    clock.now += 1.0
    cached = run_gnome_shell_helper_presentation_cycle(
        fetch_health=fetch_health,
        fetch_target=_target_payload,
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )
    clock.now = 106.0
    expired = run_gnome_shell_helper_presentation_cycle(
        fetch_health=fetch_health,
        fetch_target=_target_payload,
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )

    assert cached.health_cache_hit is True
    assert expired.health_cache_hit is False
    assert expired.presentation_skipped is True
    assert expired.presentation_skip_reason == "fresh_matching_presentation"
    assert health_calls == 2
    assert len(presentation_calls) == 1


def test_presentation_cycle_unhealthy_refresh_fails_closed_after_health_cache_expiry() -> None:
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    health_payloads = [
        _health_payload(),
        {
            **_health_payload(),
            "status": "error",
            "detail": "helper failed",
        },
    ]
    target_calls = 0

    def fetch_health() -> dict[str, object]:
        return health_payloads.pop(0)

    def fetch_target() -> dict[str, object]:
        nonlocal target_calls
        target_calls += 1
        return _target_payload()

    run_gnome_shell_helper_presentation_cycle(
        fetch_health=fetch_health,
        fetch_target=fetch_target,
        fetch_presentation=_presentation_payload,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )
    clock.now = 106.0
    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=fetch_health,
        fetch_target=fetch_target,
        fetch_presentation=_presentation_payload,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )

    assert result.helper_healthy is False
    assert result.presentation_status is None
    assert result.target_status is None
    assert target_calls == 1
