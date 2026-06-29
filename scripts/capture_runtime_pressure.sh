#!/usr/bin/env bash

set -u

LOG_DIR="/home/jon/edmc-logs/EDMCModernOverlay"
LABEL_RAW="${1:-manual}"

if [[ "$LABEL_RAW" == "-h" || "$LABEL_RAW" == "--help" ]]; then
    cat <<'EOF'
Usage: scripts/capture_runtime_pressure.sh [label]

Passive deep runtime-pressure capture for GNOME Shell Raster diagnosis.

Suggested labels:
  baseline
  soak_sample
  pre_edmc_shutdown
  post_edmc_shutdown_bad_state
  post_recovery

Detailed output is written to CAPTURE_LOG. Stdout is intentionally concise.
EOF
    exit 0
fi

LABEL_SAFE="$(printf '%s' "$LABEL_RAW" | tr -c 'A-Za-z0-9_.-' '_' | sed 's/^_*//; s/_*$//')"
if [[ -z "$LABEL_SAFE" ]]; then
    LABEL_SAFE="manual"
fi

CAPTURE_START="$(date --iso-8601=seconds)"
CAPTURE_STAMP="$(date '+%Y%m%d_%H%M%S')"
CAPTURE_LOG="${LOG_DIR}/runtime_pressure_${LABEL_SAFE}_${CAPTURE_STAMP}.log"
CAPTURE_LATEST="${LOG_DIR}/runtime_pressure.latest"
TARGET_STATE_FILE="$(mktemp)"
TMP_DIR="$(mktemp -d)"
JOURNAL_SINCE="${RUNTIME_PRESSURE_JOURNAL_SINCE:-30 minutes ago}"
PROCESS_PATTERN='[E]DMarketConnector.py|[o]verlay_client|[E]liteDangerous|[E]DLaunch|[W]atchDog64|[s]team.exe|[s]teamwebhelper|[p]v-adverb|[s]rt-bwrap|[r]eaper|[w]ineserver|[w]inedevice|[e]xplorer.exe|[s]ervices.exe|[p]roton|[g]nome-shell|[X]wayland|[f]irefox|[F]irefox|[x]dg-desktop-portal|[x]dg-document-portal|[n]vidia|[N]VIDIA|[n]vkms|[p]ipewire|[w]ireplumber|[p]ulseaudio'
TARGET_PIDS=()

cleanup() {
    status=$?
    rm -rf "$TMP_DIR" "$TARGET_STATE_FILE"
    if [[ "$status" -ne 0 ]]; then
        echo "capture: failed status=$status"
        echo "CAPTURE_LOG=$CAPTURE_LOG"
    fi
    exit "$status"
}
trap cleanup EXIT

mkdir -p "$LOG_DIR"
printf '%s\n' "$CAPTURE_LOG" > "$CAPTURE_LATEST"

echo "CAPTURE_LOG=$CAPTURE_LOG"
echo "capture: started label=$LABEL_RAW"

have() {
    command -v "$1" >/dev/null 2>&1
}

section() {
    echo
    echo "=== $* ==="
}

run_optional() {
    label="$1"
    shift
    echo
    echo "\$ $*"
    if ! have "$1"; then
        echo "$label: unavailable; missing command '$1'"
        return 0
    fi
    "$@" || echo "$label: command failed status=$?"
}

print_file_if_readable() {
    path="$1"
    if [[ -r "$path" ]]; then
        echo
        echo "--- $path ---"
        cat "$path" || echo "read failed: $path"
    else
        echo
        echo "--- $path unavailable/read-protected ---"
    fi
}

dbus_call() {
    if ! have gdbus; then
        echo "gdbus unavailable"
        return 0
    fi
    gdbus call --session \
        --dest org.edmc.ModernOverlay.Helper \
        --object-path /org/edmc/ModernOverlay/Helper \
        --method "$@" || true
}

collect_target_pids() {
    TARGET_PIDS=()
    if ! have pgrep; then
        echo "pgrep unavailable; target PID collection skipped"
        return 0
    fi
    mapfile -t TARGET_PIDS < <(pgrep -f "$PROCESS_PATTERN" | sort -n -u)
}

pid_csv() {
    local IFS=,
    printf '%s' "${TARGET_PIDS[*]}"
}

