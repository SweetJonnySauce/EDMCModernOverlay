"""Platform-specific helpers for window stacking and click-through handling."""
from __future__ import annotations

import ctypes
import logging
import os
import sys
from dataclasses import dataclass
from typing import Any, List, Mapping, Optional, Tuple

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication, QWindow
from PyQt6.QtWidgets import QWidget

MonitorSnapshot = Tuple[str, int, int, int, int]


@dataclass
class PlatformContext:
    """Hints provided by the EDMC plugin about the current desktop environment."""

    session_type: str = ""
    compositor: str = ""
    force_xwayland: bool = False
    flatpak: bool = False
    flatpak_app: str = ""


class _IntegrationBase:
    """Base class for per-platform integrations."""

    def __init__(
        self,
        widget: QWidget,
        logger: logging.Logger,
        context: PlatformContext,
        *,
        disable_ws_ex_transparent: bool = False,
    ) -> None:
        self._widget = widget
        self._logger = logger
        self._context = context
        self._window: Optional[QWindow] = None
        self._disable_ws_ex_transparent = disable_ws_ex_transparent

    def update_context(self, context: PlatformContext) -> None:
        self._context = context

    def prepare_window(self, window: Optional[QWindow]) -> None:
        self._window = window

    def apply_click_through(self, transparent: bool) -> None:
        window = self._window or self._widget.windowHandle()
        if window and hasattr(Qt.WindowType, "WindowTransparentForInput"):
            window.setFlag(Qt.WindowType.WindowTransparentForInput, transparent)

    def monitors(self) -> List[MonitorSnapshot]:
        snapshot: List[MonitorSnapshot] = []
        for index, screen in enumerate(QGuiApplication.screens()):
            try:
                geometry = screen.nativeGeometry()
            except AttributeError:
                geometry = screen.geometry()
            if geometry.width() <= 0 or geometry.height() <= 0:
                geometry = screen.geometry()
            name = screen.name() or screen.manufacturer() or f"screen-{index}"
            snapshot.append((name, geometry.x(), geometry.y(), geometry.width(), geometry.height()))
        return snapshot

    def log_native_window_state(self, reason: str, *, extra: Optional[Mapping[str, Any]] = None) -> None:
        """Emit platform-specific diagnostics for the overlay window."""
        return None


