import logging

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
from overlay_client.platform_integration import PlatformContext, PlatformController


class _FakeIntegration:
    def __init__(self, label):
        self.label = label
        self._window = None
        self.updated_contexts = []

    def update_context(self, context):
        self.updated_contexts.append(context)

    def prepare_window(self, window):
        self._window = window

    def apply_click_through(self, transparent):
        self.transparent = bool(transparent)

    def monitors(self):
        return []


def _status(instance: BackendInstance, *, family: BackendFamily, session_type: SessionType, compositor: str) -> BackendSelectionStatus:
    return BackendSelectionStatus(
        probe=PlatformProbeResult(
            operating_system=OperatingSystem.LINUX,
            session_type=session_type,
            qt_platform_name="wayland" if session_type is SessionType.WAYLAND else "xcb",
            compositor=compositor,
        ),
        selected_backend=BackendDescriptor(family, instance),
        classification=CapabilityClassification.TRUE_OVERLAY,
    )


def test_platform_controller_prefers_backend_status_over_legacy_context(monkeypatch):
    created = []

    def _factory(bundle, widget, logger, context):
        del widget, logger, context
        created.append(bundle.descriptor.instance)
        return _FakeIntegration(bundle.descriptor.instance.value)

    monkeypatch.setattr("overlay_client.platform_integration.sys.platform", "linux")
    monkeypatch.setattr("overlay_client.platform_integration.QGuiApplication.platformName", lambda: "xcb")
    monkeypatch.setattr("overlay_client.platform_integration.create_bundle_integration", _factory)

    controller = PlatformController(
        object(),
        logging.getLogger("test.platform_controller.selected_bundle"),
        PlatformContext(session_type="x11", compositor=""),
        backend_status=_status(
            BackendInstance.KWIN_WAYLAND,
            family=BackendFamily.NATIVE_WAYLAND,
            session_type=SessionType.WAYLAND,
            compositor="kwin",
        ),
    )

    assert created == [BackendInstance.KWIN_WAYLAND]
    assert controller.is_wayland_backend() is True
    assert controller.uses_transient_parent() is False
    assert controller.platform_label() == "Wayland"


def test_platform_controller_derives_backend_status_when_none_is_provided(monkeypatch):
    created = []

    def _factory(bundle, widget, logger, context):
        del widget, logger, context
        created.append(bundle.descriptor.instance)
        return _FakeIntegration(bundle.descriptor.instance.value)

    monkeypatch.setattr("overlay_client.platform_integration.sys.platform", "linux")
    monkeypatch.setattr("overlay_client.platform_integration.QGuiApplication.platformName", lambda: "wayland")
    monkeypatch.setattr("overlay_client.platform_integration.create_bundle_integration", _factory)

    controller = PlatformController(
        object(),
        logging.getLogger("test.platform_controller.derived_bundle"),
        PlatformContext(session_type="wayland", compositor="kwin"),
        backend_status=None,
    )

    assert created == [BackendInstance.KWIN_WAYLAND]
    assert controller.is_wayland_backend() is True
    assert controller.uses_transient_parent() is False
    assert controller.platform_label() == "Wayland"


def test_platform_controller_rebuilds_integration_when_backend_status_changes(monkeypatch):
    created = []
    integrations = []

    def _factory(bundle, widget, logger, context):
        del widget, logger, context
        created.append(bundle.descriptor.instance)
        integration = _FakeIntegration(bundle.descriptor.instance.value)
        integrations.append(integration)
        return integration

    monkeypatch.setattr("overlay_client.platform_integration.sys.platform", "linux")
    monkeypatch.setattr("overlay_client.platform_integration.QGuiApplication.platformName", lambda: "xcb")
    monkeypatch.setattr("overlay_client.platform_integration.create_bundle_integration", _factory)

    controller = PlatformController(
        object(),
        logging.getLogger("test.platform_controller.update_bundle"),
        PlatformContext(session_type="x11", compositor=""),
        backend_status=_status(
            BackendInstance.NATIVE_X11,
            family=BackendFamily.NATIVE_X11,
            session_type=SessionType.X11,
            compositor="",
        ),
    )
    controller.prepare_window("window-handle")
    controller.update_context(PlatformContext(session_type="wayland", compositor="kwin"))
    controller.update_backend_status(
        _status(
            BackendInstance.KWIN_WAYLAND,
            family=BackendFamily.NATIVE_WAYLAND,
            session_type=SessionType.WAYLAND,
            compositor="kwin",
        )
    )

    assert created == [BackendInstance.NATIVE_X11, BackendInstance.KWIN_WAYLAND]
    assert integrations[1]._window == "window-handle"
    assert integrations[1].updated_contexts == []
    assert controller.is_wayland_backend() is True


