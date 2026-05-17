from __future__ import annotations

from pathlib import Path

from overlay_client.backend import (
    HelperPresentationAction,
    HelperPresentationRequest,
    HelperRect,
    validate_gnome_shell_helper_health_payload,
    validate_gnome_shell_helper_target_payload,
)
from overlay_client.backend.helper_ipc import (
    GNOME_SHELL_HELPER_CAPABILITIES,
    GNOME_SHELL_HELPER_COORDINATE_SPACE,
    HELPER_KIND,
    HELPER_PROTOCOL,
    HELPER_VERSION,
)
from overlay_client.backend.shell_raster_frame import (
    SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS,
    SHELL_RASTER_FRAME_TRANSPORT_PNG_PATH,
    SHELL_RASTER_FRAME_UPDATE_REASON_REAL_CONTENT_MULTI_REGION,
    SHELL_RASTER_FRAME_UPDATE_REASON_REAL_CONTENT,
    SHELL_RASTER_FRAME_VERSION,
    SHELL_RASTER_REGION_MAX_COUNT,
    SHELL_RASTER_REAL_CONTENT_FRAME_VERSION,
    SHELL_RASTER_STATIC_FRAME_INSET_PX,
    ShellRasterCropContributor,
    build_multi_region_real_content_shell_raster_frame_request,
    build_real_content_shell_raster_frame_request,
    build_static_shell_raster_frame_request,
    compute_shell_raster_crop_rect,
    compute_shell_raster_crop_regions,
    ensure_shell_raster_cache_dir,
    shell_raster_cache_dir,
    shell_raster_frame_version,
    shell_raster_session_id,
    validate_shell_raster_frame_path,
)


def _health_status():
    return validate_gnome_shell_helper_health_payload(
        {
            "status": "healthy",
            "helper_kind": HELPER_KIND.value,
            "helper_version": HELPER_VERSION,
            "helper_protocol": HELPER_PROTOCOL,
            "capabilities": list(GNOME_SHELL_HELPER_CAPABILITIES),
        },
        observed_at_monotonic=100.0,
        now_monotonic=100.0,
    )


def _target_status(**target_overrides: object):
    target: dict[str, object] = {
        "targetToken": "meta:21",
        "title": "Elite - Dangerous (CLIENT)",
        "wmClass": "steam_app_359320",
        "wmClassInstance": "steam_app_359320",
        "appId": "steam_app_359320",
        "appName": "steam_app_359320",
        "pid": 9135,
        "windowType": 0,
        "frameRect": {"x": 0, "y": 0, "width": 3440, "height": 1440},
        "bufferRect": {"x": 0, "y": 0, "width": 3440, "height": 1440},
        "contentRect": {"x": 0, "y": 0, "width": 3440, "height": 1440},
        "decorationInsets": {"left": 0, "top": 0, "right": 0, "bottom": 0},
        "monitor": 0,
        "outputName": "DP-2",
        "monitorRect": {"x": 0, "y": 0, "width": 3440, "height": 1440},
        "monitorScale": 1.0,
        "hasFocus": True,
        "showingOnWorkspace": True,
        "minimized": False,
        "fullscreen": True,
        "workspace": "0",
    }
    target.update(target_overrides)
    return validate_gnome_shell_helper_target_payload(
        {
            "status": "target_found",
            "helper_kind": HELPER_KIND.value,
            "helper_version": HELPER_VERSION,
            "helper_protocol": HELPER_PROTOCOL,
            "coordinate_space": GNOME_SHELL_HELPER_COORDINATE_SPACE,
            "sequence": 3,
            "generated_at_monotonic_us": 123456,
            "generated_at_unix_ms": 1800000000000,
            "candidate_count": 1,
            "launcher_count": 0,
            "target": target,
        },
        health_status=_health_status(),
        observed_at_monotonic=200.0,
        now_monotonic=200.0,
    )


def _presentation_request() -> HelperPresentationRequest:
    return HelperPresentationRequest(
        action=HelperPresentationAction.ATTACH,
        target_token="meta:21",
        content_rect=HelperRect(0, 0, 3440, 1440),
    )


