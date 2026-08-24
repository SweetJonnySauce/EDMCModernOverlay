"""Deterministic analysis and Markdown reporting for strict pressure A/B evidence."""

from __future__ import annotations

import math
import re
import statistics
from dataclasses import dataclass
from datetime import date
from types import MappingProxyType
from typing import Mapping, Sequence

from overlay_client.backend.pressure_ab import (
    PRESSURE_AB_CELLS,
    WORK_COUNTER_KEYS,
    PressureAbCellDocument,
    PressureAbProvenance,
    PressureAbResourceEvidence,
    PressureAbRun,
    PressureAbSample,
    PressureAbValidationError,
    PressureAbWorkEvidence,
    _bounded_number,
    _exact_fields,
    _mapping,
    _privacy_scan,
)


PRESSURE_AB_CONTRASTS = (
    "enabled_idle_helper",
    "client_helper_disabled",
    "client_helper_enabled",
    "helper_client_interaction",
    "overall_integrated",
)

_MAX_EVIDENCE_NUMBER = 1_000_000_000.0
_HELPER_COUNTER_KEYS = ("target_queries", "presentation_calls")
_ACTOR_COUNT_KEYS = (
    "shell_actor_proof_visible",
    "shell_raster_frame_visible",
    "shell_raster_region_count",
)
_CONTRAST_PRESENTATION = MappingProxyType(
    {
        "enabled_idle_helper": ("B1-A1", "Enabled-idle helper cost"),
        "client_helper_disabled": ("A2-A1", "Client cost with helper disabled"),
        "client_helper_enabled": ("B2-B1", "Client cost with helper enabled"),
        "helper_client_interaction": (
            "(B2-B1)-(A2-A1)",
            "Helper/client interaction",
        ),
        "overall_integrated": ("B2-A1", "Overall integrated cost"),
    }
)
_REVIEW_METHOD = "all_repetitions_with_absolute_noise_floors"
_SAFE_EVIDENCE_REFERENCE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,95}$")
_SAFE_REVIEW_TEXT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .,;:()_+\-]{0,279}$")


@dataclass(frozen=True)
class PressureAbMetricStatistics:
    """Per-cell statistics across all three repetitions for one metric."""

    availability: str
    count: int
    median: float | None
    p95: float | None
    minimum: float | None
    maximum: float | None
    reason: str | None = None


@dataclass(frozen=True)
class PressureAbContrastValue:
    """One required A/B contrast or an explicit unavailable value."""

    available: bool
    value: float | None
    reason: str | None = None


@dataclass(frozen=True)
class PressureAbAnalysis:
    """Deterministic per-cell aggregation and the five required contrasts."""

    provenance: PressureAbProvenance
    execution_order: tuple[str, ...]
    cells: Mapping[str, Mapping[str, PressureAbMetricStatistics]]
    contrasts: Mapping[str, Mapping[str, PressureAbContrastValue]]


@dataclass(frozen=True)
class PressureAbBoundsReview:
    """Sanitized provenance for a human-reviewed pressure-bound decision."""

    state: str
    captured_date: str
    method: str
    rationale: str
    evidence_reference: str


@dataclass(frozen=True)
class PressureAbAcceptanceBound:
    """Inclusive reviewed range for one metric and one fixed contrast."""

    metric_path: str
    contrast: str
    minimum_inclusive: float
    maximum_inclusive: float
    absolute_noise_floor: float


@dataclass(frozen=True)
class PressureAbReviewedBounds:
    """In-memory report-only reviewed pressure-reduction bounds."""

    review: PressureAbBoundsReview
    bounds: tuple[PressureAbAcceptanceBound, ...]


@dataclass(frozen=True)
class PressureAbBoundResult:
    """Evaluation of one reviewed range against its exact observed contrast."""

    metric_path: str
    contrast: str
    minimum_inclusive: float
    maximum_inclusive: float
    absolute_noise_floor: float
    observed: float
    passed: bool


@dataclass(frozen=True)
class _PressureAbSampleMetric:
    availability: str
    value: float | None
    reason: str | None = None



def _available_sample_metric(value: int | float) -> _PressureAbSampleMetric:
    return _PressureAbSampleMetric("available", float(value))


