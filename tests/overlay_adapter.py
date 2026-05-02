"""Overlay adapter/capture helpers for harness-driven integration tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass
class OverlayCaptureAdapter:
    """Capture overlay payloads with a legacy-compatible adapter surface."""

    messages: list[dict[str, Any]] = field(default_factory=list)
    shapes: list[dict[str, Any]] = field(default_factory=list)
    raw_payloads: list[dict[str, Any]] = field(default_factory=list)

    def reset(self) -> None:
        self.messages.clear()
        self.shapes.clear()
        self.raw_payloads.clear()

    def connect(self) -> bool:
        return True

    def send_message(
        self,
        id: str,
        text: str,
        color: str,
        x: int,
        y: int,
        *,
        ttl: int = 0,
        size: str = "normal",
    ) -> None:
        payload = {
            "event": "LegacyOverlay",
            "type": "message",
            "id": str(id),
            "text": str(text),
            "color": str(color),
            "x": int(x),
            "y": int(y),
            "ttl": int(ttl),
            "size": str(size),
        }
        self.messages.append(payload)
        self.raw_payloads.append(dict(payload))

    def send_shape(self, **payload: Any) -> None:
        shaped = {"event": "LegacyOverlay", "type": "shape", **dict(payload)}
        self.shapes.append(shaped)
        self.raw_payloads.append(dict(shaped))

    def send_raw(self, payload: Mapping[str, Any]) -> None:
        snapshot = dict(payload)
        self.raw_payloads.append(snapshot)
        if str(snapshot.get("event") or "") == "LegacyOverlay":
            if str(snapshot.get("type") or "") == "message":
                self.messages.append(snapshot)
            elif str(snapshot.get("type") or "") == "shape":
                self.shapes.append(snapshot)

    def send_overlay_payload(self, payload: Mapping[str, Any]) -> bool:
        self.send_raw(payload)
        return True


def last_message_text(adapter: OverlayCaptureAdapter) -> str:
    if not adapter.messages:
        return ""
    return str(adapter.messages[-1].get("text") or "")
