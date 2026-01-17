from __future__ import annotations

from types import SimpleNamespace

from overlay_plugin import obs_capture_support as obs_support


def test_obs_capture_preference_value_windows_only(monkeypatch):
    prefs = SimpleNamespace(obs_capture_friendly=True)

    monkeypatch.setattr(obs_support.sys, "platform", "linux")
    assert obs_support.obs_capture_preference_value(prefs) is False

    monkeypatch.setattr(obs_support.sys, "platform", "win32")
    assert obs_support.obs_capture_preference_value(prefs) is True
