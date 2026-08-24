from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, Mapping

import pytest

from scripts.backend_pressure_ab import (
    CaptureProviders,
    CaptureError,
    CaptureStopped,
    CaptureTiming,
    SafetyTracker,
    _build_cell_document,
    _build_stop_document,
    _capture,
    _decode_gdbus_json,
    _distribution,
    _gpu_sample,
    _helper_owner_present,
    _helper_snapshot,
    _normalized_warning_counts,
    _process_snapshot,
    _read_port,
    _request_client_backend_status,
    _request_client_snapshot,
    _runner_cell_state,
    _sample_processes,
    _validate_client_backend_status,
    _validate_client_arguments,
    _write_new_json,
    main,
)
from overlay_client.backend.pressure_ab import WORK_COUNTER_KEYS, parse_pressure_ab_cell_document
from overlay_client.backend.helper_ipc import HelperDbusProbeError
from overlay_client.work_counters import WORK_COUNTER_MAX


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


@pytest.mark.parametrize("payload", ["('not-json',)", "(123,)"])
def test_decode_gdbus_health_rejects_malformed_tuple_payload(payload: str) -> None:
    with pytest.raises(CaptureError, match="malformed"):
        _decode_gdbus_json(payload)


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
    rows = (
        {
            "MESSAGE": "assertion failed private detail",
            "_COMM": "mutter",
            "GLIB_DOMAIN": "mutter",
            "PRIORITY": "3",
        },
        {
            "MESSAGE": "private detail",
            "SYSLOG_IDENTIFIER": "gnome-shell",
            "PRIORITY": "4",
        },
        {
            "MESSAGE": "assertion failed unrelated private detail",
            "_COMM": "unrelated",
            "PRIORITY": "3",
        },
    )
    result = type(
        "Result",
        (),
        {
            "returncode": 0,
            "stdout": "\n".join(json.dumps(row) for row in rows),
            "stderr": "",
        },
    )()
    captured = {}
    monkeypatch.setattr("scripts.backend_pressure_ab.shutil.which", lambda _name: "/usr/bin/journalctl")

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return result

    monkeypatch.setattr("scripts.backend_pressure_ab.subprocess.run", fake_run)

    assert _normalized_warning_counts(1.0, 2.0) == {
        "available": True,
        "mutter_assertions": 1,
        "shell_warnings": 1,
    }
    assert captured["command"] == [
        "journalctl",
        "--user",
        "--since",
        "@1.000000",
        "--until",
        "@2.000000",
        "--output=json",
        "--no-pager",
    ]
    assert captured["kwargs"]["timeout"] == 5.0


@pytest.mark.parametrize("failure", ["timeout", "nonzero", "malformed", "reversed"])
def test_warning_collection_fails_cleanly_without_raw_text(monkeypatch, failure: str) -> None:
    monkeypatch.setattr("scripts.backend_pressure_ab.shutil.which", lambda _name: "/usr/bin/journalctl")
    private = "/home/private/raw-journal-value"

    def fake_run(*_args, **_kwargs):
        if failure == "timeout":
            raise subprocess.TimeoutExpired("journalctl", 5.0, output=private)
        if failure == "nonzero":
            return SimpleNamespace(returncode=1, stdout="", stderr=private)
        return SimpleNamespace(returncode=0, stdout=private, stderr="")

    monkeypatch.setattr("scripts.backend_pressure_ab.subprocess.run", fake_run)
    start, end = (2.0, 1.0) if failure == "reversed" else (1.0, 2.0)

    with pytest.raises(CaptureError) as captured:
        _normalized_warning_counts(start, end)

    assert private not in str(captured.value)


def test_warning_collection_rejects_saturation_instead_of_clamping(monkeypatch) -> None:
    row = json.dumps(
        {
            "MESSAGE": "assertion failed",
            "_COMM": "gnome-shell",
            "GLIB_DOMAIN": "mutter",
            "PRIORITY": "3",
        }
    )
    result = SimpleNamespace(returncode=0, stdout="\n".join([row] * 2), stderr="")
    monkeypatch.setattr("scripts.backend_pressure_ab.shutil.which", lambda _name: "/usr/bin/journalctl")
    monkeypatch.setattr("scripts.backend_pressure_ab.WORK_COUNTER_MAX", 2)
    monkeypatch.setattr("scripts.backend_pressure_ab.subprocess.run", lambda *_args, **_kwargs: result)

    with pytest.raises(CaptureError, match="saturated"):
        _normalized_warning_counts(1.0, 2.0)


def test_warning_collection_returns_explicit_unavailable_when_binary_is_absent(monkeypatch) -> None:
    monkeypatch.setattr("scripts.backend_pressure_ab.shutil.which", lambda _name: None)

    assert _normalized_warning_counts(1.0, 2.0) == {
        "available": False,
        "mutter_assertions": 0,
        "shell_warnings": 0,
    }


def test_helper_owner_probe_accepts_only_exact_name_has_owner_result(monkeypatch) -> None:
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout="(false,)\n", stderr="")

    monkeypatch.setattr("scripts.backend_pressure_ab.subprocess.run", fake_run)

    assert _helper_owner_present() is False
    assert captured["command"][-2:] == [
        "org.freedesktop.DBus.NameHasOwner",
        "org.edmc.ModernOverlay.Helper",
    ]
    assert captured["kwargs"]["timeout"] == 2.0


@pytest.mark.parametrize("kind", ["true", "malformed", "nonzero", "timeout"])
def test_helper_disabled_probe_never_coerces_uncertainty_to_absence(monkeypatch, kind: str) -> None:
    def fake_run(*_args, **_kwargs):
        if kind == "timeout":
            raise subprocess.TimeoutExpired("gdbus", 2.0)
        if kind == "nonzero":
            return SimpleNamespace(returncode=1, stdout="", stderr="private diagnostic")
        stdout = "(true,)" if kind == "true" else "private malformed output"
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

    monkeypatch.setattr("scripts.backend_pressure_ab.subprocess.run", fake_run)

    if kind == "true":
        assert _helper_owner_present() is True
    else:
        with pytest.raises(CaptureError, match="helper owner probe"):
            _helper_owner_present()


