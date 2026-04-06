from __future__ import annotations

from pathlib import Path
import tkinter as tk
from typing import Any, Dict, Mapping

DEFAULT_PROFILE_NAME = "Default"
SHIP_TABLE_SORT_COLUMNS = {"apply", "name", "id", "type"}
SHIP_APPLY_ON = "[x]"
SHIP_APPLY_OFF = "[ ]"
RULE_CONTEXT_KEYS = (
    "InMainShip",
    "InSRV",
    "InFighter",
    "OnFoot",
    "InWing",
    "InTaxi",
    "InMulticrew",
)
ACTIVE_COLUMN_CHECKMARK = "✅"
NO_SHIPS_HINT = "Visit a shipyard and swap ships in game then close and reopen settings to populate the ship list."
_LEGACY_NO_SHIPS_HINT = "Swap ships in game and then close and reopen settings to have it show up on the ship list."
_NO_SHIPS_HINT_MESSAGES = {NO_SHIPS_HINT, _LEGACY_NO_SHIPS_HINT}


def load_profile_menu_icons(panel: Any) -> None:
    icons: Dict[str, Any] = {}
    plugin_dir = getattr(panel._preferences, "plugin_dir", None)
    if plugin_dir is None:
        panel._profile_menu_icons = icons
        return
    base = Path(plugin_dir).resolve() / "assets"
    icon_files = {
        "insert_above": "add_row_above_24dp_555555_FILL0_wght400_GRAD0_opsz24.png",
        "insert_below": "add_row_below_24dp_555555_FILL0_wght400_GRAD0_opsz24.png",
        "rename": "edit_24dp_555555_FILL0_wght400_GRAD0_opsz24.png",
        "delete": "delete_24dp_555555_FILL0_wght400_GRAD0_opsz24.png",
        "active": "icon_green_tick_16x16.png",
        "copy": "content_copy_24dp_555555_FILL0_wght400_GRAD0_opsz24.png",
        "paste": "content_paste_go_24dp_555555_FILL0_wght400_GRAD0_opsz24.png",
        "move_up": "move_selection_up_24dp_555555_FILL0_wght400_GRAD0_opsz24.png",
        "move_down": "move_selection_down_24dp_555555_FILL0_wght400_GRAD0_opsz24.png",
    }
    for key, filename in icon_files.items():
        path = base / filename
        if not path.exists():
            continue
        try:
            icons[key] = tk.PhotoImage(file=str(path))
        except Exception:
            continue
    checkbox_off = _build_sheet_checkbox_icon(checked=False)
    checkbox_on = _build_sheet_checkbox_icon(checked=True)
    if checkbox_off is not None:
        icons["check_off"] = checkbox_off
    if checkbox_on is not None:
        icons["check_on"] = checkbox_on
    panel._profile_menu_icons = icons


def _build_sheet_checkbox_icon(*, checked: bool) -> Any:
    try:
        image = tk.PhotoImage(width=14, height=14)
    except Exception:
        return None
    # Match the sheet-style checkbox look: outlined box with a filled inner
    # square when checked.
    image.put("#ffffff", to=(2, 2, 12, 12))
    image.put("#000000", to=(1, 1, 13, 2))
    image.put("#000000", to=(1, 12, 13, 13))
    image.put("#000000", to=(1, 1, 2, 13))
    image.put("#000000", to=(12, 1, 13, 13))
    if checked:
        image.put("#000000", to=(4, 4, 10, 10))
    return image


def _ship_apply_visual(panel: Any, checked: bool) -> tuple[str, Any]:
    icons = getattr(panel, "_profile_menu_icons", {})
    if isinstance(icons, Mapping):
        icon_key = "check_on" if checked else "check_off"
        icon = icons.get(icon_key)
        if icon is not None:
            return "", icon
    return (SHIP_APPLY_ON if checked else SHIP_APPLY_OFF), None


def _is_default_profile_name(profile_name: str) -> bool:
    return str(profile_name or "").strip().casefold() == DEFAULT_PROFILE_NAME.casefold()


def _all_context_state() -> Dict[str, bool]:
    return {context: True for context in RULE_CONTEXT_KEYS}


def _set_profile_rules_controls_enabled(panel: Any, *, enabled: bool) -> None:
    widget_state = "normal" if enabled else "disabled"
    rule_controls = list(getattr(panel, "_profile_rule_checkbuttons", []))
    for control in rule_controls:
        if control is None:
            continue
        try:
            control.configure(state=widget_state)
        except Exception:
            continue

    _set_profile_ship_table_enabled(panel, enabled=enabled)

    apply_button = getattr(panel, "_profile_rules_apply_button", None)
    if apply_button is not None:
        try:
            apply_button.configure(state=widget_state)
        except Exception:
            pass


def _set_profile_ship_table_enabled(panel: Any, *, enabled: bool) -> None:
    ship_table = getattr(panel, "_profile_ship_table", None)
    if ship_table is None:
        return
    try:
        ship_table.state(("!disabled",) if enabled else ("disabled",))
    except Exception:
        try:
            ship_table.configure(state="normal" if enabled else "disabled")
        except Exception:
            pass


