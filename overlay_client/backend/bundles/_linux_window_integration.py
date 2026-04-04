"""Backend-owned Linux integration implementations for shipped XCB and native Wayland paths."""

from __future__ import annotations

import logging
from typing import Protocol

from PyQt6.QtGui import QGuiApplication, QWindow
from PyQt6.QtWidgets import QWidget

from overlay_client.window_integration import IntegrationBase


class LinuxIntegrationContext(Protocol):
    """Subset of context fields used by the shipped Linux integration implementations."""

    compositor: str


class _XcbIntegration(IntegrationBase):
    """X11 integration that relies on Qt's transparent input flag."""

    # No extra logic; base implementation suffices.
    pass


def create_xcb_integration(
    widget: QWidget,
    logger: logging.Logger,
    context: LinuxIntegrationContext,
) -> IntegrationBase:
    """Create the shipped XCB/X11 integration used by both X11 and XWayland paths."""

    return _XcbIntegration(widget, logger, context)


class _WaylandIntegration(IntegrationBase):
    """Wayland integration that attempts compositor-specific behaviour."""

    def __init__(self, widget: QWidget, logger: logging.Logger, context: LinuxIntegrationContext) -> None:
        super().__init__(widget, logger, context)
        self._layer_shell = None

    def prepare_window(self, window: QWindow | None) -> None:
        super().prepare_window(window)
        if window is None:
            return
        compositor = (self._context.compositor or "").lower()
        self._logger.debug(
            "Wayland integration initialising: platform=%s compositor=%s",
            QGuiApplication.platformName(),
            compositor or "unknown",
        )
        if compositor in {"sway", "wayfire", "wlroots", "hyprland"}:
            self._initialise_layer_shell(window)
        elif compositor == "kwin":
            self._logger.debug("KWin Wayland detected; relying on Qt input flags for click-through")
        elif compositor in {"gnome-shell", "mutter"}:
            self._logger.info(
                "GNOME Shell detected – install the EDMC Modern Overlay GNOME extension for full click-through support."
            )
        elif compositor:
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
                none_value = getattr(layer_shell_enum := keyboard_enum, "None", None) or getattr(
                    layer_shell_enum, "KeyboardInteractivityNone", None
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


def create_wayland_integration(
    widget: QWidget,
    logger: logging.Logger,
    context: LinuxIntegrationContext,
) -> IntegrationBase:
    """Create the shipped Wayland integration used by native Wayland backend bundles."""

    return _WaylandIntegration(widget, logger, context)
