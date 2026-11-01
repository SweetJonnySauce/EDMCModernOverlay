from overlay_client.platform_context import _initial_platform_context
from overlay_client import platform_integration
from overlay_client.platform_integration import PlatformContext, PlatformController, _XcbIntegration


class _Initial:
    def __init__(self, force_xwayland: bool, xwayland_on_wayland: bool = False) -> None:
        self.force_xwayland = force_xwayland
        self.xwayland_on_wayland = xwayland_on_wayland


def test_initial_platform_context_prefers_env(monkeypatch):
    monkeypatch.setenv("EDMC_OVERLAY_FORCE_XWAYLAND", "0")
    monkeypatch.setenv("EDMC_OVERLAY_SESSION_TYPE", "wayland")
    monkeypatch.setenv("EDMC_OVERLAY_COMPOSITOR", "kwin")
    monkeypatch.setenv("EDMC_OVERLAY_IS_FLATPAK", "1")
    monkeypatch.setenv("EDMC_OVERLAY_FLATPAK_ID", "app.id")

    ctx = _initial_platform_context(_Initial(force_xwayland=False))
    assert ctx.session_type == "wayland"
    assert ctx.compositor == "kwin"
    assert ctx.flatpak is True
    assert ctx.flatpak_app == "app.id"
    assert ctx.force_xwayland is False


def test_initial_platform_context_respects_force(monkeypatch):
    monkeypatch.delenv("EDMC_OVERLAY_FORCE_XWAYLAND", raising=False)
    ctx = _initial_platform_context(_Initial(force_xwayland=True))
    assert ctx.force_xwayland is True


def test_initial_platform_context_selects_xwayland_only_for_wayland(monkeypatch):
    monkeypatch.setenv("EDMC_OVERLAY_SESSION_TYPE", "wayland")
    monkeypatch.setenv("EDMC_OVERLAY_XWAYLAND_ON_WAYLAND", "1")

    ctx = _initial_platform_context(_Initial(force_xwayland=False))
    assert ctx.force_xwayland is False
    assert ctx.xwayland_on_wayland is True

    monkeypatch.setenv("EDMC_OVERLAY_SESSION_TYPE", "x11")
    ctx = _initial_platform_context(_Initial(force_xwayland=False, xwayland_on_wayland=True))
    assert ctx.xwayland_on_wayland is False


def test_xwayland_on_wayland_selects_xcb_integration(monkeypatch):
    monkeypatch.setattr(platform_integration.QGuiApplication, "platformName", lambda: "wayland")

    controller = PlatformController(
        object(),
        platform_integration.logging.getLogger("test.platform"),
        PlatformContext(session_type="wayland", compositor="gnome-shell", xwayland_on_wayland=True),
    )

    assert isinstance(controller._integration, _XcbIntegration)

    monkeypatch.setenv("EDMC_OVERLAY_SESSION_TYPE", "wayland")
    monkeypatch.setenv("EDMC_OVERLAY_XWAYLAND_ON_WAYLAND", "0")
    ctx = _initial_platform_context(_Initial(force_xwayland=False, xwayland_on_wayland=True))
    assert ctx.xwayland_on_wayland is False