class _WindowsIntegration(_IntegrationBase):
    """Windows-specific integration that toggles WS_EX_TRANSPARENT."""

    def __init__(
        self,
        widget: QWidget,
        logger: logging.Logger,
        context: PlatformContext,
        *,
        disable_ws_ex_transparent: bool = False,
    ) -> None:
        super().__init__(
            widget,
            logger,
            context,
            disable_ws_ex_transparent=disable_ws_ex_transparent,
        )
        self._last_hwnd: Optional[int] = None

    def apply_click_through(self, transparent: bool) -> None:
        super().apply_click_through(transparent)
        if not transparent:
            return
        if self._disable_ws_ex_transparent:
            self._logger.debug("Skipping WS_EX_TRANSPARENT application due to dev toggle")
            return
        try:
            user32 = ctypes.windll.user32  # type: ignore[attr-defined]
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x80000
            WS_EX_TRANSPARENT = 0x20
            hwnd = int(self._widget.winId())
            style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT)
            self._logger.debug("Applied WS_EX_TRANSPARENT to overlay window (hwnd=%s)", hex(hwnd))
        except Exception as exc:  # pragma: no cover - best effort
            self._logger.debug("Failed to apply Windows click-through flags: %s", exc)

    def log_native_window_state(self, reason: str, *, extra: Optional[Mapping[str, Any]] = None) -> None:
        GWL_STYLE = -16
        GWL_EXSTYLE = -20
        DWMWA_EXTENDED_FRAME_BOUNDS = 9
        widget = self._widget
        window = self._window or widget.windowHandle()
        try:
            hwnd = int(widget.winId())
        except Exception as exc:
            self._logger.debug("Windows native window state unavailable (%s): %s", reason, exc)
            return

        style_value = None
        exstyle_value = None
        rect_value = None
        frame_value = None
        try:
            user32 = ctypes.windll.user32  # type: ignore[attr-defined]
            style_value = int(user32.GetWindowLongW(hwnd, GWL_STYLE))
            exstyle_value = int(user32.GetWindowLongW(hwnd, GWL_EXSTYLE))

            class _RECT(ctypes.Structure):
                _fields_ = [
                    ("left", ctypes.c_long),
                    ("top", ctypes.c_long),
                    ("right", ctypes.c_long),
                    ("bottom", ctypes.c_long),
                ]

            rect = _RECT()
            if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                rect_value = (int(rect.left), int(rect.top), int(rect.right), int(rect.bottom))

            try:
                dwmapi = ctypes.windll.dwmapi  # type: ignore[attr-defined]
                frame = _RECT()
                result = dwmapi.DwmGetWindowAttribute(
                    hwnd,
                    ctypes.c_uint(DWMWA_EXTENDED_FRAME_BOUNDS),
                    ctypes.byref(frame),
                    ctypes.sizeof(frame),
                )
                if result == 0:
                    frame_value = (int(frame.left), int(frame.top), int(frame.right), int(frame.bottom))
            except Exception:
                frame_value = None
        except Exception as exc:
            self._logger.debug("Failed to gather Windows native window state (%s): %s", reason, exc)
            return

        qt_flags = widget.windowFlags()
        transparent_input = False
        if window is not None:
            try:
                transparent_input = bool(window.flags() & Qt.WindowType.WindowTransparentForInput)
            except Exception:
                transparent_input = False

        state = {
            "reason": reason,
            "hwnd": hex(hwnd),
            "hwnd_changed": self._last_hwnd is not None and self._last_hwnd != hwnd,
            "qt_flags": hex(int(qt_flags)),
            "qt_flag_names": _window_flag_names(qt_flags),
            "window_handle_flags": None if window is None else hex(int(window.flags())),
            "window_handle_flag_names": [] if window is None else _window_flag_names(window.flags()),
            "translucent_background": bool(widget.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)),
            "transparent_mouse": bool(widget.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)),
            "transparent_input": transparent_input,
            "visible": bool(widget.isVisible()),
            "active": bool(widget.isActiveWindow()),
            "style": None if style_value is None else hex(style_value),
            "exstyle": None if exstyle_value is None else hex(exstyle_value),
            "style_names": [] if style_value is None else _style_flag_names(style_value),
            "exstyle_names": [] if exstyle_value is None else _exstyle_flag_names(exstyle_value),
            "rect": rect_value,
            "extended_frame": frame_value,
            "geometry": (
                int(widget.geometry().x()),
                int(widget.geometry().y()),
                int(widget.geometry().width()),
                int(widget.geometry().height()),
            ),
            "frame_geometry": (
                int(widget.frameGeometry().x()),
                int(widget.frameGeometry().y()),
                int(widget.frameGeometry().width()),
                int(widget.frameGeometry().height()),
            ),
        }
        if extra:
            state["extra"] = dict(extra)
        self._logger.debug("Windows native window state: %s", state)
        self._last_hwnd = hwnd


class _XcbIntegration(_IntegrationBase):
    """X11 integration that relies on Qt's transparent input flag."""

    # No extra logic; base implementation suffices.
    pass


