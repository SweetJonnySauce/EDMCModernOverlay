import logging

import pytest

from overlay_client.backend.consumers import is_wayland_bundle, platform_label_for_bundle, uses_transient_parent
from overlay_client.backend.bundles.gnome_shell_wayland import build_gnome_shell_wayland_bundle
from overlay_client.backend.bundles.hyprland import build_hyprland_bundle
from overlay_client.backend.bundles.kwin_wayland import build_kwin_wayland_bundle
from overlay_client.backend.bundles.sway_wayfire_wlroots import build_sway_wayfire_wlroots_bundle
from overlay_client.backend.bundles.wayland_layer_shell_generic import build_wayland_layer_shell_generic_bundle
from overlay_client.backend.contracts import BackendFamily, BackendInstance, SessionType
from overlay_client.platform_integration import PlatformContext


class _StubWidget:
    def windowHandle(self):
        return None


@pytest.mark.parametrize(
    ("build_bundle", "expected_instance"),
    [
        (build_sway_wayfire_wlroots_bundle, BackendInstance.SWAY_WAYFIRE_WLROOTS),
        (build_hyprland_bundle, BackendInstance.HYPRLAND),
        (build_kwin_wayland_bundle, BackendInstance.KWIN_WAYLAND),
        (build_gnome_shell_wayland_bundle, BackendInstance.GNOME_SHELL_WAYLAND),
        (build_wayland_layer_shell_generic_bundle, BackendInstance.WAYLAND_LAYER_SHELL_GENERIC),
    ],
)
def test_native_wayland_bundles_preserve_current_window_backend_policy_shape(build_bundle, expected_instance):
    bundle = build_bundle()

    assert bundle.descriptor.family is BackendFamily.NATIVE_WAYLAND
    assert bundle.descriptor.instance is expected_instance
    assert bundle.presentation.backend_instance is expected_instance
    assert bundle.input_policy.backend_instance is expected_instance
    assert bundle.presentation is bundle.input_policy
    assert bundle.uses_helper is False
    assert bundle.capabilities.platform_label == "Wayland"
    assert bundle.capabilities.uses_native_wayland_windowing is True
    assert bundle.capabilities.requires_transient_parent is False
    assert is_wayland_bundle(bundle) is True
    assert uses_transient_parent(bundle) is False
    assert platform_label_for_bundle(bundle) == "Wayland"


def test_sway_wayfire_wlroots_bundle_has_explicit_identity_and_shipped_tracker_shape():
    bundle = build_sway_wayfire_wlroots_bundle()
    logger = logging.getLogger("test.backend.bundles.sway")

    assert bundle.descriptor.family is BackendFamily.NATIVE_WAYLAND
    assert bundle.descriptor.instance is BackendInstance.SWAY_WAYFIRE_WLROOTS
    assert bundle.descriptor.support_label == "native_wayland / sway_wayfire_wlroots"
    assert bundle.discovery.backend_instance is BackendInstance.SWAY_WAYFIRE_WLROOTS
    assert bundle.presentation.backend_instance is BackendInstance.SWAY_WAYFIRE_WLROOTS
    assert bundle.input_policy.backend_instance is BackendInstance.SWAY_WAYFIRE_WLROOTS
    assert bundle.presentation is bundle.input_policy
    assert bundle.uses_helper is False
    assert bundle.capabilities.tracker_available is True
    assert bundle.capabilities.tracker_fallback_for(SessionType.WAYLAND) is BackendInstance.XWAYLAND_COMPAT
    assert bundle.capabilities.tracker_fallback_for(SessionType.X11) is BackendInstance.NATIVE_X11
    assert type(bundle.discovery.create_tracker(logger)).__name__ == "_SwayTracker"


