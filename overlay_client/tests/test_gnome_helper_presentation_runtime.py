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
    GNOME_SHELL_HELPER_CAPABILITY_RASTER_CONTENT_VISIBILITY,
    GNOME_SHELL_HELPER_COORDINATE_SPACE,
    GNOME_SHELL_HELPER_RECT_SOURCE_FRAME_FALLBACK,
    HELPER_KIND,
    HELPER_PROTOCOL,
    HELPER_VERSION,
    HelperPresentationRequest,
    HelperPresentationState,
    HelperRasterContentVisibility,
    HelperRasterFrameRequest,
    HelperRasterFrameRegionRequest,
    HelperRect,
)
from overlay_client.backend.bundles.gnome_shell_wayland import build_gnome_shell_wayland_bundle
from overlay_client.backend.contracts import HelperKind
from overlay_client.backend.presentation_policy import BackendPresentationContentVisibility
from overlay_client.backend.presentation_runtime import BackendPresentationRuntimeRequest
from overlay_client.backend.bundles._gnome_shell_helper_presentation import (
    GNOME_HELPER_BORDERLESS_FULLSCREEN_PREP_ENV,
    GNOME_HELPER_FULLSCREEN_HANDOFF_GUARD_ENV,
    GNOME_HELPER_GEOMETRY_DIAGNOSTICS_ENV,
    GNOME_HELPER_PRESENTATION_DIAGNOSTICS_ENV,
    GNOME_HELPER_REASON_PERSISTENT_APPLIED_RECT_MISMATCH,
    GNOME_HELPER_REASON_SURFACE_PREPARATION_FAILED,
    GNOME_HELPER_REASON_WRONG_MONITOR_APPLIED_RECT,
    GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV,
    GNOME_HELPER_SHELL_RASTER_PROOF_ENV,
    GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV,
    GNOME_HELPER_SURFACE_PREPARATION_MANAGED_WINDOWED,
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


@pytest.fixture(autouse=True)
def _default_fullscreen_handoff_guard_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(GNOME_HELPER_FULLSCREEN_HANDOFF_GUARD_ENV, "0")


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


def test_presentation_cycle_retries_once_when_applied_rect_readback_lags_despite_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(GNOME_HELPER_PRESENTATION_DIAGNOSTICS_ENV, "1")
    calls: list[HelperPresentationRequest] = []
    diagnostics = {
        "schema": 1,
        "requestedRect": {"x": 1080, "y": 253, "width": 1280, "height": 960},
        "target": {"monitor": 0},
        "placement": {"moveResizeAction": "move_to_monitor_then_resize"},
        "before": {"monitor": 1},
        "after": {"monitor": 0},
    }

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        calls.append(request)
        if len(calls) == 1:
            return _presentation_payload(
                request,
                applied_rect={"x": 0, "y": 29, "width": 1280, "height": 960},
                presentation_diagnostics=diagnostics,
            )
        return _presentation_payload(request, presentation_diagnostics=diagnostics)

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
    assert all(call.include_presentation_diagnostics for call in calls)
    assert result.presentation_status.presentation_diagnostics == diagnostics


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
    clock.now += 0.5
    refreshed = run_gnome_shell_helper_presentation_cycle(
        presentation_refresh_requested=True,
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )
    clock.now += 0.5
    backed_off_again = run_gnome_shell_helper_presentation_cycle(
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
    assert refreshed.presentation_skipped is False
    assert refreshed.attempts == 2
    assert backed_off_again.presentation_skipped is True
    assert backed_off_again.presentation_skip_reason == GNOME_HELPER_REASON_PERSISTENT_APPLIED_RECT_MISMATCH
    assert len(presentation_calls) == 6


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
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, "1")

    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        clock=lambda: 102.0,
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
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_PROOF_ENV, "1")
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
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_PROOF_ENV, "1")
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


def test_shell_raster_bridge_sends_provider_real_content_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, "1")
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, "1")
    monkeypatch.setenv(GNOME_HELPER_PRESENTATION_DIAGNOSTICS_ENV, "1")
    frame_request = HelperRasterFrameRequest(
        action="update",
        frame_version="phase14-real-content-cropped-v1:test-session:abc123",
        target_token="meta:21",
        target_rect=HelperRect(0, 0, 3440, 1440),
        frame_rect=HelperRect(20, 32, 300, 120),
        scale=1.0,
        image_path="/run/user/1000/EDMCModernOverlay/shell-raster/real-content-cropped-overlay.png",
        checksum="abc123",
        byte_size=512,
        stale_timeout_ms=SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS,
    )
    seen: dict[str, object] = {}

    def provider(target_status, request, include_diagnostics: bool) -> ShellRasterFrameBuildResult:
        seen["target_status"] = target_status
        seen["request"] = request
        seen["include_diagnostics"] = include_diagnostics
        return ShellRasterFrameBuildResult(request=frame_request, eligible=True)

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
                "frame_dimensions": {"x": 0, "y": 0, "width": 300, "height": 120},
            },
        )

    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        shell_raster_frame_provider=provider,
        clock=lambda: 100.0,
    )

    assert result.shell_raster_frame_presented is True
    assert seen["include_diagnostics"] is True
    assert calls[0].renderer == "gnome_shell_raster_frame"
    assert calls[0].shell_raster_frame == frame_request


def test_shell_raster_bridge_sends_provider_multi_region_real_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, "1")
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, "1")
    region_a = HelperRasterFrameRegionRequest(
        region_id="region-01",
        frame_version="phase14-real-content-cropped-v1-region-01:test-session:aaa",
        target_token="meta:21",
        target_rect=HelperRect(0, 0, 3440, 1440),
        frame_rect=HelperRect(8, 8, 180, 40),
        scale=1.0,
        image_path="/run/user/1000/EDMCModernOverlay/shell-raster/real-content-region-region-01.png",
        checksum="aaa",
        byte_size=256,
    )
    region_b = HelperRasterFrameRegionRequest(
        region_id="region-02",
        frame_version="phase14-real-content-cropped-v1-region-02:test-session:bbb",
        target_token="meta:21",
        target_rect=HelperRect(0, 0, 3440, 1440),
        frame_rect=HelperRect(3100, 16, 260, 48),
        scale=1.0,
        image_path="/run/user/1000/EDMCModernOverlay/shell-raster/real-content-region-region-02.png",
        checksum="bbb",
        byte_size=300,
    )
    frame_request = HelperRasterFrameRequest(
        action="update",
        frame_version="phase14-real-content-cropped-v1-multi:test-session:aggregate",
        target_token="meta:21",
        target_rect=HelperRect(0, 0, 3440, 1440),
        frame_rect=HelperRect(8, 8, 3352, 56),
        scale=1.0,
        image_path=region_a.image_path,
        checksum="aggregate",
        byte_size=556,
        stale_timeout_ms=SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS,
        regions=(region_a, region_b),
    )

    def provider(_target_status, _request, _include_diagnostics: bool) -> ShellRasterFrameBuildResult:
        return ShellRasterFrameBuildResult(request=frame_request, eligible=True)

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
                "frame_dimensions": {"x": 0, "y": 0, "width": 3352, "height": 56},
                "regions": [region.to_payload() for region in frame_request.regions],
            },
        )

    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        shell_raster_frame_provider=provider,
        clock=lambda: 100.0,
    )

    assert result.shell_raster_frame_presented is True
    assert calls[0].renderer == "gnome_shell_raster_frame"
    assert calls[0].shell_raster_frame is not None
    assert calls[0].shell_raster_frame.regions == (region_a, region_b)
    payload = calls[0].to_payload()
    assert payload["shell_raster_region_count"] == 2
    assert payload["shell_raster_regions"][1]["region_id"] == "region-02"


@pytest.mark.parametrize("reason", ["no_visible_content", "frame_export_failed"])
def test_shell_raster_bridge_keeps_pyqt_when_real_content_provider_has_no_frame(
    monkeypatch: pytest.MonkeyPatch,
    reason: str,
) -> None:
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, "1")
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, "1")
    calls: list[HelperPresentationRequest] = []

    def provider(_target_status, _request, _include_diagnostics: bool) -> ShellRasterFrameBuildResult:
        return ShellRasterFrameBuildResult(reason=reason)

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        calls.append(request)
        return _presentation_payload(request)

    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        shell_raster_frame_provider=provider,
        clock=lambda: 100.0,
    )

    assert result.shell_raster_frame_presented is False
    assert result.should_show_overlay is True
    assert calls[0].renderer == "pyqt"
    assert calls[0].shell_raster_frame is None


