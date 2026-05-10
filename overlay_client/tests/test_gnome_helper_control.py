import logging

from overlay_client.backend.gnome_helper_control import GnomeShellHelperControlClient
from overlay_client.backend.helper_ipc import (
    GNOME_SHELL_HELPER_OBJECT_PATH,
    GNOME_SHELL_HELPER_SERVICE_NAME,
)


class _Proxy:
    def __init__(self, *, result=True, exc: Exception | None = None):
        self.calls = []
        self._result = result
        self._exc = exc

    def SetOverlayInputPassthrough(self, enabled: bool):
        self.calls.append(bool(enabled))
        if self._exc is not None:
            raise self._exc
        return self._result


class _Bus:
    def __init__(self, proxy):
        self._proxy = proxy
        self.calls = []

    def get(self, service_name, object_path):
        self.calls.append((service_name, object_path))
        return self._proxy


def _logger():
    return logging.getLogger("test.gnome_helper_control")


def test_gnome_helper_control_calls_helper_method_and_returns_result():
    proxy = _Proxy(result=True)
    bus = _Bus(proxy)
    client = GnomeShellHelperControlClient(logger=_logger(), bus_factory=lambda: bus)

    applied = client.set_overlay_input_passthrough(True)

    assert applied is True
    assert bus.calls == [(GNOME_SHELL_HELPER_SERVICE_NAME, GNOME_SHELL_HELPER_OBJECT_PATH)]
    assert proxy.calls == [True]
    assert client.last_error is None


def test_gnome_helper_control_fails_soft_when_helper_call_raises():
    proxy = _Proxy(exc=RuntimeError("service unavailable"))
    bus = _Bus(proxy)
    client = GnomeShellHelperControlClient(logger=_logger(), bus_factory=lambda: bus)

    applied = client.set_overlay_input_passthrough(False)

    assert applied is False
    assert proxy.calls == [False]
    assert isinstance(client.last_error, RuntimeError)
