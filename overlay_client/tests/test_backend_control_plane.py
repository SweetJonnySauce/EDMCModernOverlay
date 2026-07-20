import json
from dataclasses import FrozenInstanceError, replace

import pytest

from overlay_client.backend.contracts import (
    BackendDescriptor,
    BackendFamily,
    BackendInstance,
    CapabilityClassification,
    FallbackReason,
    HelperKind,
    OperatingSystem,
    PlatformProbeResult,
    SessionType,
)
from overlay_client.backend.control_plane_codec import (
    deserialize_backend_envelope,
    serialize_backend_envelope,
)
from overlay_client.backend.control_plane_models import (
    BACKEND_CONTROL_PLANE_SCHEMA_VERSION,
    CAPABILITY_IDS,
    DETECTED_LINUX_BACKEND_INSTANCES,
    MAX_DIAGNOSTIC_EVENTS,
    MAX_DIAGNOSTIC_STRING_LENGTH,
    MAX_RECENT_FAILURES,
    MAX_CONTROL_PLANE_JSON_BYTES,
    REDACTION_MARKER,
    STABLE_LINUX_BACKEND_INSTANCES,
    BackendControlPlaneEnvelope,
    BackendIdentity,
    CapabilityProbe,
    DiagnosticEvent,
    EnvironmentKey,
    EvidenceLevel,
    HealthSummary,
    HelperSummary,
    InputSummary,
    LifecycleSummary,
    NormalizedFailure,
    OperationOutcome,
    OperationResult,
    OwnershipSummary,
    PresentationSummary,
    ProbeState,
    ProducerInfo,
    RecoveryClass,
    RuntimeHealth,
    SelectionSummary,
    SupportPolicy,
    SupportSummary,
)
from overlay_client.backend.shadow_status import ShadowStatusProducer, adapt_backend_selection_status
from overlay_client.backend.status import BackendSelectionStatus, HelperCapabilityState


def _environment_key(*, display_mode: str = "windowed") -> EnvironmentKey:
    return EnvironmentKey(
        operating_system="linux",
        distribution="ubuntu",
        distribution_version="24.04.4",
        session_type="wayland",
        desktop="gnome",
        compositor_or_wm="mutter",
        compositor_or_wm_version="46.0",
        display_mode=display_mode,
    )


def _support(
    policy: SupportPolicy = SupportPolicy.SUPPORTED,
    evidence_level: EvidenceLevel = EvidenceLevel.FULL_MATRIX,
) -> SupportSummary:
    return SupportSummary(
        policy=policy,
        environment_key=_environment_key().stable_key,
        evidence_level=evidence_level,
        evidence_record="ubuntu-24.04.4-gnome-46",
        last_reviewed_release="0.9.0",
    )


def _failure(index: int) -> NormalizedFailure:
    return NormalizedFailure(
        failure_code=f"failure_{index}",
        component="presentation",
        health=RuntimeHealth.DEGRADED,
        recovery=RecoveryClass.AUTOMATIC,
        state_revision=index,
        age_ms=index * 10,
        details={"reason_code": f"failure_{index}", "count": index},
    )


def _event(index: int) -> DiagnosticEvent:
    return DiagnosticEvent(
        event_code=f"event_{index}",
        component="backend",
        state_revision=index,
        safe_correlation_id=f"safe-{index}",
        age_ms=index * 5,
        details={"state": "observed", "count": index},
    )