def test_platform_controller_disables_explicit_raise_for_helper_backed_gnome(monkeypatch):
    created = []

    def _factory(bundle, widget, logger, context):
        del widget, logger, context
        created.append(bundle.descriptor.instance)
        return _FakeIntegration(bundle.descriptor.instance.value)

    monkeypatch.setattr("overlay_client.platform_integration.sys.platform", "linux")
    monkeypatch.setattr("overlay_client.platform_integration.QGuiApplication.platformName", lambda: "wayland")
    monkeypatch.setattr("overlay_client.platform_integration.create_bundle_integration", _factory)

    controller = PlatformController(
        object(),
        logging.getLogger("test.platform_controller.raise_policy.gnome_helper"),
        PlatformContext(session_type="wayland", compositor="gnome-shell"),
        backend_status=_status(
            BackendInstance.GNOME_SHELL_WAYLAND,
            family=BackendFamily.COMPOSITOR_HELPER,
            session_type=SessionType.WAYLAND,
            compositor="gnome-shell",
        ),
    )

    assert created == [BackendInstance.GNOME_SHELL_WAYLAND]
    assert controller.should_raise_overlay_window() is False
    assert controller.should_use_tool_window() is True


def test_platform_controller_keeps_explicit_raise_for_non_helper_backends(monkeypatch):
    created = []

    def _factory(bundle, widget, logger, context):
        del widget, logger, context
        created.append(bundle.descriptor.instance)
        return _FakeIntegration(bundle.descriptor.instance.value)

    monkeypatch.setattr("overlay_client.platform_integration.sys.platform", "linux")
    monkeypatch.setattr("overlay_client.platform_integration.QGuiApplication.platformName", lambda: "xcb")
    monkeypatch.setattr("overlay_client.platform_integration.create_bundle_integration", _factory)

    controller = PlatformController(
        object(),
        logging.getLogger("test.platform_controller.raise_policy.x11"),
        PlatformContext(session_type="x11", compositor=""),
        backend_status=_status(
            BackendInstance.NATIVE_X11,
            family=BackendFamily.NATIVE_X11,
            session_type=SessionType.X11,
            compositor="",
        ),
    )

    assert created == [BackendInstance.NATIVE_X11]
    assert controller.should_raise_overlay_window() is True
    assert controller.should_use_tool_window() is True


def test_platform_controller_keeps_tool_window_disabled_for_non_helper_wayland(monkeypatch):
    created = []

    def _factory(bundle, widget, logger, context):
        del widget, logger, context
        created.append(bundle.descriptor.instance)
        return _FakeIntegration(bundle.descriptor.instance.value)

    monkeypatch.setattr("overlay_client.platform_integration.sys.platform", "linux")
    monkeypatch.setattr("overlay_client.platform_integration.QGuiApplication.platformName", lambda: "wayland")
    monkeypatch.setattr("overlay_client.platform_integration.create_bundle_integration", _factory)

    controller = PlatformController(
        object(),
        logging.getLogger("test.platform_controller.tool_policy.kwin"),
        PlatformContext(session_type="wayland", compositor="kwin"),
        backend_status=_status(
            BackendInstance.KWIN_WAYLAND,
            family=BackendFamily.NATIVE_WAYLAND,
            session_type=SessionType.WAYLAND,
            compositor="kwin",
        ),
    )

    assert created == [BackendInstance.KWIN_WAYLAND]
    assert controller.should_use_tool_window() is False
