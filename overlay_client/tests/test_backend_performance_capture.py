import json
from pathlib import Path

import pytest

from scripts import backend_performance_capture as capture_script
from overlay_client.backend.performance_capture import (
    PERFORMANCE_EVENT_PREFIX,
    build_performance_capture_document,
    calculate_process_cpu_percent,
    parse_performance_event_line,
    parse_repaint_stats_line,
)
from overlay_client.backend.performance_evidence import (
    EvidenceValidationError,
    parse_performance_capture,
    parse_performance_manifest,
)


MANIFEST_PATH = Path("docs/support/validation/fix219-pre-migration/performance/manifest.json")


def _event(**overrides: object) -> dict[str, object]:
    event: dict[str, object] = {
        "schema_version": 1,
        "event": "backend_presentation_cycle",
        "presentation_cycle_ms": 2.5,
        "helper_health_calls": 1,
        "helper_target_calls": 1,
        "helper_presentation_calls": 1,
        "transition_state": "pending_fullscreen_handoff",
        "transition_elapsed_ms": 250.0,
        "raster_builds": 1,
        "raster_reuses": 0,
        "raster_skips": 0,
        "raster_bytes": 4096,
        "raster_regions": 3,
        "raster_encode_ms": 0.75,
        "raster_build_ms": 1.25,
        "helper_decode_ms": 0.2,
        "helper_apply_ms": 0.4,
        "frame_builds": 1,
        "qt_widget_visible": True,
        "qt_window_exposed": False,
        "qt_paint_count": 3,
        "target_has_focus": False,
        "prepared_surface_requires_mapping": True,
        "qt_geometry_match": True,
    }
    event.update(overrides)
    return event


def test_parse_performance_event_line_ignores_prefix_and_rejects_extra_fields() -> None:
    event = _event()
    line = f"safe logger prefix {PERFORMANCE_EVENT_PREFIX}{json.dumps(event)}"

    assert parse_performance_event_line(line) == event
    assert parse_performance_event_line("unrelated log line") is None

    event["target_token"] = "private-token"
    with pytest.raises(EvidenceValidationError, match="unexpected fields"):
        parse_performance_event_line(f"{PERFORMANCE_EVENT_PREFIX}{json.dumps(event)}")


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("qt_widget_visible", 1, "qt_widget_visible must be boolean"),
        ("qt_window_exposed", "false", "qt_window_exposed must be boolean"),
        ("target_has_focus", 1, "target_has_focus must be boolean"),
        ("prepared_surface_requires_mapping", "true", "prepared_surface_requires_mapping must be boolean"),
        ("qt_geometry_match", 1, "qt_geometry_match must be boolean"),
        ("qt_paint_count", -1, "qt_paint_count must be a non-negative integer"),
        ("qt_paint_count", 1_000_001, "qt_paint_count must be at most 1000000"),
    ),
)
def test_parse_performance_event_line_validates_qt_presentation_fields(
    field: str,
    value: object,
    message: str,
) -> None:
    event = _event(**{field: value})

    with pytest.raises(EvidenceValidationError, match=message):
        parse_performance_event_line(f"{PERFORMANCE_EVENT_PREFIX}{json.dumps(event)}")


def test_parse_repaint_stats_line_returns_only_interval_counts() -> None:
    line = (
        "prefix Repaint stats: paints=7 ingest_delta=2 purge_delta=1 "
        "total_delta=5 ingest_total=10 purge_total=4 total=14"
    )

    assert parse_repaint_stats_line(line) == {"paints": 7, "repaints": 5}
    assert parse_repaint_stats_line("prefix target_token=private") is None


def test_calculate_process_cpu_percent_uses_elapsed_process_ticks() -> None:
    assert calculate_process_cpu_percent(100, 125, elapsed_seconds=1.0, clock_ticks_per_second=100) == 25.0
    assert calculate_process_cpu_percent(125, 125, elapsed_seconds=1.0, clock_ticks_per_second=100) == 0.0

    with pytest.raises(EvidenceValidationError, match="monotonic"):
        calculate_process_cpu_percent(125, 100, elapsed_seconds=1.0, clock_ticks_per_second=100)


def _performance_event_line(**overrides: object) -> str:
    return f"prefix {PERFORMANCE_EVENT_PREFIX}{json.dumps(_event(**overrides))}\n"


def test_capture_log_slice_reads_active_log_after_start_offset(tmp_path: Path) -> None:
    active_log = tmp_path / "overlay_client.log"
    active_log.write_text("before observation\n", encoding="utf-8")
    cursor = capture_script._capture_log_cursor(active_log)
    with active_log.open("a", encoding="utf-8") as handle:
        handle.write(_performance_event_line(presentation_cycle_ms=3.0))

    events, repaint_intervals = capture_script._read_log_slice(active_log, cursor)

    assert [event["presentation_cycle_ms"] for event in events] == [3.0]
    assert repaint_intervals == []


