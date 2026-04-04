"""Shared integration base for overlay window-management helpers."""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication, QWindow
from PyQt6.QtWidgets import QWidget

MonitorSnapshot = Tuple[str, int, int, int, int]


class IntegrationBase:
    """Generic integration base shared across platform-specific implementations."""

    def __init__(self, widget: QWidget, logger: logging.Logger, context: object) -> None:
        self._widget = widget
        self._logger = logger
        self._context = context
        self._window: Optional[QWindow] = None

    def update_context(self, context: object) -> None:
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
