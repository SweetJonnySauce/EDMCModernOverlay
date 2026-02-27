from __future__ import annotations

import importlib
import logging
import threading
from typing import Any, Callable, List, Optional, Set, Tuple

HOTKEYS_IMPORT_MODULE = "EDMC-Hotkeys.load"
HOTKEYS_REGISTRY_MODULE = "edmc_hotkeys.registry"
HOTKEYS_RETRY_DELAYS_SECONDS: Tuple[float, ...] = (0.5, 1.0, 2.0, 4.0, 8.0)
HOTKEYS_OVERLAY_ON_ACTION_ID = "Overlay On"
HOTKEYS_OVERLAY_OFF_ACTION_ID = "Overlay Off"


class HotkeysManager:
    """Manage EDMC-Hotkeys action registration and callback behavior."""

    def __init__(
        self,
        *,
        is_running: Callable[[], bool],
        get_payload_opacity: Callable[[], int],
        toggle_payload_opacity: Callable[[], None],
        logger: logging.Logger,
        plugin_name: str,
    ) -> None:
        self._is_running = is_running
        self._get_payload_opacity = get_payload_opacity
        self._toggle_payload_opacity = toggle_payload_opacity
        self._logger = logger
        self._plugin_name = plugin_name
        self._lock = threading.RLock()
        self._hotkeys_api: Optional[Any] = None
        self._retry_timer: Optional[threading.Timer] = None
        self._registered_action_ids: Set[str] = set()

    def start(self) -> bool:
        if not self._is_running():
            return False
        return self._register_hotkeys_actions(attempt_index=0)

    def stop(self) -> None:
        self._clear_retry_state()
        self._unregister_hotkeys_actions()

    def _overlay_on_callback(self, *, payload: Any = None, source: str = "hotkey", hotkey: Any = None) -> None:
        current = self._current_payload_opacity()
        if current > 0:
            self._logger.debug(
                "Hotkey Overlay On no-op: source=%s hotkey=%s payload=%s opacity=%d",
                source,
                hotkey,
                payload,
                current,
            )
            return
        self._logger.debug(
            "Hotkey Overlay On applying: source=%s hotkey=%s payload=%s opacity=%d",
            source,
            hotkey,
            payload,
            current,
        )
        try:
            self._toggle_payload_opacity()
        except Exception as exc:  # pragma: no cover - defensive guard
            self._logger.warning("Hotkey Overlay On failed: %s", exc, exc_info=exc)
            return
        self._logger.debug("Hotkey Overlay On applied: opacity=%d", self._current_payload_opacity())

    def _overlay_off_callback(self, *, payload: Any = None, source: str = "hotkey", hotkey: Any = None) -> None:
        current = self._current_payload_opacity()
        if current == 0:
            self._logger.debug(
                "Hotkey Overlay Off no-op: source=%s hotkey=%s payload=%s opacity=%d",
                source,
                hotkey,
                payload,
                current,
            )
            return
        self._logger.debug(
            "Hotkey Overlay Off applying: source=%s hotkey=%s payload=%s opacity=%d",
            source,
            hotkey,
            payload,
            current,
        )
        try:
            self._toggle_payload_opacity()
        except Exception as exc:  # pragma: no cover - defensive guard
            self._logger.warning("Hotkey Overlay Off failed: %s", exc, exc_info=exc)
            return
        self._logger.debug("Hotkey Overlay Off applied: opacity=%d", self._current_payload_opacity())

    def _current_payload_opacity(self) -> int:
        try:
            numeric = int(self._get_payload_opacity())
        except (TypeError, ValueError):
            numeric = 100
        return max(0, min(100, numeric))

    def _import_hotkeys_api(self) -> Tuple[Optional[Any], Optional[Exception]]:
        try:
            module = importlib.import_module(HOTKEYS_IMPORT_MODULE)
        except Exception as exc:  # pragma: no cover - import varies by plugin install order
            return None, exc
        return module, None

    def _build_hotkeys_actions(self) -> List[Any]:
        registry = importlib.import_module(HOTKEYS_REGISTRY_MODULE)
        action_cls = getattr(registry, "Action", None)
        if action_cls is None:
            raise RuntimeError("edmc_hotkeys.registry.Action is unavailable")
        return [
            action_cls(
                id=HOTKEYS_OVERLAY_ON_ACTION_ID,
                label="Overlay On",
                plugin=self._plugin_name,
                callback=self._overlay_on_callback,
                thread_policy="main",
                cardinality="single",
                enabled=True,
            ),
            action_cls(
                id=HOTKEYS_OVERLAY_OFF_ACTION_ID,
                label="Overlay Off",
                plugin=self._plugin_name,
                callback=self._overlay_off_callback,
                thread_policy="main",
                cardinality="single",
                enabled=True,
            ),
        ]

    def _schedule_retry(self, *, attempt_index: int, delay_seconds: float) -> None:
        with self._lock:
            if not self._is_running() or self._registered_action_ids:
                return
            if self._retry_timer is not None:
                return
            timer = threading.Timer(delay_seconds, self._retry_callback, args=(attempt_index,))
            timer.daemon = True
            self._retry_timer = timer
        timer.start()

    def _clear_retry_state(self) -> None:
        timer: Optional[threading.Timer]
        with self._lock:
            timer = self._retry_timer
            self._retry_timer = None
        if timer is not None:
            timer.cancel()

    def _retry_callback(self, attempt_index: int) -> None:
        with self._lock:
            self._retry_timer = None
        if not self._is_running():
            return
        self._register_hotkeys_actions(attempt_index=attempt_index)

    def _register_hotkeys_actions(self, *, attempt_index: int) -> bool:
        with self._lock:
            if self._registered_action_ids:
                return True
        if not self._is_running():
            return False
        hotkeys_api, import_error = self._import_hotkeys_api()
        if hotkeys_api is None:
            self._retry_or_disable(
                attempt_index=attempt_index,
                label="EDMC-Hotkeys import failed",
                detail=import_error,
            )
            return False
        try:
            actions = self._build_hotkeys_actions()
        except Exception as exc:
            self._logger.warning("Unable to build EDMC-Hotkeys actions: %s", exc, exc_info=exc)
            return False

        registered_ids: List[str] = []
        register_action = getattr(hotkeys_api, "register_action", None)
        if not callable(register_action):
            self._logger.warning("EDMC-Hotkeys API does not expose register_action; skipping hotkey integration")
            return False
        for action in actions:
            action_id = str(getattr(action, "id", "") or "")
            try:
                ok = bool(register_action(action))
            except Exception as exc:
                self._logger.warning(
                    "Failed to register EDMC-Hotkeys action %s: %s",
                    action_id or "<unknown>",
                    exc,
                    exc_info=exc,
                )
                return False
            if not ok:
                if action_id:
                    self._logger.warning("EDMC-Hotkeys rejected action registration: %s", action_id)
                else:
                    self._logger.warning("EDMC-Hotkeys rejected action registration")
                self._retry_or_disable(
                    attempt_index=attempt_index,
                    label="EDMC-Hotkeys registration retry requested",
                    detail=f"register_action returned false for {action_id or '<unknown>'}",
                )
                return False
            registered_ids.append(action_id)

        with self._lock:
            self._hotkeys_api = hotkeys_api
            self._registered_action_ids = set(registered_ids)
        self._clear_retry_state()
        self._logger.info("Registered EDMC-Hotkeys actions: %s", ", ".join(sorted(self._registered_action_ids)))
        return True

    def _unregister_hotkeys_actions(self) -> None:
        with self._lock:
            hotkeys_api = self._hotkeys_api
            action_ids = sorted(self._registered_action_ids)
            self._registered_action_ids = set()
            self._hotkeys_api = None
        if not action_ids:
            return
        unregister_action = getattr(hotkeys_api, "unregister_action", None) if hotkeys_api is not None else None
        if not callable(unregister_action):
            self._logger.debug("EDMC-Hotkeys API does not expose unregister_action; leaving registrations unmanaged")
            return
        for action_id in action_ids:
            try:
                unregister_action(action_id)
            except Exception as exc:
                self._logger.warning("Failed to unregister EDMC-Hotkeys action %s: %s", action_id, exc, exc_info=exc)

    def _retry_or_disable(self, *, attempt_index: int, label: str, detail: Any) -> None:
        max_retries = len(HOTKEYS_RETRY_DELAYS_SECONDS)
        if attempt_index < max_retries:
            delay = HOTKEYS_RETRY_DELAYS_SECONDS[attempt_index]
            next_attempt = attempt_index + 1
            self._logger.warning(
                "%s (%d/%d): %s; retrying in %.1fs",
                label,
                next_attempt,
                max_retries,
                detail,
                delay,
            )
            self._schedule_retry(attempt_index=next_attempt, delay_seconds=delay)
            return
        self._logger.warning(
            "%s after %d retries: %s; hotkey action registration disabled",
            label,
            max_retries,
            detail,
        )