def test_capture_log_slice_follows_multiple_numeric_rotations(tmp_path: Path) -> None:
    active_log = tmp_path / "overlay_client.log"
    active_log.write_text("before observation\n", encoding="utf-8")
    cursor = capture_script._capture_log_cursor(active_log)
    with active_log.open("a", encoding="utf-8") as handle:
        handle.write(_performance_event_line(presentation_cycle_ms=1.0))

    first_rotation = active_log.with_name("overlay_client.log.1")
    active_log.rename(first_rotation)
    active_log.write_text(_performance_event_line(presentation_cycle_ms=2.0), encoding="utf-8")

    first_rotation.rename(active_log.with_name("overlay_client.log.2"))
    active_log.rename(first_rotation)
    active_log.write_text(
        _performance_event_line(presentation_cycle_ms=3.0)
        + "prefix Repaint stats: paints=7 ingest_delta=2 purge_delta=1 "
        "total_delta=5 ingest_total=10 purge_total=4 total=14\n",
        encoding="utf-8",
    )

    events, repaint_intervals = capture_script._read_log_slice(active_log, cursor)

    assert [event["presentation_cycle_ms"] for event in events] == [1.0, 2.0, 3.0]
    assert repaint_intervals == [{"paints": 7, "repaints": 5}]


def test_capture_log_slice_rejects_incomplete_rotation_chain(tmp_path: Path) -> None:
    active_log = tmp_path / "overlay_client.log"
    active_log.write_text("before observation\n", encoding="utf-8")
    cursor = capture_script._capture_log_cursor(active_log)
    active_log.rename(active_log.with_name("overlay_client.log.2"))
    active_log.write_text(_performance_event_line(), encoding="utf-8")

    with pytest.raises(EvidenceValidationError, match="rotation chain is incomplete"):
        capture_script._read_log_slice(active_log, cursor)


def test_capture_log_slice_rejects_expired_rotation_cursor(tmp_path: Path) -> None:
    active_log = tmp_path / "overlay_client.log"
    active_log.write_text("before observation\n", encoding="utf-8")
    cursor = capture_script._capture_log_cursor(active_log)
    active_log.rename(tmp_path / "expired.log")
    active_log.write_text(_performance_event_line(), encoding="utf-8")

    with pytest.raises(EvidenceValidationError, match="rotated beyond retained history"):
        capture_script._read_log_slice(active_log, cursor)


def test_build_capture_document_is_valid_deterministic_and_privacy_safe() -> None:
    manifest = parse_performance_manifest(MANIFEST_PATH)
    events = (
        _event(),
        _event(
            presentation_cycle_ms=3.5,
            helper_health_calls=0,
            transition_state="stable_shell_raster",
            transition_elapsed_ms=0.0,
            raster_builds=0,
            raster_reuses=1,
            raster_bytes=0,
            raster_regions=0,
            raster_encode_ms=0.0,
            raster_build_ms=0.0,
            helper_decode_ms=0.3,
            helper_apply_ms=0.5,
        ),
    )
    manual = {
        "dual_visible_presenters": False,
        "title_bar_intermediate": False,
        "monitor_relative_intermediate": False,
        "black_surface": False,
        "focus_trap": False,
        "unexpected_identity": False,
        "premature_commitment": False,
        "material_hitch": False,
        "note_codes": [],
    }

    document = build_performance_capture_document(
        manifest,
        scenario_id="scale_100_windowed_to_fullscreen_monitor_a",
        repetition=1,
        capture_role="baseline",
        events=events,
        repaint_intervals=({"paints": 7, "repaints": 5},),
        client_cpu_samples=(0.1, 0.2),
        gnome_shell_cpu_samples=(1.0, 2.0),
        manual_observations=manual,
    )

    parsed = parse_performance_capture(document, manifest)
    assert [sample.elapsed_ms for sample in parsed.latency_samples if sample.metric == "presentation_cycle_ms"] == [
        2.5,
        3.5,
    ]
    assert [sample.elapsed_ms for sample in parsed.latency_samples if sample.metric == "end_to_stable_ms"] == [250.0]
    assert parsed.work["helper_health_calls"] == 1
    assert parsed.work["raster_builds"] == 1
    assert parsed.work["raster_reuses"] == 1
    assert parsed.work["repaints"] == 5
    assert parsed.work["paints"] == 7
    assert parsed.work["transitions"] == 1
    serialized = json.dumps(document, sort_keys=True)
    assert "target_token" not in serialized
    assert "/home/" not in serialized
