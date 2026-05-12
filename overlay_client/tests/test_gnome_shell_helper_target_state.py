import json

from overlay_client.backend import (
    GNOME_SHELL_HELPER_CAPABILITIES,
    GNOME_SHELL_HELPER_COORDINATE_SPACE,
    GNOME_SHELL_HELPER_RECT_SOURCE_FRAME_FALLBACK,
    HELPER_KIND,
    HELPER_PROTOCOL,
    HELPER_VERSION,
    HelperRect,
    HelperHealthState,
    HelperTargetState,
    probe_gnome_shell_helper_target,
    resolve_gnome_shell_helper_target_rect,
    select_elite_dangerous_target,
    validate_gnome_shell_helper_health_payload,
    validate_gnome_shell_helper_target_payload,
)


def _health_status(**overrides: object):
    payload: dict[str, object] = {
        "status": "healthy",
        "helper_kind": HELPER_KIND.value,
        "helper_version": HELPER_VERSION,
        "helper_protocol": HELPER_PROTOCOL,
        "capabilities": list(GNOME_SHELL_HELPER_CAPABILITIES),
    }
    payload.update(overrides)
    return validate_gnome_shell_helper_health_payload(
        payload,
        observed_at_monotonic=100.0,
        now_monotonic=100.0,
    )


def _target_window(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "targetToken": "meta:21",
        "title": "Elite - Dangerous (CLIENT)",
        "wmClass": "steam_app_359320",
        "wmClassInstance": "steam_app_359320",
        "appId": "steam_app_359320",
        "appName": "steam_app_359320",
        "pid": 9135,
        "windowType": 0,
        "frameRect": {"x": 0, "y": 0, "width": 3440, "height": 1440},
        "bufferRect": {"x": 0, "y": 0, "width": 3440, "height": 1440},
        "contentRect": {"x": 0, "y": 0, "width": 3440, "height": 1440},
        "decorationInsets": {"left": 0, "top": 0, "right": 0, "bottom": 0},
        "monitor": 0,
        "outputName": "DP-2",
        "monitorRect": {"x": 0, "y": 0, "width": 3440, "height": 1440},
        "monitorScale": 1.0,
        "hasFocus": True,
        "showingOnWorkspace": True,
        "minimized": False,
        "fullscreen": True,
        "workspace": "0",
    }
    payload.update(overrides)
    return payload


def _target_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "status": "target_found",
        "helper_kind": HELPER_KIND.value,
        "helper_version": HELPER_VERSION,
        "helper_protocol": HELPER_PROTOCOL,
        "coordinate_space": GNOME_SHELL_HELPER_COORDINATE_SPACE,
        "sequence": 3,
        "generated_at_monotonic_us": 123456,
        "generated_at_unix_ms": 1800000000000,
        "candidate_count": 1,
        "launcher_count": 1,
        "target": _target_window(),
    }
    payload.update(overrides)
    return payload


def test_validate_gnome_shell_helper_target_accepts_borderless_geometry() -> None:
    status = validate_gnome_shell_helper_target_payload(
        (json.dumps(_target_payload()),),
        health_status=_health_status(),
        observed_at_monotonic=200.0,
        now_monotonic=200.5,
    )

    assert status.state is HelperTargetState.FOUND
    assert status.found is True
    assert status.coordinate_space == GNOME_SHELL_HELPER_COORDINATE_SPACE
    assert status.sequence == 3
    assert status.candidate_count == 1
    assert status.launcher_count == 1
    assert status.target is not None
    assert status.target.target_token == "meta:21"
    assert status.target.monitor_rect == HelperRect(x=0, y=0, width=3440, height=1440)
    assert status.target.to_payload()["monitor_rect"] == {"x": 0, "y": 0, "width": 3440, "height": 1440}
    assert status.target.content_rect is not None
    assert status.target.content_rect.to_payload() == {"x": 0, "y": 0, "width": 3440, "height": 1440}
    assert status.target.decoration_insets is not None
    assert status.target.decoration_insets.to_payload() == {"left": 0, "top": 0, "right": 0, "bottom": 0}


