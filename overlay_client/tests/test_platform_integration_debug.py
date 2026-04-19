from __future__ import annotations

import logging
import types

from PyQt6.QtCore import Qt

from overlay_client.platform_integration import PlatformContext, _IntegrationBase, _exstyle_flag_names, _style_flag_names


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


def test_base_integration_skips_qt_transparent_input_when_debug_toggle_enabled() -> None:
    window = types.SimpleNamespace(flags_set=[])
    window.setFlag = lambda flag, enabled: window.flags_set.append((flag, enabled))
    widget = types.SimpleNamespace(windowHandle=lambda: window)
    integration = _IntegrationBase(
        widget,
        logging.getLogger("test"),
        PlatformContext(),
        disable_qt_window_transparent_input=True,
    )

    integration.apply_click_through(True)

    assert window.flags_set == []


def test_base_integration_sets_qt_transparent_input_when_enabled() -> None:
    window = types.SimpleNamespace(flags_set=[])
    window.setFlag = lambda flag, enabled: window.flags_set.append((flag, enabled))
    widget = types.SimpleNamespace(windowHandle=lambda: window)
    integration = _IntegrationBase(widget, logging.getLogger("test"), PlatformContext())

    integration.apply_click_through(True)

    assert window.flags_set == [(Qt.WindowType.WindowTransparentForInput, True)]