def _raw_helper_health(**overrides) -> dict[str, object]:
    payload: dict[str, object] = {
        "status": "healthy",
        "helper_kind": "gnome_shell_extension",
        "helper_version": "4.0.0",
        "helper_protocol": 3,
        "service_name": "org.edmc.ModernOverlay.Helper",
        "feature_gate": {"mode": "full_helper", "diagnostics_enabled": False},
        "started_at_monotonic_us": 10,
        "pressure_counters": {"target_queries": 1, "presentation_calls": 2},
        "actor_counts": {
            "shell_actor_proof_visible": True,
            "shell_raster_frame_visible": False,
            "shell_raster_region_count": 1,
        },
    }
    payload.update(overrides)
    return payload


def test_helper_snapshot_requires_exact_healthy_identity_and_quiet_mode(monkeypatch) -> None:
    monkeypatch.setattr(
        "scripts.backend_pressure_ab.fetch_gnome_shell_helper_health_via_gdbus",
        lambda: _raw_helper_health(),
    )

    assert _helper_snapshot() == {
        "origin": 10,
        "counters": {"target_queries": 1, "presentation_calls": 2},
        "actors": {
            "shell_actor_proof_visible": 1,
            "shell_raster_frame_visible": 0,
            "shell_raster_region_count": 1,
        },
    }


@pytest.mark.parametrize(
    "mutation",
    [
        lambda payload: payload.pop("status"),
        lambda payload: payload.update(status="inactive"),
        lambda payload: payload.update(helper_kind="wrong_helper"),
        lambda payload: payload.update(helper_protocol=99),
        lambda payload: payload.update(service_name="wrong.service"),
        lambda payload: payload["feature_gate"].update(diagnostics_enabled=True),
    ],
)
def test_helper_snapshot_rejects_wrong_identity_or_mode(monkeypatch, mutation) -> None:
    payload = _raw_helper_health()
    mutation(payload)
    monkeypatch.setattr(
        "scripts.backend_pressure_ab.fetch_gnome_shell_helper_health_via_gdbus",
        lambda: payload,
    )

    with pytest.raises(CaptureError, match="helper"):
        _helper_snapshot()


def test_helper_snapshot_normalizes_transport_failure(monkeypatch) -> None:
    def failed_fetch() -> object:
        raise HelperDbusProbeError("/home/private/raw-helper-error")

    monkeypatch.setattr(
        "scripts.backend_pressure_ab.fetch_gnome_shell_helper_health_via_gdbus",
        failed_fetch,
    )

    with pytest.raises(CaptureError) as captured:
        _helper_snapshot()

    assert "/home/private" not in str(captured.value)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda payload: payload["pressure_counters"].update(target_queries=True),
        lambda payload: payload["pressure_counters"].update(presentation_calls=1_000_001),
        lambda payload: payload["actor_counts"].update(shell_actor_proof_visible=1),
        lambda payload: payload["actor_counts"].update(shell_raster_region_count=1025),
        lambda payload: payload.update(started_at_monotonic_us=True),
        lambda payload: payload.update(started_at_monotonic_us=-1),
    ],
)
def test_helper_snapshot_rejects_malformed_counter_actor_or_origin(monkeypatch, mutation) -> None:
    payload = _raw_helper_health()
    mutation(payload)
    monkeypatch.setattr(
        "scripts.backend_pressure_ab.fetch_gnome_shell_helper_health_via_gdbus",
        lambda: payload,
    )

    with pytest.raises(CaptureError, match="helper"):
        _helper_snapshot()


@pytest.mark.parametrize(
    ("cell", "client_pid", "port_file", "valid"),
    [
        ("A1", None, None, True),
        ("A2", 123, "port.json", True),
        ("A2", 123, None, False),
        ("A2", None, "port.json", False),
        ("A1", 123, "port.json", False),
    ],
)
def test_runner_requires_exact_client_pid_and_port_file_pair(
    cell: str,
    client_pid: int | None,
    port_file: str | None,
    valid: bool,
) -> None:
    if valid:
        _validate_client_arguments(cell, client_pid=client_pid, port_file=port_file)
    else:
        with pytest.raises(CaptureError, match="client argument"):
            _validate_client_arguments(cell, client_pid=client_pid, port_file=port_file)


