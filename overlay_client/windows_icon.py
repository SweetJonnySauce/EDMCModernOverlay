from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional, Tuple


_DEFAULT_ICON_PATH = Path(__file__).resolve().parent / "assets" / "EDMCModernOverlay.ico"
_DEFAULT_APP_USER_MODEL_ID = "EDMCModernOverlay.OverlayClient"


def apply_app_user_model_id(
    app_id: Optional[str] = None,
    *,
    logger: Optional[logging.Logger] = None,
) -> bool:
    if not sys.platform.startswith("win"):
        return False
    app_id_value = (app_id or _DEFAULT_APP_USER_MODEL_ID).strip()
    if not app_id_value:
        return False
    log = logger or logging.getLogger("EDMC.ModernOverlay.Client")
    try:
        import ctypes
    except Exception as exc:
        log.debug("ctypes unavailable; cannot set AppUserModelID: %s", exc)
        return False
    try:
        set_app_id = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID  # type: ignore[attr-defined]
    except Exception as exc:
        log.debug("SetCurrentProcessExplicitAppUserModelID unavailable: %s", exc)
        return False
    set_app_id.argtypes = [ctypes.c_wchar_p]
    set_app_id.restype = ctypes.c_long
    result = int(set_app_id(app_id_value))
    if result != 0:
        log.debug("Failed to set AppUserModelID '%s' (hr=0x%08X)", app_id_value, result & 0xFFFFFFFF)
        return False
    log.debug("Set AppUserModelID to '%s' for taskbar identity.", app_id_value)
    return True


def apply_window_icons(
    hwnd: int,
    *,
    icon_path: Optional[Path] = None,
    logger: Optional[logging.Logger] = None,
) -> Tuple[Optional[int], Optional[int]]:
    if not sys.platform.startswith("win"):
        return None, None
    if not hwnd:
        return None, None
    path = icon_path or _DEFAULT_ICON_PATH
    log = logger or logging.getLogger("EDMC.ModernOverlay.Client")
    if not path.is_file():
        log.debug("OBS capture icon missing at %s; skipping Windows icon update.", path)
        return None, None
    try:
        import ctypes
    except Exception as exc:
        log.debug("ctypes unavailable; cannot apply Windows icon override: %s", exc)
        return None, None

    user32 = ctypes.windll.user32  # type: ignore[attr-defined]
    LR_LOADFROMFILE = 0x0010
    IMAGE_ICON = 1
    SM_CXICON = 11
    SM_CYICON = 12
    SM_CXSMICON = 49
    SM_CYSMICON = 50
    WM_SETICON = 0x0080
    ICON_SMALL = 0
    ICON_BIG = 1

    load_image = user32.LoadImageW
    load_image.restype = ctypes.c_void_p

    big_w = int(user32.GetSystemMetrics(SM_CXICON) or 256)
    big_h = int(user32.GetSystemMetrics(SM_CYICON) or 256)
    small_w = int(user32.GetSystemMetrics(SM_CXSMICON) or 32)
    small_h = int(user32.GetSystemMetrics(SM_CYSMICON) or 32)

    hicon_big = load_image(None, str(path), IMAGE_ICON, big_w, big_h, LR_LOADFROMFILE)
    hicon_small = load_image(None, str(path), IMAGE_ICON, small_w, small_h, LR_LOADFROMFILE)
    if not hicon_big and not hicon_small:
        log.debug("Failed to load icon from %s for OBS capture window.", path)
        return None, None

    if hicon_small:
        user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)
    if hicon_big:
        user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_big)

    set_class_icon = getattr(user32, "SetClassLongPtrW", None) or getattr(user32, "SetClassLongW", None)
    if set_class_icon is not None:
        if hicon_big:
            set_class_icon(hwnd, -14, hicon_big)
        if hicon_small:
            set_class_icon(hwnd, -34, hicon_small)

    return int(hicon_big) if hicon_big else None, int(hicon_small) if hicon_small else None


def destroy_window_icons(handles: Tuple[Optional[int], Optional[int]], *, logger: Optional[logging.Logger] = None) -> None:
    if not sys.platform.startswith("win"):
        return
    big_handle, small_handle = handles
    if not big_handle and not small_handle:
        return
    log = logger or logging.getLogger("EDMC.ModernOverlay.Client")
    try:
        import ctypes
    except Exception as exc:
        log.debug("ctypes unavailable; cannot destroy Windows icons: %s", exc)
        return
    user32 = ctypes.windll.user32  # type: ignore[attr-defined]
    for handle in (big_handle, small_handle):
        if handle:
            try:
                user32.DestroyIcon(handle)
            except Exception as exc:
                log.debug("Failed to destroy Windows icon handle %s: %s", handle, exc)
