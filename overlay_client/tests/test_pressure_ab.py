from __future__ import annotations

import pytest

from overlay_client.backend.pressure_ab import (
    PRESSURE_AB_CELLS,
    WORK_COUNTER_KEYS,
    PressureAbValidationError,
    build_work_snapshot,
    delta_work_snapshots,
    summarize_pressure_samples,
    validate_complete_pressure_samples,
)


def _counts(value: int = 0) -> dict[str, int]:
    return {key: value for key in WORK_COUNTER_KEYS}


def test_work_snapshot_has_fixed_allowlisted_shape() -> None:
    snapshot = build_work_snapshot(
        origin_id="a" * 32,
        captured_at_ns=100,
        counters=_counts(2),
    )

    assert snapshot == {
        "schema_version": 1,
        "origin_id": "a" * 32,
        "captured_at_ns": 100,
        "counters": _counts(2),
    }


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (lambda value: value["counters"].__setitem__("private_title", 1), "unexpected counter"),
        (lambda value: value["counters"].__setitem__(WORK_COUNTER_KEYS[0], -1), "non-negative"),
        (lambda value: value["counters"].__setitem__(WORK_COUNTER_KEYS[0], True), "integer"),
        (lambda value: value.__setitem__("origin_id", "unsafe origin"), "origin_id"),
    ],
)
def test_work_snapshot_rejects_unsafe_or_unbounded_state(mutator, message: str) -> None:
    raw = {
        "schema_version": 1,
        "origin_id": "b" * 32,
        "captured_at_ns": 10,
        "counters": _counts(),
    }
    mutator(raw)

    with pytest.raises(PressureAbValidationError, match=message):
        build_work_snapshot(
            origin_id=raw["origin_id"],
            captured_at_ns=raw["captured_at_ns"],
            counters=raw["counters"],
        )


def test_delta_work_snapshots_returns_exact_same_origin_delta() -> None:
    before_counts = _counts(1)
    after_counts = _counts(3)
    before = build_work_snapshot(origin_id="c" * 32, captured_at_ns=100, counters=before_counts)
    after = build_work_snapshot(origin_id="c" * 32, captured_at_ns=200, counters=after_counts)

    delta = delta_work_snapshots(before, after)

    assert delta == {key: 2 for key in WORK_COUNTER_KEYS}


@pytest.mark.parametrize(
    ("before_origin", "after_origin", "before_time", "after_time", "counter_before", "counter_after", "message"),
    [
        ("d" * 32, "e" * 32, 1, 2, 1, 2, "origin"),
        ("d" * 32, "d" * 32, 2, 1, 1, 2, "time"),
        ("d" * 32, "d" * 32, 1, 2, 2, 1, "decreased"),
    ],
)
def test_delta_work_snapshots_rejects_mixed_or_reset_counters(
    before_origin: str,
    after_origin: str,
    before_time: int,
    after_time: int,
    counter_before: int,
    counter_after: int,
    message: str,
) -> None:
    before = build_work_snapshot(
        origin_id=before_origin,
        captured_at_ns=before_time,
        counters=_counts(counter_before),
    )
    after = build_work_snapshot(
        origin_id=after_origin,
        captured_at_ns=after_time,
        counters=_counts(counter_after),
    )

    with pytest.raises(PressureAbValidationError, match=message):
        delta_work_snapshots(before, after)


def test_complete_pressure_samples_require_three_repetitions_for_every_cell() -> None:
    samples = [
        {
            "cell": cell,
            "repetition": repetition,
            "duration_seconds": 60,
            "warm_up_seconds": 300,
            "diagnostics_enabled": False,
        }
        for cell in PRESSURE_AB_CELLS
        for repetition in range(1, 4)
    ]

    assert validate_complete_pressure_samples(samples) == tuple(samples)

    with pytest.raises(PressureAbValidationError, match="complete A1/A2/B1/B2"):
        validate_complete_pressure_samples(samples[:-1])


def test_pressure_sample_summary_is_deterministic_median_p95_and_range() -> None:
    samples = [
        {"cell": "B2", "repetition": 1, "metrics": {"shell_cpu_percent": 1.0}},
        {"cell": "B2", "repetition": 2, "metrics": {"shell_cpu_percent": 3.0}},
        {"cell": "B2", "repetition": 3, "metrics": {"shell_cpu_percent": 2.0}},
    ]

    summary = summarize_pressure_samples(samples, metric_names=("shell_cpu_percent",))

    assert summary["B2"]["shell_cpu_percent"] == {
        "median": 2.0,
        "p95": 3.0,
        "minimum": 1.0,
        "maximum": 3.0,
        "count": 3,
    }