def _set_profile_ship_hint(panel: Any, message: str) -> None:
    hint_var = getattr(panel, "_profile_ship_hint_var", None)
    if hint_var is not None:
        try:
            hint_var.set(message)
        except Exception:
            pass
    try:
        if str(panel._status_var.get() or "").strip() in _NO_SHIPS_HINT_MESSAGES:
            panel._status_var.set("")
    except Exception:
        pass


def _clear_profile_ship_hint(panel: Any) -> None:
    hint_var = getattr(panel, "_profile_ship_hint_var", None)
    if hint_var is not None:
        try:
            if str(hint_var.get() or "").strip() in _NO_SHIPS_HINT_MESSAGES:
                hint_var.set("")
        except Exception:
            pass
    try:
        if str(panel._status_var.get() or "").strip() in _NO_SHIPS_HINT_MESSAGES:
            panel._status_var.set("")
    except Exception:
        pass


def _sync_ship_table_enabled_for_selected_profile(panel: Any) -> None:
    selected_profile = panel._selected_profile_name()
    if _is_default_profile_name(selected_profile):
        _set_profile_ship_table_enabled(panel, enabled=False)
        return
    _set_profile_ship_table_enabled(panel, enabled=_in_main_ship_rule_enabled(panel))


def _in_main_ship_rule_enabled(panel: Any) -> bool:
    var = getattr(panel, "_var_rule_in_main_ship", None)
    if var is None:
        return True
    try:
        return bool(var.get())
    except Exception:
        return True


def _display_profile_name(profile_name: str) -> str:
    token = str(profile_name or "").strip()
    if not token:
        return ""
    return token


def _extract_profile_name(token: Any) -> str:
    return str(token or "").strip()


def refresh_profile_state(panel: Any) -> None:
    callback = panel._profile_status_callback
    if not callable(callback):
        panel._profile_state_snapshot = {}
        panel._sync_profile_widgets()
        return
    try:
        status = callback()
    except Exception as exc:
        panel._status_var.set(f"Failed to load profile state: {exc}")
        return
    if not isinstance(status, Mapping):
        panel._status_var.set("Invalid profile state response.")
        return
    panel._profile_state_snapshot = status
    panel._sync_profile_widgets()


def sync_profile_widgets(panel: Any) -> None:
    status = panel._profile_state_snapshot if isinstance(panel._profile_state_snapshot, Mapping) else {}
    raw_profiles = status.get("profiles")
    profiles = [str(item).strip() for item in raw_profiles] if isinstance(raw_profiles, list) else []
    profiles = [item for item in profiles if item]
    if not profiles:
        profiles = [DEFAULT_PROFILE_NAME]
    current_profile = str(status.get("current_profile") or profiles[0]).strip() or profiles[0]

    combo = panel._profile_current_combo
    if combo is not None:
        try:
            combo.configure(values=profiles)
        except Exception:
            pass
    panel._var_profile_current.set(current_profile)

    panel._sync_profile_table(status=status, profiles=profiles, current_profile=current_profile)
    panel._sync_profile_ship_list(status)
    panel._load_selected_profile_rules()


def status_rules_map(status: Mapping[str, Any]) -> Dict[str, list[Mapping[str, Any]]]:
    raw = status.get("rules")
    if not isinstance(raw, Mapping):
        return {}
    result: Dict[str, list[Mapping[str, Any]]] = {}
    for key, value in raw.items():
        profile_name = str(key or "").strip()
        if not profile_name or not isinstance(value, list):
            continue
        result[profile_name.casefold()] = [item for item in value if isinstance(item, Mapping)]
    return result


def rule_context_state(rules: list[Mapping[str, Any]]) -> Dict[str, bool]:
    state = {context: False for context in RULE_CONTEXT_KEYS}
    for item in rules:
        context = str(item.get("context") or "").strip()
        if context in state:
            state[context] = True
    return state


def sync_profile_table(panel: Any, *, status: Mapping[str, Any], profiles: list[str], current_profile: str) -> None:
    table = panel._profile_table
    if table is None:
        return
    rules_map = panel._status_rules_map(status)
    previously_selected_profile = ""
    try:
        existing_selection = table.selection()
        if existing_selection:
            existing_values = table.item(existing_selection[0], "values")
            if existing_values and len(existing_values) >= 2:
                previously_selected_profile = _extract_profile_name(existing_values[1])
    except Exception:
        previously_selected_profile = ""
    try:
        for item_id in table.get_children(""):
            table.delete(item_id)
    except Exception:
        return

    panel._profile_table_order = list(profiles)
    pending_selected = str(getattr(panel, "_profile_pending_selected_name", "") or "").strip()
    selected_item = None
    for index, profile_name in enumerate(profiles, start=1):
        profile_rules = rules_map.get(profile_name.casefold(), [])
        if _is_default_profile_name(profile_name):
            contexts = _all_context_state()
        else:
            contexts = panel._rule_context_state(profile_rules)
        is_current = profile_name.casefold() == current_profile.casefold()
        values = (
            ACTIVE_COLUMN_CHECKMARK if is_current else "",
            _display_profile_name(profile_name),
            "X" if contexts["InMainShip"] else "",
            "X" if contexts["InSRV"] else "",
            "X" if contexts["InFighter"] else "",
            "X" if contexts["OnFoot"] else "",
            "X" if contexts["InWing"] else "",
            "X" if contexts["InTaxi"] else "",
            "X" if contexts["InMulticrew"] else "",
        )
        item_id = table.insert(
            "",
            "end",
            text=str(index),
            values=values,
        )
        if pending_selected and profile_name.casefold() == pending_selected.casefold():
            selected_item = item_id
        elif (
            previously_selected_profile
            and profile_name.casefold() == previously_selected_profile.casefold()
            and selected_item is None
        ):
            selected_item = item_id
        elif is_current and selected_item is None:
            selected_item = item_id
    if selected_item is not None:
        try:
            table.selection_set(selected_item)
            table.focus(selected_item)
        except Exception:
            pass
    panel._profile_pending_selected_name = ""


