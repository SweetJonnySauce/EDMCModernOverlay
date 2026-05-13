from __future__ import annotations

from pathlib import Path


EXTENSION_SOURCE = Path(__file__).resolve().parents[2] / "helpers" / "gnome_shell_extension" / "extension.js"


def _source() -> str:
    return EXTENSION_SOURCE.read_text(encoding="utf-8")


def test_extension_uses_display_config_monitor_inventory_with_legacy_fallback() -> None:
    source = _source()

    assert "org.gnome.Mutter.DisplayConfig" in source
    assert "GetCurrentState" in source
    assert "_legacyMonitorForIndex" in source


def test_extension_skips_redundant_move_resize_when_frame_already_matches() -> None:
    source = _source()

    assert "const currentFrameRect = this._rectPayload(this._safeCall(window, 'get_frame_rect'))" in source
    assert "this._rectsMatchWithinTolerance(currentFrameRect, requestedRect, rectTolerance)" in source
    assert "} else if (typeof window?.move_resize_frame === 'function') {" in source
    assert "window.move_resize_frame(" in source
    assert "window.make_above()" in source


def test_extension_honors_request_rect_tolerance_for_move_resize_noop() -> None:
    source = _source()

    assert "const rectTolerance = this._requestInt(payload, 2, 'rect_tolerance', 'rectTolerance')" in source
    assert "_applyOverlayPresentation(overlayEntry.window, requestedRect, rectTolerance)" in source
    assert "_rectsMatchWithinTolerance(left, right, tolerance = 0)" in source
