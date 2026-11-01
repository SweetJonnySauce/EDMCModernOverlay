import pytest

from overlay_client import follow_surface
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

    def devicePixelRatio(self) -> float:
        return self._dpr

    def screen(self):
        return self._screen

    def setFlag(self, *_args, **_kwargs) -> None:
        return None


class _StubFollowController:
    def __init__(self) -> None:
        self.wm_override = None
        self.wm_override_tracker = None
        self.start_called = 0
        self.stop_called = 0
        self.suspend_called = []
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
            show_fn()
        else:
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
        self._force_render = False
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
        self._last_screen_name = None
        self._transient_parent_window = None
        self._transient_parent_id = None

        self._interaction_controller = type(
            "StubInteraction",
            (),
            {
                "set_click_through": lambda *args, **kwargs: None,
                "restore_drag_interactivity": lambda *args, **kwargs: None,
            },
        )()
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
        self._platform_controller = type(
            "StubPlatform",
            (),
            {
                "apply_click_through": lambda *args, **kwargs: None,
                "platform_label": lambda self=None: "stub",
            },
        )()

    # Qt shell shims
    def windowHandle(self):
        return _StubWindowHandle()

    def frameGeometry(self):
        return _StubFrame()

    def setGeometry(self, *_args, **_kwargs) -> None:
        return None

    def raise_(self) -> None:
        return None

    def isVisible(self) -> bool:
        return False

    def show(self) -> None:
        return None

    def hide(self) -> None:
        return None

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


def test_resolve_and_apply_geometry_updates_last_geometry_log():
    stub = _FollowSurfaceStub()
    tracker = (1, 2, 3, 4)
    desired = (5, 6, 7, 8)

    result = stub._resolve_and_apply_geometry(tracker, desired)

    assert result == desired
    assert stub._last_geometry_log == desired


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


def test_handle_missing_follow_state_force_render_enables_visibility(monkeypatch: pytest.MonkeyPatch):
    stub = _FollowSurfaceStub()
    stub._force_render = True
    applied: list[bool] = []

    def apply_click_through(self=None, flag: bool = False) -> None:
        applied.append(flag)

    stub._platform_controller = type("StubPlatform", (), {"apply_click_through": apply_click_through})()
    stub._restore_drag_interactivity = lambda: applied.append(True)  # type: ignore[assignment]

    stub._handle_missing_follow_state()

    assert applied == [True, True]  # click-through and restore
    assert stub._visibility_helper.calls == [True]


def test_raise_overlay_if_supported_only_skips_gnome_wayland(monkeypatch: pytest.MonkeyPatch):
    stub = _FollowSurfaceStub()
    raised = []
    stub.raise_ = lambda: raised.append(True)  # type: ignore[assignment]
    stub._platform_context = type("PlatformContextStub", (), {"compositor": "gnome-shell"})()
    monkeypatch.setattr(stub, "_is_wayland", lambda: True)

    stub._raise_overlay_if_supported()

    assert raised == []

    stub._platform_context.compositor = "kwin"
    stub._raise_overlay_if_supported()
    assert raised == [True]

    stub._platform_context.compositor = "gnome-shell"
    monkeypatch.setattr(stub, "_is_wayland", lambda: False)
    stub._raise_overlay_if_supported()

    assert raised == [True, True]


def test_update_follow_visibility_retries_gnome_compositor_stacking(monkeypatch):
    scheduled = []
    monkeypatch.setattr(follow_surface.QTimer, "singleShot", lambda delay, callback: scheduled.append((delay, callback)))
    stub = _FollowSurfaceStub()
    stub._platform_context = type("PlatformContextStub", (), {"compositor": "gnome-shell"})()
    stub._is_wayland = lambda: True  # type: ignore[assignment]
    stub.windowTitle = lambda: "EDMC Modern Overlay"  # type: ignore[assignment]
    setattr(stub, "isVisible", lambda: True)
    stacking_calls = []

    def set_overlay_above(title, above):
        stacking_calls.append((title, above))
        return not above or stacking_calls.count((title, above)) == 2

    setattr(stub, "_window_tracker", type(
        "StubTracker",
        (),
        {"set_overlay_above": lambda self, title, above: set_overlay_above(title, above)},
    )())

    stub._update_follow_visibility(True)
    assert stacking_calls == []
    assert [delay for delay, _ in scheduled] == [100]

    scheduled.pop(0)[1]()
    assert stacking_calls == [("EDMC Modern Overlay", True)]
    assert [delay for delay, _ in scheduled] == [100]

    scheduled.pop(0)[1]()
    stub._update_follow_visibility(False)

    assert stacking_calls == [
        ("EDMC Modern Overlay", True),
        ("EDMC Modern Overlay", True),
        ("EDMC Modern Overlay", False),
    ]


def test_apply_follow_state_does_not_make_synchronous_gnome_stacking_request():
    stub = _FollowSurfaceStub()
    stacking_calls = []
    setattr(stub, "_normalise_tracker_geometry", lambda state: ((0, 0, 10, 10), (0, 0, 10, 10), None, (0, 0, 10, 10)))
    setattr(stub, "_resolve_and_apply_geometry", lambda tracker, desired: desired)
    setattr(stub, "_post_process_follow_state", lambda state, target: None)
    setattr(stub, "_window_controller", type("StubWindowController", (), {"_fullscreen_hint_logged": False})())
    setattr(stub, "_window_tracker", type(
        "StubTracker",
        (),
        {"set_overlay_above": lambda self, title, above: stacking_calls.append((title, above))},
    )())

    FollowSurfaceMixin._apply_follow_state(
        stub,
        WindowState(0, 0, 10, 10, is_foreground=True, is_visible=True),
    )

    assert stacking_calls == []
