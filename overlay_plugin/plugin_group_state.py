from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

from overlay_plugin.plugin_group_resolver import PluginGroupResolver

_LOGGER = logging.getLogger("EDMC.ModernOverlay.PluginGroupState")

_STATE_ROOT_KEY = "_plugin_group_state"
_STATE_ENABLED_KEY = "enabled"
_STATE_ENABLED_BY_PROFILE_KEY = "enabled_by_profile"
_STATE_METADATA_KEY = "metadata"
_PROFILE_STATE_KEY = "_overlay_profile_state"
_DEFAULT_PROFILE_NAME = "Default"


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalise_profile_name(value: Any) -> Optional[str]:
    token = str(value or "").strip()
    if not token:
        return None
    if token.casefold() == _DEFAULT_PROFILE_NAME.casefold():
        return _DEFAULT_PROFILE_NAME
    return token


def _normalise_profiles(raw_profiles: Any, fallback_current: str) -> list[str]:
    profiles: list[str] = []
    seen: set[str] = set()

    def _append(raw: Any) -> None:
        token = _normalise_profile_name(raw)
        if token is None:
            return
        key = token.casefold()
        if key in seen:
            return
        seen.add(key)
        profiles.append(token)

    if isinstance(raw_profiles, list):
        for item in raw_profiles:
            _append(item)
    _append(fallback_current)
    _append(_DEFAULT_PROFILE_NAME)

    ordered: list[str] = [
        name
        for name in profiles
        if name.casefold() != _DEFAULT_PROFILE_NAME.casefold()
    ]
    ordered.append(_DEFAULT_PROFILE_NAME)
    return ordered


