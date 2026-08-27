from __future__ import annotations

import pytest

from utils import shape_gallery


def test_shape_gallery_covers_visual_variations_with_requested_ttl() -> None:
    payloads = shape_gallery.build_gallery_payloads(ttl=17)

    assert payloads
    assert {payload["shape"] for payload in payloads} == {"circle", "rect"}
    assert all(payload["type"] == "shape" for payload in payloads)
    assert all(payload["id"].startswith("shape-gallery-") for payload in payloads)
    assert {payload["ttl"] for payload in payloads} == {17}

    circles = [payload for payload in payloads if payload["shape"] == "circle"]
    rectangles = [payload for payload in payloads if payload["shape"] == "rect"]
    assert all("radius" in payload and "w" not in payload and "h" not in payload for payload in circles)
    assert all("w" in payload and "h" in payload for payload in rectangles)
    assert {payload["fill"] for payload in payloads} >= {"none", "#1a1a1a"}
    assert len({payload["color"] for payload in payloads}) >= 4
    assert len({payload["thickness"] for payload in payloads}) >= 3
    assert len({(payload.get("radius"), payload.get("w"), payload.get("h")) for payload in payloads}) >= 4


def test_shape_gallery_includes_concentric_outline_circles_and_solid_fills() -> None:
    payloads = shape_gallery.build_gallery_payloads()
    concentric = [payload for payload in payloads if payload["id"].startswith("shape-gallery-circle-concentric-")]

    assert len(concentric) == 3
    assert len({(payload["x"], payload["y"]) for payload in concentric}) == 1
    assert [payload["radius"] for payload in concentric] == [140, 95, 50]
    assert all(payload["fill"] == "none" for payload in concentric)
    assert len({payload["color"] for payload in concentric}) == 3

    solid_fills = [payload for payload in payloads if payload["fill"] in {"#1a1a1a", "#102a3a", "#163a16"}]
    assert len(solid_fills) == 3


def test_shape_gallery_supports_persistent_payloads() -> None:
    assert {payload["ttl"] for payload in shape_gallery.build_gallery_payloads(ttl=0)} == {0}


def test_shape_gallery_rejects_negative_ttl_before_connecting() -> None:
    with pytest.raises(SystemExit, match="zero or positive"):
        shape_gallery.main(["--ttl", "-1"])
