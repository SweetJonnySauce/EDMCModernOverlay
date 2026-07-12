import sys
import types

import pytest

try:  # pragma: no cover - exercised when PyQt6 is present
    from PyQt6 import QtCore as _QtCore  # noqa: F401
    from PyQt6 import QtGui as _QtGui  # noqa: F401
    from PyQt6 import QtWidgets as _QtWidgets  # noqa: F401
    from PyQt6.QtCore import QRect as _QRectImport  # noqa: F401
    from PyQt6.QtCore import QSize as _QSizeImport  # noqa: F401
except Exception:  # pragma: no cover - lightweight stub path
    if "PyQt6" not in sys.modules:
        sys.modules["PyQt6"] = types.ModuleType("PyQt6")

    class _QRect:
        def __init__(self, x=0, y=0, width=0, height=0) -> None:
            self._x = int(x)
            self._y = int(y)
            self._width = int(width)
            self._height = int(height)

        def x(self) -> int:
            return self._x

        def y(self) -> int:
            return self._y

        def width(self) -> int:
            return self._width

        def height(self) -> int:
            return self._height

        def center(self):
            return self

        def intersects(self, other) -> bool:
            return not (
                self._x + self._width <= other.x()
                or other.x() + other.width() <= self._x
                or self._y + self._height <= other.y()
                or other.y() + other.height() <= self._y
            )

    class _QSize:
        def __init__(self, width=0, height=0) -> None:
            self._width = int(width)
            self._height = int(height)

        def width(self) -> int:
            return self._width

        def height(self) -> int:
            return self._height

    class _QPoint:
        def __init__(self, x=0, y=0) -> None:
            self._x = int(x)
            self._y = int(y)

        def x(self) -> int:
            return self._x

        def y(self) -> int:
            return self._y

    qtcore = sys.modules.get("PyQt6.QtCore") or types.ModuleType("PyQt6.QtCore")
    qtcore.QPoint = getattr(qtcore, "QPoint", _QPoint)
    qtcore.QRect = getattr(qtcore, "QRect", _QRect)
    qtcore.QSize = getattr(qtcore, "QSize", _QSize)
    qtcore.Qt = getattr(
        qtcore,
        "Qt",
        type(
            "Qt",
            (),
            {
                "KeyboardModifier": type("KeyboardModifier", (), {"AltModifier": 1}),
            },
        ),
    )
    sys.modules["PyQt6.QtCore"] = qtcore

    qtgui = sys.modules.get("PyQt6.QtGui") or types.ModuleType("PyQt6.QtGui")
    qtgui.QGuiApplication = getattr(
        qtgui,
        "QGuiApplication",
        type(
            "QGuiApplication",
            (),
            {
                "screens": staticmethod(lambda: []),
                "primaryScreen": staticmethod(lambda: None),
                "screenAt": staticmethod(lambda _point: None),
            },
        ),
    )
    qtgui.QWindow = getattr(qtgui, "QWindow", object)
    qtgui.QScreen = getattr(qtgui, "QScreen", object)
    sys.modules["PyQt6.QtGui"] = qtgui

    qtwidgets = sys.modules.get("PyQt6.QtWidgets") or types.ModuleType("PyQt6.QtWidgets")
    qtwidgets.QApplication = getattr(
        qtwidgets,
        "QApplication",
        type("QApplication", (), {"queryKeyboardModifiers": staticmethod(lambda: 0)}),
    )
    sys.modules["PyQt6.QtWidgets"] = qtwidgets

from overlay_client.backend import (
    BackendDescriptor,
    BackendFamily,
    BackendInstance,
    CapabilityClassification,
    HelperCapabilityState,
    HelperKind,
    PlatformProbeResult,
)
from overlay_client.backend.consumers import BackendPresentationCycleResult
from overlay_client.backend.presentation_policy import (
    BackendPresentationVisibilitySnapshot,
    BackendPresentationVisibilityState,
)
from overlay_client.backend.surface_preparation import BackendPresentationSurfacePreparation
from overlay_client.follow_surface import FollowSurfaceMixin
from overlay_client.window_tracking import WindowState


class _StubFrame:
    def __init__(self) -> None:
        self._x = 0
        self._y = 0
        self._w = 10
        self._h = 10

    def x(self) -> int:
        return self._x

    def y(self) -> int:
        return self._y

    def width(self) -> int:
        return self._w

    def height(self) -> int:
        return self._h


