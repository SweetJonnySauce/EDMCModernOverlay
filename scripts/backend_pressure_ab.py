#!/usr/bin/env python3
"""Capture one controlled diagnostics-off helper-pressure A/B cell."""

from __future__ import annotations

import argparse
import ast
import json
import math
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from overlay_client.backend.bundles._gnome_shell_helper_presentation import (  # noqa: E402
    fetch_gnome_shell_helper_health_via_gdbus,
)
from overlay_client.backend.pressure_ab import (  # noqa: E402
    PRESSURE_AB_CELLS,
    PressureAbValidationError,
    delta_work_snapshots,
    parse_work_snapshot,
)


WARM_UP_SECONDS = 300
SAMPLE_SECONDS = 60
REPETITIONS = 3
SAFETY_FIELDS = (
    "flashing",
    "input_loss",
    "drag_corruption",
    "repeated_mutter_assertions",
    "rapidly_rising_shell_cpu",
)
CELL_STATE = {
    "A1": {"client": False, "helper": False},
    "A2": {"client": True, "helper": False},
    "B1": {"client": False, "helper": True},
    "B2": {"client": True, "helper": True},
}


class CaptureError(RuntimeError):
    """Raised when a live pressure sample cannot be accepted."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cell", required=True, choices=PRESSURE_AB_CELLS)
    parser.add_argument("--shell-pid", required=True, type=int)
    parser.add_argument("--client-pid", type=int)
    parser.add_argument("--port-file", type=Path)
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


def _request_client_snapshot(port_file: Path) -> dict[str, object]:
    request = json.dumps({"cli": "pressure_snapshot"}, separators=(",", ":")).encode() + b"\n"
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
                if payload.get("status") != "ok" or not isinstance(payload.get("snapshot"), Mapping):
                    raise CaptureError(str(payload.get("reason") or "client pressure snapshot unavailable"))
                return parse_work_snapshot(payload["snapshot"])
    except (OSError, PressureAbValidationError) as exc:
        raise CaptureError("client pressure snapshot request failed") from exc
    raise CaptureError("client pressure snapshot response timed out")


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
            value = json.loads(unpacked[0])
    if not isinstance(value, Mapping):
        raise CaptureError("helper health response is malformed")
    return value


def _helper_snapshot() -> dict[str, object]:
    payload = _decode_gdbus_json(fetch_gnome_shell_helper_health_via_gdbus())
    gate = payload.get("feature_gate")
    counters = payload.get("pressure_counters")
    actors = payload.get("actor_counts")
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
    values: dict[str, int] = {"ticks": int(fields[11]) + int(fields[12])}
    for line in status:
        if line.startswith("VmRSS:"):
            values["rss_kib"] = int(line.split()[1])
        elif line.startswith("voluntary_ctxt_switches:"):
            values["voluntary"] = int(line.split()[1])
        elif line.startswith("nonvoluntary_ctxt_switches:"):
            values["involuntary"] = int(line.split()[1])
    if set(values) != {"ticks", "rss_kib", "voluntary", "involuntary"}:
        raise CaptureError("required process aggregates are unavailable")
    return values


def _gpu_sample() -> tuple[float, float] | None:
    if shutil.which("nvidia-smi") is None:
        return None


def _normalized_warning_counts(since_epoch: float) -> dict[str, int | bool]:
    """Count only approved warning classes and discard all journal text."""

    if shutil.which("journalctl") is None:
        return {"available": False, "mutter_assertions": 0, "shell_warnings": 0}
    result = subprocess.run(
        [
            "journalctl",
            "--user",
            "--since",
            f"@{since_epoch:.6f}",
            "--output=cat",
            "--no-pager",
        ],
        text=True,
        capture_output=True,
        timeout=5.0,
        check=False,
    )
    if result.returncode != 0:
        return {"available": False, "mutter_assertions": 0, "shell_warnings": 0}
    mutter_assertions = 0
    shell_warnings = 0
    for line in result.stdout.splitlines():
        normalized = line.casefold()
        if "mutter" in normalized and ("assertion" in normalized or "assert failed" in normalized):
            mutter_assertions += 1
        if "gnome-shell" in normalized and any(
            token in normalized for token in ("warning", "critical", "assertion", "assert failed")
        ):
            shell_warnings += 1
    return {
        "available": True,
        "mutter_assertions": min(1_000_000, mutter_assertions),
        "shell_warnings": min(1_000_000, shell_warnings),
    }
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
    if result.returncode != 0:
        return None
    try:
        utilization, memory = result.stdout.splitlines()[0].split(",", 1)
        return max(0.0, min(100.0, float(utilization))), max(0.0, float(memory))
    except (IndexError, ValueError):
        return None


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


def _sample_processes(shell_pid: int, client_pid: int | None) -> dict[str, object]:
    clock_ticks = int(os.sysconf("SC_CLK_TCK"))
    process_ids = {"shell": shell_pid}
    if client_pid is not None:
        process_ids["client"] = client_pid
    previous = {name: _process_snapshot(pid) for name, pid in process_ids.items()}
    previous_time = time.perf_counter()
    observations: dict[str, dict[str, list[float]]] = {
        name: {"cpu": [], "rss": [], "context": []} for name in process_ids
    }
    gpu_utilization: list[float] = []
    gpu_memory: list[float] = []
    for second in range(1, SAMPLE_SECONDS + 1):
        target = previous_time + 1.0
        time.sleep(max(0.0, target - time.perf_counter()))
        current_time = time.perf_counter()
        elapsed = current_time - previous_time
        for name, pid in process_ids.items():
            current = _process_snapshot(pid)
            tick_delta = current["ticks"] - previous[name]["ticks"]
            context_delta = (
                current["voluntary"] + current["involuntary"]
                - previous[name]["voluntary"] - previous[name]["involuntary"]
            )
            if tick_delta < 0 or context_delta < 0:
                raise CaptureError("process counters reset during sample")
            observations[name]["cpu"].append(tick_delta / clock_ticks / elapsed * 100.0)
            observations[name]["rss"].append(float(current["rss_kib"]))
            observations[name]["context"].append(float(context_delta))
            previous[name] = current
        gpu = _gpu_sample()
        if gpu is not None:
            gpu_utilization.append(gpu[0])
            gpu_memory.append(gpu[1])
        previous_time = current_time
        if second % 10 == 0:
            print(f"sample: {second}/{SAMPLE_SECONDS}s", flush=True)
    result: dict[str, object] = {}
    for name, metrics in observations.items():
        result[name] = {metric: _distribution(values) for metric, values in metrics.items()}
    result["gpu"] = {
        "available": bool(gpu_utilization),
        "utilization_percent": _distribution(gpu_utilization),
        "vram_mib": _distribution(gpu_memory),
    }
    return result


def _manual_safety() -> tuple[str, ...]:
    print("Safety fields: " + ", ".join(SAFETY_FIELDS), flush=True)
    response = input("Enter none, or comma-separated fields observed> ").strip().lower()
    selected = () if response == "none" else tuple(item.strip() for item in response.split(",") if item.strip())
    if any(item not in SAFETY_FIELDS for item in selected):
        raise CaptureError("unknown safety observation")
    return selected


def _capture(args: argparse.Namespace) -> dict[str, object]:
    state = CELL_STATE[args.cell]
    if state["client"] != bool(args.client_pid and args.port_file):
        raise CaptureError("cell client state does not match --client-pid/--port-file")
    _process_snapshot(args.shell_pid)
    if args.client_pid is not None:
        _process_snapshot(args.client_pid)
    helper_before = _helper_snapshot() if state["helper"] else None
    if not state["helper"]:
        try:
            _helper_snapshot()
        except Exception:
            pass
        else:
            raise CaptureError("helper is available in a helper-disabled cell")
    print(f"{args.cell}: fixed warm-up {WARM_UP_SECONDS}s", flush=True)
    for elapsed in range(1, WARM_UP_SECONDS + 1):
        time.sleep(1.0)
        if elapsed % 30 == 0:
            print(f"warm-up: {elapsed}/{WARM_UP_SECONDS}s", flush=True)
    samples: list[dict[str, object]] = []
    for repetition in range(1, REPETITIONS + 1):
        client_before = _request_client_snapshot(args.port_file) if args.port_file else None
        helper_before = _helper_snapshot() if state["helper"] else None
        print(f"{args.cell} repetition {repetition}/{REPETITIONS}", flush=True)
        journal_since = time.time()
        resources = _sample_processes(args.shell_pid, args.client_pid)
        warnings = _normalized_warning_counts(journal_since)
        helper_after = _helper_snapshot() if state["helper"] else None
        client_after = _request_client_snapshot(args.port_file) if args.port_file else None
        safety = _manual_safety()
        if safety:
            raise CaptureError("safety stop: " + ",".join(safety))
        client_work = delta_work_snapshots(client_before, client_after) if client_before and client_after else {}
        helper_work: dict[str, int] = {}
        actor_counts: dict[str, int] = {}
        if helper_before and helper_after:
            if helper_before["origin"] != helper_after["origin"]:
                raise CaptureError("helper restarted during sample")
            before_counts = helper_before["counters"]
            after_counts = helper_after["counters"]
            assert isinstance(before_counts, Mapping) and isinstance(after_counts, Mapping)
            for name in ("target_queries", "presentation_calls"):
                delta = int(after_counts[name]) - int(before_counts[name])
                if delta < 0:
                    raise CaptureError("helper counter reset during sample")
                helper_work[name] = delta
            actors = helper_after["actors"]
            assert isinstance(actors, Mapping)
            actor_counts = {str(name): int(value) for name, value in actors.items()}
        samples.append(
            {
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
                "safety_failures": [],
            }
        )
    return {"schema_version": 1, "cell": args.cell, "samples": samples}


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.output.exists():
        sys.stderr.write("backend_pressure_ab: output already exists\n")
        return 2
    try:
        document = _capture(args)
    except (CaptureError, PressureAbValidationError, EOFError, KeyboardInterrupt, OSError) as exc:
        sys.stderr.write(f"backend_pressure_ab: {exc}\n")
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Validated cell written: {args.output.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
