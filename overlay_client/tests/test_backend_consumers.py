import logging

import pytest

from overlay_client.backend.bundles import (
    gnome_shell_wayland,
    hyprland,
    kwin_wayland,
    native_x11,
    sway_wayfire_wlroots,
    wayland_layer_shell_generic,
    xwayland_compat,
)
from overlay_client.backend.bundles import _wayland_common
from overlay_client.backend.consumers import (
    create_bundle_integration,
    create_bundle_tracker,
    derive_linux_backend_status,
    is_wayland_bundle,
    platform_label_for_bundle,
    resolve_linux_bundle_from_status,
    resolve_tracker_fallback_bundle,
    uses_transient_parent,
)
from overlay_client.backend.contracts import (
    BackendBundle,
    BackendCapabilities,
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


class _CapabilityOnlyDiscovery:
    @property
    def backend_instance(self) -> BackendInstance:
        return BackendInstance.NATIVE_X11

    def create_tracker(self, logger, *, title_hint="elite - dangerous", monitor_provider=None):
        del logger, title_hint, monitor_provider
        return None


class _CapabilityOnlyPresentation:
    @property
    def backend_instance(self) -> BackendInstance:
        return BackendInstance.NATIVE_X11

    def create_integration(self, widget, logger, context):
        return (widget, logger, context)


class _CapabilityOnlyInputPolicy:
    @property
    def backend_instance(self) -> BackendInstance:
        return BackendInstance.NATIVE_X11


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
    context = PlatformContext(session_type="x11", compositor="none")

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


def test_capability_helpers_use_backend_declared_metadata_over_descriptor_inference():
    bundle = BackendBundle(
        descriptor=BackendDescriptor(
            family=BackendFamily.NATIVE_X11,
            instance=BackendInstance.NATIVE_X11,
        ),
        capabilities=BackendCapabilities(
            platform_label="Wayland",
            uses_native_wayland_windowing=True,
            requires_transient_parent=False,
            tracker_available=False,
            tracker_fallback_by_session=((SessionType.WAYLAND, BackendInstance.XWAYLAND_COMPAT),),
        ),
        discovery=_CapabilityOnlyDiscovery(),
        presentation=_CapabilityOnlyPresentation(),
        input_policy=_CapabilityOnlyInputPolicy(),
    )

    assert platform_label_for_bundle(bundle) == "Wayland"
    assert is_wayland_bundle(bundle) is True
    assert uses_transient_parent(bundle) is False


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
    context = PlatformContext(session_type="wayland", compositor="kwin")

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
    context = PlatformContext(session_type="wayland", compositor="hyprland")

    integration = create_bundle_integration(bundle, widget, logger, context)

    assert integration is sentinel
    assert observed["widget"] is widget
    assert observed["logger"] is logger
    assert observed["context"] is context


@pytest.mark.parametrize(
    ("build_bundle", "context"),
    [
        (
            sway_wayfire_wlroots.build_sway_wayfire_wlroots_bundle,
            PlatformContext(session_type="wayland", compositor="sway"),
        ),
        (
            hyprland.build_hyprland_bundle,
            PlatformContext(session_type="wayland", compositor="hyprland"),
        ),
        (
            kwin_wayland.build_kwin_wayland_bundle,
            PlatformContext(session_type="wayland", compositor="kwin"),
        ),
        (
            gnome_shell_wayland.build_gnome_shell_wayland_bundle,
            PlatformContext(session_type="wayland", compositor="gnome-shell"),
        ),
    ],
)
def test_consumer_helper_routes_native_wayland_bundles_through_shared_wayland_factory(
    monkeypatch,
    build_bundle,
    context,
):
    sentinel = object()
    observed = {}

    def _factory(widget, logger, incoming_context):
        observed["widget"] = widget
        observed["logger"] = logger
        observed["context"] = incoming_context
        return sentinel

    monkeypatch.setattr(_wayland_common, "create_wayland_integration", _factory)
    bundle = build_bundle()
    widget = object()
    logger = logging.getLogger("test.backend.consumers.native_wayland")

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


def test_derive_linux_backend_status_preserves_xwayland_compat_identity_for_wayland_xcb_path():
    status = derive_linux_backend_status(
        session_type="wayland",
        compositor="kwin",
        qt_platform_name="xcb",
        env={"XDG_SESSION_TYPE": "wayland"},
    )
    bundle = resolve_linux_bundle_from_status(status)

    assert status.selected_backend.instance is BackendInstance.XWAYLAND_COMPAT
    assert bundle.descriptor.instance is BackendInstance.XWAYLAND_COMPAT
    assert platform_label_for_bundle(bundle) == "Wayland (XWayland)"
    assert is_wayland_bundle(bundle) is False
    assert uses_transient_parent(bundle) is True


def test_derive_linux_backend_status_preserves_native_x11_identity_for_x11_path():
    status = derive_linux_backend_status(
        session_type="x11",
        compositor="none",
        qt_platform_name="xcb",
        env={"XDG_SESSION_TYPE": "x11"},
    )
    bundle = resolve_linux_bundle_from_status(status)

    assert status.selected_backend.instance is BackendInstance.NATIVE_X11
    assert bundle.descriptor.instance is BackendInstance.NATIVE_X11
    assert platform_label_for_bundle(bundle) == "X11"
    assert is_wayland_bundle(bundle) is False
    assert uses_transient_parent(bundle) is True


def test_derive_linux_backend_status_preserves_kwin_native_wayland_identity():
    status = derive_linux_backend_status(
        session_type="wayland",
        compositor="kwin",
        qt_platform_name="wayland",
        env={"XDG_SESSION_TYPE": "wayland"},
    )
    bundle = resolve_linux_bundle_from_status(status)

    assert status.selected_backend.instance is BackendInstance.KWIN_WAYLAND
    assert bundle.descriptor.instance is BackendInstance.KWIN_WAYLAND
    assert platform_label_for_bundle(bundle) == "Wayland"
    assert is_wayland_bundle(bundle) is True
    assert uses_transient_parent(bundle) is False


def test_derive_linux_backend_status_infers_gnome_and_generic_wayland_paths_from_runtime_context():
    gnome_status = derive_linux_backend_status(
        session_type="wayland",
        compositor="",
        qt_platform_name="wayland",
        env={"XDG_SESSION_TYPE": "wayland", "XDG_CURRENT_DESKTOP": "GNOME"},
    )
    generic_status = derive_linux_backend_status(
        session_type="wayland",
        compositor="cosmic",
        qt_platform_name="wayland",
        env={"XDG_SESSION_TYPE": "wayland"},
    )
    gnome_bundle = resolve_linux_bundle_from_status(gnome_status)
    generic_bundle = resolve_linux_bundle_from_status(generic_status)

    assert gnome_status.selected_backend.instance is BackendInstance.GNOME_SHELL_WAYLAND
    assert generic_status.selected_backend.instance is BackendInstance.COSMIC
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


def test_resolve_tracker_fallback_bundle_uses_native_x11_for_x11_selection():
    status = BackendSelectionStatus(
        probe=PlatformProbeResult(
            operating_system=OperatingSystem.LINUX,
            session_type=SessionType.X11,
            qt_platform_name="xcb",
            compositor="kwin",
        ),
        selected_backend=BackendDescriptor(
            BackendFamily.NATIVE_WAYLAND,
            BackendInstance.KWIN_WAYLAND,
        ),
        classification=CapabilityClassification.TRUE_OVERLAY,
    )

    fallback_bundle = resolve_tracker_fallback_bundle(status)

    assert fallback_bundle is not None
    assert fallback_bundle.descriptor.instance is BackendInstance.NATIVE_X11


def test_resolve_tracker_fallback_bundle_uses_bundle_declared_fallback_mapping(monkeypatch):
    status = BackendSelectionStatus(
        probe=PlatformProbeResult(
            operating_system=OperatingSystem.LINUX,
            session_type=SessionType.WAYLAND,
            qt_platform_name="wayland",
            compositor="custom",
        ),
        selected_backend=BackendDescriptor(
            BackendFamily.NATIVE_WAYLAND,
            BackendInstance.KWIN_WAYLAND,
        ),
        classification=CapabilityClassification.TRUE_OVERLAY,
    )

    capability_bundle = BackendBundle(
        descriptor=BackendDescriptor(
            family=BackendFamily.NATIVE_WAYLAND,
            instance=BackendInstance.KWIN_WAYLAND,
        ),
        capabilities=BackendCapabilities(
            platform_label="Wayland",
            uses_native_wayland_windowing=True,
            requires_transient_parent=False,
            tracker_available=False,
            tracker_fallback_by_session=((SessionType.WAYLAND, BackendInstance.NATIVE_X11),),
        ),
        discovery=_CapabilityOnlyDiscovery(),
        presentation=_CapabilityOnlyPresentation(),
        input_policy=_CapabilityOnlyInputPolicy(),
    )

    monkeypatch.setattr("overlay_client.backend.consumers.resolve_linux_bundle_from_status", lambda _: capability_bundle)
    monkeypatch.setattr(
        "overlay_client.backend.consumers._build_linux_bundle_for_instance",
        lambda instance: BackendBundle(
            descriptor=BackendDescriptor(BackendFamily.NATIVE_X11, instance),
            capabilities=BackendCapabilities(
                platform_label="X11",
                uses_native_wayland_windowing=False,
                requires_transient_parent=True,
            ),
            discovery=_CapabilityOnlyDiscovery(),
            presentation=_CapabilityOnlyPresentation(),
            input_policy=_CapabilityOnlyInputPolicy(),
        ),
    )

    fallback_bundle = resolve_tracker_fallback_bundle(status)

    assert fallback_bundle is not None
    assert fallback_bundle.descriptor.instance is BackendInstance.NATIVE_X11
