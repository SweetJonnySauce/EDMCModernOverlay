from __future__ import annotations

from overlay_client.follow_controller import FollowController
from overlay_client.window_tracking_support import WindowState


class _Logger:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def debug(self, message: str, *args) -> None:
        if args:
            message = message % args
        self.messages.append(message)


class _Timer:
    def __init__(self) -> None:
        self.active = False

    def isActive(self) -> bool:
        return self.active

    def start(self) -> None:
        self.active = True

    def stop(self) -> None:
        self.active = False


def _state(*, is_foreground: bool = True, is_visible: bool = True) -> WindowState:
    return WindowState(
        x=0,
        y=0,
        width=1920,
        height=1080,
        is_foreground=is_foreground,
        is_visible=is_visible,
        identifier="stable:14",
        global_x=0,
        global_y=0,
    )


def test_refresh_logs_foreground_transition_even_when_geometry_is_unchanged() -> None:
    logger = _Logger()
    timer = _Timer()
    states = [_state(is_foreground=True), _state(is_foreground=False)]
    controller = FollowController(
        poll_fn=lambda: states.pop(0),
        logger=logger,
        tracking_timer=timer,
        debug_suffix=lambda: "debug-suffix",
    )

    controller.refresh()
    controller.refresh()

    tracker_logs = [message for message in logger.messages if message.startswith("Tracker state:")]
    assert len(tracker_logs) == 2
    assert "foreground=True visible=True" in tracker_logs[0]
    assert "foreground=False visible=True" in tracker_logs[1]
    assert controller.last_tracker_state == ("stable:14", 0, 0, 1920, 1080, False, True)


def test_refresh_does_not_relog_identical_tracker_state() -> None:
    logger = _Logger()
    timer = _Timer()
    states = [_state(is_foreground=True), _state(is_foreground=True)]
    controller = FollowController(
        poll_fn=lambda: states.pop(0),
        logger=logger,
        tracking_timer=timer,
        debug_suffix=lambda: "debug-suffix",
    )

    controller.refresh()
    controller.refresh()

    tracker_logs = [message for message in logger.messages if message.startswith("Tracker state:")]
    assert len(tracker_logs) == 1
    assert controller.last_tracker_state == ("stable:14", 0, 0, 1920, 1080, True, True)