def selected_profile_name(panel: Any) -> str:
    table = panel._profile_table
    if table is not None:
        try:
            selected = table.selection()
            if selected:
                values = table.item(selected[0], "values")
                if values and len(values) >= 2:
                    token = _extract_profile_name(values[1])
                    if token:
                        return token
        except Exception:
            pass
    listbox = panel._profile_listbox
    if listbox is not None:
        try:
            selected = listbox.curselection()
            if selected:
                return str(listbox.get(selected[0])).strip()
        except Exception:
            pass
    return str(panel._var_profile_current.get() or DEFAULT_PROFILE_NAME).strip() or DEFAULT_PROFILE_NAME


def on_profile_table_selected(panel: Any, _event=None) -> None:  # pragma: no cover - Tk event
    profile_name = panel._selected_profile_name()
    if profile_name:
        panel._var_profile_current.set(profile_name)
    panel._load_selected_profile_rules()


def on_profile_table_right_click(panel: Any, event) -> None:  # pragma: no cover - Tk event
    table = panel._profile_table
    if table is None:
        return
    row = table.identify_row(event.y)
    if row:
        try:
            table.selection_set(row)
            table.focus(row)
        except Exception:
            pass
    menu = tk.Menu(table, tearoff=False)
    icon_insert_above = panel._profile_menu_icons.get("insert_above")
    icon_insert_below = panel._profile_menu_icons.get("insert_below")
    icon_delete = panel._profile_menu_icons.get("delete")
    icon_rename = panel._profile_menu_icons.get("rename")
    icon_active = panel._profile_menu_icons.get("active")
    icon_copy = panel._profile_menu_icons.get("copy")
    icon_paste = panel._profile_menu_icons.get("paste")
    icon_move_up = panel._profile_menu_icons.get("move_up")
    icon_move_down = panel._profile_menu_icons.get("move_down")
    menu.add_command(
        label="Insert Row Above",
        command=lambda: panel._on_profile_insert_row("above"),
        image=icon_insert_above,
        compound="left",
    )
    menu.add_command(
        label="Insert Row Below",
        command=lambda: panel._on_profile_insert_row("below"),
        image=icon_insert_below,
        compound="left",
    )
    menu.add_command(
        label="Move Row Up",
        command=lambda: panel._on_profile_move_row("up"),
        image=icon_move_up,
        compound="left",
    )
    menu.add_command(
        label="Move Row Down",
        command=lambda: panel._on_profile_move_row("down"),
        image=icon_move_down,
        compound="left",
    )
    menu.add_command(
        label="Rename",
        command=lambda: _start_profile_table_rename_for_selected_row(panel),
        image=icon_rename,
        compound="left",
    )
    menu.add_command(label="Delete Row", command=panel._on_profile_delete, image=icon_delete, compound="left")
    menu.add_separator()
    menu.add_command(label="Set Active", command=panel._on_profile_set_current, image=icon_active, compound="left")
    menu.add_separator()
    menu.add_command(label="Copy", command=panel._on_profile_copy, image=icon_copy, compound="left")
    menu.add_command(label="Paste", command=panel._on_profile_paste, image=icon_paste, compound="left")
    _show_profile_context_menu(panel, table, menu, event.x_root, event.y_root)


def _start_profile_table_rename_for_selected_row(panel: Any) -> None:
    table = panel._profile_table
    if table is None:
        return
    try:
        selected = table.selection()
    except Exception:
        selected = ()
    if not selected:
        panel._status_var.set("Select a profile first.")
        return
    _start_profile_table_rename(panel, row_id=selected[0])