def _complete_envelope(
    *,
    revision: int = 42,
    failures: tuple[NormalizedFailure, ...] = (),
    events: tuple[DiagnosticEvent, ...] = (),
) -> BackendControlPlaneEnvelope:
    return BackendControlPlaneEnvelope(
        schema_version=BACKEND_CONTROL_PLANE_SCHEMA_VERSION,
        producer=ProducerInfo(component="overlay_client", version="0.9.0"),
        revision=revision,
        selected_runtime=BackendIdentity(family="compositor_helper", instance="gnome_shell_wayland"),
        selection=SelectionSummary(mode="automatic", restart_required=False, inputs_revision=7),
        support=_support(),
        health=HealthSummary(
            state=RuntimeHealth.HEALTHY,
            reason_code="ready",
            recovery=RecoveryClass.AUTOMATIC,
        ),
        probes=(
            CapabilityProbe(
                capability_id="presentation.windowed",
                state=ProbeState.OPERATIONAL,
                source="gnome_helper",
                reason_code=None,
                sanitized_evidence={"available": True, "protocol_version": 4},
            ),
        ),
        presentation=PresentationSummary(
            outcome=OperationOutcome.APPLIED,
            reason_code="presented",
            state_revision=revision,
            requested_mode="windowed",
            visible=True,
            presenter_label="managed",
            diagnostics={"elapsed_ms": 1.25, "state": "stable"},
        ),
        input=InputSummary(
            outcome=OperationOutcome.APPLIED,
            reason_code="click_through",
            state_revision=revision,
            interactive=False,
            click_through=True,
            focus_accepting=False,
            diagnostics={"state": "click_through"},
        ),
        helper=HelperSummary(
            required=True,
            available=True,
            compatible=True,
            owned=True,
            health=RuntimeHealth.HEALTHY,
            recovery=RecoveryClass.AUTOMATIC,
            reason_code="helper_ready",
            diagnostics={"protocol_version": 4, "reported_version": "1.0.0"},
        ),
        ownership=OwnershipSummary(
            connected=True,
            state="owned",
            reason_code="owner_connected",
            age_ms=25,
            diagnostics={"state": "connected"},
        ),
        lifecycle=LifecycleSummary(
            state="running",
            state_revision=revision,
            age_ms=500,
            restart_required=False,
            recent_events=events,
            diagnostics={"state": "running"},
        ),
        recent_failures=failures,
    )


def _legacy_status(
    *,
    family: BackendFamily,
    instance: BackendInstance,
    classification: CapabilityClassification,
    session_type: SessionType = SessionType.WAYLAND,
    compositor: str = "gnome",
    fallback_reason: FallbackReason | None = None,
    helper_states: tuple[HelperCapabilityState, ...] = (),
) -> BackendSelectionStatus:
    return BackendSelectionStatus(
        probe=PlatformProbeResult(
            operating_system=OperatingSystem.LINUX,
            session_type=session_type,
            qt_platform_name="xcb" if instance is BackendInstance.XWAYLAND_COMPAT else "wayland",
            compositor=compositor,
        ),
        selected_backend=BackendDescriptor(family=family, instance=instance),
        classification=classification,
        fallback_reason=fallback_reason,
        helper_states=helper_states,
    )


def test_converged_enum_values_and_linux_identities_match_the_design() -> None:
    assert [item.value for item in ProbeState] == [
        "operational",
        "unavailable",
        "incompatible",
        "not_implemented",
        "not_applicable",
    ]
    assert [item.value for item in SupportPolicy] == [
        "supported",
        "compatibility",
        "unvalidated_operational",
        "unimplemented",
        "unsupported",
    ]
    assert [item.value for item in EvidenceLevel] == [
        "full_matrix",
        "maintainer_smoke",
        "community_confirmed",
        "mixed_reports",
        "reported_failure",
        "not_yet_reported",
        "not_applicable",
    ]
    assert [item.value for item in RuntimeHealth] == [
        "constructing",
        "healthy",
        "degraded",
        "unavailable",
        "incompatible",
        "ownership_conflict",
        "stopping",
        "stopped",
    ]
    assert [item.value for item in OperationOutcome] == [
        "applied",
        "pending",
        "hidden",
        "unavailable",
        "rejected",
    ]
    assert [item.value for item in RecoveryClass] == [
        "automatic",
        "retry_wait",
        "restart_required",
        "terminal",
    ]
    assert STABLE_LINUX_BACKEND_INSTANCES == (
        "gnome_shell_wayland",
        "native_x11",
        "xwayland_compat",
    )
    assert DETECTED_LINUX_BACKEND_INSTANCES == (
        "kwin_wayland",
        "wlroots_wayland",
        "hyprland_wayland",
        "generic_wayland",
        "cosmic_wayland",
        "gamescope_wayland",
    )
    assert "gnome_shell_raster" not in STABLE_LINUX_BACKEND_INSTANCES
    assert "capture.exclusion" in CAPABILITY_IDS


def test_environment_key_is_immutable_and_stable() -> None:
    environment = _environment_key()

    assert environment.stable_key == ("linux|ubuntu|24.04.4|wayland|gnome|mutter|46.0|windowed")
    with pytest.raises(FrozenInstanceError):
        environment.desktop = "kde"  # type: ignore[misc]


