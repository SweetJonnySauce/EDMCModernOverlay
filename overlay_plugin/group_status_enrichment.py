"""Compose enriched `!ovr status` lines."""
from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence


def normalise_plugin_status_label(raw_status: Optional[str]) -> str:
    token = str(raw_status or "").strip().lower()
    if token == "enabled":
        return "Enabled"
    if token == "disabled":
        return "Not Enabled"
    if token == "ignored":
        return "Ignored"
    if token == "unknown":
        return "Unknown"
    return "Unknown"


def _casefold_lookup(mapping: Mapping[str, Any], key: str) -> Any:
    direct = mapping.get(key)
    if direct is not None:
        return direct
    key_cf = key.casefold()
    for candidate, value in mapping.items():
        if str(candidate).casefold() == key_cf:
            return value
    return None


def _group_seen(metadata_snapshot: Mapping[str, Mapping[str, Any]], group_name: str) -> bool:
    entry = _casefold_lookup(metadata_snapshot, group_name)
    if not isinstance(entry, Mapping):
        return False
    seen_at = entry.get("last_payload_seen_at")
    return isinstance(seen_at, str) and bool(seen_at.strip())


def build_enriched_group_status_lines(
    *,
    group_names: Sequence[str],
    group_owner_map: Mapping[str, Optional[str]],
    plugin_status_map: Mapping[str, str],
    group_state_map: Mapping[str, bool],
    metadata_snapshot: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    plugin_status_cf = {str(name).casefold(): str(status).lower() for name, status in plugin_status_map.items()}
    lines: list[str] = []
    for group_name in sorted({str(name) for name in group_names if str(name or "").strip()}, key=str.casefold):
        owner = _casefold_lookup(group_owner_map, group_name)
        if not isinstance(owner, str) or not owner.strip():
            plugin_status = "Unknown"
        else:
            plugin_status = normalise_plugin_status_label(plugin_status_cf.get(owner.casefold()))

        seen = "Seen" if _group_seen(metadata_snapshot, group_name) else "Not Seen"
        group_enabled = _casefold_lookup(group_state_map, group_name)
        on_off = "On" if bool(True if group_enabled is None else group_enabled) else "Off"
        lines.append(f"{group_name}: {plugin_status}, {seen}, {on_off}")
    return lines
