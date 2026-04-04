from overlay_client.backend import (
    BackendBundle,
    BackendCapabilities,
    BackendDescriptor,
    BackendFamily,
    BackendInstance,
    BackendSelectionStatus,
    CapabilityClassification,
    FallbackReason,
    HelperCapabilityState,
    HelperIpcBackend,
    HelperKind,
    InputPolicyBackend,
    OperatingSystem,
    PlatformProbe,
    PlatformProbeResult,
    PresentationBackend,
    SessionType,
    TargetDiscoveryBackend,
)


class _Probe:
    def collect(self) -> PlatformProbeResult:
        return PlatformProbeResult(
            operating_system=OperatingSystem.LINUX,
            session_type=SessionType.WAYLAND,
            qt_platform_name="wayland",
            compositor="kwin",
            available_protocols=frozenset({"layer-shell", "foreign-toplevel"}),
            available_helpers=frozenset({HelperKind.KWIN_SCRIPT}),
        )


class _Discovery:
    @property
    def backend_instance(self) -> BackendInstance:
        return BackendInstance.KWIN_WAYLAND

    def create_tracker(self, logger, *, title_hint="elite - dangerous", monitor_provider=None):
        del logger, title_hint, monitor_provider
        return None


class _Presentation:
    @property
    def backend_instance(self) -> BackendInstance:
        return BackendInstance.KWIN_WAYLAND

    def create_integration(self, widget, logger, context):
        return (widget, logger, context)


class _InputPolicy:
    @property
    def backend_instance(self) -> BackendInstance:
        return BackendInstance.KWIN_WAYLAND


class _HelperIpc:
    @property
    def backend_instance(self) -> BackendInstance:
        return BackendInstance.KWIN_WAYLAND

    @property
    def helper_kind(self) -> HelperKind:
        return HelperKind.KWIN_SCRIPT


def test_backend_family_values_include_locked_support_labels():
    assert BackendFamily.NATIVE_X11.value == "native_x11"
    assert BackendFamily.XWAYLAND_COMPAT.value == "xwayland_compat"
    assert BackendFamily.NATIVE_WAYLAND.value == "native_wayland"
    assert BackendFamily.COMPOSITOR_HELPER.value == "compositor_helper"
    assert BackendFamily.PORTAL_FALLBACK.value == "portal_fallback"


def test_platform_probe_and_component_protocols_are_runtime_checkable():
    probe = _Probe()
    discovery = _Discovery()
    presentation = _Presentation()
    input_policy = _InputPolicy()
    helper_ipc = _HelperIpc()

    assert isinstance(probe, PlatformProbe)
    assert isinstance(discovery, TargetDiscoveryBackend)
    assert isinstance(presentation, PresentationBackend)
    assert isinstance(input_policy, InputPolicyBackend)
    assert isinstance(helper_ipc, HelperIpcBackend)


def test_platform_probe_result_tracks_protocol_and_helper_availability():
    result = _Probe().collect()

    assert result.operating_system is OperatingSystem.LINUX
    assert result.session_type is SessionType.WAYLAND
    assert result.qt_platform_name == "wayland"
    assert result.compositor == "kwin"
    assert result.has_protocol("layer-shell") is True
    assert result.has_protocol("ext-foreign-toplevel-list-v1") is False
    assert result.has_helper(HelperKind.KWIN_SCRIPT) is True
    assert result.has_helper(HelperKind.GNOME_SHELL_EXTENSION) is False


def test_backend_bundle_and_selection_status_capture_stable_identity():
    descriptor = BackendDescriptor(
        family=BackendFamily.NATIVE_WAYLAND,
        instance=BackendInstance.KWIN_WAYLAND,
    )
    bundle = BackendBundle(
        descriptor=descriptor,
        capabilities=BackendCapabilities(
            platform_label="Wayland",
            uses_native_wayland_windowing=True,
            requires_transient_parent=False,
            tracker_available=True,
            tracker_fallback_by_session=((SessionType.WAYLAND, BackendInstance.XWAYLAND_COMPAT),),
        ),
        discovery=_Discovery(),
        presentation=_Presentation(),
        input_policy=_InputPolicy(),
        helper_ipc=_HelperIpc(),
    )
    status = BackendSelectionStatus(
        probe=_Probe().collect(),
        selected_backend=descriptor,
        classification=CapabilityClassification.DEGRADED_OVERLAY,
        fallback_from=BackendDescriptor(
            family=BackendFamily.COMPOSITOR_HELPER,
            instance=BackendInstance.GNOME_SHELL_WAYLAND,
        ),
        fallback_reason=FallbackReason.MISSING_HELPER,
        helper_states=(
            HelperCapabilityState(
                helper=HelperKind.KWIN_SCRIPT,
                installed=True,
                enabled=True,
                approved=True,
                version="1.2.3",
            ),
        ),
        notes=("shadow selector result",),
        shadow_mode=True,
    )

    assert descriptor.support_label == "native_wayland / kwin_wayland"
    assert bundle.uses_helper is True
    assert bundle.descriptor is descriptor
    assert status.uses_fallback is True
    assert status.is_true_overlay is False
    assert status.helper_states[0].available is True
    assert status.helper_states[0].version == "1.2.3"
    assert bundle.helper_ipc is not None
    assert bundle.helper_ipc.helper_kind is HelperKind.KWIN_SCRIPT
    assert bundle.capabilities.platform_label == "Wayland"
    assert bundle.capabilities.uses_native_wayland_windowing is True
    assert bundle.capabilities.tracker_fallback_for(SessionType.WAYLAND) is BackendInstance.XWAYLAND_COMPAT


