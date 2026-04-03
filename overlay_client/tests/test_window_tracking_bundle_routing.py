import logging

from overlay_client.backend import consumers as backend_consumers
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
from overlay_client.window_tracking import create_elite_window_tracker


def _status(instance: BackendInstance, *, family: BackendFamily, session_type: SessionType, compositor: str):
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


def test_create_elite_window_tracker_uses_native_x11_bundle_for_x11_sessions(monkeypatch):
    sentinel = object()
    seen_instances = []

    def _factory(bundle, logger, *, title_hint="elite - dangerous", monitor_provider=None):
        del logger, title_hint, monitor_provider
        seen_instances.append(bundle.descriptor.instance)
        return sentinel

    monkeypatch.setattr("overlay_client.window_tracking.sys.platform", "linux")
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    monkeypatch.delenv("EDMC_OVERLAY_COMPOSITOR", raising=False)
    monkeypatch.delenv("EDMC_OVERLAY_FORCE_XWAYLAND", raising=False)
    monkeypatch.setattr(backend_consumers, "create_bundle_tracker", _factory)

    tracker = create_elite_window_tracker(logging.getLogger("test.window_tracking.x11"))

    assert tracker is sentinel
    assert seen_instances == [BackendInstance.NATIVE_X11]


def test_create_elite_window_tracker_uses_native_wayland_bundle_before_fallback(monkeypatch):
    sentinel = object()
    seen_instances = []

    def _factory(bundle, logger, *, title_hint="elite - dangerous", monitor_provider=None):
        del logger, title_hint, monitor_provider
        seen_instances.append(bundle.descriptor.instance)
        if bundle.descriptor.instance is BackendInstance.GNOME_SHELL_WAYLAND:
            return None
        if bundle.descriptor.instance is BackendInstance.XWAYLAND_COMPAT:
            return sentinel
        raise AssertionError(f"unexpected bundle {bundle.descriptor.instance}")

    monkeypatch.setattr("overlay_client.window_tracking.sys.platform", "linux")
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("EDMC_OVERLAY_COMPOSITOR", "gnome-shell")
    monkeypatch.delenv("EDMC_OVERLAY_FORCE_XWAYLAND", raising=False)
    monkeypatch.setattr(backend_consumers, "create_bundle_tracker", _factory)

    tracker = create_elite_window_tracker(logging.getLogger("test.window_tracking.gnome"))

    assert tracker is sentinel
    assert seen_instances == [
        BackendInstance.GNOME_SHELL_WAYLAND,
        BackendInstance.XWAYLAND_COMPAT,
    ]


def test_create_elite_window_tracker_preserves_wayland_bundle_when_tracker_exists(monkeypatch):
    sentinel = object()
    seen_instances = []

    def _factory(bundle, logger, *, title_hint="elite - dangerous", monitor_provider=None):
        del logger, title_hint, monitor_provider
        seen_instances.append(bundle.descriptor.instance)
        if bundle.descriptor.instance is BackendInstance.KWIN_WAYLAND:
            return sentinel
        raise AssertionError(f"unexpected fallback bundle {bundle.descriptor.instance}")

    monkeypatch.setattr("overlay_client.window_tracking.sys.platform", "linux")
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("EDMC_OVERLAY_COMPOSITOR", "kwin")
    monkeypatch.delenv("EDMC_OVERLAY_FORCE_XWAYLAND", raising=False)
    monkeypatch.setattr(backend_consumers, "create_bundle_tracker", _factory)

    tracker = create_elite_window_tracker(logging.getLogger("test.window_tracking.kwin"))

    assert tracker is sentinel
    assert seen_instances == [BackendInstance.KWIN_WAYLAND]


def test_create_elite_window_tracker_prefers_client_selected_bundle_when_provided(monkeypatch):
    sentinel = object()
    seen_instances = []

    def _factory(bundle, logger, *, title_hint="elite - dangerous", monitor_provider=None):
        del logger, title_hint, monitor_provider
        seen_instances.append(bundle.descriptor.instance)
        return sentinel

    monkeypatch.setattr("overlay_client.window_tracking.sys.platform", "linux")
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    monkeypatch.setattr(backend_consumers, "create_bundle_tracker", _factory)

    tracker = create_elite_window_tracker(
        logging.getLogger("test.window_tracking.selected_status"),
        backend_status=_status(
            BackendInstance.KWIN_WAYLAND,
            family=BackendFamily.NATIVE_WAYLAND,
            session_type=SessionType.WAYLAND,
            compositor="kwin",
        ),
    )

    assert tracker is sentinel
    assert seen_instances == [BackendInstance.KWIN_WAYLAND]


def test_create_elite_window_tracker_uses_status_based_wayland_fallback(monkeypatch):
    sentinel = object()
    seen_instances = []

    def _factory(bundle, logger, *, title_hint="elite - dangerous", monitor_provider=None):
        del logger, title_hint, monitor_provider
        seen_instances.append(bundle.descriptor.instance)
        if bundle.descriptor.instance is BackendInstance.GNOME_SHELL_WAYLAND:
            return None
        if bundle.descriptor.instance is BackendInstance.XWAYLAND_COMPAT:
            return sentinel
        raise AssertionError(f"unexpected bundle {bundle.descriptor.instance}")

    monkeypatch.setattr("overlay_client.window_tracking.sys.platform", "linux")
    monkeypatch.setattr(backend_consumers, "create_bundle_tracker", _factory)

    tracker = create_elite_window_tracker(
        logging.getLogger("test.window_tracking.selected_status_fallback"),
        backend_status=_status(
            BackendInstance.GNOME_SHELL_WAYLAND,
            family=BackendFamily.NATIVE_WAYLAND,
            session_type=SessionType.WAYLAND,
            compositor="gnome-shell",
        ),
    )

    assert tracker is sentinel
    assert seen_instances == [
        BackendInstance.GNOME_SHELL_WAYLAND,
        BackendInstance.XWAYLAND_COMPAT,
    ]