class _WaylandIntegration(_IntegrationBase):
    """Wayland integration that attempts compositor-specific behaviour."""

    def __init__(
        self,
        widget: QWidget,
        logger: logging.Logger,
        context: PlatformContext,
        *,
        disable_ws_ex_transparent: bool = False,
    ) -> None:
        super().__init__(
            widget,
            logger,
            context,
            disable_ws_ex_transparent=disable_ws_ex_transparent,
        )
        self._layer_shell = None

    def prepare_window(self, window: Optional[QWindow]) -> None:
        super().prepare_window(window)
        if window is None:
            return
        compositor = (self._context.compositor or "").lower()
        self._logger.debug(
            "Wayland integration initialising: platform=%s compositor=%s force_xwayland=%s",
            QGuiApplication.platformName(),
            compositor or "unknown",
            self._context.force_xwayland,
        )
        if compositor in {"sway", "wayfire", "wlroots", "hyprland"}:
            self._initialise_layer_shell(window)
        elif compositor == "kwin":
            self._logger.debug("KWin Wayland detected; relying on Qt input flags for click-through")
        elif compositor in {"gnome-shell", "mutter"}:
            self._logger.info(
                "GNOME Shell detected – install the EDMC Modern Overlay GNOME extension for full click-through support."
            )
        else:
            if compositor:
                self._logger.debug("Unknown Wayland compositor '%s'; falling back to generic behaviour", compositor)

    def apply_click_through(self, transparent: bool) -> None:
        super().apply_click_through(transparent)
        window = self._window or self._widget.windowHandle()
        compositor = (self._context.compositor or "").lower()
        if not transparent or window is None:
            return
        if self._layer_shell is not None:
            self._configure_layer_shell_interactivity()
        elif compositor == "kwin":
            self._apply_kwin_input_region(window)
        else:
            self._apply_native_transparency(window)

    def _initialise_layer_shell(self, window: QWindow) -> None:
        try:
            import importlib

            module = importlib.import_module("PyQt6.QtWaylandClient")
        except Exception as exc:
            self._logger.debug("QtWaylandClient unavailable; cannot request layer-shell surface: %s", exc)
            return

        layer_shell_cls = getattr(module, "QWaylandLayerShellV1", None) or getattr(
            module, "QWaylandLayerShell", None
        )
        if layer_shell_cls is None:
            self._logger.debug("QtWaylandClient missing QWaylandLayerShellV1/QWaylandLayerShell class")
            return
        try:
            layer_shell = layer_shell_cls(window)
            layer_enum = getattr(layer_shell_cls, "Layer", None)
            if layer_enum is not None:
                overlay_layer = getattr(layer_enum, "Overlay", None)
                if overlay_layer is not None:
                    layer_shell.setLayer(overlay_layer)
            scope_method = getattr(layer_shell, "setScope", None)
            if callable(scope_method):
                scope_method("edmc-modern-overlay")
            exclusive_zone = getattr(layer_shell, "setExclusiveZone", None)
            if callable(exclusive_zone):
                exclusive_zone(-1)
            keyboard_enum = getattr(layer_shell_cls, "KeyboardInteractivity", None)
            if keyboard_enum is not None:
                none_value = getattr(keyboard_enum, "None", None) or getattr(
                    keyboard_enum, "KeyboardInteractivityNone", None
                )
                if none_value is not None:
                    set_keyboard = getattr(layer_shell, "setKeyboardInteractivity", None)
                    if callable(set_keyboard):
                        set_keyboard(none_value)
            apply_method = getattr(layer_shell, "apply", None)
            if callable(apply_method):
                apply_method()
            self._layer_shell = layer_shell
            self._logger.debug("Configured Wayland layer-shell surface for overlay window")
        except Exception as exc:  # pragma: no cover - best effort only
            self._logger.warning("Failed to initialise Wayland layer-shell surface: %s", exc)

    def _configure_layer_shell_interactivity(self) -> None:
        try:
            set_keyboard = getattr(self._layer_shell, "setKeyboardInteractivity", None)
            keyboard_enum = getattr(type(self._layer_shell), "KeyboardInteractivity", None)
            if callable(set_keyboard) and keyboard_enum is not None:
                none_value = getattr(keyboard_enum, "None", None) or getattr(
                    keyboard_enum, "KeyboardInteractivityNone", None
                )
                if none_value is not None:
                    set_keyboard(none_value)
            exclusive_zone = getattr(self._layer_shell, "setExclusiveZone", None)
            if callable(exclusive_zone):
                exclusive_zone(-1)
            apply_method = getattr(self._layer_shell, "apply", None)
            if callable(apply_method):
                apply_method()
            self._logger.debug("Updated Wayland layer-shell surface to disable input")
        except Exception as exc:  # pragma: no cover - best effort
            self._logger.debug("Failed to adjust layer-shell interactivity: %s", exc)

    def _apply_kwin_input_region(self, window: QWindow) -> None:
        try:
            from pydbus import SessionBus  # type: ignore  # pylint: disable=import-outside-toplevel
        except Exception as exc:
            self._logger.debug("pydbus unavailable; falling back to generic Qt click-through for KWin: %s", exc)
            return
        try:
            bus = SessionBus()
            scripting = bus.get("org.kde.KWin", "/Scripting")
            script_source = """
                var winId = %d;
                var client = workspace.windowForId(winId);
                if (client) {
                    client.skipSwitcher = true;
                    client.skipTaskbar = true;
                    client.blockInput = true;
                }
            """ % int(self._widget.winId())
            script = scripting.loadScript("edmcModernOverlayClickThrough", script_source)
            script.run()
            self._logger.debug("Executed KWin scripting hook to suppress overlay input")
        except Exception as exc:
            self._logger.debug("KWin scripting hook failed: %s", exc)

    def _apply_native_transparency(self, window: QWindow) -> None:
        native_getter = getattr(window, "nativeInterface", None)
        if not callable(native_getter):
            self._logger.debug(
                "QWindow.nativeInterface() unavailable; skipping Wayland native transparency hook (Qt<6.6?)"
            )
            return
        native_interface = native_getter()
        try:
            wayland_namespace = getattr(native_interface, "nativeResourceForWindow", None)
            if callable(wayland_namespace):
                wl_surface = wayland_namespace("wl_surface", window)
                if wl_surface:
                    self._logger.debug("Wayland wl_surface acquired; compositor should honour transparent input")
        except Exception as exc:  # pragma: no cover - diagnostic only
            self._logger.debug("Unable to query Wayland native resources: %s", exc)


