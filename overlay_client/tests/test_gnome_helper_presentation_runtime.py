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
                "screenAt": staticmethod(lambda _point: None),
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
    HelperRasterFrameRequest,
    HelperRect,
)
from overlay_client.backend.bundles._gnome_shell_helper_presentation import (
    GNOME_HELPER_BORDERLESS_FULLSCREEN_PREP_ENV,
    GNOME_HELPER_GEOMETRY_DIAGNOSTICS_ENV,
    GNOME_HELPER_PRESENTATION_DIAGNOSTICS_ENV,
    GNOME_HELPER_REASON_PERSISTENT_APPLIED_RECT_MISMATCH,
    GNOME_HELPER_REASON_SURFACE_PREPARATION_FAILED,
    GNOME_HELPER_REASON_WRONG_MONITOR_APPLIED_RECT,
    GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV,
    GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV,
    GNOME_HELPER_SURFACE_PREPARATION_FULLSCREEN_MONITOR,
    GnomeHelperPresentationRuntimeState,
    build_shell_raster_frame_clear_request,
    clear_gnome_shell_raster_frame_via_gdbus,
    _target_query_payload,
    run_gnome_shell_helper_presentation_cycle,
)
from overlay_client.backend.shell_raster_frame import (
    SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS,
    ShellRasterFrameBuildResult,
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


def _borderless_target(**overrides: object) -> dict[str, object]:
    payload = _target_window(
        frameRect={"x": 0, "y": 0, "width": 3440, "height": 1440},
        bufferRect={"x": 0, "y": 0, "width": 3440, "height": 1440},
        contentRect={"x": 0, "y": 0, "width": 3440, "height": 1440},
        decorationInsets={"left": 0, "top": 0, "right": 0, "bottom": 0},
        monitorRect={"x": 0, "y": 0, "width": 3440, "height": 1440},
        fullscreen=True,
    )
    payload.update(overrides)
    return payload


def _wrong_monitor_presentation_payload(request: HelperPresentationRequest) -> dict[str, object]:
    return _presentation_payload(
        request,
        applied_rect={"x": 3440, "y": 0, "width": 3440, "height": 1440},
    )


def _work_area_offset_presentation_payload(request: HelperPresentationRequest) -> dict[str, object]:
    return _presentation_payload(
        request,
        applied_rect={"x": 0, "y": 29, "width": 3440, "height": 1440},
    )


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


def test_presentation_cycle_tracks_persistent_wrong_monitor_mismatch_and_backs_off() -> None:
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    presentation_calls: list[HelperPresentationRequest] = []

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        presentation_calls.append(request)
        return _wrong_monitor_presentation_payload(request)

    first = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )
    clock.now += 0.5
    second = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )
    clock.now += 0.5
    third = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )

    assert first.attempts == 2
    assert first.presentation_status is not None
    assert GNOME_HELPER_REASON_WRONG_MONITOR_APPLIED_RECT in first.presentation_status.degrade_reasons
    assert GNOME_HELPER_REASON_PERSISTENT_APPLIED_RECT_MISMATCH not in first.presentation_status.degrade_reasons
    assert first.persistent_mismatch_count == 1

    assert second.attempts == 2
    assert second.presentation_status is not None
    assert GNOME_HELPER_REASON_WRONG_MONITOR_APPLIED_RECT in second.presentation_status.degrade_reasons
    assert GNOME_HELPER_REASON_PERSISTENT_APPLIED_RECT_MISMATCH in second.presentation_status.degrade_reasons
    assert second.persistent_mismatch_count == 2

    assert third.attempts == 0
    assert third.presentation_skipped is True
    assert third.presentation_skip_reason == GNOME_HELPER_REASON_PERSISTENT_APPLIED_RECT_MISMATCH
    assert third.persistent_mismatch_backoff is True
    assert third.should_show_overlay is True
    assert third.presentation_status is not None
    assert GNOME_HELPER_REASON_PERSISTENT_APPLIED_RECT_MISMATCH in third.presentation_status.degrade_reasons
    assert len(presentation_calls) == 4


