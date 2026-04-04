from overlay_client.backend import (
    BackendInstance,
    backend_override_options_for_status,
    backend_override_requires_restart,
)


def test_backend_override_options_for_kwin_wayland_status_include_explicit_xwayland_fallback():
    options = backend_override_options_for_status(
        {
            "probe": {
                "operating_system": "linux",
                "session_type": "wayland",
                "compositor": "kwin",
            },
            "selected_backend": {
                "family": "native_wayland",
                "instance": "kwin_wayland",
            },
        }
    )

    assert tuple(option.value for option in options) == (
        BackendInstance.KWIN_WAYLAND.value,
        BackendInstance.XWAYLAND_COMPAT.value,
    )
    assert options[0].restart_required is False
    assert options[1].restart_required is True


def test_backend_override_options_for_x11_status_include_native_x11_only():
    options = backend_override_options_for_status(
        {
            "probe": {
                "operating_system": "linux",
                "session_type": "x11",
            },
            "selected_backend": {
                "family": "native_x11",
                "instance": "native_x11",
            },
        }
    )

    assert tuple(option.value for option in options) == (BackendInstance.NATIVE_X11.value,)


def test_backend_override_options_preserve_current_unknown_value_for_ui_roundtrip():
    options = backend_override_options_for_status(
        {
            "selected_backend": {
                "family": "native_wayland",
                "instance": "kwin_wayland",
            },
        },
        current_value="custom_backend",
    )

    assert tuple(option.value for option in options) == (
        BackendInstance.KWIN_WAYLAND.value,
        "custom_backend",
    )
    assert options[1].restart_required is False


def test_backend_override_requires_restart_only_for_xwayland_transition():
    assert backend_override_requires_restart("", "xwayland_compat") is True
    assert backend_override_requires_restart("xwayland_compat", "") is True
    assert backend_override_requires_restart("kwin_wayland", "wayland_layer_shell_generic") is False
    assert backend_override_requires_restart("kwin_wayland", "kwin_wayland") is False