class _StubWindowHandle:
    def __init__(self, dpr: float = 1.5) -> None:
        self._dpr = dpr
        self._screen = None
        self.transient_parents = []

    def devicePixelRatio(self) -> float:
        return self._dpr

    def screen(self):
        return self._screen

    def setFlag(self, *_args, **_kwargs) -> None:
        return None

    def setTransientParent(self, parent) -> None:
        self.transient_parents.append(parent)

    def setScreen(self, screen) -> None:
        self._screen = screen


class _StubLabel:
    def __init__(self) -> None:
        self.visible = True
        self.calls: list[bool] = []

    def setVisible(self, visible: bool) -> None:
        self.visible = bool(visible)
        self.calls.append(self.visible)


class _StubFollowController:
    def __init__(self) -> None:
        self.wm_override = None
        self.wm_override_tracker = None
        self.start_called = 0
        self.stop_called = 0
        self.suspend_called = []
        self.refresh_called = 0
        self._enabled = False
        self.last_poll_attempted = False
        self.last_state_missing = False
        self.last_tracker_state = None

    def set_follow_enabled(self, enabled: bool) -> None:
        self._enabled = enabled

    def set_drag_state(self, *_args, **_kwargs) -> None:
        return None

    def start(self) -> None:
        self.start_called += 1

    def stop(self) -> None:
        self.stop_called += 1

    def suspend(self, delay: float) -> None:
        self.suspend_called.append(delay)

    def refresh(self):
        self.refresh_called += 1
        return None

    def record_override(self, rect, tracker, reason, classification) -> None:
        self.wm_override = rect
        self.wm_override_tracker = tracker
        self._reason = reason
        self._classification = classification

    def clear_override(self, reason: str) -> None:
        self.wm_override = None
        self._clear_reason = reason

    def override_expired(self) -> bool:
        return False


class _StubVisibilityHelper:
    def __init__(self) -> None:
        self.calls = []

    def update_visibility(self, show, is_visible_fn, show_fn, hide_fn, raise_fn, apply_drag_state_fn, format_scale_debug_fn):
        self.calls.append(show)
        if show:
            if not is_visible_fn():
                show_fn()
                raise_fn()
                apply_drag_state_fn()
        else:
            if is_visible_fn():
                hide_fn()
        return {"show": show}


