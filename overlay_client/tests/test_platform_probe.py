from overlay_client.backend import (
    HelperKind,
    HelperProbeAvailability,
    HelperProbeState,
    OperatingSystem,
    ProbeInputs,
    ProbeSource,
    SessionType,
    collect_platform_probe,
)


def test_collect_platform_probe_normalizes_explicit_hints():
    probe = collect_platform_probe(
        ProbeInputs(
            source=ProbeSource.INITIAL_HINTS,
            sys_platform="linux",
            qt_platform_name="wayland",
            session_type="Wayland",
            compositor="Mutter",
            is_flatpak=True,
            flatpak_app_id="app.id",
            available_protocols=frozenset({"layer-shell"}),
            available_helpers=frozenset({HelperKind.GNOME_SHELL_EXTENSION}),
        )
    )

    assert probe.operating_system is OperatingSystem.LINUX
    assert probe.session_type is SessionType.WAYLAND
    assert probe.qt_platform_name == "wayland"
    assert probe.compositor == "gnome-shell"
    assert probe.is_flatpak is True
    assert probe.flatpak_app_id == "app.id"
    assert probe.has_protocol("layer-shell") is True
    assert probe.has_helper(HelperKind.GNOME_SHELL_EXTENSION) is True


def test_collect_platform_probe_infers_compositor_from_env():
    probe = collect_platform_probe(
        ProbeInputs(
            source=ProbeSource.RUNTIME_UPDATE,
            sys_platform="linux",
            session_type="wayland",
            env={"SWAYSOCK": "/tmp/sway.sock"},
        )
    )

    assert probe.operating_system is OperatingSystem.LINUX
    assert probe.session_type is SessionType.WAYLAND
    assert probe.compositor == "sway"


def test_collect_platform_probe_infers_fedora_kde_wayland_desktop():
    kwin = collect_platform_probe(
        ProbeInputs(
            sys_platform="linux",
            session_type="wayland",
            env={"XDG_CURRENT_DESKTOP": "KDE"},
        )
    )

    assert kwin.compositor == "kwin"


def test_collect_platform_probe_infers_gnome_wayland_desktop():
    gnome = collect_platform_probe(
        ProbeInputs(
            sys_platform="linux",
            session_type="wayland",
            env={"XDG_CURRENT_DESKTOP": "ubuntu:GNOME"},
        )
    )

    assert gnome.compositor == "gnome-shell"


def test_collect_platform_probe_derives_available_helpers_from_probe_state():
    probe = collect_platform_probe(
        ProbeInputs(
            sys_platform="linux",
            session_type="wayland",
            compositor="gnome-shell",
            helper_probe_states=(
                HelperProbeState(
                    helper=HelperKind.GNOME_SHELL_EXTENSION,
                    availability=HelperProbeAvailability.AVAILABLE,
                    version="stage2.3",
                    detail="session_dbus_reachable",
                ),
            ),
        )
    )

    assert probe.has_helper(HelperKind.GNOME_SHELL_EXTENSION) is True
    assert probe.has_incompatible_helper(HelperKind.GNOME_SHELL_EXTENSION) is False
    assert probe.helper_state(HelperKind.GNOME_SHELL_EXTENSION) == HelperProbeState(
        helper=HelperKind.GNOME_SHELL_EXTENSION,
        availability=HelperProbeAvailability.AVAILABLE,
        version="stage2.3",
        detail="session_dbus_reachable",
    )


def test_collect_platform_probe_tracks_incompatible_helper_without_marking_it_available():
    probe = collect_platform_probe(
        ProbeInputs(
            sys_platform="linux",
            session_type="wayland",
            compositor="gnome-shell",
            helper_probe_states=(
                HelperProbeState(
                    helper=HelperKind.GNOME_SHELL_EXTENSION,
                    availability=HelperProbeAvailability.INCOMPATIBLE,
                    detail="protocol_version_mismatch:2",
                ),
            ),
        )
    )

    assert probe.has_helper(HelperKind.GNOME_SHELL_EXTENSION) is False
    assert probe.has_incompatible_helper(HelperKind.GNOME_SHELL_EXTENSION) is True
    assert probe.helper_state(HelperKind.GNOME_SHELL_EXTENSION) is not None