def test_shell_raster_bridge_exposes_debug_metrics_in_log_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, "1")
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, "1")
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_PROOF_ENV, "1")
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


def test_shell_raster_skipped_reused_payload_reports_noop_helper_metrics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, "1")
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, "1")
    monkeypatch.setenv(GNOME_HELPER_PRESENTATION_DIAGNOSTICS_ENV, "1")
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    frame_kwargs = {
        "action": "update",
        "frame_version": "phase14-real-content-cropped-v1-multi:test-session:aggregate",
        "target_token": "meta:21",
        "target_rect": HelperRect(0, 0, 3440, 1440),
        "frame_rect": HelperRect(0, 0, 3440, 1440),
        "scale": 1.0,
        "image_path": "/run/user/1000/EDMCModernOverlay/shell-raster/real-content-region-region-01.png",
        "checksum": "aggregate",
        "byte_size": 128,
        "stale_timeout_ms": SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS,
    }
    first_frame = HelperRasterFrameRequest(
        **frame_kwargs,
        diagnostics={
            "schema": 1,
            "update_reason": "real_content_multi_region_overlay",
            "client_reused_region_count": 7,
            "client_encoded_region_count": 1,
            "client_payload_reused": False,
        },
    )
    reused_frame = HelperRasterFrameRequest(
        **frame_kwargs,
        diagnostics={
            "schema": 1,
            "update_reason": "real_content_multi_region_overlay",
            "client_reused_region_count": 8,
            "client_encoded_region_count": 0,
            "client_reused_all_regions": True,
            "client_payload_reused": True,
            "client_payload_reuse_skip_reason": "",
        },
    )
    provider_calls = 0
    presentation_calls: list[HelperPresentationRequest] = []

    def provider(_target_status, _request, _include_diagnostics: bool) -> ShellRasterFrameBuildResult:
        nonlocal provider_calls
        provider_calls += 1
        return ShellRasterFrameBuildResult(
            request=first_frame if provider_calls == 1 else reused_frame,
            eligible=True,
        )

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        presentation_calls.append(request)
        return _presentation_payload(
            request,
            applied_rect=first_frame.frame_rect.to_payload(),
            renderer="gnome_shell_raster_frame",
            shell_raster_frame={
                "frame_version": first_frame.frame_version,
                "frame_rect": first_frame.frame_rect.to_payload(),
                "frame_dimensions": {"x": 0, "y": 0, "width": 3440, "height": 1440},
                "diagnostics": {
                    "schema": 1,
                    "request": dict(first_frame.diagnostics or {}),
                    "helper": {
                        "helper_decode_ms": 1.25,
                        "helper_apply_ms": 0.2,
                        "helper_reused_frame": False,
                        "helper_decode_skipped": False,
                        "helper_update_reason": "decoded_changed_regions",
                    },
                },
            },
        )

    run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        shell_raster_frame_provider=provider,
        clock=clock,
        runtime_state=state,
    )
    clock.now += 0.5
    skipped = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        shell_raster_frame_provider=provider,
        clock=clock,
        runtime_state=state,
    )

    assert skipped.presentation_skipped is True
    assert skipped.presentation_skip_reason == "fresh_matching_presentation"
    assert provider_calls == 2
    assert len(presentation_calls) == 1
    metrics = skipped.to_log_payload()["shell_raster_metrics"]
    assert isinstance(metrics, dict)
    status_metrics = metrics["status"]
    assert isinstance(status_metrics, dict)
    helper_metrics = status_metrics["helper"]
    assert helper_metrics["helper_update_reason"] == "client_reused_all_regions"
    assert helper_metrics["helper_call_skipped"] is True
    assert helper_metrics["helper_reused_frame"] is True
    assert helper_metrics["helper_decode_skipped"] is True
    assert helper_metrics["helper_decode_ms"] == 0


def test_shell_raster_bridge_refreshes_before_short_lease_expires(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, "1")
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, "1")
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_PROOF_ENV, "1")
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
    target_calls = 0
    calls: list[HelperPresentationRequest] = []

    def fetch_target() -> dict[str, object]:
        nonlocal target_calls
        target_calls += 1
        return _target_payload(_borderless_target())

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
        previous_surface_action="mapped_suppressed",
        fetch_health=_health_payload,
        fetch_target=fetch_target,
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
    )
    clock.now += 0.5
    skipped = run_gnome_shell_helper_presentation_cycle(
        previous_surface_action="mapped_suppressed",
        fetch_health=_health_payload,
        fetch_target=fetch_target,
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
    )
    clock.now += 0.3
    refreshed = run_gnome_shell_helper_presentation_cycle(
        previous_surface_action="mapped_suppressed",
        fetch_health=_health_payload,
        fetch_target=fetch_target,
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
    )

    assert first.shell_raster_frame_presented is True
    assert skipped.presentation_skipped is True
    assert skipped.presentation_skip_reason == "suppressed_poll_throttle"
    assert skipped.target_poll_skipped is True
    assert refreshed.presentation_skipped is False
    assert refreshed.shell_raster_frame_presented is True
    assert target_calls == 2
    assert len(calls) == 2


@pytest.mark.parametrize(
    "reason",
    ["target_not_focused", "gnome_overview_active", "shell_raster_parent_unavailable"],
)
def test_shell_raster_focus_risk_degrade_keeps_managed_pyqt_suppressed(
    monkeypatch: pytest.MonkeyPatch,
    reason: str,
) -> None:
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, "1")
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, "1")
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_PROOF_ENV, "1")
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


def test_selected_shell_raster_preserves_fullscreen_actor_continuity_when_unfocused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, "1")
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, "1")
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_PROOF_ENV, "1")
    frame_request = HelperRasterFrameRequest(
        action="update",
        frame_version="phase13-static-pyqt-proof-v1:test-session:abc123",
        target_token="meta:21",
        target_rect=HelperRect(0, 0, 3440, 1440),
        frame_rect=HelperRect(0, 0, 3440, 1440),
        scale=1.0,
        image_path="/run/user/1000/EDMCModernOverlay/shell-raster/frame.png",
        checksum="abc123",
        byte_size=128,
        stale_timeout_ms=SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS,
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
                "frame_dimensions": {"x": 0, "y": 0, "width": 3440, "height": 1440},
                "session_id": "test-session",
                "allow_unfocused_target": True,
            },
        )

    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target(hasFocus=False)),
        fetch_presentation=fetch_presentation,
        clock=lambda: 0.2,
        shell_raster_frame_provider=lambda *_args, **_kwargs: ShellRasterFrameBuildResult(
            request=frame_request,
            eligible=True,
        ),
        shell_raster_runtime_enabled=True,
        suppress_pyqt_fallback_on_shell_raster_failure=True,
    )

    assert result.presentation_status is not None
    assert result.presentation_status.state is HelperPresentationState.APPLIED
    assert result.presentation_status.rect_match is True
    assert result.shell_raster_frame_presented is True
    assert result.shell_raster_frame_suspended_for_focus_risk is False
    assert result.should_show_overlay is False
    assert calls


def test_selected_shell_raster_allows_unfocused_fullscreen_target_when_keep_visible_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, "1")
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, "1")
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_PROOF_ENV, "1")
    frame_request = HelperRasterFrameRequest(
        action="update",
        frame_version="phase13-static-pyqt-proof-v1:test-session:abc123",
        target_token="meta:21",
        target_rect=HelperRect(0, 0, 3440, 1440),
        frame_rect=HelperRect(0, 0, 3440, 1440),
        scale=1.0,
        image_path="/run/user/1000/EDMCModernOverlay/shell-raster/frame.png",
        checksum="abc123",
        byte_size=128,
        stale_timeout_ms=SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS,
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
                "frame_dimensions": {"x": 0, "y": 0, "width": 3440, "height": 1440},
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
        shell_raster_frame_provider=lambda *_args, **_kwargs: ShellRasterFrameBuildResult(
            request=frame_request,
            eligible=True,
        ),
        shell_raster_runtime_enabled=True,
        suppress_pyqt_fallback_on_shell_raster_failure=True,
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
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_PROOF_ENV, "1")
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
    monkeypatch.setenv(GNOME_HELPER_SHELL_RASTER_PROOF_ENV, "1")
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


