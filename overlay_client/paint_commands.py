"""Paint command types and Qt painter adapter for legacy rendering."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Mapping, Optional, Sequence, Tuple

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QColor, QBrush, QFont, QFontMetrics, QPainter, QPen

from overlay_client.group_transform import GroupTransform  # type: ignore
from overlay_client.grouping_adapter import GroupKey  # type: ignore
from overlay_client.legacy_store import LegacyItem  # type: ignore
from overlay_client.vector_renderer import render_vector, VectorPainterAdapter  # type: ignore

if TYPE_CHECKING:
    from overlay_client.overlay_client import OverlayWindow  # type: ignore


@dataclass
class _LegacyPaintCommand:
    group_key: GroupKey
    group_transform: Optional[GroupTransform]
    legacy_item: LegacyItem
    bounds: Optional[Tuple[int, int, int, int]]
    overlay_bounds: Optional[Tuple[float, float, float, float]] = None
    effective_anchor: Optional[Tuple[float, float]] = None
    debug_log: Optional[str] = None
    justification_dx: float = 0.0
    base_overlay_bounds: Optional[Tuple[float, float, float, float]] = None
    reference_overlay_bounds: Optional[Tuple[float, float, float, float]] = None
    debug_vertices: Optional[Sequence[Tuple[int, int]]] = None
    raw_min_x: Optional[float] = None
    right_just_multiplier: int = 0

    def paint(self, window: "OverlayWindow", painter: QPainter, offset_x: int, offset_y: int) -> None:
        raise NotImplementedError


@dataclass
class _MessagePaintCommand(_LegacyPaintCommand):
    text: str = ""
    color: QColor = field(default_factory=lambda: QColor("white"))
    point_size: float = 12.0
    x: int = 0
    baseline: int = 0
    text_width: int = 0
    ascent: int = 0
    descent: int = 0
    line_spacing: int = 0
    cycle_anchor: Optional[Tuple[int, int]] = None
    trace_fn: Optional[Callable[[str, Mapping[str, Any]], None]] = None

    def paint(self, window: "OverlayWindow", painter: QPainter, offset_x: int, offset_y: int) -> None:
        font = QFont(window._font_family)
        window._apply_font_fallbacks(font)
        font.setPointSizeF(self.point_size)
        font.setWeight(QFont.Weight.Normal)
        painter.setFont(font)
        painter.setPen(window._apply_payload_opacity_color(self.color))
        draw_x = int(round(self.x + offset_x))
        draw_baseline = int(round(self.baseline + offset_y))
        normalised = str(self.text).replace("\r\n", "\n").replace("\r", "\n")
        lines = normalised.split("\n") or [""]
        line_spacing = self.line_spacing or (self.ascent + self.descent)
        if line_spacing <= 0:
            line_spacing = 0
        for idx, line in enumerate(lines):
            painter.drawText(draw_x, draw_baseline + (line_spacing * idx), line)
        if self.trace_fn:
            self.trace_fn(
                "render_message:draw",
                {
                    "pixel_x": draw_x,
                    "baseline": draw_baseline,
                    "text_width": self.text_width,
                    "font_size": self.point_size,
                    "color": self.color.name(),
                },
            )
            self.trace_fn("trace:complete", {"kind": "message"})
        if self.cycle_anchor:
            anchor_x = int(round(self.cycle_anchor[0] + offset_x))
            anchor_y = int(round(self.cycle_anchor[1] + offset_y))
            window._register_cycle_anchor(self.legacy_item.item_id, anchor_x, anchor_y)


@dataclass
class _RectPaintCommand(_LegacyPaintCommand):
    pen: QPen = field(default_factory=lambda: QPen(Qt.PenStyle.NoPen))
    brush: QBrush = field(default_factory=lambda: QBrush(Qt.BrushStyle.NoBrush))
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    cycle_anchor: Optional[Tuple[int, int]] = None
    trace_fn: Optional[Callable[[str, Mapping[str, Any]], None]] = None

    def paint(self, window: "OverlayWindow", painter: QPainter, offset_x: int, offset_y: int) -> None:
        pen = self.pen
        brush = self.brush
        if window._payload_opacity_percent() < 100:
            if pen.style() != Qt.PenStyle.NoPen:
                pen = QPen(pen)
                pen.setColor(window._apply_payload_opacity_color(pen.color()))
            if brush.style() != Qt.BrushStyle.NoBrush:
                brush = QBrush(brush)
                brush.setColor(window._apply_payload_opacity_color(brush.color()))
        painter.setPen(pen)
        painter.setBrush(brush)
        draw_x = int(round(self.x + offset_x))
        draw_y = int(round(self.y + offset_y))
        painter.drawRect(draw_x, draw_y, self.width, self.height)
        if self.trace_fn:
            self.trace_fn("trace:complete", {"kind": "rect"})
        if self.cycle_anchor:
            anchor_x = int(round(self.cycle_anchor[0] + offset_x))
            anchor_y = int(round(self.cycle_anchor[1] + offset_y))
            window._register_cycle_anchor(self.legacy_item.item_id, anchor_x, anchor_y)


@dataclass
class _CirclePaintCommand(_LegacyPaintCommand):
    pen: QPen = field(default_factory=lambda: QPen(Qt.PenStyle.NoPen))
    brush: QBrush = field(default_factory=lambda: QBrush(Qt.BrushStyle.NoBrush))
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    cycle_anchor: Optional[Tuple[int, int]] = None
    trace_fn: Optional[Callable[[str, Mapping[str, Any]], None]] = None

    def paint(self, window: "OverlayWindow", painter: QPainter, offset_x: int, offset_y: int) -> None:
        pen = self.pen
        brush = self.brush
        if window._payload_opacity_percent() < 100:
            if pen.style() != Qt.PenStyle.NoPen:
                pen = QPen(pen)
                pen.setColor(window._apply_payload_opacity_color(pen.color()))
            if brush.style() != Qt.BrushStyle.NoBrush:
                brush = QBrush(brush)
                brush.setColor(window._apply_payload_opacity_color(brush.color()))
        painter.setPen(pen)
        painter.setBrush(brush)
        draw_x = int(round(self.x + offset_x))
        draw_y = int(round(self.y + offset_y))
        painter.drawEllipse(draw_x, draw_y, self.width, self.height)
        if self.trace_fn:
            self.trace_fn("trace:complete", {"kind": "circle"})
        if self.cycle_anchor:
            anchor_x = int(round(self.cycle_anchor[0] + offset_x))
            anchor_y = int(round(self.cycle_anchor[1] + offset_y))
            window._register_cycle_anchor(self.legacy_item.item_id, anchor_x, anchor_y)

@dataclass
class _TablePaintCommand(_LegacyPaintCommand):
    """Paint a proportional-font table using measured pixel widths.

    Column positions are calculated from the actual QFontMetrics used by the
    overlay. This means alignment does not depend on character count.
    """

    rows: Sequence[Sequence[str]] = field(default_factory=list)
    x: int = 0
    y: int = 0
    point_size: float = 12.0
    column_widths: Sequence[float] = field(default_factory=list)
    column_alignments: Sequence[str] = field(default_factory=list)
    row_colors: Sequence[QColor] = field(default_factory=list)
    row_backgrounds: Sequence[QColor] = field(default_factory=list)
    header_color: QColor = field(default_factory=lambda: QColor("white"))
    header_background: Optional[QColor] = None
    background: Optional[QColor] = None
    padding: float = 6.0
    row_height: float = 14.0
    header: bool = True
    header_bold: bool = False
    font_family: str = ""
    scale: float = 1.0
    font_fallbacks: Sequence[str] = field(default_factory=tuple)
    trace_fn: Optional[Callable[[str, Mapping[str, Any]], None]] = None

    def paint(
        self,
        window: "OverlayWindow",
        painter: QPainter,
        offset_x: int,
        offset_y: int,
    ) -> None:
        # Configure the font.
        font = QFont(self.font_family or window._font_family)
        window._apply_font_fallbacks(font)
        font.setPointSizeF(self.point_size)

        # Calculate the drawing position and scale.
        draw_x = int(round(self.x + offset_x))
        draw_y = int(round(self.y + offset_y))
        scale = max(float(self.scale), 1e-6)

        # Convert overlay units to pixels.
        widths_px = [
            max(0, int(round(width * scale)))
            for width in self.column_widths
        ]
        padding_px = max(0, int(round(self.padding * scale)))
        row_height_px = max(
            1,
            int(round(self.row_height * scale)),
        )

        total_width = sum(widths_px)
        total_height = row_height_px * len(self.rows)

        # Draw the overall table background, if configured.
        if (
            self.background is not None
            and total_width > 0
            and total_height > 0
        ):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(
                QBrush(
                    window._apply_payload_opacity_color(self.background)
                )
            )
            painter.drawRect(
                draw_x,
                draw_y,
                total_width,
                total_height,
            )

        current_y = draw_y

        for row_index, row in enumerate(self.rows):
            # Determine whether this is the header row.
            is_header = (
                self.header
                and row_index == 0
                and self.header_color is not None
            )

            data_index = row_index - 1 if self.header else row_index

            # Select the row background.
            if is_header:
                row_background = self.header_background
            elif 0 <= data_index < len(self.row_backgrounds):
                row_background = self.row_backgrounds[data_index]
            else:
                row_background = None

            if row_background is not None and total_width > 0:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(
                    QBrush(
                        window._apply_payload_opacity_color(
                            row_background
                        )
                    )
                )
                painter.drawRect(
                    draw_x,
                    current_y,
                    total_width,
                    row_height_px,
                )

            # Apply the appropriate font weight for this row.
            font.setWeight(
                QFont.Weight.Bold
                if (is_header and self.header_bold)
                else QFont.Weight.Normal
            )
            painter.setFont(font)

            # Measure text using the font actually used for this row.
            metrics = QFontMetrics(font)

            # Select the row text color.
            if is_header:
                color = self.header_color
            elif 0 <= data_index < len(self.row_colors):
                color = self.row_colors[data_index]
            else:
                color = QColor("white")

            painter.setPen(
                window._apply_payload_opacity_color(color)
            )

            current_x = draw_x

            # Draw each cell.
            for col_index, cell in enumerate(row):
                if col_index >= len(widths_px):
                    break

                width_px = widths_px[col_index]
                text = str(cell)
                text_width = metrics.horizontalAdvance(text)

                align = (
                    self.column_alignments[col_index].lower()
                    if col_index < len(self.column_alignments)
                    else "left"
                )

                # Calculate the horizontal position using pixel measurements.
                if align == "right":
                    text_x = current_x + max(
                        padding_px,
                        width_px - padding_px - text_width,
                    )
                elif align in {"center", "centre"}:
                    text_x = current_x + max(
                        padding_px,
                        (width_px - text_width) // 2,
                    )
                else:
                    text_x = current_x + padding_px

                # Vertically center the text within the row.
                baseline = current_y + (
                    row_height_px
                    + metrics.ascent()
                    - metrics.descent()
                ) // 2

                painter.drawText(
                    int(text_x),
                    int(baseline),
                    text,
                )

                current_x += width_px

            # Advance to the next row.
            current_y += row_height_px

        # Report completion through the optional tracing callback.
        if self.trace_fn:
            self.trace_fn(
                "trace:complete",
                {
                    "kind": "table",
                    "rows": len(self.rows),
                    "columns": len(self.column_widths),
                    "row_height": self.row_height,
                    "scale": scale,
                    "row_height_px": row_height_px,
                    "point_size": self.point_size,
                },
            )

@dataclass
class _VectorPaintCommand(_LegacyPaintCommand):
    vector_payload: Mapping[str, Any] = field(default_factory=dict)
    scale: float = 1.0
    base_offset_x: float = 0.0
    base_offset_y: float = 0.0
    trace_fn: Optional[Callable[[str, Mapping[str, Any]], None]] = None
    cycle_anchor: Optional[Tuple[int, int]] = None

    def paint(self, window: "OverlayWindow", painter: QPainter, offset_x: int, offset_y: int) -> None:
        adapter = _QtVectorPainterAdapter(window, painter)
        marker_label_position = "below"
        if self.group_transform is not None:
            marker_label_position = getattr(self.group_transform, "marker_label_position", None) or "below"
        render_vector(
            adapter,
            self.vector_payload,
            self.scale,
            self.scale,
            offset_x=self.base_offset_x + offset_x,
            offset_y=self.base_offset_y + offset_y,
            marker_label_position=marker_label_position,
            trace=self.trace_fn,
        )
        if self.trace_fn:
            self.trace_fn("trace:complete", {"kind": "vector"})
        if self.cycle_anchor:
            anchor_x = int(round(self.cycle_anchor[0] + offset_x))
            anchor_y = int(round(self.cycle_anchor[1] + offset_y))
            window._register_cycle_anchor(self.legacy_item.item_id, anchor_x, anchor_y)


class _QtVectorPainterAdapter(VectorPainterAdapter):
    def __init__(self, window: "OverlayWindow", painter: QPainter) -> None:
        self._window = window
        self._painter = painter

    def _text_font(self, text_size: Optional[str] = None) -> QFont:
        font = QFont(self._window._font_family)
        self._window._apply_font_fallbacks(font)
        mapper = self._window._compute_legacy_mapper()
        state = self._window._viewport_state()
        size_token = (text_size or "normal").strip().lower()
        if size_token not in {"small", "normal", "large", "huge"}:
            size_token = "normal"
        font.setPointSizeF(self._window._legacy_preset_point_size(size_token, state, mapper))
        font.setWeight(QFont.Weight.Normal)
        return font

    def measure_text_block(self, text: str, text_size: Optional[str] = None) -> tuple[int, int]:
        font = self._text_font(text_size)
        metrics = QFontMetrics(font)
        normalised = str(text).replace("\r\n", "\n").replace("\r", "\n")
        lines = normalised.split("\n") or [""]
        max_width = 0
        for line in lines:
            try:
                advance = metrics.horizontalAdvance(line)
            except Exception:
                advance = 0
            if advance > max_width:
                max_width = advance
        line_spacing = max(metrics.lineSpacing(), metrics.height(), 0)
        total_height = line_spacing * max(1, len(lines))
        return max(0, max_width), max(0, total_height)

    def set_pen(self, color: str, *, width: Optional[int] = None) -> None:
        q_color = QColor(color)
        if not q_color.isValid():
            q_color = QColor("white")
        q_color = self._window._apply_payload_opacity_color(q_color)
        pen = QPen(q_color)
        pen_width = self._window._line_width("vector_line") if width is None else max(0, int(width))
        pen.setWidth(pen_width)
        self._painter.setPen(pen)
        self._painter.setBrush(Qt.BrushStyle.NoBrush)

    def draw_line(self, x1: int, y1: int, x2: int, y2: int) -> None:
        self._painter.drawLine(x1, y1, x2, y2)

    def draw_circle_marker(self, x: int, y: int, radius: int, color: str) -> None:
        q_color = QColor(color)
        if not q_color.isValid():
            q_color = QColor("white")
        q_color = self._window._apply_payload_opacity_color(q_color)
        pen = QPen(q_color)
        pen.setWidth(self._window._line_width("vector_marker"))
        self._painter.setPen(pen)
        self._painter.setBrush(QBrush(q_color))
        self._painter.drawEllipse(QPoint(x, y), radius, radius)

    def draw_cross_marker(self, x: int, y: int, size: int, color: str) -> None:
        self.set_pen(color, width=self._window._line_width("vector_cross"))
        self._painter.drawLine(x - size, y - size, x + size, y + size)
        self._painter.drawLine(x - size, y + size, x + size, y - size)

    def draw_text(self, x: int, y: int, text: str, color: str, text_size: Optional[str] = None) -> None:
        q_color = QColor(color)
        if not q_color.isValid():
            q_color = QColor("white")
        q_color = self._window._apply_payload_opacity_color(q_color)
        pen = QPen(q_color)
        self._painter.setPen(pen)
        font = self._text_font(text_size)
        self._painter.setFont(font)
        metrics = QFontMetrics(font)
        normalised = str(text).replace("\r\n", "\n").replace("\r", "\n")
        lines = normalised.split("\n") or [""]
        baseline = int(round(y + metrics.ascent()))
        line_spacing = max(metrics.lineSpacing(), metrics.height(), 0)
        if line_spacing <= 0:
            line_spacing = metrics.ascent() + metrics.descent()
        for idx, line in enumerate(lines):
            self._painter.drawText(x, baseline + (line_spacing * idx), line)