extract_target_token() {
    if ! have python3; then
        echo ""
        return 0
    fi
    python3 - "$TARGET_STATE_FILE" <<'PY'
import ast
import json
import sys

try:
    text = open(sys.argv[1], encoding="utf-8").read().strip()
    payload = ast.literal_eval(text)[0]
    print(json.loads(payload).get("target", {}).get("targetToken", ""))
except Exception:
    print("")
PY
}

diagnostic_request() {
    if ! have python3; then
        echo ""
        return 0
    fi
    python3 - "$TARGET_STATE_FILE" <<'PY'
import ast
import json
import sys

try:
    text = open(sys.argv[1], encoding="utf-8").read().strip()
    payload = json.loads(ast.literal_eval(text)[0])
    target = payload.get("target") or {}
    rect = (
        target.get("contentRect")
        or target.get("frameRect")
        or target.get("monitorRect")
        or {"x": 0, "y": 0, "width": 1, "height": 1}
    )
    token = target.get("targetToken") or ""
    if not token:
        print("")
    else:
        print(json.dumps({
            "action": "attach",
            "target_token": token,
            "content_rect": {
                "x": int(rect.get("x", 0)),
                "y": int(rect.get("y", 0)),
                "width": int(rect.get("width", 1)),
                "height": int(rect.get("height", 1)),
            },
            "rect_tolerance": 2,
            "shell_actor_proof": True,
            "shell_actor_proof_action": "diagnose_groups",
        }))
except Exception:
    print("")
PY
}

print_process_census() {
    section "Process census"
    echo "PROCESS_PATTERN=$PROCESS_PATTERN"
    echo
    echo "Matched process command lines:"
    if have pgrep; then
        pgrep -af "$PROCESS_PATTERN" || true
    else
        echo "pgrep unavailable"
    fi

    collect_target_pids
    echo
    echo "Target PIDs: ${TARGET_PIDS[*]:-none}"
    if [[ "${#TARGET_PIDS[@]}" -eq 0 ]]; then
        return 0
    fi

    echo
    echo "ps summary:"
    ps -o pid,ppid,stat,etimes,pcpu,rss,vsz,nlwp,comm,args -p "$(pid_csv)" || true

    if have pstree; then
        echo
        echo "Process ancestry samples:"
        for pid in "${TARGET_PIDS[@]}"; do
            pstree -sp "$pid" 2>/dev/null || true
        done
    else
        echo
        echo "pstree unavailable"
    fi
}