def test_selected_shell_raster_runtime_uses_provider_without_env_gates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, raising=False)
    monkeypatch.delenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, raising=False)
    calls: list[HelperPresentationRequest] = []

    def provider(
        _target_status,
        request: HelperPresentationRequest | None,
        _include_diagnostics: bool,
    ) -> ShellRasterFrameBuildResult:
        assert request is not None
        rect = request.content_rect
        assert rect is not None
        return ShellRasterFrameBuildResult(
            request=HelperRasterFrameRequest(
                action="update",
                frame_version="test-selected-raster",
                target_token=request.target_token,
                target_rect=rect,
                frame_rect=HelperRect(rect.x + 10, rect.y + 10, rect.width - 20, rect.height - 20),
                scale=1.0,
                image_path="/tmp/test-selected-raster.png",
                checksum="abc123",
                byte_size=123,
                stale_timeout_ms=SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS,
                diagnostics={"update_reason": "test_selected_raster"},
            )
        )

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        calls.append(request)
        assert request.shell_raster_frame is not None
        frame_rect = request.shell_raster_frame.frame_rect.to_payload()
        return _presentation_payload(
            request,
            requested_rect=frame_rect,
            applied_rect=frame_rect,
            renderer="gnome_shell_raster_frame",
            shell_raster_frame={
                "frame_version": request.shell_raster_frame.frame_version,
                "frame_rect": frame_rect,
            },
        )

    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        shell_raster_frame_provider=provider,
        shell_raster_runtime_enabled=True,
        clock=lambda: 100.0,
    )

    assert result.shell_raster_frame_presented is True
    assert result.should_show_overlay is False
    assert calls[0].renderer == "gnome_shell_raster_frame"
    assert calls[0].shell_raster_frame is not None


def test_native_gnome_runtime_routes_eligible_fullscreen_to_real_content_raster(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, raising=False)
    monkeypatch.delenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, raising=False)
    runtime = build_gnome_shell_wayland_bundle().presentation_runtime
    assert runtime is not None
    status = type(
        "NativeGnomeStatus",
        (),
        {
            "helper_states": (
                type(
                    "HelperState",
                    (),
                    {"helper": HelperKind.GNOME_SHELL_EXTENSION, "available": True},
                )(),
            )
        },
    )()
    calls: list[HelperPresentationRequest] = []

    def provider(
        _target_status,
        request: HelperPresentationRequest | None,
        _include_diagnostics: bool,
    ) -> ShellRasterFrameBuildResult:
        assert request is not None
        rect = request.content_rect
        assert rect is not None
        return ShellRasterFrameBuildResult(
            request=HelperRasterFrameRequest(
                action="update",
                frame_version="phase14-real-content-cropped-v1:native-gnome:abc123",
                target_token=request.target_token,
                target_rect=rect,
                frame_rect=HelperRect(rect.x + 10, rect.y + 10, rect.width - 20, rect.height - 20),
                scale=1.0,
                image_path="/tmp/native-gnome-real-content-cropped.png",
                checksum="abc123",
                byte_size=123,
                stale_timeout_ms=SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS,
            ),
            eligible=True,
        )

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        calls.append(request)
        assert request.shell_raster_frame is not None
        frame_rect = request.shell_raster_frame.frame_rect.to_payload()
        return _presentation_payload(
            request,
            requested_rect=frame_rect,
            applied_rect=frame_rect,
            renderer="gnome_shell_raster_frame",
            shell_raster_frame={
                "frame_version": request.shell_raster_frame.frame_version,
                "frame_rect": frame_rect,
            },
        )

    def runner(**kwargs):
        return run_gnome_shell_helper_presentation_cycle(
            fetch_health=_health_payload,
            fetch_target=lambda: _target_payload(_borderless_target()),
            fetch_presentation=fetch_presentation,
            clock=lambda: 100.0,
            **kwargs,
        )

    runtime_result = runtime.run_presentation_cycle(
        status,
        BackendPresentationRuntimeRequest(
            presentation_cycle_runner=runner,
            raster_frame_provider=provider,
        ),
    )

    assert runtime_result is not None
    result = runtime_result.presentation_result
    assert result is not None
    assert result.shell_raster_frame_presented is True
    assert result.should_show_overlay is False
    assert calls[0].renderer == "gnome_shell_raster_frame"
    assert calls[0].shell_raster_frame is not None
    assert calls[0].shell_raster_frame.frame_version.startswith("phase14-real-content-cropped")


def test_native_gnome_runtime_wires_supported_content_visibility_without_losing_fullscreen_continuity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, raising=False)
    monkeypatch.delenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, raising=False)
    runtime = build_gnome_shell_wayland_bundle().presentation_runtime
    assert runtime is not None
    status = type(
        "NativeGnomeStatus",
        (),
        {
            "helper_states": (
                type("HelperState", (), {"helper": HelperKind.GNOME_SHELL_EXTENSION, "available": True})(),
            )
        },
    )()
    runtime_state = GnomeHelperPresentationRuntimeState()
    calls: list[HelperPresentationRequest] = []

    def provider(
        _target_status,
        request: HelperPresentationRequest | None,
        _include_diagnostics: bool,
    ) -> ShellRasterFrameBuildResult:
        assert request is not None
        rect = request.content_rect
        assert rect is not None
        return ShellRasterFrameBuildResult(
            request=HelperRasterFrameRequest(
                action="update",
                frame_version="content-visibility-v1",
                target_token=request.target_token,
                target_rect=rect,
                frame_rect=HelperRect(24, 24, 520, 128),
                scale=1.0,
                image_path="/tmp/native-gnome-content-visibility.png",
                checksum="content-visibility",
                byte_size=123,
                stale_timeout_ms=SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS,
            ),
            eligible=True,
        )

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        calls.append(request)
        frame = request.shell_raster_frame
        assert frame is not None
        assert frame.content_visibility is not None
        frame_rect = frame.frame_rect.to_payload()
        return _presentation_payload(
            request,
            requested_rect=frame_rect,
            applied_rect=frame_rect,
            renderer="gnome_shell_raster_frame",
            shell_raster_frame={
                "frame_version": frame.frame_version,
                "frame_rect": frame_rect,
                "content_visibility": frame.content_visibility.value,
                "content_visibility_supported": True,
            },
        )

    def runner(**kwargs):
        return run_gnome_shell_helper_presentation_cycle(
            fetch_health=lambda: {
                **_health_payload(),
                "capabilities": [
                    *GNOME_SHELL_HELPER_CAPABILITIES,
                    GNOME_SHELL_HELPER_CAPABILITY_RASTER_CONTENT_VISIBILITY,
                ],
            },
            fetch_target=lambda: _target_payload(_borderless_target(hasFocus=False)),
            fetch_presentation=fetch_presentation,
            clock=lambda: 100.0,
            runtime_state=runtime_state,
            health_cache_jitter_seconds=lambda: 0.0,
            **kwargs,
        )

    result = runtime.run_presentation_cycle(
        status,
        BackendPresentationRuntimeRequest(
            content_visibility=BackendPresentationContentVisibility.SUPPRESSED,
            presentation_cycle_runner=runner,
            raster_frame_provider=provider,
        ),
    )

    assert result is not None
    assert len(calls) == 1
    frame = calls[0].shell_raster_frame
    assert frame is not None
    assert frame.content_visibility is HelperRasterContentVisibility.SUPPRESSED
    assert frame.allow_unfocused_target is True