def _structural_zero_sample_metric() -> _PressureAbSampleMetric:
    return _PressureAbSampleMetric("structural_zero", 0.0, "structural_absence")


def _unavailable_sample_metric(reason: str) -> _PressureAbSampleMetric:
    return _PressureAbSampleMetric("unavailable", None, reason)


def _resource_sample_metrics(
    prefix: str,
    evidence: PressureAbResourceEvidence,
    metric_names: Sequence[str],
    *,
    structural_absence: bool,
) -> dict[str, _PressureAbSampleMetric]:
    if not evidence.available:
        value = _structural_zero_sample_metric() if structural_absence else _unavailable_sample_metric(
            evidence.reason or "provider_unavailable"
        )
        return {f"{prefix}.{metric}": value for metric in metric_names}
    if evidence.distributions is None or set(evidence.distributions) != set(metric_names):
        raise PressureAbValidationError(f"{prefix} distributions are incomplete for analysis")
    return {
        f"{prefix}.{metric}": _available_sample_metric(evidence.distributions[metric].median)
        for metric in metric_names
    }


def _work_sample_metrics(
    prefix: str,
    evidence: PressureAbWorkEvidence,
    metric_names: Sequence[str],
) -> dict[str, _PressureAbSampleMetric]:
    if not evidence.available:
        return {f"{prefix}.{metric}": _structural_zero_sample_metric() for metric in metric_names}
    if set(evidence.counters) != set(metric_names):
        raise PressureAbValidationError(f"{prefix} counters are incomplete for analysis")
    return {
        f"{prefix}.{metric}": _available_sample_metric(evidence.counters[metric])
        for metric in metric_names
    }


def _sample_metrics(sample: PressureAbSample) -> Mapping[str, _PressureAbSampleMetric]:
    metrics: dict[str, _PressureAbSampleMetric] = {}
    metrics.update(
        _resource_sample_metrics(
            "resources.shell",
            sample.resources["shell"],
            ("cpu_percent", "rss_kib", "context_switches"),
            structural_absence=False,
        )
    )
    metrics.update(
        _resource_sample_metrics(
            "resources.client",
            sample.resources["client"],
            ("cpu_percent", "rss_kib", "context_switches"),
            structural_absence=True,
        )
    )
    metrics.update(
        _resource_sample_metrics(
            "resources.gpu",
            sample.resources["gpu"],
            ("utilization_percent", "vram_mib"),
            structural_absence=False,
        )
    )
    metrics.update(_work_sample_metrics("client_work", sample.client_work, WORK_COUNTER_KEYS))
    metrics.update(_work_sample_metrics("helper_work", sample.helper_work, _HELPER_COUNTER_KEYS))
    if sample.actor_counts.available:
        if set(sample.actor_counts.values) != set(_ACTOR_COUNT_KEYS):
            raise PressureAbValidationError("actor_counts are incomplete for analysis")
        metrics.update(
            {
                f"actor_counts.{metric}": _available_sample_metric(sample.actor_counts.values[metric])
                for metric in _ACTOR_COUNT_KEYS
            }
        )
    else:
        metrics.update(
            {f"actor_counts.{metric}": _structural_zero_sample_metric() for metric in _ACTOR_COUNT_KEYS}
        )
    warnings_available = sample.warning_counts["available"]
    if not isinstance(warnings_available, bool):
        raise PressureAbValidationError("warning availability is invalid for analysis")
    for metric in ("mutter_assertions", "shell_warnings"):
        path = f"warning_counts.{metric}"
        metrics[path] = (
            _available_sample_metric(int(sample.warning_counts[metric]))
            if warnings_available
            else _unavailable_sample_metric("warning_provider_unavailable")
        )
    return MappingProxyType(dict(sorted(metrics.items())))