def _png_writer(path: Path, width: int, height: int) -> None:
    assert width == 3440 - (SHELL_RASTER_STATIC_FRAME_INSET_PX * 2)
    assert height == 1440 - (SHELL_RASTER_STATIC_FRAME_INSET_PX * 2)
    path.write_bytes(b"\x89PNG\r\n\x1a\nphase12-test")


def test_shell_raster_cache_prefers_xdg_runtime_dir(tmp_path: Path) -> None:
    cache_dir = shell_raster_cache_dir({"XDG_RUNTIME_DIR": str(tmp_path)})

    assert cache_dir == tmp_path / "EDMCModernOverlay" / "shell-raster"
    ensured = ensure_shell_raster_cache_dir(cache_dir)
    assert ensured.exists()
    assert oct(ensured.stat().st_mode & 0o777) == "0o700"


def test_shell_raster_path_validation_rejects_outside_and_accepts_cache_png(tmp_path: Path) -> None:
    cache_dir = ensure_shell_raster_cache_dir(tmp_path / "runtime" / "EDMCModernOverlay" / "shell-raster")
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"\x89PNG\r\n\x1a\n")
    inside = cache_dir / "frame.png"
    inside.write_bytes(b"\x89PNG\r\n\x1a\n")

    assert validate_shell_raster_frame_path(outside, cache_dir=cache_dir)[0] is False
    assert validate_shell_raster_frame_path(inside, cache_dir=cache_dir) == (True, "")


def test_static_shell_raster_request_is_borderless_fullscreen_only(tmp_path: Path) -> None:
    request = _presentation_request()

    eligible = build_static_shell_raster_frame_request(
        _target_status(),
        request,
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        writer=_png_writer,
        session_id="test-session",
    )
    windowed = build_static_shell_raster_frame_request(
        _target_status(fullscreen=False),
        request,
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        writer=_png_writer,
    )
    not_full_monitor = build_static_shell_raster_frame_request(
        _target_status(contentRect={"x": 0, "y": 29, "width": 3440, "height": 1411}),
        request,
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        writer=_png_writer,
    )

    assert eligible.eligible is True
    assert eligible.request is not None
    assert eligible.request.action == "update"
    assert eligible.request.target_rect == HelperRect(0, 0, 3440, 1440)
    assert eligible.request.frame_rect == HelperRect(10, 10, 3420, 1420)
    assert eligible.request.stale_timeout_ms == SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS
    assert eligible.request.allow_unfocused_target is False
    assert eligible.request.diagnostics is None
    assert eligible.request.frame_version.startswith(f"{SHELL_RASTER_FRAME_VERSION}:test-session:")
    assert windowed.reason == "target_not_fullscreen"
    assert not_full_monitor.reason == "target_not_borderless_full_monitor"


def test_static_shell_raster_request_debug_metrics_and_cache_reuse(tmp_path: Path) -> None:
    calls = 0

    def writer(path: Path, width: int, height: int) -> None:
        nonlocal calls
        calls += 1
        _png_writer(path, width, height)

    first = build_static_shell_raster_frame_request(
        _target_status(),
        _presentation_request(),
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        writer=writer,
        session_id="test-session",
        include_diagnostics=True,
    )
    second = build_static_shell_raster_frame_request(
        _target_status(),
        _presentation_request(),
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        writer=writer,
        session_id="test-session",
        include_diagnostics=True,
    )

    assert calls == 1
    assert first.request is not None
    assert second.request is not None
    assert first.request.signature() == second.request.signature()
    assert first.request.diagnostics is not None
    assert second.request.diagnostics is not None
    assert first.request.diagnostics["transport"] == SHELL_RASTER_FRAME_TRANSPORT_PNG_PATH
    assert first.request.diagnostics["cache_hit"] is False
    assert second.request.diagnostics["cache_hit"] is True
    assert second.request.diagnostics["encode_ms"] == 0.0
    assert second.request.diagnostics["checksum_ms"] == 0.0

    payload = second.request.to_payload()
    assert payload["shell_raster_frame_diagnostics"] == dict(second.request.diagnostics)