summarize_fd_for_pid() {
    local pid="$1"
    local fd_dir="/proc/${pid}/fd"
    local comm
    comm="$(cat "/proc/${pid}/comm" 2>/dev/null || echo "unknown")"

    echo
    echo "--- FD summary pid=$pid comm=$comm ---"
    if [[ ! -d "$fd_dir" ]]; then
        echo "fd directory unavailable"
        return 0
    fi

    local total=0 sockets=0 pipes=0 eventfds=0 timerfds=0 inotifyfds=0 memfds=0 deleted=0 tmp_paths=0 runtime_paths=0 log_paths=0 raster_paths=0 unreadable=0
    local samples=()
    local fd_path target

    for fd_path in "$fd_dir"/*; do
        [[ -e "$fd_path" || -L "$fd_path" ]] || continue
        total=$((total + 1))
        if ! target="$(readlink "$fd_path" 2>/dev/null)"; then
            target="<unreadable>"
            unreadable=$((unreadable + 1))
        fi

        [[ "$target" == socket:* ]] && sockets=$((sockets + 1))
        [[ "$target" == pipe:* ]] && pipes=$((pipes + 1))
        [[ "$target" == anon_inode:\[eventfd\]* ]] && eventfds=$((eventfds + 1))
        [[ "$target" == anon_inode:\[timerfd\]* ]] && timerfds=$((timerfds + 1))
        [[ "$target" == anon_inode:inotify* || "$target" == anon_inode:\[inotify\]* ]] && inotifyfds=$((inotifyfds + 1))
        [[ "$target" == memfd:* || "$target" == /memfd:* || "$target" == *"/memfd:"* ]] && memfds=$((memfds + 1))
        [[ "$target" == *"(deleted)"* ]] && deleted=$((deleted + 1))
        [[ "$target" == /tmp/* || "$target" == /var/tmp/* ]] && tmp_paths=$((tmp_paths + 1))
        if [[ -n "${XDG_RUNTIME_DIR:-}" && "$target" == "$XDG_RUNTIME_DIR"/* ]]; then
            runtime_paths=$((runtime_paths + 1))
        fi
        [[ "$target" == /home/jon/edmc-logs/* ]] && log_paths=$((log_paths + 1))
        [[ "$target" == *EDMCModernOverlay/shell-raster* || "$target" == *EDMCModernOverlay-shell-raster* ]] && raster_paths=$((raster_paths + 1))

        if [[ "${#samples[@]}" -lt 12 ]]; then
            samples+=("$(basename "$fd_path") -> $target")
        fi
    done

    echo "total=$total sockets=$sockets pipes=$pipes eventfds=$eventfds timerfds=$timerfds inotify=$inotifyfds memfds=$memfds deleted=$deleted tmp_paths=$tmp_paths runtime_paths=$runtime_paths log_paths=$log_paths raster_paths=$raster_paths unreadable=$unreadable"
    if [[ "${#samples[@]}" -gt 0 ]]; then
        echo "sample_fds:"
        printf '  %s\n' "${samples[@]}"
    fi
}

print_fd_census() {
    section "Descriptor and socket census"
    if [[ "${#TARGET_PIDS[@]}" -eq 0 ]]; then
        echo "No target PIDs found"
        return 0
    fi
    for pid in "${TARGET_PIDS[@]}"; do
        summarize_fd_for_pid "$pid"
    done

    section "Socket command sample"
    if have ss; then
        ss -xap 2>&1 \
            | grep -Ei 'EDMarketConnector|overlay_client|EliteDangerous|EDLaunch|WatchDog64|steam|proton|gnome-shell|Xwayland|nvidia' \
            | head -n 200 || true
    else
        echo "ss unavailable"
    fi

    section "lsof short samples"
    if have lsof && [[ "${#TARGET_PIDS[@]}" -gt 0 ]]; then
        for pid in "${TARGET_PIDS[@]}"; do
            echo
            echo "--- lsof sample pid=$pid ---"
            lsof -nP -p "$pid" 2>&1 | sed -n '1,25p' || true
        done
    else
        echo "lsof unavailable or no target PIDs"
    fi
}

print_kernel_pressure() {
    section "Kernel and system pressure"
    print_file_if_readable /proc/pressure/cpu
    print_file_if_readable /proc/pressure/memory
    print_file_if_readable /proc/pressure/io
    print_file_if_readable /proc/meminfo
    run_optional "free" free -h
    run_optional "vmstat" vmstat 1 2
    run_optional "uptime" uptime
    run_optional "df" df -h /tmp "${XDG_RUNTIME_DIR:-/run/user/$UID}" /home/jon/edmc-logs
}

print_proc_snapshots() {
    section "Per-process /proc snapshots"
    if [[ "${#TARGET_PIDS[@]}" -eq 0 ]]; then
        echo "No target PIDs found"
        return 0
    fi
    for pid in "${TARGET_PIDS[@]}"; do
        local comm
        comm="$(cat "/proc/${pid}/comm" 2>/dev/null || echo "unknown")"
        echo
        echo "### pid=$pid comm=$comm"
        print_file_if_readable "/proc/${pid}/status"
        print_file_if_readable "/proc/${pid}/io"
        print_file_if_readable "/proc/${pid}/smaps_rollup"
        print_file_if_readable "/proc/${pid}/task/${pid}/children"
    done
}

print_raster_cache_summary() {
    section "Shell raster cache summary"
    local dirs=()
    if [[ -n "${XDG_RUNTIME_DIR:-}" ]]; then
        dirs+=("${XDG_RUNTIME_DIR}/EDMCModernOverlay/shell-raster")
    fi
    dirs+=("/tmp/EDMCModernOverlay-shell-raster-${USER:-jon}")

    local dir count bytes
    for dir in "${dirs[@]}"; do
        echo
        echo "--- $dir ---"
        if [[ ! -d "$dir" ]]; then
            echo "missing"
            continue
        fi
        count="$(find "$dir" -maxdepth 1 -type f 2>/dev/null | wc -l | tr -d ' ')"
        bytes="$(du -sb "$dir" 2>/dev/null | awk '{print $1}')"
        echo "file_count=${count:-unknown} bytes=${bytes:-unknown}"
        echo "recent files:"
        find "$dir" -maxdepth 1 -type f -printf '%TY-%Tm-%Td %TH:%TM:%TS %s %p\n' 2>/dev/null \
            | sort \
            | tail -n 20 || true
    done
}

print_helper_diagnostics() {
    section "GNOME helper diagnostics"
    echo "Helper health:"
    dbus_call org.edmc.ModernOverlay.Helper.GetHealth

    echo
    echo "Target state:"
    dbus_call org.edmc.ModernOverlay.Helper.GetTargetState '{}' | tee "$TARGET_STATE_FILE" || true

    local target_token request
    target_token="$(extract_target_token)"
    echo
    echo "TARGET_TOKEN=${target_token:-unknown}"
    if [[ -n "$target_token" ]]; then
        request="$(diagnostic_request)"
        if [[ -n "$request" ]]; then
            echo
            echo "Actor diagnostics:"
            dbus_call org.edmc.ModernOverlay.Helper.ApplyPresentation "$request"
        else
            echo "Actor diagnostics skipped: diagnostic request unavailable"
        fi
    else
        echo "Actor diagnostics skipped: no target token"
    fi
}

print_overlay_log_summary() {
    section "Overlay client log pressure"
    local log_path="/home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log"
    local sample_file="${TMP_DIR}/overlay_client_tail.log"
    if [[ ! -r "$log_path" ]]; then
        echo "overlay log unavailable: $log_path"
        return 0
    fi

    tail -n 1000 "$log_path" > "$sample_file" 2>/dev/null || true
    if have python3; then
        python3 - "$sample_file" <<'PY'
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone

path = sys.argv[1]
lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
timestamp_re = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?) UTC")
patterns = {
    "gnome_helper_presentation": "GNOME helper presentation",
    "presentation_applied": "presentation_applied",
    "presentation_degraded": "presentation_degraded",
    "target_poll_skipped_true": "target_poll_skipped=True",
    "presentation_skipped_true": "presentation_skipped=True",
    "raster_mentions": "raster",
    "region_mentions": "region",
    "png_mentions": ".png",
    "explicit_clear": "explicit_clear",
    "raster_clear": "raster_clear",
    "hidden": "hidden",
    "suspended": "suspended",
    "shutdown": "shutdown",
    "cleanup": "cleanup",
}

def parse_ts(line: str) -> datetime | None:
    match = timestamp_re.match(line)
    if not match:
        return None
    text = match.group(1)
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None

timestamps = [ts for line in lines if (ts := parse_ts(line)) is not None]
elapsed = None
if len(timestamps) >= 2:
    elapsed = max(0.0, (timestamps[-1] - timestamps[0]).total_seconds())

print(f"sample_lines={len(lines)}")
if timestamps:
    print(f"first_timestamp_utc={timestamps[0].isoformat()}")
    print(f"last_timestamp_utc={timestamps[-1].isoformat()}")
if elapsed is not None:
    print(f"sample_elapsed_seconds={elapsed:.3f}")
    if elapsed > 0:
        print(f"log_lines_per_second={len(lines) / elapsed:.3f}")

for name, needle in patterns.items():
    if name.endswith("_mentions") or name in {"hidden", "suspended", "shutdown", "cleanup"}:
        count = sum(1 for line in lines if needle.lower() in line.lower())
    else:
        count = sum(1 for line in lines if needle in line)
    print(f"{name}={count}")

attempt_values = []
for line in lines:
    for match in re.finditer(r"\battempts=(\d+)", line):
        attempt_values.append(int(match.group(1)))
if attempt_values:
    print(f"attempt_field_count={len(attempt_values)}")
    print(f"attempt_field_sum={sum(attempt_values)}")
    if elapsed and elapsed > 0:
        print(f"attempts_per_second={sum(attempt_values) / elapsed:.3f}")

region_counts = []
for line in lines:
    for match in re.finditer(r"\bregion_count=(\d+)", line):
        region_counts.append(int(match.group(1)))
if region_counts:
    print(f"region_count_samples={len(region_counts)}")
    print(f"region_count_max={max(region_counts)}")

byte_sizes = []
for line in lines:
    for match in re.finditer(r"\bbyte_size=(\d+)", line):
        byte_sizes.append(int(match.group(1)))
if byte_sizes:
    print(f"byte_size_samples={len(byte_sizes)}")
    print(f"byte_size_max={max(byte_sizes)}")
PY
    else
        echo "python3 unavailable; structured overlay log summary skipped"
        wc -l "$sample_file" || true
    fi

    echo
    echo "Recent overlay log tail:"
    tail -n 240 "$log_path" || true
}

print_edmc_debug_log_tail() {
    section "EDMarketConnector debug log tail"
    local log_path="/home/jon/edmc-logs/EDMarketConnector-debug.log"
    if [[ -r "$log_path" ]]; then
        tail -n 160 "$log_path" || true
    else
        echo "EDMC debug log unavailable: $log_path"
    fi
}

print_journal_markers() {
    section "Journal markers"
    local pattern='edmc-modern-overlay-helper|edmc_modern_overlay_gnome_helper|EDMCModernOverlay|overlay_client|gnome-shell|Mutter|clutter-frame-clock|NVIDIA|NVKMS|nvkms|nv_drm|Xwayland|Steam|steam|Proton|Firefox|firefox|xdg-desktop-portal|xdg-document-portal|portal|pressure|OOM|out of memory|PipeWire|pipewire|WirePlumber|wireplumber|PulseAudio|pulseaudio|ALSA|alsa|xrun|XRUN|underrun|audio'
    echo "JOURNAL_SINCE=$JOURNAL_SINCE"

    if have journalctl; then
        echo
        echo "User journal markers:"
        journalctl --user -b --since "$JOURNAL_SINCE" --no-pager 2>&1 \
            | grep -Ei "$pattern" \
            | tail -n 400 || true

        echo
        echo "System journal markers:"
        journalctl -b --since "$JOURNAL_SINCE" --no-pager 2>&1 \
            | grep -Ei "$pattern" \
            | tail -n 400 || true
    else
        echo "journalctl unavailable"
    fi
}

print_audio_summary() {
    section "Audio optional summary"
    print_file_if_readable /proc/asound/cards
    print_file_if_readable /proc/asound/pcm

    run_optional "pipewire services" systemctl --user --no-pager --full status pipewire pipewire-pulse wireplumber
    run_optional "pactl info" pactl info
    run_optional "pactl sinks" pactl list short sinks
    run_optional "pactl sink inputs" pactl list short sink-inputs
    run_optional "wpctl status" wpctl status
    run_optional "pw-cli info" pw-cli info 0
}

print_gpu_summary() {
    section "GPU/compositor optional summary"
    if have nvidia-smi; then
        nvidia-smi || true
        echo
        echo "nvidia-smi process monitor sample:"
        nvidia-smi pmon -c 1 2>&1 || true
    else
        echo "nvidia-smi unavailable"
    fi
}

{
    echo "--- RUNTIME PRESSURE CAPTURE ---"
    echo "CAPTURE_START=$CAPTURE_START"
    echo "CAPTURE_LOG=$CAPTURE_LOG"
    echo "CAPTURE_LABEL=$LABEL_RAW"
    echo "CAPTURE_LABEL_SAFE=$LABEL_SAFE"
    echo "CAPTURE_LATEST=$CAPTURE_LATEST"
    echo "JOURNAL_SINCE=$JOURNAL_SINCE"
    date --iso-8601=seconds

    section "Environment"
    echo "USER=${USER:-unknown}"
    echo "UID=${UID:-unknown}"
    echo "PWD=$PWD"
    echo "SHELL=${SHELL:-unknown}"
    echo "XDG_SESSION_TYPE=${XDG_SESSION_TYPE:-unknown}"
    echo "XDG_CURRENT_DESKTOP=${XDG_CURRENT_DESKTOP:-unknown}"
    echo "XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-}"
    echo "DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-}"

    print_process_census
    print_kernel_pressure
    print_raster_cache_summary
    print_helper_diagnostics
    print_overlay_log_summary
    print_edmc_debug_log_tail
    print_fd_census
    print_proc_snapshots
    print_journal_markers
    print_audio_summary
    print_gpu_summary

    echo
    echo "--- CAPTURE END ---"
    date --iso-8601=seconds
} >> "$CAPTURE_LOG" 2>&1

echo "capture: complete"
