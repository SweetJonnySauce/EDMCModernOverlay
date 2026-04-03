import logging

from overlay_client.backend.bundles.native_x11 import build_native_x11_bundle
from overlay_client.backend.bundles.xwayland_compat import build_xwayland_compat_bundle
from overlay_client.backend.contracts import BackendFamily, BackendInstance
from overlay_client.platform_integration import PlatformContext


class _StubWidget:
    def windowHandle(self):
        return None


def test_native_x11_bundle_has_explicit_identity_and_shared_window_backend():
    bundle = build_native_x11_bundle()

    assert bundle.descriptor.family is BackendFamily.NATIVE_X11
    assert bundle.descriptor.instance is BackendInstance.NATIVE_X11
    assert bundle.descriptor.support_label == "native_x11 / native_x11"
    assert bundle.discovery.backend_instance is BackendInstance.NATIVE_X11
    assert bundle.presentation.backend_instance is BackendInstance.NATIVE_X11
    assert bundle.input_policy.backend_instance is BackendInstance.NATIVE_X11
    assert bundle.presentation is bundle.input_policy
    assert bundle.uses_helper is False


def test_xwayland_bundle_has_explicit_identity_and_shared_window_backend():
    bundle = build_xwayland_compat_bundle()

    assert bundle.descriptor.family is BackendFamily.XWAYLAND_COMPAT
    assert bundle.descriptor.instance is BackendInstance.XWAYLAND_COMPAT
    assert bundle.descriptor.support_label == "xwayland_compat / xwayland_compat"
    assert bundle.discovery.backend_instance is BackendInstance.XWAYLAND_COMPAT
    assert bundle.presentation.backend_instance is BackendInstance.XWAYLAND_COMPAT
    assert bundle.input_policy.backend_instance is BackendInstance.XWAYLAND_COMPAT
    assert bundle.presentation is bundle.input_policy
    assert bundle.uses_helper is False


def test_x11_and_xwayland_bundles_share_current_shipped_xcb_integration_shape():
    logger = logging.getLogger("test.backend.bundles.x11")
    context = PlatformContext(session_type="x11", compositor="none", force_xwayland=False)
    widget = _StubWidget()

    native_integration = build_native_x11_bundle().presentation.create_integration(widget, logger, context)
    xwayland_integration = build_xwayland_compat_bundle().presentation.create_integration(widget, logger, context)

    assert type(native_integration).__name__ == "_XcbIntegration"
    assert type(xwayland_integration).__name__ == "_XcbIntegration"


def test_x11_and_xwayland_bundles_share_current_shipped_wmctrl_tracker_shape():
    logger = logging.getLogger("test.backend.bundles.x11")

    native_tracker = build_native_x11_bundle().discovery.create_tracker(logger)
    xwayland_tracker = build_xwayland_compat_bundle().discovery.create_tracker(logger)

    assert type(native_tracker).__name__ == "_WmctrlTracker"
    assert type(xwayland_tracker).__name__ == "_WmctrlTracker"