def _start_profile_table_rename(panel: Any, *, row_id: str) -> None:
    table = panel._profile_table
    if table is None:
        return
    bbox = table.bbox(row_id, "#2")
    if not bbox:
        return
    x, y, width, height = bbox
    values = table.item(row_id, "values")
    if not values or len(values) < 2:
        return
    old_name = str(values[1]).strip()
    old_name = _extract_profile_name(old_name)
    if not old_name:
        return
    if panel._profile_table_editor is not None:
        try:
            panel._profile_table_editor.destroy()
        except Exception:
            pass
        panel._profile_table_editor = None
    editor = tk.Entry(table)
    editor.insert(0, old_name)
    editor.place(x=x, y=y, width=width, height=height)
    editor.focus_set()
    editor.selection_range(0, "end")

    def _commit(_event=None) -> None:
        new_name = str(editor.get() or "").strip()
        try:
            editor.destroy()
        except Exception:
            pass
        panel._profile_table_editor = None
        if not new_name or new_name.casefold() == old_name.casefold():
            return
        callback = panel._rename_profile_callback
        if not callable(callback):
            panel._status_var.set("Profile rename is unavailable.")
            return
        try:
            callback(old_name, new_name)
        except Exception as exc:
            panel._status_var.set(f"Failed to rename profile: {exc}")
            return
        panel._status_var.set(f"Renamed profile {old_name} to {new_name}.")
        panel._refresh_profile_state()

    def _cancel(_event=None) -> None:
        try:
            editor.destroy()
        except Exception:
            pass
        panel._profile_table_editor = None

    editor.bind("<Return>", _commit)
    editor.bind("<Escape>", _cancel)
    editor.bind("<FocusOut>", _commit)
    panel._profile_table_editor = editor


def _show_profile_context_menu(panel: Any, table: Any, menu: tk.Menu, x_root: int, y_root: int) -> None:
    previous = getattr(panel, "_profile_context_menu", None)
    if previous is not None:
        try:
            previous.unpost()
        except Exception:
            pass
        try:
            previous.destroy()
        except Exception:
            pass
    panel._profile_context_menu = menu
    toplevel = table.winfo_toplevel()
    binding_ids: dict[str, str] = {}

    def _cleanup(_event=None) -> None:
        if getattr(panel, "_profile_context_menu", None) is not menu:
            return
        for sequence, binding_id in list(binding_ids.items()):
            try:
                toplevel.unbind(sequence, binding_id)
            except Exception:
                pass
        binding_ids.clear()
        try:
            menu.unpost()
        except Exception:
            pass
        try:
            menu.destroy()
        except Exception:
            pass
        if getattr(panel, "_profile_context_menu", None) is menu:
            panel._profile_context_menu = None

    def _defer_cleanup(_event=None) -> None:
        try:
            toplevel.after_idle(_cleanup)
        except Exception:
            _cleanup()

    # Close on the next outside left-click release while letting any
    # menu command callback run first (via after_idle).
    for sequence in ("<ButtonRelease-1>",):
        try:
            binding_id = toplevel.bind(sequence, _defer_cleanup, add="+")
        except Exception:
            continue
        if binding_id:
            binding_ids[sequence] = binding_id

    menu.bind("<Escape>", _cleanup, add="+")
    try:
        menu.tk_popup(x_root, y_root)
    finally:
        try:
            menu.grab_release()
        except Exception:
            pass


def next_profile_copy_name(source_name: str, existing: list[str]) -> str:
    existing_cf = {name.casefold() for name in existing}
    candidate = f"{source_name} (Copy)"
    if candidate.casefold() not in existing_cf:
        return candidate
    suffix = 2
    while True:
        candidate = f"{source_name} (Copy {suffix})"
        if candidate.casefold() not in existing_cf:
            return candidate
        suffix += 1


def on_profile_copy(panel: Any) -> None:
    profile_name = panel._selected_profile_name()
    if not profile_name:
        panel._status_var.set("Select a profile first.")
        return
    panel._profile_table_clipboard = profile_name
    panel._status_var.set(f"Copied profile {profile_name}.")


def on_profile_paste(panel: Any) -> None:
    source_profile = str(panel._profile_table_clipboard or "").strip()
    if not source_profile:
        panel._status_var.set("Copy a profile first.")
        return
    callback = panel._clone_profile_callback
    if not callable(callback):
        panel._status_var.set("Profile paste is unavailable.")
        return
    status = panel._profile_state_snapshot if isinstance(panel._profile_state_snapshot, Mapping) else {}
    raw_profiles = status.get("profiles")
    profiles = [str(item).strip() for item in raw_profiles] if isinstance(raw_profiles, list) else []
    profiles = [item for item in profiles if item]
    new_name = panel._next_profile_copy_name(source_profile, profiles)
    try:
        callback(source_profile, new_name)
    except Exception as exc:
        panel._status_var.set(f"Failed to paste profile: {exc}")
        return
    panel._status_var.set(f"Pasted profile as {new_name}.")
    panel._refresh_profile_state()


