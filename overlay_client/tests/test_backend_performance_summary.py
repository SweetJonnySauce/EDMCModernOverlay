from __future__ import annotations

import copy
import json
import subprocess
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from overlay_client.backend.performance_evidence import (
    REQUIRED_THRESHOLD_PATHS,
    EvidenceValidationError,
    build_performance_summary,
    compare_performance_summaries,
    format_performance_comparison,
    format_performance_summary,
    parse_performance_capture,
    parse_performance_manifest,
    parse_performance_summary,
    parse_performance_thresholds,
    serialize_performance_comparison,
    serialize_performance_summary,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
COMMITTED_MANIFEST = (
    REPO_ROOT / "docs" / "support" / "validation" / "fix219-pre-migration" / "performance" / "manifest.json"
)
SUPERSEDED_FULL_MATRIX_ROOT = (
    REPO_ROOT
    / "docs"
    / "support"
    / "validation"
    / "fix219-pre-migration"
    / "performance"
    / "superseded"
    / "full-matrix-v1"
)
PERFORMANCE_CLI = REPO_ROOT / "scripts" / "backend_performance.py"
SAFE_REVISION = "3d2332869454d6561995203752fd239a558a95a5"
FIXTURE_SHA256 = "3766f57248d032c8a01844de0994fe31f0211211a3292660a442aa9d68b923f9"


def _scenario(
    scale: int,
    suffix: str,
    *,
    action: str,
    start_mode: str,
    end_mode: str,
    start_monitor: str,
    end_monitor: str,
    interaction: str = "none",
) -> dict[str, object]:
    return {
        "scenario_id": f"scale_{scale}_{suffix}",
        "display_configuration_id": f"dual_ultrawide_scale_{scale}",
        "action": action,
        "start_mode": start_mode,
        "end_mode": end_mode,
        "start_monitor": start_monitor,
        "end_monitor": end_monitor,
        "interaction": interaction,
        "payload_fixture_id": "representative_payload_v1",
        "diagnostic_configuration_id": "performance_diagnostics_v1",
        "workload": "idle_then_representative",
    }


def _required_scenarios(scale: int) -> list[dict[str, object]]:
    scenarios = [
        _scenario(
            scale,
            "stable_windowed_monitor_a",
            action="stable",
            start_mode="windowed",
            end_mode="windowed",
            start_monitor="monitor_a",
            end_monitor="monitor_a",
        ),
        _scenario(
            scale,
            "stable_borderless_fullscreen_monitor_a",
            action="stable",
            start_mode="borderless_fullscreen",
            end_mode="borderless_fullscreen",
            start_monitor="monitor_a",
            end_monitor="monitor_a",
        ),
        _scenario(
            scale,
            "windowed_to_fullscreen_monitor_a",
            action="mode_transition",
            start_mode="windowed",
            end_mode="borderless_fullscreen",
            start_monitor="monitor_a",
            end_monitor="monitor_a",
        ),
        _scenario(
            scale,
            "fullscreen_to_windowed_monitor_a",
            action="mode_transition",
            start_mode="borderless_fullscreen",
            end_mode="windowed",
            start_monitor="monitor_a",
            end_monitor="monitor_a",
        ),
        _scenario(
            scale,
            "stable_windowed_monitor_b",
            action="stable",
            start_mode="windowed",
            end_mode="windowed",
            start_monitor="monitor_b",
            end_monitor="monitor_b",
        ),
    ]
    if scale == 100:
        scenarios.extend(
            [
                _scenario(
                    scale,
                    "fullscreen_handoff_a_to_b",
                    action="monitor_handoff",
                    start_mode="borderless_fullscreen",
                    end_mode="borderless_fullscreen",
                    start_monitor="monitor_a",
                    end_monitor="monitor_b",
                ),
                _scenario(
                    scale,
                    "fullscreen_handoff_b_to_a",
                    action="monitor_handoff",
                    start_mode="borderless_fullscreen",
                    end_mode="borderless_fullscreen",
                    start_monitor="monitor_b",
                    end_monitor="monitor_a",
                ),
                _scenario(
                    scale,
                    "alt_tab_stable_fullscreen",
                    action="shell_interaction",
                    start_mode="borderless_fullscreen",
                    end_mode="borderless_fullscreen",
                    start_monitor="monitor_a",
                    end_monitor="monitor_a",
                    interaction="alt_tab",
                ),
                _scenario(
                    scale,
                    "overview_stable_windowed",
                    action="shell_interaction",
                    start_mode="windowed",
                    end_mode="windowed",
                    start_monitor="monitor_a",
                    end_monitor="monitor_a",
                    interaction="overview",
                ),
            ]
        )
    return scenarios


def _manifest_dict() -> dict[str, object]:
    return {
        "schema_version": 1,
        "manifest_id": "fix219_gnome46_pre_migration_reduced_v2",
        "capture_route": "shipped_pre_migration",
        "target_environment": {
            "operating_system": "linux",
            "distribution": "ubuntu",
            "distribution_version": "24.04.4",
            "session_type": "wayland",
            "desktop": "gnome",
            "compositor": "mutter",
            "compositor_version": "46.0",
        },
        "reference_versions": {
            "plugin": "1.0.0",
            "client": "1.0.0",
            "helper_protocol": 3,
            "source_revision": SAFE_REVISION,
        },
        "payload_fixtures": [
            {
                "fixture_id": "representative_payload_v1",
                "repository_path": "tests/archive/display_all.json",
                "sha256": FIXTURE_SHA256,
            }
        ],
        "diagnostic_configurations": [
            {
                "configuration_id": "performance_diagnostics_v1",
                "toggles": {
                    "developer_mode": True,
                    "client_raster_timing": True,
                    "helper_raster_timing": True,
                    "presentation_timing": True,
                    "repaint_metrics": True,
                    "idle_cpu_sampling": True,
                    "detailed_traces": True,
                    "visual_debug_overlays": False,
                },
            }
        ],
        "clock_domains": {
            "client_elapsed": "client_perf_counter",
            "helper_elapsed": "gnome_shell_monotonic",
        },
        "timing": {
            "warm_up_seconds": 10,
            "observation_seconds": 30,
            "idle_cpu_seconds": 15,
            "repetitions": 3,
        },
        "display_configurations": [
            {
                "configuration_id": "dual_ultrawide_scale_100",
                "scale_percent": 100,
                "orientation": "horizontal",
                "primary_monitor": "monitor_b",
                "compositor_coordinate_space": "gnome_shell_global_logical",
                "negative_coordinate_space": "primary_monitor_relative_logical",
                "monitors": [
                    {
                        "monitor_id": "monitor_a",
                        "compositor_logical_x": 0,
                        "compositor_logical_y": 0,
                        "primary_relative_logical_x": -3440,
                        "primary_relative_logical_y": 0,
                        "logical_width": 3440,
                        "logical_height": 1440,
                        "physical_width_px": 3440,
                        "physical_height_px": 1440,
                    },
                    {
                        "monitor_id": "monitor_b",
                        "compositor_logical_x": 3440,
                        "compositor_logical_y": 0,
                        "primary_relative_logical_x": 0,
                        "primary_relative_logical_y": 0,
                        "logical_width": 3440,
                        "logical_height": 1440,
                        "physical_width_px": 3440,
                        "physical_height_px": 1440,
                    },
                ],
            },
            {
                "configuration_id": "dual_ultrawide_scale_125",
                "scale_percent": 125,
                "orientation": "horizontal",
                "primary_monitor": "monitor_b",
                "compositor_coordinate_space": "gnome_shell_global_logical",
                "negative_coordinate_space": "primary_monitor_relative_logical",
                "monitors": [
                    {
                        "monitor_id": "monitor_a",
                        "compositor_logical_x": 0,
                        "compositor_logical_y": 0,
                        "primary_relative_logical_x": -2752,
                        "primary_relative_logical_y": 0,
                        "logical_width": 2752,
                        "logical_height": 1152,
                        "physical_width_px": 3440,
                        "physical_height_px": 1440,
                    },
                    {
                        "monitor_id": "monitor_b",
                        "compositor_logical_x": 2752,
                        "compositor_logical_y": 0,
                        "primary_relative_logical_x": 0,
                        "primary_relative_logical_y": 0,
                        "logical_width": 2752,
                        "logical_height": 1152,
                        "physical_width_px": 3440,
                        "physical_height_px": 1440,
                    },
                ],
            },
        ],
        "scenarios": _required_scenarios(100) + _required_scenarios(125),
        "outside_gate": [
            {
                "case_id": "mixed_scale",
                "classification": "deferred",
                "reason_code": "mixed_per_monitor_scale_not_in_initial_gate",
            },
            {
                "case_id": "vertical_layout",
                "classification": "deferred",
                "reason_code": "vertical_layout_not_in_initial_gate",
            },
            {
                "case_id": "primary_monitor_change",
                "classification": "deferred",
                "reason_code": "runtime_primary_change_not_in_initial_gate",
            },
            {
                "case_id": "exclusive_fullscreen",
                "classification": "unsupported",
                "reason_code": "exclusive_fullscreen_not_supported",
            },
        ],
    }


def _capture_dict(
    manifest: dict[str, object],
    scenario_id: str,
    repetition: int,
    *,
    capture_role: str = "baseline",
    latency_offset: float = 0.0,
) -> dict[str, object]:
    scenarios = manifest["scenarios"]
    assert isinstance(scenarios, list)
    scenario = next(item for item in scenarios if item["scenario_id"] == scenario_id)
    reference_versions = copy.deepcopy(manifest["reference_versions"])
    assert isinstance(reference_versions, dict)
    timing = manifest["timing"]
    assert isinstance(timing, dict)
    return {
        "schema_version": 1,
        "manifest_id": manifest["manifest_id"],
        "capture_id": f"capture_{capture_role}_{scenario_id}_{repetition}",
        "capture_role": capture_role,
        "scenario_id": scenario_id,
        "repetition": repetition,
        "environment": copy.deepcopy(manifest["target_environment"]),
        "versions": {
            **reference_versions,
            "architecture_stage": "pre_migration" if capture_role == "baseline" else "candidate",
        },
        "display_configuration_id": scenario["display_configuration_id"],
        "payload_fixture_id": scenario["payload_fixture_id"],
        "diagnostic_configuration_id": scenario["diagnostic_configuration_id"],
        "clock_domains": copy.deepcopy(manifest["clock_domains"]),
        "warm_up_seconds": timing["warm_up_seconds"],
        "observation_seconds": timing["observation_seconds"],
        "idle_cpu_seconds": timing["idle_cpu_seconds"],
        "diagnostic_reference": f"diag_{scenario_id}_{repetition}",
        "latency_samples": [
            {
                "metric": "presentation_cycle_ms",
                "elapsed_ms": 1.0 + latency_offset + repetition,
                "clock_domain": "client_perf_counter",
                "correlation_id": f"cycle_{repetition}_a",
            },
            {
                "metric": "presentation_cycle_ms",
                "elapsed_ms": 3.0 + latency_offset + repetition,
                "clock_domain": "client_perf_counter",
                "correlation_id": f"cycle_{repetition}_b",
            },
            {
                "metric": "end_to_stable_ms",
                "elapsed_ms": 10.0 + latency_offset + repetition,
                "clock_domain": "client_perf_counter",
                "correlation_id": f"transition_{repetition}",
            },
            {
                "metric": "helper_apply_ms",
                "elapsed_ms": 2.0 + latency_offset + repetition,
                "clock_domain": "gnome_shell_monotonic",
                "correlation_id": f"frame_{repetition}",
            },
        ],
        "work": {
            "helper_health_calls": 6,
            "helper_target_calls": 12,
            "helper_presentation_calls": 18,
            "transitions": 1,
            "raster_builds": 4,
            "raster_reuses": 5,
            "raster_skips": 6,
            "raster_bytes": 1000,
            "raster_regions": 8,
            "raster_encode_ms": 9.5,
            "helper_decode_ms": 7.5,
            "helper_apply_ms": 3.5,
            "repaints": 20,
            "paints": 15,
            "frame_builds": 10,
        },
        "idle_cpu": {
            "interval_seconds": timing["idle_cpu_seconds"],
            "client_percent_samples": [1.0 + repetition, 2.0 + repetition],
            "gnome_shell_percent_samples": [3.0 + repetition, 4.0 + repetition],
        },
        "manual_observations": {
            "dual_visible_presenters": False,
            "title_bar_intermediate": False,
            "monitor_relative_intermediate": False,
            "black_surface": False,
            "focus_trap": False,
            "unexpected_identity": False,
            "premature_commitment": False,
            "material_hitch": False,
            "note_codes": [],
        },
    }


def _threshold_dict(manifest_id: str, baseline_summary_id: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "threshold_id": "fix219_baseline_thresholds_v1",
        "manifest_id": manifest_id,
        "baseline_summary_id": baseline_summary_id,
        "provenance": {
            "captured_date": "2026-07-20",
            "baseline_repetitions": 3,
            "review_state": "reviewed_and_frozen",
            "rationale": "Limits exceed observed repeated baseline variance and retain an absolute noise floor.",
            "diagnostic_references": ["baseline_review_01"],
        },
        "thresholds": [
            {
                "metric_path": path,
                "relative_limit": 0.10,
                "absolute_noise_floor": 0.05 if path.startswith("work.") else 1.0,
            }
            for path in REQUIRED_THRESHOLD_PATHS
        ],
    }


def _summaries_for_comparison(*, candidate_offset: float = 0.0):
    manifest_raw = _manifest_dict()
    manifest = parse_performance_manifest(manifest_raw)
    scenario_id = "scale_100_windowed_to_fullscreen_monitor_a"
    baseline_captures = [
        parse_performance_capture(_capture_dict(manifest_raw, scenario_id, repetition), manifest)
        for repetition in (1, 2)
    ]
    candidate_captures = [
        parse_performance_capture(
            _capture_dict(
                manifest_raw,
                scenario_id,
                repetition,
                capture_role="candidate",
                latency_offset=candidate_offset,
            ),
            manifest,
        )
        for repetition in (1, 2)
    ]
    baseline = build_performance_summary(
        manifest,
        baseline_captures,
        summary_id="baseline_summary_v1",
    )
    candidate = build_performance_summary(
        manifest,
        candidate_captures,
        summary_id="candidate_summary_v1",
    )
    thresholds = parse_performance_thresholds(
        _threshold_dict(manifest.manifest_id, baseline.summary_id),
        manifest,
    )
    return manifest, baseline, candidate, thresholds


def test_committed_manifest_is_complete_and_machine_validated() -> None:
    manifest = parse_performance_manifest(COMMITTED_MANIFEST.read_text(encoding="utf-8"))

    assert manifest.schema_version == 1
    assert manifest.manifest_id == "fix219_gnome46_pre_migration_reduced_v2"
    assert {configuration.scale_percent for configuration in manifest.display_configurations} == {100, 125}
    assert len(manifest.scenarios) == 14
    assert manifest.timing.warm_up_seconds == 10
    assert manifest.timing.observation_seconds == 30
    assert manifest.timing.idle_cpu_seconds == 15
    assert manifest.timing.repetitions == 3
    assert len(manifest.scenarios) * manifest.timing.repetitions == 42
    assert all(
        configuration.compositor_coordinate_space == "gnome_shell_global_logical"
        and configuration.negative_coordinate_space == "primary_monitor_relative_logical"
        and min(monitor.compositor_logical_x for monitor in configuration.monitors) == 0
        and any(monitor.primary_relative_logical_x < 0 for monitor in configuration.monitors)
        for configuration in manifest.display_configurations
    )
    assert {case.case_id for case in manifest.outside_gate} == {
        "mixed_scale",
        "vertical_layout",
        "primary_monitor_change",
        "exclusive_fullscreen",
    }


def test_superseded_full_matrix_manifest_and_captures_remain_machine_validated() -> None:
    manifest = parse_performance_manifest(SUPERSEDED_FULL_MATRIX_ROOT / "manifest.json")
    capture_paths = sorted((SUPERSEDED_FULL_MATRIX_ROOT / "captures").glob("**/*.json"))
    captures = [parse_performance_capture(path, manifest) for path in capture_paths]

    assert manifest.manifest_id == "fix219_gnome46_pre_migration_v1"
    assert len(manifest.scenarios) == 36
    assert manifest.timing.repetitions == 5
    assert [capture.repetition for capture in captures] == [1, 2]


def test_manifest_rejects_missing_required_scenario() -> None:
    raw = _manifest_dict()
    scenarios = raw["scenarios"]
    assert isinstance(scenarios, list)
    scenarios.pop()

    with pytest.raises(EvidenceValidationError, match="required scenario coverage"):
        parse_performance_manifest(raw)


def test_manifest_rejects_duplicate_and_unsafe_scenario_ids() -> None:
    duplicate = _manifest_dict()
    scenarios = duplicate["scenarios"]
    assert isinstance(scenarios, list)
    scenarios[1]["scenario_id"] = scenarios[0]["scenario_id"]
    with pytest.raises(EvidenceValidationError, match="duplicate scenario_id"):
        parse_performance_manifest(duplicate)

    unsafe = _manifest_dict()
    unsafe_scenarios = unsafe["scenarios"]
    assert isinstance(unsafe_scenarios, list)
    unsafe_scenarios[0]["scenario_id"] = "../../unsafe"
    with pytest.raises(EvidenceValidationError, match="safe identifier"):
        parse_performance_manifest(unsafe)


def test_manifest_rejects_duplicate_scenario_signatures_even_with_unique_ids() -> None:
    raw = _manifest_dict()
    scenarios = raw["scenarios"]
    assert isinstance(scenarios, list)
    duplicate = copy.deepcopy(scenarios[0])
    duplicate["scenario_id"] = "scale_100_duplicate_stable_windowed_a"
    scenarios.append(duplicate)

    with pytest.raises(EvidenceValidationError, match="duplicate required scenario signature"):
        parse_performance_manifest(raw)


@pytest.mark.parametrize("schema_version", [0, 2, "1", None])
def test_manifest_rejects_unknown_schema_versions(schema_version: object) -> None:
    raw = _manifest_dict()
    raw["schema_version"] = schema_version

    with pytest.raises(EvidenceValidationError, match="schema_version"):
        parse_performance_manifest(raw)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("logical_width", 0),
        ("logical_height", -1),
        ("physical_width_px", 0),
        ("physical_height_px", -1),
    ],
)
def test_manifest_rejects_invalid_monitor_dimensions(field: str, value: int) -> None:
    raw = _manifest_dict()
    configurations = raw["display_configurations"]
    assert isinstance(configurations, list)
    configurations[0]["monitors"][0][field] = value

    with pytest.raises(EvidenceValidationError, match=field):
        parse_performance_manifest(raw)


