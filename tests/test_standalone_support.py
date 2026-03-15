from __future__ import annotations

from types import SimpleNamespace

from overlay_plugin import standalone_support


def test_standalone_mode_preference_value_cross_platform():
    prefs = SimpleNamespace(standalone_mode=True)

    assert standalone_support.standalone_mode_preference_value(prefs) is True

    prefs.standalone_mode = False
    assert standalone_support.standalone_mode_preference_value(prefs) is False
