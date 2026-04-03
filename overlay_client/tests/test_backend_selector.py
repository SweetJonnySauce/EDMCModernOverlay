from overlay_client.backend import (
    BackendDescriptor,
    BackendFamily,
    BackendInstance,
    BackendSelector,
    CapabilityClassification,
    FallbackReason,
    HelperKind,
    OperatingSystem,
    PlatformProbeResult,
    SessionType,
)


def test_selector_prefers_windows_desktop_on_windows():
    selector = BackendSelector()
    status = selector.select(
        PlatformProbeResult(
            operating_system=OperatingSystem.WINDOWS,
            session_type=SessionType.WINDOWS,
        )
    )

    assert status.shadow_mode is True
    assert status.selected_backend.family is BackendFamily.NATIVE_WINDOWS
    assert status.selected_backend.instance is BackendInstance.WINDOWS_DESKTOP
    assert status.classification is CapabilityClassification.TRUE_OVERLAY
    assert status.notes == ("shadow_selector_result",)


def test_selector_uses_xwayland_compat_for_wayland_xcb_path():
    selector = BackendSelector()
    status = selector.select(
        PlatformProbeResult(
            operating_system=OperatingSystem.LINUX,
            session_type=SessionType.WAYLAND,
            qt_platform_name="xcb",
            compositor="kwin",
        )
    )

    assert status.selected_backend.family is BackendFamily.XWAYLAND_COMPAT
    assert status.selected_backend.instance is BackendInstance.XWAYLAND_COMPAT
    assert status.classification is CapabilityClassification.TRUE_OVERLAY
    assert status.fallback_from == BackendDescriptor(BackendFamily.NATIVE_WAYLAND, BackendInstance.KWIN_WAYLAND)
    assert status.fallback_reason is FallbackReason.XWAYLAND_COMPAT_ONLY
    assert status.review_required is True
    assert status.review_reasons == ("no_silent_downgrade:xwayland_compat",)
    assert "wayland_session_uses_xwayland_compat" in status.notes


def test_selector_uses_native_x11_for_gnome_x11_session():
    selector = BackendSelector()
    status = selector.select(
        PlatformProbeResult(
            operating_system=OperatingSystem.LINUX,
            session_type=SessionType.X11,
            qt_platform_name="xcb",
        )
    )

    assert status.selected_backend.family is BackendFamily.NATIVE_X11
    assert status.selected_backend.instance is BackendInstance.NATIVE_X11
    assert status.classification is CapabilityClassification.TRUE_OVERLAY


def test_selector_uses_generic_wayland_instance_for_unknown_wayland_fallback():
    selector = BackendSelector()
    status = selector.select(
        PlatformProbeResult(
            operating_system=OperatingSystem.LINUX,
            session_type=SessionType.WAYLAND,
            qt_platform_name="wayland",
            compositor="unknown",
        )
    )

    assert status.selected_backend.family is BackendFamily.NATIVE_WAYLAND
    assert status.selected_backend.instance is BackendInstance.WAYLAND_LAYER_SHELL_GENERIC
    assert "follow_mode_fallback:native_x11" in status.notes


def test_selector_uses_kwin_native_wayland_for_kwin_wayland():
    selector = BackendSelector()
    status = selector.select(
        PlatformProbeResult(
            operating_system=OperatingSystem.LINUX,
            session_type=SessionType.WAYLAND,
            qt_platform_name="wayland",
            compositor="kwin",
        )
    )

    assert status.selected_backend.family is BackendFamily.NATIVE_WAYLAND
    assert status.selected_backend.instance is BackendInstance.KWIN_WAYLAND
    assert status.classification is CapabilityClassification.TRUE_OVERLAY
    assert status.notes == ("shadow_selector_result",)


def test_selector_keeps_gnome_wayland_conservative_without_helper():
    selector = BackendSelector()
    status = selector.select(
        PlatformProbeResult(
            operating_system=OperatingSystem.LINUX,
            session_type=SessionType.WAYLAND,
            qt_platform_name="wayland",
            compositor="gnome-shell",
        )
    )

    assert status.selected_backend.family is BackendFamily.NATIVE_WAYLAND
    assert status.selected_backend.instance is BackendInstance.GNOME_SHELL_WAYLAND
    assert status.classification is CapabilityClassification.TRUE_OVERLAY
    assert status.fallback_from == BackendDescriptor(BackendFamily.COMPOSITOR_HELPER, BackendInstance.GNOME_SHELL_WAYLAND)
    assert status.fallback_reason is FallbackReason.MISSING_HELPER
    assert status.review_required is False
    assert len(status.helper_states) == 1
    assert status.helper_states[0].helper is HelperKind.GNOME_SHELL_EXTENSION
    assert status.helper_states[0].required is True
    assert status.helper_states[0].available is False
    assert "helper_recommended:gnome_shell_extension" in status.notes
    assert "follow_mode_fallback:native_x11" in status.notes