class _FollowSurfaceStub(FollowSurfaceMixin):
    def __init__(self) -> None:
        # follow/platform state
        self._drag_enabled = True
        self._drag_active = False
        self._move_mode = False
        self._cursor_saved = False
        self._saved_cursor = None
        self._follow_enabled = True
        self._keep_overlay_visible = False
        self._lost_window_logged = False
        self._fullscreen_hint_logged = False
        self._title_bar_enabled = False
        self._title_bar_height = 0
        self._last_title_bar_offset = 0
        self._aspect_guard_skip_logged = False
        self._base_width = 0
        self._base_height = 0
        self._last_raw_window_log = None
        self._last_normalised_tracker = None
        self._last_device_ratio_log = None
        self._last_geometry_log = None
        self._last_follow_state = None
        self._last_visibility_state = None
        self._last_backend_presentation = None
        self._last_backend_presentation_log = None
        self._backend_presentation_visibility_state = BackendPresentationVisibilityState()
        self._backend_presentation_content_suppressed = False
        self._last_screen_name = None
        self._transient_parent_window = None
        self._transient_parent_id = None
        self._visible = False
        self._window_state = 1
        self._geometry_calls = []
        self._event_order = []
        self._update_calls = 0
        self.message_label = _StubLabel()

        owner = self

        class _StubInteraction:
            def set_click_through(self, *args, **kwargs) -> None:
                return None

            def restore_drag_interactivity(self, *args, **kwargs) -> None:
                return None

            def prepare_window_flags_for_click_through(self, *args, **kwargs) -> None:
                owner._event_order.append("prepareWindowFlags")

        self._interaction_controller = _StubInteraction()
        self._follow_controller = _StubFollowController()
        self._window_controller = type(
            "StubWindowController",
            (),
            {
                "_fullscreen_hint_logged": False,
                "resolve_and_apply_geometry": lambda self_controller, tracker_tuple, desired_tuple, **kwargs: desired_tuple,
                "post_process_follow_state": lambda *args, **kwargs: None,
                "clear_override": lambda *args, **kwargs: None,
            },
        )()
        self._visibility_helper = _StubVisibilityHelper()
        class _StubPlatform:
            def prepare_window(self, *_args, **_kwargs) -> None:
                owner._event_order.append("platformPrepare")

            def apply_click_through(self, *_args, **_kwargs) -> None:
                owner._event_order.append("platformClickThrough")

            def platform_label(self) -> str:
                return "stub"

            def uses_transient_parent(self) -> bool:
                return False

            def is_wayland_backend(self) -> bool:
                return False

        self._platform_controller = _StubPlatform()
        self._client_backend_status = _backend_status(helper_available=False)

    # Qt shell shims
    def windowHandle(self):
        if not hasattr(self, "_stub_window_handle"):
            self._stub_window_handle = _StubWindowHandle()
        return self._stub_window_handle

    def frameGeometry(self):
        return _StubFrame()

    def setGeometry(self, rect, *_args, **_kwargs) -> None:
        self._geometry_calls.append((rect.x(), rect.y(), rect.width(), rect.height()))
        self._event_order.append("setGeometry")

    def raise_(self) -> None:
        return None

    def isVisible(self) -> bool:
        return self._visible

    def show(self) -> None:
        self._visible = True
        self._event_order.append("show")

    def showFullScreen(self) -> None:
        self._visible = True
        self._event_order.append("showFullScreen")

    def showNormal(self) -> None:
        self._visible = True
        self._event_order.append("showNormal")

    def windowState(self):
        return self._window_state

    def setWindowState(self, state) -> None:
        self._window_state = state
        self._event_order.append("setWindowState")

    def hide(self) -> None:
        self._visible = False
        self._event_order.append("hide")

    def update(self) -> None:
        self._update_calls += 1
        self._event_order.append("update")

    def _current_physical_size(self):
        return (100.0, 50.0)

    def format_scale_debug(self) -> str:
        return "debug"

    def _apply_title_bar_offset(self, geometry, scale_y=1.0):
        return geometry, 0

    def _apply_aspect_guard(self, geometry, original_geometry=None, applied_title_offset=0):
        return geometry

    def _move_to_screen(self, *_args, **_kwargs):
        return None

    def _sync_base_dimensions_to_widget(self):
        self._base_width = 100
        self._base_height = 50

    def _describe_screen(self, screen):
        return "stub-screen"

    def _is_wayland(self) -> bool:
        return False

    def _restore_drag_interactivity(self) -> None:
        return None

    def _apply_drag_state(self) -> None:
        return None

    def _update_auto_legacy_scale(self, *_args, **_kwargs) -> None:
        return None


def _backend_status(*, helper_available: bool):
    return type(
        "Status",
        (),
        {
            "selected_backend": BackendDescriptor(BackendFamily.NATIVE_WAYLAND, BackendInstance.GNOME_SHELL_WAYLAND),
            "classification": CapabilityClassification.DEGRADED_OVERLAY,
            "probe": PlatformProbeResult(),
            "helper_states": (
                HelperCapabilityState(
                    helper=HelperKind.GNOME_SHELL_EXTENSION,
                    required=True,
                    installed=helper_available,
                    enabled=helper_available,
                    approved=helper_available,
                ),
            ),
        },
    )()


