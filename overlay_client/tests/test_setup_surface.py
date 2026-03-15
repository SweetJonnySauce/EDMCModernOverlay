from __future__ import annotations

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPaintEvent, QShowEvent
from PyQt6.QtWidgets import QApplication

from overlay_client.client_config import InitialClientSettings
from overlay_client.debug_config import DebugConfig
from overlay_client.overlay_client import OverlayWindow, _LINE_WIDTH_DEFAULTS
from overlay_client.setup_surface import SetupSurfaceMixin


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
def test_paint_event_calls_mixin(monkeypatch, qt_app):
    window = OverlayWindow(InitialClientSettings(), DebugConfig())
    try:
        captured = []
        monkeypatch.setattr(window, "_paint_overlay", lambda painter: captured.append(painter))
        event = QPaintEvent(window.rect())

        window.paintEvent(event)

        assert captured and captured[0] is not None
    finally:
        window._legacy_timer.stop()
        window._modifier_timer.stop()
        window._tracking_timer.stop()
        window.close()


class _ProfileStub(SetupSurfaceMixin):
    def __init__(self, *, standalone_mode: bool, wayland: bool) -> None:
        self._standalone_mode = standalone_mode
        self._wayland = wayland
        self._window_flag_state_cache = {}
        self._standalone_profile_signature = None
        self._window_flags = 0
        self._widget_attrs = {}
        self.window_flag_calls = []
        self.widget_attr_calls = []

    def _is_wayland(self) -> bool:
        return self._wayland

    def windowFlags(self):
        return Qt.WindowType(self._window_flags)

    def setWindowFlag(self, flag: Qt.WindowType, enabled: bool) -> None:
        if enabled:
            self._window_flags |= int(flag)
        else:
            self._window_flags &= ~int(flag)
        self.window_flag_calls.append((flag, enabled))

    def testAttribute(self, attr: Qt.WidgetAttribute) -> bool:
        return bool(self._widget_attrs.get(attr, False))

    def setAttribute(self, attr: Qt.WidgetAttribute, enabled: bool) -> None:
        self._widget_attrs[attr] = enabled
        self.widget_attr_calls.append((attr, enabled))


def test_standalone_profile_disables_hidden_window_flags_on_linux(monkeypatch) -> None:
    stub = _ProfileStub(standalone_mode=True, wayland=False)
    monkeypatch.setattr("overlay_client.setup_surface.sys.platform", "linux")

    stub._apply_standalone_window_profile(reason="unit_test")

    assert not bool(int(stub.windowFlags()) & int(Qt.WindowType.Tool))
    assert not bool(int(stub.windowFlags()) & int(Qt.WindowType.X11BypassWindowManagerHint))
    assert stub.testAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating) is False


def test_non_standalone_profile_preserves_default_hidden_flags_on_linux(monkeypatch) -> None:
    stub = _ProfileStub(standalone_mode=False, wayland=False)
    monkeypatch.setattr("overlay_client.setup_surface.sys.platform", "linux")

    stub._apply_standalone_window_profile(reason="unit_test")

    assert bool(int(stub.windowFlags()) & int(Qt.WindowType.Tool))
    assert bool(int(stub.windowFlags()) & int(Qt.WindowType.X11BypassWindowManagerHint))
    assert stub.testAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating) is True


def test_set_window_flag_noops_when_state_unchanged() -> None:
    stub = _ProfileStub(standalone_mode=False, wayland=False)

    stub._set_window_flag(Qt.WindowType.Tool, True)
    stub._set_window_flag(Qt.WindowType.Tool, True)

    assert stub.window_flag_calls == [(Qt.WindowType.Tool, True)]


def test_standalone_profile_dedupes_unchanged_signature(monkeypatch) -> None:
    stub = _ProfileStub(standalone_mode=True, wayland=False)
    monkeypatch.setattr("overlay_client.setup_surface.sys.platform", "linux")

    stub._apply_standalone_window_profile(reason="show_event")
    first_window_calls = list(stub.window_flag_calls)
    first_attr_calls = list(stub.widget_attr_calls)

    stub._apply_standalone_window_profile(reason="show_event")

    assert stub.window_flag_calls == first_window_calls
    assert stub.widget_attr_calls == first_attr_calls


def test_standalone_profile_reapplies_when_signature_changes(monkeypatch) -> None:
    stub = _ProfileStub(standalone_mode=False, wayland=False)
    monkeypatch.setattr("overlay_client.setup_surface.sys.platform", "linux")

    stub._apply_standalone_window_profile(reason="show_event")
    baseline_calls = len(stub.window_flag_calls)
    stub._standalone_mode = True
    stub._apply_standalone_window_profile(reason="set_standalone_mode")

    assert len(stub.window_flag_calls) > baseline_calls