def _strict_runner_args(**overrides) -> SimpleNamespace:
    values = {
        "cell": "B2",
        "client_backend_state": "helper_selected",
        "execution_order": 3,
        "fixture_sha256": "1" * 64,
        "source_revision": "2" * 40,
        "plugin_version": "2.0.0",
        "client_version": "2.0.0",
        "helper_version": "4.0.0",
        "display_width_px": 1920,
        "display_height_px": 1080,
        "refresh_hz": 60.0,
        "quiet_host_confirmed": True,
        "operator_observing": True,
        "shell_pid": 101,
        "client_pid": 202,
        "port_file": Path("port.json"),
        "output": Path("B2.json"),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_runner_cell_document_is_validated_in_its_direct_output_shape(monkeypatch) -> None:
    captured = []
    monkeypatch.setattr(
        "scripts.backend_pressure_ab.parse_pressure_ab_cell_document",
        lambda document: captured.append(document),
    )

    document = _build_cell_document(_strict_runner_args(), [{"runner_nested_sample": True}])

    assert captured == [document]
    assert document == {
        "schema_version": 1,
        "cell": "B2",
        "execution_order": 3,
        "provenance": {
            "fixture_sha256": "1" * 64,
            "source_revision": "2" * 40,
            "component_versions": {"plugin": "2.0.0", "client": "2.0.0", "helper": "4.0.0"},
            "display": {
                "monitor": "A",
                "width_px": 1920,
                "height_px": 1080,
                "scale_percent": 100,
                "refresh_hz": 60.0,
            },
            "workload": "stable_windowed_fixed_fixture",
            "quiet_host": True,
        },
        "state": {
            "client": "running",
            "helper": "full_helper",
            "client_backend": "helper_selected",
            "client_pid_argument": "provided",
            "port_file_argument": "provided",
            "capture_diagnostics_enabled": False,
            "helper_diagnostics_enabled": False,
        },
        "samples": [{"runner_nested_sample": True}],
    }


@pytest.mark.parametrize(
    ("cell", "backend_state"),
    [
        ("A1", "helper_selected"),
        ("A2", "helper_selected"),
        ("B2", "documented_unavailable"),
    ],
)
def test_runner_rejects_wrong_declared_client_backend_state(cell: str, backend_state: str) -> None:
    with pytest.raises(CaptureError, match="backend state"):
        _runner_cell_state(_strict_runner_args(cell=cell, client_backend_state=backend_state))


def _runtime_backend_status(*, helper_available: bool) -> dict[str, object]:
    helper_state = {
        "helper": "gnome_shell_extension",
        "required": True,
        "installed": helper_available,
        "enabled": helper_available,
        "approved": helper_available,
        "version": "4.0.0" if helper_available else "",
        "detail": "health_state=healthy" if helper_available else "health_state=missing_service",
    }
    status: dict[str, object] = {
        "selected_backend": {
            "family": "compositor_helper" if helper_available else "native_wayland",
            "instance": "gnome_shell_wayland",
        },
        "classification": "degraded_overlay",
        "shadow_mode": False,
        "helper_states": [helper_state],
        "report": {"source": "client_runtime"},
    }
    if not helper_available:
        status["fallback_from"] = {
            "family": "compositor_helper",
            "instance": "gnome_shell_wayland",
        }
        status["fallback_reason"] = "missing_helper"
    return status


@pytest.mark.parametrize("cell", ["A2", "B2"])
def test_client_backend_state_requires_live_exact_route_proof(cell: str) -> None:
    status = _runtime_backend_status(helper_available=cell == "B2")

    assert _validate_client_backend_status(cell, status) is None


@pytest.mark.parametrize(
    "mutation",
    [
        lambda status: status.update(shadow_mode=True),
        lambda status: status["report"].update(source="plugin_hint"),
        lambda status: status["selected_backend"].update(instance="xwayland_compat"),
        lambda status: status.update(fallback_reason="manual_override"),
        lambda status: status.update(helper_states=[]),
        lambda status: status["helper_states"][0].update(installed=True),
    ],
)
def test_client_backend_state_rejects_shadow_stale_or_wrong_route(
    mutation: Callable[[dict[str, object]], None],
) -> None:
    status = _runtime_backend_status(helper_available=False)
    mutation(status)

    with pytest.raises(CaptureError, match="runtime backend state"):
        _validate_client_backend_status("A2", status)


def test_b2_client_backend_state_requires_versioned_available_helper() -> None:
    status = _runtime_backend_status(helper_available=True)
    status["helper_states"][0]["version"] = ""

    with pytest.raises(CaptureError, match="runtime backend state"):
        _validate_client_backend_status("B2", status)


def test_client_backend_status_primes_then_requires_live_runtime_response(monkeypatch) -> None:
    responses = iter(
        (
            {"status": "ok", "backend_status": {"report": {"source": "plugin_hint"}}},
            {"status": "ok", "backend_status": _runtime_backend_status(helper_available=True)},
        )
    )
    sleeps = []
    monkeypatch.setattr("scripts.backend_pressure_ab._request_client_command", lambda *_args: next(responses))
    monkeypatch.setattr("scripts.backend_pressure_ab.time.sleep", lambda seconds: sleeps.append(seconds))

    assert _request_client_backend_status(Path("port.json")) == _runtime_backend_status(helper_available=True)
    assert sleeps == [0.1]


def test_process_snapshot_parses_spaced_process_name_and_exact_aggregates(monkeypatch) -> None:
    fields = ["0"] * 20
    fields[0] = "S"
    fields[11] = "10"
    fields[12] = "5"
    fields[19] = "99"
    stat = f"123 (process name with spaces) {' '.join(fields)}"
    status = "\n".join(
        (
            "VmRSS:\t100 kB",
            "voluntary_ctxt_switches:\t2",
            "nonvoluntary_ctxt_switches:\t3",
        )
    )

    def read_text(path: Path, *, encoding: str) -> str:
        assert encoding == "utf-8"
        return stat if path.name == "stat" else status

    monkeypatch.setattr(Path, "read_text", read_text)

    assert _process_snapshot(123) == {
        "start_ticks": 99,
        "ticks": 15,
        "rss_kib": 100,
        "voluntary": 2,
        "involuntary": 3,
    }


@pytest.mark.parametrize("kind", ["missing", "short", "missing_status", "bounds"])
def test_process_snapshot_rejects_missing_malformed_or_out_of_bounds_data(monkeypatch, kind: str) -> None:
    private = "/home/private/process-detail"
    fields = ["0"] * 20
    fields[0] = "S"
    fields[11] = "10"
    fields[12] = "5"
    fields[19] = "99"
    stat = f"123 (private process name) {' '.join(fields)}"
    status = "\n".join(
        (
            f"VmRSS:\t{1_000_000_001 if kind == 'bounds' else 100} kB",
            "voluntary_ctxt_switches:\t2",
            "nonvoluntary_ctxt_switches:\t3",
        )
    )
    if kind == "short":
        stat = "123 (private process name) S 0"
    if kind == "missing_status":
        status = "VmRSS:\t100 kB"

    def read_text(path: Path, *, encoding: str) -> str:
        assert encoding == "utf-8"
        if kind == "missing":
            raise OSError(private)
        return stat if path.name == "stat" else status

    monkeypatch.setattr(Path, "read_text", read_text)

    with pytest.raises(CaptureError) as captured:
        _process_snapshot(123)

    assert private not in str(captured.value)


def test_client_snapshot_normalizes_malformed_and_transport_failures(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        "scripts.backend_pressure_ab._request_client_command",
        lambda *_args: {"status": "ok", "snapshot": {}},
    )
    with pytest.raises(CaptureError, match="malformed"):
        _request_client_snapshot(tmp_path / "port.json")

    port_file = tmp_path / "port.json"
    port_file.write_text('{"port": 32123}', encoding="utf-8")
    monkeypatch.undo()
    monkeypatch.setattr(
        "scripts.backend_pressure_ab.socket.create_connection",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("/home/private/socket")),
    )
    with pytest.raises(CaptureError) as captured:
        _request_client_snapshot(port_file)
    assert "/home/private" not in str(captured.value)


