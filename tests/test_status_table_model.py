from __future__ import annotations

from overlay_plugin.status_table_model import apply_row_cap, build_rows, parse_status_line


def test_parse_status_line_reads_columns() -> None:
    row = parse_status_line("BGS-Tally Objectives: Enabled, Seen, On")
    assert row is not None
    assert row.plugin_group == "BGS-Tally Objectives"
    assert row.plugin_status == "Enabled"
    assert row.seen_status == "Seen"
    assert row.onoff_status == "On"


def test_build_rows_sorts_by_group_name() -> None:
    rows = build_rows(
        [
            "Zulu: Enabled, Seen, On",
            "alpha: Not Enabled, Not Seen, Off",
        ]
    )
    assert [row.plugin_group for row in rows] == ["alpha", "Zulu"]


def test_apply_row_cap_adds_overflow_row() -> None:
    rows = build_rows(
        [
            "A: Enabled, Seen, On",
            "B: Enabled, Seen, On",
            "C: Enabled, Seen, On",
            "D: Enabled, Seen, On",
        ]
    )
    visible_rows, overflow_count = apply_row_cap(rows, 3)
    assert overflow_count == 2
    assert len(visible_rows) == 3
    assert visible_rows[-1].overflow is True
    assert visible_rows[-1].plugin_group == "+2 more"