def _aggregate_metric(
    values: Sequence[_PressureAbSampleMetric],
    *,
    metric_path: str,
) -> PressureAbMetricStatistics:
    availability = {value.availability for value in values}
    if len(availability) != 1:
        raise PressureAbValidationError(f"mixed provider availability for {metric_path}")
    state = next(iter(availability))
    if state == "unavailable":
        reasons = {value.reason for value in values}
        if len(reasons) != 1:
            raise PressureAbValidationError(f"mixed unavailable reasons for {metric_path}")
        return PressureAbMetricStatistics(
            availability="unavailable",
            count=0,
            median=None,
            p95=None,
            minimum=None,
            maximum=None,
            reason=next(iter(reasons)),
        )
    numeric = [value.value for value in values]
    if any(value is None for value in numeric):
        raise PressureAbValidationError(f"available metric {metric_path} lacks a value")
    ordered = sorted(float(value) for value in numeric if value is not None)
    if state == "structural_zero" and any(value != 0.0 for value in ordered):
        raise PressureAbValidationError(f"structural-zero metric {metric_path} is nonzero")
    return PressureAbMetricStatistics(
        availability=state,
        count=len(ordered),
        median=float(statistics.median(ordered)),
        p95=ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)],
        minimum=ordered[0],
        maximum=ordered[-1],
        reason="structural_absence" if state == "structural_zero" else None,
    )


def _aggregate_cell(cell: PressureAbCellDocument) -> Mapping[str, PressureAbMetricStatistics]:
    repetitions = tuple(_sample_metrics(sample) for sample in cell.samples)
    metric_paths = tuple(repetitions[0])
    if any(tuple(metrics) != metric_paths for metrics in repetitions[1:]):
        raise PressureAbValidationError(f"cell {cell.cell} metric paths differ across repetitions")
    return MappingProxyType(
        {
            metric_path: _aggregate_metric(
                tuple(metrics[metric_path] for metrics in repetitions),
                metric_path=metric_path,
            )
            for metric_path in metric_paths
        }
    )


def _contrast_value(
    operands: Sequence[tuple[PressureAbMetricStatistics, float]],
) -> PressureAbContrastValue:
    unavailable = [statistic.reason for statistic, _coefficient in operands if statistic.median is None]
    if unavailable:
        reasons = sorted({reason or "provider_unavailable" for reason in unavailable})
        return PressureAbContrastValue(False, None, ",".join(reasons))
    value = 0.0
    for statistic, coefficient in operands:
        assert statistic.median is not None
        value += statistic.median * coefficient
    return PressureAbContrastValue(True, value)


def _validate_run_for_analysis(run: PressureAbRun) -> Mapping[str, PressureAbCellDocument]:
    if len(run.cells) != 4:
        raise PressureAbValidationError("analysis requires four strict pressure A/B cells")
    by_cell = {cell.cell: cell for cell in run.cells}
    if set(by_cell) != set(PRESSURE_AB_CELLS) or len(by_cell) != 4:
        raise PressureAbValidationError("analysis requires exact A1/A2/B1/B2 cells")
    if {cell.execution_order for cell in run.cells} != {1, 2, 3, 4}:
        raise PressureAbValidationError("analysis requires unique execution order 1-4")
    provenance = run.cells[0].provenance
    for cell in run.cells:
        if not isinstance(cell, PressureAbCellDocument) or cell.provenance != provenance:
            raise PressureAbValidationError("analysis requires strict cells with fixed provenance")
        if tuple(sample.repetition for sample in cell.samples) != (1, 2, 3):
            raise PressureAbValidationError("analysis requires all three strict repetitions")
        if any(any(sample.safety.values()) or any(sample.continuity.values()) for sample in cell.samples):
            raise PressureAbValidationError("analysis rejects unsafe or discontinuous evidence")
    return MappingProxyType(by_cell)