@pytest.mark.parametrize("scale", [0, 99, 110, 150])
def test_manifest_rejects_invalid_or_missing_scale_coverage(scale: int) -> None:
    raw = _manifest_dict()
    configurations = raw["display_configurations"]
    assert isinstance(configurations, list)
    configurations[0]["scale_percent"] = scale

    with pytest.raises(EvidenceValidationError, match="scale"):
        parse_performance_manifest(raw)


def test_manifest_rejects_non_horizontal_overlapping_or_non_negative_layouts() -> None:
    vertical = _manifest_dict()
    configurations = vertical["display_configurations"]
    assert isinstance(configurations, list)
    configurations[0]["monitors"][1]["compositor_logical_y"] = 100
    with pytest.raises(EvidenceValidationError, match="horizontal"):
        parse_performance_manifest(vertical)

    overlap = _manifest_dict()
    overlap_configurations = overlap["display_configurations"]
    assert isinstance(overlap_configurations, list)
    overlap_configurations[0]["monitors"][1]["compositor_logical_x"] = 3000
    with pytest.raises(EvidenceValidationError, match="overlap|contiguous"):
        parse_performance_manifest(overlap)

    non_negative = _manifest_dict()
    non_negative_configurations = non_negative["display_configurations"]
    assert isinstance(non_negative_configurations, list)
    non_negative_configurations[0]["monitors"][0]["primary_relative_logical_x"] = 0
    with pytest.raises(EvidenceValidationError, match="negative"):
        parse_performance_manifest(non_negative)


