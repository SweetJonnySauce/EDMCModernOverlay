import logging

from overlay_client.backend.bundles import (
    gnome_shell_wayland,
    hyprland,
    native_x11,
    wayland_layer_shell_generic,
    xwayland_compat,
)
from overlay_client.backend.bundles import _wayland_common
from overlay_client.backend.consumers import (
    create_bundle_integration,
    create_bundle_tracker,
    is_wayland_bundle,
    platform_label_for_bundle,
    resolve_legacy_linux_bundle,
    resolve_linux_bundle_from_status,
    resolve_tracker_fallback_bundle,
    uses_transient_parent,
)
from overlay_client.backend.contracts import (
    BackendDescriptor,
    BackendFamily,
    BackendInstance,
    CapabilityClassification,
    OperatingSystem,
    PlatformProbeResult,
    SessionType,
)
from overlay_client.backend.status import BackendSelectionStatus
from overlay_client.platform_integration import PlatformContext


def test_consumer_helper_uses_native_x11_integration_factory(monkeypatch):
    sentinel = object()
    observed = {}

    def _factory(widget, logger, context):
        observed["widget"] = widget
        observed["logger"] = logger
        observed["context"] = context
        return sentinel

    monkeypatch.setattr(native_x11, "create_xcb_integration", _factory)
    bundle = native_x11.build_native_x11_bundle()
    widget = object()
    logger = logging.getLogger("test.backend.consumers.native_x11")
    context = PlatformContext(session_type="x11", compositor="none", force_xwayland=False)

    integration = create_bundle_integration(bundle, widget, logger, context)

    assert integration is sentinel
    assert observed["widget"] is widget
    assert observed["logger"] is logger
    assert observed["context"] is context


def test_consumer_helper_uses_native_x11_tracker_factory(monkeypatch):
    sentinel = object()
    observed = {}

    def _factory(logger, *, title_hint="elite - dangerous", monitor_provider=None):
        observed["logger"] = logger
        observed["title_hint"] = title_hint
        observed["monitor_provider"] = monitor_provider
        return sentinel

    def _monitor_provider():
        return []

    monkeypatch.setattr(native_x11, "create_wmctrl_tracker", _factory)
    bundle = native_x11.build_native_x11_bundle()
    logger = logging.getLogger("test.backend.consumers.native_x11")
    monitor_provider = _monitor_provider

    tracker = create_bundle_tracker(bundle, logger, title_hint="elite", monitor_provider=monitor_provider)

    assert tracker is sentinel
    assert observed["logger"] is logger
    assert observed["title_hint"] == "elite"
    assert observed["monitor_provider"] is monitor_provider


def test_consumer_helper_uses_xwayland_integration_factory(monkeypatch):
    sentinel = object()
    observed = {}

    def _factory(widget, logger, context):
        observed["widget"] = widget
        observed["logger"] = logger
        observed["context"] = context
        return sentinel

    monkeypatch.setattr(xwayland_compat, "create_xcb_integration", _factory)
    bundle = xwayland_compat.build_xwayland_compat_bundle()
    widget = object()
    logger = logging.getLogger("test.backend.consumers.xwayland")
    context = PlatformContext(session_type="wayland", compositor="kwin", force_xwayland=True)

    integration = create_bundle_integration(bundle, widget, logger, context)

    assert integration is sentinel
    assert observed["widget"] is widget
    assert observed["logger"] is logger
    assert observed["context"] is context


def test_consumer_helper_uses_xwayland_tracker_factory(monkeypatch):
    sentinel = object()
    observed = {}

    def _factory(logger, *, title_hint="elite - dangerous", monitor_provider=None):
        observed["logger"] = logger
        observed["title_hint"] = title_hint
        observed["monitor_provider"] = monitor_provider
        return sentinel

    def _monitor_provider():
        return []

    monkeypatch.setattr(xwayland_compat, "create_wmctrl_tracker", _factory)
    bundle = xwayland_compat.build_xwayland_compat_bundle()
    logger = logging.getLogger("test.backend.consumers.xwayland")
    monitor_provider = _monitor_provider

    tracker = create_bundle_tracker(bundle, logger, title_hint="elite", monitor_provider=monitor_provider)

    assert tracker is sentinel
    assert observed["logger"] is logger
    assert observed["title_hint"] == "elite"
    assert observed["monitor_provider"] is monitor_provider


