from overlay_client.backend import (
    BackendBundle,
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
            force_xwayland=False,
            available_protocols=frozenset({"layer-shell", "foreign-toplevel"}),
            available_helpers=frozenset({HelperKind.KWIN_SCRIPT}),
        )


class _Discovery:
    @property
    def backend_instance(self) -> BackendInstance:
        return BackendInstance.KWIN_WAYLAND


class _Presentation:
    @property
    def backend_instance(self) -> BackendInstance:
        return BackendInstance.KWIN_WAYLAND


class _InputPolicy:
    @property
    def backend_instance(self) -> BackendInstance:
        return BackendInstance.KWIN_WAYLAND


class _HelperIpc:
    @property
    def backend_instance(self) -> BackendInstance:
        return BackendInstance.KWIN_WAYLAND


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
