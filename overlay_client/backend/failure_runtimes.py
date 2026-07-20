"""Generic fail-closed runtimes for known-unavailable and unimplemented backends."""

from __future__ import annotations

import re
import time
from collections.abc import Callable, Sequence

from .control_plane_models import (
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
    ProducerInfo,
    RecoveryClass,
    RuntimeHealth,
    SelectionSummary,
    SupportPolicy,
    SupportSummary,
)
from .runtime_contracts import (
    DisplayMode,
    FrameSnapshot,
    HelperHealthSnapshot,
    HelperOwnershipState,
    HideReason,
    InputPolicySnapshot,
    InteractionIntent,
    LifecycleSnapshot,
    LifecycleState,
    OverlaySurface,
    PresentationIntent,
    PresentationSnapshot,
    StopReason,
    TargetObserver,
    TargetSnapshot,
)


_NORMALIZED_CODE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
_DEFAULT_CLEANUP_TIMEOUT_MS = 100


class _InertDiscovery:
    def __init__(self, owner: _FailureRuntime) -> None:
        self._owner = owner
        self._revision = 0
        self._stopped = False
        self._snapshot = _missing_target(self._revision)

    def start(self, observer: TargetObserver) -> OperationResult:
        del observer
        if self._stopped:
            return self._owner._rejected("discovery_stopped", self._revision)
        return self._owner._unavailable("discovery_unavailable", self._revision)

    def snapshot(self) -> TargetSnapshot:
        return self._snapshot

    def stop(self) -> OperationResult:
        if not self._stopped:
            self._stopped = True
            self._revision += 1
            self._snapshot = _missing_target(self._revision)
            self._owner._changed()
        return self._owner._applied("discovery_stopped", self._revision)


class _InertPresentation:
    def __init__(self, owner: _FailureRuntime) -> None:
        self._owner = owner
        self._revision = 0
        self._stopped = False
        self._snapshot = self._make_snapshot(OperationOutcome.UNAVAILABLE, owner.reason_code)

    def present(self, intent: PresentationIntent, frame: FrameSnapshot | None) -> OperationResult:
        del intent, frame
        if self._stopped:
            return self._owner._rejected("presentation_stopped", self._revision)
        self._revision += 1
        self._snapshot = self._make_snapshot(OperationOutcome.UNAVAILABLE, self._owner.reason_code)
        self._owner._changed()
        return self._owner._unavailable(self._owner.reason_code, self._revision)

    def hide(self, reason: HideReason) -> OperationResult:
        if not isinstance(reason, HideReason):
            raise TypeError("reason must be HideReason")
        if not self._stopped:
            self._revision += 1
            self._snapshot = self._make_snapshot(OperationOutcome.HIDDEN, reason.value)
            self._owner._changed()
        return OperationResult(
            outcome=OperationOutcome.HIDDEN,
            reason_code=reason.value,
            health=self._owner.health,
            recovery=self._owner.recovery,
            state_revision=self._revision,
        )

    def presentation_snapshot(self) -> PresentationSnapshot:
        return self._snapshot

    def stop(self) -> OperationResult:
        if not self._stopped:
            self.hide(HideReason.RUNTIME_STOPPING)
            self._stopped = True
        return self._owner._applied("presentation_stopped", self._revision)

    def _make_snapshot(self, outcome: OperationOutcome, reason_code: str) -> PresentationSnapshot:
        return PresentationSnapshot(
            outcome=outcome,
            reason_code=reason_code,
            health=self._owner.health,
            recovery=self._owner.recovery,
            state_revision=self._revision,
            requested_mode=DisplayMode.HIDDEN,
            visible=False,
            frame_revision=None,
            presenter_label="",
        )


class _InertInputPolicy:
    def __init__(self, owner: _FailureRuntime) -> None:
        self._owner = owner
        self._revision = 0
        self._stopped = False
        self._snapshot = self._make_snapshot(OperationOutcome.UNAVAILABLE, owner.reason_code)

    def apply(self, intent: InteractionIntent) -> OperationResult:
        if not isinstance(intent, InteractionIntent):
            raise TypeError("intent must be InteractionIntent")
        if self._stopped:
            return self._owner._rejected("input_policy_stopped", self._revision)
        self._revision += 1
        self._snapshot = self._make_snapshot(OperationOutcome.UNAVAILABLE, self._owner.reason_code)
        self._owner._changed()
        return self._owner._unavailable(self._owner.reason_code, self._revision)

    def input_snapshot(self) -> InputPolicySnapshot:
        return self._snapshot

    def stop(self) -> OperationResult:
        if not self._stopped:
            self._stopped = True
            self._revision += 1
            self._snapshot = self._make_snapshot(OperationOutcome.UNAVAILABLE, "input_policy_stopped")
            self._owner._changed()
        return self._owner._applied("input_policy_stopped", self._revision)

    def _make_snapshot(self, outcome: OperationOutcome, reason_code: str) -> InputPolicySnapshot:
        return InputPolicySnapshot(
            outcome=outcome,
            reason_code=reason_code,
            health=self._owner.health,
            recovery=self._owner.recovery,
            state_revision=self._revision,
            interactive=False,
            click_through=True,
            focus_accepting=False,
        )


