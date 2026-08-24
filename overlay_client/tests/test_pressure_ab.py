from __future__ import annotations

import dataclasses
import json
from copy import deepcopy

import pytest

from overlay_client.backend.pressure_ab import (
    PRESSURE_AB_CELLS,
    PRESSURE_AB_SAFETY_FIELDS,
    WORK_COUNTER_KEYS,
    PressureAbRun,
    PressureAbValidationError,
    build_work_snapshot,
    delta_work_snapshots,
    load_complete_pressure_ab_run,
    parse_complete_pressure_ab_run,
    parse_pressure_ab_cell_document,
    parse_pressure_ab_sample,
    validate_client_argument_pair,
)
from overlay_client.backend.pressure_ab_report import (
    PRESSURE_AB_CONTRASTS,
    analyze_pressure_ab_run,
    evaluate_pressure_ab_bounds,
    parse_pressure_ab_reviewed_bounds,
    render_pressure_ab_report,
)
from overlay_client.work_counters import WORK_COUNTER_MAX


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


def test_delta_work_snapshots_rejects_saturated_counter_endpoints() -> None:
    before_counts = _counts(1)
    after_counts = _counts(2)
    after_counts[WORK_COUNTER_KEYS[0]] = WORK_COUNTER_MAX
    before = build_work_snapshot(origin_id="d" * 32, captured_at_ns=1, counters=before_counts)
    after = build_work_snapshot(origin_id="d" * 32, captured_at_ns=2, counters=after_counts)

    with pytest.raises(PressureAbValidationError, match="saturated"):
        delta_work_snapshots(before, after)


def _distribution(value: float = 1.0) -> dict[str, int | float]:
    return {
        "count": 60,
        "median": value,
        "p95": value,
        "minimum": value,
        "maximum": value,
    }


def _available_process_resources() -> dict[str, object]:
    return {
        "available": True,
        "cpu_percent": _distribution(),
        "rss_kib": _distribution(1024.0),
        "context_switches": _distribution(2.0),
    }


def _unavailable(reason: str) -> dict[str, object]:
    return {"available": False, "reason": reason}


def _provenance() -> dict[str, object]:
    return {
        "fixture_sha256": "1" * 64,
        "source_revision": "2" * 40,
        "component_versions": {
            "plugin": "2.0.0",
            "client": "2.0.0",
            "helper": "4.0.0",
        },
        "display": {
            "monitor": "A",
            "width_px": 1920,
            "height_px": 1080,
            "scale_percent": 100,
            "refresh_hz": 60.0,
        },
        "workload": "stable_windowed_fixed_fixture",
        "quiet_host": True,
    }


def _cell_state(cell: str) -> dict[str, object]:
    client_running = cell in {"A2", "B2"}
    helper_enabled = cell in {"B1", "B2"}
    backend_state = {
        "A1": "unavailable",
        "A2": "documented_unavailable",
        "B1": "unavailable",
        "B2": "helper_selected",
    }[cell]
    return {
        "client": "running" if client_running else "stopped",
        "helper": "full_helper" if helper_enabled else "disabled",
        "client_backend": backend_state,
        "client_pid_argument": "provided" if client_running else "unavailable",
        "port_file_argument": "provided" if client_running else "unavailable",
        "capture_diagnostics_enabled": False,
        "helper_diagnostics_enabled": False,
    }


def _sample(cell: str, repetition: int) -> dict[str, object]:
    client_running = cell in {"A2", "B2"}
    helper_enabled = cell in {"B1", "B2"}
    client_work: dict[str, object]
    helper_work: dict[str, object]
    actor_counts: dict[str, object]
    if client_running:
        client_work = {
            "available": True,
            "origin_id": "a" * 32,
            "counters": _counts(1),
        }
    else:
        client_work = {
            "available": False,
            "reason": "client_stopped",
            "origin_id": "unavailable",
            "counters": {},
        }
    if helper_enabled:
        helper_work = {
            "available": True,
            "origin_id": "b" * 32,
            "counters": {"target_queries": 1, "presentation_calls": 1},
        }
        actor_counts = {
            "available": True,
            "values": {
                "shell_actor_proof_visible": 0,
                "shell_raster_frame_visible": 0,
                "shell_raster_region_count": 0,
            },
        }
    else:
        helper_work = {
            "available": False,
            "reason": "helper_disabled",
            "origin_id": "unavailable",
            "counters": {},
        }
        actor_counts = {"available": False, "reason": "helper_disabled", "values": {}}
    return {
        "schema_version": 1,
        "cell": cell,
        "repetition": repetition,
        "warm_up_seconds": 300,
        "duration_seconds": 60,
        "diagnostics_enabled": False,
        "resources": {
            "shell": _available_process_resources(),
            "client": _available_process_resources() if client_running else _unavailable("client_stopped"),
            "gpu": _unavailable("provider_unavailable"),
        },
        "client_work": client_work,
        "helper_work": helper_work,
        "actor_counts": actor_counts,
        "warning_counts": {"available": True, "mutter_assertions": 0, "shell_warnings": 0},
        "safety": {field: False for field in PRESSURE_AB_SAFETY_FIELDS},
        "continuity": {
            "client_restarted": False,
            "helper_restarted": False,
            "client_counter_decreased": False,
            "helper_counter_decreased": False,
            "client_counter_saturated": False,
            "helper_counter_saturated": False,
        },
    }


