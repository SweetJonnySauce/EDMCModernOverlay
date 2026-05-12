"""Backend-facing presentation visibility policy."""

from __future__ import annotations

from dataclasses import dataclass

BACKEND_PRESENTATION_FOCUS_LOSS_HIDE_SAMPLES = 2
BACKEND_PRESENTATION_FOCUS_LOSS_DEBOUNCE_SECONDS = 1.0
BACKEND_PRESENTATION_REMAP_WARMUP_MAX_SAMPLES = 4
BACKEND_PRESENTATION_REMAP_WARMUP_SECONDS = 2.0
BACKEND_PRESENTATION_SURFACE_HIDDEN = "hidden"
BACKEND_PRESENTATION_SURFACE_MAPPED_VISIBLE = "mapped_visible"
BACKEND_PRESENTATION_SURFACE_MAPPED_SUPPRESSED = "mapped_suppressed"


@dataclass(frozen=True, slots=True)
class BackendPresentationVisibilitySnapshot:
    """Backend-neutral presentation facts used by generic follow surfaces."""

    target_available: bool = False
    target_has_focus: bool = False
    target_showing_on_workspace: bool = False
    target_minimized: bool = False
    presentation_available: bool = False
    presentation_attachable: bool = False
    overlay_window_found: bool = False
    presentation_rect_match: bool = False


@dataclass(frozen=True, slots=True)
class BackendPresentationVisibilityState:
    """Debounce state for backend-driven presentation visibility."""

    focus_loss_samples: int = 0
    focus_lost_since_monotonic: float | None = None
    remap_warmup_active: bool = False
    remap_warmup_samples: int = 0
    remap_warmup_started_monotonic: float | None = None


@dataclass(frozen=True, slots=True)
class BackendPresentationVisibilityDecision:
    """Visibility decision plus state needed for the next sample."""

    show: bool
    reason: str
    state: BackendPresentationVisibilityState
    focus_loss_elapsed_seconds: float = 0.0
    remap_warmup_elapsed_seconds: float = 0.0
    remap_warmup_status: str = "inactive"
    surface_action: str = BACKEND_PRESENTATION_SURFACE_MAPPED_VISIBLE
    content_visible: bool = True

    @property
    def content_suppressed(self) -> bool:
        return not self.content_visible


