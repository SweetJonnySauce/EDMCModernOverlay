"""Backend-owned Linux tracker implementations for shipped X11 and native Wayland paths."""

from __future__ import annotations

import json
import logging
import re
import subprocess
import time
from typing import List, Optional, Tuple

from overlay_client.window_tracking_support import (
    MonitorProvider,
    MonitorSnapshot,
    WindowState,
    WindowTracker,
    augment_state_with_monitors,
    invoke_monitor_provider,
    matches_window_title,
)


class _WmctrlTracker:
    """Use wmctrl/xwininfo to locate Elite windows under X11."""

    def __init__(
        self,
        logger: logging.Logger,
        title_hint: str,
        monitor_provider: Optional[MonitorProvider],
    ) -> None:
        self._logger = logger
        self._title_hint = title_hint.lower()
        self._last_state: Optional[WindowState] = None
        self._last_refresh: float = 0.0
        self._min_interval: float = 0.3
        self._wmctrl_missing = False
        self._last_logged_identifier: Optional[str] = None
        self._monitor_provider = monitor_provider

    def poll(self) -> Optional[WindowState]:
        if self._wmctrl_missing:
            return None
        now = time.monotonic()
        if self._last_state and now - self._last_refresh < self._min_interval:
            return self._last_state
        try:
            result = subprocess.run(
                ["wmctrl", "-lGx"],
                check=False,
                capture_output=True,
                text=True,
                timeout=1.0,
            )
        except FileNotFoundError:
            self._wmctrl_missing = True
            self._logger.warning("wmctrl binary not found; overlay follow mode disabled")
            self._last_state = None
            return None
        except subprocess.SubprocessError as exc:
            self._logger.debug("wmctrl invocation failed: %s", exc)
            self._last_state = None
            self._last_refresh = now
            return None

        self._last_refresh = now
        if result.returncode != 0:
            self._logger.debug("wmctrl returned non-zero status: %s", result.returncode)
            self._last_state = None
            return None

        active_id = self._active_window_id()
        target_state: Optional[WindowState] = None
        best_state: Optional[WindowState] = None
        best_area = 0
        for line in result.stdout.splitlines():
            fields = line.split(None, 8)
            if len(fields) < 9:
                continue
            win_id_hex, desktop, x, y, w, h, wm_class, host, title = fields
            if not self._matches_title(title):
                continue
            try:
                x_val = int(x)
                y_val = int(y)
                width = int(w)
                height = int(h)
                win_id = int(win_id_hex, 16)
            except ValueError:
                continue
            is_foreground = active_id is not None and win_id == active_id
            is_visible = width > 0 and height > 0
            candidate = WindowState(
                x=x_val,
                y=y_val,
                width=width,
                height=height,
                is_foreground=is_foreground,
                is_visible=is_visible,
                identifier=win_id_hex,
            )
            if is_foreground:
                target_state = candidate
                break
            area = max(width, 0) * max(height, 0)
            if area > best_area:
                best_state = candidate
                best_area = area

        if target_state is None:
            target_state = best_state

        if target_state is None:
            if self._last_logged_identifier is not None:
                self._logger.debug("wmctrl tracker did not locate an Elite Dangerous window")
                self._last_logged_identifier = None
            self._last_state = None
            return None

        monitor_offsets = invoke_monitor_provider(self._monitor_provider, self._logger)
        augmented = self._augment_with_global_coordinates(target_state, monitor_offsets)
        self._last_state = augmented
        return augmented

    def set_monitor_provider(self, provider: Optional[MonitorProvider]) -> None:
        self._monitor_provider = provider

    def _augment_with_global_coordinates(
        self,
        state: WindowState,
        monitor_offsets: List[MonitorSnapshot],
    ) -> WindowState:
        geometry = self._absolute_geometry(state.identifier) if monitor_offsets else None
        return augment_state_with_monitors(
            state,
            monitor_offsets,
            self._logger,
            absolute_geometry=geometry,
        )

    def _absolute_geometry(self, win_id_hex: str) -> Optional[Tuple[int, int, int, int]]:
        try:
            result = subprocess.run(
                ["xwininfo", "-id", win_id_hex],
                check=False,
                capture_output=True,
                text=True,
                timeout=0.5,
            )
        except FileNotFoundError:
            return None
        except subprocess.SubprocessError as exc:
            self._logger.debug("xwininfo invocation failed: %s", exc)
            return None
        if result.returncode != 0:
            self._logger.debug(
                "xwininfo returned non-zero status %s for window %s",
                result.returncode,
                win_id_hex,
            )
            return None
        if win_id_hex != self._last_logged_identifier:
            self._logger.debug("xwininfo dump for %s:\n%s", win_id_hex, result.stdout.strip())
            self._last_logged_identifier = win_id_hex
        abs_x = abs_y = width = height = None
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("Absolute upper-left X:"):
                try:
                    abs_x = int(line.split(":", 1)[1])
                except ValueError:
                    abs_x = None
            elif line.startswith("Absolute upper-left Y:"):
                try:
                    abs_y = int(line.split(":", 1)[1])
                except ValueError:
                    abs_y = None
            elif line.startswith("Width:"):
                try:
                    width = int(line.split(":", 1)[1])
                except ValueError:
                    width = None
            elif line.startswith("Height:"):
                try:
                    height = int(line.split(":", 1)[1])
                except ValueError:
                    height = None
            if abs_x is not None and abs_y is not None and width is not None and height is not None:
                break
        if abs_x is None or abs_y is None:
            return None
        return abs_x, abs_y, width or 0, height or 0

    def _matches_title(self, title: str) -> bool:
        return matches_window_title(title, self._title_hint)

    def _active_window_id(self) -> Optional[int]:
        try:
            result = subprocess.run(
                ["xprop", "-root", "_NET_ACTIVE_WINDOW"],
                check=False,
                capture_output=True,
                text=True,
                timeout=0.5,
            )
        except FileNotFoundError:
            return None
        except subprocess.SubprocessError:
            return None
        if result.returncode != 0 or not result.stdout:
            return None
        match = re.search(r"0x[0-9a-fA-F]+", result.stdout)
        if not match:
            return None
        try:
            return int(match.group(0), 16)
        except ValueError:
            return None


