from __future__ import annotations

import types

from PyQt6.QtCore import Qt

from overlay_client.setup_surface import SetupSurfaceMixin


def test_set_window_flag_disables_tool_in_windows_debug_mode(monkeypatch) -> None:
    calls: list[tuple[Qt.WindowType, bool]] = []
    stub = types.SimpleNamespace(
        _standalone_mode=False,
        _debug_config=types.SimpleNamespace(disable_qt_tool=True),
        setWindowFlag=lambda flag, enabled: calls.append((flag, enabled)),
    )
    monkeypatch.setattr("overlay_client.setup_surface.sys.platform", "win32")

    SetupSurfaceMixin._set_window_flag(stub, Qt.WindowType.Tool, True)

    assert calls == [(Qt.WindowType.Tool, False)]


def test_set_window_flag_preserves_non_tool_flags(monkeypatch) -> None:
    calls: list[tuple[Qt.WindowType, bool]] = []
    stub = types.SimpleNamespace(
        _standalone_mode=False,
        _debug_config=types.SimpleNamespace(disable_qt_tool=True),
        setWindowFlag=lambda flag, enabled: calls.append((flag, enabled)),
    )
    monkeypatch.setattr("overlay_client.setup_surface.sys.platform", "win32")

    SetupSurfaceMixin._set_window_flag(stub, Qt.WindowType.WindowStaysOnTopHint, True)

    assert calls == [(Qt.WindowType.WindowStaysOnTopHint, True)]
