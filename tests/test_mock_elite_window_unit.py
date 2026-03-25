from __future__ import annotations

import json
from pathlib import Path

import pytest

from utils.mock_elite_window import _load_settings, _parse_size_token


def test_parse_size_token_accepts_expected_formats() -> None:
    assert _parse_size_token("1920x1080") == (1920, 1080)
    assert _parse_size_token("2560X1440") == (2560, 1440)
    assert _parse_size_token("800 600") == (800, 600)


@pytest.mark.parametrize("token", ["", "abc", "1920", "0x1080", "-1x1080"])
def test_parse_size_token_rejects_invalid_tokens(token: str) -> None:
    with pytest.raises(ValueError):
        _parse_size_token(token)


def test_load_settings_reads_width_height_and_scale_mode(tmp_path: Path) -> None:
    settings_path = tmp_path / "overlay_settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "mock_window_width": 1600,
                "mock_window_height": 900,
                "scale_mode": " FIT ",
            }
        ),
        encoding="utf-8",
    )
    width, height, scale_mode = _load_settings(str(settings_path))
    assert width == 1600
    assert height == 900
    assert scale_mode == "fit"


def test_load_settings_handles_missing_or_invalid_files(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.json"
    assert _load_settings(str(missing_path)) == (None, None, None)

    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text("{broken", encoding="utf-8")
    assert _load_settings(str(invalid_json)) == (None, None, None)

    invalid_values = tmp_path / "bad_values.json"
    invalid_values.write_text(
        json.dumps({"mock_window_width": "x", "mock_window_height": 900, "scale_mode": "fill"}),
        encoding="utf-8",
    )
    assert _load_settings(str(invalid_values)) == (None, None, None)