def create_wmctrl_tracker(
    logger: logging.Logger,
    title_hint: str = "elite - dangerous",
    monitor_provider: Optional[MonitorProvider] = None,
) -> WindowTracker:
    """Create the shipped X11 wmctrl/xwininfo tracker used by X11-derived paths."""

    return _WmctrlTracker(logger, title_hint, monitor_provider)


class _WaylandTrackerBase:
    """Shared helpers for Wayland-based trackers."""

    def __init__(
        self,
        logger: logging.Logger,
        title_hint: str,
        monitor_provider: Optional[MonitorProvider],
    ) -> None:
        self._logger = logger
        self._title_hint = title_hint.lower()
        self._monitor_provider = monitor_provider
        self._last_state: Optional[WindowState] = None
        self._last_refresh: float = 0.0
        self._refresh_interval: float = 0.3

    def set_monitor_provider(self, provider: Optional[MonitorProvider]) -> None:
        self._monitor_provider = provider

    def _maybe_use_cache(self) -> Optional[WindowState]:
        now = time.monotonic()
        if self._last_state is not None and now - self._last_refresh < self._refresh_interval:
            return self._last_state
        self._last_refresh = now
        return None

    def _complete(self, state: Optional[WindowState]) -> Optional[WindowState]:
        self._last_state = state
        return state

    def _monitors(self) -> List[MonitorSnapshot]:
        return invoke_monitor_provider(self._monitor_provider, self._logger)

    def _matches(self, title: str) -> bool:
        return matches_window_title(title, self._title_hint)


