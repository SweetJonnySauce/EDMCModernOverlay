from __future__ import annotations

import sys
import types
from typing import Any, Optional

# Prefer real PyQt6; fall back to lightweight stubs only if unavailable (CI/headless).
try:  # pragma: no cover - exercised in environments with PyQt6 present
    from PyQt6 import QtCore as _QtCore  # noqa: F401
    from PyQt6 import QtGui as _QtGui  # noqa: F401
    from PyQt6 import QtWidgets as _QtWidgets  # noqa: F401
except Exception:  # pragma: no cover - lightweight stub path
    if "PyQt6" not in sys.modules:
        sys.modules["PyQt6"] = types.ModuleType("PyQt6")
    if "PyQt6.QtCore" not in sys.modules:
        qtcore = types.ModuleType("PyQt6.QtCore")
        qtcore.Qt = types.SimpleNamespace(KeyboardModifier=types.SimpleNamespace(AltModifier=1))
        sys.modules["PyQt6.QtCore"] = qtcore
    if "PyQt6.QtGui" not in sys.modules:
        qtgui = types.ModuleType("PyQt6.QtGui")

        class _QFont:
            def __init__(self, *args, **kwargs) -> None:
                self._family = ""

            def family(self) -> str:
                return self._family

            def setFamilies(self, families):
                self._family = families[0] if families else ""

            def setFallbackFamilies(self, families):
                return

        class _QFontMetrics:
            def __init__(self, font) -> None:
                self._font = font

        qtgui.QFont = _QFont
        qtgui.QFontMetrics = _QFontMetrics
        qtgui.QGuiApplication = type(
            "QGuiApplication",
            (),
            {"primaryScreen": staticmethod(lambda: None), "screens": staticmethod(lambda: [])},
        )
        qtgui.QWindow = type(
            "QWindow",
            (),
            {"setFlag": lambda self, *args, **kwargs: None},
        )
        qtgui.QPainter = object
        sys.modules["PyQt6.QtGui"] = qtgui
    if "PyQt6.QtWidgets" not in sys.modules:
        qtwidgets = types.ModuleType("PyQt6.QtWidgets")
        qtwidgets.QApplication = type(
            "QApplication",
            (),
            {"queryKeyboardModifiers": staticmethod(lambda: 0)},
        )
        qtwidgets.QWidget = type(
            "QWidget",
            (),
            {"windowHandle": lambda self: None, "winId": lambda self: 0},
        )
        sys.modules["PyQt6.QtWidgets"] = qtwidgets

from overlay_client.control_surface import ControlSurfaceMixin
from overlay_client.platform_context import PlatformContext


class _StubFollowController:
    def __init__(self) -> None:
        self.reset_resume_window_calls = 0
        self.wm_override = None

    def reset_resume_window(self) -> None:
        self.reset_resume_window_calls += 1


class _StubWindow(ControlSurfaceMixin):
    def __init__(self, *, follow_enabled: bool = True, has_tracker: bool = True) -> None:
        self._physical_clamp_overrides = {}
        self._follow_controller = _StubFollowController()
        self._follow_enabled = follow_enabled
        self._window_tracker = object() if has_tracker else None
        self._last_follow_state: Optional[tuple[Any, ...]] = ("state",)
        self.refresh_called = 0
        self.apply_called = 0
        self.update_called = 0

    def _refresh_follow_geometry(self) -> None:
        self.refresh_called += 1

    def _apply_follow_state(self, state) -> None:  # pragma: no cover - simple counter
        self.apply_called += 1

    def update(self) -> None:  # pragma: no cover - simple counter
        self.update_called += 1


class _StubStandaloneWindow(ControlSurfaceMixin):
    def __init__(self) -> None:
        self._standalone_mode = False
        self._standalone_restart_warning_key = None
        self._platform_context = PlatformContext(
            session_type="wayland",
            compositor="mutter",
            force_xwayland=True,
            flatpak=False,
            flatpak_app="",
        )
        self._status = ""
        self._status_raw = ""
        self._show_status = False
        self.messages: list[tuple[str, Optional[float]]] = []
        self.profile_reasons: list[str] = []
        self.drag_state_calls = 0
        self.identity_calls = 0
        self.clear_override_reasons: list[str] = []
        self.clear_parent_reasons: list[str] = []
        self.restore_drag_calls = 0
        self.reapply_reasons: list[str] = []
        self._follow_controller = _StubFollowController()
        self._interaction_controller = type(
            "StubInteractionController",
            (),
            {"reapply_current": lambda _self, *, reason="": self.reapply_reasons.append(reason)},
        )()
        self._platform_controller = type(
            "StubPlatformController",
            (),
            {
                "update_context": lambda _self, _ctx: None,
                "prepare_window": lambda _self, _window: None,
                "apply_click_through": lambda _self, _flag: None,
                "platform_label": lambda _self: "Wayland",
            },
        )()

    def _apply_standalone_window_profile(self, *, reason: str) -> None:
        self.profile_reasons.append(reason)

    def _apply_drag_state(self) -> None:
        self.drag_state_calls += 1

    def _apply_standalone_window_identity(self) -> None:
        self.identity_calls += 1

    def _clear_transient_parent_binding(self, *, reason: str) -> None:
        self.clear_parent_reasons.append(reason)

    def _clear_wm_override(self, reason: str) -> None:
        self.clear_override_reasons.append(reason)
        self._follow_controller.wm_override = None

    def _restore_drag_interactivity(self) -> None:
        self.restore_drag_calls += 1

    def display_message(self, message: str, *, ttl: Optional[float] = None) -> None:
        self.messages.append((message, ttl))

    def windowHandle(self):
        return object()

    def _format_status_message(self, status: str) -> str:
        return status

    def _show_overlay_status_message(self, status: str) -> None:
        return None


