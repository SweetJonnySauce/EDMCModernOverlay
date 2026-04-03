from overlay_client.backend import (
    BackendFamily,
    BackendInstance,
    BackendSelector,
    CapabilityClassification,
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