def test_status_axes_remain_independent_and_records_are_deeply_immutable() -> None:
    support = _support(SupportPolicy.SUPPORTED, EvidenceLevel.MAINTAINER_SMOKE)
    health = HealthSummary(
        state=RuntimeHealth.UNAVAILABLE,
        reason_code="helper_missing",
        recovery=RecoveryClass.RESTART_REQUIRED,
    )
    probe_evidence = {"available": False, "capabilities": ["presentation.windowed"]}
    probe = CapabilityProbe(
        capability_id="helper.compatible",
        state=ProbeState.UNAVAILABLE,
        source="shadow_adapter",
        reason_code="helper_missing",
        sanitized_evidence=probe_evidence,
    )

    probe_evidence["available"] = True
    probe_evidence["capabilities"].append("private")

    assert support.policy is SupportPolicy.SUPPORTED
    assert support.evidence_level is EvidenceLevel.MAINTAINER_SMOKE
    assert health.state is RuntimeHealth.UNAVAILABLE
    assert probe.sanitized_evidence == {
        "available": False,
        "capabilities": ("presentation.windowed",),
    }
    with pytest.raises(TypeError):
        probe.sanitized_evidence["available"] = True  # type: ignore[index]


@pytest.mark.parametrize(
    ("factory", "expected_exception"),
    [
        (lambda: SelectionSummary(mode="automatic", restart_required=False, inputs_revision=-1), ValueError),
        (lambda: SelectionSummary(mode="automatic", restart_required=False, inputs_revision=True), TypeError),
        (
            lambda: OperationResult(
                outcome=OperationOutcome.APPLIED,
                reason_code="ready",
                health=RuntimeHealth.HEALTHY,
                recovery=RecoveryClass.AUTOMATIC,
                state_revision=-1,
                diagnostics={},
            ),
            ValueError,
        ),
        (
            lambda: NormalizedFailure(
                failure_code="failed",
                component="backend",
                health=RuntimeHealth.DEGRADED,
                recovery=RecoveryClass.RETRY_WAIT,
                state_revision=0,
                age_ms=-1,
                details={},
            ),
            ValueError,
        ),
    ],
)
def test_revision_and_local_age_validation_is_per_record(factory, expected_exception) -> None:
    with pytest.raises(expected_exception):
        factory()

    assert _complete_envelope(revision=0).revision == 0
    assert _failure(0).age_ms == 0


def test_diagnostic_boundaries_allowlist_freeze_and_redact_before_formatting() -> None:
    adversarial = {
        "elapsed_ms": 3.5,
        "state": "token=super-secret",
        "capabilities": ["safe", {"path": "/home/alice/private"}],
        "launch_token": "super-secret",
        "owner_instance_id": "owner-raw",
        "target_handle": "0x1234",
        "title": "Elite - Dangerous",
        "command_line": "python --token super-secret",
        "exception": "Traceback private-data",
        "personal_path": "/home/alice/private",
        "unknown_but_safe": "must not cross allowlist",
    }

    result = OperationResult(
        outcome=OperationOutcome.REJECTED,
        reason_code="sanitized",
        health=RuntimeHealth.DEGRADED,
        recovery=RecoveryClass.RETRY_WAIT,
        state_revision=3,
        diagnostics=adversarial,
    )

    encoded = json.dumps(result.diagnostics, default=lambda value: dict(value), sort_keys=True)
    assert result.diagnostics["elapsed_ms"] == 3.5
    assert result.diagnostics["state"] == REDACTION_MARKER
    assert result.diagnostics["redacted"] == REDACTION_MARKER
    assert "unknown_but_safe" not in result.diagnostics
    for prohibited in (
        "super-secret",
        "owner-raw",
        "0x1234",
        "Elite - Dangerous",
        "python --token",
        "Traceback",
        "/home/alice",
    ):
        assert prohibited not in encoded
    with pytest.raises(TypeError):
        result.diagnostics["state"] = "changed"  # type: ignore[index]


def test_schema_v1_round_trip_is_deterministic_equivalent_and_immutable() -> None:
    envelope = _complete_envelope(failures=(_failure(1),), events=(_event(1),))

    first = serialize_backend_envelope(envelope)
    decoded = deserialize_backend_envelope(first)

    assert decoded.ok is True
    assert decoded.failure_code is None
    assert decoded.envelope == envelope
    assert serialize_backend_envelope(decoded.require_envelope()) == first
    assert first == json.dumps(json.loads(first), sort_keys=True, separators=(",", ":"))
    with pytest.raises(FrozenInstanceError):
        decoded.require_envelope().revision = 99  # type: ignore[misc]
    with pytest.raises(TypeError):
        decoded.require_envelope().presentation.diagnostics["state"] = "changed"  # type: ignore[index]