def test_shell_raster_crop_margin_expands_and_clamps_to_target_rect() -> None:
    crop = compute_shell_raster_crop_rect(
        HelperRect(2, 4, 20, 30),
        HelperRect(0, 0, 100, 100),
        margin_px=8,
    )
    right_edge_crop = compute_shell_raster_crop_rect(
        HelperRect(95, 95, 20, 20),
        HelperRect(0, 0, 100, 100),
        margin_px=8,
    )

    assert crop == HelperRect(0, 0, 30, 42)
    assert right_edge_crop == HelperRect(87, 87, 13, 13)


def test_shell_raster_crop_rejects_invalid_or_empty_bounds() -> None:
    assert compute_shell_raster_crop_rect(None, HelperRect(0, 0, 100, 100)) is None
    assert compute_shell_raster_crop_rect(HelperRect(0, 0, 0, 10), HelperRect(0, 0, 100, 100)) is None
    assert compute_shell_raster_crop_rect(HelperRect(100, 100, 1, 1), HelperRect(0, 0, 100, 100)) is None


def _contributor(
    bounds: tuple[float, float, float, float],
    *,
    source: str = "message",
    order: int = 0,
    item_id: str = "item",
    content_key: str | None = None,
) -> ShellRasterCropContributor:
    return ShellRasterCropContributor(
        source=source,
        plugin="BGS-Tally",
        item_id=item_id,
        group_key=("BGS-Tally", None),
        bounds=bounds,
        order=order,
        content_key=content_key if content_key is not None else f"{source}:{item_id}",
    )


def test_shell_raster_crop_regions_split_far_apart_contributors() -> None:
    regions = compute_shell_raster_crop_regions(
        [
            _contributor((10, 10, 50, 30), order=0, item_id="left"),
            _contributor((900, 700, 980, 740), order=1, item_id="right"),
        ],
        HelperRect(0, 0, 1000, 800),
    )

    assert len(regions) == 2
    assert regions[0].crop_rect == HelperRect(2, 2, 56, 36)
    assert regions[1].crop_rect == HelperRect(892, 692, 96, 56)


def test_shell_raster_crop_regions_merge_nearby_and_overlapping_contributors() -> None:
    nearby = compute_shell_raster_crop_regions(
        [
            _contributor((10, 10, 50, 30), order=0),
            _contributor((58, 12, 90, 32), order=1),
        ],
        HelperRect(0, 0, 200, 100),
    )
    overlapping = compute_shell_raster_crop_regions(
        [
            _contributor((10, 10, 50, 30), order=0),
            _contributor((40, 20, 90, 50), order=1),
        ],
        HelperRect(0, 0, 200, 100),
    )

    assert len(nearby) == 1
    assert nearby[0].crop_rect == HelperRect(2, 2, 96, 38)
    assert len(overlapping) == 1
    assert overlapping[0].crop_rect == HelperRect(2, 2, 96, 56)


def test_shell_raster_crop_regions_cap_merges_deterministically() -> None:
    contributors = [
        _contributor((index * 30.0, 10.0, index * 30.0 + 10.0, 20.0), order=index, item_id=f"item-{index}")
        for index in range(SHELL_RASTER_REGION_MAX_COUNT + 2)
    ]

    regions = compute_shell_raster_crop_regions(
        contributors,
        HelperRect(0, 0, 400, 100),
        max_regions=SHELL_RASTER_REGION_MAX_COUNT,
    )

    assert len(regions) == SHELL_RASTER_REGION_MAX_COUNT
    assert any(region.merge_reasons for region in regions)
    assert [region.region_id for region in regions] == [f"region-{index + 1:02d}" for index in range(8)]


def test_shell_raster_crop_regions_ignore_invalid_and_off_target_contributors() -> None:
    regions = compute_shell_raster_crop_regions(
        [
            _contributor((10, 10, 10, 30), order=0, item_id="zero-width"),
            _contributor((300, 300, 320, 320), order=1, item_id="off-target"),
            _contributor((20, 20, 60, 40), order=2, item_id="visible"),
        ],
        HelperRect(0, 0, 100, 100),
    )

    assert len(regions) == 1
    assert regions[0].contributors[0].item_id == "visible"


