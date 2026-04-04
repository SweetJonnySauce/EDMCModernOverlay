from __future__ import annotations

import overlay_controller.overlay_controller as oc


class _Bridge:
    def __init__(self, response):
        self._response = response
        self.calls = 0

    def backend_status(self):
        self.calls += 1
        return self._response


def test_update_backend_status_title_keeps_base_controller_title() -> None:
    app = object.__new__(oc.OverlayConfigApp)
    app._base_window_title = "Overlay Controller"
    captured: list[str] = []
    app.title = lambda value: captured.append(value)

    oc.OverlayConfigApp._update_backend_status_title(
        app,
        {
            "selected_backend": {"family": "native_wayland", "instance": "kwin_wayland"},
            "classification": "true_overlay",
            "shadow_mode": True,
            "helper_states": [],
            "review_required": False,
            "review_reasons": [],
        },
    )

    assert captured == ["Overlay Controller"]


def test_refresh_backend_status_cache_updates_snapshot_and_title() -> None:
    app = object.__new__(oc.OverlayConfigApp)
    app._base_window_title = "Overlay Controller"
    app._backend_status_snapshot = {}
    app._last_backend_status_refresh_ts = 0.0
    app._plugin_bridge = _Bridge(
        {
            "status": "ok",
            "backend_status": {
                "selected_backend": {"family": "xwayland_compat", "instance": "xwayland_compat"},
                "classification": "degraded_overlay",
                "fallback_from": {"family": "native_wayland", "instance": "kwin_wayland"},
                "fallback_reason": "xwayland_compat_only",
                "shadow_mode": True,
                "helper_states": [],
                "review_required": False,
                "review_reasons": [],
            },
        }
    )
    captured: list[str] = []
    app.title = lambda value: captured.append(value)

    oc.OverlayConfigApp._refresh_backend_status_cache(app, force=True)

    assert app._plugin_bridge.calls == 1
    assert app._backend_status_snapshot["classification"] == "degraded_overlay"
    assert captured[-1] == "Overlay Controller"