class PlatformController:
    """Facade that selects the correct integration for the running platform."""

    def __init__(
        self,
        widget: QWidget,
        logger: logging.Logger,
        context: PlatformContext,
        *,
        disable_ws_ex_transparent: bool = False,
    ) -> None:
        self._widget = widget
        self._logger = logger
        self._context = context
        self._disable_ws_ex_transparent = disable_ws_ex_transparent
        self._platform_name = (QGuiApplication.platformName() or "").lower()
        self._integration = self._select_integration()

    def _select_integration(self) -> _IntegrationBase:
        if sys.platform.startswith("win"):
            self._logger.debug("Selecting Windows integration for overlay client")
            return _WindowsIntegration(
                self._widget,
                self._logger,
                self._context,
                disable_ws_ex_transparent=self._disable_ws_ex_transparent,
            )
        if self._context.force_xwayland or self._platform_name.startswith("xcb"):
            self._logger.debug("Selecting XCB/X11 integration for overlay client")
            return _XcbIntegration(
                self._widget,
                self._logger,
                self._context,
                disable_ws_ex_transparent=self._disable_ws_ex_transparent,
            )
        if (os.environ.get("XDG_SESSION_TYPE") or "").lower() == "x11":
            self._logger.debug("XDG_SESSION_TYPE indicates X11; using XCB integration")
            return _XcbIntegration(
                self._widget,
                self._logger,
                self._context,
                disable_ws_ex_transparent=self._disable_ws_ex_transparent,
            )
        self._logger.debug("Selecting Wayland integration for overlay client")
        return _WaylandIntegration(
            self._widget,
            self._logger,
            self._context,
            disable_ws_ex_transparent=self._disable_ws_ex_transparent,
        )

    def update_context(self, context: PlatformContext) -> None:
        self._context = context
        self._integration.update_context(context)

    def prepare_window(self, window: Optional[QWindow]) -> None:
        self._integration.prepare_window(window)

    def apply_click_through(self, transparent: bool) -> None:
        self._integration.apply_click_through(transparent)

    def monitors(self) -> List[MonitorSnapshot]:
        return self._integration.monitors()

    def log_native_window_state(self, reason: str, *, extra: Optional[Mapping[str, Any]] = None) -> None:
        self._integration.log_native_window_state(reason, extra=extra)

    def platform_label(self) -> str:
        """Return a human-readable platform label for status messages."""
        if sys.platform.startswith("win"):
            return "Windows"
        session = (self._context.session_type or "").lower()
        if not session:
            session = (os.environ.get("XDG_SESSION_TYPE") or "").lower()
        platform_name = (QGuiApplication.platformName() or self._platform_name or "").lower()
        if session == "wayland" and (self._context.force_xwayland or platform_name.startswith("xcb")):
            return "Wayland (XWayland)"
        if platform_name.startswith("wayland"):
            return "Wayland"
        if session == "wayland":
            return "Wayland"
        if self._context.force_xwayland:
            return "X11"
        if session == "x11":
            return "X11"
        if platform_name.startswith("xcb"):
            return "X11"
        return "Wayland"


