"""Generic bundle-consumer helpers introduced before runtime cutover."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Mapping, Optional

from overlay_client.backend.contracts import BackendBundle, BackendFamily, BackendInstance, SessionType
from overlay_client.backend.status import BackendSelectionStatus

if TYPE_CHECKING:
    from overlay_client.platform_integration import PlatformContext
    from overlay_client.window_tracking import MonitorProvider, WindowTracker


def create_bundle_integration(bundle: BackendBundle, widget, logger: logging.Logger, context: "PlatformContext"):
    """Create a platform integration object from a bundle presentation backend."""

    factory = getattr(bundle.presentation, "create_integration", None)
    if not callable(factory):
        raise TypeError(
            f"Presentation backend {type(bundle.presentation).__name__} does not expose create_integration()"
        )
    return factory(widget, logger, context)


def create_bundle_tracker(
    bundle: BackendBundle,
    logger: logging.Logger,
    *,
    title_hint: str = "elite - dangerous",
    monitor_provider: Optional["MonitorProvider"] = None,
) -> Optional["WindowTracker"]:
    """Create a window tracker from a bundle discovery backend."""

    factory = getattr(bundle.discovery, "create_tracker", None)
    if not callable(factory):
        raise TypeError(f"Discovery backend {type(bundle.discovery).__name__} does not expose create_tracker()")
    return factory(logger, title_hint=title_hint, monitor_provider=monitor_provider)


def resolve_legacy_linux_bundle(
    *,
    session_type: str = "",
    compositor: str = "",
    force_xwayland: bool = False,
    qt_platform_name: str = "",
    env: Optional[Mapping[str, str]] = None,
) -> BackendBundle:
    """Resolve the current shipped Linux runtime path to an explicit backend bundle."""

    from overlay_client.backend.bundles.gnome_shell_wayland import build_gnome_shell_wayland_bundle
    from overlay_client.backend.bundles.hyprland import build_hyprland_bundle
    from overlay_client.backend.bundles.kwin_wayland import build_kwin_wayland_bundle
    from overlay_client.backend.bundles.native_x11 import build_native_x11_bundle
    from overlay_client.backend.bundles.sway_wayfire_wlroots import build_sway_wayfire_wlroots_bundle
    from overlay_client.backend.bundles.wayland_layer_shell_generic import build_wayland_layer_shell_generic_bundle
    from overlay_client.backend.bundles.xwayland_compat import build_xwayland_compat_bundle

    env_map = dict(env or {})
    session = str(session_type or env_map.get("XDG_SESSION_TYPE") or "").strip().lower()
    platform_name = str(qt_platform_name or "").strip().lower()

    if session == "wayland" and (force_xwayland or platform_name.startswith("xcb")):
        return build_xwayland_compat_bundle()
    if session == "x11" or platform_name.startswith("xcb") or force_xwayland:
        return build_native_x11_bundle()

    compositor_name = _resolve_wayland_compositor(compositor, env_map)
    if compositor_name in {"sway", "wayfire", "wlroots"}:
        return build_sway_wayfire_wlroots_bundle()
    if compositor_name == "hyprland":
        return build_hyprland_bundle()
    if compositor_name == "kwin":
        return build_kwin_wayland_bundle()
    if compositor_name == "gnome-shell":
        return build_gnome_shell_wayland_bundle()
    return build_wayland_layer_shell_generic_bundle()


def resolve_linux_bundle_from_status(status: BackendSelectionStatus) -> BackendBundle:
    """Resolve the explicit Linux bundle chosen by the client-owned selector result."""

    instance = status.selected_backend.instance
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

    session_type = status.probe.session_type
    selected_instance = status.selected_backend.instance
    if session_type is SessionType.WAYLAND and selected_instance is not BackendInstance.XWAYLAND_COMPAT:
        from overlay_client.backend.bundles.xwayland_compat import build_xwayland_compat_bundle

        return build_xwayland_compat_bundle()
    if session_type is SessionType.X11 and selected_instance is not BackendInstance.NATIVE_X11:
        from overlay_client.backend.bundles.native_x11 import build_native_x11_bundle

        return build_native_x11_bundle()
    return None


def is_wayland_bundle(bundle: BackendBundle) -> bool:
    """Return whether the bundle uses native Wayland window-management behavior."""

    return bundle.descriptor.family is BackendFamily.NATIVE_WAYLAND


def uses_transient_parent(bundle: BackendBundle) -> bool:
    """Return whether the bundle requires the legacy X11 transient-parent workaround."""

    return bundle.descriptor.family in {BackendFamily.NATIVE_X11, BackendFamily.XWAYLAND_COMPAT}


def platform_label_for_bundle(bundle: BackendBundle) -> str:
    """Return the current human-readable platform label for a bundle-backed runtime path."""

    if bundle.descriptor.family is BackendFamily.XWAYLAND_COMPAT:
        return "Wayland (XWayland)"
    if bundle.descriptor.family is BackendFamily.NATIVE_X11:
        return "X11"
    return "Wayland"


def _resolve_wayland_compositor(compositor: str, env: Mapping[str, str]) -> str:
    token = str(compositor or "").strip().lower()
    if token in {"mutter", "gnome"}:
        return "gnome-shell"
    if token:
        return token
    if env.get("SWAYSOCK"):
        return "sway"
    if env.get("HYPRLAND_INSTANCE_SIGNATURE"):
        return "hyprland"
    desktop = (env.get("XDG_CURRENT_DESKTOP") or "").upper()
    if "KDE" in desktop or env.get("KDE_FULL_SESSION"):
        return "kwin"
    if "GNOME" in desktop or env.get("GNOME_SHELL_SESSION_MODE"):
        return "gnome-shell"
    return ""
