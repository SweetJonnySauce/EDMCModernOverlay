"""Pure adapters for privacy-safe Step 03 runtime performance samples."""

from __future__ import annotations

import json
import math
import re
from typing import Mapping, Sequence

from overlay_client.backend.performance_evidence import (
    EvidenceValidationError,
    PerformanceScenarioManifest,
)


PERFORMANCE_EVENT_PREFIX = "BACKEND_PERFORMANCE_SAMPLE "
QT_PAINT_COUNT_MAX = 1_000_000

_EVENT_FIELDS = frozenset(
    {
        "schema_version",
        "event",
        "presentation_cycle_ms",
        "helper_health_calls",
        "helper_target_calls",
        "helper_presentation_calls",
        "transition_state",
        "transition_elapsed_ms",
        "raster_builds",
        "raster_reuses",
        "raster_skips",
        "raster_bytes",
        "raster_regions",
        "raster_encode_ms",
        "raster_build_ms",
        "helper_decode_ms",
        "helper_apply_ms",
        "frame_builds",
        "qt_widget_visible",
        "qt_window_exposed",
        "qt_paint_count",
        "target_has_focus",
        "prepared_surface_requires_mapping",
        "qt_geometry_match",
    }
)
_COUNT_FIELDS = frozenset(
    {
        "helper_health_calls",
        "helper_target_calls",
        "helper_presentation_calls",
        "raster_builds",
        "raster_reuses",
        "raster_skips",
        "raster_bytes",
        "raster_regions",
        "frame_builds",
        "qt_paint_count",
    }
)
_BOOLEAN_FIELDS = frozenset(
    {
        "qt_widget_visible",
        "qt_window_exposed",
        "target_has_focus",
        "prepared_surface_requires_mapping",
        "qt_geometry_match",
    }
)
_NUMBER_FIELDS = _EVENT_FIELDS - _COUNT_FIELDS - _BOOLEAN_FIELDS - {"schema_version", "event", "transition_state"}
_SAFE_STATE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_REPAINT_STATS = re.compile(
    r"Repaint stats: paints=(?P<paints>\d+) ingest_delta=\d+ purge_delta=\d+ "
    r"total_delta=(?P<repaints>\d+) ingest_total=\d+ purge_total=\d+ total=\d+"
)
_MANUAL_FIELDS = (
    "dual_visible_presenters",
    "title_bar_intermediate",
    "monitor_relative_intermediate",
    "black_surface",
    "focus_trap",
    "unexpected_identity",
    "premature_commitment",
    "material_hitch",
)
_WORK_EVENT_FIELDS = (
    "helper_health_calls",
    "helper_target_calls",
    "helper_presentation_calls",
    "raster_builds",
    "raster_reuses",
    "raster_skips",
    "raster_bytes",
    "raster_regions",
    "raster_encode_ms",
    "helper_decode_ms",
    "helper_apply_ms",
    "frame_builds",
)
_WORK_COUNT_EVENT_FIELDS = _COUNT_FIELDS & set(_WORK_EVENT_FIELDS)


