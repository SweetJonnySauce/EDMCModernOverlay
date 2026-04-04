"""Explicit native X11 backend bundle built from current shipped XCB/X11 logic."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from overlay_client.backend.contracts import (
    BackendBundle,
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
class NativeX11DiscoveryBackend(TargetDiscoveryBackend):
    """Bundle-scoped discovery backend for true X11 sessions."""

    @property
    def backend_instance(self) -> BackendInstance:
        return BackendInstance.NATIVE_X11

    def create_tracker(
        self,
        logger: logging.Logger,
        *,
        title_hint: str = "elite - dangerous",
        monitor_provider: Optional[MonitorProvider] = None,
    ) -> WindowTracker:
        return create_wmctrl_tracker(logger, title_hint=title_hint, monitor_provider=monitor_provider)


@dataclass(frozen=True, slots=True)
class NativeX11WindowBackend(PresentationBackend, InputPolicyBackend):
    """Bundle-scoped presentation/input backend for true X11 sessions."""

    @property
    def backend_instance(self) -> BackendInstance:
        return BackendInstance.NATIVE_X11

    def create_integration(self, widget, logger: logging.Logger, context: PlatformContext):
        return create_xcb_integration(widget, logger, context)


def build_native_x11_bundle() -> BackendBundle:
    """Build the explicit native X11 bundle from current shipped implementation pieces."""

    window_backend = NativeX11WindowBackend()
    return BackendBundle(
        descriptor=BackendDescriptor(
            family=BackendFamily.NATIVE_X11,
            instance=BackendInstance.NATIVE_X11,
        ),
        discovery=NativeX11DiscoveryBackend(),
        presentation=window_backend,
        input_policy=window_backend,
    )