def _cell_document(cell: str, execution_order: int) -> dict[str, object]:
    return {
        "schema_version": 1,
        "cell": cell,
        "execution_order": execution_order,
        "provenance": _provenance(),
        "state": _cell_state(cell),
        "samples": [_sample(cell, repetition) for repetition in range(1, 4)],
    }


@pytest.mark.parametrize("cell", PRESSURE_AB_CELLS)
def test_parse_pressure_ab_sample_accepts_exact_runner_shape_for_each_cell(cell: str) -> None:
    parsed = parse_pressure_ab_sample(_sample(cell, 1), expected_cell=cell)

    assert parsed.cell == cell
    assert parsed.repetition == 1
    assert parsed.resources["client"].available is (cell in {"A2", "B2"})
    assert parsed.helper_work.available is (cell in {"B1", "B2"})


@pytest.mark.parametrize(
    "mutator",
    [
        lambda document: document.__setitem__("client_pid", 123),
        lambda document: document["samples"][0]["warning_counts"].__setitem__("journal_text", "raw"),
        lambda document: document["provenance"].__setitem__("fixture_path", "/home/private/fixture.json"),
        lambda document: document["provenance"].__setitem__("host_name", "private-workstation"),
        lambda document: document["provenance"].__setitem__("access_token", "secret"),
    ],
)
def test_pressure_ab_cell_rejects_prohibited_or_host_identifying_data(mutator) -> None:
    document = _cell_document("B2", 1)
    mutator(document)

    with pytest.raises(PressureAbValidationError, match="privacy|schema"):
        parse_pressure_ab_cell_document(document)


@pytest.mark.parametrize(
    "mutator",
    [
        lambda sample: sample.__setitem__("diagnostics_enabled", True),
        lambda sample: sample.__setitem__("duration_seconds", 59),
        lambda sample: sample["resources"]["shell"]["cpu_percent"].__setitem__("median", float("inf")),
        lambda sample: sample["client_work"]["counters"].__setitem__(WORK_COUNTER_KEYS[0], WORK_COUNTER_MAX),
        lambda sample: sample["continuity"].__setitem__("client_restarted", True),
        lambda sample: sample["safety"].__setitem__(PRESSURE_AB_SAFETY_FIELDS[0], True),
    ],
)
def test_pressure_ab_sample_rejects_unsafe_timing_bounds_continuity_or_safety(mutator) -> None:
    sample = _sample("B2", 1)
    mutator(sample)

    with pytest.raises(PressureAbValidationError):
        parse_pressure_ab_sample(sample, expected_cell="B2")


@pytest.mark.parametrize("cell", ("A1", "B1"))
def test_client_absence_requires_explicit_unavailable_fields(cell: str) -> None:
    document = _cell_document(cell, 1)
    document["samples"][0]["client_work"] = {}

    with pytest.raises(PressureAbValidationError, match="client_work|schema|unavailable"):
        parse_pressure_ab_cell_document(document)


@pytest.mark.parametrize("cell", ("A1", "A2"))
def test_helper_absence_requires_explicit_unavailable_fields(cell: str) -> None:
    document = _cell_document(cell, 1)
    del document["samples"][0]["helper_work"]["reason"]

    with pytest.raises(PressureAbValidationError, match="helper_work|schema|unavailable"):
        parse_pressure_ab_cell_document(document)


