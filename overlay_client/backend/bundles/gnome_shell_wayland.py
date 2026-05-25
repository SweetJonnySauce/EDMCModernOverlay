"""Explicit GNOME Shell Wayland bundle built from current shipped logic."""

from __future__ import annotations

from dataclasses import replace

from overlay_client.backend.bundles._wayland_common import build_native_wayland_bundle, create_unavailable_tracker
from overlay_client.backend.contracts import BackendBundle, BackendDescriptor, BackendFamily, BackendInstance


def build_gnome_shell_wayland_bundle() -> BackendBundle:
    """Build the explicit GNOME Shell Wayland bundle for the current helper-required path."""

    return build_native_wayland_bundle(BackendInstance.GNOME_SHELL_WAYLAND, create_unavailable_tracker)


def build_gnome_shell_raster_bundle() -> BackendBundle:
    """Build the explicit GNOME Shell raster bundle for the support-gated helper path."""

    bundle = build_native_wayland_bundle(BackendInstance.GNOME_SHELL_RASTER, create_unavailable_tracker)
    return replace(
        bundle,
        descriptor=BackendDescriptor(BackendFamily.COMPOSITOR_HELPER, BackendInstance.GNOME_SHELL_RASTER),
        capabilities=replace(bundle.capabilities, platform_label="GNOME Shell Raster"),
    )
