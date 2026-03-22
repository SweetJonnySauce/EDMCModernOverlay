from __future__ import annotations

import tkinter as tk
from tkinter import colorchooser
from typing import Callable, Optional

_HEX_DIGITS = set("0123456789ABCDEFabcdef")
_COLOR_DIALOG_PATCHED = False


class BackgroundWidget(tk.Frame):
    """Background color + border width editor."""

    def __init__(self, parent, *, min_border: int = 0, max_border: int = 10) -> None:
        super().__init__(parent, bd=0, highlightthickness=0, bg=parent.cget("background"))
        self._request_focus: Optional[Callable[[], None]] = None
        self._change_callback: Optional[Callable[[Optional[str], Optional[str], Optional[int]], None]] = None
        self._min_border = min_border
        self._max_border = max_border
        self._color_var = tk.StringVar()
        self._border_color_var = tk.StringVar()
        self._border_var = tk.StringVar(value=str(min_border))
        self._active_field = "color"
        self._enabled = True
        self._picker_open = False
        self._pre_key_state: tuple[tk.Widget, int, int | None, bool] | None = None
        self._opacity_var = tk.IntVar(value=100)
        self._opacity_label_var = tk.StringVar(value="100%")
        self._opacity_adjust_mode = False
        self._opacity_pending_commit = False
        self._opacity_sync_guard = False
        self._remembered_opacity_percent = 100
        self._last_valid_color: Optional[str] = None
        self._last_valid_border_color: Optional[str] = None

        color_row = tk.Frame(self, bd=0, highlightthickness=0, bg=self.cget("background"))
        color_row.pack(fill="x", padx=4, pady=(4, 2))
        color_label = tk.Label(color_row, text="Background color", anchor="w", bg=self.cget("background"))
        color_label.pack(side="left")
        entry = tk.Entry(color_row, textvariable=self._color_var, width=14)
        entry.pack(side="left", padx=(6, 4))
        entry.bind("<Button-1>", lambda _e: self._handle_entry_click("color"), add="+")
        entry.bind("<FocusIn>", lambda _e: self._handle_focus_event("color"), add="+")
        entry.bind("<FocusOut>", lambda _e: self._emit_change())
        entry.bind("<KeyRelease>", lambda _e: self._validate_color("color", lazy=True))
        entry.bind("<KeyPress-Left>", lambda e: self._record_pre_key_state(e, -1), add="+")
        entry.bind("<KeyPress-Right>", lambda e: self._record_pre_key_state(e, 1), add="+")
        self._bind_tab_navigation(entry)
        self._entry = entry
        picker_btn = tk.Button(color_row, text="Pick…", command=lambda: self._handle_picker_click("color"), width=6)
        picker_btn.pack(side="left")
        picker_btn.bind("<FocusIn>", lambda _e: self._handle_focus_event("pick"), add="+")
        picker_btn.bind("<Return>", lambda e: self._handle_picker_keypress("color", e), add="+")
        picker_btn.bind("<KP_Enter>", lambda e: self._handle_picker_keypress("color", e), add="+")
        picker_btn.bind("<space>", lambda e: self._handle_picker_keypress("color", e), add="+")
        self._bind_tab_navigation(picker_btn)
        self._picker_btn = picker_btn

        border_color_row = tk.Frame(self, bd=0, highlightthickness=0, bg=self.cget("background"))
        border_color_row.pack(fill="x", padx=4, pady=(2, 2))
        border_color_label = tk.Label(
            border_color_row, text="Border color", anchor="w", bg=self.cget("background")
        )
        border_color_label.pack(side="left")
        border_entry = tk.Entry(border_color_row, textvariable=self._border_color_var, width=14)
        border_entry.pack(side="left", padx=(6, 4))
        border_entry.bind("<Button-1>", lambda _e: self._handle_entry_click("border_color"), add="+")
        border_entry.bind("<FocusIn>", lambda _e: self._handle_focus_event("border_color"), add="+")
        border_entry.bind("<FocusOut>", lambda _e: self._emit_change())
        border_entry.bind("<KeyRelease>", lambda _e: self._validate_color("border_color", lazy=True))
        border_entry.bind("<KeyPress-Left>", lambda e: self._record_pre_key_state(e, -1), add="+")
        border_entry.bind("<KeyPress-Right>", lambda e: self._record_pre_key_state(e, 1), add="+")
        self._bind_tab_navigation(border_entry)
        self._border_entry = border_entry
        border_picker_btn = tk.Button(
            border_color_row,
            text="Pick…",
            command=lambda: self._handle_picker_click("border_color"),
            width=6,
        )
        border_picker_btn.pack(side="left")
        border_picker_btn.bind("<FocusIn>", lambda _e: self._handle_focus_event("border_pick"), add="+")
        border_picker_btn.bind("<Return>", lambda e: self._handle_picker_keypress("border_color", e), add="+")
        border_picker_btn.bind("<KP_Enter>", lambda e: self._handle_picker_keypress("border_color", e), add="+")
        border_picker_btn.bind("<space>", lambda e: self._handle_picker_keypress("border_color", e), add="+")
        self._bind_tab_navigation(border_picker_btn)
        self._border_picker_btn = border_picker_btn

        border_row = tk.Frame(self, bd=0, highlightthickness=0, bg=self.cget("background"))
        border_row.pack(fill="x", padx=4, pady=(2, 4))
        border_label = tk.Label(border_row, text="Border (px)", anchor="w", bg=self.cget("background"))
        border_label.pack(side="left")
        spin = tk.Spinbox(
            border_row,
            from_=min_border,
            to=max_border,
            width=4,
            textvariable=self._border_var,
            command=self._emit_change,
            repeatdelay=0,
            repeatinterval=0,
        )
        spin.pack(side="left", padx=(6, 4))
        spin.bind("<Button-1>", self._handle_spin_click, add="+")
        spin.bind("<space>", self._handle_space_exit, add="+")
        spin.bind("<FocusIn>", lambda _e: self._handle_focus_event("border"), add="+")
        spin.bind("<FocusOut>", lambda _e: self._emit_change())
        spin.bind("<KeyRelease>", lambda _e: self._emit_change(commit_border=False))
        spin.bind("<KeyPress-Left>", lambda e: self._record_pre_key_state(e, -1), add="+")
        spin.bind("<KeyPress-Right>", lambda e: self._record_pre_key_state(e, 1), add="+")
        self._bind_tab_navigation(spin)
        self._spin = spin
        opacity_controls = tk.Frame(border_row, bd=0, highlightthickness=0, bg=self.cget("background"))
        opacity_controls.pack(side="right", padx=(4, 0))
        opacity_text_label = tk.Label(opacity_controls, text="Opacity", anchor="w", bg=self.cget("background"))
        opacity_text_label.pack(side="left", padx=(0, 2))
        opacity_scale = tk.Scale(
            opacity_controls,
            from_=0,
            to=100,
            orient="horizontal",
            resolution=1,
            showvalue=False,
            variable=self._opacity_var,
            command=self._handle_opacity_drag,
            length=120,
        )
        opacity_scale.pack(side="left", padx=(8, 4))
        opacity_scale.bind("<ButtonPress-1>", self._handle_opacity_press, add="+")
        opacity_scale.bind("<ButtonRelease-1>", self._handle_opacity_release, add="+")
        opacity_scale.bind("<FocusIn>", lambda _e: self._handle_focus_event("opacity"), add="+")
        self._bind_tab_navigation(opacity_scale)
        self._opacity_scale = opacity_scale
        opacity_label = tk.Label(
            opacity_controls,
            textvariable=self._opacity_label_var,
            anchor="w",
            bg=self.cget("background"),
        )
        opacity_label.pack(side="left")
        self._opacity_value_label = opacity_label
        self._bind_focus_target(self, None)
        self._bind_focus_target(color_row, "color")
        self._bind_focus_target(color_label, "color")
        self._bind_focus_target(border_color_row, "border_color")
        self._bind_focus_target(border_color_label, "border_color")
        self._bind_focus_target(border_label, "border")

    def set_focus_request_callback(self, callback: Callable[[], None] | None) -> None:
        self._request_focus = callback

    def set_change_callback(self, callback: Callable[[Optional[str], Optional[str], Optional[int]], None]) -> None:
        self._change_callback = callback

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        state = "normal" if enabled else "disabled"
        try:
            self._entry.configure(state=state)
            self._border_entry.configure(state=state)
            self._spin.configure(state=state)
            self._picker_btn.configure(state=state)
            self._border_picker_btn.configure(state=state)
            self._opacity_scale.configure(state=state)
        except Exception:
            pass

    def set_values(self, color: Optional[str], border_color: Optional[str], border_width: Optional[int]) -> None:
        display = color or ""
        border_display = border_color or ""
        self._color_var.set(display)
        self._border_color_var.set(border_display)
        if border_width is None:
            border_width = self._min_border
        try:
            border_int = max(self._min_border, min(self._max_border, int(border_width)))
        except Exception:
            border_int = self._min_border
        self._border_var.set(str(border_int))
        self._entry.configure(background="white")
        self._border_entry.configure(background="white")
        self._last_valid_color = self._normalise_color_text(display) if display else None
        self._last_valid_border_color = self._normalise_color_text(border_display) if border_display else None
        self._sync_slider_from_loaded_values(self._last_valid_color, self._last_valid_border_color)

    def on_focus_enter(self) -> None:
        if not self._enabled:
            return
        self._focus_field(self._active_field)

    def on_focus_exit(self) -> None:
        try:
            self.winfo_toplevel().focus_set()
        except Exception:
            pass

    def get_binding_targets(self) -> list[tk.Widget]:  # type: ignore[name-defined]
        # Intentionally exclude the opacity slider so Return/Up/Down route through
        # handle_key() active-field logic (commit-on-exit) instead of focus_next/prev bindings.
        return [self._entry, self._border_entry, self._spin]

    def focus_next_field(self, _event: object | None = None) -> str:
        if not self._enabled:
            return "break"
        self._emit_change()
        if self._active_field in ("color", "pick"):
            next_field = "border_color"
        elif self._active_field in ("border_color", "border_pick"):
            next_field = "border"
        elif self._active_field == "border":
            next_field = "opacity"
        else:
            next_field = "color"
        self._focus_field(next_field)
        return "break"

    def focus_previous_field(self, _event: object | None = None) -> str:
        if not self._enabled:
            return "break"
        self._emit_change()
        if self._active_field in ("border",):
            prev_field = "border_color"
        elif self._active_field == "opacity":
            prev_field = "border"
        elif self._active_field in ("border_color", "border_pick"):
            prev_field = "color"
        else:
            prev_field = "opacity"
        self._focus_field(prev_field)
        return "break"

    def handle_key(self, keysym: str, _event: object | None = None) -> bool:
        if not self._enabled:
            return False
        key = keysym.lower()
        if self._active_field == "opacity":
            if key in {"left", "right"}:
                delta = 1 if key == "right" else -1
                if self._opacity_adjust_mode:
                    self._adjust_slider_value(delta)
                    return True
                self._move_horizontal(delta)
                return True
            if key in {"space", "return", "kp_enter"}:
                self._commit_opacity_changes()
                self._focus_field("opacity", slider_adjust_mode=False)
                return True
            if key == "up":
                self._commit_opacity_changes()
                self._move_horizontal(-1)
                return True
            if key == "down":
                self._commit_opacity_changes()
                self._move_horizontal(1)
                return True
            return False
        if key in {"left", "right"}:
            if not self._should_move_horizontal(_event, 1 if key == "right" else -1):
                return False
            self._move_horizontal(1 if key == "right" else -1)
            return True
        if key in {"return", "kp_enter", "space"} and self._active_field in {"pick", "border_pick"}:
            target = "color" if self._active_field == "pick" else "border_color"
            self._open_color_picker(target)
            return True
        if key in {"down", "return", "kp_enter"}:
            self.focus_next_field()
            return True
        if key == "up":
            self.focus_previous_field()
            return True
        return False

    def focus_set(self) -> None:  # type: ignore[override]
        if not self._enabled:
            return
        self._focus_field(self._active_field)

    def _set_active_field(self, field: str) -> None:
        if field not in ("color", "pick", "border_color", "border_pick", "border", "opacity"):
            return
        self._active_field = field
        self._pre_key_state = None

    def _focus_field(self, field: str, *, slider_adjust_mode: bool | None = None) -> None:
        self._set_active_field(field)
        if field == "color":
            target = self._entry
        elif field == "pick":
            target = self._picker_btn
        elif field == "border_color":
            target = self._border_entry
        elif field == "border_pick":
            target = self._border_picker_btn
        elif field == "opacity":
            target = self._opacity_scale
            if slider_adjust_mode is None:
                slider_adjust_mode = True
            self._opacity_adjust_mode = bool(slider_adjust_mode)
        else:
            target = self._spin
        try:
            target.focus_set()
            try:
                if field in ("pick", "border_pick", "opacity"):
                    return
                if hasattr(target, "select_range"):
                    target.select_range(0, tk.END)
                else:
                    target.selection_range(0, tk.END)
                target.icursor("end")
            except Exception:
                pass
        except Exception:
            pass

    def _handle_focus_event(self, field: str) -> None:
        if not self._enabled:
            return
        self._set_active_field(field)
        if field in ("pick", "border_pick"):
            return
        if field == "opacity":
            self._opacity_adjust_mode = True
            return
        if field == "color":
            target = self._entry
        elif field == "border_color":
            target = self._border_entry
        else:
            target = self._spin
        try:
            if hasattr(target, "select_range"):
                target.select_range(0, tk.END)
            else:
                target.selection_range(0, tk.END)
            target.icursor("end")
        except Exception:
            pass

    def _handle_entry_click(self, field: str) -> str:
        if not self._enabled:
            return "break"
        if self._request_focus:
            try:
                self._request_focus()
            except Exception:
                pass
        if field not in ("color", "border_color"):
            field = "color"
        self._set_active_field(field)
        self._focus_field(field)
        return "break"

    def _handle_space_exit(self, _event: tk.Event[tk.Misc]) -> str | None:  # type: ignore[name-defined]
        if not self._enabled:
            return "break"
        try:
            root = self.winfo_toplevel()
        except Exception:
            root = None
        if root is not None:
            handler = getattr(root, "exit_focus_mode", None)
            if callable(handler):
                try:
                    handler()
                except Exception:
                    pass
        return "break"

    def _handle_container_click(self, field: str | None) -> str:
        if not self._enabled:
            return "break"
        if self._request_focus:
            try:
                self._request_focus()
            except Exception:
                pass
        if field:
            self._set_active_field(field)
        self._focus_field(self._active_field)
        return "break"

    def _bind_focus_target(self, widget: tk.Widget, field: str | None) -> None:
        widget.bind("<Button-1>", lambda _e, f=field: self._handle_container_click(f), add="+")

    def _handle_spin_click(self, event: tk.Event[tk.Misc]) -> str | None:  # type: ignore[name-defined]
        if not self._enabled:
            return "break"
        if self._request_focus:
            try:
                self._request_focus()
            except Exception:
                pass
        self._set_active_field("border")
        element = None
        try:
            element = self._spin.identify(event.x, event.y)
        except Exception:
            element = None
        if element in {"buttonup", "buttondown"}:
            try:
                self._spin.focus_set()
            except Exception:
                pass
            return None
        self._focus_field("border")
        return "break"

    def _handle_opacity_press(self, _event: tk.Event[tk.Misc]) -> None:  # type: ignore[name-defined]
        if not self._enabled:
            return
        if self._request_focus:
            try:
                self._request_focus()
            except Exception:
                pass
        self._focus_field("opacity", slider_adjust_mode=True)

    def _handle_opacity_release(self, _event: tk.Event[tk.Misc]) -> None:  # type: ignore[name-defined]
        if not self._enabled:
            return
        self._commit_opacity_changes()

    def _bind_tab_navigation(self, widget: tk.Widget) -> None:  # type: ignore[name-defined]
        widget.bind("<Tab>", self._handle_tab, add="+")
        widget.bind("<Shift-Tab>", self._handle_shift_tab, add="+")
        widget.bind("<ISO_Left_Tab>", self._handle_shift_tab, add="+")

    def _handle_tab(self, _event: tk.Event[tk.Misc]) -> str:  # type: ignore[name-defined]
        if not self._enabled:
            return "break"
        return self.focus_next_field()

    def _handle_shift_tab(self, _event: tk.Event[tk.Misc]) -> str:  # type: ignore[name-defined]
        if not self._enabled:
            return "break"
        return self.focus_previous_field()

    def _handle_opacity_drag(self, value: str) -> None:
        if self._opacity_sync_guard:
            return
        try:
            percent = int(round(float(value)))
        except Exception:
            percent = self._remembered_opacity_percent
        self._set_opacity_percent(percent, mark_pending=True)

    def _set_opacity_percent(self, percent: int, *, mark_pending: bool = False) -> None:
        bounded = max(0, min(100, int(percent)))
        self._opacity_sync_guard = True
        try:
            self._opacity_var.set(bounded)
        finally:
            self._opacity_sync_guard = False
        self._opacity_label_var.set(f"{bounded}%")
        self._remembered_opacity_percent = bounded
        if mark_pending:
            self._opacity_pending_commit = True

    def _adjust_slider_value(self, delta: int) -> None:
        current = int(self._opacity_var.get())
        self._set_opacity_percent(current + delta, mark_pending=True)

    def _handle_picker_click(self, target: str) -> None:
        if not self._enabled:
            return
        if self._request_focus:
            try:
                self._request_focus()
            except Exception:
                pass
        field = "pick" if target == "color" else "border_pick"
        self._set_active_field(field)
        self._focus_field(field)
        self._open_color_picker(target)

    def _handle_picker_keypress(self, target: str, _event: tk.Event[tk.Misc]) -> str | None:  # type: ignore[name-defined]
        self._handle_picker_click(target)
        return "break"

    def _open_color_picker(self, target: str) -> None:
        if self._picker_open:
            return
        self._picker_open = True
        if target == "border_color":
            target_var = self._border_color_var
        else:
            target_var = self._color_var
        original_value = target_var.get()
        try:
            self._ensure_color_dialog_bindings()
            rgb, alpha_value, had_alpha = self._parse_color_value(target_var.get())
            if alpha_value is None:
                alpha_value = 255
            initial = None
            if rgb is not None:
                initial = f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
            parent = None
            try:
                parent = self.winfo_toplevel()
            except Exception:
                parent = None
            try:
                picked = colorchooser.askcolor(color=initial, parent=parent)
            except tk.TclError:
                picked = colorchooser.askcolor(parent=parent)
            if picked is None or picked[1] is None:
                target_var.set(original_value)
                return
            hex_value = picked[1].lstrip("#")
            if len(hex_value) != 6 or not all(ch in "0123456789abcdefABCDEF" for ch in hex_value):
                target_var.set(original_value)
                return
            hex_value = hex_value.upper()
            _ = rgb, alpha_value, had_alpha
            result = self._apply_slider_alpha_to_token(f"#{hex_value}")
            if result is None:
                result = f"#{hex_value}"
            target_var.set(result)
            self._emit_change()
        finally:
            self._picker_open = False

    def _validate_color(self, field: str, *, lazy: bool = False) -> Optional[str]:
        if field == "border_color":
            target_var = self._border_color_var
            entry = self._border_entry
        else:
            target_var = self._color_var
            entry = self._entry
        raw = target_var.get().strip()
        if not raw:
            entry.configure(background="white")
            return None
        token = self._normalise_color_text(raw)
        if token is None:
            if not lazy:
                entry.configure(background="#ffdddd")
            return None
        entry.configure(background="white")
        return token

    def _emit_change(self, *, commit_border: bool = True) -> None:
        color_raw = self._color_var.get().strip()
        color_value = self._validate_color("color")
        color_invalid = bool(color_raw) and color_value is None
        border_raw = self._border_color_var.get().strip()
        border_color_value = self._validate_color("border_color")
        border_invalid = bool(border_raw) and border_color_value is None
        self._sync_slider_from_manual_alpha(
            color_value if not color_invalid else None,
            border_color_value if not border_invalid else None,
        )
        if color_invalid or border_invalid:
            return
        raw_border = self._border_var.get().strip()
        border_value = self._resolve_border_value(raw_border, commit_border=commit_border)
        if border_value is None:
            return
        color_slider_token = self._slider_target_token(color_value)
        border_slider_token = self._slider_target_token(border_color_value)
        color_output = self._apply_slider_alpha_to_token(color_slider_token) if color_slider_token is not None else None
        if self._should_slider_control_border(color_slider_token, border_slider_token):
            border_output = (
                self._apply_slider_alpha_to_token(border_slider_token) if border_slider_token is not None else None
            )
        else:
            border_output = self._canonical_argb_token(border_slider_token)
        if color_output is not None:
            self._color_var.set(color_output)
            self._last_valid_color = color_output
        else:
            self._last_valid_color = None
        if border_output is not None:
            self._border_color_var.set(border_output)
            self._last_valid_border_color = border_output
        else:
            self._last_valid_border_color = None
        if self._change_callback is not None:
            self._change_callback(color_output, border_output, border_value)

    def _commit_opacity_changes(self) -> None:
        if not self._opacity_pending_commit:
            return
        color_raw = self._color_var.get().strip()
        color_value = self._validate_color("color")
        color_invalid = bool(color_raw) and color_value is None
        border_raw = self._border_color_var.get().strip()
        border_value_token = self._validate_color("border_color")
        border_invalid = bool(border_raw) and border_value_token is None
        self._opacity_pending_commit = False
        color_slider_token = self._slider_target_token(None if color_invalid else color_value)
        border_slider_token = self._slider_target_token(None if border_invalid else border_value_token)
        target_present = color_slider_token is not None or border_slider_token is not None
        if not target_present:
            return
        raw_border = self._border_var.get().strip()
        border_width = self._resolve_border_value(raw_border, commit_border=True)
        if border_width is None:
            return
        control_border = self._should_slider_control_border(color_slider_token, border_slider_token)

        color_output: Optional[str]
        if color_invalid:
            color_output = self._last_valid_color
        elif color_slider_token is not None:
            color_output = self._apply_slider_alpha_to_token(color_slider_token)
            if color_output is not None:
                self._color_var.set(color_output)
                self._last_valid_color = color_output
            else:
                color_output = self._last_valid_color
        else:
            color_output = None
            self._last_valid_color = None

        border_output: Optional[str]
        if border_invalid:
            border_output = self._last_valid_border_color
        elif border_slider_token is not None:
            if control_border:
                border_output = self._apply_slider_alpha_to_token(border_slider_token)
                if border_output is not None:
                    self._border_color_var.set(border_output)
                    self._last_valid_border_color = border_output
                else:
                    border_output = self._last_valid_border_color
            else:
                border_output = self._canonical_argb_token(border_slider_token)
                if border_output is not None:
                    self._border_color_var.set(border_output)
                    self._last_valid_border_color = border_output
                else:
                    border_output = self._last_valid_border_color
        else:
            border_output = None
            self._last_valid_border_color = None

        if self._change_callback is not None:
            self._change_callback(color_output, border_output, border_width)

    @staticmethod
    def _slider_target_token(token: Optional[str]) -> Optional[str]:
        if token is None:
            return None
        if token.strip().casefold() == "none":
            return None
        return token

    def _should_slider_control_border(self, color_token: Optional[str], border_token: Optional[str]) -> bool:
        if border_token is None:
            return False
        if color_token is None:
            return True
        color_alpha = self._effective_alpha_for_link(color_token)
        border_alpha = self._effective_alpha_for_link(border_token)
        if color_alpha is None or border_alpha is None:
            return False
        return color_alpha == border_alpha

    @staticmethod
    def _effective_alpha_for_link(token: str) -> Optional[int]:
        text = (token or "").strip()
        if not text:
            return None
        if text.startswith("#"):
            body = text[1:]
            if len(body) == 8 and all(ch in _HEX_DIGITS for ch in body):
                return int(body[0:2], 16)
            if len(body) == 6 and all(ch in _HEX_DIGITS for ch in body):
                return 255
            return None
        return 255

    def _canonical_argb_token(self, token: Optional[str]) -> Optional[str]:
        if token is None:
            return None
        alpha = self._effective_alpha_for_link(token)
        if alpha is None:
            return None
        return self._apply_alpha_to_token(token, alpha)

    def _resolve_border_value(self, raw_border: str, *, commit_border: bool) -> Optional[int]:
        if not raw_border:
            if not commit_border:
                return None
            border_value = self._min_border
            self._border_var.set(str(border_value))
            return border_value
        try:
            border_value = int(raw_border)
        except Exception:
            if not commit_border:
                return None
            border_value = self._min_border
            self._border_var.set(str(border_value))
            return border_value
        if not commit_border:
            if border_value < self._min_border or border_value > self._max_border:
                return None
            return border_value
        border_value = max(self._min_border, min(self._max_border, border_value))
        self._border_var.set(str(border_value))
        return border_value

    def _sync_slider_from_loaded_values(
        self,
        color_value: Optional[str],
        border_color_value: Optional[str],
    ) -> None:
        if color_value:
            percent = self._token_alpha_percent(color_value, use_default=True)
        elif border_color_value:
            percent = self._token_alpha_percent(border_color_value, use_default=True)
        else:
            percent = self._remembered_opacity_percent
        self._set_opacity_percent(percent, mark_pending=False)
        self._opacity_pending_commit = False

    def _sync_slider_from_manual_alpha(
        self,
        color_value: Optional[str],
        border_color_value: Optional[str],
    ) -> None:
        percent: Optional[int] = None
        if color_value and self._token_has_explicit_alpha(color_value):
            percent = self._token_alpha_percent(color_value, use_default=False)
        elif color_value is None and border_color_value and self._token_has_explicit_alpha(border_color_value):
            percent = self._token_alpha_percent(border_color_value, use_default=False)
        if percent is None:
            return
        self._set_opacity_percent(percent, mark_pending=False)
        self._opacity_pending_commit = False

    def _token_has_explicit_alpha(self, token: str) -> bool:
        text = (token or "").strip()
        if not text.startswith("#"):
            return False
        return len(text) == 9

    def _token_alpha_percent(self, token: str, *, use_default: bool) -> int:
        rgba, alpha, had_alpha = self._parse_color_value(token)
        if rgba is None:
            return self._remembered_opacity_percent
        if had_alpha and alpha is not None:
            return self._alpha_to_percent(alpha)
        if use_default:
            return 100
        return self._remembered_opacity_percent

    @staticmethod
    def _alpha_to_percent(alpha: int) -> int:
        bounded = max(0, min(255, int(alpha)))
        return int(round((bounded / 255.0) * 100.0))

    @staticmethod
    def _percent_to_alpha(percent: int) -> int:
        bounded = max(0, min(100, int(percent)))
        return int(round((bounded / 100.0) * 255.0))

    def _apply_slider_alpha_to_token(self, token: str) -> Optional[str]:
        alpha = self._percent_to_alpha(self._remembered_opacity_percent)
        return self._apply_alpha_to_token(token, alpha)

    def _apply_alpha_to_token(self, token: str, alpha: int) -> Optional[str]:
        normalized = self._normalise_color_text(token)
        if normalized is None:
            return None
        alpha_int = max(0, min(255, int(alpha)))
        if normalized.startswith("#"):
            body = normalized[1:]
            if len(body) == 8:
                rgb = body[2:]
            elif len(body) == 6:
                rgb = body
            else:
                return None
            return f"#{alpha_int:02X}{rgb.upper()}"
        rgb = self._resolve_named_color_rgb(normalized)
        if rgb is None:
            return None
        red, green, blue = rgb
        return f"#{alpha_int:02X}{red:02X}{green:02X}{blue:02X}"

    def _resolve_named_color_rgb(self, name: str) -> Optional[tuple[int, int, int]]:
        try:
            red16, green16, blue16 = self.winfo_rgb(name)
        except Exception:
            return None
        return red16 // 256, green16 // 256, blue16 // 256

    def _move_horizontal(self, delta: int) -> None:
        order = ("color", "pick", "border_color", "border_pick", "border", "opacity")
        try:
            idx = order.index(self._active_field)
        except ValueError:
            idx = 0
        next_idx = (idx + delta) % len(order)
        self._focus_field(order[next_idx])

    def _should_move_horizontal(self, event: object | None, delta: int) -> bool:
        if self._active_field in ("pick", "border_pick"):
            return True
        widget = getattr(event, "widget", None) if event is not None else None
        if widget not in (self._entry, self._border_entry, self._spin):
            try:
                widget = self.winfo_toplevel().focus_get()
            except Exception:
                widget = None
        if widget not in (self._entry, self._border_entry, self._spin):
            return False
        pre_state = self._consume_pre_key_state(widget, delta)
        if pre_state is not None:
            pre_insert, pre_selection = pre_state
            if pre_selection or pre_insert is None:
                return False
            try:
                end_idx = int(widget.index(tk.END))
            except Exception:
                return False
            at_edge = pre_insert <= 0 if delta < 0 else pre_insert >= end_idx
            return at_edge
        if self._selection_exists(widget):
            return False
        try:
            insert_idx = int(widget.index(tk.INSERT))
            end_idx = int(widget.index(tk.END))
        except Exception:
            return False
        at_edge = insert_idx <= 0 if delta < 0 else insert_idx >= end_idx
        return at_edge

    def _record_pre_key_state(self, event: tk.Event[tk.Misc], delta: int) -> None:  # type: ignore[name-defined]
        widget = getattr(event, "widget", None)
        if widget not in (self._entry, self._border_entry, self._spin):
            return
        try:
            insert_idx = int(widget.index(tk.INSERT))
        except Exception:
            insert_idx = None
        self._pre_key_state = (widget, delta, insert_idx, self._selection_exists(widget))

    def _consume_pre_key_state(self, widget: tk.Widget, delta: int) -> tuple[int | None, bool] | None:
        state = self._pre_key_state
        self._pre_key_state = None
        if state is None:
            return None
        stored_widget, stored_delta, insert_idx, has_selection = state
        if stored_widget is widget and stored_delta == delta:
            return insert_idx, has_selection
        return None

    @staticmethod
    def _parse_color_value(raw: str) -> tuple[tuple[int, int, int] | None, int | None, bool]:
        token = (raw or "").strip()
        if not token:
            return None, None, False
        if token.startswith("#"):
            token = token[1:]
        if len(token) not in (6, 8):
            return None, None, False
        try:
            if len(token) == 8:
                alpha = int(token[0:2], 16)
                red = int(token[2:4], 16)
                green = int(token[4:6], 16)
                blue = int(token[6:8], 16)
            else:
                red = int(token[0:2], 16)
                green = int(token[2:4], 16)
                blue = int(token[4:6], 16)
        except Exception:
            return None, None, False
        if len(token) == 8:
            return (red, green, blue), alpha, True
        return (red, green, blue), 255, False

    def _ensure_color_dialog_bindings(self) -> None:
        global _COLOR_DIALOG_PATCHED
        if _COLOR_DIALOG_PATCHED:
            return
        try:
            script = r"""
if {![info exists ::edmcoverlay_color_dialog_patched]} {
    if {[llength [info commands ::tk::dialog::color::BuildDialog]] == 0} {
        catch {auto_load ::tk::dialog::color::BuildDialog}
    }
    if {[llength [info commands ::tk::dialog::color::BuildDialog]]} {
        rename ::tk::dialog::color::BuildDialog ::tk::dialog::color::BuildDialog_orig
        proc ::tk::dialog::color::BuildDialog {w} {
            ::tk::dialog::color::BuildDialog_orig $w
            upvar ::tk::dialog::color::[winfo name $w] data
            foreach color {red green blue} {
                set entry $data($color,entry)
                bind $entry <KeyRelease> [list tk::dialog::color::HandleRGBEntry $w]
                bind $entry <FocusOut> [list tk::dialog::color::HandleRGBEntry $w]
            }
            if {[winfo exists $w.top.sel.ent]} {
                bind $w.top.sel.ent <KeyRelease> [list tk::dialog::color::HandleSelEntry $w]
                bind $w.top.sel.ent <FocusOut> [list tk::dialog::color::HandleSelEntry $w]
            }
        }
    }
    set ::edmcoverlay_color_dialog_patched 1
}
"""
            self.tk.eval(script)
        except Exception:
            return
        _COLOR_DIALOG_PATCHED = True

    def _normalise_color_text(self, raw: str) -> Optional[str]:
        token = (raw or "").strip()
        if not token:
            return None
        hex_part = token[1:] if token.startswith("#") else token
        if len(hex_part) in (6, 8) and all(ch in _HEX_DIGITS for ch in hex_part):
            return "#" + hex_part.upper()
        if token.casefold() == "none":
            return token
        if self._resolve_named_color_rgb(token) is not None:
            return token
        return None

    @staticmethod
    def _selection_exists(widget: tk.Widget) -> bool:
        try:
            if widget.selection_present():
                return True
        except Exception:
            pass
        try:
            widget.index("sel.first")
            widget.index("sel.last")
            return True
        except tk.TclError:
            return False
        except Exception:
            return False