def test_shell_raster_crop_regions_preserve_genuine_full_width_region() -> None:
    regions = compute_shell_raster_crop_regions(
        [_contributor((0, 40, 1000, 42), source="vector", order=0)],
        HelperRect(0, 0, 1000, 200),
    )

    assert len(regions) == 1
    assert regions[0].crop_rect == HelperRect(0, 32, 1000, 18)


def test_real_content_shell_raster_request_is_cropped_and_diagnostic(tmp_path: Path) -> None:
    seen_crop: HelperRect | None = None

    def writer(path: Path, crop_rect: HelperRect) -> None:
        nonlocal seen_crop
        seen_crop = crop_rect
        payload = f"real:{crop_rect.x},{crop_rect.y},{crop_rect.width},{crop_rect.height}".encode()
        path.write_bytes(b"\x89PNG\r\n\x1a\n" + payload)

    result = build_real_content_shell_raster_frame_request(
        _target_status(),
        _presentation_request(),
        content_bounds=HelperRect(20, 40, 100, 60),
        writer=writer,
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        session_id="test-session",
        include_diagnostics=True,
        crop_diagnostics={
            "crop_source": "visible_paint_contributors",
            "crop_contributor_count": 1,
            "crop_largest_contributors": [
                {
                    "source": "message",
                    "plugin": "BGS-Tally",
                    "item_id": "msg-1",
                    "width": 100,
                    "height": 60,
                    "area": 6000,
                }
            ],
        },
    )

    assert result.eligible is True
    assert result.request is not None
    assert seen_crop == HelperRect(12, 32, 116, 76)
    assert result.request.frame_rect == HelperRect(12, 32, 116, 76)
    assert result.request.frame_version.startswith(f"{SHELL_RASTER_REAL_CONTENT_FRAME_VERSION}:test-session:")
    assert result.request.diagnostics is not None
    assert result.request.diagnostics["update_reason"] == SHELL_RASTER_FRAME_UPDATE_REASON_REAL_CONTENT
    assert result.request.diagnostics["frame_width"] == 116
    assert result.request.diagnostics["frame_height"] == 76
    assert result.request.diagnostics["transport"] == SHELL_RASTER_FRAME_TRANSPORT_PNG_PATH
    assert result.request.diagnostics["content_bounds"] == {"x": 20, "y": 40, "width": 100, "height": 60}
    assert result.request.diagnostics["crop_rect"] == {"x": 12, "y": 32, "width": 116, "height": 76}
    assert result.request.diagnostics["crop_margin_px"] == 8
    assert result.request.diagnostics["crop_source"] == "visible_paint_contributors"
    assert result.request.diagnostics["crop_contributor_count"] == 1
    assert result.request.diagnostics["crop_outlier"]["present"] is False


def test_real_content_shell_raster_diagnostics_flag_near_full_target_outlier(tmp_path: Path) -> None:
    def writer(path: Path, crop_rect: HelperRect) -> None:
        path.write_bytes(b"\x89PNG\r\n\x1a\nnear-full")

    result = build_real_content_shell_raster_frame_request(
        _target_status(),
        _presentation_request(),
        content_bounds=HelperRect(0, 0, 3430, 1440),
        writer=writer,
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        include_diagnostics=True,
        crop_diagnostics={
            "crop_source": "visible_paint_contributors",
            "crop_contributor_count": 1,
            "crop_largest_contributors": [
                {
                    "source": "group_background",
                    "plugin": "BGS-Tally",
                    "item_id": "",
                    "width": 3430,
                    "height": 1440,
                    "area": 4939200,
                }
            ],
        },
    )

    assert result.request is not None
    assert result.request.diagnostics is not None
    outlier = result.request.diagnostics["crop_outlier"]
    assert outlier["present"] is True
    assert outlier["largest_contributor"]["source"] == "group_background"


