"""Neutral contracts for bundle-owned runtime presentation cycles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol, runtime_checkable


PresentationCycleRunner = Callable[..., object]
SurfacePreparer = Callable[[object], bool]
RasterFrameProvider = Callable[[object | None, object | None, bool], object]


@dataclass(frozen=True, slots=True)
class BackendPresentationRuntimeProfile:
    """Bundle-declared presentation ownership, raster, and helper-loss policy."""

    owns_helper_presentation: bool
    supports_fullscreen_shell_raster: bool
    fullscreen_shell_raster_active: bool
    suppress_managed_pyqt_fallback_on_shell_raster_failure: bool
    helper_unavailable_is_terminal: bool


@dataclass(frozen=True, slots=True)
class BackendPresentationRuntimeRequest:
    """Neutral inputs supplied by generic consumers for one runtime cycle."""

    standalone_mode: bool = False
    keep_overlay_visible: bool = False
    previous_surface_action: str = ""
    title_bar_compensation_enabled: bool = False
    title_bar_compensation_height: int = 0
    presentation_refresh_requested: bool = False
    presentation_cycle_runner: PresentationCycleRunner | None = None
    prepare_surface: SurfacePreparer | None = None
    raster_frame_provider: RasterFrameProvider | None = None


@dataclass(frozen=True, slots=True)
class BackendPresentationRuntimeResult:
    """Neutral runtime result, including the legacy fail-closed helper state."""

    presentation_result: object | None = None
    helper_unavailable: bool = False


@runtime_checkable
class PresentationRuntimeBackend(Protocol):
    """Bundle-owned runtime presentation behavior consumed without backend enums."""

    @property
    def profile(self) -> BackendPresentationRuntimeProfile:
        """Return the bundle-owned presentation policy."""

    def helper_presentation_available(self, status: object) -> bool:
        """Return whether the runtime can currently use its helper."""

    def run_presentation_cycle(
        self,
        status: object,
        request: BackendPresentationRuntimeRequest,
    ) -> BackendPresentationRuntimeResult | None:
        """Run one bundle-owned presentation cycle, if applicable."""
