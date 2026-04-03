"""Pure backend selector logic that mirrors current shipped behavior in shadow mode."""

from __future__ import annotations

from dataclasses import dataclass, field

from .contracts import (
    BackendDescriptor,
    BackendFamily,
    BackendInstance,
    CapabilityClassification,
    HelperKind,
    OperatingSystem,
    PlatformProbeResult,
    SessionType,
)
from .status import BackendSelectionStatus


@dataclass(frozen=True, slots=True)
class BackendSelector:
    """Select a shadow backend result without driving runtime consumers yet."""

    shadow_mode: bool = True
    conservative_existing_classification: bool = True
    stable_notes: tuple[str, ...] = field(default_factory=lambda: ("shadow_selector_result",))

    def select(self, probe: PlatformProbeResult) -> BackendSelectionStatus:
        descriptor = self._select_descriptor(probe)
        classification = self._classify(descriptor, probe)
        notes = self._selection_notes(descriptor, probe)
        return BackendSelectionStatus(
            probe=probe,
            selected_backend=descriptor,
            classification=classification,
            notes=self.stable_notes + notes,
            shadow_mode=self.shadow_mode,
        )

    def _select_descriptor(self, probe: PlatformProbeResult) -> BackendDescriptor:
        if probe.operating_system is OperatingSystem.WINDOWS:
            return BackendDescriptor(BackendFamily.NATIVE_WINDOWS, BackendInstance.WINDOWS_DESKTOP)

        if probe.operating_system is OperatingSystem.LINUX:
            if probe.session_type is SessionType.WAYLAND and (
                probe.force_xwayland or probe.qt_platform_name.startswith("xcb")
            ):
                return BackendDescriptor(BackendFamily.XWAYLAND_COMPAT, BackendInstance.XWAYLAND_COMPAT)
            if probe.session_type is SessionType.X11 or probe.qt_platform_name.startswith("xcb"):
                return BackendDescriptor(BackendFamily.NATIVE_X11, BackendInstance.NATIVE_X11)
            if probe.session_type is SessionType.WAYLAND:
                return self._select_wayland_descriptor(probe)

        return BackendDescriptor(BackendFamily.NATIVE_WINDOWS, BackendInstance.UNKNOWN)

    def _select_wayland_descriptor(self, probe: PlatformProbeResult) -> BackendDescriptor:
        compositor = probe.compositor
        if compositor in {"sway", "wayfire", "wlroots"}:
            return BackendDescriptor(BackendFamily.NATIVE_WAYLAND, BackendInstance.SWAY_WAYFIRE_WLROOTS)
        if compositor == "hyprland":
            return BackendDescriptor(BackendFamily.NATIVE_WAYLAND, BackendInstance.HYPRLAND)
        if compositor == "kwin":
            return BackendDescriptor(BackendFamily.NATIVE_WAYLAND, BackendInstance.KWIN_WAYLAND)
        if compositor == "gnome-shell":
            family = (
                BackendFamily.COMPOSITOR_HELPER
                if probe.has_helper(HelperKind.GNOME_SHELL_EXTENSION)
                else BackendFamily.NATIVE_WAYLAND
            )
            return BackendDescriptor(family, BackendInstance.GNOME_SHELL_WAYLAND)
        if compositor == "cosmic":
            return BackendDescriptor(BackendFamily.NATIVE_WAYLAND, BackendInstance.COSMIC)
        if compositor == "gamescope":
            return BackendDescriptor(BackendFamily.NATIVE_WAYLAND, BackendInstance.GAMESCOPE)
        return BackendDescriptor(BackendFamily.NATIVE_WAYLAND, BackendInstance.WAYLAND_LAYER_SHELL_GENERIC)

    def _classify(self, descriptor: BackendDescriptor, probe: PlatformProbeResult) -> CapabilityClassification:
        if descriptor.instance in {BackendInstance.COSMIC, BackendInstance.GAMESCOPE}:
            return CapabilityClassification.UNSUPPORTED
        if (
            not self.conservative_existing_classification
            and descriptor.instance is BackendInstance.XWAYLAND_COMPAT
            and probe.session_type is SessionType.WAYLAND
        ):
            return CapabilityClassification.DEGRADED_OVERLAY
        return CapabilityClassification.TRUE_OVERLAY

    def _selection_notes(self, descriptor: BackendDescriptor, probe: PlatformProbeResult) -> tuple[str, ...]:
        notes: list[str] = []
        if descriptor.instance is BackendInstance.XWAYLAND_COMPAT and probe.session_type is SessionType.WAYLAND:
            notes.append("wayland_session_uses_xwayland_compat")
        if descriptor.instance is BackendInstance.GNOME_SHELL_WAYLAND and not probe.has_helper(
            HelperKind.GNOME_SHELL_EXTENSION
        ):
            notes.append("helper_recommended:gnome_shell_extension")
            notes.append("follow_mode_fallback:native_x11")
        elif descriptor.instance in {
            BackendInstance.COSMIC,
            BackendInstance.GAMESCOPE,
        }:
            notes.append("follow_mode_fallback:native_x11")
            notes.append("backend_not_implemented")
        elif (
            probe.session_type is SessionType.WAYLAND
            and descriptor.instance is BackendInstance.WAYLAND_LAYER_SHELL_GENERIC
            and probe.compositor not in {"sway", "wayfire", "wlroots", "hyprland", "kwin", "gnome-shell"}
        ):
            notes.append("follow_mode_fallback:native_x11")
        return tuple(notes)
