from __future__ import annotations

import pytest

from overlay_client.backend.presentation_policy import (
    BackendPresentationContentVisibility,
    BACKEND_PRESENTATION_FOCUS_LOSS_HIDE_SAMPLES,
    BACKEND_PRESENTATION_FOCUS_LOSS_DEBOUNCE_SECONDS,
    BACKEND_PRESENTATION_REMAP_WARMUP_MAX_SAMPLES,
    BACKEND_PRESENTATION_REMAP_WARMUP_SECONDS,
    BACKEND_PRESENTATION_SURFACE_HIDDEN,
    BACKEND_PRESENTATION_SURFACE_MAPPED_SUPPRESSED,
    BACKEND_PRESENTATION_SURFACE_MAPPED_VISIBLE,
    BackendPresentationVisibilitySnapshot,
    BackendPresentationVisibilityState,
    decide_backend_presentation_visibility,
)


def _valid_snapshot(
    *,
    focused: bool = True,
    presentation_attachable: bool = True,
    retained_content_visibility_available: bool = False,
    prepared_surface_requires_mapping: bool = False,
    prepared_surface_allows_unfocused_content: bool = False,
) -> BackendPresentationVisibilitySnapshot:
    return BackendPresentationVisibilitySnapshot(
        target_available=True,
        target_has_focus=focused,
        target_showing_on_workspace=True,
        target_minimized=False,
        presentation_available=True,
        presentation_attachable=presentation_attachable,
        retained_content_visibility_available=retained_content_visibility_available,
        overlay_window_found=True,
        presentation_rect_match=True,
        prepared_surface_requires_mapping=prepared_surface_requires_mapping,
        prepared_surface_allows_unfocused_content=prepared_surface_allows_unfocused_content,
    )


def test_backend_presentation_visibility_hides_when_target_unavailable() -> None:
    decision = decide_backend_presentation_visibility(
        BackendPresentationVisibilitySnapshot(),
        keep_overlay_visible=True,
        previous=BackendPresentationVisibilityState(focus_loss_samples=1, focus_lost_since_monotonic=5.0),
        now_monotonic=10.0,
    )

    assert decision.show is False
    assert decision.reason == "target_unavailable"
    assert decision.surface_action == BACKEND_PRESENTATION_SURFACE_HIDDEN
    assert decision.content_visible is False
    assert decision.content_suppressed is True
    assert decision.content_visibility is BackendPresentationContentVisibility.SUPPRESSED
    assert decision.state == BackendPresentationVisibilityState()


def test_backend_presentation_visibility_hides_when_target_minimized_or_off_workspace() -> None:
    minimized = decide_backend_presentation_visibility(
        BackendPresentationVisibilitySnapshot(
            target_available=True,
            target_showing_on_workspace=True,
            target_minimized=True,
            presentation_available=True,
            presentation_attachable=True,
        ),
        keep_overlay_visible=True,
    )
    off_workspace = decide_backend_presentation_visibility(
        BackendPresentationVisibilitySnapshot(
            target_available=True,
            target_showing_on_workspace=False,
            target_minimized=False,
            presentation_available=True,
            presentation_attachable=True,
        ),
        keep_overlay_visible=True,
    )

    assert minimized.show is False
    assert minimized.reason == "target_minimized"
    assert minimized.surface_action == BACKEND_PRESENTATION_SURFACE_HIDDEN
    assert minimized.content_visible is False
    assert minimized.content_visibility is BackendPresentationContentVisibility.SUPPRESSED
    assert off_workspace.show is False
    assert off_workspace.reason == "target_hidden_or_off_workspace"
    assert off_workspace.surface_action == BACKEND_PRESENTATION_SURFACE_HIDDEN
    assert off_workspace.content_visible is False
    assert off_workspace.content_visibility is BackendPresentationContentVisibility.SUPPRESSED


def test_backend_presentation_visibility_hides_when_presentation_unavailable() -> None:
    decision = decide_backend_presentation_visibility(
        BackendPresentationVisibilitySnapshot(
            target_available=True,
            target_has_focus=True,
            target_showing_on_workspace=True,
            target_minimized=False,
            presentation_available=False,
            presentation_attachable=False,
        ),
        keep_overlay_visible=True,
    )

    assert decision.show is False
    assert decision.reason == "presentation_unavailable"
    assert decision.surface_action == BACKEND_PRESENTATION_SURFACE_HIDDEN
    assert decision.content_visible is False


