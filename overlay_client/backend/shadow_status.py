"""Developer-only translation of transitional status into the converged envelope."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import BackendInstance, CapabilityClassification
from .control_plane_codec import serialize_backend_envelope
from .control_plane_models import (
    CAPABILITY_IDS,
    DETECTED_LINUX_BACKEND_INSTANCES,
    BACKEND_CONTROL_PLANE_SCHEMA_VERSION,
    BackendControlPlaneEnvelope,
    BackendIdentity,
    CapabilityProbe,
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
    SupportSummary,
)
from .status import BackendSelectionStatus, HelperCapabilityState


_SHADOW_IDENTITY_BY_TRANSITIONAL_INSTANCE = {
    BackendInstance.GNOME_SHELL_WAYLAND: BackendIdentity("compositor_helper", "gnome_shell_wayland"),
    BackendInstance.GNOME_SHELL_RASTER: BackendIdentity("compositor_helper", "gnome_shell_wayland"),
    BackendInstance.NATIVE_X11: BackendIdentity("native_x11", "native_x11"),
    BackendInstance.XWAYLAND_COMPAT: BackendIdentity("xwayland_compat", "xwayland_compat"),
    BackendInstance.KWIN_WAYLAND: BackendIdentity("native_wayland", "kwin_wayland"),
    BackendInstance.SWAY_WAYFIRE_WLROOTS: BackendIdentity("native_wayland", "wlroots_wayland"),
    BackendInstance.HYPRLAND: BackendIdentity("native_wayland", "hyprland_wayland"),
    BackendInstance.WAYLAND_LAYER_SHELL_GENERIC: BackendIdentity("native_wayland", "generic_wayland"),
    BackendInstance.COSMIC: BackendIdentity("native_wayland", "cosmic_wayland"),
    BackendInstance.GAMESCOPE: BackendIdentity("native_wayland", "gamescope_wayland"),
    BackendInstance.WINDOWS_DESKTOP: BackendIdentity("native_windows", "windows_desktop"),
    BackendInstance.PORTAL_FALLBACK: BackendIdentity("portal_fallback", "portal_fallback"),
    BackendInstance.UNKNOWN: BackendIdentity("unknown", "unknown"),
}


def adapt_backend_selection_status(
    status: BackendSelectionStatus,
    *,
    producer: ProducerInfo,
    support: SupportSummary,
    revision: int,
) -> BackendControlPlaneEnvelope:
    """Build a diagnostic-only schema-v1 snapshot from transitional status.

    Support and reviewed evidence are explicit inputs because the transitional classification
    cannot establish either dimension.  The returned snapshot is never a behavior input.
    """

    if not isinstance(status, BackendSelectionStatus):
        raise TypeError("status must be BackendSelectionStatus")
    if not isinstance(producer, ProducerInfo):
        raise TypeError("producer must be ProducerInfo")
    if not isinstance(support, SupportSummary):
        raise TypeError("support must be SupportSummary")

    identity = _shadow_identity(status)
    helper = _helper_summary(status.helper_states)
    health = _health_summary(status, identity=identity, helper=helper)
    restart_required = health.recovery is RecoveryClass.RESTART_REQUIRED or status.manual_override is not None
    requested_mode = _display_mode_from_support(support)
    presentation_outcome = _operation_outcome(health.state)
    input_outcome = _operation_outcome(health.state)

    return BackendControlPlaneEnvelope(
        schema_version=BACKEND_CONTROL_PLANE_SCHEMA_VERSION,
        producer=producer,
        revision=revision,
        selected_runtime=identity,
        selection=SelectionSummary(
            mode="manual" if status.manual_override is not None else "automatic",
            restart_required=restart_required,
            inputs_revision=0,
        ),
        support=support,
        health=health,
        probes=_capability_probes(status, identity=identity, health=health, helper=helper),
        presentation=PresentationSummary(
            outcome=presentation_outcome,
            reason_code=health.reason_code,
            state_revision=revision,
            requested_mode=requested_mode,
            visible=False,
            presenter_label="",
            diagnostics={
                "state": health.state.value,
                "classification": status.classification.value,
                "selected_instance": identity.instance,
            },
        ),
        input=InputSummary(
            outcome=input_outcome,
            reason_code=health.reason_code,
            state_revision=revision,
            interactive=False,
            click_through=input_outcome is OperationOutcome.APPLIED,
            focus_accepting=False,
            diagnostics={"state": health.state.value},
        ),
        helper=helper,
        ownership=OwnershipSummary(
            connected=False,
            state="not_reported",
            reason_code="legacy_status_no_ownership",
            age_ms=0,
            diagnostics={"state": "not_reported"},
        ),
        lifecycle=LifecycleSummary(
            state="shadow",
            state_revision=revision,
            age_ms=0,
            restart_required=restart_required,
            recent_events=(),
            diagnostics={"state": "shadow"},
        ),
        recent_failures=_normalized_failures(status, health=health, revision=revision, helper=helper),
    )


@dataclass(slots=True)
class ShadowStatusProducer:
    """Process-local, developer-gated producer with monotonic visible revisions."""

    enabled: bool
    producer: ProducerInfo
    support: SupportSummary
    _revision: int = 0
    _comparison_json: str | None = None

    def emit(self, status: BackendSelectionStatus) -> BackendControlPlaneEnvelope | None:
        if not self.enabled:
            return None

        comparison = adapt_backend_selection_status(
            status,
            producer=self.producer,
            support=self.support,
            revision=0,
        )
        comparison_json = serialize_backend_envelope(comparison)
        if comparison_json != self._comparison_json:
            self._revision += 1
            self._comparison_json = comparison_json
        return adapt_backend_selection_status(
            status,
            producer=self.producer,
            support=self.support,
            revision=self._revision,
        )


def _shadow_identity(status: BackendSelectionStatus) -> BackendIdentity:
    descriptor = status.selected_backend
    mapped = _SHADOW_IDENTITY_BY_TRANSITIONAL_INSTANCE.get(descriptor.instance)
    if mapped is not None:
        return mapped
    return BackendIdentity(descriptor.family.value, descriptor.instance.value)


def _helper_summary(states: tuple[HelperCapabilityState, ...]) -> HelperSummary | None:
    if not states:
        return None
    required_states = tuple(state for state in states if state.required)
    relevant_states = required_states or tuple(states)
    required = bool(required_states)
    available = all(state.available for state in relevant_states)
    incompatible = any(
        "incompatible" in state.detail.lower() or "protocol_mismatch" in state.detail.lower()
        for state in relevant_states
    )
    compatible = available and all(state.approved for state in relevant_states) and not incompatible
    if incompatible:
        health = RuntimeHealth.INCOMPATIBLE
        recovery = RecoveryClass.RESTART_REQUIRED
        reason_code = "helper_incompatible"
    elif required and not available:
        health = RuntimeHealth.UNAVAILABLE
        recovery = RecoveryClass.RESTART_REQUIRED
        reason_code = "helper_unavailable"
    elif not available:
        health = RuntimeHealth.DEGRADED
        recovery = RecoveryClass.AUTOMATIC
        reason_code = "optional_helper_unavailable"
    elif not compatible:
        health = RuntimeHealth.DEGRADED
        recovery = RecoveryClass.RETRY_WAIT
        reason_code = "helper_compatibility_unconfirmed"
    else:
        health = RuntimeHealth.HEALTHY
        recovery = RecoveryClass.AUTOMATIC
        reason_code = "helper_ready"
    versions = tuple(state.version for state in relevant_states if state.version)
    return HelperSummary(
        required=required,
        available=available,
        compatible=compatible,
        owned=None,
        health=health,
        recovery=recovery,
        reason_code=reason_code,
        diagnostics={
            "helper_count": len(relevant_states),
            "helper_kinds": tuple(state.helper.value for state in relevant_states),
            "reported_version": versions[0] if len(versions) == 1 else "",
            "available": available,
            "compatible": compatible,
        },
    )


def _health_summary(
    status: BackendSelectionStatus,
    *,
    identity: BackendIdentity,
    helper: HelperSummary | None,
) -> HealthSummary:
    if identity.instance in DETECTED_LINUX_BACKEND_INSTANCES:
        return HealthSummary(
            state=RuntimeHealth.UNAVAILABLE,
            reason_code="backend_not_implemented",
            recovery=RecoveryClass.TERMINAL,
        )
    if helper is not None and helper.required and helper.health is not RuntimeHealth.HEALTHY:
        return HealthSummary(
            state=helper.health,
            reason_code=helper.reason_code,
            recovery=helper.recovery,
        )
    if status.classification is CapabilityClassification.TRUE_OVERLAY:
        return HealthSummary(
            state=RuntimeHealth.HEALTHY,
            reason_code="legacy_true_overlay",
            recovery=RecoveryClass.AUTOMATIC,
        )
    if status.classification is CapabilityClassification.DEGRADED_OVERLAY:
        return HealthSummary(
            state=RuntimeHealth.DEGRADED,
            reason_code="legacy_degraded_overlay",
            recovery=RecoveryClass.AUTOMATIC,
        )
    return HealthSummary(
        state=RuntimeHealth.UNAVAILABLE,
        reason_code="legacy_unsupported",
        recovery=RecoveryClass.TERMINAL,
    )


def _capability_probes(
    status: BackendSelectionStatus,
    *,
    identity: BackendIdentity,
    health: HealthSummary,
    helper: HelperSummary | None,
) -> tuple[CapabilityProbe, ...]:
    probes: list[CapabilityProbe] = []
    unimplemented = identity.instance in DETECTED_LINUX_BACKEND_INSTANCES
    for capability_id in CAPABILITY_IDS:
        state, reason_code = _probe_state(
            capability_id,
            health=health,
            helper=helper,
            unimplemented=unimplemented,
        )
        probes.append(
            CapabilityProbe(
                capability_id=capability_id,
                state=state,
                source="shadow_adapter",
                reason_code=reason_code,
                sanitized_evidence={
                    "state": state.value,
                    "classification": status.classification.value,
                    "selected_instance": identity.instance,
                    "available": state is ProbeState.OPERATIONAL,
                },
            )
        )
    return tuple(probes)


def _probe_state(
    capability_id: str,
    *,
    health: HealthSummary,
    helper: HelperSummary | None,
    unimplemented: bool,
) -> tuple[ProbeState, str | None]:
    if capability_id == "capture.exclusion":
        return ProbeState.NOT_APPLICABLE, "vocabulary_only"
    if unimplemented:
        return ProbeState.NOT_IMPLEMENTED, "backend_not_implemented"
    if capability_id in {"lifecycle.owner_liveness", "lifecycle.external_expiry", "helper.ownership"}:
        return ProbeState.NOT_APPLICABLE, "legacy_status_not_reported"
    if capability_id == "helper.compatible":
        if helper is None:
            return ProbeState.NOT_APPLICABLE, "helper_not_applicable"
        if helper.health is RuntimeHealth.INCOMPATIBLE:
            return ProbeState.INCOMPATIBLE, helper.reason_code
        if not helper.available:
            return ProbeState.UNAVAILABLE, helper.reason_code
        if helper.compatible:
            return ProbeState.OPERATIONAL, None
        return ProbeState.UNAVAILABLE, helper.reason_code
    if health.state is RuntimeHealth.INCOMPATIBLE:
        return ProbeState.INCOMPATIBLE, health.reason_code
    if health.state is RuntimeHealth.UNAVAILABLE:
        return ProbeState.UNAVAILABLE, health.reason_code
    return ProbeState.OPERATIONAL, None


def _normalized_failures(
    status: BackendSelectionStatus,
    *,
    health: HealthSummary,
    revision: int,
    helper: HelperSummary | None,
) -> tuple[NormalizedFailure, ...]:
    failures: list[NormalizedFailure] = []
    if status.override_error:
        failures.append(
            NormalizedFailure(
                failure_code="invalid_override",
                component="selection",
                health=health.state,
                recovery=health.recovery,
                state_revision=revision,
                age_ms=0,
                details={"reason_code": status.override_error},
            )
        )
    if status.fallback_reason is not None:
        failures.append(
            NormalizedFailure(
                failure_code="legacy_fallback",
                component="selection",
                health=health.state,
                recovery=health.recovery,
                state_revision=revision,
                age_ms=0,
                details={"fallback_reason": status.fallback_reason.value},
            )
        )
    if helper is not None and helper.health in {RuntimeHealth.INCOMPATIBLE, RuntimeHealth.UNAVAILABLE}:
        failures.append(
            NormalizedFailure(
                failure_code=helper.reason_code,
                component="helper",
                health=helper.health,
                recovery=helper.recovery,
                state_revision=revision,
                age_ms=0,
                details={"reason_code": helper.reason_code},
            )
        )
    return tuple(failures)


def _operation_outcome(health: RuntimeHealth) -> OperationOutcome:
    if health in {RuntimeHealth.HEALTHY, RuntimeHealth.DEGRADED}:
        return OperationOutcome.APPLIED
    return OperationOutcome.UNAVAILABLE


def _display_mode_from_support(support: SupportSummary) -> str:
    parts = support.environment_key.rsplit("|", 1)
    return parts[-1] if len(parts) == 2 else ""