def test_persistent_wrong_monitor_backoff_preserves_mapped_suppressed_visibility_policy() -> None:
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    target = _borderless_target(hasFocus=False)
    presentation_calls: list[HelperPresentationRequest] = []

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        presentation_calls.append(request)
        return _wrong_monitor_presentation_payload(request)

    for _ in range(2):
        run_gnome_shell_helper_presentation_cycle(
            previous_surface_action="mapped_suppressed",
            fetch_health=_health_payload,
            fetch_target=lambda: _target_payload(target),
            fetch_presentation=fetch_presentation,
            clock=clock,
            runtime_state=state,
            health_cache_jitter_seconds=lambda: 0.0,
        )
        clock.now += 0.5

    backed_off = run_gnome_shell_helper_presentation_cycle(
        previous_surface_action="mapped_suppressed",
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(target),
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )

    assert backed_off.presentation_skipped is True
    assert backed_off.presentation_skip_reason == GNOME_HELPER_REASON_PERSISTENT_APPLIED_RECT_MISMATCH
    assert backed_off.target_found is True
    assert backed_off.should_show_overlay is True
    assert backed_off.target_status is not None
    assert backed_off.target_status.target is not None
    assert backed_off.target_status.target.has_focus is False
    assert len(presentation_calls) == 4


def test_borderless_fullscreen_prep_is_dev_gated(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(GNOME_HELPER_BORDERLESS_FULLSCREEN_PREP_ENV, raising=False)
    surface_preparations = []

    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=_presentation_payload,
        prepare_surface=lambda request: surface_preparations.append(request) or True,
        clock=lambda: 100.0,
    )

    assert result.presentation_status is not None
    assert result.presentation_status.rect_match is True
    assert surface_preparations == []
    assert result.surface_preparation is None


def test_borderless_fullscreen_prep_runs_before_helper_presentation_when_eligible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(GNOME_HELPER_BORDERLESS_FULLSCREEN_PREP_ENV, "1")
    events: list[str] = []

    def prepare_surface(preparation) -> bool:
        events.append("prepare")
        assert preparation.mode == GNOME_HELPER_SURFACE_PREPARATION_FULLSCREEN_MONITOR
        assert preparation.rect == (0, 0, 3440, 1440)
        assert preparation.target_token == "meta:21"
        assert preparation.rect_source == "content_rect"
        return True

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        events.append("presentation")
        return _presentation_payload(request)

    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        prepare_surface=prepare_surface,
        clock=lambda: 100.0,
    )

    assert events == ["prepare", "presentation"]
    assert result.surface_preparation is not None
    assert result.surface_preparation.mode == GNOME_HELPER_SURFACE_PREPARATION_FULLSCREEN_MONITOR
    assert result.presentation_status is not None
    assert result.presentation_status.rect_match is True


@pytest.mark.parametrize(
    "target",
    [
        _target_window(contentRect=None, decorationInsets=None),
        _borderless_target(fullscreen=False),
        _borderless_target(contentRect={"x": 0, "y": 29, "width": 3440, "height": 1411}),
        _borderless_target(monitorRect={"x": 3440, "y": 0, "width": 3440, "height": 1440}),
    ],
)
def test_borderless_fullscreen_prep_is_not_eligible_for_non_full_monitor_attach(
    monkeypatch: pytest.MonkeyPatch,
    target: dict[str, object],
) -> None:
    monkeypatch.setenv(GNOME_HELPER_BORDERLESS_FULLSCREEN_PREP_ENV, "1")
    surface_preparations = []

    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(target),
        fetch_presentation=_presentation_payload,
        prepare_surface=lambda request: surface_preparations.append(request) or True,
        clock=lambda: 100.0,
    )

    assert surface_preparations == []
    assert result.surface_preparation is None


