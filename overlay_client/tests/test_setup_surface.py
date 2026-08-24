from __future__ import annotations

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPaintEvent, QPainter, QShowEvent
from PyQt6.QtWidgets import QApplication

from overlay_client.client_config import InitialClientSettings
from overlay_client.debug_config import DebugConfig
import overlay_client.overlay_client as overlay_client_module
from overlay_client.overlay_client import OverlayWindow, _LINE_WIDTH_DEFAULTS


class _RecordingPainter:
    """Small painter seam for verifying paint-event operation order."""

    CompositionMode = QPainter.CompositionMode
    RenderHint = QPainter.RenderHint
    instances: list["_RecordingPainter"] = []

    def __init__(self, _widget) -> None:
        self.operations: list[tuple[str, object]] = []
        self.composition_mode = None
        self.__class__.instances.append(self)

    def setCompositionMode(self, mode) -> None:
        self.composition_mode = mode
        self.operations.append(("composition", mode))

    def fillRect(self, _rect, color) -> None:
        self.operations.append(("fill", color))

    def setRenderHint(self, hint) -> None:
        self.operations.append(("render_hint", hint))

    def end(self) -> None:
        self.operations.append(("end", None))


@pytest.fixture
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.mark.pyqt_required
def test_setup_surface_initialises_defaults(qt_app):
    window = OverlayWindow(InitialClientSettings(), DebugConfig())
    try:
        assert window._gridline_spacing == 120
        assert window._line_width_defaults == _LINE_WIDTH_DEFAULTS
        assert window._text_cache == {}
        assert window._text_cache_generation == 0
        assert window._repaint_timer.interval() == window._REPAINT_DEBOUNCE_MS
        assert window._legacy_timer.isActive()
        assert window._backend_presentation_content_suppressed is False
    finally:
        window._legacy_timer.stop()
        window._modifier_timer.stop()
        window._tracking_timer.stop()
        window.close()


@pytest.mark.pyqt_required
def test_setup_surface_forces_linux_standalone_setting_off(monkeypatch, qt_app):
    monkeypatch.setattr("overlay_client.setup_surface.sys.platform", "linux")
    window = OverlayWindow(InitialClientSettings(standalone_mode=True), DebugConfig())
    try:
        assert window._standalone_mode is False
    finally:
        window._legacy_timer.stop()
        window._modifier_timer.stop()
        window._tracking_timer.stop()
        window.close()


@pytest.mark.pyqt_required
def test_show_event_delegates_to_setup_surface(monkeypatch, qt_app):
    window = OverlayWindow(InitialClientSettings(), DebugConfig())
    try:
        calls = []
        monkeypatch.setattr(window, "_apply_legacy_scale", lambda: calls.append("scale"))
        monkeypatch.setattr(window._platform_controller, "prepare_window", lambda _handle: calls.append("prepare"))
        monkeypatch.setattr(window._platform_controller, "apply_click_through", lambda transparent: calls.append(("click", transparent)))

        window.showEvent(QShowEvent())

        assert "scale" in calls
        assert "prepare" in calls
        assert ("click", True) in calls
    finally:
        window._legacy_timer.stop()
        window._modifier_timer.stop()
        window._tracking_timer.stop()
        window.close()


@pytest.mark.pyqt_required
def test_paint_event_clears_before_normal_overlay_draw_and_preserves_paint_count(monkeypatch, qt_app):
    window = OverlayWindow(InitialClientSettings(), DebugConfig())
    try:
        _RecordingPainter.instances = []
        monkeypatch.setattr(overlay_client_module, "QPainter", _RecordingPainter)
        monkeypatch.setattr(
            window,
            "_paint_overlay",
            lambda painter: painter.operations.append(("overlay", painter.composition_mode)),
        )
        window._paint_stats = {"paint_count": 7}
        event = QPaintEvent(window.rect())

        window.paintEvent(event)

        painter = _RecordingPainter.instances[-1]
        assert painter.operations == [
            ("composition", QPainter.CompositionMode.CompositionMode_Clear),
            ("fill", Qt.GlobalColor.transparent),
            ("composition", QPainter.CompositionMode.CompositionMode_SourceOver),
            ("render_hint", QPainter.RenderHint.Antialiasing),
            ("overlay", QPainter.CompositionMode.CompositionMode_SourceOver),
            ("end", None),
        ]
        assert window._paint_stats["paint_count"] == 8
    finally:
        window._legacy_timer.stop()
        window._modifier_timer.stop()
        window._tracking_timer.stop()
        window.close()


@pytest.mark.pyqt_required
def test_paint_event_clears_once_and_skips_overlay_when_backend_content_suppressed(monkeypatch, qt_app):
    window = OverlayWindow(InitialClientSettings(), DebugConfig())
    try:
        _RecordingPainter.instances = []
        monkeypatch.setattr(overlay_client_module, "QPainter", _RecordingPainter)
        captured = []
        window._backend_presentation_content_suppressed = True
        monkeypatch.setattr(window, "_paint_overlay", lambda painter: captured.append(painter))
        window._paint_stats = {"paint_count": 2}
        event = QPaintEvent(window.rect())

        window.paintEvent(event)

        assert captured == []
        painter = _RecordingPainter.instances[-1]
        assert painter.operations == [
            ("composition", QPainter.CompositionMode.CompositionMode_Clear),
            ("fill", Qt.GlobalColor.transparent),
            ("composition", QPainter.CompositionMode.CompositionMode_SourceOver),
            ("end", None),
        ]
        assert window._paint_stats["paint_count"] == 3
    finally:
        window._legacy_timer.stop()
        window._modifier_timer.stop()
        window._tracking_timer.stop()
        window.close()


@pytest.mark.pyqt_required
def test_repeated_normal_paints_each_start_from_a_transparent_surface(monkeypatch, qt_app):
    window = OverlayWindow(InitialClientSettings(), DebugConfig())
    try:
        _RecordingPainter.instances = []
        monkeypatch.setattr(overlay_client_module, "QPainter", _RecordingPainter)
        monkeypatch.setattr(
            window,
            "_paint_overlay",
            lambda painter: painter.operations.append(("overlay", painter.composition_mode)),
        )
        event = QPaintEvent(window.rect())

        window.paintEvent(event)
        window.paintEvent(event)

        assert len(_RecordingPainter.instances) == 2
        for painter in _RecordingPainter.instances:
            assert painter.operations[:3] == [
                ("composition", QPainter.CompositionMode.CompositionMode_Clear),
                ("fill", Qt.GlobalColor.transparent),
                ("composition", QPainter.CompositionMode.CompositionMode_SourceOver),
            ]
    finally:
        window._legacy_timer.stop()
        window._modifier_timer.stop()
        window._tracking_timer.stop()
        window.close()
