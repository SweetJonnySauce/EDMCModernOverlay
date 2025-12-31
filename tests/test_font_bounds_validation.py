from __future__ import annotations

from overlay_plugin import preferences as prefs


def test_apply_font_bounds_edit_accepts_valid_min() -> None:
    current_min = 6.0
    current_max = 12.0

    new_min, new_max, accepted = prefs._apply_font_bounds_edit(current_min, current_max, "min", 8.0)

    assert accepted is True
    assert new_min == 8.0
    assert new_max == current_max


def test_apply_font_bounds_edit_rejects_min_above_max() -> None:
    current_min = 6.0
    current_max = 12.0

    new_min, new_max, accepted = prefs._apply_font_bounds_edit(current_min, current_max, "min", 20.0)

    assert accepted is False
    assert new_min == current_min
    assert new_max == current_max


def test_apply_font_bounds_edit_rejects_max_below_min() -> None:
    current_min = 6.0
    current_max = 12.0

    new_min, new_max, accepted = prefs._apply_font_bounds_edit(current_min, current_max, "max", 4.0)

    assert accepted is False
    assert new_min == current_min
    assert new_max == current_max


def test_apply_font_bounds_edit_rejects_out_of_range() -> None:
    current_min = 6.0
    current_max = 12.0

    new_min, new_max, accepted = prefs._apply_font_bounds_edit(current_min, current_max, "max", 33.0)

    assert accepted is False
    assert new_min == current_min
    assert new_max == current_max


def test_apply_font_step_edit_accepts_valid_value() -> None:
    step, accepted = prefs._apply_font_step_edit(2, 4)

    assert accepted is True
    assert step == 4


def test_apply_font_step_edit_rejects_invalid_value() -> None:
    step, accepted = prefs._apply_font_step_edit(2, 11)

    assert accepted is False
    assert step == 2