def test_backend_presentation_visibility_keep_visible_ignores_focus_loss_for_valid_target() -> None:
    decision = decide_backend_presentation_visibility(
        _valid_snapshot(focused=False),
        keep_overlay_visible=True,
        now_monotonic=10.0,
    )

    assert decision.show is True
    assert decision.reason == "keep_overlay_visible"
    assert decision.surface_action == BACKEND_PRESENTATION_SURFACE_MAPPED_VISIBLE
    assert decision.content_visible is True
    assert decision.content_suppressed is False
    assert decision.content_visibility is BackendPresentationContentVisibility.VISIBLE
    assert decision.state == BackendPresentationVisibilityState()


def test_backend_presentation_visibility_focused_target_shows_and_resets_debounce() -> None:
    decision = decide_backend_presentation_visibility(
        _valid_snapshot(focused=True),
        keep_overlay_visible=False,
        previous=BackendPresentationVisibilityState(focus_loss_samples=1, focus_lost_since_monotonic=5.0),
        now_monotonic=10.0,
    )

    assert decision.show is True
    assert decision.reason == "target_focused"
    assert decision.surface_action == BACKEND_PRESENTATION_SURFACE_MAPPED_VISIBLE
    assert decision.content_visible is True
    assert decision.content_visibility is BackendPresentationContentVisibility.VISIBLE
    assert decision.state == BackendPresentationVisibilityState()


def test_backend_presentation_visibility_debounces_single_focus_loss_sample() -> None:
    decision = decide_backend_presentation_visibility(
        _valid_snapshot(focused=False),
        keep_overlay_visible=False,
        now_monotonic=10.0,
    )

    assert BACKEND_PRESENTATION_FOCUS_LOSS_HIDE_SAMPLES == 2
    assert decision.show is True
    assert decision.reason == "focus_loss_debouncing"
    assert decision.state.focus_loss_samples == 1
    assert decision.state.focus_lost_since_monotonic == 10.0


def test_backend_presentation_visibility_keeps_hidden_overlay_hidden_until_focus_returns() -> None:
    decision = decide_backend_presentation_visibility(
        _valid_snapshot(focused=False),
        keep_overlay_visible=False,
        currently_visible=False,
        now_monotonic=10.0,
    )

    assert decision.show is False
    assert decision.reason == "focus_lost_hidden"
    assert decision.surface_action == BACKEND_PRESENTATION_SURFACE_HIDDEN
    assert decision.content_visible is False
    assert decision.state.focus_loss_samples == 1
    assert decision.state.focus_lost_since_monotonic == 10.0


def test_backend_presentation_visibility_maps_prepared_surface_suppressed_until_focus_returns() -> None:
    decision = decide_backend_presentation_visibility(
        _valid_snapshot(focused=False, prepared_surface_requires_mapping=True),
        keep_overlay_visible=False,
        currently_visible=False,
        now_monotonic=10.0,
    )

    assert decision.show is True
    assert decision.reason == "prepared_surface_focus_lost_suppressed"
    assert decision.surface_action == BACKEND_PRESENTATION_SURFACE_MAPPED_SUPPRESSED
    assert decision.content_visible is False
    assert decision.content_suppressed is True
    assert decision.content_visibility is BackendPresentationContentVisibility.SUPPRESSED
    assert decision.state.focus_loss_samples == 1
    assert decision.state.focus_lost_since_monotonic == 10.0


def test_backend_presentation_visibility_shows_matched_prepared_surface_when_focus_is_unreliable() -> None:
    decision = decide_backend_presentation_visibility(
        _valid_snapshot(
            focused=False,
            prepared_surface_requires_mapping=True,
            prepared_surface_allows_unfocused_content=True,
        ),
        keep_overlay_visible=False,
        currently_visible=True,
        previous=BackendPresentationVisibilityState(focus_loss_samples=3, focus_lost_since_monotonic=10.0),
        now_monotonic=20.0,
    )

    assert decision.show is True
    assert decision.reason == "prepared_surface_focus_unreliable_visible"
    assert decision.surface_action == BACKEND_PRESENTATION_SURFACE_MAPPED_VISIBLE
    assert decision.content_visible is True
    assert decision.content_suppressed is False
    assert decision.content_visibility is BackendPresentationContentVisibility.VISIBLE
    assert decision.state == BackendPresentationVisibilityState()


