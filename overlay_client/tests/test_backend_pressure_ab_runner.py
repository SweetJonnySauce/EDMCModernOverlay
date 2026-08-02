from __future__ import annotations

import json

import pytest

from scripts.backend_pressure_ab import (
    CaptureError,
    _decode_gdbus_json,
    _distribution,
    _normalized_warning_counts,
    _read_port,
)


def test_decode_gdbus_health_tuple_keeps_only_decoded_mapping() -> None:
    payload = {
        "status": "healthy",
        "pressure_counters": {"target_queries": 2, "presentation_calls": 1},
    }
    encoded = repr((json.dumps(payload),))

    assert _decode_gdbus_json(encoded) == payload


def test_decode_gdbus_health_rejects_non_mapping_payload() -> None:
    with pytest.raises(CaptureError, match="malformed"):
        _decode_gdbus_json("[]")


def test_distribution_uses_nearest_rank_p95_and_bounded_summary() -> None:
    assert _distribution((1.0, 3.0, 2.0)) == {
        "count": 3,
        "median": 2.0,
        "p95": 3.0,
        "minimum": 1.0,
        "maximum": 3.0,
    }


def test_port_metadata_rejects_non_integer_port(tmp_path) -> None:
    path = tmp_path / "port.json"
    path.write_text('{"port": true}', encoding="utf-8")

    with pytest.raises(CaptureError, match="invalid port"):
        _read_port(path)


def test_warning_collection_discards_text_and_returns_only_normalized_counts(monkeypatch) -> None:
    result = type(
        "Result",
        (),
        {
            "returncode": 0,
            "stdout": "Mutter assertion failed private detail\ngnome-shell WARNING private detail\n",
        },
    )()
    monkeypatch.setattr("scripts.backend_pressure_ab.shutil.which", lambda _name: "/usr/bin/journalctl")
    monkeypatch.setattr("scripts.backend_pressure_ab.subprocess.run", lambda *_args, **_kwargs: result)

    assert _normalized_warning_counts(1.0) == {
        "available": True,
        "mutter_assertions": 1,
        "shell_warnings": 1,
    }
