"""Backend-owned helpers for the GNOME Shell raster proof frame."""

from __future__ import annotations

import getpass
import hashlib
import os
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping

from .helper_ipc import (
    GNOME_SHELL_HELPER_RECT_SOURCE_CONTENT,
    HelperPresentationAction,
    HelperPresentationRequest,
    HelperRasterFrameRequest,
    HelperRect,
    HelperTargetStatus,
)

SHELL_RASTER_FRAME_RENDERER = "gnome_shell_raster_frame"
SHELL_RASTER_FRAME_DEFAULT_TIMEOUT_MS = 1500
SHELL_RASTER_FRAME_MAX_BYTES = 8 * 1024 * 1024
SHELL_RASTER_FRAME_MAX_FPS = 4
SHELL_RASTER_FRAME_VERSION = "phase13-static-pyqt-proof-v1"
SHELL_RASTER_STATIC_FRAME_INSET_PX = 10
SHELL_RASTER_RUNTIME_SUBDIR = Path("EDMCModernOverlay") / "shell-raster"
SHELL_RASTER_TMP_PREFIX = "EDMCModernOverlay-shell-raster-"
SHELL_RASTER_STATIC_FRAME_NAME = "phase12-static-pyqt-proof.png"
_SHELL_RASTER_SESSION_ID = f"pid{os.getpid()}-{time.monotonic_ns():x}"
SHELL_RASTER_FRAME_TRANSPORT_PNG_PATH = "png_path"
SHELL_RASTER_FRAME_UPDATE_REASON_STATIC_PROOF = "phase13_static_pyqt_proof"


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


def shell_raster_frame_version(checksum: str, *, session_id: str | None = None) -> str:
    """Return a frame version that carries proof renderer, session, and content identity."""

    session = _frame_version_component(session_id or shell_raster_session_id())
    digest = _frame_version_component(str(checksum or "")[:12]) or "no-checksum"
    return f"{SHELL_RASTER_FRAME_VERSION}:{session}:{digest}"


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
) -> dict[str, object]:
    return {
        "schema": 1,
        "renderer": SHELL_RASTER_FRAME_RENDERER,
        "transport": SHELL_RASTER_FRAME_TRANSPORT_PNG_PATH,
        "update_reason": SHELL_RASTER_FRAME_UPDATE_REASON_STATIC_PROOF,
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


def _timer_start(enabled: bool) -> int:
    return time.perf_counter_ns() if enabled else 0


def _elapsed_ms(started_ns: int) -> float:
    if started_ns <= 0:
        return 0.0
    return (time.perf_counter_ns() - int(started_ns)) / 1_000_000.0
