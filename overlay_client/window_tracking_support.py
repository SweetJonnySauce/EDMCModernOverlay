"""Shared tracker data and monitor-normalization helpers."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Callable, List, Optional, Protocol, Tuple


@dataclass(slots=True)
class WindowState:
    """Geometry details for a tracked window in virtual desktop coordinates."""

    x: int
    y: int
    width: int
    height: int
    is_foreground: bool
    is_visible: bool
    identifier: str = ""
    global_x: Optional[int] = None
    global_y: Optional[int] = None


MonitorSnapshot = Tuple[str, int, int, int, int]
MonitorProvider = Callable[[], List[MonitorSnapshot]]

_TITLE_PATTERN = re.compile(r"elite\s*-\s*dangerous", re.IGNORECASE)


def matches_window_title(title: str, hint: str) -> bool:
    """Return whether a window title matches the Elite title hint/pattern."""

    if not title:
        return False
    lowered = title.lower()
    if hint and hint in lowered:
        return True
    return bool(_TITLE_PATTERN.search(title))


def invoke_monitor_provider(provider: Optional[MonitorProvider], logger: logging.Logger) -> List[MonitorSnapshot]:
    """Safely collect a monitor snapshot from the provided callback."""

    if provider is None:
        return []
    try:
        snapshot = provider()
    except Exception as exc:
        logger.debug("Monitor provider failed: %s", exc)
        return []
    return list(snapshot)


def _find_monitor_for_rect(
    monitors: List[MonitorSnapshot],
    x: int,
    y: int,
    width: int,
    height: int,
    *,
    relative: bool,
) -> Optional[MonitorSnapshot]:
    best: Optional[MonitorSnapshot] = None
    best_area = 0
    for name, offset_x, offset_y, mon_w, mon_h in monitors:
        global_x = x + offset_x if relative else x
        global_y = y + offset_y if relative else y
        overlap_w = max(0, min(global_x + width, offset_x + mon_w) - max(global_x, offset_x))
        overlap_h = max(0, min(global_y + height, offset_y + mon_h) - max(global_y, offset_y))
        area = overlap_w * overlap_h
        if area > best_area:
            best_area = area
            best = (name, offset_x, offset_y, mon_w, mon_h)
    return best


def augment_state_with_monitors(
    state: WindowState,
    monitors: List[MonitorSnapshot],
    logger: logging.Logger,
    *,
    absolute_geometry: Optional[Tuple[int, int, int, int]] = None,
) -> WindowState:
    """Augment tracker state with absolute/global coordinates from monitor offsets."""

    width = state.width
    height = state.height
    abs_x: Optional[int]
    abs_y: Optional[int]

    if absolute_geometry is not None:
        abs_x, abs_y, abs_width, abs_height = absolute_geometry
        if abs_width:
            width = abs_width
        if abs_height:
            height = abs_height
    else:
        abs_x = None
        abs_y = None

    monitor_info = None
    if abs_x is not None and abs_y is not None and monitors:
        monitor_info = _find_monitor_for_rect(monitors, abs_x, abs_y, width, height, relative=False)
    if monitor_info is None and monitors:
        monitor_info = _find_monitor_for_rect(monitors, state.x, state.y, state.width, state.height, relative=True)

    if monitor_info is not None:
        name, offset_x, offset_y, mon_w, mon_h = monitor_info
        global_x = abs_x if abs_x is not None else state.x + offset_x
        global_y = abs_y if abs_y is not None else state.y + offset_y
        if abs_x is None or abs_y is None or (global_x, global_y) != (abs_x, abs_y):
            logger.debug(
                "Monitor %s offsets applied: offset=(%d,%d) raw=(%s,%s) global=(%d,%d) size=%dx%d",
                name,
                offset_x,
                offset_y,
                abs_x if abs_x is not None else "n/a",
                abs_y if abs_y is not None else "n/a",
                global_x,
                global_y,
                mon_w,
                mon_h,
            )
        abs_x = global_x
        abs_y = global_y

    if abs_x is None or abs_y is None:
        return WindowState(
            x=state.x,
            y=state.y,
            width=width,
            height=height,
            is_foreground=state.is_foreground,
            is_visible=state.is_visible,
            identifier=state.identifier,
            global_x=None,
            global_y=None,
        )

    return WindowState(
        x=abs_x,
        y=abs_y,
        width=width,
        height=height,
        is_foreground=state.is_foreground,
        is_visible=state.is_visible,
        identifier=state.identifier,
        global_x=abs_x,
        global_y=abs_y,
    )


class WindowTracker(Protocol):
    """Simple protocol for retrieving Elite window state."""

    def poll(self) -> Optional[WindowState]:
        ...

    def set_monitor_provider(self, provider: Optional[MonitorProvider]) -> None:
        ...
