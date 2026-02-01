from __future__ import annotations

import tkinter as tk


class ToolTip:
    """Lightweight tooltip helper for Tk widgets."""

    def __init__(self, widget: tk.Widget, text: str, *, delay_ms: int = 500) -> None:
        self._widget = widget
        self._text = text
        self._delay_ms = max(0, int(delay_ms))
        self._window: tk.Toplevel | None = None
        self._label: tk.Label | None = None
        self._after_handle: str | None = None

        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        widget.bind("<ButtonPress>", self._on_leave, add="+")

    def _on_enter(self, _event: object | None = None) -> None:
        if not self._text:
            return
        self._cancel()
        try:
            self._after_handle = self._widget.after(self._delay_ms, self._show)
        except Exception:
            self._show()

    def _on_leave(self, _event: object | None = None) -> None:
        self._cancel()
        self._hide()

    def _cancel(self) -> None:
        if self._after_handle is None:
            return
        try:
            self._widget.after_cancel(self._after_handle)
        except Exception:
            pass
        self._after_handle = None

    def _show(self) -> None:
        self._after_handle = None
        if not self._text:
            return
        try:
            x = int(self._widget.winfo_rootx()) + 12
            y = int(self._widget.winfo_rooty()) + int(self._widget.winfo_height()) + 8
        except Exception:
            x = y = 0
        if self._window is None:
            window = tk.Toplevel(self._widget)
            window.wm_overrideredirect(True)
            try:
                window.attributes("-topmost", True)
            except Exception:
                pass
            label = tk.Label(
                window,
                text=self._text,
                background="#ffffe0",
                relief="solid",
                borderwidth=1,
                font=("TkDefaultFont", 9),
                justify="left",
            )
            label.pack(ipadx=6, ipady=3)
            self._window = window
            self._label = label
        else:
            if self._label is not None:
                self._label.config(text=self._text)
            self._window.deiconify()
        try:
            self._window.geometry(f"+{x}+{y}")
        except Exception:
            pass

    def _hide(self) -> None:
        if self._window is None:
            return
        try:
            self._window.withdraw()
        except Exception:
            pass
