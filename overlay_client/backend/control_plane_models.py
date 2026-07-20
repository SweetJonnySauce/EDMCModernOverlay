"""Immutable normalized models for the backend control plane.

These types are additive migration contracts.  Production selection and presentation still
use the transitional backend models until the later control-plane migration step.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Mapping, Sequence


BACKEND_CONTROL_PLANE_SCHEMA_VERSION = 1
MAX_RECENT_FAILURES = 16
MAX_DIAGNOSTIC_EVENTS = 32
MAX_DIAGNOSTIC_STRING_LENGTH = 512
MAX_DIAGNOSTIC_COLLECTION_ITEMS = 32
MAX_DIAGNOSTIC_DEPTH = 4
MAX_CONTROL_PLANE_JSON_BYTES = 64 * 1024
REDACTION_MARKER = "<redacted>"

STABLE_LINUX_BACKEND_INSTANCES = (
    "gnome_shell_wayland",
    "native_x11",
    "xwayland_compat",
)

DETECTED_LINUX_BACKEND_INSTANCES = (
    "kwin_wayland",
    "wlroots_wayland",
    "hyprland_wayland",
    "generic_wayland",
    "cosmic_wayland",
    "gamescope_wayland",
)

CAPABILITY_IDS = (
    "target.discovery",
    "target.geometry",
    "target.display_mode",
    "presentation.windowed",
    "presentation.borderless_fullscreen",
    "input.click_through",
    "input.focus_safe",
    "lifecycle.owner_liveness",
    "lifecycle.external_expiry",
    "helper.compatible",
    "helper.ownership",
    "capture.exclusion",
)


class ProbeState(str, Enum):
    OPERATIONAL = "operational"
    UNAVAILABLE = "unavailable"
    INCOMPATIBLE = "incompatible"
    NOT_IMPLEMENTED = "not_implemented"
    NOT_APPLICABLE = "not_applicable"


class SupportPolicy(str, Enum):
    SUPPORTED = "supported"
    COMPATIBILITY = "compatibility"
    UNVALIDATED_OPERATIONAL = "unvalidated_operational"
    UNIMPLEMENTED = "unimplemented"
    UNSUPPORTED = "unsupported"


class EvidenceLevel(str, Enum):
    FULL_MATRIX = "full_matrix"
    MAINTAINER_SMOKE = "maintainer_smoke"
    COMMUNITY_CONFIRMED = "community_confirmed"
    MIXED_REPORTS = "mixed_reports"
    REPORTED_FAILURE = "reported_failure"
    NOT_YET_REPORTED = "not_yet_reported"
    NOT_APPLICABLE = "not_applicable"


class RuntimeHealth(str, Enum):
    CONSTRUCTING = "constructing"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    INCOMPATIBLE = "incompatible"
    OWNERSHIP_CONFLICT = "ownership_conflict"
    STOPPING = "stopping"
    STOPPED = "stopped"


class OperationOutcome(str, Enum):
    APPLIED = "applied"
    PENDING = "pending"
    HIDDEN = "hidden"
    UNAVAILABLE = "unavailable"
    REJECTED = "rejected"


class RecoveryClass(str, Enum):
    AUTOMATIC = "automatic"
    RETRY_WAIT = "retry_wait"
    RESTART_REQUIRED = "restart_required"
    TERMINAL = "terminal"


_SENSITIVE_KEY_PARTS = (
    "token",
    "secret",
    "owner_id",
    "owner_instance",
    "target_handle",
    "window_handle",
    "title",
    "command",
    "argv",
    "exception",
    "traceback",
    "personal_path",
    "username",
    "user_name",
    "pid",
)
_SENSITIVE_VALUE_PATTERN = re.compile(
    r"(?:^|[\s,;])(?:token|secret|owner[_ -]?id|target[_ -]?handle|command[_ -]?line)\s*[:=]"
    r"|(?:^|[\s=])/(?:home|users)/[^\s]+"
    r"|[A-Za-z]:\\Users\\[^\s]+",
    re.IGNORECASE,
)

_BASE_DIAGNOSTIC_KEYS = frozenset(
    {
        "attempt",
        "available",
        "capabilities",
        "classification",
        "compatible",
        "component",
        "count",
        "elapsed_ms",
        "enabled",
        "fallback_reason",
        "focus_accepting",
        "health",
        "helper_count",
        "helper_kinds",
        "installed",
        "interactive",
        "outcome",
        "presenter_label",
        "protocol_version",
        "reason_code",
        "recovery",
        "redacted",
        "reported_version",
        "required",
        "retry_after_ms",
        "selected_instance",
        "source",
        "state",
        "visible",
        "click_through",
    }
)

PROBE_EVIDENCE_KEYS = _BASE_DIAGNOSTIC_KEYS
OPERATION_DIAGNOSTIC_KEYS = _BASE_DIAGNOSTIC_KEYS
PRESENTATION_DIAGNOSTIC_KEYS = _BASE_DIAGNOSTIC_KEYS
INPUT_DIAGNOSTIC_KEYS = _BASE_DIAGNOSTIC_KEYS
HELPER_DIAGNOSTIC_KEYS = _BASE_DIAGNOSTIC_KEYS
OWNERSHIP_DIAGNOSTIC_KEYS = _BASE_DIAGNOSTIC_KEYS
LIFECYCLE_DIAGNOSTIC_KEYS = _BASE_DIAGNOSTIC_KEYS
FAILURE_DETAIL_KEYS = _BASE_DIAGNOSTIC_KEYS
EVENT_DETAIL_KEYS = _BASE_DIAGNOSTIC_KEYS


JsonValue = object
FrozenJsonMapping = Mapping[str, JsonValue]


def _require_text(value: object, field_name: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    return value


def _require_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{field_name} must be a boolean")
    return value


def _require_non_negative_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _require_enum(value: object, enum_type: type[Enum], field_name: str) -> None:
    if not isinstance(value, enum_type):
        raise TypeError(f"{field_name} must be {enum_type.__name__}")


def _is_sensitive_key(key: str) -> bool:
    normalized = key.strip().lower()
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


def _freeze_json_value(value: object, *, depth: int = 0) -> tuple[JsonValue, bool]:
    if depth > MAX_DIAGNOSTIC_DEPTH:
        return REDACTION_MARKER, True
    if value is None or isinstance(value, bool) or isinstance(value, int):
        return value, False
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("diagnostic floats must be finite")
        return value, False
    if isinstance(value, str):
        if _SENSITIVE_VALUE_PATTERN.search(value):
            return REDACTION_MARKER, True
        if len(value) > MAX_DIAGNOSTIC_STRING_LENGTH:
            return value[:MAX_DIAGNOSTIC_STRING_LENGTH], True
        return value, False
    if isinstance(value, Mapping):
        frozen, redacted = _sanitize_mapping(
            value,
            allowed_keys=_BASE_DIAGNOSTIC_KEYS,
            depth=depth + 1,
        )
        return frozen, redacted
    if isinstance(value, (list, tuple)):
        items: list[JsonValue] = []
        redacted = len(value) > MAX_DIAGNOSTIC_COLLECTION_ITEMS
        for item in value[:MAX_DIAGNOSTIC_COLLECTION_ITEMS]:
            frozen_item, item_redacted = _freeze_json_value(item, depth=depth + 1)
            items.append(frozen_item)
            redacted = redacted or item_redacted
        return tuple(items), redacted
    raise TypeError(f"diagnostic value is not JSON-compatible: {type(value).__name__}")


def _sanitize_mapping(
    value: Mapping[str, object],
    *,
    allowed_keys: frozenset[str],
    depth: int = 0,
) -> tuple[FrozenJsonMapping, bool]:
    if not isinstance(value, Mapping):
        raise TypeError("diagnostics must be a mapping")
    sanitized: dict[str, JsonValue] = {}
    redacted = False
    for raw_key, raw_value in value.items():
        if not isinstance(raw_key, str):
            raise TypeError("diagnostic keys must be strings")
        key = raw_key.strip()
        if _is_sensitive_key(key):
            redacted = True
            continue
        if key not in allowed_keys:
            continue
        sanitized_value, value_redacted = _freeze_json_value(raw_value, depth=depth)
        sanitized[key] = sanitized_value
        redacted = redacted or value_redacted
    if redacted:
        sanitized["redacted"] = REDACTION_MARKER
    return MappingProxyType(sanitized), redacted


def _freeze_diagnostics(value: Mapping[str, object], *, allowed_keys: frozenset[str]) -> FrozenJsonMapping:
    return _sanitize_mapping(value, allowed_keys=allowed_keys)[0]


@dataclass(frozen=True, slots=True)
class BackendIdentity:
    family: str
    instance: str

    def __post_init__(self) -> None:
        _require_text(self.family, "family")
        _require_text(self.instance, "instance")


@dataclass(frozen=True, slots=True)
class EnvironmentKey:
    operating_system: str
    distribution: str
    distribution_version: str
    session_type: str
    desktop: str
    compositor_or_wm: str
    compositor_or_wm_version: str
    display_mode: str

    def __post_init__(self) -> None:
        for field_name in (
            "operating_system",
            "distribution",
            "distribution_version",
            "session_type",
            "desktop",
            "compositor_or_wm",
            "compositor_or_wm_version",
            "display_mode",
        ):
            value = _require_text(getattr(self, field_name), field_name, allow_empty=True)
            if "|" in value:
                raise ValueError(f"{field_name} must not contain the stable-key delimiter")

    @property
    def stable_key(self) -> str:
        return "|".join(
            (
                self.operating_system,
                self.distribution,
                self.distribution_version,
                self.session_type,
                self.desktop,
                self.compositor_or_wm,
                self.compositor_or_wm_version,
                self.display_mode,
            )
        )


@dataclass(frozen=True, slots=True)
class CapabilityProbe:
    capability_id: str
    state: ProbeState
    source: str
    reason_code: str | None
    sanitized_evidence: FrozenJsonMapping = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.capability_id not in CAPABILITY_IDS:
            raise ValueError(f"unknown normalized capability_id: {self.capability_id}")
        _require_enum(self.state, ProbeState, "state")
        _require_text(self.source, "source")
        if self.reason_code is not None:
            _require_text(self.reason_code, "reason_code")
        object.__setattr__(
            self,
            "sanitized_evidence",
            _freeze_diagnostics(self.sanitized_evidence, allowed_keys=PROBE_EVIDENCE_KEYS),
        )


@dataclass(frozen=True, slots=True)
class ProducerInfo:
    component: str
    version: str

    def __post_init__(self) -> None:
        _require_text(self.component, "component")
        _require_text(self.version, "version", allow_empty=True)


@dataclass(frozen=True, slots=True)
class SelectionSummary:
    mode: str
    restart_required: bool
    inputs_revision: int

    def __post_init__(self) -> None:
        _require_text(self.mode, "mode")
        _require_bool(self.restart_required, "restart_required")
        _require_non_negative_int(self.inputs_revision, "inputs_revision")


@dataclass(frozen=True, slots=True)
class SupportSummary:
    policy: SupportPolicy
    environment_key: str
    evidence_level: EvidenceLevel
    evidence_record: str
    last_reviewed_release: str

    def __post_init__(self) -> None:
        _require_enum(self.policy, SupportPolicy, "policy")
        _require_text(self.environment_key, "environment_key")
        _require_enum(self.evidence_level, EvidenceLevel, "evidence_level")
        _require_text(self.evidence_record, "evidence_record", allow_empty=True)
        _require_text(self.last_reviewed_release, "last_reviewed_release", allow_empty=True)


@dataclass(frozen=True, slots=True)
class HealthSummary:
    state: RuntimeHealth
    reason_code: str
    recovery: RecoveryClass

    def __post_init__(self) -> None:
        _require_enum(self.state, RuntimeHealth, "state")
        _require_text(self.reason_code, "reason_code")
        _require_enum(self.recovery, RecoveryClass, "recovery")


@dataclass(frozen=True, slots=True)
class OperationResult:
    outcome: OperationOutcome
    reason_code: str
    health: RuntimeHealth
    recovery: RecoveryClass
    state_revision: int
    diagnostics: FrozenJsonMapping = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_enum(self.outcome, OperationOutcome, "outcome")
        _require_text(self.reason_code, "reason_code")
        _require_enum(self.health, RuntimeHealth, "health")
        _require_enum(self.recovery, RecoveryClass, "recovery")
        _require_non_negative_int(self.state_revision, "state_revision")
        object.__setattr__(
            self,
            "diagnostics",
            _freeze_diagnostics(self.diagnostics, allowed_keys=OPERATION_DIAGNOSTIC_KEYS),
        )


@dataclass(frozen=True, slots=True)
class PresentationSummary:
    outcome: OperationOutcome
    reason_code: str
    state_revision: int
    requested_mode: str
    visible: bool
    presenter_label: str
    diagnostics: FrozenJsonMapping = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_enum(self.outcome, OperationOutcome, "outcome")
        _require_text(self.reason_code, "reason_code")
        _require_non_negative_int(self.state_revision, "state_revision")
        _require_text(self.requested_mode, "requested_mode", allow_empty=True)
        _require_bool(self.visible, "visible")
        _require_text(self.presenter_label, "presenter_label", allow_empty=True)
        object.__setattr__(
            self,
            "diagnostics",
            _freeze_diagnostics(self.diagnostics, allowed_keys=PRESENTATION_DIAGNOSTIC_KEYS),
        )


@dataclass(frozen=True, slots=True)
class InputSummary:
    outcome: OperationOutcome
    reason_code: str
    state_revision: int
    interactive: bool
    click_through: bool
    focus_accepting: bool
    diagnostics: FrozenJsonMapping = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_enum(self.outcome, OperationOutcome, "outcome")
        _require_text(self.reason_code, "reason_code")
        _require_non_negative_int(self.state_revision, "state_revision")
        _require_bool(self.interactive, "interactive")
        _require_bool(self.click_through, "click_through")
        _require_bool(self.focus_accepting, "focus_accepting")
        object.__setattr__(
            self,
            "diagnostics",
            _freeze_diagnostics(self.diagnostics, allowed_keys=INPUT_DIAGNOSTIC_KEYS),
        )


@dataclass(frozen=True, slots=True)
class HelperSummary:
    required: bool
    available: bool
    compatible: bool
    owned: bool | None
    health: RuntimeHealth
    recovery: RecoveryClass
    reason_code: str
    diagnostics: FrozenJsonMapping = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_bool(self.required, "required")
        _require_bool(self.available, "available")
        _require_bool(self.compatible, "compatible")
        if self.owned is not None:
            _require_bool(self.owned, "owned")
        _require_enum(self.health, RuntimeHealth, "health")
        _require_enum(self.recovery, RecoveryClass, "recovery")
        _require_text(self.reason_code, "reason_code")
        object.__setattr__(
            self,
            "diagnostics",
            _freeze_diagnostics(self.diagnostics, allowed_keys=HELPER_DIAGNOSTIC_KEYS),
        )


@dataclass(frozen=True, slots=True)
class OwnershipSummary:
    connected: bool
    state: str
    reason_code: str
    age_ms: int
    diagnostics: FrozenJsonMapping = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_bool(self.connected, "connected")
        _require_text(self.state, "state")
        _require_text(self.reason_code, "reason_code")
        _require_non_negative_int(self.age_ms, "age_ms")
        object.__setattr__(
            self,
            "diagnostics",
            _freeze_diagnostics(self.diagnostics, allowed_keys=OWNERSHIP_DIAGNOSTIC_KEYS),
        )


@dataclass(frozen=True, slots=True)
class NormalizedFailure:
    failure_code: str
    component: str
    health: RuntimeHealth
    recovery: RecoveryClass
    state_revision: int
    age_ms: int
    details: FrozenJsonMapping = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_text(self.failure_code, "failure_code")
        _require_text(self.component, "component")
        _require_enum(self.health, RuntimeHealth, "health")
        _require_enum(self.recovery, RecoveryClass, "recovery")
        _require_non_negative_int(self.state_revision, "state_revision")
        _require_non_negative_int(self.age_ms, "age_ms")
        object.__setattr__(self, "details", _freeze_diagnostics(self.details, allowed_keys=FAILURE_DETAIL_KEYS))


@dataclass(frozen=True, slots=True)
class DiagnosticEvent:
    event_code: str
    component: str
    state_revision: int
    safe_correlation_id: str | None
    age_ms: int
    details: FrozenJsonMapping = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_text(self.event_code, "event_code")
        _require_text(self.component, "component")
        _require_non_negative_int(self.state_revision, "state_revision")
        if self.safe_correlation_id is not None:
            _require_text(self.safe_correlation_id, "safe_correlation_id")
        _require_non_negative_int(self.age_ms, "age_ms")
        object.__setattr__(self, "details", _freeze_diagnostics(self.details, allowed_keys=EVENT_DETAIL_KEYS))


@dataclass(frozen=True, slots=True)
class LifecycleSummary:
    state: str
    state_revision: int
    age_ms: int
    restart_required: bool
    recent_events: tuple[DiagnosticEvent, ...] = ()
    diagnostics: FrozenJsonMapping = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_text(self.state, "state")
        _require_non_negative_int(self.state_revision, "state_revision")
        _require_non_negative_int(self.age_ms, "age_ms")
        _require_bool(self.restart_required, "restart_required")
        events = tuple(self.recent_events)
        if any(not isinstance(event, DiagnosticEvent) for event in events):
            raise TypeError("recent_events must contain DiagnosticEvent records")
        object.__setattr__(self, "recent_events", events[-MAX_DIAGNOSTIC_EVENTS:])
        object.__setattr__(
            self,
            "diagnostics",
            _freeze_diagnostics(self.diagnostics, allowed_keys=LIFECYCLE_DIAGNOSTIC_KEYS),
        )


@dataclass(frozen=True, slots=True)
class BackendControlPlaneEnvelope:
    schema_version: int
    producer: ProducerInfo
    revision: int
    selected_runtime: BackendIdentity
    selection: SelectionSummary
    support: SupportSummary
    health: HealthSummary
    probes: tuple[CapabilityProbe, ...]
    presentation: PresentationSummary
    input: InputSummary
    helper: HelperSummary | None
    ownership: OwnershipSummary
    lifecycle: LifecycleSummary
    recent_failures: tuple[NormalizedFailure, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.schema_version, bool) or self.schema_version != BACKEND_CONTROL_PLANE_SCHEMA_VERSION:
            raise ValueError(
                f"schema_version must be {BACKEND_CONTROL_PLANE_SCHEMA_VERSION}, got {self.schema_version!r}"
            )
        _require_non_negative_int(self.revision, "revision")
        for field_name, expected_type in (
            ("producer", ProducerInfo),
            ("selected_runtime", BackendIdentity),
            ("selection", SelectionSummary),
            ("support", SupportSummary),
            ("health", HealthSummary),
            ("presentation", PresentationSummary),
            ("input", InputSummary),
            ("ownership", OwnershipSummary),
            ("lifecycle", LifecycleSummary),
        ):
            if not isinstance(getattr(self, field_name), expected_type):
                raise TypeError(f"{field_name} must be {expected_type.__name__}")
        if self.helper is not None and not isinstance(self.helper, HelperSummary):
            raise TypeError("helper must be HelperSummary or None")
        probes = tuple(self.probes)
        if any(not isinstance(probe, CapabilityProbe) for probe in probes):
            raise TypeError("probes must contain CapabilityProbe records")
        failures = tuple(self.recent_failures)
        if any(not isinstance(failure, NormalizedFailure) for failure in failures):
            raise TypeError("recent_failures must contain NormalizedFailure records")
        capability_ids = tuple(probe.capability_id for probe in probes)
        if len(capability_ids) != len(set(capability_ids)):
            raise ValueError("probes must not contain a duplicate capability_id")
        if len(probes) > len(CAPABILITY_IDS):
            raise ValueError("probes exceed the normalized capability vocabulary")
        object.__setattr__(self, "probes", probes)
        object.__setattr__(self, "recent_failures", failures[-MAX_RECENT_FAILURES:])


def mutable_json_value(value: JsonValue) -> object:
    """Return a standard-JSON-compatible copy of an immutable diagnostic value."""

    if isinstance(value, Mapping):
        return {key: mutable_json_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [mutable_json_value(item) for item in value]
    return value


def bounded_failures(values: Sequence[NormalizedFailure]) -> tuple[NormalizedFailure, ...]:
    """Return the deterministic newest failure window used by schema version 1."""

    return tuple(values)[-MAX_RECENT_FAILURES:]