@pytest.mark.parametrize(("cell", "work_key"), [("A2", "client_work"), ("B2", "helper_work")])
def test_cell_rejects_origin_discontinuity_across_post_warm_up_samples(cell: str, work_key: str) -> None:
    document = _cell_document(cell, 1)
    document["samples"][1][work_key]["origin_id"] = "f" * 32

    with pytest.raises(PressureAbValidationError, match="origin.*continuity"):
        parse_pressure_ab_cell_document(document)


@pytest.mark.parametrize(
    ("cell", "client_pid_present", "port_file_present", "valid"),
    [
        ("A1", False, False, True),
        ("B1", False, False, True),
        ("A2", True, True, True),
        ("B2", True, True, True),
        ("A1", True, True, False),
        ("A2", True, False, False),
        ("A2", False, True, False),
        ("B2", False, False, False),
    ],
)
def test_validate_client_argument_pair_requires_exact_cell_pairing(
    cell: str,
    client_pid_present: bool,
    port_file_present: bool,
    valid: bool,
) -> None:
    if valid:
        validate_client_argument_pair(
            cell,
            client_pid_present=client_pid_present,
            port_file_present=port_file_present,
        )
    else:
        with pytest.raises(PressureAbValidationError, match="client argument"):
            validate_client_argument_pair(
                cell,
                client_pid_present=client_pid_present,
                port_file_present=port_file_present,
            )


@pytest.mark.parametrize(
    "mutator",
    [
        lambda document: document["state"].__setitem__("client", "running"),
        lambda document: document["state"].__setitem__("helper", "full_helper"),
        lambda document: document["state"].__setitem__("client_backend", "helper_selected"),
        lambda document: document["state"].__setitem__("client_pid_argument", "provided"),
        lambda document: document["state"].__setitem__("capture_diagnostics_enabled", True),
    ],
)
def test_cell_rejects_state_that_does_not_match_exact_cell_contract(mutator) -> None:
    document = _cell_document("A1", 1)
    mutator(document)

    with pytest.raises(PressureAbValidationError, match="state|diagnostics|argument"):
        parse_pressure_ab_cell_document(document)


def test_complete_run_accepts_four_cells_and_preserves_actual_execution_order() -> None:
    documents = [
        _cell_document("B1", 1),
        _cell_document("A1", 2),
        _cell_document("B2", 3),
        _cell_document("A2", 4),
    ]

    run = parse_complete_pressure_ab_run(reversed(documents))

    assert tuple(cell.cell for cell in run.cells) == ("B1", "A1", "B2", "A2")
    assert tuple(cell.execution_order for cell in run.cells) == (1, 2, 3, 4)
    assert all(tuple(sample.repetition for sample in cell.samples) == (1, 2, 3) for cell in run.cells)


@pytest.mark.parametrize(
    "mutator",
    [
        lambda documents: documents.pop(),
        lambda documents: documents.__setitem__(3, deepcopy(documents[0])),
        lambda documents: documents[3].__setitem__("execution_order", 1),
        lambda documents: documents[3]["provenance"].__setitem__("fixture_sha256", "3" * 64),
        lambda documents: documents[3]["provenance"].__setitem__("quiet_host", False),
    ],
)
def test_complete_run_rejects_incomplete_duplicate_or_mixed_evidence(mutator) -> None:
    documents = [_cell_document(cell, index) for index, cell in enumerate(PRESSURE_AB_CELLS, start=1)]
    mutator(documents)

    with pytest.raises(PressureAbValidationError):
        parse_complete_pressure_ab_run(documents)


def test_complete_run_loader_requires_four_distinct_immutable_cell_documents(tmp_path) -> None:
    paths = []
    for index, cell in enumerate(PRESSURE_AB_CELLS, start=1):
        path = tmp_path / f"{cell}.json"
        path.write_text(json.dumps(_cell_document(cell, index)), encoding="utf-8")
        paths.append(path)

    run = load_complete_pressure_ab_run(paths)

    assert tuple(cell.cell for cell in run.cells) == PRESSURE_AB_CELLS
    with pytest.raises(dataclasses.FrozenInstanceError):
        run.cells[0].cell = "B2"
    with pytest.raises(PressureAbValidationError, match="distinct"):
        load_complete_pressure_ab_run((paths[0], paths[0], paths[2], paths[3]))


