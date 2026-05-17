"""Backend-owned helpers for the GNOME Shell raster proof frame."""

from __future__ import annotations

import getpass
import hashlib
import math
import os
import tempfile
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable, Mapping, Sequence

from .helper_ipc import (
    GNOME_SHELL_HELPER_RECT_SOURCE_CONTENT,
    HelperPresentationAction,
    HelperPresentationRequest,
    HelperRasterFrameRequest,
    HelperRasterFrameRegionRequest,
    HelperRect,
    HelperTargetStatus,
)

SHELL_RASTER_FRAME_RENDERER = "gnome_shell_raster_frame"
SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS = 1500
SHELL_RASTER_FRAME_MAX_BYTES = 8 * 1024 * 1024
SHELL_RASTER_FRAME_MAX_FPS = 4
SHELL_RASTER_FRAME_VERSION = "phase13-static-pyqt-proof-v1"
SHELL_RASTER_REAL_CONTENT_FRAME_VERSION = "phase14-real-content-cropped-v1"
SHELL_RASTER_STATIC_FRAME_INSET_PX = 10
SHELL_RASTER_CONTENT_CROP_MARGIN_PX = 8
SHELL_RASTER_RUNTIME_SUBDIR = Path("EDMCModernOverlay") / "shell-raster"
SHELL_RASTER_TMP_PREFIX = "EDMCModernOverlay-shell-raster-"
SHELL_RASTER_STATIC_FRAME_NAME = "phase12-static-pyqt-proof.png"
SHELL_RASTER_REAL_CONTENT_FRAME_NAME = "real-content-cropped-overlay.png"
SHELL_RASTER_REAL_CONTENT_REGION_FRAME_NAME = "real-content-region-{region_id}.png"
_SHELL_RASTER_SESSION_ID = f"pid{os.getpid()}-{time.monotonic_ns():x}"
SHELL_RASTER_FRAME_TRANSPORT_PNG_PATH = "png_path"
SHELL_RASTER_FRAME_UPDATE_REASON_STATIC_PROOF = "phase13_static_pyqt_proof"
SHELL_RASTER_FRAME_UPDATE_REASON_REAL_CONTENT = "real_content_cropped_overlay"
SHELL_RASTER_FRAME_UPDATE_REASON_REAL_CONTENT_MULTI_REGION = "real_content_multi_region_overlay"
SHELL_RASTER_REGION_CLUSTER_DISTANCE_PX = 8
SHELL_RASTER_REGION_MAX_COUNT = 8


@dataclass(frozen=True, slots=True)
class ShellRasterCropContributor:
    """Visible paint bounds considered for Shell raster region cropping."""

    source: str
    plugin: str
    item_id: str
    group_key: tuple[str, str | None]
    bounds: tuple[float, float, float, float]
    order: int = 0
    content_key: str = ""

    @property
    def width(self) -> float:
        return max(0.0, float(self.bounds[2]) - float(self.bounds[0]))

    @property
    def height(self) -> float:
        return max(0.0, float(self.bounds[3]) - float(self.bounds[1]))

    @property
    def area(self) -> float:
        return self.width * self.height

    def to_diagnostics(self) -> dict[str, object]:
        return {
            "source": self.source,
            "plugin": self.plugin,
            "item_id": self.item_id,
            "group_key": [self.group_key[0], self.group_key[1] or ""],
            "bounds": {
                "left": round(float(self.bounds[0]), 3),
                "top": round(float(self.bounds[1]), 3),
                "right": round(float(self.bounds[2]), 3),
                "bottom": round(float(self.bounds[3]), 3),
            },
            "width": round(self.width, 3),
            "height": round(self.height, 3),
            "area": round(self.area, 3),
            "order": int(self.order),
            "content_key_prefix": str(self.content_key or "")[:12],
        }


@dataclass(frozen=True, slots=True)
class ShellRasterCropRegion:
    """One deterministic cropped raster region and its source contributors."""

    region_id: str
    content_bounds: HelperRect
    crop_rect: HelperRect
    contributors: tuple[ShellRasterCropContributor, ...]
    merge_reasons: tuple[str, ...] = ()

    def to_diagnostics(self) -> dict[str, object]:
        largest = sorted(self.contributors, key=lambda contributor: contributor.area, reverse=True)[:5]
        return {
            "region_id": self.region_id,
            "content_bounds": self.content_bounds.to_payload(),
            "crop_rect": self.crop_rect.to_payload(),
            "contributor_count": len(self.contributors),
            "largest_contributors": [contributor.to_diagnostics() for contributor in largest],
            "merge_reasons": list(self.merge_reasons),
        }


@dataclass(frozen=True, slots=True)
class ShellRasterFrameBuildResult:
    """Result of preparing an optional Shell raster proof frame."""

    request: HelperRasterFrameRequest | None = None
    eligible: bool = False
    reason: str = ""
    cache_dir: Path | None = None
    image_path: Path | None = None
    diagnostics: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class _StaticFrameCacheEntry:
    byte_size: int
    checksum: str
    mtime_ns: int


_STATIC_FRAME_CACHE: dict[tuple[str, int, int, str], _StaticFrameCacheEntry] = {}


@dataclass(frozen=True, slots=True)
class _RegionFrameCacheEntry:
    identity: str
    byte_size: int
    checksum: str
    frame_version: str
    mtime_ns: int


_MULTI_REGION_FRAME_CACHE: dict[tuple[str, str], _RegionFrameCacheEntry] = {}


@dataclass(frozen=True, slots=True)
class _PreparedRegionFrame:
    region: ShellRasterCropRegion
    image_path: Path
    frame_rect: HelperRect
    frame_version: str
    byte_size: int
    checksum: str
    client_reused_region: bool
    client_reuse_skip_reason: str
    encode_ms: float
    validate_ms: float
    checksum_ms: float


@dataclass(frozen=True, slots=True)
class _MultiRegionPayloadCacheEntry:
    identity: str
    request: HelperRasterFrameRequest


_MULTI_REGION_PAYLOAD_CACHE: dict[tuple[str, str], _MultiRegionPayloadCacheEntry] = {}


def shell_raster_cache_dir(env: Mapping[str, str] | None = None) -> Path:
    """Return the controlled cache directory for helper-readable PNG frames."""

    source = env if env is not None else os.environ
    runtime_dir = str(source.get("XDG_RUNTIME_DIR") or "").strip()
    if runtime_dir:
        return Path(runtime_dir) / SHELL_RASTER_RUNTIME_SUBDIR
    user = getpass.getuser() or str(os.getuid() if hasattr(os, "getuid") else "user")
    return Path(tempfile.gettempdir()) / f"{SHELL_RASTER_TMP_PREFIX}{user}"


def ensure_shell_raster_cache_dir(cache_dir: Path) -> Path:
    """Create the raster cache with user-only permissions where possible."""

    cache_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        cache_dir.chmod(0o700)
    except OSError:
        pass
    return cache_dir


def validate_shell_raster_frame_path(
    image_path: Path,
    *,
    cache_dir: Path,
    max_bytes: int = SHELL_RASTER_FRAME_MAX_BYTES,
) -> tuple[bool, str]:
    """Validate a PNG frame path before sending it to the helper."""

    if not image_path.is_absolute():
        return False, "invalid_path"
    cache_root = cache_dir.resolve(strict=False)
    resolved_path = image_path.resolve(strict=False)
    try:
        resolved_path.relative_to(cache_root)
    except ValueError:
        return False, "path_outside_allowed_cache_dir"
    if resolved_path.suffix.lower() != ".png":
        return False, "invalid_image_format"
    if not resolved_path.exists():
        return False, "file_missing"
    if not resolved_path.is_file():
        return False, "not_regular_file"
    try:
        byte_size = resolved_path.stat().st_size
    except OSError:
        return False, "file_missing"
    if byte_size <= 0:
        return False, "file_empty"
    if byte_size > int(max_bytes):
        return False, "file_too_large"
    return True, ""


def shell_raster_frame_checksum(image_path: Path) -> str:
    """Return a stable SHA-256 checksum for a prepared frame file."""

    digest = hashlib.sha256()
    with image_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 256), b""):
            digest.update(chunk)
    return digest.hexdigest()


