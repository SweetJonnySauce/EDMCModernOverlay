#!/usr/bin/env python3
"""Interactively collect one privacy-safe Step 03 performance repetition."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from overlay_client.backend.performance_capture import (  # noqa: E402
    build_performance_capture_document,
    calculate_process_cpu_percent,
    parse_performance_event_line,
    parse_repaint_stats_line,
)
from overlay_client.backend.performance_evidence import (  # noqa: E402
    EvidenceValidationError,
    parse_performance_capture,
    parse_performance_manifest,
)


_MANUAL_FIELDS = (
    "dual_visible_presenters",
    "title_bar_intermediate",
    "monitor_relative_intermediate",
    "black_surface",
    "focus_trap",
    "unexpected_identity",
    "premature_commitment",
    "material_hitch",
)


@dataclass(frozen=True)
class _LogCursor:
    device: int
    inode: int
    offset: int


@dataclass(frozen=True)
class _LogSegment:
    path: Path
    device: int
    inode: int
    start: int
    end: int


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--repetition", required=True, type=int)
    parser.add_argument("--capture-role", choices=("baseline", "candidate"), default="baseline")
    parser.add_argument("--client-pid", required=True, type=int)
    parser.add_argument("--gnome-shell-pid", required=True, type=int)
    parser.add_argument("--client-log", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def _process_ticks(pid: int) -> int:
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
        fields = stat[stat.rfind(")") + 2 :].split()
        return int(fields[11]) + int(fields[12])
    except (OSError, ValueError, IndexError) as exc:
        raise EvidenceValidationError("a required capture process is unavailable") from exc


def _sample_idle_cpu(client_pid: int, shell_pid: int, interval_seconds: int) -> tuple[list[float], list[float]]:
    clock_ticks = int(os.sysconf("SC_CLK_TCK"))
    client_samples: list[float] = []
    shell_samples: list[float] = []
    previous_client = _process_ticks(client_pid)
    previous_shell = _process_ticks(shell_pid)
    previous_time = time.perf_counter()
    for second in range(1, interval_seconds + 1):
        target = previous_time + 1.0
        time.sleep(max(0.0, target - time.perf_counter()))
        current_time = time.perf_counter()
        current_client = _process_ticks(client_pid)
        current_shell = _process_ticks(shell_pid)
        elapsed = current_time - previous_time
        client_samples.append(
            calculate_process_cpu_percent(
                previous_client,
                current_client,
                elapsed_seconds=elapsed,
                clock_ticks_per_second=clock_ticks,
            )
        )
        shell_samples.append(
            calculate_process_cpu_percent(
                previous_shell,
                current_shell,
                elapsed_seconds=elapsed,
                clock_ticks_per_second=clock_ticks,
            )
        )
        previous_client = current_client
        previous_shell = current_shell
        previous_time = current_time
        if second % 10 == 0 or second == interval_seconds:
            print(f"idle CPU: {second}/{interval_seconds}s", flush=True)
    return client_samples, shell_samples


def _countdown(label: str, seconds: int) -> None:
    print(f"{label}: {seconds}s", flush=True)
    for elapsed in range(1, seconds + 1):
        time.sleep(1.0)
        if elapsed % 10 == 0 or elapsed == seconds:
            print(f"{label}: {elapsed}/{seconds}s", flush=True)


def _capture_log_cursor(path: Path) -> _LogCursor:
    try:
        status = path.stat()
    except OSError as exc:
        raise EvidenceValidationError("unable to inspect the overlay client diagnostic log") from exc
    return _LogCursor(device=status.st_dev, inode=status.st_ino, offset=status.st_size)


def _numeric_rotation_paths(path: Path) -> dict[int, Path]:
    paths = {0: path}
    prefix = f"{path.name}."
    for candidate in path.parent.glob(f"{path.name}.*"):
        suffix = candidate.name.removeprefix(prefix)
        if suffix.isdigit() and int(suffix) > 0:
            paths[int(suffix)] = candidate
    return paths


def _log_segments_since_cursor(path: Path, cursor: _LogCursor) -> tuple[_LogSegment, ...]:
    indexed_paths = _numeric_rotation_paths(path)
    indexed_status: dict[int, os.stat_result] = {}
    cursor_index: int | None = None
    for index, candidate in indexed_paths.items():
        try:
            status = candidate.stat()
        except OSError:
            continue
        indexed_status[index] = status
        if (status.st_dev, status.st_ino) == (cursor.device, cursor.inode):
            cursor_index = index

    if cursor_index is None:
        raise EvidenceValidationError("diagnostic log rotated beyond retained history during observation")

    required_indices = tuple(range(cursor_index, -1, -1))
    missing = [index for index in required_indices if index not in indexed_status]
    if missing:
        raise EvidenceValidationError("diagnostic log rotation chain is incomplete")

    segments: list[_LogSegment] = []
    for index in required_indices:
        candidate = indexed_paths[index]
        status = indexed_status[index]
        start = cursor.offset if index == cursor_index else 0
        if status.st_size < start:
            raise EvidenceValidationError("diagnostic log was truncated before the capture cursor")
        segments.append(
            _LogSegment(
                path=candidate,
                device=status.st_dev,
                inode=status.st_ino,
                start=start,
                end=status.st_size,
            )
        )
    return tuple(segments)


def _read_log_slice(path: Path, cursor: _LogCursor) -> tuple[list[dict[str, object]], list[dict[str, int]]]:
    text_parts: list[str] = []
    try:
        for segment in _log_segments_since_cursor(path, cursor):
            with segment.path.open("rb") as handle:
                opened_status = os.fstat(handle.fileno())
                if (opened_status.st_dev, opened_status.st_ino) != (segment.device, segment.inode):
                    raise EvidenceValidationError("diagnostic log rotated again while reading the observation")
                handle.seek(segment.start)
                text_parts.append(handle.read(segment.end - segment.start).decode("utf-8", errors="replace"))
    except OSError as exc:
        raise EvidenceValidationError("unable to read the overlay client diagnostic log") from exc
    events: list[dict[str, object]] = []
    repaint_intervals: list[dict[str, int]] = []
    for line in "".join(text_parts).splitlines():
        event = parse_performance_event_line(line)
        if event is not None:
            events.append(event)
        repaint = parse_repaint_stats_line(line)
        if repaint is not None:
            repaint_intervals.append(repaint)
    return events, repaint_intervals


def _manual_observations() -> dict[str, object]:
    print("Manual review fields:", flush=True)
    for field in _MANUAL_FIELDS:
        print(f"- {field}", flush=True)
    print("Enter 'none' if no issue occurred, or comma-separated field names that occurred.", flush=True)
    response = input("manual review> ").strip().lower()
    selected = set() if response == "none" else {item.strip() for item in response.split(",") if item.strip()}
    unknown = sorted(selected - set(_MANUAL_FIELDS))
    if unknown:
        raise EvidenceValidationError(f"unknown manual observation field(s): {unknown}")
    return {**{field: field in selected for field in _MANUAL_FIELDS}, "note_codes": []}


def _run(args: argparse.Namespace) -> Path:
    manifest = parse_performance_manifest(args.manifest)
    scenario = manifest.scenario(args.scenario)
    if args.repetition < 1 or args.repetition > manifest.timing.repetitions:
        raise EvidenceValidationError("repetition is outside the manifest range")
    if args.output.exists():
        raise EvidenceValidationError("output already exists; captures are never overwritten")
    if not args.client_log.is_file():
        raise EvidenceValidationError("overlay client diagnostic log is unavailable")
    _process_ticks(args.client_pid)
    _process_ticks(args.gnome_shell_pid)

    print(f"Ready: {scenario.scenario_id}, repetition {args.repetition}", flush=True)
    input("Press Enter to begin the fixed warm-up. ")
    _countdown("warm-up", manifest.timing.warm_up_seconds)
    print("Keep the game and overlay idle for the CPU interval.", flush=True)
    client_cpu, shell_cpu = _sample_idle_cpu(
        args.client_pid,
        args.gnome_shell_pid,
        manifest.timing.idle_cpu_seconds,
    )
    print("Prepare the scenario start mode/monitor now.", flush=True)
    input("Press Enter when ready to begin the observation/action interval. ")
    log_cursor = _capture_log_cursor(args.client_log)
    _countdown("observation - perform the named scenario now", manifest.timing.observation_seconds)
    events, repaint_intervals = _read_log_slice(args.client_log, log_cursor)
    manual = _manual_observations()
    document = build_performance_capture_document(
        manifest,
        scenario_id=scenario.scenario_id,
        repetition=args.repetition,
        capture_role=args.capture_role,
        events=events,
        repaint_intervals=repaint_intervals,
        client_cpu_samples=client_cpu,
        gnome_shell_cpu_samples=shell_cpu,
        manual_observations=manual,
    )
    parse_performance_capture(document, manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return args.output


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        output = _run(args)
    except (EvidenceValidationError, OSError, EOFError, KeyboardInterrupt) as exc:
        sys.stderr.write(f"backend_performance_capture: {exc}\n")
        return 2
    print(f"Validated capture written: {output.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