def test_set_physical_clamp_overrides_applies_and_refreshes() -> None:
    window = _StubWindow()

    window.set_physical_clamp_overrides({"DisplayPort-2": 4.0})

    assert window._physical_clamp_overrides == {"DisplayPort-2": 3.0}
    assert window._follow_controller.reset_resume_window_calls == 1
    assert window.refresh_called == 1
    assert window.apply_called == 0
    assert window.update_called == 0


def test_set_physical_clamp_overrides_no_change_noops() -> None:
    window = _StubWindow()
    window.set_physical_clamp_overrides({"DisplayPort-2": 1.25})

    window.set_physical_clamp_overrides({"DisplayPort-2": 1.25})

    assert window._follow_controller.reset_resume_window_calls == 1
    assert window.refresh_called == 1


def test_set_physical_clamp_overrides_empty_map_noops() -> None:
    window = _StubWindow()

    window.set_physical_clamp_overrides({})

    assert window._physical_clamp_overrides == {}
    assert window._follow_controller.reset_resume_window_calls == 0
    assert window.refresh_called == 0


def test_set_physical_clamp_overrides_applies_when_follow_disabled() -> None:
    window = _StubWindow(follow_enabled=False, has_tracker=False)

    window.set_physical_clamp_overrides({"HDMI-0": 0.75})

    assert window._physical_clamp_overrides == {"HDMI-0": 0.75}
    assert window._follow_controller.reset_resume_window_calls == 1
    assert window.refresh_called == 0
    assert window.apply_called == 1
    assert window.update_called == 0


def test_set_physical_clamp_overrides_ignores_invalid_values() -> None:
    window = _StubWindow()

    window.set_physical_clamp_overrides({"DisplayPort-2": 0, "HDMI-0": float("nan")})

    assert window._physical_clamp_overrides == {}
    assert window._follow_controller.reset_resume_window_calls == 0
    assert window.refresh_called == 0


def test_set_standalone_mode_applies_runtime_profile_and_warning(monkeypatch) -> None:
    window = _StubStandaloneWindow()
    monkeypatch.setattr("overlay_client.control_surface.sys.platform", "linux")

    window.set_standalone_mode(True)

    assert window._standalone_mode is True
    assert window.profile_reasons == ["set_standalone_mode"]
    assert window.reapply_reasons == ["standalone_mode_toggle"]
    assert window.clear_parent_reasons == ["standalone_mode_toggle"]
    assert window.drag_state_calls == 1
    assert window.identity_calls == 1
    assert len(window.messages) == 1
    assert window.clear_override_reasons == []


def test_standalone_warning_dedupes_same_transition() -> None:
    window = _StubStandaloneWindow()

    window._warn_standalone_restart_required(transition="context", reason="platform_context_update")
    window._warn_standalone_restart_required(transition="context", reason="platform_context_update")

    assert len(window.messages) == 1


def test_set_standalone_mode_reapplies_follow_state_immediately(monkeypatch) -> None:
    window = _StubStandaloneWindow()
    window._follow_enabled = True
    window._last_follow_state = ("follow-state",)
    applied: list[object] = []
    window._apply_follow_state = lambda state: applied.append(state)  # type: ignore[assignment]
    monkeypatch.setattr("overlay_client.control_surface.sys.platform", "linux")

    window.set_standalone_mode(True)

    assert applied == [("follow-state",)]


def test_set_standalone_mode_refreshes_follow_geometry_when_no_cached_state(monkeypatch) -> None:
    window = _StubStandaloneWindow()
    window._follow_enabled = True
    window._last_follow_state = None
    window._window_tracker = object()
    refresh_calls: list[bool] = []
    window._refresh_follow_geometry = lambda: refresh_calls.append(True)  # type: ignore[assignment]
    monkeypatch.setattr("overlay_client.control_surface.sys.platform", "linux")

    window.set_standalone_mode(True)

    assert refresh_calls == [True]


def test_platform_context_update_preserves_force_xwayland_and_reapplies_profile(monkeypatch) -> None:
    window = _StubStandaloneWindow()
    window._standalone_mode = True
    monkeypatch.setattr("overlay_client.control_surface.sys.platform", "linux")

    window.update_platform_context({"session_type": "wayland", "compositor": "kwin"})

    assert window._platform_context.force_xwayland is True
    assert window.profile_reasons == ["platform_context_update"]
    assert window.reapply_reasons == ["platform_context_update"]
    assert window.restore_drag_calls == 1
    assert len(window.messages) == 1


def test_set_standalone_mode_clears_wm_override_when_present(monkeypatch) -> None:
    window = _StubStandaloneWindow()
    window._follow_controller.wm_override = (1, 2, 3, 4)
    monkeypatch.setattr("overlay_client.control_surface.sys.platform", "linux")

    window.set_standalone_mode(True)

    assert window.clear_override_reasons == ["standalone_mode_toggle"]


def test_platform_context_update_clears_wm_override_when_present(monkeypatch) -> None:
    window = _StubStandaloneWindow()
    window._standalone_mode = True
    window._follow_controller.wm_override = (1, 2, 3, 4)
    monkeypatch.setattr("overlay_client.control_surface.sys.platform", "linux")

    window.update_platform_context({"session_type": "wayland", "compositor": "kwin"})

    assert window.clear_override_reasons == ["platform_context_update"]
