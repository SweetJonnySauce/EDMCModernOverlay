"""Pure backend selector logic that mirrors current shipped behavior in shadow mode."""

from __future__ import annotations

from typing import Optional

from dataclasses import dataclass, field

from .contracts import (
    BackendDescriptor,
    BackendFamily,
    BackendInstance,
    CapabilityClassification,
    FallbackReason,
    HelperKind,
    OperatingSystem,
    PlatformProbeResult,
    SessionType,
)
from .status import BackendSelectionStatus, HelperCapabilityState


@dataclass(frozen=True, slots=True)
class BackendSelector:
    """Select a shadow backend result without driving runtime consumers yet."""

    shadow_mode: bool = True
    conservative_existing_classification: bool = True
    stable_notes: tuple[str, ...] = field(default_factory=lambda: ("shadow_selector_result",))

    def select(self, probe: PlatformProbeResult, *, manual_override: str = "") -> BackendSelectionStatus:
        auto_descriptor = self._select_descriptor(probe)
        override_instance, override_error = self._resolve_manual_override(manual_override, probe, auto_descriptor)
        descriptor = self._descriptor_for_override(override_instance, probe, auto_descriptor)
        strict_classification = self._strict_classification(descriptor, probe)
        classification = self._classify(descriptor, probe, strict_classification)
        if override_instance is not None and descriptor != auto_descriptor:
            fallback_from, fallback_reason = auto_descriptor, FallbackReason.MANUAL_OVERRIDE
        elif override_instance is not None:
            fallback_from, fallback_reason = None, None
        else:
            fallback_from, fallback_reason = self._fallback_context(descriptor, probe)
        review_required, review_reasons = self._review_guard(
            descriptor,
            probe,
            classification=classification,
            strict_classification=strict_classification,
        )
        notes = self._selection_notes(descriptor, probe, override_instance=override_instance, override_error=override_error)
        return BackendSelectionStatus(
            probe=probe,
            selected_backend=descriptor,
            classification=classification,
            fallback_from=fallback_from,
            fallback_reason=fallback_reason,
            manual_override=override_instance,
            override_error=override_error,
            helper_states=self._helper_states(descriptor, probe),
            review_required=review_required,
            review_reasons=review_reasons,
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
            family = (
                BackendFamily.COMPOSITOR_HELPER
                if probe.has_helper(HelperKind.KWIN_SCRIPT) or probe.has_helper(HelperKind.KWIN_EFFECT)
                else BackendFamily.NATIVE_WAYLAND
            )
            return BackendDescriptor(family, BackendInstance.KWIN_WAYLAND)
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

    def _valid_override_instances(
        self,
        probe: PlatformProbeResult,
        auto_descriptor: BackendDescriptor,
    ) -> frozenset[BackendInstance]:
        if probe.operating_system is OperatingSystem.WINDOWS:
            return frozenset({BackendInstance.WINDOWS_DESKTOP})
        if probe.operating_system is not OperatingSystem.LINUX:
            return frozenset()
        if probe.session_type is SessionType.WAYLAND:
            return frozenset({auto_descriptor.instance, BackendInstance.XWAYLAND_COMPAT})
        if probe.session_type is SessionType.X11 or probe.qt_platform_name.startswith("xcb"):
            return frozenset({BackendInstance.NATIVE_X11})
        return frozenset({auto_descriptor.instance})

    def _resolve_manual_override(
        self,
        raw_override: str,
        probe: PlatformProbeResult,
        auto_descriptor: BackendDescriptor,
    ) -> tuple[BackendInstance | None, str]:
        token = str(raw_override or "").strip().lower()
        if not token or token == "auto":
            return None, ""
        try:
            instance = BackendInstance(token)
        except ValueError:
            return None, token
        if instance not in self._valid_override_instances(probe, auto_descriptor):
            return None, token
        return instance, ""

    def _descriptor_for_override(
        self,
        override_instance: BackendInstance | None,
        probe: PlatformProbeResult,
        auto_descriptor: BackendDescriptor,
    ) -> BackendDescriptor:
        if override_instance is None:
            return auto_descriptor
        if override_instance is auto_descriptor.instance:
            return auto_descriptor
        if override_instance is BackendInstance.WINDOWS_DESKTOP:
            return BackendDescriptor(BackendFamily.NATIVE_WINDOWS, BackendInstance.WINDOWS_DESKTOP)
        if override_instance is BackendInstance.NATIVE_X11:
            return BackendDescriptor(BackendFamily.NATIVE_X11, BackendInstance.NATIVE_X11)
        if override_instance is BackendInstance.XWAYLAND_COMPAT:
            return BackendDescriptor(BackendFamily.XWAYLAND_COMPAT, BackendInstance.XWAYLAND_COMPAT)
        if override_instance is BackendInstance.GNOME_SHELL_WAYLAND:
            family = (
                BackendFamily.COMPOSITOR_HELPER
                if probe.has_helper(HelperKind.GNOME_SHELL_EXTENSION)
                else BackendFamily.NATIVE_WAYLAND
            )
            return BackendDescriptor(family, BackendInstance.GNOME_SHELL_WAYLAND)
        return BackendDescriptor(BackendFamily.NATIVE_WAYLAND, override_instance)

    def _strict_classification(
        self,
        descriptor: BackendDescriptor,
        probe: PlatformProbeResult,
    ) -> CapabilityClassification:
        if descriptor.instance in {BackendInstance.COSMIC, BackendInstance.GAMESCOPE}:
            return CapabilityClassification.UNSUPPORTED
        if descriptor.instance is BackendInstance.XWAYLAND_COMPAT and probe.session_type is SessionType.WAYLAND:
            return CapabilityClassification.DEGRADED_OVERLAY
        return CapabilityClassification.TRUE_OVERLAY

    def _classify(
        self,
        descriptor: BackendDescriptor,
        probe: PlatformProbeResult,
        strict_classification: CapabilityClassification,
    ) -> CapabilityClassification:
        if (
            self.conservative_existing_classification
            and descriptor.instance is BackendInstance.XWAYLAND_COMPAT
            and probe.session_type is SessionType.WAYLAND
        ):
            return CapabilityClassification.TRUE_OVERLAY
        return strict_classification

    def _fallback_context(
        self,
        descriptor: BackendDescriptor,
        probe: PlatformProbeResult,
    ) -> tuple[Optional[BackendDescriptor], Optional[FallbackReason]]:
        if descriptor.instance is BackendInstance.XWAYLAND_COMPAT and probe.session_type is SessionType.WAYLAND:
            return self._select_wayland_descriptor(probe), FallbackReason.XWAYLAND_COMPAT_ONLY
        if descriptor.instance is BackendInstance.GNOME_SHELL_WAYLAND and not probe.has_helper(
            HelperKind.GNOME_SHELL_EXTENSION
        ):
            return (
                BackendDescriptor(BackendFamily.COMPOSITOR_HELPER, BackendInstance.GNOME_SHELL_WAYLAND),
                FallbackReason.MISSING_HELPER,
            )
        return None, None

    def _review_guard(
        self,
        descriptor: BackendDescriptor,
        probe: PlatformProbeResult,
        *,
        classification: CapabilityClassification,
        strict_classification: CapabilityClassification,
    ) -> tuple[bool, tuple[str, ...]]:
        if classification is strict_classification:
            return False, ()
        if descriptor.instance is BackendInstance.XWAYLAND_COMPAT and probe.session_type is SessionType.WAYLAND:
            return True, ("no_silent_downgrade:xwayland_compat",)
        return True, ("no_silent_downgrade:review_required",)

    def _selection_notes(
        self,
        descriptor: BackendDescriptor,
        probe: PlatformProbeResult,
        *,
        override_instance: BackendInstance | None = None,
        override_error: str = "",
    ) -> tuple[str, ...]:
        notes: list[str] = []
        if override_instance is not None:
            notes.append(f"manual_override_active:{override_instance.value}")
        if override_error:
            notes.append(f"invalid_manual_override:{override_error}")
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

    def _helper_states(
        self,
        descriptor: BackendDescriptor,
        probe: PlatformProbeResult,
    ) -> tuple[HelperCapabilityState, ...]:
        if descriptor.instance is BackendInstance.GNOME_SHELL_WAYLAND:
            helper_available = probe.has_helper(HelperKind.GNOME_SHELL_EXTENSION)
            return (
                HelperCapabilityState(
                    helper=HelperKind.GNOME_SHELL_EXTENSION,
                    required=True,
                    installed=helper_available,
                    enabled=helper_available,
                    approved=helper_available,
                    detail="required_for_true_overlay",
                ),
            )
        if descriptor.instance is BackendInstance.KWIN_WAYLAND:
            states: list[HelperCapabilityState] = []
            for helper_kind in (HelperKind.KWIN_SCRIPT, HelperKind.KWIN_EFFECT):
                helper_available = probe.has_helper(helper_kind)
                if helper_available:
                    states.append(
                        HelperCapabilityState(
                            helper=helper_kind,
                            required=False,
                            installed=True,
                            enabled=True,
                            approved=True,
                            detail="optional_helper_path",
                        )
                    )
            return tuple(states)
        return ()