@pytest.mark.parametrize("schema_version", [None, 0, 2, "1", True])
def test_unknown_missing_stale_or_invalid_schema_version_fails_explicitly(schema_version) -> None:
    payload = json.loads(serialize_backend_envelope(_complete_envelope()))
    if schema_version is None:
        payload.pop("schema_version")
    else:
        payload["schema_version"] = schema_version

    result = deserialize_backend_envelope(json.dumps(payload))

    assert result.ok is False
    assert result.envelope is None
    assert result.failure_code == "incompatible_schema"
    assert "schema version" in result.message.lower()


@pytest.mark.parametrize(
    "mutate",
    [
        lambda payload: payload.update({"revision": "42"}),
        lambda payload: payload.update({"unexpected": True}),
        lambda payload: payload["producer"].pop("component"),
        lambda payload: payload.update({"probes": {}}),
        lambda payload: payload["health"].update({"state": "invented"}),
    ],
)
def test_malformed_schema_v1_fields_fail_without_coercion(mutate) -> None:
    payload = json.loads(serialize_backend_envelope(_complete_envelope()))
    mutate(payload)

    result = deserialize_backend_envelope(json.dumps(payload))

    assert result.ok is False
    assert result.failure_code == "malformed_envelope"
    assert result.envelope is None
    assert result.message


def test_failure_and_event_histories_retain_the_newest_bounded_entries() -> None:
    failures = tuple(_failure(index) for index in range(MAX_RECENT_FAILURES + 3))
    events = tuple(_event(index) for index in range(MAX_DIAGNOSTIC_EVENTS + 4))

    envelope = _complete_envelope(failures=failures, events=events)

    assert len(envelope.recent_failures) == MAX_RECENT_FAILURES
    assert envelope.recent_failures[0].failure_code == "failure_3"
    assert len(envelope.lifecycle.recent_events) == MAX_DIAGNOSTIC_EVENTS
    assert envelope.lifecycle.recent_events[0].event_code == "event_4"
    decoded = deserialize_backend_envelope(serialize_backend_envelope(envelope)).require_envelope()
    assert decoded.recent_failures == envelope.recent_failures
    assert decoded.lifecycle.recent_events == envelope.lifecycle.recent_events


def test_diagnostics_and_wire_payload_have_explicit_size_bounds() -> None:
    result = OperationResult(
        outcome=OperationOutcome.APPLIED,
        reason_code="bounded",
        health=RuntimeHealth.HEALTHY,
        recovery=RecoveryClass.AUTOMATIC,
        state_revision=1,
        diagnostics={"state": "x" * (MAX_DIAGNOSTIC_STRING_LENGTH + 100)},
    )

    assert len(result.diagnostics["state"]) == MAX_DIAGNOSTIC_STRING_LENGTH
    oversized = "{" + (" " * MAX_CONTROL_PLANE_JSON_BYTES) + "}"
    decoded = deserialize_backend_envelope(oversized)
    assert decoded.ok is False
    assert decoded.failure_code == "malformed_envelope"
    assert "size limit" in decoded.message


def test_duplicate_capability_probes_are_rejected_instead_of_growing_the_envelope() -> None:
    probe = _complete_envelope().probes[0]

    with pytest.raises(ValueError, match="duplicate capability"):
        replace(_complete_envelope(), probes=(probe, probe))


def test_codec_never_serializes_adversarial_secret_or_personal_data() -> None:
    unsafe_failure = NormalizedFailure(
        failure_code="helper_failed",
        component="helper",
        health=RuntimeHealth.UNAVAILABLE,
        recovery=RecoveryClass.RESTART_REQUIRED,
        state_revision=9,
        age_ms=10,
        details={
            "reason_code": "token=codec-secret",
            "owner_id": "raw-owner",
            "target_handle": "0xbeef",
            "path": "/home/bob/.private",
        },
    )

    encoded = serialize_backend_envelope(_complete_envelope(failures=(unsafe_failure,)))

    assert REDACTION_MARKER in encoded
    for prohibited in ("codec-secret", "raw-owner", "0xbeef", "/home/bob"):
        assert prohibited not in encoded