def test_selector_uses_compositor_helper_family_when_gnome_helper_exists():
    selector = BackendSelector()
    status = selector.select(
        PlatformProbeResult(
            operating_system=OperatingSystem.LINUX,
            session_type=SessionType.WAYLAND,
            qt_platform_name="wayland",
            compositor="gnome-shell",
            available_helpers=frozenset({HelperKind.GNOME_SHELL_EXTENSION}),
        )
    )

    assert status.selected_backend.family is BackendFamily.COMPOSITOR_HELPER
    assert status.selected_backend.instance is BackendInstance.GNOME_SHELL_WAYLAND
    assert status.classification is CapabilityClassification.TRUE_OVERLAY
    assert status.fallback_from is None
    assert status.fallback_reason is None
    assert len(status.helper_states) == 1
    assert status.helper_states[0].available is True
    assert "helper_recommended:gnome_shell_extension" not in status.notes


def test_selector_marks_backlog_wayland_targets_unsupported():
    selector = BackendSelector()
    status = selector.select(
        PlatformProbeResult(
            operating_system=OperatingSystem.LINUX,
            session_type=SessionType.WAYLAND,
            qt_platform_name="wayland",
            compositor="cosmic",
        )
    )

    assert status.selected_backend.family is BackendFamily.NATIVE_WAYLAND
    assert status.selected_backend.instance is BackendInstance.COSMIC
    assert status.classification is CapabilityClassification.UNSUPPORTED
    assert "backend_not_implemented" in status.notes


def test_selector_uses_compositor_helper_family_for_kwin_when_helper_exists():
    selector = BackendSelector()
    status = selector.select(
        PlatformProbeResult(
            operating_system=OperatingSystem.LINUX,
            session_type=SessionType.WAYLAND,
            qt_platform_name="wayland",
            compositor="kwin",
            available_helpers=frozenset({HelperKind.KWIN_SCRIPT}),
        )
    )

    assert status.selected_backend.family is BackendFamily.COMPOSITOR_HELPER
    assert status.selected_backend.instance is BackendInstance.KWIN_WAYLAND
    assert len(status.helper_states) == 1
    assert status.helper_states[0].helper is HelperKind.KWIN_SCRIPT
    assert status.helper_states[0].required is False
    assert status.helper_states[0].available is True


def test_selector_applies_manual_xwayland_override_on_wayland():
    selector = BackendSelector()
    status = selector.select(
        PlatformProbeResult(
            operating_system=OperatingSystem.LINUX,
            session_type=SessionType.WAYLAND,
            qt_platform_name="wayland",
            compositor="kwin",
        ),
        manual_override="xwayland_compat",
    )

    assert status.selected_backend.instance is BackendInstance.XWAYLAND_COMPAT
    assert status.manual_override is BackendInstance.XWAYLAND_COMPAT
    assert status.override_error == ""
    assert status.fallback_from == BackendDescriptor(BackendFamily.NATIVE_WAYLAND, BackendInstance.KWIN_WAYLAND)
    assert status.fallback_reason is FallbackReason.MANUAL_OVERRIDE
    assert "manual_override_active:xwayland_compat" in status.notes


def test_selector_keeps_auto_backend_when_manual_override_matches_selected_backend():
    selector = BackendSelector()
    status = selector.select(
        PlatformProbeResult(
            operating_system=OperatingSystem.LINUX,
            session_type=SessionType.WAYLAND,
            qt_platform_name="wayland",
            compositor="kwin",
        ),
        manual_override="kwin_wayland",
    )

    assert status.selected_backend.instance is BackendInstance.KWIN_WAYLAND
    assert status.manual_override is BackendInstance.KWIN_WAYLAND
    assert status.fallback_from is None
    assert status.fallback_reason is None


def test_selector_reports_invalid_manual_override_without_changing_auto_selection():
    selector = BackendSelector()
    status = selector.select(
        PlatformProbeResult(
            operating_system=OperatingSystem.LINUX,
            session_type=SessionType.WAYLAND,
            qt_platform_name="wayland",
            compositor="kwin",
        ),
        manual_override="bogus_backend",
    )

    assert status.selected_backend.instance is BackendInstance.KWIN_WAYLAND
    assert status.manual_override is None
    assert status.override_error == "bogus_backend"
    assert status.fallback_from is None
    assert status.fallback_reason is None
    assert "invalid_manual_override:bogus_backend" in status.notes


def test_selector_can_expose_stricter_xwayland_classification_when_conservative_mode_is_disabled():
    selector = BackendSelector(conservative_existing_classification=False)
    status = selector.select(
        PlatformProbeResult(
            operating_system=OperatingSystem.LINUX,
            session_type=SessionType.WAYLAND,
            qt_platform_name="xcb",
            compositor="kwin",
        )
    )

    assert status.selected_backend.instance is BackendInstance.XWAYLAND_COMPAT
    assert status.classification is CapabilityClassification.DEGRADED_OVERLAY
    assert status.fallback_reason is FallbackReason.XWAYLAND_COMPAT_ONLY
    assert status.review_required is False
