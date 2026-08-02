from __future__ import annotations

from dataclasses import replace
import types
import os

import pytest

from overlay_client.overlay_client import OverlayWindow
from overlay_client.debug_config import DebugConfig
from overlay_client.client_config import InitialClientSettings
from PyQt6.QtWidgets import QApplication

from overlay_client.backend.helper_ipc import (
    HelperPresentationAction,
    HelperPresentationRequest,
    HelperRasterFrameRequest,
    HelperRect,
    HelperTargetState,
    HelperTargetStatus,
    HelperTargetWindow,
)
from overlay_client.backend.shell_raster_frame import ShellRasterFrameBuildResult


@pytest.fixture
def qt_app(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", os.getenv("QT_QPA_PLATFORM", "offscreen"))
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class DummyTimer:
    def __init__(self):
        self._active = False
        self.started = 0
        self.stopped = 0

    def isActive(self) -> bool:
        return self._active

    def start(self):
        self._active = True
        self.started += 1

    def stop(self):
        self._active = False
        self.stopped += 1


@pytest.fixture
def window(monkeypatch, qt_app):
    settings = InitialClientSettings()
    debug_config = DebugConfig(repaint_debounce_enabled=True, log_repaint_debounce=False)
    win = OverlayWindow(settings, debug_config)
    dummy_timer = DummyTimer()
    monkeypatch.setattr(win, "_repaint_timer", dummy_timer)
    monkeypatch.setattr(win, "update", types.MethodType(lambda self: setattr(self, "_updated", True), win))
    win._updated = False
    win._repaint_metrics["enabled"] = True
    return win


def test_should_bypass_debounce():
    assert OverlayWindow._should_bypass_debounce({"animate": True}) is True
    assert OverlayWindow._should_bypass_debounce({"ttl": 0.5}) is True
    assert OverlayWindow._should_bypass_debounce({"ttl": "0.7"}) is True
    assert OverlayWindow._should_bypass_debounce({"ttl": 2}) is False
    assert OverlayWindow._should_bypass_debounce({"ttl": "bad"}) is False
    assert OverlayWindow._should_bypass_debounce({}) is False


def test_request_repaint_immediate_bypasses_timer(window: OverlayWindow):
    timer = window._repaint_timer
    window._request_repaint("ingest", immediate=True)
    assert window._updated is True
    assert timer.started == 0


def test_request_repaint_refreshes_backend_when_content_is_suppressed(window: OverlayWindow):
    calls = []
    window._backend_presentation_content_suppressed = True

    def refresh(self):
        calls.append(("refresh", self._backend_presentation_refresh_requested))
        return True

    window._refresh_backend_presentation = types.MethodType(refresh, window)

    window._request_repaint("ingest", immediate=True)

    assert calls == [("refresh", True)]


def test_debounced_repaint_refreshes_backend_when_content_is_suppressed(window: OverlayWindow):
    calls = []
    window._backend_presentation_content_suppressed = True
    window._refresh_backend_presentation = types.MethodType(lambda self: calls.append("refresh") or True, window)

    window._trigger_debounced_repaint()

    assert calls == ["refresh"]
    assert window._updated is True


def test_request_repaint_uses_timer_when_enabled(window: OverlayWindow):
    timer = window._repaint_timer
    window._request_repaint("ingest", immediate=False)
    assert window._updated is False
    assert timer.started == 1
    assert timer.isActive() is True


def test_request_repaint_disables_debounce_when_configured(window: OverlayWindow):
    window._repaint_debounce_enabled = False
    timer = window._repaint_timer
    window._updated = False
    window._request_repaint("ingest", immediate=False)
    assert window._updated is True
    assert timer.started == 0


def test_repaint_attribution_distinguishes_scheduling_paths(window: OverlayWindow) -> None:
    timer = window._repaint_timer

    window._request_repaint("ingest", immediate=False)
    window._request_repaint("ingest", immediate=False)
    window._request_repaint("explicit_refresh", immediate=True)

    counts = window._repaint_metrics["counts"]
    assert counts["total"] == 3
    assert counts["ingest"] == 2
    assert counts["explicit_refresh"] == 1
    assert counts["debounce_started"] == 1
    assert counts["debounce_coalesced"] == 1
    assert counts["immediate"] == 1
    assert counts["qt_update"] == 1
    assert counts["backend_refresh"] == 0
    assert timer.started == 1
    assert timer.stopped == 1


def test_repaint_attribution_counts_saturate(window: OverlayWindow) -> None:
    counts = window._repaint_metrics["counts"]
    counts["total"] = window._REPAINT_COUNT_MAX

    window._request_repaint("ingest", immediate=True)

    assert counts["total"] == window._REPAINT_COUNT_MAX


def _shell_target_and_request() -> tuple[HelperTargetStatus, HelperPresentationRequest]:
    rect = HelperRect(0, 0, 1920, 1080)
    target = HelperTargetWindow(
        target_token="target-1",
        title="Elite Dangerous",
        content_rect=rect,
        frame_rect=rect,
        buffer_rect=rect,
        monitor=0,
        output_name="Display-1",
        monitor_rect=rect,
        monitor_scale=1.0,
        has_focus=True,
        showing_on_workspace=True,
        minimized=False,
        fullscreen=True,
        workspace="workspace-1",
    )
    status = HelperTargetStatus(state=HelperTargetState.FOUND, target=target)
    request = HelperPresentationRequest(
        action=HelperPresentationAction.ATTACH,
        target_token=target.target_token,
        content_rect=rect,
    )
    return status, request


def _shell_frame_result(*, eligible: bool = True, reason: str = "") -> ShellRasterFrameBuildResult:
    if not eligible:
        return ShellRasterFrameBuildResult(eligible=False, reason=reason or "frame_export_failed")
    rect = HelperRect(0, 0, 1920, 1080)
    frame = HelperRasterFrameRequest(
        action="update",
        frame_version="frame-v1",
        target_token="target-1",
        target_rect=rect,
        frame_rect=rect,
        scale=1.0,
        image_path="/tmp/frame.png",
        checksum="a" * 64,
        byte_size=100,
        stale_timeout_ms=1500,
        diagnostics={
            "cache_hit": False,
            "frame_preparation_skipped": False,
            "frame_preparation_skip_reason": "",
        },
    )
    return ShellRasterFrameBuildResult(request=frame, eligible=True, diagnostics=frame.diagnostics)


def _install_shell_frame_builder(
    monkeypatch: pytest.MonkeyPatch,
    window: OverlayWindow,
    results: list[ShellRasterFrameBuildResult],
) -> list[tuple[object, object]]:
    calls: list[tuple[object, object]] = []
    monkeypatch.setattr(window, "_prepare_shell_raster_payload_results", lambda: {"commands": [object()]})
    monkeypatch.setattr(window, "_shell_raster_crop_contributor_snapshot", lambda _results: (object(),))

    def build(target_status, request, **_kwargs):
        calls.append((target_status, request))
        index = min(len(calls) - 1, len(results) - 1)
        return results[index]

    monkeypatch.setattr(
        "overlay_client.backend.shell_raster_frame.build_multi_region_real_content_shell_raster_frame_request",
        build,
    )
    return calls


def test_shell_frame_preparation_reuses_proven_equal_visual_and_target_state(
    monkeypatch: pytest.MonkeyPatch,
    window: OverlayWindow,
) -> None:
    status, request = _shell_target_and_request()
    calls = _install_shell_frame_builder(monkeypatch, window, [_shell_frame_result()])

    first = window._build_backend_shell_raster_content_frame(status, request, include_diagnostics=True)
    second = window._build_backend_shell_raster_content_frame(status, request, include_diagnostics=True)

    assert len(calls) == 1
    assert first.request is not None
    assert second.request is not None
    assert second.request.diagnostics is not None
    assert second.request.diagnostics["frame_preparation_skipped"] is True
    assert second.request.diagnostics["frame_preparation_skip_reason"] == "unchanged_visual"
    assert window._shell_raster_frame_work_counts == {
        "requests": 2,
        "builds": 1,
        "unchanged_reuses": 1,
        "uncacheable": 0,
        "failures": 0,
    }


@pytest.mark.parametrize(
    "change",
    ["content", "scale", "mode", "monitor", "workspace", "visibility", "geometry", "diagnostics"],
)
def test_shell_frame_preparation_invalidates_every_render_or_target_trigger(
    monkeypatch: pytest.MonkeyPatch,
    window: OverlayWindow,
    change: str,
) -> None:
    status, request = _shell_target_and_request()
    calls = _install_shell_frame_builder(monkeypatch, window, [_shell_frame_result(), _shell_frame_result()])
    first_diagnostics = True
    second_status = status
    second_request = request
    second_diagnostics = True

    window._build_backend_shell_raster_content_frame(status, request, include_diagnostics=first_diagnostics)
    target = status.target
    assert target is not None
    if change == "content":
        window._mark_legacy_cache_dirty()
    elif change == "scale":
        second_status = replace(status, target=replace(target, monitor_scale=1.25))
    elif change == "mode":
        second_status = replace(status, target=replace(target, fullscreen=False))
    elif change == "monitor":
        second_status = replace(status, target=replace(target, monitor=1, output_name="Display-2"))
    elif change == "workspace":
        second_status = replace(status, target=replace(target, workspace="workspace-2"))
    elif change == "visibility":
        second_status = replace(status, target=replace(target, showing_on_workspace=False))
    elif change == "geometry":
        moved = HelperRect(1920, 0, 1920, 1080)
        second_status = replace(status, target=replace(target, content_rect=moved, monitor_rect=moved))
        second_request = replace(request, content_rect=moved)
    elif change == "diagnostics":
        second_diagnostics = False

    window._build_backend_shell_raster_content_frame(
        second_status,
        second_request,
        include_diagnostics=second_diagnostics,
    )

    assert len(calls) == 2


def test_shell_frame_preparation_does_not_cache_unknown_or_failed_state(
    monkeypatch: pytest.MonkeyPatch,
    window: OverlayWindow,
) -> None:
    _status, request = _shell_target_and_request()
    calls = _install_shell_frame_builder(
        monkeypatch,
        window,
        [_shell_frame_result(eligible=False), _shell_frame_result(eligible=False)],
    )

    window._build_backend_shell_raster_content_frame(None, request, include_diagnostics=True)
    window._build_backend_shell_raster_content_frame(None, request, include_diagnostics=True)

    assert len(calls) == 2
    assert window._shell_raster_frame_work_counts["uncacheable"] == 2
    assert window._shell_raster_frame_work_counts["failures"] == 2