def _parsed_run(
    *,
    shell_cpu: dict[str, tuple[float, float, float]] | None = None,
    execution_order: tuple[str, ...] = PRESSURE_AB_CELLS,
):
    order_by_cell = {cell: index for index, cell in enumerate(execution_order, start=1)}
    documents = [_cell_document(cell, order_by_cell[cell]) for cell in reversed(PRESSURE_AB_CELLS)]
    if shell_cpu is not None:
        for document in documents:
            cell = document["cell"]
            for sample, value in zip(document["samples"], shell_cpu[cell], strict=True):
                sample["resources"]["shell"]["cpu_percent"] = _distribution(value)
    return parse_complete_pressure_ab_run(documents)


def _reviewed_bounds(*entries: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "review": {
            "state": "reviewed",
            "captured_date": "2026-08-02",
            "method": "all_repetitions_with_absolute_noise_floors",
            "rationale": "Reviewed all repetitions with fixed attribution and noise floors.",
            "evidence_reference": "pressure_ab_quiet_run_v1",
        },
        "bounds": list(entries),
    }


def _bound(
    metric_path: str,
    contrast: str,
    minimum: float,
    maximum: float,
    absolute_noise_floor: float = 0.0,
) -> dict[str, object]:
    return {
        "metric_path": metric_path,
        "contrast": contrast,
        "minimum_inclusive": minimum,
        "maximum_inclusive": maximum,
        "absolute_noise_floor": absolute_noise_floor,
    }


def test_analysis_aggregates_nested_runner_metrics_with_nearest_rank_statistics() -> None:
    run = _parsed_run(
        shell_cpu={
            "A1": (1.0, 3.0, 2.0),
            "A2": (4.0, 4.0, 4.0),
            "B1": (5.0, 5.0, 5.0),
            "B2": (6.0, 6.0, 6.0),
        }
    )
    analysis = analyze_pressure_ab_run(run)

    assert analysis.cells["A1"]["resources.shell.cpu_percent"] == type(
        analysis.cells["A1"]["resources.shell.cpu_percent"]
    )(
        availability="available",
        count=3,
        median=2.0,
        p95=3.0,
        minimum=1.0,
        maximum=3.0,
        reason=None,
    )
    assert analysis.cells["B2"]["client_work.repaint_total"].count == 3
    assert analysis.cells["B2"]["helper_work.target_queries"].count == 3
    assert analysis.cells["B2"]["actor_counts.shell_raster_region_count"].count == 3
    assert analysis.cells["B2"]["warning_counts.shell_warnings"].count == 3


def test_analysis_distinguishes_structural_zero_from_provider_unavailable() -> None:
    analysis = analyze_pressure_ab_run(_parsed_run())

    stopped_client = analysis.cells["A1"]["resources.client.cpu_percent"]
    disabled_helper = analysis.cells["A2"]["helper_work.target_queries"]
    unavailable_gpu = analysis.cells["B2"]["resources.gpu.utilization_percent"]
    assert (stopped_client.availability, stopped_client.median) == ("structural_zero", 0.0)
    assert (disabled_helper.availability, disabled_helper.median) == ("structural_zero", 0.0)
    assert unavailable_gpu.availability == "unavailable"
    assert unavailable_gpu.reason == "provider_unavailable"
    assert unavailable_gpu.median is None


@pytest.mark.parametrize("provider", ("gpu", "warning"))
def test_analysis_rejects_mixed_provider_availability_within_a_cell(provider: str) -> None:
    documents = [_cell_document(cell, index) for index, cell in enumerate(PRESSURE_AB_CELLS, start=1)]
    b2 = next(document for document in documents if document["cell"] == "B2")
    if provider == "gpu":
        b2["samples"][0]["resources"]["gpu"] = {
            "available": True,
            "utilization_percent": _distribution(1.0),
            "vram_mib": _distribution(100.0),
        }
    else:
        b2["samples"][0]["warning_counts"] = {
            "available": False,
            "mutter_assertions": 0,
            "shell_warnings": 0,
        }
    run = parse_complete_pressure_ab_run(documents)

    with pytest.raises(PressureAbValidationError, match="mixed.*availability"):
        analyze_pressure_ab_run(run)


