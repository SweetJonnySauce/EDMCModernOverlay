#!/usr/bin/env python3
"""Capture one controlled diagnostics-off helper-pressure A/B cell."""

from __future__ import annotations

import argparse
import ast
import json
import math
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from overlay_client.backend.bundles._gnome_shell_helper_presentation import (  # noqa: E402
    fetch_gnome_shell_helper_health_via_gdbus,
)
from overlay_client.backend.helper_ipc import (  # noqa: E402
    GNOME_SHELL_HELPER_DBUS_SERVICE,
    HELPER_PROTOCOL,
    HelperDbusProbeError,
)
from overlay_client.backend.pressure_ab import (  # noqa: E402
    PRESSURE_AB_CELLS,
    PRESSURE_AB_SAFETY_FIELDS,
    PressureAbValidationError,
    delta_work_snapshots,
    parse_pressure_ab_cell_document,
    parse_work_snapshot,
    validate_client_argument_pair,
)
from overlay_client.work_counters import WORK_COUNTER_MAX  # noqa: E402


WARM_UP_SECONDS = 300
SAMPLE_SECONDS = 60
REPETITIONS = 3
SAFETY_FIELDS = PRESSURE_AB_SAFETY_FIELDS
SHELL_CPU_STOP_PERCENT = 80.0
SHELL_CPU_STOP_CONSECUTIVE = 3
MUTTER_ASSERTION_STOP_COUNT = 2
PROCESS_COUNTER_MAX = (1 << 63) - 1
PROCESS_RSS_MAX_KIB = 1_000_000_000
GPU_VRAM_MAX_MIB = 1_000_000.0
ELAPSED_WINDOW_TOLERANCE_SECONDS = 1.0
CLOCK_ALIGNMENT_TOLERANCE_SECONDS = 0.25
_FIXTURE_HASH = re.compile(r"^[a-f0-9]{64}$")
_SOURCE_REVISION = re.compile(r"^[a-f0-9]{40}$")
_COMPONENT_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,63}$")
CELL_STATE = {
    "A1": {"client": False, "helper": False},
    "A2": {"client": True, "helper": False},
    "B1": {"client": False, "helper": True},
    "B2": {"client": True, "helper": True},
}


class CaptureError(RuntimeError):
    """Raised when a live pressure sample cannot be accepted."""


class CaptureStopped(CaptureError):
    """A sanitized operator or machine-enforced non-acceptance stop."""

    def __init__(self, *, phase: str, reason_code: str, safety_field: str | None) -> None:
        if phase not in {"capture", "warm_up", "observation"}:
            raise ValueError("invalid pressure stop phase")
        if reason_code not in {"operator_interrupt", "safety_condition"}:
            raise ValueError("invalid pressure stop reason")
        if safety_field is not None and safety_field not in SAFETY_FIELDS:
            raise ValueError("invalid pressure stop safety field")
        self.phase = phase
        self.reason_code = reason_code
        self.safety_field = safety_field
        super().__init__(f"capture stopped: {reason_code}")


@dataclass(frozen=True)
class CaptureTiming:
    """Injectable clocks used without weakening fixed evidence timing."""

    monotonic: Callable[[], float] = time.perf_counter
    epoch: Callable[[], float] = time.time
    sleep: Callable[[float], None] = time.sleep


@dataclass(frozen=True)
class CaptureProviders:
    """Injectable local providers for deterministic runner orchestration tests."""

    process_snapshot: Callable[[int], dict[str, int]]
    gpu_sample: Callable[[], tuple[float, float] | None]
    warning_counts: Callable[[float, float], dict[str, int | bool]]
    client_snapshot: Callable[[Path], dict[str, object]]
    client_backend_status: Callable[[Path], Mapping[str, object]]
    helper_snapshot: Callable[[], dict[str, object]]
    helper_owner_present: Callable[[], bool]


