from __future__ import annotations

import copy
import importlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

LOGGER = logging.getLogger("EDMC.ModernOverlay.ProfileState")

PROFILE_STATE_KEY = "_overlay_profile_state"
PROFILE_OVERRIDES_KEY = "_overlay_profile_overrides"
PROFILE_STATE_VERSION = 1
DEFAULT_PROFILE_NAME = "Default"
RULE_CONTEXTS = (
    "InMainShip",
    "InSRV",
    "InFighter",
    "OnFoot",
    "InWing",
    "InTaxi",
    "InMulticrew",
)
CONTROLLER_PLACEMENT_FIELDS = (
    "offsetX",
    "offsetY",
    "idPrefixGroupAnchor",
    "payloadJustification",
    "backgroundColor",
    "backgroundBorderColor",
    "backgroundBorderWidth",
)
_MISSING = object()

_edmc_data: Any = None
try:
    _edmc_data = importlib.import_module("edmc_data")
except Exception:  # pragma: no cover - running outside EDMC
    pass
_SHIP_NAME_MAP: Dict[str, str] = {}
if _edmc_data is not None:
    raw_ship_name_map = getattr(_edmc_data, "ship_name_map", None)
    if isinstance(raw_ship_name_map, Mapping):
        for raw_key, raw_value in raw_ship_name_map.items():
            key = str(raw_key or "").strip().casefold()
            value = str(raw_value or "").strip()
            if key and value:
                _SHIP_NAME_MAP[key] = value


class ProfileStateError(ValueError):
    """Raised when profile operations fail validation."""


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json_object(path: Path) -> Dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    except OSError:
        return {}
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _write_json_object(path: Path, payload: Dict[str, Any], logger: logging.Logger) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(text, encoding="utf-8")
        tmp_path.replace(path)
    except OSError as exc:  # pragma: no cover - environment-specific filesystem failures
        logger.warning("Unable to persist profile state: %s", exc)


def _normalise_profile_name(value: Any) -> Optional[str]:
    if value is None:
        return None
    token = str(value).strip()
    if not token:
        return None
    if token.casefold() == DEFAULT_PROFILE_NAME.casefold():
        return DEFAULT_PROFILE_NAME
    return token


def _is_plugin_override_key(key: object) -> bool:
    return isinstance(key, str) and bool(key) and not key.startswith("_")


def _extract_plugin_overrides(payload: Mapping[str, Any]) -> Dict[str, Any]:
    overrides: Dict[str, Any] = {}
    for key, value in payload.items():
        if _is_plugin_override_key(key):
            overrides[str(key)] = copy.deepcopy(value)
    return overrides


def _extract_metadata(payload: Mapping[str, Any]) -> Dict[str, Any]:
    metadata: Dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(key, str) and key.startswith("_"):
            metadata[key] = copy.deepcopy(value)
    return metadata


def _resolve_profile_case_insensitive(candidates: Iterable[str], wanted: Optional[str]) -> Optional[str]:
    if wanted is None:
        return None
    wanted_cf = wanted.casefold()
    for name in candidates:
        if name.casefold() == wanted_cf:
            return name
    return None


def _coerce_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalise_context(value: Any) -> str:
    token = str(value or "").strip()
    if token in RULE_CONTEXTS:
        return token
    token_cf = token.casefold()
    for candidate in RULE_CONTEXTS:
        if candidate.casefold() == token_cf:
            return candidate
    return "InMainShip"


