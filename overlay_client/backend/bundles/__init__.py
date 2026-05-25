"""Explicit backend bundle builders used during staged backend extraction."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_BUNDLE_BUILDERS = {
    "build_gnome_shell_raster_bundle": ("gnome_shell_wayland", "build_gnome_shell_raster_bundle"),
    "build_gnome_shell_wayland_bundle": ("gnome_shell_wayland", "build_gnome_shell_wayland_bundle"),
    "build_hyprland_bundle": ("hyprland", "build_hyprland_bundle"),
    "build_kwin_wayland_bundle": ("kwin_wayland", "build_kwin_wayland_bundle"),
    "build_native_x11_bundle": ("native_x11", "build_native_x11_bundle"),
    "build_sway_wayfire_wlroots_bundle": (
        "sway_wayfire_wlroots",
        "build_sway_wayfire_wlroots_bundle",
    ),
    "build_wayland_layer_shell_generic_bundle": (
        "wayland_layer_shell_generic",
        "build_wayland_layer_shell_generic_bundle",
    ),
    "build_xwayland_compat_bundle": ("xwayland_compat", "build_xwayland_compat_bundle"),
}

__all__ = [
    "build_gnome_shell_raster_bundle",
    "build_gnome_shell_wayland_bundle",
    "build_hyprland_bundle",
    "build_kwin_wayland_bundle",
    "build_native_x11_bundle",
    "build_sway_wayfire_wlroots_bundle",
    "build_wayland_layer_shell_generic_bundle",
    "build_xwayland_compat_bundle",
]


def __getattr__(name: str) -> Any:
    """Load backend bundle builders lazily so utility submodules stay Qt-free."""

    try:
        module_name, attr_name = _BUNDLE_BUILDERS[name]
    except KeyError as exc:
        raise AttributeError(name) from exc
    value = getattr(import_module(f"{__name__}.{module_name}"), attr_name)
    globals()[name] = value
    return value
