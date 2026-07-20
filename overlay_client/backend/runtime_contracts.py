"""Pure behavior-oriented contracts for process-lifetime backend runtimes."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Protocol, runtime_checkable

from .control_plane_models import (
    BackendControlPlaneEnvelope,
    BackendIdentity,
    OperationOutcome,
    OperationResult,
    RecoveryClass,
    RuntimeHealth,
)


class DisplayMode(str, Enum):
    """Normalized presentation behavior requested by generic consumers."""

    WINDOWED = "windowed"
    BORDERLESS_FULLSCREEN = "borderless_fullscreen"
    HIDDEN = "hidden"


class HideReason(str, Enum):
    """Generic reasons for making presentation non-visible."""

    REQUESTED = "requested"
    TARGET_LOST = "target_lost"
    OWNER_LOST = "owner_lost"
    RUNTIME_STOPPING = "runtime_stopping"
    PRESENTATION_UNAVAILABLE = "presentation_unavailable"


class StopReason(str, Enum):
    """Generic terminal runtime stop reasons."""

    REQUESTED = "requested"
    OWNER_LOST = "owner_lost"
    START_FAILED = "start_failed"
    CONSTRUCTION_FAILED = "construction_failed"


class LifecycleState(str, Enum):
    """Observable process-lifetime runtime states."""

    CONSTRUCTED = "constructed"
    STARTING = "starting"
    RUNNING = "running"
    START_FAILED = "start_failed"
    STOPPING = "stopping"
    STOPPED = "stopped"


class HelperOwnershipState(str, Enum):
    """Normalized ownership state for an optional external helper."""

    NOT_APPLICABLE = "not_applicable"
    UNOWNED = "unowned"
    OWNED = "owned"
    CONFLICT = "conflict"


@dataclass(frozen=True, slots=True)
class NormalizedRect:
    """Rectangle in a named normalized coordinate space."""

    x: int
    y: int
    width: int
    height: int

    def __post_init__(self) -> None:
        for name in ("x", "y", "width", "height"):
            _require_int(getattr(self, name), name)
        if self.width < 0:
            raise ValueError("width must be non-negative")
        if self.height < 0:
            raise ValueError("height must be non-negative")


@dataclass(frozen=True, slots=True)
class CoordinateSpace:
    """Normalized coordinate-space identity, scale, and revision."""

    identifier: str
    scale: float
    revision: int

    def __post_init__(self) -> None:
        _require_text(self.identifier, "identifier")
        if isinstance(self.scale, bool) or not isinstance(self.scale, (int, float)):
            raise TypeError("scale must be a finite positive number")
        if not math.isfinite(float(self.scale)) or self.scale <= 0:
            raise ValueError("scale must be a finite positive number")
        _require_revision(self.revision, "revision")


@dataclass(frozen=True, slots=True)
class TargetIdentity:
    """Normalized target identity without backend-specific representation details."""

    application_id: str
    instance_id: str

    def __post_init__(self) -> None:
        _require_text(self.application_id, "application_id")
        _require_text(self.instance_id, "instance_id")


@dataclass(frozen=True, slots=True)
class TargetSnapshot:
    """Latest normalized target availability and geometry snapshot."""

    identity: TargetIdentity | None
    available: bool
    target_rect: NormalizedRect | None
    monitor_id: str | None
    monitor_rect: NormalizedRect | None
    coordinate_space: CoordinateSpace | None
    scale_revision: int
    display_mode: DisplayMode
    state_revision: int

    def __post_init__(self) -> None:
        _require_bool(self.available, "available")
        _require_revision(self.scale_revision, "scale_revision")
        _require_enum(self.display_mode, DisplayMode, "display_mode")
        _require_revision(self.state_revision, "state_revision")
        if self.monitor_id is not None:
            _require_text(self.monitor_id, "monitor_id")
        if self.identity is not None and not isinstance(self.identity, TargetIdentity):
            raise TypeError("identity must be TargetIdentity or None")
        if self.target_rect is not None and not isinstance(self.target_rect, NormalizedRect):
            raise TypeError("target_rect must be NormalizedRect or None")
        if self.monitor_rect is not None and not isinstance(self.monitor_rect, NormalizedRect):
            raise TypeError("monitor_rect must be NormalizedRect or None")
        if self.coordinate_space is not None and not isinstance(self.coordinate_space, CoordinateSpace):
            raise TypeError("coordinate_space must be CoordinateSpace or None")
        if self.available and any(
            value is None
            for value in (
                self.identity,
                self.target_rect,
                self.monitor_id,
                self.monitor_rect,
                self.coordinate_space,
            )
        ):
            raise ValueError("available target snapshots require identity and complete normalized geometry")


@dataclass(frozen=True, slots=True)
class FrameSnapshot:
    """Normalized frame availability and revision."""

    available: bool
    revision: int

    def __post_init__(self) -> None:
        _require_bool(self.available, "available")
        _require_revision(self.revision, "revision")


@dataclass(frozen=True, slots=True)
class InteractionIntent:
    """Requested click-through and focus behavior, independently revisioned."""

    interactive: bool
    click_through: bool
    focus_accepting: bool
    revision: int

    def __post_init__(self) -> None:
        _require_bool(self.interactive, "interactive")
        _require_bool(self.click_through, "click_through")
        _require_bool(self.focus_accepting, "focus_accepting")
        _require_revision(self.revision, "revision")


@dataclass(frozen=True, slots=True)
class PresentationIntent:
    """Requested presentation behavior expressed without implementation choices."""

    requested_mode: DisplayMode
    target_identity: TargetIdentity | None
    target_rect: NormalizedRect | None
    monitor_id: str | None
    monitor_rect: NormalizedRect | None
    coordinate_space: CoordinateSpace | None
    target_revision: int
    monitor_revision: int
    scale_revision: int
    requested_visible: bool
    frame_available: bool
    frame_revision: int
    interaction: InteractionIntent

    def __post_init__(self) -> None:
        _require_enum(self.requested_mode, DisplayMode, "requested_mode")
        _require_revision(self.target_revision, "target_revision")
        _require_revision(self.monitor_revision, "monitor_revision")
        _require_revision(self.scale_revision, "scale_revision")
        _require_bool(self.requested_visible, "requested_visible")
        _require_bool(self.frame_available, "frame_available")
        _require_revision(self.frame_revision, "frame_revision")
        if not isinstance(self.interaction, InteractionIntent):
            raise TypeError("interaction must be InteractionIntent")
        if self.monitor_id is not None:
            _require_text(self.monitor_id, "monitor_id")
        if self.target_identity is not None and not isinstance(self.target_identity, TargetIdentity):
            raise TypeError("target_identity must be TargetIdentity or None")
        if self.target_rect is not None and not isinstance(self.target_rect, NormalizedRect):
            raise TypeError("target_rect must be NormalizedRect or None")
        if self.monitor_rect is not None and not isinstance(self.monitor_rect, NormalizedRect):
            raise TypeError("monitor_rect must be NormalizedRect or None")
        if self.coordinate_space is not None and not isinstance(self.coordinate_space, CoordinateSpace):
            raise TypeError("coordinate_space must be CoordinateSpace or None")
        if self.requested_mode is DisplayMode.HIDDEN and self.requested_visible:
            raise ValueError("hidden presentation cannot request visibility")
        if self.requested_visible and any(
            value is None
            for value in (
                self.target_identity,
                self.target_rect,
                self.monitor_id,
                self.monitor_rect,
                self.coordinate_space,
            )
        ):
            raise ValueError("visible presentation requires target and monitor geometry")


@dataclass(frozen=True, slots=True)
class PresentationSnapshot:
    """Observable presentation state with its own revision."""

    outcome: OperationOutcome
    reason_code: str
    health: RuntimeHealth
    recovery: RecoveryClass
    state_revision: int
    requested_mode: DisplayMode
    visible: bool
    frame_revision: int | None
    presenter_label: str
    diagnostics: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_enum(self.requested_mode, DisplayMode, "requested_mode")
        _require_bool(self.visible, "visible")
        if self.frame_revision is not None:
            _require_revision(self.frame_revision, "frame_revision")
        _require_text(self.presenter_label, "presenter_label", allow_empty=True)
        operation = _validated_operation(
            outcome=self.outcome,
            reason_code=self.reason_code,
            health=self.health,
            recovery=self.recovery,
            state_revision=self.state_revision,
            diagnostics=self.diagnostics,
        )
        object.__setattr__(self, "diagnostics", operation.diagnostics)


@dataclass(frozen=True, slots=True)
class InputPolicySnapshot:
    """Observable input state with a revision independent of presentation."""

    outcome: OperationOutcome
    reason_code: str
    health: RuntimeHealth
    recovery: RecoveryClass
    state_revision: int
    interactive: bool
    click_through: bool
    focus_accepting: bool
    diagnostics: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_bool(self.interactive, "interactive")
        _require_bool(self.click_through, "click_through")
        _require_bool(self.focus_accepting, "focus_accepting")
        operation = _validated_operation(
            outcome=self.outcome,
            reason_code=self.reason_code,
            health=self.health,
            recovery=self.recovery,
            state_revision=self.state_revision,
            diagnostics=self.diagnostics,
        )
        object.__setattr__(self, "diagnostics", operation.diagnostics)


@dataclass(frozen=True, slots=True)
class HelperHealthSnapshot:
    """Normalized optional-helper availability, compatibility, and ownership state."""

    required: bool
    available: bool
    compatible: bool
    ownership: HelperOwnershipState
    health: RuntimeHealth
    recovery: RecoveryClass
    reason_code: str
    state_revision: int
    diagnostics: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_bool(self.required, "required")
        _require_bool(self.available, "available")
        _require_bool(self.compatible, "compatible")
        _require_enum(self.ownership, HelperOwnershipState, "ownership")
        operation = _validated_operation(
            outcome=OperationOutcome.APPLIED if self.available else OperationOutcome.UNAVAILABLE,
            reason_code=self.reason_code,
            health=self.health,
            recovery=self.recovery,
            state_revision=self.state_revision,
            diagnostics=self.diagnostics,
        )
        object.__setattr__(self, "diagnostics", operation.diagnostics)


@dataclass(frozen=True, slots=True)
class LifecycleSnapshot:
    """Observable runtime lifecycle and bounded cleanup state."""

    state: LifecycleState
    state_revision: int
    start_attempted: bool
    stop_requested: bool
    cleanup_elapsed_ms: int
    restart_allowed: bool
    diagnostics: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_enum(self.state, LifecycleState, "state")
        _require_revision(self.state_revision, "state_revision")
        _require_bool(self.start_attempted, "start_attempted")
        _require_bool(self.stop_requested, "stop_requested")
        _require_revision(self.cleanup_elapsed_ms, "cleanup_elapsed_ms")
        _require_bool(self.restart_allowed, "restart_allowed")
        if self.state is LifecycleState.STOPPED and self.restart_allowed:
            raise ValueError("stopped runtime cannot allow restart")
        operation = _validated_operation(
            outcome=OperationOutcome.APPLIED,
            reason_code="lifecycle_snapshot",
            health=RuntimeHealth.STOPPED if self.state is LifecycleState.STOPPED else RuntimeHealth.HEALTHY,
            recovery=RecoveryClass.TERMINAL if self.state is LifecycleState.STOPPED else RecoveryClass.AUTOMATIC,
            state_revision=self.state_revision,
            diagnostics=self.diagnostics,
        )
        object.__setattr__(self, "diagnostics", operation.diagnostics)


RuntimeResult = OperationResult
PresentationResult = OperationResult
InputPolicyResult = OperationResult
HelperResult = OperationResult


@runtime_checkable
class TargetObserver(Protocol):
    """Receives normalized target changes from discovery."""

    def target_changed(self, snapshot: TargetSnapshot) -> None:
        """Observe one immutable target snapshot."""


@runtime_checkable
class OverlaySurface(Protocol):
    """Opaque generic surface boundary attached by the composition root."""

    @property
    def surface_id(self) -> str:
        """Return a process-local stable surface identity."""


@runtime_checkable
class DiscoveryService(Protocol):
    """Own normalized target discovery and target lifecycle."""

    def start(self, observer: TargetObserver) -> OperationResult:
        """Start discovery with one observer."""

    def snapshot(self) -> TargetSnapshot:
        """Return the latest target snapshot."""

    def stop(self) -> OperationResult:
        """Stop discovery idempotently."""


@runtime_checkable
class PresentationService(Protocol):
    """Own prepare, present, hide, transition, and teardown behavior."""

    def present(self, intent: PresentationIntent, frame: FrameSnapshot | None) -> PresentationResult:
        """Apply normalized presentation intent."""

    def hide(self, reason: HideReason) -> PresentationResult:
        """Make presentation non-visible for a normalized reason."""

    def presentation_snapshot(self) -> PresentationSnapshot:
        """Return the latest presentation state."""

    def stop(self) -> OperationResult:
        """Stop presentation idempotently."""


@runtime_checkable
class InputPolicyService(Protocol):
    """Own click-through, focus acceptance, and interaction state."""

    def apply(self, intent: InteractionIntent) -> InputPolicyResult:
        """Apply normalized interaction intent."""

    def input_snapshot(self) -> InputPolicySnapshot:
        """Return the latest independently revisioned input state."""

    def stop(self) -> OperationResult:
        """Stop input policy idempotently."""


@runtime_checkable
class HelperLifecycle(Protocol):
    """Optional helper availability, health, ownership, and release behavior."""

    def acquire(self) -> HelperResult:
        """Acquire helper ownership when applicable."""

    def renew(self) -> HelperResult:
        """Renew active helper ownership when applicable."""

    def health(self) -> HelperHealthSnapshot:
        """Return normalized helper health without private protocol details."""

    def release(self) -> HelperResult:
        """Release helper ownership idempotently."""


@runtime_checkable
class BackendRuntime(Protocol):
    """One immutable backend identity and its process-lifetime owned services."""

    @property
    def identity(self) -> BackendIdentity:
        """Return the immutable selected runtime identity."""

    @property
    def discovery(self) -> DiscoveryService:
        """Return the stable owned discovery service."""

    @property
    def presentation(self) -> PresentationService:
        """Return the stable owned presentation service."""

    @property
    def input_policy(self) -> InputPolicyService:
        """Return the stable owned input-policy service."""

    @property
    def helper_lifecycle(self) -> HelperLifecycle | None:
        """Return the optional stable owned helper lifecycle."""

    def start(self) -> RuntimeResult:
        """Attempt runtime start once."""

    def attach_surface(self, surface: OverlaySurface) -> RuntimeResult:
        """Attach the process-local overlay surface."""

    def status_snapshot(self) -> BackendControlPlaneEnvelope:
        """Return the latest normalized schema-version-1 status."""

    def lifecycle_snapshot(self) -> LifecycleSnapshot:
        """Return the latest lifecycle state."""

    def stop(self, reason: StopReason) -> RuntimeResult:
        """Stop all owned resources terminally and idempotently."""


def _validated_operation(
    *,
    outcome: OperationOutcome,
    reason_code: str,
    health: RuntimeHealth,
    recovery: RecoveryClass,
    state_revision: int,
    diagnostics: Mapping[str, object],
) -> OperationResult:
    return OperationResult(
        outcome=outcome,
        reason_code=reason_code,
        health=health,
        recovery=recovery,
        state_revision=state_revision,
        diagnostics=diagnostics,
    )


def _require_text(value: object, name: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value):
        suffix = " string" if allow_empty else " non-empty string"
        raise TypeError(f"{name} must be a{suffix}")
    return value


def _require_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    return value


def _require_revision(value: object, name: str) -> int:
    revision = _require_int(value, name)
    if revision < 0:
        raise ValueError(f"{name} must be non-negative")
    return revision


def _require_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be bool")
    return value


def _require_enum(value: object, enum_type: type[Enum], name: str) -> None:
    if not isinstance(value, enum_type):
        raise TypeError(f"{name} must be {enum_type.__name__}")
