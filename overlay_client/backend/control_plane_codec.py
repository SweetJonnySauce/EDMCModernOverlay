"""Deterministic schema-version-1 codec for backend control-plane snapshots."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Mapping

from .control_plane_models import (
    BACKEND_CONTROL_PLANE_SCHEMA_VERSION,
    MAX_CONTROL_PLANE_JSON_BYTES,
    BackendControlPlaneEnvelope,
    BackendIdentity,
    CapabilityProbe,
    DiagnosticEvent,
    EvidenceLevel,
    HealthSummary,
    HelperSummary,
    InputSummary,
    LifecycleSummary,
    NormalizedFailure,
    OperationOutcome,
    OwnershipSummary,
    PresentationSummary,
    ProbeState,
    ProducerInfo,
    RecoveryClass,
    RuntimeHealth,
    SelectionSummary,
    SupportPolicy,
    SupportSummary,
    mutable_json_value,
)


@dataclass(frozen=True, slots=True)
class EnvelopeDecodeResult:
    """A decoded envelope or a normalized safe failure."""

    envelope: BackendControlPlaneEnvelope | None
    failure_code: str | None
    message: str

    def __post_init__(self) -> None:
        if (self.envelope is None) == (self.failure_code is None):
            raise ValueError("decode result must contain exactly one of envelope or failure_code")

    @property
    def ok(self) -> bool:
        return self.envelope is not None

    def require_envelope(self) -> BackendControlPlaneEnvelope:
        if self.envelope is None:
            raise ValueError(self.message)
        return self.envelope


def serialize_backend_envelope(envelope: BackendControlPlaneEnvelope) -> str:
    """Serialize one immutable envelope to deterministic standard JSON."""

    if not isinstance(envelope, BackendControlPlaneEnvelope):
        raise TypeError("envelope must be BackendControlPlaneEnvelope")
    payload = json.dumps(
        _encode_envelope(envelope),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    if len(payload.encode("utf-8")) > MAX_CONTROL_PLANE_JSON_BYTES:
        raise ValueError(f"serialized backend envelope exceeds {MAX_CONTROL_PLANE_JSON_BYTES}-byte size limit")
    return payload


def deserialize_backend_envelope(payload: str | bytes) -> EnvelopeDecodeResult:
    """Strictly decode schema version 1 without guessing or coercing versions."""

    if not isinstance(payload, (str, bytes)):
        return _decode_failure("malformed_envelope", "backend envelope must be JSON text")
    payload_size = len(payload) if isinstance(payload, bytes) else len(payload.encode("utf-8"))
    if payload_size > MAX_CONTROL_PLANE_JSON_BYTES:
        return _decode_failure(
            "malformed_envelope",
            f"backend envelope exceeds {MAX_CONTROL_PLANE_JSON_BYTES}-byte size limit",
        )
    try:
        raw = json.loads(payload)
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as exc:
        return _decode_failure(
            "malformed_envelope", f"invalid backend envelope JSON: {exc.msg if hasattr(exc, 'msg') else exc}"
        )
    if not isinstance(raw, dict):
        return _decode_failure("malformed_envelope", "backend envelope must be a JSON object")

    schema_version = raw.get("schema_version")
    if isinstance(schema_version, bool) or not isinstance(schema_version, int):
        return _decode_failure(
            "incompatible_schema",
            f"backend schema version must be {BACKEND_CONTROL_PLANE_SCHEMA_VERSION}; received {schema_version!r}",
        )
    if schema_version != BACKEND_CONTROL_PLANE_SCHEMA_VERSION:
        return _decode_failure(
            "incompatible_schema",
            f"backend schema version {schema_version} is incompatible; expected {BACKEND_CONTROL_PLANE_SCHEMA_VERSION}",
        )

    try:
        envelope = _decode_envelope(raw)
    except (KeyError, TypeError, ValueError) as exc:
        return _decode_failure("malformed_envelope", f"malformed backend schema version 1 envelope: {exc}")
    return EnvelopeDecodeResult(envelope=envelope, failure_code=None, message="")


def _decode_failure(code: str, message: str) -> EnvelopeDecodeResult:
    return EnvelopeDecodeResult(envelope=None, failure_code=code, message=message)


def _encode_envelope(envelope: BackendControlPlaneEnvelope) -> dict[str, object]:
    return {
        "schema_version": envelope.schema_version,
        "producer": {
            "component": envelope.producer.component,
            "version": envelope.producer.version,
        },
        "revision": envelope.revision,
        "selected_runtime": {
            "family": envelope.selected_runtime.family,
            "instance": envelope.selected_runtime.instance,
        },
        "selection": {
            "mode": envelope.selection.mode,
            "restart_required": envelope.selection.restart_required,
            "inputs_revision": envelope.selection.inputs_revision,
        },
        "support": {
            "policy": envelope.support.policy.value,
            "environment_key": envelope.support.environment_key,
            "evidence_level": envelope.support.evidence_level.value,
            "evidence_record": envelope.support.evidence_record,
            "last_reviewed_release": envelope.support.last_reviewed_release,
        },
        "health": {
            "state": envelope.health.state.value,
            "reason_code": envelope.health.reason_code,
            "recovery": envelope.health.recovery.value,
        },
        "probes": [_encode_probe(probe) for probe in envelope.probes],
        "presentation": {
            "outcome": envelope.presentation.outcome.value,
            "reason_code": envelope.presentation.reason_code,
            "state_revision": envelope.presentation.state_revision,
            "requested_mode": envelope.presentation.requested_mode,
            "visible": envelope.presentation.visible,
            "presenter_label": envelope.presentation.presenter_label,
            "diagnostics": mutable_json_value(envelope.presentation.diagnostics),
        },
        "input": {
            "outcome": envelope.input.outcome.value,
            "reason_code": envelope.input.reason_code,
            "state_revision": envelope.input.state_revision,
            "interactive": envelope.input.interactive,
            "click_through": envelope.input.click_through,
            "focus_accepting": envelope.input.focus_accepting,
            "diagnostics": mutable_json_value(envelope.input.diagnostics),
        },
        "helper": _encode_helper(envelope.helper),
        "ownership": {
            "connected": envelope.ownership.connected,
            "state": envelope.ownership.state,
            "reason_code": envelope.ownership.reason_code,
            "age_ms": envelope.ownership.age_ms,
            "diagnostics": mutable_json_value(envelope.ownership.diagnostics),
        },
        "lifecycle": {
            "state": envelope.lifecycle.state,
            "state_revision": envelope.lifecycle.state_revision,
            "age_ms": envelope.lifecycle.age_ms,
            "restart_required": envelope.lifecycle.restart_required,
            "recent_events": [_encode_event(event) for event in envelope.lifecycle.recent_events],
            "diagnostics": mutable_json_value(envelope.lifecycle.diagnostics),
        },
        "recent_failures": [_encode_failure(failure) for failure in envelope.recent_failures],
    }


def _encode_probe(probe: CapabilityProbe) -> dict[str, object]:
    return {
        "capability_id": probe.capability_id,
        "state": probe.state.value,
        "source": probe.source,
        "reason_code": probe.reason_code,
        "sanitized_evidence": mutable_json_value(probe.sanitized_evidence),
    }


def _encode_helper(helper: HelperSummary | None) -> dict[str, object]:
    if helper is None:
        return {}
    return {
        "required": helper.required,
        "available": helper.available,
        "compatible": helper.compatible,
        "owned": helper.owned,
        "health": helper.health.value,
        "recovery": helper.recovery.value,
        "reason_code": helper.reason_code,
        "diagnostics": mutable_json_value(helper.diagnostics),
    }


def _encode_failure(failure: NormalizedFailure) -> dict[str, object]:
    return {
        "failure_code": failure.failure_code,
        "component": failure.component,
        "health": failure.health.value,
        "recovery": failure.recovery.value,
        "state_revision": failure.state_revision,
        "age_ms": failure.age_ms,
        "details": mutable_json_value(failure.details),
    }


def _encode_event(event: DiagnosticEvent) -> dict[str, object]:
    return {
        "event_code": event.event_code,
        "component": event.component,
        "state_revision": event.state_revision,
        "safe_correlation_id": event.safe_correlation_id,
        "age_ms": event.age_ms,
        "details": mutable_json_value(event.details),
    }


def _decode_envelope(raw: Mapping[str, object]) -> BackendControlPlaneEnvelope:
    root = _strict_object(
        raw,
        "envelope",
        {
            "schema_version",
            "producer",
            "revision",
            "selected_runtime",
            "selection",
            "support",
            "health",
            "probes",
            "presentation",
            "input",
            "helper",
            "ownership",
            "lifecycle",
            "recent_failures",
        },
    )
    producer = _strict_object(root["producer"], "producer", {"component", "version"})
    identity = _strict_object(root["selected_runtime"], "selected_runtime", {"family", "instance"})
    selection = _strict_object(
        root["selection"],
        "selection",
        {"mode", "restart_required", "inputs_revision"},
    )
    support = _strict_object(
        root["support"],
        "support",
        {"policy", "environment_key", "evidence_level", "evidence_record", "last_reviewed_release"},
    )
    health = _strict_object(root["health"], "health", {"state", "reason_code", "recovery"})
    probes = _strict_list(root["probes"], "probes")
    presentation = _strict_object(
        root["presentation"],
        "presentation",
        {
            "outcome",
            "reason_code",
            "state_revision",
            "requested_mode",
            "visible",
            "presenter_label",
            "diagnostics",
        },
    )
    input_summary = _strict_object(
        root["input"],
        "input",
        {
            "outcome",
            "reason_code",
            "state_revision",
            "interactive",
            "click_through",
            "focus_accepting",
            "diagnostics",
        },
    )
    ownership = _strict_object(
        root["ownership"],
        "ownership",
        {"connected", "state", "reason_code", "age_ms", "diagnostics"},
    )
    lifecycle = _strict_object(
        root["lifecycle"],
        "lifecycle",
        {"state", "state_revision", "age_ms", "restart_required", "recent_events", "diagnostics"},
    )
    failures = _strict_list(root["recent_failures"], "recent_failures")
    events = _strict_list(lifecycle["recent_events"], "lifecycle.recent_events")

    return BackendControlPlaneEnvelope(
        schema_version=_strict_int(root["schema_version"], "schema_version"),
        producer=ProducerInfo(
            component=_strict_string(producer["component"], "producer.component"),
            version=_strict_string(producer["version"], "producer.version"),
        ),
        revision=_strict_int(root["revision"], "revision"),
        selected_runtime=BackendIdentity(
            family=_strict_string(identity["family"], "selected_runtime.family"),
            instance=_strict_string(identity["instance"], "selected_runtime.instance"),
        ),
        selection=SelectionSummary(
            mode=_strict_string(selection["mode"], "selection.mode"),
            restart_required=_strict_bool(selection["restart_required"], "selection.restart_required"),
            inputs_revision=_strict_int(selection["inputs_revision"], "selection.inputs_revision"),
        ),
        support=SupportSummary(
            policy=_strict_enum(SupportPolicy, support["policy"], "support.policy"),
            environment_key=_strict_string(support["environment_key"], "support.environment_key"),
            evidence_level=_strict_enum(EvidenceLevel, support["evidence_level"], "support.evidence_level"),
            evidence_record=_strict_string(support["evidence_record"], "support.evidence_record"),
            last_reviewed_release=_strict_string(
                support["last_reviewed_release"],
                "support.last_reviewed_release",
            ),
        ),
        health=HealthSummary(
            state=_strict_enum(RuntimeHealth, health["state"], "health.state"),
            reason_code=_strict_string(health["reason_code"], "health.reason_code"),
            recovery=_strict_enum(RecoveryClass, health["recovery"], "health.recovery"),
        ),
        probes=tuple(_decode_probe(item, index) for index, item in enumerate(probes)),
        presentation=PresentationSummary(
            outcome=_strict_enum(OperationOutcome, presentation["outcome"], "presentation.outcome"),
            reason_code=_strict_string(presentation["reason_code"], "presentation.reason_code"),
            state_revision=_strict_int(presentation["state_revision"], "presentation.state_revision"),
            requested_mode=_strict_string(presentation["requested_mode"], "presentation.requested_mode"),
            visible=_strict_bool(presentation["visible"], "presentation.visible"),
            presenter_label=_strict_string(presentation["presenter_label"], "presentation.presenter_label"),
            diagnostics=_strict_mapping(presentation["diagnostics"], "presentation.diagnostics"),
        ),
        input=InputSummary(
            outcome=_strict_enum(OperationOutcome, input_summary["outcome"], "input.outcome"),
            reason_code=_strict_string(input_summary["reason_code"], "input.reason_code"),
            state_revision=_strict_int(input_summary["state_revision"], "input.state_revision"),
            interactive=_strict_bool(input_summary["interactive"], "input.interactive"),
            click_through=_strict_bool(input_summary["click_through"], "input.click_through"),
            focus_accepting=_strict_bool(input_summary["focus_accepting"], "input.focus_accepting"),
            diagnostics=_strict_mapping(input_summary["diagnostics"], "input.diagnostics"),
        ),
        helper=_decode_helper(root["helper"]),
        ownership=OwnershipSummary(
            connected=_strict_bool(ownership["connected"], "ownership.connected"),
            state=_strict_string(ownership["state"], "ownership.state"),
            reason_code=_strict_string(ownership["reason_code"], "ownership.reason_code"),
            age_ms=_strict_int(ownership["age_ms"], "ownership.age_ms"),
            diagnostics=_strict_mapping(ownership["diagnostics"], "ownership.diagnostics"),
        ),
        lifecycle=LifecycleSummary(
            state=_strict_string(lifecycle["state"], "lifecycle.state"),
            state_revision=_strict_int(lifecycle["state_revision"], "lifecycle.state_revision"),
            age_ms=_strict_int(lifecycle["age_ms"], "lifecycle.age_ms"),
            restart_required=_strict_bool(lifecycle["restart_required"], "lifecycle.restart_required"),
            recent_events=tuple(_decode_event(item, index) for index, item in enumerate(events)),
            diagnostics=_strict_mapping(lifecycle["diagnostics"], "lifecycle.diagnostics"),
        ),
        recent_failures=tuple(_decode_failure_record(item, index) for index, item in enumerate(failures)),
    )


def _decode_probe(value: object, index: int) -> CapabilityProbe:
    path = f"probes[{index}]"
    item = _strict_object(
        value,
        path,
        {"capability_id", "state", "source", "reason_code", "sanitized_evidence"},
    )
    reason_code = item["reason_code"]
    if reason_code is not None:
        reason_code = _strict_string(reason_code, f"{path}.reason_code")
    return CapabilityProbe(
        capability_id=_strict_string(item["capability_id"], f"{path}.capability_id"),
        state=_strict_enum(ProbeState, item["state"], f"{path}.state"),
        source=_strict_string(item["source"], f"{path}.source"),
        reason_code=reason_code,
        sanitized_evidence=_strict_mapping(item["sanitized_evidence"], f"{path}.sanitized_evidence"),
    )


def _decode_helper(value: object) -> HelperSummary | None:
    helper = _strict_mapping(value, "helper")
    if not helper:
        return None
    item = _strict_object(
        helper,
        "helper",
        {"required", "available", "compatible", "owned", "health", "recovery", "reason_code", "diagnostics"},
    )
    owned = item["owned"]
    if owned is not None:
        owned = _strict_bool(owned, "helper.owned")
    return HelperSummary(
        required=_strict_bool(item["required"], "helper.required"),
        available=_strict_bool(item["available"], "helper.available"),
        compatible=_strict_bool(item["compatible"], "helper.compatible"),
        owned=owned,
        health=_strict_enum(RuntimeHealth, item["health"], "helper.health"),
        recovery=_strict_enum(RecoveryClass, item["recovery"], "helper.recovery"),
        reason_code=_strict_string(item["reason_code"], "helper.reason_code"),
        diagnostics=_strict_mapping(item["diagnostics"], "helper.diagnostics"),
    )


def _decode_failure_record(value: object, index: int) -> NormalizedFailure:
    path = f"recent_failures[{index}]"
    item = _strict_object(
        value,
        path,
        {"failure_code", "component", "health", "recovery", "state_revision", "age_ms", "details"},
    )
    return NormalizedFailure(
        failure_code=_strict_string(item["failure_code"], f"{path}.failure_code"),
        component=_strict_string(item["component"], f"{path}.component"),
        health=_strict_enum(RuntimeHealth, item["health"], f"{path}.health"),
        recovery=_strict_enum(RecoveryClass, item["recovery"], f"{path}.recovery"),
        state_revision=_strict_int(item["state_revision"], f"{path}.state_revision"),
        age_ms=_strict_int(item["age_ms"], f"{path}.age_ms"),
        details=_strict_mapping(item["details"], f"{path}.details"),
    )


def _decode_event(value: object, index: int) -> DiagnosticEvent:
    path = f"lifecycle.recent_events[{index}]"
    item = _strict_object(
        value,
        path,
        {"event_code", "component", "state_revision", "safe_correlation_id", "age_ms", "details"},
    )
    correlation = item["safe_correlation_id"]
    if correlation is not None:
        correlation = _strict_string(correlation, f"{path}.safe_correlation_id")
    return DiagnosticEvent(
        event_code=_strict_string(item["event_code"], f"{path}.event_code"),
        component=_strict_string(item["component"], f"{path}.component"),
        state_revision=_strict_int(item["state_revision"], f"{path}.state_revision"),
        safe_correlation_id=correlation,
        age_ms=_strict_int(item["age_ms"], f"{path}.age_ms"),
        details=_strict_mapping(item["details"], f"{path}.details"),
    )


def _strict_object(value: object, path: str, expected_keys: set[str]) -> Mapping[str, object]:
    item = _strict_mapping(value, path)
    actual_keys = set(item)
    missing = expected_keys - actual_keys
    unknown = actual_keys - expected_keys
    if missing:
        raise ValueError(f"{path} is missing fields: {', '.join(sorted(missing))}")
    if unknown:
        raise ValueError(f"{path} contains unknown fields: {', '.join(sorted(unknown))}")
    return item


def _strict_mapping(value: object, path: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{path} must be an object")
    if any(not isinstance(key, str) for key in value):
        raise TypeError(f"{path} keys must be strings")
    return value


def _strict_list(value: object, path: str) -> list[object]:
    if not isinstance(value, list):
        raise TypeError(f"{path} must be an array")
    return value


def _strict_string(value: object, path: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{path} must be a string")
    return value


def _strict_bool(value: object, path: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{path} must be a boolean")
    return value


def _strict_int(value: object, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{path} must be an integer")
    return value


def _strict_enum(enum_type, value: object, path: str):
    token = _strict_string(value, path)
    try:
        return enum_type(token)
    except ValueError as exc:
        raise ValueError(f"{path} has unknown value {token!r}") from exc