def decide_backend_presentation_visibility(
    snapshot: BackendPresentationVisibilitySnapshot,
    *,
    keep_overlay_visible: bool,
    previous: BackendPresentationVisibilityState | None = None,
    now_monotonic: float = 0.0,
    currently_visible: bool = True,
    focus_loss_hide_samples: int = BACKEND_PRESENTATION_FOCUS_LOSS_HIDE_SAMPLES,
    focus_loss_debounce_seconds: float = BACKEND_PRESENTATION_FOCUS_LOSS_DEBOUNCE_SECONDS,
    remap_warmup_max_samples: int = BACKEND_PRESENTATION_REMAP_WARMUP_MAX_SAMPLES,
    remap_warmup_seconds: float = BACKEND_PRESENTATION_REMAP_WARMUP_SECONDS,
) -> BackendPresentationVisibilityDecision:
    """Return a debounced visibility decision for backend-owned presentation mode."""

    reset_state = BackendPresentationVisibilityState()
    if not snapshot.target_available:
        return BackendPresentationVisibilityDecision(
            False,
            "target_unavailable",
            reset_state,
            surface_action=BACKEND_PRESENTATION_SURFACE_HIDDEN,
            content_visible=False,
        )
    if snapshot.target_minimized:
        return BackendPresentationVisibilityDecision(
            False,
            "target_minimized",
            reset_state,
            surface_action=BACKEND_PRESENTATION_SURFACE_HIDDEN,
            content_visible=False,
        )
    if not snapshot.target_showing_on_workspace:
        return BackendPresentationVisibilityDecision(
            False,
            "target_hidden_or_off_workspace",
            reset_state,
            surface_action=BACKEND_PRESENTATION_SURFACE_HIDDEN,
            content_visible=False,
        )
    if not snapshot.presentation_available:
        return BackendPresentationVisibilityDecision(
            False,
            "presentation_unavailable",
            reset_state,
            surface_action=BACKEND_PRESENTATION_SURFACE_HIDDEN,
            content_visible=False,
        )
    if not snapshot.presentation_attachable:
        return BackendPresentationVisibilityDecision(
            False,
            "presentation_not_attachable",
            reset_state,
            surface_action=BACKEND_PRESENTATION_SURFACE_HIDDEN,
            content_visible=False,
        )
    if keep_overlay_visible:
        return BackendPresentationVisibilityDecision(True, "keep_overlay_visible", reset_state)

    previous_state = previous or reset_state
    if previous_state.remap_warmup_active:
        warmup_started = previous_state.remap_warmup_started_monotonic
        if warmup_started is None:
            warmup_started = float(now_monotonic)
        warmup_elapsed = max(0.0, float(now_monotonic) - warmup_started)
        if snapshot.overlay_window_found and snapshot.presentation_rect_match:
            return BackendPresentationVisibilityDecision(
                True,
                "presentation_warmup_complete",
                reset_state,
                remap_warmup_elapsed_seconds=warmup_elapsed,
                remap_warmup_status="complete",
            )
        warmup_samples = previous_state.remap_warmup_samples + 1
        if (
            warmup_samples >= max(1, int(remap_warmup_max_samples))
            or warmup_elapsed >= max(0.0, float(remap_warmup_seconds))
        ):
            if snapshot.target_has_focus:
                return BackendPresentationVisibilityDecision(
                    True,
                    "target_focused_warmup_expired",
                    reset_state,
                    remap_warmup_elapsed_seconds=warmup_elapsed,
                    remap_warmup_status="expired",
                )
            return BackendPresentationVisibilityDecision(
                False,
                "presentation_warmup_expired",
                reset_state,
                remap_warmup_elapsed_seconds=warmup_elapsed,
                remap_warmup_status="expired",
                surface_action=BACKEND_PRESENTATION_SURFACE_HIDDEN,
                content_visible=False,
            )
        return BackendPresentationVisibilityDecision(
            True,
            "presentation_warmup_waiting",
            BackendPresentationVisibilityState(
                remap_warmup_active=True,
                remap_warmup_samples=warmup_samples,
                remap_warmup_started_monotonic=warmup_started,
            ),
            remap_warmup_elapsed_seconds=warmup_elapsed,
            remap_warmup_status="active",
        )

    if not currently_visible and snapshot.target_has_focus:
        return BackendPresentationVisibilityDecision(
            True,
            "target_focused_remap_warmup",
            BackendPresentationVisibilityState(
                remap_warmup_active=True,
                remap_warmup_samples=0,
                remap_warmup_started_monotonic=float(now_monotonic),
            ),
            remap_warmup_status="started",
        )
    if snapshot.target_has_focus:
        return BackendPresentationVisibilityDecision(True, "target_focused", reset_state)

    samples = previous_state.focus_loss_samples + 1
    lost_since = previous_state.focus_lost_since_monotonic
    if lost_since is None:
        lost_since = float(now_monotonic)
    elapsed = max(0.0, float(now_monotonic) - lost_since)
    next_state = BackendPresentationVisibilityState(
        focus_loss_samples=samples,
        focus_lost_since_monotonic=lost_since,
    )
    if not currently_visible:
        return BackendPresentationVisibilityDecision(
            False,
            "focus_lost_hidden",
            next_state,
            elapsed,
            surface_action=BACKEND_PRESENTATION_SURFACE_HIDDEN,
            content_visible=False,
        )
    if samples >= max(1, int(focus_loss_hide_samples)) and elapsed >= max(0.0, float(focus_loss_debounce_seconds)):
        return BackendPresentationVisibilityDecision(
            True,
            "focus_lost_suppressed",
            next_state,
            elapsed,
            surface_action=BACKEND_PRESENTATION_SURFACE_MAPPED_SUPPRESSED,
            content_visible=False,
        )
    return BackendPresentationVisibilityDecision(True, "focus_loss_debouncing", next_state, elapsed)
