"""Explicit GNOME Shell Wayland bundle built from current shipped logic."""

from __future__ import annotations

import logging

from overlay_client.backend.bundles._wayland_common import build_native_wayland_bundle, create_unavailable_tracker
from overlay_client.backend.contracts import BackendBundle, BackendFamily, BackendInstance
from overlay_client.backend.gnome_helper_runtime import GnomeShellHelperIpcBackend, create_gnome_shell_helper_tracker
from overlay_client.window_tracking import MonitorProvider, WindowTracker


def _create_gnome_helper_tracker(
    helper_backend: GnomeShellHelperIpcBackend,
    logger: logging.Logger,
    *,
    title_hint: str = "elite - dangerous",
    monitor_provider: MonitorProvider | None = None,
) -> WindowTracker:
    return create_gnome_shell_helper_tracker(
        logger,
        helper_backend=helper_backend,
        title_hint=title_hint,
        monitor_provider=monitor_provider,
    )


def build_gnome_shell_wayland_bundle(*, helper_enabled: bool = False) -> BackendBundle:
    """Build the explicit GNOME Shell Wayland bundle for the current helper-required path."""

    if not helper_enabled:
        return build_native_wayland_bundle(BackendInstance.GNOME_SHELL_WAYLAND, create_unavailable_tracker)

    helper_backend = GnomeShellHelperIpcBackend()
    return build_native_wayland_bundle(
        BackendInstance.GNOME_SHELL_WAYLAND,
        lambda logger, *, title_hint="elite - dangerous", monitor_provider=None: _create_gnome_helper_tracker(
            helper_backend,
            logger,
            title_hint=title_hint,
            monitor_provider=monitor_provider,
        ),
        family=BackendFamily.COMPOSITOR_HELPER,
        platform_label="GNOME Shell helper",
        helper_ipc=helper_backend,
    )
