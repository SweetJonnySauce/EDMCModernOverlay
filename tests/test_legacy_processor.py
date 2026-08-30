from __future__ import annotations

# ruff: noqa: E402

import pytest

from EDMCOverlay.edmcoverlay import normalise_legacy_payload
from overlay_client.legacy_processor import _hashable_payload_snapshot, process_legacy_payload
from overlay_client.legacy_store import LegacyItemStore


def test_process_message_payload():
    store = LegacyItemStore()
    changed = process_legacy_payload(
        store,
        {
            "type": "message",
            "id": "msg1",
            "text": "Hello",
            "color": "green",
            "x": 10,
            "y": 20,
            "ttl": 5,
        },
    )
    assert changed is True
    item = store.get("msg1")
    assert item is not None
    assert item.kind == "message"
    assert item.data["text"] == "Hello"
    assert item.data["color"] == "green"
    assert item.data["x"] == 10
    assert item.data["y"] == 20


def test_process_rect_payload():
    store = LegacyItemStore()
    changed = process_legacy_payload(
        store,
        {
            "type": "shape",
            "shape": "rect",
            "id": "rect1",
            "color": "#abcdef",
            "fill": "#112233",
            "x": 5,
            "y": 6,
            "w": 40,
            "h": 20,
            "ttl": 3,
        },
    )
    assert changed is True
    item = store.get("rect1")
    assert item is not None
    assert item.kind == "rect"
    assert item.data["fill"] == "#112233"
    assert item.data["w"] == 40
    assert item.data["h"] == 20
    assert "thickness" not in item.data


def test_process_rect_payload_preserves_valid_explicit_thickness():
    store = LegacyItemStore()

    changed = process_legacy_payload(
        store,
        {
            "type": "shape",
            "shape": "rect",
            "id": "rect-explicit-width",
            "color": "#abcdef",
            "fill": "#112233",
            "x": 5,
            "y": 6,
            "w": 40,
            "h": 20,
            "thickness": "3",
            "ttl": 3,
        },
    )

    assert changed is True
    item = store.get("rect-explicit-width")
    assert item is not None
    assert item.data["thickness"] == 3


def test_process_circle_payload_allows_omitted_thickness():
    store = LegacyItemStore()

    changed = process_legacy_payload(
        store,
        {
            "type": "shape",
            "shape": "circle",
            "id": "circle-default-width",
            "color": "#abcdef",
            "fill": "#112233",
            "x": 5,
            "y": 6,
            "radius": 40,
            "ttl": 3,
        },
    )

    assert changed is True
    item = store.get("circle-default-width")
    assert item is not None
    assert item.kind == "circle"
    assert "thickness" not in item.data


def test_process_normalised_raw_circle_allows_omitted_thickness():
    store = LegacyItemStore()
    payload = normalise_legacy_payload(
        {
            "shape": "circle",
            "id": "raw-circle-default-width",
            "x": 5,
            "y": 6,
            "radius": 40,
            "ttl": 3,
        },
    )

    assert payload is not None
    assert "thickness" not in payload
    assert process_legacy_payload(store, payload) is True
    item = store.get("raw-circle-default-width")
    assert item is not None
    assert "thickness" not in item.data


@pytest.mark.parametrize("invalid_thickness", [None, "not-a-number", 0, -1])
def test_invalid_explicit_rect_thickness_warns_and_preserves_existing_item(
    caplog: pytest.LogCaptureFixture,
    invalid_thickness: object,
):
    store = LegacyItemStore()
    valid_payload = {
        "type": "shape",
        "shape": "rect",
        "id": "rect-preserve",
        "x": 5,
        "y": 6,
        "w": 40,
        "h": 20,
        "thickness": 2,
    }
    assert process_legacy_payload(store, valid_payload) is True
    existing = store.get("rect-preserve")
    assert existing is not None

    invalid_payload = dict(valid_payload, thickness=invalid_thickness)
    caplog.set_level("WARNING", logger="EDMC.ModernOverlay.LegacyProcessor")

    assert process_legacy_payload(store, invalid_payload) is False
    assert store.get("rect-preserve") is existing
    assert "id=rect-preserve" in caplog.messages[-1]
    assert "thickness" in caplog.messages[-1]