def shell_raster_session_id() -> str:
    """Return the process-scoped raster proof session identifier."""

    return _SHELL_RASTER_SESSION_ID


def shell_raster_frame_version(
    checksum: str,
    *,
    session_id: str | None = None,
    prefix: str = SHELL_RASTER_FRAME_VERSION,
) -> str:
    """Return a frame version that carries proof renderer, session, and content identity."""

    session = _frame_version_component(session_id or shell_raster_session_id())
    digest = _frame_version_component(str(checksum or "")[:12]) or "no-checksum"
    return f"{_frame_version_component(prefix)}:{session}:{digest}"


def write_static_pyqt_test_frame(
    image_path: Path,
    *,
    width: int,
    height: int,
) -> None:
    """Write the Phase 12 static transparent PNG proof frame using PyQt."""

    from PyQt6.QtGui import QColor, QFont, QImage, QPainter, QPen

    image_format = getattr(QImage.Format, "Format_ARGB32")
    image = QImage(int(width), int(height), image_format)
    image.fill(QColor(0, 0, 0, 0))

    painter = QPainter(image)
    try:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(QColor(0, 255, 180, 230), 4))
        painter.drawRect(2, 2, max(1, int(width) - 4), max(1, int(height) - 4))
        painter.setPen(QPen(QColor(255, 255, 255, 235), 1))
        painter.setFont(QFont("Sans Serif", 18, QFont.Weight.Bold))
        painter.drawText(18, min(max(32, int(height) // 2), int(height) - 18), "EDMC PyQt Raster Proof")
    finally:
        painter.end()

    image_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not image.save(str(image_path), "PNG"):
        raise RuntimeError("static PyQt PNG proof frame save failed")


def build_static_shell_raster_frame_request(
    target_status: HelperTargetStatus | None,
    presentation_request: HelperPresentationRequest | None,
    *,
    env: Mapping[str, str] | None = None,
    writer: Callable[[Path, int, int], None] | None = None,
    max_bytes: int = SHELL_RASTER_FRAME_MAX_BYTES,
    stale_timeout_ms: int = SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS,
    session_id: str | None = None,
    include_diagnostics: bool = False,
) -> ShellRasterFrameBuildResult:
    """Prepare a gated static PNG frame request for borderless/full-monitor targets."""

    build_started_ns = _timer_start(include_diagnostics)
    if target_status is None or presentation_request is None:
        return ShellRasterFrameBuildResult(reason="missing_target_or_request")
    if presentation_request.action is not HelperPresentationAction.ATTACH:
        return ShellRasterFrameBuildResult(reason="not_attach_action")
    target = target_status.target if target_status.found else None
    if target is None:
        return ShellRasterFrameBuildResult(reason="target_unavailable")
    if not target.fullscreen:
        return ShellRasterFrameBuildResult(reason="target_not_fullscreen")
    if target.minimized:
        return ShellRasterFrameBuildResult(reason="target_minimized")
    if not target.showing_on_workspace:
        return ShellRasterFrameBuildResult(reason="target_not_on_current_workspace")
    if presentation_request.rect_source != GNOME_SHELL_HELPER_RECT_SOURCE_CONTENT:
        return ShellRasterFrameBuildResult(reason="not_content_rect_source")
    target_rect = target.content_rect
    monitor_rect = target.monitor_rect
    requested_rect = presentation_request.content_rect
    if not _valid_rect(target_rect) or not _valid_rect(monitor_rect) or not _valid_rect(requested_rect):
        return ShellRasterFrameBuildResult(reason="missing_rect")
    tolerance = max(0, int(presentation_request.rect_tolerance))
    if not _rects_match(target_rect, monitor_rect, tolerance=tolerance):
        return ShellRasterFrameBuildResult(reason="target_not_borderless_full_monitor")
    if not _rects_match(requested_rect, target_rect, tolerance=tolerance):
        return ShellRasterFrameBuildResult(reason="request_rect_mismatch")

    frame_rect = _static_frame_rect(target_rect)
    if frame_rect is None:
        return ShellRasterFrameBuildResult(reason="invalid_frame_rect")

    cache_dir = ensure_shell_raster_cache_dir(shell_raster_cache_dir(env))
    image_path = cache_dir / SHELL_RASTER_STATIC_FRAME_NAME
    frame_writer = writer or _write_static_pyqt_test_frame_adapter
    cache_key = _static_frame_cache_key(image_path, frame_rect)
    cache_entry = _valid_static_frame_cache_entry(image_path, cache_key, max_bytes=max_bytes)
    cache_hit = cache_entry is not None
    encode_ms = 0.0
    if cache_entry is None:
        export_started_ns = _timer_start(include_diagnostics)
        try:
            frame_writer(image_path, frame_rect.width, frame_rect.height)
        except Exception:
            diagnostics = (
                _shell_raster_frame_diagnostics(
                    frame_rect=frame_rect,
                    byte_size=0,
                    checksum="",
                    cache_hit=False,
                    encode_ms=_elapsed_ms(export_started_ns),
                    validate_ms=0.0,
                    checksum_ms=0.0,
                    build_ms=_elapsed_ms(build_started_ns),
                )
                if include_diagnostics
                else None
            )
            return ShellRasterFrameBuildResult(
                reason="frame_export_failed",
                cache_dir=cache_dir,
                image_path=image_path,
                diagnostics=diagnostics,
            )
        encode_ms = _elapsed_ms(export_started_ns)

    validate_started_ns = _timer_start(include_diagnostics)
    path_ok, path_reason = validate_shell_raster_frame_path(
        image_path,
        cache_dir=cache_dir,
        max_bytes=max_bytes,
    )
    validate_ms = _elapsed_ms(validate_started_ns)
    if not path_ok:
        diagnostics = (
            _shell_raster_frame_diagnostics(
                frame_rect=frame_rect,
                byte_size=0,
                checksum="",
                cache_hit=cache_hit,
                encode_ms=encode_ms,
                validate_ms=validate_ms,
                checksum_ms=0.0,
                build_ms=_elapsed_ms(build_started_ns),
            )
            if include_diagnostics
            else None
        )
        return ShellRasterFrameBuildResult(
            reason=path_reason,
            cache_dir=cache_dir,
            image_path=image_path,
            diagnostics=diagnostics,
        )

    stat_result = image_path.stat()
    byte_size = stat_result.st_size
    checksum_ms = 0.0
    if cache_entry is not None:
        checksum = cache_entry.checksum
    else:
        checksum_started_ns = _timer_start(include_diagnostics)
        checksum = shell_raster_frame_checksum(image_path)
        checksum_ms = _elapsed_ms(checksum_started_ns)
        _STATIC_FRAME_CACHE[cache_key] = _StaticFrameCacheEntry(
            byte_size=int(byte_size),
            checksum=checksum,
            mtime_ns=int(getattr(stat_result, "st_mtime_ns", 0)),
        )
    diagnostics = (
        _shell_raster_frame_diagnostics(
            frame_rect=frame_rect,
            byte_size=int(byte_size),
            checksum=checksum,
            cache_hit=cache_hit,
            encode_ms=encode_ms,
            validate_ms=validate_ms,
            checksum_ms=checksum_ms,
            build_ms=_elapsed_ms(build_started_ns),
        )
        if include_diagnostics
        else None
    )
    request = HelperRasterFrameRequest(
        action="update",
        frame_version=shell_raster_frame_version(checksum, session_id=session_id),
        target_token=target.target_token,
        target_rect=target_rect,
        frame_rect=frame_rect,
        scale=float(target.monitor_scale or 1.0),
        image_path=str(image_path),
        checksum=checksum,
        byte_size=int(byte_size),
        stale_timeout_ms=int(stale_timeout_ms),
        diagnostics=diagnostics,
    )
    return ShellRasterFrameBuildResult(
        request=request,
        eligible=True,
        cache_dir=cache_dir,
        image_path=image_path,
        diagnostics=diagnostics,
    )


def compute_shell_raster_crop_rect(
    content_bounds: HelperRect | None,
    target_rect: HelperRect | None,
    *,
    margin_px: int = SHELL_RASTER_CONTENT_CROP_MARGIN_PX,
) -> HelperRect | None:
    """Return a content crop expanded by margin and clamped to the target rect."""

    if not _valid_rect(content_bounds) or not _valid_rect(target_rect):
        return None

    margin = max(0, int(margin_px))
    target_left = int(target_rect.x)
    target_top = int(target_rect.y)
    target_right = target_left + int(target_rect.width)
    target_bottom = target_top + int(target_rect.height)
    content_left = int(content_bounds.x)
    content_top = int(content_bounds.y)
    content_right = content_left + int(content_bounds.width)
    content_bottom = content_top + int(content_bounds.height)
    if (
        content_right <= target_left
        or content_left >= target_right
        or content_bottom <= target_top
        or content_top >= target_bottom
    ):
        return None

    left = max(target_left, content_left - margin)
    top = max(target_top, content_top - margin)
    right = min(target_right, content_right + margin)
    bottom = min(target_bottom, content_bottom + margin)
    width = right - left
    height = bottom - top
    if width <= 0 or height <= 0:
        return None
    return HelperRect(x=left, y=top, width=width, height=height)


def compute_shell_raster_crop_regions(
    contributors: Sequence[ShellRasterCropContributor],
    target_rect: HelperRect | None,
    *,
    margin_px: int = SHELL_RASTER_CONTENT_CROP_MARGIN_PX,
    cluster_distance_px: int = SHELL_RASTER_REGION_CLUSTER_DISTANCE_PX,
    max_regions: int = SHELL_RASTER_REGION_MAX_COUNT,
) -> tuple[ShellRasterCropRegion, ...]:
    """Cluster visible paint contributors into deterministic cropped regions."""

    if not _valid_rect(target_rect):
        return ()
    valid_contributors = _visible_region_contributors(contributors, target_rect)
    if not valid_contributors:
        return ()

    clusters: list[_RegionCluster] = []
    distance = max(0, int(cluster_distance_px))
    for contributor in valid_contributors:
        cluster = _RegionCluster((contributor,), ())
        touching = [
            index
            for index, existing in enumerate(clusters)
            if _bounds_distance(existing.bounds, contributor.bounds) <= distance
        ]
        if not touching:
            clusters.append(cluster)
            continue
        merged = cluster
        for index in reversed(touching):
            merged = merged.merged(clusters.pop(index), reason="cluster_overlap_or_nearby")
        clusters.append(merged)
        clusters.sort(key=_cluster_sort_key)

    clusters = _merge_clusters_to_cap(clusters, max_regions=max_regions)
    regions: list[ShellRasterCropRegion] = []
    for index, cluster in enumerate(sorted(clusters, key=_cluster_sort_key)):
        content_bounds = _helper_rect_from_bounds(cluster.bounds)
        crop_rect = compute_shell_raster_crop_rect(content_bounds, target_rect, margin_px=margin_px)
        if crop_rect is None:
            continue
        regions.append(
            ShellRasterCropRegion(
                region_id=f"region-{index + 1:02d}",
                content_bounds=content_bounds,
                crop_rect=crop_rect,
                contributors=tuple(sorted(cluster.contributors, key=lambda item: int(item.order))),
                merge_reasons=cluster.merge_reasons,
            )
        )
    return tuple(regions)


def build_real_content_shell_raster_frame_request(
    target_status: HelperTargetStatus | None,
    presentation_request: HelperPresentationRequest | None,
    *,
    content_bounds: HelperRect | None,
    writer: Callable[[Path, HelperRect], None],
    env: Mapping[str, str] | None = None,
    crop_margin_px: int = SHELL_RASTER_CONTENT_CROP_MARGIN_PX,
    crop_diagnostics: Mapping[str, object] | None = None,
    max_bytes: int = SHELL_RASTER_FRAME_MAX_BYTES,
    stale_timeout_ms: int = SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS,
    session_id: str | None = None,
    include_diagnostics: bool = False,
) -> ShellRasterFrameBuildResult:
    """Prepare a cropped real-content PNG frame request for a borderless target."""

    build_started_ns = _timer_start(include_diagnostics)
    if target_status is None or presentation_request is None:
        return ShellRasterFrameBuildResult(reason="missing_target_or_request")
    if presentation_request.action is not HelperPresentationAction.ATTACH:
        return ShellRasterFrameBuildResult(reason="not_attach_action")
    target = target_status.target if target_status.found else None
    if target is None:
        return ShellRasterFrameBuildResult(reason="target_unavailable")
    if not target.fullscreen:
        return ShellRasterFrameBuildResult(reason="target_not_fullscreen")
    if target.minimized:
        return ShellRasterFrameBuildResult(reason="target_minimized")
    if not target.showing_on_workspace:
        return ShellRasterFrameBuildResult(reason="target_not_on_current_workspace")
    if presentation_request.rect_source != GNOME_SHELL_HELPER_RECT_SOURCE_CONTENT:
        return ShellRasterFrameBuildResult(reason="not_content_rect_source")
    target_rect = target.content_rect
    monitor_rect = target.monitor_rect
    requested_rect = presentation_request.content_rect
    if not _valid_rect(target_rect) or not _valid_rect(monitor_rect) or not _valid_rect(requested_rect):
        return ShellRasterFrameBuildResult(reason="missing_rect")
    tolerance = max(0, int(presentation_request.rect_tolerance))
    if not _rects_match(target_rect, monitor_rect, tolerance=tolerance):
        return ShellRasterFrameBuildResult(reason="target_not_borderless_full_monitor")
    if not _rects_match(requested_rect, target_rect, tolerance=tolerance):
        return ShellRasterFrameBuildResult(reason="request_rect_mismatch")

    local_target_rect = HelperRect(x=0, y=0, width=target_rect.width, height=target_rect.height)
    crop_rect = compute_shell_raster_crop_rect(
        content_bounds,
        local_target_rect,
        margin_px=crop_margin_px,
    )
    if crop_rect is None:
        return ShellRasterFrameBuildResult(reason="no_visible_content")
    crop_diagnostics_payload = (
        _shell_raster_crop_diagnostics(
            content_bounds=content_bounds,
            crop_rect=crop_rect,
            clamp_rect=local_target_rect,
            crop_margin_px=crop_margin_px,
            crop_diagnostics=crop_diagnostics,
        )
        if include_diagnostics
        else None
    )

    frame_rect = HelperRect(
        x=int(target_rect.x) + int(crop_rect.x),
        y=int(target_rect.y) + int(crop_rect.y),
        width=int(crop_rect.width),
        height=int(crop_rect.height),
    )
    cache_dir = ensure_shell_raster_cache_dir(shell_raster_cache_dir(env))
    image_path = cache_dir / SHELL_RASTER_REAL_CONTENT_FRAME_NAME
    encode_started_ns = _timer_start(include_diagnostics)
    try:
        writer(image_path, crop_rect)
    except Exception:
        diagnostics = (
            _shell_raster_frame_diagnostics(
                frame_rect=frame_rect,
                byte_size=0,
                checksum="",
                cache_hit=False,
                encode_ms=_elapsed_ms(encode_started_ns),
                validate_ms=0.0,
                checksum_ms=0.0,
                build_ms=_elapsed_ms(build_started_ns),
                update_reason=SHELL_RASTER_FRAME_UPDATE_REASON_REAL_CONTENT,
                extra=crop_diagnostics_payload,
            )
            if include_diagnostics
            else None
        )
        return ShellRasterFrameBuildResult(
            reason="frame_export_failed",
            cache_dir=cache_dir,
            image_path=image_path,
            diagnostics=diagnostics,
        )
    encode_ms = _elapsed_ms(encode_started_ns)

    validate_started_ns = _timer_start(include_diagnostics)
    path_ok, path_reason = validate_shell_raster_frame_path(
        image_path,
        cache_dir=cache_dir,
        max_bytes=max_bytes,
    )
    validate_ms = _elapsed_ms(validate_started_ns)
    if not path_ok:
        diagnostics = (
            _shell_raster_frame_diagnostics(
                frame_rect=frame_rect,
                byte_size=0,
                checksum="",
                cache_hit=False,
                encode_ms=encode_ms,
                validate_ms=validate_ms,
                checksum_ms=0.0,
                build_ms=_elapsed_ms(build_started_ns),
                update_reason=SHELL_RASTER_FRAME_UPDATE_REASON_REAL_CONTENT,
                extra=crop_diagnostics_payload,
            )
            if include_diagnostics
            else None
        )
        return ShellRasterFrameBuildResult(
            reason=path_reason,
            cache_dir=cache_dir,
            image_path=image_path,
            diagnostics=diagnostics,
        )

    stat_result = image_path.stat()
    byte_size = stat_result.st_size
    checksum_started_ns = _timer_start(include_diagnostics)
    checksum = shell_raster_frame_checksum(image_path)
    checksum_ms = _elapsed_ms(checksum_started_ns)
    diagnostics = (
        _shell_raster_frame_diagnostics(
            frame_rect=frame_rect,
            byte_size=int(byte_size),
            checksum=checksum,
            cache_hit=False,
            encode_ms=encode_ms,
            validate_ms=validate_ms,
            checksum_ms=checksum_ms,
            build_ms=_elapsed_ms(build_started_ns),
            update_reason=SHELL_RASTER_FRAME_UPDATE_REASON_REAL_CONTENT,
            extra=crop_diagnostics_payload,
        )
        if include_diagnostics
        else None
    )
    request = HelperRasterFrameRequest(
        action="update",
        frame_version=shell_raster_frame_version(
            checksum,
            session_id=session_id,
            prefix=SHELL_RASTER_REAL_CONTENT_FRAME_VERSION,
        ),
        target_token=target.target_token,
        target_rect=target_rect,
        frame_rect=frame_rect,
        scale=float(target.monitor_scale or 1.0),
        image_path=str(image_path),
        checksum=checksum,
        byte_size=int(byte_size),
        stale_timeout_ms=int(stale_timeout_ms),
        diagnostics=diagnostics,
    )
    return ShellRasterFrameBuildResult(
        request=request,
        eligible=True,
        cache_dir=cache_dir,
        image_path=image_path,
        diagnostics=diagnostics,
    )


def build_multi_region_real_content_shell_raster_frame_request(
    target_status: HelperTargetStatus | None,
    presentation_request: HelperPresentationRequest | None,
    *,
    contributors: Sequence[ShellRasterCropContributor],
    writer: Callable[[Path, HelperRect, ShellRasterCropRegion], None],
    env: Mapping[str, str] | None = None,
    crop_margin_px: int = SHELL_RASTER_CONTENT_CROP_MARGIN_PX,
    cluster_distance_px: int = SHELL_RASTER_REGION_CLUSTER_DISTANCE_PX,
    max_regions: int = SHELL_RASTER_REGION_MAX_COUNT,
    max_bytes: int = SHELL_RASTER_FRAME_MAX_BYTES,
    stale_timeout_ms: int = SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS,
    session_id: str | None = None,
    include_diagnostics: bool = False,
) -> ShellRasterFrameBuildResult:
    """Prepare cropped real-content PNG region requests for a borderless target."""

    build_started_ns = _timer_start(include_diagnostics)
    if target_status is None or presentation_request is None:
        return ShellRasterFrameBuildResult(reason="missing_target_or_request")
    if presentation_request.action is not HelperPresentationAction.ATTACH:
        return ShellRasterFrameBuildResult(reason="not_attach_action")
    target = target_status.target if target_status.found else None
    if target is None:
        return ShellRasterFrameBuildResult(reason="target_unavailable")
    if not target.fullscreen:
        return ShellRasterFrameBuildResult(reason="target_not_fullscreen")
    if target.minimized:
        return ShellRasterFrameBuildResult(reason="target_minimized")
    if not target.showing_on_workspace:
        return ShellRasterFrameBuildResult(reason="target_not_on_current_workspace")
    if presentation_request.rect_source != GNOME_SHELL_HELPER_RECT_SOURCE_CONTENT:
        return ShellRasterFrameBuildResult(reason="not_content_rect_source")
    target_rect = target.content_rect
    monitor_rect = target.monitor_rect
    requested_rect = presentation_request.content_rect
    if not _valid_rect(target_rect) or not _valid_rect(monitor_rect) or not _valid_rect(requested_rect):
        return ShellRasterFrameBuildResult(reason="missing_rect")
    tolerance = max(0, int(presentation_request.rect_tolerance))
    if not _rects_match(target_rect, monitor_rect, tolerance=tolerance):
        return ShellRasterFrameBuildResult(reason="target_not_borderless_full_monitor")
    if not _rects_match(requested_rect, target_rect, tolerance=tolerance):
        return ShellRasterFrameBuildResult(reason="request_rect_mismatch")

    region_build_started_ns = _timer_start(include_diagnostics)
    local_target_rect = HelperRect(x=0, y=0, width=target_rect.width, height=target_rect.height)
    regions = compute_shell_raster_crop_regions(
        contributors,
        local_target_rect,
        margin_px=crop_margin_px,
        cluster_distance_px=cluster_distance_px,
        max_regions=max_regions,
    )
    region_build_ms = _elapsed_ms(region_build_started_ns)
    if not regions:
        return ShellRasterFrameBuildResult(reason="no_visible_content")

    cache_dir = ensure_shell_raster_cache_dir(shell_raster_cache_dir(env))
    prepared_regions: list[_PreparedRegionFrame] = []
    total_byte_size = 0
    total_encode_ms = 0.0
    total_validate_ms = 0.0
    total_checksum_ms = 0.0
    total_region_identity_ms = 0.0
    client_encoded_region_count = 0
    client_reused_region_count = 0
    aggregate_digest = hashlib.sha256()
    first_image_path: Path | None = None

    for region in regions:
        image_path = cache_dir / SHELL_RASTER_REAL_CONTENT_REGION_FRAME_NAME.format(region_id=region.region_id)
        if first_image_path is None:
            first_image_path = image_path
        frame_rect = HelperRect(
            x=int(target_rect.x) + int(region.crop_rect.x),
            y=int(target_rect.y) + int(region.crop_rect.y),
            width=int(region.crop_rect.width),
            height=int(region.crop_rect.height),
        )
        identity_started_ns = _timer_start(include_diagnostics)
        region_identity = _multi_region_content_identity(
            region=region,
            target_rect=target_rect,
            frame_rect=frame_rect,
            scale=float(target.monitor_scale or 1.0),
        )
        total_region_identity_ms += _elapsed_ms(identity_started_ns)
        cache_key = (str(image_path), region.region_id)
        reuse_skip_reason = _multi_region_cache_skip_reason(
            image_path,
            cache_key,
            identity=region_identity,
            max_bytes=max_bytes,
        )
        cache_entry = _valid_multi_region_frame_cache_entry(
            image_path,
            cache_key,
            identity=region_identity,
            max_bytes=max_bytes,
        )
        if cache_entry is not None:
            reuse_skip_reason = ""

        encode_ms = 0.0
        validate_ms = 0.0
        checksum_ms = 0.0
        client_reused_region = cache_entry is not None
        if cache_entry is not None:
            byte_size = cache_entry.byte_size
            checksum = cache_entry.checksum
            region_version = cache_entry.frame_version
            client_reused_region_count += 1
        else:
            encode_started_ns = _timer_start(include_diagnostics)
            try:
                writer(image_path, region.crop_rect, region)
            except Exception:
                diagnostics = (
                    _shell_raster_frame_diagnostics(
                        frame_rect=frame_rect,
                        byte_size=0,
                        checksum="",
                        cache_hit=False,
                        encode_ms=_elapsed_ms(encode_started_ns),
                        validate_ms=0.0,
                        checksum_ms=0.0,
                        build_ms=_elapsed_ms(build_started_ns),
                        update_reason=SHELL_RASTER_FRAME_UPDATE_REASON_REAL_CONTENT_MULTI_REGION,
                        extra=_shell_raster_regions_diagnostics(
                            regions=regions,
                            region_diagnostics=[
                                _prepared_region_diagnostics(prepared) for prepared in prepared_regions
                            ],
                            crop_margin_px=crop_margin_px,
                            cluster_distance_px=cluster_distance_px,
                            max_regions=max_regions,
                            clamp_rect=local_target_rect,
                            client_reused_region_count=client_reused_region_count,
                            client_encoded_region_count=client_encoded_region_count,
                            client_reused_all_regions=False,
                            client_payload_reused=False,
                            client_payload_reuse_skip_reason="frame_export_failed",
                            helper_call_skipped=False,
                            region_build_ms=region_build_ms,
                            region_identity_ms=total_region_identity_ms,
                        ),
                    )
                    if include_diagnostics
                    else None
                )
                return ShellRasterFrameBuildResult(
                    reason="frame_export_failed",
                    cache_dir=cache_dir,
                    image_path=image_path,
                    diagnostics=diagnostics,
                )
            encode_ms = _elapsed_ms(encode_started_ns)
            total_encode_ms += encode_ms
            client_encoded_region_count += 1

            validate_started_ns = _timer_start(include_diagnostics)
            path_ok, path_reason = validate_shell_raster_frame_path(
                image_path,
                cache_dir=cache_dir,
                max_bytes=max_bytes,
            )
            validate_ms = _elapsed_ms(validate_started_ns)
            total_validate_ms += validate_ms
            if not path_ok:
                diagnostics = (
                    _shell_raster_frame_diagnostics(
                        frame_rect=frame_rect,
                        byte_size=0,
                        checksum="",
                        cache_hit=False,
                        encode_ms=total_encode_ms,
                        validate_ms=total_validate_ms,
                        checksum_ms=total_checksum_ms,
                        build_ms=_elapsed_ms(build_started_ns),
                        update_reason=SHELL_RASTER_FRAME_UPDATE_REASON_REAL_CONTENT_MULTI_REGION,
                        extra=_shell_raster_regions_diagnostics(
                            regions=regions,
                            region_diagnostics=[
                                _prepared_region_diagnostics(prepared) for prepared in prepared_regions
                            ],
                            crop_margin_px=crop_margin_px,
                            cluster_distance_px=cluster_distance_px,
                            max_regions=max_regions,
                            clamp_rect=local_target_rect,
                            client_reused_region_count=client_reused_region_count,
                            client_encoded_region_count=client_encoded_region_count,
                            client_reused_all_regions=False,
                            client_payload_reused=False,
                            client_payload_reuse_skip_reason=path_reason,
                            helper_call_skipped=False,
                            region_build_ms=region_build_ms,
                            region_identity_ms=total_region_identity_ms,
                        ),
                    )
                    if include_diagnostics
                    else None
                )
                return ShellRasterFrameBuildResult(
                    reason=path_reason,
                    cache_dir=cache_dir,
                    image_path=image_path,
                    diagnostics=diagnostics,
                )

            stat_result = image_path.stat()
            byte_size = int(stat_result.st_size)
            checksum_started_ns = _timer_start(include_diagnostics)
            checksum = shell_raster_frame_checksum(image_path)
            checksum_ms = _elapsed_ms(checksum_started_ns)
            total_checksum_ms += checksum_ms
            region_version = shell_raster_frame_version(
                checksum,
                session_id=session_id,
                prefix=f"{SHELL_RASTER_REAL_CONTENT_FRAME_VERSION}-{region.region_id}",
            )
            _MULTI_REGION_FRAME_CACHE[cache_key] = _RegionFrameCacheEntry(
                identity=region_identity,
                byte_size=byte_size,
                checksum=checksum,
                frame_version=region_version,
                mtime_ns=int(getattr(stat_result, "st_mtime_ns", 0)),
            )
        total_byte_size += byte_size
        prepared_regions.append(
            _PreparedRegionFrame(
                region=region,
                image_path=image_path,
                frame_rect=frame_rect,
                frame_version=region_version,
                byte_size=byte_size,
                checksum=checksum,
                client_reused_region=client_reused_region,
                client_reuse_skip_reason=reuse_skip_reason,
                encode_ms=encode_ms,
                validate_ms=validate_ms,
                checksum_ms=checksum_ms,
            )
        )
        aggregate_digest.update(region.region_id.encode("utf-8"))
        aggregate_digest.update(checksum.encode("utf-8"))
        aggregate_digest.update(str(frame_rect.to_payload()).encode("utf-8"))

    payload_assembly_started_ns = _timer_start(include_diagnostics)
    region_requests = tuple(
        _helper_raster_region_request(
            prepared,
            target_token=target.target_token,
            target_rect=target_rect,
            scale=float(target.monitor_scale or 1.0),
        )
        for prepared in prepared_regions
    )
    aggregate_region_frame_rect = _union_helper_rects(tuple(region.frame_rect for region in region_requests))
    if aggregate_region_frame_rect is None:
        return ShellRasterFrameBuildResult(reason="no_visible_content", cache_dir=cache_dir, image_path=first_image_path)
    aggregate_checksum = aggregate_digest.hexdigest()
    presentation_frame_rect = target_rect
    client_reused_all_regions = client_reused_region_count == len(regions)
    payload_identity = _multi_region_payload_identity(
        region_requests=region_requests,
        frame_rect=presentation_frame_rect,
        checksum=aggregate_checksum,
        byte_size=total_byte_size,
        stale_timeout_ms=stale_timeout_ms,
    )
    payload_cache_key = (target.target_token, str(cache_dir))
    payload_cache_entry = _MULTI_REGION_PAYLOAD_CACHE.get(payload_cache_key)
    client_payload_reused = False
    client_payload_reuse_skip_reason = "changed_regions"
    payload_assembly_ms = _elapsed_ms(payload_assembly_started_ns)
    if client_reused_all_regions:
        if payload_cache_entry is None:
            client_payload_reuse_skip_reason = "payload_cache_miss"
        elif payload_cache_entry.identity != payload_identity:
            client_payload_reuse_skip_reason = "payload_identity_changed"
        else:
            client_payload_reused = True
            client_payload_reuse_skip_reason = ""
            diagnostics = (
                _reused_multi_region_payload_diagnostics(
                    payload_cache_entry.request.diagnostics,
                    frame_rect=presentation_frame_rect,
                    byte_size=total_byte_size,
                    checksum=aggregate_checksum,
                    encode_ms=0.0,
                    validate_ms=0.0,
                    checksum_ms=0.0,
                    build_ms=_elapsed_ms(build_started_ns),
                    region_build_ms=region_build_ms,
                    region_identity_ms=total_region_identity_ms,
                    payload_assembly_ms=payload_assembly_ms,
                    client_reused_region_count=client_reused_region_count,
                    client_encoded_region_count=client_encoded_region_count,
                )
                if include_diagnostics
                else None
            )
            cached_regions = payload_cache_entry.request.regions
            if include_diagnostics and diagnostics is not None:
                raw_region_diagnostics = diagnostics.get("regions")
                if isinstance(raw_region_diagnostics, list) and len(raw_region_diagnostics) == len(cached_regions):
                    cached_regions = tuple(
                        replace(region, diagnostics=dict(raw_region_diagnostics[index]))
                        for index, region in enumerate(cached_regions)
                        if isinstance(raw_region_diagnostics[index], Mapping)
                    )
                    if len(cached_regions) != len(payload_cache_entry.request.regions):
                        cached_regions = payload_cache_entry.request.regions
            request = replace(payload_cache_entry.request, diagnostics=diagnostics, regions=cached_regions)
            _MULTI_REGION_PAYLOAD_CACHE[payload_cache_key] = _MultiRegionPayloadCacheEntry(
                identity=payload_identity,
                request=request,
            )
            return ShellRasterFrameBuildResult(
                request=request,
                eligible=True,
                cache_dir=cache_dir,
                image_path=first_image_path,
                diagnostics=diagnostics,
            )

    diagnostics_assembly_started_ns = _timer_start(include_diagnostics)
    region_diagnostics = (
        [_prepared_region_diagnostics(prepared) for prepared in prepared_regions]
        if include_diagnostics
        else []
    )
    diagnostics = (
        _shell_raster_frame_diagnostics(
            frame_rect=presentation_frame_rect,
            byte_size=total_byte_size,
            checksum=aggregate_checksum,
            cache_hit=client_reused_region_count == len(regions),
            encode_ms=total_encode_ms,
            validate_ms=total_validate_ms,
            checksum_ms=total_checksum_ms,
            build_ms=_elapsed_ms(build_started_ns),
            update_reason=SHELL_RASTER_FRAME_UPDATE_REASON_REAL_CONTENT_MULTI_REGION,
            extra=_shell_raster_regions_diagnostics(
                regions=regions,
                region_diagnostics=region_diagnostics,
                crop_margin_px=crop_margin_px,
                cluster_distance_px=cluster_distance_px,
                max_regions=max_regions,
                clamp_rect=local_target_rect,
                client_reused_region_count=client_reused_region_count,
                client_encoded_region_count=client_encoded_region_count,
                client_reused_all_regions=client_reused_all_regions,
                client_payload_reused=client_payload_reused,
                client_payload_reuse_skip_reason=client_payload_reuse_skip_reason,
                helper_call_skipped=False,
                region_build_ms=region_build_ms,
                region_identity_ms=total_region_identity_ms,
                payload_assembly_ms=payload_assembly_ms,
                diagnostics_assembly_ms=_elapsed_ms(diagnostics_assembly_started_ns),
            ),
        )
        if include_diagnostics
        else None
    )
    region_requests = tuple(
        replace(region_request, diagnostics=region_diagnostics[index] if include_diagnostics else None)
        for index, region_request in enumerate(region_requests)
    )
    request = HelperRasterFrameRequest(
        action="update",
        frame_version=shell_raster_frame_version(
            aggregate_checksum,
            session_id=session_id,
            prefix=f"{SHELL_RASTER_REAL_CONTENT_FRAME_VERSION}-multi",
        ),
        target_token=target.target_token,
        target_rect=target_rect,
        frame_rect=presentation_frame_rect,
        scale=float(target.monitor_scale or 1.0),
        image_path=str(first_image_path or ""),
        checksum=aggregate_checksum,
        byte_size=total_byte_size,
        stale_timeout_ms=int(stale_timeout_ms),
        regions=tuple(region_requests),
        diagnostics=diagnostics,
    )
    _MULTI_REGION_PAYLOAD_CACHE[payload_cache_key] = _MultiRegionPayloadCacheEntry(
        identity=payload_identity,
        request=request,
    )
    return ShellRasterFrameBuildResult(
        request=request,
        eligible=True,
        cache_dir=cache_dir,
        image_path=first_image_path,
        diagnostics=diagnostics,
    )


def _write_static_pyqt_test_frame_adapter(image_path: Path, width: int, height: int) -> None:
    write_static_pyqt_test_frame(image_path, width=width, height=height)


def _static_frame_rect(target_rect: HelperRect) -> HelperRect | None:
    inset = SHELL_RASTER_STATIC_FRAME_INSET_PX
    width = target_rect.width - (inset * 2)
    height = target_rect.height - (inset * 2)
    if width <= 0 or height <= 0:
        return None
    return HelperRect(
        x=target_rect.x + inset,
        y=target_rect.y + inset,
        width=width,
        height=height,
    )


def _valid_rect(rect: HelperRect | None) -> bool:
    return rect is not None and rect.valid


def _rects_match(left: HelperRect | None, right: HelperRect | None, *, tolerance: int) -> bool:
    if not _valid_rect(left) or not _valid_rect(right):
        return False
    return (
        abs(left.x - right.x) <= tolerance
        and abs(left.y - right.y) <= tolerance
        and abs(left.width - right.width) <= tolerance
        and abs(left.height - right.height) <= tolerance
    )


def _frame_version_component(value: str) -> str:
    text = str(value or "").strip()
    return "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in text)[:96]


def _static_frame_cache_key(image_path: Path, frame_rect: HelperRect) -> tuple[str, int, int, str]:
    return (
        str(image_path),
        int(frame_rect.width),
        int(frame_rect.height),
        SHELL_RASTER_FRAME_VERSION,
    )


def _valid_static_frame_cache_entry(
    image_path: Path,
    cache_key: tuple[str, int, int, str],
    *,
    max_bytes: int,
) -> _StaticFrameCacheEntry | None:
    entry = _STATIC_FRAME_CACHE.get(cache_key)
    if entry is None:
        return None
    try:
        stat_result = image_path.stat()
    except OSError:
        _STATIC_FRAME_CACHE.pop(cache_key, None)
        return None
    byte_size = int(stat_result.st_size)
    mtime_ns = int(getattr(stat_result, "st_mtime_ns", 0))
    if byte_size <= 0 or byte_size > int(max_bytes):
        _STATIC_FRAME_CACHE.pop(cache_key, None)
        return None
    if byte_size != entry.byte_size or mtime_ns != entry.mtime_ns:
        _STATIC_FRAME_CACHE.pop(cache_key, None)
        return None
    return entry


def _multi_region_content_identity(
    *,
    region: ShellRasterCropRegion,
    target_rect: HelperRect,
    frame_rect: HelperRect,
    scale: float,
) -> str:
    digest = hashlib.sha256()
    digest.update(region.region_id.encode("utf-8"))
    digest.update(str(region.crop_rect.to_payload()).encode("utf-8"))
    digest.update(str(region.content_bounds.to_payload()).encode("utf-8"))
    digest.update(str(frame_rect.to_payload()).encode("utf-8"))
    digest.update(str(target_rect.to_payload()).encode("utf-8"))
    digest.update(f"{float(scale):.6f}".encode("utf-8"))
    for contributor in region.contributors:
        digest.update(str(contributor.order).encode("utf-8"))
        digest.update(contributor.source.encode("utf-8"))
        digest.update(contributor.plugin.encode("utf-8"))
        digest.update(contributor.item_id.encode("utf-8"))
        digest.update(contributor.group_key[0].encode("utf-8"))
        digest.update(str(contributor.group_key[1] or "").encode("utf-8"))
        digest.update(_bounds_identity(contributor.bounds).encode("utf-8"))
        digest.update(str(contributor.content_key or "").encode("utf-8"))
    return digest.hexdigest()


def _multi_region_payload_identity(
    *,
    region_requests: Sequence[HelperRasterFrameRegionRequest],
    frame_rect: HelperRect,
    checksum: str,
    byte_size: int,
    stale_timeout_ms: int,
) -> str:
    digest = hashlib.sha256()
    digest.update(str(frame_rect.to_payload()).encode("utf-8"))
    digest.update(str(checksum or "").encode("utf-8"))
    digest.update(str(int(byte_size)).encode("utf-8"))
    digest.update(str(int(stale_timeout_ms)).encode("utf-8"))
    for region_request in region_requests:
        digest.update(str(region_request.signature()).encode("utf-8"))
    return digest.hexdigest()


def _helper_raster_region_request(
    prepared: _PreparedRegionFrame,
    *,
    target_token: str,
    target_rect: HelperRect,
    scale: float,
    diagnostics: Mapping[str, object] | None = None,
) -> HelperRasterFrameRegionRequest:
    return HelperRasterFrameRegionRequest(
        region_id=prepared.region.region_id,
        frame_version=prepared.frame_version,
        target_token=target_token,
        target_rect=target_rect,
        frame_rect=prepared.frame_rect,
        scale=float(scale),
        image_path=str(prepared.image_path),
        checksum=prepared.checksum,
        byte_size=prepared.byte_size,
        diagnostics=diagnostics,
    )


def _prepared_region_diagnostics(prepared: _PreparedRegionFrame) -> dict[str, object]:
    return {
        **prepared.region.to_diagnostics(),
        "frame_rect": prepared.frame_rect.to_payload(),
        "frame_width": int(prepared.region.crop_rect.width),
        "frame_height": int(prepared.region.crop_rect.height),
        "byte_size": prepared.byte_size,
        "checksum_prefix": prepared.checksum[:12],
        "client_reused_region": prepared.client_reused_region,
        "client_reuse_skip_reason": prepared.client_reuse_skip_reason,
        "encode_ms": round(float(prepared.encode_ms), 3),
        "validate_ms": round(float(prepared.validate_ms), 3),
        "checksum_ms": round(float(prepared.checksum_ms), 3),
    }


def _reused_multi_region_payload_diagnostics(
    cached_diagnostics: Mapping[str, object] | None,
    *,
    frame_rect: HelperRect,
    byte_size: int,
    checksum: str,
    encode_ms: float,
    validate_ms: float,
    checksum_ms: float,
    build_ms: float,
    region_build_ms: float,
    region_identity_ms: float,
    payload_assembly_ms: float,
    client_reused_region_count: int,
    client_encoded_region_count: int,
) -> dict[str, object]:
    diagnostics = _shell_raster_frame_diagnostics(
        frame_rect=frame_rect,
        byte_size=byte_size,
        checksum=checksum,
        cache_hit=True,
        encode_ms=encode_ms,
        validate_ms=validate_ms,
        checksum_ms=checksum_ms,
        build_ms=build_ms,
        update_reason=SHELL_RASTER_FRAME_UPDATE_REASON_REAL_CONTENT_MULTI_REGION,
    )
    if cached_diagnostics:
        diagnostics.update(dict(cached_diagnostics))
    diagnostics.update(
        {
            "frame_width": int(frame_rect.width),
            "frame_height": int(frame_rect.height),
            "byte_size": int(byte_size),
            "checksum_prefix": str(checksum or "")[:12],
            "cache_hit": True,
            "encode_ms": round(float(encode_ms), 3),
            "validate_ms": round(float(validate_ms), 3),
            "checksum_ms": round(float(checksum_ms), 3),
            "build_ms": round(float(build_ms), 3),
            "client_reused_region_count": int(client_reused_region_count),
            "client_encoded_region_count": int(client_encoded_region_count),
            "client_reused_all_regions": True,
            "client_payload_reused": True,
            "client_payload_reuse_skip_reason": "",
            "helper_call_skipped": False,
            "client_region_build_ms": round(float(region_build_ms), 3),
            "client_region_identity_ms": round(float(region_identity_ms), 3),
            "client_payload_assembly_ms": round(float(payload_assembly_ms), 3),
            "client_diagnostics_assembly_ms": 0.0,
        }
    )
    raw_regions = diagnostics.get("regions")
    if isinstance(raw_regions, list):
        reused_regions: list[object] = []
        for raw_region in raw_regions:
            if not isinstance(raw_region, Mapping):
                reused_regions.append(raw_region)
                continue
            region = dict(raw_region)
            region["client_reused_region"] = True
            region["client_reuse_skip_reason"] = ""
            region["encode_ms"] = 0.0
            region["validate_ms"] = 0.0
            region["checksum_ms"] = 0.0
            reused_regions.append(region)
        diagnostics["regions"] = reused_regions
    return diagnostics


def _valid_multi_region_frame_cache_entry(
    image_path: Path,
    cache_key: tuple[str, str],
    *,
    identity: str,
    max_bytes: int,
) -> _RegionFrameCacheEntry | None:
    entry = _MULTI_REGION_FRAME_CACHE.get(cache_key)
    if entry is None:
        return None
    if entry.identity != identity:
        return None
    try:
        stat_result = image_path.stat()
    except OSError:
        _MULTI_REGION_FRAME_CACHE.pop(cache_key, None)
        return None
    byte_size = int(stat_result.st_size)
    mtime_ns = int(getattr(stat_result, "st_mtime_ns", 0))
    if byte_size <= 0 or byte_size > int(max_bytes):
        _MULTI_REGION_FRAME_CACHE.pop(cache_key, None)
        return None
    if byte_size != entry.byte_size or mtime_ns != entry.mtime_ns:
        _MULTI_REGION_FRAME_CACHE.pop(cache_key, None)
        return None
    if not entry.checksum or not entry.frame_version:
        _MULTI_REGION_FRAME_CACHE.pop(cache_key, None)
        return None
    return entry


def _multi_region_cache_skip_reason(
    image_path: Path,
    cache_key: tuple[str, str],
    *,
    identity: str,
    max_bytes: int,
) -> str:
    entry = _MULTI_REGION_FRAME_CACHE.get(cache_key)
    if entry is None:
        return "cache_miss"
    if entry.identity != identity:
        return "identity_changed"
    try:
        stat_result = image_path.stat()
    except OSError:
        return "cached_png_missing"
    byte_size = int(stat_result.st_size)
    mtime_ns = int(getattr(stat_result, "st_mtime_ns", 0))
    if byte_size <= 0:
        return "cached_png_empty"
    if byte_size > int(max_bytes):
        return "cached_png_too_large"
    if byte_size != entry.byte_size:
        return "byte_size_changed"
    if mtime_ns != entry.mtime_ns:
        return "mtime_changed"
    if not entry.checksum:
        return "checksum_missing"
    if not entry.frame_version:
        return "frame_version_missing"
    return "cache_unavailable"


def _bounds_identity(bounds: tuple[float, float, float, float]) -> str:
    return ",".join(f"{float(value):.3f}" for value in bounds)


@dataclass(frozen=True, slots=True)
class _RegionCluster:
    contributors: tuple[ShellRasterCropContributor, ...]
    merge_reasons: tuple[str, ...] = ()

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        left = min(float(contributor.bounds[0]) for contributor in self.contributors)
        top = min(float(contributor.bounds[1]) for contributor in self.contributors)
        right = max(float(contributor.bounds[2]) for contributor in self.contributors)
        bottom = max(float(contributor.bounds[3]) for contributor in self.contributors)
        return (left, top, right, bottom)

    @property
    def area(self) -> float:
        bounds = self.bounds
        return max(0.0, bounds[2] - bounds[0]) * max(0.0, bounds[3] - bounds[1])

    @property
    def first_order(self) -> int:
        return min(int(contributor.order) for contributor in self.contributors)

    def merged(self, other: "_RegionCluster", *, reason: str) -> "_RegionCluster":
        contributors = tuple(sorted(self.contributors + other.contributors, key=lambda item: int(item.order)))
        reasons = tuple(dict.fromkeys(self.merge_reasons + other.merge_reasons + (reason,)))
        return _RegionCluster(contributors, reasons)


def _visible_region_contributors(
    contributors: Sequence[ShellRasterCropContributor],
    target_rect: HelperRect,
) -> tuple[ShellRasterCropContributor, ...]:
    valid: list[ShellRasterCropContributor] = []
    for index, contributor in enumerate(contributors):
        bounds = contributor.bounds
        if not _bounds_valid(bounds):
            continue
        content_bounds = _helper_rect_from_bounds(bounds)
        if compute_shell_raster_crop_rect(content_bounds, target_rect, margin_px=0) is None:
            continue
        order = int(contributor.order)
        if order == 0 and index > 0:
            contributor = ShellRasterCropContributor(
                source=contributor.source,
                plugin=contributor.plugin,
                item_id=contributor.item_id,
                group_key=contributor.group_key,
                bounds=contributor.bounds,
                order=index,
                content_key=contributor.content_key,
            )
        valid.append(contributor)
    return tuple(sorted(valid, key=lambda item: int(item.order)))


def _merge_clusters_to_cap(
    clusters: list[_RegionCluster],
    *,
    max_regions: int,
) -> list[_RegionCluster]:
    cap = max(1, int(max_regions))
    merged = list(sorted(clusters, key=_cluster_sort_key))
    while len(merged) > cap:
        left_index, right_index = _nearest_cluster_pair(merged)
        left = merged.pop(right_index)
        right = merged.pop(left_index)
        merged.append(right.merged(left, reason="merged_to_region_cap"))
        merged.sort(key=_cluster_sort_key)
    return merged


def _nearest_cluster_pair(clusters: Sequence[_RegionCluster]) -> tuple[int, int]:
    best: tuple[float, float, int, int] | None = None
    best_pair = (0, 1)
    for left_index in range(len(clusters)):
        for right_index in range(left_index + 1, len(clusters)):
            left = clusters[left_index]
            right = clusters[right_index]
            distance = _bounds_distance(left.bounds, right.bounds)
            combined_area = _union_bounds_area(left.bounds, right.bounds)
            candidate = (distance, combined_area, left.first_order, right.first_order)
            if best is None or candidate < best:
                best = candidate
                best_pair = (left_index, right_index)
    return best_pair if best is not None else (0, 1)


def _cluster_sort_key(cluster: _RegionCluster) -> tuple[int, float, float]:
    bounds = cluster.bounds
    return (cluster.first_order, float(bounds[1]), float(bounds[0]))


def _helper_rect_from_bounds(bounds: tuple[float, float, float, float]) -> HelperRect:
    left = math.floor(float(bounds[0]))
    top = math.floor(float(bounds[1]))
    right = math.ceil(float(bounds[2]))
    bottom = math.ceil(float(bounds[3]))
    return HelperRect(x=left, y=top, width=max(0, right - left), height=max(0, bottom - top))


def _bounds_distance(
    left: tuple[float, float, float, float],
    right: tuple[float, float, float, float],
) -> float:
    horizontal = max(0.0, max(float(left[0]), float(right[0])) - min(float(left[2]), float(right[2])))
    vertical = max(0.0, max(float(left[1]), float(right[1])) - min(float(left[3]), float(right[3])))
    if horizontal <= 0.0:
        return vertical
    if vertical <= 0.0:
        return horizontal
    return (horizontal * horizontal + vertical * vertical) ** 0.5


def _bounds_valid(bounds: tuple[float, float, float, float]) -> bool:
    return (
        len(bounds) == 4
        and all(math.isfinite(float(value)) for value in bounds)
        and float(bounds[2]) > float(bounds[0])
        and float(bounds[3]) > float(bounds[1])
    )


def _union_bounds_area(
    left: tuple[float, float, float, float],
    right: tuple[float, float, float, float],
) -> float:
    return (max(left[2], right[2]) - min(left[0], right[0])) * (max(left[3], right[3]) - min(left[1], right[1]))


def _union_helper_rects(rects: Sequence[HelperRect]) -> HelperRect | None:
    valid_rects = [rect for rect in rects if _valid_rect(rect)]
    if not valid_rects:
        return None
    left = min(rect.x for rect in valid_rects)
    top = min(rect.y for rect in valid_rects)
    right = max(rect.x + rect.width for rect in valid_rects)
    bottom = max(rect.y + rect.height for rect in valid_rects)
    if right <= left or bottom <= top:
        return None
    return HelperRect(left, top, right - left, bottom - top)


def _shell_raster_regions_diagnostics(
    *,
    regions: Sequence[ShellRasterCropRegion],
    region_diagnostics: Sequence[Mapping[str, object]],
    crop_margin_px: int,
    cluster_distance_px: int,
    max_regions: int,
    clamp_rect: HelperRect,
    client_reused_region_count: int = 0,
    client_encoded_region_count: int | None = None,
    client_reused_all_regions: bool = False,
    client_payload_reused: bool = False,
    client_payload_reuse_skip_reason: str = "",
    helper_call_skipped: bool = False,
    region_build_ms: float = 0.0,
    region_identity_ms: float = 0.0,
    payload_assembly_ms: float = 0.0,
    diagnostics_assembly_ms: float = 0.0,
) -> dict[str, object]:
    merged_regions = [region for region in regions if region.merge_reasons]
    encoded_count = len(regions) - int(client_reused_region_count) if client_encoded_region_count is None else int(client_encoded_region_count)
    return {
        "region_count": len(regions),
        "regions": [dict(region) for region in region_diagnostics],
        "region_crop_rects": [region.crop_rect.to_payload() for region in regions],
        "region_content_bounds": [region.content_bounds.to_payload() for region in regions],
        "region_contributor_counts": [len(region.contributors) for region in regions],
        "client_reused_region_count": int(client_reused_region_count),
        "client_encoded_region_count": encoded_count,
        "client_reused_all_regions": bool(client_reused_all_regions),
        "client_payload_reused": bool(client_payload_reused),
        "client_payload_reuse_skip_reason": str(client_payload_reuse_skip_reason or ""),
        "helper_call_skipped": bool(helper_call_skipped),
        "client_region_build_ms": round(float(region_build_ms), 3),
        "client_region_identity_ms": round(float(region_identity_ms), 3),
        "client_payload_assembly_ms": round(float(payload_assembly_ms), 3),
        "client_diagnostics_assembly_ms": round(float(diagnostics_assembly_ms), 3),
        "region_merge_count": len(merged_regions),
        "region_merge_reasons": [
            {"region_id": region.region_id, "reasons": list(region.merge_reasons)} for region in merged_regions
        ],
        "crop_margin_px": max(0, int(crop_margin_px)),
        "cluster_distance_px": max(0, int(cluster_distance_px)),
        "max_regions": max(1, int(max_regions)),
        "crop_clamp_rect": clamp_rect.to_payload(),
    }


def _shell_raster_frame_diagnostics(
    *,
    frame_rect: HelperRect,
    byte_size: int,
    checksum: str,
    cache_hit: bool,
    encode_ms: float,
    validate_ms: float,
    checksum_ms: float,
    build_ms: float,
    update_reason: str = SHELL_RASTER_FRAME_UPDATE_REASON_STATIC_PROOF,
    extra: Mapping[str, object] | None = None,
) -> dict[str, object]:
    diagnostics: dict[str, object] = {
        "schema": 1,
        "renderer": SHELL_RASTER_FRAME_RENDERER,
        "transport": SHELL_RASTER_FRAME_TRANSPORT_PNG_PATH,
        "update_reason": update_reason,
        "frame_width": int(frame_rect.width),
        "frame_height": int(frame_rect.height),
        "byte_size": int(byte_size),
        "checksum_prefix": str(checksum or "")[:12],
        "cache_hit": bool(cache_hit),
        "encode_ms": round(float(encode_ms), 3),
        "validate_ms": round(float(validate_ms), 3),
        "checksum_ms": round(float(checksum_ms), 3),
        "build_ms": round(float(build_ms), 3),
        "transfer_ms": None,
        "transfer_observable": False,
        "dropped_frames": 0,
        "throttled_frames": 0,
    }
    if extra:
        diagnostics.update(dict(extra))
    return diagnostics


def _shell_raster_crop_diagnostics(
    *,
    content_bounds: HelperRect,
    crop_rect: HelperRect,
    clamp_rect: HelperRect,
    crop_margin_px: int,
    crop_diagnostics: Mapping[str, object] | None,
) -> dict[str, object]:
    diagnostics = dict(crop_diagnostics or {})
    diagnostics.update(
        {
            "content_bounds": content_bounds.to_payload(),
            "crop_rect": crop_rect.to_payload(),
            "crop_margin_px": max(0, int(crop_margin_px)),
            "crop_clamp_rect": clamp_rect.to_payload(),
        }
    )
    diagnostics["crop_outlier"] = _shell_raster_crop_outlier(
        crop_rect=crop_rect,
        clamp_rect=clamp_rect,
        crop_diagnostics=diagnostics,
    )
    return diagnostics


def _shell_raster_crop_outlier(
    *,
    crop_rect: HelperRect,
    clamp_rect: HelperRect,
    crop_diagnostics: Mapping[str, object],
) -> dict[str, object]:
    clamp_area = max(1, int(clamp_rect.width) * int(clamp_rect.height))
    crop_area = max(0, int(crop_rect.width) * int(crop_rect.height))
    crop_area_ratio = crop_area / float(clamp_area)
    crop_width_ratio = int(crop_rect.width) / float(max(1, int(clamp_rect.width)))
    crop_height_ratio = int(crop_rect.height) / float(max(1, int(clamp_rect.height)))
    present = crop_area_ratio >= 0.75 or crop_width_ratio >= 0.9 or crop_height_ratio >= 0.9
    largest: object = None
    raw_largest = crop_diagnostics.get("crop_largest_contributors")
    if isinstance(raw_largest, list) and raw_largest:
        largest = raw_largest[0]
    return {
        "present": bool(present),
        "crop_area_ratio": round(crop_area_ratio, 4),
        "crop_width_ratio": round(crop_width_ratio, 4),
        "crop_height_ratio": round(crop_height_ratio, 4),
        "largest_contributor": largest,
    }


def _timer_start(enabled: bool) -> int:
    return time.perf_counter_ns() if enabled else 0


def _elapsed_ms(started_ns: int) -> float:
    if started_ns <= 0:
        return 0.0
    return (time.perf_counter_ns() - int(started_ns)) / 1_000_000.0
