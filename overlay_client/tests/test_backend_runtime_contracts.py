from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from overlay_client.backend import (
    BackendIdentity,
    DisplayMode,
    EvidenceLevel,
    OperationOutcome,
    ProducerInfo,
    RecoveryClass,
    RuntimeHealth,
    SupportPolicy,
    SupportSummary,
    deserialize_backend_envelope,
    serialize_backend_envelope,
)
from overlay_client.backend.failure_runtimes import UnavailableBackendRuntime, UnimplementedBackendRuntime
from overlay_client.backend.runtime_contracts import (
    BackendRuntime,
    CoordinateSpace,
    DiscoveryService,
    FrameSnapshot,
    HelperHealthSnapshot,
    HelperLifecycle,
    HelperOwnershipState,
    HideReason,
    InputPolicyService,
    InputPolicySnapshot,
    InteractionIntent,
    LifecycleSnapshot,
    LifecycleState,
    NormalizedRect,
    OverlaySurface,
    PresentationIntent,
    PresentationService,
    PresentationSnapshot,
    StopReason,
    TargetIdentity,
    TargetObserver,
    TargetSnapshot,
)
from overlay_client.tests.backend_runtime_testkit import (
    BackendRuntimeTestFactory,
    PaperBackendFactory,
    assert_backend_runtime_contract,
)


class _Observer:
    def __init__(self) -> None:
        self.snapshots: list[TargetSnapshot] = []

    def target_changed(self, snapshot: TargetSnapshot) -> None:
        self.snapshots.append(snapshot)


class _Surface:
    @property
    def surface_id(self) -> str:
        return "overlay-surface"


class _DiscoveryStub:
    def start(self, observer: TargetObserver):
        del observer
        return _result()

    def snapshot(self) -> TargetSnapshot:
        return _missing_target()

    def stop(self):
        return _result()


class _PresentationStub:
    def present(self, intent: PresentationIntent, frame: FrameSnapshot | None):
        del intent, frame
        return _result()

    def hide(self, reason: HideReason):
        del reason
        return _result(outcome=OperationOutcome.HIDDEN)

    def presentation_snapshot(self) -> PresentationSnapshot:
        return _presentation_snapshot()

    def stop(self):
        return _result()


class _InputStub:
    def apply(self, intent: InteractionIntent):
        del intent
        return _result()

    def input_snapshot(self) -> InputPolicySnapshot:
        return _input_snapshot()

    def stop(self):
        return _result()


class _CombinedPresentationInputStub(_PresentationStub, _InputStub):
    pass


class _HelperStub:
    def acquire(self):
        return _result()

    def renew(self):
        return _result()

    def health(self) -> HelperHealthSnapshot:
        return _helper_snapshot()

    def release(self):
        return _result()


class _RuntimeStub:
    def __init__(self, *, combined: bool) -> None:
        self._identity = BackendIdentity(family="test", instance="structural_stub")
        self._discovery = _DiscoveryStub()
        if combined:
            shared = _CombinedPresentationInputStub()
            self._presentation = shared
            self._input_policy = shared
        else:
            self._presentation = _PresentationStub()
            self._input_policy = _InputStub()
        self._helper_lifecycle = _HelperStub()

    @property
    def identity(self) -> BackendIdentity:
        return self._identity

    @property
    def discovery(self) -> DiscoveryService:
        return self._discovery

    @property
    def presentation(self) -> PresentationService:
        return self._presentation

    @property
    def input_policy(self) -> InputPolicyService:
        return self._input_policy

    @property
    def helper_lifecycle(self) -> HelperLifecycle | None:
        return self._helper_lifecycle

    def start(self):
        return _result()

    def attach_surface(self, surface: OverlaySurface):
        del surface
        return _result()

    def status_snapshot(self):
        raise NotImplementedError

    def lifecycle_snapshot(self) -> LifecycleSnapshot:
        return _lifecycle_snapshot()

    def stop(self, reason: StopReason):
        del reason
        return _result()


class _Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance_ms(self, milliseconds: int) -> None:
        self.now += milliseconds / 1000.0