def test_manifest_rejects_primary_relative_geometry_not_derived_from_compositor_geometry() -> None:
    raw = _manifest_dict()
    configurations = raw["display_configurations"]
    assert isinstance(configurations, list)
    configurations[0]["monitors"][0]["primary_relative_logical_x"] = -3000

    with pytest.raises(EvidenceValidationError, match="derived from compositor geometry"):
        parse_performance_manifest(raw)


@pytest.mark.parametrize("field", ["warm_up_seconds", "observation_seconds", "idle_cpu_seconds", "repetitions"])
@pytest.mark.parametrize("value", [0, -1, True, 1.5])
def test_manifest_rejects_invalid_timing_and_counts(field: str, value: object) -> None:
    raw = _manifest_dict()
    timing = raw["timing"]
    assert isinstance(timing, dict)
    timing[field] = value

    with pytest.raises(EvidenceValidationError, match=field):
        parse_performance_manifest(raw)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("desktop", "token=super-secret"),
        ("desktop", "/home/alice/private"),
        ("desktop", r"C:\\Users\\Alice\\private"),
        ("desktop", "window_title=Elite Dangerous"),
        ("desktop", "command_line=python secret.py"),
        ("desktop", "owner_id=raw-owner"),
        ("desktop", "target_handle=0x123"),
    ],
)
def test_manifest_rejects_prohibited_private_values(field: str, value: str) -> None:
    raw = _manifest_dict()
    environment = raw["target_environment"]
    assert isinstance(environment, dict)
    environment[field] = value

    with pytest.raises(EvidenceValidationError, match="privacy|prohibited"):
        parse_performance_manifest(raw)