def _normalise_rule(rule: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(rule, Mapping):
        return None
    context = _normalise_context(rule.get("context"))
    if context not in RULE_CONTEXTS:
        return None
    ship_id = _coerce_int(rule.get("ship_id"))
    if ship_id is None:
        ship_id = _coerce_int(rule.get("shipId"))
    if ship_id is None:
        ship_id = _coerce_int(rule.get("ShipID"))
    normalized: Dict[str, Any] = {"context": context}
    if context == "InMainShip" and ship_id is not None:
        normalized["ship_id"] = int(ship_id)
    return normalized


def _default_profile_rules() -> list[Dict[str, Any]]:
    return [{"context": context} for context in RULE_CONTEXTS]


def _normalise_rules_map(raw_rules: Any, profiles: list[str]) -> Dict[str, list[Dict[str, Any]]]:
    rules_by_profile: Dict[str, list[Dict[str, Any]]] = {name: [] for name in profiles}
    if not isinstance(raw_rules, Mapping):
        if DEFAULT_PROFILE_NAME in rules_by_profile:
            rules_by_profile[DEFAULT_PROFILE_NAME] = _default_profile_rules()
        return rules_by_profile
    for raw_profile, raw_profile_rules in raw_rules.items():
        profile_name = _normalise_profile_name(raw_profile)
        if profile_name is None:
            continue
        resolved = _resolve_profile_case_insensitive(profiles, profile_name)
        if resolved is None:
            continue
        if not isinstance(raw_profile_rules, list):
            continue
        unique: list[Dict[str, Any]] = []
        seen: set[tuple[str, Optional[int]]] = set()
        for raw_rule in raw_profile_rules:
            normalized = _normalise_rule(raw_rule)
            if normalized is None:
                continue
            key = (normalized["context"], normalized.get("ship_id"))
            if key in seen:
                continue
            seen.add(key)
            unique.append(normalized)
        rules_by_profile[resolved] = unique
    if DEFAULT_PROFILE_NAME in rules_by_profile:
        rules_by_profile[DEFAULT_PROFILE_NAME] = _default_profile_rules()
    return rules_by_profile


def _normalise_profiles(raw_profiles: Any, raw_overrides: Any, current: Optional[str], manual: Optional[str]) -> list[str]:
    candidates: list[str] = []
    if isinstance(raw_profiles, list):
        for item in raw_profiles:
            token = _normalise_profile_name(item)
            if token is not None:
                candidates.append(token)
    if isinstance(raw_overrides, Mapping):
        for key in raw_overrides.keys():
            token = _normalise_profile_name(key)
            if token is not None:
                candidates.append(token)
    for item in (current, manual, DEFAULT_PROFILE_NAME):
        token = _normalise_profile_name(item)
        if token is not None:
            candidates.append(token)

    deduped: list[str] = []
    seen: set[str] = set()
    for token in candidates:
        cf = token.casefold()
        if cf in seen:
            continue
        seen.add(cf)
        deduped.append(token)

    if DEFAULT_PROFILE_NAME not in deduped:
        deduped.append(DEFAULT_PROFILE_NAME)
    else:
        deduped = [name for name in deduped if name != DEFAULT_PROFILE_NAME] + [DEFAULT_PROFILE_NAME]
    return deduped


def _normalise_overrides(raw_overrides: Any, profiles: list[str], root_overrides: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    raw_mapping: Mapping[str, Any] = raw_overrides if isinstance(raw_overrides, Mapping) else {}
    for profile_name in profiles:
        source_payload: Mapping[str, Any] = {}
        for raw_name, value in raw_mapping.items():
            if not isinstance(raw_name, str):
                continue
            if raw_name.casefold() != profile_name.casefold():
                continue
            if isinstance(value, Mapping):
                source_payload = value
            break
        result[profile_name] = _extract_plugin_overrides(source_payload)

    for profile_name in profiles:
        if profile_name in result:
            continue
        result[profile_name] = {}
    return result


def _normalise_ship_entry(raw: Mapping[str, Any], existing: Optional[Mapping[str, Any]] = None) -> Optional[Dict[str, Any]]:
    ship_id = _ship_id_from_mapping(raw)
    if ship_id is None:
        return None

    merged: Dict[str, Any] = dict(existing or {})
    merged["ship_id"] = int(ship_id)

    ship_type_fallback = _first_non_empty(
        raw,
        (
            "ShipType",
            "Ship",
            "ship_type",
        ),
    )
    fallback_token = str(ship_type_fallback or "").strip()
    fallback_label = _ship_type_label(fallback_token)
    existing_type = str(merged.get("ship_type") or "").strip()
    # Ship-type display names come exclusively from ShipType + edmc_data.ship_name_map.
    # Update when empty or when the stored value is the same raw ShipType token.
    if fallback_label and (
        not existing_type or (
            fallback_token and existing_type.casefold() == fallback_token.casefold()
        )
    ):
        merged["ship_type"] = fallback_label

    ship_name = _first_non_empty(
        raw,
        (
            "UserShipName",
            "ShipName",
            "ShipName_Localised",
            "ShipNameLocalised",
            "Name_Localised",
            "NameLocalised",
            "ship_name",
            "Name",
        ),
    )
    if ship_name is not None:
        token = str(ship_name).strip()
        if token and not token.startswith("$"):
            merged["ship_name"] = token

    ship_ident = raw.get("UserShipId")
    if ship_ident is None:
        ship_ident = raw.get("ShipIdent")
    if ship_ident is None:
        ship_ident = raw.get("ship_ident")
    if ship_ident is not None:
        token = str(ship_ident).strip()
        if token:
            merged["ship_ident"] = token

    return merged


def _ship_id_from_mapping(raw: Mapping[str, Any]) -> Optional[int]:
    for key in ("ShipID", "ship_id", "shipId"):
        ship_id = _coerce_int(raw.get(key))
        if ship_id is not None:
            return int(ship_id)
    return None


def _ship_type_label(value: Any) -> str:
    token = str(value or "").strip()
    if not token or token.startswith("$"):
        return ""
    return _SHIP_NAME_MAP.get(token.casefold(), token)


def _first_non_empty(raw: Mapping[str, Any], keys: tuple[str, ...]) -> Optional[str]:
    for key in keys:
        value = raw.get(key)
        if value is None:
            continue
        token = str(value).strip()
        if token:
            return token
    return None


def _ship_sort_key(entry: Mapping[str, Any]) -> int:
    return int(entry.get("ship_id") or 0)


def _ship_label(entry: Mapping[str, Any]) -> str:
    ship_name = str(entry.get("ship_name") or "").strip()
    ship_ident = str(entry.get("ship_ident") or "").strip()
    if not ship_name:
        return ""
    if ship_ident:
        return f"{ship_name} ({ship_ident})"
    return ship_name


def _deep_merge(base: Dict[str, Any], overlay: Mapping[str, Any]) -> Dict[str, Any]:
    for key, value in overlay.items():
        if isinstance(value, Mapping):
            existing = base.get(key)
            if isinstance(existing, dict):
                base[key] = _deep_merge(existing, value)
            else:
                base[key] = _deep_merge({}, value)
            continue
        base[key] = copy.deepcopy(value)
    return base


def _normalise_profile_order(values: Iterable[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for item in values:
        token = _normalise_profile_name(item)
        if token is None:
            continue
        cf = token.casefold()
        if cf in seen:
            continue
        seen.add(cf)
        ordered.append(token)
    if DEFAULT_PROFILE_NAME in ordered:
        ordered = [name for name in ordered if name != DEFAULT_PROFILE_NAME] + [DEFAULT_PROFILE_NAME]
    else:
        ordered.append(DEFAULT_PROFILE_NAME)
    return ordered


def _normalise_fleet_cache(raw: Any) -> Dict[str, Any]:
    cache = raw if isinstance(raw, Mapping) else {}
    ships_raw = cache.get("ships") if isinstance(cache, Mapping) else None
    ships: Dict[int, Dict[str, Any]] = {}
    if isinstance(ships_raw, list):
        for item in ships_raw:
            if not isinstance(item, Mapping):
                continue
            normalized = _normalise_ship_entry(item)
            if normalized is None:
                continue
            ships[int(normalized["ship_id"])] = normalized
    ordered = [ships[key] for key in sorted(ships.keys(), key=lambda sid: _ship_sort_key(ships[sid]))]
    updated_at = cache.get("updated_at")
    updated_token = str(updated_at).strip() if updated_at is not None else ""
    return {"ships": ordered, "updated_at": updated_token}


def _rules_for_payload(rules_by_profile: Mapping[str, list[Dict[str, Any]]]) -> Dict[str, list[Dict[str, Any]]]:
    payload: Dict[str, list[Dict[str, Any]]] = {}
    for profile_name, rules in rules_by_profile.items():
        payload[profile_name] = []
        for rule in rules:
            entry = {"context": rule.get("context")}
            if rule.get("context") == "InMainShip" and rule.get("ship_id") is not None:
                entry["ship_id"] = int(rule["ship_id"])
            payload[profile_name].append(entry)
    return payload


def _normalise_context_tokens(values: Iterable[Any]) -> set[str]:
    tokens: set[str] = set()
    for item in values:
        normalized = _normalise_context(item)
        if normalized in RULE_CONTEXTS:
            tokens.add(normalized)
    return tokens


def _rule_matches(rule: Mapping[str, Any], active_contexts: set[str], ship_id: Optional[int]) -> bool:
    context = str(rule.get("context") or "")
    if context not in active_contexts:
        return False
    required_ship_id = _coerce_int(rule.get("ship_id"))
    if context == "InMainShip" and required_ship_id is not None:
        return ship_id is not None and int(ship_id) == int(required_ship_id)
    return True


class OverlayProfileStore:
    """Profile/fleet persistence and activation logic for overlay placements."""

    def __init__(self, *, user_path: Path, logger: Optional[logging.Logger] = None) -> None:
        self._user_path = user_path
        self._logger = logger or LOGGER

    # Public API ---------------------------------------------------------

    def status(self) -> Dict[str, Any]:
        model = self._load_model()
        return self._status_payload(model)

    def create_profile(self, name: str) -> Dict[str, Any]:
        token = _normalise_profile_name(name)
        if token is None:
            raise ProfileStateError("Profile name is required.")

        model = self._load_model()
        existing = _resolve_profile_case_insensitive(model["profiles"], token)
        if existing is not None:
            raise ProfileStateError(f"Profile '{token}' already exists.")
        if token == DEFAULT_PROFILE_NAME:
            raise ProfileStateError("Default profile already exists.")

        default_payload = copy.deepcopy(model["overrides"].get(DEFAULT_PROFILE_NAME, {}))
        model["profiles"].append(token)
        model["profiles"] = _normalise_profile_order(model["profiles"])
        model["rules"][token] = []
        model["overrides"][token] = default_payload
        self._save_model(model)
        return self._status_payload(model)

    def clone_profile(self, source_profile: str, new_profile: str) -> Dict[str, Any]:
        source_token = _normalise_profile_name(source_profile)
        target_token = _normalise_profile_name(new_profile)
        if source_token is None:
            raise ProfileStateError("Source profile name is required.")
        if target_token is None:
            raise ProfileStateError("New profile name is required.")

        model = self._load_model()
        resolved_source = _resolve_profile_case_insensitive(model["profiles"], source_token)
        if resolved_source is None:
            raise ProfileStateError(f"Profile '{source_profile}' was not found.")
        existing_target = _resolve_profile_case_insensitive(model["profiles"], target_token)
        if existing_target is not None:
            raise ProfileStateError(f"Profile '{target_token}' already exists.")
        if target_token == DEFAULT_PROFILE_NAME:
            raise ProfileStateError("Default profile already exists.")

        model["profiles"].append(target_token)
        model["profiles"] = _normalise_profile_order(model["profiles"])
        model["rules"][target_token] = copy.deepcopy(model["rules"].get(resolved_source, []))
        model["overrides"][target_token] = copy.deepcopy(model["overrides"].get(resolved_source, {}))
        self._save_model(model)
        return self._status_payload(model)

    def rename_profile(self, old_name: str, new_name: str) -> Dict[str, Any]:
        source = _normalise_profile_name(old_name)
        target = _normalise_profile_name(new_name)
        if source is None:
            raise ProfileStateError("Source profile name is required.")
        if target is None:
            raise ProfileStateError("New profile name is required.")

        model = self._load_model()
        resolved_source = _resolve_profile_case_insensitive(model["profiles"], source)
        if resolved_source is None:
            raise ProfileStateError(f"Profile '{old_name}' was not found.")
        if resolved_source == DEFAULT_PROFILE_NAME:
            raise ProfileStateError("Default profile cannot be renamed.")

        resolved_target = _resolve_profile_case_insensitive(model["profiles"], target)
        if resolved_target is not None and resolved_target.casefold() != resolved_source.casefold():
            raise ProfileStateError(f"Profile '{target}' already exists.")

        if resolved_source == target:
            return self._status_payload(model)

        model["profiles"] = [target if name == resolved_source else name for name in model["profiles"]]
        model["profiles"] = _normalise_profile_order(model["profiles"])
        model["rules"][target] = list(model["rules"].get(resolved_source, []))
        model["rules"].pop(resolved_source, None)
        model["overrides"][target] = copy.deepcopy(model["overrides"].get(resolved_source, {}))
        model["overrides"].pop(resolved_source, None)

        if model["current_profile"] == resolved_source:
            model["current_profile"] = target
        if model["manual_profile"] == resolved_source:
            model["manual_profile"] = target

        self._save_model(model)
        return self._status_payload(model)

    def delete_profile(self, name: str) -> Dict[str, Any]:
        token = _normalise_profile_name(name)
        if token is None:
            raise ProfileStateError("Profile name is required.")

        model = self._load_model()
        resolved = _resolve_profile_case_insensitive(model["profiles"], token)
        if resolved is None:
            raise ProfileStateError(f"Profile '{name}' was not found.")
        if resolved == DEFAULT_PROFILE_NAME:
            raise ProfileStateError("Default profile cannot be deleted.")

        model["profiles"] = [item for item in model["profiles"] if item != resolved]
        model["rules"].pop(resolved, None)
        model["overrides"].pop(resolved, None)

        if model["manual_profile"] == resolved:
            model["manual_profile"] = DEFAULT_PROFILE_NAME
        if model["current_profile"] == resolved:
            fallback = _resolve_profile_case_insensitive(model["profiles"], model["manual_profile"])
            model["current_profile"] = fallback or DEFAULT_PROFILE_NAME

        self._save_model(model)
        return self._status_payload(model)

    def reorder_profile(self, profile_name: str, target_index: int) -> Dict[str, Any]:
        token = _normalise_profile_name(profile_name)
        if token is None:
            raise ProfileStateError("Profile name is required.")

        model = self._load_model()
        resolved = _resolve_profile_case_insensitive(model["profiles"], token)
        if resolved is None:
            raise ProfileStateError(f"Profile '{profile_name}' was not found.")
        if resolved == DEFAULT_PROFILE_NAME:
            return self._status_payload(model)

        non_default = [name for name in model["profiles"] if name != DEFAULT_PROFILE_NAME]
        non_default = [name for name in non_default if name.casefold() != resolved.casefold()]
        index = max(0, min(int(target_index), len(non_default)))
        non_default.insert(index, resolved)
        model["profiles"] = [*non_default, DEFAULT_PROFILE_NAME]
        self._save_model(model)
        return self._status_payload(model)

    def set_current_profile(self, name: str, *, source: str = "manual") -> Dict[str, Any]:
        token = _normalise_profile_name(name)
        if token is None:
            raise ProfileStateError("Profile name is required.")

        model = self._load_model()
        resolved = _resolve_profile_case_insensitive(model["profiles"], token)
        if resolved is None:
            raise ProfileStateError(f"Profile '{name}' was not found.")

        changed = model["current_profile"] != resolved
        model["current_profile"] = resolved
        if source == "manual":
            model["manual_profile"] = resolved

        if changed:
            self._save_model(model)
        return self._status_payload(model)

    def set_profile_rules(self, profile_name: str, rules: list[Mapping[str, Any]]) -> Dict[str, Any]:
        token = _normalise_profile_name(profile_name)
        if token is None:
            raise ProfileStateError("Profile name is required.")

        model = self._load_model()
        resolved = _resolve_profile_case_insensitive(model["profiles"], token)
        if resolved is None:
            raise ProfileStateError(f"Profile '{profile_name}' was not found.")

        if resolved.casefold() == DEFAULT_PROFILE_NAME.casefold():
            model["rules"][resolved] = _default_profile_rules()
            self._save_model(model)
            return self._status_payload(model)

        unique: list[Dict[str, Any]] = []
        seen: set[tuple[str, Optional[int]]] = set()
        for raw_rule in rules:
            normalized = _normalise_rule(raw_rule)
            if normalized is None:
                continue
            key = (normalized["context"], normalized.get("ship_id"))
            if key in seen:
                continue
            seen.add(key)
            unique.append(normalized)
        model["rules"][resolved] = unique
        self._save_model(model)
        return self._status_payload(model)

    def apply_group_fields(
        self,
        *,
        plugin_name: str,
        group_label: str,
        updates: Mapping[str, Any],
        clear_fields: Iterable[str] = (),
    ) -> Dict[str, Any]:
        plugin_token = str(plugin_name or "").strip()
        group_token = str(group_label or "").strip()
        if not plugin_token or not group_token:
            raise ProfileStateError("Plugin and group names are required.")

        model = self._load_model()
        self._ensure_full_snapshots(model)
        current_profile = str(model.get("current_profile") or DEFAULT_PROFILE_NAME)
        changed = False
        changed_fields = {
            str(key).strip()
            for key in set(list(updates.keys()) + [str(item) for item in clear_fields])
            if str(key).strip()
        }
        if current_profile == DEFAULT_PROFILE_NAME:
            before_default = copy.deepcopy(model["overrides"].get(DEFAULT_PROFILE_NAME, {}))
            default_snapshot = model["overrides"].setdefault(DEFAULT_PROFILE_NAME, {})
            changed = self._apply_group_patch(
                default_snapshot,
                plugin_token,
                group_token,
                updates=updates,
                clear_fields=clear_fields,
            ) or changed
            if changed_fields:
                for profile_name in model["profiles"]:
                    if str(profile_name).casefold() == DEFAULT_PROFILE_NAME.casefold():
                        continue
                    snapshot = model["overrides"].setdefault(profile_name, {})
                    for field in changed_fields:
                        previous_default = self._get_group_field(
                            before_default,
                            plugin_token,
                            group_token,
                            field,
                            missing=_MISSING,
                        )
                        profile_value = self._get_group_field(
                            snapshot,
                            plugin_token,
                            group_token,
                            field,
                            missing=_MISSING,
                        )
                        if profile_value is not _MISSING and profile_value != previous_default:
                            continue
                        new_default = self._get_group_field(
                            default_snapshot,
                            plugin_token,
                            group_token,
                            field,
                            missing=_MISSING,
                        )
                        changed = self._set_group_field(
                            snapshot,
                            plugin_token,
                            group_token,
                            field,
                            new_default,
                        ) or changed
        else:
            snapshot = model["overrides"].setdefault(current_profile, {})
            changed = self._apply_group_patch(
                snapshot,
                plugin_token,
                group_token,
                updates=updates,
                clear_fields=clear_fields,
            ) or changed
        if changed:
            self._save_model(model)
        return self._status_payload(model)

    def reset_group_for_active_profile(
        self,
        *,
        plugin_name: str,
        group_label: str,
        shipped_group: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        plugin_token = str(plugin_name or "").strip()
        group_token = str(group_label or "").strip()
        if not plugin_token or not group_token:
            raise ProfileStateError("Plugin and group names are required.")

        model = self._load_model()
        self._ensure_full_snapshots(model)
        current_profile = str(model.get("current_profile") or DEFAULT_PROFILE_NAME)
        changed = False
        if current_profile.casefold() == DEFAULT_PROFILE_NAME.casefold():
            for profile_name in model["profiles"]:
                snapshot = model["overrides"].setdefault(profile_name, {})
                changed = self._reset_group_fields(
                    snapshot,
                    plugin_token,
                    group_token,
                    source_group=shipped_group,
                ) or changed
        else:
            default_snapshot = model["overrides"].setdefault(DEFAULT_PROFILE_NAME, {})
            source_group = self._get_group_mapping(default_snapshot, plugin_token, group_token, create=False)
            snapshot = model["overrides"].setdefault(current_profile, {})
            changed = self._reset_group_fields(
                snapshot,
                plugin_token,
                group_token,
                source_group=source_group,
            ) or changed
        if changed:
            self._save_model(model)
        return self._status_payload(model)

    def apply_context(self, *, context: str, ship_id: Optional[int]) -> Dict[str, Any]:
        model = self._load_model()
        normalized_context = _normalise_context(context)
        active_contexts = {normalized_context}
        selected = self._select_profile_for_context(
            model,
            active_contexts=active_contexts,
            ship_id=ship_id,
        )
        changed = selected != model["current_profile"]
        if changed:
            model["current_profile"] = selected
            self._save_model(model)
        return {
            "changed": changed,
            "current_profile": model["current_profile"],
            "manual_profile": model["manual_profile"],
            "matched_profile": self._match_profile(model, active_contexts=active_contexts, ship_id=ship_id),
            "context": normalized_context,
            "ship_id": ship_id,
        }

    def match_profile(
        self,
        *,
        context: Optional[str] = None,
        active_contexts: Optional[Iterable[str]] = None,
        ship_id: Optional[int] = None,
    ) -> Optional[str]:
        model = self._load_model()
        if active_contexts is not None:
            tokens = _normalise_context_tokens(active_contexts)
        else:
            tokens = {_normalise_context(context)}
        return self._match_profile(model, active_contexts=tokens, ship_id=ship_id)

    def update_fleet_from_journal(
        self,
        *,
        entry: Mapping[str, Any],
        state: Optional[Mapping[str, Any]] = None,
    ) -> bool:
        model = self._load_model()
        cache = model["fleet_cache"]
        fleet_by_id: Dict[int, Dict[str, Any]] = {
            int(item["ship_id"]): dict(item)
            for item in cache.get("ships", [])
            if isinstance(item, Mapping) and _coerce_int(item.get("ship_id")) is not None
        }
        changed = False
        event = str(entry.get("event") or "").strip()

        if event == "StoredShips":
            snapshot: Dict[int, Dict[str, Any]] = {}
            for ship_record in self._iter_stored_ship_records(entry):
                ship_id = _ship_id_from_mapping(ship_record)
                existing_entry = fleet_by_id.get(ship_id) if ship_id is not None else None
                normalized = _normalise_ship_entry(ship_record, existing=existing_entry)
                if normalized is None:
                    continue
                snapshot[int(normalized["ship_id"])] = normalized

            # FDev StoredShips snapshots may omit the currently occupied ship.
            # Merge active-ship deltas from entry/state so the cache remains complete.
            for record in self._delta_ship_records(event=event, entry=entry, state=state):
                ship_id = _ship_id_from_mapping(record)
                if ship_id is None:
                    continue
                existing_entry = snapshot.get(ship_id) or fleet_by_id.get(ship_id)
                normalized = _normalise_ship_entry(record, existing=existing_entry)
                if normalized is None:
                    continue
                snapshot[int(normalized["ship_id"])] = normalized
            if snapshot and snapshot != fleet_by_id:
                fleet_by_id = snapshot
                changed = True
        else:
            for removed_id in self._removed_ship_ids(event=event, entry=entry):
                if removed_id in fleet_by_id:
                    fleet_by_id.pop(removed_id, None)
                    changed = True

            for record in self._delta_ship_records(event=event, entry=entry, state=state):
                ship_id = _ship_id_from_mapping(record)
                existing = fleet_by_id.get(ship_id) if ship_id is not None else None
                normalized = _normalise_ship_entry(record, existing=existing)
                if normalized is None:
                    continue
                ship_id = int(normalized["ship_id"])
                existing = fleet_by_id.get(ship_id)
                if normalized != existing:
                    fleet_by_id[ship_id] = normalized
                    changed = True

        if not changed:
            return False

        ordered = [fleet_by_id[sid] for sid in sorted(fleet_by_id.keys(), key=lambda sid: _ship_sort_key(fleet_by_id[sid]))]
        model["fleet_cache"] = {"ships": ordered, "updated_at": _utc_iso_now()}
        self._save_model(model)
        return True

    def _ensure_full_snapshots(self, model: Dict[str, Any]) -> None:
        profiles_raw = model.get("profiles")
        if not isinstance(profiles_raw, list):
            return
        profiles = [str(item) for item in profiles_raw if isinstance(item, str)]
        model["profiles"] = _normalise_profile_order(profiles)
        overrides_raw = model.get("overrides")
        overrides: Dict[str, Dict[str, Any]] = overrides_raw if isinstance(overrides_raw, dict) else {}
        default_snapshot = overrides.get(DEFAULT_PROFILE_NAME)
        if not isinstance(default_snapshot, dict):
            default_snapshot = {}
        overrides[DEFAULT_PROFILE_NAME] = copy.deepcopy(default_snapshot)
        for profile_name in model["profiles"]:
            if profile_name == DEFAULT_PROFILE_NAME:
                continue
            current = overrides.get(profile_name)
            current_map = current if isinstance(current, Mapping) else {}
            merged = _deep_merge(copy.deepcopy(default_snapshot), current_map)
            overrides[profile_name] = merged
        model["overrides"] = overrides

    @staticmethod
    def _get_group_mapping(
        snapshot: Mapping[str, Any],
        plugin_name: str,
        group_label: str,
        *,
        create: bool,
    ) -> Optional[Dict[str, Any]]:
        plugin_entry = snapshot.get(plugin_name)
        if not isinstance(plugin_entry, dict):
            if not create:
                return None
            plugin_entry = {}
            if isinstance(snapshot, dict):
                snapshot[plugin_name] = plugin_entry
        groups = plugin_entry.get("idPrefixGroups")
        if not isinstance(groups, dict):
            if not create:
                return None
            groups = {}
            plugin_entry["idPrefixGroups"] = groups
        group = groups.get(group_label)
        if not isinstance(group, dict):
            if not create:
                return None
            group = {}
            groups[group_label] = group
        return group

    @classmethod
    def _get_group_field(
        cls,
        snapshot: Mapping[str, Any],
        plugin_name: str,
        group_label: str,
        field: str,
        *,
        missing: object,
    ) -> Any:
        group = cls._get_group_mapping(snapshot, plugin_name, group_label, create=False)
        if not isinstance(group, Mapping) or field not in group:
            return missing
        return copy.deepcopy(group.get(field))

    @classmethod
    def _set_group_field(
        cls,
        snapshot: Dict[str, Any],
        plugin_name: str,
        group_label: str,
        field: str,
        value: Any,
    ) -> bool:
        group = cls._get_group_mapping(snapshot, plugin_name, group_label, create=True)
        if group is None:
            return False
        if value is _MISSING:
            if field in group:
                group.pop(field, None)
                return True
            return False
        copied = copy.deepcopy(value)
        if group.get(field) == copied:
            return False
        group[field] = copied
        return True

    @classmethod
    def _apply_group_patch(
        cls,
        snapshot: Dict[str, Any],
        plugin_name: str,
        group_label: str,
        *,
        updates: Mapping[str, Any],
        clear_fields: Iterable[str],
    ) -> bool:
        changed = False
        for field in clear_fields:
            token = str(field or "").strip()
            if not token:
                continue
            changed = cls._set_group_field(snapshot, plugin_name, group_label, token, _MISSING) or changed
        for field, value in updates.items():
            token = str(field or "").strip()
            if not token:
                continue
            changed = cls._set_group_field(snapshot, plugin_name, group_label, token, value) or changed
        return changed

    @classmethod
    def _reset_group_fields(
        cls,
        snapshot: Dict[str, Any],
        plugin_name: str,
        group_label: str,
        *,
        source_group: Optional[Mapping[str, Any]],
    ) -> bool:
        changed = False
        source = source_group if isinstance(source_group, Mapping) else {}
        for field in CONTROLLER_PLACEMENT_FIELDS:
            if field in source:
                changed = cls._set_group_field(
                    snapshot,
                    plugin_name,
                    group_label,
                    field,
                    source.get(field),
                ) or changed
            else:
                changed = cls._set_group_field(
                    snapshot,
                    plugin_name,
                    group_label,
                    field,
                    _MISSING,
                ) or changed
        return changed

    # Internal helpers ---------------------------------------------------

    def _load_model(self) -> Dict[str, Any]:
        payload = _read_json_object(self._user_path)
        root_overrides = _extract_plugin_overrides(payload)
        state_payload = payload.get(PROFILE_STATE_KEY)
        state_payload = state_payload if isinstance(state_payload, Mapping) else {}
        overrides_payload = payload.get(PROFILE_OVERRIDES_KEY)
        overrides_payload = overrides_payload if isinstance(overrides_payload, Mapping) else {}

        current_raw = _normalise_profile_name(state_payload.get("current_profile"))
        manual_raw = _normalise_profile_name(state_payload.get("manual_profile"))
        profiles = _normalise_profiles(state_payload.get("profiles"), overrides_payload, current_raw, manual_raw)

        current = _resolve_profile_case_insensitive(profiles, current_raw) or DEFAULT_PROFILE_NAME
        manual = _resolve_profile_case_insensitive(profiles, manual_raw) or current
        overrides = _normalise_overrides(overrides_payload, profiles, root_overrides)
        overrides[current] = copy.deepcopy(root_overrides)

        rules = _normalise_rules_map(state_payload.get("rules"), profiles)
        fleet_cache = _normalise_fleet_cache(state_payload.get("fleet_cache"))

        model = {
            "profiles": _normalise_profile_order(profiles),
            "current_profile": current,
            "manual_profile": manual,
            "rules": rules,
            "overrides": overrides,
            "fleet_cache": fleet_cache,
            "metadata": _extract_metadata(payload),
        }
        if model["current_profile"] not in model["profiles"]:
            model["profiles"].append(model["current_profile"])
            model["profiles"] = _normalise_profile_order(model["profiles"])
        if model["manual_profile"] not in model["profiles"]:
            model["manual_profile"] = DEFAULT_PROFILE_NAME
        for name in model["profiles"]:
            model["rules"].setdefault(name, [])
            model["overrides"].setdefault(name, {})
        self._ensure_full_snapshots(model)
        return model

    def _save_model(self, model: Dict[str, Any]) -> None:
        existing_payload = _read_json_object(self._user_path)
        preserved_metadata = _extract_metadata(existing_payload)
        preserved_metadata.pop(PROFILE_STATE_KEY, None)
        preserved_metadata.pop(PROFILE_OVERRIDES_KEY, None)

        payload: Dict[str, Any] = {}
        payload.update(preserved_metadata)

        current_profile = model["current_profile"]
        current_overrides = model["overrides"].get(current_profile, {})
        if isinstance(current_overrides, Mapping):
            for key, value in _extract_plugin_overrides(current_overrides).items():
                payload[key] = value

        state_payload = {
            "version": PROFILE_STATE_VERSION,
            "current_profile": current_profile,
            "manual_profile": model["manual_profile"],
            "profiles": list(model["profiles"]),
            "rules": _rules_for_payload(model["rules"]),
            "fleet_cache": model["fleet_cache"],
        }
        payload[PROFILE_STATE_KEY] = state_payload

        profile_overrides_payload: Dict[str, Any] = {}
        for profile_name in model["profiles"]:
            source = model["overrides"].get(profile_name, {})
            if not isinstance(source, Mapping):
                source = {}
            profile_overrides_payload[profile_name] = _extract_plugin_overrides(source)
        payload[PROFILE_OVERRIDES_KEY] = profile_overrides_payload

        _write_json_object(self._user_path, payload, self._logger)

    def _status_payload(self, model: Dict[str, Any]) -> Dict[str, Any]:
        ships = []
        for item in model["fleet_cache"].get("ships", []):
            if not isinstance(item, Mapping):
                continue
            ship_id = _coerce_int(item.get("ship_id"))
            if ship_id is None:
                continue
            ships.append(
                {
                    "ship_id": int(ship_id),
                    "ship_type": str(item.get("ship_type") or "").strip(),
                    "ship_name": str(item.get("ship_name") or "").strip(),
                    "ship_ident": str(item.get("ship_ident") or "").strip(),
                    "label": _ship_label(item),
                }
            )
        return {
            "profiles": list(model["profiles"]),
            "current_profile": model["current_profile"],
            "manual_profile": model["manual_profile"],
            "rules": _rules_for_payload(model["rules"]),
            "ships": ships,
            "fleet_updated_at": str(model["fleet_cache"].get("updated_at") or ""),
        }

    @staticmethod
    def _iter_stored_ship_records(entry: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
        for key in ("ShipsHere", "ShipsRemote"):
            raw = entry.get(key)
            if isinstance(raw, list):
                for item in raw:
                    if isinstance(item, Mapping):
                        yield item
            elif isinstance(raw, Mapping):
                for item in raw.values():
                    if isinstance(item, Mapping):
                        yield item

    @staticmethod
    def _removed_ship_ids(event: str, entry: Mapping[str, Any]) -> list[int]:
        if event not in {"ShipyardSell", "SellShipOnRebuy"}:
            return []
        removed: list[int] = []
        for key in ("SellShipID", "ShipID", "ship_id"):
            candidate = _coerce_int(entry.get(key))
            if candidate is None:
                continue
            removed.append(int(candidate))
        return removed

    @staticmethod
    def _delta_ship_records(
        *,
        event: str,
        entry: Mapping[str, Any],
        state: Optional[Mapping[str, Any]],
    ) -> list[Mapping[str, Any]]:
        records: list[Mapping[str, Any]] = []
        if event in {
            "LoadGame",
            "Loadout",
            "StoredShips",
            "ShipyardBuy",
            "ShipyardSwap",
            "SetUserShipName",
            "Embark",
            "DockSRV",
            "DockFighter",
        }:
            records.append(entry)
        if isinstance(state, Mapping):
            records.append(state)
        return records

    @staticmethod
    def _match_profile(
        model: Mapping[str, Any],
        *,
        active_contexts: set[str],
        ship_id: Optional[int],
    ) -> Optional[str]:
        profiles = model.get("profiles")
        rules_by_profile = model.get("rules")
        if not isinstance(profiles, list) or not isinstance(rules_by_profile, Mapping):
            return None
        default_token = DEFAULT_PROFILE_NAME.casefold()
        for profile_name in profiles:
            if not isinstance(profile_name, str):
                continue
            if profile_name.casefold() == default_token:
                continue
            raw_rules = rules_by_profile.get(profile_name)
            if not isinstance(raw_rules, list) or not raw_rules:
                continue
            if any(_rule_matches(rule, active_contexts, ship_id) for rule in raw_rules if isinstance(rule, Mapping)):
                # Among non-default matches, persisted profile order is the tie-breaker.
                return profile_name
        return None

    def _select_profile_for_context(
        self,
        model: Mapping[str, Any],
        *,
        active_contexts: set[str],
        ship_id: Optional[int],
    ) -> str:
        matched = self._match_profile(model, active_contexts=active_contexts, ship_id=ship_id)
        if matched is not None:
            return matched
        manual_profile = _normalise_profile_name(model.get("manual_profile"))
        profiles = model.get("profiles")
        if isinstance(profiles, list):
            resolved = _resolve_profile_case_insensitive([str(item) for item in profiles if isinstance(item, str)], manual_profile)
            if resolved is not None:
                return resolved
        return DEFAULT_PROFILE_NAME