def test_consumer_helper_uses_shipped_wayland_integration_factory(monkeypatch):
    sentinel = object()
    observed = {}

    def _factory(widget, logger, context):
        observed["widget"] = widget
        observed["logger"] = logger
        observed["context"] = context
        return sentinel

    monkeypatch.setattr(_wayland_common, "create_wayland_integration", _factory)
    bundle = hyprland.build_hyprland_bundle()
    widget = object()
    logger = logging.getLogger("test.backend.consumers.hyprland")
    context = PlatformContext(session_type="wayland", compositor="hyprland", force_xwayland=False)

    integration = create_bundle_integration(bundle, widget, logger, context)

    assert integration is sentinel
    assert observed["widget"] is widget
    assert observed["logger"] is logger
    assert observed["context"] is context


def test_consumer_helper_uses_hyprland_tracker_factory(monkeypatch):
    sentinel = object()
    observed = {}

    def _factory(logger, *, title_hint="elite - dangerous", monitor_provider=None):
        observed["logger"] = logger
        observed["title_hint"] = title_hint
        observed["monitor_provider"] = monitor_provider
        return sentinel

    def _monitor_provider():
        return []

    monkeypatch.setattr(hyprland, "create_hyprland_tracker", _factory)
    bundle = hyprland.build_hyprland_bundle()
    logger = logging.getLogger("test.backend.consumers.hyprland")
    monitor_provider = _monitor_provider

    tracker = create_bundle_tracker(bundle, logger, title_hint="elite", monitor_provider=monitor_provider)

    assert tracker is sentinel
    assert observed["logger"] is logger
    assert observed["title_hint"] == "elite"
    assert observed["monitor_provider"] is monitor_provider


def test_consumer_helper_allows_missing_tracker_for_gnome_wayland_bundle():
    bundle = gnome_shell_wayland.build_gnome_shell_wayland_bundle()
    logger = logging.getLogger("test.backend.consumers.gnome")

    tracker = create_bundle_tracker(bundle, logger, title_hint="elite", monitor_provider=lambda: [])

    assert tracker is None


def test_consumer_helper_allows_missing_tracker_for_generic_wayland_bundle():
    bundle = wayland_layer_shell_generic.build_wayland_layer_shell_generic_bundle()
    logger = logging.getLogger("test.backend.consumers.generic_wayland")

    tracker = create_bundle_tracker(bundle, logger, title_hint="elite", monitor_provider=lambda: [])

    assert tracker is None


def test_resolve_legacy_linux_bundle_preserves_xwayland_compat_identity_for_wayland_xcb_path():
    bundle = resolve_legacy_linux_bundle(
        session_type="wayland",
        compositor="kwin",
        force_xwayland=False,
        qt_platform_name="xcb",
        env={"XDG_SESSION_TYPE": "wayland"},
    )

    assert bundle.descriptor.instance is BackendInstance.XWAYLAND_COMPAT
    assert platform_label_for_bundle(bundle) == "Wayland (XWayland)"
    assert is_wayland_bundle(bundle) is False
    assert uses_transient_parent(bundle) is True


def test_resolve_legacy_linux_bundle_preserves_native_x11_identity_for_x11_path():
    bundle = resolve_legacy_linux_bundle(
        session_type="x11",
        compositor="none",
        force_xwayland=False,
        qt_platform_name="xcb",
        env={"XDG_SESSION_TYPE": "x11"},
    )

    assert bundle.descriptor.instance is BackendInstance.NATIVE_X11
    assert platform_label_for_bundle(bundle) == "X11"
    assert is_wayland_bundle(bundle) is False
    assert uses_transient_parent(bundle) is True


