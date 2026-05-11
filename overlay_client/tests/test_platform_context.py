import sys
import types

try:  # pragma: no cover - exercised when PyQt6 is present
    from PyQt6 import QtGui as _QtGui  # noqa: F401
except Exception:  # pragma: no cover - lightweight stub path
    if "PyQt6" not in sys.modules:
        sys.modules["PyQt6"] = types.ModuleType("PyQt6")
    qtgui = sys.modules.get("PyQt6.QtGui") or types.ModuleType("PyQt6.QtGui")
    qtgui.QGuiApplication = getattr(
        qtgui,
        "QGuiApplication",
        type("QGuiApplication", (), {"platformName": staticmethod(lambda: "wayland")}),
    )
    qtgui.QWindow = getattr(qtgui, "QWindow", object)
    sys.modules["PyQt6.QtGui"] = qtgui

    qtwidgets = sys.modules.get("PyQt6.QtWidgets") or types.ModuleType("PyQt6.QtWidgets")
    qtwidgets.QWidget = getattr(qtwidgets, "QWidget", object)
    sys.modules["PyQt6.QtWidgets"] = qtwidgets

    qtcore = sys.modules.get("PyQt6.QtCore") or types.ModuleType("PyQt6.QtCore")
    qtcore.Qt = type(
        "Qt",
        (),
        {
            "WidgetAttribute": type("WidgetAttribute", (), {"WA_TransparentForMouseEvents": object()}),
            "WindowType": type(
                "WindowType",
                (),
                {
                    "WindowStaysOnTopHint": 1,
                    "Tool": 2,
                    "FramelessWindowHint": 4,
                    "WindowTransparentForInput": object(),
                },
            ),
            "PenStyle": type("PenStyle", (), {"NoPen": object()}),
            "PenJoinStyle": type("PenJoinStyle", (), {"MiterJoin": object()}),
        },
    )
    sys.modules["PyQt6.QtCore"] = qtcore

from overlay_client.backend import (
    BackendFamily,
    BackendInstance,
    CapabilityClassification,
    GNOME_SHELL_HELPER_CAPABILITIES,
    HelperDbusServiceMissing,
    ProbeSource,
)
from overlay_client import platform_context as platform_context_module
from overlay_client.platform_context import _backend_status_signature, _client_backend_status, _initial_platform_context
from overlay_client.platform_integration import PlatformContext


class _Initial:
    def __init__(self, manual_backend_override: str = "") -> None:
        self.manual_backend_override = manual_backend_override


def _healthy_gnome_helper_payload() -> dict[str, object]:
    return {
        "status": "healthy",
        "helper_kind": "gnome_shell_extension",
        "helper_version": "1.0.0",
        "helper_protocol": 3,
        "capabilities": list(GNOME_SHELL_HELPER_CAPABILITIES),
    }


def test_initial_platform_context_prefers_env(monkeypatch):
    monkeypatch.setenv("EDMC_OVERLAY_SESSION_TYPE", "wayland")
    monkeypatch.setenv("EDMC_OVERLAY_COMPOSITOR", "kwin")
    monkeypatch.setenv("EDMC_OVERLAY_IS_FLATPAK", "1")
    monkeypatch.setenv("EDMC_OVERLAY_FLATPAK_ID", "app.id")

    ctx = _initial_platform_context(_Initial())
    assert ctx.session_type == "wayland"
    assert ctx.compositor == "kwin"
    assert ctx.flatpak is True
    assert ctx.flatpak_app == "app.id"
    assert ctx.manual_backend_override == ""


def test_initial_platform_context_carries_manual_backend_override():
    ctx = _initial_platform_context(_Initial(manual_backend_override="xwayland_compat"))
    assert ctx.manual_backend_override == "xwayland_compat"


def test_client_backend_status_prefers_local_runtime_over_plugin_hint(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "GNOME")
    context = PlatformContext(session_type="x11", compositor="kwin")

    status = _client_backend_status(
        context,
        source=ProbeSource.RUNTIME_UPDATE,
        qt_platform_name="wayland",
        env={"XDG_SESSION_TYPE": "wayland", "XDG_CURRENT_DESKTOP": "GNOME"},
        sys_platform_name="linux",
    )

    assert status.shadow_mode is False
    assert status.selected_backend.instance is BackendInstance.GNOME_SHELL_WAYLAND
    assert status.classification is CapabilityClassification.DEGRADED_OVERLAY
    assert status.fallback_reason is not None
    assert status.fallback_reason.value == "missing_helper"
    assert status.notes[0] == "client_selector_result"


