"""Pure privacy-safe contracts for the controlled helper pressure A/B."""

from __future__ import annotations

import math
import re
import statistics
from collections import Counter
from typing import Mapping, Sequence

from overlay_client.work_counters import WORK_COUNTER_MAX


PRESSURE_AB_CELLS = ("A1", "A2", "B1", "B2")
WORK_COUNTER_KEYS = (
    "backend_cycles",
    "helper_health_calls",
    "helper_target_calls",
    "helper_presentation_calls",
    "ingest_visual_change",
    "ingest_lifecycle_refresh",
    "ingest_animation_bypass",
    "ingest_unknown_fallback",
    "ingest_rejected",
    "repaint_total",
    "repaint_ingest",
    "repaint_purge",
    "repaint_plugin_group_clear",
    "repaint_override_reload",
    "repaint_override_payload",
    "repaint_controller_target",
    "repaint_explicit_refresh",
    "repaint_other",
    "repaint_immediate",
    "repaint_debounce_started",
    "repaint_debounce_coalesced",
    "repaint_backend_refresh",
    "repaint_qt_update",
    "qt_paints",
    "frame_requests",
    "frame_builds",
    "frame_unchanged_reuses",
    "frame_uncacheable",
    "frame_failures",
)

_ORIGIN_ID = re.compile(r"^[a-f0-9]{32}$")


class PressureAbValidationError(ValueError):
    """Raised when pressure A/B evidence is incomplete, unsafe, or inconsistent."""


def build_work_snapshot(
    *,
    origin_id: object,
    captured_at_ns: object,
    counters: Mapping[str, object],
) -> dict[str, object]:
    """Build one strict cumulative work snapshot containing only fixed counters."""

    if not isinstance(origin_id, str) or _ORIGIN_ID.fullmatch(origin_id) is None:
        raise PressureAbValidationError("pressure snapshot origin_id must be 32 lowercase hex characters")
    if isinstance(captured_at_ns, bool) or not isinstance(captured_at_ns, int) or captured_at_ns < 0:
        raise PressureAbValidationError("pressure snapshot time must be a non-negative integer")
    provided = set(counters)
    expected = set(WORK_COUNTER_KEYS)
    unexpected = sorted(provided - expected)
    missing = sorted(expected - provided)
    if unexpected:
        raise PressureAbValidationError(f"pressure snapshot contains unexpected counter(s): {unexpected}")
    if missing:
        raise PressureAbValidationError(f"pressure snapshot is missing counter(s): {missing}")
    normalized: dict[str, int] = {}
    for key in WORK_COUNTER_KEYS:
        value = counters[key]
        if isinstance(value, bool) or not isinstance(value, int):
            raise PressureAbValidationError(f"pressure snapshot counter {key} must be an integer")
        if value < 0:
            raise PressureAbValidationError(f"pressure snapshot counter {key} must be non-negative")
        if value > WORK_COUNTER_MAX:
            raise PressureAbValidationError(
                f"pressure snapshot counter {key} must be at most {WORK_COUNTER_MAX}"
            )
        normalized[key] = value
    return {
        "schema_version": 1,
        "origin_id": origin_id,
        "captured_at_ns": captured_at_ns,
        "counters": normalized,
    }


def parse_work_snapshot(raw: Mapping[str, object]) -> dict[str, object]:
    """Validate a decoded snapshot without retaining any unrecognized fields."""

    expected = {"schema_version", "origin_id", "captured_at_ns", "counters"}
    unexpected = sorted(set(raw) - expected)
    missing = sorted(expected - set(raw))
    if unexpected or missing or raw.get("schema_version") != 1:
        raise PressureAbValidationError("invalid pressure snapshot schema")
    counters = raw.get("counters")
    if not isinstance(counters, Mapping) or not all(isinstance(key, str) for key in counters):
        raise PressureAbValidationError("invalid pressure snapshot counters")
    return build_work_snapshot(
        origin_id=raw.get("origin_id"),
        captured_at_ns=raw.get("captured_at_ns"),
        counters=counters,
    )