def test_process_vector_payload():
    store = LegacyItemStore()
    changed = process_legacy_payload(
        store,
        {
            "type": "shape",
            "shape": "vect",
            "id": "vect1",
            "color": "red",
            "vector": [
                {"x": 0, "y": 0},
                {"x": 10, "y": 0, "color": "green"},
                {"x": 10, "y": 10, "marker": "circle", "text": "Target"},
            ],
            "ttl": 6,
        },
    )
    assert changed is True
    item = store.get("vect1")
    assert item is not None
    assert item.kind == "vector"
    data = item.data
    assert data["base_color"] == "red"
    assert len(data["points"]) == 3
    assert data["points"][1]["color"] == "green"
    assert data["points"][2]["marker"] == "circle"
    assert data["points"][2]["text"] == "Target"


def test_process_vector_single_point_marker_is_kept():
    store = LegacyItemStore()
    changed = process_legacy_payload(
        store,
        {
            "type": "shape",
            "shape": "vect",
            "id": "vect-single-marker",
            "color": "white",
            "vector": [{"x": 1, "y": 2, "marker": "cross", "text": "Here"}],
            "ttl": 6,
        },
    )
    assert changed is True
    item = store.get("vect-single-marker")
    assert item is not None
    assert item.kind == "vector"
    data = item.data
    assert data["base_color"] == "white"
    assert len(data["points"]) == 1
    assert data["points"][0]["marker"] == "cross"
    assert data["points"][0]["text"] == "Here"


def test_process_vector_single_point_without_marker_is_dropped():
    store = LegacyItemStore()
    changed = process_legacy_payload(
        store,
        {
            "type": "shape",
            "shape": "vect",
            "id": "vect-single-no-marker",
            "color": "white",
            "vector": [{"x": 1, "y": 2}],
            "ttl": 6,
        },
    )
    assert changed is False
    assert store.get("vect-single-no-marker") is None


def test_ttl_purge(monkeypatch: pytest.MonkeyPatch):
    store = LegacyItemStore()

    base_time = 1000.0
    monkeypatch.setattr("overlay_client.legacy_processor.time.monotonic", lambda: base_time)

    process_legacy_payload(
        store,
        {
            "type": "message",
            "id": "msg-ttl",
            "text": "Timed",
            "ttl": 1,
        },
    )
    item = store.get("msg-ttl")
    assert item is not None
    assert item.expiry is not None

    # Advance beyond expiry and purge
    assert store.purge_expired(base_time + 2.0) is True
    assert store.get("msg-ttl") is None


def test_ttl_zero_expires_next_purge(monkeypatch: pytest.MonkeyPatch):
    store = LegacyItemStore()

    base_time = 1000.0
    monkeypatch.setattr("overlay_client.legacy_processor.time.monotonic", lambda: base_time)

    process_legacy_payload(
        store,
        {
            "type": "message",
            "id": "msg-ttl-zero",
            "text": "Timed",
            "ttl": 0,
        },
    )
    item = store.get("msg-ttl-zero")
    assert item is not None
    assert item.expiry == base_time

    assert store.purge_expired(base_time) is False
    assert store.get("msg-ttl-zero") is not None
    assert store.purge_expired(base_time + 0.01) is True
    assert store.get("msg-ttl-zero") is None


def test_negative_ttl_expires_next_purge(monkeypatch: pytest.MonkeyPatch):
    store = LegacyItemStore()

    base_time = 2000.0
    monkeypatch.setattr("overlay_client.legacy_processor.time.monotonic", lambda: base_time)

    process_legacy_payload(
        store,
        {
            "type": "message",
            "id": "msg-ttl-negative",
            "text": "Timed",
            "ttl": -5,
        },
    )
    item = store.get("msg-ttl-negative")
    assert item is not None
    assert item.expiry == base_time

    assert store.purge_expired(base_time + 0.01) is True
    assert store.get("msg-ttl-negative") is None


def _circle_payload(**overrides):
    payload = {
        "type": "shape",
        "shape": "circle",
        "id": "circle-1",
        "color": "#80d0ff",
        "fill": "#102030",
        "x": "100",
        "y": "200",
        "radius": "50",
        "thickness": "3",
        "ttl": 4,
    }
    payload.update(overrides)
    return payload


