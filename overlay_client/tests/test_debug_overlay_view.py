from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import Any

import pytest

OVERLAY_ROOT = __file__.rsplit("/overlay_client/tests/", 1)[0]
if OVERLAY_ROOT not in sys.path:
    sys.path.append(OVERLAY_ROOT)

try:
    from PyQt6.QtCore import QRect
except Exception:  # pragma: no cover - import guard
    pytest.skip("PyQt6 not available", allow_module_level=True)

from overlay_client.debug_cycle_overlay import DebugOverlayView  # noqa: E402
from overlay_client.viewport_helper import ScaleMode, compute_viewport_transform  # noqa: E402
from overlay_client.viewport_transform import LegacyMapper, ViewportState  # noqa: E402


class _FakeFontMetrics:
    def height(self) -> int:
        return 10

    def ascent(self) -> int:
        return 8

    def horizontalAdvance(self, text: str) -> int:
        return max(1, len(text)) * 6


class _FakePainter:
    def __init__(self) -> None:
        self.texts: list[str] = []

    def save(self) -> None:
        return None

    def restore(self) -> None:
        return None

    def setPen(self, *_: Any, **__: Any) -> None:
        return None

    def setBrush(self, *_: Any, **__: Any) -> None:
        return None

    def setFont(self, *_: Any, **__: Any) -> None:
        return None

    def fontMetrics(self) -> _FakeFontMetrics:
        return _FakeFontMetrics()

    def drawRoundedRect(self, *_: Any, **__: Any) -> None:
        return None

    def drawText(self, *_: Any, **__: Any) -> None:
        if _:
            self.texts.append(str(_[-1]))


def test_debug_overlay_includes_backend_choice_and_source() -> None:
    transform = compute_viewport_transform(400, 300, ScaleMode.FIT)
    mapper = LegacyMapper(
        scale_x=transform.scale,
        scale_y=transform.scale,
        offset_x=transform.offset[0],
        offset_y=transform.offset[1],
        transform=transform,
    )
    painter = _FakePainter()
    view = DebugOverlayView(lambda _font: None, lambda _key: 1)

    view.paint_debug_overlay(
        painter,
        show_debug_overlay=True,
        frame_geometry=QRect(0, 0, 400, 300),
        width_px=400.0,
        height_px=300.0,
        mapper=mapper,
        viewport_state=ViewportState(width=400.0, height=300.0, device_ratio=1.0),
        font_family="TestFont",
        font_scale_diag=1.0,
        font_min_point=8.0,
        font_max_point=18.0,
        debug_message_pt=12.0,
        debug_status_pt=10.0,
        debug_legacy_pt=11.0,
        aspect_ratio_label_fn=lambda _w, _h: None,
        last_screen_name=None,
        describe_screen_fn=lambda _screen: "screen",
        active_screen=None,
        last_follow_state=None,
        follow_controller=SimpleNamespace(wm_override=None, wm_override_classification=None),
        last_raw_window_log=None,
        title_bar_enabled=False,
        title_bar_height=0,
        last_title_bar_offset=0,
        backend_status={
            "selected_backend": {"family": "native_wayland", "instance": "kwin_wayland"},
            "classification": "true_overlay",
            "shadow_mode": False,
            "helper_states": [],
            "review_required": False,
            "review_reasons": [],
        },
        debug_overlay_corner="SW",
        legacy_preset_point_size_fn=lambda _name, _state, _mapper: 12.0,
    )

    assert "Backend:" in painter.texts
    assert "  choice=native_wayland / kwin_wayland" in painter.texts
    assert "  source=client_runtime" in painter.texts
    assert "  mode=true_overlay" in painter.texts