def on_profile_insert_row(panel: Any, where: str) -> None:
    callback = panel._create_profile_callback
    if not callable(callback):
        panel._status_var.set("Profile insertion is unavailable.")
        return
    status = panel._profile_state_snapshot if isinstance(panel._profile_state_snapshot, Mapping) else {}
    raw_profiles = status.get("profiles")
    profiles = [str(item).strip() for item in raw_profiles] if isinstance(raw_profiles, list) else []
    profiles = [item for item in profiles if item]
    base_name = "New Profile"
    candidate = base_name
    suffix = 2
    existing_cf = {item.casefold() for item in profiles}
    while candidate.casefold() in existing_cf:
        candidate = f"{base_name} {suffix}"
        suffix += 1
    selected_profile = panel._selected_profile_name()
    try:
        selected_index = next(
            idx for idx, name in enumerate(panel._profile_table_order) if name.casefold() == selected_profile.casefold()
        )
    except StopIteration:
        selected_index = len(panel._profile_table_order)
    desired_index = selected_index if str(where).lower() == "above" else selected_index + 1
    target_non_default_index = len(
        [name for name in panel._profile_table_order[:desired_index] if name.casefold() != DEFAULT_PROFILE_NAME.casefold()]
    )
    try:
        callback(candidate)
    except Exception as exc:
        panel._status_var.set(f"Failed to insert profile: {exc}")
        return
    reorder_callback = panel._reorder_profile_callback
    if callable(reorder_callback):
        try:
            reorder_callback(candidate, target_non_default_index)
        except Exception:
            pass
    panel._profile_pending_selected_name = candidate
    panel._status_var.set(f"Inserted profile {candidate}.")
    panel._refresh_profile_state()


def on_profile_move_row(panel: Any, direction: str) -> None:
    callback = panel._reorder_profile_callback
    if not callable(callback):
        panel._status_var.set("Profile reordering is unavailable.")
        return
    profile_name = panel._selected_profile_name()
    if not profile_name:
        panel._status_var.set("Select a profile first.")
        return
    if profile_name.casefold() == DEFAULT_PROFILE_NAME.casefold():
        panel._status_var.set("Default profile stays at the bottom.")
        return
    ordered = [str(name).strip() for name in panel._profile_table_order if str(name).strip()]
    non_default = [name for name in ordered if name.casefold() != DEFAULT_PROFILE_NAME.casefold()]
    try:
        current_index = next(idx for idx, name in enumerate(non_default) if name.casefold() == profile_name.casefold())
    except StopIteration:
        panel._status_var.set("Selected profile is not in the current order.")
        return
    token = str(direction).casefold()
    if token not in {"up", "down"}:
        panel._status_var.set("Unknown move direction.")
        return
    step = -1 if token == "up" else 1
    target_index = max(0, min(current_index + step, len(non_default) - 1))
    if target_index == current_index:
        panel._status_var.set(
            f"Profile {profile_name} is already at the {'top' if step < 0 else 'bottom'} of custom profiles."
        )
        return
    try:
        callback(profile_name, target_index)
    except Exception as exc:
        panel._status_var.set(f"Failed to move profile: {exc}")
        return
    panel._status_var.set(f"Moved profile {profile_name} {'up' if step < 0 else 'down'}.")
    panel._refresh_profile_state()


def on_profile_table_double_click(panel: Any, event) -> None:  # pragma: no cover - Tk event
    table = panel._profile_table
    if table is None:
        return
    row_id = table.identify_row(event.y)
    column_id = table.identify_column(event.x)
    if not row_id or not column_id:
        return
    try:
        table.selection_set(row_id)
        table.focus(row_id)
    except Exception:
        pass
    if column_id == "#1":
        panel._on_profile_set_current()
        return
    column_to_context = {
        "#3": "InMainShip",
        "#4": "InSRV",
        "#5": "InFighter",
        "#6": "OnFoot",
        "#7": "InWing",
        "#8": "InTaxi",
        "#9": "InMulticrew",
    }
    if column_id in column_to_context:
        panel._toggle_profile_table_rule(column_to_context[column_id])
        return
    if column_id != "#2":
        return
    _start_profile_table_rename(panel, row_id=row_id)


def toggle_profile_table_rule(panel: Any, context: str) -> None:
    callback = getattr(panel, "_set_profile_rules_callback", None)
    if not callable(callback):
        panel._status_var.set("Profile rule updates are unavailable.")
        return
    profile_name = panel._selected_profile_name()
    if not profile_name:
        panel._status_var.set("Select a profile first.")
        return
    if _is_default_profile_name(profile_name):
        panel._status_var.set("Default profile rules apply to all contexts.")
        return
    status = panel._profile_state_snapshot if isinstance(panel._profile_state_snapshot, Mapping) else {}
    rules_map = panel._status_rules_map(status)
    current_rules = list(rules_map.get(profile_name.casefold(), []))
    has_context = any(str(item.get("context") or "").strip() == context for item in current_rules)
    if has_context:
        current_rules = [item for item in current_rules if str(item.get("context") or "").strip() != context]
    else:
        if context == "InMainShip":
            ship_ids = panel._selected_ship_ids_for_rules()
            if ship_ids:
                for ship_id in ship_ids:
                    current_rules.append({"context": "InMainShip", "ship_id": int(ship_id)})
            else:
                current_rules.append({"context": "InMainShip"})
        else:
            current_rules.append({"context": context})
    try:
        callback(profile_name, current_rules)
    except Exception as exc:
        panel._status_var.set(f"Failed to update profile rules: {exc}")
        return
    panel._status_var.set(f"Rules updated for profile {profile_name}.")
    panel._refresh_profile_state()


