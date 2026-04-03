from overlay_client.backend import BackendInstance, ProbeSource
from overlay_client.platform_context import _backend_status_signature, _client_backend_status, _initial_platform_context
from overlay_client.platform_integration import PlatformContext


class _Initial:
    def __init__(self, force_xwayland: bool, manual_backend_override: str = "") -> None:
        self.force_xwayland = force_xwayland
        self.manual_backend_override = manual_backend_override


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
    assert ctx.manual_backend_override == ""


def test_initial_platform_context_respects_force(monkeypatch):
    monkeypatch.delenv("EDMC_OVERLAY_FORCE_XWAYLAND", raising=False)
    ctx = _initial_platform_context(_Initial(force_xwayland=True))
    assert ctx.force_xwayland is True


def test_initial_platform_context_carries_manual_backend_override(monkeypatch):
    monkeypatch.delenv("EDMC_OVERLAY_FORCE_XWAYLAND", raising=False)
    ctx = _initial_platform_context(_Initial(force_xwayland=False, manual_backend_override="xwayland_compat"))
    assert ctx.manual_backend_override == "xwayland_compat"


def test_client_backend_status_prefers_local_runtime_over_plugin_hint(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "GNOME")
    context = PlatformContext(session_type="x11", compositor="kwin", force_xwayland=False)

    status = _client_backend_status(
        context,
        source=ProbeSource.RUNTIME_UPDATE,
        qt_platform_name="wayland",
        env={"XDG_SESSION_TYPE": "wayland", "XDG_CURRENT_DESKTOP": "GNOME"},
        sys_platform_name="linux",
    )

    assert status.shadow_mode is False
    assert status.selected_backend.instance is BackendInstance.GNOME_SHELL_WAYLAND
    assert status.notes[0] == "client_selector_result"


def test_client_backend_status_uses_plugin_hint_as_fallback_when_runtime_unknown():
    context = PlatformContext(session_type="wayland", compositor="kwin", force_xwayland=False)

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
    context = PlatformContext(session_type="wayland", compositor="kwin", force_xwayland=False)
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
        force_xwayland=False,
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
    assert status.manual_override is BackendInstance.XWAYLAND_COMPAT
    assert status.fallback_reason is not None