def test_native_gnome_runtime_keeps_capability_missing_content_visible_without_cache_skipping_restore(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, raising=False)
    monkeypatch.delenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, raising=False)
    state = GnomeHelperPresentationRuntimeState()
    calls: list[HelperPresentationRequest] = []

    def provider(
        _target_status,
        request: HelperPresentationRequest | None,
        _include_diagnostics: bool,
    ) -> ShellRasterFrameBuildResult:
        assert request is not None
        rect = request.content_rect
        assert rect is not None
        return ShellRasterFrameBuildResult(
            request=HelperRasterFrameRequest(
                action="update",
                frame_version="content-visibility-v1",
                target_token=request.target_token,
                target_rect=rect,
                frame_rect=HelperRect(24, 24, 520, 128),
                scale=1.0,
                image_path="/tmp/native-gnome-content-visibility.png",
                checksum="content-visibility",
                byte_size=123,
                stale_timeout_ms=5000,
            ),
            eligible=True,
        )

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        calls.append(request)
        frame = request.shell_raster_frame
        assert frame is not None
        frame_rect = frame.frame_rect.to_payload()
        shell_raster_frame: dict[str, object] = {
            "frame_version": frame.frame_version,
            "frame_rect": frame_rect,
        }
        if frame.content_visibility is not None:
            shell_raster_frame.update(
                {
                    "content_visibility": frame.content_visibility.value,
                    "content_visibility_supported": True,
                }
            )
        return _presentation_payload(
            request,
            requested_rect=frame_rect,
            applied_rect=frame_rect,
            renderer="gnome_shell_raster_frame",
            shell_raster_frame=shell_raster_frame,
        )

    unsupported = run_gnome_shell_helper_presentation_cycle(
        content_visibility=BackendPresentationContentVisibility.SUPPRESSED,
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target(hasFocus=False)),
        fetch_presentation=fetch_presentation,
        shell_raster_frame_provider=provider,
        shell_raster_runtime_enabled=True,
        suppress_pyqt_fallback_on_shell_raster_failure=True,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
        clock=lambda: 100.0,
    )

    assert unsupported.request is not None
    unsupported_frame = unsupported.request.shell_raster_frame
    assert unsupported_frame is not None
    assert unsupported_frame.content_visibility is None
    assert unsupported_frame.allow_unfocused_target is True
    assert unsupported_frame.diagnostics is not None
    assert unsupported_frame.diagnostics["content_visibility"]["reason"] == (
        "shell_raster_content_visibility_capability_missing"
    )

    supported_state = GnomeHelperPresentationRuntimeState()
    visible = run_gnome_shell_helper_presentation_cycle(
        content_visibility=BackendPresentationContentVisibility.VISIBLE,
        fetch_health=lambda: {
            **_health_payload(),
            "capabilities": [
                *GNOME_SHELL_HELPER_CAPABILITIES,
                GNOME_SHELL_HELPER_CAPABILITY_RASTER_CONTENT_VISIBILITY,
            ],
        },
        fetch_target=lambda: _target_payload(_borderless_target(hasFocus=False)),
        fetch_presentation=fetch_presentation,
        shell_raster_frame_provider=provider,
        shell_raster_runtime_enabled=True,
        suppress_pyqt_fallback_on_shell_raster_failure=True,
        runtime_state=supported_state,
        health_cache_jitter_seconds=lambda: 0.0,
        clock=lambda: 100.1,
    )

    suppressed = run_gnome_shell_helper_presentation_cycle(
        content_visibility=BackendPresentationContentVisibility.SUPPRESSED,
        fetch_health=lambda: {
            **_health_payload(),
            "capabilities": [
                *GNOME_SHELL_HELPER_CAPABILITIES,
                GNOME_SHELL_HELPER_CAPABILITY_RASTER_CONTENT_VISIBILITY,
            ],
        },
        fetch_target=lambda: _target_payload(_borderless_target(hasFocus=False)),
        fetch_presentation=fetch_presentation,
        shell_raster_frame_provider=provider,
        shell_raster_runtime_enabled=True,
        suppress_pyqt_fallback_on_shell_raster_failure=True,
        runtime_state=supported_state,
        health_cache_jitter_seconds=lambda: 0.0,
        clock=lambda: 100.1,
    )

    restored = run_gnome_shell_helper_presentation_cycle(
        content_visibility=BackendPresentationContentVisibility.VISIBLE,
        fetch_health=lambda: {
            **_health_payload(),
            "capabilities": [
                *GNOME_SHELL_HELPER_CAPABILITIES,
                GNOME_SHELL_HELPER_CAPABILITY_RASTER_CONTENT_VISIBILITY,
            ],
        },
        fetch_target=lambda: _target_payload(_borderless_target(hasFocus=True)),
        fetch_presentation=fetch_presentation,
        shell_raster_frame_provider=provider,
        shell_raster_runtime_enabled=True,
        suppress_pyqt_fallback_on_shell_raster_failure=True,
        runtime_state=supported_state,
        health_cache_jitter_seconds=lambda: 0.0,
        clock=lambda: 100.2,
    )

    assert visible.presentation_skipped is False
    assert suppressed.presentation_skipped is False
    assert restored.presentation_skipped is False
    assert len(calls) == 4
    assert calls[-3].shell_raster_frame is not None
    assert calls[-3].shell_raster_frame.content_visibility is HelperRasterContentVisibility.VISIBLE
    assert calls[-2].shell_raster_frame is not None
    assert calls[-2].shell_raster_frame.content_visibility is HelperRasterContentVisibility.SUPPRESSED
    assert calls[-1].shell_raster_frame is not None
    assert calls[-1].shell_raster_frame.content_visibility is HelperRasterContentVisibility.VISIBLE
    assert calls[-1].shell_raster_frame.allow_unfocused_target is True


def test_selected_shell_raster_failure_clears_and_does_not_fallback_to_pyqt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, raising=False)
    monkeypatch.delenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, raising=False)
    calls: list[HelperPresentationRequest] = []

    def provider(*_args, **_kwargs) -> ShellRasterFrameBuildResult:
        return ShellRasterFrameBuildResult(reason="frame_export_failed")

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        calls.append(request)
        return {"status": "shell_raster_frame_cleared"}

    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        shell_raster_frame_provider=provider,
        shell_raster_runtime_enabled=True,
        suppress_pyqt_fallback_on_shell_raster_failure=True,
        clock=lambda: 100.0,
    )

    assert result.should_show_overlay is False
    assert result.request is not None
    assert result.request.action.value == "degrade"
    assert "frame_export_failed" in result.request.degrade_reasons
    assert calls[0].renderer == "gnome_shell_raster_frame"
    assert calls[0].shell_raster_frame is not None
    assert calls[0].shell_raster_frame.action == "clear"


