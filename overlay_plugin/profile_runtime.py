from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional

from .command_overlay_groups import COMMAND_PROFILE_STATUS_ID_PREFIX
from .profile_state import DEFAULT_PROFILE_NAME

UTC = timezone.utc
PROFILE_STATUS_MESSAGE_COLOR = "#80d0ff"
PROFILE_STATUS_MESSAGE_SIZE = "large"
PROFILE_STATUS_MESSAGE_X = 40
PROFILE_STATUS_MESSAGE_Y = 76

# Elite Dangerous dashboard status bit masks used for profile rule evaluation.
FLAG_IN_WING = 1 << 7
FLAG_IN_MAIN_SHIP = 1 << 24
FLAG_IN_FIGHTER = 1 << 25
FLAG_IN_SRV = 1 << 26
FLAG2_ON_FOOT = 1 << 0
FLAG2_IN_TAXI = 1 << 1
FLAG2_IN_MULTICREW = 1 << 2


def _fallback_status() -> Dict[str, Any]:
    return {
        "profiles": [DEFAULT_PROFILE_NAME],
        "current_profile": DEFAULT_PROFILE_NAME,
        "manual_profile": DEFAULT_PROFILE_NAME,
        "rules": {DEFAULT_PROFILE_NAME: []},
        "ships": [],
        "fleet_updated_at": "",
    }


def profile_ship_id_from_mapping(mapping: Optional[Mapping[str, Any]]) -> Optional[int]:
    if not isinstance(mapping, Mapping):
        return None
    for key in ("ShipID", "ship_id", "ShipId"):
        raw = mapping.get(key)
        if raw is None:
            continue
        try:
            return int(raw)
        except (TypeError, ValueError):
            continue
    return None


def update_profile_runtime_state(runtime: Any, entry: Mapping[str, Any], state: Optional[Mapping[str, Any]]) -> None:
    ship_id = profile_ship_id_from_mapping(entry)
    if ship_id is None:
        ship_id = profile_ship_id_from_mapping(state)
    if ship_id is not None:
        runtime._profile_ship_id = ship_id


