"""Generic bundle-consumer helpers introduced before runtime cutover."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Mapping, Optional

from overlay_client.backend.contracts import BackendBundle, BackendInstance, HelperKind
from overlay_client.backend.presentation_policy import BackendPresentationVisibilitySnapshot
from overlay_client.backend.probe import ProbeInputs, ProbeSource, collect_platform_probe
from overlay_client.backend.selector import BackendSelector
from overlay_client.backend.status import BackendSelectionStatus
from overlay_client.backend.surface_preparation import (
    BACKEND_PRESENTATION_SURFACE_PREPARATION_MANAGED_WINDOWED,
    BackendPresentationSurfacePreparation,
)

if TYPE_CHECKING:
    from overlay_client.backend import HelperPresentationRequest, HelperTargetStatus
    from overlay_client.backend.bundles._gnome_shell_helper_presentation import GnomeHelperPresentationCycleResult
    from overlay_client.backend.shell_raster_frame import ShellRasterFrameBuildResult
    from overlay_client.platform_integration import PlatformContext
    from overlay_client.window_tracking import MonitorProvider, WindowTracker


@dataclass(frozen=True, slots=True)
class BackendPresentationCycleResult:
    """Backend-facing runtime presentation result for generic follow consumers."""

    should_show_overlay: bool
    scale_size: tuple[int, int] | None = None
    prime_rect: tuple[int, int, int, int] | None = None
    prime_rect_source: str = "unavailable"
    diagnostics: Mapping[str, object] = field(default_factory=dict)
    visibility_snapshot: BackendPresentationVisibilitySnapshot = field(default_factory=BackendPresentationVisibilitySnapshot)
    log_prefix: str = "Backend presentation"

    def diagnostic_signature(self) -> tuple[object, ...]:
        """Return a stable signature suitable for log de-duplication."""

        payload = self.diagnostics
        return (
            payload.get("helper_health"),
            payload.get("target_state"),
            payload.get("target_token"),
            payload.get("target_sequence"),
            payload.get("target_monitor"),
            payload.get("target_output_name"),
            str(payload.get("target_monitor_rect")),
            str(payload.get("target_frame_rect")),
            payload.get("rect_source"),
            str(payload.get("requested_rect")),
            payload.get("presentation_state"),
            str(payload.get("applied_rect")),
            payload.get("rect_match"),
            str(payload.get("rect_delta")),
            str(self.prime_rect),
            self.prime_rect_source,
            tuple(payload.get("presentation_reasons") or ()),
            tuple(payload.get("retry_reasons") or ()),
            payload.get("presentation_skipped"),
            payload.get("presentation_skip_reason"),
            payload.get("target_poll_skipped"),
            payload.get("surface_preparation"),
            str(payload.get("surface_preparation_rect")),
            payload.get("surface_preparation_failed"),
            payload.get("prepared_surface_requires_mapping"),
            payload.get("prepared_surface_allows_unfocused_content"),
            payload.get("legacy_geometry_policy"),
            str(payload.get("shell_raster_metrics")),
        )


def create_bundle_integration(bundle: BackendBundle, widget, logger: logging.Logger, context: "PlatformContext"):
    """Create a platform integration object from a bundle presentation backend."""

    return bundle.presentation.create_integration(widget, logger, context)


def create_bundle_tracker(
    bundle: BackendBundle,
    logger: logging.Logger,
    *,
    title_hint: str = "elite - dangerous",
    monitor_provider: Optional["MonitorProvider"] = None,
) -> Optional["WindowTracker"]:
    """Create a window tracker from a bundle discovery backend."""

    return bundle.discovery.create_tracker(logger, title_hint=title_hint, monitor_provider=monitor_provider)


_COMPAT_SELECTOR = BackendSelector(shadow_mode=False)


def derive_linux_backend_status(
    *,
    session_type: str = "",
    compositor: str = "",
    qt_platform_name: str = "",
    manual_override: str = "",
    flatpak: bool = False,
    flatpak_app_id: str = "",
    env: Optional[Mapping[str, str]] = None,
    source: ProbeSource = ProbeSource.RUNTIME_UPDATE,
) -> BackendSelectionStatus:
    """Derive a Linux backend status through the shared pure probe/selector path."""

    probe = collect_platform_probe(
        ProbeInputs(
            source=source,
            sys_platform="linux",
            qt_platform_name=qt_platform_name,
            session_type=session_type,
            compositor=compositor,
            is_flatpak=flatpak,
            flatpak_app_id=flatpak_app_id,
            env=dict(env or {}),
        )
    )
    return _COMPAT_SELECTOR.select(probe, manual_override=manual_override)


def ensure_linux_backend_status(
    status: Optional[BackendSelectionStatus],
    *,
    session_type: str = "",
    compositor: str = "",
    qt_platform_name: str = "",
    manual_override: str = "",
    flatpak: bool = False,
    flatpak_app_id: str = "",
    env: Optional[Mapping[str, str]] = None,
    source: ProbeSource = ProbeSource.RUNTIME_UPDATE,
) -> BackendSelectionStatus:
    """Return the provided Linux backend status, or derive one through the shared selector."""

    if status is not None:
        return status
    return derive_linux_backend_status(
        session_type=session_type,
        compositor=compositor,
        qt_platform_name=qt_platform_name,
        manual_override=manual_override,
        flatpak=flatpak,
        flatpak_app_id=flatpak_app_id,
        env=env,
        source=source,
    )


def resolve_legacy_linux_bundle(
    *,
    session_type: str = "",
    compositor: str = "",
    qt_platform_name: str = "",
    env: Optional[Mapping[str, str]] = None,
) -> BackendBundle:
    """Compatibility shim for older no-status callers; resolves through the shared selector."""

    status = derive_linux_backend_status(
        session_type=session_type,
        compositor=compositor,
        qt_platform_name=qt_platform_name,
        env=env,
    )
    return resolve_linux_bundle_from_status(status)


def resolve_linux_bundle_from_status(status: BackendSelectionStatus) -> BackendBundle:
    """Resolve the explicit Linux bundle chosen by the client-owned selector result."""

    return _build_linux_bundle_for_instance(status.selected_backend.instance)


def _build_linux_bundle_for_instance(instance: BackendInstance) -> BackendBundle:
    """Build the concrete Linux bundle for an explicit backend instance."""

    if instance is BackendInstance.NATIVE_X11:
        from overlay_client.backend.bundles.native_x11 import build_native_x11_bundle

        return build_native_x11_bundle()
    if instance is BackendInstance.XWAYLAND_COMPAT:
        from overlay_client.backend.bundles.xwayland_compat import build_xwayland_compat_bundle

        return build_xwayland_compat_bundle()
    if instance is BackendInstance.KWIN_WAYLAND:
        from overlay_client.backend.bundles.kwin_wayland import build_kwin_wayland_bundle

        return build_kwin_wayland_bundle()
    if instance is BackendInstance.GNOME_SHELL_WAYLAND:
        from overlay_client.backend.bundles.gnome_shell_wayland import build_gnome_shell_wayland_bundle

        return build_gnome_shell_wayland_bundle()
    if instance is BackendInstance.GNOME_SHELL_RASTER:
        from overlay_client.backend.bundles.gnome_shell_wayland import build_gnome_shell_raster_bundle

        return build_gnome_shell_raster_bundle()
    if instance is BackendInstance.SWAY_WAYFIRE_WLROOTS:
        from overlay_client.backend.bundles.sway_wayfire_wlroots import build_sway_wayfire_wlroots_bundle

        return build_sway_wayfire_wlroots_bundle()
    if instance is BackendInstance.HYPRLAND:
        from overlay_client.backend.bundles.hyprland import build_hyprland_bundle

        return build_hyprland_bundle()
    if instance in {
        BackendInstance.WAYLAND_LAYER_SHELL_GENERIC,
        BackendInstance.COSMIC,
        BackendInstance.GAMESCOPE,
    }:
        from overlay_client.backend.bundles.wayland_layer_shell_generic import build_wayland_layer_shell_generic_bundle

        return build_wayland_layer_shell_generic_bundle()
    raise ValueError(f"Backend instance {instance.value} does not map to a Linux bundle")


def resolve_tracker_fallback_bundle(status: BackendSelectionStatus) -> Optional[BackendBundle]:
    """Return the current shipped tracker fallback bundle for a selected Linux status."""

    bundle = resolve_linux_bundle_from_status(status)
    fallback_instance = bundle.capabilities.tracker_fallback_for(status.probe.session_type)
    if fallback_instance is None or fallback_instance is bundle.descriptor.instance:
        return None
    return _build_linux_bundle_for_instance(fallback_instance)


def is_wayland_bundle(bundle: BackendBundle) -> bool:
    """Return whether the bundle uses native Wayland window-management behavior."""

    return bundle.capabilities.uses_native_wayland_windowing


def uses_transient_parent(bundle: BackendBundle) -> bool:
    """Return whether the bundle requires the legacy X11 transient-parent workaround."""

    return bundle.capabilities.requires_transient_parent


def requires_focus_safe_overlay_flags(status: Optional[BackendSelectionStatus]) -> bool:
    """Return whether the selected backend needs non-focus-stealing overlay window flags."""

    return _gnome_shell_helper_presentation_available(status)


def platform_label_for_bundle(bundle: BackendBundle) -> str:
    """Return the current human-readable platform label for a bundle-backed runtime path."""

    return bundle.capabilities.platform_label


GnomePresentationCycleRunner = Callable[..., "GnomeHelperPresentationCycleResult"]
BackendPresentationSurfacePreparer = Callable[[BackendPresentationSurfacePreparation], bool]
BackendRasterFrameProvider = Callable[
    ["HelperTargetStatus | None", "HelperPresentationRequest | None", bool],
    "ShellRasterFrameBuildResult",
]


def run_backend_presentation_cycle(
    status: Optional[BackendSelectionStatus],
    *,
    standalone_mode: bool = False,
    keep_overlay_visible: bool = False,
    previous_surface_action: str = "",
    title_bar_compensation_enabled: bool = False,
    title_bar_compensation_height: int = 0,
    gnome_runner: GnomePresentationCycleRunner | None = None,
    prepare_surface: BackendPresentationSurfacePreparer | None = None,
    raster_frame_provider: BackendRasterFrameProvider | None = None,
) -> BackendPresentationCycleResult | None:
    """Run a backend-owned runtime presentation cycle when the selected backend exposes one."""

    if not _gnome_shell_helper_presentation_available(status):
        if _gnome_shell_raster_selected(status):
            return _gnome_shell_raster_unavailable_result(status)
        return None
    runner = gnome_runner or _gnome_shell_helper_presentation_runner()
    return _backend_result_from_gnome_helper_result(
        runner(
            standalone_mode=standalone_mode,
            keep_overlay_visible=keep_overlay_visible,
            previous_surface_action=previous_surface_action,
            title_bar_compensation_enabled=title_bar_compensation_enabled,
            title_bar_compensation_height=title_bar_compensation_height,
            prepare_surface=prepare_surface,
            shell_raster_frame_provider=raster_frame_provider,
            shell_raster_runtime_enabled=_gnome_shell_raster_selected(status),
            suppress_pyqt_fallback_on_shell_raster_failure=_gnome_shell_raster_selected(status),
        )
    )


def _gnome_shell_helper_presentation_available(status: Optional[BackendSelectionStatus]) -> bool:
    selected_backend = getattr(status, "selected_backend", None)
    if getattr(selected_backend, "instance", None) not in {
        BackendInstance.GNOME_SHELL_WAYLAND,
        BackendInstance.GNOME_SHELL_RASTER,
    }:
        return False
    for helper_state in getattr(status, "helper_states", ()):
        if getattr(helper_state, "helper", None) is HelperKind.GNOME_SHELL_EXTENSION and helper_state.available:
            return True
    return False


def _gnome_shell_raster_selected(status: Optional[BackendSelectionStatus]) -> bool:
    selected_backend = getattr(status, "selected_backend", None)
    return getattr(selected_backend, "instance", None) is BackendInstance.GNOME_SHELL_RASTER


def _gnome_shell_raster_unavailable_result(
    status: Optional[BackendSelectionStatus],
) -> BackendPresentationCycleResult:
    del status
    return BackendPresentationCycleResult(
        should_show_overlay=False,
        diagnostics={
            "helper_health": "unavailable",
            "target_state": "unknown",
            "presentation_state": "helper_unavailable",
            "presentation_reasons": ["gnome_shell_helper_unavailable"],
            "presentation_available": False,
            "presentation_attachable": False,
            "target_available": True,
        },
        visibility_snapshot=BackendPresentationVisibilitySnapshot(
            target_available=True,
            presentation_available=False,
            presentation_attachable=False,
        ),
        log_prefix="GNOME helper presentation",
    )


def _gnome_shell_helper_presentation_runner() -> GnomePresentationCycleRunner:
    from overlay_client.backend.bundles._gnome_shell_helper_presentation import run_gnome_shell_helper_presentation_cycle

    return run_gnome_shell_helper_presentation_cycle


def _backend_result_from_gnome_helper_result(
    result: "GnomeHelperPresentationCycleResult",
) -> BackendPresentationCycleResult:
    return BackendPresentationCycleResult(
        should_show_overlay=bool(result.should_show_overlay and result.presentation_status is not None),
        scale_size=_scale_size_from_gnome_helper_result(result),
        prime_rect=_prime_rect_from_gnome_helper_result(result),
        prime_rect_source=_prime_rect_source_from_gnome_helper_result(result),
        diagnostics=_diagnostics_from_gnome_helper_result(result),
        visibility_snapshot=_visibility_snapshot_from_gnome_helper_result(result),
        log_prefix="GNOME helper presentation",
    )


def _diagnostics_from_gnome_helper_result(
    result: "GnomeHelperPresentationCycleResult",
) -> dict[str, object]:
    payload = dict(result.to_log_payload())
    target = result.target_status.target if result.target_status is not None else None
    payload.update(
        {
            "prime_rect": _prime_rect_payload_from_gnome_helper_result(result),
            "prime_rect_source": _prime_rect_source_from_gnome_helper_result(result),
            "target_available": bool(result.target_found),
            "target_has_focus": bool(target.has_focus) if target is not None else False,
            "target_showing_on_workspace": bool(target.showing_on_workspace) if target is not None else False,
            "target_minimized": bool(target.minimized) if target is not None else False,
            "presentation_available": result.presentation_status is not None,
            "presentation_attachable": bool(result.should_show_overlay and result.presentation_status is not None),
            "overlay_window_found": bool(
                result.presentation_status is not None and result.presentation_status.overlay_token
            ),
            "presentation_rect_match": bool(
                result.presentation_status is not None and result.presentation_status.rect_match
            ),
            "prepared_surface_requires_mapping": _prepared_surface_requires_mapping_from_gnome_helper_result(result),
            "prepared_surface_allows_unfocused_content": (
                _prepared_surface_allows_unfocused_content_from_gnome_helper_result(result)
            ),
        }
    )
    return payload


def _visibility_snapshot_from_gnome_helper_result(
    result: "GnomeHelperPresentationCycleResult",
) -> BackendPresentationVisibilitySnapshot:
    target = result.target_status.target if result.target_status is not None else None
    return BackendPresentationVisibilitySnapshot(
        target_available=bool(result.target_found),
        target_has_focus=bool(target.has_focus) if target is not None else False,
        target_showing_on_workspace=bool(target.showing_on_workspace) if target is not None else False,
        target_minimized=bool(target.minimized) if target is not None else False,
        presentation_available=result.presentation_status is not None,
        presentation_attachable=bool(result.should_show_overlay and result.presentation_status is not None),
        overlay_window_found=bool(result.presentation_status is not None and result.presentation_status.overlay_token),
        presentation_rect_match=bool(result.presentation_status is not None and result.presentation_status.rect_match),
        prepared_surface_requires_mapping=_prepared_surface_requires_mapping_from_gnome_helper_result(result),
        prepared_surface_allows_unfocused_content=_prepared_surface_allows_unfocused_content_from_gnome_helper_result(
            result
        ),
    )


def _prepared_surface_requires_mapping_from_gnome_helper_result(
    result: "GnomeHelperPresentationCycleResult",
) -> bool:
    surface_preparation = getattr(result, "surface_preparation", None)
    return (
        surface_preparation is not None
        and getattr(surface_preparation, "mode", "") == BACKEND_PRESENTATION_SURFACE_PREPARATION_MANAGED_WINDOWED
        and not bool(getattr(result, "surface_preparation_failed", False))
    )


def _prepared_surface_allows_unfocused_content_from_gnome_helper_result(
    result: "GnomeHelperPresentationCycleResult",
) -> bool:
    return _prepared_surface_requires_mapping_from_gnome_helper_result(result)


def _scale_size_from_gnome_helper_result(
    result: "GnomeHelperPresentationCycleResult",
) -> tuple[int, int] | None:
    rect = None
    if result.presentation_status is not None and result.presentation_status.applied_rect is not None:
        rect = result.presentation_status.applied_rect
    elif result.request is not None:
        rect = result.request.content_rect
    if rect is None or not rect.valid:
        return None
    return (rect.width, rect.height)


def _prime_rect_from_gnome_helper_result(
    result: "GnomeHelperPresentationCycleResult",
) -> tuple[int, int, int, int] | None:
    rect = None
    if (
        result.presentation_status is not None
        and result.presentation_status.rect_match
        and result.presentation_status.applied_rect is not None
    ):
        rect = result.presentation_status.applied_rect
    elif result.request is not None:
        rect = result.request.content_rect
    elif result.presentation_status is not None:
        rect = result.presentation_status.requested_rect
    if rect is None or not rect.valid:
        return None
    return (rect.x, rect.y, rect.width, rect.height)


def _prime_rect_payload_from_gnome_helper_result(
    result: "GnomeHelperPresentationCycleResult",
) -> dict[str, int] | None:
    rect = _prime_rect_from_gnome_helper_result(result)
    if rect is None:
        return None
    x, y, width, height = rect
    return {"x": x, "y": y, "width": width, "height": height}


def _prime_rect_source_from_gnome_helper_result(
    result: "GnomeHelperPresentationCycleResult",
) -> str:
    if (
        result.presentation_status is not None
        and result.presentation_status.rect_match
        and result.presentation_status.applied_rect is not None
        and result.presentation_status.applied_rect.valid
    ):
        return "applied_rect"
    if result.request is not None and result.request.content_rect is not None and result.request.content_rect.valid:
        return "requested_rect"
    if (
        result.presentation_status is not None
        and result.presentation_status.requested_rect is not None
        and result.presentation_status.requested_rect.valid
    ):
        return "requested_rect"
    return "unavailable"
