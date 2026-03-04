from __future__ import annotations

import logging
import threading
from types import SimpleNamespace
from typing import Any, Callable, List, Optional, Set, Tuple

HOTKEYS_RETRY_DELAYS_SECONDS: Tuple[float, ...] = (0.5, 1.0, 2.0, 4.0, 8.0)
HOTKEYS_OVERLAY_ON_ACTION_ID = "edmcmodernoverlay.hotkeys.on"
HOTKEYS_OVERLAY_OFF_ACTION_ID = "edmcmodernoverlay.hotkeys.off"
HOTKEYS_LAUNCH_CONTROLLER_ACTION_ID = "edmcmodernoverlay.hotkeys.launch_controller"
HOTKEYS_LAUNCH_CONTROLLER_LABEL = "Launch Overlay Controller"


def _import_hotkeys_api_module() -> Any:
    from EDMCHotkeys import register_action

    return SimpleNamespace(register_action=register_action)


def _import_hotkeys_action_class() -> Any:
    from edmc_hotkeys.registry import Action

    return Action


class HotkeysManager:
    """Manage EDMCHotkeys action registration and callback behavior."""

    def __init__(
        self,
        *,
        is_running: Callable[[], bool],
        get_payload_opacity: Callable[[], int],
        toggle_payload_opacity: Callable[[], None],
        launch_controller: Callable[[], None],
        logger: logging.Logger,
        plugin_name: str,
    ) -> None:
        self._is_running = is_running
        self._get_payload_opacity = get_payload_opacity
        self._toggle_payload_opacity = toggle_payload_opacity
        self._launch_controller = launch_controller
        self._logger = logger
        self._plugin_name = plugin_name
        self._lock = threading.RLock()
        self._retry_timer: Optional[threading.Timer] = None
        self._registered_action_ids: Set[str] = set()

    def start(self) -> bool:
        if not self._is_running():
            return False
        return self._register_hotkeys_actions(attempt_index=0)

    def stop(self) -> None:
        self._clear_retry_state()

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

    def _launch_controller_callback(self, *, payload: Any = None, source: str = "hotkey", hotkey: Any = None) -> None:
        self._logger.debug(
            "Hotkey Launch Controller requested: source=%s hotkey=%s payload=%s",
            source,
            hotkey,
            payload,
        )
        try:
            self._launch_controller()
        except Exception as exc:  # pragma: no cover - defensive guard
            self._logger.warning("Hotkey Launch Controller failed: %s", exc, exc_info=exc)

    def _import_hotkeys_api(self) -> Tuple[Optional[Any], Optional[Exception]]:
        try:
            module = _import_hotkeys_api_module()
        except Exception as exc:  # pragma: no cover - import varies by plugin install order
            return None, exc
        return module, None

    def _build_hotkeys_actions(self) -> List[Any]:
        action_cls = _import_hotkeys_action_class()
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
            action_cls(
                id=HOTKEYS_LAUNCH_CONTROLLER_ACTION_ID,
                label=HOTKEYS_LAUNCH_CONTROLLER_LABEL,
                plugin=self._plugin_name,
                callback=self._launch_controller_callback,
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
                label="EDMCHotkeys import failed",
                detail=import_error,
            )
            return False
        try:
            actions = self._build_hotkeys_actions()
        except Exception as exc:
            self._logger.warning("Unable to build EDMCHotkeys actions: %s", exc, exc_info=exc)
            return False

        registered_ids: List[str] = []
        register_action = getattr(hotkeys_api, "register_action", None)
        if not callable(register_action):
            self._logger.warning("EDMCHotkeys API does not expose register_action; skipping hotkey integration")
            return False
        for action in actions:
            action_id = str(getattr(action, "id", "") or "")
            try:
                ok = bool(register_action(action))
            except Exception as exc:
                self._logger.warning(
                    "Failed to register EDMCHotkeys action %s: %s",
                    action_id or "<unknown>",
                    exc,
                    exc_info=exc,
                )
                return False
            if not ok:
                if action_id:
                    self._logger.warning("EDMCHotkeys rejected action registration: %s", action_id)
                else:
                    self._logger.warning("EDMCHotkeys rejected action registration")
                self._retry_or_disable(
                    attempt_index=attempt_index,
                    label="EDMCHotkeys registration retry requested",
                    detail=f"register_action returned false for {action_id or '<unknown>'}",
                )
                return False
            registered_ids.append(action_id)

        with self._lock:
            self._registered_action_ids = set(registered_ids)
        self._clear_retry_state()
        self._logger.info("Registered EDMCHotkeys actions: %s", ", ".join(sorted(self._registered_action_ids)))
        return True

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