def test_real_content_shell_raster_identity_is_stable_for_unchanged_frame(tmp_path: Path) -> None:
    def writer(path: Path, crop_rect: HelperRect) -> None:
        path.write_bytes(b"\x89PNG\r\n\x1a\nstable-real-content")

    first = build_real_content_shell_raster_frame_request(
        _target_status(),
        _presentation_request(),
        content_bounds=HelperRect(20, 40, 100, 60),
        writer=writer,
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        session_id="test-session",
    )
    second = build_real_content_shell_raster_frame_request(
        _target_status(),
        _presentation_request(),
        content_bounds=HelperRect(20, 40, 100, 60),
        writer=writer,
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        session_id="test-session",
    )

    assert first.request is not None
    assert second.request is not None
    assert first.request.signature() == second.request.signature()


def test_multi_region_real_content_request_writes_independent_regions(tmp_path: Path) -> None:
    seen: list[tuple[str, HelperRect, str]] = []

    def writer(path: Path, crop_rect: HelperRect, region) -> None:
        seen.append((path.name, crop_rect, region.region_id))
        path.write_bytes(
            b"\x89PNG\r\n\x1a\n"
            + f"{region.region_id}:{crop_rect.x},{crop_rect.y},{crop_rect.width},{crop_rect.height}".encode()
        )

    result = build_multi_region_real_content_shell_raster_frame_request(
        _target_status(),
        _presentation_request(),
        contributors=[
            _contributor((10, 10, 50, 30), order=0, item_id="left"),
            _contributor((900, 700, 980, 740), order=1, item_id="right"),
        ],
        writer=writer,
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        session_id="test-session",
        include_diagnostics=True,
    )

    assert result.eligible is True
    assert result.request is not None
    assert len(result.request.regions) == 2
    assert seen[0] == ("real-content-region-region-01.png", HelperRect(2, 2, 56, 36), "region-01")
    assert seen[1] == ("real-content-region-region-02.png", HelperRect(892, 692, 96, 56), "region-02")
    assert result.request.frame_rect == HelperRect(0, 0, 3440, 1440)
    assert result.request.regions[0].frame_rect == HelperRect(2, 2, 56, 36)
    assert result.request.regions[1].frame_rect == HelperRect(892, 692, 96, 56)
    assert result.request.diagnostics is not None
    assert result.request.diagnostics["update_reason"] == SHELL_RASTER_FRAME_UPDATE_REASON_REAL_CONTENT_MULTI_REGION
    assert result.request.diagnostics["frame_width"] == 3440
    assert result.request.diagnostics["frame_height"] == 1440
    assert result.request.diagnostics["region_count"] == 2
    assert result.request.diagnostics["regions"][0]["region_id"] == "region-01"
    payload = result.request.to_payload()
    assert payload["shell_raster_region_count"] == 2
    assert payload["shell_raster_regions"][0]["region_id"] == "region-01"


def test_multi_region_real_content_identity_is_stable_per_unchanged_region(tmp_path: Path) -> None:
    def writer(path: Path, crop_rect: HelperRect, region) -> None:
        path.write_bytes(b"\x89PNG\r\n\x1a\n" + f"{region.region_id}:stable".encode())

    kwargs = {
        "contributors": [
            _contributor((10, 10, 50, 30), order=0, item_id="left"),
            _contributor((900, 700, 980, 740), order=1, item_id="right"),
        ],
        "writer": writer,
        "env": {"XDG_RUNTIME_DIR": str(tmp_path)},
        "session_id": "test-session",
    }

    first = build_multi_region_real_content_shell_raster_frame_request(
        _target_status(),
        _presentation_request(),
        **kwargs,
    )
    second = build_multi_region_real_content_shell_raster_frame_request(
        _target_status(),
        _presentation_request(),
        **kwargs,
    )

    assert first.request is not None
    assert second.request is not None
    assert first.request.signature() == second.request.signature()
    assert first.request.regions[0].signature() == second.request.regions[0].signature()