def test_client_backend_status_retry_exhaustion_is_bounded(monkeypatch) -> None:
    calls = []
    sleeps = []
    stale = {"status": "ok", "backend_status": {"report": {"source": "plugin_hint"}}}
    monkeypatch.setattr(
        "scripts.backend_pressure_ab._request_client_command",
        lambda *_args: calls.append("request") or stale,
    )
    monkeypatch.setattr("scripts.backend_pressure_ab.time.sleep", lambda seconds: sleeps.append(seconds))

    with pytest.raises(CaptureError, match="unavailable"):
        _request_client_backend_status(Path("port.json"))

    assert calls == ["request", "request", "request"]
    assert sleeps == [0.1, 0.1]


def test_gpu_provider_returns_explicit_unavailable_when_binary_is_absent(monkeypatch) -> None:
    monkeypatch.setattr("scripts.backend_pressure_ab.shutil.which", lambda _name: None)

    assert _gpu_sample() is None


def test_gpu_provider_aggregates_multiple_devices_with_bounded_values(monkeypatch) -> None:
    result = SimpleNamespace(returncode=0, stdout="20, 100\n40, 300\n", stderr="")
    monkeypatch.setattr("scripts.backend_pressure_ab.shutil.which", lambda _name: "/usr/bin/nvidia-smi")
    monkeypatch.setattr("scripts.backend_pressure_ab.subprocess.run", lambda *_args, **_kwargs: result)

    assert _gpu_sample() == (30.0, 400.0)


def test_gpu_provider_rejects_out_of_bounds_aggregate_memory(monkeypatch) -> None:
    result = SimpleNamespace(returncode=0, stdout="20, 600000\n40, 600000\n", stderr="")
    monkeypatch.setattr("scripts.backend_pressure_ab.shutil.which", lambda _name: "/usr/bin/nvidia-smi")
    monkeypatch.setattr("scripts.backend_pressure_ab.subprocess.run", lambda *_args, **_kwargs: result)

    with pytest.raises(CaptureError, match="GPU provider response"):
        _gpu_sample()


@pytest.mark.parametrize("kind", ["timeout", "nonzero", "malformed", "bounds"])
def test_gpu_provider_fails_cleanly_for_unusable_available_provider(monkeypatch, kind: str) -> None:
    private = "/home/private/gpu-output"
    monkeypatch.setattr("scripts.backend_pressure_ab.shutil.which", lambda _name: "/usr/bin/nvidia-smi")

    def fake_run(*_args, **_kwargs):
        if kind == "timeout":
            raise subprocess.TimeoutExpired("nvidia-smi", 2.0, output=private)
        if kind == "nonzero":
            return SimpleNamespace(returncode=1, stdout="", stderr=private)
        stdout = private if kind == "malformed" else "101, 1"
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

    monkeypatch.setattr("scripts.backend_pressure_ab.subprocess.run", fake_run)

    with pytest.raises(CaptureError) as captured:
        _gpu_sample()

    assert private not in str(captured.value)


class _FakeClock:
    def __init__(self) -> None:
        self.monotonic_value = 0.0
        self.epoch_value = 1_000.0
        self.sleep_calls: list[float] = []

    def monotonic(self) -> float:
        return self.monotonic_value

    def epoch(self) -> float:
        return self.epoch_value

    def sleep(self, seconds: float) -> None:
        self.sleep_calls.append(seconds)
        self.monotonic_value += seconds
        self.epoch_value += seconds


def _work_snapshot(origin: str, value: int) -> dict[str, object]:
    return {
        "schema_version": 1,
        "origin_id": origin,
        "captured_at_ns": value + 1,
        "counters": {key: value for key in WORK_COUNTER_KEYS},
    }


def _helper_health(value: int, *, origin: int = 9) -> dict[str, object]:
    return {
        "origin": origin,
        "counters": {"target_queries": value, "presentation_calls": value},
        "actors": {
            "shell_actor_proof_visible": 1,
            "shell_raster_frame_visible": 1,
            "shell_raster_region_count": 1,
        },
    }


def _fake_capture_dependencies(*, client: bool = True, helper: bool = True):
    clock = _FakeClock()
    process_values: dict[int, int] = {}
    client_value = 0
    helper_value = 0
    warning_windows: list[tuple[float, float]] = []
    calls: list[str] = []

    def process_snapshot(pid: int) -> dict[str, int]:
        process_values[pid] = process_values.get(pid, 0) + 1
        value = process_values[pid]
        return {
            "start_ticks": pid * 10,
            "ticks": value,
            "rss_kib": 100 + value,
            "voluntary": value,
            "involuntary": value,
        }

    def client_snapshot(_port_file: Path) -> dict[str, object]:
        nonlocal client_value
        calls.append("client_snapshot")
        client_value += 1
        return _work_snapshot("a" * 32, client_value)

    def helper_snapshot() -> dict[str, object]:
        nonlocal helper_value
        calls.append("helper_snapshot")
        helper_value += 1
        return _helper_health(helper_value)

    def warning_counts(start: float, end: float) -> dict[str, int | bool]:
        warning_windows.append((start, end))
        return {"available": True, "mutter_assertions": 0, "shell_warnings": 0}

    providers = CaptureProviders(
        process_snapshot=process_snapshot,
        gpu_sample=lambda: None,
        warning_counts=warning_counts,
        client_snapshot=client_snapshot,
        client_backend_status=lambda _path: _runtime_backend_status(helper_available=helper),
        helper_snapshot=helper_snapshot,
        helper_owner_present=lambda: helper,
    )
    timing = CaptureTiming(monotonic=clock.monotonic, epoch=clock.epoch, sleep=clock.sleep)
    return providers, timing, clock, warning_windows, calls