def test_process_circle_payload_stores_normalised_first_class_item(monkeypatch: pytest.MonkeyPatch):
    store = LegacyItemStore()
    transform = {"group": "hud", "opacity": 80}
    monkeypatch.setattr("overlay_client.legacy_processor.time.monotonic", lambda: 1000.0)

    changed = process_legacy_payload(
        store,
        _circle_payload(
            plugin_name="CirclePlugin",
            __mo_transform__=transform,
            ttl=5,
        ),
    )

    assert changed is True
    item = store.get("circle-1")
    assert item is not None
    assert item.kind == "circle"
    assert item.plugin == "CirclePlugin"
    assert item.expiry == 1005.0
    assert item.data["color"] == "#80d0ff"
    assert item.data["fill"] == "#102030"
    assert item.data["x"] == 100
    assert item.data["y"] == 200
    assert item.data["radius"] == 50
    assert item.data["thickness"] == 3
    assert item.data["__mo_ttl__"] == 5
    assert item.data["__mo_transform__"] == transform
    assert item.data["__mo_transform__"] is not transform
    assert item.data["__mo_updated__"]


def test_process_circle_defaults_fill_and_replaces_same_id(monkeypatch: pytest.MonkeyPatch):
    store = LegacyItemStore()
    current_time = [1000.0]
    monkeypatch.setattr("overlay_client.legacy_processor.time.monotonic", lambda: current_time[0])

    assert process_legacy_payload(store, _circle_payload(fill=None, ttl=2)) is True
    first = store.get("circle-1")
    assert first is not None
    assert first.data["fill"] == "#00000000"
    assert first.expiry == 1002.0

    current_time[0] = 1010.0
    assert process_legacy_payload(store, _circle_payload(radius=75, color="red", ttl=6)) is True
    replacement = store.get("circle-1")
    assert replacement is not None
    assert replacement.kind == "circle"
    assert replacement.data["radius"] == 75
    assert replacement.data["color"] == "red"
    assert replacement.expiry == 1016.0


def test_circle_zero_ttl_uses_existing_next_purge_contract(monkeypatch: pytest.MonkeyPatch):
    store = LegacyItemStore()
    base_time = 1000.0
    monkeypatch.setattr("overlay_client.legacy_processor.time.monotonic", lambda: base_time)

    assert process_legacy_payload(store, _circle_payload(ttl=0)) is True
    item = store.get("circle-1")
    assert item is not None
    assert item.expiry == base_time
    assert store.purge_expired(base_time) is False
    assert store.purge_expired(base_time + 0.01) is True


@pytest.mark.parametrize(
    ("field", "invalid_value", "omit_field"),
    [
        ("radius", None, True),
        ("radius", "not-a-number", False),
        ("radius", 0, False),
        ("radius", -1, False),
        ("thickness", None, False),
        ("thickness", "not-a-number", False),
        ("thickness", 0, False),
        ("thickness", -1, False),
    ],
)
def test_invalid_circle_geometry_warns_and_preserves_existing_item(
    caplog: pytest.LogCaptureFixture,
    field: str,
    invalid_value: object,
    omit_field: bool,
):
    store = LegacyItemStore()
    traces = []
    assert process_legacy_payload(store, _circle_payload()) is True
    existing = store.get("circle-1")
    assert existing is not None

    invalid = _circle_payload(radius=70, thickness=4)
    if omit_field:
        invalid.pop(field)
    else:
        invalid[field] = invalid_value

    caplog.set_level("WARNING", logger="EDMC.ModernOverlay.LegacyProcessor")
    assert process_legacy_payload(store, invalid, trace_fn=lambda *args: traces.append(args)) is False
    assert store.get("circle-1") is existing
    assert traces == []
    warning = caplog.messages[-1]
    assert "id=circle-1" in warning
    assert field in warning
    assert f"{invalid_value!r}" in warning


