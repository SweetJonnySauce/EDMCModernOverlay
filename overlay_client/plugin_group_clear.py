from __future__ import annotations

from typing import Any, Callable, Mapping, Optional, Sequence

from overlay_client.legacy_store import LegacyItemStore


def dedupe_group_names(group_names: Sequence[object]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for raw in group_names:
        token = str(raw or "").strip()
        if not token:
            continue
        key = token.casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(token)
    return deduped


def parse_clear_targets(payload: Mapping[str, Any]) -> list[str]:
    raw_targets: list[object] = []
    single = payload.get("plugin_group")
    if isinstance(single, str) and single.strip():
        raw_targets.append(single.strip())
    multi = payload.get("plugin_groups")
    if isinstance(multi, Sequence) and not isinstance(multi, (str, bytes)):
        for entry in multi:
            if isinstance(entry, str) and entry.strip():
                raw_targets.append(entry.strip())
    return dedupe_group_names(raw_targets)


def clear_store_for_groups(
    *,
    store: LegacyItemStore,
    target_groups: Sequence[str],
    resolve_group_name: Optional[Callable[[Mapping[str, Any]], Optional[str]]],
) -> int:
    if resolve_group_name is None:
        return 0
    targets = {name.casefold() for name in dedupe_group_names(target_groups)}
    if not targets:
        return 0

    removed = 0
    for item_id, legacy_item in list(store.items()):
        probe_payload: dict[str, object] = {"event": "LegacyOverlay", "id": item_id}
        plugin_name = str(getattr(legacy_item, "plugin", "") or "").strip()
        if plugin_name:
            probe_payload["plugin"] = plugin_name
        group_name = resolve_group_name(probe_payload)
        if not group_name:
            continue
        if group_name.casefold() not in targets:
            continue
        store.remove(item_id)
        removed += 1
    return removed