def test_process_sampler_aligns_fake_clock_warning_and_resource_windows() -> None:
    providers, timing, clock, warning_windows, _calls = _fake_capture_dependencies()
    safety = SafetyTracker()

    resources, warnings = _sample_processes(
        101,
        202,
        providers=providers,
        timing=timing,
        safety=safety,
        verify_state=lambda: None,
        phase="observation",
    )

    assert len(clock.sleep_calls) == 60
    assert sum(clock.sleep_calls) == 60.0
    assert len(warning_windows) == 60
    assert warning_windows[0] == (1_000.0, 1_001.0)
    assert warning_windows[-1] == (1_059.0, 1_060.0)
    assert resources["shell"]["cpu_percent"]["count"] == 60
    assert resources["client"]["context_switches"]["count"] == 60
    assert warnings == {"available": True, "mutter_assertions": 0, "shell_warnings": 0}


def test_process_sampler_rejects_process_restart() -> None:
    providers, timing, _clock, _warning_windows, _calls = _fake_capture_dependencies()
    original = providers.process_snapshot
    count = 0

    def restarted(pid: int) -> dict[str, int]:
        nonlocal count
        snapshot = original(pid)
        count += 1
        if pid == 101 and count > 2:
            snapshot["start_ticks"] += 1
        return snapshot

    providers = CaptureProviders(
        process_snapshot=restarted,
        gpu_sample=providers.gpu_sample,
        warning_counts=providers.warning_counts,
        client_snapshot=providers.client_snapshot,
        client_backend_status=providers.client_backend_status,
        helper_snapshot=providers.helper_snapshot,
        helper_owner_present=providers.helper_owner_present,
    )

    with pytest.raises(CaptureError, match="restarted"):
        _sample_processes(
            101,
            202,
            providers=providers,
            timing=timing,
            safety=SafetyTracker(),
            verify_state=lambda: None,
            phase="observation",
        )


def test_process_sampler_rejects_wall_clock_shift_that_misaligns_warning_window() -> None:
    providers, timing, clock, _warning_windows, _calls = _fake_capture_dependencies()
    shifted_timing = CaptureTiming(
        monotonic=timing.monotonic,
        epoch=lambda: clock.epoch() + (10.0 if clock.monotonic() >= 1.0 else 0.0),
        sleep=timing.sleep,
    )

    with pytest.raises(CaptureError, match="clock"):
        _sample_processes(
            101,
            202,
            providers=providers,
            timing=shifted_timing,
            safety=SafetyTracker(),
            verify_state=lambda: None,
            phase="observation",
        )


def test_process_sampler_rejects_out_of_bounds_injected_gpu_value() -> None:
    providers, timing, _clock, _warning_windows, _calls = _fake_capture_dependencies()
    providers = CaptureProviders(
        process_snapshot=providers.process_snapshot,
        gpu_sample=lambda: (101.0, 1.0),
        warning_counts=providers.warning_counts,
        client_snapshot=providers.client_snapshot,
        client_backend_status=providers.client_backend_status,
        helper_snapshot=providers.helper_snapshot,
        helper_owner_present=providers.helper_owner_present,
    )

    with pytest.raises(CaptureError, match="GPU aggregate"):
        _sample_processes(
            101,
            202,
            providers=providers,
            timing=timing,
            safety=SafetyTracker(),
            verify_state=lambda: None,
            phase="observation",
        )


@pytest.mark.parametrize("provider_name", ["gpu", "warnings"])
def test_process_sampler_rejects_provider_availability_change(provider_name: str) -> None:
    providers, timing, _clock, _warning_windows, _calls = _fake_capture_dependencies()
    calls = 0

    def gpu_sample() -> tuple[float, float] | None:
        nonlocal calls
        calls += 1
        return None if calls == 1 else (1.0, 1.0)

    def warning_counts(_start: float, _end: float) -> dict[str, int | bool]:
        nonlocal calls
        calls += 1
        return {
            "available": calls == 1,
            "mutter_assertions": 0,
            "shell_warnings": 0,
        }

    providers = CaptureProviders(
        process_snapshot=providers.process_snapshot,
        gpu_sample=gpu_sample if provider_name == "gpu" else providers.gpu_sample,
        warning_counts=warning_counts if provider_name == "warnings" else providers.warning_counts,
        client_snapshot=providers.client_snapshot,
        client_backend_status=providers.client_backend_status,
        helper_snapshot=providers.helper_snapshot,
        helper_owner_present=providers.helper_owner_present,
    )

    with pytest.raises(CaptureError, match="availability changed"):
        _sample_processes(
            101,
            202,
            providers=providers,
            timing=timing,
            safety=SafetyTracker(),
            verify_state=lambda: None,
            phase="observation",
        )


@pytest.mark.parametrize(
    ("cpu_values", "warnings", "field"),
    [
        ([90.0, 90.0, 90.0], {"available": True, "mutter_assertions": 0, "shell_warnings": 0}, "rapidly_rising_shell_cpu"),
        ([1.0], {"available": True, "mutter_assertions": 2, "shell_warnings": 0}, "repeated_mutter_assertions"),
    ],
)
def test_safety_tracker_stops_on_machine_enforced_conditions(cpu_values, warnings, field) -> None:
    tracker = SafetyTracker()

    with pytest.raises(CaptureStopped) as stopped:
        for cpu in cpu_values:
            tracker.observe(shell_cpu_percent=cpu, warning_counts=warnings, phase="warm_up")

    assert stopped.value.phase == "warm_up"
    assert stopped.value.reason_code == "safety_condition"
    assert stopped.value.safety_field == field


