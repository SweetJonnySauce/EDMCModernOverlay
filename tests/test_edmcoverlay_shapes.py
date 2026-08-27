from __future__ import annotations

import pytest

from EDMCOverlay import edmcoverlay


def test_send_shape_emits_exact_circle_payload(monkeypatch):
    published = []
    monkeypatch.setattr(edmcoverlay, "send_overlay_message", lambda payload: published.append(payload) or True)

    overlay = edmcoverlay.Overlay()
    overlay.send_shape(
        "myplugin-radius",
        "circle",
        color="#80d0ff",
        fill="#1a1a1acc",
        x=100,
        y=100,
        radius=50,
        thickness=2,
        ttl=5,
    )

    assert published == [
        {
            "event": "LegacyOverlay",
            "type": "shape",
            "shape": "circle",
            "id": "myplugin-radius",
            "color": "#80d0ff",
            "fill": "#1a1a1acc",
            "x": 100,
            "y": 100,
            "radius": 50,
            "thickness": 2,
            "ttl": 5,
        }
    ]


def test_send_shape_circle_preserves_stable_id_and_ttl(monkeypatch):
    published = []
    monkeypatch.setattr(edmcoverlay, "send_overlay_message", lambda payload: published.append(payload) or True)

    overlay = edmcoverlay.Overlay()
    overlay.send_shape("stable-circle", "circle", "white", "", 1, 2, radius=3, thickness=4, ttl=5)
    overlay.send_shape("stable-circle", "circle", "white", "", 6, 7, radius=8, thickness=9, ttl=0)

    assert [(payload["id"], payload["ttl"]) for payload in published] == [
        ("stable-circle", 5),
        ("stable-circle", 0),
    ]


def test_send_shape_preserves_positional_rectangle_payload(monkeypatch):
    published = []
    monkeypatch.setattr(edmcoverlay, "send_overlay_message", lambda payload: published.append(payload) or True)

    edmcoverlay.Overlay().send_shape("legacy-rect", "rect", "#ffffff", "#000000", "10", "20", "30", "40", 4)

    assert published == [
        {
            "event": "LegacyOverlay",
            "type": "shape",
            "shape": "rect",
            "id": "legacy-rect",
            "color": "#ffffff",
            "fill": "#000000",
            "x": 10,
            "y": 20,
            "w": 30,
            "h": 40,
            "ttl": 4,
        }
    ]


def test_send_shape_emits_explicit_rectangle_thickness(monkeypatch):
    published = []
    monkeypatch.setattr(edmcoverlay, "send_overlay_message", lambda payload: published.append(payload) or True)

    edmcoverlay.Overlay().send_shape(
        "explicit-rect",
        "rect",
        color="#80d0ff",
        fill="none",
        x=100,
        y=200,
        w=300,
        h=400,
        thickness=2,
        ttl=5,
    )

    assert published[-1]["thickness"] == 2
    assert published[-1]["w"] == 300
    assert published[-1]["h"] == 400


def test_normalise_raw_circle_preserves_canonical_geometry_and_metadata():
    payload = edmcoverlay.normalise_legacy_payload(
        {
            "shape": "circle",
            "id": "circle-canonical",
            "color": "#80d0ff",
            "fill": "#1a1a1acc",
            "x": 100,
            "y": 200,
            "radius": 50,
            "thickness": 2,
            "ttl": 5,
            "plugin": "example-plugin",
        }
    )

    assert payload is not None
    assert payload["type"] == "shape"
    assert payload["shape"] == "circle"
    assert payload["id"] == "circle-canonical"
    assert payload["color"] == "#80d0ff"
    assert payload["fill"] == "#1a1a1acc"
    assert payload["x"] == 100
    assert payload["y"] == 200
    assert payload["radius"] == 50
    assert payload["thickness"] == 2
    assert payload["ttl"] == 5
    assert payload["plugin"] == "example-plugin"


@pytest.mark.parametrize(
    ("message", "radius", "thickness"),
    [
        (
            {"Shape": "circle", "Id": "circle-alias", "Radius": "invalid", "Thickness": -2},
            "invalid",
            -2,
        ),
        (
            {"shape": "circle", "id": "circle-zero", "radius": 0, "thickness": 0},
            0,
            0,
        ),
        ({"shape": "circle", "id": "circle-missing"}, None, None),
    ],
)
def test_normalise_raw_circle_preserves_aliased_and_invalid_geometry(message, radius, thickness):
    payload = edmcoverlay.normalise_legacy_payload(message)

    assert payload is not None
    assert payload["type"] == "shape"
    assert payload["radius"] == radius
    assert payload["thickness"] == thickness


def test_normalise_raw_rectangle_and_vector_contracts_are_unchanged():
    rectangle = edmcoverlay.normalise_legacy_payload(
        {
            "shape": "rect",
            "id": "legacy-rect",
            "color": "#ffffff",
            "fill": "#000000",
            "x": "10",
            "y": "20",
            "w": "30",
            "h": "40",
            "ttl": "6",
            "plugin_name": "example-plugin",
        }
    )
    vector = edmcoverlay.normalise_legacy_payload(
        {
            "shape": "vect",
            "id": "legacy-vector",
            "vector": [{"x": 1, "y": 2}, {"x": 3, "y": 4}],
            "ttl": 7,
            "Plugin": "example-plugin",
        }
    )
    rejected_vector = edmcoverlay.normalise_legacy_payload(
        {"shape": "vect", "id": "rejected-vector", "vector": [{"x": 1, "y": 2}]}
    )

    assert rectangle == {
        "type": "shape",
        "shape": "rect",
        "id": "legacy-rect",
        "color": "#ffffff",
        "fill": "#000000",
        "x": 10,
        "y": 20,
        "w": 30,
        "h": 40,
        "ttl": 6,
        "plugin": "example-plugin",
    }
    assert vector is not None
    assert vector["shape"] == "vect"
    assert vector["vector"] == [{"x": 1, "y": 2}, {"x": 3, "y": 4}]
    assert vector["ttl"] == 7
    assert vector["plugin"] == "example-plugin"
    assert rejected_vector is None


def test_normalise_raw_rectangle_preserves_explicit_thickness_only_when_supplied():
    payload = edmcoverlay.normalise_legacy_payload(
        {
            "shape": "rect",
            "id": "explicit-rect",
            "x": 10,
            "y": 20,
            "w": 30,
            "h": 40,
            "Thickness": "2",
        }
    )

    assert payload is not None
    assert payload["thickness"] == "2"