def test_borderless_fullscreen_prep_is_not_eligible_for_hidden_action(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(GNOME_HELPER_BORDERLESS_FULLSCREEN_PREP_ENV, "1")
    surface_preparations = []
    presentation_calls: list[HelperPresentationRequest] = []

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        presentation_calls.append(request)
        return {
            **_presentation_payload(request),
            "status": "presentation_hidden",
            "action": request.action.value,
            "applied_rect": None,
            "placement": False,
            "chrome_free": False,
            "stacking": False,
            "click_through": False,
            "focus_safe": False,
            "degrade_reasons": ["target_hidden"],
        }

    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target(minimized=True)),
        fetch_presentation=fetch_presentation,
        prepare_surface=lambda request: surface_preparations.append(request) or True,
        clock=lambda: 100.0,
    )

    assert surface_preparations == []
    assert result.surface_preparation is None
    assert presentation_calls


def test_borderless_fullscreen_prep_failure_does_not_call_helper_presentation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(GNOME_HELPER_BORDERLESS_FULLSCREEN_PREP_ENV, "1")
    presentation_calls: list[HelperPresentationRequest] = []

    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=lambda request: presentation_calls.append(request) or _presentation_payload(request),
        prepare_surface=lambda _request: False,
        clock=lambda: 100.0,
    )

    assert presentation_calls == []
    assert result.surface_preparation_failed is True
    assert result.presentation_status is not None
    assert result.presentation_status.state is HelperPresentationState.DEGRADED
    assert GNOME_HELPER_REASON_SURFACE_PREPARATION_FAILED in result.presentation_status.degrade_reasons
    assert result.should_show_overlay is True


def test_borderless_fullscreen_prep_mismatch_backs_off_without_wrong_monitor_reason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(GNOME_HELPER_BORDERLESS_FULLSCREEN_PREP_ENV, "1")
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    presentation_calls: list[HelperPresentationRequest] = []

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        presentation_calls.append(request)
        return _work_area_offset_presentation_payload(request)

    for _ in range(2):
        run_gnome_shell_helper_presentation_cycle(
            fetch_health=_health_payload,
            fetch_target=lambda: _target_payload(_borderless_target()),
            fetch_presentation=fetch_presentation,
            prepare_surface=lambda _request: True,
            clock=clock,
            runtime_state=state,
            health_cache_jitter_seconds=lambda: 0.0,
        )
        clock.now += 0.5

    backed_off = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        prepare_surface=lambda _request: True,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )

    assert backed_off.presentation_skipped is True
    assert backed_off.presentation_skip_reason == GNOME_HELPER_REASON_PERSISTENT_APPLIED_RECT_MISMATCH
    assert backed_off.presentation_status is not None
    assert GNOME_HELPER_REASON_PERSISTENT_APPLIED_RECT_MISMATCH in backed_off.presentation_status.degrade_reasons
    assert GNOME_HELPER_REASON_WRONG_MONITOR_APPLIED_RECT not in backed_off.presentation_status.degrade_reasons
    assert len(presentation_calls) == 4


def test_shell_raster_bridge_is_env_gated(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, raising=False)
    monkeypatch.delenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, raising=False)
    calls: list[HelperPresentationRequest] = []

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        calls.append(request)
        return _presentation_payload(request)

    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        clock=lambda: 100.0,
    )

    assert result.presentation_status is not None
    assert calls
    assert calls[0].shell_raster_frame is None
    assert calls[0].renderer == "pyqt"

    calls.clear()
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, "1")

    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        clock=lambda: 101.0,
    )

    assert result.presentation_status is not None
    assert calls
    assert calls[0].shell_raster_frame is None
    assert calls[0].renderer == "pyqt"


