"""Explicit generic layer-shell Wayland bundle built from current shipped logic."""

from __future__ import annotations

from overlay_client.backend.bundles._wayland_common import build_native_wayland_bundle, create_unavailable_tracker
from overlay_client.backend.contracts import BackendBundle, BackendInstance


def build_wayland_layer_shell_generic_bundle() -> BackendBundle:
    """Build the explicit generic native Wayland bundle for capability-gated layer-shell paths."""

    return build_native_wayland_bundle(BackendInstance.WAYLAND_LAYER_SHELL_GENERIC, create_unavailable_tracker)
