from __future__ import annotations

from overlay_plugin import preferences as prefs


def test_toggle_argument_trims_whitespace() -> None:
    value, error = prefs._validate_toggle_argument(" t ", default="t", previous="x")

    assert value == "t"
    assert error is None


def test_toggle_argument_empty_falls_back_to_default() -> None:
    value, error = prefs._validate_toggle_argument("   ", default="t", previous="x")

    assert value == "t"
    assert error is None


def test_toggle_argument_rejects_non_alphanumeric() -> None:
    value, error = prefs._validate_toggle_argument("t!", default="t", previous="x")

    assert value == "x"
    assert error is not None


def test_toggle_argument_rejects_numeric_only() -> None:
    value, error = prefs._validate_toggle_argument("42", default="t", previous="x")

    assert value == "x"
    assert error is not None


def test_toggle_argument_accepts_mixed_alphanumeric() -> None:
    value, error = prefs._validate_toggle_argument("t5", default="t", previous="x")

    assert value == "t5"
    assert error is None


def test_coerce_toggle_argument_defaults_on_invalid() -> None:
    assert prefs._coerce_toggle_argument("t!", default="t") == "t"


def test_coerce_last_on_payload_opacity_defaults_when_invalid() -> None:
    assert prefs._coerce_last_on_payload_opacity(0, 100) == 100
