import pytest

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


class _StubFollowController:
    def __init__(self) -> None:
        self.wm_override = None
        self.wm_override_tracker = None
        self.override_expired_calls = []
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

    def override_expired(self, *, tracker_tuple=None, standalone_mode: bool = False) -> bool:
        self.override_expired_calls.append(
            {
                "tracker_tuple": tracker_tuple,
                "standalone_mode": standalone_mode,
            }
        )
        return False


class _StubVisibilityHelper:
    def __init__(self) -> None:
        self.calls = []
        self.raise_on_show_flags = []

    def update_visibility(
        self,
        show,
        *,
        is_visible_fn,
        show_fn,
        hide_fn,
        raise_fn,
        apply_drag_state_fn,
        format_scale_debug_fn,
        raise_on_show=True,
    ):
        self.calls.append(show)
        self.raise_on_show_flags.append(bool(raise_on_show))
        if show:
            show_fn()
            if raise_on_show:
                raise_fn()
            apply_drag_state_fn()
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
        self._standalone_mode = False
        self.raise_calls = 0
        self._window_handle = _StubWindowHandle()

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
        return self._window_handle

    def frameGeometry(self):
        return _StubFrame()

    def setGeometry(self, *_args, **_kwargs) -> None:
        return None

    def raise_(self) -> None:
        self.raise_calls += 1
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

    def _apply_drag_state(self, *, raise_window: bool = True) -> None:
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
    assert stub._follow_controller.override_expired_calls[-1] == {
        "tracker_tuple": tracker,
        "standalone_mode": False,
    }


def test_resolve_and_apply_geometry_passes_standalone_mode_to_override_expiry():
    stub = _FollowSurfaceStub()
    stub._standalone_mode = True

    stub._resolve_and_apply_geometry((2, 4, 6, 8), (10, 20, 30, 40))

    assert stub._follow_controller.override_expired_calls[-1] == {
        "tracker_tuple": (2, 4, 6, 8),
        "standalone_mode": True,
    }


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


def test_ensure_transient_parent_clears_existing_parent_when_standalone(monkeypatch: pytest.MonkeyPatch):
    stub = _FollowSurfaceStub()
    stub._standalone_mode = True
    stub._transient_parent_window = object()
    stub._transient_parent_id = "abc"
    state = WindowState(x=0, y=0, width=100, height=50, is_foreground=True, is_visible=True, identifier="10")
    monkeypatch.setattr("overlay_client.follow_surface.sys.platform", "linux")

    stub._ensure_transient_parent(state)

    assert stub._transient_parent_window is None
    assert stub._transient_parent_id is None
    assert stub.windowHandle().transient_parents[-1] is None


def test_ensure_transient_parent_sets_parent_when_not_standalone(monkeypatch: pytest.MonkeyPatch):
    stub = _FollowSurfaceStub()
    parent_window = object()
    state = WindowState(x=0, y=0, width=100, height=50, is_foreground=True, is_visible=True, identifier="10")
    monkeypatch.setattr("overlay_client.follow_surface.sys.platform", "linux")
    monkeypatch.setattr("overlay_client.follow_surface.QWindow.fromWinId", lambda _native_id: parent_window)

    stub._ensure_transient_parent(state)

    assert stub._transient_parent_window is parent_window
    assert stub._transient_parent_id == "10"
    assert stub.windowHandle().transient_parents[-1] is parent_window


def test_post_process_follow_state_passes_standalone_mode_to_controller() -> None:
    stub = _FollowSurfaceStub()
    stub._standalone_mode = True
    captured = {}
    visibility_calls: list[bool] = []

    class _CaptureController:
        def __init__(self) -> None:
            self._fullscreen_hint_logged = False

        def post_process_follow_state(self, state, target_tuple, **kwargs):
            captured["standalone_mode"] = kwargs.get("standalone_mode")
            kwargs["update_follow_visibility_fn"](True)

    stub._window_controller = _CaptureController()
    stub._update_follow_visibility = lambda show: visibility_calls.append(show)  # type: ignore[assignment]
    state = WindowState(x=0, y=0, width=100, height=50, is_foreground=False, is_visible=True, identifier="10")

    stub._post_process_follow_state(state, target_tuple=(0, 0, 100, 50))

    assert captured["standalone_mode"] is True
    assert visibility_calls == [True]


def test_update_follow_visibility_disables_raise_on_show_in_standalone() -> None:
    stub = _FollowSurfaceStub()
    stub._standalone_mode = True

    stub._update_follow_visibility(True)

    assert stub._visibility_helper.raise_on_show_flags == [False]
    assert stub.raise_calls == 0


def test_update_follow_visibility_keeps_raise_on_show_when_not_standalone() -> None:
    stub = _FollowSurfaceStub()
    stub._standalone_mode = False

    stub._update_follow_visibility(True)

    assert stub._visibility_helper.raise_on_show_flags == [True]
    assert stub.raise_calls == 1