def _fake_backend_presentation_result(
    *,
    target_has_focus: bool = True,
    target_showing_on_workspace: bool = True,
    target_minimized: bool = False,
    presentation_attachable: bool = True,
    overlay_window_found: bool = True,
    presentation_rect_match: bool = True,
    prime_rect: tuple[int, int, int, int] | None = (10, 20, 300, 200),
    geometry_diagnostics: dict[str, object] | None = None,
) -> BackendPresentationCycleResult:
    diagnostics = {
        "helper_health": "healthy",
        "target_state": "target_found",
        "target_token": "meta:21",
        "target_sequence": 3,
        "rect_source": "content_rect",
        "requested_rect": {"x": 10, "y": 20, "width": 300, "height": 200},
        "presentation_state": "presentation_applied",
        "applied_rect": {"x": 10, "y": 20, "width": 300, "height": 200},
        "rect_match": True,
        "rect_delta": [0, 0, 0, 0],
        "presentation_reasons": [],
        "attempts": 1,
        "retry_reasons": [],
        "legacy_geometry_policy": "ignored_helper_source_of_truth",
        "target_available": True,
        "target_has_focus": target_has_focus,
        "target_showing_on_workspace": target_showing_on_workspace,
        "target_minimized": target_minimized,
        "presentation_available": True,
        "presentation_attachable": presentation_attachable,
        "overlay_window_found": overlay_window_found,
        "presentation_rect_match": presentation_rect_match,
        "prime_rect": (
            {"x": prime_rect[0], "y": prime_rect[1], "width": prime_rect[2], "height": prime_rect[3]}
            if prime_rect is not None
            else None
        ),
        "prime_rect_source": "requested_rect" if prime_rect is not None else "unavailable",
    }
    if geometry_diagnostics is not None:
        diagnostics["target_geometry_diagnostics"] = geometry_diagnostics
    return BackendPresentationCycleResult(
        should_show_overlay=True,
        scale_size=(300, 200),
        prime_rect=prime_rect,
        prime_rect_source="requested_rect" if prime_rect is not None else "unavailable",
        visibility_snapshot=BackendPresentationVisibilitySnapshot(
            target_available=True,
            target_has_focus=target_has_focus,
            target_showing_on_workspace=target_showing_on_workspace,
            target_minimized=target_minimized,
            presentation_available=True,
            presentation_attachable=presentation_attachable,
            overlay_window_found=overlay_window_found,
            presentation_rect_match=presentation_rect_match,
        ),
        diagnostics=diagnostics,
        log_prefix="GNOME helper presentation",
    )


def test_resolve_and_apply_geometry_updates_last_geometry_log():
    stub = _FollowSurfaceStub()
    tracker = (1, 2, 3, 4)
    desired = (5, 6, 7, 8)

    result = stub._resolve_and_apply_geometry(tracker, desired)

    assert result == desired
    assert stub._last_geometry_log == desired


def test_refresh_follow_geometry_uses_gnome_helper_presentation_and_skips_legacy_refresh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub = _FollowSurfaceStub()
    stub._client_backend_status = _backend_status(helper_available=True)
    stub._title_bar_enabled = True
    stub._title_bar_height = 30
    result = _fake_backend_presentation_result()
    calls: list[tuple[bool, bool, str, bool, int]] = []

    def fake_cycle(
        _status,
        *,
        standalone_mode: bool = False,
        keep_overlay_visible: bool = False,
        previous_surface_action: str = "",
        title_bar_compensation_enabled: bool = False,
        title_bar_compensation_height: int = 0,
        **_kwargs,
    ):
        calls.append(
            (
                standalone_mode,
                keep_overlay_visible,
                previous_surface_action,
                title_bar_compensation_enabled,
                title_bar_compensation_height,
            )
        )
        return result

    monkeypatch.setattr("overlay_client.follow_surface.run_backend_presentation_cycle", fake_cycle)

    stub._refresh_follow_geometry()

    assert calls == [(False, False, "", True, 30)]
    assert stub._follow_controller.refresh_called == 0
    assert stub._last_backend_presentation is result
    assert stub._last_backend_presentation_surface_action == "mapped_visible"
    assert stub._visibility_helper.calls == [True]


def test_refresh_follow_geometry_logs_backend_geometry_diagnostics_when_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub = _FollowSurfaceStub()
    result = _fake_backend_presentation_result(
        geometry_diagnostics={
            "candidates": [
                {
                    "name": "client_area",
                    "rect": {"x": 10, "y": 57, "width": 300, "height": 163},
                },
            ]
        }
    )
    debug_calls: list[tuple[str, tuple[object, ...]]] = []

    monkeypatch.setattr("overlay_client.follow_surface.run_backend_presentation_cycle", lambda *_args, **_kwargs: result)
    monkeypatch.setattr(
        "overlay_client.follow_surface._CLIENT_LOGGER.debug",
        lambda message, *args, **_kwargs: debug_calls.append((str(message), args)),
    )

    stub._refresh_follow_geometry()

    assert any("geometry diagnostics" in message for message, _args in debug_calls)
    assert any("client_area" in str(args) for _message, args in debug_calls)


