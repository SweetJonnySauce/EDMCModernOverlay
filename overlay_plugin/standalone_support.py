"""Helpers for stand-alone mode support."""
from __future__ import annotations

import sys


STANDALONE_MODE_PREF_KEY = "standalone_mode"
STANDALONE_MODE_LABEL = "Run overlay in stand-alone mode (Windows Only)"
STANDALONE_MODE_TOOLTIP = (
    "Run the overlay as a stand-alone window for capture tools and VR "
    "(may appear in Alt-Tab/taskbar)."
)


def standalone_mode_supported() -> bool:
    return sys.platform.startswith("win")


def standalone_mode_preference_value(preferences: object) -> bool:
    if not standalone_mode_supported():
        return False
    return bool(getattr(preferences, STANDALONE_MODE_PREF_KEY, False))
