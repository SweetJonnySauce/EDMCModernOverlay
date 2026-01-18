from __future__ import annotations

from overlay_plugin.toggle_helpers import toggle_payload_opacity


class _StubPrefs:
    def __init__(self, *, opacity: int, last_on: int | None = None) -> None:
        self.global_payload_opacity = opacity
        if last_on is not None:
            self.last_on_payload_opacity = last_on


def test_toggle_from_on_sets_zero_and_tracks_last_on() -> None:
    prefs = _StubPrefs(opacity=42)

    new_value = toggle_payload_opacity(prefs)

    assert new_value == 0
    assert prefs.global_payload_opacity == 0
    assert prefs.last_on_payload_opacity == 42


def test_toggle_from_off_restores_last_on() -> None:
    prefs = _StubPrefs(opacity=0, last_on=75)

    new_value = toggle_payload_opacity(prefs)

    assert new_value == 75
    assert prefs.global_payload_opacity == 75
    assert prefs.last_on_payload_opacity == 75


def test_toggle_from_off_defaults_to_100_when_last_on_invalid() -> None:
    prefs = _StubPrefs(opacity=0, last_on=0)

    new_value = toggle_payload_opacity(prefs)

    assert new_value == 100
    assert prefs.global_payload_opacity == 100
    assert prefs.last_on_payload_opacity == 100
