from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from overlay_controller.widgets.common import alt_modifier_active

IDPREFIX_DROPDOWN_WIDTH = 32
PROFILE_DROPDOWN_WIDTH = 18


class _LabeledSelectorWidget(tk.Frame):
    """Single-selector widget with label, dropdown, and step arrows."""

    def __init__(
        self,
        parent: tk.Widget,
        *,
        label_text: str,
        options: list[str] | None = None,
        dropdown_width: int,
    ) -> None:
        super().__init__(parent, bd=0, highlightthickness=0, bg=parent.cget("background"))
        self._choices = options or []
        self._selection = tk.StringVar()
        self._dropdown_posted = False
        self._request_focus: Callable[[], None] | None = None
        self._on_selection_changed: Callable[[str | None], None] | None = None

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=0)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)

        self.label = tk.Label(self, text=label_text, anchor="w", bg=self.cget("background"))
        self.label.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 2))

        self.dropdown = ttk.Combobox(
            self,
            values=self._choices,
            state="readonly",
            textvariable=self._selection,
            width=dropdown_width,
        )
        if self._choices:
            self.dropdown.current(0)
        self.dropdown.grid(row=1, column=1, padx=0, pady=0, sticky="we")

        self._block_classes = ("TComboboxListbox", "Listbox", "TComboboxPopdown")
        self._bind_dropdown_common()
        self._build_triangles()

    def _bind_dropdown_common(self) -> None:
        alt_sequences = (
            "<Alt-Up>",
            "<Alt-Down>",
            "<Alt-Left>",
            "<Alt-Right>",
            "<Alt-KeyPress-Up>",
            "<Alt-KeyPress-Down>",
            "<Alt-KeyPress-Left>",
            "<Alt-KeyPress-Right>",
        )
        for seq in alt_sequences:
            self.dropdown.bind(seq, lambda _e: "break")
            for class_name in self._block_classes:
                try:
                    self.dropdown.bind_class(class_name, seq, lambda _e: "break")
                except Exception:
                    continue

        for seq in ("<Left>", "<Right>", "<Up>", "<Down>"):
            self.dropdown.bind(seq, self._handle_arrow_key, add="+")
            for class_name in self._block_classes:
                try:
                    self.dropdown.bind_class(class_name, seq, self._handle_arrow_key, add="+")
                except Exception:
                    continue

        self.dropdown.bind("<Button-1>", self._handle_dropdown_click, add="+")
        self.dropdown.bind("<<ComboboxSelected>>", self._handle_selection_change, add="+")

    def update_options(self, options: list[str], selected_index: int | None = None) -> None:
        self._choices = options or []
        try:
            self.dropdown.configure(values=self._choices)
        except Exception:
            pass
        if selected_index is not None and 0 <= selected_index < len(self._choices):
            try:
                self.dropdown.current(selected_index)
            except Exception:
                selected_index = None
        if selected_index is None:
            try:
                self._selection.set("")
                self.dropdown.set("")
            except Exception:
                pass

    def on_focus_enter(self) -> None:
        try:
            self.dropdown.focus_set()
        except Exception:
            pass

    def on_focus_exit(self) -> None:
        try:
            self.winfo_toplevel().focus_set()
        except Exception:
            pass

    def _is_dropdown_open(self) -> bool:
        try:
            popdown = self.dropdown.tk.call("ttk::combobox::PopdownWindow", self.dropdown)
            return bool(int(self.dropdown.tk.call("winfo", "viewable", popdown)))
        except Exception:
            return False

    def _sync_dropdown_selection(self, index: int) -> None:
        try:
            popdown = self.dropdown.tk.call("ttk::combobox::PopdownWindow", self.dropdown)
            listbox = f"{popdown}.f.l"
            exists = bool(int(self.dropdown.tk.call("winfo", "exists", listbox)))
            if not exists:
                return
            self.dropdown.tk.call(listbox, "selection", "clear", 0, "end")
            self.dropdown.tk.call(listbox, "selection", "set", index)
            self.dropdown.tk.call(listbox, "activate", index)
            self.dropdown.tk.call(listbox, "see", index)
        except Exception:
            return

    def _advance_selection(self, step: int = 1) -> bool:
        count = len(self._choices)
        if not count:
            return False
        try:
            current_index = int(self.dropdown.current())
        except Exception:
            current_index = -1
        if current_index < 0:
            current_index = 0

        target_index = (current_index + step) % count
        try:
            self.dropdown.current(target_index)
            self.dropdown.event_generate("<<ComboboxSelected>>")
            self._sync_dropdown_selection(target_index)
            return True
        except Exception:
            return False

    def _build_triangles(self) -> None:
        def _make_button(*, column: int, direction: str, on_click: Callable[[], None]) -> None:
            btn = tk.Canvas(
                self,
                width=24,
                height=24,
                bd=0,
                highlightthickness=0,
                bg=self.cget("background"),
            )
            size = 24
            inset = 6
            if direction == "left":
                points = (inset, size / 2, size - inset, inset, size - inset, size - inset)
            else:
                points = (size - inset, size / 2, inset, inset, inset, size - inset)
            btn.create_polygon(*points, fill="black", outline="black")
            btn.grid(row=1, column=column, padx=2, pady=0)

            def _handler(_event: object) -> str:
                if self._request_focus:
                    try:
                        self._request_focus()
                    except Exception:
                        pass
                on_click()
                return "break"

            btn.bind("<Button-1>", _handler)

        _make_button(column=0, direction="left", on_click=lambda: self._advance_selection(-1))
        _make_button(column=2, direction="right", on_click=lambda: self._advance_selection(1))

    def set_focus_request_callback(self, callback: Callable[[], None] | None) -> None:
        self._request_focus = callback

    def set_selection_change_callback(self, callback: Callable[[str | None], None] | None) -> None:
        self._on_selection_changed = callback

    def _handle_dropdown_click(self, _event: object) -> None:
        if self._request_focus:
            try:
                self._request_focus()
            except Exception:
                pass
        try:
            self.dropdown.focus_set()
        except Exception:
            pass

    def _handle_selection_change(self, _event: object | None = None) -> None:
        if self._on_selection_changed:
            try:
                self._on_selection_changed(self.dropdown.get())
            except Exception:
                pass

    def set_exit_focus_sequences(self, sequences: list[str]) -> None:
        for sequence in sequences:
            try:
                self.dropdown.bind(sequence, self._handle_exit_focus, add="+")
            except Exception:
                continue
            for class_name in self._block_classes:
                try:
                    self.dropdown.bind_class(class_name, sequence, self._handle_exit_focus, add="+")
                except Exception:
                    continue

    def _handle_exit_focus(self, _event: tk.Event[tk.Misc]) -> str | None:  # type: ignore[name-defined]
        self._dropdown_posted = False
        try:
            self.dropdown.tk.call("ttk::combobox::Unpost", self.dropdown)
        except Exception:
            pass
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

    def _post_dropdown(self) -> None:
        try:
            self.dropdown.tk.call("ttk::combobox::Post", self.dropdown)
            self._dropdown_posted = True
            try:
                popdown = self.dropdown.tk.call("ttk::combobox::PopdownWindow", self.dropdown)
                listbox = f"{popdown}.f.l"
                exists = bool(int(self.dropdown.tk.call("winfo", "exists", listbox)))
                if exists:
                    current = self.dropdown.current()
                    self.dropdown.tk.call(listbox, "activate", current)
                    self.dropdown.tk.call("focus", listbox)
            except Exception:
                pass
            try:
                self.update_idletasks()
            except Exception:
                pass
        except Exception:
            pass

    def _navigate(self, step: int) -> bool:
        changed = self._advance_selection(step)
        if changed:
            try:
                current = int(self.dropdown.current())
            except Exception:
                current = None
            if current is not None:
                self._sync_dropdown_selection(current)
        return changed

    def handle_key(self, keysym: str, event: tk.Event[tk.Misc] | None = None) -> str | None:  # type: ignore[name-defined]
        if alt_modifier_active(self, event):
            return "break"

        key = keysym.lower()
        if key == "left":
            self._advance_selection(-1)
            return "break"
        if key == "right":
            self._advance_selection(1)
            return "break"
        if key == "down":
            if not self._is_dropdown_open():
                if self._dropdown_posted:
                    self._dropdown_posted = False
                    self._navigate(1)
                    return "break"
                self._post_dropdown()
                return "break"
            self._dropdown_posted = False
            self._navigate(1)
            return "break"
        if key == "up":
            self._navigate(-1)
            return "break"
        if key == "return":
            try:
                if self._is_dropdown_open():
                    focus_target = self.dropdown.tk.call("focus")
                    if focus_target:
                        self.dropdown.tk.call("event", "generate", focus_target, "<Return>")
                    else:
                        self.dropdown.event_generate("<Return>")
                else:
                    self.dropdown.event_generate("<Return>")
            except Exception:
                pass
            return "break"
        return None

    def _handle_arrow_key(self, event: tk.Event[tk.Misc]) -> str | None:  # type: ignore[name-defined]
        return self.handle_key(event.keysym, event)


class ProfileSelectorWidget(_LabeledSelectorWidget):
    def __init__(self, parent: tk.Widget, options: list[str] | None = None) -> None:
        super().__init__(
            parent,
            label_text="Profile",
            options=options,
            dropdown_width=PROFILE_DROPDOWN_WIDTH,
        )


class OverlaySelectorWidget(_LabeledSelectorWidget):
    def __init__(self, parent: tk.Widget, options: list[str] | None = None) -> None:
        super().__init__(
            parent,
            label_text="Overlay",
            options=options,
            dropdown_width=IDPREFIX_DROPDOWN_WIDTH,
        )


# Backward-compatible alias used by some tests/import sites.
IdPrefixGroupWidget = OverlaySelectorWidget


__all__ = ["IdPrefixGroupWidget", "OverlaySelectorWidget", "ProfileSelectorWidget"]