def test_refresh_follow_geometry_logs_partial_backend_diagnostics_without_crashing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub = _FollowSurfaceStub()
    result = BackendPresentationCycleResult(
        should_show_overlay=False,
        diagnostics={
            "helper_health": "unavailable",
            "target_state": "launcher_only",
            "presentation_state": "malformed_payload",
            "presentation_reasons": ["missing_helper"],
        },
        visibility_snapshot=BackendPresentationVisibilitySnapshot(
            target_available=False,
            presentation_available=False,
        ),
        log_prefix="GNOME helper presentation",
    )
    debug_calls: list[tuple[str, tuple[object, ...]]] = []

    monkeypatch.setattr("overlay_client.follow_surface.run_backend_presentation_cycle", lambda *_args, **_kwargs: result)
    monkeypatch.setattr(
        "overlay_client.follow_surface._CLIENT_LOGGER.debug",
        lambda message, *args, **_kwargs: debug_calls.append((str(message), args)),
    )

    stub._refresh_follow_geometry()

    assert stub._last_backend_presentation is result
    assert stub._visibility_helper.calls == [False]
    assert any("token=%s" in message and "malformed_payload" in str(args) for message, args in debug_calls)


def test_refresh_follow_geometry_primes_backend_rect_before_showing_hidden_overlay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub = _FollowSurfaceStub()
    result = _fake_backend_presentation_result(prime_rect=(431, 167, 1440, 997))

    monkeypatch.setattr("overlay_client.follow_surface.run_backend_presentation_cycle", lambda *_args, **_kwargs: result)
    monkeypatch.setattr("overlay_client.follow_surface.time.monotonic", lambda: 20.0)

    stub._refresh_follow_geometry()

    assert stub._geometry_calls == [(431, 167, 1440, 997)]
    assert stub._event_order[:3] == ["prepareWindowFlags", "setGeometry", "show"]
    assert stub._backend_presentation_visibility_state.remap_warmup_active is True


