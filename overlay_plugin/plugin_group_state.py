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
_STATE_METADATA_KEY = "metadata"


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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

        for target in targets:
            canonical = self._canonical_group_name(target)
            if canonical is None:
                unknown.append(str(target))
                continue
            previous = self._enabled_overrides.get(canonical)
            if previous is not None and bool(previous) == bool(enabled):
                continue
            self._enabled_overrides[canonical] = bool(enabled)
            updated.append(canonical)

        if updated:
            self._persist_state()
        return updated, unknown

    def toggle_groups(self, group_names: Optional[Sequence[str]] = None) -> Tuple[list[str], list[str]]:
        self.reload_if_changed()
        unknown: list[str] = []
        updated: list[str] = []
        targets = self._resolve_targets(group_names)

        for target in targets:
            canonical = self._canonical_group_name(target)
            if canonical is None:
                unknown.append(str(target))
                continue
            next_state = not self.is_group_enabled(canonical)
            previous_override = self._enabled_overrides.get(canonical)
            if previous_override is not None and bool(previous_override) == next_state:
                continue
            self._enabled_overrides[canonical] = next_state
            updated.append(canonical)

        if updated:
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

    def _load_user_state(self) -> None:
        payload = self._read_user_file()
        state_root = payload.get(_STATE_ROOT_KEY)
        if not isinstance(state_root, Mapping):
            return
        enabled = state_root.get(_STATE_ENABLED_KEY)
        if isinstance(enabled, Mapping):
            for group_name, value in enabled.items():
                if not isinstance(group_name, str):
                    continue
                if isinstance(value, bool):
                    self._enabled_overrides[group_name] = value
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

        state_root[_STATE_ENABLED_KEY] = dict(self._enabled_overrides)
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
