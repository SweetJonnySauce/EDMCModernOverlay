#!/usr/bin/env bash
set -u

log_dir=${EDMC_LOG_DIR:-"$HOME/.local/share/EDMarketConnector/logs"}
edmc_log=${EDMC_LOG:-"$log_dir/EDMarketConnector-debug.log"}
client_log=${OVERLAY_CLIENT_LOG:-"$log_dir/EDMCModernOverlay/overlay_client.log"}

trace_id=${1:-}
if [ -z "$trace_id" ]; then
  if [ -f "$edmc_log" ]; then
    trace_id=$(
      awk -F'trace_id=' '/trace_id=/{id=$2} END{if(id){split(id,a,/[^A-Za-z0-9-]/); print a[1]}}' "$edmc_log"
    )
  fi
  if [ -z "$trace_id" ]; then
    echo "Usage: $0 <trace_id>" >&2
    exit 1
  fi
  echo "Using last trace_id from $edmc_log: $trace_id"
fi

grep_log() {
  local label=$1
  local file=$2
  if [ -f "$file" ]; then
    echo "==> $label ($file)"
    cat "$file" | grep -F -- "$trace_id" || true
  else
    echo "Missing log: $file" >&2
  fi
}

grep_log "EDMC" "$edmc_log"
grep_log "overlay_client" "$client_log"
