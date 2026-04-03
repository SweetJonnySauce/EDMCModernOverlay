"""Platform-specific helpers for window stacking and click-through handling."""
from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication, QWindow
from PyQt6.QtWidgets import QWidget

from overlay_client.backend import BackendSelectionStatus
from overlay_client.backend.consumers import (
    create_bundle_integration,
    is_wayland_bundle,
    platform_label_for_bundle,
    resolve_legacy_linux_bundle,
    resolve_linux_bundle_from_status,
    uses_transient_parent,
)

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

    def __init__(self, widget: QWidget, logger: logging.Logger, context: PlatformContext) -> None:
        self._widget = widget
        self._logger = logger
        self._context = context
        self._window: Optional[QWindow] = None

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


class _WindowsIntegration(_IntegrationBase):
    """Windows-specific integration that toggles WS_EX_TRANSPARENT."""

    def apply_click_through(self, transparent: bool) -> None:
        super().apply_click_through(transparent)
        if not transparent:
            return
        try:
            import ctypes  # pylint: disable=import-outside-toplevel

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


class _XcbIntegration(_IntegrationBase):
    """X11 integration that relies on Qt's transparent input flag."""

    # No extra logic; base implementation suffices.
    pass


def create_xcb_integration(widget: QWidget, logger: logging.Logger, context: PlatformContext) -> _IntegrationBase:
    """Create the shipped XCB/X11 integration used by both X11 and XWayland paths."""

    return _XcbIntegration(widget, logger, context)


class _WaylandIntegration(_IntegrationBase):
    """Wayland integration that attempts compositor-specific behaviour."""

    def __init__(self, widget: QWidget, logger: logging.Logger, context: PlatformContext) -> None:
        super().__init__(widget, logger, context)
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


def create_wayland_integration(widget: QWidget, logger: logging.Logger, context: PlatformContext) -> _IntegrationBase:
    """Create the shipped Wayland integration used by native Wayland backend bundles."""

    return _WaylandIntegration(widget, logger, context)


class PlatformController:
    """Facade that selects the correct integration for the running platform."""

    def __init__(
        self,
        widget: QWidget,
        logger: logging.Logger,
        context: PlatformContext,
        *,
        backend_status: Optional[BackendSelectionStatus] = None,
    ) -> None:
        self._widget = widget
        self._logger = logger
        self._context = context
        self._platform_name = (QGuiApplication.platformName() or "").lower()
        self._backend_status = backend_status
        self._integration = self._select_integration()

    def _select_integration(self) -> _IntegrationBase:
        if sys.platform.startswith("win"):
            self._logger.debug("Selecting Windows integration for overlay client")
            return _WindowsIntegration(self._widget, self._logger, self._context)
        bundle = self._current_linux_bundle()
        self._logger.debug("Selecting bundle-backed integration for overlay client: %s", bundle.descriptor.support_label)
        return create_bundle_integration(bundle, self._widget, self._logger, self._context)

    def _current_linux_bundle(self):
        if self._backend_status is not None:
            return resolve_linux_bundle_from_status(self._backend_status)
        return resolve_legacy_linux_bundle(
            session_type=self._context.session_type,
            compositor=self._context.compositor,
            force_xwayland=self._context.force_xwayland,
            qt_platform_name=self._platform_name,
            env=os.environ,
        )

    def update_context(self, context: PlatformContext) -> None:
        self._context = context
        self._integration.update_context(context)

    def update_backend_status(self, status: Optional[BackendSelectionStatus]) -> None:
        if sys.platform.startswith("win"):
            self._backend_status = status
            return
        previous_bundle = self._current_linux_bundle()
        previous_window = getattr(self._integration, "_window", None)
        self._backend_status = status
        next_bundle = self._current_linux_bundle()
        if previous_bundle.descriptor != next_bundle.descriptor:
            self._logger.debug(
                "Switching bundle-backed integration for overlay client: %s -> %s",
                previous_bundle.descriptor.support_label,
                next_bundle.descriptor.support_label,
            )
            self._integration = create_bundle_integration(next_bundle, self._widget, self._logger, self._context)
            if previous_window is not None:
                self._integration.prepare_window(previous_window)

    def prepare_window(self, window: Optional[QWindow]) -> None:
        self._integration.prepare_window(window)

    def apply_click_through(self, transparent: bool) -> None:
        self._integration.apply_click_through(transparent)

    def monitors(self) -> List[MonitorSnapshot]:
        return self._integration.monitors()

    def is_wayland_backend(self) -> bool:
        if sys.platform.startswith("win"):
            return False
        return is_wayland_bundle(self._current_linux_bundle())

    def uses_transient_parent(self) -> bool:
        if not sys.platform.startswith("linux"):
            return False
        return uses_transient_parent(self._current_linux_bundle())

    def platform_label(self) -> str:
        """Return a human-readable platform label for status messages."""
        if sys.platform.startswith("win"):
            return "Windows"
        return platform_label_for_bundle(self._current_linux_bundle())