def test_selected_shell_raster_windowed_transition_clears_then_uses_managed_pyqt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, raising=False)
    monkeypatch.delenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, raising=False)
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    calls: list[HelperPresentationRequest] = []
    surface_preparations = []

    def provider(
        target_status,
        request: HelperPresentationRequest | None,
        _include_diagnostics: bool,
    ) -> ShellRasterFrameBuildResult:
        assert request is not None
        target = target_status.target if target_status is not None else None
        if target is None or not target.fullscreen:
            return ShellRasterFrameBuildResult(reason="target_not_fullscreen")
        rect = request.content_rect
        assert rect is not None
        return ShellRasterFrameBuildResult(
            request=HelperRasterFrameRequest(
                action="update",
                frame_version="test-selected-raster",
                target_token=request.target_token,
                target_rect=rect,
                frame_rect=HelperRect(rect.x + 10, rect.y + 10, rect.width - 20, rect.height - 20),
                scale=1.0,
                image_path="/tmp/test-selected-raster.png",
                checksum="abc123",
                byte_size=123,
                stale_timeout_ms=SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS,
            )
        )

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        calls.append(request)
        if request.shell_raster_frame is not None and request.shell_raster_frame.action == "clear":
            return {
                "status": "shell_raster_frame_cleared",
                "helper_kind": HELPER_KIND.value,
                "helper_version": HELPER_VERSION,
                "helper_protocol": HELPER_PROTOCOL,
                "coordinate_space": GNOME_SHELL_HELPER_COORDINATE_SPACE,
                "action": request.action.value,
                "target_token": request.target_token,
                "renderer": "gnome_shell_raster_frame",
                "cleanup_action": "explicit_clear",
                "shell_raster_frame": {
                    "requested_action": "clear",
                    "visible": False,
                    "target_token": request.target_token,
                    "cleanup_action": "explicit_clear",
                },
            }
        if request.shell_raster_frame is not None:
            frame_rect = request.shell_raster_frame.frame_rect.to_payload()
            return _presentation_payload(
                request,
                requested_rect=frame_rect,
                applied_rect=frame_rect,
                renderer="gnome_shell_raster_frame",
                shell_raster_frame={
                    "frame_version": request.shell_raster_frame.frame_version,
                    "frame_rect": frame_rect,
                },
            )
        return _presentation_payload(request)

    first = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        shell_raster_frame_provider=provider,
        shell_raster_runtime_enabled=True,
        suppress_pyqt_fallback_on_shell_raster_failure=True,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )
    clock.now += 12.0
    second = run_gnome_shell_helper_presentation_cycle(
        previous_surface_action="hidden",
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_target_window(contentRect=None, decorationInsets=None)),
        fetch_presentation=fetch_presentation,
        prepare_surface=lambda preparation: surface_preparations.append(preparation) or True,
        shell_raster_frame_provider=provider,
        shell_raster_runtime_enabled=True,
        suppress_pyqt_fallback_on_shell_raster_failure=True,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )
    clock.now += 0.5
    third = run_gnome_shell_helper_presentation_cycle(
        previous_surface_action="hidden",
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_target_window(contentRect=None, decorationInsets=None)),
        fetch_presentation=fetch_presentation,
        prepare_surface=lambda preparation: surface_preparations.append(preparation) or True,
        shell_raster_frame_provider=provider,
        shell_raster_runtime_enabled=True,
        suppress_pyqt_fallback_on_shell_raster_failure=True,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )

    assert first.shell_raster_frame_presented is True
    assert first.should_show_overlay is False
    assert second.should_show_overlay is False
    assert second.surface_preparation_action == "stabilizing"
    assert third.should_show_overlay is True
    assert third.request is not None
    assert third.request.renderer == "pyqt"
    assert third.request.shell_raster_frame is None
    assert third.request.rect_source == GNOME_SHELL_HELPER_RECT_SOURCE_FRAME_FALLBACK
    assert second.shell_raster_transition_clear_requested is True
    assert second.shell_raster_transition_clear_succeeded is True
    assert second.transition_action == ""
    assert third.shell_raster_transition_clear_requested is False
    assert len(calls) == 3
    assert calls[1].shell_raster_frame is not None
    assert calls[1].shell_raster_frame.action == "clear"
    assert calls[2].renderer == "pyqt"
    assert calls[2].shell_raster_frame is None
    assert surface_preparations
    assert surface_preparations[-1].mode == GNOME_HELPER_SURFACE_PREPARATION_MANAGED_WINDOWED


def test_default_guard_transient_fullscreen_handoff_holds_raster_without_managed_preparation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(GNOME_HELPER_FULLSCREEN_HANDOFF_GUARD_ENV)
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    calls: list[HelperPresentationRequest] = []
    preparations = []
    target = _borderless_target()

    def provider(target_status, request, _include_diagnostics) -> ShellRasterFrameBuildResult:
        current = target_status.target if target_status is not None else None
        if current is None or not current.fullscreen or request is None or request.content_rect is None:
            return ShellRasterFrameBuildResult(reason="target_not_fullscreen")
        rect = request.content_rect
        return ShellRasterFrameBuildResult(
            request=HelperRasterFrameRequest(
                action="update",
                frame_version="phase19-transient",
                target_token=request.target_token,
                target_rect=rect,
                frame_rect=rect,
                scale=1.0,
                image_path="/tmp/phase19-transient.png",
                checksum="phase19",
                byte_size=123,
                stale_timeout_ms=SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS,
            )
        )

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        calls.append(request)
        assert request.shell_raster_frame is not None
        rect = request.shell_raster_frame.frame_rect.to_payload()
        return _presentation_payload(
            request,
            requested_rect=rect,
            applied_rect=rect,
            renderer="gnome_shell_raster_frame",
            shell_raster_frame={"frame_rect": rect},
        )

    def run_cycle():
        return run_gnome_shell_helper_presentation_cycle(
            fetch_health=_health_payload,
            fetch_target=lambda: _target_payload(target),
            fetch_presentation=fetch_presentation,
            prepare_surface=lambda preparation: preparations.append(preparation) or True,
            shell_raster_frame_provider=provider,
            shell_raster_runtime_enabled=True,
            suppress_pyqt_fallback_on_shell_raster_failure=True,
            clock=clock,
            runtime_state=state,
            health_cache_jitter_seconds=lambda: 0.0,
        )

    fullscreen = run_cycle()
    clock.now += 0.2
    target = _borderless_target(
        frameRect={"x": 0, "y": 29, "width": 3440, "height": 1411},
        bufferRect={"x": 0, "y": 29, "width": 3440, "height": 1411},
        contentRect={"x": 0, "y": 29, "width": 3440, "height": 1411},
        fullscreen=False,
    )
    pending = run_cycle()
    clock.now += 0.2
    target = _borderless_target(
        frameRect={"x": 3440, "y": 0, "width": 3440, "height": 1440},
        bufferRect={"x": 3440, "y": 0, "width": 3440, "height": 1440},
        contentRect={"x": 3440, "y": 0, "width": 3440, "height": 1440},
        monitor=1,
        outputName="HDMI-1",
        monitorRect={"x": 3440, "y": 0, "width": 3440, "height": 1440},
    )
    restored = run_cycle()
    clock.now += 0.2
    target = dict(target, targetToken="meta:22")
    replaced = run_cycle()

    assert fullscreen.transition_action == "commit_raster"
    assert pending.transition_action == "hold_raster"
    assert pending.transition_state == "pending_fullscreen_handoff"
    assert pending.presentation_skipped is True
    assert pending.shell_raster_transition_clear_requested is False
    assert restored.transition_action == "commit_raster"
    assert restored.managed_surface_reset_requested is True
    assert replaced.transition_action == "hide_all"
    assert replaced.transition_reason == "target_token_replaced"
    assert replaced.shell_raster_transition_clear_requested is True
    assert len(calls) == 3
    assert preparations == []
    assert all(call.shell_raster_frame is not None for call in calls)
    assert calls[-1].shell_raster_frame.action == "clear"