class _InertHelperLifecycle:
    def __init__(self, owner: _FailureRuntime) -> None:
        self._owner = owner
        self._revision = 0
        self._released = False

    def acquire(self) -> OperationResult:
        if self._released:
            return self._owner._rejected("helper_released", self._revision)
        return self._owner._unavailable(self._owner.reason_code, self._revision)

    def renew(self) -> OperationResult:
        if self._released:
            return self._owner._rejected("helper_released", self._revision)
        return self._owner._unavailable(self._owner.reason_code, self._revision)

    def health(self) -> HelperHealthSnapshot:
        return HelperHealthSnapshot(
            required=True,
            available=False,
            compatible=False,
            ownership=HelperOwnershipState.UNOWNED,
            health=self._owner.health,
            recovery=self._owner.recovery,
            reason_code=self._owner.reason_code,
            state_revision=self._revision,
        )

    def release(self) -> OperationResult:
        if not self._released:
            self._released = True
            self._revision += 1
            self._owner._changed()
        return self._owner._applied("helper_released", self._revision)


class _FailureRuntime:
    """Shared lifecycle-safe implementation for inert failure runtimes."""

    def __init__(
        self,
        *,
        identity: BackendIdentity,
        support: SupportSummary,
        reason_code: str,
        recovery: RecoveryClass,
        producer: ProducerInfo | None,
        health: RuntimeHealth,
        probes: Sequence[CapabilityProbe],
        helper_required: bool,
        monotonic: Callable[[], float],
        cleanup_timeout_ms: int,
        cleanup_actions: Sequence[tuple[str, Callable[[], None]]],
    ) -> None:
        if not isinstance(identity, BackendIdentity):
            raise TypeError("identity must be BackendIdentity")
        if not isinstance(support, SupportSummary):
            raise TypeError("support must be SupportSummary")
        _require_code(reason_code, "reason_code")
        if not isinstance(recovery, RecoveryClass):
            raise TypeError("recovery must be RecoveryClass")
        if health not in (RuntimeHealth.UNAVAILABLE, RuntimeHealth.INCOMPATIBLE):
            raise ValueError("failure runtime health must be unavailable or incompatible")
        if isinstance(cleanup_timeout_ms, bool) or not isinstance(cleanup_timeout_ms, int):
            raise TypeError("cleanup_timeout_ms must be an integer")
        if cleanup_timeout_ms < 0:
            raise ValueError("cleanup_timeout_ms must be non-negative")

        self._identity = identity
        self._support = support
        self.reason_code = reason_code
        self.recovery = recovery
        self.health = health
        self._producer = producer or ProducerInfo(component="overlay_client", version="")
        self._probes = tuple(probes)
        if any(not isinstance(probe, CapabilityProbe) for probe in self._probes):
            raise TypeError("probes must contain CapabilityProbe records")
        self._monotonic = monotonic
        self._cleanup_timeout_ms = cleanup_timeout_ms
        self._cleanup_actions = tuple((_safe_component(name), action) for name, action in cleanup_actions)
        if any(not callable(action) for _, action in self._cleanup_actions):
            raise TypeError("cleanup actions must be callable")

        self._status_revision = 0
        self._lifecycle_revision = 0
        self._lifecycle_state = LifecycleState.CONSTRUCTED
        self._start_attempted = False
        self._stop_requested = False
        self._cleanup_elapsed_ms = 0
        self._recent_failures: list[NormalizedFailure] = []
        self._stop_result: OperationResult | None = None

        self._discovery = _InertDiscovery(self)
        self._presentation = _InertPresentation(self)
        self._input_policy = _InertInputPolicy(self)
        self._helper_lifecycle = _InertHelperLifecycle(self) if helper_required else None

    @property
    def identity(self) -> BackendIdentity:
        return self._identity

    @property
    def discovery(self) -> _InertDiscovery:
        return self._discovery

    @property
    def presentation(self) -> _InertPresentation:
        return self._presentation

    @property
    def input_policy(self) -> _InertInputPolicy:
        return self._input_policy

    @property
    def helper_lifecycle(self) -> _InertHelperLifecycle | None:
        return self._helper_lifecycle

    def start(self) -> OperationResult:
        if self._lifecycle_state is LifecycleState.STOPPED:
            return self._rejected("runtime_stopped", self._lifecycle_revision, health=RuntimeHealth.STOPPED)
        if self._start_attempted:
            return self._rejected("runtime_start_already_attempted", self._lifecycle_revision)
        self._start_attempted = True
        self._lifecycle_state = LifecycleState.START_FAILED
        self._lifecycle_revision += 1
        self._changed()
        return self._unavailable(self.reason_code, self._lifecycle_revision)

    def attach_surface(self, surface: OverlaySurface) -> OperationResult:
        if not isinstance(surface, OverlaySurface):
            raise TypeError("surface must satisfy OverlaySurface")
        if self._lifecycle_state is LifecycleState.STOPPED:
            return self._rejected("runtime_stopped", self._lifecycle_revision, health=RuntimeHealth.STOPPED)
        return self._unavailable("surface_attachment_unavailable", self._lifecycle_revision)

    def status_snapshot(self) -> BackendControlPlaneEnvelope:
        presentation = self._presentation.presentation_snapshot()
        input_state = self._input_policy.input_snapshot()
        helper = self._helper_lifecycle.health() if self._helper_lifecycle is not None else None
        stopped = self._lifecycle_state is LifecycleState.STOPPED
        health = RuntimeHealth.STOPPED if stopped else self.health
        recovery = RecoveryClass.TERMINAL if stopped else self.recovery
        reason_code = "runtime_stopped" if stopped else self.reason_code
        return BackendControlPlaneEnvelope(
            schema_version=BACKEND_CONTROL_PLANE_SCHEMA_VERSION,
            producer=self._producer,
            revision=self._status_revision,
            selected_runtime=self._identity,
            selection=SelectionSummary(
                mode="automatic",
                restart_required=not stopped and self.recovery is RecoveryClass.RESTART_REQUIRED,
                inputs_revision=0,
            ),
            support=self._support,
            health=HealthSummary(state=health, reason_code=reason_code, recovery=recovery),
            probes=self._probes,
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
            helper=_helper_summary(helper),
            ownership=OwnershipSummary(
                connected=False,
                state="not_attached",
                reason_code="owner_not_attached",
                age_ms=0,
            ),
            lifecycle=LifecycleSummary(
                state=self._lifecycle_state.value,
                state_revision=self._lifecycle_revision,
                age_ms=0,
                restart_required=not stopped and self.recovery is RecoveryClass.RESTART_REQUIRED,
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
        self._presentation.stop()
        self._input_policy.stop()
        self._discovery.stop()
        if self._helper_lifecycle is not None:
            self._helper_lifecycle.release()
        self._run_cleanup()
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

    def _run_cleanup(self) -> None:
        started = self._monotonic()
        for name, action in reversed(self._cleanup_actions):
            elapsed_ms = max(0, round((self._monotonic() - started) * 1000))
            if elapsed_ms >= self._cleanup_timeout_ms:
                self._record_failure(
                    failure_code="cleanup_deadline_exceeded",
                    component=name,
                    details={"elapsed_ms": elapsed_ms},
                )
                break
            try:
                action()
            except Exception as exc:  # noqa: BLE001 - normalized at this boundary
                self._record_failure(
                    failure_code="cleanup_failed",
                    component=name,
                    details={"exception": str(exc)},
                )
        elapsed_ms = max(0, round((self._monotonic() - started) * 1000))
        self._cleanup_elapsed_ms = min(elapsed_ms, self._cleanup_timeout_ms)

    def _record_failure(self, *, failure_code: str, component: str, details: dict[str, object]) -> None:
        self._recent_failures.append(
            NormalizedFailure(
                failure_code=failure_code,
                component=component,
                health=self.health,
                recovery=self.recovery,
                state_revision=self._status_revision,
                age_ms=0,
                details=details,
            )
        )
        self._changed()

    def _changed(self) -> None:
        self._status_revision += 1

    def _unavailable(self, reason_code: str, revision: int) -> OperationResult:
        return OperationResult(
            outcome=OperationOutcome.UNAVAILABLE,
            reason_code=reason_code,
            health=self.health,
            recovery=self.recovery,
            state_revision=revision,
        )

    def _rejected(
        self,
        reason_code: str,
        revision: int,
        *,
        health: RuntimeHealth | None = None,
    ) -> OperationResult:
        return OperationResult(
            outcome=OperationOutcome.REJECTED,
            reason_code=reason_code,
            health=health or self.health,
            recovery=RecoveryClass.TERMINAL if health is RuntimeHealth.STOPPED else self.recovery,
            state_revision=revision,
        )

    def _applied(self, reason_code: str, revision: int) -> OperationResult:
        return OperationResult(
            outcome=OperationOutcome.APPLIED,
            reason_code=reason_code,
            health=RuntimeHealth.STOPPED if self._lifecycle_state is LifecycleState.STOPPED else self.health,
            recovery=RecoveryClass.TERMINAL if self._lifecycle_state is LifecycleState.STOPPED else self.recovery,
            state_revision=revision,
        )


class UnavailableBackendRuntime(_FailureRuntime):
    """Known selected runtime whose construction prerequisite is unavailable."""

    def __init__(
        self,
        *,
        identity: BackendIdentity,
        support: SupportSummary,
        reason_code: str,
        recovery: RecoveryClass,
        producer: ProducerInfo | None = None,
        health: RuntimeHealth = RuntimeHealth.UNAVAILABLE,
        probes: Sequence[CapabilityProbe] = (),
        helper_required: bool = False,
        monotonic: Callable[[], float] = time.monotonic,
        cleanup_timeout_ms: int = _DEFAULT_CLEANUP_TIMEOUT_MS,
        cleanup_actions: Sequence[tuple[str, Callable[[], None]]] = (),
    ) -> None:
        super().__init__(
            identity=identity,
            support=support,
            reason_code=reason_code,
            recovery=recovery,
            producer=producer,
            health=health,
            probes=probes,
            helper_required=helper_required,
            monotonic=monotonic,
            cleanup_timeout_ms=cleanup_timeout_ms,
            cleanup_actions=cleanup_actions,
        )


class UnimplementedBackendRuntime(_FailureRuntime):
    """Detected environment with no implemented backend behavior."""

    def __init__(
        self,
        *,
        identity: BackendIdentity,
        environment_key: str,
        reason_code: str = "backend_not_implemented",
        producer: ProducerInfo | None = None,
        probes: Sequence[CapabilityProbe] = (),
        monotonic: Callable[[], float] = time.monotonic,
        cleanup_timeout_ms: int = _DEFAULT_CLEANUP_TIMEOUT_MS,
        cleanup_actions: Sequence[tuple[str, Callable[[], None]]] = (),
    ) -> None:
        support = SupportSummary(
            policy=SupportPolicy.UNIMPLEMENTED,
            environment_key=environment_key,
            evidence_level=EvidenceLevel.NOT_APPLICABLE,
            evidence_record="",
            last_reviewed_release="",
        )
        super().__init__(
            identity=identity,
            support=support,
            reason_code=reason_code,
            recovery=RecoveryClass.TERMINAL,
            producer=producer,
            health=RuntimeHealth.UNAVAILABLE,
            probes=probes,
            helper_required=False,
            monotonic=monotonic,
            cleanup_timeout_ms=cleanup_timeout_ms,
            cleanup_actions=cleanup_actions,
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


def _helper_summary(snapshot: HelperHealthSnapshot | None) -> HelperSummary | None:
    if snapshot is None:
        return None
    owned: bool | None
    if snapshot.ownership is HelperOwnershipState.NOT_APPLICABLE:
        owned = None
    else:
        owned = snapshot.ownership is HelperOwnershipState.OWNED
    return HelperSummary(
        required=snapshot.required,
        available=snapshot.available,
        compatible=snapshot.compatible,
        owned=owned,
        health=snapshot.health,
        recovery=snapshot.recovery,
        reason_code=snapshot.reason_code,
        diagnostics=snapshot.diagnostics,
    )


def _require_code(value: object, name: str) -> str:
    if not isinstance(value, str) or _NORMALIZED_CODE.fullmatch(value) is None:
        raise ValueError(f"{name} must be a normalized code")
    return value


def _safe_component(value: object) -> str:
    if isinstance(value, str) and _NORMALIZED_CODE.fullmatch(value) is not None:
        return value
    return "cleanup_resource"