def parse_performance_event_line(line: str) -> dict[str, object] | None:
    """Extract one strict allowlisted performance event from an arbitrary log prefix."""

    marker_index = line.find(PERFORMANCE_EVENT_PREFIX)
    if marker_index < 0:
        return None
    payload = line[marker_index + len(PERFORMANCE_EVENT_PREFIX) :].strip()
    try:
        raw = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise EvidenceValidationError(f"invalid backend performance event JSON: {exc}") from exc
    if not isinstance(raw, dict) or not all(isinstance(key, str) for key in raw):
        raise EvidenceValidationError("backend performance event must be a JSON object")
    unexpected = sorted(set(raw) - _EVENT_FIELDS)
    missing = sorted(_EVENT_FIELDS - set(raw))
    if unexpected:
        raise EvidenceValidationError(f"backend performance event contains unexpected fields: {unexpected}")
    if missing:
        raise EvidenceValidationError(f"backend performance event is missing fields: {missing}")
    if raw["schema_version"] != 1 or raw["event"] != "backend_presentation_cycle":
        raise EvidenceValidationError("unsupported backend performance event schema or type")
    state = raw["transition_state"]
    if not isinstance(state, str) or not _SAFE_STATE.fullmatch(state):
        raise EvidenceValidationError("backend performance event transition_state is unsafe")
    for field in _COUNT_FIELDS:
        value = raw[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise EvidenceValidationError(f"backend performance event {field} must be a non-negative integer")
    if raw["qt_paint_count"] > QT_PAINT_COUNT_MAX:
        raise EvidenceValidationError(f"backend performance event qt_paint_count must be at most {QT_PAINT_COUNT_MAX}")
    for field in _BOOLEAN_FIELDS:
        if not isinstance(raw[field], bool):
            raise EvidenceValidationError(f"backend performance event {field} must be boolean")
    for field in _NUMBER_FIELDS:
        value = raw[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise EvidenceValidationError(f"backend performance event {field} must be numeric")
        if not math.isfinite(float(value)) or float(value) < 0:
            raise EvidenceValidationError(f"backend performance event {field} must be finite and non-negative")
    return raw


def parse_repaint_stats_line(line: str) -> dict[str, int] | None:
    """Extract only paint/repaint interval counts from the existing sanitized stats line."""

    match = _REPAINT_STATS.search(line)
    if match is None:
        return None
    return {"paints": int(match.group("paints")), "repaints": int(match.group("repaints"))}


def calculate_process_cpu_percent(
    previous_ticks: int,
    current_ticks: int,
    *,
    elapsed_seconds: float,
    clock_ticks_per_second: int,
) -> float:
    """Calculate one process CPU sample from two monotonic `/proc` tick snapshots."""

    if current_ticks < previous_ticks:
        raise EvidenceValidationError("process CPU ticks must be monotonic")
    if elapsed_seconds <= 0 or clock_ticks_per_second <= 0:
        raise EvidenceValidationError("process CPU elapsed time and clock rate must be positive")
    cpu_seconds = (current_ticks - previous_ticks) / float(clock_ticks_per_second)
    return round(cpu_seconds / elapsed_seconds * 100.0, 6)


def build_performance_capture_document(
    manifest: PerformanceScenarioManifest,
    *,
    scenario_id: str,
    repetition: int,
    capture_role: str,
    events: Sequence[Mapping[str, object]],
    repaint_intervals: Sequence[Mapping[str, int]],
    client_cpu_samples: Sequence[float],
    gnome_shell_cpu_samples: Sequence[float],
    manual_observations: Mapping[str, object],
) -> dict[str, object]:
    """Build a normalized capture document from already allowlisted observations."""

    scenario = manifest.scenario(scenario_id)
    if not events:
        raise EvidenceValidationError("capture requires at least one backend performance event")
    normalized_events = tuple(_validated_event(event) for event in events)
    manual = _validated_manual_observations(manual_observations)
    latency_samples: list[dict[str, object]] = []
    for index, event in enumerate(normalized_events, start=1):
        latency_samples.append(
            {
                "metric": "presentation_cycle_ms",
                "elapsed_ms": event["presentation_cycle_ms"],
                "clock_domain": manifest.clock_domains.client_elapsed,
                "correlation_id": f"cycle_{index:06d}",
            }
        )
    helper_events = [event for event in normalized_events if _event_count(event, "helper_presentation_calls") > 0]
    if not helper_events:
        helper_events = [normalized_events[-1]]
    for index, event in enumerate(helper_events, start=1):
        latency_samples.append(
            {
                "metric": "helper_apply_ms",
                "elapsed_ms": event["helper_apply_ms"],
                "clock_domain": manifest.clock_domains.helper_elapsed,
                "correlation_id": f"helper_{index:06d}",
            }
        )
    latency_samples.append(
        {
            "metric": "end_to_stable_ms",
            "elapsed_ms": max(float(event["transition_elapsed_ms"]) for event in normalized_events),
            "clock_domain": manifest.clock_domains.client_elapsed,
            "correlation_id": "transition_000001",
        }
    )

    work: dict[str, int | float] = {}
    for field in _WORK_EVENT_FIELDS:
        if field in _WORK_COUNT_EVENT_FIELDS:
            work[field] = sum(_event_count(event, field) for event in normalized_events)
        else:
            work[field] = sum(_event_number(event, field) for event in normalized_events)
    work["transitions"] = int(
        scenario.start_mode != scenario.end_mode or scenario.start_monitor != scenario.end_monitor
    )
    work["repaints"] = sum(_interval_count(item, "repaints") for item in repaint_intervals)
    work["paints"] = sum(_interval_count(item, "paints") for item in repaint_intervals)

    reference = manifest.reference_versions
    environment = manifest.target_environment
    capture_id = f"{capture_role}_{scenario_id}_r{repetition}"
    diagnostic_reference = f"diag_{scenario_id}_r{repetition}"
    return {
        "schema_version": 1,
        "manifest_id": manifest.manifest_id,
        "capture_id": capture_id,
        "capture_role": capture_role,
        "scenario_id": scenario_id,
        "repetition": repetition,
        "environment": {
            "operating_system": environment.operating_system,
            "distribution": environment.distribution,
            "distribution_version": environment.distribution_version,
            "session_type": environment.session_type,
            "desktop": environment.desktop,
            "compositor": environment.compositor,
            "compositor_version": environment.compositor_version,
        },
        "versions": {
            "plugin": reference.plugin,
            "client": reference.client,
            "helper_protocol": reference.helper_protocol,
            "source_revision": reference.source_revision,
            "architecture_stage": "pre_migration" if capture_role == "baseline" else "candidate",
        },
        "display_configuration_id": scenario.display_configuration_id,
        "payload_fixture_id": scenario.payload_fixture_id,
        "diagnostic_configuration_id": scenario.diagnostic_configuration_id,
        "clock_domains": {
            "client_elapsed": manifest.clock_domains.client_elapsed,
            "helper_elapsed": manifest.clock_domains.helper_elapsed,
        },
        "warm_up_seconds": manifest.timing.warm_up_seconds,
        "observation_seconds": manifest.timing.observation_seconds,
        "idle_cpu_seconds": manifest.timing.idle_cpu_seconds,
        "diagnostic_reference": diagnostic_reference,
        "latency_samples": latency_samples,
        "work": work,
        "idle_cpu": {
            "interval_seconds": manifest.timing.idle_cpu_seconds,
            "client_percent_samples": list(client_cpu_samples),
            "gnome_shell_percent_samples": list(gnome_shell_cpu_samples),
        },
        "manual_observations": manual,
    }


def _validated_event(event: Mapping[str, object]) -> dict[str, object]:
    serialized = json.dumps(dict(event), sort_keys=True, separators=(",", ":"))
    parsed = parse_performance_event_line(PERFORMANCE_EVENT_PREFIX + serialized)
    if parsed is None:  # pragma: no cover - prefix is supplied above
        raise EvidenceValidationError("backend performance event was not recognized")
    return parsed


def _validated_manual_observations(value: Mapping[str, object]) -> dict[str, object]:
    expected = set(_MANUAL_FIELDS) | {"note_codes"}
    unexpected = sorted(set(value) - expected)
    missing = sorted(expected - set(value))
    if unexpected or missing:
        raise EvidenceValidationError(
            f"manual observations fields mismatch: unexpected={unexpected}, missing={missing}"
        )
    normalized: dict[str, object] = {}
    for field in _MANUAL_FIELDS:
        if not isinstance(value[field], bool):
            raise EvidenceValidationError(f"manual observation {field} must be boolean")
        normalized[field] = value[field]
    notes = value["note_codes"]
    if not isinstance(notes, (list, tuple)):
        raise EvidenceValidationError("manual observation note_codes must be an array")
    normalized["note_codes"] = list(notes)
    return normalized


def _interval_count(interval: Mapping[str, int], field: str) -> int:
    value = interval.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise EvidenceValidationError(f"repaint interval {field} must be a non-negative integer")
    return value


def _event_count(event: Mapping[str, object], field: str) -> int:
    value = event[field]
    if isinstance(value, bool) or not isinstance(value, int):  # pragma: no cover - validated upstream
        raise EvidenceValidationError(f"backend performance event {field} must be an integer")
    return value


def _event_number(event: Mapping[str, object], field: str) -> float:
    value = event[field]
    if isinstance(value, bool) or not isinstance(value, (int, float)):  # pragma: no cover - validated upstream
        raise EvidenceValidationError(f"backend performance event {field} must be numeric")
    return float(value)