def test_shell_raster_bridge_passes_debug_metrics_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, "1")
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, "1")
    monkeypatch.setenv(GNOME_HELPER_PRESENTATION_DIAGNOSTICS_ENV, "1")
    seen: dict[str, object] = {}

    def fake_builder(*_args, **kwargs) -> ShellRasterFrameBuildResult:
        seen["include_diagnostics"] = kwargs.get("include_diagnostics")
        return ShellRasterFrameBuildResult(reason="not_built")

    monkeypatch.setattr(
        "overlay_client.backend.bundles._gnome_shell_helper_presentation.build_static_shell_raster_frame_request",
        fake_builder,
    )

    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=lambda request: _presentation_payload(request),
        clock=lambda: 100.0,
    )

    assert result.presentation_status is not None
    assert seen["include_diagnostics"] is True


def test_shell_raster_bridge_sends_static_frame_when_eligible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, "1")
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, "1")
    frame_request = HelperRasterFrameRequest(
        action="update",
        frame_version="phase13-static-pyqt-proof-v1:test-session:abc123",
        target_token="meta:21",
        target_rect=HelperRect(0, 0, 3440, 1440),
        frame_rect=HelperRect(24, 24, 520, 128),
        scale=1.0,
        image_path="/run/user/1000/EDMCModernOverlay/shell-raster/frame.png",
        checksum="abc123",
        byte_size=128,
        stale_timeout_ms=SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS,
    )

    monkeypatch.setattr(
        "overlay_client.backend.bundles._gnome_shell_helper_presentation.build_static_shell_raster_frame_request",
        lambda *_args, **_kwargs: ShellRasterFrameBuildResult(request=frame_request, eligible=True),
    )
    calls: list[HelperPresentationRequest] = []

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        calls.append(request)
        return _presentation_payload(
            request,
            applied_rect=frame_request.frame_rect.to_payload(),
            renderer="gnome_shell_raster_frame",
            shell_raster_frame={
                "frame_version": frame_request.frame_version,
                "frame_rect": frame_request.frame_rect.to_payload(),
                "frame_dimensions": {"x": 0, "y": 0, "width": 520, "height": 128},
                "session_id": "test-session",
            },
        )

    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        clock=lambda: 100.0,
    )

    assert result.presentation_status is not None
    assert result.presentation_status.renderer == "gnome_shell_raster_frame"
    assert result.presentation_status.pyqt_renderer_preserved is True
    assert result.presentation_status.requested_rect == HelperRect(0, 0, 3440, 1440)
    assert result.presentation_status.applied_rect == frame_request.frame_rect
    assert result.presentation_status.rect_match is True
    assert result.presentation_status.rect_delta == (0, 0, 0, 0)
    assert result.presentation_status.true_overlay_ready is False
    assert result.shell_raster_frame_presented is True
    assert result.should_show_overlay is False
    assert calls[0].renderer == "gnome_shell_raster_frame"
    assert calls[0].shell_raster_frame == frame_request
    assert calls[0].shell_raster_frame.stale_timeout_ms == 1500


def test_shell_raster_bridge_exposes_debug_metrics_in_log_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, "1")
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, "1")
    frame_request = HelperRasterFrameRequest(
        action="update",
        frame_version="phase13-static-pyqt-proof-v1:test-session:abc123",
        target_token="meta:21",
        target_rect=HelperRect(0, 0, 3440, 1440),
        frame_rect=HelperRect(24, 24, 520, 128),
        scale=1.0,
        image_path="/run/user/1000/EDMCModernOverlay/shell-raster/frame.png",
        checksum="abc123",
        byte_size=128,
        stale_timeout_ms=SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS,
        diagnostics={
            "schema": 1,
            "transport": "png_path",
            "cache_hit": True,
            "encode_ms": 0.0,
        },
    )

    monkeypatch.setattr(
        "overlay_client.backend.bundles._gnome_shell_helper_presentation.build_static_shell_raster_frame_request",
        lambda *_args, **_kwargs: ShellRasterFrameBuildResult(request=frame_request, eligible=True),
    )

    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=lambda request: _presentation_payload(
            request,
            applied_rect=frame_request.frame_rect.to_payload(),
            renderer="gnome_shell_raster_frame",
            shell_raster_frame={
                "frame_version": frame_request.frame_version,
                "frame_rect": frame_request.frame_rect.to_payload(),
                "frame_dimensions": {"x": 0, "y": 0, "width": 520, "height": 128},
                "diagnostics": {
                    "schema": 1,
                    "request": dict(frame_request.diagnostics or {}),
                    "helper": {"helper_decode_ms": 1.5, "helper_apply_ms": 0.25},
                },
            },
        ),
        clock=lambda: 100.0,
    )

    metrics = result.to_log_payload()["shell_raster_metrics"]
    assert isinstance(metrics, dict)
    request_metrics = metrics["request"]
    status_metrics = metrics["status"]
    assert isinstance(request_metrics, dict)
    assert isinstance(status_metrics, dict)
    helper_metrics = status_metrics["helper"]
    assert isinstance(helper_metrics, dict)
    assert request_metrics["transport"] == "png_path"
    assert request_metrics["cache_hit"] is True
    assert helper_metrics["helper_decode_ms"] == 1.5
    assert helper_metrics["helper_apply_ms"] == 0.25