def test_backend_presentation_visibility_suppresses_retained_content_when_normal_attachment_is_unavailable() -> None:
    decision = decide_backend_presentation_visibility(
        _valid_snapshot(
            focused=False,
            presentation_attachable=False,
            retained_content_visibility_available=True,
        ),
        keep_overlay_visible=False,
        currently_visible=True,
        previous=BackendPresentationVisibilityState(focus_loss_samples=3, focus_lost_since_monotonic=10.0),
        now_monotonic=20.0,
    )

    assert decision.show is True
    assert decision.reason == "focus_lost_suppressed"
    assert decision.surface_action == BACKEND_PRESENTATION_SURFACE_MAPPED_SUPPRESSED
    assert decision.content_visibility is BackendPresentationContentVisibility.SUPPRESSED


def test_backend_presentation_visibility_keeps_visible_until_focus_loss_time_threshold() -> None:
    previous = BackendPresentationVisibilityState(focus_loss_samples=1, focus_lost_since_monotonic=10.0)

    decision = decide_backend_presentation_visibility(
        _valid_snapshot(focused=False),
        keep_overlay_visible=False,
        previous=previous,
        now_monotonic=10.4,
    )

    assert decision.show is True
    assert decision.reason == "focus_loss_debouncing"
    assert decision.state.focus_loss_samples == 2


def test_backend_presentation_visibility_suppresses_after_focus_loss_sample_and_time_thresholds() -> None:
    previous = BackendPresentationVisibilityState(focus_loss_samples=1, focus_lost_since_monotonic=10.0)

    decision = decide_backend_presentation_visibility(
        _valid_snapshot(focused=False),
        keep_overlay_visible=False,
        previous=previous,
        now_monotonic=11.1,
    )

    assert BACKEND_PRESENTATION_FOCUS_LOSS_DEBOUNCE_SECONDS == 1.0
    assert decision.show is True
    assert decision.reason == "focus_lost_suppressed"
    assert decision.surface_action == BACKEND_PRESENTATION_SURFACE_MAPPED_SUPPRESSED
    assert decision.content_visible is False
    assert decision.content_suppressed is True
    assert decision.content_visibility is BackendPresentationContentVisibility.SUPPRESSED
    assert decision.focus_loss_elapsed_seconds == pytest.approx(1.1)


def test_backend_presentation_visibility_keeps_visible_until_focus_loss_sample_threshold() -> None:
    previous = BackendPresentationVisibilityState(focus_loss_samples=1, focus_lost_since_monotonic=10.0)

    decision = decide_backend_presentation_visibility(
        _valid_snapshot(focused=False),
        keep_overlay_visible=False,
        previous=previous,
        now_monotonic=11.1,
        focus_loss_hide_samples=3,
    )

    assert decision.show is True
    assert decision.reason == "focus_loss_debouncing"
    assert decision.state.focus_loss_samples == 2
    assert decision.focus_loss_elapsed_seconds == pytest.approx(1.1)


def test_backend_presentation_visibility_starts_warmup_when_hidden_overlay_remaps() -> None:
    decision = decide_backend_presentation_visibility(
        _valid_snapshot(focused=True),
        keep_overlay_visible=False,
        currently_visible=False,
        now_monotonic=20.0,
    )

    assert decision.show is True
    assert decision.reason == "target_focused_remap_warmup"
    assert decision.remap_warmup_status == "started"
    assert decision.surface_action == BACKEND_PRESENTATION_SURFACE_MAPPED_SUPPRESSED
    assert decision.content_visible is False
    assert decision.state.remap_warmup_active is True
    assert decision.state.remap_warmup_samples == 0
    assert decision.state.remap_warmup_started_monotonic == 20.0