@pytest.mark.parametrize(
    ("status", "support", "expected_instance", "expected_policy", "expected_evidence", "expected_health"),
    [
        (
            _legacy_status(
                family=BackendFamily.COMPOSITOR_HELPER,
                instance=BackendInstance.GNOME_SHELL_WAYLAND,
                classification=CapabilityClassification.TRUE_OVERLAY,
                helper_states=(
                    HelperCapabilityState(
                        helper=HelperKind.GNOME_SHELL_EXTENSION,
                        required=True,
                        installed=False,
                        enabled=False,
                        approved=False,
                    ),
                ),
            ),
            _support(SupportPolicy.SUPPORTED, EvidenceLevel.MAINTAINER_SMOKE),
            "gnome_shell_wayland",
            SupportPolicy.SUPPORTED,
            EvidenceLevel.MAINTAINER_SMOKE,
            RuntimeHealth.UNAVAILABLE,
        ),
        (
            _legacy_status(
                family=BackendFamily.NATIVE_X11,
                instance=BackendInstance.NATIVE_X11,
                classification=CapabilityClassification.TRUE_OVERLAY,
                session_type=SessionType.X11,
                compositor="mutter",
            ),
            _support(SupportPolicy.SUPPORTED, EvidenceLevel.FULL_MATRIX),
            "native_x11",
            SupportPolicy.SUPPORTED,
            EvidenceLevel.FULL_MATRIX,
            RuntimeHealth.HEALTHY,
        ),
        (
            _legacy_status(
                family=BackendFamily.XWAYLAND_COMPAT,
                instance=BackendInstance.XWAYLAND_COMPAT,
                classification=CapabilityClassification.DEGRADED_OVERLAY,
                fallback_reason=FallbackReason.XWAYLAND_COMPAT_ONLY,
            ),
            _support(SupportPolicy.COMPATIBILITY, EvidenceLevel.MAINTAINER_SMOKE),
            "xwayland_compat",
            SupportPolicy.COMPATIBILITY,
            EvidenceLevel.MAINTAINER_SMOKE,
            RuntimeHealth.DEGRADED,
        ),
        (
            _legacy_status(
                family=BackendFamily.NATIVE_WAYLAND,
                instance=BackendInstance.KWIN_WAYLAND,
                classification=CapabilityClassification.UNSUPPORTED,
                compositor="kwin",
            ),
            _support(SupportPolicy.UNIMPLEMENTED, EvidenceLevel.NOT_APPLICABLE),
            "kwin_wayland",
            SupportPolicy.UNIMPLEMENTED,
            EvidenceLevel.NOT_APPLICABLE,
            RuntimeHealth.UNAVAILABLE,
        ),
    ],
)
def test_shadow_adapter_maps_representative_statuses_without_collapsing_axes(
    status,
    support,
    expected_instance,
    expected_policy,
    expected_evidence,
    expected_health,
) -> None:
    envelope = adapt_backend_selection_status(
        status,
        producer=ProducerInfo(component="overlay_client_shadow", version="0.9.0"),
        support=support,
        revision=4,
    )

    assert envelope.selected_runtime.instance == expected_instance
    assert envelope.support.policy is expected_policy
    assert envelope.support.evidence_level is expected_evidence
    assert envelope.health.state is expected_health
    assert envelope.revision == 4
    assert envelope.probes
    assert {probe.capability_id for probe in envelope.probes} <= set(CAPABILITY_IDS)
    assert deserialize_backend_envelope(serialize_backend_envelope(envelope)).ok is True


def test_shadow_adapter_normalizes_transitional_raster_without_creating_a_new_identity() -> None:
    status = _legacy_status(
        family=BackendFamily.COMPOSITOR_HELPER,
        instance=BackendInstance.GNOME_SHELL_RASTER,
        classification=CapabilityClassification.DEGRADED_OVERLAY,
    )

    envelope = adapt_backend_selection_status(
        status,
        producer=ProducerInfo(component="overlay_client_shadow", version="0.9.0"),
        support=_support(SupportPolicy.SUPPORTED, EvidenceLevel.NOT_YET_REPORTED),
        revision=1,
    )

    assert envelope.selected_runtime == BackendIdentity(
        family="compositor_helper",
        instance="gnome_shell_wayland",
    )
    assert "gnome_shell_raster" not in serialize_backend_envelope(envelope)