def sync_profile_ship_list(panel: Any, status: Mapping[str, Any]) -> None:
    ships_raw = status.get("ships")
    ship_table = panel._profile_ship_table
    panel._profile_ship_ids = []
    panel._profile_ship_row_to_ship_id = {}
    if ship_table is None:
        return
    try:
        for item_id in ship_table.get_children(""):
            ship_table.delete(item_id)
    except Exception:
        return
    rows = _build_ship_table_rows(ships_raw)
    sort_column = str(getattr(panel, "_profile_ship_sort_column", "name") or "name").strip().lower()
    if sort_column not in SHIP_TABLE_SORT_COLUMNS:
        sort_column = "name"
    sort_desc = bool(getattr(panel, "_profile_ship_sort_desc", False))
    checked_ids = {int(value) for value in getattr(panel, "_profile_ship_checked_ids", set()) if _is_int_like(value)}
    rows = _sorted_ship_table_rows(rows, column=sort_column, descending=sort_desc, checked_ids=checked_ids)
    row_ship_ids = {int(row["ship_id"]) for row in rows}
    panel._profile_ship_checked_ids = checked_ids.intersection(row_ship_ids)
    if not rows:
        ship_table.insert("", "end", text="", values=("no ships yet", "", ""))
        _set_profile_ship_hint(panel, NO_SHIPS_HINT)
        return
    _clear_profile_ship_hint(panel)
    for row in rows:
        ship_id = int(row["ship_id"])
        text, image = _ship_apply_visual(panel, ship_id in panel._profile_ship_checked_ids)
        item_id = ship_table.insert(
            "",
            "end",
            text=text,
            image=image,
            values=(row["name"], row["ship_ident"], row["type"]),
        )
        panel._profile_ship_row_to_ship_id[item_id] = ship_id
        panel._profile_ship_ids.append(ship_id)


def _build_ship_table_rows(ships_raw: Any) -> list[Dict[str, Any]]:
    rows: list[Dict[str, Any]] = []
    if not isinstance(ships_raw, list):
        return rows
    for item in ships_raw:
        if not isinstance(item, Mapping):
            continue
        ship_id = item.get("ship_id")
        try:
            numeric_ship_id = int(ship_id)
        except (TypeError, ValueError):
            continue
        ship_name = str(item.get("ship_name") or "").strip()
        ship_type = str(item.get("ship_type") or "").strip()
        if not ship_name and not ship_type:
            continue
        display_name = ship_name or "Unnamed"
        ship_ident = str(item.get("ship_ident") or "").strip()
        rows.append(
            {
                "name": display_name,
                "ship_id": numeric_ship_id,
                "ship_ident": ship_ident,
                "type": ship_type,
            }
        )
    return rows


def _sorted_ship_table_rows(
    rows: list[Dict[str, Any]],
    *,
    column: str,
    descending: bool,
    checked_ids: set[int] | None = None,
) -> list[Dict[str, Any]]:
    token = str(column or "").strip().lower()
    checked = set(checked_ids or set())
    if token == "apply":
        def key(row: Dict[str, Any]) -> tuple[object, ...]:
            return (
                0 if int(row.get("ship_id", 0)) in checked else 1,
                str(row.get("name", "")).casefold(),
                int(row.get("ship_id", 0)),
            )
    elif token == "id":
        def key(row: Dict[str, Any]) -> tuple[object, ...]:
            return (
                str(row.get("ship_ident", "")).casefold(),
                str(row.get("name", "")).casefold(),
                int(row.get("ship_id", 0)),
            )
    elif token == "type":
        def key(row: Dict[str, Any]) -> tuple[object, ...]:
            return (
                str(row.get("type", "")).casefold(),
                str(row.get("name", "")).casefold(),
                int(row.get("ship_id", 0)),
            )
    else:
        def key(row: Dict[str, Any]) -> tuple[object, ...]:
            return (
                str(row.get("name", "")).casefold(),
                int(row.get("ship_id", 0)),
            )
    return sorted(list(rows), key=key, reverse=bool(descending))


def on_profile_ship_sort(panel: Any, column: str) -> None:
    if _is_default_profile_name(panel._selected_profile_name()):
        return
    token = str(column or "").strip().lower()
    if token not in SHIP_TABLE_SORT_COLUMNS:
        return
    current = str(getattr(panel, "_profile_ship_sort_column", "name") or "name").strip().lower()
    if current == token:
        panel._profile_ship_sort_desc = not bool(getattr(panel, "_profile_ship_sort_desc", False))
    else:
        panel._profile_ship_sort_column = token
        panel._profile_ship_sort_desc = False
    panel._profile_ship_sort_column = token
    status = panel._profile_state_snapshot if isinstance(panel._profile_state_snapshot, Mapping) else {}
    panel._sync_profile_ship_list(status)


