from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Optional


def _extract_json_segment(line: str) -> Optional[Dict[str, Any]]:
    start = line.find("{")
    if start < 0:
        return None
    try:
        parsed = json.loads(line[start:])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _extract_payload_object(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    raw = record.get("raw")
    if isinstance(raw, dict):
        return dict(raw)
    payload = record.get("payload")
    if isinstance(payload, dict):
        return dict(payload)
    return dict(record)


def _normalise_payload(
    payload: Dict[str, Any],
    *,
    ttl_override: Optional[int],
) -> Optional[Dict[str, Any]]:
    if ttl_override is not None:
        payload["ttl"] = int(ttl_override)

    payload_type = payload.get("type")
    if isinstance(payload_type, str) and payload_type.lower() == "legacy_clear":
        return None

    ttl_value = payload.get("ttl")
    if isinstance(ttl_value, (int, float)) and ttl_value < 0:
        return None

    event = payload.get("event")
    if not isinstance(event, str) or not event.strip():
        payload["event"] = "LegacyOverlay"

    payload_type = payload.get("type")
    if not isinstance(payload_type, str) or not payload_type.strip():
        if isinstance(payload.get("shape"), str) and str(payload.get("shape")).strip():
            payload["type"] = "shape"
        elif isinstance(payload.get("text"), str) and str(payload.get("text")).strip():
            payload["type"] = "message"

    return payload


def iter_payloads_from_log(
    log_path: Path,
    *,
    ttl_override: Optional[int] = None,
    max_payloads: int = 0,
) -> Iterator[Dict[str, Any]]:
    emitted = 0
    with log_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = _extract_json_segment(line)
            if record is None:
                continue
            payload = _extract_payload_object(record)
            normalised = _normalise_payload(payload, ttl_override=ttl_override)
            if normalised is None:
                continue
            yield normalised
            emitted += 1
            if max_payloads > 0 and emitted >= max_payloads:
                return


def load_payloads_from_log(
    log_path: Path,
    *,
    ttl_override: Optional[int] = None,
    max_payloads: int = 0,
) -> list[Dict[str, Any]]:
    return list(iter_payloads_from_log(log_path, ttl_override=ttl_override, max_payloads=max_payloads))


def payload_store_path() -> Path:
    return Path(__file__).resolve().parents[1] / "payload_store"


def sample_payload_logs() -> Iterable[Path]:
    root = payload_store_path()
    for name in ("landingpad.log", "edr_docking.log", "test-rect.log"):
        yield root / name