def test_guarded_persistent_fullscreen_loss_clears_before_managed_preparation_and_attach(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(GNOME_HELPER_FULLSCREEN_HANDOFF_GUARD_ENV, "1")
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    calls: list[HelperPresentationRequest] = []
    preparations = []
    events: list[str] = []
    target = _borderless_target()

    def provider(target_status, request, _include_diagnostics) -> ShellRasterFrameBuildResult:
        current = target_status.target if target_status is not None else None
        if current is None or not current.fullscreen or request is None or request.content_rect is None:
            return ShellRasterFrameBuildResult(reason="target_not_fullscreen")
        rect = request.content_rect
        return ShellRasterFrameBuildResult(
            request=HelperRasterFrameRequest(
                action="update",
                frame_version="phase19-persistent",
                target_token=request.target_token,
                target_rect=rect,
                frame_rect=rect,
                scale=1.0,
                image_path="/tmp/phase19-persistent.png",
                checksum="phase19",
                byte_size=123,
                stale_timeout_ms=SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS,
            )
        )

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        calls.append(request)
        frame = request.shell_raster_frame
        if frame is not None and frame.action == "clear":
            events.append("clear")
            return {"status": "shell_raster_frame_cleared"}
        if frame is not None:
            events.append("raster_attach")
            rect = frame.frame_rect.to_payload()
            return _presentation_payload(
                request,
                requested_rect=rect,
                applied_rect=rect,
                renderer="gnome_shell_raster_frame",
                shell_raster_frame={"frame_rect": rect},
            )
        events.append("managed_attach")
        return _presentation_payload(request)

    def run_cycle():
        return run_gnome_shell_helper_presentation_cycle(
            previous_surface_action="hidden",
            fetch_health=_health_payload,
            fetch_target=lambda: _target_payload(target),
            fetch_presentation=fetch_presentation,
            prepare_surface=lambda preparation: events.append("prepare") or preparations.append(preparation) or True,
            shell_raster_frame_provider=provider,
            shell_raster_runtime_enabled=True,
            suppress_pyqt_fallback_on_shell_raster_failure=True,
            clock=clock,
            runtime_state=state,
            health_cache_jitter_seconds=lambda: 0.0,
        )

    run_cycle()
    events.clear()
    target = _borderless_target(
        frameRect={"x": 0, "y": 29, "width": 3440, "height": 1411},
        bufferRect={"x": 0, "y": 29, "width": 3440, "height": 1411},
        contentRect={"x": 0, "y": 29, "width": 3440, "height": 1411},
        fullscreen=False,
    )
    clock.now += 0.1
    first_pending = run_cycle()
    clock.now += 1.4
    second_pending = run_cycle()
    clock.now += 0.1
    stabilizing = run_cycle()
    clock.now += 0.1
    committed = run_cycle()

    assert first_pending.transition_action == "hold_raster"
    assert second_pending.transition_action == "hold_raster"
    assert stabilizing.transition_action == "commit_managed"
    assert stabilizing.surface_preparation_action == "stabilizing"
    assert stabilizing.shell_raster_transition_clear_requested is True
    assert stabilizing.shell_raster_transition_clear_succeeded is True
    assert committed.transition_action == "commit_managed"
    assert len(preparations) == 1
    assert events == ["clear", "prepare", "managed_attach"]
    assert [call.renderer for call in calls] == [
        "gnome_shell_raster_frame",
        "gnome_shell_raster_frame",
        "pyqt",
    ]
    assert calls[-2].shell_raster_frame is not None
    assert calls[-2].shell_raster_frame.action == "clear"


def test_selected_shell_raster_windowed_startup_uses_managed_pyqt_without_clear(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, raising=False)
    monkeypatch.delenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, raising=False)
    calls: list[HelperPresentationRequest] = []
    surface_preparations = []

    def provider(*_args, **_kwargs) -> ShellRasterFrameBuildResult:
        return ShellRasterFrameBuildResult(reason="target_not_fullscreen")

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        calls.append(request)
        return _presentation_payload(request)

    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()

    first = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_target_window(contentRect=None, decorationInsets=None)),
        fetch_presentation=fetch_presentation,
        prepare_surface=lambda preparation: surface_preparations.append(preparation) or True,
        shell_raster_frame_provider=provider,
        shell_raster_runtime_enabled=True,
        suppress_pyqt_fallback_on_shell_raster_failure=True,
        clock=clock,
        runtime_state=state,
    )
    clock.now += 0.5
    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_target_window(contentRect=None, decorationInsets=None)),
        fetch_presentation=fetch_presentation,
        prepare_surface=lambda preparation: surface_preparations.append(preparation) or True,
        shell_raster_frame_provider=provider,
        shell_raster_runtime_enabled=True,
        suppress_pyqt_fallback_on_shell_raster_failure=True,
        clock=clock,
        runtime_state=state,
    )

    assert first.should_show_overlay is False
    assert first.surface_preparation_action == "stabilizing"
    assert result.should_show_overlay is True
    assert result.shell_raster_transition_clear_requested is False
    assert result.request is not None
    assert result.request.renderer == "pyqt"
    assert result.request.shell_raster_frame is None
    assert calls == [result.request]
    assert surface_preparations
    assert surface_preparations[-1].mode == GNOME_HELPER_SURFACE_PREPARATION_MANAGED_WINDOWED


def test_selected_shell_raster_windowed_title_bar_compensation_offsets_managed_pyqt_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, raising=False)
    monkeypatch.delenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, raising=False)
    calls: list[HelperPresentationRequest] = []
    surface_preparations = []

    def provider(*_args, **_kwargs) -> ShellRasterFrameBuildResult:
        return ShellRasterFrameBuildResult(reason="target_not_fullscreen")

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        calls.append(request)
        return _presentation_payload(request)

    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    first = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_target_window(contentRect=None, decorationInsets=None)),
        fetch_presentation=fetch_presentation,
        prepare_surface=lambda preparation: surface_preparations.append(preparation) or True,
        shell_raster_frame_provider=provider,
        shell_raster_runtime_enabled=True,
        suppress_pyqt_fallback_on_shell_raster_failure=True,
        title_bar_compensation_enabled=True,
        title_bar_compensation_height=30,
        clock=clock,
        runtime_state=state,
    )
    clock.now += 0.5
    result = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_target_window(contentRect=None, decorationInsets=None)),
        fetch_presentation=fetch_presentation,
        prepare_surface=lambda preparation: surface_preparations.append(preparation) or True,
        shell_raster_frame_provider=provider,
        shell_raster_runtime_enabled=True,
        suppress_pyqt_fallback_on_shell_raster_failure=True,
        title_bar_compensation_enabled=True,
        title_bar_compensation_height=30,
        clock=clock,
        runtime_state=state,
    )

    assert first.should_show_overlay is False
    assert result.should_show_overlay is True
    assert result.request is not None
    assert result.request.rect_source == GNOME_SHELL_HELPER_RECT_SOURCE_FRAME_FALLBACK
    assert result.request.content_rect == HelperRect(1080, 246, 1280, 967)
    assert calls == [result.request]
    assert surface_preparations
    assert surface_preparations[-1].mode == GNOME_HELPER_SURFACE_PREPARATION_MANAGED_WINDOWED
    assert surface_preparations[-1].rect == (1080, 246, 1280, 967)


def test_managed_window_focus_changes_refresh_presentation_without_repreparing_surface() -> None:
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    target = _target_window()
    preparations = []
    presentation_calls: list[HelperPresentationRequest] = []

    def run_cycle():
        result = run_gnome_shell_helper_presentation_cycle(
            fetch_health=_health_payload,
            fetch_target=lambda: _target_payload(target),
            fetch_presentation=lambda request: presentation_calls.append(request) or _presentation_payload(request),
            prepare_surface=lambda preparation: preparations.append(preparation) or True,
            shell_raster_frame_provider=lambda *_args: ShellRasterFrameBuildResult(reason="target_not_fullscreen"),
            shell_raster_runtime_enabled=True,
            suppress_pyqt_fallback_on_shell_raster_failure=True,
            clock=clock,
            runtime_state=state,
            health_cache_jitter_seconds=lambda: 0.0,
        )
        clock.now += 0.5
        return result

    assert run_cycle().surface_preparation_action == "stabilizing"
    assert run_cycle().surface_preparation_action == "apply"
    target["hasFocus"] = False
    unfocused = run_cycle()
    target["hasFocus"] = True
    refocused = run_cycle()

    assert unfocused.target_status is not None
    assert unfocused.target_status.target is not None
    assert unfocused.target_status.target.has_focus is False
    assert unfocused.surface_preparation_action == "reused"
    assert refocused.surface_preparation_action == "reused"
    assert len(preparations) == 1
    assert len(presentation_calls) == 3


def test_managed_window_monitor_change_stabilizes_and_transient_monitor_sample_is_ignored() -> None:
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    current_target = _target_window()
    preparations = []

    def run_cycle():
        result = run_gnome_shell_helper_presentation_cycle(
            fetch_health=_health_payload,
            fetch_target=lambda: _target_payload(current_target),
            fetch_presentation=_presentation_payload,
            prepare_surface=lambda preparation: preparations.append(preparation) or True,
            shell_raster_frame_provider=lambda *_args: ShellRasterFrameBuildResult(reason="target_not_fullscreen"),
            shell_raster_runtime_enabled=True,
            suppress_pyqt_fallback_on_shell_raster_failure=True,
            clock=clock,
            runtime_state=state,
            health_cache_jitter_seconds=lambda: 0.0,
        )
        clock.now += 0.5
        return result

    run_cycle()
    run_cycle()
    hdmi_target = _target_window(
        frameRect={"x": 4520, "y": 216, "width": 1280, "height": 997},
        bufferRect={"x": 4506, "y": 204, "width": 1308, "height": 1026},
        contentRect={"x": 4520, "y": 253, "width": 1280, "height": 960},
        monitor=1,
        outputName="HDMI-1",
        monitorRect={"x": 3440, "y": 0, "width": 3440, "height": 1440},
    )

    current_target = hdmi_target
    transient = run_cycle()
    current_target = _target_window()
    settled_back = run_cycle()

    assert transient.surface_preparation_action == "stabilizing"
    assert transient.should_show_overlay is False
    assert settled_back.surface_preparation_action == "reused"
    assert len(preparations) == 1

    current_target = hdmi_target
    first_hdmi = run_cycle()
    second_hdmi = run_cycle()

    assert first_hdmi.surface_preparation_action == "stabilizing"
    assert second_hdmi.surface_preparation_action == "apply"
    assert len(preparations) == 2
    assert preparations[-1].target_monitor == 1
    assert preparations[-1].target_output_name == "HDMI-1"
    assert preparations[-1].target_monitor_rect == (3440, 0, 3440, 1440)

    current_target = dict(hdmi_target, targetToken="meta:22")
    assert run_cycle().surface_preparation_action == "stabilizing"
    assert run_cycle().surface_preparation_action == "apply"
    assert len(preparations) == 3
    assert preparations[-1].target_token == "meta:22"