def _result(*, outcome: OperationOutcome = OperationOutcome.APPLIED, revision: int = 0):
    from overlay_client.backend import OperationResult

    return OperationResult(
        outcome=outcome,
        reason_code="test_result",
        health=RuntimeHealth.HEALTHY,
        recovery=RecoveryClass.AUTOMATIC,
        state_revision=revision,
    )


def _support(
    *,
    policy: SupportPolicy = SupportPolicy.SUPPORTED,
    evidence: EvidenceLevel = EvidenceLevel.FULL_MATRIX,
) -> SupportSummary:
    return SupportSummary(
        policy=policy,
        environment_key="linux|ubuntu|24.04.4|wayland|gnome|mutter|46|windowed",
        evidence_level=evidence,
        evidence_record="ubuntu-24.04.4-gnome-46",
        last_reviewed_release="0.9.0",
    )


def _coordinate_space() -> CoordinateSpace:
    return CoordinateSpace(identifier="desktop-logical", scale=1.25, revision=3)


def _target() -> TargetSnapshot:
    return TargetSnapshot(
        identity=TargetIdentity(application_id="elite-dangerous", instance_id="primary"),
        available=True,
        target_rect=NormalizedRect(x=-1920, y=0, width=1920, height=1080),
        monitor_id="monitor-left",
        monitor_rect=NormalizedRect(x=-1920, y=0, width=1920, height=1080),
        coordinate_space=_coordinate_space(),
        scale_revision=4,
        display_mode=DisplayMode.WINDOWED,
        state_revision=5,
    )


def _missing_target(*, revision: int = 0) -> TargetSnapshot:
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


def _interaction(*, revision: int = 2, interactive: bool = False) -> InteractionIntent:
    return InteractionIntent(
        interactive=interactive,
        click_through=not interactive,
        focus_accepting=interactive,
        revision=revision,
    )


def _presentation_intent(
    *,
    mode: DisplayMode = DisplayMode.WINDOWED,
    visible: bool = True,
    interaction: InteractionIntent | None = None,
) -> PresentationIntent:
    target = _target()
    return PresentationIntent(
        requested_mode=mode,
        target_identity=target.identity,
        target_rect=target.target_rect,
        monitor_id=target.monitor_id,
        monitor_rect=target.monitor_rect,
        coordinate_space=target.coordinate_space,
        target_revision=target.state_revision,
        monitor_revision=7,
        scale_revision=target.scale_revision,
        requested_visible=visible,
        frame_available=True,
        frame_revision=11,
        interaction=interaction or _interaction(),
    )


def _presentation_snapshot() -> PresentationSnapshot:
    return PresentationSnapshot(
        outcome=OperationOutcome.HIDDEN,
        reason_code="not_presented",
        health=RuntimeHealth.HEALTHY,
        recovery=RecoveryClass.AUTOMATIC,
        state_revision=0,
        requested_mode=DisplayMode.HIDDEN,
        visible=False,
        frame_revision=None,
        presenter_label="",
    )


def _input_snapshot() -> InputPolicySnapshot:
    return InputPolicySnapshot(
        outcome=OperationOutcome.APPLIED,
        reason_code="input_ready",
        health=RuntimeHealth.HEALTHY,
        recovery=RecoveryClass.AUTOMATIC,
        state_revision=0,
        interactive=False,
        click_through=True,
        focus_accepting=False,
    )


def _helper_snapshot() -> HelperHealthSnapshot:
    return HelperHealthSnapshot(
        required=False,
        available=True,
        compatible=True,
        ownership=HelperOwnershipState.NOT_APPLICABLE,
        health=RuntimeHealth.HEALTHY,
        recovery=RecoveryClass.AUTOMATIC,
        reason_code="helper_not_required",
        state_revision=0,
    )


def _lifecycle_snapshot() -> LifecycleSnapshot:
    return LifecycleSnapshot(
        state=LifecycleState.CONSTRUCTED,
        state_revision=0,
        start_attempted=False,
        stop_requested=False,
        cleanup_elapsed_ms=0,
        restart_allowed=True,
    )


def test_behavioral_protocols_are_runtime_checkable_with_independent_services():
    runtime = _RuntimeStub(combined=False)

    assert isinstance(runtime, BackendRuntime)
    assert isinstance(runtime.discovery, DiscoveryService)
    assert isinstance(runtime.presentation, PresentationService)
    assert isinstance(runtime.input_policy, InputPolicyService)
    assert isinstance(runtime.helper_lifecycle, HelperLifecycle)
    assert isinstance(_Observer(), TargetObserver)
    assert isinstance(_Surface(), OverlaySurface)
    assert runtime.presentation is not runtime.input_policy