def _window_flag_names(flags: Qt.WindowType) -> list[str]:
    names: list[str] = []
    known_flags = (
        ("Window", Qt.WindowType.Window),
        ("Tool", Qt.WindowType.Tool),
        ("FramelessWindowHint", Qt.WindowType.FramelessWindowHint),
        ("WindowStaysOnTopHint", Qt.WindowType.WindowStaysOnTopHint),
        ("WindowTransparentForInput", getattr(Qt.WindowType, "WindowTransparentForInput", Qt.WindowType(0))),
        ("NoDropShadowWindowHint", getattr(Qt.WindowType, "NoDropShadowWindowHint", Qt.WindowType(0))),
    )
    for name, flag in known_flags:
        if flag and flags & flag:
            names.append(name)
    return names


def _style_flag_names(style: int) -> list[str]:
    known_flags = (
        ("WS_BORDER", 0x00800000),
        ("WS_CAPTION", 0x00C00000),
        ("WS_CHILD", 0x40000000),
        ("WS_CLIPCHILDREN", 0x02000000),
        ("WS_CLIPSIBLINGS", 0x04000000),
        ("WS_DISABLED", 0x08000000),
        ("WS_DLGFRAME", 0x00400000),
        ("WS_GROUP", 0x00020000),
        ("WS_HSCROLL", 0x00100000),
        ("WS_MAXIMIZE", 0x01000000),
        ("WS_MAXIMIZEBOX", 0x00010000),
        ("WS_MINIMIZE", 0x20000000),
        ("WS_MINIMIZEBOX", 0x00020000),
        ("WS_OVERLAPPED", 0x00000000),
        ("WS_OVERLAPPEDWINDOW", 0x00CF0000),
        ("WS_POPUP", 0x80000000),
        ("WS_SIZEBOX", 0x00040000),
        ("WS_SYSMENU", 0x00080000),
        ("WS_THICKFRAME", 0x00040000),
        ("WS_VISIBLE", 0x10000000),
        ("WS_VSCROLL", 0x00200000),
    )
    return [name for name, flag in known_flags if flag != 0 and style & flag == flag]


def _exstyle_flag_names(exstyle: int) -> list[str]:
    known_flags = (
        ("WS_EX_ACCEPTFILES", 0x00000010),
        ("WS_EX_APPWINDOW", 0x00040000),
        ("WS_EX_CLIENTEDGE", 0x00000200),
        ("WS_EX_COMPOSITED", 0x02000000),
        ("WS_EX_DLGMODALFRAME", 0x00000001),
        ("WS_EX_LAYERED", 0x00080000),
        ("WS_EX_LAYOUTRTL", 0x00400000),
        ("WS_EX_NOACTIVATE", 0x08000000),
        ("WS_EX_NOREDIRECTIONBITMAP", 0x00200000),
        ("WS_EX_OVERLAPPEDWINDOW", 0x00000300),
        ("WS_EX_STATICEDGE", 0x00020000),
        ("WS_EX_TOOLWINDOW", 0x00000080),
        ("WS_EX_TOPMOST", 0x00000008),
        ("WS_EX_TRANSPARENT", 0x00000020),
        ("WS_EX_WINDOWEDGE", 0x00000100),
    )
    return [name for name, flag in known_flags if exstyle & flag == flag]
