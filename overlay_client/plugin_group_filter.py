from __future__ import annotations

import logging
from typing import Any, Dict, Mapping, Optional

from overlay_plugin.plugin_group_resolver import PluginGroupResolver


class PluginGroupVisibilityFilter:
    """Client-side defensive payload filter keyed by plugin-group state."""

    def __init__(self, resolver: PluginGroupResolver, logger: Optional[logging.Logger] = None) -> None:
        self._resolver = resolver
        self._logger = logger or logging.getLogger("EDMC.ModernOverlay.Client")
        self._group_states: Dict[str, bool] = {}
        self._default_on = True

    def update_from_config(self, payload: Mapping[str, Any]) -> None:
        raw_default = payload.get("plugin_group_state_default_on")
        if isinstance(raw_default, bool):
            self._default_on = raw_default
        states = payload.get("plugin_group_states")
        if not isinstance(states, Mapping):
            return
        updated: Dict[str, bool] = {}
        for group_name, value in states.items():
            if not isinstance(group_name, str):
                continue
            if isinstance(value, bool):
                updated[group_name] = value
        self._group_states = updated

    def allow_payload(self, payload: Mapping[str, Any]) -> bool:
        event = payload.get("event")
        if event != "LegacyOverlay":
            return True
        group_name = self._resolver.resolve_group_name(payload)
        if not group_name:
            return True
        enabled = self._group_states.get(group_name, self._default_on)
        if not enabled:
            self._logger.debug("Client fallback drop for disabled plugin group: %s", group_name)
        return bool(enabled)

    def resolve_group_name(self, payload: Mapping[str, Any]) -> Optional[str]:
        return self._resolver.resolve_group_name(payload)