def test_combined_presentation_input_object_conforms_without_becoming_a_requirement():
    independent = _RuntimeStub(combined=False)
    combined = _RuntimeStub(combined=True)

    assert isinstance(combined, BackendRuntime)
    assert isinstance(combined.presentation, PresentationService)
    assert isinstance(combined.input_policy, InputPolicyService)
    assert combined.presentation is combined.input_policy
    assert independent.presentation is not independent.input_policy
    assert isinstance(combined.presentation.presentation_snapshot(), PresentationSnapshot)
    assert isinstance(combined.input_policy.input_snapshot(), InputPolicySnapshot)


def test_normalized_contract_values_are_immutable_and_compare_by_value():
    target = _target()
    frame = FrameSnapshot(available=True, revision=11)
    intent = _presentation_intent()

    assert target == _target()
    assert frame == FrameSnapshot(available=True, revision=11)
    assert intent == _presentation_intent()
    with pytest.raises(FrozenInstanceError):
        target.available = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        intent.requested_visible = False  # type: ignore[misc]


@pytest.mark.parametrize(
    ("factory", "match"),
    [
        (lambda: NormalizedRect(0, 0, -1, 1), "width"),
        (lambda: CoordinateSpace("desktop", 0.0, 0), "scale"),
        (lambda: FrameSnapshot(True, -1), "revision"),
        (lambda: _interaction(revision=-1), "revision"),
        (lambda: _presentation_intent(mode=DisplayMode.HIDDEN, visible=True), "hidden"),
    ],
)
def test_normalized_contract_values_reject_invalid_state(factory, match):
    with pytest.raises((TypeError, ValueError), match=match):
        factory()


def test_contract_module_excludes_backend_private_and_gui_vocabulary():
    import overlay_client.backend.runtime_contracts as contracts_module

    source = inspect.getsource(contracts_module).casefold()
    prohibited = (
        "managed_pyqt",
        "shell_raster",
        "gnome",
        "dbus",
        "overview",
        "helper_token",
        "target_handle",
        "pyqt",
        "tkinter",
    )

    assert not any(term in source for term in prohibited)


def test_unavailable_runtime_preserves_selected_identity_and_independent_status_axes():
    identity = BackendIdentity(family="compositor_helper", instance="gnome_shell_wayland")
    runtime = UnavailableBackendRuntime(
        identity=identity,
        support=_support(),
        reason_code="required_helper_missing",
        recovery=RecoveryClass.RESTART_REQUIRED,
        producer=ProducerInfo(component="overlay_client", version="test"),
        helper_required=True,
    )

    status = runtime.status_snapshot()

    assert runtime.identity is identity
    assert status.selected_runtime == identity
    assert status.support.policy is SupportPolicy.SUPPORTED
    assert status.support.evidence_level is EvidenceLevel.FULL_MATRIX
    assert status.health.state is RuntimeHealth.UNAVAILABLE
    assert status.health.recovery is RecoveryClass.RESTART_REQUIRED
    assert status.selection.restart_required is True
    assert status.helper is not None
    assert status.helper.required is True


def test_unavailable_runtime_services_are_stable_independent_and_fail_closed():
    runtime = UnavailableBackendRuntime(
        identity=BackendIdentity(family="compositor_helper", instance="gnome_shell_wayland"),
        support=_support(),
        reason_code="required_helper_missing",
        recovery=RecoveryClass.RESTART_REQUIRED,
    )

    assert runtime.discovery is runtime.discovery
    assert runtime.presentation is runtime.presentation
    assert runtime.input_policy is runtime.input_policy
    assert runtime.presentation is not runtime.input_policy

    result = runtime.presentation.present(_presentation_intent(), FrameSnapshot(True, 11))
    snapshot = runtime.presentation.presentation_snapshot()

    assert result.outcome is OperationOutcome.UNAVAILABLE
    assert result.recovery is RecoveryClass.RESTART_REQUIRED
    assert snapshot.visible is False
    assert snapshot.outcome is OperationOutcome.UNAVAILABLE
    assert runtime.input_policy.apply(_interaction()).outcome is OperationOutcome.UNAVAILABLE


