"""Helpers for stand-alone mode support."""
from __future__ import annotations


STANDALONE_MODE_PREF_KEY = "standalone_mode"
STANDALONE_MODE_LABEL = "Run overlay in stand-alone mode"
STANDALONE_MODE_TOOLTIP = (
    "Run the overlay as a stand-alone window for capture tools and VR "
    "(may appear in Alt-Tab/taskbar)."
)


def standalone_mode_supported() -> bool:
    return True


def standalone_mode_preference_value(preferences: object) -> bool:
    return bool(getattr(preferences, STANDALONE_MODE_PREF_KEY, False))