def test_shadow_adapter_does_not_manufacture_missing_evidence() -> None:
    status = _legacy_status(
        family=BackendFamily.NATIVE_X11,
        instance=BackendInstance.NATIVE_X11,
        classification=CapabilityClassification.TRUE_OVERLAY,
        session_type=SessionType.X11,
    )

    envelope = adapt_backend_selection_status(
        status,
        producer=ProducerInfo(component="overlay_client_shadow", version="0.9.0"),
        support=_support(SupportPolicy.UNVALIDATED_OPERATIONAL, EvidenceLevel.NOT_YET_REPORTED),
        revision=1,
    )

    assert envelope.health.state is RuntimeHealth.HEALTHY
    assert envelope.support.policy is SupportPolicy.UNVALIDATED_OPERATIONAL
    assert envelope.support.evidence_level is EvidenceLevel.NOT_YET_REPORTED


def test_shadow_adapter_degrades_when_required_helper_compatibility_is_unconfirmed() -> None:
    status = _legacy_status(
        family=BackendFamily.COMPOSITOR_HELPER,
        instance=BackendInstance.GNOME_SHELL_WAYLAND,
        classification=CapabilityClassification.TRUE_OVERLAY,
        helper_states=(
            HelperCapabilityState(
                helper=HelperKind.GNOME_SHELL_EXTENSION,
                required=True,
                installed=True,
                enabled=True,
                approved=False,
            ),
        ),
    )

    envelope = adapt_backend_selection_status(
        status,
        producer=ProducerInfo(component="overlay_client_shadow", version="0.9.0"),
        support=_support(SupportPolicy.SUPPORTED, EvidenceLevel.NOT_YET_REPORTED),
        revision=1,
    )

    assert envelope.helper is not None
    assert envelope.helper.compatible is False
    assert envelope.helper.health is RuntimeHealth.DEGRADED
    assert envelope.health.state is RuntimeHealth.DEGRADED
    assert envelope.support.policy is SupportPolicy.SUPPORTED
    assert envelope.support.evidence_level is EvidenceLevel.NOT_YET_REPORTED


def test_shadow_producer_is_a_cheap_disabled_noop_and_revisions_never_decrease() -> None:
    status = _legacy_status(
        family=BackendFamily.NATIVE_X11,
        instance=BackendInstance.NATIVE_X11,
        classification=CapabilityClassification.TRUE_OVERLAY,
        session_type=SessionType.X11,
    )
    producer_info = ProducerInfo(component="overlay_client_shadow", version="0.9.0")
    support = _support()

    disabled = ShadowStatusProducer(enabled=False, producer=producer_info, support=support)
    assert disabled.emit(object()) is None  # type: ignore[arg-type]

    producer = ShadowStatusProducer(enabled=True, producer=producer_info, support=support)
    first = producer.emit(status)
    equivalent = producer.emit(status)
    changed = producer.emit(replace(status, classification=CapabilityClassification.DEGRADED_OVERLAY))
    unchanged_again = producer.emit(replace(status, classification=CapabilityClassification.DEGRADED_OVERLAY))

    assert first is not None
    assert equivalent is not None
    assert changed is not None
    assert unchanged_again is not None
    assert first.revision == equivalent.revision == 1
    assert changed.revision == unchanged_again.revision == 2
    assert [first.revision, equivalent.revision, changed.revision, unchanged_again.revision] == sorted(
        [first.revision, equivalent.revision, changed.revision, unchanged_again.revision]
    )


def test_shadow_adapter_redacts_legacy_helper_detail() -> None:
    status = _legacy_status(
        family=BackendFamily.COMPOSITOR_HELPER,
        instance=BackendInstance.GNOME_SHELL_WAYLAND,
        classification=CapabilityClassification.DEGRADED_OVERLAY,
        helper_states=(
            HelperCapabilityState(
                helper=HelperKind.GNOME_SHELL_EXTENSION,
                required=True,
                installed=True,
                enabled=False,
                approved=False,
                version="1.0.0",
                detail="token=shadow-secret path=/home/carol/private",
            ),
        ),
    )

    encoded = serialize_backend_envelope(
        adapt_backend_selection_status(
            status,
            producer=ProducerInfo(component="overlay_client_shadow", version="0.9.0"),
            support=_support(),
            revision=1,
        )
    )

    assert "shadow-secret" not in encoded
    assert "/home/carol" not in encoded