def test_backend_presentation_visibility_warmup_keeps_visible_during_transient_focus_loss() -> None:
    previous = BackendPresentationVisibilityState(
        remap_warmup_active=True,
        remap_warmup_samples=0,
        remap_warmup_started_monotonic=20.0,
    )
    snapshot = BackendPresentationVisibilitySnapshot(
        target_available=True,
        target_has_focus=False,
        target_showing_on_workspace=True,
        target_minimized=False,
        presentation_available=True,
        presentation_attachable=True,
        overlay_window_found=True,
        presentation_rect_match=False,
    )

    decision = decide_backend_presentation_visibility(
        snapshot,
        keep_overlay_visible=False,
        previous=previous,
        currently_visible=True,
        now_monotonic=20.5,
    )

    assert decision.show is True
    assert decision.reason == "presentation_warmup_waiting"
    assert decision.remap_warmup_status == "active"
    assert decision.surface_action == BACKEND_PRESENTATION_SURFACE_MAPPED_SUPPRESSED
    assert decision.content_visible is False
    assert decision.state.remap_warmup_active is True
    assert decision.state.remap_warmup_samples == 1
    assert decision.state.focus_loss_samples == 0


def test_backend_presentation_visibility_warmup_completes_after_rect_match() -> None:
    previous = BackendPresentationVisibilityState(
        remap_warmup_active=True,
        remap_warmup_samples=1,
        remap_warmup_started_monotonic=20.0,
    )

    decision = decide_backend_presentation_visibility(
        _valid_snapshot(focused=False),
        keep_overlay_visible=False,
        previous=previous,
        currently_visible=True,
        now_monotonic=21.0,
    )

    assert decision.show is True
    assert decision.reason == "presentation_warmup_complete"
    assert decision.surface_action == BACKEND_PRESENTATION_SURFACE_MAPPED_VISIBLE
    assert decision.content_visible is True
    assert decision.remap_warmup_status == "complete"
    assert decision.state == BackendPresentationVisibilityState()


def test_backend_presentation_visibility_keep_visible_still_suppresses_unconfirmed_remap() -> None:
    snapshot = BackendPresentationVisibilitySnapshot(
        target_available=True,
        target_has_focus=False,
        target_showing_on_workspace=True,
        target_minimized=False,
        presentation_available=True,
        presentation_attachable=True,
        overlay_window_found=False,
        presentation_rect_match=False,
        prepared_surface_requires_mapping=True,
    )

    decision = decide_backend_presentation_visibility(
        snapshot,
        keep_overlay_visible=True,
        currently_visible=False,
        now_monotonic=20.0,
    )

    assert decision.show is True
    assert decision.reason == "prepared_surface_remap_warmup"
    assert decision.surface_action == BACKEND_PRESENTATION_SURFACE_MAPPED_SUPPRESSED
    assert decision.content_visible is False
    assert decision.remap_warmup_status == "started"
    assert decision.state.remap_warmup_active is True


def test_backend_presentation_visibility_warmup_expires_when_rect_never_matches() -> None:
    previous = BackendPresentationVisibilityState(
        remap_warmup_active=True,
        remap_warmup_samples=BACKEND_PRESENTATION_REMAP_WARMUP_MAX_SAMPLES - 1,
        remap_warmup_started_monotonic=20.0,
    )
    snapshot = BackendPresentationVisibilitySnapshot(
        target_available=True,
        target_has_focus=False,
        target_showing_on_workspace=True,
        target_minimized=False,
        presentation_available=True,
        presentation_attachable=True,
        overlay_window_found=True,
        presentation_rect_match=False,
    )

    decision = decide_backend_presentation_visibility(
        snapshot,
        keep_overlay_visible=False,
        previous=previous,
        currently_visible=True,
        now_monotonic=20.5,
    )

    assert BACKEND_PRESENTATION_REMAP_WARMUP_MAX_SAMPLES == 4
    assert BACKEND_PRESENTATION_REMAP_WARMUP_SECONDS == 2.0
    assert decision.show is False
    assert decision.reason == "presentation_warmup_expired"
    assert decision.surface_action == BACKEND_PRESENTATION_SURFACE_HIDDEN
    assert decision.content_visible is False
    assert decision.remap_warmup_status == "expired"
    assert decision.state == BackendPresentationVisibilityState()
