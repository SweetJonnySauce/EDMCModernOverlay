from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from prefix_entries import parse_prefix_entries

from overlay_plugin.groupings_loader import GroupingsLoader


_LOGGER = logging.getLogger("EDMC.ModernOverlay.PluginGroupResolver")


@dataclass(frozen=True)
class _GroupPrefixRule:
    plugin_name: str
    plugin_name_cf: str
    group_name: str
    prefix: str
    prefix_cf: str
    exact: bool

    def matches(self, payload_id_cf: str) -> bool:
        if self.exact:
            return payload_id_cf == self.prefix_cf
        return payload_id_cf.startswith(self.prefix_cf)


class PluginGroupResolver:
    """Resolve LegacyOverlay payloads to canonical plugin group names."""

    def __init__(
        self,
        shipped_path: Path,
        user_path: Optional[Path] = None,
        *,
        loader: Optional[GroupingsLoader] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._logger = logger or _LOGGER
        self._loader = loader or GroupingsLoader(shipped_path, user_path, logger=self._logger)
        self._group_rules: Tuple[_GroupPrefixRule, ...] = tuple()
        self._plugin_rules: Tuple[Tuple[str, str], ...] = tuple()
        self._known_groups: Tuple[str, ...] = tuple()
        self._group_owner_map: Dict[str, Optional[str]] = {}
        self.reload(force=True)

    def reload(self, *, force: bool = False) -> bool:
        """Reload resolver indexes; returns True when files changed or forced."""

        changed = False
        if force:
            merged = self._loader.load()
            changed = True
        else:
            changed = bool(self._loader.reload_if_changed())
            merged = self._loader.merged()
        self._rebuild(merged)
        return changed

    def known_group_names(self) -> Tuple[str, ...]:
        self.reload(force=False)
        return self._known_groups

    def group_owner_map(self) -> Dict[str, Optional[str]]:
        self.reload(force=False)
        return dict(self._group_owner_map)

    def resolve_group_name(self, payload: Mapping[str, Any]) -> Optional[str]:
        self.reload(force=False)
        payload_id = self._extract_payload_id(payload)
        if not payload_id:
            return None
        payload_id_cf = payload_id.casefold()
        plugin_name = self._extract_plugin_name(payload) or self._infer_plugin_from_id(payload_id_cf)
        plugin_cf = plugin_name.casefold() if plugin_name else ""

        plugin_candidates: list[Tuple[int, str]] = []
        fallback_candidates: list[Tuple[int, str]] = []
        for rule in self._group_rules:
            if not rule.matches(payload_id_cf):
                continue
            score = len(rule.prefix_cf)
            if plugin_cf and rule.plugin_name_cf == plugin_cf:
                plugin_candidates.append((score, rule.group_name))
            fallback_candidates.append((score, rule.group_name))

        if plugin_candidates:
            plugin_candidates.sort(key=lambda item: (-item[0], item[1].casefold()))
            return plugin_candidates[0][1]
        if fallback_candidates:
            fallback_candidates.sort(key=lambda item: (-item[0], item[1].casefold()))
            return fallback_candidates[0][1]
        return None

    @staticmethod
    def _extract_plugin_name(payload: Mapping[str, Any]) -> Optional[str]:
        def _from_mapping(mapping: Mapping[str, Any]) -> Optional[str]:
            for key in ("plugin", "plugin_name", "source_plugin"):
                value = mapping.get(key)
                if isinstance(value, str):
                    token = value.strip()
                    if token:
                        return token
            return None

        direct = _from_mapping(payload)
        if direct:
            return direct
        for key in ("meta", "raw", "legacy_raw"):
            nested = payload.get(key)
            if isinstance(nested, Mapping):
                candidate = _from_mapping(nested)
                if candidate:
                    return candidate
        return None

    @staticmethod
    def _extract_payload_id(payload: Mapping[str, Any]) -> Optional[str]:
        def _id_from_mapping(mapping: Mapping[str, Any]) -> Optional[str]:
            value = mapping.get("id")
            if isinstance(value, str):
                token = value.strip()
                if token:
                    return token
            return None

        direct = _id_from_mapping(payload)
        if direct:
            return direct
        for key in ("meta", "raw", "legacy_raw"):
            nested = payload.get(key)
            if isinstance(nested, Mapping):
                candidate = _id_from_mapping(nested)
                if candidate:
                    return candidate
        return None

    def _infer_plugin_from_id(self, payload_id_cf: str) -> Optional[str]:
        if not payload_id_cf:
            return None
        best: Optional[Tuple[int, str]] = None
        for plugin_name_cf, prefix_cf in self._plugin_rules:
            if payload_id_cf.startswith(prefix_cf):
                score = len(prefix_cf)
                if best is None or score > best[0]:
                    best = (score, plugin_name_cf)
        if best is None:
            return None
        return best[1]

    def _rebuild(self, merged: Mapping[str, Any]) -> None:
        rules: list[_GroupPrefixRule] = []
        plugin_rules: list[Tuple[str, str]] = []
        known_groups: set[str] = set()
        owner_sets: Dict[str, set[str]] = {}
        for plugin_name, plugin_entry in merged.items():
            if not isinstance(plugin_name, str):
                continue
            if plugin_name.startswith("_"):
                continue
            if not isinstance(plugin_entry, Mapping):
                continue
            plugin_name_cf = plugin_name.casefold()

            matching_prefixes = plugin_entry.get("matchingPrefixes")
            if isinstance(matching_prefixes, Sequence) and not isinstance(matching_prefixes, (str, bytes)):
                for value in matching_prefixes:
                    if not isinstance(value, str):
                        continue
                    token = value.strip().casefold()
                    if token:
                        plugin_rules.append((plugin_name_cf, token))

            groups = plugin_entry.get("idPrefixGroups")
            if not isinstance(groups, Mapping):
                continue
            for group_name, group_entry in groups.items():
                if not isinstance(group_name, str):
                    continue
                known_groups.add(group_name)
                owner_sets.setdefault(group_name, set()).add(plugin_name)
                if not isinstance(group_entry, Mapping):
                    continue
                id_prefixes = parse_prefix_entries(group_entry.get("idPrefixes"))
                for id_prefix in id_prefixes:
                    prefix_cf = id_prefix.value_cf
                    if not prefix_cf:
                        continue
                    rules.append(
                        _GroupPrefixRule(
                            plugin_name=plugin_name,
                            plugin_name_cf=plugin_name_cf,
                            group_name=group_name,
                            prefix=id_prefix.value,
                            prefix_cf=prefix_cf,
                            exact=(id_prefix.match_mode == "exact"),
                        )
                    )

        self._group_rules = tuple(rules)
        self._plugin_rules = tuple(plugin_rules)
        self._known_groups = tuple(sorted(known_groups, key=str.casefold))
        owner_map: Dict[str, Optional[str]] = {}
        for group_name, owners in owner_sets.items():
            canonical = sorted(owners, key=str.casefold)
            owner_map[group_name] = canonical[0] if len(canonical) == 1 else None
        self._group_owner_map = owner_map
