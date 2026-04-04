"""Explicit Hyprland Wayland bundle built from current shipped logic."""

from __future__ import annotations

from overlay_client.backend.bundles._linux_trackers import create_hyprland_tracker
from overlay_client.backend.bundles._wayland_common import build_native_wayland_bundle
from overlay_client.backend.contracts import BackendBundle, BackendInstance


def build_hyprland_bundle() -> BackendBundle:
    """Build the explicit Hyprland bundle from the current shipped implementation."""

    return build_native_wayland_bundle(BackendInstance.HYPRLAND, create_hyprland_tracker)
