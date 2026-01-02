"""Helpers for OBS capture-friendly support."""
from __future__ import annotations

import sys


OBS_CAPTURE_PREF_KEY = "obs_capture_friendly"
OBS_CAPTURE_LABEL = "OBS capture-friendly mode (Windows only)"
OBS_CAPTURE_TOOLTIP = (
    "Expose the overlay window for OBS Window Capture "
    "(may appear in Alt-Tab/taskbar)."
)


def obs_capture_supported() -> bool:
    return sys.platform.startswith("win")


def obs_capture_preference_value(preferences: object) -> bool:
    if not obs_capture_supported():
        return False
    return bool(getattr(preferences, OBS_CAPTURE_PREF_KEY, False))
