"""Reusable backend-runtime contract suite and deterministic test-only paper backend."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Protocol, runtime_checkable

from overlay_client.backend.control_plane_codec import deserialize_backend_envelope, serialize_backend_envelope
from overlay_client.backend.control_plane_models import (
    BACKEND_CONTROL_PLANE_SCHEMA_VERSION,
    BackendControlPlaneEnvelope,
    BackendIdentity,
    CapabilityProbe,
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
from overlay_client.backend.runtime_contracts import (
    BackendRuntime,
    CoordinateSpace,
    DisplayMode,
    FrameSnapshot,
    HelperHealthSnapshot,
    HelperOwnershipState,
    HideReason,
    InputPolicySnapshot,
    InteractionIntent,
    LifecycleSnapshot,
    LifecycleState,
    NormalizedRect,
    OverlaySurface,
    PresentationIntent,
    PresentationSnapshot,
    StopReason,
    TargetIdentity,
    TargetObserver,
    TargetSnapshot,
)


@runtime_checkable
class BackendRuntimeTestRig(Protocol):
    """Injected controls required by the reusable behavioral contract suite."""

    @property
    def runtime(self) -> BackendRuntime: ...

    @property
    def cleanup_order(self) -> list[str]: ...

    @property
    def cleanup_counts(self) -> Mapping[str, int]: ...

    def appear_target(self, snapshot: TargetSnapshot) -> None: ...

    def lose_target(self) -> None: ...

    def next_presentation_outcome(self, outcome: OperationOutcome) -> None: ...

    def lose_owner(self) -> OperationResult: ...


@runtime_checkable
class BackendRuntimeTestFactory(Protocol):
    """Factory extension point supplied by each backend contract-test adapter."""

    def create(
        self,
        *,
        start_failure_after: str | None = None,
        include_helper: bool = False,
        cleanup_failures: Mapping[str, str] | None = None,
        cleanup_delays_ms: Mapping[str, int] | None = None,
        cleanup_timeout_ms: int = 100,
    ) -> BackendRuntimeTestRig: ...


class PaperBackendFactory:
    """Construct fresh deterministic in-memory runtimes for contract tests."""

    def create(
        self,
        *,
        start_failure_after: str | None = None,
        include_helper: bool = False,
        cleanup_failures: Mapping[str, str] | None = None,
        cleanup_delays_ms: Mapping[str, int] | None = None,
        cleanup_timeout_ms: int = 100,
    ) -> PaperBackendRig:
        return PaperBackendRig(
            start_failure_after=start_failure_after,
            include_helper=include_helper,
            cleanup_failures=dict(cleanup_failures or {}),
            cleanup_delays_ms=dict(cleanup_delays_ms or {}),
            cleanup_timeout_ms=cleanup_timeout_ms,
        )


class PaperBackendRig:
    """Test controls and observable resource ledger for one paper runtime."""

    def __init__(
        self,
        *,
        start_failure_after: str | None,
        include_helper: bool,
        cleanup_failures: dict[str, str],
        cleanup_delays_ms: dict[str, int],
        cleanup_timeout_ms: int,
    ) -> None:
        self._clock_ms = 0
        self._cleanup_order: list[str] = []
        resources = ["discovery", "presentation", "input"]
        if include_helper:
            resources.append("helper")
        self._cleanup_counts = {name: 0 for name in resources}
        self._runtime = _PaperRuntime(
            rig=self,
            start_failure_after=start_failure_after,
            include_helper=include_helper,
            cleanup_failures=cleanup_failures,
            cleanup_delays_ms=cleanup_delays_ms,
            cleanup_timeout_ms=cleanup_timeout_ms,
        )

    @property
    def runtime(self) -> _PaperRuntime:
        return self._runtime

    @property
    def cleanup_order(self) -> list[str]:
        return list(self._cleanup_order)

    @property
    def cleanup_counts(self) -> Mapping[str, int]:
        return dict(self._cleanup_counts)

    def appear_target(self, snapshot: TargetSnapshot) -> None:
        self._runtime._discovery_service.publish(snapshot)

    def lose_target(self) -> None:
        self._runtime._discovery_service.lose()
        self._runtime._presentation_service.hide(HideReason.TARGET_LOST)

    def next_presentation_outcome(self, outcome: OperationOutcome) -> None:
        self._runtime._presentation_service.set_next_outcome(outcome)

    def lose_owner(self) -> OperationResult:
        self._runtime._owner_connected = False
        self._runtime._changed()
        return self._runtime.stop(StopReason.OWNER_LOST)

    def _release(self, resource: str) -> None:
        self._cleanup_order.append(resource)
        self._cleanup_counts[resource] += 1

    def _advance(self, milliseconds: int) -> None:
        self._clock_ms += milliseconds


class _PaperDiscovery:
    def __init__(self, owner: _PaperRuntime) -> None:
        self._owner = owner
        self._observer: TargetObserver | None = None
        self._revision = 0
        self._stopped = False
        self._snapshot = _missing_target(0)

    def start(self, observer: TargetObserver) -> OperationResult:
        if not isinstance(observer, TargetObserver):
            raise TypeError("observer must satisfy TargetObserver")
        if self._stopped:
            return self._owner._rejected("discovery_stopped", self._revision)
        self._observer = observer
        return self._owner._applied("discovery_started", self._revision)

    def snapshot(self) -> TargetSnapshot:
        return self._snapshot

    def stop(self) -> OperationResult:
        if not self._stopped:
            self._stopped = True
            self._observer = None
            self._revision += 1
            self._snapshot = _missing_target(self._revision)
            self._owner._changed()
        return self._owner._applied("discovery_stopped", self._revision)

    def publish(self, snapshot: TargetSnapshot) -> None:
        if self._stopped:
            return
        if not isinstance(snapshot, TargetSnapshot) or not snapshot.available:
            raise ValueError("published target must be an available TargetSnapshot")
        self._revision += 1
        self._snapshot = replace(snapshot, state_revision=self._revision)
        self._owner._changed()
        if self._observer is not None:
            self._observer.target_changed(self._snapshot)

    def lose(self) -> None:
        if self._stopped:
            return
        self._revision += 1
        self._snapshot = _missing_target(self._revision)
        self._owner._changed()
        if self._observer is not None:
            self._observer.target_changed(self._snapshot)


class _PaperPresentation:
    def __init__(self, owner: _PaperRuntime) -> None:
        self._owner = owner
        self._revision = 0
        self._stopped = False
        self._next_outcome: OperationOutcome | None = None
        self._snapshot = PresentationSnapshot(
            outcome=OperationOutcome.HIDDEN,
            reason_code="not_presented",
            health=RuntimeHealth.CONSTRUCTING,
            recovery=RecoveryClass.AUTOMATIC,
            state_revision=0,
            requested_mode=DisplayMode.HIDDEN,
            visible=False,
            frame_revision=None,
            presenter_label="",
        )

    def present(self, intent: PresentationIntent, frame: FrameSnapshot | None) -> OperationResult:
        if not isinstance(intent, PresentationIntent):
            raise TypeError("intent must be PresentationIntent")
        if frame is not None and not isinstance(frame, FrameSnapshot):
            raise TypeError("frame must be FrameSnapshot or None")
        if self._stopped or self._owner._lifecycle_state is not LifecycleState.RUNNING:
            return self._owner._rejected("presentation_not_running", self._revision)
        if intent.requested_mode is DisplayMode.HIDDEN or not intent.requested_visible:
            return self.hide(HideReason.REQUESTED)
        if not self._owner._discovery_service.snapshot().available:
            return self._set_outcome(OperationOutcome.UNAVAILABLE, intent, "target_unavailable", False)
        if frame is None or not frame.available or not intent.frame_available:
            return self._set_outcome(OperationOutcome.PENDING, intent, "frame_pending", False)
        if frame.revision != intent.frame_revision:
            return self._owner._rejected("frame_revision_mismatch", self._revision)

        outcome = self._next_outcome or OperationOutcome.APPLIED
        self._next_outcome = None
        visible = outcome is OperationOutcome.APPLIED
        reason = {
            OperationOutcome.APPLIED: "presentation_applied",
            OperationOutcome.PENDING: "presentation_pending",
            OperationOutcome.UNAVAILABLE: "presentation_unavailable",
            OperationOutcome.HIDDEN: "presentation_hidden",
            OperationOutcome.REJECTED: "presentation_rejected",
        }[outcome]
        return self._set_outcome(outcome, intent, reason, visible)

    def hide(self, reason: HideReason) -> OperationResult:
        if not isinstance(reason, HideReason):
            raise TypeError("reason must be HideReason")
        self._revision += 1
        health = (
            RuntimeHealth.STOPPED if self._owner._lifecycle_state is LifecycleState.STOPPED else self._owner._health()
        )
        recovery = RecoveryClass.TERMINAL if health is RuntimeHealth.STOPPED else RecoveryClass.AUTOMATIC
        self._snapshot = PresentationSnapshot(
            outcome=OperationOutcome.HIDDEN,
            reason_code=reason.value,
            health=health,
            recovery=recovery,
            state_revision=self._revision,
            requested_mode=DisplayMode.HIDDEN,
            visible=False,
            frame_revision=None,
            presenter_label="paper",
        )
        self._owner._changed()
        return OperationResult(
            outcome=OperationOutcome.HIDDEN,
            reason_code=reason.value,
            health=health,
            recovery=recovery,
            state_revision=self._revision,
        )

    def presentation_snapshot(self) -> PresentationSnapshot:
        return self._snapshot

    def stop(self) -> OperationResult:
        if not self._stopped:
            self.hide(HideReason.RUNTIME_STOPPING)
            self._stopped = True
        return self._owner._applied("presentation_stopped", self._revision)

    def set_next_outcome(self, outcome: OperationOutcome) -> None:
        if outcome not in (OperationOutcome.PENDING, OperationOutcome.UNAVAILABLE, OperationOutcome.REJECTED):
            raise ValueError("injected presentation outcome must be pending, unavailable, or rejected")
        self._next_outcome = outcome

    def _set_outcome(
        self,
        outcome: OperationOutcome,
        intent: PresentationIntent,
        reason_code: str,
        visible: bool,
    ) -> OperationResult:
        self._revision += 1
        health = (
            RuntimeHealth.HEALTHY
            if outcome in (OperationOutcome.APPLIED, OperationOutcome.PENDING)
            else RuntimeHealth.DEGRADED
        )
        recovery = RecoveryClass.AUTOMATIC if outcome is not OperationOutcome.REJECTED else RecoveryClass.RETRY_WAIT
        self._snapshot = PresentationSnapshot(
            outcome=outcome,
            reason_code=reason_code,
            health=health,
            recovery=recovery,
            state_revision=self._revision,
            requested_mode=intent.requested_mode,
            visible=visible,
            frame_revision=intent.frame_revision,
            presenter_label="paper",
        )
        self._owner._changed()
        return OperationResult(
            outcome=outcome,
            reason_code=reason_code,
            health=health,
            recovery=recovery,
            state_revision=self._revision,
        )


class _PaperInputPolicy:
    def __init__(self, owner: _PaperRuntime) -> None:
        self._owner = owner
        self._revision = 0
        self._stopped = False
        self._snapshot = InputPolicySnapshot(
            outcome=OperationOutcome.APPLIED,
            reason_code="input_ready",
            health=RuntimeHealth.CONSTRUCTING,
            recovery=RecoveryClass.AUTOMATIC,
            state_revision=0,
            interactive=False,
            click_through=True,
            focus_accepting=False,
        )

    def apply(self, intent: InteractionIntent) -> OperationResult:
        if not isinstance(intent, InteractionIntent):
            raise TypeError("intent must be InteractionIntent")
        if self._stopped or self._owner._lifecycle_state is not LifecycleState.RUNNING:
            return self._owner._rejected("input_policy_not_running", self._revision)
        self._revision += 1
        self._snapshot = InputPolicySnapshot(
            outcome=OperationOutcome.APPLIED,
            reason_code="input_applied",
            health=RuntimeHealth.HEALTHY,
            recovery=RecoveryClass.AUTOMATIC,
            state_revision=self._revision,
            interactive=intent.interactive,
            click_through=intent.click_through,
            focus_accepting=intent.focus_accepting,
        )
        self._owner._changed()
        return self._owner._applied("input_applied", self._revision)

    def input_snapshot(self) -> InputPolicySnapshot:
        return self._snapshot

    def stop(self) -> OperationResult:
        if not self._stopped:
            self._stopped = True
            self._revision += 1
            self._snapshot = InputPolicySnapshot(
                outcome=OperationOutcome.APPLIED,
                reason_code="input_stopped",
                health=RuntimeHealth.STOPPED,
                recovery=RecoveryClass.TERMINAL,
                state_revision=self._revision,
                interactive=False,
                click_through=True,
                focus_accepting=False,
            )
            self._owner._changed()
        return self._owner._applied("input_stopped", self._revision)


class _PaperHelperLifecycle:
    def __init__(self, owner: _PaperRuntime) -> None:
        self._owner = owner
        self._revision = 0
        self._ownership = HelperOwnershipState.UNOWNED
        self._released = False

    def acquire(self) -> OperationResult:
        if self._released:
            return self._owner._rejected("helper_released", self._revision)
        if self._ownership is not HelperOwnershipState.OWNED:
            self._ownership = HelperOwnershipState.OWNED
            self._revision += 1
            self._owner._changed()
        return self._owner._applied("helper_acquired", self._revision)

    def renew(self) -> OperationResult:
        if self._ownership is not HelperOwnershipState.OWNED:
            return self._owner._rejected("helper_not_owned", self._revision)
        return self._owner._applied("helper_renewed", self._revision)

    def health(self) -> HelperHealthSnapshot:
        return HelperHealthSnapshot(
            required=True,
            available=True,
            compatible=True,
            ownership=self._ownership,
            health=self._owner._health(),
            recovery=RecoveryClass.AUTOMATIC,
            reason_code="helper_ready" if not self._released else "helper_released",
            state_revision=self._revision,
        )

    def release(self) -> OperationResult:
        if not self._released:
            self._ownership = HelperOwnershipState.UNOWNED
            self._released = True
            self._revision += 1
            self._owner._changed()
        return self._owner._applied("helper_released", self._revision)


class _PaperRuntime:
    def __init__(
        self,
        *,
        rig: PaperBackendRig,
        start_failure_after: str | None,
        include_helper: bool,
        cleanup_failures: dict[str, str],
        cleanup_delays_ms: dict[str, int],
        cleanup_timeout_ms: int,
    ) -> None:
        resources = (
            ("discovery", "presentation", "input", "helper")
            if include_helper
            else (
                "discovery",
                "presentation",
                "input",
            )
        )
        if start_failure_after is not None and start_failure_after not in resources:
            raise ValueError("start_failure_after must name an owned resource")
        if isinstance(cleanup_timeout_ms, bool) or not isinstance(cleanup_timeout_ms, int) or cleanup_timeout_ms < 0:
            raise ValueError("cleanup_timeout_ms must be a non-negative integer")
        self._rig = rig
        self._identity = BackendIdentity(family="test", instance="paper_backend")
        self._start_failure_after = start_failure_after
        self._resources = resources
        self._cleanup_failures = cleanup_failures
        self._cleanup_delays_ms = cleanup_delays_ms
        self._cleanup_timeout_ms = cleanup_timeout_ms
        self._acquired: list[str] = []
        self._released: set[str] = set()
        self._recent_failures: list[NormalizedFailure] = []
        self._status_revision = 0
        self._lifecycle_revision = 0
        self._lifecycle_state = LifecycleState.CONSTRUCTED
        self._start_attempted = False
        self._stop_requested = False
        self._cleanup_elapsed_ms = 0
        self._stop_result: OperationResult | None = None
        self._owner_connected = True
        self._surface: OverlaySurface | None = None
        self._discovery_service = _PaperDiscovery(self)
        self._presentation_service = _PaperPresentation(self)
        self._input_service = _PaperInputPolicy(self)
        self._helper_service = _PaperHelperLifecycle(self) if include_helper else None

    @property
    def identity(self) -> BackendIdentity:
        return self._identity

    @property
    def discovery(self) -> _PaperDiscovery:
        return self._discovery_service

    @property
    def presentation(self) -> _PaperPresentation:
        return self._presentation_service

    @property
    def input_policy(self) -> _PaperInputPolicy:
        return self._input_service

    @property
    def helper_lifecycle(self) -> _PaperHelperLifecycle | None:
        return self._helper_service

    def start(self) -> OperationResult:
        if self._lifecycle_state is LifecycleState.STOPPED:
            return self._rejected("runtime_stopped", self._lifecycle_revision)
        if self._start_attempted:
            return self._rejected("runtime_start_already_attempted", self._lifecycle_revision)
        self._start_attempted = True
        self._lifecycle_state = LifecycleState.STARTING
        self._lifecycle_revision += 1
        self._changed()
        for resource in self._resources:
            self._acquired.append(resource)
            if resource == self._start_failure_after:
                self._lifecycle_state = LifecycleState.START_FAILED
                self._lifecycle_revision += 1
                self._changed()
                self._record_failure("runtime_start_failed", resource, {"state": "partial_start"})
                self._cleanup_acquired()
                return OperationResult(
                    outcome=OperationOutcome.UNAVAILABLE,
                    reason_code="runtime_start_failed",
                    health=RuntimeHealth.UNAVAILABLE,
                    recovery=RecoveryClass.RETRY_WAIT,
                    state_revision=self._lifecycle_revision,
                )
        self._lifecycle_state = LifecycleState.RUNNING
        self._lifecycle_revision += 1
        self._changed()
        return self._applied("runtime_started", self._lifecycle_revision)

    def attach_surface(self, surface: OverlaySurface) -> OperationResult:
        if not isinstance(surface, OverlaySurface):
            raise TypeError("surface must satisfy OverlaySurface")
        if self._lifecycle_state is not LifecycleState.RUNNING:
            return self._rejected("runtime_not_running", self._lifecycle_revision)
        self._surface = surface
        self._changed()
        return self._applied("surface_attached", self._lifecycle_revision)

    def status_snapshot(self) -> BackendControlPlaneEnvelope:
        presentation = self._presentation_service.presentation_snapshot()
        input_state = self._input_service.input_snapshot()
        helper_state = self._helper_service.health() if self._helper_service is not None else None
        health = self._health()
        recovery = RecoveryClass.TERMINAL if health is RuntimeHealth.STOPPED else RecoveryClass.AUTOMATIC
        reason_code = {
            RuntimeHealth.CONSTRUCTING: "runtime_constructed",
            RuntimeHealth.HEALTHY: "runtime_ready",
            RuntimeHealth.UNAVAILABLE: "runtime_start_failed",
            RuntimeHealth.STOPPING: "runtime_stopping",
            RuntimeHealth.STOPPED: "runtime_stopped",
        }.get(health, "runtime_degraded")
        return BackendControlPlaneEnvelope(
            schema_version=BACKEND_CONTROL_PLANE_SCHEMA_VERSION,
            producer=ProducerInfo(component="test_support", version="1"),
            revision=self._status_revision,
            selected_runtime=self._identity,
            selection=SelectionSummary(mode="test", restart_required=False, inputs_revision=0),
            support=SupportSummary(
                policy=SupportPolicy.SUPPORTED,
                environment_key="test|paper",
                evidence_level=EvidenceLevel.NOT_YET_REPORTED,
                evidence_record="paper-contract-suite",
                last_reviewed_release="test",
            ),
            health=HealthSummary(state=health, reason_code=reason_code, recovery=recovery),
            probes=tuple(
                CapabilityProbe(
                    capability_id=capability_id,
                    state=ProbeState.OPERATIONAL,
                    source="test_support",
                    reason_code=None,
                )
                for capability_id in (
                    "target.discovery",
                    "presentation.windowed",
                    "presentation.borderless_fullscreen",
                    "input.click_through",
                    "input.focus_safe",
                    "lifecycle.owner_liveness",
                )
            ),
            presentation=PresentationSummary(
                outcome=presentation.outcome,
                reason_code=presentation.reason_code,
                state_revision=presentation.state_revision,
                requested_mode=presentation.requested_mode.value,
                visible=presentation.visible,
                presenter_label=presentation.presenter_label,
                diagnostics=presentation.diagnostics,
            ),
            input=InputSummary(
                outcome=input_state.outcome,
                reason_code=input_state.reason_code,
                state_revision=input_state.state_revision,
                interactive=input_state.interactive,
                click_through=input_state.click_through,
                focus_accepting=input_state.focus_accepting,
                diagnostics=input_state.diagnostics,
            ),
            helper=_paper_helper_summary(helper_state),
            ownership=OwnershipSummary(
                connected=self._owner_connected,
                state="connected" if self._owner_connected else "owner_lost",
                reason_code="owner_connected" if self._owner_connected else "owner_lost",
                age_ms=0,
            ),
            lifecycle=LifecycleSummary(
                state=self._lifecycle_state.value,
                state_revision=self._lifecycle_revision,
                age_ms=0,
                restart_required=False,
                diagnostics={"elapsed_ms": self._cleanup_elapsed_ms},
            ),
            recent_failures=tuple(self._recent_failures),
        )

    def lifecycle_snapshot(self) -> LifecycleSnapshot:
        return LifecycleSnapshot(
            state=self._lifecycle_state,
            state_revision=self._lifecycle_revision,
            start_attempted=self._start_attempted,
            stop_requested=self._stop_requested,
            cleanup_elapsed_ms=self._cleanup_elapsed_ms,
            restart_allowed=not self._start_attempted and not self._stop_requested,
            diagnostics={"elapsed_ms": self._cleanup_elapsed_ms},
        )

    def stop(self, reason: StopReason) -> OperationResult:
        if not isinstance(reason, StopReason):
            raise TypeError("reason must be StopReason")
        if self._stop_result is not None:
            return self._stop_result
        self._stop_requested = True
        self._lifecycle_state = LifecycleState.STOPPING
        self._lifecycle_revision += 1
        self._changed()
        self._presentation_service.stop()
        self._input_service.stop()
        self._discovery_service.stop()
        if self._helper_service is not None:
            self._helper_service.release()
        self._cleanup_acquired()
        self._surface = None
        self._lifecycle_state = LifecycleState.STOPPED
        self._lifecycle_revision += 1
        self._changed()
        self._stop_result = OperationResult(
            outcome=OperationOutcome.APPLIED,
            reason_code="runtime_stopped",
            health=RuntimeHealth.STOPPED,
            recovery=RecoveryClass.TERMINAL,
            state_revision=self._lifecycle_revision,
        )
        return self._stop_result

    def _cleanup_acquired(self) -> None:
        started_ms = self._rig._clock_ms
        for resource in reversed(self._acquired):
            if resource in self._released:
                continue
            elapsed_ms = self._rig._clock_ms - started_ms
            if elapsed_ms >= self._cleanup_timeout_ms:
                self._record_failure(
                    "cleanup_deadline_exceeded",
                    resource,
                    {"elapsed_ms": elapsed_ms},
                )
                break
            self._rig._release(resource)
            self._released.add(resource)
            self._rig._advance(self._cleanup_delays_ms.get(resource, 0))
            failure = self._cleanup_failures.get(resource)
            if failure is not None:
                self._record_failure("cleanup_failed", resource, {"exception": failure})
        elapsed_ms = self._rig._clock_ms - started_ms
        self._cleanup_elapsed_ms = min(elapsed_ms, self._cleanup_timeout_ms)

    def _record_failure(self, failure_code: str, component: str, details: dict[str, object]) -> None:
        self._recent_failures.append(
            NormalizedFailure(
                failure_code=failure_code,
                component=component,
                health=self._health(),
                recovery=RecoveryClass.RETRY_WAIT,
                state_revision=self._status_revision,
                age_ms=0,
                details=details,
            )
        )
        self._changed()

    def _health(self) -> RuntimeHealth:
        return {
            LifecycleState.CONSTRUCTED: RuntimeHealth.CONSTRUCTING,
            LifecycleState.STARTING: RuntimeHealth.CONSTRUCTING,
            LifecycleState.RUNNING: RuntimeHealth.HEALTHY,
            LifecycleState.START_FAILED: RuntimeHealth.UNAVAILABLE,
            LifecycleState.STOPPING: RuntimeHealth.STOPPING,
            LifecycleState.STOPPED: RuntimeHealth.STOPPED,
        }[self._lifecycle_state]

    def _changed(self) -> None:
        self._status_revision += 1

    def _applied(self, reason_code: str, revision: int) -> OperationResult:
        health = self._health()
        return OperationResult(
            outcome=OperationOutcome.APPLIED,
            reason_code=reason_code,
            health=health,
            recovery=RecoveryClass.TERMINAL if health is RuntimeHealth.STOPPED else RecoveryClass.AUTOMATIC,
            state_revision=revision,
        )

    def _rejected(self, reason_code: str, revision: int) -> OperationResult:
        health = self._health()
        return OperationResult(
            outcome=OperationOutcome.REJECTED,
            reason_code=reason_code,
            health=health,
            recovery=RecoveryClass.TERMINAL if health is RuntimeHealth.STOPPED else RecoveryClass.RETRY_WAIT,
            state_revision=revision,
        )


class _Observer:
    def __init__(self) -> None:
        self.snapshots: list[TargetSnapshot] = []

    def target_changed(self, snapshot: TargetSnapshot) -> None:
        self.snapshots.append(snapshot)


class _Surface:
    @property
    def surface_id(self) -> str:
        return "contract-surface"


def assert_backend_runtime_contract(factory: BackendRuntimeTestFactory) -> None:
    """Assert observable runtime behavior without depending on an implementation class."""

    rig = factory.create()
    runtime = rig.runtime
    identity = runtime.identity
    discovery = runtime.discovery
    presentation = runtime.presentation
    input_policy = runtime.input_policy

    assert isinstance(runtime, BackendRuntime)
    assert runtime.identity == identity
    assert runtime.discovery is discovery
    assert runtime.presentation is presentation
    assert runtime.input_policy is input_policy
    assert presentation is not input_policy
    assert runtime.start().outcome is OperationOutcome.APPLIED
    assert runtime.start().outcome is OperationOutcome.REJECTED
    assert runtime.attach_surface(_Surface()).outcome is OperationOutcome.APPLIED

    observer = _Observer()
    assert discovery.start(observer).outcome is OperationOutcome.APPLIED
    rig.appear_target(_contract_target())
    assert discovery.snapshot().available is True
    assert observer.snapshots[-1] == discovery.snapshot()

    presentation_revision = presentation.presentation_snapshot().state_revision
    input_revision = input_policy.input_snapshot().state_revision
    assert (
        presentation.present(_contract_intent(), FrameSnapshot(available=True, revision=3)).outcome
        is OperationOutcome.APPLIED
    )
    assert presentation.presentation_snapshot().visible is True
    assert presentation.presentation_snapshot().state_revision > presentation_revision
    assert input_policy.input_snapshot().state_revision == input_revision
    assert input_policy.apply(_contract_interaction(interactive=True)).outcome is OperationOutcome.APPLIED
    assert input_policy.input_snapshot().state_revision > input_revision

    status = runtime.status_snapshot()
    assert status.selected_runtime == identity
    assert status.support.policy is SupportPolicy.SUPPORTED
    assert status.support.evidence_level is EvidenceLevel.NOT_YET_REPORTED
    assert status.health.state is RuntimeHealth.HEALTHY
    assert deserialize_backend_envelope(serialize_backend_envelope(status)).require_envelope() == status

    rig.lose_target()
    assert discovery.snapshot().available is False
    assert presentation.presentation_snapshot().visible is False
    first_stop = rig.lose_owner()
    second_stop = runtime.stop(StopReason.REQUESTED)
    assert first_stop == second_stop
    assert runtime.lifecycle_snapshot().state is LifecycleState.STOPPED
    assert runtime.start().outcome is OperationOutcome.REJECTED
    assert all(count == 1 for count in rig.cleanup_counts.values())

    partial = factory.create(start_failure_after="presentation")
    assert partial.runtime.start().outcome is OperationOutcome.UNAVAILABLE
    assert partial.cleanup_order == ["presentation", "discovery"]
    assert partial.runtime.lifecycle_snapshot().state is LifecycleState.START_FAILED


def _contract_target() -> TargetSnapshot:
    return TargetSnapshot(
        identity=TargetIdentity(application_id="contract-app", instance_id="primary"),
        available=True,
        target_rect=NormalizedRect(x=0, y=0, width=1920, height=1080),
        monitor_id="monitor-primary",
        monitor_rect=NormalizedRect(x=0, y=0, width=1920, height=1080),
        coordinate_space=CoordinateSpace(identifier="desktop-logical", scale=1.0, revision=1),
        scale_revision=1,
        display_mode=DisplayMode.WINDOWED,
        state_revision=1,
    )


def _contract_interaction(*, interactive: bool = False) -> InteractionIntent:
    return InteractionIntent(
        interactive=interactive,
        click_through=not interactive,
        focus_accepting=interactive,
        revision=2,
    )


def _contract_intent() -> PresentationIntent:
    target = _contract_target()
    return PresentationIntent(
        requested_mode=DisplayMode.WINDOWED,
        target_identity=target.identity,
        target_rect=target.target_rect,
        monitor_id=target.monitor_id,
        monitor_rect=target.monitor_rect,
        coordinate_space=target.coordinate_space,
        target_revision=target.state_revision,
        monitor_revision=1,
        scale_revision=target.scale_revision,
        requested_visible=True,
        frame_available=True,
        frame_revision=3,
        interaction=_contract_interaction(),
    )


def _missing_target(revision: int) -> TargetSnapshot:
    return TargetSnapshot(
        identity=None,
        available=False,
        target_rect=None,
        monitor_id=None,
        monitor_rect=None,
        coordinate_space=None,
        scale_revision=0,
        display_mode=DisplayMode.HIDDEN,
        state_revision=revision,
    )


def _paper_helper_summary(snapshot: HelperHealthSnapshot | None) -> HelperSummary | None:
    if snapshot is None:
        return None
    return HelperSummary(
        required=snapshot.required,
        available=snapshot.available,
        compatible=snapshot.compatible,
        owned=snapshot.ownership is HelperOwnershipState.OWNED,
        health=snapshot.health,
        recovery=snapshot.recovery,
        reason_code=snapshot.reason_code,
        diagnostics=snapshot.diagnostics,
    )
