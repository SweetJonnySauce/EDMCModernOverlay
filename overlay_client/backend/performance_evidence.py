"""Pure, privacy-safe performance evidence models and comparison tooling.

This module is intentionally independent of Qt, Tk, compositor APIs, and production backend
routing.  It validates already-sanitized developer captures; it does not enable diagnostics or
collect data from a running process.
"""

from __future__ import annotations

import json
import math
import re
import statistics
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from types import MappingProxyType
from typing import Iterable, Mapping, Sequence


PERFORMANCE_MANIFEST_SCHEMA_VERSION = 1
PERFORMANCE_CAPTURE_SCHEMA_VERSION = 1
PERFORMANCE_SUMMARY_SCHEMA_VERSION = 1
PERFORMANCE_THRESHOLD_SCHEMA_VERSION = 1
PERFORMANCE_COMPARISON_SCHEMA_VERSION = 1

_SAFE_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]{0,95}$")
_SAFE_REVISION = re.compile(r"^[0-9a-f]{7,64}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_PERSONAL_PATH = re.compile(r"(?:^|\s)/(?:home|users)/[^\s]+|[A-Za-z]:\\+Users\\+[^\s]+", re.IGNORECASE)
_PROHIBITED_VALUE = re.compile(
    r"(?:^|[\s,;])(?:token|secret|owner[_ -]?id|target[_ -]?handle|window[_ -]?handle|"
    r"window[_ -]?title|command[_ -]?line|argv|screenshot|personal[_ -]?path)\s*[:=]",
    re.IGNORECASE,
)

_TARGET_ENVIRONMENT_FIELDS = frozenset(
    {
        "operating_system",
        "distribution",
        "distribution_version",
        "session_type",
        "desktop",
        "compositor",
        "compositor_version",
    }
)
_DIAGNOSTIC_TOGGLE_FIELDS = frozenset(
    {
        "developer_mode",
        "client_raster_timing",
        "helper_raster_timing",
        "presentation_timing",
        "repaint_metrics",
        "idle_cpu_sampling",
        "detailed_traces",
        "visual_debug_overlays",
    }
)
_OUTSIDE_GATE_CASES = frozenset({"mixed_scale", "vertical_layout", "primary_monitor_change", "exclusive_fullscreen"})
_MODES = frozenset({"windowed", "borderless_fullscreen"})
_ACTIONS = frozenset({"stable", "mode_transition", "monitor_handoff", "shell_interaction"})
_INTERACTIONS = frozenset({"none", "alt_tab", "overview"})
_WORKLOADS = frozenset({"idle_then_representative"})
_CAPTURE_ROLES = frozenset({"baseline", "candidate"})
_COMPOSITOR_COORDINATE_SPACE = "gnome_shell_global_logical"
_NEGATIVE_COORDINATE_SPACE = "primary_monitor_relative_logical"
_LATENCY_CLOCKS = {
    "presentation_cycle_ms": "client_elapsed",
    "end_to_stable_ms": "client_elapsed",
    "helper_apply_ms": "helper_elapsed",
}
_WORK_FIELDS = (
    "helper_health_calls",
    "helper_target_calls",
    "helper_presentation_calls",
    "transitions",
    "raster_builds",
    "raster_reuses",
    "raster_skips",
    "raster_bytes",
    "raster_regions",
    "raster_encode_ms",
    "helper_decode_ms",
    "helper_apply_ms",
    "repaints",
    "paints",
    "frame_builds",
)
_COUNT_WORK_FIELDS = frozenset(
    {
        "helper_health_calls",
        "helper_target_calls",
        "helper_presentation_calls",
        "transitions",
        "raster_builds",
        "raster_reuses",
        "raster_skips",
        "raster_bytes",
        "raster_regions",
        "repaints",
        "paints",
        "frame_builds",
    }
)
_MANUAL_OBSERVATION_FIELDS = (
    "dual_visible_presenters",
    "title_bar_intermediate",
    "monitor_relative_intermediate",
    "black_surface",
    "focus_trap",
    "unexpected_identity",
    "premature_commitment",
    "material_hitch",
)

REQUIRED_THRESHOLD_PATHS = (
    "latency.presentation_cycle_ms.p95",
    "latency.end_to_stable_ms.p95",
    "work.helper_health_calls_per_second",
    "work.helper_target_calls_per_second",
    "work.helper_presentation_calls_per_second",
    "work.helper_health_calls_per_transition",
    "work.helper_target_calls_per_transition",
    "work.helper_presentation_calls_per_transition",
    "work.raster_builds_per_second",
    "work.raster_reuses_per_second",
    "work.raster_skips_per_second",
    "work.raster_bytes_per_second",
    "work.raster_regions_per_second",
    "work.raster_encode_ms_per_second",
    "work.helper_decode_ms_per_second",
    "work.helper_apply_ms_per_second",
    "work.repaints_per_second",
    "work.paints_per_second",
    "work.frame_builds_per_second",
    "idle_cpu.client.mean",
    "idle_cpu.gnome_shell.mean",
)


class EvidenceValidationError(ValueError):
    """Raised when an evidence artifact violates its strict schema or privacy boundary."""


@dataclass(frozen=True, slots=True)
class TargetEnvironment:
    operating_system: str
    distribution: str
    distribution_version: str
    session_type: str
    desktop: str
    compositor: str
    compositor_version: str

    @property
    def stable_key(self) -> str:
        return "|".join(
            (
                self.operating_system,
                self.distribution,
                self.distribution_version,
                self.session_type,
                self.desktop,
                self.compositor,
                self.compositor_version,
            )
        )


@dataclass(frozen=True, slots=True)
class ReferenceVersions:
    plugin: str
    client: str
    helper_protocol: int
    source_revision: str


@dataclass(frozen=True, slots=True)
class CaptureVersions:
    plugin: str
    client: str
    helper_protocol: int
    source_revision: str
    architecture_stage: str

    @property
    def reference(self) -> ReferenceVersions:
        return ReferenceVersions(
            plugin=self.plugin,
            client=self.client,
            helper_protocol=self.helper_protocol,
            source_revision=self.source_revision,
        )


@dataclass(frozen=True, slots=True)
class PayloadFixture:
    fixture_id: str
    repository_path: str
    sha256: str


@dataclass(frozen=True, slots=True)
class DiagnosticConfiguration:
    configuration_id: str
    toggles: Mapping[str, bool]


@dataclass(frozen=True, slots=True)
class ClockDomains:
    client_elapsed: str
    helper_elapsed: str


@dataclass(frozen=True, slots=True)
class CaptureTiming:
    warm_up_seconds: int
    observation_seconds: int
    idle_cpu_seconds: int
    repetitions: int


@dataclass(frozen=True, slots=True)
class MonitorGeometry:
    monitor_id: str
    compositor_logical_x: int
    compositor_logical_y: int
    primary_relative_logical_x: int
    primary_relative_logical_y: int
    logical_width: int
    logical_height: int
    physical_width_px: int
    physical_height_px: int


@dataclass(frozen=True, slots=True)
class DisplayConfiguration:
    configuration_id: str
    scale_percent: int
    orientation: str
    primary_monitor: str
    compositor_coordinate_space: str
    negative_coordinate_space: str
    monitors: tuple[MonitorGeometry, ...]


@dataclass(frozen=True, slots=True)
class PerformanceScenario:
    scenario_id: str
    display_configuration_id: str
    action: str
    start_mode: str
    end_mode: str
    start_monitor: str
    end_monitor: str
    interaction: str
    payload_fixture_id: str
    diagnostic_configuration_id: str
    workload: str


@dataclass(frozen=True, slots=True)
class OutsideGateCase:
    case_id: str
    classification: str
    reason_code: str


@dataclass(frozen=True, slots=True)
class PerformanceScenarioManifest:
    schema_version: int
    manifest_id: str
    capture_route: str
    target_environment: TargetEnvironment
    reference_versions: ReferenceVersions
    payload_fixtures: tuple[PayloadFixture, ...]
    diagnostic_configurations: tuple[DiagnosticConfiguration, ...]
    clock_domains: ClockDomains
    timing: CaptureTiming
    display_configurations: tuple[DisplayConfiguration, ...]
    scenarios: tuple[PerformanceScenario, ...]
    outside_gate: tuple[OutsideGateCase, ...]

    def scenario(self, scenario_id: str) -> PerformanceScenario:
        for scenario in self.scenarios:
            if scenario.scenario_id == scenario_id:
                return scenario
        raise EvidenceValidationError(f"unknown scenario_id {scenario_id!r}")

    def display_configuration(self, configuration_id: str) -> DisplayConfiguration:
        for configuration in self.display_configurations:
            if configuration.configuration_id == configuration_id:
                return configuration
        raise EvidenceValidationError(f"unknown display_configuration_id {configuration_id!r}")


@dataclass(frozen=True, slots=True)
class LatencySample:
    metric: str
    elapsed_ms: float
    clock_domain: str
    correlation_id: str


@dataclass(frozen=True, slots=True)
class IdleCpuSamples:
    interval_seconds: int
    client_percent_samples: tuple[float, ...]
    gnome_shell_percent_samples: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class ManualObservations:
    blocking: Mapping[str, bool]
    note_codes: tuple[str, ...]

    @property
    def blocking_failures(self) -> tuple[str, ...]:
        return tuple(sorted(key for key, value in self.blocking.items() if value))


@dataclass(frozen=True, slots=True)
class PerformanceCapture:
    schema_version: int
    manifest_id: str
    capture_id: str
    capture_role: str
    scenario_id: str
    repetition: int
    environment: TargetEnvironment
    versions: CaptureVersions
    display_configuration_id: str
    payload_fixture_id: str
    diagnostic_configuration_id: str
    clock_domains: ClockDomains
    warm_up_seconds: int
    observation_seconds: int
    idle_cpu_seconds: int
    diagnostic_reference: str
    latency_samples: tuple[LatencySample, ...]
    work: Mapping[str, float]
    idle_cpu: IdleCpuSamples
    manual_observations: ManualObservations


@dataclass(frozen=True, slots=True)
class LatencyStatistics:
    clock_domain: str
    sample_count: int
    median: float
    p95: float
    maximum: float


@dataclass(frozen=True, slots=True)
class CpuStatistics:
    sample_count: int
    mean: float
    maximum: float


@dataclass(frozen=True, slots=True)
class ScenarioPerformanceSummary:
    scenario_id: str
    capture_role: str
    repetitions: tuple[int, ...]
    versions: CaptureVersions
    display_configuration_id: str
    payload_fixture_id: str
    diagnostic_configuration_id: str
    diagnostic_references: tuple[str, ...]
    latency: Mapping[str, LatencyStatistics]
    work: Mapping[str, float]
    idle_cpu: Mapping[str, CpuStatistics]
    blocking_failures: tuple[str, ...]
    note_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PerformanceSummary:
    schema_version: int
    summary_id: str
    manifest_id: str
    capture_role: str
    environment_key: str
    scenarios: tuple[ScenarioPerformanceSummary, ...]


@dataclass(frozen=True, slots=True)
class ThresholdProvenance:
    captured_date: str
    baseline_repetitions: int
    review_state: str
    rationale: str
    diagnostic_references: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class InvestigationThreshold:
    metric_path: str
    relative_limit: float
    absolute_noise_floor: float


@dataclass(frozen=True, slots=True)
class PerformanceThresholds:
    schema_version: int
    threshold_id: str
    manifest_id: str
    baseline_summary_id: str
    provenance: ThresholdProvenance
    thresholds: Mapping[str, InvestigationThreshold]


@dataclass(frozen=True, slots=True)
class ScenarioComparison:
    scenario_id: str
    state: str
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PerformanceComparison:
    schema_version: int
    manifest_id: str
    baseline_summary_id: str
    candidate_summary_id: str
    threshold_id: str
    state: str
    scenarios: tuple[ScenarioComparison, ...]


def parse_performance_manifest(
    payload: str | bytes | Mapping[str, object] | Path,
) -> PerformanceScenarioManifest:
    """Parse and strictly validate a schema-version-1 scenario manifest."""

    raw = _json_object(payload, "performance manifest")
    root = _strict_object(
        raw,
        "performance manifest",
        {
            "schema_version",
            "manifest_id",
            "capture_route",
            "target_environment",
            "reference_versions",
            "payload_fixtures",
            "diagnostic_configurations",
            "clock_domains",
            "timing",
            "display_configurations",
            "scenarios",
            "outside_gate",
        },
    )
    _schema_version(root["schema_version"], PERFORMANCE_MANIFEST_SCHEMA_VERSION, "manifest.schema_version")
    manifest_id = _safe_identifier(root["manifest_id"], "manifest_id")
    capture_route = _safe_identifier(root["capture_route"], "capture_route")
    if capture_route != "shipped_pre_migration":
        raise EvidenceValidationError("capture_route must be shipped_pre_migration for the Step 03 oracle")
    environment = _parse_environment(root["target_environment"], "target_environment")
    reference_versions = _parse_reference_versions(root["reference_versions"])
    fixtures = _parse_payload_fixtures(root["payload_fixtures"])
    diagnostics = _parse_diagnostic_configurations(root["diagnostic_configurations"])
    clock_domains = _parse_clock_domains(root["clock_domains"], "clock_domains")
    if clock_domains.client_elapsed == clock_domains.helper_elapsed:
        raise EvidenceValidationError("client and helper clock domains must remain separate")
    timing = _parse_timing(root["timing"])
    displays = _parse_display_configurations(root["display_configurations"])
    scenarios = _parse_scenarios(root["scenarios"])
    outside_gate = _parse_outside_gate(root["outside_gate"])
    _validate_manifest_references(fixtures, diagnostics, displays, scenarios)
    _validate_required_coverage(manifest_id, displays, scenarios)
    _validate_outside_gate(outside_gate)
    return PerformanceScenarioManifest(
        schema_version=PERFORMANCE_MANIFEST_SCHEMA_VERSION,
        manifest_id=manifest_id,
        capture_route=capture_route,
        target_environment=environment,
        reference_versions=reference_versions,
        payload_fixtures=fixtures,
        diagnostic_configurations=diagnostics,
        clock_domains=clock_domains,
        timing=timing,
        display_configurations=displays,
        scenarios=scenarios,
        outside_gate=outside_gate,
    )


def parse_performance_capture(
    payload: str | bytes | Mapping[str, object] | Path,
    manifest: PerformanceScenarioManifest,
) -> PerformanceCapture:
    """Parse one sanitized capture repetition linked to a validated manifest."""

    if not isinstance(manifest, PerformanceScenarioManifest):
        raise TypeError("manifest must be PerformanceScenarioManifest")
    raw = _json_object(payload, "performance capture")
    root = _strict_object(
        raw,
        "performance capture",
        {
            "schema_version",
            "manifest_id",
            "capture_id",
            "capture_role",
            "scenario_id",
            "repetition",
            "environment",
            "versions",
            "display_configuration_id",
            "payload_fixture_id",
            "diagnostic_configuration_id",
            "clock_domains",
            "warm_up_seconds",
            "observation_seconds",
            "idle_cpu_seconds",
            "diagnostic_reference",
            "latency_samples",
            "work",
            "idle_cpu",
            "manual_observations",
        },
    )
    _schema_version(root["schema_version"], PERFORMANCE_CAPTURE_SCHEMA_VERSION, "capture.schema_version")
    manifest_id = _safe_identifier(root["manifest_id"], "capture.manifest_id")
    if manifest_id != manifest.manifest_id:
        raise EvidenceValidationError("capture manifest_id does not match the validated manifest")
    capture_id = _safe_identifier(root["capture_id"], "capture.capture_id")
    capture_role = _safe_identifier(root["capture_role"], "capture.capture_role")
    if capture_role not in _CAPTURE_ROLES:
        raise EvidenceValidationError(f"capture_role must be one of {sorted(_CAPTURE_ROLES)}")
    scenario_id = _safe_identifier(root["scenario_id"], "capture.scenario_id")
    scenario = manifest.scenario(scenario_id)
    repetition = _positive_int(root["repetition"], "capture.repetition")
    if repetition > manifest.timing.repetitions:
        raise EvidenceValidationError("capture.repetition exceeds manifest timing.repetitions")
    environment = _parse_environment(root["environment"], "capture.environment")
    if environment != manifest.target_environment:
        raise EvidenceValidationError("capture environment does not match manifest target_environment")
    versions = _parse_capture_versions(root["versions"])
    if capture_role == "baseline":
        if versions.reference != manifest.reference_versions or versions.architecture_stage != "pre_migration":
            raise EvidenceValidationError("baseline capture versions do not match manifest reference_versions")
    display_configuration_id = _safe_identifier(root["display_configuration_id"], "capture.display_configuration_id")
    payload_fixture_id = _safe_identifier(root["payload_fixture_id"], "capture.payload_fixture_id")
    diagnostic_configuration_id = _safe_identifier(
        root["diagnostic_configuration_id"], "capture.diagnostic_configuration_id"
    )
    if display_configuration_id != scenario.display_configuration_id:
        raise EvidenceValidationError("capture display_configuration_id does not match scenario")
    if payload_fixture_id != scenario.payload_fixture_id:
        raise EvidenceValidationError("capture payload_fixture_id does not match scenario")
    if diagnostic_configuration_id != scenario.diagnostic_configuration_id:
        raise EvidenceValidationError("capture diagnostic_configuration_id does not match scenario")
    clock_domains = _parse_clock_domains(root["clock_domains"], "capture.clock_domains")
    if clock_domains != manifest.clock_domains:
        raise EvidenceValidationError("capture clock_domains do not match manifest")
    warm_up_seconds = _positive_int(root["warm_up_seconds"], "capture.warm_up_seconds")
    observation_seconds = _positive_int(root["observation_seconds"], "capture.observation_seconds")
    idle_cpu_seconds = _positive_int(root["idle_cpu_seconds"], "capture.idle_cpu_seconds")
    if warm_up_seconds != manifest.timing.warm_up_seconds:
        raise EvidenceValidationError("capture warm_up_seconds does not match manifest")
    if observation_seconds != manifest.timing.observation_seconds:
        raise EvidenceValidationError("capture observation_seconds does not match manifest")
    if idle_cpu_seconds != manifest.timing.idle_cpu_seconds:
        raise EvidenceValidationError("capture idle_cpu_seconds does not match manifest")
    diagnostic_reference = _safe_identifier(root["diagnostic_reference"], "capture.diagnostic_reference")
    latency_samples = _parse_latency_samples(root["latency_samples"], manifest.clock_domains)
    work = _parse_work(root["work"])
    idle_cpu = _parse_idle_cpu(root["idle_cpu"], idle_cpu_seconds)
    manual_observations = _parse_manual_observations(root["manual_observations"])
    return PerformanceCapture(
        schema_version=PERFORMANCE_CAPTURE_SCHEMA_VERSION,
        manifest_id=manifest_id,
        capture_id=capture_id,
        capture_role=capture_role,
        scenario_id=scenario_id,
        repetition=repetition,
        environment=environment,
        versions=versions,
        display_configuration_id=display_configuration_id,
        payload_fixture_id=payload_fixture_id,
        diagnostic_configuration_id=diagnostic_configuration_id,
        clock_domains=clock_domains,
        warm_up_seconds=warm_up_seconds,
        observation_seconds=observation_seconds,
        idle_cpu_seconds=idle_cpu_seconds,
        diagnostic_reference=diagnostic_reference,
        latency_samples=latency_samples,
        work=work,
        idle_cpu=idle_cpu,
        manual_observations=manual_observations,
    )


def build_performance_summary(
    manifest: PerformanceScenarioManifest,
    captures: Iterable[PerformanceCapture],
    *,
    summary_id: str,
    require_complete: bool = False,
) -> PerformanceSummary:
    """Aggregate validated repetitions into deterministic per-scenario statistics."""

    if not isinstance(manifest, PerformanceScenarioManifest):
        raise TypeError("manifest must be PerformanceScenarioManifest")
    normalized_summary_id = _safe_identifier(summary_id, "summary_id")
    capture_list = sorted(tuple(captures), key=lambda item: (item.scenario_id, item.repetition, item.capture_id))
    if not capture_list:
        raise EvidenceValidationError("at least one performance capture is required")
    groups: dict[str, list[PerformanceCapture]] = {}
    seen_repetitions: set[tuple[str, int]] = set()
    roles: set[str] = set()
    versions: set[CaptureVersions] = set()
    for capture in capture_list:
        if not isinstance(capture, PerformanceCapture):
            raise TypeError("captures must contain PerformanceCapture values")
        if capture.manifest_id != manifest.manifest_id:
            raise EvidenceValidationError("capture manifest_id does not match summary manifest")
        key = (capture.scenario_id, capture.repetition)
        if key in seen_repetitions:
            raise EvidenceValidationError(
                f"duplicate repetition {capture.repetition} for scenario {capture.scenario_id}"
            )
        seen_repetitions.add(key)
        roles.add(capture.capture_role)
        versions.add(capture.versions)
        groups.setdefault(capture.scenario_id, []).append(capture)
    if len(roles) != 1:
        raise EvidenceValidationError("one summary cannot mix baseline and candidate captures")
    if len(versions) != 1:
        raise EvidenceValidationError("one summary cannot mix component versions or source revisions")
    if require_complete:
        expected_ids = {scenario.scenario_id for scenario in manifest.scenarios}
        expected_repetitions = set(range(1, manifest.timing.repetitions + 1))
        if set(groups) != expected_ids or any(
            {capture.repetition for capture in group} != expected_repetitions for group in groups.values()
        ):
            raise EvidenceValidationError("complete capture set is missing a required scenario or repetition")
    scenario_summaries = tuple(_summarize_scenario(groups[scenario_id]) for scenario_id in sorted(groups))
    return PerformanceSummary(
        schema_version=PERFORMANCE_SUMMARY_SCHEMA_VERSION,
        summary_id=normalized_summary_id,
        manifest_id=manifest.manifest_id,
        capture_role=next(iter(roles)),
        environment_key=manifest.target_environment.stable_key,
        scenarios=scenario_summaries,
    )


def serialize_performance_summary(summary: PerformanceSummary) -> str:
    """Serialize a summary to deterministic standard JSON."""

    if not isinstance(summary, PerformanceSummary):
        raise TypeError("summary must be PerformanceSummary")
    return _deterministic_json(_encode_summary(summary))


def parse_performance_summary(
    payload: str | bytes | Mapping[str, object] | Path,
    manifest: PerformanceScenarioManifest,
) -> PerformanceSummary:
    """Strictly decode a deterministic summary for review/comparison."""

    raw = _json_object(payload, "performance summary")
    root = _strict_object(
        raw,
        "performance summary",
        {"schema_version", "summary_id", "manifest_id", "capture_role", "environment_key", "scenarios"},
    )
    _schema_version(root["schema_version"], PERFORMANCE_SUMMARY_SCHEMA_VERSION, "summary.schema_version")
    summary_id = _safe_identifier(root["summary_id"], "summary.summary_id")
    manifest_id = _safe_identifier(root["manifest_id"], "summary.manifest_id")
    if manifest_id != manifest.manifest_id:
        raise EvidenceValidationError("summary manifest_id does not match validated manifest")
    capture_role = _safe_identifier(root["capture_role"], "summary.capture_role")
    if capture_role not in _CAPTURE_ROLES:
        raise EvidenceValidationError("summary capture_role is invalid")
    environment_key = _safe_text(root["environment_key"], "summary.environment_key")
    if environment_key != manifest.target_environment.stable_key:
        raise EvidenceValidationError("summary environment_key does not match manifest")
    scenario_values = _sequence(root["scenarios"], "summary.scenarios")
    if not scenario_values:
        raise EvidenceValidationError("summary.scenarios must not be empty")
    scenarios = tuple(_parse_scenario_summary(value, manifest, capture_role) for value in scenario_values)
    scenario_ids = [scenario.scenario_id for scenario in scenarios]
    if len(scenario_ids) != len(set(scenario_ids)):
        raise EvidenceValidationError("summary contains duplicate scenario_id values")
    if scenario_ids != sorted(scenario_ids):
        raise EvidenceValidationError("summary scenarios must be sorted deterministically")
    if len({scenario.versions for scenario in scenarios}) != 1:
        raise EvidenceValidationError("one summary cannot mix component versions or source revisions")
    return PerformanceSummary(
        schema_version=PERFORMANCE_SUMMARY_SCHEMA_VERSION,
        summary_id=summary_id,
        manifest_id=manifest_id,
        capture_role=capture_role,
        environment_key=environment_key,
        scenarios=scenarios,
    )


def format_performance_summary(summary: PerformanceSummary) -> str:
    """Return a concise stable human-readable summary."""

    lines = [
        f"Performance summary {summary.summary_id} ({summary.capture_role})",
        f"Manifest: {summary.manifest_id}",
    ]
    for scenario in summary.scenarios:
        blocking = ",".join(scenario.blocking_failures) if scenario.blocking_failures else "none"
        lines.append(f"- {scenario.scenario_id}: repetitions={len(scenario.repetitions)} blocking={blocking}")
        for metric, stats in sorted(scenario.latency.items()):
            lines.append(
                f"  {metric}: n={stats.sample_count} median={stats.median:.3f} "
                f"p95={stats.p95:.3f} max={stats.maximum:.3f} domain={stats.clock_domain}"
            )
    return "\n".join(lines)


def parse_performance_thresholds(
    payload: str | bytes | Mapping[str, object] | Path,
    manifest: PerformanceScenarioManifest,
) -> PerformanceThresholds:
    """Load reviewed fixed thresholds without inferring or modifying any values."""

    raw = _json_object(payload, "performance thresholds")
    root = _strict_object(
        raw,
        "performance thresholds",
        {
            "schema_version",
            "threshold_id",
            "manifest_id",
            "baseline_summary_id",
            "provenance",
            "thresholds",
        },
    )
    _schema_version(root["schema_version"], PERFORMANCE_THRESHOLD_SCHEMA_VERSION, "thresholds.schema_version")
    threshold_id = _safe_identifier(root["threshold_id"], "threshold_id")
    manifest_id = _safe_identifier(root["manifest_id"], "thresholds.manifest_id")
    if manifest_id != manifest.manifest_id:
        raise EvidenceValidationError("threshold manifest_id does not match validated manifest")
    baseline_summary_id = _safe_identifier(root["baseline_summary_id"], "baseline_summary_id")
    provenance = _parse_threshold_provenance(root["provenance"])
    if provenance.baseline_repetitions != manifest.timing.repetitions:
        raise EvidenceValidationError(
            "thresholds.provenance.baseline_repetitions must match manifest timing.repetitions"
        )
    threshold_values = _sequence(root["thresholds"], "thresholds.thresholds")
    thresholds: dict[str, InvestigationThreshold] = {}
    for index, value in enumerate(threshold_values):
        entry = _strict_object(
            value,
            f"thresholds.thresholds[{index}]",
            {"metric_path", "relative_limit", "absolute_noise_floor"},
        )
        metric_path = _safe_text(entry["metric_path"], f"thresholds.thresholds[{index}].metric_path")
        if metric_path not in REQUIRED_THRESHOLD_PATHS:
            raise EvidenceValidationError(f"unknown threshold metric_path {metric_path!r}")
        if metric_path in thresholds:
            raise EvidenceValidationError(f"duplicate threshold metric_path {metric_path!r}")
        relative_limit = _non_negative_number(entry["relative_limit"], f"thresholds.thresholds[{index}].relative_limit")
        absolute_noise_floor = _positive_number(
            entry["absolute_noise_floor"], f"thresholds.thresholds[{index}].absolute_noise_floor"
        )
        thresholds[metric_path] = InvestigationThreshold(
            metric_path=metric_path,
            relative_limit=relative_limit,
            absolute_noise_floor=absolute_noise_floor,
        )
    missing = sorted(set(REQUIRED_THRESHOLD_PATHS) - set(thresholds))
    if missing:
        raise EvidenceValidationError(f"required threshold metrics are missing: {missing}")
    return PerformanceThresholds(
        schema_version=PERFORMANCE_THRESHOLD_SCHEMA_VERSION,
        threshold_id=threshold_id,
        manifest_id=manifest_id,
        baseline_summary_id=baseline_summary_id,
        provenance=provenance,
        thresholds=MappingProxyType(dict(sorted(thresholds.items()))),
    )


def compare_performance_summaries(
    baseline: PerformanceSummary,
    candidate: PerformanceSummary,
    thresholds: PerformanceThresholds,
) -> PerformanceComparison:
    """Compare like-for-like summaries using immutable dual thresholds and invariant-first gates."""

    if baseline.capture_role != "baseline":
        raise EvidenceValidationError("baseline summary must have capture_role=baseline")
    if candidate.capture_role != "candidate":
        raise EvidenceValidationError("candidate summary must have capture_role=candidate")
    if baseline.manifest_id != candidate.manifest_id or baseline.manifest_id != thresholds.manifest_id:
        raise EvidenceValidationError("baseline, candidate, and thresholds must share one manifest_id")
    if baseline.environment_key != candidate.environment_key:
        raise EvidenceValidationError("baseline and candidate environment_key values differ")
    if thresholds.baseline_summary_id != baseline.summary_id:
        raise EvidenceValidationError("threshold baseline_summary_id does not match baseline summary")
    baseline_by_id = {scenario.scenario_id: scenario for scenario in baseline.scenarios}
    candidate_by_id = {scenario.scenario_id: scenario for scenario in candidate.scenarios}
    if set(baseline_by_id) != set(candidate_by_id):
        raise EvidenceValidationError("baseline and candidate scenario sets differ")
    comparisons: list[ScenarioComparison] = []
    for scenario_id in sorted(baseline_by_id):
        baseline_scenario = baseline_by_id[scenario_id]
        candidate_scenario = candidate_by_id[scenario_id]
        _validate_comparable_scenarios(baseline_scenario, candidate_scenario)
        reasons: list[str] = []
        reasons.extend(f"baseline_blocking:{reason}" for reason in baseline_scenario.blocking_failures)
        reasons.extend(f"candidate_blocking:{reason}" for reason in candidate_scenario.blocking_failures)
        if reasons:
            state = "blocked"
        else:
            for metric_path in REQUIRED_THRESHOLD_PATHS:
                threshold = thresholds.thresholds[metric_path]
                baseline_value = _summary_metric(baseline_scenario, metric_path)
                candidate_value = _summary_metric(candidate_scenario, metric_path)
                delta = candidate_value - baseline_value
                relative = (
                    math.inf
                    if baseline_value == 0 and delta > 0
                    else (delta / baseline_value if baseline_value > 0 else 0.0)
                )
                if delta > threshold.absolute_noise_floor and relative > threshold.relative_limit:
                    if metric_path.startswith("latency."):
                        category = "latency_regression"
                    elif metric_path.startswith("work."):
                        category = "work_regression"
                    else:
                        category = "idle_cpu_regression"
                    reasons.append(f"{category}:{metric_path}")
            state = "investigate" if reasons else "pass"
        comparisons.append(ScenarioComparison(scenario_id=scenario_id, state=state, reasons=tuple(reasons)))
    overall_state = "pass"
    if any(comparison.state == "blocked" for comparison in comparisons):
        overall_state = "blocked"
    elif any(comparison.state == "investigate" for comparison in comparisons):
        overall_state = "investigate"
    return PerformanceComparison(
        schema_version=PERFORMANCE_COMPARISON_SCHEMA_VERSION,
        manifest_id=baseline.manifest_id,
        baseline_summary_id=baseline.summary_id,
        candidate_summary_id=candidate.summary_id,
        threshold_id=thresholds.threshold_id,
        state=overall_state,
        scenarios=tuple(comparisons),
    )


def serialize_performance_comparison(comparison: PerformanceComparison) -> str:
    """Serialize a comparison report to deterministic standard JSON."""

    if not isinstance(comparison, PerformanceComparison):
        raise TypeError("comparison must be PerformanceComparison")
    return _deterministic_json(
        {
            "schema_version": comparison.schema_version,
            "manifest_id": comparison.manifest_id,
            "baseline_summary_id": comparison.baseline_summary_id,
            "candidate_summary_id": comparison.candidate_summary_id,
            "threshold_id": comparison.threshold_id,
            "state": comparison.state,
            "scenarios": [
                {"scenario_id": scenario.scenario_id, "state": scenario.state, "reasons": list(scenario.reasons)}
                for scenario in comparison.scenarios
            ],
        }
    )


def format_performance_comparison(comparison: PerformanceComparison) -> str:
    """Return a concise stable human-readable comparison report."""

    lines = [
        f"Performance comparison: {comparison.state}",
        f"Baseline={comparison.baseline_summary_id} Candidate={comparison.candidate_summary_id}",
        f"Thresholds={comparison.threshold_id}",
    ]
    for scenario in comparison.scenarios:
        reasons = ",".join(scenario.reasons) if scenario.reasons else "none"
        lines.append(f"- {scenario.scenario_id}: {scenario.state} ({reasons})")
    return "\n".join(lines)


def _parse_environment(value: object, context: str) -> TargetEnvironment:
    raw = _strict_object(value, context, _TARGET_ENVIRONMENT_FIELDS)
    fields = {key: _safe_text(raw[key], f"{context}.{key}") for key in _TARGET_ENVIRONMENT_FIELDS}
    return TargetEnvironment(**fields)


def _parse_reference_versions(value: object) -> ReferenceVersions:
    raw = _strict_object(
        value,
        "reference_versions",
        {"plugin", "client", "helper_protocol", "source_revision"},
    )
    return ReferenceVersions(
        plugin=_safe_version(raw["plugin"], "reference_versions.plugin"),
        client=_safe_version(raw["client"], "reference_versions.client"),
        helper_protocol=_positive_int(raw["helper_protocol"], "reference_versions.helper_protocol"),
        source_revision=_source_revision(raw["source_revision"], "reference_versions.source_revision"),
    )


def _parse_capture_versions(value: object) -> CaptureVersions:
    raw = _strict_object(
        value,
        "capture.versions",
        {"plugin", "client", "helper_protocol", "source_revision", "architecture_stage"},
    )
    return CaptureVersions(
        plugin=_safe_version(raw["plugin"], "capture.versions.plugin"),
        client=_safe_version(raw["client"], "capture.versions.client"),
        helper_protocol=_positive_int(raw["helper_protocol"], "capture.versions.helper_protocol"),
        source_revision=_source_revision(raw["source_revision"], "capture.versions.source_revision"),
        architecture_stage=_safe_identifier(raw["architecture_stage"], "capture.versions.architecture_stage"),
    )


def _parse_payload_fixtures(value: object) -> tuple[PayloadFixture, ...]:
    values = _sequence(value, "payload_fixtures")
    if not values:
        raise EvidenceValidationError("payload_fixtures must not be empty")
    fixtures: list[PayloadFixture] = []
    seen: set[str] = set()
    for index, item in enumerate(values):
        raw = _strict_object(
            item,
            f"payload_fixtures[{index}]",
            {"fixture_id", "repository_path", "sha256"},
        )
        fixture_id = _safe_identifier(raw["fixture_id"], f"payload_fixtures[{index}].fixture_id")
        if fixture_id in seen:
            raise EvidenceValidationError(f"duplicate fixture_id {fixture_id!r}")
        seen.add(fixture_id)
        repository_path = _repository_path(raw["repository_path"], f"payload_fixtures[{index}].repository_path")
        sha256 = _safe_text(raw["sha256"], f"payload_fixtures[{index}].sha256")
        if not _SHA256.fullmatch(sha256):
            raise EvidenceValidationError(f"payload_fixtures[{index}].sha256 must be lowercase SHA-256")
        fixtures.append(PayloadFixture(fixture_id=fixture_id, repository_path=repository_path, sha256=sha256))
    return tuple(fixtures)


def _parse_diagnostic_configurations(value: object) -> tuple[DiagnosticConfiguration, ...]:
    values = _sequence(value, "diagnostic_configurations")
    if not values:
        raise EvidenceValidationError("diagnostic_configurations must not be empty")
    configurations: list[DiagnosticConfiguration] = []
    seen: set[str] = set()
    for index, item in enumerate(values):
        raw = _strict_object(
            item,
            f"diagnostic_configurations[{index}]",
            {"configuration_id", "toggles"},
        )
        configuration_id = _safe_identifier(
            raw["configuration_id"], f"diagnostic_configurations[{index}].configuration_id"
        )
        if configuration_id in seen:
            raise EvidenceValidationError(f"duplicate diagnostic configuration_id {configuration_id!r}")
        seen.add(configuration_id)
        toggle_raw = _strict_object(
            raw["toggles"], f"diagnostic_configurations[{index}].toggles", _DIAGNOSTIC_TOGGLE_FIELDS
        )
        toggles = {
            key: _boolean(toggle_raw[key], f"diagnostic_configurations[{index}].toggles.{key}")
            for key in sorted(toggle_raw)
        }
        if not all(toggles[key] for key in _DIAGNOSTIC_TOGGLE_FIELDS - {"visual_debug_overlays"}):
            raise EvidenceValidationError("performance diagnostic timing/capture toggles must all be enabled")
        if toggles["visual_debug_overlays"]:
            raise EvidenceValidationError("visual_debug_overlays must remain disabled during performance capture")
        configurations.append(
            DiagnosticConfiguration(configuration_id=configuration_id, toggles=MappingProxyType(toggles))
        )
    return tuple(configurations)


def _parse_clock_domains(value: object, context: str) -> ClockDomains:
    raw = _strict_object(value, context, {"client_elapsed", "helper_elapsed"})
    return ClockDomains(
        client_elapsed=_safe_identifier(raw["client_elapsed"], f"{context}.client_elapsed"),
        helper_elapsed=_safe_identifier(raw["helper_elapsed"], f"{context}.helper_elapsed"),
    )


def _parse_timing(value: object) -> CaptureTiming:
    raw = _strict_object(
        value,
        "timing",
        {"warm_up_seconds", "observation_seconds", "idle_cpu_seconds", "repetitions"},
    )
    return CaptureTiming(
        warm_up_seconds=_positive_int(raw["warm_up_seconds"], "timing.warm_up_seconds"),
        observation_seconds=_positive_int(raw["observation_seconds"], "timing.observation_seconds"),
        idle_cpu_seconds=_positive_int(raw["idle_cpu_seconds"], "timing.idle_cpu_seconds"),
        repetitions=_positive_int(raw["repetitions"], "timing.repetitions"),
    )


def _parse_display_configurations(value: object) -> tuple[DisplayConfiguration, ...]:
    values = _sequence(value, "display_configurations")
    configurations: list[DisplayConfiguration] = []
    seen: set[str] = set()
    for index, item in enumerate(values):
        context = f"display_configurations[{index}]"
        raw = _strict_object(
            item,
            context,
            {
                "configuration_id",
                "scale_percent",
                "orientation",
                "primary_monitor",
                "compositor_coordinate_space",
                "negative_coordinate_space",
                "monitors",
            },
        )
        configuration_id = _safe_identifier(raw["configuration_id"], f"{context}.configuration_id")
        if configuration_id in seen:
            raise EvidenceValidationError(f"duplicate display configuration_id {configuration_id!r}")
        seen.add(configuration_id)
        scale_percent = _positive_int(raw["scale_percent"], f"{context}.scale_percent")
        if scale_percent not in {100, 125}:
            raise EvidenceValidationError(f"{context}.scale_percent must be 100 or 125")
        orientation = _safe_identifier(raw["orientation"], f"{context}.orientation")
        if orientation != "horizontal":
            raise EvidenceValidationError(f"{context}.orientation must be horizontal")
        primary_monitor = _safe_identifier(raw["primary_monitor"], f"{context}.primary_monitor")
        compositor_coordinate_space = _safe_identifier(
            raw["compositor_coordinate_space"], f"{context}.compositor_coordinate_space"
        )
        if compositor_coordinate_space != _COMPOSITOR_COORDINATE_SPACE:
            raise EvidenceValidationError(
                f"{context}.compositor_coordinate_space must be {_COMPOSITOR_COORDINATE_SPACE}"
            )
        negative_coordinate_space = _safe_identifier(
            raw["negative_coordinate_space"], f"{context}.negative_coordinate_space"
        )
        if negative_coordinate_space != _NEGATIVE_COORDINATE_SPACE:
            raise EvidenceValidationError(f"{context}.negative_coordinate_space must be {_NEGATIVE_COORDINATE_SPACE}")
        monitor_values = _sequence(raw["monitors"], f"{context}.monitors")
        monitors = tuple(
            _parse_monitor(monitor, f"{context}.monitors[{i}]") for i, monitor in enumerate(monitor_values)
        )
        _validate_display_geometry(monitors, scale_percent, primary_monitor, context)
        configurations.append(
            DisplayConfiguration(
                configuration_id=configuration_id,
                scale_percent=scale_percent,
                orientation=orientation,
                primary_monitor=primary_monitor,
                compositor_coordinate_space=compositor_coordinate_space,
                negative_coordinate_space=negative_coordinate_space,
                monitors=monitors,
            )
        )
    if {configuration.scale_percent for configuration in configurations} != {100, 125}:
        raise EvidenceValidationError("display scale coverage must contain exactly uniform 100 and 125 percent")
    primary_ids = {configuration.primary_monitor for configuration in configurations}
    if len(primary_ids) != 1:
        raise EvidenceValidationError("primary monitor must remain fixed across display scale configurations")
    return tuple(configurations)


def _parse_monitor(value: object, context: str) -> MonitorGeometry:
    raw = _strict_object(
        value,
        context,
        {
            "monitor_id",
            "compositor_logical_x",
            "compositor_logical_y",
            "primary_relative_logical_x",
            "primary_relative_logical_y",
            "logical_width",
            "logical_height",
            "physical_width_px",
            "physical_height_px",
        },
    )
    return MonitorGeometry(
        monitor_id=_safe_identifier(raw["monitor_id"], f"{context}.monitor_id"),
        compositor_logical_x=_integer(raw["compositor_logical_x"], f"{context}.compositor_logical_x"),
        compositor_logical_y=_integer(raw["compositor_logical_y"], f"{context}.compositor_logical_y"),
        primary_relative_logical_x=_integer(raw["primary_relative_logical_x"], f"{context}.primary_relative_logical_x"),
        primary_relative_logical_y=_integer(raw["primary_relative_logical_y"], f"{context}.primary_relative_logical_y"),
        logical_width=_positive_int(raw["logical_width"], f"{context}.logical_width"),
        logical_height=_positive_int(raw["logical_height"], f"{context}.logical_height"),
        physical_width_px=_positive_int(raw["physical_width_px"], f"{context}.physical_width_px"),
        physical_height_px=_positive_int(raw["physical_height_px"], f"{context}.physical_height_px"),
    )


def _validate_display_geometry(
    monitors: tuple[MonitorGeometry, ...],
    scale_percent: int,
    primary_monitor: str,
    context: str,
) -> None:
    if len(monitors) != 2:
        raise EvidenceValidationError(f"{context}.monitors must contain exactly two monitors")
    ids = [monitor.monitor_id for monitor in monitors]
    if len(ids) != len(set(ids)):
        raise EvidenceValidationError(f"{context}.monitors contains duplicate monitor_id")
    if set(ids) != {"monitor_a", "monitor_b"}:
        raise EvidenceValidationError(f"{context}.monitors must use monitor_a and monitor_b")
    if primary_monitor not in ids:
        raise EvidenceValidationError(f"{context}.primary_monitor must reference a known monitor")
    if (
        len({monitor.compositor_logical_y for monitor in monitors}) != 1
        or len({monitor.logical_height for monitor in monitors}) != 1
    ):
        raise EvidenceValidationError(f"{context} must be a horizontal monitor layout")
    ordered = sorted(monitors, key=lambda monitor: monitor.compositor_logical_x)
    if ordered[0].compositor_logical_x != 0:
        raise EvidenceValidationError(f"{context} compositor geometry must be normalized from zero")
    if ordered[0].compositor_logical_x + ordered[0].logical_width != ordered[1].compositor_logical_x:
        raise EvidenceValidationError(f"{context} monitors must be non-overlapping and contiguous")
    if not any(monitor.primary_relative_logical_x < 0 for monitor in monitors):
        raise EvidenceValidationError(f"{context} must include negative-coordinate coverage")
    primary = next(monitor for monitor in monitors if monitor.monitor_id == primary_monitor)
    for monitor in monitors:
        expected_relative_x = monitor.compositor_logical_x - primary.compositor_logical_x
        expected_relative_y = monitor.compositor_logical_y - primary.compositor_logical_y
        if (
            monitor.primary_relative_logical_x != expected_relative_x
            or monitor.primary_relative_logical_y != expected_relative_y
        ):
            raise EvidenceValidationError(
                f"{context} primary-relative geometry must be derived from compositor geometry"
            )
    for monitor in monitors:
        if monitor.logical_width * scale_percent != monitor.physical_width_px * 100:
            raise EvidenceValidationError(f"{context} logical_width is incompatible with uniform scale")
        if monitor.logical_height * scale_percent != monitor.physical_height_px * 100:
            raise EvidenceValidationError(f"{context} logical_height is incompatible with uniform scale")


def _parse_scenarios(value: object) -> tuple[PerformanceScenario, ...]:
    values = _sequence(value, "scenarios")
    scenarios: list[PerformanceScenario] = []
    seen: set[str] = set()
    for index, item in enumerate(values):
        context = f"scenarios[{index}]"
        raw = _strict_object(
            item,
            context,
            {
                "scenario_id",
                "display_configuration_id",
                "action",
                "start_mode",
                "end_mode",
                "start_monitor",
                "end_monitor",
                "interaction",
                "payload_fixture_id",
                "diagnostic_configuration_id",
                "workload",
            },
        )
        scenario_id = _safe_identifier(raw["scenario_id"], f"{context}.scenario_id")
        if scenario_id in seen:
            raise EvidenceValidationError(f"duplicate scenario_id {scenario_id!r}")
        seen.add(scenario_id)
        scenario = PerformanceScenario(
            scenario_id=scenario_id,
            display_configuration_id=_safe_identifier(
                raw["display_configuration_id"], f"{context}.display_configuration_id"
            ),
            action=_choice(raw["action"], _ACTIONS, f"{context}.action"),
            start_mode=_choice(raw["start_mode"], _MODES, f"{context}.start_mode"),
            end_mode=_choice(raw["end_mode"], _MODES, f"{context}.end_mode"),
            start_monitor=_choice(raw["start_monitor"], {"monitor_a", "monitor_b"}, f"{context}.start_monitor"),
            end_monitor=_choice(raw["end_monitor"], {"monitor_a", "monitor_b"}, f"{context}.end_monitor"),
            interaction=_choice(raw["interaction"], _INTERACTIONS, f"{context}.interaction"),
            payload_fixture_id=_safe_identifier(raw["payload_fixture_id"], f"{context}.payload_fixture_id"),
            diagnostic_configuration_id=_safe_identifier(
                raw["diagnostic_configuration_id"], f"{context}.diagnostic_configuration_id"
            ),
            workload=_choice(raw["workload"], _WORKLOADS, f"{context}.workload"),
        )
        _validate_scenario_semantics(scenario)
        scenarios.append(scenario)
    return tuple(scenarios)


def _validate_scenario_semantics(scenario: PerformanceScenario) -> None:
    if scenario.action == "stable":
        valid = (
            scenario.start_mode == scenario.end_mode
            and scenario.start_monitor == scenario.end_monitor
            and scenario.interaction == "none"
        )
    elif scenario.action == "mode_transition":
        valid = (
            scenario.start_mode != scenario.end_mode
            and scenario.start_monitor == scenario.end_monitor
            and scenario.interaction == "none"
        )
    elif scenario.action == "monitor_handoff":
        valid = (
            scenario.start_mode == scenario.end_mode == "borderless_fullscreen"
            and scenario.start_monitor != scenario.end_monitor
            and scenario.interaction == "none"
        )
    else:
        valid = scenario.start_monitor == scenario.end_monitor and scenario.interaction in {"alt_tab", "overview"}
    if not valid:
        raise EvidenceValidationError(f"scenario {scenario.scenario_id!r} has inconsistent action semantics")


def _parse_outside_gate(value: object) -> tuple[OutsideGateCase, ...]:
    values = _sequence(value, "outside_gate")
    cases: list[OutsideGateCase] = []
    seen: set[str] = set()
    for index, item in enumerate(values):
        context = f"outside_gate[{index}]"
        raw = _strict_object(item, context, {"case_id", "classification", "reason_code"})
        case_id = _safe_identifier(raw["case_id"], f"{context}.case_id")
        if case_id in seen:
            raise EvidenceValidationError(f"duplicate outside-gate case_id {case_id!r}")
        seen.add(case_id)
        classification = _choice(raw["classification"], {"deferred", "unsupported"}, f"{context}.classification")
        cases.append(
            OutsideGateCase(
                case_id=case_id,
                classification=classification,
                reason_code=_safe_identifier(raw["reason_code"], f"{context}.reason_code"),
            )
        )
    return tuple(cases)


def _validate_manifest_references(
    fixtures: tuple[PayloadFixture, ...],
    diagnostics: tuple[DiagnosticConfiguration, ...],
    displays: tuple[DisplayConfiguration, ...],
    scenarios: tuple[PerformanceScenario, ...],
) -> None:
    fixture_ids = {fixture.fixture_id for fixture in fixtures}
    diagnostic_ids = {configuration.configuration_id for configuration in diagnostics}
    display_ids = {configuration.configuration_id for configuration in displays}
    for scenario in scenarios:
        if scenario.payload_fixture_id not in fixture_ids:
            raise EvidenceValidationError(f"scenario {scenario.scenario_id} has unknown payload_fixture_id")
        if scenario.diagnostic_configuration_id not in diagnostic_ids:
            raise EvidenceValidationError(f"scenario {scenario.scenario_id} has unknown diagnostic_configuration_id")
        if scenario.display_configuration_id not in display_ids:
            raise EvidenceValidationError(f"scenario {scenario.scenario_id} has unknown display_configuration_id")


def _validate_required_coverage(
    manifest_id: str,
    displays: tuple[DisplayConfiguration, ...],
    scenarios: tuple[PerformanceScenario, ...],
) -> None:
    scale_by_display = {configuration.configuration_id: configuration.scale_percent for configuration in displays}
    actual: dict[int, set[tuple[str, str, str, str, str, str]]] = {100: set(), 125: set()}
    for scenario in scenarios:
        scale = scale_by_display[scenario.display_configuration_id]
        signature = (
            scenario.action,
            scenario.start_mode,
            scenario.end_mode,
            scenario.start_monitor,
            scenario.end_monitor,
            scenario.interaction,
        )
        if signature in actual[scale]:
            raise EvidenceValidationError(f"duplicate required scenario signature for scale {scale}: {signature}")
        actual[scale].add(signature)
    for scale in (100, 125):
        expected = _required_scenario_signatures(manifest_id, scale)
        if actual[scale] != expected:
            missing = sorted(expected - actual[scale])
            extra = sorted(actual[scale] - expected)
            raise EvidenceValidationError(
                f"required scenario coverage for scale {scale} is incomplete or ambiguous; missing={missing} extra={extra}"
            )


def _required_scenario_signatures(manifest_id: str, scale: int) -> set[tuple[str, str, str, str, str, str]]:
    if manifest_id == "fix219_gnome46_pre_migration_v1":
        return _full_matrix_scenario_signatures()
    return _reduced_matrix_scenario_signatures(scale)


def _reduced_matrix_scenario_signatures(scale: int) -> set[tuple[str, str, str, str, str, str]]:
    signatures = {
        ("stable", "windowed", "windowed", "monitor_a", "monitor_a", "none"),
        (
            "stable",
            "borderless_fullscreen",
            "borderless_fullscreen",
            "monitor_a",
            "monitor_a",
            "none",
        ),
        (
            "mode_transition",
            "windowed",
            "borderless_fullscreen",
            "monitor_a",
            "monitor_a",
            "none",
        ),
        (
            "mode_transition",
            "borderless_fullscreen",
            "windowed",
            "monitor_a",
            "monitor_a",
            "none",
        ),
        ("stable", "windowed", "windowed", "monitor_b", "monitor_b", "none"),
    }
    if scale == 100:
        signatures.update(
            {
                (
                    "monitor_handoff",
                    "borderless_fullscreen",
                    "borderless_fullscreen",
                    "monitor_a",
                    "monitor_b",
                    "none",
                ),
                (
                    "monitor_handoff",
                    "borderless_fullscreen",
                    "borderless_fullscreen",
                    "monitor_b",
                    "monitor_a",
                    "none",
                ),
                (
                    "shell_interaction",
                    "borderless_fullscreen",
                    "borderless_fullscreen",
                    "monitor_a",
                    "monitor_a",
                    "alt_tab",
                ),
                (
                    "shell_interaction",
                    "windowed",
                    "windowed",
                    "monitor_a",
                    "monitor_a",
                    "overview",
                ),
            }
        )
    return signatures


def _full_matrix_scenario_signatures() -> set[tuple[str, str, str, str, str, str]]:
    signatures: set[tuple[str, str, str, str, str, str]] = set()
    for monitor in ("monitor_a", "monitor_b"):
        signatures.update(
            {
                ("stable", "windowed", "windowed", monitor, monitor, "none"),
                (
                    "stable",
                    "borderless_fullscreen",
                    "borderless_fullscreen",
                    monitor,
                    monitor,
                    "none",
                ),
                ("mode_transition", "windowed", "borderless_fullscreen", monitor, monitor, "none"),
                ("mode_transition", "borderless_fullscreen", "windowed", monitor, monitor, "none"),
            }
        )
    signatures.update(
        {
            (
                "monitor_handoff",
                "borderless_fullscreen",
                "borderless_fullscreen",
                "monitor_a",
                "monitor_b",
                "none",
            ),
            (
                "monitor_handoff",
                "borderless_fullscreen",
                "borderless_fullscreen",
                "monitor_b",
                "monitor_a",
                "none",
            ),
        }
    )
    for interaction in ("alt_tab", "overview"):
        signatures.update(
            {
                ("shell_interaction", "windowed", "windowed", "monitor_a", "monitor_a", interaction),
                (
                    "shell_interaction",
                    "borderless_fullscreen",
                    "borderless_fullscreen",
                    "monitor_a",
                    "monitor_a",
                    interaction,
                ),
                (
                    "shell_interaction",
                    "windowed",
                    "borderless_fullscreen",
                    "monitor_a",
                    "monitor_a",
                    interaction,
                ),
                (
                    "shell_interaction",
                    "borderless_fullscreen",
                    "windowed",
                    "monitor_a",
                    "monitor_a",
                    interaction,
                ),
            }
        )
    return signatures


def _validate_outside_gate(cases: tuple[OutsideGateCase, ...]) -> None:
    actual = {case.case_id for case in cases}
    if actual != _OUTSIDE_GATE_CASES:
        raise EvidenceValidationError(
            f"outside_gate must explicitly list {sorted(_OUTSIDE_GATE_CASES)}; received {sorted(actual)}"
        )
    by_id = {case.case_id: case for case in cases}
    if by_id["exclusive_fullscreen"].classification != "unsupported":
        raise EvidenceValidationError("exclusive_fullscreen must be explicitly unsupported")
    if any(by_id[case_id].classification != "deferred" for case_id in _OUTSIDE_GATE_CASES - {"exclusive_fullscreen"}):
        raise EvidenceValidationError("mixed scale, vertical layout, and primary change must be explicitly deferred")


def _parse_latency_samples(value: object, clock_domains: ClockDomains) -> tuple[LatencySample, ...]:
    values = _sequence(value, "capture.latency_samples")
    if not values:
        raise EvidenceValidationError("capture.latency_samples must not be empty")
    samples: list[LatencySample] = []
    seen_metrics: set[str] = set()
    domains = {
        "client_elapsed": clock_domains.client_elapsed,
        "helper_elapsed": clock_domains.helper_elapsed,
    }
    for index, item in enumerate(values):
        context = f"capture.latency_samples[{index}]"
        raw = _strict_object(item, context, {"metric", "elapsed_ms", "clock_domain", "correlation_id"})
        metric = _choice(raw["metric"], set(_LATENCY_CLOCKS), f"{context}.metric")
        clock_domain = _safe_identifier(raw["clock_domain"], f"{context}.clock_domain")
        expected_domain = domains[_LATENCY_CLOCKS[metric]]
        if clock_domain != expected_domain:
            raise EvidenceValidationError(
                f"{context}.clock_domain must be {expected_domain!r} for {metric}; raw cross-domain clocks are forbidden"
            )
        samples.append(
            LatencySample(
                metric=metric,
                elapsed_ms=_non_negative_number(raw["elapsed_ms"], f"{context}.elapsed_ms"),
                clock_domain=clock_domain,
                correlation_id=_safe_identifier(raw["correlation_id"], f"{context}.correlation_id"),
            )
        )
        seen_metrics.add(metric)
    missing = set(_LATENCY_CLOCKS) - seen_metrics
    if missing:
        raise EvidenceValidationError(f"capture.latency_samples is missing required metrics {sorted(missing)}")
    return tuple(samples)


def _parse_work(value: object) -> Mapping[str, float]:
    raw = _strict_object(value, "capture.work", set(_WORK_FIELDS))
    normalized: dict[str, float] = {}
    for field in _WORK_FIELDS:
        if field in _COUNT_WORK_FIELDS:
            normalized[field] = float(_non_negative_int(raw[field], f"capture.work.{field}"))
        else:
            normalized[field] = _non_negative_number(raw[field], f"capture.work.{field}")
    return MappingProxyType(normalized)


def _parse_idle_cpu(value: object, expected_interval: int) -> IdleCpuSamples:
    raw = _strict_object(
        value,
        "capture.idle_cpu",
        {"interval_seconds", "client_percent_samples", "gnome_shell_percent_samples"},
    )
    interval_seconds = _positive_int(raw["interval_seconds"], "capture.idle_cpu.interval_seconds")
    if interval_seconds != expected_interval:
        raise EvidenceValidationError("capture.idle_cpu.interval_seconds does not match manifest idle interval")
    client = _number_sequence(raw["client_percent_samples"], "capture.idle_cpu.client_percent_samples")
    shell = _number_sequence(raw["gnome_shell_percent_samples"], "capture.idle_cpu.gnome_shell_percent_samples")
    return IdleCpuSamples(
        interval_seconds=interval_seconds,
        client_percent_samples=client,
        gnome_shell_percent_samples=shell,
    )


def _parse_manual_observations(value: object) -> ManualObservations:
    raw = _strict_object(
        value,
        "capture.manual_observations",
        set(_MANUAL_OBSERVATION_FIELDS) | {"note_codes"},
    )
    blocking = {
        field: _boolean(raw[field], f"capture.manual_observations.{field}") for field in _MANUAL_OBSERVATION_FIELDS
    }
    note_values = _sequence(raw["note_codes"], "capture.manual_observations.note_codes")
    note_codes = tuple(
        _safe_identifier(note, f"capture.manual_observations.note_codes[{index}]")
        for index, note in enumerate(note_values)
    )
    if len(note_codes) != len(set(note_codes)):
        raise EvidenceValidationError("capture.manual_observations.note_codes contains duplicates")
    return ManualObservations(blocking=MappingProxyType(blocking), note_codes=note_codes)


def _summarize_scenario(captures: list[PerformanceCapture]) -> ScenarioPerformanceSummary:
    ordered = sorted(captures, key=lambda capture: capture.repetition)
    first = ordered[0]
    comparable = (
        "capture_role",
        "versions",
        "display_configuration_id",
        "payload_fixture_id",
        "diagnostic_configuration_id",
        "observation_seconds",
        "idle_cpu_seconds",
    )
    for capture in ordered[1:]:
        if any(getattr(capture, field) != getattr(first, field) for field in comparable):
            raise EvidenceValidationError(
                f"scenario {first.scenario_id} captures have incompatible metadata or versions"
            )
    latency: dict[str, LatencyStatistics] = {}
    for metric in sorted(_LATENCY_CLOCKS):
        samples = [sample for capture in ordered for sample in capture.latency_samples if sample.metric == metric]
        domains = {sample.clock_domain for sample in samples}
        if len(domains) != 1:
            raise EvidenceValidationError(f"scenario {first.scenario_id} metric {metric} mixes clock domains")
        latency[metric] = _latency_statistics([sample.elapsed_ms for sample in samples], next(iter(domains)))
    observation_total = float(sum(capture.observation_seconds for capture in ordered))
    work_totals = {field: sum(capture.work[field] for capture in ordered) for field in _WORK_FIELDS}
    transitions = work_totals["transitions"]
    work: dict[str, float] = {}
    for field in _WORK_FIELDS:
        if field == "transitions":
            work["transitions_total"] = work_totals[field]
            continue
        work[f"{field}_total"] = work_totals[field]
        work[f"{field}_per_second"] = work_totals[field] / observation_total
    for field in ("helper_health_calls", "helper_target_calls", "helper_presentation_calls"):
        work[f"{field}_per_transition"] = work_totals[field] / transitions if transitions > 0 else 0.0
    client_cpu = [sample for capture in ordered for sample in capture.idle_cpu.client_percent_samples]
    shell_cpu = [sample for capture in ordered for sample in capture.idle_cpu.gnome_shell_percent_samples]
    idle_cpu = {
        "client": _cpu_statistics(client_cpu),
        "gnome_shell": _cpu_statistics(shell_cpu),
    }
    blocking_failures = tuple(
        sorted({reason for capture in ordered for reason in capture.manual_observations.blocking_failures})
    )
    note_codes = tuple(sorted({note for capture in ordered for note in capture.manual_observations.note_codes}))
    return ScenarioPerformanceSummary(
        scenario_id=first.scenario_id,
        capture_role=first.capture_role,
        repetitions=tuple(capture.repetition for capture in ordered),
        versions=first.versions,
        display_configuration_id=first.display_configuration_id,
        payload_fixture_id=first.payload_fixture_id,
        diagnostic_configuration_id=first.diagnostic_configuration_id,
        diagnostic_references=tuple(sorted(capture.diagnostic_reference for capture in ordered)),
        latency=MappingProxyType(latency),
        work=MappingProxyType(dict(sorted(work.items()))),
        idle_cpu=MappingProxyType(idle_cpu),
        blocking_failures=blocking_failures,
        note_codes=note_codes,
    )


def _latency_statistics(values: Sequence[float], clock_domain: str) -> LatencyStatistics:
    if not values:
        raise EvidenceValidationError("latency statistics require at least one sample")
    ordered = sorted(values)
    p95_index = max(0, math.ceil(0.95 * len(ordered)) - 1)
    return LatencyStatistics(
        clock_domain=clock_domain,
        sample_count=len(ordered),
        median=float(statistics.median(ordered)),
        p95=float(ordered[p95_index]),
        maximum=float(ordered[-1]),
    )


def _cpu_statistics(values: Sequence[float]) -> CpuStatistics:
    if not values:
        raise EvidenceValidationError("idle CPU statistics require at least one sample")
    return CpuStatistics(sample_count=len(values), mean=float(statistics.fmean(values)), maximum=float(max(values)))


def _encode_summary(summary: PerformanceSummary) -> dict[str, object]:
    return {
        "schema_version": summary.schema_version,
        "summary_id": summary.summary_id,
        "manifest_id": summary.manifest_id,
        "capture_role": summary.capture_role,
        "environment_key": summary.environment_key,
        "scenarios": [_encode_scenario_summary(scenario) for scenario in summary.scenarios],
    }


def _encode_scenario_summary(summary: ScenarioPerformanceSummary) -> dict[str, object]:
    return {
        "scenario_id": summary.scenario_id,
        "capture_role": summary.capture_role,
        "repetitions": list(summary.repetitions),
        "versions": _encode_capture_versions(summary.versions),
        "display_configuration_id": summary.display_configuration_id,
        "payload_fixture_id": summary.payload_fixture_id,
        "diagnostic_configuration_id": summary.diagnostic_configuration_id,
        "diagnostic_references": list(summary.diagnostic_references),
        "latency": {
            metric: {
                "clock_domain": stats.clock_domain,
                "sample_count": stats.sample_count,
                "median": stats.median,
                "p95": stats.p95,
                "maximum": stats.maximum,
            }
            for metric, stats in sorted(summary.latency.items())
        },
        "work": dict(sorted(summary.work.items())),
        "idle_cpu": {
            component: {
                "sample_count": stats.sample_count,
                "mean": stats.mean,
                "maximum": stats.maximum,
            }
            for component, stats in sorted(summary.idle_cpu.items())
        },
        "blocking_failures": list(summary.blocking_failures),
        "note_codes": list(summary.note_codes),
    }


def _parse_scenario_summary(
    value: object,
    manifest: PerformanceScenarioManifest,
    expected_role: str,
) -> ScenarioPerformanceSummary:
    raw = _strict_object(
        value,
        "summary.scenario",
        {
            "scenario_id",
            "capture_role",
            "repetitions",
            "versions",
            "display_configuration_id",
            "payload_fixture_id",
            "diagnostic_configuration_id",
            "diagnostic_references",
            "latency",
            "work",
            "idle_cpu",
            "blocking_failures",
            "note_codes",
        },
    )
    scenario_id = _safe_identifier(raw["scenario_id"], "summary.scenario.scenario_id")
    scenario = manifest.scenario(scenario_id)
    capture_role = _safe_identifier(raw["capture_role"], "summary.scenario.capture_role")
    if capture_role != expected_role:
        raise EvidenceValidationError("summary scenario capture_role differs from summary role")
    repetitions = tuple(
        _positive_int(item, f"summary.scenario.repetitions[{index}]")
        for index, item in enumerate(_sequence(raw["repetitions"], "summary.scenario.repetitions"))
    )
    if not repetitions or repetitions != tuple(sorted(set(repetitions))):
        raise EvidenceValidationError("summary scenario repetitions must be unique, non-empty, and sorted")
    versions = _parse_capture_versions(raw["versions"])
    display_configuration_id = _safe_identifier(
        raw["display_configuration_id"], "summary.scenario.display_configuration_id"
    )
    payload_fixture_id = _safe_identifier(raw["payload_fixture_id"], "summary.scenario.payload_fixture_id")
    diagnostic_configuration_id = _safe_identifier(
        raw["diagnostic_configuration_id"], "summary.scenario.diagnostic_configuration_id"
    )
    if (
        display_configuration_id != scenario.display_configuration_id
        or payload_fixture_id != scenario.payload_fixture_id
        or diagnostic_configuration_id != scenario.diagnostic_configuration_id
    ):
        raise EvidenceValidationError("summary scenario metadata does not match manifest scenario")
    diagnostic_references = tuple(
        _safe_identifier(item, f"summary.scenario.diagnostic_references[{index}]")
        for index, item in enumerate(_sequence(raw["diagnostic_references"], "summary.scenario.diagnostic_references"))
    )
    latency_raw = _strict_object(raw["latency"], "summary.scenario.latency", set(_LATENCY_CLOCKS))
    latency: dict[str, LatencyStatistics] = {}
    for metric in sorted(_LATENCY_CLOCKS):
        stats_raw = _strict_object(
            latency_raw[metric],
            f"summary.scenario.latency.{metric}",
            {"clock_domain", "sample_count", "median", "p95", "maximum"},
        )
        expected_domain = getattr(manifest.clock_domains, _LATENCY_CLOCKS[metric])
        clock_domain = _safe_identifier(stats_raw["clock_domain"], f"summary.scenario.latency.{metric}.clock_domain")
        if clock_domain != expected_domain:
            raise EvidenceValidationError(f"summary metric {metric} has an incompatible clock domain")
        latency_stats = LatencyStatistics(
            clock_domain=clock_domain,
            sample_count=_positive_int(stats_raw["sample_count"], f"summary.scenario.latency.{metric}.sample_count"),
            median=_non_negative_number(stats_raw["median"], f"summary.scenario.latency.{metric}.median"),
            p95=_non_negative_number(stats_raw["p95"], f"summary.scenario.latency.{metric}.p95"),
            maximum=_non_negative_number(stats_raw["maximum"], f"summary.scenario.latency.{metric}.maximum"),
        )
        if not (latency_stats.median <= latency_stats.p95 <= latency_stats.maximum):
            raise EvidenceValidationError(f"summary metric {metric} statistics are not ordered")
        latency[metric] = latency_stats
    work_raw = _mapping(raw["work"], "summary.scenario.work")
    expected_work_fields = _summary_work_fields()
    if set(work_raw) != expected_work_fields:
        raise EvidenceValidationError("summary.scenario.work has unexpected or missing fields")
    work = {key: _non_negative_number(work_raw[key], f"summary.scenario.work.{key}") for key in sorted(work_raw)}
    idle_raw = _strict_object(raw["idle_cpu"], "summary.scenario.idle_cpu", {"client", "gnome_shell"})
    idle_cpu: dict[str, CpuStatistics] = {}
    for component in ("client", "gnome_shell"):
        stats_raw = _strict_object(
            idle_raw[component],
            f"summary.scenario.idle_cpu.{component}",
            {"sample_count", "mean", "maximum"},
        )
        cpu_stats = CpuStatistics(
            sample_count=_positive_int(
                stats_raw["sample_count"], f"summary.scenario.idle_cpu.{component}.sample_count"
            ),
            mean=_non_negative_number(stats_raw["mean"], f"summary.scenario.idle_cpu.{component}.mean"),
            maximum=_non_negative_number(stats_raw["maximum"], f"summary.scenario.idle_cpu.{component}.maximum"),
        )
        if cpu_stats.mean > cpu_stats.maximum:
            raise EvidenceValidationError(f"summary.scenario.idle_cpu.{component} mean exceeds maximum")
        idle_cpu[component] = cpu_stats
    blocking_failures = _safe_identifier_sequence(raw["blocking_failures"], "summary.scenario.blocking_failures")
    if any(reason not in _MANUAL_OBSERVATION_FIELDS for reason in blocking_failures):
        raise EvidenceValidationError("summary.scenario.blocking_failures contains unknown invariant code")
    note_codes = _safe_identifier_sequence(raw["note_codes"], "summary.scenario.note_codes")
    return ScenarioPerformanceSummary(
        scenario_id=scenario_id,
        capture_role=capture_role,
        repetitions=repetitions,
        versions=versions,
        display_configuration_id=display_configuration_id,
        payload_fixture_id=payload_fixture_id,
        diagnostic_configuration_id=diagnostic_configuration_id,
        diagnostic_references=diagnostic_references,
        latency=MappingProxyType(latency),
        work=MappingProxyType(work),
        idle_cpu=MappingProxyType(idle_cpu),
        blocking_failures=blocking_failures,
        note_codes=note_codes,
    )


def _summary_work_fields() -> set[str]:
    fields = {"transitions_total"}
    for field in _WORK_FIELDS:
        if field == "transitions":
            continue
        fields.add(f"{field}_total")
        fields.add(f"{field}_per_second")
    for field in ("helper_health_calls", "helper_target_calls", "helper_presentation_calls"):
        fields.add(f"{field}_per_transition")
    return fields


def _parse_threshold_provenance(value: object) -> ThresholdProvenance:
    raw = _strict_object(
        value,
        "thresholds.provenance",
        {"captured_date", "baseline_repetitions", "review_state", "rationale", "diagnostic_references"},
    )
    captured_date = _safe_text(raw["captured_date"], "thresholds.provenance.captured_date")
    try:
        date.fromisoformat(captured_date)
    except ValueError as exc:
        raise EvidenceValidationError("thresholds.provenance.captured_date must be ISO-8601") from exc
    review_state = _safe_identifier(raw["review_state"], "thresholds.provenance.review_state")
    if review_state != "reviewed_and_frozen":
        raise EvidenceValidationError("thresholds must be reviewed_and_frozen before candidate comparison")
    rationale = _safe_text(raw["rationale"], "thresholds.provenance.rationale")
    if len(rationale) > 1000:
        raise EvidenceValidationError("thresholds.provenance.rationale is too long")
    references = _safe_identifier_sequence(raw["diagnostic_references"], "thresholds.provenance.diagnostic_references")
    if not references:
        raise EvidenceValidationError("threshold provenance requires diagnostic_references")
    return ThresholdProvenance(
        captured_date=captured_date,
        baseline_repetitions=_positive_int(raw["baseline_repetitions"], "thresholds.provenance.baseline_repetitions"),
        review_state=review_state,
        rationale=rationale,
        diagnostic_references=references,
    )


def _validate_comparable_scenarios(
    baseline: ScenarioPerformanceSummary,
    candidate: ScenarioPerformanceSummary,
) -> None:
    fields = (
        "scenario_id",
        "display_configuration_id",
        "payload_fixture_id",
        "diagnostic_configuration_id",
    )
    if any(getattr(baseline, field) != getattr(candidate, field) for field in fields):
        raise EvidenceValidationError(f"scenario {baseline.scenario_id} comparison inputs differ")


def _summary_metric(summary: ScenarioPerformanceSummary, metric_path: str) -> float:
    parts = metric_path.split(".")
    if parts[0] == "latency":
        stats = summary.latency[parts[1]]
        return float(getattr(stats, parts[2]))
    if parts[0] == "work":
        return float(summary.work[parts[1]])
    return float(getattr(summary.idle_cpu[parts[1]], parts[2]))


def _json_object(payload: str | bytes | Mapping[str, object] | Path, context: str) -> Mapping[str, object]:
    if isinstance(payload, Path):
        try:
            raw_payload: object = json.loads(payload.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise EvidenceValidationError(f"unable to read {context}: {exc}") from exc
    elif isinstance(payload, (str, bytes)):
        try:
            raw_payload = json.loads(payload)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise EvidenceValidationError(f"invalid {context} JSON: {exc}") from exc
    elif isinstance(payload, Mapping):
        raw_payload = payload
    else:
        raise EvidenceValidationError(f"{context} must be standard JSON text, a mapping, or a Path")
    if not isinstance(raw_payload, Mapping):
        raise EvidenceValidationError(f"{context} must be a JSON object")
    _validate_privacy(raw_payload, context)
    return raw_payload


def _validate_privacy(value: object, context: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise EvidenceValidationError(f"{context} contains a non-string JSON key")
            _validate_privacy(child, f"{context}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _validate_privacy(child, f"{context}[{index}]")
    elif isinstance(value, str) and (_PERSONAL_PATH.search(value) or _PROHIBITED_VALUE.search(value)):
        raise EvidenceValidationError(f"{context} contains a prohibited privacy-sensitive value")


def _strict_object(value: object, context: str, fields: set[str] | frozenset[str]) -> Mapping[str, object]:
    raw = _mapping(value, context)
    unexpected = sorted(set(raw) - set(fields))
    missing = sorted(set(fields) - set(raw))
    if unexpected:
        raise EvidenceValidationError(f"{context} contains unexpected field(s): {unexpected}")
    if missing:
        raise EvidenceValidationError(f"{context} is missing required field(s): {missing}")
    return raw


def _mapping(value: object, context: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise EvidenceValidationError(f"{context} must be a JSON object")
    if not all(isinstance(key, str) for key in value):
        raise EvidenceValidationError(f"{context} keys must be strings")
    return value


def _sequence(value: object, context: str) -> Sequence[object]:
    if not isinstance(value, (list, tuple)):
        raise EvidenceValidationError(f"{context} must be a JSON array")
    return value


def _safe_text(value: object, context: str) -> str:
    if not isinstance(value, str) or not value:
        raise EvidenceValidationError(f"{context} must be a non-empty string")
    _validate_privacy(value, context)
    return value


def _safe_identifier(value: object, context: str) -> str:
    text = _safe_text(value, context)
    if not _SAFE_IDENTIFIER.fullmatch(text):
        raise EvidenceValidationError(f"{context} must be a stable safe identifier")
    return text


def _safe_version(value: object, context: str) -> str:
    text = _safe_text(value, context)
    if len(text) > 64 or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.+_-]{0,63}", text):
        raise EvidenceValidationError(f"{context} must be a bounded safe version")
    return text


def _source_revision(value: object, context: str) -> str:
    text = _safe_text(value, context)
    if not _SAFE_REVISION.fullmatch(text):
        raise EvidenceValidationError(f"{context} must be a lowercase source revision")
    return text


def _repository_path(value: object, context: str) -> str:
    text = _safe_text(value, context)
    path = Path(text)
    if path.is_absolute() or ".." in path.parts or "~" in path.parts:
        raise EvidenceValidationError(f"{context} must be a safe repository-relative path")
    return path.as_posix()


def _schema_version(value: object, expected: int, context: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value != expected:
        raise EvidenceValidationError(f"{context} must be supported schema_version {expected}")


def _integer(value: object, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise EvidenceValidationError(f"{context} must be an integer")
    return value


def _positive_int(value: object, context: str) -> int:
    result = _integer(value, context)
    if result <= 0:
        raise EvidenceValidationError(f"{context} must be positive")
    return result


def _non_negative_int(value: object, context: str) -> int:
    result = _integer(value, context)
    if result < 0:
        raise EvidenceValidationError(f"{context} must be non-negative")
    return result


def _number(value: object, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EvidenceValidationError(f"{context} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise EvidenceValidationError(f"{context} must be finite")
    return result


def _positive_number(value: object, context: str) -> float:
    result = _number(value, context)
    if result <= 0:
        raise EvidenceValidationError(f"{context} must be positive")
    return result


def _non_negative_number(value: object, context: str) -> float:
    result = _number(value, context)
    if result < 0:
        raise EvidenceValidationError(f"{context} must be non-negative")
    return result


def _boolean(value: object, context: str) -> bool:
    if not isinstance(value, bool):
        raise EvidenceValidationError(f"{context} must be a boolean")
    return value


def _choice(value: object, choices: set[str] | frozenset[str], context: str) -> str:
    text = _safe_identifier(value, context)
    if text not in choices:
        raise EvidenceValidationError(f"{context} must be one of {sorted(choices)}")
    return text


def _number_sequence(value: object, context: str) -> tuple[float, ...]:
    values = _sequence(value, context)
    if not values:
        raise EvidenceValidationError(f"{context} must not be empty")
    return tuple(_non_negative_number(item, f"{context}[{index}]") for index, item in enumerate(values))


def _safe_identifier_sequence(value: object, context: str) -> tuple[str, ...]:
    values = _sequence(value, context)
    normalized = tuple(_safe_identifier(item, f"{context}[{index}]") for index, item in enumerate(values))
    if len(normalized) != len(set(normalized)) or normalized != tuple(sorted(normalized)):
        raise EvidenceValidationError(f"{context} must contain unique sorted safe identifiers")
    return normalized


def _encode_capture_versions(versions: CaptureVersions) -> dict[str, object]:
    return {
        "plugin": versions.plugin,
        "client": versions.client,
        "helper_protocol": versions.helper_protocol,
        "source_revision": versions.source_revision,
        "architecture_stage": versions.architecture_stage,
    }


def _deterministic_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n"


__all__ = [
    "REQUIRED_THRESHOLD_PATHS",
    "CaptureTiming",
    "ClockDomains",
    "CpuStatistics",
    "DiagnosticConfiguration",
    "DisplayConfiguration",
    "EvidenceValidationError",
    "InvestigationThreshold",
    "LatencySample",
    "LatencyStatistics",
    "ManualObservations",
    "MonitorGeometry",
    "OutsideGateCase",
    "PayloadFixture",
    "PerformanceCapture",
    "PerformanceComparison",
    "PerformanceScenario",
    "PerformanceScenarioManifest",
    "PerformanceSummary",
    "PerformanceThresholds",
    "ScenarioComparison",
    "ScenarioPerformanceSummary",
    "TargetEnvironment",
    "build_performance_summary",
    "compare_performance_summaries",
    "format_performance_comparison",
    "format_performance_summary",
    "parse_performance_capture",
    "parse_performance_manifest",
    "parse_performance_summary",
    "parse_performance_thresholds",
    "serialize_performance_comparison",
    "serialize_performance_summary",
]
