import json

import pytest

from overlay_client.backend import (
    GNOME_SHELL_HELPER_CAPABILITIES,
    HELPER_KIND,
    HELPER_PROTOCOL,
    HELPER_VERSION,
    HelperDbusProbeError,
    HelperDbusServiceMissing,
    HelperHealthState,
    probe_gnome_shell_helper_health,
    validate_gnome_shell_helper_health_payload,
)


def _health_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "status": "healthy",
        "helper_kind": HELPER_KIND.value,
        "helper_version": HELPER_VERSION,
        "helper_protocol": HELPER_PROTOCOL,
        "capabilities": list(GNOME_SHELL_HELPER_CAPABILITIES),
    }
    payload.update(overrides)
    return payload


def test_validate_gnome_shell_helper_health_accepts_valid_mapping() -> None:
    status = validate_gnome_shell_helper_health_payload(
        _health_payload(),
        observed_at_monotonic=100.0,
        now_monotonic=101.0,
    )

    assert status.state is HelperHealthState.HEALTHY
    assert status.healthy is True
    assert status.helper_kind is HELPER_KIND
    assert status.helper_version == HELPER_VERSION
    assert status.helper_protocol == HELPER_PROTOCOL
    assert status.capabilities == tuple(sorted(GNOME_SHELL_HELPER_CAPABILITIES))
    assert status.to_payload()["healthy"] is True


def test_validate_gnome_shell_helper_health_accepts_valid_json_string() -> None:
    status = validate_gnome_shell_helper_health_payload(
        json.dumps(_health_payload()),
        observed_at_monotonic=100.0,
        now_monotonic=100.0,
    )

    assert status.state is HelperHealthState.HEALTHY


def test_validate_gnome_shell_helper_health_accepts_single_value_dbus_tuple() -> None:
    status = validate_gnome_shell_helper_health_payload(
        (json.dumps(_health_payload()),),
        observed_at_monotonic=100.0,
        now_monotonic=100.0,
    )

    assert status.state is HelperHealthState.HEALTHY


def test_validate_gnome_shell_helper_health_accepts_gdbus_tuple_output_string() -> None:
    status = validate_gnome_shell_helper_health_payload(
        f"('{json.dumps(_health_payload())}',)",
        observed_at_monotonic=100.0,
        now_monotonic=100.0,
    )

    assert status.state is HelperHealthState.HEALTHY


@pytest.mark.parametrize("raw_health", ["not-json", ["unexpected", "tuple"], 123, {"status": "healthy"}])
def test_validate_gnome_shell_helper_health_rejects_malformed_payloads(raw_health: object) -> None:
    status = validate_gnome_shell_helper_health_payload(
        raw_health,
        observed_at_monotonic=100.0,
        now_monotonic=100.0,
    )

    assert status.state is HelperHealthState.MALFORMED_PAYLOAD
    assert status.healthy is False


def test_validate_gnome_shell_helper_health_rejects_wrong_helper_kind() -> None:
    status = validate_gnome_shell_helper_health_payload(
        _health_payload(helper_kind="kwin_script"),
        observed_at_monotonic=100.0,
        now_monotonic=100.0,
    )

    assert status.state is HelperHealthState.HELPER_KIND_MISMATCH
    assert status.healthy is False


def test_validate_gnome_shell_helper_health_rejects_version_mismatch() -> None:
    status = validate_gnome_shell_helper_health_payload(
        _health_payload(helper_version="0.0.0"),
        observed_at_monotonic=100.0,
        now_monotonic=100.0,
    )

    assert status.state is HelperHealthState.VERSION_INCOMPATIBLE
    assert status.detail == f"expected version={HELPER_VERSION}"


@pytest.mark.parametrize("protocol", [0, HELPER_PROTOCOL + 1])
def test_validate_gnome_shell_helper_health_rejects_protocol_mismatch(protocol: int) -> None:
    status = validate_gnome_shell_helper_health_payload(
        _health_payload(helper_protocol=protocol),
        observed_at_monotonic=100.0,
        now_monotonic=100.0,
    )

    assert status.state is HelperHealthState.PROTOCOL_INCOMPATIBLE
    assert status.healthy is False


def test_validate_gnome_shell_helper_health_rejects_missing_capability() -> None:
    status = validate_gnome_shell_helper_health_payload(
        _health_payload(capabilities=["hello", "health"]),
        observed_at_monotonic=100.0,
        now_monotonic=100.0,
    )

    assert status.state is HelperHealthState.CAPABILITY_MISSING
    assert status.missing_capabilities == (
        "version",
        "protocol",
        "capabilities",
        "target_state",
        "presentation_state",
    )


def test_validate_gnome_shell_helper_health_rejects_stale_observation() -> None:
    status = validate_gnome_shell_helper_health_payload(
        _health_payload(),
        observed_at_monotonic=100.0,
        now_monotonic=111.0,
        stale_after_seconds=10.0,
    )

    assert status.state is HelperHealthState.STALE
    assert status.is_stale(111.0) is True


@pytest.mark.parametrize(
    ("payload_status", "expected_state"),
    [
        ("inactive", HelperHealthState.INACTIVE),
        ("disabled", HelperHealthState.INACTIVE),
        ("error", HelperHealthState.ERROR),
        ("failed", HelperHealthState.ERROR),
    ],
)
def test_validate_gnome_shell_helper_health_reports_inactive_and_error_states(
    payload_status: str,
    expected_state: HelperHealthState,
) -> None:
    status = validate_gnome_shell_helper_health_payload(
        _health_payload(status=payload_status, detail="extension state"),
        observed_at_monotonic=100.0,
        now_monotonic=100.0,
    )

    assert status.state is expected_state
    assert status.healthy is False


def test_probe_gnome_shell_helper_health_maps_missing_service() -> None:
    def fetch_health() -> object:
        raise HelperDbusServiceMissing("service not owned")

    status = probe_gnome_shell_helper_health(fetch_health)

    assert status.state is HelperHealthState.MISSING_SERVICE
    assert status.healthy is False


def test_probe_gnome_shell_helper_health_maps_unreachable_dbus() -> None:
    def fetch_health() -> object:
        raise HelperDbusProbeError("session bus unavailable")

    status = probe_gnome_shell_helper_health(fetch_health)

    assert status.state is HelperHealthState.DBUS_UNREACHABLE
    assert status.healthy is False


def test_probe_gnome_shell_helper_health_validates_successful_fetch() -> None:
    status = probe_gnome_shell_helper_health(
        lambda: _health_payload(),
        clock=lambda: 100.0,
    )

    assert status.state is HelperHealthState.HEALTHY
    assert status.observed_at_monotonic == 100.0
