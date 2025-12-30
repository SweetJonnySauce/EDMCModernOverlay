#!/usr/bin/env bash
set -u
shopt -s nullglob

usage() {
  cat <<'EOF'
Monitor EDMC trace_ids and verify they reach the overlay client.

Usage:
  trace_watch.sh [-h]

Behavior:
  - Tails EDMarketConnector-debug.log for new trace_id entries.
  - Waits briefly, then checks overlay_client.log (and rotated logs) for that trace_id.
  - Prints OK/MISSING with duration_ms and message text when available.

Environment overrides:
  EDMC_LOG_DIR, EDMC_LOG, OVERLAY_CLIENT_LOG, TRACE_WAIT_SECONDS,
  TRACE_COMPLETE_WAIT_SECONDS, TRACE_COMPLETE_RETRIES
EOF
}

status=0
while getopts ":h" opt; do
  case "$opt" in
    h)
      status=1
      ;;
    *)
      status=2
      ;;
  esac
done
shift $((OPTIND - 1))
if [ "$status" -ne 0 ]; then
  usage
  if [ "$status" -eq 1 ]; then
    if [ "${BASH_SOURCE[0]}" != "$0" ]; then
      return 0
    fi
    exit 0
  fi
  if [ "${BASH_SOURCE[0]}" != "$0" ]; then
    return 2
  fi
  exit 2
fi

log_dir=${EDMC_LOG_DIR:-"$HOME/.local/share/EDMarketConnector/logs"}
edmc_log=${EDMC_LOG:-"$log_dir/EDMarketConnector-debug.log"}
client_log=${OVERLAY_CLIENT_LOG:-"$log_dir/EDMCModernOverlay/overlay_client.log"}
wait_seconds=${TRACE_WAIT_SECONDS:-1}
complete_wait_seconds=${TRACE_COMPLETE_WAIT_SECONDS:-1}
complete_retries=${TRACE_COMPLETE_RETRIES:-2}

if [ ! -f "$edmc_log" ]; then
  echo "Missing log: $edmc_log" >&2
  exit 1
fi

declare -A seen_ids

extract_timestamp() {
  printf '%s\n' "$1" | sed -n 's/^\([0-9-]\{10\} [0-9:]\{8\}\.[0-9]\{3\}\).*/\1/p'
}

to_epoch_ms() {
  python3 - "$1" <<'PY'
import sys
from datetime import datetime, timezone

value = sys.argv[1].strip()
try:
    parsed = datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)
except ValueError:
    print("")
    raise SystemExit(0)
print(int(parsed.timestamp() * 1000))
PY
}

extract_text_from_line() {
  printf '%s\n' "$1" | awk '
    /"type"[[:space:]]*:[[:space:]]*"message"/ {
      if (match($0, /"text"[[:space:]]*:[[:space:]]*"[^"]*"/)) {
        s = substr($0, RSTART, RLENGTH)
        sub(/.*"text"[[:space:]]*:[[:space:]]*"/, "", s)
        sub(/"$/, "", s)
        print s
      }
    }'
}

extract_text_hint() {
  local trace_id="$1"
  local line="$2"
  local hint=""
  hint=$(extract_text_from_line "$line")
  if [ -n "$hint" ]; then
    printf '%s\n' "$hint"
    return
  fi
  if [ -f "$edmc_log" ]; then
    line=$(tail -n 2000 "$edmc_log" | grep -F "Trace starting" | grep -F "trace_id=$trace_id" | tail -n 1)
    if [ -n "$line" ]; then
      hint=$(extract_text_from_line "$line")
      if [ -n "$hint" ]; then
        printf '%s\n' "$hint"
      fi
    fi
  fi
}

find_trace_complete_line() {
  local trace_id="$1"
  local attempt=0
  local line=""
  local -a logs

  while [ "$attempt" -le "$complete_retries" ]; do
    logs=()
    if [ -f "$client_log" ]; then
      logs+=("$client_log")
    fi
    logs+=("$client_log".*)
    if [ "${#logs[@]}" -gt 0 ]; then
      line=$(grep -hF "trace_id=$trace_id" "${logs[@]}" 2>/dev/null | grep -F "stage=trace:complete" | tail -n 1)
      if [ -n "$line" ]; then
        printf '%s\n' "$line"
        return 0
      fi
    fi
    if [ "$attempt" -lt "$complete_retries" ]; then
      sleep "$complete_wait_seconds"
    fi
    attempt=$((attempt + 1))
  done
}

while IFS= read -r line; do
  case "$line" in
    *trace_id=*) ;;
    *) continue ;;
  esac
  trace_id=$(printf '%s\n' "$line" | sed -n 's/.*trace_id=\([a-f0-9-]\{36\}\).*/\1/p')
  if [ -z "$trace_id" ]; then
    continue
  fi
  if [ -n "${seen_ids[$trace_id]+set}" ]; then
    continue
  fi
  seen_ids[$trace_id]=1
  sleep "$wait_seconds"
  text_hint=$(extract_text_hint "$trace_id" "$line")
  if [ -n "$text_hint" ]; then
    text_hint=" text=\"${text_hint}\""
  fi
  duration_hint=""
  start_ts=$(extract_timestamp "$line")
  start_ms=""
  if [ -n "$start_ts" ]; then
    start_ms=$(to_epoch_ms "$start_ts")
  fi
  complete_line=$(find_trace_complete_line "$trace_id")
  if [ -n "$complete_line" ] && [ -n "$start_ms" ]; then
    complete_ts=$(extract_timestamp "$complete_line")
    if [ -n "$complete_ts" ]; then
      complete_ms=$(to_epoch_ms "$complete_ts")
      if [ -n "$complete_ms" ] && [ "$complete_ms" -ge "$start_ms" ]; then
        duration_ms=$((complete_ms - start_ms))
        duration_hint=" duration_ms=$duration_ms"
      fi
    fi
  fi
  client_logs=()
  if [ -f "$client_log" ]; then
    client_logs+=("$client_log")
  fi
  client_logs+=("$client_log".*)
  if [ "${#client_logs[@]}" -gt 0 ] && grep -Fq -- "$trace_id" "${client_logs[@]}"; then
    echo "OK trace_id=$trace_id${duration_hint}${text_hint}"
  else
    echo "MISSING trace_id=$trace_id${duration_hint}${text_hint}"
  fi
done < <(tail -F "$edmc_log")
