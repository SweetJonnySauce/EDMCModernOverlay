"""Pure renderer-ownership policy for fullscreen presentation transitions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

PRESENTATION_TRANSITION_DEFAULT_GRACE_SECONDS = 1.5
PRESENTATION_TRANSITION_DEFAULT_STABLE_SAMPLES = 2


class PresentationTransitionMode(str, Enum):
    """Stable or pending renderer ownership known by the backend."""

    UNKNOWN = "unknown"
    SHELL_RASTER = "stable_shell_raster"
    FULLSCREEN_HANDOFF = "pending_fullscreen_handoff"
    MANAGED_WINDOWED = "stable_managed_windowed"


class PresentationTransitionAction(str, Enum):
    """Backend action selected for the current target sample."""

    HOLD_RASTER = "hold_raster"
    COMMIT_RASTER = "commit_raster"
    COMMIT_MANAGED = "commit_managed"
    HIDE_ALL = "hide_all"


@dataclass(frozen=True, slots=True)
class PresentationTransitionSnapshot:
    """Minimal target facts consumed by the transition policy."""

    target_available: bool = False
    target_token: str = ""
    target_monitor: int | None = None
    target_rect: tuple[int, int, int, int] | None = None
    target_monitor_rect: tuple[int, int, int, int] | None = None
    target_showing_on_workspace: bool = False
    target_minimized: bool = False
    target_fullscreen: bool = False


@dataclass(frozen=True, slots=True)
class PresentationTransitionState:
    """Immutable renderer-ownership state carried between samples."""

    mode: PresentationTransitionMode = PresentationTransitionMode.UNKNOWN
    target_token: str = ""
    stable_monitor: int | None = None
    stable_relative_rect: tuple[int, int, int, int] | None = None
    pending_started_monotonic: float | None = None
    pending_samples: int = 0
    pending_monitor: int | None = None
    pending_relative_rect: tuple[int, int, int, int] | None = None


@dataclass(frozen=True, slots=True)
class PresentationTransitionDecision:
    """Selected action and next immutable policy state."""

    action: PresentationTransitionAction
    reason: str
    state: PresentationTransitionState
    elapsed_seconds: float = 0.0
    sample_count: int = 0


def decide_presentation_transition(
    snapshot: PresentationTransitionSnapshot,
    *,
    previous: PresentationTransitionState | None = None,
    now_monotonic: float = 0.0,
    grace_seconds: float = PRESENTATION_TRANSITION_DEFAULT_GRACE_SECONDS,
    stable_samples: int = PRESENTATION_TRANSITION_DEFAULT_STABLE_SAMPLES,
) -> PresentationTransitionDecision:
    """Select renderer ownership for one deterministic target sample."""

    prior = previous or PresentationTransitionState()
    reset = PresentationTransitionState()
    if not snapshot.target_available or not snapshot.target_token:
        return PresentationTransitionDecision(
            PresentationTransitionAction.HIDE_ALL,
            "target_unavailable",
            reset,
        )
    if snapshot.target_minimized:
        return PresentationTransitionDecision(
            PresentationTransitionAction.HIDE_ALL,
            "target_minimized",
            reset,
        )
    if not snapshot.target_showing_on_workspace:
        return PresentationTransitionDecision(
            PresentationTransitionAction.HIDE_ALL,
            "target_hidden_or_off_workspace",
            reset,
        )
    if prior.target_token and prior.target_token != snapshot.target_token:
        return PresentationTransitionDecision(
            PresentationTransitionAction.HIDE_ALL,
            "target_token_replaced",
            reset,
        )

    relative_rect = _monitor_relative_rect(snapshot.target_rect, snapshot.target_monitor_rect)
    if snapshot.target_fullscreen:
        return PresentationTransitionDecision(
            PresentationTransitionAction.COMMIT_RASTER,
            "fullscreen_target",
            PresentationTransitionState(
                mode=PresentationTransitionMode.SHELL_RASTER,
                target_token=snapshot.target_token,
                stable_monitor=snapshot.target_monitor,
                stable_relative_rect=relative_rect,
            ),
        )

    if prior.mode is PresentationTransitionMode.FULLSCREEN_HANDOFF:
        return _continue_pending_handoff(
            snapshot,
            prior,
            relative_rect=relative_rect,
            now_monotonic=now_monotonic,
            grace_seconds=grace_seconds,
            stable_samples=stable_samples,
        )

    transition_evidence = (
        prior.stable_monitor != snapshot.target_monitor
        or prior.stable_relative_rect != relative_rect
    )
    if prior.mode is PresentationTransitionMode.SHELL_RASTER and transition_evidence:
        pending = PresentationTransitionState(
            mode=PresentationTransitionMode.FULLSCREEN_HANDOFF,
            target_token=snapshot.target_token,
            stable_monitor=prior.stable_monitor,
            stable_relative_rect=prior.stable_relative_rect,
            pending_started_monotonic=float(now_monotonic),
            pending_samples=1,
            pending_monitor=snapshot.target_monitor,
            pending_relative_rect=relative_rect,
        )
        return PresentationTransitionDecision(
            PresentationTransitionAction.HOLD_RASTER,
            "fullscreen_handoff_started",
            pending,
            sample_count=1,
        )

    reason = "stable_managed_windowed"
    if prior.mode is PresentationTransitionMode.SHELL_RASTER:
        reason = "fullscreen_loss_without_transition_evidence"
    return PresentationTransitionDecision(
        PresentationTransitionAction.COMMIT_MANAGED,
        reason,
        _managed_state(snapshot, relative_rect),
    )


def _continue_pending_handoff(
    snapshot: PresentationTransitionSnapshot,
    previous: PresentationTransitionState,
    *,
    relative_rect: tuple[int, int, int, int] | None,
    now_monotonic: float,
    grace_seconds: float,
    stable_samples: int,
) -> PresentationTransitionDecision:
    started = previous.pending_started_monotonic
    if started is None:
        started = float(now_monotonic)
    elapsed = max(0.0, float(now_monotonic) - started)
    compatible = (
        previous.pending_monitor == snapshot.target_monitor
        and previous.pending_relative_rect == relative_rect
    )
    samples = previous.pending_samples + 1 if compatible else 1
    pending = PresentationTransitionState(
        mode=PresentationTransitionMode.FULLSCREEN_HANDOFF,
        target_token=snapshot.target_token,
        stable_monitor=previous.stable_monitor,
        stable_relative_rect=previous.stable_relative_rect,
        pending_started_monotonic=started,
        pending_samples=samples,
        pending_monitor=snapshot.target_monitor,
        pending_relative_rect=relative_rect,
    )
    if (
        samples >= max(1, int(stable_samples))
        and elapsed >= max(0.0, float(grace_seconds))
    ):
        return PresentationTransitionDecision(
            PresentationTransitionAction.COMMIT_MANAGED,
            "fullscreen_handoff_expired",
            _managed_state(snapshot, relative_rect),
            elapsed_seconds=elapsed,
            sample_count=samples,
        )
    reason = "fullscreen_handoff_waiting" if compatible else "fullscreen_handoff_geometry_changed"
    return PresentationTransitionDecision(
        PresentationTransitionAction.HOLD_RASTER,
        reason,
        pending,
        elapsed_seconds=elapsed,
        sample_count=samples,
    )


def _managed_state(
    snapshot: PresentationTransitionSnapshot,
    relative_rect: tuple[int, int, int, int] | None,
) -> PresentationTransitionState:
    return PresentationTransitionState(
        mode=PresentationTransitionMode.MANAGED_WINDOWED,
        target_token=snapshot.target_token,
        stable_monitor=snapshot.target_monitor,
        stable_relative_rect=relative_rect,
    )


def _monitor_relative_rect(
    rect: tuple[int, int, int, int] | None,
    monitor_rect: tuple[int, int, int, int] | None,
) -> tuple[int, int, int, int] | None:
    if rect is None:
        return None
    if monitor_rect is None:
        return rect
    return (
        rect[0] - monitor_rect[0],
        rect[1] - monitor_rect[1],
        rect[2],
        rect[3],
    )
