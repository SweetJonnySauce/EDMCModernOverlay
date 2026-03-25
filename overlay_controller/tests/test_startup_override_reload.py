from types import SimpleNamespace

import overlay_controller.overlay_controller as oc


def test_emit_startup_override_reload_schedules_emit_signal() -> None:
    calls: list[tuple[int, object]] = []

    fake = SimpleNamespace(
        after=lambda delay, callback: calls.append((delay, callback)),
        _emit_override_reload_signal=lambda: None,
    )

    oc.OverlayConfigApp._emit_startup_override_reload(fake)

    assert len(calls) == 1
    assert calls[0][0] == 0
    assert calls[0][1] is fake._emit_override_reload_signal