@dataclass
class SafetyTracker:
    """Machine-enforced fixed safety rules for warm-up and observations."""

    consecutive_high_shell_cpu: int = 0
    mutter_assertions_seen: int = 0

    def observe(
        self,
        *,
        shell_cpu_percent: float,
        warning_counts: Mapping[str, int | bool],
        phase: str,
    ) -> None:
        assertions = warning_counts.get("mutter_assertions")
        if isinstance(assertions, bool) or not isinstance(assertions, int):
            raise CaptureError("warning safety aggregate is invalid")
        self.mutter_assertions_seen += assertions
        if self.mutter_assertions_seen >= MUTTER_ASSERTION_STOP_COUNT:
            raise CaptureStopped(
                phase=phase,
                reason_code="safety_condition",
                safety_field="repeated_mutter_assertions",
            )
        if not math.isfinite(shell_cpu_percent) or shell_cpu_percent < 0.0:
            raise CaptureError("Shell CPU safety aggregate is invalid")
        if shell_cpu_percent >= SHELL_CPU_STOP_PERCENT:
            self.consecutive_high_shell_cpu += 1
        else:
            self.consecutive_high_shell_cpu = 0
        if self.consecutive_high_shell_cpu >= SHELL_CPU_STOP_CONSECUTIVE:
            raise CaptureStopped(
                phase=phase,
                reason_code="safety_condition",
                safety_field="rapidly_rising_shell_cpu",
            )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cell", required=True, choices=PRESSURE_AB_CELLS)
    parser.add_argument("--shell-pid", required=True, type=int)
    parser.add_argument("--client-pid", type=int)
    parser.add_argument("--port-file", type=Path)
    parser.add_argument(
        "--client-backend-state",
        choices=("documented_unavailable", "helper_selected"),
    )
    parser.add_argument("--execution-order", required=True, type=int)
    parser.add_argument("--fixture-sha256", required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--plugin-version", required=True)
    parser.add_argument("--client-version", required=True)
    parser.add_argument("--helper-version", required=True)
    parser.add_argument("--display-width-px", required=True, type=int)
    parser.add_argument("--display-height-px", required=True, type=int)
    parser.add_argument("--refresh-hz", required=True, type=float)
    parser.add_argument("--quiet-host-confirmed", required=True, action="store_true")
    parser.add_argument(
        "--operator-observing",
        required=True,
        action="store_true",
        help="Confirm continuous visible-Shell observation and Ctrl-C emergency-stop responsibility.",
    )
    parser.add_argument("--output", required=True, type=Path)
    return parser


def _read_port(path: Path) -> int:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CaptureError("plugin port metadata is unavailable") from exc
    port = raw.get("port") if isinstance(raw, Mapping) else None
    if isinstance(port, bool) or not isinstance(port, int) or not 0 < port <= 65535:
        raise CaptureError("plugin port metadata has an invalid port")
    return port


def _request_client_command(port_file: Path, command: str) -> Mapping[str, object]:
    request = json.dumps({"cli": command}, separators=(",", ":")).encode() + b"\n"
    try:
        with socket.create_connection(("127.0.0.1", _read_port(port_file)), timeout=2.0) as connection:
            connection.settimeout(3.0)
            connection.sendall(request)
            reader = connection.makefile("rb")
            for _ in range(64):
                line = reader.readline()
                if not line:
                    break
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(payload, Mapping) or "status" not in payload:
                    continue
                if payload.get("status") != "ok":
                    raise CaptureError(f"client {command} is unavailable")
                return payload
    except OSError as exc:
        raise CaptureError(f"client {command} request failed") from exc
    raise CaptureError(f"client {command} response timed out")


def _request_client_snapshot(port_file: Path) -> dict[str, object]:
    payload = _request_client_command(port_file, "pressure_snapshot")
    snapshot = payload.get("snapshot")
    if not isinstance(snapshot, Mapping):
        raise CaptureError("client pressure snapshot response is malformed")
    try:
        return parse_work_snapshot(snapshot)
    except PressureAbValidationError as exc:
        raise CaptureError("client pressure snapshot response is malformed") from exc


def _request_client_backend_status(port_file: Path) -> Mapping[str, object]:
    # The first synchronous plugin request may return its shadow hint while the queued client
    # status response populates the cache. Bounded retries require the authoritative live source.
    for attempt in range(3):
        payload = _request_client_command(port_file, "backend_status")
        status = payload.get("backend_status")
        if not isinstance(status, Mapping):
            raise CaptureError("client runtime backend state is malformed")
        report = status.get("report")
        if isinstance(report, Mapping) and report.get("source") == "client_runtime":
            return status
        if attempt < 2:
            time.sleep(0.1)
    raise CaptureError("client runtime backend state is unavailable")


def _decode_gdbus_json(raw: object) -> Mapping[str, object]:
    value = raw
    if isinstance(value, str):
        text = value.strip()
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            try:
                unpacked = ast.literal_eval(text)
            except (SyntaxError, ValueError) as exc:
                raise CaptureError("helper health response is malformed") from exc
            if not isinstance(unpacked, (tuple, list)) or len(unpacked) != 1:
                raise CaptureError("helper health response is malformed")
            try:
                value = json.loads(unpacked[0])
            except (json.JSONDecodeError, TypeError) as exc:
                raise CaptureError("helper health response is malformed") from exc
    if not isinstance(value, Mapping):
        raise CaptureError("helper health response is malformed")
    return value


def _helper_owner_present() -> bool:
    """Return exact session-bus ownership; never infer absence from probe failure."""

    try:
        result = subprocess.run(
            [
                "gdbus",
                "call",
                "--session",
                "--dest",
                "org.freedesktop.DBus",
                "--object-path",
                "/org/freedesktop/DBus",
                "--method",
                "org.freedesktop.DBus.NameHasOwner",
                GNOME_SHELL_HELPER_DBUS_SERVICE,
            ],
            text=True,
            capture_output=True,
            timeout=2.0,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise CaptureError("helper owner probe failed") from exc
    if result.returncode != 0:
        raise CaptureError("helper owner probe failed")
    normalized = (result.stdout or "").strip().casefold().replace(" ", "")
    if normalized == "(true,)":
        return True
    if normalized == "(false,)":
        return False
    raise CaptureError("helper owner probe response is malformed")


def _helper_snapshot() -> dict[str, object]:
    try:
        raw_payload = fetch_gnome_shell_helper_health_via_gdbus()
    except HelperDbusProbeError as exc:
        raise CaptureError("helper health request failed") from exc
    payload = _decode_gdbus_json(raw_payload)
    gate = payload.get("feature_gate")
    counters = payload.get("pressure_counters")
    actors = payload.get("actor_counts")
    if (
        payload.get("status") != "healthy"
        or payload.get("helper_kind") != "gnome_shell_extension"
        or payload.get("helper_protocol") != HELPER_PROTOCOL
        or payload.get("service_name") != GNOME_SHELL_HELPER_DBUS_SERVICE
    ):
        raise CaptureError("helper health identity is invalid")
    helper_version = payload.get("helper_version")
    if not isinstance(helper_version, str) or _COMPONENT_VERSION.fullmatch(helper_version) is None:
        raise CaptureError("helper health version is invalid")
    if not isinstance(gate, Mapping) or not isinstance(counters, Mapping) or not isinstance(actors, Mapping):
        raise CaptureError("helper health lacks quiet pressure aggregates")
    if gate.get("mode") != "full_helper" or gate.get("diagnostics_enabled") is not False:
        raise CaptureError("helper must be full_helper with diagnostics disabled")
    normalized_counters: dict[str, int] = {}
    for name in ("target_queries", "presentation_calls"):
        value = counters.get(name)
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 1_000_000:
            raise CaptureError("helper pressure counter is invalid")
        normalized_counters[name] = value
    normalized_actors: dict[str, int] = {}
    for name in ("shell_actor_proof_visible", "shell_raster_frame_visible", "shell_raster_region_count"):
        value = actors.get(name)
        if name.endswith("_visible"):
            if not isinstance(value, bool):
                raise CaptureError("helper actor aggregate is invalid")
            normalized_actors[name] = int(value)
        else:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 1024:
                raise CaptureError("helper actor aggregate is invalid")
            normalized_actors[name] = value
    origin = payload.get("started_at_monotonic_us")
    if isinstance(origin, bool) or not isinstance(origin, int) or origin < 0:
        raise CaptureError("helper health origin is invalid")
    return {"origin": origin, "counters": normalized_counters, "actors": normalized_actors}


def _process_snapshot(pid: int) -> dict[str, int]:
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
        fields = stat[stat.rfind(")") + 2 :].split()
        status = Path(f"/proc/{pid}/status").read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise CaptureError("required measurement process is unavailable") from exc
    try:
        values: dict[str, int] = {
            "start_ticks": int(fields[19]),
            "ticks": int(fields[11]) + int(fields[12]),
        }
        for line in status:
            if line.startswith("VmRSS:"):
                values["rss_kib"] = int(line.split()[1])
            elif line.startswith("voluntary_ctxt_switches:"):
                values["voluntary"] = int(line.split()[1])
            elif line.startswith("nonvoluntary_ctxt_switches:"):
                values["involuntary"] = int(line.split()[1])
    except (IndexError, ValueError) as exc:
        raise CaptureError("required process aggregates are malformed") from exc
    if set(values) != {"start_ticks", "ticks", "rss_kib", "voluntary", "involuntary"}:
        raise CaptureError("required process aggregates are unavailable")
    for name in ("start_ticks", "ticks", "voluntary", "involuntary"):
        if not 0 <= values[name] <= PROCESS_COUNTER_MAX:
            raise CaptureError("required process aggregate is out of bounds")
    if not 0 <= values["rss_kib"] <= PROCESS_RSS_MAX_KIB:
        raise CaptureError("required process aggregate is out of bounds")
    return values


def _gpu_sample() -> tuple[float, float] | None:
    if shutil.which("nvidia-smi") is None:
        return None
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,memory.used",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            capture_output=True,
            timeout=2.0,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise CaptureError("GPU provider failed") from exc
    if result.returncode != 0:
        raise CaptureError("GPU provider failed")
    rows: list[tuple[float, float]] = []
    try:
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            raw_utilization, raw_memory = line.split(",", 1)
            utilization = float(raw_utilization.strip())
            memory = float(raw_memory.strip())
            if not math.isfinite(utilization) or not 0.0 <= utilization <= 100.0:
                raise ValueError("invalid utilization")
            if not math.isfinite(memory) or not 0.0 <= memory <= GPU_VRAM_MAX_MIB:
                raise ValueError("invalid memory")
            rows.append((utilization, memory))
    except ValueError as exc:
        raise CaptureError("GPU provider response is malformed") from exc
    if not rows:
        raise CaptureError("GPU provider response is malformed")
    total_memory = sum(row[1] for row in rows)
    if total_memory > GPU_VRAM_MAX_MIB:
        raise CaptureError("GPU provider response is out of bounds")
    return (
        sum(row[0] for row in rows) / len(rows),
        total_memory,
    )


def _warning_source(record: Mapping[str, object]) -> str:
    return " ".join(
        str(record.get(key) or "").casefold()
        for key in ("_COMM", "SYSLOG_IDENTIFIER", "_SYSTEMD_UNIT", "GLIB_DOMAIN")
    )


def _normalized_warning_counts(since_epoch: float, until_epoch: float) -> dict[str, int | bool]:
    """Count scoped warning classes over one exact interval and discard all text."""

    if not math.isfinite(since_epoch) or not math.isfinite(until_epoch) or until_epoch <= since_epoch:
        raise CaptureError("warning observation window is invalid")
    if shutil.which("journalctl") is None:
        return {"available": False, "mutter_assertions": 0, "shell_warnings": 0}
    try:
        result = subprocess.run(
            [
                "journalctl",
                "--user",
                "--since",
                f"@{since_epoch:.6f}",
                "--until",
                f"@{until_epoch:.6f}",
                "--output=json",
                "--no-pager",
            ],
            text=True,
            capture_output=True,
            timeout=5.0,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise CaptureError("warning provider failed") from exc
    if result.returncode != 0:
        raise CaptureError("warning provider failed")
    mutter_assertions = 0
    shell_warnings = 0
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CaptureError("warning provider response is malformed") from exc
        if not isinstance(record, Mapping):
            raise CaptureError("warning provider response is malformed")
        source = _warning_source(record)
        message = str(record.get("MESSAGE") or "").casefold()
        priority = str(record.get("PRIORITY") or "")
        is_shell = "gnome-shell" in source
        is_mutter = "mutter" in source
        assertion = "assertion" in message or "assert failed" in message
        if is_mutter and assertion:
            mutter_assertions += 1
        if is_shell and (assertion or priority in {"0", "1", "2", "3", "4"}):
            shell_warnings += 1
        if mutter_assertions >= WORK_COUNTER_MAX or shell_warnings >= WORK_COUNTER_MAX:
            raise CaptureError("warning counter saturated")
    return {
        "available": True,
        "mutter_assertions": mutter_assertions,
        "shell_warnings": shell_warnings,
    }


def _distribution(values: Sequence[float]) -> dict[str, float | int]:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return {"count": 0}
    middle = len(ordered) // 2
    median = ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2.0
    return {
        "count": len(ordered),
        "median": round(median, 6),
        "p95": round(ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)], 6),
        "minimum": round(ordered[0], 6),
        "maximum": round(ordered[-1], 6),
    }


def _process_step(
    previous: Mapping[str, int],
    current: Mapping[str, int],
    *,
    elapsed: float,
    clock_ticks: int,
) -> tuple[float, float]:
    if current["start_ticks"] != previous["start_ticks"]:
        raise CaptureError("required measurement process restarted")
    tick_delta = current["ticks"] - previous["ticks"]
    context_delta = (
        current["voluntary"] + current["involuntary"]
        - previous["voluntary"] - previous["involuntary"]
    )
    if tick_delta < 0 or context_delta < 0:
        raise CaptureError("process counters reset during sample")
    if elapsed <= 0.0 or not math.isfinite(elapsed):
        raise CaptureError("process observation clock is invalid")
    cpu_percent = tick_delta / clock_ticks / elapsed * 100.0
    cpu_bound = max(1, os.cpu_count() or 1) * 100.0 * 1.25
    if not math.isfinite(cpu_percent) or cpu_percent > cpu_bound:
        raise CaptureError("process CPU aggregate is out of bounds")
    if context_delta > PROCESS_COUNTER_MAX:
        raise CaptureError("process context aggregate is out of bounds")
    return cpu_percent, float(context_delta)


def _validate_clock_alignment(
    *,
    previous_monotonic: float,
    current_monotonic: float,
    previous_epoch: float,
    current_epoch: float,
) -> None:
    monotonic_delta = current_monotonic - previous_monotonic
    epoch_delta = current_epoch - previous_epoch
    if (
        not math.isfinite(epoch_delta)
        or epoch_delta <= 0.0
        or abs(epoch_delta - monotonic_delta) > CLOCK_ALIGNMENT_TOLERANCE_SECONDS
    ):
        raise CaptureError("wall and monotonic clocks lost observation alignment")


def _merge_warning_counts(
    total: dict[str, int | bool],
    current: Mapping[str, int | bool],
) -> None:
    available = current.get("available")
    if not isinstance(available, bool):
        raise CaptureError("warning provider aggregate is invalid")
    if total["available"] is not available:
        raise CaptureError("warning provider availability changed during interval")
    for name in ("mutter_assertions", "shell_warnings"):
        value = current.get(name)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise CaptureError("warning provider aggregate is invalid")
        combined = int(total[name]) + value
        if combined >= WORK_COUNTER_MAX:
            raise CaptureError("warning counter saturated")
        total[name] = combined


def _sample_processes(
    shell_pid: int,
    client_pid: int | None,
    *,
    providers: CaptureProviders | None = None,
    timing: CaptureTiming | None = None,
    safety: SafetyTracker | None = None,
    verify_state: Callable[[], object] | None = None,
    expected_process_origins: Mapping[str, int] | None = None,
    phase: str = "observation",
) -> tuple[dict[str, object], dict[str, int | bool]]:
    providers = providers or _default_providers()
    timing = timing or CaptureTiming()
    safety = safety or SafetyTracker()
    verify_state = verify_state or (lambda: None)
    clock_ticks = int(os.sysconf("SC_CLK_TCK"))
    process_ids = {"shell": shell_pid}
    if client_pid is not None:
        process_ids["client"] = client_pid
    previous = {name: providers.process_snapshot(pid) for name, pid in process_ids.items()}
    if expected_process_origins is not None and any(
        previous[name]["start_ticks"] != expected_process_origins.get(name)
        for name in process_ids
    ):
        raise CaptureError("required measurement process restarted")
    started_at = timing.monotonic()
    previous_time = started_at
    previous_epoch = timing.epoch()
    observations: dict[str, dict[str, list[float]]] = {
        name: {"cpu": [], "rss": [], "context": []} for name in process_ids
    }
    gpu_utilization: list[float] = []
    gpu_memory: list[float] = []
    gpu_availability: bool | None = None
    warning_total: dict[str, int | bool] | None = None
    for second in range(1, SAMPLE_SECONDS + 1):
        target = started_at + second
        timing.sleep(max(0.0, target - timing.monotonic()))
        current_time = timing.monotonic()
        elapsed = current_time - previous_time
        current_epoch = timing.epoch()
        _validate_clock_alignment(
            previous_monotonic=previous_time,
            current_monotonic=current_time,
            previous_epoch=previous_epoch,
            current_epoch=current_epoch,
        )
        warnings = providers.warning_counts(previous_epoch, current_epoch)
        if warning_total is None:
            warning_available = warnings.get("available")
            if not isinstance(warning_available, bool):
                raise CaptureError("warning provider aggregate is invalid")
            warning_total = {
                "available": warning_available,
                "mutter_assertions": 0,
                "shell_warnings": 0,
            }
        _merge_warning_counts(warning_total, warnings)
        verify_state()
        shell_cpu = 0.0
        for name, pid in process_ids.items():
            current = providers.process_snapshot(pid)
            cpu_percent, context_delta = _process_step(
                previous[name],
                current,
                elapsed=elapsed,
                clock_ticks=clock_ticks,
            )
            observations[name]["cpu"].append(cpu_percent)
            observations[name]["rss"].append(float(current["rss_kib"]))
            observations[name]["context"].append(context_delta)
            if name == "shell":
                shell_cpu = cpu_percent
            previous[name] = current
        safety.observe(shell_cpu_percent=shell_cpu, warning_counts=warnings, phase=phase)
        gpu = providers.gpu_sample()
        available = gpu is not None
        if gpu_availability is None:
            gpu_availability = available
        elif gpu_availability is not available:
            raise CaptureError("GPU provider availability changed during sample")
        if gpu is not None:
            utilization, memory = gpu
            if (
                not math.isfinite(utilization)
                or not 0.0 <= utilization <= 100.0
                or not math.isfinite(memory)
                or not 0.0 <= memory <= GPU_VRAM_MAX_MIB
            ):
                raise CaptureError("GPU aggregate is out of bounds")
            gpu_utilization.append(gpu[0])
            gpu_memory.append(gpu[1])
        previous_time = current_time
        previous_epoch = current_epoch
        if second % 10 == 0:
            print(f"sample: {second}/{SAMPLE_SECONDS}s", flush=True)
    elapsed_window = timing.monotonic() - started_at
    if not SAMPLE_SECONDS <= elapsed_window <= SAMPLE_SECONDS + ELAPSED_WINDOW_TOLERANCE_SECONDS:
        raise CaptureError("observation timing drift exceeded the fixed bound")
    result: dict[str, object] = {}
    for name, metrics in observations.items():
        result[name] = {
            "available": True,
            "cpu_percent": _distribution(metrics["cpu"]),
            "rss_kib": _distribution(metrics["rss"]),
            "context_switches": _distribution(metrics["context"]),
        }
    if client_pid is None:
        result["client"] = {"available": False, "reason": "client_stopped"}
    if gpu_utilization:
        result["gpu"] = {
            "available": True,
            "utilization_percent": _distribution(gpu_utilization),
            "vram_mib": _distribution(gpu_memory),
        }
    else:
        result["gpu"] = {"available": False, "reason": "provider_unavailable"}
    assert warning_total is not None
    return result, warning_total


def _warm_up(
    args: argparse.Namespace,
    *,
    providers: CaptureProviders,
    timing: CaptureTiming,
    safety: SafetyTracker,
    verify_state: Callable[[], object],
) -> None:
    previous = providers.process_snapshot(args.shell_pid)
    clock_ticks = int(os.sysconf("SC_CLK_TCK"))
    started_at = timing.monotonic()
    previous_time = started_at
    previous_epoch = timing.epoch()
    for elapsed_second in range(1, WARM_UP_SECONDS + 1):
        target = started_at + elapsed_second
        timing.sleep(max(0.0, target - timing.monotonic()))
        current_time = timing.monotonic()
        current_epoch = timing.epoch()
        _validate_clock_alignment(
            previous_monotonic=previous_time,
            current_monotonic=current_time,
            previous_epoch=previous_epoch,
            current_epoch=current_epoch,
        )
        warnings = providers.warning_counts(previous_epoch, current_epoch)
        verify_state()
        current = providers.process_snapshot(args.shell_pid)
        shell_cpu, _context_delta = _process_step(
            previous,
            current,
            elapsed=current_time - previous_time,
            clock_ticks=clock_ticks,
        )
        safety.observe(shell_cpu_percent=shell_cpu, warning_counts=warnings, phase="warm_up")
        previous = current
        previous_time = current_time
        previous_epoch = current_epoch
        if elapsed_second % 30 == 0:
            print(f"warm-up: {elapsed_second}/{WARM_UP_SECONDS}s", flush=True)
    elapsed_window = timing.monotonic() - started_at
    if not WARM_UP_SECONDS <= elapsed_window <= WARM_UP_SECONDS + ELAPSED_WINDOW_TOLERANCE_SECONDS:
        raise CaptureError("warm-up timing drift exceeded the fixed bound")


def _validate_client_arguments(
    cell: str,
    *,
    client_pid: int | None,
    port_file: object | None,
) -> None:
    """Translate strict client argument validation into the runner error contract."""

    try:
        validate_client_argument_pair(
            cell,
            client_pid_present=client_pid is not None,
            port_file_present=port_file is not None,
        )
    except PressureAbValidationError as exc:
        raise CaptureError(str(exc)) from exc


def _validate_client_backend_status(cell: str, status: Mapping[str, object]) -> None:
    """Require client-runtime proof of the exact A2 or B2 GNOME route."""

    if cell not in {"A2", "B2"}:
        raise CaptureError("client runtime backend state is not applicable")
    selected = status.get("selected_backend")
    report = status.get("report")
    helper_states = status.get("helper_states")
    if (
        not isinstance(selected, Mapping)
        or not isinstance(report, Mapping)
        or not isinstance(helper_states, list)
        or len(helper_states) != 1
        or not isinstance(helper_states[0], Mapping)
        or status.get("shadow_mode") is not False
        or report.get("source") != "client_runtime"
    ):
        raise CaptureError("client runtime backend state is not authoritative")
    helper = helper_states[0]
    if helper.get("helper") != "gnome_shell_extension" or helper.get("required") is not True:
        raise CaptureError("client runtime backend state has the wrong helper")
    expected_available = cell == "B2"
    expected_selected = {
        "family": "compositor_helper" if expected_available else "native_wayland",
        "instance": "gnome_shell_wayland",
    }
    if dict(selected) != expected_selected:
        raise CaptureError("client runtime backend state has the wrong selected route")
    if any(helper.get(key) is not expected_available for key in ("installed", "enabled", "approved")):
        raise CaptureError("client runtime backend state has the wrong helper availability")
    if expected_available:
        version = helper.get("version")
        if not isinstance(version, str) or _COMPONENT_VERSION.fullmatch(version) is None:
            raise CaptureError("client runtime backend state lacks a versioned helper")
        if "fallback_from" in status or status.get("fallback_reason") not in {None, ""}:
            raise CaptureError("client runtime backend state unexpectedly uses fallback")
        return
    if helper.get("detail") != "health_state=missing_service":
        raise CaptureError("client runtime backend state lacks missing-service proof")
    fallback = status.get("fallback_from")
    if not isinstance(fallback, Mapping) or dict(fallback) != {
        "family": "compositor_helper",
        "instance": "gnome_shell_wayland",
    }:
        raise CaptureError("client runtime backend state lacks documented fallback proof")
    if status.get("fallback_reason") != "missing_helper":
        raise CaptureError("client runtime backend state lacks missing-helper proof")


def _default_providers() -> CaptureProviders:
    return CaptureProviders(
        process_snapshot=_process_snapshot,
        gpu_sample=_gpu_sample,
        warning_counts=_normalized_warning_counts,
        client_snapshot=_request_client_snapshot,
        client_backend_status=_request_client_backend_status,
        helper_snapshot=_helper_snapshot,
        helper_owner_present=_helper_owner_present,
    )


def _verify_helper_state(
    *,
    helper_enabled: bool,
    providers: CaptureProviders,
) -> dict[str, object] | None:
    if helper_enabled:
        return providers.helper_snapshot()
    if providers.helper_owner_present():
        raise CaptureError("helper is available in a helper-disabled cell")
    return None


def _verify_client_state(
    *,
    cell: str,
    port_file: Path | None,
    providers: CaptureProviders,
) -> None:
    if cell not in {"A2", "B2"}:
        return
    if port_file is None:
        raise CaptureError("running-client cell lacks port metadata")
    _validate_client_backend_status(cell, providers.client_backend_status(port_file))


def _runner_cell_state(args: argparse.Namespace) -> dict[str, object]:
    client_running = args.cell in {"A2", "B2"}
    helper_enabled = args.cell in {"B1", "B2"}
    expected_backend = {
        "A1": "unavailable",
        "A2": "documented_unavailable",
        "B1": "unavailable",
        "B2": "helper_selected",
    }[args.cell]
    if not client_running and args.client_backend_state is not None:
        raise CaptureError("cell client backend state does not match the exact contract")
    supplied_backend = args.client_backend_state if client_running else "unavailable"
    if supplied_backend != expected_backend:
        raise CaptureError("cell client backend state does not match the exact contract")
    return {
        "client": "running" if client_running else "stopped",
        "helper": "full_helper" if helper_enabled else "disabled",
        "client_backend": supplied_backend,
        "client_pid_argument": "provided" if client_running else "unavailable",
        "port_file_argument": "provided" if client_running else "unavailable",
        "capture_diagnostics_enabled": False,
        "helper_diagnostics_enabled": False,
    }


def _runner_provenance(args: argparse.Namespace) -> dict[str, object]:
    if not isinstance(args.fixture_sha256, str) or _FIXTURE_HASH.fullmatch(args.fixture_sha256) is None:
        raise CaptureError("provenance fixture hash is invalid")
    if not isinstance(args.source_revision, str) or _SOURCE_REVISION.fullmatch(args.source_revision) is None:
        raise CaptureError("provenance source revision is invalid")
    for value in (args.plugin_version, args.client_version, args.helper_version):
        if not isinstance(value, str) or _COMPONENT_VERSION.fullmatch(value) is None:
            raise CaptureError("provenance component version is invalid")
    if (
        isinstance(args.display_width_px, bool)
        or not isinstance(args.display_width_px, int)
        or not 1 <= args.display_width_px <= 16384
        or isinstance(args.display_height_px, bool)
        or not isinstance(args.display_height_px, int)
        or not 1 <= args.display_height_px <= 16384
        or isinstance(args.refresh_hz, bool)
        or not isinstance(args.refresh_hz, (int, float))
        or not math.isfinite(float(args.refresh_hz))
        or not 0.0 < float(args.refresh_hz) <= 1000.0
        or args.quiet_host_confirmed is not True
    ):
        raise CaptureError("provenance display or quiet-host decision is invalid")
    return {
        "fixture_sha256": args.fixture_sha256,
        "source_revision": args.source_revision,
        "component_versions": {
            "plugin": args.plugin_version,
            "client": args.client_version,
            "helper": args.helper_version,
        },
        "display": {
            "monitor": "A",
            "width_px": args.display_width_px,
            "height_px": args.display_height_px,
            "scale_percent": 100,
            "refresh_hz": args.refresh_hz,
        },
        "workload": "stable_windowed_fixed_fixture",
        "quiet_host": args.quiet_host_confirmed,
    }


def _build_cell_document(
    args: argparse.Namespace,
    samples: list[dict[str, object]],
) -> dict[str, object]:
    document: dict[str, object] = {
        "schema_version": 1,
        "cell": args.cell,
        "execution_order": args.execution_order,
        "provenance": _runner_provenance(args),
        "state": _runner_cell_state(args),
        "samples": samples,
    }
    parse_pressure_ab_cell_document(document)
    return document


def _helper_work_delta(
    before: Mapping[str, object],
    after: Mapping[str, object],
) -> dict[str, int]:
    if before["origin"] != after["origin"]:
        raise CaptureError("helper restarted during sample")
    before_counts = before["counters"]
    after_counts = after["counters"]
    if not isinstance(before_counts, Mapping) or not isinstance(after_counts, Mapping):
        raise CaptureError("helper pressure counters are malformed")
    deltas: dict[str, int] = {}
    for name in ("target_queries", "presentation_calls"):
        before_value = int(before_counts[name])
        after_value = int(after_counts[name])
        if before_value == WORK_COUNTER_MAX or after_value == WORK_COUNTER_MAX:
            raise CaptureError("helper counter saturated during sample")
        if after_value < before_value:
            raise CaptureError("helper counter reset during sample")
        deltas[name] = after_value - before_value
    return deltas


def _capture(
    args: argparse.Namespace,
    *,
    providers: CaptureProviders | None = None,
    timing: CaptureTiming | None = None,
) -> dict[str, object]:
    providers = providers or _default_providers()
    timing = timing or CaptureTiming()
    state = CELL_STATE[args.cell]
    phase = "capture"
    try:
        _validate_client_arguments(args.cell, client_pid=args.client_pid, port_file=args.port_file)
        _runner_cell_state(args)
        _runner_provenance(args)
        if (
            isinstance(args.execution_order, bool)
            or not isinstance(args.execution_order, int)
            or not 1 <= args.execution_order <= 4
        ):
            raise CaptureError("execution order is invalid")
        if args.quiet_host_confirmed is not True or getattr(args, "operator_observing", False) is not True:
            raise CaptureError("quiet host and continuous operator observation must be confirmed")
        providers.process_snapshot(args.shell_pid)
        if args.client_pid is not None:
            providers.process_snapshot(args.client_pid)
        _verify_helper_state(helper_enabled=bool(state["helper"]), providers=providers)
        _verify_client_state(cell=args.cell, port_file=args.port_file, providers=providers)

        print(
            "Continuous operator observation required: press Ctrl-C for any visible Shell instability.",
            flush=True,
        )
        print(f"{args.cell}: fixed warm-up {WARM_UP_SECONDS}s", flush=True)
        phase = "warm_up"
        cell_safety = SafetyTracker()

        def verify_warm_up_state() -> None:
            _verify_helper_state(helper_enabled=bool(state["helper"]), providers=providers)
            _verify_client_state(cell=args.cell, port_file=args.port_file, providers=providers)

        _warm_up(
            args,
            providers=providers,
            timing=timing,
            safety=cell_safety,
            verify_state=verify_warm_up_state,
        )

        process_origins = {"shell": providers.process_snapshot(args.shell_pid)["start_ticks"]}
        if args.client_pid is not None:
            process_origins["client"] = providers.process_snapshot(args.client_pid)["start_ticks"]
        helper_initial = _verify_helper_state(
            helper_enabled=bool(state["helper"]),
            providers=providers,
        )
        helper_cell_origin = helper_initial["origin"] if helper_initial else None
        helper_evidence_origin = uuid.uuid4().hex if helper_initial else "unavailable"
        client_cell_origin: object | None = None
        samples: list[dict[str, object]] = []
        phase = "observation"
        for repetition in range(1, REPETITIONS + 1):
            _verify_client_state(cell=args.cell, port_file=args.port_file, providers=providers)
            helper_before = _verify_helper_state(
                helper_enabled=bool(state["helper"]),
                providers=providers,
            )
            if helper_before is not None and helper_before["origin"] != helper_cell_origin:
                raise CaptureError("helper restarted during the post-warm-up cell")
            client_before = providers.client_snapshot(args.port_file) if args.port_file else None
            if client_before is not None:
                if client_cell_origin is None:
                    client_cell_origin = client_before["origin_id"]
                elif client_before["origin_id"] != client_cell_origin:
                    raise CaptureError("client restarted during the post-warm-up cell")
            print(f"{args.cell} repetition {repetition}/{REPETITIONS}", flush=True)

            def verify_observation_state() -> None:
                helper_now = _verify_helper_state(
                    helper_enabled=bool(state["helper"]),
                    providers=providers,
                )
                if helper_now is not None and helper_now["origin"] != helper_cell_origin:
                    raise CaptureError("helper restarted during the post-warm-up cell")

            resources, warnings = _sample_processes(
                args.shell_pid,
                args.client_pid,
                providers=providers,
                timing=timing,
                safety=cell_safety,
                verify_state=verify_observation_state,
                expected_process_origins=process_origins,
                phase="observation",
            )
            helper_after = _verify_helper_state(
                helper_enabled=bool(state["helper"]),
                providers=providers,
            )
            client_after = providers.client_snapshot(args.port_file) if args.port_file else None
            _verify_client_state(cell=args.cell, port_file=args.port_file, providers=providers)
            if client_after is not None and client_after["origin_id"] != client_cell_origin:
                raise CaptureError("client restarted during the post-warm-up cell")

            client_work: dict[str, object]
            if client_before is not None and client_after is not None:
                try:
                    client_delta = delta_work_snapshots(client_before, client_after)
                except PressureAbValidationError as exc:
                    raise CaptureError("client work endpoints are unsafe") from exc
                client_work = {
                    "available": True,
                    "origin_id": client_before["origin_id"],
                    "counters": client_delta,
                }
            else:
                client_work = {
                    "available": False,
                    "reason": "client_stopped",
                    "origin_id": "unavailable",
                    "counters": {},
                }
            helper_work: dict[str, object] = {
                "available": False,
                "reason": "helper_disabled",
                "origin_id": "unavailable",
                "counters": {},
            }
            actor_counts: dict[str, object] = {
                "available": False,
                "reason": "helper_disabled",
                "values": {},
            }
            if helper_before is not None and helper_after is not None:
                if helper_after["origin"] != helper_cell_origin:
                    raise CaptureError("helper restarted during the post-warm-up cell")
                helper_work = {
                    "available": True,
                    "origin_id": helper_evidence_origin,
                    "counters": _helper_work_delta(helper_before, helper_after),
                }
                actors = helper_after["actors"]
                if not isinstance(actors, Mapping):
                    raise CaptureError("helper actor aggregates are malformed")
                actor_counts = {
                    "available": True,
                    "values": {str(name): int(value) for name, value in actors.items()},
                }
            samples.append(
                {
                    "schema_version": 1,
                    "cell": args.cell,
                    "repetition": repetition,
                    "warm_up_seconds": WARM_UP_SECONDS,
                    "duration_seconds": SAMPLE_SECONDS,
                    "diagnostics_enabled": False,
                    "resources": resources,
                    "client_work": client_work,
                    "helper_work": helper_work,
                    "actor_counts": actor_counts,
                    "warning_counts": warnings,
                    "safety": {field: False for field in SAFETY_FIELDS},
                    "continuity": {
                        "client_restarted": False,
                        "helper_restarted": False,
                        "client_counter_decreased": False,
                        "helper_counter_decreased": False,
                        "client_counter_saturated": False,
                        "helper_counter_saturated": False,
                    },
                }
            )
        return _build_cell_document(args, samples)
    except KeyboardInterrupt as exc:
        raise CaptureStopped(
            phase=phase,
            reason_code="operator_interrupt",
            safety_field=None,
        ) from exc


def _build_stop_document(
    args: argparse.Namespace,
    stopped: CaptureStopped,
) -> dict[str, object]:
    """Build a privacy-safe non-acceptance artifact with no partial measurements."""

    _validate_client_arguments(args.cell, client_pid=args.client_pid, port_file=args.port_file)
    _runner_cell_state(args)
    if isinstance(args.execution_order, bool) or not isinstance(args.execution_order, int):
        raise CaptureError("stop evidence execution order is invalid")
    if not 1 <= args.execution_order <= 4:
        raise CaptureError("stop evidence execution order is invalid")
    provenance = _runner_provenance(args)
    return {
        "schema_version": 1,
        "artifact_type": "pressure_ab_stop",
        "accepted": False,
        "cell": args.cell,
        "execution_order": args.execution_order,
        "phase": stopped.phase,
        "reason_code": stopped.reason_code,
        "safety_field": stopped.safety_field or "unavailable",
        "provenance": provenance,
    }


def _write_new_json(path: Path, document: Mapping[str, object]) -> None:
    """Write one JSON artifact exclusively so no success or stop can be replaced."""

    path.parent.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        with path.open("x", encoding="utf-8") as output:
            created = True
            json.dump(document, output, indent=2, sort_keys=True)
            output.write("\n")
    except BaseException:
        if created:
            try:
                path.unlink()
            except OSError:
                pass
        raise


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.output.exists():
        sys.stderr.write("backend_pressure_ab: output already exists\n")
        return 2
    try:
        document = _capture(args)
    except CaptureStopped as stopped:
        try:
            _write_new_json(args.output, _build_stop_document(args, stopped))
        except FileExistsError:
            sys.stderr.write("backend_pressure_ab: output already exists\n")
            return 2
        except OSError:
            sys.stderr.write("backend_pressure_ab: output write failed\n")
            return 2
        sys.stderr.write(f"backend_pressure_ab: capture stopped ({stopped.reason_code})\n")
        return 2
    except KeyboardInterrupt:
        interrupt_stop = CaptureStopped(
            phase="capture",
            reason_code="operator_interrupt",
            safety_field=None,
        )
        try:
            _write_new_json(args.output, _build_stop_document(args, interrupt_stop))
        except FileExistsError:
            sys.stderr.write("backend_pressure_ab: output already exists\n")
            return 2
        except OSError:
            sys.stderr.write("backend_pressure_ab: output write failed\n")
            return 2
        sys.stderr.write("backend_pressure_ab: capture stopped (operator_interrupt)\n")
        return 2
    except (CaptureError, PressureAbValidationError, EOFError, OSError) as exc:
        sys.stderr.write(f"backend_pressure_ab: {exc}\n")
        return 2
    try:
        _write_new_json(args.output, document)
    except FileExistsError:
        sys.stderr.write("backend_pressure_ab: output already exists\n")
        return 2
    except OSError:
        sys.stderr.write("backend_pressure_ab: output write failed\n")
        return 2
    print(f"Validated cell written: {args.output.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