def analyze_pressure_ab_run(run: PressureAbRun) -> PressureAbAnalysis:
    """Aggregate one strict complete run and calculate the five fixed A/B contrasts."""

    if not isinstance(run, PressureAbRun):
        raise TypeError("run must be a PressureAbRun from the strict parser")
    by_cell = _validate_run_for_analysis(run)
    cells = MappingProxyType({cell: _aggregate_cell(by_cell[cell]) for cell in PRESSURE_AB_CELLS})
    metric_paths = tuple(cells["A1"])
    if any(tuple(cells[cell]) != metric_paths for cell in PRESSURE_AB_CELLS[1:]):
        raise PressureAbValidationError("cell metric paths are incompatible")
    contrasts: dict[str, Mapping[str, PressureAbContrastValue]] = {}
    for contrast in PRESSURE_AB_CONTRASTS:
        values: dict[str, PressureAbContrastValue] = {}
        for metric_path in metric_paths:
            a1 = cells["A1"][metric_path]
            a2 = cells["A2"][metric_path]
            b1 = cells["B1"][metric_path]
            b2 = cells["B2"][metric_path]
            operands = {
                "enabled_idle_helper": ((b1, 1.0), (a1, -1.0)),
                "client_helper_disabled": ((a2, 1.0), (a1, -1.0)),
                "client_helper_enabled": ((b2, 1.0), (b1, -1.0)),
                "helper_client_interaction": ((b2, 1.0), (b1, -1.0), (a2, -1.0), (a1, 1.0)),
                "overall_integrated": ((b2, 1.0), (a1, -1.0)),
            }[contrast]
            values[metric_path] = _contrast_value(operands)
        contrasts[contrast] = MappingProxyType(values)
    execution_order = tuple(
        cell.cell for cell in sorted(run.cells, key=lambda value: value.execution_order)
    )
    return PressureAbAnalysis(
        provenance=run.cells[0].provenance,
        execution_order=execution_order,
        cells=cells,
        contrasts=MappingProxyType(contrasts),
    )


