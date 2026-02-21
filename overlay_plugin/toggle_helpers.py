from __future__ import annotations

from typing import Any

from .preferences import _coerce_last_on_payload_opacity


def toggle_payload_opacity(preferences: Any) -> int:
    """Toggle payload opacity and update last-on tracking, returning the new opacity."""
    try:
        current = int(getattr(preferences, "global_payload_opacity", 100))
    except (TypeError, ValueError):
        current = 100
    if current > 0:
        last_on = _coerce_last_on_payload_opacity(current, 100)
        preferences.last_on_payload_opacity = last_on
        preferences.global_payload_opacity = 0
        return 0
    last_on = _coerce_last_on_payload_opacity(
        getattr(preferences, "last_on_payload_opacity", 100),
        100,
    )
    preferences.last_on_payload_opacity = last_on
    preferences.global_payload_opacity = last_on
    return last_on