def on_profile_ship_table_click(panel: Any, event) -> str | None:  # pragma: no cover - Tk event
    if _is_default_profile_name(panel._selected_profile_name()):
        return "break"
    if not _in_main_ship_rule_enabled(panel):
        return "break"
    ship_table = panel._profile_ship_table
    if ship_table is None:
        return None
    try:
        region = str(ship_table.identify_region(event.x, event.y) or "")
    except Exception:
        region = ""
    column_id = ship_table.identify_column(event.x)
    if region == "heading" and column_id == "#0":
        panel._on_profile_ship_sort("apply")
        return "break"
    row_id = ship_table.identify_row(event.y)
    if not row_id or column_id != "#0":
        return None
    return _toggle_profile_ship_row(panel, row_id)


def on_profile_ship_table_double_click(panel: Any, event) -> str | None:  # pragma: no cover - Tk event
    if _is_default_profile_name(panel._selected_profile_name()):
        return "break"
    if not _in_main_ship_rule_enabled(panel):
        return "break"
    ship_table = panel._profile_ship_table
    if ship_table is None:
        return None
    row_id = ship_table.identify_row(event.y)
    if not row_id:
        return None
    return _toggle_profile_ship_row(panel, row_id)


def _toggle_profile_ship_row(panel: Any, row_id: str) -> str:
    ship_table = panel._profile_ship_table
    if ship_table is None:
        return "break"
    ship_id = panel._profile_ship_row_to_ship_id.get(str(row_id))
    if ship_id is None:
        return "break"
    checked_ids = {int(value) for value in getattr(panel, "_profile_ship_checked_ids", set()) if _is_int_like(value)}
    if ship_id in checked_ids:
        checked_ids.remove(ship_id)
    else:
        checked_ids.add(ship_id)
    panel._profile_ship_checked_ids = checked_ids
    try:
        text, image = _ship_apply_visual(panel, ship_id in checked_ids)
        ship_table.item(row_id, text=text, image=image)
    except Exception:
        pass
    on_profile_rules_apply(panel)
    return "break"


def _is_int_like(value: Any) -> bool:
    try:
        int(value)
        return True
    except (TypeError, ValueError):
        return False


def on_profile_list_selected(panel: Any, _event=None) -> None:  # pragma: no cover - Tk event
    panel._on_profile_table_selected(_event)


def on_profile_in_main_ship_toggle(panel: Any) -> None:
    _sync_ship_table_enabled_for_selected_profile(panel)


def on_profile_rule_toggle(panel: Any) -> None:
    _sync_ship_table_enabled_for_selected_profile(panel)
    on_profile_rules_apply(panel)


def load_selected_profile_rules(panel: Any) -> None:
    status = panel._profile_state_snapshot if isinstance(panel._profile_state_snapshot, Mapping) else {}
    rules_raw = status.get("rules")
    rules_map = rules_raw if isinstance(rules_raw, Mapping) else {}
    selected_profile = panel._selected_profile_name()
    selected_is_default = _is_default_profile_name(selected_profile)
    selected_rules = []
    for raw_profile, raw_rules in rules_map.items():
        if str(raw_profile).casefold() != selected_profile.casefold():
            continue
        if isinstance(raw_rules, list):
            selected_rules = raw_rules
        break

    contexts = {context: False for context in RULE_CONTEXT_KEYS}
    selected_ship_ids: set[int] = set()
    if selected_is_default:
        contexts = _all_context_state()
    else:
        for item in selected_rules:
            if not isinstance(item, Mapping):
                continue
            context = str(item.get("context") or "").strip()
            if context in contexts:
                contexts[context] = True
            if context == "InMainShip":
                ship_id = item.get("ship_id")
                try:
                    numeric_ship_id = int(ship_id)
                except (TypeError, ValueError):
                    continue
                selected_ship_ids.add(numeric_ship_id)

    panel._var_rule_in_main_ship.set(contexts["InMainShip"])
    panel._var_rule_in_srv.set(contexts["InSRV"])
    panel._var_rule_in_fighter.set(contexts["InFighter"])
    panel._var_rule_on_foot.set(contexts["OnFoot"])
    panel._var_rule_in_wing.set(contexts["InWing"])
    panel._var_rule_in_taxi.set(contexts["InTaxi"])
    panel._var_rule_in_multicrew.set(contexts["InMulticrew"])
    panel._profile_ship_checked_ids = set(selected_ship_ids)
    _set_profile_rules_controls_enabled(panel, enabled=not selected_is_default)
    _sync_ship_table_enabled_for_selected_profile(panel)

    ship_table = panel._profile_ship_table
    if ship_table is not None:
        try:
            ship_table.selection_remove(ship_table.selection())
            first_match = None
            for item_id in ship_table.get_children(""):
                ship_id = panel._profile_ship_row_to_ship_id.get(str(item_id))
                if ship_id is None:
                    continue
                text, image = _ship_apply_visual(panel, ship_id in selected_ship_ids)
                ship_table.item(item_id, text=text, image=image)
                if ship_id in selected_ship_ids:
                    ship_table.selection_add(item_id)
                    if first_match is None:
                        first_match = item_id
            if first_match is not None:
                ship_table.focus(first_match)
        except Exception:
            pass


