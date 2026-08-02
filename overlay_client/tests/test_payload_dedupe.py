from __future__ import annotations

from typing import Mapping

import pytest

from overlay_client.payload_model import PayloadModel


def _trace_logger(plugin: str, item_id: str, stage: str, details: Mapping[str, object]) -> None:
    return


def test_message_dedupe_skips_identical_payload() -> None:
    model = PayloadModel(_trace_logger)
    payload = {
        "id": "msg-1",
        "type": "message",
        "text": "hello",
        "color": "white",
        "x": 10,
        "y": 20,
        "size": "normal",
    }
    first = model.ingest(payload.copy(), override_generation=1, group_label="group-a")
    second = model.ingest(payload.copy(), override_generation=1, group_label="group-a")
    assert first is True
    assert second is False


def test_message_dedupe_detects_changed_position() -> None:
    model = PayloadModel(_trace_logger)
    payload = {
        "id": "msg-2",
        "type": "message",
        "text": "hello",
        "color": "white",
        "x": 10,
        "y": 20,
        "size": "normal",
    }
    assert model.ingest(payload.copy(), override_generation=1, group_label="group-a") is True
    moved = payload.copy()
    moved["x"] = 11
    assert model.ingest(moved, override_generation=1, group_label="group-a") is True


def test_message_dedupe_detects_changed_text() -> None:
    model = PayloadModel(_trace_logger)
    payload = {
        "id": "msg-3",
        "type": "message",
        "text": "hello",
        "color": "white",
        "x": 10,
        "y": 20,
        "size": "normal",
    }
    assert model.ingest(payload.copy(), override_generation=1, group_label="group-a") is True
    changed = payload.copy()
    changed["text"] = "hello world"
    assert model.ingest(changed, override_generation=1, group_label="group-a") is True


def test_override_generation_busts_dedupe() -> None:
    model = PayloadModel(_trace_logger)
    payload = {
        "id": "msg-4",
        "type": "message",
        "text": "same",
        "color": "white",
        "x": 1,
        "y": 2,
        "size": "normal",
    }
    assert model.ingest(payload.copy(), override_generation=1, group_label="group-a") is True
    # Same payload but new override generation should not dedupe.
    assert model.ingest(payload.copy(), override_generation=2, group_label="group-a") is True


def test_dedupe_refresh_respects_ttl_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    model = PayloadModel(_trace_logger)
    payload = {
        "id": "msg-ttl-zero",
        "type": "message",
        "text": "hello",
        "color": "white",
        "x": 10,
        "y": 20,
        "size": "normal",
        "ttl": 0,
    }
    base_time = 1000.0
    monkeypatch.setattr("overlay_client.payload_model.time.monotonic", lambda: base_time)
    assert model.ingest(payload.copy(), override_generation=1, group_label="group-a") is True
    item = model.store.get("msg-ttl-zero")
    assert item is not None
    assert item.expiry == base_time

    later_time = 1000.5
    monkeypatch.setattr("overlay_client.payload_model.time.monotonic", lambda: later_time)
    assert model.ingest(payload.copy(), override_generation=1, group_label="group-a") is False
    item = model.store.get("msg-ttl-zero")
    assert item is not None
    assert item.expiry == later_time