def test_analysis_computes_all_five_exact_contrasts_from_cell_medians() -> None:
    run = _parsed_run(
        shell_cpu={
            "A1": (10.0, 10.0, 10.0),
            "A2": (13.0, 13.0, 13.0),
            "B1": (12.0, 12.0, 12.0),
            "B2": (20.0, 20.0, 20.0),
        }
    )
    analysis = analyze_pressure_ab_run(run)
    metric = "resources.shell.cpu_percent"

    assert tuple(analysis.contrasts) == PRESSURE_AB_CONTRASTS
    assert analysis.contrasts["enabled_idle_helper"][metric].value == 2.0
    assert analysis.contrasts["client_helper_disabled"][metric].value == 3.0
    assert analysis.contrasts["client_helper_enabled"][metric].value == 8.0
    assert analysis.contrasts["helper_client_interaction"][metric].value == 5.0
    assert analysis.contrasts["overall_integrated"][metric].value == 10.0


def test_contrasts_preserve_genuine_provider_unavailability() -> None:
    analysis = analyze_pressure_ab_run(_parsed_run())

    value = analysis.contrasts["overall_integrated"]["resources.gpu.utilization_percent"]

    assert value.available is False
    assert value.value is None
    assert value.reason == "provider_unavailable"


def test_analysis_requires_the_strict_complete_run_model() -> None:
    with pytest.raises(TypeError, match="PressureAbRun"):
        analyze_pressure_ab_run({})
    with pytest.raises(PressureAbValidationError, match="four strict"):
        analyze_pressure_ab_run(PressureAbRun(()))


def test_reviewed_bounds_are_strict_frozen_and_sorted() -> None:
    analysis = analyze_pressure_ab_run(_parsed_run())
    raw = _reviewed_bounds(
        _bound("resources.shell.cpu_percent", "overall_integrated", -5.0, 5.0),
        _bound("helper_work.target_queries", "client_helper_enabled", 0.0, 10.0),
    )

    reviewed = parse_pressure_ab_reviewed_bounds(raw, analysis)

    assert tuple((item.metric_path, item.contrast) for item in reviewed.bounds) == (
        ("helper_work.target_queries", "client_helper_enabled"),
        ("resources.shell.cpu_percent", "overall_integrated"),
    )
    assert reviewed.review.method == "all_repetitions_with_absolute_noise_floors"
    with pytest.raises(dataclasses.FrozenInstanceError):
        reviewed.review.state = "changed"


@pytest.mark.parametrize(
    "mutator",
    [
        lambda raw: raw["review"].__setitem__("state", "draft"),
        lambda raw: raw["review"].__setitem__("method", "favorable_singleton"),
        lambda raw: raw["review"].__setitem__("rationale", "/home/private/review.txt"),
        lambda raw: raw["bounds"][0].__setitem__("metric_path", "unknown.metric"),
        lambda raw: raw["bounds"][0].__setitem__("contrast", "unknown_contrast"),
        lambda raw: raw["bounds"][0].__setitem__("minimum_inclusive", 20.0),
        lambda raw: raw["bounds"][0].__setitem__("absolute_noise_floor", -1.0),
        lambda raw: raw["bounds"].append(deepcopy(raw["bounds"][0])),
    ],
)
def test_reviewed_bounds_reject_unsafe_unreviewed_or_incompatible_inputs(mutator) -> None:
    analysis = analyze_pressure_ab_run(_parsed_run())
    raw = _reviewed_bounds(_bound("resources.shell.cpu_percent", "overall_integrated", -10.0, 10.0))
    mutator(raw)

    with pytest.raises(PressureAbValidationError):
        parse_pressure_ab_reviewed_bounds(raw, analysis)


def test_bound_evaluation_uses_exact_observed_contrast_and_inclusive_ranges() -> None:
    analysis = analyze_pressure_ab_run(
        _parsed_run(
            shell_cpu={
                "A1": (10.0, 10.0, 10.0),
                "A2": (13.0, 13.0, 13.0),
                "B1": (12.0, 12.0, 12.0),
                "B2": (20.0, 20.0, 20.0),
            }
        )
    )
    reviewed = parse_pressure_ab_reviewed_bounds(
        _reviewed_bounds(
            _bound("resources.shell.cpu_percent", "enabled_idle_helper", 2.0, 2.0),
            _bound("resources.shell.cpu_percent", "overall_integrated", 0.0, 9.0, 0.5),
        ),
        analysis,
    )

    results = evaluate_pressure_ab_bounds(analysis, reviewed)

    assert [(result.contrast, result.observed, result.passed) for result in results] == [
        ("enabled_idle_helper", 2.0, True),
        ("overall_integrated", 10.0, False),
    ]


