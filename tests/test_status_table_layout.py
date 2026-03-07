from __future__ import annotations

from overlay_plugin.status_table_layout import StatusTableLayout, ellipsize


def test_ellipsize_keeps_short_text() -> None:
    assert ellipsize("Status", 10) == "Status"


def test_ellipsize_truncates_with_dots() -> None:
    assert ellipsize("ABCDEFGHIJKLMNOPQRSTUVWXYZ", 10) == "ABCDEFG..."


def test_default_layout_has_expected_width_and_origins() -> None:
    layout = StatusTableLayout.default()
    assert layout.table_width == (
        layout.column_group_width
        + layout.column_plugin_width
        + layout.column_seen_width
        + layout.column_state_width
    )
    first, second, third, fourth = layout.column_origins
    assert first == 0
    assert second > first
    assert third > second
    assert fourth > third
