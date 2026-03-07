from __future__ import annotations

from overlay_plugin.status_table_payloads import STATUS_TABLE_MAX_ROWS, build_status_table_payloads


def test_status_table_default_max_rows_is_sixty() -> None:
    assert STATUS_TABLE_MAX_ROWS == 60


def test_status_table_payloads_include_headers_rows_and_minimal_borders() -> None:
    payloads = build_status_table_payloads(
        [
            "Alpha: Enabled, Seen, On",
            "Beta: Unknown, Not Seen, Off",
        ],
        id_prefix="edmcmodernoverlay-group-status-",
        ttl_seconds=9,
        max_rows=12,
    )
    assert payloads
    assert all(str(payload["id"]).startswith("edmcmodernoverlay-group-status-") for payload in payloads)
    assert all(int(payload["ttl"]) == 9 for payload in payloads)

    messages = [payload for payload in payloads if payload.get("type") == "message"]
    shapes = [payload for payload in payloads if payload.get("type") == "shape"]
    assert any(payload.get("text") == "Plugin Group" for payload in messages)
    assert any(payload.get("text") == "Plugin" for payload in messages)
    assert any(payload.get("text") == "Seen" for payload in messages)
    assert any(payload.get("text") == "State" for payload in messages)
    assert any(payload.get("text") == "Alpha" for payload in messages)
    assert any(payload.get("text") == "Enabled" for payload in messages)

    rects = [payload for payload in shapes if payload.get("shape") == "rect"]
    separators = [payload for payload in shapes if payload.get("shape") == "vect"]
    assert len(rects) == 1
    assert len(separators) == 2  # header separator + one row separator


def test_status_table_payloads_apply_row_cap_and_ellipsis() -> None:
    payloads = build_status_table_payloads(
        [
            "A: Enabled, Seen, On",
            "B: Enabled, Seen, On",
            "C: Enabled, Seen, On",
            "D: Enabled, Seen, On",
            "A Very Long Plugin Group Name That Should Truncate: Not Enabled, Not Seen, Off",
        ],
        id_prefix="edmcmodernoverlay-group-status-",
        ttl_seconds=5,
        max_rows=3,
    )
    messages = [payload for payload in payloads if payload.get("type") == "message"]
    assert any(payload.get("text") == "+3 more" for payload in messages)
    assert any(str(payload.get("text", "")).endswith("...") for payload in messages)
