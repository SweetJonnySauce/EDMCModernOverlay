from __future__ import annotations

from overlay_client.platform_integration import _exstyle_flag_names, _style_flag_names


def test_style_flag_names_decode_common_window_bits() -> None:
    style = 0x10000000 | 0x80000000 | 0x00C00000

    names = _style_flag_names(style)

    assert "WS_VISIBLE" in names
    assert "WS_POPUP" in names
    assert "WS_CAPTION" in names


def test_exstyle_flag_names_decode_common_extended_bits() -> None:
    exstyle = 0x00080000 | 0x00000020 | 0x00000080

    names = _exstyle_flag_names(exstyle)

    assert "WS_EX_LAYERED" in names
    assert "WS_EX_TRANSPARENT" in names
    assert "WS_EX_TOOLWINDOW" in names