def test_safety_tracker_treats_assertions_in_separate_ticks_as_repeated() -> None:
    tracker = SafetyTracker()
    warning = {"available": True, "mutter_assertions": 1, "shell_warnings": 0}

    tracker.observe(shell_cpu_percent=1.0, warning_counts=warning, phase="observation")
    with pytest.raises(CaptureStopped) as stopped:
        tracker.observe(shell_cpu_percent=1.0, warning_counts=warning, phase="observation")

    assert stopped.value.safety_field == "repeated_mutter_assertions"


def test_complete_capture_uses_fake_time_and_emits_strict_three_sample_cell() -> None:
    providers, timing, clock, warning_windows, _calls = _fake_capture_dependencies()

    document = _capture(_strict_runner_args(), providers=providers, timing=timing)

    parsed = parse_pressure_ab_cell_document(document)
    assert parsed.cell == "B2"
    assert tuple(sample.repetition for sample in parsed.samples) == (1, 2, 3)
    assert len(clock.sleep_calls) == 300 + (3 * 60)
    assert sum(clock.sleep_calls) == 480.0
    assert len(warning_windows) == 480
    assert document["execution_order"] == 3


def test_complete_stopped_client_helper_disabled_cell_is_strict() -> None:
    providers, timing, _clock, _warning_windows, _calls = _fake_capture_dependencies(
        client=False,
        helper=False,
    )
    args = _strict_runner_args(
        cell="A1",
        client_pid=None,
        port_file=None,
        client_backend_state=None,
        execution_order=1,
    )

    document = _capture(args, providers=providers, timing=timing)

    parsed = parse_pressure_ab_cell_document(document)
    assert parsed.cell == "A1"
    assert all(sample.client_work.available is False for sample in parsed.samples)
    assert all(sample.helper_work.available is False for sample in parsed.samples)


@pytest.mark.parametrize(
    ("cell", "client_pid", "port_file", "backend_state", "helper_enabled"),
    [
        ("A2", 202, Path("port.json"), "documented_unavailable", False),
        ("B1", None, None, None, True),
    ],
)
def test_complete_capture_covers_remaining_exact_cell_states(
    cell: str,
    client_pid: int | None,
    port_file: Path | None,
    backend_state: str | None,
    helper_enabled: bool,
) -> None:
    providers, timing, clock, warning_windows, _calls = _fake_capture_dependencies(
        client=client_pid is not None,
        helper=helper_enabled,
    )
    args = _strict_runner_args(
        cell=cell,
        client_pid=client_pid,
        port_file=port_file,
        client_backend_state=backend_state,
        execution_order=2,
    )

    parsed = parse_pressure_ab_cell_document(_capture(args, providers=providers, timing=timing))

    assert parsed.cell == cell
    assert tuple(sample.repetition for sample in parsed.samples) == (1, 2, 3)
    assert sum(clock.sleep_calls) == 480.0
    assert len(warning_windows) == 480
    assert all(sample.client_work.available is (client_pid is not None) for sample in parsed.samples)
    assert all(sample.helper_work.available is helper_enabled for sample in parsed.samples)


@pytest.mark.parametrize(
    ("overrides", "error"),
    [
        ({"execution_order": 0}, "execution order"),
        ({"fixture_sha256": "/home/private/fixture"}, "provenance"),
        ({"quiet_host_confirmed": False}, "provenance"),
        ({"operator_observing": False}, "operator observation"),
    ],
)
def test_capture_rejects_invalid_inputs_before_timing(overrides, error: str) -> None:
    providers, timing, clock, _warning_windows, _calls = _fake_capture_dependencies()

    with pytest.raises(CaptureError, match=error):
        _capture(_strict_runner_args(**overrides), providers=providers, timing=timing)

    assert clock.sleep_calls == []


@pytest.mark.parametrize(("component", "unsafe_value"), [("client", "decrease"), ("client", "saturation"), ("helper", "decrease"), ("helper", "saturation")])
def test_capture_rejects_unsafe_work_endpoints(component: str, unsafe_value: str) -> None:
    providers, timing, clock, _warning_windows, _calls = _fake_capture_dependencies()

    def client_snapshot(_path: Path) -> dict[str, object]:
        value = WORK_COUNTER_MAX if unsafe_value == "saturation" else (10 if clock.monotonic() < 360 else 9)
        snapshot = _work_snapshot("a" * 32, value)
        snapshot["captured_at_ns"] = int(clock.monotonic() * 1_000_000_000) + 1
        return snapshot

    def helper_snapshot() -> dict[str, object]:
        value = WORK_COUNTER_MAX if unsafe_value == "saturation" else (10 if clock.monotonic() < 360 else 9)
        return _helper_health(value)

    providers = CaptureProviders(
        process_snapshot=providers.process_snapshot,
        gpu_sample=providers.gpu_sample,
        warning_counts=providers.warning_counts,
        client_snapshot=client_snapshot if component == "client" else providers.client_snapshot,
        client_backend_status=providers.client_backend_status,
        helper_snapshot=helper_snapshot if component == "helper" else providers.helper_snapshot,
        helper_owner_present=providers.helper_owner_present,
    )

    with pytest.raises(CaptureError, match=f"{component} (work endpoints are unsafe|counter)"):
        _capture(_strict_runner_args(), providers=providers, timing=timing)


def test_capture_rechecks_helper_disabled_state_instead_of_catching_probe_error() -> None:
    providers, timing, _clock, _warning_windows, _calls = _fake_capture_dependencies(client=True, helper=False)

    def uncertain_owner() -> bool:
        raise CaptureError("helper owner probe failed")

    providers = CaptureProviders(
        process_snapshot=providers.process_snapshot,
        gpu_sample=providers.gpu_sample,
        warning_counts=providers.warning_counts,
        client_snapshot=providers.client_snapshot,
        client_backend_status=providers.client_backend_status,
        helper_snapshot=providers.helper_snapshot,
        helper_owner_present=uncertain_owner,
    )

    with pytest.raises(CaptureError, match="owner probe failed"):
        _capture(
            _strict_runner_args(cell="A2", client_backend_state="documented_unavailable"),
            providers=providers,
            timing=timing,
        )


