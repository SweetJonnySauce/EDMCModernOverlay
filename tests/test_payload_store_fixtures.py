from __future__ import annotations

from pathlib import Path

import pytest

from tests.payload_log_fixtures import load_payloads_from_log, sample_payload_logs


@pytest.mark.parametrize("log_path", list(sample_payload_logs()), ids=lambda p: Path(p).name)
def test_sample_payload_logs_parse_into_overlay_payloads(log_path: Path) -> None:
    payloads = load_payloads_from_log(log_path, max_payloads=200)
    assert payloads

    for payload in payloads:
        event = str(payload.get("event") or "")
        payload_type = str(payload.get("type") or "")
        payload_id = str(payload.get("id") or "")

        assert event
        assert payload_type in {"message", "shape", "LegacyOverlay", "OverlayMetrics", "OverlayConfig"} or bool(
            payload_type
        )
        assert payload_id

        ttl = payload.get("ttl")
        if isinstance(ttl, (int, float)):
            assert ttl >= 0

        if payload_type == "shape":
            assert any(
                key in payload for key in ("shape", "vector", "w", "h")
            )


def test_ttl_override_applies_to_replayed_payloads() -> None:
    landingpad = next(iter(sample_payload_logs()))
    payloads = load_payloads_from_log(landingpad, ttl_override=9, max_payloads=25)
    assert payloads
    assert all(int(payload.get("ttl")) == 9 for payload in payloads if "ttl" in payload)


def test_edr_fixture_contains_messages_and_shapes() -> None:
    logs = list(sample_payload_logs())
    edr_path = next(path for path in logs if path.name == "edr_docking.log")
    payloads = load_payloads_from_log(edr_path, max_payloads=200)
    message_count = sum(1 for payload in payloads if str(payload.get("type") or "").lower() == "message")
    shape_count = sum(1 for payload in payloads if str(payload.get("type") or "").lower() == "shape")
    assert message_count > 0
    assert shape_count > 0
