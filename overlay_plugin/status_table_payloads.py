"""Render status rows into true table overlay payloads."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from .status_table_layout import StatusTableLayout, ellipsize
from .status_table_model import apply_row_cap, build_rows

STATUS_TABLE_MAX_ROWS = 60
_TEXT_COLOR = "#ffffff"
_BORDER_COLOR = "blue"
_TRANSPARENT_FILL = "#00000000"


def _message_payload(*, payload_id: str, text: str, x: int, y: int, ttl_seconds: int) -> dict[str, object]:
    return {
        "event": "LegacyOverlay",
        "type": "message",
        "id": payload_id,
        "text": text,
        "color": _TEXT_COLOR,
        "x": int(x),
        "y": int(y),
        "ttl": int(ttl_seconds),
        "size": "normal",
    }


def _rect_shape_payload(
    *,
    payload_id: str,
    x: int,
    y: int,
    w: int,
    h: int,
    ttl_seconds: int,
) -> dict[str, object]:
    return {
        "event": "LegacyOverlay",
        "type": "shape",
        "shape": "rect",
        "id": payload_id,
        "color": _BORDER_COLOR,
        "fill": _TRANSPARENT_FILL,
        "x": int(x),
        "y": int(y),
        "w": int(w),
        "h": int(h),
        "ttl": int(ttl_seconds),
    }


def _separator_payload(*, payload_id: str, y: int, width: int, ttl_seconds: int) -> dict[str, object]:
    return {
        "event": "LegacyOverlay",
        "type": "shape",
        "shape": "vect",
        "id": payload_id,
        "color": _BORDER_COLOR,
        "vector": [
            {"x": 0, "y": int(y)},
            {"x": int(width), "y": int(y)},
        ],
        "ttl": int(ttl_seconds),
    }


def build_status_table_payloads(
    lines: Sequence[str],
    *,
    id_prefix: str,
    ttl_seconds: int = 10,
    max_rows: int = STATUS_TABLE_MAX_ROWS,
    layout: StatusTableLayout | None = None,
) -> list[dict[str, object]]:
    table_layout = layout or StatusTableLayout.default()
    rows = build_rows(lines)
    visible_rows, _overflow_count = apply_row_cap(rows, max_rows)
    if not visible_rows:
        return []

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    first_col_x, second_col_x, third_col_x, fourth_col_x = table_layout.column_origins
    payloads: list[dict[str, object]] = []

    header_y = table_layout.text_inset_y
    headers = (
        ("Plugin Group", first_col_x, table_layout.max_group_chars),
        ("Plugin", second_col_x, table_layout.max_plugin_chars),
        ("Seen", third_col_x, table_layout.max_seen_chars),
        ("State", fourth_col_x, table_layout.max_state_chars),
    )
    for idx, (header, origin_x, max_chars) in enumerate(headers):
        payloads.append(
            _message_payload(
                payload_id=f"{id_prefix}{timestamp}-h{idx}",
                text=ellipsize(header, max_chars),
                x=origin_x + table_layout.text_inset_x,
                y=header_y,
                ttl_seconds=ttl_seconds,
            )
        )

    for row_index, row in enumerate(visible_rows):
        row_top = table_layout.header_height + (row_index * table_layout.row_height)
        row_text_y = row_top + table_layout.text_inset_y
        if row.overflow:
            payloads.append(
                _message_payload(
                    payload_id=f"{id_prefix}{timestamp}-r{row_index}c0",
                    text=ellipsize(row.plugin_group, table_layout.max_group_chars),
                    x=first_col_x + table_layout.text_inset_x,
                    y=row_text_y,
                    ttl_seconds=ttl_seconds,
                )
            )
            continue

        cells = (
            (row.plugin_group, first_col_x, table_layout.max_group_chars),
            (row.plugin_status, second_col_x, table_layout.max_plugin_chars),
            (row.seen_status, third_col_x, table_layout.max_seen_chars),
            (row.onoff_status, fourth_col_x, table_layout.max_state_chars),
        )
        for column_index, (cell_text, origin_x, max_chars) in enumerate(cells):
            payloads.append(
                _message_payload(
                    payload_id=f"{id_prefix}{timestamp}-r{row_index}c{column_index}",
                    text=ellipsize(cell_text, max_chars),
                    x=origin_x + table_layout.text_inset_x,
                    y=row_text_y,
                    ttl_seconds=ttl_seconds,
                )
            )

    table_height = table_layout.header_height + (len(visible_rows) * table_layout.row_height)
    payloads.append(
        _rect_shape_payload(
            payload_id=f"{id_prefix}{timestamp}-b0",
            x=0,
            y=0,
            w=table_layout.table_width,
            h=table_height,
            ttl_seconds=ttl_seconds,
        )
    )
    payloads.append(
        _separator_payload(
            payload_id=f"{id_prefix}{timestamp}-s0",
            y=table_layout.header_height,
            width=table_layout.table_width,
            ttl_seconds=ttl_seconds,
        )
    )
    for idx in range(1, len(visible_rows)):
        separator_y = table_layout.header_height + (idx * table_layout.row_height)
        payloads.append(
            _separator_payload(
                payload_id=f"{id_prefix}{timestamp}-s{idx}",
                y=separator_y,
                width=table_layout.table_width,
                ttl_seconds=ttl_seconds,
            )
        )
    return payloads