def test_capture_rejects_whole_cell_client_origin_change() -> None:
    providers, timing, _clock, _warning_windows, _calls = _fake_capture_dependencies()
    value = 0

    def changing_client(_path: Path) -> dict[str, object]:
        nonlocal value
        value += 1
        origin = "a" * 32 if value <= 2 else "b" * 32
        return _work_snapshot(origin, value)

    providers = CaptureProviders(
        process_snapshot=providers.process_snapshot,
        gpu_sample=providers.gpu_sample,
        warning_counts=providers.warning_counts,
        client_snapshot=changing_client,
        client_backend_status=providers.client_backend_status,
        helper_snapshot=providers.helper_snapshot,
        helper_owner_present=providers.helper_owner_present,
    )

    with pytest.raises(CaptureError, match="client restarted"):
        _capture(_strict_runner_args(), providers=providers, timing=timing)


def test_capture_rejects_helper_origin_change_anywhere_post_warm_up() -> None:
    providers, timing, clock, _warning_windows, _calls = _fake_capture_dependencies()
    original = providers.helper_snapshot

    def changing_helper() -> dict[str, object]:
        snapshot = original()
        if clock.monotonic() > 300.0:
            snapshot["origin"] = 10
        return snapshot

    providers = CaptureProviders(
        process_snapshot=providers.process_snapshot,
        gpu_sample=providers.gpu_sample,
        warning_counts=providers.warning_counts,
        client_snapshot=providers.client_snapshot,
        client_backend_status=providers.client_backend_status,
        helper_snapshot=changing_helper,
        helper_owner_present=providers.helper_owner_present,
    )

    with pytest.raises(CaptureError, match="helper restarted"):
        _capture(_strict_runner_args(), providers=providers, timing=timing)


def test_capture_rechecks_disabled_helper_during_observation() -> None:
    providers, timing, clock, _warning_windows, _calls = _fake_capture_dependencies(helper=False)
    providers = CaptureProviders(
        process_snapshot=providers.process_snapshot,
        gpu_sample=providers.gpu_sample,
        warning_counts=providers.warning_counts,
        client_snapshot=providers.client_snapshot,
        client_backend_status=providers.client_backend_status,
        helper_snapshot=providers.helper_snapshot,
        helper_owner_present=lambda: clock.monotonic() > 300.0,
    )

    with pytest.raises(CaptureError, match="helper is available"):
        _capture(
            _strict_runner_args(cell="A2", client_backend_state="documented_unavailable"),
            providers=providers,
            timing=timing,
        )


def test_capture_rechecks_client_runtime_route_after_observation() -> None:
    providers, timing, clock, _warning_windows, _calls = _fake_capture_dependencies()

    def backend_status(_path: Path) -> Mapping[str, object]:
        status = _runtime_backend_status(helper_available=True)
        if clock.monotonic() >= 360.0:
            status["shadow_mode"] = True
        return status

    providers = CaptureProviders(
        process_snapshot=providers.process_snapshot,
        gpu_sample=providers.gpu_sample,
        warning_counts=providers.warning_counts,
        client_snapshot=providers.client_snapshot,
        client_backend_status=backend_status,
        helper_snapshot=providers.helper_snapshot,
        helper_owner_present=providers.helper_owner_present,
    )

    with pytest.raises(CaptureError, match="runtime backend state"):
        _capture(_strict_runner_args(), providers=providers, timing=timing)


@pytest.mark.parametrize(("interrupt_tick", "expected_phase"), [(1, "warm_up"), (301, "observation")])
def test_capture_normalizes_keyboard_interrupt_in_each_timed_phase(interrupt_tick, expected_phase) -> None:
    providers, timing, clock, _warning_windows, _calls = _fake_capture_dependencies()
    calls = 0

    def interrupted_sleep(seconds: float) -> None:
        nonlocal calls
        calls += 1
        if calls == interrupt_tick:
            raise KeyboardInterrupt
        clock.sleep(seconds)

    interrupted_timing = CaptureTiming(
        monotonic=timing.monotonic,
        epoch=timing.epoch,
        sleep=interrupted_sleep,
    )

    with pytest.raises(CaptureStopped) as stopped:
        _capture(_strict_runner_args(), providers=providers, timing=interrupted_timing)

    assert stopped.value.phase == expected_phase
    assert stopped.value.reason_code == "operator_interrupt"


def test_stop_document_is_sanitized_and_distinct_from_accepted_cell() -> None:
    stopped = CaptureStopped(
        phase="observation",
        reason_code="safety_condition",
        safety_field="repeated_mutter_assertions",
    )

    document = _build_stop_document(_strict_runner_args(), stopped)

    assert document["artifact_type"] == "pressure_ab_stop"
    assert document["accepted"] is False
    assert "samples" not in document
    assert "shell_pid" not in json.dumps(document)
    assert "port.json" not in json.dumps(document)
    with pytest.raises(Exception):
        parse_pressure_ab_cell_document(document)


def test_stop_document_rejects_privacy_invalid_provenance() -> None:
    stopped = CaptureStopped(
        phase="warm_up",
        reason_code="operator_interrupt",
        safety_field=None,
    )

    with pytest.raises(CaptureError, match="provenance"):
        _build_stop_document(_strict_runner_args(fixture_sha256="/home/private"), stopped)