class _SwayTracker(_WaylandTrackerBase):
    """Use swaymsg on wlroots compositors such as Sway or Wayfire."""

    def __init__(
        self,
        logger: logging.Logger,
        title_hint: str,
        monitor_provider: Optional[MonitorProvider],
    ) -> None:
        super().__init__(logger, title_hint, monitor_provider)
        self._binary_missing = False

    def poll(self) -> Optional[WindowState]:
        cached = self._maybe_use_cache()
        if cached is not None:
            return cached
        try:
            result = subprocess.run(
                ["swaymsg", "-t", "get_tree"],
                check=False,
                capture_output=True,
                text=True,
                timeout=1.0,
            )
        except FileNotFoundError:
            if not self._binary_missing:
                self._logger.warning("swaymsg not found; Wayland follow mode disabled for wlroots compositor")
                self._binary_missing = True
            return self._complete(None)
        except subprocess.SubprocessError as exc:
            self._logger.debug("swaymsg invocation failed: %s", exc)
            return self._complete(None)

        if result.returncode != 0 or not result.stdout:
            self._logger.debug("swaymsg returned status %s", result.returncode)
            return self._complete(None)

        try:
            tree = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            self._logger.debug("Failed to parse sway tree JSON: %s", exc)
            return self._complete(None)

        focused, fallback = self._extract_window(tree)
        state = focused or fallback
        if state is None:
            return self._complete(None)

        monitors = self._monitors()
        augmented = augment_state_with_monitors(state, monitors, self._logger)
        return self._complete(augmented)

    def _extract_window(self, root: dict) -> Tuple[Optional[WindowState], Optional[WindowState]]:
        target: Optional[WindowState] = None
        best: Optional[WindowState] = None
        best_area = 0
        stack = [root]
        while stack:
            node = stack.pop()
            name = node.get("name") or ""
            if self._matches(name):
                rect = node.get("rect") or {}
                try:
                    x = int(rect.get("x", 0))
                    y = int(rect.get("y", 0))
                    width = int(rect.get("width", 0))
                    height = int(rect.get("height", 0))
                except (TypeError, ValueError):
                    width = height = 0
                    x = y = 0
                if width > 0 and height > 0:
                    identifier = str(node.get("id", ""))
                    state = WindowState(
                        x=x,
                        y=y,
                        width=width,
                        height=height,
                        is_foreground=bool(node.get("focused")),
                        is_visible=True,
                        identifier=identifier,
                    )
                    if node.get("focused"):
                        return state, best
                    area = width * height
                    if area > best_area:
                        best_area = area
                        best = state
            for key in ("nodes", "floating_nodes"):
                children = node.get(key, [])
                if isinstance(children, list):
                    stack.extend(children)
        return target, best


def create_sway_tracker(
    logger: logging.Logger,
    title_hint: str = "elite - dangerous",
    monitor_provider: Optional[MonitorProvider] = None,
) -> WindowTracker:
    """Create the shipped wlroots/Sway tracker used by native Wayland bundles."""

    return _SwayTracker(logger, title_hint, monitor_provider)


