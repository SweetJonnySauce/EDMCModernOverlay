"""Cross-platform helpers for tracking the Elite Dangerous game window."""
from __future__ import annotations

import logging
import os
import sys
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from overlay_client.backend import BackendSelectionStatus

from overlay_client.window_tracking_support import MonitorProvider, WindowState, WindowTracker, matches_window_title

_DWMWA_EXTENDED_FRAME_BOUNDS = 9


def create_elite_window_tracker(
    logger: logging.Logger,
    title_hint: str = "elite - dangerous",
    monitor_provider: Optional[MonitorProvider] = None,
    backend_status: Optional["BackendSelectionStatus"] = None,
) -> Optional[WindowTracker]:
    """Instantiate a platform-specific tracker for the Elite client."""

    platform = sys.platform
    if platform.startswith("win"):
        try:
            tracker: Optional[WindowTracker] = _WindowsTracker(logger, title_hint)
            return tracker
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.warning("Windows tracker unavailable: %s", exc)
            return None
    if platform.startswith("linux"):
        from overlay_client.backend.consumers import (
            create_bundle_tracker,
            ensure_linux_backend_status,
            resolve_linux_bundle_from_status,
            resolve_tracker_fallback_bundle,
        )

        effective_status = ensure_linux_backend_status(
            backend_status,
            session_type=(os.environ.get("EDMC_OVERLAY_SESSION_TYPE") or os.environ.get("XDG_SESSION_TYPE") or ""),
            compositor=(os.environ.get("EDMC_OVERLAY_COMPOSITOR") or ""),
            qt_platform_name=str(os.environ.get("QT_QPA_PLATFORM") or "").strip().lower(),
            env=os.environ,
        )
        bundle = resolve_linux_bundle_from_status(effective_status)
        try:
            tracker = create_bundle_tracker(
                bundle,
                logger,
                title_hint=title_hint,
                monitor_provider=monitor_provider,
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.warning("Tracker backend unavailable: %s", exc)
            return None
        if tracker is not None:
            return tracker
        fallback_bundle = resolve_tracker_fallback_bundle(effective_status)
        if fallback_bundle is None:
            return None
        if effective_status.probe.session_type.value == "wayland":
            logger.debug(
                "Wayland backend '%s' does not provide a tracker; attempting X11 fallback",
                bundle.descriptor.instance.value,
            )
        try:
            return create_bundle_tracker(
                fallback_bundle,
                logger,
                title_hint=title_hint,
                monitor_provider=monitor_provider,
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.warning("X11 tracker unavailable: %s", exc)
            return None

    logger.info("Window tracking not implemented for platform '%s'; follow mode disabled", platform)
    return None

ctypes: Any
wintypes: Any
try:
    import ctypes as _ctypes
    from ctypes import wintypes as _wintypes

    ctypes = _ctypes
    wintypes = _wintypes
except Exception:  # pragma: no cover - non-Windows platform
    ctypes = None
    wintypes = None


class _WindowsTracker:
    """Locate Elite - Dangerous windows using Win32 APIs."""

    def __init__(self, logger: logging.Logger, title_hint: str) -> None:
        if ctypes is None or wintypes is None:
            raise RuntimeError("ctypes is unavailable; cannot create Windows tracker")
        self._logger = logger
        self._title_hint = title_hint.lower()
        self._user32 = ctypes.windll.user32  # type: ignore[attr-defined]
        try:
            dwmapi = ctypes.windll.dwmapi  # type: ignore[attr-defined]
            self._dwm_get_window_attribute = dwmapi.DwmGetWindowAttribute
            self._dwm_get_window_attribute.argtypes = [  # type: ignore[attr-defined]
                wintypes.HWND,
                ctypes.c_uint,
                ctypes.POINTER(_RECT),
                ctypes.c_uint,
            ]
            self._dwm_get_window_attribute.restype = ctypes.c_int  # type: ignore[attr-defined]
        except Exception:
            self._dwm_get_window_attribute = None
        self._last_hwnd: Optional[int] = None
        self._enum_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)(self._enum_windows)

    def poll(self) -> Optional[WindowState]:
        hwnd = self._resolve_window()
        if hwnd is None:
            return None
        rect = self._window_bounds(hwnd)
        if rect is None:
            return None
        left, top, right, bottom = rect.left, rect.top, rect.right, rect.bottom
        width = max(0, right - left)
        height = max(0, bottom - top)
        if width <= 0 or height <= 0:
            return None
        foreground = self._user32.GetForegroundWindow()
        is_foreground = foreground and hwnd == foreground
        is_visible = bool(self._user32.IsWindowVisible(hwnd)) and not bool(self._user32.IsIconic(hwnd))
        identifier = hex(hwnd)
        return WindowState(
            x=int(left),
            y=int(top),
            width=int(width),
            height=int(height),
            is_foreground=bool(is_foreground),
            is_visible=is_visible,
            identifier=identifier,
        )

    def set_monitor_provider(self, provider: Optional[MonitorProvider]) -> None:
        # Monitor offsets are only used on X11/Wayland; Windows tracker ignores this hook.
        return None

    # Internal helpers -------------------------------------------------

    def _resolve_window(self) -> Optional[int]:
        hwnd = self._last_hwnd
        if hwnd and self._is_target(hwnd):
            return hwnd
        self._last_hwnd = None
        self._user32.EnumWindows(self._enum_proc, 0)
        return self._last_hwnd

    def _enum_windows(self, hwnd: int, _: int) -> bool:
        if self._is_target(hwnd):
            self._last_hwnd = hwnd
            return False
        return True

    def _window_bounds(self, hwnd: int) -> Optional[_RECT]:
        rect = _RECT()
        if self._dwm_get_window_attribute is not None:
            result = self._dwm_get_window_attribute(
                hwnd,
                ctypes.c_uint(_DWMWA_EXTENDED_FRAME_BOUNDS),
                ctypes.byref(rect),
                ctypes.sizeof(rect),
            )
            if result == 0:
                return rect
            self._logger.debug("DwmGetWindowAttribute failed with %s; falling back to GetWindowRect", result)
        if not self._user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            self._logger.debug("GetWindowRect failed for hwnd=%s", hex(hwnd))
            return None
        return rect

    def _is_target(self, hwnd: int) -> bool:
        if not self._user32.IsWindow(hwnd):
            return False
        length = self._user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return False
        buffer = ctypes.create_unicode_buffer(length + 1)
        self._user32.GetWindowTextW(hwnd, buffer, length + 1)
        title = buffer.value.strip().lower()
        if not title:
            return False
        if not matches_window_title(title, self._title_hint):
            return False
        if not self._user32.IsWindowVisible(hwnd):
            return False
        return True


class _RECT(ctypes.Structure):  # type: ignore[misc]
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]
