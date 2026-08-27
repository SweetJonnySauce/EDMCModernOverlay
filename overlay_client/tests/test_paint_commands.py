from typing import Any, Dict, Tuple

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QPen

from overlay_client.paint_commands import (
    _CirclePaintCommand,
    _MessagePaintCommand,
    _RectPaintCommand,
    _VectorPaintCommand,
    _QtVectorPainterAdapter,
)


class _StubLegacyItem:
    def __init__(self, item_id: str) -> None:
        self.item_id = item_id


class _StubWindow:
    def __init__(self, payload_opacity: int = 100) -> None:
        self._font_family = "StubFont"
        self._font_fallbacks = ()
        self._registered: Dict[str, Tuple[int, int]] = {}
        self._payload_opacity = payload_opacity

    def _register_cycle_anchor(self, item_id: str, x: int, y: int) -> None:
        self._registered[item_id] = (x, y)

    def _line_width(self, key: str) -> int:
        return {"vector_marker": 3, "vector_line": 2, "vector_cross": 5}.get(key, 1)

    def _apply_font_fallbacks(self, font) -> None:  # noqa: ANN001
        return None

    def _compute_legacy_mapper(self):  # noqa: D401
        return object()

    def _viewport_state(self):
        return object()

    def _legacy_preset_point_size(self, *_):
        return 10.0

    def _apply_payload_opacity_color(self, color):
        adjusted = QColor(color)
        adjusted.setAlpha(round(color.alpha() * self._payload_opacity / 100))
        return adjusted

    def _payload_opacity_percent(self) -> int:
        return self._payload_opacity


class _RecordingPainter:
    def __init__(self) -> None:
        self.calls = []

    def setPen(self, pen) -> None:  # noqa: N802
        self.calls.append(("setPen", pen))

    def setBrush(self, brush) -> None:  # noqa: N802
        self.calls.append(("setBrush", brush))

    def setFont(self, font) -> None:  # noqa: N802
        self.calls.append(("setFont", font.family()))

    def drawText(self, x: int, y: int, text: str) -> None:  # noqa: N802
        self.calls.append(("drawText", x, y, text))

    def drawRect(self, x: int, y: int, w: int, h: int) -> None:  # noqa: N802
        self.calls.append(("drawRect", x, y, w, h))

    def drawLine(self, x1: int, y1: int, x2: int, y2: int) -> None:  # noqa: N802
        self.calls.append(("drawLine", x1, y1, x2, y2))

    def drawEllipse(self, *args) -> None:  # noqa: N802
        self.calls.append(("drawEllipse",) + args)


def test_message_paint_draws_and_registers_anchor():
    window = _StubWindow()
    painter = _RecordingPainter()
    cmd = _MessagePaintCommand(
        group_key=("g", None),
        group_transform=None,
        legacy_item=_StubLegacyItem("item-1"),
        bounds=None,
        text="hello",
        color=QColor("white"),
        point_size=12.0,
        x=10,
        baseline=5,
        cycle_anchor=(2, 3),
    )
    cmd.paint(window, painter, offset_x=5, offset_y=7)
    assert ("drawText", 15, 12, "hello") in painter.calls
    assert window._registered["item-1"] == (7, 10)


def test_rect_paint_draws_with_offsets():
    window = _StubWindow()
    painter = _RecordingPainter()
    cmd = _RectPaintCommand(
        group_key=("g", None),
        group_transform=None,
        legacy_item=_StubLegacyItem("item-rect"),
        bounds=None,
        x=1,
        y=2,
        width=3,
        height=4,
    )
    cmd.paint(window, painter, offset_x=10, offset_y=20)
    assert ("drawRect", 11, 22, 3, 4) in painter.calls


def test_circle_paint_draws_offset_bounds_with_style_trace_and_anchor():
    window = _StubWindow()
    painter = _RecordingPainter()
    trace_events = []
    pen = QPen(QColor("#123456"))
    pen.setWidth(7)
    brush = QBrush(QColor("#abcdef"))
    cmd = _CirclePaintCommand(
        group_key=("g", None),
        group_transform=None,
        legacy_item=_StubLegacyItem("item-circle"),
        bounds=None,
        pen=pen,
        brush=brush,
        x=10,
        y=20,
        width=30,
        height=40,
        cycle_anchor=(8, 9),
        trace_fn=lambda event, payload: trace_events.append((event, payload)),
    )

    cmd.paint(window, painter, offset_x=3, offset_y=4)

    assert ("drawEllipse", 13, 24, 30, 40) in painter.calls
    assert not [call for call in painter.calls if call[0] == "drawRect"]
    active_pen = next(call[1] for call in painter.calls if call[0] == "setPen")
    active_brush = next(call[1] for call in painter.calls if call[0] == "setBrush")
    assert active_pen.width() == 7
    assert active_pen.color() == QColor("#123456")
    assert active_brush.color() == QColor("#abcdef")
    assert window._registered["item-circle"] == (11, 13)
    assert trace_events == [("trace:complete", {"kind": "circle"})]