def test_shell_raster_bridge_refreshes_before_short_lease_expires(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, "1")
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, "1")
    frame_request = HelperRasterFrameRequest(
        action="update",
        frame_version="phase13-static-pyqt-proof-v1:test-session:abc123",
        target_token="meta:21",
        target_rect=HelperRect(0, 0, 3440, 1440),
        frame_rect=HelperRect(10, 10, 3420, 1420),
        scale=1.0,
        image_path="/run/user/1000/EDMCModernOverlay/shell-raster/frame.png",
        checksum="abc123",
        byte_size=128,
        stale_timeout_ms=SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS,
    )
    monkeypatch.setattr(
        "overlay_client.backend.bundles._gnome_shell_helper_presentation.build_static_shell_raster_frame_request",
        lambda *_args, **_kwargs: ShellRasterFrameBuildResult(request=frame_request, eligible=True),
    )
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    calls: list[HelperPresentationRequest] = []

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        calls.append(request)
        return _presentation_payload(
            request,
            applied_rect=frame_request.frame_rect.to_payload(),
            renderer="gnome_shell_raster_frame",
            shell_raster_frame={
                "frame_version": frame_request.frame_version,
                "frame_rect": frame_request.frame_rect.to_payload(),
                "frame_dimensions": {"x": 0, "y": 0, "width": 3420, "height": 1420},
                "session_id": "test-session",
            },
        )

    first = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
    )
    clock.now += 0.5
    skipped = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
    )
    clock.now += 0.3
    refreshed = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
    )

    assert first.shell_raster_frame_presented is True
    assert skipped.presentation_skipped is True
    assert skipped.presentation_skip_reason == "fresh_matching_presentation"
    assert refreshed.presentation_skipped is False
    assert refreshed.shell_raster_frame_presented is True
    assert len(calls) == 2