def test_manifest_rejects_broad_environment_or_screenshot_fields() -> None:
    broad = _manifest_dict()
    broad["environment_dump"] = {"HOME": "/home/alice", "PATH": "..."}
    with pytest.raises(EvidenceValidationError, match="unexpected field|privacy|prohibited"):
        parse_performance_manifest(broad)

    screenshot = _manifest_dict()
    screenshot["screenshot"] = "capture.png"
    with pytest.raises(EvidenceValidationError, match="unexpected field"):
        parse_performance_manifest(screenshot)


def test_manifest_rejects_unknown_references() -> None:
    raw = _manifest_dict()
    scenarios = raw["scenarios"]
    assert isinstance(scenarios, list)
    scenarios[0]["payload_fixture_id"] = "missing_fixture"

    with pytest.raises(EvidenceValidationError, match="payload_fixture_id"):
        parse_performance_manifest(raw)


def test_capture_accepts_manifest_linked_sanitized_record() -> None:
    raw = _manifest_dict()
    manifest = parse_performance_manifest(raw)
    scenario_id = "scale_100_windowed_to_fullscreen_monitor_a"

    capture = parse_performance_capture(_capture_dict(raw, scenario_id, 1), manifest)

    assert capture.manifest_id == manifest.manifest_id
    assert capture.scenario_id == scenario_id
    assert capture.repetition == 1
    assert {sample.clock_domain for sample in capture.latency_samples} == {
        "client_perf_counter",
        "gnome_shell_monotonic",
    }


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("manifest_id", "other_manifest", "manifest_id"),
        ("scenario_id", "unknown_scenario", "scenario_id"),
        ("display_configuration_id", "other_display", "display_configuration_id"),
        ("payload_fixture_id", "other_fixture", "payload_fixture_id"),
        ("diagnostic_configuration_id", "other_diagnostics", "diagnostic_configuration_id"),
        ("warm_up_seconds", 31, "warm_up_seconds"),
        ("observation_seconds", 61, "observation_seconds"),
        ("idle_cpu_seconds", 61, "idle_cpu_seconds"),
    ],
)
def test_capture_rejects_incompatible_manifest_inputs(field: str, value: object, match: str) -> None:
    raw = _manifest_dict()
    manifest = parse_performance_manifest(raw)
    capture = _capture_dict(raw, "scale_100_windowed_to_fullscreen_monitor_a", 1)
    capture[field] = value

    with pytest.raises(EvidenceValidationError, match=match):
        parse_performance_capture(capture, manifest)


