"""Explicit XWayland compatibility backend bundle built from current shipped XCB/X11 logic."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from overlay_client.backend.contracts import (
    BackendBundle,
    BackendCapabilities,
    BackendDescriptor,
    BackendFamily,
    BackendInstance,
    InputPolicyBackend,
    PresentationBackend,
    TargetDiscoveryBackend,
)
from overlay_client.backend.bundles._linux_window_integration import create_xcb_integration
from overlay_client.backend.bundles._linux_trackers import create_wmctrl_tracker
from overlay_client.platform_integration import PlatformContext
from overlay_client.window_tracking import MonitorProvider, WindowTracker


@dataclass(frozen=True, slots=True)
class XWaylandCompatDiscoveryBackend(TargetDiscoveryBackend):
    """Bundle-scoped discovery backend for X11-in-Wayland compatibility sessions."""

    @property
    def backend_instance(self) -> BackendInstance:
        return BackendInstance.XWAYLAND_COMPAT

    def create_tracker(
        self,
        logger: logging.Logger,
        *,
        title_hint: str = "elite - dangerous",
        monitor_provider: Optional[MonitorProvider] = None,
    ) -> WindowTracker:
        return create_wmctrl_tracker(logger, title_hint=title_hint, monitor_provider=monitor_provider)


@dataclass(frozen=True, slots=True)
class XWaylandCompatWindowBackend(PresentationBackend, InputPolicyBackend):
    """Bundle-scoped presentation/input backend for XWayland compatibility sessions."""

    @property
    def backend_instance(self) -> BackendInstance:
        return BackendInstance.XWAYLAND_COMPAT

    def create_integration(self, widget, logger: logging.Logger, context: PlatformContext):
        return create_xcb_integration(widget, logger, context)


def build_xwayland_compat_bundle() -> BackendBundle:
    """Build the explicit XWayland compatibility bundle from current shipped implementation pieces."""

    window_backend = XWaylandCompatWindowBackend()
    return BackendBundle(
        descriptor=BackendDescriptor(
            family=BackendFamily.XWAYLAND_COMPAT,
            instance=BackendInstance.XWAYLAND_COMPAT,
        ),
        capabilities=BackendCapabilities(
            platform_label="Wayland (XWayland)",
            uses_native_wayland_windowing=False,
            requires_transient_parent=True,
        ),
        discovery=XWaylandCompatDiscoveryBackend(),
        presentation=window_backend,
        input_policy=window_backend,
    )
