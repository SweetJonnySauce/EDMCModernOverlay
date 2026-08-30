from __future__ import annotations

from typing import Any

from utils.payload_inspector import PayloadInspectorApp


class _Canvas:
    def __init__(self) -> None:
        self.ovals: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def create_oval(self, *args: Any, **kwargs: Any) -> None:
        self.ovals.append((args, kwargs))


def test_circle_payload_preview_draws_scaled_oval() -> None:
    canvas = _Canvas()
    app = PayloadInspectorApp.__new__(PayloadInspectorApp)

    app._render_payload(
        canvas,
        {
            "type": "shape",
            "shape": "circle",
            "color": "#80d0ff",
            "fill": "none",
            "x": 100,
            "y": 200,
            "radius": 50,
            "thickness": 2,
        },
        offset_x=20,
        offset_y=30,
        scale=0.25,
    )

    assert canvas.ovals == [
        (
            (32.5, 67.5, 57.5, 92.5),
            {"outline": "#80d0ff", "width": 2, "fill": ""},
        )
    ]