@pytest.mark.parametrize(
    ("field", "invalid_value", "omit_field"),
    [
        ("radius", None, True),
        ("radius", "not-a-number", False),
        ("radius", 0, False),
        ("radius", -1, False),
        ("thickness", None, False),
        ("thickness", "not-a-number", False),
        ("thickness", 0, False),
        ("thickness", -1, False),
    ],
)
def test_raw_normalised_invalid_circle_replay_preserves_existing_drawable_item(
    caplog: pytest.LogCaptureFixture,
    field: str,
    invalid_value: object,
    omit_field: bool,
):
    store = LegacyItemStore()
    assert process_legacy_payload(store, _circle_payload()) is True
    existing = store.get("circle-1")
    assert existing is not None

    raw_payload = {
        "id": "circle-1",
        "shape": "circle",
        "color": "#ff00ff",
        "fill": "#010203",
        "x": 300,
        "y": 400,
        "radius": 70,
        "thickness": 4,
        "ttl": 9,
        "plugin": "RawCirclePlugin",
    }
    if omit_field:
        raw_payload.pop(field)
    else:
        raw_payload[field] = invalid_value
    normalised = normalise_legacy_payload(raw_payload)
    assert normalised is not None

    caplog.set_level("WARNING", logger="EDMC.ModernOverlay.LegacyProcessor")
    # Raw normalization preserves geometry; only the client rejects it before mutation.
    assert process_legacy_payload(store, normalised) is False
    assert store.get("circle-1") is existing
    warning = caplog.messages[-1]
    assert "id=circle-1" in warning
    assert field in warning
    assert f"{invalid_value!r}" in warning


@pytest.mark.parametrize(
    "change",
    [
        {"x": 101},
        {"y": 201},
        {"radius": 51},
        {"thickness": 4},
        {"color": "red"},
        {"fill": "#abcdef"},
        {"__mo_transform__": {"group": "alternate"}},
    ],
)
def test_circle_trace_snapshot_changes_for_each_rendering_field(change: dict):
    def trace_snapshot(payload):
        traces = []
        assert process_legacy_payload(
            LegacyItemStore(),
            payload,
            trace_fn=lambda *args: traces.append(args),
        ) is True
        assert len(traces) == 1
        assert traces[0][0] == "legacy_processor:dedupe_snapshot"
        return traces[0][2]["snapshot"]

    base = _circle_payload(__mo_transform__={"group": "primary"})
    changed = dict(base)
    changed.update(change)
    assert trace_snapshot(changed) != trace_snapshot(base)


def test_rectangle_and_vector_dedupe_snapshots_remain_unchanged():
    transform = {"group": "hud"}
    frozen_transform = (("group", "hud"),)
    assert _hashable_payload_snapshot(
        "shape",
        {
            "shape": "rect",
            "color": "red",
            "fill": "blue",
            "x": 1,
            "y": 2,
            "w": 3,
            "h": 4,
            "__mo_transform__": transform,
        },
    ) == ("rect", "red", "blue", 1, 2, 3, 4, frozen_transform)
    assert _hashable_payload_snapshot(
        "shape",
        {
            "shape": "rect",
            "color": "red",
            "fill": "blue",
            "x": 1,
            "y": 2,
            "w": 3,
            "h": 4,
            "thickness": 2,
            "__mo_transform__": transform,
        },
    ) != ("rect", "red", "blue", 1, 2, 3, 4, frozen_transform)
    assert _hashable_payload_snapshot(
        "shape",
        {
            "shape": "vect",
            "color": "green",
            "size": "large",
            "vector": [{"x": 1, "y": 2, "color": "red", "marker": "Circle", "text": "A", "size": "small"}],
            "__mo_transform__": transform,
        },
    ) == ("vect", "green", "large", ((1, 2, "red", "circle", "A", "small"),), frozen_transform)


def test_circle_dedupe_snapshot_freezes_transform_metadata():
    snapshot = _hashable_payload_snapshot(
        "shape",
        {
            "shape": "circle",
            "color": "red",
            "fill": "blue",
            "x": 1,
            "y": 2,
            "radius": 3,
            "thickness": 4,
            "__mo_transform__": {"group": "hud"},
        },
    )

    assert snapshot == ("circle", "red", "blue", 1, 2, 3, 4, (("group", "hud"),))