def test_managed_window_negative_monitor_coordinates_are_valid() -> None:
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    target = _target_window(
        frameRect={"x": -1700, "y": -860, "width": 1280, "height": 997},
        bufferRect={"x": -1714, "y": -872, "width": 1308, "height": 1026},
        contentRect={"x": -1700, "y": -823, "width": 1280, "height": 960},
        monitor=2,
        outputName="DP-3",
        monitorRect={"x": -1920, "y": -1080, "width": 1920, "height": 1080},
    )
    preparations = []

    for _ in range(2):
        result = run_gnome_shell_helper_presentation_cycle(
            fetch_health=_health_payload,
            fetch_target=lambda: _target_payload(target),
            fetch_presentation=_presentation_payload,
            prepare_surface=lambda preparation: preparations.append(preparation) or True,
            shell_raster_frame_provider=lambda *_args: ShellRasterFrameBuildResult(reason="target_not_fullscreen"),
            shell_raster_runtime_enabled=True,
            suppress_pyqt_fallback_on_shell_raster_failure=True,
            clock=clock,
            runtime_state=state,
            health_cache_jitter_seconds=lambda: 0.0,
        )
        clock.now += 0.5

    assert result.surface_preparation_action == "apply"
    assert len(preparations) == 1
    assert preparations[0].rect == (-1700, -823, 1280, 960)
    assert preparations[0].target_monitor_rect == (-1920, -1080, 1920, 1080)


def test_managed_window_surface_loss_recovery_is_bounded_and_forced() -> None:
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    preparations = []
    overlay_found = True
    target = _target_window()

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        return _presentation_payload(request, overlay_token="overlay:1" if overlay_found else "")

    def run_cycle():
        result = run_gnome_shell_helper_presentation_cycle(
            fetch_health=_health_payload,
            fetch_target=lambda: _target_payload(target),
            fetch_presentation=fetch_presentation,
            prepare_surface=lambda preparation: preparations.append(preparation) or True,
            shell_raster_frame_provider=lambda *_args: ShellRasterFrameBuildResult(reason="target_not_fullscreen"),
            shell_raster_runtime_enabled=True,
            suppress_pyqt_fallback_on_shell_raster_failure=True,
            clock=clock,
            runtime_state=state,
            health_cache_jitter_seconds=lambda: 0.0,
        )
        clock.now += 0.5
        return result

    run_cycle()
    run_cycle()
    overlay_found = False
    loss_results = []
    for index in range(5):
        target["hasFocus"] = bool(index % 2)
        loss_results.append(run_cycle())

    assert [result.surface_preparation_action for result in loss_results[:4]] == ["reused"] * 4
    assert loss_results[4].surface_preparation_action == "recovery"
    assert len(preparations) == 2
    assert preparations[-1].force_recovery is True


def test_failed_managed_window_preparation_is_not_cached_and_retries_with_backoff() -> None:
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    preparations = []
    preparation_succeeds = False

    def prepare_surface(preparation) -> bool:
        preparations.append(preparation)
        return preparation_succeeds

    def run_cycle():
        result = run_gnome_shell_helper_presentation_cycle(
            fetch_health=_health_payload,
            fetch_target=lambda: _target_payload(_target_window()),
            fetch_presentation=_presentation_payload,
            prepare_surface=prepare_surface,
            shell_raster_frame_provider=lambda *_args: ShellRasterFrameBuildResult(reason="target_not_fullscreen"),
            shell_raster_runtime_enabled=True,
            suppress_pyqt_fallback_on_shell_raster_failure=True,
            clock=clock,
            runtime_state=state,
            health_cache_jitter_seconds=lambda: 0.0,
        )
        clock.now += 0.5
        return result

    assert run_cycle().surface_preparation_action == "stabilizing"
    failed = run_cycle()
    backed_off = run_cycle()

    assert failed.surface_preparation_failed is True
    assert failed.surface_preparation_action == "failed"
    assert state.last_surface_preparation is None
    assert backed_off.surface_preparation_action == "retry_backoff"
    assert len(preparations) == 1

    preparation_succeeds = True
    clock.now = state.next_surface_preparation_retry_at
    recovered = run_cycle()

    assert recovered.surface_preparation_action == "apply"
    assert recovered.surface_preparation_failed is False
    assert state.last_surface_preparation is not None
    assert len(preparations) == 2


def test_managed_window_to_borderless_invalidates_pyqt_preparation_and_resumes_raster(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(GNOME_HELPER_FULLSCREEN_HANDOFF_GUARD_ENV, "1")
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    target = _target_window()
    preparations = []

    def provider(
        target_status,
        request: HelperPresentationRequest | None,
        _include_diagnostics: bool,
    ) -> ShellRasterFrameBuildResult:
        assert request is not None
        current = target_status.target if target_status is not None else None
        if current is None or not current.fullscreen:
            return ShellRasterFrameBuildResult(reason="target_not_fullscreen")
        rect = request.content_rect
        assert rect is not None
        return ShellRasterFrameBuildResult(
            request=HelperRasterFrameRequest(
                action="update",
                frame_version="test-windowed-to-borderless",
                target_token=request.target_token,
                target_rect=rect,
                frame_rect=HelperRect(rect.x + 10, rect.y + 10, rect.width - 20, rect.height - 20),
                scale=1.0,
                image_path="/tmp/test-windowed-to-borderless.png",
                checksum="windowed-to-borderless",
                byte_size=123,
                stale_timeout_ms=SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS,
            )
        )

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        if request.shell_raster_frame is None:
            return _presentation_payload(request)
        frame_rect = request.shell_raster_frame.frame_rect.to_payload()
        return _presentation_payload(
            request,
            requested_rect=frame_rect,
            applied_rect=frame_rect,
            renderer="gnome_shell_raster_frame",
            shell_raster_frame={
                "frame_version": request.shell_raster_frame.frame_version,
                "frame_rect": frame_rect,
            },
        )

    for _ in range(2):
        windowed = run_gnome_shell_helper_presentation_cycle(
            fetch_health=_health_payload,
            fetch_target=lambda: _target_payload(target),
            fetch_presentation=fetch_presentation,
            prepare_surface=lambda preparation: preparations.append(preparation) or True,
            shell_raster_frame_provider=provider,
            shell_raster_runtime_enabled=True,
            suppress_pyqt_fallback_on_shell_raster_failure=True,
            clock=clock,
            runtime_state=state,
            health_cache_jitter_seconds=lambda: 0.0,
        )
        clock.now += 0.5

    target = _borderless_target()
    borderless = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(target),
        fetch_presentation=fetch_presentation,
        prepare_surface=lambda preparation: preparations.append(preparation) or True,
        shell_raster_frame_provider=provider,
        shell_raster_runtime_enabled=True,
        suppress_pyqt_fallback_on_shell_raster_failure=True,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )

    assert windowed.should_show_overlay is True
    assert len(preparations) == 1
    assert borderless.shell_raster_frame_presented is True
    assert borderless.should_show_overlay is False
    assert borderless.surface_preparation is None
    assert borderless.surface_preparation_action == "invalidated"
    assert borderless.transition_action == "commit_raster"
    assert borderless.managed_surface_reset_requested is True
    assert state.last_surface_preparation is None


