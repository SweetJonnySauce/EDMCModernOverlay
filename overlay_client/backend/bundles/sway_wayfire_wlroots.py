"""Explicit wlroots-family Wayland bundle built from current shipped logic."""

from __future__ import annotations

from overlay_client.backend.bundles._wayland_common import build_native_wayland_bundle
from overlay_client.backend.contracts import BackendBundle, BackendInstance
from overlay_client.window_tracking import create_sway_tracker


def build_sway_wayfire_wlroots_bundle() -> BackendBundle:
    """Build the explicit wlroots-family Wayland bundle from the current shipped implementation."""

    return build_native_wayland_bundle(BackendInstance.SWAY_WAYFIRE_WLROOTS, create_sway_tracker)