def decode_dashboard_contexts(entry: Mapping[str, Any]) -> set[str]:
    def _to_int(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    flags = _to_int(entry.get("Flags"))
    flags2 = _to_int(entry.get("Flags2"))
    contexts: set[str] = set()
    if flags & FLAG_IN_MAIN_SHIP:
        contexts.add("InMainShip")
    if flags & FLAG_IN_SRV:
        contexts.add("InSRV")
    if flags & FLAG_IN_FIGHTER:
        contexts.add("InFighter")
    if flags2 & FLAG2_ON_FOOT:
        contexts.add("OnFoot")
    if flags & FLAG_IN_WING:
        contexts.add("InWing")
    if flags2 & FLAG2_IN_TAXI:
        contexts.add("InTaxi")
    if flags2 & FLAG2_IN_MULTICREW:
        contexts.add("InMulticrew")
    return contexts


def handle_dashboard_entry(runtime: Any, entry: Mapping[str, Any]) -> None:
    if not isinstance(entry, Mapping):
        return
    contexts = decode_dashboard_contexts(entry)
    runtime._profile_active_contexts = contexts if contexts else set()
    ship_id = profile_ship_id_from_mapping(entry)
    if ship_id is not None:
        runtime._profile_ship_id = ship_id
    runtime._profile_dashboard_ready = True
    runtime._apply_profile_runtime_rules()


def get_profile_status(runtime: Any, *, logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    store = getattr(runtime, "_profile_store", None)
    if store is None:
        return _fallback_status()
    try:
        return store.status()
    except Exception as exc:
        if logger is not None:
            logger.debug("Failed to load profile status: %s", exc, exc_info=exc)
        return _fallback_status()


def sync_profile_scoped_group_state(
    runtime: Any,
    *,
    status: Optional[Mapping[str, Any]] = None,
    logger: Optional[logging.Logger] = None,
) -> None:
    group_state = getattr(runtime, "_plugin_group_state", None)
    if group_state is None:
        return
    if not isinstance(status, Mapping):
        status = get_profile_status(runtime, logger=logger)
    raw_profiles = status.get("profiles") if isinstance(status, Mapping) else None
    profiles = [str(item).strip() for item in raw_profiles] if isinstance(raw_profiles, list) else []
    profiles = [item for item in profiles if item]
    current_profile = str(status.get("current_profile") or DEFAULT_PROFILE_NAME).strip() or DEFAULT_PROFILE_NAME
    try:
        if hasattr(group_state, "sync_profiles"):
            group_state.sync_profiles(profiles=profiles, current_profile=current_profile)
        elif hasattr(group_state, "set_current_profile"):
            group_state.set_current_profile(current_profile)
    except Exception as exc:
        if logger is not None:
            logger.debug("Failed to sync profile-scoped group state: %s", exc, exc_info=exc)


def emit_profile_change_event(runtime: Any, *, source: str, matched_profile: Optional[str] = None) -> None:
    status = runtime.get_profile_status()
    context_summary = ",".join(sorted(runtime._profile_active_contexts, key=str.casefold))
    current_profile = str(status.get("current_profile") or "").strip()
    payload = {
        "event": "OverlayProfileChanged",
        "source": source,
        "current_profile": current_profile,
        "manual_profile": status.get("manual_profile"),
        "matched_profile": matched_profile or "",
        "context": context_summary,
        "ship_id": runtime._profile_ship_id,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    runtime._publish_payload(payload)
    if current_profile:
        runtime._publish_payload(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "event": "LegacyOverlay",
                "type": "message",
                "id": f"{COMMAND_PROFILE_STATUS_ID_PREFIX}active",
                "text": f"Active Profile: {current_profile}",
                "color": PROFILE_STATUS_MESSAGE_COLOR,
                "x": PROFILE_STATUS_MESSAGE_X,
                "y": PROFILE_STATUS_MESSAGE_Y,
                "size": PROFILE_STATUS_MESSAGE_SIZE,
                "ttl": 2.0,
            }
        )
    runtime._send_overlay_config()
    runtime._publish_payload(
        {
            "event": "OverlayOverrideReload",
            "nonce": f"profile-{int(time.time() * 1000)}",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )


def set_current_profile(
    runtime: Any,
    profile_name: str,
    *,
    source: str = "manual",
    logger: Optional[logging.Logger] = None,
) -> Dict[str, Any]:
    store = getattr(runtime, "_profile_store", None)
    if store is None:
        raise RuntimeError("Profile store is unavailable.")

    controls = getattr(runtime, "_plugin_group_controls", None)
    before_group_states: Dict[str, bool] = {}
    if controls is not None and hasattr(controls, "state_snapshot"):
        try:
            snapshot = controls.state_snapshot()
            if isinstance(snapshot, Mapping):
                before_group_states = {str(name): bool(enabled) for name, enabled in snapshot.items()}
        except Exception as exc:
            if logger is not None:
                logger.debug("Failed to capture pre-switch group visibility snapshot: %s", exc, exc_info=exc)

    before_status = store.status()
    before_current = str(before_status.get("current_profile") or "")
    status = store.set_current_profile(profile_name, source=source)
    sync_profile_scoped_group_state(runtime, status=status, logger=logger)

    if before_group_states and controls is not None and hasattr(controls, "state_snapshot"):
        try:
            after_snapshot = controls.state_snapshot()
        except Exception as exc:
            if logger is not None:
                logger.debug("Failed to capture post-switch group visibility snapshot: %s", exc, exc_info=exc)
            after_snapshot = {}
        turned_off: list[str] = []
        if isinstance(after_snapshot, Mapping):
            for group_name, after_enabled in after_snapshot.items():
                name = str(group_name)
                if not name:
                    continue
                before_enabled = bool(before_group_states.get(name, True))
                if before_enabled and not bool(after_enabled):
                    turned_off.append(name)
        if turned_off:
            runtime._publish_group_clear_event(turned_off, source=f"profile_switch:{source}")

    after_current = str(status.get("current_profile") or "")
    if before_current.casefold() != after_current.casefold():
        runtime._emit_profile_change_event(source=source)
    return status


def cycle_profile(runtime: Any, direction: int, *, source: str = "manual") -> Dict[str, Any]:
    status = runtime.get_profile_status()
    profiles_raw = status.get("profiles")
    profiles = [str(item).strip() for item in profiles_raw] if isinstance(profiles_raw, list) else []
    profiles = [item for item in profiles if item]
    if not profiles:
        raise RuntimeError("No profiles available.")
    current = str(status.get("current_profile") or profiles[0]).strip() or profiles[0]
    try:
        current_idx = next(
            idx for idx, name in enumerate(profiles) if name.casefold() == current.casefold()
        )
    except StopIteration:
        current_idx = 0
    step = -1 if int(direction) < 0 else 1
    target = profiles[(current_idx + step) % len(profiles)]
    return runtime.set_current_profile(target, source=source)


def create_profile(runtime: Any, profile_name: str, *, logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    store = getattr(runtime, "_profile_store", None)
    if store is None:
        raise RuntimeError("Profile store is unavailable.")
    status = store.create_profile(profile_name)
    group_state = getattr(runtime, "_plugin_group_state", None)
    if group_state is not None and hasattr(group_state, "create_profile"):
        try:
            group_state.create_profile(profile_name)
        except Exception as exc:
            if logger is not None:
                logger.debug("Failed to create plugin-group profile state: %s", exc, exc_info=exc)
    sync_profile_scoped_group_state(runtime, status=status, logger=logger)
    return status


def clone_profile(
    runtime: Any,
    source_profile: str,
    new_profile: str,
    *,
    logger: Optional[logging.Logger] = None,
) -> Dict[str, Any]:
    store = getattr(runtime, "_profile_store", None)
    if store is None:
        raise RuntimeError("Profile store is unavailable.")
    status = store.clone_profile(source_profile, new_profile)
    group_state = getattr(runtime, "_plugin_group_state", None)
    if group_state is not None and hasattr(group_state, "clone_profile"):
        try:
            group_state.clone_profile(source_profile, new_profile)
        except Exception as exc:
            if logger is not None:
                logger.debug("Failed to clone plugin-group profile state: %s", exc, exc_info=exc)
    sync_profile_scoped_group_state(runtime, status=status, logger=logger)
    return status


def rename_profile(
    runtime: Any,
    old_name: str,
    new_name: str,
    *,
    logger: Optional[logging.Logger] = None,
) -> Dict[str, Any]:
    store = getattr(runtime, "_profile_store", None)
    if store is None:
        raise RuntimeError("Profile store is unavailable.")
    status = store.rename_profile(old_name, new_name)
    group_state = getattr(runtime, "_plugin_group_state", None)
    if group_state is not None and hasattr(group_state, "rename_profile"):
        try:
            group_state.rename_profile(old_name, new_name)
        except Exception as exc:
            if logger is not None:
                logger.debug("Failed to rename plugin-group profile state: %s", exc, exc_info=exc)
    sync_profile_scoped_group_state(runtime, status=status, logger=logger)
    return status


def delete_profile(runtime: Any, profile_name: str, *, logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    store = getattr(runtime, "_profile_store", None)
    if store is None:
        raise RuntimeError("Profile store is unavailable.")
    before_status = store.status()
    before_current = str(before_status.get("current_profile") or "")
    status = store.delete_profile(profile_name)
    group_state = getattr(runtime, "_plugin_group_state", None)
    if group_state is not None and hasattr(group_state, "delete_profile"):
        try:
            group_state.delete_profile(profile_name)
        except Exception as exc:
            if logger is not None:
                logger.debug("Failed to delete plugin-group profile state: %s", exc, exc_info=exc)
    sync_profile_scoped_group_state(runtime, status=status, logger=logger)
    after_current = str(status.get("current_profile") or "")
    if before_current.casefold() != after_current.casefold():
        runtime._emit_profile_change_event(source="delete")
    return status


def reorder_profile(
    runtime: Any,
    profile_name: str,
    target_index: int,
    *,
    logger: Optional[logging.Logger] = None,
) -> Dict[str, Any]:
    store = getattr(runtime, "_profile_store", None)
    if store is None:
        raise RuntimeError("Profile store is unavailable.")
    status = store.reorder_profile(profile_name, target_index)
    sync_profile_scoped_group_state(runtime, status=status, logger=logger)
    return status


def set_profile_rules(runtime: Any, profile_name: str, rules: list[Mapping[str, Any]]) -> Dict[str, Any]:
    store = getattr(runtime, "_profile_store", None)
    if store is None:
        raise RuntimeError("Profile store is unavailable.")
    return store.set_profile_rules(profile_name, rules)


def apply_profile_runtime_rules(runtime: Any, *, logger: Optional[logging.Logger] = None) -> None:
    store = getattr(runtime, "_profile_store", None)
    if store is None:
        return
    if not bool(getattr(runtime, "_profile_dashboard_ready", False)):
        return
    try:
        matched_profile = store.match_profile(
            active_contexts=runtime._profile_active_contexts,
            ship_id=runtime._profile_ship_id,
        )
    except Exception as exc:
        if logger is not None:
            logger.debug("Profile rule evaluation failed: %s", exc, exc_info=exc)
        return
    normalized_match = str(matched_profile or "").strip() or None
    if normalized_match is None:
        normalized_match = DEFAULT_PROFILE_NAME
    previous_match = str(getattr(runtime, "_profile_last_matched_profile", "") or "").strip() or None
    runtime._profile_last_matched_profile = normalized_match

    # Transition-only auto-switching: unchanged matches do not re-trigger.
    if previous_match is not None and normalized_match is not None:
        if previous_match.casefold() == normalized_match.casefold():
            return

    current = str(runtime.get_profile_status().get("current_profile") or "").strip()
    if current and current.casefold() == normalized_match.casefold():
        return
    runtime.set_current_profile(normalized_match, source="auto_rule")