def test_backend_selection_status_serializes_to_plain_payload():
    status = BackendSelectionStatus(
        probe=_Probe().collect(),
        selected_backend=BackendDescriptor(
            family=BackendFamily.NATIVE_WAYLAND,
            instance=BackendInstance.KWIN_WAYLAND,
        ),
        classification=CapabilityClassification.TRUE_OVERLAY,
        notes=("shadow_selector_result", "fedora_kde_wayland"),
        shadow_mode=True,
    )

    payload = status.to_payload()

    assert payload["classification"] == "true_overlay"
    assert payload["shadow_mode"] is True
    assert payload["selected_backend"] == {
        "family": "native_wayland",
        "instance": "kwin_wayland",
    }
    assert payload["probe"]["qt_platform_name"] == "wayland"
    assert payload["notes"] == ["shadow_selector_result", "fedora_kde_wayland"]


def test_backend_capabilities_expose_explicit_fallback_mapping_by_session():
    capabilities = BackendCapabilities(
        platform_label="Wayland",
        uses_native_wayland_windowing=True,
        requires_transient_parent=False,
        tracker_available=False,
        tracker_fallback_by_session=(
            (SessionType.WAYLAND, BackendInstance.XWAYLAND_COMPAT),
            (SessionType.X11, BackendInstance.NATIVE_X11),
        ),
    )

    assert capabilities.tracker_fallback_for(SessionType.WAYLAND) is BackendInstance.XWAYLAND_COMPAT
    assert capabilities.tracker_fallback_for(SessionType.X11) is BackendInstance.NATIVE_X11
    assert capabilities.tracker_fallback_for(SessionType.UNKNOWN) is None


def test_actual_linux_bundle_components_conform_to_tightened_protocols():
    from overlay_client.backend.bundles.hyprland import build_hyprland_bundle
    from overlay_client.backend.bundles.gnome_shell_wayland import build_gnome_shell_wayland_bundle
    from overlay_client.backend.bundles.kwin_wayland import build_kwin_wayland_bundle
    from overlay_client.backend.bundles.native_x11 import build_native_x11_bundle
    from overlay_client.backend.bundles.sway_wayfire_wlroots import build_sway_wayfire_wlroots_bundle
    from overlay_client.backend.bundles.wayland_layer_shell_generic import build_wayland_layer_shell_generic_bundle
    from overlay_client.backend.bundles.xwayland_compat import build_xwayland_compat_bundle

    for bundle in (
        build_native_x11_bundle(),
        build_xwayland_compat_bundle(),
        build_hyprland_bundle(),
        build_kwin_wayland_bundle(),
        build_gnome_shell_wayland_bundle(),
        build_sway_wayfire_wlroots_bundle(),
        build_wayland_layer_shell_generic_bundle(),
    ):
        assert isinstance(bundle.discovery, TargetDiscoveryBackend)
        assert isinstance(bundle.presentation, PresentationBackend)
        assert isinstance(bundle.input_policy, InputPolicyBackend)


def test_fix219_intentionally_keeps_combined_presentation_input_adapter_shape_for_linux_bundles():
    from overlay_client.backend.bundles.gnome_shell_wayland import build_gnome_shell_wayland_bundle
    from overlay_client.backend.bundles.hyprland import build_hyprland_bundle
    from overlay_client.backend.bundles.kwin_wayland import build_kwin_wayland_bundle
    from overlay_client.backend.bundles.native_x11 import build_native_x11_bundle
    from overlay_client.backend.bundles.sway_wayfire_wlroots import build_sway_wayfire_wlroots_bundle
    from overlay_client.backend.bundles.wayland_layer_shell_generic import build_wayland_layer_shell_generic_bundle
    from overlay_client.backend.bundles.xwayland_compat import build_xwayland_compat_bundle

    for bundle in (
        build_native_x11_bundle(),
        build_xwayland_compat_bundle(),
        build_hyprland_bundle(),
        build_kwin_wayland_bundle(),
        build_gnome_shell_wayland_bundle(),
        build_sway_wayfire_wlroots_bundle(),
        build_wayland_layer_shell_generic_bundle(),
    ):
        assert bundle.presentation is bundle.input_policy