def test_unimplemented_runtime_is_terminal_and_never_claims_a_fallback():
    identity = BackendIdentity(family="native_wayland", instance="kwin_wayland")
    runtime = UnimplementedBackendRuntime(
        identity=identity,
        environment_key="linux|ubuntu|24.04.4|wayland|kde|kwin|6|windowed",
    )

    start = runtime.start()
    present = runtime.presentation.present(_presentation_intent(), FrameSnapshot(True, 11))
    status = runtime.status_snapshot()
    wire = serialize_backend_envelope(status)

    assert start.outcome is OperationOutcome.UNAVAILABLE
    assert start.recovery is RecoveryClass.TERMINAL
    assert present.outcome is OperationOutcome.UNAVAILABLE
    assert runtime.presentation.presentation_snapshot().visible is False
    assert status.selected_runtime == identity
    assert status.support.policy is SupportPolicy.UNIMPLEMENTED
    assert status.support.evidence_level is EvidenceLevel.NOT_APPLICABLE
    assert status.health.state is RuntimeHealth.UNAVAILABLE
    assert status.health.recovery is RecoveryClass.TERMINAL
    assert "fallback" not in wire.casefold()


@pytest.mark.parametrize("start_first", [False, True])
def test_failure_runtime_stop_is_idempotent_terminal_and_prevents_restart(start_first):
    runtime = UnavailableBackendRuntime(
        identity=BackendIdentity(family="native_x11", instance="native_x11"),
        support=_support(),
        reason_code="required_capability_missing",
        recovery=RecoveryClass.RESTART_REQUIRED,
    )
    if start_first:
        runtime.start()

    first = runtime.stop(StopReason.REQUESTED)
    second = runtime.stop(StopReason.OWNER_LOST)
    restart = runtime.start()

    assert first == second
    assert first.health is RuntimeHealth.STOPPED
    assert restart.outcome is OperationOutcome.REJECTED
    assert restart.health is RuntimeHealth.STOPPED
    assert runtime.lifecycle_snapshot().state is LifecycleState.STOPPED
    assert runtime.lifecycle_snapshot().restart_allowed is False


def test_failure_runtime_attempts_start_once_and_reports_repeat_deterministically():
    runtime = UnavailableBackendRuntime(
        identity=BackendIdentity(family="native_x11", instance="native_x11"),
        support=_support(),
        reason_code="required_capability_missing",
        recovery=RecoveryClass.RESTART_REQUIRED,
    )

    first = runtime.start()
    second = runtime.start()

    assert first.outcome is OperationOutcome.UNAVAILABLE
    assert second.outcome is OperationOutcome.REJECTED
    assert second.reason_code == "runtime_start_already_attempted"
    assert runtime.lifecycle_snapshot().start_attempted is True


def test_failure_runtime_cleanup_is_deadline_aware_continues_after_failure_and_sanitizes():
    clock = _Clock()
    calls: list[str] = []

    def release_first() -> None:
        calls.append("first")
        clock.advance_ms(4)
        raise RuntimeError("token=secret-value /home/alice/private owner_id=raw-owner")

    def release_second() -> None:
        calls.append("second")
        clock.advance_ms(7)

    def release_third() -> None:
        calls.append("third")

    runtime = UnavailableBackendRuntime(
        identity=BackendIdentity(family="native_x11", instance="native_x11"),
        support=_support(),
        reason_code="required_capability_missing",
        recovery=RecoveryClass.RESTART_REQUIRED,
        monotonic=clock,
        cleanup_timeout_ms=10,
        cleanup_actions=(
            ("third", release_third),
            ("second", release_second),
            ("first", release_first),
        ),
    )

    runtime.stop(StopReason.START_FAILED)
    status = runtime.status_snapshot()
    wire = serialize_backend_envelope(status)

    assert calls == ["first", "second"]
    assert runtime.lifecycle_snapshot().cleanup_elapsed_ms == 10
    assert any(failure.failure_code == "cleanup_failed" for failure in status.recent_failures)
    assert any(failure.failure_code == "cleanup_deadline_exceeded" for failure in status.recent_failures)
    for prohibited in ("secret-value", "/home/alice/private", "raw-owner"):
        assert prohibited not in wire