@pytest.mark.parametrize(("warning_tick", "expected_phase"), [(1, "warm_up"), (301, "observation")])
def test_capture_propagates_machine_safety_stop_from_each_phase(warning_tick, expected_phase) -> None:
    providers, timing, _clock, _warning_windows, _calls = _fake_capture_dependencies()
    tick = 0

    def warning_counts(_start: float, _end: float) -> dict[str, int | bool]:
        nonlocal tick
        tick += 1
        return {
            "available": True,
            "mutter_assertions": 2 if tick == warning_tick else 0,
            "shell_warnings": 0,
        }

    providers = CaptureProviders(
        process_snapshot=providers.process_snapshot,
        gpu_sample=providers.gpu_sample,
        warning_counts=warning_counts,
        client_snapshot=providers.client_snapshot,
        client_backend_status=providers.client_backend_status,
        helper_snapshot=providers.helper_snapshot,
        helper_owner_present=providers.helper_owner_present,
    )

    with pytest.raises(CaptureStopped) as stopped:
        _capture(_strict_runner_args(), providers=providers, timing=timing)

    assert stopped.value.phase == expected_phase
    assert stopped.value.safety_field == "repeated_mutter_assertions"


def test_exclusive_json_writer_never_overwrites_success_or_stop(tmp_path) -> None:
    output = tmp_path / "cell.json"
    _write_new_json(output, {"first": True})

    with pytest.raises(FileExistsError):
        _write_new_json(output, {"second": True})

    assert json.loads(output.read_text(encoding="utf-8")) == {"first": True}


def test_exclusive_json_writer_removes_its_partial_file_on_write_failure(monkeypatch, tmp_path) -> None:
    output = tmp_path / "partial.json"

    def failed_dump(_document, stream, **_kwargs) -> None:
        stream.write("{")
        raise OSError("/home/private/write-failure")

    monkeypatch.setattr("scripts.backend_pressure_ab.json.dump", failed_dump)

    with pytest.raises(OSError):
        _write_new_json(output, {"accepted": True})

    assert not output.exists()


def _main_argv(tmp_path: Path, output: Path) -> list[str]:
    return [
        "--cell", "B2",
        "--shell-pid", "101",
        "--client-pid", "202",
        "--port-file", str(tmp_path / "port.json"),
        "--client-backend-state", "helper_selected",
        "--execution-order", "3",
        "--fixture-sha256", "1" * 64,
        "--source-revision", "2" * 40,
        "--plugin-version", "2.0.0",
        "--client-version", "2.0.0",
        "--helper-version", "4.0.0",
        "--display-width-px", "1920",
        "--display-height-px", "1080",
        "--refresh-hz", "60",
        "--quiet-host-confirmed",
        "--operator-observing",
        "--output", str(output),
    ]


def test_main_writes_success_once_without_replacement(monkeypatch, tmp_path) -> None:
    output = tmp_path / "success.json"
    document = {"accepted": "synthetic-unit-evidence"}
    monkeypatch.setattr("scripts.backend_pressure_ab._capture", lambda _args: document)
    argv = _main_argv(tmp_path, output)

    assert main(argv) == 0
    assert json.loads(output.read_text(encoding="utf-8")) == document

    assert main(argv) == 2
    assert json.loads(output.read_text(encoding="utf-8")) == document


def test_main_provider_failure_writes_no_artifact(monkeypatch, tmp_path) -> None:
    output = tmp_path / "failed.json"
    monkeypatch.setattr(
        "scripts.backend_pressure_ab._capture",
        lambda _args: (_ for _ in ()).throw(CaptureError("provider unavailable")),
    )

    assert main(_main_argv(tmp_path, output)) == 2
    assert not output.exists()


def test_main_normalizes_output_write_failure_without_private_path(monkeypatch, tmp_path, capsys) -> None:
    output = tmp_path / "failed-write.json"
    monkeypatch.setattr(
        "scripts.backend_pressure_ab._capture",
        lambda _args: {"accepted": "synthetic-unit-evidence"},
    )
    monkeypatch.setattr(
        "scripts.backend_pressure_ab._write_new_json",
        lambda *_args: (_ for _ in ()).throw(OSError("/home/private/output")),
    )

    assert main(_main_argv(tmp_path, output)) == 2
    assert "/home/private" not in capsys.readouterr().err
    assert not output.exists()


@pytest.mark.parametrize("capture_failure", ["typed_stop", "raw_interrupt"])
def test_main_normalizes_stop_output_write_failure(
    monkeypatch,
    tmp_path,
    capsys,
    capture_failure: str,
) -> None:
    output = tmp_path / "failed-stop-write.json"

    def failed_capture(_args) -> object:
        if capture_failure == "typed_stop":
            raise CaptureStopped(
                phase="observation",
                reason_code="safety_condition",
                safety_field="repeated_mutter_assertions",
            )
        raise KeyboardInterrupt

    monkeypatch.setattr("scripts.backend_pressure_ab._capture", failed_capture)
    monkeypatch.setattr(
        "scripts.backend_pressure_ab._write_new_json",
        lambda *_args: (_ for _ in ()).throw(OSError("/home/private/output")),
    )

    assert main(_main_argv(tmp_path, output)) == 2
    assert capsys.readouterr().err == "backend_pressure_ab: output write failed\n"
    assert not output.exists()


def test_main_writes_sanitized_stop_evidence_for_interruption(monkeypatch, tmp_path) -> None:
    output = tmp_path / "stopped.json"
    monkeypatch.setattr(
        "scripts.backend_pressure_ab._capture",
        lambda _args: (_ for _ in ()).throw(
            CaptureStopped(phase="warm_up", reason_code="operator_interrupt", safety_field=None)
        ),
    )
    argv = _main_argv(tmp_path, output)

    assert main(argv) == 2
    document = json.loads(output.read_text(encoding="utf-8"))
    assert document["artifact_type"] == "pressure_ab_stop"
    assert document["phase"] == "warm_up"
    assert document["reason_code"] == "operator_interrupt"
    assert str(tmp_path) not in json.dumps(document)

    assert main(argv) == 2
    assert json.loads(output.read_text(encoding="utf-8")) == document