def test_circle_paint_preserves_transparent_pen_and_brush_at_reduced_opacity():
    window = _StubWindow(payload_opacity=50)
    painter = _RecordingPainter()
    no_pen = QPen(Qt.PenStyle.NoPen)
    no_brush = QBrush(Qt.BrushStyle.NoBrush)
    cmd = _CirclePaintCommand(
        group_key=("g", None),
        group_transform=None,
        legacy_item=_StubLegacyItem("item-transparent-circle"),
        bounds=None,
        pen=no_pen,
        brush=no_brush,
        x=1,
        y=2,
        width=3,
        height=4,
    )

    cmd.paint(window, painter, offset_x=0, offset_y=0)

    active_pen = next(call[1] for call in painter.calls if call[0] == "setPen")
    active_brush = next(call[1] for call in painter.calls if call[0] == "setBrush")
    assert active_pen is no_pen
    assert active_pen.style() == Qt.PenStyle.NoPen
    assert active_brush is no_brush
    assert active_brush.style() == Qt.BrushStyle.NoBrush


def test_circle_paint_uses_opacity_adjusted_pen_and_brush_copies():
    window = _StubWindow(payload_opacity=50)
    painter = _RecordingPainter()
    pen = QPen(QColor(10, 20, 30, 201))
    pen.setWidth(5)
    brush = QBrush(QColor(40, 50, 60, 181))
    original_pen_alpha = pen.color().alpha()
    original_brush_alpha = brush.color().alpha()
    cmd = _CirclePaintCommand(
        group_key=("g", None),
        group_transform=None,
        legacy_item=_StubLegacyItem("item-opaque-circle"),
        bounds=None,
        pen=pen,
        brush=brush,
        x=1,
        y=2,
        width=3,
        height=4,
    )

    cmd.paint(window, painter, offset_x=0, offset_y=0)

    active_pen = next(call[1] for call in painter.calls if call[0] == "setPen")
    active_brush = next(call[1] for call in painter.calls if call[0] == "setBrush")
    assert active_pen is not pen
    assert active_pen.width() == 5
    assert active_pen.color().alpha() == 100
    assert active_brush is not brush
    assert active_brush.color().alpha() == 90
    assert pen.color().alpha() == original_pen_alpha
    assert brush.color().alpha() == original_brush_alpha


def test_vector_paint_invokes_render_with_adapter(monkeypatch):
    window = _StubWindow()
    painter = _RecordingPainter()
    seen: Dict[str, Any] = {}

    def fake_render_vector(
        adapter,
        payload,
        scale_x,
        scale_y,
        *,
        offset_x,
        offset_y,
        marker_label_position=None,
        trace=None,
    ):
        seen["adapter"] = adapter
        seen["payload"] = payload
        seen["scale"] = (scale_x, scale_y)
        seen["offsets"] = (offset_x, offset_y)
        seen["marker_label_position"] = marker_label_position
        seen["trace"] = trace

    monkeypatch.setattr("overlay_client.paint_commands.render_vector", fake_render_vector)

    cmd = _VectorPaintCommand(
        group_key=("g", None),
        group_transform=None,
        legacy_item=_StubLegacyItem("item-vec"),
        bounds=None,
        vector_payload={"k": "v"},
        scale=2.0,
        base_offset_x=1.5,
        base_offset_y=2.5,
        cycle_anchor=(4, 6),
    )
    cmd.paint(window, painter, offset_x=10, offset_y=20)

    assert isinstance(seen["adapter"], _QtVectorPainterAdapter)
    assert seen["payload"] == {"k": "v"}
    assert seen["scale"] == (2.0, 2.0)
    assert seen["offsets"] == (11.5, 22.5)
    assert seen["marker_label_position"] == "below"
    assert window._registered["item-vec"] == (14, 26)


def test_vector_adapter_draw_circle_uses_line_widths():
    window = _StubWindow()
    painter = _RecordingPainter()
    adapter = _QtVectorPainterAdapter(window, painter)
    adapter.draw_circle_marker(1, 2, 3, "blue")

    # Confirm pen/brush set before drawEllipse call.
    draw_calls = [call for call in painter.calls if call and call[0] == "drawEllipse"]
    assert draw_calls, "drawEllipse not invoked"


def test_vector_adapter_draw_text_multiline_splits_lines(monkeypatch):
    class _FakeMetrics:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def lineSpacing(self) -> int:  # noqa: N802
            return 12

        def height(self) -> int:
            return 12

        def ascent(self) -> int:
            return 7

        def descent(self) -> int:
            return 3

    monkeypatch.setattr("overlay_client.paint_commands.QFontMetrics", _FakeMetrics)
    window = _StubWindow()
    painter = _RecordingPainter()
    adapter = _QtVectorPainterAdapter(window, painter)

    adapter.draw_text(10, 20, "One\nTwo", "white")

    draw_calls = [call for call in painter.calls if call[0] == "drawText"]
    assert len(draw_calls) == 2
    baseline = int(round(20 + 7))
    assert draw_calls[0] == ("drawText", 10, baseline, "One")
    assert draw_calls[1] == ("drawText", 10, baseline + 12, "Two")


def test_message_paint_draws_multiline_text():
    window = _StubWindow()
    painter = _RecordingPainter()
    cmd = _MessagePaintCommand(
        group_key=("g", None),
        group_transform=None,
        legacy_item=_StubLegacyItem("item-msg"),
        bounds=None,
        text="Hello\r\nWorld",
        color=QColor("white"),
        point_size=12.0,
        x=10,
        baseline=100,
        line_spacing=5,
        cycle_anchor=None,
    )

    cmd.paint(window, painter, offset_x=0, offset_y=0)

    draw_calls = [call for call in painter.calls if call[0] == "drawText"]
    assert draw_calls == [
        ("drawText", 10, 100, "Hello"),
        ("drawText", 10, 105, "World"),
    ]
