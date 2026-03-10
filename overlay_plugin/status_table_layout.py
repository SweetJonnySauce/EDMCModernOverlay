"""Layout helpers for rendering `!ovr status` as a table."""
from __future__ import annotations

from dataclasses import dataclass


def ellipsize(text: str, max_chars: int) -> str:
    value = str(text or "")
    if max_chars <= 0:
        return ""
    if len(value) <= max_chars:
        return value
    if max_chars <= 3:
        return "." * max_chars
    return value[: max_chars - 3] + "..."


@dataclass(frozen=True)
class StatusTableLayout:
    header_height: int
    row_height: int
    text_inset_x: int
    text_inset_y: int
    column_group_width: int
    column_plugin_width: int
    column_seen_width: int
    column_state_width: int
    max_group_chars: int
    max_plugin_chars: int
    max_seen_chars: int
    max_state_chars: int

    @property
    def table_width(self) -> int:
        return (
            self.column_group_width
            + self.column_plugin_width
            + self.column_seen_width
            + self.column_state_width
        )

    @property
    def column_origins(self) -> tuple[int, int, int, int]:
        first = 0
        second = first + self.column_group_width
        third = second + self.column_plugin_width
        fourth = third + self.column_seen_width
        return first, second, third, fourth

    @staticmethod
    def default() -> "StatusTableLayout":
        # Tuned for readable status tables while preserving current group colors.
        return StatusTableLayout(
            header_height=26,
            row_height=22,
            text_inset_x=6,
            text_inset_y=4,
            column_group_width=380,
            column_plugin_width=220,
            column_seen_width=120,
            column_state_width=90,
            max_group_chars=42,
            max_plugin_chars=20,
            max_seen_chars=9,
            max_state_chars=5,
        )
