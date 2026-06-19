#!/usr/bin/env bash

set -u

CAPTURE_START="$(date --iso-8601=seconds)"
CAPTURE_LOG="/home/jon/edmc-logs/EDMCModernOverlay/focused_overlay_retest_$(date '+%Y%m%d_%H%M%S').log"
CAPTURE_LATEST="/home/jon/edmc-logs/EDMCModernOverlay/focused_overlay_retest.latest"
TARGET_STATE_FILE="$(mktemp)"

cleanup() {
    status=$?
    rm -f "$TARGET_STATE_FILE"
    if [[ "$status" -ne 0 ]]; then
        echo "capture: failed status=$status"
        echo "CAPTURE_LOG=$CAPTURE_LOG"
    fi
    exit "$status"
}
trap cleanup EXIT

mkdir -p "$(dirname "$CAPTURE_LOG")"
printf '%s\n' "$CAPTURE_LOG" > "$CAPTURE_LATEST"

echo "CAPTURE_LOG=$CAPTURE_LOG"
echo "capture: started"

dbus_call() {
    gdbus call --session \
        --dest org.edmc.ModernOverlay.Helper \
        --object-path /org/edmc/ModernOverlay/Helper \
        --method "$@"
}

extract_target_token() {
    python3 - "$TARGET_STATE_FILE" <<'PY'
import ast
import json
import sys

text = open(sys.argv[1], encoding="utf-8").read().strip()
try:
    payload = ast.literal_eval(text)[0]
    print(json.loads(payload).get("target", {}).get("targetToken", ""))
except Exception:
    print("")
PY
}

diagnostic_request() {
    python3 - "$1" <<'PY'
import json
import sys

print(json.dumps({
    "action": "attach",
    "target_token": sys.argv[1],
    "content_rect": {"x": 0, "y": 0, "width": 3440, "height": 1440},
    "rect_tolerance": 2,
    "shell_actor_proof": True,
    "shell_actor_proof_action": "diagnose_groups",
}))
PY
}

{
    echo "--- FOCUSED OVERLAY RETEST CAPTURE ---"
    echo "CAPTURE_START=$CAPTURE_START"
    echo "CAPTURE_LOG=$CAPTURE_LOG"
    date --iso-8601=seconds

    echo
    echo "EDMC / overlay_client / Elite processes:"
    pgrep -af '[E]DMarketConnector.py|[o]verlay_client|[E]liteDangerous|[E]DLaunch|[W]atchDog64' || true

    echo
    echo "Helper health:"
    dbus_call org.edmc.ModernOverlay.Helper.GetHealth || true

    echo
    echo "Target state:"
    dbus_call org.edmc.ModernOverlay.Helper.GetTargetState '{}' | tee "$TARGET_STATE_FILE" || true

    TARGET_TOKEN="$(extract_target_token)"
    echo
    echo "TARGET_TOKEN=${TARGET_TOKEN:-unknown}"

    if [[ -n "$TARGET_TOKEN" ]]; then
        echo
        echo "Actor diagnostics:"
        REQUEST="$(diagnostic_request "$TARGET_TOKEN")"
        dbus_call org.edmc.ModernOverlay.Helper.ApplyPresentation "$REQUEST" || true
    fi

    echo
    echo "Overlay client log tail:"
    tail -n 240 /home/jon/edmc-logs/EDMCModernOverlay/overlay_client.log || true

    echo
    echo "User journal since capture start:"
    journalctl --user -b --since "$CAPTURE_START" --no-pager \
        | grep -E 'edmc-modern-overlay-helper|EDMCModernOverlay|overlay_client|gnome-shell|Mutter|frame|NVIDIA|nvkms|nv_drm' || true

    echo
    echo "System journal since capture start:"
    journalctl -b --since "$CAPTURE_START" --no-pager \
        | grep -E 'edmc-modern-overlay-helper|EDMCModernOverlay|overlay_client|gnome-shell|Mutter|frame|NVIDIA|nvkms|nv_drm' || true

    echo
    echo "--- CAPTURE END ---"
    date --iso-8601=seconds
} >> "$CAPTURE_LOG" 2>&1

echo "capture: complete"