@pytest.mark.parametrize("reason", ["target_not_focused", "gnome_overview_active"])
def test_shell_raster_focus_risk_degrade_keeps_managed_pyqt_suppressed(
    monkeypatch: pytest.MonkeyPatch,
    reason: str,
) -> None:
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, "1")
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, "1")
    frame_request = HelperRasterFrameRequest(
        action="update",
        frame_version="phase13-static-pyqt-proof-v1:test-session:abc123",
        target_token="meta:21",
        target_rect=HelperRect(0, 0, 3440, 1440),
        frame_rect=HelperRect(24, 24, 520, 128),
        scale=1.0,
        image_path="/run/user/1000/EDMCModernOverlay/shell-raster/frame.png",
        checksum="abc123",
        byte_size=128,
        stale_timeout_ms=SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS,
    )

    monkeypatch.setattr(
        "overlay_client.backend.bundles._gnome_shell_helper_presentation.build_static_shell_raster_frame_request",
        lambda *_args, **_kwargs: ShellRasterFrameBuildResult(request=frame_request, eligible=True),
    )
    calls: list[HelperPresentationRequest] = []

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        calls.append(request)
        return _presentation_payload(
            request,
            status="presentation_degraded",
            applied_rect=None,
            renderer="gnome_shell_raster_frame",
            placement=False,
            chrome_free=False,
            stacking=False,
            click_through=False,
            focus_safe=False,
            degrade_reasons=[reason],
            shell_raster_frame={
                "frame_version": frame_request.frame_version,
                "frame_rect": frame_request.frame_rect.to_payload(),
                "session_id": "test-session",
                "cleanup_action": reason,
            },
        )

    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target(hasFocus=False)),
        fetch_presentation=fetch_presentation,
        clock=lambda: 100.0,
    )

    assert result.presentation_status is not None
    assert result.presentation_status.renderer == "gnome_shell_raster_frame"
    assert result.shell_raster_frame_presented is False
    assert result.shell_raster_frame_suspended_for_focus_risk is True
    assert result.should_show_overlay is False
    assert calls[0].shell_raster_frame == frame_request
    assert calls[0].shell_raster_frame.allow_unfocused_target is False


def test_shell_raster_bridge_allows_unfocused_target_when_keep_visible_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, "1")
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, "1")
    frame_request = HelperRasterFrameRequest(
        action="update",
        frame_version="phase13-static-pyqt-proof-v1:test-session:abc123",
        target_token="meta:21",
        target_rect=HelperRect(0, 0, 3440, 1440),
        frame_rect=HelperRect(10, 10, 3420, 1420),
        scale=1.0,
        image_path="/run/user/1000/EDMCModernOverlay/shell-raster/frame.png",
        checksum="abc123",
        byte_size=128,
        stale_timeout_ms=SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS,
    )

    monkeypatch.setattr(
        "overlay_client.backend.bundles._gnome_shell_helper_presentation.build_static_shell_raster_frame_request",
        lambda *_args, **_kwargs: ShellRasterFrameBuildResult(request=frame_request, eligible=True),
    )
    calls: list[HelperPresentationRequest] = []

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        calls.append(request)
        assert request.shell_raster_frame is not None
        assert request.shell_raster_frame.allow_unfocused_target is True
        return _presentation_payload(
            request,
            applied_rect=frame_request.frame_rect.to_payload(),
            renderer="gnome_shell_raster_frame",
            shell_raster_frame={
                "frame_version": frame_request.frame_version,
                "frame_rect": frame_request.frame_rect.to_payload(),
                "frame_dimensions": {"x": 0, "y": 0, "width": 3420, "height": 1420},
                "session_id": "test-session",
                "allow_unfocused_target": True,
            },
        )

    result = run_gnome_shell_helper_presentation_cycle(
        keep_overlay_visible=True,
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target(hasFocus=False)),
        fetch_presentation=fetch_presentation,
        clock=lambda: 100.0,
    )

    assert result.presentation_status is not None
    assert result.presentation_status.state is HelperPresentationState.APPLIED
    assert result.presentation_status.rect_match is True
    assert result.presentation_status.degrade_reasons == ()
    assert result.shell_raster_frame_presented is True
    assert result.shell_raster_frame_suspended_for_focus_risk is False
    assert result.should_show_overlay is False
    assert calls