def test_baseline_capture_requires_exact_reference_versions() -> None:
    raw = _manifest_dict()
    manifest = parse_performance_manifest(raw)
    capture = _capture_dict(raw, "scale_100_windowed_to_fullscreen_monitor_a", 1)
    versions = capture["versions"]
    assert isinstance(versions, dict)
    versions["source_revision"] = "abcdef1"

    with pytest.raises(EvidenceValidationError, match="reference_versions"):
        parse_performance_capture(capture, manifest)


def test_capture_rejects_cross_domain_or_raw_clock_inputs() -> None:
    raw = _manifest_dict()
    manifest = parse_performance_manifest(raw)
    capture = _capture_dict(raw, "scale_100_windowed_to_fullscreen_monitor_a", 1)
    latency_samples = capture["latency_samples"]
    assert isinstance(latency_samples, list)
    latency_samples[0]["clock_domain"] = "gnome_shell_monotonic"
    with pytest.raises(EvidenceValidationError, match="clock_domain"):
        parse_performance_capture(capture, manifest)

    raw_clock = _capture_dict(raw, "scale_100_windowed_to_fullscreen_monitor_a", 1)
    raw_clock_samples = raw_clock["latency_samples"]
    assert isinstance(raw_clock_samples, list)
    raw_clock_samples[0]["started_at_monotonic"] = 999999.0
    with pytest.raises(EvidenceValidationError, match="unexpected field"):
        parse_performance_capture(raw_clock, manifest)