def _bounded_signed_number(value: object, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PressureAbValidationError(f"{label} must be numeric")
    numeric = float(value)
    if not math.isfinite(numeric) or abs(numeric) > _MAX_EVIDENCE_NUMBER:
        raise PressureAbValidationError(f"{label} must be finite and bounded")
    return numeric


def parse_pressure_ab_reviewed_bounds(
    raw_value: Mapping[str, object],
    analysis: PressureAbAnalysis,
) -> PressureAbReviewedBounds:
    """Validate report-only reviewed bounds without inferring or serializing them."""

    if not isinstance(analysis, PressureAbAnalysis):
        raise TypeError("analysis must be PressureAbAnalysis")
    _privacy_scan(raw_value, location="reviewed_bounds")
    raw = _mapping(raw_value, label="reviewed bounds")
    _exact_fields(raw, {"schema_version", "review", "bounds"}, label="reviewed bounds")
    if raw["schema_version"] != 1:
        raise PressureAbValidationError("reviewed bounds schema_version must be 1")
    review_raw = _mapping(raw["review"], label="bounds review")
    _exact_fields(
        review_raw,
        {"state", "captured_date", "method", "rationale", "evidence_reference"},
        label="bounds review",
    )
    if review_raw["state"] != "reviewed" or review_raw["method"] != _REVIEW_METHOD:
        raise PressureAbValidationError("bounds require reviewed all-repetitions selection")
    captured_date = review_raw["captured_date"]
    if not isinstance(captured_date, str):
        raise PressureAbValidationError("bounds captured_date must be ISO-8601")
    try:
        date.fromisoformat(captured_date)
    except ValueError as exc:
        raise PressureAbValidationError("bounds captured_date must be ISO-8601") from exc
    rationale = review_raw["rationale"]
    if not isinstance(rationale, str) or _SAFE_REVIEW_TEXT.fullmatch(rationale) is None:
        raise PressureAbValidationError("bounds rationale must be sanitized review text")
    evidence_reference = review_raw["evidence_reference"]
    if not isinstance(evidence_reference, str) or _SAFE_EVIDENCE_REFERENCE.fullmatch(evidence_reference) is None:
        raise PressureAbValidationError("bounds evidence_reference must be privacy-safe")
    bounds_raw = raw["bounds"]
    if not isinstance(bounds_raw, list) or not bounds_raw:
        raise PressureAbValidationError("reviewed bounds require at least one bound")
    known_metrics = set(analysis.cells["A1"])
    bounds: list[PressureAbAcceptanceBound] = []
    seen: set[tuple[str, str]] = set()
    for index, value in enumerate(bounds_raw):
        entry = _mapping(value, label=f"bounds[{index}]")
        _exact_fields(
            entry,
            {
                "metric_path",
                "contrast",
                "minimum_inclusive",
                "maximum_inclusive",
                "absolute_noise_floor",
            },
            label=f"bounds[{index}]",
        )
        metric_path = entry["metric_path"]
        contrast = entry["contrast"]
        if not isinstance(metric_path, str) or metric_path not in known_metrics:
            raise PressureAbValidationError("reviewed bound metric_path is unknown")
        if not isinstance(contrast, str) or contrast not in PRESSURE_AB_CONTRASTS:
            raise PressureAbValidationError("reviewed bound contrast is unknown")
        key = (metric_path, contrast)
        if key in seen:
            raise PressureAbValidationError("reviewed bounds contain a duplicate metric/contrast pair")
        seen.add(key)
        minimum = _bounded_signed_number(entry["minimum_inclusive"], label="minimum_inclusive")
        maximum = _bounded_signed_number(entry["maximum_inclusive"], label="maximum_inclusive")
        noise_floor = _bounded_number(entry["absolute_noise_floor"], label="absolute_noise_floor")
        if minimum > maximum:
            raise PressureAbValidationError("reviewed bound minimum exceeds maximum")
        if not analysis.contrasts[contrast][metric_path].available:
            raise PressureAbValidationError("reviewed bound cannot target an unavailable contrast")
        bounds.append(PressureAbAcceptanceBound(metric_path, contrast, minimum, maximum, noise_floor))
    return PressureAbReviewedBounds(
        review=PressureAbBoundsReview(
            state="reviewed",
            captured_date=captured_date,
            method=_REVIEW_METHOD,
            rationale=rationale,
            evidence_reference=evidence_reference,
        ),
        bounds=tuple(sorted(bounds, key=lambda item: (item.metric_path, item.contrast))),
    )


def evaluate_pressure_ab_bounds(
    analysis: PressureAbAnalysis,
    reviewed_bounds: PressureAbReviewedBounds,
) -> tuple[PressureAbBoundResult, ...]:
    """Evaluate every reviewed range against its exact fixed contrast."""

    if not isinstance(analysis, PressureAbAnalysis) or not isinstance(
        reviewed_bounds, PressureAbReviewedBounds
    ):
        raise TypeError("bound evaluation requires PressureAbAnalysis and PressureAbReviewedBounds")
    results: list[PressureAbBoundResult] = []
    for bound in reviewed_bounds.bounds:
        observed = analysis.contrasts[bound.contrast][bound.metric_path]
        if not observed.available or observed.value is None:
            raise PressureAbValidationError("reviewed bound contrast became unavailable")
        results.append(
            PressureAbBoundResult(
                metric_path=bound.metric_path,
                contrast=bound.contrast,
                minimum_inclusive=bound.minimum_inclusive,
                maximum_inclusive=bound.maximum_inclusive,
                absolute_noise_floor=bound.absolute_noise_floor,
                observed=observed.value,
                passed=(
                    bound.minimum_inclusive - bound.absolute_noise_floor
                    <= observed.value
                    <= bound.maximum_inclusive + bound.absolute_noise_floor
                ),
            )
        )
    return tuple(results)


def _format_number(value: float) -> str:
    if value == 0.0:
        return "0"
    return f"{value:.6f}".rstrip("0").rstrip(".")


def _format_metric_statistics(statistics_value: PressureAbMetricStatistics) -> str:
    if statistics_value.median is None:
        return f"unavailable ({statistics_value.reason})"
    prefix = "structural zero; " if statistics_value.availability == "structural_zero" else ""
    assert statistics_value.p95 is not None
    assert statistics_value.minimum is not None
    assert statistics_value.maximum is not None
    return (
        f"{prefix}median={_format_number(statistics_value.median)}; "
        f"p95={_format_number(statistics_value.p95)}; "
        f"range={_format_number(statistics_value.minimum)}..{_format_number(statistics_value.maximum)}; "
        f"n={statistics_value.count}"
    )


def _format_contrast(value: PressureAbContrastValue) -> str:
    return _format_number(value.value) if value.available and value.value is not None else f"unavailable ({value.reason})"


def render_pressure_ab_report(
    analysis: PressureAbAnalysis,
    reviewed_bounds: PressureAbReviewedBounds,
) -> str:
    """Render deterministic sanitized Markdown without writing an evidence artifact."""

    if not isinstance(analysis, PressureAbAnalysis) or not isinstance(
        reviewed_bounds, PressureAbReviewedBounds
    ):
        raise TypeError("report rendering requires PressureAbAnalysis and PressureAbReviewedBounds")
    results = evaluate_pressure_ab_bounds(analysis, reviewed_bounds)
    result_by_key = {(result.metric_path, result.contrast): result for result in results}
    overall_state = "PASS" if all(result.passed for result in results) else "FAIL"
    provenance = analysis.provenance
    display = provenance.display
    lines = [
        "# Controlled Helper Pressure A/B Report",
        "",
        f"Reviewed bound result: **{overall_state}**",
        "",
        "## Evidence provenance",
        "",
        f"- Fixture SHA-256: `{provenance.fixture_sha256}`",
        f"- Source revision: `{provenance.source_revision}`",
        (
            "- Component versions: "
            f"plugin `{provenance.component_versions['plugin']}`, "
            f"client `{provenance.component_versions['client']}`, "
            f"helper `{provenance.component_versions['helper']}`"
        ),
        (
            "- Display: monitor `A`, "
            f"{display['width_px']}x{display['height_px']} px, "
            f"{_format_number(float(display['refresh_hz']))} Hz, 100% scale"
        ),
        f"- Workload: `{provenance.workload}`; quiet host confirmed: `yes`",
        f"- Execution order: `{' -> '.join(analysis.execution_order)}`",
        "- Timing: 300-second warm-up; three 60-second repetitions per cell",
        "- Capture/helper diagnostics: off; strict safety and continuity gates: passed",
        "",
        "## Contrast definitions",
        "",
        "| Formula | Attribution |",
        "| --- | --- |",
    ]
    for contrast in PRESSURE_AB_CONTRASTS:
        formula, label = _CONTRAST_PRESENTATION[contrast]
        lines.append(f"| `{formula}` | {label} |")
    lines.extend(
        [
            "",
            "## Per-cell statistics",
            "",
            "Each value summarizes all three repetitions; resource inputs are each repetition's 60-observation median.",
            "",
            "| Metric | A1 | A2 | B1 | B2 |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    metric_paths = tuple(analysis.cells["A1"])
    for metric_path in metric_paths:
        cells = " | ".join(
            _format_metric_statistics(analysis.cells[cell][metric_path]) for cell in PRESSURE_AB_CELLS
        )
        lines.append(f"| `{metric_path}` | {cells} |")
    lines.extend(
        [
            "",
            "## Four-cell contrasts",
            "",
            "| Metric | B1-A1 | A2-A1 | B2-B1 | Interaction | B2-A1 |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for metric_path in metric_paths:
        values = " | ".join(
            _format_contrast(analysis.contrasts[contrast][metric_path])
            for contrast in PRESSURE_AB_CONTRASTS
        )
        lines.append(f"| `{metric_path}` | {values} |")
    review = reviewed_bounds.review
    lines.extend(
        [
            "",
            "## Reviewed pressure-reduction acceptance bounds",
            "",
            f"- Review state: `{review.state}` on `{review.captured_date}`",
            f"- Selection method: `{review.method}`",
            f"- Evidence reference: `{review.evidence_reference}`",
            f"- Rationale: {review.rationale}",
            "",
            "| Metric | Contrast | Inclusive range | Absolute noise floor | Observed | Result |",
            "| --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for bound in reviewed_bounds.bounds:
        result = result_by_key[(bound.metric_path, bound.contrast)]
        formula = _CONTRAST_PRESENTATION[bound.contrast][0]
        lines.append(
            f"| `{bound.metric_path}` | `{formula}` | "
            f"[{_format_number(bound.minimum_inclusive)}, {_format_number(bound.maximum_inclusive)}] | "
            f"{_format_number(bound.absolute_noise_floor)} | "
            f"{_format_number(result.observed)} | {'PASS' if result.passed else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            "## Threshold separation",
            "",
            "These are pressure-reduction acceptance bounds, not migration-regression thresholds.",
            "`thresholds.json` must remain absent until the separate coherent repeated baseline is complete and reviewed.",
            "",
        ]
    )
    return "\n".join(lines)