def test_client_backend_status_marks_gnome_helper_available_when_dbus_health_is_healthy():
    context = PlatformContext(session_type="wayland", compositor="gnome-shell")

    status = _client_backend_status(
        context,
        source=ProbeSource.RUNTIME_UPDATE,
        qt_platform_name="wayland",
        env={
            "XDG_SESSION_TYPE": "wayland",
            "XDG_CURRENT_DESKTOP": "GNOME",
            "DBUS_SESSION_BUS_ADDRESS": "unix:path=/tmp/fake-session-bus",
        },
        sys_platform_name="linux",
        fetch_gnome_helper_health=_healthy_gnome_helper_payload,
    )

    assert status.selected_backend.family is BackendFamily.COMPOSITOR_HELPER
    assert status.selected_backend.instance is BackendInstance.GNOME_SHELL_WAYLAND
    assert status.classification is CapabilityClassification.DEGRADED_OVERLAY
    assert status.fallback_reason is None
    assert status.helper_states[0].available is True
    assert status.helper_states[0].version == "1.0.0"
    assert status.helper_states[0].detail == "health_state=healthy"
    assert "helper_health:healthy" in status.notes


def test_client_backend_status_keeps_gnome_helper_missing_when_dbus_service_is_missing():
    context = PlatformContext(session_type="wayland", compositor="gnome-shell")

    def missing_helper() -> object:
        raise HelperDbusServiceMissing("missing helper service")

    status = _client_backend_status(
        context,
        source=ProbeSource.RUNTIME_UPDATE,
        qt_platform_name="wayland",
        env={
            "XDG_SESSION_TYPE": "wayland",
            "XDG_CURRENT_DESKTOP": "GNOME",
            "DBUS_SESSION_BUS_ADDRESS": "unix:path=/tmp/fake-session-bus",
        },
        sys_platform_name="linux",
        fetch_gnome_helper_health=missing_helper,
    )

    assert status.selected_backend.family is BackendFamily.NATIVE_WAYLAND
    assert status.selected_backend.instance is BackendInstance.GNOME_SHELL_WAYLAND
    assert status.classification is CapabilityClassification.DEGRADED_OVERLAY
    assert status.fallback_reason is not None
    assert status.fallback_reason.value == "missing_helper"
    assert status.helper_states[0].available is False
    assert status.helper_states[0].detail == "health_state=missing_service"
    assert "helper_health:missing_service" in status.notes


def test_gdbus_health_fetch_uses_runtime_bus_address_when_env_missing(monkeypatch, tmp_path):
    captured = {}

    class _Result:
        returncode = 0
        stdout = "('{\"status\":\"healthy\"}',)\n"
        stderr = ""

    def fake_run(_command, **kwargs):
        captured.update(kwargs)
        return _Result()

    monkeypatch.delenv("DBUS_SESSION_BUS_ADDRESS", raising=False)
    monkeypatch.setattr(platform_context_module.subprocess, "run", fake_run)

    payload = platform_context_module._fetch_gnome_helper_health_via_gdbus(
        {"XDG_RUNTIME_DIR": str(tmp_path / "runtime")}
    )

    assert payload == "('{\"status\":\"healthy\"}',)"
    assert captured["env"]["XDG_RUNTIME_DIR"] == str(tmp_path / "runtime")
    assert captured["env"]["DBUS_SESSION_BUS_ADDRESS"] == f"unix:path={tmp_path / 'runtime'}/bus"


def test_client_backend_status_uses_plugin_hint_as_fallback_when_runtime_unknown():
    context = PlatformContext(session_type="wayland", compositor="kwin")

    status = _client_backend_status(
        context,
        source=ProbeSource.RUNTIME_UPDATE,
        qt_platform_name="wayland",
        env={},
        sys_platform_name="linux",
    )

    assert status.selected_backend.instance is BackendInstance.KWIN_WAYLAND
    assert status.shadow_mode is False


def test_backend_status_signature_handles_status_objects_and_payload_dicts():
    context = PlatformContext(session_type="wayland", compositor="kwin")
    status = _client_backend_status(
        context,
        source=ProbeSource.RUNTIME_UPDATE,
        qt_platform_name="wayland",
        env={"XDG_SESSION_TYPE": "wayland", "XDG_CURRENT_DESKTOP": "KDE"},
        sys_platform_name="linux",
    )

    assert _backend_status_signature(status) == (
        "native_wayland",
        "kwin_wayland",
        "true_overlay",
        "",
        False,
        "",
        "",
    )
    assert _backend_status_signature(status.to_payload()) == (
        "native_wayland",
        "kwin_wayland",
        "true_overlay",
        "",
        False,
        "",
        "",
    )


def test_client_backend_status_applies_manual_override_from_context():
    context = PlatformContext(
        session_type="wayland",
        compositor="kwin",
        manual_backend_override="xwayland_compat",
    )

    status = _client_backend_status(
        context,
        source=ProbeSource.RUNTIME_UPDATE,
        qt_platform_name="wayland",
        env={"XDG_SESSION_TYPE": "wayland", "XDG_CURRENT_DESKTOP": "KDE"},
        sys_platform_name="linux",
    )

    assert status.selected_backend.instance is BackendInstance.XWAYLAND_COMPAT
    assert status.classification is CapabilityClassification.DEGRADED_OVERLAY
    assert status.manual_override is BackendInstance.XWAYLAND_COMPAT
    assert status.fallback_reason is not None