def on_profile_set_current(panel: Any) -> None:
    callback = panel._set_current_profile_callback
    if not callable(callback):
        panel._status_var.set("Profile switching is unavailable.")
        return
    profile_name = panel._selected_profile_name() or str(panel._var_profile_current.get() or "").strip()
    if not profile_name:
        panel._status_var.set("Select a profile first.")
        return
    try:
        callback(profile_name)
    except Exception as exc:
        panel._status_var.set(f"Failed to switch profile: {exc}")
        return
    panel._status_var.set(f"Current profile set to {profile_name}.")
    panel._refresh_profile_state()


def on_profile_create(panel: Any, _event=None) -> None:  # pragma: no cover - Tk event
    callback = panel._create_profile_callback
    if not callable(callback):
        panel._status_var.set("Profile creation is unavailable.")
        return
    name = str(panel._var_profile_new_name.get() or "").strip()
    if not name:
        panel._status_var.set("Enter a profile name.")
        return
    try:
        callback(name)
    except Exception as exc:
        panel._status_var.set(f"Failed to create profile: {exc}")
        return
    panel._var_profile_new_name.set("")
    panel._status_var.set(f"Created profile {name}.")
    panel._refresh_profile_state()


def on_profile_rename(panel: Any, _event=None) -> None:  # pragma: no cover - Tk event
    callback = panel._rename_profile_callback
    if not callable(callback):
        panel._status_var.set("Profile rename is unavailable.")
        return
    old_name = panel._selected_profile_name()
    new_name = str(panel._var_profile_rename_name.get() or "").strip()
    if not old_name:
        panel._status_var.set("Select a profile first.")
        return
    if not new_name:
        panel._status_var.set("Enter a new profile name.")
        return
    try:
        callback(old_name, new_name)
    except Exception as exc:
        panel._status_var.set(f"Failed to rename profile: {exc}")
        return
    panel._var_profile_rename_name.set("")
    panel._status_var.set(f"Renamed profile {old_name} to {new_name}.")
    panel._refresh_profile_state()


def on_profile_delete(panel: Any) -> None:
    callback = panel._delete_profile_callback
    if not callable(callback):
        panel._status_var.set("Profile deletion is unavailable.")
        return
    profile_name = panel._selected_profile_name()
    if not profile_name:
        panel._status_var.set("Select a profile first.")
        return
    try:
        callback(profile_name)
    except Exception as exc:
        panel._status_var.set(f"Failed to delete profile: {exc}")
        return
    panel._status_var.set(f"Deleted profile {profile_name}.")
    panel._refresh_profile_state()


def on_profile_rules_apply(panel: Any) -> None:
    callback = getattr(panel, "_set_profile_rules_callback", None)
    if not callable(callback):
        panel._status_var.set("Profile rule updates are unavailable.")
        return
    profile_name = panel._selected_profile_name()
    if not profile_name:
        panel._status_var.set("Select a profile first.")
        return
    if _is_default_profile_name(profile_name):
        panel._status_var.set("Default profile rules apply to all contexts.")
        return

    rules: list[Mapping[str, Any]] = []
    if bool(panel._var_rule_in_main_ship.get()):
        selected_ship_ids = panel._selected_ship_ids_for_rules()
        if selected_ship_ids:
            for ship_id in selected_ship_ids:
                rules.append({"context": "InMainShip", "ship_id": int(ship_id)})
        else:
            rules.append({"context": "InMainShip"})
    if bool(panel._var_rule_in_srv.get()):
        rules.append({"context": "InSRV"})
    if bool(panel._var_rule_in_fighter.get()):
        rules.append({"context": "InFighter"})
    if bool(panel._var_rule_on_foot.get()):
        rules.append({"context": "OnFoot"})
    if bool(panel._var_rule_in_wing.get()):
        rules.append({"context": "InWing"})
    if bool(panel._var_rule_in_taxi.get()):
        rules.append({"context": "InTaxi"})
    if bool(panel._var_rule_in_multicrew.get()):
        rules.append({"context": "InMulticrew"})

    try:
        callback(profile_name, rules)
    except Exception as exc:
        panel._status_var.set(f"Failed to update profile rules: {exc}")
        return
    panel._status_var.set(f"Rules updated for profile {profile_name}.")
    panel._refresh_profile_state()


def selected_ship_ids_for_rules(panel: Any) -> list[int]:
    if _is_default_profile_name(panel._selected_profile_name()):
        return []
    ship_table = panel._profile_ship_table
    if ship_table is None:
        return []
    checked_ids = [int(value) for value in getattr(panel, "_profile_ship_checked_ids", set()) if _is_int_like(value)]
    if checked_ids:
        return sorted(set(checked_ids))
    try:
        selected_rows = list(ship_table.selection())
    except Exception:
        return []
    selected_ids: list[int] = []
    for item_id in selected_rows:
        ship_id = panel._profile_ship_row_to_ship_id.get(str(item_id))
        if ship_id is None:
            continue
        selected_ids.append(int(ship_id))
    return selected_ids