class PluginGroupStateManager:
    """Runtime manager for per-group enabled state and hybrid metadata."""

    def __init__(
        self,
        shipped_path: Path,
        user_path: Path,
        *,
        resolver: Optional[PluginGroupResolver] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._logger = logger or _LOGGER
        self._user_path = user_path
        self._resolver = resolver or PluginGroupResolver(shipped_path=shipped_path, user_path=user_path, logger=self._logger)
        self._enabled_overrides: Dict[str, bool] = {}
        self._enabled_by_profile: Dict[str, Dict[str, bool]] = {}
        self._current_profile: str = _DEFAULT_PROFILE_NAME
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._counter_drop = 0
        self._counter_metadata = 0
        self._counter_parity_match = 0
        self._counter_parity_mismatch = 0
        self._load_user_state()

    def reload_if_changed(self) -> bool:
        return self._resolver.reload(force=False)

    def known_group_names(self) -> Tuple[str, ...]:
        return self._resolver.known_group_names()

    def group_owner_map(self) -> Dict[str, Optional[str]]:
        return self._resolver.group_owner_map()

    def resolve_payload_group_name(self, payload: Mapping[str, Any]) -> Optional[str]:
        return self._resolver.resolve_group_name(payload)

    def is_group_enabled(self, group_name: str) -> bool:
        canonical = self._canonical_group_name(group_name)
        if canonical is None:
            return True
        value = self._enabled_overrides.get(canonical)
        if value is None:
            return True
        return bool(value)

    def state_snapshot(self) -> Dict[str, bool]:
        snapshot: Dict[str, bool] = {}
        for group_name in self.known_group_names():
            snapshot[group_name] = self.is_group_enabled(group_name)
        return snapshot

    def status_lines(self) -> list[str]:
        lines: list[str] = []
        for group_name in sorted(self.known_group_names(), key=str.casefold):
            enabled = self.is_group_enabled(group_name)
            lines.append(f"{group_name}: {'On' if enabled else 'Off'}")
        return lines

    def overlay_config_fragment(self) -> Dict[str, Any]:
        return {
            "plugin_group_states": self.state_snapshot(),
            "plugin_group_state_default_on": True,
        }

    def should_drop_payload(self, payload: Mapping[str, Any]) -> Tuple[bool, Optional[str]]:
        event = payload.get("event")
        if not isinstance(event, str) or event != "LegacyOverlay":
            return False, None
        self.reload_if_changed()
        group_name = self.resolve_payload_group_name(payload)
        if not group_name:
            return False, None

        enabled = self.is_group_enabled(group_name)
        self._touch_metadata(group_name, payload, count_disabled_update=not enabled)
        if enabled:
            self._counter_parity_match += 1
            return False, group_name
        self._counter_drop += 1
        self._counter_parity_match += 1
        return True, group_name

    def set_groups_enabled(self, enabled: bool, group_names: Optional[Sequence[str]] = None) -> Tuple[list[str], list[str]]:
        self.reload_if_changed()
        unknown: list[str] = []
        updated: list[str] = []
        targets = self._resolve_targets(group_names)

        updates: Dict[str, bool] = {}
        for target in targets:
            canonical = self._canonical_group_name(target)
            if canonical is None:
                unknown.append(str(target))
                continue
            previous = self._resolved_group_enabled(self._enabled_overrides, canonical)
            if previous == bool(enabled):
                continue
            updates[canonical] = bool(enabled)
            updated.append(canonical)

        if updated:
            self._apply_enabled_updates(updates)
            self._persist_state()
        return updated, unknown

    def toggle_groups(self, group_names: Optional[Sequence[str]] = None) -> Tuple[list[str], list[str]]:
        self.reload_if_changed()
        unknown: list[str] = []
        updated: list[str] = []
        targets = self._resolve_targets(group_names)

        updates: Dict[str, bool] = {}
        for target in targets:
            canonical = self._canonical_group_name(target)
            if canonical is None:
                unknown.append(str(target))
                continue
            next_state = not self._resolved_group_enabled(self._enabled_overrides, canonical)
            updates[canonical] = next_state
            updated.append(canonical)

        if updated:
            self._apply_enabled_updates(updates)
            self._persist_state()
        return updated, unknown

    def reset_groups_to_default(self, group_names: Optional[Sequence[str]] = None) -> Tuple[list[str], list[str]]:
        """Reset active-profile group visibility back to the Default profile values."""
        self.reload_if_changed()
        unknown: list[str] = []
        updated: list[str] = []
        targets = self._resolve_targets(group_names)

        active_profile = self._resolve_profile_name(self._current_profile) or _DEFAULT_PROFILE_NAME
        active_map = dict(self._enabled_by_profile.get(active_profile, {}))
        default_map = dict(self._enabled_by_profile.get(_DEFAULT_PROFILE_NAME, {}))

        updates: Dict[str, bool] = {}
        for target in targets:
            canonical = self._canonical_group_name(target)
            if canonical is None:
                unknown.append(str(target))
                continue
            current_enabled = self._resolved_group_enabled(active_map, canonical)
            default_enabled = self._resolved_group_enabled(default_map, canonical)
            if current_enabled == default_enabled:
                continue
            updates[canonical] = bool(default_enabled)
            updated.append(canonical)

        if updated:
            self._apply_enabled_updates(updates)
            self._persist_state()
        return updated, unknown

    def counters(self) -> Dict[str, int]:
        return {
            "disabled_payload_drop_count": int(self._counter_drop),
            "disabled_payload_hybrid_metadata_update_count": int(self._counter_metadata),
            "resolver_parity_match_count": int(self._counter_parity_match),
            "resolver_parity_mismatch_count": int(self._counter_parity_mismatch),
        }

    def metadata_snapshot(self) -> Dict[str, Dict[str, Any]]:
        return {key: dict(value) for key, value in self._metadata.items()}

    def sync_profiles(self, *, profiles: Sequence[str], current_profile: str) -> None:
        normalised_profiles = _normalise_profiles(list(profiles), str(current_profile or _DEFAULT_PROFILE_NAME))
        current = _normalise_profile_name(current_profile) or _DEFAULT_PROFILE_NAME

        existing_by_cf = {name.casefold(): name for name in self._enabled_by_profile.keys()}
        updated_by_profile: Dict[str, Dict[str, bool]] = {}
        default_snapshot = dict(self._enabled_by_profile.get(_DEFAULT_PROFILE_NAME, {}))
        for profile_name in normalised_profiles:
            resolved_existing = existing_by_cf.get(profile_name.casefold())
            if resolved_existing is not None:
                updated_by_profile[profile_name] = dict(self._enabled_by_profile.get(resolved_existing, {}))
                continue
            updated_by_profile[profile_name] = dict(default_snapshot)

        self._enabled_by_profile = updated_by_profile
        self._current_profile = self._resolve_profile_name(current) or _DEFAULT_PROFILE_NAME
        self._enabled_overrides = dict(self._enabled_by_profile.get(self._current_profile, {}))
        self._persist_state()

    def create_profile(self, profile_name: str) -> None:
        token = _normalise_profile_name(profile_name)
        if token is None:
            return
        resolved = self._resolve_profile_name(token)
        if resolved is not None:
            return
        default_snapshot = dict(self._enabled_by_profile.get(_DEFAULT_PROFILE_NAME, {}))
        self._enabled_by_profile[token] = default_snapshot
        self._persist_state()

    def clone_profile(self, source_profile: str, new_profile: str) -> None:
        source_token = _normalise_profile_name(source_profile)
        target_token = _normalise_profile_name(new_profile)
        if source_token is None or target_token is None:
            return
        source_resolved = self._resolve_profile_name(source_token)
        if source_resolved is None:
            source_resolved = _DEFAULT_PROFILE_NAME
        source_snapshot = dict(self._enabled_by_profile.get(source_resolved, {}))
        target_resolved = self._resolve_profile_name(target_token)
        if target_resolved is not None:
            self._enabled_by_profile[target_resolved] = source_snapshot
        else:
            self._enabled_by_profile[target_token] = source_snapshot
        self._persist_state()

    def rename_profile(self, old_name: str, new_name: str) -> None:
        old_token = _normalise_profile_name(old_name)
        new_token = _normalise_profile_name(new_name)
        if old_token is None or new_token is None:
            return
        old_resolved = self._resolve_profile_name(old_token)
        if old_resolved is None:
            return
        old_map = dict(self._enabled_by_profile.get(old_resolved, {}))
        existing_new = self._resolve_profile_name(new_token)
        if existing_new is not None and existing_new.casefold() != old_resolved.casefold():
            return

        updated: Dict[str, Dict[str, bool]] = {}
        inserted = False
        for profile_name, profile_map in self._enabled_by_profile.items():
            if str(profile_name).casefold() == old_resolved.casefold():
                if not inserted:
                    updated[new_token] = old_map
                    inserted = True
                continue
            updated[str(profile_name)] = dict(profile_map)
        if not inserted:
            updated[new_token] = old_map

        self._enabled_by_profile = updated
        if str(self._current_profile).casefold() == old_resolved.casefold():
            self._current_profile = new_token
            self._enabled_overrides = dict(old_map)
        self._persist_state()

    def delete_profile(self, profile_name: str) -> None:
        token = _normalise_profile_name(profile_name)
        if token is None or token.casefold() == _DEFAULT_PROFILE_NAME.casefold():
            return
        resolved = self._resolve_profile_name(token)
        if resolved is None:
            return
        self._enabled_by_profile.pop(resolved, None)
        if str(self._current_profile).casefold() == resolved.casefold():
            self._current_profile = _DEFAULT_PROFILE_NAME
            self._enabled_overrides = dict(self._enabled_by_profile.get(_DEFAULT_PROFILE_NAME, {}))
        self._persist_state()

    def set_current_profile(self, profile_name: str) -> None:
        token = _normalise_profile_name(profile_name)
        if token is None:
            return
        resolved = self._resolve_profile_name(token)
        if resolved is None:
            default_snapshot = dict(self._enabled_by_profile.get(_DEFAULT_PROFILE_NAME, {}))
            self._enabled_by_profile[token] = default_snapshot
            resolved = token
        self._current_profile = resolved
        self._enabled_overrides = dict(self._enabled_by_profile.get(resolved, {}))
        self._persist_state()

    def _load_user_state(self) -> None:
        payload = self._read_user_file()
        state_root = payload.get(_STATE_ROOT_KEY)
        state_root = state_root if isinstance(state_root, Mapping) else {}
        enabled = state_root.get(_STATE_ENABLED_KEY)
        legacy_enabled: Dict[str, bool] = {}
        if isinstance(enabled, Mapping):
            for group_name, value in enabled.items():
                if isinstance(group_name, str) and isinstance(value, bool):
                    legacy_enabled[group_name] = value

        profile_state = payload.get(_PROFILE_STATE_KEY)
        profile_state = profile_state if isinstance(profile_state, Mapping) else {}
        current_profile = _normalise_profile_name(profile_state.get("current_profile")) or _DEFAULT_PROFILE_NAME
        profiles = _normalise_profiles(profile_state.get("profiles"), current_profile)

        enabled_by_profile: Dict[str, Dict[str, bool]] = {}
        raw_enabled_by_profile = state_root.get(_STATE_ENABLED_BY_PROFILE_KEY)
        if isinstance(raw_enabled_by_profile, Mapping):
            for raw_profile, raw_group_map in raw_enabled_by_profile.items():
                profile_name = _normalise_profile_name(raw_profile)
                if profile_name is None or not isinstance(raw_group_map, Mapping):
                    continue
                entry: Dict[str, bool] = {}
                for group_name, value in raw_group_map.items():
                    if isinstance(group_name, str) and isinstance(value, bool):
                        entry[group_name] = value
                enabled_by_profile[profile_name] = entry

        if not enabled_by_profile:
            enabled_by_profile[current_profile] = dict(legacy_enabled)

        default_snapshot = dict(
            enabled_by_profile.get(_DEFAULT_PROFILE_NAME)
            or enabled_by_profile.get(current_profile)
            or legacy_enabled
        )
        enabled_by_profile.setdefault(_DEFAULT_PROFILE_NAME, dict(default_snapshot))
        for profile_name in profiles:
            enabled_by_profile.setdefault(profile_name, dict(default_snapshot))

        self._enabled_by_profile = enabled_by_profile
        self._current_profile = self._resolve_profile_name(current_profile) or _DEFAULT_PROFILE_NAME
        self._enabled_overrides = dict(self._enabled_by_profile.get(self._current_profile, {}))

        metadata = state_root.get(_STATE_METADATA_KEY)
        if isinstance(metadata, Mapping):
            for group_name, value in metadata.items():
                if not isinstance(group_name, str):
                    continue
                if not isinstance(value, Mapping):
                    continue
                self._metadata[group_name] = dict(value)

    def _persist_state(self) -> None:
        payload = self._read_user_file()
        state_root: Dict[str, Any] = {}
        existing = payload.get(_STATE_ROOT_KEY)
        if isinstance(existing, Mapping):
            state_root = dict(existing)

        current_map = dict(self._enabled_by_profile.get(self._current_profile, self._enabled_overrides))
        self._enabled_overrides = dict(current_map)
        self._enabled_by_profile[self._current_profile] = dict(current_map)
        state_root[_STATE_ENABLED_KEY] = dict(current_map)
        state_root[_STATE_ENABLED_BY_PROFILE_KEY] = {
            profile_name: dict(values)
            for profile_name, values in self._enabled_by_profile.items()
            if isinstance(profile_name, str) and isinstance(values, Mapping)
        }
        state_root[_STATE_METADATA_KEY] = dict(self._metadata)
        payload[_STATE_ROOT_KEY] = state_root

        try:
            self._user_path.parent.mkdir(parents=True, exist_ok=True)
            text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
            tmp_path = self._user_path.with_suffix(self._user_path.suffix + ".tmp")
            tmp_path.write_text(text, encoding="utf-8")
            tmp_path.replace(self._user_path)
        except OSError as exc:  # pragma: no cover - filesystem errors are environment-specific
            self._logger.warning("Failed to persist plugin-group state: %s", exc)

    def _read_user_file(self) -> Dict[str, Any]:
        try:
            raw = self._user_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return {}
        except OSError as exc:  # pragma: no cover
            self._logger.debug("Unable to read %s: %s", self._user_path, exc)
            return {}
        if not raw.strip():
            return {}
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            self._logger.debug("Ignoring invalid JSON in %s: %s", self._user_path, exc)
            return {}
        if not isinstance(payload, dict):
            return {}
        return payload

    def _canonical_group_name(self, group_name: str) -> Optional[str]:
        token = str(group_name or "").strip()
        if not token:
            return None
        known = self.known_group_names()
        by_casefold: Dict[str, str] = {name.casefold(): name for name in known}
        return by_casefold.get(token.casefold())

    def _resolve_profile_name(self, profile_name: str) -> Optional[str]:
        token = _normalise_profile_name(profile_name)
        if token is None:
            return None
        for existing in self._enabled_by_profile.keys():
            if str(existing).casefold() == token.casefold():
                return existing
        return None

    @staticmethod
    def _resolved_group_enabled(values: Mapping[str, bool], group_name: str) -> bool:
        raw = values.get(group_name)
        if raw is None:
            return True
        return bool(raw)

    def _apply_enabled_updates(self, updates: Mapping[str, bool]) -> None:
        active_profile = self._resolve_profile_name(self._current_profile) or _DEFAULT_PROFILE_NAME
        active_map = dict(self._enabled_by_profile.get(active_profile, {}))
        default_map = dict(self._enabled_by_profile.get(_DEFAULT_PROFILE_NAME, {}))
        previous_default_resolved = {
            group_name: self._resolved_group_enabled(default_map, group_name)
            for group_name in updates.keys()
        }

        for group_name, enabled in updates.items():
            active_map[group_name] = bool(enabled)
        self._enabled_by_profile[active_profile] = dict(active_map)

        # Default edits propagate to non-divergent profile values.
        if active_profile.casefold() == _DEFAULT_PROFILE_NAME.casefold():
            updated_default = dict(active_map)
            for profile_name, profile_map in list(self._enabled_by_profile.items()):
                if str(profile_name).casefold() == _DEFAULT_PROFILE_NAME.casefold():
                    continue
                current_map = dict(profile_map)
                for group_name, enabled in updates.items():
                    previous_default = previous_default_resolved.get(group_name, True)
                    profile_value = self._resolved_group_enabled(current_map, group_name)
                    if profile_value != previous_default:
                        continue
                    current_map[group_name] = bool(enabled)
                self._enabled_by_profile[profile_name] = current_map
            self._enabled_by_profile[_DEFAULT_PROFILE_NAME] = updated_default
            self._enabled_overrides = dict(updated_default)
            return

        self._enabled_overrides = dict(active_map)

    def _touch_metadata(self, group_name: str, payload: Mapping[str, Any], *, count_disabled_update: bool) -> None:
        entry = self._metadata.setdefault(group_name, {})
        now_iso = _utc_iso_now()
        entry["last_payload_seen_at"] = now_iso
        bounds = self._extract_bounds(payload)
        if bounds is not None:
            entry["bounds"] = list(bounds)
            entry["last_bounds_updated_at"] = now_iso
        if count_disabled_update:
            self._counter_metadata += 1

    def _resolve_targets(self, group_names: Optional[Sequence[str]]) -> Iterable[str]:
        if group_names is None:
            return self.known_group_names()
        seen: set[str] = set()
        deduped: list[str] = []
        for raw in group_names:
            token = str(raw or "").strip()
            if not token:
                continue
            cf = token.casefold()
            if cf in seen:
                continue
            seen.add(cf)
            deduped.append(token)
        return deduped

    @staticmethod
    def _extract_bounds(payload: Mapping[str, Any]) -> Optional[Tuple[float, float, float, float]]:
        payload_type = str(payload.get("type") or "").strip().lower()
        if payload_type == "message":
            try:
                x = float(payload.get("x", 0.0))
                y = float(payload.get("y", 0.0))
            except (TypeError, ValueError):
                return None
            return (x, y, x, y)

        if payload_type == "image":
            try:
                x = float(payload.get("x", 0.0))
                y = float(payload.get("y", 0.0))
                w = float(payload.get("w", 0.0))
                h = float(payload.get("h", 0.0))
            except (TypeError, ValueError):
                return None
            return (x, y, x + w, y + h)

        if payload_type == "shape":
            shape = str(payload.get("shape") or "").strip().lower()
            if shape == "rect":
                try:
                    x = float(payload.get("x", 0.0))
                    y = float(payload.get("y", 0.0))
                    w = float(payload.get("w", 0.0))
                    h = float(payload.get("h", 0.0))
                except (TypeError, ValueError):
                    return None
                return (x, y, x + w, y + h)
            if shape == "vect":
                vector = payload.get("vector")
                if not isinstance(vector, Sequence):
                    return None
                min_x: Optional[float] = None
                min_y: Optional[float] = None
                max_x: Optional[float] = None
                max_y: Optional[float] = None
                for point in vector:
                    if not isinstance(point, Mapping):
                        continue
                    try:
                        x = float(point.get("x", 0.0))
                        y = float(point.get("y", 0.0))
                    except (TypeError, ValueError):
                        continue
                    if min_x is None or x < min_x:
                        min_x = x
                    if max_x is None or x > max_x:
                        max_x = x
                    if min_y is None or y < min_y:
                        min_y = y
                    if max_y is None or y > max_y:
                        max_y = y
                if min_x is None or min_y is None or max_x is None or max_y is None:
                    return None
                return (min_x, min_y, max_x, max_y)
        return None
