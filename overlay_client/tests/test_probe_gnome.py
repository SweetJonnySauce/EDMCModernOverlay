import builtins
import sys
from types import SimpleNamespace

from overlay_client.backend import HelperKind, HelperProbeAvailability
from overlay_client.backend.probe_gnome import probe_gnome_shell_helper


def test_probe_gnome_shell_helper_reports_missing_host_python_gi(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "pydbus":
            raise ModuleNotFoundError("No module named 'gi'", name="gi")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    result = probe_gnome_shell_helper(session_type="wayland", compositor="gnome-shell")

    assert result is not None
    assert result.helper is HelperKind.GNOME_SHELL_EXTENSION
    assert result.availability is HelperProbeAvailability.MISSING
    assert result.detail == "host_prerequisite_missing:python3-gi"


def test_probe_gnome_shell_helper_reports_missing_service(monkeypatch):
    class _Bus:
        def get(self, _service_name, _object_path):
            raise RuntimeError("org.freedesktop.DBus.Error.ServiceUnknown")

    monkeypatch.setitem(sys.modules, "pydbus", SimpleNamespace(SessionBus=lambda: _Bus()))

    result = probe_gnome_shell_helper(session_type="wayland", compositor="gnome-shell")

    assert result is not None
    assert result.helper is HelperKind.GNOME_SHELL_EXTENSION
    assert result.availability is HelperProbeAvailability.MISSING
    assert result.detail == "service_unavailable"
