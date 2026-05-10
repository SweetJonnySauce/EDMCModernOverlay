"""Client-owned GNOME helper control seam for non-tracking presentation/input calls."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from .helper_ipc import (
    GNOME_SHELL_HELPER_OBJECT_PATH,
    GNOME_SHELL_HELPER_SERVICE_NAME,
    GNOME_SHELL_HELPER_SET_OVERLAY_INPUT_PASSTHROUGH_METHOD,
)

SessionBusFactory = Callable[[], Any]


@dataclass(slots=True)
class GnomeShellHelperControlClient:
    """Best-effort GNOME helper control client for overlay presentation/input toggles."""

    logger: logging.Logger
    bus_factory: SessionBusFactory | None = None
    last_error: Exception | None = field(init=False, default=None)
    _bus: Any = field(init=False, default=None, repr=False)
    _proxy: Any = field(init=False, default=None, repr=False)
    _warned_unavailable: bool = field(init=False, default=False, repr=False)

    def set_overlay_input_passthrough(self, enabled: bool) -> bool:
        """Request compositor-side overlay input passthrough and return whether it was applied."""

        proxy = self._ensure_proxy()
        if proxy is None:
            return False

        try:
            method = getattr(proxy, GNOME_SHELL_HELPER_SET_OVERLAY_INPUT_PASSTHROUGH_METHOD)
            applied = bool(method(bool(enabled)))
        except Exception as exc:
            self.last_error = exc
            self._proxy = None
            self._bus = None
            if not self._warned_unavailable:
                self.logger.debug("GNOME helper input control unavailable: %s", exc)
                self._warned_unavailable = True
            return False

        self.last_error = None
        self._warned_unavailable = False
        return applied

    def _ensure_proxy(self) -> Any | None:
        if self._proxy is not None:
            return self._proxy

        try:
            bus = self._session_bus()
            proxy = bus.get(
                GNOME_SHELL_HELPER_SERVICE_NAME,
                GNOME_SHELL_HELPER_OBJECT_PATH,
            )
        except Exception as exc:
            self.last_error = exc
            if not self._warned_unavailable:
                self.logger.debug("GNOME helper control proxy unavailable: %s", exc)
                self._warned_unavailable = True
            return None

        self._bus = bus
        self._proxy = proxy
        self.last_error = None
        return proxy

    def _session_bus(self):
        if self.bus_factory is not None:
            return self.bus_factory()

        try:
            from pydbus import SessionBus  # type: ignore
        except Exception as exc:  # pragma: no cover - dependency/runtime guard
            raise RuntimeError(f"pydbus is required for GNOME helper control: {exc}") from exc
        return SessionBus()