def test_resolve_legacy_linux_bundle_preserves_kwin_native_wayland_identity():
    bundle = resolve_legacy_linux_bundle(
        session_type="wayland",
        compositor="kwin",
        force_xwayland=False,
        qt_platform_name="wayland",
        env={"XDG_SESSION_TYPE": "wayland"},
    )

    assert bundle.descriptor.instance is BackendInstance.KWIN_WAYLAND
    assert platform_label_for_bundle(bundle) == "Wayland"
    assert is_wayland_bundle(bundle) is True
    assert uses_transient_parent(bundle) is False


def test_resolve_legacy_linux_bundle_infers_gnome_and_generic_wayland_paths_from_runtime_context():
    gnome_bundle = resolve_legacy_linux_bundle(
        session_type="wayland",
        compositor="",
        force_xwayland=False,
        qt_platform_name="wayland",
        env={"XDG_SESSION_TYPE": "wayland", "XDG_CURRENT_DESKTOP": "GNOME"},
    )
    generic_bundle = resolve_legacy_linux_bundle(
        session_type="wayland",
        compositor="cosmic",
        force_xwayland=False,
        qt_platform_name="wayland",
        env={"XDG_SESSION_TYPE": "wayland"},
    )

    assert gnome_bundle.descriptor.instance is BackendInstance.GNOME_SHELL_WAYLAND
    assert generic_bundle.descriptor.instance is BackendInstance.WAYLAND_LAYER_SHELL_GENERIC


def test_resolve_linux_bundle_from_status_preserves_selected_xwayland_bundle():
    status = BackendSelectionStatus(
        probe=PlatformProbeResult(
            operating_system=OperatingSystem.LINUX,
            session_type=SessionType.WAYLAND,
            qt_platform_name="xcb",
            compositor="kwin",
        ),
        selected_backend=BackendDescriptor(
            BackendFamily.XWAYLAND_COMPAT,
            BackendInstance.XWAYLAND_COMPAT,
        ),
        classification=CapabilityClassification.TRUE_OVERLAY,
    )

    bundle = resolve_linux_bundle_from_status(status)

    assert bundle.descriptor.instance is BackendInstance.XWAYLAND_COMPAT


def test_resolve_linux_bundle_from_status_maps_unsupported_cosmic_to_generic_bundle():
    status = BackendSelectionStatus(
        probe=PlatformProbeResult(
            operating_system=OperatingSystem.LINUX,
            session_type=SessionType.WAYLAND,
            qt_platform_name="wayland",
            compositor="cosmic",
        ),
        selected_backend=BackendDescriptor(
            BackendFamily.NATIVE_WAYLAND,
            BackendInstance.COSMIC,
        ),
        classification=CapabilityClassification.UNSUPPORTED,
    )

    bundle = resolve_linux_bundle_from_status(status)

    assert bundle.descriptor.instance is BackendInstance.WAYLAND_LAYER_SHELL_GENERIC


def test_resolve_tracker_fallback_bundle_uses_xwayland_for_wayland_selection():
    status = BackendSelectionStatus(
        probe=PlatformProbeResult(
            operating_system=OperatingSystem.LINUX,
            session_type=SessionType.WAYLAND,
            qt_platform_name="wayland",
            compositor="gnome-shell",
        ),
        selected_backend=BackendDescriptor(
            BackendFamily.NATIVE_WAYLAND,
            BackendInstance.GNOME_SHELL_WAYLAND,
        ),
        classification=CapabilityClassification.TRUE_OVERLAY,
    )

    fallback_bundle = resolve_tracker_fallback_bundle(status)

    assert fallback_bundle is not None
    assert fallback_bundle.descriptor.instance is BackendInstance.XWAYLAND_COMPAT