def test_hyprland_bundle_has_explicit_identity_and_shipped_tracker_shape():
    bundle = build_hyprland_bundle()
    logger = logging.getLogger("test.backend.bundles.hyprland")

    assert bundle.descriptor.family is BackendFamily.NATIVE_WAYLAND
    assert bundle.descriptor.instance is BackendInstance.HYPRLAND
    assert bundle.descriptor.support_label == "native_wayland / hyprland"
    assert bundle.discovery.backend_instance is BackendInstance.HYPRLAND
    assert bundle.presentation.backend_instance is BackendInstance.HYPRLAND
    assert bundle.input_policy.backend_instance is BackendInstance.HYPRLAND
    assert bundle.presentation is bundle.input_policy
    assert bundle.uses_helper is False
    assert bundle.capabilities.tracker_available is True
    assert type(bundle.discovery.create_tracker(logger)).__name__ == "_HyprlandTracker"


def test_kwin_bundle_has_explicit_identity_and_shipped_tracker_shape():
    bundle = build_kwin_wayland_bundle()
    logger = logging.getLogger("test.backend.bundles.kwin")

    assert bundle.descriptor.family is BackendFamily.NATIVE_WAYLAND
    assert bundle.descriptor.instance is BackendInstance.KWIN_WAYLAND
    assert bundle.descriptor.support_label == "native_wayland / kwin_wayland"
    assert bundle.discovery.backend_instance is BackendInstance.KWIN_WAYLAND
    assert bundle.presentation.backend_instance is BackendInstance.KWIN_WAYLAND
    assert bundle.input_policy.backend_instance is BackendInstance.KWIN_WAYLAND
    assert bundle.presentation is bundle.input_policy
    assert bundle.uses_helper is False
    assert bundle.capabilities.tracker_available is True
    assert type(bundle.discovery.create_tracker(logger)).__name__ == "_KWinTracker"


def test_gnome_and_generic_wayland_bundles_preserve_current_no_tracker_behavior():
    gnome_bundle = build_gnome_shell_wayland_bundle()
    generic_bundle = build_wayland_layer_shell_generic_bundle()
    logger = logging.getLogger("test.backend.bundles.generic_wayland")

    assert gnome_bundle.descriptor.family is BackendFamily.NATIVE_WAYLAND
    assert gnome_bundle.descriptor.instance is BackendInstance.GNOME_SHELL_WAYLAND
    assert gnome_bundle.descriptor.support_label == "native_wayland / gnome_shell_wayland"
    assert gnome_bundle.capabilities.tracker_available is False
    assert gnome_bundle.discovery.create_tracker(logger) is None

    assert generic_bundle.descriptor.family is BackendFamily.NATIVE_WAYLAND
    assert generic_bundle.descriptor.instance is BackendInstance.WAYLAND_LAYER_SHELL_GENERIC
    assert generic_bundle.descriptor.support_label == "native_wayland / wayland_layer_shell_generic"
    assert generic_bundle.capabilities.tracker_available is False
    assert generic_bundle.discovery.create_tracker(logger) is None


def test_native_wayland_bundles_share_current_shipped_wayland_integration_shape():
    logger = logging.getLogger("test.backend.bundles.wayland")
    context = PlatformContext(session_type="wayland", compositor="kwin")
    widget = _StubWidget()

    sway_integration = build_sway_wayfire_wlroots_bundle().presentation.create_integration(widget, logger, context)
    hyprland_integration = build_hyprland_bundle().presentation.create_integration(widget, logger, context)
    kwin_integration = build_kwin_wayland_bundle().presentation.create_integration(widget, logger, context)
    gnome_integration = build_gnome_shell_wayland_bundle().presentation.create_integration(widget, logger, context)
    generic_integration = build_wayland_layer_shell_generic_bundle().presentation.create_integration(widget, logger, context)

    assert type(sway_integration).__name__ == "_WaylandIntegration"
    assert type(hyprland_integration).__name__ == "_WaylandIntegration"
    assert type(kwin_integration).__name__ == "_WaylandIntegration"
    assert type(gnome_integration).__name__ == "_WaylandIntegration"
    assert type(generic_integration).__name__ == "_WaylandIntegration"
