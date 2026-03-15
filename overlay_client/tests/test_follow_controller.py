from __future__ import annotations

import types

from overlay_client.follow_controller import FollowController


class _TimerStub:
    def __init__(self) -> None:
        self._active = False

    def isActive(self) -> bool:
        return self._active

    def start(self) -> None:
        self._active = True

    def stop(self) -> None:
        self._active = False


def _build_controller() -> FollowController:
    logger = types.SimpleNamespace(debug=lambda *_args, **_kwargs: None)
    timer = _TimerStub()
    return FollowController(
        poll_fn=lambda: None,
        logger=logger,
        tracking_timer=timer,
        debug_suffix=lambda: "debug",
    )


def test_override_expired_is_suppressed_for_standalone_with_stable_tracker(monkeypatch) -> None:
    controller = _build_controller()
    tracker_tuple = (1, 2, 3, 4)
    rect_tuple = (10, 20, 30, 40)
    monotonic_value = {"now": 100.0}
    monkeypatch.setattr("overlay_client.follow_controller.time.monotonic", lambda: monotonic_value["now"])

    controller.record_override(rect_tuple, tracker_tuple, reason="unit")
    monotonic_value["now"] = 102.0

    assert controller.override_expired(tracker_tuple=tracker_tuple, standalone_mode=True) is False
    assert controller.override_expired(tracker_tuple=tracker_tuple, standalone_mode=False) is True


def test_override_expired_remains_true_for_standalone_when_tracker_changes(monkeypatch) -> None:
    controller = _build_controller()
    tracker_tuple = (1, 2, 3, 4)
    rect_tuple = (10, 20, 30, 40)
    monotonic_value = {"now": 100.0}
    monkeypatch.setattr("overlay_client.follow_controller.time.monotonic", lambda: monotonic_value["now"])

    controller.record_override(rect_tuple, tracker_tuple, reason="unit")
    monotonic_value["now"] = 102.0

    assert controller.override_expired(tracker_tuple=(9, 9, 9, 9), standalone_mode=True) is True