def test_supported_payload_ttl_and_metadata_refresh_updates_lifecycle_without_visual_change(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = PayloadModel(_trace_logger)
    payload = {
        "id": "msg-lifecycle",
        "type": "message",
        "text": "same pixels",
        "color": "white",
        "x": 10,
        "y": 20,
        "size": "normal",
        "ttl": 4,
        "plugin": "PluginA",
        "meta": {"sequence": 1},
    }
    monkeypatch.setattr("overlay_client.payload_model.time.monotonic", lambda: 100.0)
    assert model.ingest(payload.copy(), override_generation=1, group_label="group-a") is True

    refreshed = payload.copy()
    refreshed["ttl"] = 9
    refreshed["meta"] = {"sequence": 2, "received_at": "later"}
    monkeypatch.setattr("overlay_client.payload_model.time.monotonic", lambda: 102.0)

    assert model.ingest(refreshed, override_generation=1, group_label="group-a") is False
    item = model.store.get("msg-lifecycle")
    assert item is not None
    assert item.expiry == 111.0
    assert item.data["__mo_ttl__"] == 9
    assert model.ingest_counts == {
        "visual_change": 1,
        "lifecycle_refresh": 1,
        "animation_bypass": 0,
        "unknown_fallback": 0,
        "rejected": 0,
    }


@pytest.mark.parametrize(
    ("payload", "field", "changed_value"),
    [
        ({"id": "msg-content", "type": "message", "text": "hello", "color": "white", "x": 1, "y": 2, "size": "normal"}, "text", "changed"),
        ({"id": "msg-style", "type": "message", "text": "hello", "color": "white", "x": 1, "y": 2, "size": "normal"}, "color", "red"),
        ({"id": "msg-x", "type": "message", "text": "hello", "color": "white", "x": 1, "y": 2, "size": "normal"}, "x", 3),
        ({"id": "msg-y", "type": "message", "text": "hello", "color": "white", "x": 1, "y": 2, "size": "normal"}, "y", 4),
        ({"id": "msg-size", "type": "message", "text": "hello", "color": "white", "x": 1, "y": 2, "size": "normal"}, "size", "large"),
        ({"id": "msg-transform", "type": "message", "text": "hello", "color": "white", "x": 1, "y": 2, "size": "normal", "__mo_transform__": {"x": 0}}, "__mo_transform__", {"x": 5}),
        ({"id": "rect-style", "type": "shape", "shape": "rect", "color": "white", "fill": "black", "x": 1, "y": 2, "w": 3, "h": 4}, "fill", "red"),
        ({"id": "rect-geometry", "type": "shape", "shape": "rect", "color": "white", "fill": "black", "x": 1, "y": 2, "w": 3, "h": 4}, "w", 8),
        ({"id": "vect-style", "type": "shape", "shape": "vect", "color": "white", "vector": [{"x": 1, "y": 2, "marker": "circle"}]}, "color", "green"),
        ({"id": "vect-content", "type": "shape", "shape": "vect", "color": "white", "vector": [{"x": 1, "y": 2, "marker": "circle"}]}, "vector", [{"x": 2, "y": 2, "marker": "circle"}]),
    ],
)
def test_supported_visual_changes_are_never_suppressed(
    payload: dict[str, object], field: str, changed_value: object
) -> None:
    model = PayloadModel(_trace_logger)
    assert model.ingest(payload.copy(), override_generation=1, group_label="group-a") is True
    changed = payload.copy()
    changed[field] = changed_value
    assert model.ingest(changed, override_generation=1, group_label="group-a") is True


@pytest.mark.parametrize(
    ("first_plugin", "first_group", "second_plugin", "second_group"),
    [
        ("PluginA", "group-a", "PluginB", "group-a"),
        ("PluginA", "group-a", "PluginA", "group-b"),
    ],
)
def test_plugin_or_resolved_group_change_busts_visual_dedupe(
    first_plugin: str,
    first_group: str,
    second_plugin: str,
    second_group: str,
) -> None:
    model = PayloadModel(_trace_logger)
    payload = {
        "id": "msg-group",
        "type": "message",
        "text": "same",
        "color": "white",
        "x": 1,
        "y": 2,
        "size": "normal",
        "plugin": first_plugin,
    }
    assert model.ingest(payload.copy(), override_generation=1, group_label=first_group) is True
    payload["plugin"] = second_plugin
    assert model.ingest(payload, override_generation=1, group_label=second_group) is True


def test_animated_supported_payload_bypasses_visual_dedupe() -> None:
    model = PayloadModel(_trace_logger)
    payload = {
        "id": "msg-animated",
        "type": "message",
        "text": "pulse",
        "color": "white",
        "x": 1,
        "y": 2,
        "size": "normal",
        "animate": True,
    }

    assert model.ingest(payload.copy(), override_generation=1, group_label="group-a") is True
    assert model.ingest(payload.copy(), override_generation=1, group_label="group-a") is True
    assert model.ingest_counts["animation_bypass"] == 2


def test_unknown_shape_uses_safe_repaint_fallback() -> None:
    model = PayloadModel(_trace_logger)
    payload = {
        "id": "future-shape",
        "type": "shape",
        "shape": "future-shape-kind",
        "color": "white",
        "metadata": {"sequence": 1},
    }

    assert model.ingest(payload.copy(), override_generation=1, group_label="group-a") is True
    assert model.ingest(payload.copy(), override_generation=1, group_label="group-a") is True
    assert model.ingest_counts["unknown_fallback"] == 2


def test_ingest_attribution_counts_saturate_without_new_reason_keys() -> None:
    model = PayloadModel(_trace_logger)
    model._ingest_counts["visual_change"] = model.INGEST_COUNT_MAX
    payload = {"id": "bounded", "type": "message", "text": "one"}

    assert model.ingest(payload, override_generation=1, group_label="group-a") is True

    assert model.ingest_counts["visual_change"] == model.INGEST_COUNT_MAX
    assert set(model.ingest_counts) == {
        "visual_change",
        "lifecycle_refresh",
        "animation_bypass",
        "unknown_fallback",
        "rejected",
    }
