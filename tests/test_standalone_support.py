from __future__ import annotations

from types import SimpleNamespace

from overlay_plugin import standalone_support


def test_standalone_mode_preference_value_windows_only(monkeypatch):
    prefs = SimpleNamespace(standalone_mode=True)

    monkeypatch.setattr(standalone_support.sys, "platform", "linux")
    assert standalone_support.standalone_mode_preference_value(prefs) is False

    monkeypatch.setattr(standalone_support.sys, "platform", "win32")
    assert standalone_support.standalone_mode_preference_value(prefs) is True
