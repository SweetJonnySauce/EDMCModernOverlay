"""Explicit KWin Wayland bundle built from current shipped logic."""

from __future__ import annotations

from overlay_client.backend.bundles._wayland_common import build_native_wayland_bundle
from overlay_client.backend.contracts import BackendBundle, BackendInstance
from overlay_client.window_tracking import create_kwin_tracker


def build_kwin_wayland_bundle() -> BackendBundle:
    """Build the explicit native KWin Wayland bundle from the current shipped implementation."""

    return build_native_wayland_bundle(BackendInstance.KWIN_WAYLAND, create_kwin_tracker)