def test_backend_fullscreen_surface_preparation_sets_screen_geometry_and_fullscreen(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub = _FollowSurfaceStub()
    screen = type("Screen", (), {"geometry": lambda self: type("Rect", (), {"intersects": lambda *_: True})()})()
    monkeypatch.setattr("overlay_client.follow_surface.QGuiApplication.screenAt", lambda _point: screen)

    prepared = stub._prepare_backend_presentation_surface(
        BackendPresentationSurfacePreparation(
            mode="fullscreen_monitor",
            rect=(0, 0, 3440, 1440),
            reason="test",
            target_token="meta:18",
            rect_source="content_rect",
        )
    )

    assert prepared is True
    assert stub.windowHandle().screen() is screen
    assert stub._geometry_calls[-1] == (0, 0, 3440, 1440)
    assert stub._visible is True
    assert stub._event_order[:5] == [
        "prepareWindowFlags",
        "setGeometry",
        "showFullScreen",
        "platformPrepare",
        "platformClickThrough",
    ]


def test_backend_managed_windowed_surface_preparation_resets_fullscreen_state_without_showing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub = _FollowSurfaceStub()
    screen = type("Screen", (), {"geometry": lambda self: type("Rect", (), {"intersects": lambda *_: True})()})()
    monkeypatch.setattr("overlay_client.follow_surface.QGuiApplication.screenAt", lambda _point: screen)

    prepared = stub._prepare_backend_presentation_surface(
        BackendPresentationSurfacePreparation(
            mode="managed_windowed",
            rect=(1080, 216, 1280, 997),
            reason="test",
            target_token="meta:21",
            rect_source="frame_rect_fallback",
        )
    )

    assert prepared is True
    assert stub.windowHandle().screen() is screen
    assert stub._geometry_calls[-1] == (1080, 216, 1280, 997)
    assert stub._visible is False
    assert "showNormal" not in stub._event_order
    assert stub._event_order[:5] == [
        "prepareWindowFlags",
        "setWindowState",
        "setGeometry",
        "platformPrepare",
        "platformClickThrough",
    ]


def test_refresh_follow_geometry_passes_backend_surface_preparer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub = _FollowSurfaceStub()
    result = _fake_backend_presentation_result()
    callbacks = []

    def fake_cycle(_status, **kwargs):
        callbacks.append(kwargs.get("prepare_surface"))
        return result

    monkeypatch.setattr("overlay_client.follow_surface.run_backend_presentation_cycle", fake_cycle)

    stub._refresh_follow_geometry()

    assert callbacks and callbacks[0] == stub._prepare_backend_presentation_surface


def test_refresh_follow_geometry_warmup_keeps_visible_after_remap_focus_flip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub = _FollowSurfaceStub()
    results = iter(
        (
            _fake_backend_presentation_result(
                target_has_focus=True,
                overlay_window_found=False,
                presentation_rect_match=False,
                prime_rect=(431, 167, 1440, 997),
            ),
            _fake_backend_presentation_result(
                target_has_focus=False,
                overlay_window_found=True,
                presentation_rect_match=False,
                prime_rect=(431, 167, 1440, 997),
            ),
        )
    )
    ticks = iter((20.0, 20.5))

    monkeypatch.setattr("overlay_client.follow_surface.run_backend_presentation_cycle", lambda *_args, **_kwargs: next(results))
    monkeypatch.setattr("overlay_client.follow_surface.time.monotonic", lambda: next(ticks))

    stub._refresh_follow_geometry()
    stub._refresh_follow_geometry()

    assert stub._visibility_helper.calls == [True, True]
    assert stub._visible is True
    assert stub._backend_presentation_visibility_state.remap_warmup_active is True
    assert stub._backend_presentation_visibility_state.remap_warmup_samples == 1
    assert stub._backend_presentation_visibility_state.focus_loss_samples == 0


def test_refresh_follow_geometry_debounces_backend_presentation_focus_loss(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub = _FollowSurfaceStub()
    stub._visible = True
    result = _fake_backend_presentation_result(target_has_focus=False)

    monkeypatch.setattr("overlay_client.follow_surface.run_backend_presentation_cycle", lambda *_args, **_kwargs: result)
    monkeypatch.setattr("overlay_client.follow_surface.time.monotonic", lambda: 10.0)

    stub._refresh_follow_geometry()
    stub._refresh_follow_geometry()

    assert stub._follow_controller.refresh_called == 0
    assert stub._visibility_helper.calls == [True, True]
    assert stub._backend_presentation_visibility_state.focus_loss_samples == 2


def test_refresh_follow_geometry_suppresses_content_without_hiding_after_soft_focus_loss(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub = _FollowSurfaceStub()
    stub._visible = True
    stub._backend_presentation_visibility_state = BackendPresentationVisibilityState(
        focus_loss_samples=1,
        focus_lost_since_monotonic=10.0,
    )
    result = _fake_backend_presentation_result(target_has_focus=False)

    monkeypatch.setattr("overlay_client.follow_surface.run_backend_presentation_cycle", lambda *_args, **_kwargs: result)
    monkeypatch.setattr("overlay_client.follow_surface.time.monotonic", lambda: 11.1)

    stub._refresh_follow_geometry()

    assert stub._visible is True
    assert "hide" not in stub._event_order
    assert "show" not in stub._event_order
    assert stub._backend_presentation_content_suppressed is True
    assert stub.message_label.visible is False
    assert stub._update_calls == 1
    assert stub._visibility_helper.calls == [True]
    assert stub._backend_presentation_visibility_state.focus_loss_samples == 2


def test_refresh_follow_geometry_restores_suppressed_content_without_remap_on_focus_return(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub = _FollowSurfaceStub()
    stub._visible = True
    stub._backend_presentation_content_suppressed = True
    stub.message_label.visible = False
    stub._backend_presentation_visibility_state = BackendPresentationVisibilityState(
        focus_loss_samples=2,
        focus_lost_since_monotonic=10.0,
    )
    result = _fake_backend_presentation_result(target_has_focus=True)

    monkeypatch.setattr("overlay_client.follow_surface.run_backend_presentation_cycle", lambda *_args, **_kwargs: result)
    monkeypatch.setattr("overlay_client.follow_surface.time.monotonic", lambda: 12.0)

    stub._refresh_follow_geometry()

    assert stub._visible is True
    assert "hide" not in stub._event_order
    assert "show" not in stub._event_order
    assert stub._backend_presentation_content_suppressed is False
    assert stub.message_label.visible is True
    assert stub._update_calls == 1
    assert stub._backend_presentation_visibility_state == BackendPresentationVisibilityState()


def test_refresh_follow_geometry_hard_hides_and_restores_content_for_target_minimized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub = _FollowSurfaceStub()
    stub._visible = True
    stub._backend_presentation_content_suppressed = True
    stub.message_label.visible = False
    stub._backend_presentation_visibility_state = BackendPresentationVisibilityState(
        focus_loss_samples=2,
        focus_lost_since_monotonic=10.0,
    )
    result = _fake_backend_presentation_result(target_has_focus=False, target_minimized=True)

    monkeypatch.setattr("overlay_client.follow_surface.run_backend_presentation_cycle", lambda *_args, **_kwargs: result)
    monkeypatch.setattr("overlay_client.follow_surface.time.monotonic", lambda: 12.0)

    stub._refresh_follow_geometry()

    assert stub._visible is False
    assert "hide" in stub._event_order
    assert stub._backend_presentation_content_suppressed is False
    assert stub.message_label.visible is True
    assert stub._backend_presentation_visibility_state == BackendPresentationVisibilityState()


def test_refresh_follow_geometry_keeps_backend_presentation_visible_when_setting_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub = _FollowSurfaceStub()
    stub._keep_overlay_visible = True
    result = _fake_backend_presentation_result(target_has_focus=False)
    keep_flags: list[bool] = []

    def fake_cycle(*_args, **kwargs):
        keep_flags.append(bool(kwargs["keep_overlay_visible"]))
        return result

    monkeypatch.setattr("overlay_client.follow_surface.run_backend_presentation_cycle", fake_cycle)

    stub._refresh_follow_geometry()
    stub._refresh_follow_geometry()

    assert keep_flags == [True, True]
    assert stub._follow_controller.refresh_called == 0
    assert stub._visibility_helper.calls == [True, True]


def test_refresh_follow_geometry_uses_legacy_path_when_gnome_helper_is_not_available() -> None:
    stub = _FollowSurfaceStub()

    stub._refresh_follow_geometry()

    assert stub._follow_controller.refresh_called == 1


def test_normalise_tracker_geometry_updates_logs(monkeypatch: pytest.MonkeyPatch):
    stub = _FollowSurfaceStub()
    stub._title_bar_enabled = True
    stub._title_bar_height = 10

    def fake_convert(rect):
        return rect, ("screen-a", 1.5, 2.0, 1.25)

    monkeypatch.setattr(stub, "_convert_native_rect_to_qt", fake_convert)
    tracker_qt, tracker_native, norm_info, desired = stub._normalise_tracker_geometry(
        WindowState(x=10, y=20, width=30, height=40, is_foreground=True, is_visible=True, identifier="abc")
    )

    assert tracker_native == (10, 20, 30, 40)
    assert tracker_qt == tracker_native
    assert norm_info == ("screen-a", 1.5, 2.0, 1.25)
    assert stub._last_raw_window_log == tracker_native
    assert stub._last_device_ratio_log is not None
    assert desired == tracker_qt


def test_handle_missing_follow_state_keep_overlay_visible_enables_visibility(monkeypatch: pytest.MonkeyPatch):
    stub = _FollowSurfaceStub()
    stub._keep_overlay_visible = True
    applied: list[bool] = []

    def apply_click_through(self=None, flag: bool = False) -> None:
        applied.append(flag)

    stub._platform_controller = type("StubPlatform", (), {"apply_click_through": apply_click_through})()
    stub._restore_drag_interactivity = lambda: applied.append(True)  # type: ignore[assignment]

    stub._handle_missing_follow_state()

    assert applied == [True, True]  # click-through and restore
    assert stub._visibility_helper.calls == [True]


def test_ensure_transient_parent_uses_platform_controller_policy():
    stub = _FollowSurfaceStub()
    stub._transient_parent_window = object()
    stub._transient_parent_id = "0x123"
    handle = stub.windowHandle()
    stub._platform_controller = type(
        "StubPlatform",
        (),
        {
            "uses_transient_parent": lambda self=None: False,
            "apply_click_through": lambda *args, **kwargs: None,
            "platform_label": lambda self=None: "stub",
            "is_wayland_backend": lambda self=None: False,
        },
    )()

    stub._ensure_transient_parent(
        WindowState(x=1, y=2, width=3, height=4, is_foreground=True, is_visible=True, identifier="0x456")
    )

    assert handle.transient_parents == [None]
    assert stub._transient_parent_window is None
    assert stub._transient_parent_id is None