def test_selected_shell_raster_windowed_transition_blocks_pyqt_when_clear_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(GNOME_HELPER_SHELL_RASTER_BRIDGE_ENV, raising=False)
    monkeypatch.delenv(GNOME_HELPER_SHELL_RASTER_RUNTIME_ENV, raising=False)
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    calls: list[HelperPresentationRequest] = []

    def provider(
        target_status,
        request: HelperPresentationRequest | None,
        _include_diagnostics: bool,
    ) -> ShellRasterFrameBuildResult:
        assert request is not None
        target = target_status.target if target_status is not None else None
        if target is None or not target.fullscreen:
            return ShellRasterFrameBuildResult(reason="target_not_fullscreen")
        rect = request.content_rect
        assert rect is not None
        return ShellRasterFrameBuildResult(
            request=HelperRasterFrameRequest(
                action="update",
                frame_version="test-selected-raster",
                target_token=request.target_token,
                target_rect=rect,
                frame_rect=HelperRect(rect.x + 10, rect.y + 10, rect.width - 20, rect.height - 20),
                scale=1.0,
                image_path="/tmp/test-selected-raster.png",
                checksum="abc123",
                byte_size=123,
                stale_timeout_ms=SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS,
            )
        )

    def fetch_presentation(request: HelperPresentationRequest) -> dict[str, object]:
        calls.append(request)
        if request.shell_raster_frame is not None and request.shell_raster_frame.action == "clear":
            raise RuntimeError("clear failed")
        if request.shell_raster_frame is not None:
            frame_rect = request.shell_raster_frame.frame_rect.to_payload()
            return _presentation_payload(
                request,
                requested_rect=frame_rect,
                applied_rect=frame_rect,
                renderer="gnome_shell_raster_frame",
                shell_raster_frame={
                    "frame_version": request.shell_raster_frame.frame_version,
                    "frame_rect": frame_rect,
                },
            )
        return _presentation_payload(request)

    first = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_borderless_target()),
        fetch_presentation=fetch_presentation,
        shell_raster_frame_provider=provider,
        shell_raster_runtime_enabled=True,
        suppress_pyqt_fallback_on_shell_raster_failure=True,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )
    clock.now += 12.0
    second = run_gnome_shell_helper_presentation_cycle(
        previous_surface_action="hidden",
        fetch_health=_health_payload,
        fetch_target=lambda: _target_payload(_target_window(contentRect=None, decorationInsets=None)),
        fetch_presentation=fetch_presentation,
        shell_raster_frame_provider=provider,
        shell_raster_runtime_enabled=True,
        suppress_pyqt_fallback_on_shell_raster_failure=True,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )

    assert first.shell_raster_frame_presented is True
    assert second.should_show_overlay is False
    assert second.shell_raster_transition_clear_requested is True
    assert second.shell_raster_transition_clear_succeeded is False
    assert len(calls) == 2
    assert calls[1].shell_raster_frame is not None
    assert calls[1].shell_raster_frame.action == "clear"


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


def test_presentation_cycle_refresh_request_bypasses_matching_cache_once() -> None:
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
    refreshed = run_gnome_shell_helper_presentation_cycle(
        presentation_refresh_requested=True,
        fetch_health=_health_payload,
        fetch_target=_target_payload,
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )
    clock.now += 0.5
    cached_again = run_gnome_shell_helper_presentation_cycle(
        fetch_health=_health_payload,
        fetch_target=_target_payload,
        fetch_presentation=fetch_presentation,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )

    assert first.presentation_skipped is False
    assert refreshed.presentation_skipped is False
    assert refreshed.attempts == 1
    assert cached_again.presentation_skipped is True
    assert cached_again.presentation_skip_reason == "fresh_matching_presentation"
    assert len(presentation_calls) == 2


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


def test_guarded_stable_target_query_uses_and_rearms_monotonic_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(GNOME_HELPER_FULLSCREEN_HANDOFF_GUARD_ENV, "1")
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

    def run_cycle():
        return run_gnome_shell_helper_presentation_cycle(
            previous_surface_action="mapped_suppressed",
            fetch_health=_health_payload,
            fetch_target=fetch_target,
            fetch_presentation=fetch_presentation,
            prepare_surface=lambda _preparation: True,
            shell_raster_frame_provider=lambda *_args: ShellRasterFrameBuildResult(
                reason="target_not_fullscreen"
            ),
            shell_raster_runtime_enabled=True,
            suppress_pyqt_fallback_on_shell_raster_failure=True,
            clock=clock,
            runtime_state=state,
            health_cache_jitter_seconds=lambda: 0.0,
        )

    assert run_cycle().surface_preparation_action == "stabilizing"
    clock.now += 0.5
    assert run_cycle().surface_preparation_action == "apply"
    clock.now += 0.5
    cached = run_cycle()
    clock.now += 1.0
    expired = run_cycle()
    clock.now += 0.5
    cached_again = run_cycle()

    assert cached.target_poll_skipped is True
    assert cached.presentation_skip_reason == "suppressed_poll_throttle"
    assert expired.target_poll_skipped is False
    assert expired.presentation_skip_reason == "fresh_matching_presentation"
    assert cached_again.target_poll_skipped is True
    assert target_calls == 3
    assert len(presentation_calls) == 1


def test_guarded_stable_target_query_explicit_refresh_bypasses_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(GNOME_HELPER_FULLSCREEN_HANDOFF_GUARD_ENV, "1")
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

    def run_cycle(*, refresh: bool = False):
        return run_gnome_shell_helper_presentation_cycle(
            previous_surface_action="mapped_suppressed",
            presentation_refresh_requested=refresh,
            fetch_health=_health_payload,
            fetch_target=fetch_target,
            fetch_presentation=fetch_presentation,
            prepare_surface=lambda _preparation: True,
            shell_raster_frame_provider=lambda *_args: ShellRasterFrameBuildResult(
                reason="target_not_fullscreen"
            ),
            shell_raster_runtime_enabled=True,
            suppress_pyqt_fallback_on_shell_raster_failure=True,
            clock=clock,
            runtime_state=state,
            health_cache_jitter_seconds=lambda: 0.0,
        )

    run_cycle()
    clock.now += 0.5
    run_cycle()
    clock.now += 0.5
    refreshed = run_cycle(refresh=True)
    clock.now += 0.5
    cached_again = run_cycle()

    assert refreshed.target_poll_skipped is False
    assert refreshed.presentation_skipped is False
    assert refreshed.attempts == 1
    assert cached_again.target_poll_skipped is True
    assert target_calls == 3
    assert len(presentation_calls) == 2


def test_suppressed_target_loss_clears_deadline_and_recovery_queries_immediately() -> None:
    clock = _Clock()
    state = GnomeHelperPresentationRuntimeState()
    targets = [
        _target_payload(_target_window(hasFocus=False)),
        {
            **_target_payload(),
            "status": "target_not_found",
            "target": None,
            "candidate_count": 0,
        },
        _target_payload(_target_window(hasFocus=False)),
    ]
    target_calls = 0

    def fetch_target() -> dict[str, object]:
        nonlocal target_calls
        target_calls += 1
        return targets.pop(0)

    first = run_gnome_shell_helper_presentation_cycle(
        previous_surface_action="mapped_suppressed",
        fetch_health=_health_payload,
        fetch_target=fetch_target,
        fetch_presentation=_presentation_payload,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )
    clock.now += 1.5
    lost = run_gnome_shell_helper_presentation_cycle(
        previous_surface_action="mapped_suppressed",
        fetch_health=_health_payload,
        fetch_target=fetch_target,
        fetch_presentation=_presentation_payload,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )
    clock.now += 0.1
    recovered = run_gnome_shell_helper_presentation_cycle(
        previous_surface_action="mapped_suppressed",
        fetch_health=_health_payload,
        fetch_target=fetch_target,
        fetch_presentation=_presentation_payload,
        clock=clock,
        runtime_state=state,
        health_cache_jitter_seconds=lambda: 0.0,
    )

    assert first.presentation_ready is True
    assert lost.target_found is False
    assert recovered.presentation_ready is True
    assert recovered.target_poll_skipped is False
    assert target_calls == 3


@pytest.mark.parametrize(
    ("target_overrides", "first_surface_action", "second_surface_action"),
    [
        ({"targetToken": "meta:22"}, "", ""),
        ({"frameRect": {"x": 1100, "y": 220, "width": 1280, "height": 997}}, "", ""),
        ({"bufferRect": {"x": 1086, "y": 208, "width": 1308, "height": 1026}}, "", ""),
        ({"monitorRect": {"x": 3440, "y": 0, "width": 3440, "height": 1440}}, "", ""),
        ({"monitor": 1}, "", ""),
        ({"outputName": "HDMI-1"}, "", ""),
        ({"monitorScale": 1.25}, "", ""),
        ({"hasFocus": False}, "", ""),
        ({"showingOnWorkspace": False}, "", ""),
        ({"workspace": "1"}, "", ""),
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
