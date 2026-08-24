"""Pure privacy-safe contracts for the controlled helper pressure A/B."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from json import JSONDecodeError, loads
from pathlib import Path
from types import MappingProxyType
from typing import Iterable, Mapping, Sequence

from overlay_client.work_counters import WORK_COUNTER_MAX


PRESSURE_AB_CELLS = ("A1", "A2", "B1", "B2")
PRESSURE_AB_SAFETY_FIELDS = (
    "flashing",
    "input_loss",
    "drag_corruption",
    "repeated_mutter_assertions",
    "rapidly_rising_shell_cpu",
)
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
_FIXTURE_HASH = re.compile(r"^[a-f0-9]{64}$")
_SOURCE_REVISION = re.compile(r"^[a-f0-9]{40}$")
_COMPONENT_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,63}$")
_MAX_EVIDENCE_NUMBER = 1_000_000_000.0
_HELPER_COUNTER_KEYS = ("target_queries", "presentation_calls")
_ACTOR_COUNT_KEYS = (
    "shell_actor_proof_visible",
    "shell_raster_frame_visible",
    "shell_raster_region_count",
)
_CONTINUITY_FIELDS = (
    "client_restarted",
    "helper_restarted",
    "client_counter_decreased",
    "helper_counter_decreased",
    "client_counter_saturated",
    "helper_counter_saturated",
)
_PROHIBITED_PRIVACY_KEYS = frozenset(
    {
        "pid",
        "shell_pid",
        "client_pid",
        "path",
        "fixture_path",
        "port_file",
        "title",
        "window_title",
        "handle",
        "window_handle",
        "command",
        "command_line",
        "cmdline",
        "journal",
        "journal_text",
        "raw_journal",
        "raw_helper_payload",
        "helper_payload",
        "payload",
        "token",
        "access_token",
        "secret",
        "hostname",
        "host_name",
        "username",
        "user_name",
        "home",
        "cwd",
    }
)
_EXPECTED_CELL_STATE: Mapping[str, Mapping[str, object]] = MappingProxyType(
    {
        "A1": MappingProxyType(
            {
                "client": "stopped",
                "helper": "disabled",
                "client_backend": "unavailable",
                "client_pid_argument": "unavailable",
                "port_file_argument": "unavailable",
                "capture_diagnostics_enabled": False,
                "helper_diagnostics_enabled": False,
            }
        ),
        "A2": MappingProxyType(
            {
                "client": "running",
                "helper": "disabled",
                "client_backend": "documented_unavailable",
                "client_pid_argument": "provided",
                "port_file_argument": "provided",
                "capture_diagnostics_enabled": False,
                "helper_diagnostics_enabled": False,
            }
        ),
        "B1": MappingProxyType(
            {
                "client": "stopped",
                "helper": "full_helper",
                "client_backend": "unavailable",
                "client_pid_argument": "unavailable",
                "port_file_argument": "unavailable",
                "capture_diagnostics_enabled": False,
                "helper_diagnostics_enabled": False,
            }
        ),
        "B2": MappingProxyType(
            {
                "client": "running",
                "helper": "full_helper",
                "client_backend": "helper_selected",
                "client_pid_argument": "provided",
                "port_file_argument": "provided",
                "capture_diagnostics_enabled": False,
                "helper_diagnostics_enabled": False,
            }
        ),
    }
)


class PressureAbValidationError(ValueError):
    """Raised when pressure A/B evidence is incomplete, unsafe, or inconsistent."""


@dataclass(frozen=True)
class PressureAbDistribution:
    """One bounded distribution over the fixed 60-second observation window."""

    count: int
    median: float
    p95: float
    minimum: float
    maximum: float


@dataclass(frozen=True)
class PressureAbResourceEvidence:
    """Available bounded resource distributions or an explicit unavailable state."""

    available: bool
    reason: str | None = None
    distributions: Mapping[str, PressureAbDistribution] | None = None


@dataclass(frozen=True)
class PressureAbWorkEvidence:
    """Bounded work deltas tied to one privacy-safe runtime origin."""

    available: bool
    origin_id: str
    counters: Mapping[str, int]
    reason: str | None = None


@dataclass(frozen=True)
class PressureAbActorEvidence:
    """Bounded helper actor state or an explicit unavailable state."""

    available: bool
    values: Mapping[str, int]
    reason: str | None = None


@dataclass(frozen=True)
class PressureAbProvenance:
    """Fixed privacy-safe inputs shared by every cell in one run."""

    fixture_sha256: str
    source_revision: str
    component_versions: Mapping[str, str]
    display: Mapping[str, int | float | str]
    workload: str
    quiet_host: bool


@dataclass(frozen=True)
class PressureAbSample:
    """One complete post-warm-up sample parsed from runner JSON."""

    cell: str
    repetition: int
    resources: Mapping[str, PressureAbResourceEvidence]
    client_work: PressureAbWorkEvidence
    helper_work: PressureAbWorkEvidence
    actor_counts: PressureAbActorEvidence
    warning_counts: Mapping[str, int | bool]
    safety: Mapping[str, bool]
    continuity: Mapping[str, bool]


@dataclass(frozen=True)
class PressureAbCellDocument:
    """One immutable runner cell document containing three accepted samples."""

    cell: str
    execution_order: int
    provenance: PressureAbProvenance
    state: Mapping[str, object]
    samples: tuple[PressureAbSample, ...]


@dataclass(frozen=True)
class PressureAbRun:
    """One complete four-cell run in actual execution order."""

    cells: tuple[PressureAbCellDocument, ...]




def _privacy_scan(value: object, *, location: str = "evidence") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise PressureAbValidationError(f"privacy-invalid non-string key at {location}")
            if key.casefold() in _PROHIBITED_PRIVACY_KEYS:
                raise PressureAbValidationError(f"privacy-invalid field {key!r} at {location}")
            _privacy_scan(nested, location=f"{location}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            _privacy_scan(nested, location=f"{location}[{index}]")
        return
    if isinstance(value, str) and ("/" in value or "\\" in value or "\x00" in value):
        raise PressureAbValidationError(f"privacy-invalid path-like string at {location}")


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or not all(isinstance(key, str) for key in value):
        raise PressureAbValidationError(f"{label} must be an object")
    return value


def _exact_fields(value: Mapping[str, object], expected: set[str], *, label: str) -> None:
    actual = set(value)
    if actual != expected:
        raise PressureAbValidationError(f"invalid {label} schema")


def _bounded_int(value: object, *, label: str, maximum: int, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise PressureAbValidationError(f"{label} must be an integer from {minimum} through {maximum}")
    return value


def _bounded_number(value: object, *, label: str, maximum: float = _MAX_EVIDENCE_NUMBER) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PressureAbValidationError(f"{label} must be numeric")
    numeric = float(value)
    if not math.isfinite(numeric) or not 0.0 <= numeric <= maximum:
        raise PressureAbValidationError(f"{label} must be finite, non-negative, and bounded")
    return numeric


def _parse_distribution(value: object, *, label: str) -> PressureAbDistribution:
    raw = _mapping(value, label=label)
    _exact_fields(raw, {"count", "median", "p95", "minimum", "maximum"}, label=label)
    count = _bounded_int(raw["count"], label=f"{label}.count", minimum=60, maximum=60)
    median = _bounded_number(raw["median"], label=f"{label}.median")
    p95 = _bounded_number(raw["p95"], label=f"{label}.p95")
    minimum = _bounded_number(raw["minimum"], label=f"{label}.minimum")
    maximum = _bounded_number(raw["maximum"], label=f"{label}.maximum")
    if not minimum <= median <= p95 <= maximum:
        raise PressureAbValidationError(f"{label} distribution ordering is invalid")
    return PressureAbDistribution(count, median, p95, minimum, maximum)


def _parse_process_resource(
    value: object,
    *,
    label: str,
    expected_available: bool,
) -> PressureAbResourceEvidence:
    raw = _mapping(value, label=label)
    if expected_available:
        _exact_fields(
            raw,
            {"available", "cpu_percent", "rss_kib", "context_switches"},
            label=label,
        )
        if raw["available"] is not True:
            raise PressureAbValidationError(f"{label} must be available")
        distributions = MappingProxyType(
            {
                "cpu_percent": _parse_distribution(raw["cpu_percent"], label=f"{label}.cpu_percent"),
                "rss_kib": _parse_distribution(raw["rss_kib"], label=f"{label}.rss_kib"),
                "context_switches": _parse_distribution(
                    raw["context_switches"], label=f"{label}.context_switches"
                ),
            }
        )
        return PressureAbResourceEvidence(available=True, distributions=distributions)
    _exact_fields(raw, {"available", "reason"}, label=label)
    if raw != {"available": False, "reason": "client_stopped"}:
        raise PressureAbValidationError(f"{label} requires explicit client_stopped unavailability")
    return PressureAbResourceEvidence(available=False, reason="client_stopped")


def _parse_gpu_resource(value: object) -> PressureAbResourceEvidence:
    raw = _mapping(value, label="resources.gpu")
    if raw.get("available") is True:
        _exact_fields(raw, {"available", "utilization_percent", "vram_mib"}, label="resources.gpu")
        distributions = MappingProxyType(
            {
                "utilization_percent": _parse_distribution(
                    raw["utilization_percent"], label="resources.gpu.utilization_percent"
                ),
                "vram_mib": _parse_distribution(raw["vram_mib"], label="resources.gpu.vram_mib"),
            }
        )
        return PressureAbResourceEvidence(available=True, distributions=distributions)
    _exact_fields(raw, {"available", "reason"}, label="resources.gpu")
    if raw != {"available": False, "reason": "provider_unavailable"}:
        raise PressureAbValidationError("GPU evidence requires explicit provider_unavailable state")
    return PressureAbResourceEvidence(available=False, reason="provider_unavailable")


def _parse_work_evidence(
    value: object,
    *,
    label: str,
    expected_available: bool,
    counter_keys: Sequence[str],
    unavailable_reason: str,
) -> PressureAbWorkEvidence:
    raw = _mapping(value, label=label)
    counters = _mapping(raw.get("counters"), label=f"{label}.counters")
    if expected_available:
        _exact_fields(raw, {"available", "origin_id", "counters"}, label=label)
        if raw["available"] is not True:
            raise PressureAbValidationError(f"{label} must be available")
        origin_id = raw["origin_id"]
        if not isinstance(origin_id, str) or _ORIGIN_ID.fullmatch(origin_id) is None:
            raise PressureAbValidationError(f"{label} origin_id must be privacy-safe")
        _exact_fields(counters, set(counter_keys), label=f"{label}.counters")
        normalized = {
            key: _bounded_int(
                counters[key],
                label=f"{label}.{key}",
                maximum=WORK_COUNTER_MAX - 1,
            )
            for key in counter_keys
        }
        return PressureAbWorkEvidence(True, origin_id, MappingProxyType(normalized))
    _exact_fields(raw, {"available", "reason", "origin_id", "counters"}, label=label)
    if raw.get("available") is not False or raw.get("reason") != unavailable_reason:
        raise PressureAbValidationError(f"{label} requires explicit {unavailable_reason} unavailability")
    if raw.get("origin_id") != "unavailable" or counters:
        raise PressureAbValidationError(f"{label} unavailable origin/counters must be explicit")
    return PressureAbWorkEvidence(False, "unavailable", MappingProxyType({}), unavailable_reason)


def _parse_actor_evidence(value: object, *, helper_available: bool) -> PressureAbActorEvidence:
    raw = _mapping(value, label="actor_counts")
    values = _mapping(raw.get("values"), label="actor_counts.values")
    if helper_available:
        _exact_fields(raw, {"available", "values"}, label="actor_counts")
        if raw["available"] is not True:
            raise PressureAbValidationError("actor_counts must be available with the helper")
        _exact_fields(values, set(_ACTOR_COUNT_KEYS), label="actor_counts.values")
        normalized = {
            key: _bounded_int(values[key], label=f"actor_counts.{key}", maximum=1024)
            for key in _ACTOR_COUNT_KEYS
        }
        return PressureAbActorEvidence(True, MappingProxyType(normalized))
    _exact_fields(raw, {"available", "reason", "values"}, label="actor_counts")
    if raw.get("available") is not False or raw.get("reason") != "helper_disabled" or values:
        raise PressureAbValidationError("actor_counts require explicit helper_disabled unavailability")
    return PressureAbActorEvidence(False, MappingProxyType({}), "helper_disabled")


def _parse_provenance(value: object) -> PressureAbProvenance:
    raw = _mapping(value, label="provenance")
    _exact_fields(
        raw,
        {
            "fixture_sha256",
            "source_revision",
            "component_versions",
            "display",
            "workload",
            "quiet_host",
        },
        label="provenance",
    )
    fixture = raw["fixture_sha256"]
    revision = raw["source_revision"]
    if not isinstance(fixture, str) or _FIXTURE_HASH.fullmatch(fixture) is None:
        raise PressureAbValidationError("provenance fixture_sha256 is invalid")
    if not isinstance(revision, str) or _SOURCE_REVISION.fullmatch(revision) is None:
        raise PressureAbValidationError("provenance source_revision is invalid")
    versions = _mapping(raw["component_versions"], label="provenance.component_versions")
    _exact_fields(versions, {"plugin", "client", "helper"}, label="provenance.component_versions")
    normalized_versions: dict[str, str] = {}
    for component in ("plugin", "client", "helper"):
        version = versions[component]
        if not isinstance(version, str) or _COMPONENT_VERSION.fullmatch(version) is None:
            raise PressureAbValidationError(f"provenance {component} version is invalid")
        normalized_versions[component] = version
    display = _mapping(raw["display"], label="provenance.display")
    _exact_fields(
        display,
        {"monitor", "width_px", "height_px", "scale_percent", "refresh_hz"},
        label="provenance.display",
    )
    if display["monitor"] != "A" or display["scale_percent"] != 100:
        raise PressureAbValidationError("provenance requires monitor A at 100 percent scale")
    normalized_display: dict[str, int | float | str] = {
        "monitor": "A",
        "width_px": _bounded_int(display["width_px"], label="display.width_px", minimum=1, maximum=16384),
        "height_px": _bounded_int(
            display["height_px"], label="display.height_px", minimum=1, maximum=16384
        ),
        "scale_percent": 100,
        "refresh_hz": _bounded_number(display["refresh_hz"], label="display.refresh_hz", maximum=1000.0),
    }
    if raw["workload"] != "stable_windowed_fixed_fixture" or raw["quiet_host"] is not True:
        raise PressureAbValidationError("provenance requires the fixed workload and quiet host decision")
    return PressureAbProvenance(
        fixture,
        revision,
        MappingProxyType(normalized_versions),
        MappingProxyType(normalized_display),
        "stable_windowed_fixed_fixture",
        True,
    )


def validate_client_argument_pair(
    cell: str,
    *,
    client_pid_present: bool,
    port_file_present: bool,
) -> None:
    """Require both privacy-sensitive client arguments only for running-client cells."""

    if cell not in PRESSURE_AB_CELLS:
        raise PressureAbValidationError("client argument cell is invalid")
    expected = cell in {"A2", "B2"}
    if client_pid_present is not expected or port_file_present is not expected:
        raise PressureAbValidationError("client argument pair does not match the exact cell state")


def parse_pressure_ab_sample(
    raw_value: Mapping[str, object],
    *,
    expected_cell: str,
) -> PressureAbSample:
    """Parse one exact runner-shaped sample and reject unsafe evidence."""

    _privacy_scan(raw_value)
    raw = _mapping(raw_value, label="pressure sample")
    _exact_fields(
        raw,
        {
            "schema_version",
            "cell",
            "repetition",
            "warm_up_seconds",
            "duration_seconds",
            "diagnostics_enabled",
            "resources",
            "client_work",
            "helper_work",
            "actor_counts",
            "warning_counts",
            "safety",
            "continuity",
        },
        label="pressure sample",
    )
    if raw["schema_version"] != 1 or raw["cell"] != expected_cell or expected_cell not in PRESSURE_AB_CELLS:
        raise PressureAbValidationError("pressure sample cell/schema does not match")
    repetition = _bounded_int(raw["repetition"], label="repetition", minimum=1, maximum=3)
    if raw["warm_up_seconds"] != 300 or raw["duration_seconds"] != 60:
        raise PressureAbValidationError("pressure sample requires fixed 300/60 timing")
    if raw["diagnostics_enabled"] is not False:
        raise PressureAbValidationError("pressure sample requires diagnostics off")
    client_available = expected_cell in {"A2", "B2"}
    helper_available = expected_cell in {"B1", "B2"}
    resources_raw = _mapping(raw["resources"], label="resources")
    _exact_fields(resources_raw, {"shell", "client", "gpu"}, label="resources")
    resources = MappingProxyType(
        {
            "shell": _parse_process_resource(
                resources_raw["shell"], label="resources.shell", expected_available=True
            ),
            "client": _parse_process_resource(
                resources_raw["client"], label="resources.client", expected_available=client_available
            ),
            "gpu": _parse_gpu_resource(resources_raw["gpu"]),
        }
    )
    client_work = _parse_work_evidence(
        raw["client_work"],
        label="client_work",
        expected_available=client_available,
        counter_keys=WORK_COUNTER_KEYS,
        unavailable_reason="client_stopped",
    )
    helper_work = _parse_work_evidence(
        raw["helper_work"],
        label="helper_work",
        expected_available=helper_available,
        counter_keys=_HELPER_COUNTER_KEYS,
        unavailable_reason="helper_disabled",
    )
    actor_counts = _parse_actor_evidence(raw["actor_counts"], helper_available=helper_available)
    warnings = _mapping(raw["warning_counts"], label="warning_counts")
    _exact_fields(warnings, {"available", "mutter_assertions", "shell_warnings"}, label="warning_counts")
    if not isinstance(warnings["available"], bool):
        raise PressureAbValidationError("warning_counts.available must be boolean")
    normalized_warnings: dict[str, int | bool] = {
        "available": warnings["available"],
        "mutter_assertions": _bounded_int(
            warnings["mutter_assertions"], label="warning_counts.mutter_assertions", maximum=WORK_COUNTER_MAX - 1
        ),
        "shell_warnings": _bounded_int(
            warnings["shell_warnings"], label="warning_counts.shell_warnings", maximum=WORK_COUNTER_MAX - 1
        ),
    }
    safety = _mapping(raw["safety"], label="safety")
    _exact_fields(safety, set(PRESSURE_AB_SAFETY_FIELDS), label="safety")
    if any(safety[field] is not False for field in PRESSURE_AB_SAFETY_FIELDS):
        raise PressureAbValidationError("pressure sample contains a safety failure")
    continuity = _mapping(raw["continuity"], label="continuity")
    _exact_fields(continuity, set(_CONTINUITY_FIELDS), label="continuity")
    if any(continuity[field] is not False for field in _CONTINUITY_FIELDS):
        raise PressureAbValidationError("pressure sample continuity is unsafe")
    return PressureAbSample(
        expected_cell,
        repetition,
        resources,
        client_work,
        helper_work,
        actor_counts,
        MappingProxyType(normalized_warnings),
        MappingProxyType({field: False for field in PRESSURE_AB_SAFETY_FIELDS}),
        MappingProxyType({field: False for field in _CONTINUITY_FIELDS}),
    )


def parse_pressure_ab_cell_document(raw_value: Mapping[str, object]) -> PressureAbCellDocument:
    """Parse one complete immutable cell document emitted directly by the runner."""

    _privacy_scan(raw_value)
    raw = _mapping(raw_value, label="pressure cell document")
    _exact_fields(
        raw,
        {"schema_version", "cell", "execution_order", "provenance", "state", "samples"},
        label="pressure cell document",
    )
    cell = raw["cell"]
    if raw["schema_version"] != 1 or cell not in PRESSURE_AB_CELLS or not isinstance(cell, str):
        raise PressureAbValidationError("pressure cell/schema is invalid")
    execution_order = _bounded_int(raw["execution_order"], label="execution_order", minimum=1, maximum=4)
    state = _mapping(raw["state"], label="cell state")
    expected_state = _EXPECTED_CELL_STATE[cell]
    _exact_fields(state, set(expected_state), label="cell state")
    if any(state[key] != expected_state[key] for key in expected_state):
        raise PressureAbValidationError("cell state or client argument declaration does not match exact contract")
    provenance = _parse_provenance(raw["provenance"])
    samples_raw = raw["samples"]
    if not isinstance(samples_raw, list) or len(samples_raw) != 3:
        raise PressureAbValidationError("cell requires exactly three samples")
    samples = tuple(
        parse_pressure_ab_sample(_mapping(sample, label="pressure sample"), expected_cell=cell)
        for sample in samples_raw
    )
    if tuple(sample.repetition for sample in samples) != (1, 2, 3):
        raise PressureAbValidationError("cell requires repetitions 1, 2, and 3 in order")
    for label in ("client_work", "helper_work"):
        origins = {
            getattr(sample, label).origin_id
            for sample in samples
            if getattr(sample, label).available
        }
        if len(origins) > 1:
            raise PressureAbValidationError(f"{label} origin continuity changed across the cell")
    return PressureAbCellDocument(
        cell,
        execution_order,
        provenance,
        MappingProxyType({key: expected_state[key] for key in expected_state}),
        samples,
    )


def parse_complete_pressure_ab_run(
    documents: Iterable[Mapping[str, object]],
) -> PressureAbRun:
    """Require all four strict cell documents with fixed provenance and actual order."""

    raw_documents = tuple(documents)
    if len(raw_documents) != 4:
        raise PressureAbValidationError("complete pressure run requires four cell documents")
    cells = tuple(parse_pressure_ab_cell_document(document) for document in raw_documents)
    if {cell.cell for cell in cells} != set(PRESSURE_AB_CELLS):
        raise PressureAbValidationError("complete pressure run requires exact A1/A2/B1/B2 cells")
    if {cell.execution_order for cell in cells} != {1, 2, 3, 4}:
        raise PressureAbValidationError("complete pressure run requires unique actual execution order 1-4")
    provenance = cells[0].provenance
    if any(cell.provenance != provenance for cell in cells[1:]):
        raise PressureAbValidationError("complete pressure run requires identical fixed provenance")
    return PressureAbRun(tuple(sorted(cells, key=lambda cell: cell.execution_order)))


def load_complete_pressure_ab_run(paths: Sequence[str | Path]) -> PressureAbRun:
    """Load four distinct stable JSON files into one strict immutable run model."""

    if len(paths) != 4:
        raise PressureAbValidationError("complete pressure run requires four distinct cell files")
    resolved = tuple(Path(path).resolve() for path in paths)
    if len(set(resolved)) != 4:
        raise PressureAbValidationError("complete pressure run requires four distinct cell files")
    documents: list[Mapping[str, object]] = []
    for path in resolved:
        try:
            before = path.stat()
            decoded = loads(path.read_text(encoding="utf-8"))
            after = path.stat()
        except (OSError, JSONDecodeError) as exc:
            raise PressureAbValidationError("pressure cell file is unavailable or malformed") from exc
        if (before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise PressureAbValidationError("pressure cell file changed while loading")
        documents.append(_mapping(decoded, label="pressure cell document"))
    return parse_complete_pressure_ab_run(documents)




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
        if int(before_counts[key]) == WORK_COUNTER_MAX or int(after_counts[key]) == WORK_COUNTER_MAX:
            raise PressureAbValidationError(f"pressure snapshot counter {key} saturated during sample")
        difference = int(after_counts[key]) - int(before_counts[key])
        if difference < 0:
            raise PressureAbValidationError(f"pressure snapshot counter {key} decreased during sample")
        delta[key] = difference
    return delta
