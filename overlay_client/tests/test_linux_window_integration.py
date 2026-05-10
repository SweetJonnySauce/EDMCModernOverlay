import logging
from types import SimpleNamespace

from overlay_client.backend.bundles import _linux_window_integration


class _FakeWindow:
    def __init__(self):
        self.flags = []

    def setFlag(self, flag, enabled):
        self.flags.append((flag, bool(enabled)))


class _FakeWidget:
    def __init__(self, window):
        self._window = window

    def windowHandle(self):
        return self._window


class _HelperClient:
    def __init__(self, result: bool):
        self.result = result
        self.calls = []

    def set_overlay_input_passthrough(self, enabled: bool) -> bool:
        self.calls.append(bool(enabled))
        return self.result


def test_wayland_integration_uses_gnome_helper_for_click_through(monkeypatch):
    helper_client = _HelperClient(result=True)

    def _factory(_logger):
        return helper_client

    window = _FakeWindow()
    integration = _linux_window_integration._WaylandIntegration(
        _FakeWidget(window),
        logging.getLogger("test.linux_window_integration.gnome_helper"),
        SimpleNamespace(compositor="gnome-shell"),
    )
    native_calls = []
    monkeypatch.setattr(_linux_window_integration, "GnomeShellHelperControlClient", _factory)
    monkeypatch.setattr(integration, "_apply_native_transparency", lambda _window: native_calls.append(_window))

    integration.apply_click_through(True)
    integration.apply_click_through(False)

    assert helper_client.calls == [True, False]
    assert native_calls == []


def test_wayland_integration_falls_back_when_gnome_helper_control_is_unavailable(monkeypatch):
    helper_client = _HelperClient(result=False)

    def _factory(_logger):
        return helper_client

    window = _FakeWindow()
    integration = _linux_window_integration._WaylandIntegration(
        _FakeWidget(window),
        logging.getLogger("test.linux_window_integration.gnome_fallback"),
        SimpleNamespace(compositor="gnome-shell"),
    )
    native_calls = []
    monkeypatch.setattr(_linux_window_integration, "GnomeShellHelperControlClient", _factory)
    monkeypatch.setattr(integration, "_apply_native_transparency", lambda _window: native_calls.append(_window))

    integration.apply_click_through(True)
    integration.apply_click_through(False)

    assert helper_client.calls == [True, False]
    assert native_calls == [window]
