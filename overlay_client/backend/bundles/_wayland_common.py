"""Shared helpers for explicit native Wayland backend bundles."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Optional

from overlay_client.backend.contracts import (
    BackendBundle,
    BackendDescriptor,
    BackendFamily,
    BackendInstance,
    InputPolicyBackend,
    PresentationBackend,
    TargetDiscoveryBackend,
)
from overlay_client.platform_integration import PlatformContext, create_wayland_integration
from overlay_client.window_tracking import MonitorProvider, WindowTracker

WaylandTrackerFactory = Callable[..., Optional[WindowTracker]]


@dataclass(frozen=True, slots=True)
class NativeWaylandDiscoveryBackend(TargetDiscoveryBackend):
    """Bundle-scoped discovery backend for native Wayland bundle identities."""

    instance: BackendInstance
    tracker_factory: WaylandTrackerFactory

    @property
    def backend_instance(self) -> BackendInstance:
        return self.instance

    def create_tracker(
        self,
        logger: logging.Logger,
        *,
        title_hint: str = "elite - dangerous",
        monitor_provider: Optional[MonitorProvider] = None,
    ) -> Optional[WindowTracker]:
        return self.tracker_factory(logger, title_hint=title_hint, monitor_provider=monitor_provider)


@dataclass(frozen=True, slots=True)
class NativeWaylandWindowBackend(PresentationBackend, InputPolicyBackend):
    """Bundle-scoped presentation/input backend for native Wayland bundles."""

    instance: BackendInstance

    @property
    def backend_instance(self) -> BackendInstance:
        return self.instance

    def create_integration(self, widget, logger: logging.Logger, context: PlatformContext):
        return create_wayland_integration(widget, logger, context)


def create_unavailable_tracker(
    logger: logging.Logger,
    *,
    title_hint: str = "elite - dangerous",
    monitor_provider: Optional[MonitorProvider] = None,
) -> None:
    """Represent current shipped Wayland bundle paths that intentionally expose no tracker yet."""

    del logger, title_hint, monitor_provider
    return None


def build_native_wayland_bundle(
    instance: BackendInstance,
    tracker_factory: WaylandTrackerFactory,
) -> BackendBundle:
    """Build a native Wayland bundle with an explicit backend identity."""

    window_backend = NativeWaylandWindowBackend(instance=instance)
    return BackendBundle(
        descriptor=BackendDescriptor(
            family=BackendFamily.NATIVE_WAYLAND,
            instance=instance,
        ),
        discovery=NativeWaylandDiscoveryBackend(instance=instance, tracker_factory=tracker_factory),
        presentation=window_backend,
        input_policy=window_backend,
    )
