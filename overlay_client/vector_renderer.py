from __future__ import annotations

from typing import Any, Callable, List, Mapping, Optional


class VectorPainterAdapter:
    def set_pen(self, color: str, *, width: Optional[int] = None) -> None: ...
    def draw_line(self, x1: int, y1: int, x2: int, y2: int) -> None: ...
    def draw_circle_marker(self, x: int, y: int, radius: int, color: str) -> None: ...
    def draw_cross_marker(self, x: int, y: int, size: int, color: str) -> None: ...
    def draw_text(self, x: int, y: int, text: str, color: str, *, text_size: Optional[str] = None) -> None: ...
    def measure_text_block(self, text: str, *, text_size: Optional[str] = None) -> tuple[int, int]: ...


_MARKER_LABEL_POSITIONS = {"below", "above", "centered"}
_MARKER_TEXT_SIZES = {"small", "normal", "large", "huge"}


def _normalise_marker_label_position(value: Optional[str]) -> str:
    if not isinstance(value, str):
        return "below"
    token = value.strip().lower()
    if token in _MARKER_LABEL_POSITIONS:
        return token
    return "below"


def _normalise_marker_text_size(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    token = value.strip().lower()
    if token in _MARKER_TEXT_SIZES:
        return token
    return None


def _call_measure_text_block(
    adapter: VectorPainterAdapter,
    text: str,
    text_size: Optional[str],
) -> tuple[int, int]:
    if text_size is None:
        return adapter.measure_text_block(text)
    try:
        return adapter.measure_text_block(text, text_size=text_size)
    except TypeError:
        # Backwards compatibility: older adapters may not accept text_size.
        return adapter.measure_text_block(text)


def _call_draw_text(
    adapter: VectorPainterAdapter,
    x: int,
    y: int,
    text: str,
    color: str,
    text_size: Optional[str],
) -> None:
    if text_size is None:
        adapter.draw_text(x, y, text, color)
        return
    try:
        adapter.draw_text(x, y, text, color, text_size=text_size)
    except TypeError:
        # Backwards compatibility: older adapters may not accept text_size.
        adapter.draw_text(x, y, text, color)


def _measure_text_height(adapter: VectorPainterAdapter, text: str, text_size: Optional[str]) -> float:
    try:
        _, height = _call_measure_text_block(adapter, text, text_size)
    except Exception:
        return 0.0
    try:
        height_value = float(height)
    except (TypeError, ValueError):
        return 0.0
    if height_value < 0.0:
        return 0.0
    return height_value


def render_vector(
    adapter: VectorPainterAdapter,
    payload: Mapping[str, Any],
    scale_x: float,
    scale_y: float,
    *,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
    marker_label_position: Optional[str] = None,
    trace: Optional[Callable[[str, Mapping[str, Any]], None]] = None,
) -> None:
    base_color = str(payload.get("base_color") or "white")
    label_position = _normalise_marker_label_position(marker_label_position)
    payload_text_size = _normalise_marker_text_size(payload.get("text_size") or payload.get("size"))
    points: List[Mapping[str, Any]] = list(payload.get("points") or [])
    if not points:
        return

    def scaled(point: Mapping[str, Any]) -> tuple[int, int]:
        x = int(round(float(point.get("x", 0)) * scale_x + offset_x))
        y = int(round(float(point.get("y", 0)) * scale_y + offset_y))
        return x, y

    scaled_points = [scaled(point) for point in points]
    if trace:
        trace(
            "render_vector:scaled_points",
            {
                "scaled_points": scaled_points,
                "scale_x": scale_x,
                "scale_y": scale_y,
                "offset_x": offset_x,
                "offset_y": offset_y,
            },
        )

    if len(points) >= 2:
        for idx in range(len(points) - 1):
            adapter.set_pen(base_color)
            x1, y1 = scaled_points[idx]
            x2, y2 = scaled_points[idx + 1]
            adapter.draw_line(x1, y1, x2, y2)

    for idx, point in enumerate(points):
        marker = (point.get("marker") or "").lower()
        color = str(point.get("color") or base_color)
        x, y = scaled_points[idx]
        if marker == "circle":
            adapter.draw_circle_marker(x, y, radius=6, color=color)
        elif marker == "cross":
            adapter.draw_cross_marker(x, y, size=6, color=color)

        text = point.get("text")
        if text:
            text_value = str(text)
            point_text_size = _normalise_marker_text_size(point.get("size"))
            effective_text_size = point_text_size or payload_text_size or "normal"
            draw_y: float
            if label_position == "below":
                draw_y = y + 7
            else:
                text_height = _measure_text_height(adapter, text_value, effective_text_size)
                if label_position == "above":
                    draw_y = y - 7 - text_height
                else:
                    draw_y = y - (text_height / 2.0)
            _call_draw_text(
                adapter,
                x + 8,
                int(round(draw_y)),
                text_value,
                color,
                effective_text_size,
            )