def test_shell_raster_keep_visible_preference_changes_presentation_signature(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, "1")
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, "1")
    frame_request = HelperRasterFrameRequest(
        action="update",
        frame_version="phase13-static-pyqt-proof-v1:test-session:abc123",
        target_token="meta:21",
        target_rect=HelperRect(0, 0, 3440, 1440),
        frame_rect=HelperRect(10, 10, 3420, 1420),
        scale=1.0,
        image_path="/run/user/1000/EDMCModernOverlay/shell-raster/frame.png",
        checksum="abc123",
        byte_size=128,
        stale_timeout_ms=SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS,
    )
    monkeypatch.setattr(
        "overlay_client.backend.bundles._gnome_shell_helper_presentation.build_static_shell_raster_frame_request",
        lambda *_args, **_kwargs: ShellRasterFrameBuildResult(request=frame_request, eligible=True),
    )
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    calls: list[HelperPresentationRequest] = []

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        calls.append(request)
        assert request.shell_raster_frame is not None
        return _presentation_payload(
            request,
            applied_rect=frame_request.frame_rect.to_payload(),
            renderer="gnome_shell_raster_frame",
            shell_raster_frame={
                "frame_version": frame_request.frame_version,
                "frame_rect": frame_request.frame_rect.to_payload(),
                "frame_dimensions": {"x": 0, "y": 0, "width": 3420, "height": 1420},
                "session_id": "test-session",
                "allow_unfocused_target": request.shell_raster_frame.allow_unfocused_target,
            },
        )

    first = run_gnome_shell_helper_presentation_cycle(
        keep_overlay_visible=False,
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )
    clock.now += 0.2
    second = run_gnome_shell_helper_presentation_cycle(
        keep_overlay_visible=True,
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )

    assert first.presentation_skipped is False
    assert second.presentation_skipped is False
    assert len(calls) == 2
    assert calls[0].shell_raster_frame is not None
    assert calls[1].shell_raster_frame is not None
    assert calls[0].shell_raster_frame.allow_unfocused_target is False
    assert calls[1].shell_raster_frame.allow_unfocused_target is True


def test_shell_raster_bridge_falls_back_to_pyqt_when_frame_not_built(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, "1")
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, "1")
    monkeypatch.setattr(
        "overlay_client.backend.bundles._gnome_shell_helper_presentation.build_static_shell_raster_frame_request",
        lambda *_args, **_kwargs: ShellRasterFrameBuildResult(reason="frame_export_failed"),
    )
    calls: list[HelperPresentationRequest] = []

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        calls.append(request)
        return _presentation_payload(request)

    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        clock=lambda: 100.0,
    )

    assert result.presentation_status is not None
    assert result.shell_raster_frame_presented is False
    assert result.should_show_overlay is True
    assert calls[0].renderer == "pyqt"
    assert calls[0].shell_raster_frame is None


def test_shell_raster_clear_request_is_shutdown_only_payload() -> None:
    request = build_shell_raster_frame_clear_request()

    assert request.action.value == "degrade"
    assert request.renderer == "gnome_shell_raster_frame"
    assert request.content_rect is None
    assert request.require_placement is False
    assert request.require_chrome_free is False
    assert request.require_stacking is False
    assert request.require_click_through is False
    assert request.require_focus_safe is False
    assert request.shell_raster_frame is not None
    assert request.shell_raster_frame.action == "clear"
    payload = request.to_payload()
    assert payload["shell_raster_frame"] is True
    assert payload["shell_raster_frame_action"] == "clear"


def test_shell_raster_shutdown_clear_calls_fetcher() -> None:
    calls: list[HelperPresentationRequest] = []

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        calls.append(request)
        return {"status": "shell_raster_frame_cleared"}

    assert clear_gnome_shell_raster_frame_via_gdbus(fetch_presentation) is True
    assert len(calls) == 1
    assert calls[0].shell_raster_frame is not None
    assert calls[0].shell_raster_frame.action == "clear"


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


def test_target_query_payload_requests_geometry_diagnostics_only_when_enabled() -> None:
    assert _target_query_payload({}) == "{}"
    assert _target_query_payload({GNOME_HELPER_GEOMETRY_DIAGNOSTICS_ENV: "0"}) == "{}"
    assert _target_query_payload({GNOME_HELPER_GEOMETRY_DIAGNOSTICS_ENV: "1"}) == (
        '{"include_geometry_diagnostics":true}'
    )


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


