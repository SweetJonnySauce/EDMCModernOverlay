from __future__ import annotations

from types import SimpleNamespace

from overlay_client.backend.pressure_ab import WORK_COUNTER_KEYS
from overlay_client.control_surface import ControlSurfaceMixin
from overlay_client.backend.consumers import BackendPresentationCycleResult
from overlay_client.follow_surface import _record_backend_work_counts


class _DataClient:
    def __init__(self) -> None:
        self.payloads: list[dict[str, object]] = []

    def send_cli_payload(self, payload: dict[str, object]) -> bool:
        self.payloads.append(payload)
        return True


def _window_stub() -> SimpleNamespace:
    return SimpleNamespace(
        _pressure_snapshot_origin_id="a" * 32,
        _payload_model=SimpleNamespace(
            ingest_counts={
                "visual_change": 1,
                "lifecycle_refresh": 2,
                "animation_bypass": 3,
                "unknown_fallback": 4,
                "rejected": 5,
            }
        ),
        _repaint_metrics={
            "counts": {
                "total": 6,
                "ingest": 7,
                "purge": 8,
                "plugin_group_clear": 9,
                "override_reload": 10,
                "override_payload": 11,
                "controller_target": 12,
                "explicit_refresh": 13,
                "other": 14,
                "immediate": 15,
                "debounce_started": 16,
                "debounce_coalesced": 17,
                "backend_refresh": 18,
                "qt_update": 19,
            }
        },
        _paint_stats={"paint_count": 20},
        _shell_raster_frame_work_counts={
            "requests": 21,
            "builds": 22,
            "unchanged_reuses": 23,
            "uncacheable": 24,
            "failures": 25,
        },
        _backend_work_counts={
            "cycles": 26,
            "helper_health_calls": 27,
            "helper_target_calls": 28,
            "helper_presentation_calls": 29,
        },
        _data_client=_DataClient(),
    )


def test_current_pressure_snapshot_maps_only_fixed_counters(monkeypatch) -> None:
    monkeypatch.setattr("overlay_client.control_surface.time.monotonic_ns", lambda: 123)
    window = _window_stub()

    snapshot = ControlSurfaceMixin.current_pressure_snapshot(window)

    assert tuple(snapshot["counters"]) == WORK_COUNTER_KEYS
    assert snapshot["captured_at_ns"] == 123
    assert snapshot["counters"]["ingest_lifecycle_refresh"] == 2
    assert snapshot["counters"]["repaint_qt_update"] == 19
    assert snapshot["counters"]["qt_paints"] == 20
    assert snapshot["counters"]["frame_unchanged_reuses"] == 23
    assert snapshot["counters"]["helper_target_calls"] == 28


def test_send_current_pressure_snapshot_uses_existing_client_channel(monkeypatch) -> None:
    monkeypatch.setattr("overlay_client.control_surface.time.monotonic_ns", lambda: 456)
    window = _window_stub()
    window.current_pressure_snapshot = lambda: ControlSurfaceMixin.current_pressure_snapshot(window)

    sent = ControlSurfaceMixin.send_current_pressure_snapshot(window, "request-1")

    assert sent is True
    assert window._data_client.payloads == [
        {
            "cli": "client_runtime_pressure_snapshot",
            "request_id": "request-1",
            "snapshot": window.current_pressure_snapshot(),
        }
    ]


def test_backend_work_counts_accumulate_generic_helper_work_without_logging() -> None:
    target = SimpleNamespace(
        _backend_work_counts={
            "cycles": 0,
            "helper_health_calls": 0,
            "helper_target_calls": 0,
            "helper_presentation_calls": 0,
        }
    )
    result = BackendPresentationCycleResult(
        should_show_overlay=True,
        diagnostics={
            "health_cache_hit": False,
            "target_poll_skipped": False,
            "presentation_skipped": False,
            "attempts": 2,
        },
    )

    _record_backend_work_counts(target, result)

    assert target._backend_work_counts == {
        "cycles": 1,
        "helper_health_calls": 1,
        "helper_target_calls": 1,
        "helper_presentation_calls": 2,
    }
