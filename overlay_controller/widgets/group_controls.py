from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional

from .tooltip import ToolTip


class GroupControlsWidget(tk.Frame):
    """Bottom controls widget hosting group-enabled and reset controls."""

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent, bd=0, highlightthickness=0, bg=parent.cget("background"))
        self._request_focus: Optional[Callable[[], None]] = None
        self._on_enabled_changed: Optional[Callable[[bool], None]] = None
        self._on_reset_clicked: Optional[Callable[[], None]] = None
        self._active_field = "enabled"
        self._enabled = True

        self.group_enabled_var = tk.BooleanVar(value=True)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.enabled_checkbox = tk.Checkbutton(
            self,
            text="Enabled",
            variable=self.group_enabled_var,
            command=self._handle_enabled_changed,
        )
        self.enabled_checkbox.grid(row=0, column=0, sticky="w", padx=(8, 4), pady=(8, 8))

        self.reset_button = tk.Button(
            self,
            text="Reset",
            command=self._handle_reset_clicked,
            width=6,
        )
        self.reset_button.grid(row=0, column=1, sticky="e", padx=(4, 8), pady=(6, 8))
        ToolTip(self.reset_button, "Reset returns the overlay to the plugin defaults")

        self.enabled_checkbox.bind("<Button-1>", self._handle_enabled_click, add="+")
        self.enabled_checkbox.bind("<FocusIn>", lambda _e: self._set_active_field("enabled"), add="+")
        self.reset_button.bind("<Button-1>", self._handle_reset_click, add="+")
        self.reset_button.bind("<FocusIn>", lambda _e: self._set_active_field("reset"), add="+")

    def set_focus_request_callback(self, callback: Callable[[], None] | None) -> None:
        self._request_focus = callback

    def set_enabled_change_callback(self, callback: Callable[[bool], None] | None) -> None:
        self._on_enabled_changed = callback

    def set_reset_callback(self, callback: Callable[[], None] | None) -> None:
        self._on_reset_clicked = callback

    def get_binding_targets(self) -> list[tk.Widget]:  # type: ignore[name-defined]
        return [self.enabled_checkbox, self.reset_button]

    def focus_next_field(self, _event: object | None = None) -> str:
        if not self._enabled:
            return "break"
        target = "reset" if self._active_field == "enabled" else "enabled"
        self._focus_field(target)
        return "break"

    def focus_previous_field(self, _event: object | None = None) -> str:
        if not self._enabled:
            return "break"
        target = "enabled" if self._active_field == "reset" else "reset"
        self._focus_field(target)
        return "break"

    def on_focus_enter(self) -> None:
        if not self._enabled:
            return
        self._focus_field(self._active_field)

    def on_focus_exit(self) -> None:
        try:
            self.winfo_toplevel().focus_set()
        except Exception:
            pass

    def handle_key(self, keysym: str, _event: object | None = None) -> bool:
        if not self._enabled:
            return False
        key = keysym.lower()
        if key in {"tab", "return", "kp_enter", "down"}:
            self.focus_next_field()
            return True
        if key in {"iso_left_tab", "shift-tab", "up"}:
            self.focus_previous_field()
            return True
        if key == "space":
            event_widget = getattr(_event, "widget", None) if _event is not None else None
            if self._active_field == "enabled":
                if event_widget is self.enabled_checkbox:
                    return True
                self._invoke_enabled()
            else:
                if event_widget is self.reset_button:
                    return True
                self._invoke_reset()
            return True
        if key == "left":
            self.focus_previous_field()
            return True
        if key == "right":
            self.focus_next_field()
            return True
        return False

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)
        state = "normal" if self._enabled else "disabled"
        try:
            self.enabled_checkbox.configure(state=state)
        except Exception:
            pass
        try:
            self.reset_button.configure(state=state)
        except Exception:
            pass

    def focus_set(self) -> None:  # type: ignore[override]
        if not self._enabled:
            return
        self._focus_field(self._active_field)

    def _set_active_field(self, field: str) -> None:
        if field in {"enabled", "reset"}:
            self._active_field = field

    def _focus_field(self, field: str) -> None:
        self._set_active_field(field)
        target = self.enabled_checkbox if field == "enabled" else self.reset_button
        try:
            target.focus_set()
        except Exception:
            pass

    def _request_host_focus(self) -> None:
        if self._request_focus is None:
            return
        try:
            self._request_focus()
        except Exception:
            pass

    def _handle_enabled_click(self, _event: object | None = None) -> None:
        if not self._enabled:
            return
        self._request_host_focus()
        self._set_active_field("enabled")

    def _handle_reset_click(self, _event: object | None = None) -> None:
        if not self._enabled:
            return
        self._request_host_focus()
        self._set_active_field("reset")

    def _handle_enabled_changed(self) -> None:
        if self._on_enabled_changed is None:
            return
        if not self._enabled:
            return
        try:
            self._on_enabled_changed(bool(self.group_enabled_var.get()))
        except Exception:
            pass

    def _handle_reset_clicked(self) -> None:
        if self._on_reset_clicked is None:
            return
        if not self._enabled:
            return
        try:
            self._on_reset_clicked()
        except Exception:
            pass

    def _invoke_enabled(self) -> None:
        try:
            self.enabled_checkbox.invoke()
            return
        except Exception:
            pass
        current = bool(self.group_enabled_var.get())
        self.group_enabled_var.set(not current)
        self._handle_enabled_changed()

    def _invoke_reset(self) -> None:
        try:
            self.reset_button.invoke()
            return
        except Exception:
            pass
        self._handle_reset_clicked()
