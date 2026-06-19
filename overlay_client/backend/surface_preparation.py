"""Backend-owned requests for preparing the Qt surface before presentation."""

from __future__ import annotations

from dataclasses import dataclass

BACKEND_PRESENTATION_SURFACE_PREPARATION_FULLSCREEN_MONITOR = "fullscreen_monitor"
BACKEND_PRESENTATION_SURFACE_PREPARATION_MANAGED_WINDOWED = "managed_windowed"


@dataclass(frozen=True, slots=True)
class BackendPresentationSurfacePreparation:
    """Request a generic Qt surface state before backend presentation validation."""

    mode: str
    rect: tuple[int, int, int, int]
    reason: str
    target_token: str = ""
    rect_source: str = ""
