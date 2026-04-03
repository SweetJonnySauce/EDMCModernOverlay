from __future__ import annotations

import logging
import sys
import types

try:  # pragma: no cover - exercised when PyQt6 is present
    from PyQt6 import QtGui as _QtGui  # noqa: F401
except Exception:  # pragma: no cover - lightweight stub path
    if "PyQt6" not in sys.modules:
        sys.modules["PyQt6"] = types.ModuleType("PyQt6")
    if "PyQt6.QtGui" not in sys.modules:
        qtgui = types.ModuleType("PyQt6.QtGui")
        qtgui.QGuiApplication = type(
            "QGuiApplication",
            (),
            {"platformName": staticmethod(lambda: "wayland")},
        )
        qtgui.QPainter = object
        sys.modules["PyQt6.QtGui"] = qtgui

from overlay_client.backend import ProbeSource
from overlay_client.control_surface import ControlSurfaceMixin
from overlay_client.platform_context import _backend_status_signature, _client_backend_status
from overlay_client.platform_integration import PlatformContext


class _StubPlatformController:
    def __init__(self) -> None:
        self.updated = []
        self.backend_statuses = []
        self.prepared = []
        self.click_through = []

    def update_context(self, context) -> None:
        self.updated.append(context)

    def update_backend_status(self, status) -> None:
        self.backend_statuses.append(status)

    def prepare_window(self, window) -> None:
        self.prepared.append(window)

    def apply_click_through(self, transparent: bool) -> None:
        self.click_through.append(bool(transparent))


class _StubInteractionController:
    def __init__(self) -> None:
        self.reapply_calls = []

    def reapply_current(self, *, reason: str = "") -> None:
        self.reapply_calls.append(reason)


class _Window(ControlSurfaceMixin):
    def __init__(self) -> None:
        self._platform_context = PlatformContext(session_type="x11", compositor="kwin", force_xwayland=False)
        self._platform_controller = _StubPlatformController()
        self._interaction_controller = _StubInteractionController()
        self._show_status = False
        self._status_raw = "ready"
        self._status = "ready"
        self._plugin_backend_status_hint = None
        self._client_backend_status = _client_backend_status(
            self._platform_context,
            source=ProbeSource.INITIAL_HINTS,
            qt_platform_name="xcb",
            env={"XDG_SESSION_TYPE": "x11"},
            sys_platform_name="linux",
        )
        self._last_client_backend_status_signature = _backend_status_signature(self._client_backend_status)
        self._last_backend_mismatch_signature = None
        self.restore_calls = 0

    def windowHandle(self):
        return object()

    def _restore_drag_interactivity(self) -> None:
        self.restore_calls += 1

    def _format_status_message(self, raw: str) -> str:
        return f"formatted:{raw}"

    def _show_overlay_status_message(self, message: str) -> None:  # pragma: no cover - not used in this test
        raise AssertionError(f"unexpected status message: {message}")


def test_update_platform_context_computes_client_owned_status_and_logs_mismatch(monkeypatch, caplog) -> None:
    window = _Window()
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "GNOME")
    monkeypatch.setattr("overlay_client.control_surface.QGuiApplication.platformName", lambda: "wayland")

    caplog.set_level(logging.INFO, logger="EDMC.ModernOverlay.Client")
    window.update_platform_context(
        {
            "session_type": "x11",
            "compositor": "kwin",
            "force_xwayland": False,
            "shadow_backend_status": {
                "selected_backend": {"family": "native_x11", "instance": "native_x11"},
                "classification": "true_overlay",
                "shadow_mode": True,
            },
        }
    )

    assert window._plugin_backend_status_hint is not None
    assert window._client_backend_status.shadow_mode is False
    assert window._client_backend_status.selected_backend.instance.value == "gnome_shell_wayland"
    assert window._platform_controller.updated == []
    assert window._platform_controller.backend_statuses == []
    assert window._interaction_controller.reapply_calls == []
    assert window.restore_calls == 0
    assert window._last_backend_mismatch_signature is not None


def test_update_platform_context_pushes_client_backend_status_into_runtime_consumers(monkeypatch) -> None:
    window = _Window()
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "KDE")
    monkeypatch.setattr("overlay_client.control_surface.QGuiApplication.platformName", lambda: "wayland")

    window.update_platform_context(
        {
            "session_type": "wayland",
            "compositor": "kwin",
            "force_xwayland": False,
        }
    )

    assert window._platform_controller.updated
    assert len(window._platform_controller.backend_statuses) == 1
    assert window._platform_controller.backend_statuses[0].selected_backend.instance.value == "kwin_wayland"
    assert window._interaction_controller.reapply_calls == ["platform_context_update"]
    assert window.restore_calls == 1