def test_failure_runtime_status_round_trips_through_schema_version_one():
    runtime = UnavailableBackendRuntime(
        identity=BackendIdentity(family="compositor_helper", instance="gnome_shell_wayland"),
        support=_support(evidence=EvidenceLevel.COMMUNITY_CONFIRMED),
        reason_code="helper_protocol_incompatible",
        recovery=RecoveryClass.RESTART_REQUIRED,
        health=RuntimeHealth.INCOMPATIBLE,
    )

    decoded = deserialize_backend_envelope(serialize_backend_envelope(runtime.status_snapshot()))

    assert decoded.ok is True
    assert decoded.require_envelope() == runtime.status_snapshot()


def test_paper_factory_satisfies_reusable_test_factory_protocol():
    assert isinstance(PaperBackendFactory(), BackendRuntimeTestFactory)


def test_paper_backend_passes_reusable_runtime_contract_suite():
    assert_backend_runtime_contract(PaperBackendFactory())


def test_paper_backend_complete_deterministic_lifecycle_demo():
    rig = PaperBackendFactory().create()
    runtime = rig.runtime
    observer = _Observer()

    assert runtime.start().outcome is OperationOutcome.APPLIED
    assert runtime.discovery.start(observer).outcome is OperationOutcome.APPLIED
    rig.appear_target(_target())
    assert observer.snapshots[-1].available is True

    presentation_revision = runtime.presentation.presentation_snapshot().state_revision
    input_revision = runtime.input_policy.input_snapshot().state_revision
    assert (
        runtime.presentation.present(_presentation_intent(), FrameSnapshot(True, 11)).outcome
        is OperationOutcome.APPLIED
    )
    assert runtime.presentation.presentation_snapshot().visible is True
    assert runtime.presentation.presentation_snapshot().state_revision > presentation_revision
    assert runtime.input_policy.input_snapshot().state_revision == input_revision

    assert runtime.input_policy.apply(_interaction(interactive=True)).outcome is OperationOutcome.APPLIED
    assert runtime.input_policy.input_snapshot().interactive is True
    assert runtime.input_policy.input_snapshot().state_revision > input_revision

    owner_stop = rig.lose_owner()
    repeated_stop = runtime.stop(StopReason.OWNER_LOST)
    final_status = runtime.status_snapshot()
    decoded = deserialize_backend_envelope(serialize_backend_envelope(final_status))

    assert owner_stop == repeated_stop
    assert runtime.lifecycle_snapshot().state is LifecycleState.STOPPED
    assert runtime.presentation.presentation_snapshot().visible is False
    assert all(count == 1 for count in rig.cleanup_counts.values())
    assert decoded.require_envelope() == final_status


@pytest.mark.parametrize(
    ("outcome", "visible"),
    [
        (OperationOutcome.PENDING, False),
        (OperationOutcome.UNAVAILABLE, False),
    ],
)
def test_paper_backend_injects_presentation_outcomes_without_fallback(outcome, visible):
    rig = PaperBackendFactory().create()
    rig.runtime.start()
    rig.appear_target(_target())
    rig.next_presentation_outcome(outcome)

    result = rig.runtime.presentation.present(_presentation_intent(), FrameSnapshot(True, 11))

    assert result.outcome is outcome
    assert rig.runtime.presentation.presentation_snapshot().visible is visible
    assert "fallback" not in result.reason_code


def test_paper_backend_target_loss_hides_and_recovery_can_present_again():
    rig = PaperBackendFactory().create()
    rig.runtime.start()
    rig.appear_target(_target())
    rig.runtime.presentation.present(_presentation_intent(), FrameSnapshot(True, 11))

    rig.lose_target()
    hidden_revision = rig.runtime.presentation.presentation_snapshot().state_revision
    assert rig.runtime.discovery.snapshot().available is False
    assert rig.runtime.presentation.presentation_snapshot().visible is False

    rig.appear_target(_target())
    result = rig.runtime.presentation.present(_presentation_intent(), FrameSnapshot(True, 11))

    assert result.outcome is OperationOutcome.APPLIED
    assert rig.runtime.presentation.presentation_snapshot().state_revision > hidden_revision


