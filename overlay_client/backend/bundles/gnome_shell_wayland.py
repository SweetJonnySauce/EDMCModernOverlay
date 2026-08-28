"""Explicit GNOME Shell Wayland bundle built from current shipped logic."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from overlay_client.backend.bundles._wayland_common import build_native_wayland_bundle, create_unavailable_tracker
from overlay_client.backend.contracts import BackendBundle, BackendDescriptor, BackendFamily, BackendInstance, HelperKind
from overlay_client.backend.presentation_runtime import (
    BackendPresentationRuntimeProfile,
    BackendPresentationRuntimeRequest,
    BackendPresentationRuntimeResult,
)

if TYPE_CHECKING:
    from overlay_client.backend.status import BackendSelectionStatus


@dataclass(frozen=True, slots=True)
class GnomeShellPresentationRuntime:
    """GNOME-owned adaptation of the existing helper presentation runner."""

    profile: BackendPresentationRuntimeProfile

    def helper_presentation_available(self, status: object) -> bool:
        for helper_state in getattr(status, "helper_states", ()):
            if getattr(helper_state, "helper", None) is HelperKind.GNOME_SHELL_EXTENSION and helper_state.available:
                return True
        return False

    def run_presentation_cycle(
        self,
        status: "BackendSelectionStatus",
        request: BackendPresentationRuntimeRequest,
    ) -> BackendPresentationRuntimeResult | None:
        if not self.helper_presentation_available(status):
            if self.profile.helper_unavailable_is_terminal:
                return BackendPresentationRuntimeResult(helper_unavailable=True)
            return None
        runner = request.presentation_cycle_runner or self._presentation_cycle_runner()
        return BackendPresentationRuntimeResult(
            presentation_result=runner(
                standalone_mode=request.standalone_mode,
                keep_overlay_visible=request.keep_overlay_visible,
                previous_surface_action=request.previous_surface_action,
                title_bar_compensation_enabled=request.title_bar_compensation_enabled,
                title_bar_compensation_height=request.title_bar_compensation_height,
                presentation_refresh_requested=request.presentation_refresh_requested,
                prepare_surface=request.prepare_surface,
                shell_raster_frame_provider=request.raster_frame_provider,
                shell_raster_runtime_enabled=self.profile.fullscreen_shell_raster_active,
                suppress_pyqt_fallback_on_shell_raster_failure=(
                    self.profile.suppress_managed_pyqt_fallback_on_shell_raster_failure
                ),
            )
        )

    @staticmethod
    def _presentation_cycle_runner():
        from overlay_client.backend.bundles._gnome_shell_helper_presentation import (
            run_gnome_shell_helper_presentation_cycle,
        )

        return run_gnome_shell_helper_presentation_cycle


_NATIVE_GNOME_PRESENTATION_PROFILE = BackendPresentationRuntimeProfile(
    owns_helper_presentation=True,
    supports_fullscreen_shell_raster=True,
    fullscreen_shell_raster_active=True,
    suppress_managed_pyqt_fallback_on_shell_raster_failure=True,
    helper_unavailable_is_terminal=False,
)

_LEGACY_RASTER_PRESENTATION_PROFILE = BackendPresentationRuntimeProfile(
    owns_helper_presentation=True,
    supports_fullscreen_shell_raster=True,
    fullscreen_shell_raster_active=True,
    suppress_managed_pyqt_fallback_on_shell_raster_failure=True,
    helper_unavailable_is_terminal=True,
)


def build_gnome_shell_wayland_bundle() -> BackendBundle:
    """Build the explicit GNOME Shell Wayland bundle for the current helper-required path."""

    return replace(
        build_native_wayland_bundle(BackendInstance.GNOME_SHELL_WAYLAND, create_unavailable_tracker),
        presentation_runtime=GnomeShellPresentationRuntime(_NATIVE_GNOME_PRESENTATION_PROFILE),
    )


def build_gnome_shell_raster_bundle() -> BackendBundle:
    """Build the explicit GNOME Shell raster bundle for the support-gated helper path."""

    bundle = build_native_wayland_bundle(BackendInstance.GNOME_SHELL_RASTER, create_unavailable_tracker)
    return replace(
        bundle,
        descriptor=BackendDescriptor(BackendFamily.COMPOSITOR_HELPER, BackendInstance.GNOME_SHELL_RASTER),
        capabilities=replace(bundle.capabilities, platform_label="GNOME Shell Raster"),
        presentation_runtime=GnomeShellPresentationRuntime(_LEGACY_RASTER_PRESENTATION_PROFILE),
    )