def test_validate_gnome_shell_helper_target_accepts_windowed_content_rect_and_insets() -> None:
    status = validate_gnome_shell_helper_target_payload(
        _target_payload(
            target=_target_window(
                frameRect={"x": 1080, "y": 216, "width": 1280, "height": 997},
                bufferRect={"x": 1066, "y": 204, "width": 1308, "height": 1026},
                contentRect={"x": 1080, "y": 253, "width": 1280, "height": 960},
                decorationInsets={"left": 0, "top": 37, "right": 0, "bottom": 0},
                fullscreen=False,
            )
        ),
        health_status=_health_status(),
        observed_at_monotonic=200.0,
        now_monotonic=200.0,
    )

    assert status.state is HelperTargetState.FOUND
    assert status.target is not None
    assert status.target.frame_rect is not None
    assert status.target.frame_rect.y == 216
    assert status.target.content_rect is not None
    assert status.target.content_rect.y == 253
    assert status.target.decoration_insets is not None
    assert status.target.decoration_insets.top == 37


def test_validate_gnome_shell_helper_target_accepts_geometry_without_content_rect_for_frame_fallback() -> None:
    target = _target_window()
    target.pop("contentRect")
    target.pop("decorationInsets")

    status = validate_gnome_shell_helper_target_payload(
        _target_payload(target=target),
        health_status=_health_status(),
        observed_at_monotonic=200.0,
        now_monotonic=200.0,
    )
    resolution = resolve_gnome_shell_helper_target_rect(status)

    assert status.state is HelperTargetState.FOUND
    assert status.found is True
    assert status.target is not None
    assert status.target.content_rect is None
    assert status.target.decoration_insets is None
    assert resolution.resolved is True
    assert resolution.source == GNOME_SHELL_HELPER_RECT_SOURCE_FRAME_FALLBACK
    assert resolution.degrade_reasons == (GNOME_SHELL_HELPER_RECT_SOURCE_FRAME_FALLBACK,)


def test_validate_gnome_shell_helper_target_reports_not_found_launcher_only_and_ambiguous() -> None:
    health = _health_status()

    for state in ("target_not_found", "launcher_only", "target_ambiguous"):
        status = validate_gnome_shell_helper_target_payload(
            _target_payload(status=state, target=None, candidate_count=0, launcher_count=1),
            health_status=health,
            observed_at_monotonic=200.0,
            now_monotonic=200.0,
        )
        assert status.state is HelperTargetState(state)
        assert status.found is False


def test_validate_gnome_shell_helper_target_fails_closed_when_health_is_unhealthy() -> None:
    unhealthy = _health_status(status="inactive")

    status = validate_gnome_shell_helper_target_payload(
        _target_payload(),
        health_status=unhealthy,
        observed_at_monotonic=200.0,
        now_monotonic=200.0,
    )

    assert unhealthy.state is HelperHealthState.INACTIVE
    assert status.state is HelperTargetState.HELPER_UNHEALTHY
    assert status.detail == "inactive"


def test_validate_gnome_shell_helper_target_rejects_stale_observation() -> None:
    status = validate_gnome_shell_helper_target_payload(
        _target_payload(),
        health_status=_health_status(),
        observed_at_monotonic=200.0,
        now_monotonic=203.0,
        stale_after_seconds=2.0,
    )

    assert status.state is HelperTargetState.STALE
    assert status.is_stale(203.0) is True


def test_probe_gnome_shell_helper_target_maps_transport_errors_to_unhealthy() -> None:
    inactive = _health_status(status="disabled")

    status = probe_gnome_shell_helper_target(
        lambda: _target_payload(),
        health_status=inactive,
        clock=lambda: 200.0,
    )

    assert status.state is HelperTargetState.HELPER_UNHEALTHY
    assert status.detail == "inactive"


def test_select_elite_dangerous_target_rejects_launcher_only_and_ambiguous_candidates() -> None:
    launcher = {
        "title": "elite launcher",
        "wmClass": "steam_app_359320",
        "frameRect": {"x": 1080, "y": 360, "width": 1280, "height": 720},
    }
    client = _target_window()

    launcher_only = select_elite_dangerous_target([launcher])
    ambiguous = select_elite_dangerous_target([client, {**client, "targetToken": "meta:22"}])
    found = select_elite_dangerous_target([launcher, client])

    assert launcher_only["status"] == "launcher_only"
    assert ambiguous["status"] == "target_ambiguous"
    assert found["status"] == "target_found"
    assert found["target"] == client