def test_paper_backend_status_revision_is_stable_for_reads_and_monotonic_for_changes():
    rig = PaperBackendFactory().create()
    runtime = rig.runtime

    constructed = runtime.status_snapshot()
    assert runtime.status_snapshot().revision == constructed.revision
    runtime.start()
    started = runtime.status_snapshot()
    assert started.revision > constructed.revision
    assert runtime.status_snapshot().revision == started.revision
    rig.appear_target(_target())
    target_visible = runtime.status_snapshot()
    assert target_visible.revision > started.revision
    runtime.presentation.present(_presentation_intent(), FrameSnapshot(True, 11))
    presented = runtime.status_snapshot()
    assert presented.revision > target_visible.revision
    runtime.input_policy.apply(_interaction(interactive=True))
    input_changed = runtime.status_snapshot()
    assert input_changed.revision > presented.revision
    rig.lose_owner()
    assert runtime.status_snapshot().revision > input_changed.revision


def test_paper_backend_partial_start_cleans_acquired_resources_in_reverse_order():
    rig = PaperBackendFactory().create(start_failure_after="presentation")

    result = rig.runtime.start()

    assert result.outcome is OperationOutcome.UNAVAILABLE
    assert rig.cleanup_order == ["presentation", "discovery"]
    assert rig.cleanup_counts["presentation"] == 1
    assert rig.cleanup_counts["discovery"] == 1
    assert rig.cleanup_counts["input"] == 0
    assert rig.runtime.lifecycle_snapshot().state is LifecycleState.START_FAILED


def test_paper_backend_owner_loss_cleanup_is_bounded_and_secret_safe():
    rig = PaperBackendFactory().create(
        cleanup_failures={
            "input": "token=paper-secret /home/alice/private owner_id=paper-owner",
        },
        cleanup_delays_ms={"input": 4, "presentation": 7},
        cleanup_timeout_ms=10,
    )
    rig.runtime.start()

    rig.lose_owner()
    wire = serialize_backend_envelope(rig.runtime.status_snapshot())

    assert rig.cleanup_order == ["input", "presentation"]
    assert rig.cleanup_counts["input"] == 1
    assert rig.cleanup_counts["presentation"] == 1
    assert rig.cleanup_counts["discovery"] == 0
    assert any(failure.failure_code == "cleanup_failed" for failure in rig.runtime.status_snapshot().recent_failures)
    assert any(
        failure.failure_code == "cleanup_deadline_exceeded" for failure in rig.runtime.status_snapshot().recent_failures
    )
    assert rig.runtime.lifecycle_snapshot().cleanup_elapsed_ms == 10
    for prohibited in ("paper-secret", "/home/alice/private", "paper-owner"):
        assert prohibited not in wire


def test_paper_backend_helper_lifecycle_is_optional_normalized_and_stable():
    with_helper = PaperBackendFactory().create(include_helper=True)
    without_helper = PaperBackendFactory().create(include_helper=False)

    helper = with_helper.runtime.helper_lifecycle
    assert helper is not None
    assert helper is with_helper.runtime.helper_lifecycle
    assert helper.acquire().outcome is OperationOutcome.APPLIED
    assert helper.health().ownership is HelperOwnershipState.OWNED
    assert helper.renew().outcome is OperationOutcome.APPLIED
    assert helper.release().outcome is OperationOutcome.APPLIED
    assert helper.health().ownership is HelperOwnershipState.UNOWNED
    assert without_helper.runtime.helper_lifecycle is None


def test_paper_backend_is_not_imported_or_registered_by_production_modules():
    repo_root = Path(__file__).resolve().parents[2]
    production_paths = (
        repo_root / "overlay_client" / "launcher.py",
        repo_root / "overlay_client" / "backend" / "selector.py",
        repo_root / "overlay_client" / "backend" / "contracts.py",
        repo_root / "overlay_client" / "backend" / "consumers.py",
        repo_root / "overlay_client" / "backend" / "__init__.py",
    )

    for path in production_paths:
        source = path.read_text(encoding="utf-8").casefold()
        assert "paperbackend" not in source
        assert "backend_runtime_testkit" not in source