def delta_work_snapshots(
    before_raw: Mapping[str, object],
    after_raw: Mapping[str, object],
) -> dict[str, int]:
    """Return a same-process cumulative-counter delta or reject the sample."""

    before = parse_work_snapshot(before_raw)
    after = parse_work_snapshot(after_raw)
    if before["origin_id"] != after["origin_id"]:
        raise PressureAbValidationError("pressure snapshot origin changed during sample")
    before_time = before["captured_at_ns"]
    after_time = after["captured_at_ns"]
    assert isinstance(before_time, int) and isinstance(after_time, int)
    if after_time <= before_time:
        raise PressureAbValidationError("pressure snapshot time must increase during sample")
    before_counts = before["counters"]
    after_counts = after["counters"]
    assert isinstance(before_counts, dict) and isinstance(after_counts, dict)
    delta: dict[str, int] = {}
    for key in WORK_COUNTER_KEYS:
        difference = int(after_counts[key]) - int(before_counts[key])
        if difference < 0:
            raise PressureAbValidationError(f"pressure snapshot counter {key} decreased during sample")
        delta[key] = difference
    return delta


def validate_complete_pressure_samples(
    samples: Sequence[Mapping[str, object]],
) -> tuple[Mapping[str, object], ...]:
    """Require the approved four cells, repetitions, timing, and quiet diagnostics."""

    expected = Counter((cell, repetition) for cell in PRESSURE_AB_CELLS for repetition in range(1, 4))
    observed: Counter[tuple[str, int]] = Counter()
    for sample in samples:
        cell = sample.get("cell")
        repetition = sample.get("repetition")
        if cell not in PRESSURE_AB_CELLS or isinstance(repetition, bool) or not isinstance(repetition, int):
            raise PressureAbValidationError("pressure samples require recognized cell and repetition")
        if sample.get("warm_up_seconds") != 300 or sample.get("duration_seconds") != 60:
            raise PressureAbValidationError("pressure samples require 300-second warm-up and 60-second duration")
        if sample.get("diagnostics_enabled") is not False:
            raise PressureAbValidationError("pressure samples require diagnostics disabled")
        observed[(str(cell), repetition)] += 1
    if observed != expected:
        raise PressureAbValidationError("pressure evidence requires complete A1/A2/B1/B2 repetitions")
    return tuple(samples)


def summarize_pressure_samples(
    samples: Sequence[Mapping[str, object]],
    *,
    metric_names: Sequence[str],
) -> dict[str, dict[str, dict[str, int | float]]]:
    """Summarize repeated allowlisted metrics using deterministic nearest-rank p95."""

    summary: dict[str, dict[str, dict[str, int | float]]] = {}
    for cell in PRESSURE_AB_CELLS:
        cell_samples = [sample for sample in samples if sample.get("cell") == cell]
        if not cell_samples:
            continue
        metric_summary: dict[str, dict[str, int | float]] = {}
        for metric_name in metric_names:
            values: list[float] = []
            for sample in cell_samples:
                metrics = sample.get("metrics")
                if not isinstance(metrics, Mapping):
                    raise PressureAbValidationError("pressure sample metrics must be an object")
                value = metrics.get(metric_name)
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise PressureAbValidationError(f"pressure metric {metric_name} must be numeric")
                numeric = float(value)
                if not math.isfinite(numeric) or numeric < 0:
                    raise PressureAbValidationError(f"pressure metric {metric_name} must be finite and non-negative")
                values.append(numeric)
            ordered = sorted(values)
            median = float(statistics.median(ordered))
            p95 = ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]
            metric_summary[metric_name] = {
                "median": median,
                "p95": p95,
                "minimum": ordered[0],
                "maximum": ordered[-1],
                "count": len(ordered),
            }
        summary[cell] = metric_summary
    return summary
