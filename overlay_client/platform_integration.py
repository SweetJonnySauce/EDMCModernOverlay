"""Platform-specific helpers for window stacking and click-through handling."""
from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from typing import List, Optional

from PyQt6.QtGui import QGuiApplication, QWindow
from PyQt6.QtWidgets import QWidget

from overlay_client.backend import BackendSelectionStatus
from overlay_client.backend.consumers import (
    create_bundle_integration,
    ensure_linux_backend_status,
    is_wayland_bundle,
    platform_label_for_bundle,
    resolve_linux_bundle_from_status,
    uses_transient_parent,
)
from overlay_client.window_integration import IntegrationBase as _IntegrationBase, MonitorSnapshot


@dataclass
class PlatformContext:
    """Hints provided by the EDMC plugin about the current desktop environment."""

    session_type: str = ""
    compositor: str = ""
    manual_backend_override: str = ""
    flatpak: bool = False
    flatpak_app: str = ""


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

    def _current_linux_status(self) -> BackendSelectionStatus:
        return ensure_linux_backend_status(
            self._backend_status,
            session_type=self._context.session_type,
            compositor=self._context.compositor,
            qt_platform_name=self._platform_name,
            manual_override=self._context.manual_backend_override,
            flatpak=self._context.flatpak,
            flatpak_app_id=self._context.flatpak_app,
        )

    def _current_linux_bundle(self):
        return resolve_linux_bundle_from_status(self._current_linux_status())

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