class _HyprlandTracker(_WaylandTrackerBase):
    """Use hyprctl JSON output on Hyprland."""

    def __init__(
        self,
        logger: logging.Logger,
        title_hint: str,
        monitor_provider: Optional[MonitorProvider],
    ) -> None:
        super().__init__(logger, title_hint, monitor_provider)
        self._binary_missing = False
        self._active_query_supported = True

    def poll(self) -> Optional[WindowState]:
        cached = self._maybe_use_cache()
        if cached is not None:
            return cached
        try:
            result = subprocess.run(
                ["hyprctl", "clients", "-j"],
                check=False,
                capture_output=True,
                text=True,
                timeout=1.0,
            )
        except FileNotFoundError:
            if not self._binary_missing:
                self._logger.warning("hyprctl not found; Wayland follow mode disabled for Hyprland")
                self._binary_missing = True
            return self._complete(None)
        except subprocess.SubprocessError as exc:
            self._logger.debug("hyprctl invocation failed: %s", exc)
            return self._complete(None)

        if result.returncode != 0 or not result.stdout:
            self._logger.debug("hyprctl returned status %s", result.returncode)
            return self._complete(None)

        try:
            clients = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            self._logger.debug("Failed to parse hyprctl clients JSON: %s", exc)
            return self._complete(None)

        active_address = None
        if self._active_query_supported:
            try:
                active = subprocess.run(
                    ["hyprctl", "activewindow", "-j"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=0.5,
                )
                if active.returncode == 0 and active.stdout:
                    data = json.loads(active.stdout)
                    active_address = str(data.get("address"))
            except (FileNotFoundError, subprocess.SubprocessError, json.JSONDecodeError):
                self._active_query_supported = False

        target: Optional[WindowState] = None
        best: Optional[WindowState] = None
        best_area = 0
        if isinstance(clients, list):
            for client in clients:
                title = str(client.get("title") or "")
                if not self._matches(title):
                    continue
                at = client.get("at") or client.get("position") or [client.get("x"), client.get("y")]
                size = client.get("size") or [client.get("width"), client.get("height")]
                try:
                    x = int(at[0])
                    y = int(at[1])
                    width = int(size[0])
                    height = int(size[1])
                except (TypeError, ValueError, IndexError):
                    continue
                if width <= 0 or height <= 0:
                    continue
                identifier = str(client.get("address") or "")
                is_focused = bool(client.get("focused")) or (active_address is not None and identifier == active_address)
                state = WindowState(
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    is_foreground=is_focused,
                    is_visible=bool(client.get("mapped", True)) and not bool(client.get("hidden", False)),
                    identifier=identifier or title,
                )
                if is_focused:
                    target = state
                    break
                area = width * height
                if area > best_area:
                    best_area = area
                    best = state

        state: Optional[WindowState] = target or best
        if state is None:
            return self._complete(None)

        monitors = self._monitors()
        augmented = augment_state_with_monitors(state, monitors, self._logger)
        return self._complete(augmented)


def create_hyprland_tracker(
    logger: logging.Logger,
    title_hint: str = "elite - dangerous",
    monitor_provider: Optional[MonitorProvider] = None,
) -> WindowTracker:
    """Create the shipped Hyprland tracker used by native Wayland bundles."""

    return _HyprlandTracker(logger, title_hint, monitor_provider)


class _KWinTracker(_WaylandTrackerBase):
    """Use the KWin DBus interface on KDE Plasma Wayland."""

    def __init__(
        self,
        logger: logging.Logger,
        title_hint: str,
        monitor_provider: Optional[MonitorProvider],
    ) -> None:
        super().__init__(logger, title_hint, monitor_provider)
        self._kwin = None
        self._pydbus_available = True
        self._warned = False

    def _ensure_interface(self) -> bool:
        if self._kwin is not None:
            return True
        if not self._pydbus_available:
            return False
        try:
            from pydbus import SessionBus  # type: ignore
        except Exception as exc:
            if not self._warned:
                self._logger.warning("pydbus is required for KDE Wayland tracking: %s", exc)
                self._warned = True
            self._pydbus_available = False
            return False
        try:
            bus = SessionBus()
            self._kwin = bus.get("org.kde.KWin", "/KWin")
            return True
        except Exception as exc:
            if not self._warned:
                self._logger.warning("Failed to connect to KWin via DBus: %s", exc)
                self._warned = True
            return False

    def poll(self) -> Optional[WindowState]:
        cached = self._maybe_use_cache()
        if cached is not None:
            return cached
        if not self._ensure_interface():
            return self._complete(None)

        try:
            window_ids = list(self._kwin.windowList())  # type: ignore[operator]
        except Exception as exc:
            self._logger.debug("KWin windowList query failed: %s", exc)
            return self._complete(None)

        try:
            active_window = str(self._kwin.activeWindow())  # type: ignore[operator]
        except Exception:
            active_window = ""

        target: Optional[WindowState] = None
        best: Optional[WindowState] = None
        best_area = 0

        for window_id in window_ids:
            try:
                info = dict(self._kwin.windowInfo(window_id))  # type: ignore[operator]
            except Exception:
                continue
            title = str(info.get("caption") or info.get("visibleName") or "")
            if not self._matches(title):
                continue
            geometry = info.get("geometry") or {}
            try:
                x = int(geometry.get("x", 0))
                y = int(geometry.get("y", 0))
                width = int(geometry.get("width", 0))
                height = int(geometry.get("height", 0))
            except (TypeError, ValueError):
                continue
            if width <= 0 or height <= 0:
                continue
            identifier = str(window_id)
            is_foreground = identifier == active_window
            is_visible = not bool(info.get("minimized", False))
            state = WindowState(
                x=x,
                y=y,
                width=width,
                height=height,
                is_foreground=is_foreground,
                is_visible=is_visible,
                identifier=identifier,
            )
            if is_foreground:
                target = state
                break
            area = width * height
            if area > best_area:
                best_area = area
                best = state

        state: Optional[WindowState] = target or best
        if state is None:
            return self._complete(None)

        monitors = self._monitors()
        augmented = augment_state_with_monitors(state, monitors, self._logger)
        return self._complete(augmented)


def create_kwin_tracker(
    logger: logging.Logger,
    title_hint: str = "elite - dangerous",
    monitor_provider: Optional[MonitorProvider] = None,
) -> WindowTracker:
    """Create the shipped KWin tracker used by native Wayland bundles."""

    return _KWinTracker(logger, title_hint, monitor_provider)