def test_bound_evaluation_preserves_absolute_noise_floor() -> None:
    analysis = analyze_pressure_ab_run(
        _parsed_run(
            shell_cpu={
                "A1": (10.0, 10.0, 10.0),
                "A2": (13.0, 13.0, 13.0),
                "B1": (12.0, 12.0, 12.0),
                "B2": (20.0, 20.0, 20.0),
            }
        )
    )
    reviewed = parse_pressure_ab_reviewed_bounds(
        _reviewed_bounds(
            _bound("resources.shell.cpu_percent", "overall_integrated", 0.0, 9.0, 1.0),
        ),
        analysis,
    )

    result = evaluate_pressure_ab_bounds(analysis, reviewed)[0]

    assert result.absolute_noise_floor == 1.0
    assert result.observed == 10.0
    assert result.passed is True


def test_report_is_deterministic_sanitized_and_contains_required_sections() -> None:
    shell_cpu = {
        "A1": (10.0, 10.0, 10.0),
        "A2": (13.0, 13.0, 13.0),
        "B1": (12.0, 12.0, 12.0),
        "B2": (20.0, 20.0, 20.0),
    }
    first_analysis = analyze_pressure_ab_run(
        _parsed_run(shell_cpu=shell_cpu, execution_order=("B1", "A1", "B2", "A2"))
    )
    second_analysis = analyze_pressure_ab_run(
        _parsed_run(shell_cpu=shell_cpu, execution_order=("B1", "A1", "B2", "A2"))
    )
    first_raw = _reviewed_bounds(
        _bound("resources.shell.cpu_percent", "overall_integrated", 0.0, 10.0),
        _bound("resources.shell.cpu_percent", "enabled_idle_helper", -1.0, 3.0),
    )
    second_raw = deepcopy(first_raw)
    second_raw["bounds"].reverse()
    first_bounds = parse_pressure_ab_reviewed_bounds(first_raw, first_analysis)
    second_bounds = parse_pressure_ab_reviewed_bounds(second_raw, second_analysis)

    first = render_pressure_ab_report(first_analysis, first_bounds)
    second = render_pressure_ab_report(second_analysis, second_bounds)

    assert first == second
    assert first.startswith("# Controlled Helper Pressure A/B Report\n")
    assert "Execution order: `B1 -> A1 -> B2 -> A2`" in first
    assert "| `B1-A1` | Enabled-idle helper cost |" in first
    assert "| `A2-A1` | Client cost with helper disabled |" in first
    assert "| `B2-B1` | Client cost with helper enabled |" in first
    assert "| `(B2-B1)-(A2-A1)` | Helper/client interaction |" in first
    assert "| `B2-A1` | Overall integrated cost |" in first
    assert "## Reviewed pressure-reduction acceptance bounds" in first
    assert "all_repetitions_with_absolute_noise_floors" in first
    assert "not migration-regression thresholds" in first
    assert "`thresholds.json` must remain absent" in first
    assert "a" * 32 not in first
    assert "client_pid" not in first


def test_synthetic_report_rendering_is_memory_only(tmp_path) -> None:
    analysis = analyze_pressure_ab_run(_parsed_run())
    bounds = parse_pressure_ab_reviewed_bounds(
        _reviewed_bounds(_bound("resources.shell.cpu_percent", "overall_integrated", -10.0, 10.0)),
        analysis,
    )

    rendered = render_pressure_ab_report(analysis, bounds)

    assert rendered
    assert not (tmp_path / "pressure-ab-report.md").exists()
    assert not (tmp_path / "thresholds.json").exists()


def test_four_immutable_cell_files_reach_strict_in_memory_report(tmp_path) -> None:
    paths = []
    for index, cell in enumerate(PRESSURE_AB_CELLS, start=1):
        path = tmp_path / f"{cell}.json"
        path.write_text(json.dumps(_cell_document(cell, index)), encoding="utf-8")
        paths.append(path)

    run = load_complete_pressure_ab_run(tuple(reversed(paths)))
    analysis = analyze_pressure_ab_run(run)
    bounds = parse_pressure_ab_reviewed_bounds(
        _reviewed_bounds(_bound("resources.shell.cpu_percent", "overall_integrated", -10.0, 10.0)),
        analysis,
    )
    rendered = render_pressure_ab_report(analysis, bounds)

    assert "# Controlled Helper Pressure A/B Report" in rendered
    assert "Reviewed bound result: **PASS**" in rendered
    assert not (tmp_path / "pressure-ab-report.md").exists()
    assert not (tmp_path / "thresholds.json").exists()
