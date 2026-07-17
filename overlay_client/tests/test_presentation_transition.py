from __future__ import annotations

from overlay_client.backend.presentation_transition import (
    PresentationTransitionAction,
    PresentationTransitionMode,
    PresentationTransitionSnapshot,
    PresentationTransitionState,
    decide_presentation_transition,
)


def _snapshot(**overrides: object) -> PresentationTransitionSnapshot:
    values: dict[str, object] = {
        "target_available": True,
        "target_token": "meta:21",
        "target_monitor": 0,
        "target_rect": (0, 0, 3440, 1440),
        "target_monitor_rect": (0, 0, 3440, 1440),
        "target_showing_on_workspace": True,
        "target_minimized": False,
        "target_fullscreen": True,
    }
    values.update(overrides)
    return PresentationTransitionSnapshot(**values)  # type: ignore[arg-type]


def _stable_raster() -> PresentationTransitionState:
    return decide_presentation_transition(_snapshot()).state


def test_transient_fullscreen_loss_returns_directly_to_raster() -> None:
    pending = decide_presentation_transition(
        _snapshot(target_fullscreen=False, target_rect=(0, 29, 3440, 1411)),
        previous=_stable_raster(),
        now_monotonic=10.0,
    )
    restored = decide_presentation_transition(
        _snapshot(target_monitor=1, target_rect=(3440, 0, 3440, 1440), target_monitor_rect=(3440, 0, 3440, 1440)),
        previous=pending.state,
        now_monotonic=10.5,
    )

    assert pending.action is PresentationTransitionAction.HOLD_RASTER
    assert pending.state.mode is PresentationTransitionMode.FULLSCREEN_HANDOFF
    assert restored.action is PresentationTransitionAction.COMMIT_RASTER
    assert restored.state.mode is PresentationTransitionMode.SHELL_RASTER


def test_persistent_fullscreen_loss_commits_after_bound_and_samples() -> None:
    windowed = _snapshot(target_fullscreen=False, target_rect=(0, 29, 3440, 1411))
    first = decide_presentation_transition(windowed, previous=_stable_raster(), now_monotonic=10.0)
    early = decide_presentation_transition(windowed, previous=first.state, now_monotonic=11.49)
    settled = decide_presentation_transition(windowed, previous=early.state, now_monotonic=11.5)

    assert early.action is PresentationTransitionAction.HOLD_RASTER
    assert settled.action is PresentationTransitionAction.COMMIT_MANAGED
    assert settled.elapsed_seconds == 1.5
    assert settled.sample_count == 3


def test_initial_windowed_startup_is_not_held() -> None:
    decision = decide_presentation_transition(
        _snapshot(target_fullscreen=False, target_rect=(100, 100, 1280, 960))
    )

    assert decision.action is PresentationTransitionAction.COMMIT_MANAGED
    assert decision.state.mode is PresentationTransitionMode.MANAGED_WINDOWED


def test_monitor_change_enters_handoff_and_changed_geometry_resets_samples_not_deadline() -> None:
    first = decide_presentation_transition(
        _snapshot(
            target_fullscreen=False,
            target_monitor=1,
            target_rect=(3440, 29, 3440, 1411),
            target_monitor_rect=(3440, 0, 3440, 1440),
        ),
        previous=_stable_raster(),
        now_monotonic=10.0,
    )
    changed = decide_presentation_transition(
        _snapshot(target_fullscreen=False, target_rect=(0, 30, 3440, 1410)),
        previous=first.state,
        now_monotonic=11.5,
    )
    settled = decide_presentation_transition(
        _snapshot(target_fullscreen=False, target_rect=(0, 30, 3440, 1410)),
        previous=changed.state,
        now_monotonic=11.6,
    )

    assert first.action is PresentationTransitionAction.HOLD_RASTER
    assert changed.action is PresentationTransitionAction.HOLD_RASTER
    assert changed.sample_count == 1
    assert changed.state.pending_started_monotonic == 10.0
    assert settled.action is PresentationTransitionAction.COMMIT_MANAGED


def test_token_replacement_and_hard_visibility_loss_hide_immediately() -> None:
    stable = _stable_raster()
    cases = (
        _snapshot(target_token="meta:22"),
        _snapshot(target_minimized=True),
        _snapshot(target_showing_on_workspace=False),
        _snapshot(target_available=False, target_token=""),
    )

    for snapshot in cases:
        decision = decide_presentation_transition(snapshot, previous=stable, now_monotonic=10.1)
        assert decision.action is PresentationTransitionAction.HIDE_ALL
        assert decision.state.mode is PresentationTransitionMode.UNKNOWN


def test_fullscreen_loss_without_geometry_change_is_not_held() -> None:
    decision = decide_presentation_transition(
        _snapshot(target_fullscreen=False),
        previous=_stable_raster(),
        now_monotonic=10.0,
    )

    assert decision.action is PresentationTransitionAction.COMMIT_MANAGED
    assert decision.reason == "fullscreen_loss_without_transition_evidence"