@pytest.mark.parametrize(
    ("target_overrides", "second_surface_action"),
    [
        ({"targetToken": "meta:22"}, ""),
        ({"contentRect": {"x": 80, "y": 0, "width": 3440, "height": 1440}}, ""),
        ({"monitorRect": {"x": 80, "y": 0, "width": 3440, "height": 1440}}, ""),
        ({"hasFocus": False}, ""),
        ({"showingOnWorkspace": False}, ""),
        ({"fullscreen": False}, ""),
        ({}, "mapped_suppressed"),
    ],
)
def test_persistent_wrong_monitor_backoff_clears_on_hard_signature_changes(
    target_overrides: dict[str, object],
    second_surface_action: str,
) -> None:
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    presentation_calls: list[HelperPresentationRequest] = []

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        presentation_calls.append(request)
        return _wrong_monitor_presentation_payload(request)

    for _ in range(2):
        run_gnome_shell_helper_presentation_cycle(
            fetch_health=_health_payload,
            fetch_target=lambda: _target_payload(_borderless_target()),
            fetch_presentation=fetch_presentation,
            clock=clock,
            runtime_state=state,
            health_cache_jitter_seconds=lambda: 0.0,
        )
        clock.now += 0.5

    result = run_gnome_shell_helper_presentation_cycle(
        previous_surface_action=second_surface_action,
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target(**target_overrides)),
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )

    assert result.presentation_skipped is False
    assert result.attempts >= 1
    assert len(presentation_calls) > 4


def test_same_monitor_applied_rect_mismatch_is_not_classified_as_wrong_monitor() -> None:
    state = GnomeHelperPresentationRuntimeState()
    presentation_calls: list[HelperPresentationRequest] = []

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        presentation_calls.append(request)
        return _presentation_payload(
            request,
            applied_rect={"x": 10, "y": 10, "width": 320, "height": 200},
        )

    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        clock=lambda: 100.0,
        max_attempts=1,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )

    assert result.presentation_status is not None
    assert "applied_rect_mismatch" in result.presentation_status.degrade_reasons
    assert GNOME_HELPER_REASON_WRONG_MONITOR_APPLIED_RECT not in result.presentation_status.degrade_reasons
    assert result.persistent_mismatch_count == 0
    assert len(presentation_calls) == 1


def test_successful_matching_presentation_clears_persistent_wrong_monitor_backoff() -> None:
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    presentation_calls: list[HelperPresentationRequest] = []

    def wrong_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        presentation_calls.append(request)
        return _wrong_monitor_presentation_payload(request)

    for _ in range(2):
        run_gnome_shell_helper_presentation_cycle(
            fetch_health=_health_payload,
            fetch_target=lambda: _target_payload(_borderless_target()),
            fetch_presentation=wrong_presentation,
            clock=clock,
            runtime_state=state,
            health_cache_jitter_seconds=lambda: 0.0,
        )
        clock.now += 0.5

    def matching_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        presentation_calls.append(request)
        return _presentation_payload(request)

    repaired_target = _borderless_target(contentRect={"x": 40, "y": 0, "width": 3440, "height": 1440})
    repaired = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(repaired_target),
        fetch_presentation=matching_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )

    assert repaired.presentation_status is not None
    assert repaired.presentation_status.rect_match is True
    assert repaired.persistent_mismatch_count == 0
    assert state.persistent_mismatch_key is None


def test_presentation_diagnostics_env_requests_helper_diagnostics(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(GNOME_HELPER_PRESENTATION_DIAGNOSTICS_ENV, "1")
    captured_requests: list[HelperPresentationRequest] = []

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        captured_requests.append(request)
        assert request.to_payload()["include_presentation_diagnostics"] is True
        return _presentation_payload(
            request,
            presentation_diagnostics={"schema": 1, "placement": {"moveResizeAction": "move_resize_frame"}},
        )

    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        clock=lambda: 100.0,
    )

    assert captured_requests
    assert captured_requests[0].include_presentation_diagnostics is True
    assert result.presentation_status is not None
    assert result.presentation_status.presentation_diagnostics == {
        "schema": 1,
        "placement": {"moveResizeAction": "move_resize_frame"},
    }


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