@pytest.mark.parametrize(
    "mutation",
    [
        {"capture_token": "secret"},
        {"window_title": "Elite Dangerous"},
        {"command_line": "python capture.py"},
        {"owner_id": "raw-owner"},
        {"target_handle": "0x123"},
        {"screenshot": "capture.png"},
        {"personal_path": "/home/alice/capture.json"},
    ],
)
def test_capture_rejects_prohibited_diagnostic_fields(mutation: dict[str, object]) -> None:
    raw = _manifest_dict()
    manifest = parse_performance_manifest(raw)
    capture = _capture_dict(raw, "scale_100_windowed_to_fullscreen_monitor_a", 1)
    capture.update(mutation)

    with pytest.raises(EvidenceValidationError, match="unexpected field|privacy|prohibited"):
        parse_performance_capture(capture, manifest)


def test_capture_rejects_empty_invalid_or_non_finite_samples() -> None:
    raw = _manifest_dict()
    manifest = parse_performance_manifest(raw)
    capture = _capture_dict(raw, "scale_100_windowed_to_fullscreen_monitor_a", 1)
    capture["latency_samples"] = []
    with pytest.raises(EvidenceValidationError, match="latency_samples"):
        parse_performance_capture(capture, manifest)

    invalid = _capture_dict(raw, "scale_100_windowed_to_fullscreen_monitor_a", 1)
    invalid_samples = invalid["latency_samples"]
    assert isinstance(invalid_samples, list)
    invalid_samples[0]["elapsed_ms"] = float("nan")
    with pytest.raises(EvidenceValidationError, match="finite"):
        parse_performance_capture(invalid, manifest)


def test_capture_rejects_wrong_idle_interval_or_invalid_cpu() -> None:
    raw = _manifest_dict()
    manifest = parse_performance_manifest(raw)
    capture = _capture_dict(raw, "scale_100_windowed_to_fullscreen_monitor_a", 1)
    idle_cpu = capture["idle_cpu"]
    assert isinstance(idle_cpu, dict)
    idle_cpu["interval_seconds"] = 59
    with pytest.raises(EvidenceValidationError, match="interval_seconds"):
        parse_performance_capture(capture, manifest)

    invalid = _capture_dict(raw, "scale_100_windowed_to_fullscreen_monitor_a", 1)
    invalid_idle_cpu = invalid["idle_cpu"]
    assert isinstance(invalid_idle_cpu, dict)
    invalid_idle_cpu["client_percent_samples"] = [-1]
    with pytest.raises(EvidenceValidationError, match="client_percent_samples"):
        parse_performance_capture(invalid, manifest)


def test_summary_uses_nearest_rank_p95_and_deterministic_aggregation() -> None:
    raw = _manifest_dict()
    manifest = parse_performance_manifest(raw)
    scenario_id = "scale_100_windowed_to_fullscreen_monitor_a"
    first_raw = _capture_dict(raw, scenario_id, 1)
    second_raw = _capture_dict(raw, scenario_id, 2)
    first_samples = first_raw["latency_samples"]
    second_samples = second_raw["latency_samples"]
    assert isinstance(first_samples, list)
    assert isinstance(second_samples, list)
    first_samples[0]["elapsed_ms"] = 1.0
    first_samples[1]["elapsed_ms"] = 2.0
    second_samples[0]["elapsed_ms"] = 3.0
    second_samples[1]["elapsed_ms"] = 100.0
    captures = [
        parse_performance_capture(first_raw, manifest),
        parse_performance_capture(second_raw, manifest),
    ]

    summary = build_performance_summary(manifest, reversed(captures), summary_id="summary_v1")
    scenario = summary.scenarios[0]
    latency = scenario.latency["presentation_cycle_ms"]

    assert (latency.sample_count, latency.median, latency.p95, latency.maximum) == (4, 2.5, 100.0, 100.0)
    assert scenario.latency["helper_apply_ms"].clock_domain == "gnome_shell_monotonic"
    assert scenario.work["helper_health_calls_per_second"] == pytest.approx(0.2)
    assert scenario.work["helper_presentation_calls_per_transition"] == pytest.approx(18.0)
    assert scenario.work["raster_bytes_per_second"] == pytest.approx(1000 / 30)
    assert scenario.idle_cpu["client"].mean == pytest.approx(3.0)
    assert scenario.idle_cpu["client"].maximum == 4.0
    assert serialize_performance_summary(summary) == serialize_performance_summary(
        build_performance_summary(manifest, captures, summary_id="summary_v1")
    )


