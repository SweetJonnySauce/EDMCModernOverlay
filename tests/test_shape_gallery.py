from __future__ import annotations

import pytest

from utils import shape_gallery


def test_shape_gallery_covers_visual_variations_with_requested_ttl() -> None:
    payloads = shape_gallery.build_gallery_payloads(ttl=17)
    shapes = [payload for payload in payloads if payload["type"] == "shape"]

    assert payloads
    assert {payload["shape"] for payload in shapes} == {"circle", "rect"}
    assert all(payload["id"].startswith("shape-gallery-") for payload in payloads)
    assert {payload["ttl"] for payload in payloads} == {17}

    circles = [payload for payload in shapes if payload["shape"] == "circle"]
    rectangles = [payload for payload in shapes if payload["shape"] == "rect"]
    assert all("radius" in payload and "w" not in payload and "h" not in payload for payload in circles)
    assert all("w" in payload and "h" in payload for payload in rectangles)
    assert {payload["fill"] for payload in shapes} >= {"none", "#1a1a1a"}
    assert len({payload["color"] for payload in shapes}) >= 4
    explicit_thicknesses = {payload["thickness"] for payload in shapes if "thickness" in payload}
    assert len(explicit_thicknesses) >= 3
    assert any("thickness" not in payload for payload in shapes)
    assert len({(payload.get("radius"), payload.get("w"), payload.get("h")) for payload in shapes}) >= 4


def test_shape_gallery_includes_concentric_outline_circles_and_solid_fills() -> None:
    payloads = shape_gallery.build_gallery_payloads()
    concentric = [payload for payload in payloads if payload["id"].startswith("shape-gallery-circle-concentric-")]

    assert len(concentric) == 3
    assert len({(payload["x"], payload["y"]) for payload in concentric}) == 1
    assert [payload["radius"] for payload in concentric] == [140, 95, 50]
    assert all(payload["fill"] == "none" for payload in concentric)
    assert len({payload["color"] for payload in concentric}) == 3

    solid_fills = [payload for payload in payloads if payload.get("fill") in {"#1a1a1a", "#102a3a", "#163a16"}]
    assert len(solid_fills) == 3


def test_shape_gallery_includes_explicit_and_default_width_examples_for_each_shape() -> None:
    payloads_by_id = {payload["id"]: payload for payload in shape_gallery.build_gallery_payloads()}

    for shape in ("rect", "circle"):
        thin = payloads_by_id[f"shape-gallery-{shape}-thin-outline"]
        default_width = payloads_by_id[f"shape-gallery-{shape}-default-outline"]
        assert thin["shape"] == default_width["shape"] == shape
        assert thin["thickness"] == 1
        assert "thickness" not in default_width


def test_shape_gallery_labels_each_shape_with_its_variant_and_width_mode() -> None:
    payloads = shape_gallery.build_gallery_payloads(ttl=17)
    shapes = [payload for payload in payloads if payload["type"] == "shape"]
    labels_by_id = {payload["id"]: payload for payload in payloads if payload["type"] == "message"}

    assert len(labels_by_id) == len(shapes)
    for shape in shapes:
        label = labels_by_id[f"shape-gallery-label-{shape['id'].removeprefix('shape-gallery-')}"]
        assert label["ttl"] == shape["ttl"]
        assert label["size"] == "small"
        assert label["text"].startswith("Rectangle:" if shape["shape"] == "rect" else "Circle:")
        expected_width = f"thickness={shape['thickness']}" if "thickness" in shape else "default thickness"
        assert expected_width in label["text"]


def test_shape_gallery_supports_persistent_payloads() -> None:
    assert {payload["ttl"] for payload in shape_gallery.build_gallery_payloads(ttl=0)} == {0}


def test_shape_gallery_rejects_negative_ttl_before_connecting() -> None:
    with pytest.raises(SystemExit, match="zero or positive"):
        shape_gallery.main(["--ttl", "-1"])
