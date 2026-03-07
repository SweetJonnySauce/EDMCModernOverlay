"""Model helpers for table-formatted status lines."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence


@dataclass(frozen=True)
class StatusTableRow:
    plugin_group: str
    plugin_status: str
    seen_status: str
    onoff_status: str
    overflow: bool = False


def parse_status_line(line: str) -> Optional[StatusTableRow]:
    raw = str(line or "").strip()
    if not raw:
        return None
    if ":" not in raw:
        return StatusTableRow(
            plugin_group=raw,
            plugin_status="Unknown",
            seen_status="Not Seen",
            onoff_status="On",
        )
    group_name, payload = raw.split(":", 1)
    plugin_group = group_name.strip()
    if not plugin_group:
        return None
    parts = [part.strip() for part in payload.split(",")]
    plugin_status = parts[0] if len(parts) >= 1 and parts[0] else "Unknown"
    seen_status = parts[1] if len(parts) >= 2 and parts[1] else "Not Seen"
    onoff_status = parts[2] if len(parts) >= 3 and parts[2] else "On"
    return StatusTableRow(
        plugin_group=plugin_group,
        plugin_status=plugin_status,
        seen_status=seen_status,
        onoff_status=onoff_status,
    )


def build_rows(lines: Iterable[str]) -> list[StatusTableRow]:
    rows: list[StatusTableRow] = []
    for line in lines:
        row = parse_status_line(line)
        if row is not None:
            rows.append(row)
    return sorted(rows, key=lambda row: row.plugin_group.casefold())


def apply_row_cap(rows: Sequence[StatusTableRow], max_rows: int) -> tuple[list[StatusTableRow], int]:
    if max_rows <= 0:
        return [], len(rows)
    if len(rows) <= max_rows:
        return list(rows), 0
    if max_rows == 1:
        overflow_count = len(rows)
        return [
            StatusTableRow(
                plugin_group=f"+{overflow_count} more",
                plugin_status="",
                seen_status="",
                onoff_status="",
                overflow=True,
            )
        ], overflow_count
    visible_rows = max_rows - 1
    overflow_count = len(rows) - visible_rows
    result = list(rows[:visible_rows])
    result.append(
        StatusTableRow(
            plugin_group=f"+{overflow_count} more",
            plugin_status="",
            seen_status="",
            onoff_status="",
            overflow=True,
        )
    )
    return result, overflow_count