def test_summary_rejects_duplicate_repetitions_and_incomplete_complete_set() -> None:
    raw = _manifest_dict()
    manifest = parse_performance_manifest(raw)
    scenario_id = "scale_100_windowed_to_fullscreen_monitor_a"
    capture = parse_performance_capture(_capture_dict(raw, scenario_id, 1), manifest)

    with pytest.raises(EvidenceValidationError, match="duplicate repetition"):
        build_performance_summary(manifest, [capture, capture], summary_id="summary_v1")

    with pytest.raises(EvidenceValidationError, match="complete capture set"):
        build_performance_summary(manifest, [capture], summary_id="summary_v1", require_complete=True)


def test_summary_rejects_mixed_component_versions_across_scenarios() -> None:
    raw = _manifest_dict()
    manifest = parse_performance_manifest(raw)
    first_raw = _capture_dict(raw, "scale_100_stable_windowed_monitor_a", 1, capture_role="candidate")
    second_raw = _capture_dict(raw, "scale_100_stable_windowed_monitor_b", 1, capture_role="candidate")
    second_versions = second_raw["versions"]
    assert isinstance(second_versions, dict)
    second_versions["source_revision"] = "abcdef1"
    captures = [
        parse_performance_capture(first_raw, manifest),
        parse_performance_capture(second_raw, manifest),
    ]

    with pytest.raises(EvidenceValidationError, match="component versions"):
        build_performance_summary(manifest, captures, summary_id="mixed_versions_v1")


def test_complete_summary_requires_every_configured_repetition() -> None:
    raw = _manifest_dict()
    timing = raw["timing"]
    assert isinstance(timing, dict)
    timing["repetitions"] = 1
    manifest = parse_performance_manifest(raw)
    captures = [
        parse_performance_capture(_capture_dict(raw, scenario["scenario_id"], 1), manifest)
        for scenario in raw["scenarios"]
    ]

    summary = build_performance_summary(
        manifest,
        reversed(captures),
        summary_id="complete_baseline_v1",
        require_complete=True,
    )

    assert len(summary.scenarios) == len(manifest.scenarios)
    assert all(scenario.repetitions == (1,) for scenario in summary.scenarios)


def test_summary_round_trip_and_human_view_are_stable() -> None:
    manifest, baseline, _, _ = _summaries_for_comparison()
    payload = serialize_performance_summary(baseline)

    decoded = parse_performance_summary(payload, manifest)

    assert decoded == baseline
    assert payload == serialize_performance_summary(decoded)
    human = format_performance_summary(decoded)
    assert "baseline_summary_v1" in human
    assert "presentation_cycle_ms" in human
    assert "/home/" not in human


def test_threshold_artifact_is_frozen_versioned_and_complete() -> None:
    manifest, baseline, _, _ = _summaries_for_comparison()
    thresholds = parse_performance_thresholds(
        _threshold_dict(manifest.manifest_id, baseline.summary_id),
        manifest,
    )

    assert thresholds.schema_version == 1
    assert set(thresholds.thresholds) == set(REQUIRED_THRESHOLD_PATHS)
    with pytest.raises(FrozenInstanceError):
        thresholds.threshold_id = "changed"  # type: ignore[misc]


def test_threshold_artifact_rejects_unknown_versions_missing_metrics_and_autotune() -> None:
    manifest, baseline, _, _ = _summaries_for_comparison()
    unknown = _threshold_dict(manifest.manifest_id, baseline.summary_id)
    unknown["schema_version"] = 2
    with pytest.raises(EvidenceValidationError, match="schema_version"):
        parse_performance_thresholds(unknown, manifest)

    missing = _threshold_dict(manifest.manifest_id, baseline.summary_id)
    thresholds = missing["thresholds"]
    assert isinstance(thresholds, list)
    thresholds.pop()
    with pytest.raises(EvidenceValidationError, match="required threshold"):
        parse_performance_thresholds(missing, manifest)

    autotune = _threshold_dict(manifest.manifest_id, baseline.summary_id)
    autotune["auto_tune"] = True
    with pytest.raises(EvidenceValidationError, match="unexpected field"):
        parse_performance_thresholds(autotune, manifest)

    wrong_repetitions = _threshold_dict(manifest.manifest_id, baseline.summary_id)
    provenance = wrong_repetitions["provenance"]
    assert isinstance(provenance, dict)
    provenance["baseline_repetitions"] = 4
    with pytest.raises(EvidenceValidationError, match="baseline_repetitions"):
        parse_performance_thresholds(wrong_repetitions, manifest)


@pytest.mark.parametrize(
    "observation",
    [
        "dual_visible_presenters",
        "title_bar_intermediate",
        "monitor_relative_intermediate",
        "black_surface",
        "focus_trap",
        "unexpected_identity",
        "premature_commitment",
        "material_hitch",
    ],
)
def test_invariant_or_visible_failure_blocks_candidate(observation: str) -> None:
    raw = _manifest_dict()
    manifest = parse_performance_manifest(raw)
    scenario_id = "scale_100_windowed_to_fullscreen_monitor_a"
    baseline_capture = parse_performance_capture(_capture_dict(raw, scenario_id, 1), manifest)
    candidate_raw = _capture_dict(raw, scenario_id, 1, capture_role="candidate")
    manual_observations = candidate_raw["manual_observations"]
    assert isinstance(manual_observations, dict)
    manual_observations[observation] = True
    candidate_capture = parse_performance_capture(candidate_raw, manifest)
    baseline = build_performance_summary(manifest, [baseline_capture], summary_id="baseline_summary_v1")
    candidate = build_performance_summary(manifest, [candidate_capture], summary_id="candidate_summary_v1")
    thresholds = parse_performance_thresholds(
        _threshold_dict(manifest.manifest_id, baseline.summary_id),
        manifest,
    )

    comparison = compare_performance_summaries(baseline, candidate, thresholds)

    assert comparison.state == "blocked"
    assert comparison.scenarios[0].state == "blocked"
    assert any(observation in reason for reason in comparison.scenarios[0].reasons)