def test_multi_region_reuses_unchanged_cached_regions_without_writer(tmp_path: Path) -> None:
    writes: list[str] = []

    def writer(path: Path, crop_rect: HelperRect, region) -> None:
        writes.append(region.region_id)
        path.write_bytes(b"\x89PNG\r\n\x1a\n" + f"{region.region_id}:stable".encode())

    kwargs = {
        "contributors": [
            _contributor((10, 10, 50, 30), order=0, item_id="left", content_key="left-v1"),
            _contributor((900, 700, 980, 740), order=1, item_id="right", content_key="right-v1"),
        ],
        "writer": writer,
        "env": {"XDG_RUNTIME_DIR": str(tmp_path)},
        "session_id": "test-session",
        "include_diagnostics": True,
    }

    first = build_multi_region_real_content_shell_raster_frame_request(
        _target_status(),
        _presentation_request(),
        **kwargs,
    )
    writes.clear()
    second = build_multi_region_real_content_shell_raster_frame_request(
        _target_status(),
        _presentation_request(),
        **kwargs,
    )

    assert first.request is not None
    assert second.request is not None
    assert writes == []
    assert first.request.signature() == second.request.signature()
    assert second.request.diagnostics is not None
    assert second.request.diagnostics["cache_hit"] is True
    assert second.request.diagnostics["client_reused_region_count"] == 2
    assert second.request.diagnostics["client_encoded_region_count"] == 0
    assert second.request.diagnostics["client_reused_all_regions"] is True
    assert second.request.diagnostics["client_payload_reused"] is True
    assert second.request.diagnostics["client_payload_reuse_skip_reason"] == ""
    assert second.request.diagnostics["helper_call_skipped"] is False
    assert second.request.diagnostics["encode_ms"] == 0.0
    assert second.request.diagnostics["checksum_ms"] == 0.0
    assert second.request.diagnostics["client_region_build_ms"] >= 0.0
    assert second.request.diagnostics["client_region_identity_ms"] >= 0.0
    assert second.request.diagnostics["client_payload_assembly_ms"] >= 0.0
    assert second.request.diagnostics["client_diagnostics_assembly_ms"] == 0.0
    assert all(region["client_reused_region"] is True for region in second.request.diagnostics["regions"])
    assert all(region["encode_ms"] == 0.0 for region in second.request.diagnostics["regions"])


def test_multi_region_reencodes_only_changed_region(tmp_path: Path) -> None:
    writes: list[str] = []

    def writer(path: Path, crop_rect: HelperRect, region) -> None:
        writes.append(region.region_id)
        path.write_bytes(b"\x89PNG\r\n\x1a\n" + f"{region.region_id}:{len(writes)}".encode())

    base_contributors = [
        _contributor((10, 10, 50, 30), order=0, item_id="left", content_key="left-v1"),
        _contributor((900, 700, 980, 740), order=1, item_id="right", content_key="right-v1"),
    ]
    changed_contributors = [
        _contributor((10, 10, 50, 30), order=0, item_id="left", content_key="left-v2"),
        _contributor((900, 700, 980, 740), order=1, item_id="right", content_key="right-v1"),
    ]

    first = build_multi_region_real_content_shell_raster_frame_request(
        _target_status(),
        _presentation_request(),
        contributors=base_contributors,
        writer=writer,
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        session_id="test-session",
        include_diagnostics=True,
    )
    writes.clear()
    second = build_multi_region_real_content_shell_raster_frame_request(
        _target_status(),
        _presentation_request(),
        contributors=changed_contributors,
        writer=writer,
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        session_id="test-session",
        include_diagnostics=True,
    )

    assert first.request is not None
    assert second.request is not None
    assert writes == ["region-01"]
    assert second.request.diagnostics is not None
    assert second.request.diagnostics["client_reused_region_count"] == 1
    assert second.request.diagnostics["client_encoded_region_count"] == 1
    assert second.request.diagnostics["client_reused_all_regions"] is False
    assert second.request.diagnostics["client_payload_reused"] is False
    assert second.request.diagnostics["client_payload_reuse_skip_reason"] == "changed_regions"
    regions = second.request.diagnostics["regions"]
    assert regions[0]["client_reused_region"] is False
    assert regions[0]["client_reuse_skip_reason"] == "identity_changed"
    assert regions[1]["client_reused_region"] is True
    assert second.request.regions[1].signature() == first.request.regions[1].signature()


