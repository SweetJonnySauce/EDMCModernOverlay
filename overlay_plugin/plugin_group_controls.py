from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Mapping, Optional, Sequence

from .plugin_group_state import PluginGroupStateManager

_LOGGER = logging.getLogger("EDMC.ModernOverlay.PluginGroupControls")


def dedupe_group_names(group_names: Sequence[object]) -> list[str]:
    """Return first-seen, case-insensitive group tokens."""

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


def resolve_payload_group_targets(payload: Any) -> Optional[list[str]]:
    """Extract optional plugin-group target list from hotkey/CLI payload."""

    if not isinstance(payload, Mapping):
        return None

    raw_targets: list[object] = []
    single = payload.get("plugin_group")
    if isinstance(single, str) and single.strip():
        raw_targets.append(single.strip())

    multi = payload.get("plugin_groups")
    if isinstance(multi, Sequence) and not isinstance(multi, (str, bytes)):
        for item in multi:
            if isinstance(item, str) and item.strip():
                raw_targets.append(item.strip())

    if not raw_targets:
        return None
    return dedupe_group_names(raw_targets)


class PluginGroupControlService:
    """Shared on/off/toggle orchestration for chat, hotkeys, and UI paths."""

    def __init__(
        self,
        *,
        state_manager: PluginGroupStateManager,
        publish_config: Callable[[], None],
        publish_group_clear: Optional[Callable[[Sequence[str], str], None]] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._state = state_manager
        self._publish_config = publish_config
        self._publish_group_clear = publish_group_clear
        self._logger = logger or _LOGGER

    def set_enabled(
        self,
        enabled: bool,
        *,
        group_names: Optional[Sequence[str]] = None,
        source: str = "unknown",
    ) -> Dict[str, Any]:
        updated, unknown = self._state.set_groups_enabled(bool(enabled), group_names)
        self._warn_unknown_groups(unknown, source=source)
        clear_targets: list[str] = []
        if updated:
            self._publish_config()
        if not enabled:
            clear_targets = self._resolve_clear_targets(group_names)
            self._emit_group_clear(clear_targets, source=source)
        return {
            "updated": updated,
            "unknown": unknown,
            "cleared": clear_targets,
            "changed": bool(updated),
            "action": "on" if enabled else "off",
        }

    def toggle(
        self,
        *,
        group_names: Optional[Sequence[str]] = None,
        source: str = "unknown",
    ) -> Dict[str, Any]:
        updated, unknown = self._state.toggle_groups(group_names)
        self._warn_unknown_groups(unknown, source=source)
        clear_targets: list[str] = []
        if updated:
            self._publish_config()
            clear_targets = [
                group_name for group_name in updated if not self._state.is_group_enabled(group_name)
            ]
            self._emit_group_clear(clear_targets, source=source)
        return {
            "updated": updated,
            "unknown": unknown,
            "cleared": clear_targets,
            "changed": bool(updated),
            "action": "toggle",
        }

    def status_lines(self) -> list[str]:
        return self._state.status_lines()

    def state_snapshot(self) -> Dict[str, bool]:
        return self._state.state_snapshot()

    def _warn_unknown_groups(self, unknown: Sequence[str], *, source: str) -> None:
        for group_name in dedupe_group_names(unknown):
            self._logger.warning("Ignoring unknown plugin group '%s' (%s).", group_name, source)

    def _resolve_clear_targets(self, group_names: Optional[Sequence[str]]) -> list[str]:
        if group_names is None:
            return list(self._state.known_group_names())
        known = self._state.known_group_names()
        by_casefold = {name.casefold(): name for name in known}
        resolved: list[str] = []
        for target in dedupe_group_names(group_names):
            canonical = by_casefold.get(target.casefold())
            if canonical is not None:
                resolved.append(canonical)
        return resolved

    def _emit_group_clear(self, group_names: Sequence[str], *, source: str) -> None:
        callback = self._publish_group_clear
        if callback is None:
            return
        targets = dedupe_group_names(group_names)
        if not targets:
            return
        try:
            callback(targets, source)
        except Exception as exc:  # pragma: no cover - defensive guard
            self._logger.warning("Failed to publish plugin-group clear event: %s", exc, exc_info=exc)