def test_latency_regression_requires_relative_and_absolute_thresholds() -> None:
    _, baseline, candidate, thresholds = _summaries_for_comparison(candidate_offset=0.5)

    below_absolute = compare_performance_summaries(baseline, candidate, thresholds)
    assert below_absolute.state == "pass"

    _, baseline, candidate, thresholds = _summaries_for_comparison(candidate_offset=5.0)
    above_both = compare_performance_summaries(baseline, candidate, thresholds)
    assert above_both.state == "investigate"
    assert any("latency_regression" in reason for reason in above_both.scenarios[0].reasons)


def test_work_and_idle_cpu_regressions_are_reported_separately() -> None:
    raw = _manifest_dict()
    manifest = parse_performance_manifest(raw)
    scenario_id = "scale_100_windowed_to_fullscreen_monitor_a"
    baseline_raw = _capture_dict(raw, scenario_id, 1)
    candidate_raw = _capture_dict(raw, scenario_id, 1, capture_role="candidate")
    work = candidate_raw["work"]
    idle_cpu = candidate_raw["idle_cpu"]
    assert isinstance(work, dict)
    assert isinstance(idle_cpu, dict)
    work["raster_builds"] = 20
    idle_cpu["client_percent_samples"] = [10.0, 10.0]
    baseline = build_performance_summary(
        manifest,
        [parse_performance_capture(baseline_raw, manifest)],
        summary_id="baseline_summary_v1",
    )
    candidate = build_performance_summary(
        manifest,
        [parse_performance_capture(candidate_raw, manifest)],
        summary_id="candidate_summary_v1",
    )
    thresholds = parse_performance_thresholds(
        _threshold_dict(manifest.manifest_id, baseline.summary_id),
        manifest,
    )

    comparison = compare_performance_summaries(baseline, candidate, thresholds)

    reasons = comparison.scenarios[0].reasons
    assert comparison.state == "investigate"
    assert any("work_regression" in reason for reason in reasons)
    assert any("idle_cpu_regression" in reason for reason in reasons)


def test_comparison_is_deterministic_does_not_mutate_thresholds_and_has_concise_view() -> None:
    _, baseline, candidate, thresholds = _summaries_for_comparison(candidate_offset=5.0)
    threshold_before = tuple(thresholds.thresholds.items())

    comparison = compare_performance_summaries(baseline, candidate, thresholds)
    first_payload = serialize_performance_comparison(comparison)
    second_payload = serialize_performance_comparison(compare_performance_summaries(baseline, candidate, thresholds))

    assert first_payload == second_payload
    assert tuple(thresholds.thresholds.items()) == threshold_before
    human = format_performance_comparison(comparison)
    assert "investigate" in human
    assert "latency_regression" in human
    assert "token" not in human.lower()


def test_summary_parser_rejects_prohibited_or_incompatible_artifacts() -> None:
    manifest, baseline, _, _ = _summaries_for_comparison()
    raw = json.loads(serialize_performance_summary(baseline))
    raw["personal_path"] = "/home/alice/baseline.json"
    with pytest.raises(EvidenceValidationError, match="unexpected field|privacy|prohibited"):
        parse_performance_summary(raw, manifest)

    incompatible = json.loads(serialize_performance_summary(baseline))
    incompatible["manifest_id"] = "other_manifest"
    with pytest.raises(EvidenceValidationError, match="manifest_id"):
        parse_performance_summary(incompatible, manifest)


def test_cli_validates_manifest_and_emits_deterministic_summary(tmp_path: Path) -> None:
    raw = _manifest_dict()
    manifest_path = tmp_path / "manifest.json"
    capture_path = tmp_path / "capture.json"
    manifest_path.write_text(json.dumps(raw), encoding="utf-8")
    capture_path.write_text(
        json.dumps(_capture_dict(raw, "scale_100_windowed_to_fullscreen_monitor_a", 1)),
        encoding="utf-8",
    )

    validated = subprocess.run(
        [sys.executable, str(PERFORMANCE_CLI), "validate-manifest", str(manifest_path)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert validated.returncode == 0, validated.stderr
    assert "14 scenarios" in validated.stdout

    summarized = subprocess.run(
        [
            sys.executable,
            str(PERFORMANCE_CLI),
            "summarize",
            str(manifest_path),
            "--summary-id",
            "cli_summary_v1",
            str(capture_path),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert summarized.returncode == 0, summarized.stderr
    payload = json.loads(summarized.stdout)
    assert payload["summary_id"] == "cli_summary_v1"
    assert payload["scenarios"][0]["scenario_id"] == "scale_100_windowed_to_fullscreen_monitor_a"