def test_multi_region_cache_invalidates_for_crop_change_missing_or_byte_change(tmp_path: Path) -> None:
    writes: list[str] = []

    def writer(path: Path, crop_rect: HelperRect, region) -> None:
        writes.append(region.region_id)
        path.write_bytes(b"\x89PNG\r\n\x1a\n" + f"{region.region_id}:{crop_rect.width}".encode())

    contributors = [_contributor((10, 10, 50, 30), order=0, item_id="left", content_key="left-v1")]
    build_multi_region_real_content_shell_raster_frame_request(
        _target_status(),
        _presentation_request(),
        contributors=contributors,
        writer=writer,
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        session_id="test-session",
    )

    writes.clear()
    crop_changed = build_multi_region_real_content_shell_raster_frame_request(
        _target_status(),
        _presentation_request(),
        contributors=[_contributor((10, 10, 60, 30), order=0, item_id="left", content_key="left-v1")],
        writer=writer,
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        session_id="test-session",
        include_diagnostics=True,
    )
    assert writes == ["region-01"]
    assert crop_changed.request is not None
    assert crop_changed.request.diagnostics is not None
    assert crop_changed.request.diagnostics["regions"][0]["client_reuse_skip_reason"] == "identity_changed"

    image_path = tmp_path / "EDMCModernOverlay" / "shell-raster" / "real-content-region-region-01.png"
    image_path.unlink()
    writes.clear()
    missing = build_multi_region_real_content_shell_raster_frame_request(
        _target_status(),
        _presentation_request(),
        contributors=[_contributor((10, 10, 60, 30), order=0, item_id="left", content_key="left-v1")],
        writer=writer,
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        session_id="test-session",
        include_diagnostics=True,
    )
    assert writes == ["region-01"]
    assert missing.request is not None
    assert missing.request.diagnostics is not None
    assert missing.request.diagnostics["regions"][0]["client_reuse_skip_reason"] == "cached_png_missing"

    image_path.write_bytes(b"\x89PNG\r\n\x1a\nchanged-size")
    writes.clear()
    byte_changed = build_multi_region_real_content_shell_raster_frame_request(
        _target_status(),
        _presentation_request(),
        contributors=[_contributor((10, 10, 60, 30), order=0, item_id="left", content_key="left-v1")],
        writer=writer,
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        session_id="test-session",
        include_diagnostics=True,
    )
    assert writes == ["region-01"]
    assert byte_changed.request is not None
    assert byte_changed.request.diagnostics is not None
    assert byte_changed.request.diagnostics["regions"][0]["client_reuse_skip_reason"] in {
        "byte_size_changed",
        "mtime_changed",
    }


def test_real_content_shell_raster_request_falls_back_when_no_visible_crop(tmp_path: Path) -> None:
    result = build_real_content_shell_raster_frame_request(
        _target_status(),
        _presentation_request(),
        content_bounds=HelperRect(0, 0, 0, 0),
        writer=lambda path, crop_rect: path.write_bytes(b"\x89PNG\r\n\x1a\n"),
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
    )

    assert result.request is None
    assert result.reason == "no_visible_content"


def test_shell_raster_frame_version_includes_session_and_sanitized_digest() -> None:
    version = shell_raster_frame_version("abc123456789xxxx", session_id="test/session:1")

    assert version == f"{SHELL_RASTER_FRAME_VERSION}:test-session-1:abc123456789"
    assert shell_raster_session_id()


def test_static_shell_raster_request_rejects_hidden_degrade_and_frame_fallback(
    tmp_path: Path,
) -> None:
    hidden = build_static_shell_raster_frame_request(
        _target_status(minimized=True),
        _presentation_request(),
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        writer=_png_writer,
    )
    degrade = build_static_shell_raster_frame_request(
        _target_status(),
        HelperPresentationRequest(action=HelperPresentationAction.DEGRADE),
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        writer=_png_writer,
    )
    fallback = build_static_shell_raster_frame_request(
        _target_status(),
        HelperPresentationRequest(
            action=HelperPresentationAction.ATTACH,
            target_token="meta:21",
            content_rect=HelperRect(0, 0, 3440, 1440),
            rect_source="frame_rect_fallback",
        ),
        env={"XDG_RUNTIME_DIR": str(tmp_path)},
        writer=_png_writer,
    )

    assert hidden.reason == "target_minimized"
    assert degrade.reason == "not_attach_action"
    assert fallback.reason == "not_content_rect_source"
