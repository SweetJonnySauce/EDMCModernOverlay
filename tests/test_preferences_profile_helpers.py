from __future__ import annotations

from overlay_plugin import preferences_profile_helpers as helpers


class _StatusVar:
    def __init__(self) -> None:
        self.value = ""

    def set(self, value: str) -> None:
        self.value = str(value)

    def get(self) -> str:
        return self.value


class _BoolVar:
    def __init__(self, value: bool) -> None:
        self._value = bool(value)

    def get(self) -> bool:
        return self._value

    def set(self, value: bool) -> None:
        self._value = bool(value)


class _Panel:
    def __init__(self, selected: str, order: list[str]) -> None:
        self._selected = selected
        self._profile_table_order = list(order)
        self._status_var = _StatusVar()
        self._profile_ship_hint_var = _StatusVar()
        self.reorder_calls: list[tuple[str, int]] = []
        self.refresh_count = 0

        def _reorder(name: str, index: int) -> None:
            self.reorder_calls.append((name, index))

        self._reorder_profile_callback = _reorder

    def _selected_profile_name(self) -> str:
        return self._selected

    def _refresh_profile_state(self) -> None:
        self.refresh_count += 1


class _StateAwareShipTable:
    def __init__(self) -> None:
        self.state_calls: list[tuple[str, ...]] = []

    def state(self, tokens):
        self.state_calls.append(tuple(tokens))


class _ShipTable:
    def __init__(self, selected: list[str], values_by_row: dict[str, tuple[str, ...]]) -> None:
        self._selected = list(selected)
        self._values_by_row = dict(values_by_row)

    def selection(self):
        return tuple(self._selected)

    def item(self, row_id: str, _field: str):
        return self._values_by_row.get(row_id, ())


class _InsertShipTable:
    def __init__(self) -> None:
        self.rows: dict[str, dict[str, tuple[str, ...] | str]] = {}
        self.insert_calls: list[dict[str, tuple[str, ...] | str]] = []

    def get_children(self, _root: str = ""):
        return tuple(self.rows.keys())

    def delete(self, item_id: str) -> None:
        self.rows.pop(item_id, None)

    def insert(self, _parent: str, _index: str, **kwargs):
        row_id = f"row{len(self.insert_calls) + 1}"
        self.insert_calls.append(dict(kwargs))
        self.rows[row_id] = dict(kwargs)
        return row_id


class _InsertProfileTable:
    def __init__(self) -> None:
        self.rows: dict[str, dict[str, tuple[str, ...] | str]] = {}
        self.selection_id: str | None = None
        self.focus_id: str | None = None

    def get_children(self, _root: str = ""):
        return tuple(self.rows.keys())

    def delete(self, item_id: str) -> None:
        self.rows.pop(item_id, None)

    def insert(self, _parent: str, _index: str, **kwargs):
        row_id = f"row{len(self.rows) + 1}"
        self.rows[row_id] = dict(kwargs)
        return row_id

    def selection(self):
        if self.selection_id:
            return (self.selection_id,)
        return ()

    def item(self, row_id: str, _field: str):
        row = self.rows.get(row_id, {})
        return row.get("values", ())

    def selection_set(self, item_id: str) -> None:
        self.selection_id = item_id

    def focus(self, item_id: str | None = None):
        if item_id is None:
            return self.focus_id
        self.focus_id = item_id


class _ShipTableClick:
    def identify_region(self, _x: int, _y: int):
        return "heading"

    def identify_column(self, _x: int):
        return "#0"

    def identify_row(self, _y: int):
        return ""


class _ShipTableDoubleClick:
    def __init__(self) -> None:
        self.updated: dict[str, dict[str, object]] = {}

    def identify_row(self, _y: int):
        return "r1"

    def item(self, row_id: str, **kwargs):
        if kwargs:
            self.updated[row_id] = dict(kwargs)
        return ()


class _ProfileTableDoubleClick:
    def __init__(self, *, row_id: str, column_id: str) -> None:
        self._row_id = row_id
        self._column_id = column_id
        self.selection_id: str | None = None
        self.focus_id: str | None = None

    def identify_row(self, _y: int):
        return self._row_id

    def identify_column(self, _x: int):
        return self._column_id

    def selection_set(self, item_id: str) -> None:
        self.selection_id = item_id

    def focus(self, item_id: str | None = None):
        if item_id is None:
            return self.focus_id
        self.focus_id = item_id


class _ClickEvent:
    def __init__(self, x: int = 0, y: int = 0) -> None:
        self.x = x
        self.y = y


def test_profile_move_row_up_uses_non_default_sequence_index() -> None:
    panel = _Panel(selected="On Foot", order=["PvE", "On Foot", "Mining", "Default"])

    helpers.on_profile_move_row(panel, "up")

    assert panel.reorder_calls == [("On Foot", 0)]
    assert panel.refresh_count == 1


def test_profile_move_row_down_at_bottom_is_noop() -> None:
    panel = _Panel(selected="Mining", order=["PvE", "On Foot", "Mining", "Default"])

    helpers.on_profile_move_row(panel, "down")

    assert panel.reorder_calls == []
    assert panel.refresh_count == 0
    assert "already at the bottom" in panel._status_var.value


def test_profile_move_row_rejects_default_profile() -> None:
    panel = _Panel(selected="Default", order=["PvE", "Default"])

    helpers.on_profile_move_row(panel, "up")

    assert panel.reorder_calls == []
    assert panel.refresh_count == 0
    assert "stays at the bottom" in panel._status_var.value


def test_profile_insert_row_marks_inserted_profile_for_pending_selection() -> None:
    panel = _Panel(selected="PvE", order=["PvE", "Default"])
    created: list[str] = []
    panel._profile_state_snapshot = {"profiles": ["PvE", "Default"]}
    panel._create_profile_callback = lambda name: created.append(name)

    helpers.on_profile_insert_row(panel, "below")

    assert created == ["New Profile"]
    assert panel._profile_pending_selected_name == "New Profile"
    assert panel.refresh_count == 1


def test_sync_profile_table_prefers_pending_selected_profile_row() -> None:
    panel = _Panel(selected="Default", order=["Default"])
    panel._profile_table = _InsertProfileTable()
    panel._status_rules_map = helpers.status_rules_map
    panel._rule_context_state = helpers.rule_context_state
    panel._profile_pending_selected_name = "PvE"

    helpers.sync_profile_table(
        panel,
        status={"rules": {}},
        profiles=["PvE", "Default"],
        current_profile="Default",
    )

    assert panel._profile_table.selection_id == "row1"
    assert panel._profile_table.focus_id == "row1"
    assert panel._profile_pending_selected_name == ""


def test_sync_profile_table_preserves_user_selected_profile_over_active_row() -> None:
    panel = _Panel(selected="Default", order=["Default"])
    table = _InsertProfileTable()
    table.rows = {
        "old1": {"text": "1", "values": ("", "PvE", "", "", "", "", "", "", "")},
        "old2": {"text": "2", "values": ("✅", "Default", "X", "X", "X", "X", "X", "X", "X")},
    }
    table.selection_id = "old1"
    panel._profile_table = table
    panel._status_rules_map = helpers.status_rules_map
    panel._rule_context_state = helpers.rule_context_state

    helpers.sync_profile_table(
        panel,
        status={"rules": {}},
        profiles=["PvE", "Default"],
        current_profile="Default",
    )

    assert panel._profile_table.selection_id == "row1"
    assert panel._profile_table.focus_id == "row1"


def test_sync_profile_table_marks_active_column_for_current_profile_row() -> None:
    panel = _Panel(selected="Default", order=["Default"])
    panel._profile_table = _InsertProfileTable()
    panel._status_rules_map = helpers.status_rules_map
    panel._rule_context_state = helpers.rule_context_state

    helpers.sync_profile_table(
        panel,
        status={"rules": {}},
        profiles=["PvE", "Default"],
        current_profile="Default",
    )

    assert panel._profile_table.rows["row1"]["values"][0] == ""
    assert panel._profile_table.rows["row2"]["values"][0] == helpers.ACTIVE_COLUMN_CHECKMARK


def test_build_ship_table_rows_uses_unnamed_when_name_missing() -> None:
    rows = helpers._build_ship_table_rows(
        [
            {"ship_id": 91, "ship_name": "Type-11 Prospector", "ship_ident": "SW-29L", "ship_type": "Type-11"},
            {"ship_id": 67, "ship_name": "Kate Koss", "ship_ident": "", "ship_type": "Type-8"},
            {"ship_id": 68, "ship_name": "", "ship_ident": "TR-005", "ship_type": "Python"},
        ]
    )

    assert rows == [
        {"name": "Type-11 Prospector", "ship_id": 91, "ship_ident": "SW-29L", "type": "Type-11"},
        {"name": "Kate Koss", "ship_id": 67, "ship_ident": "", "type": "Type-8"},
        {"name": "Unnamed", "ship_id": 68, "ship_ident": "TR-005", "type": "Python"},
    ]


def test_sorted_ship_table_rows_supports_name_id_type_columns() -> None:
    rows = [
        {"name": "Bravo", "ship_id": 12, "ship_ident": "B-2", "type": "Type-9"},
        {"name": "Alpha", "ship_id": 30, "ship_ident": "A-3", "type": "Adder"},
        {"name": "Alpha", "ship_id": 10, "ship_ident": "A-1", "type": "Anaconda"},
    ]

    by_name = helpers._sorted_ship_table_rows(rows, column="name", descending=False)
    by_id_desc = helpers._sorted_ship_table_rows(rows, column="id", descending=True)
    by_type = helpers._sorted_ship_table_rows(rows, column="type", descending=False)
    by_apply = helpers._sorted_ship_table_rows(rows, column="apply", descending=False, checked_ids={30, 12})
    by_apply_desc = helpers._sorted_ship_table_rows(rows, column="apply", descending=True, checked_ids={30, 12})

    assert [row["ship_id"] for row in by_name] == [10, 30, 12]
    assert [row["ship_id"] for row in by_id_desc] == [12, 30, 10]
    assert [row["ship_id"] for row in by_type] == [30, 10, 12]
    assert [row["ship_id"] for row in by_apply] == [30, 12, 10]
    assert [row["ship_id"] for row in by_apply_desc] == [10, 12, 30]


def test_selected_ship_ids_for_rules_prefers_checked_apply_column() -> None:
    panel = _Panel(selected="PvE", order=["Default", "PvE"])
    panel._profile_ship_table = _ShipTable(
        selected=["r1", "r2"],
        values_by_row={
            "r1": ("[ ]", "Ship A", "A-1", "Type-A"),
            "r2": ("[ ]", "Ship B", "B-2", "Type-B"),
        },
    )
    panel._profile_ship_row_to_ship_id = {"r1": 10, "r2": 30}
    panel._profile_ship_checked_ids = {30}

    selected_ids = helpers.selected_ship_ids_for_rules(panel)

    assert selected_ids == [30]


def test_ship_apply_visual_uses_icons_when_available() -> None:
    check_on = object()
    check_off = object()
    panel = _Panel(selected="Default", order=["Default"])
    panel._profile_menu_icons = {"check_on": check_on, "check_off": check_off}

    assert helpers._ship_apply_visual(panel, True) == ("", check_on)
    assert helpers._ship_apply_visual(panel, False) == ("", check_off)


def test_sync_profile_ship_list_renders_apply_in_tree_column() -> None:
    panel = _Panel(selected="Default", order=["Default"])
    panel._profile_ship_table = _InsertShipTable()
    panel._profile_ship_checked_ids = {91}
    panel._profile_menu_icons = {}

    helpers.sync_profile_ship_list(
        panel,
        {
            "ships": [
                {
                    "ship_id": 91,
                    "ship_name": "Type-11 Prospector",
                    "ship_ident": "SW-29L",
                    "ship_type": "Type-11",
                }
            ]
        },
    )

    insert = panel._profile_ship_table.insert_calls[0]
    assert insert["text"] == "[x]"
    assert insert["values"] == ("Type-11 Prospector", "SW-29L", "Type-11")


def test_sync_profile_ship_list_labels_unnamed_ships_in_name_column() -> None:
    panel = _Panel(selected="Default", order=["Default"])
    panel._profile_ship_table = _InsertShipTable()
    panel._profile_ship_checked_ids = set()
    panel._profile_menu_icons = {}

    helpers.sync_profile_ship_list(
        panel,
        {
            "ships": [
                {
                    "ship_id": 68,
                    "ship_name": "",
                    "ship_ident": "TR-005",
                    "ship_type": "Python",
                }
            ]
        },
    )

    insert = panel._profile_ship_table.insert_calls[0]
    assert insert["text"] == "[ ]"
    assert insert["values"] == ("Unnamed", "TR-005", "Python")


def test_sync_profile_ship_list_shows_no_ships_hint_in_profiles_hint_only() -> None:
    panel = _Panel(selected="Default", order=["Default"])
    panel._profile_ship_table = _InsertShipTable()
    panel._profile_ship_checked_ids = set()
    panel._profile_menu_icons = {}

    helpers.sync_profile_ship_list(panel, {"ships": []})

    insert = panel._profile_ship_table.insert_calls[0]
    assert insert["values"] == ("no ships yet", "", "")
    assert panel._profile_ship_hint_var.value == helpers.NO_SHIPS_HINT
    assert panel._status_var.value == ""


def test_sync_profile_ship_list_clears_no_ships_hint_when_ships_exist() -> None:
    panel = _Panel(selected="Default", order=["Default"])
    panel._profile_ship_table = _InsertShipTable()
    panel._profile_ship_checked_ids = set()
    panel._profile_menu_icons = {}
    panel._profile_ship_hint_var.set(helpers.NO_SHIPS_HINT)
    panel._status_var.set(helpers.NO_SHIPS_HINT)

    helpers.sync_profile_ship_list(
        panel,
        {
            "ships": [
                {
                    "ship_id": 91,
                    "ship_name": "Type-11 Prospector",
                    "ship_ident": "SW-29L",
                    "ship_type": "Type-11",
                }
            ]
        },
    )

    assert panel._profile_ship_hint_var.value == ""
    assert panel._status_var.value == ""


def test_sync_profile_ship_list_clears_legacy_shared_no_ships_hint() -> None:
    panel = _Panel(selected="Default", order=["Default"])
    panel._profile_ship_table = _InsertShipTable()
    panel._profile_ship_checked_ids = set()
    panel._profile_menu_icons = {}
    panel._status_var.set("Swap ships in game and then close and reopen settings to have it show up on the ship list.")

    helpers.sync_profile_ship_list(
        panel,
        {
            "ships": [
                {
                    "ship_id": 91,
                    "ship_name": "Type-11 Prospector",
                    "ship_ident": "SW-29L",
                    "ship_type": "Type-11",
                }
            ]
        },
    )

    assert panel._profile_ship_hint_var.value == ""
    assert panel._status_var.value == ""


def test_profile_ship_table_click_apply_heading_sorts_apply_column() -> None:
    panel = _Panel(selected="PvE", order=["Default", "PvE"])
    panel._profile_ship_table = _ShipTableClick()
    calls: list[str] = []
    panel._on_profile_ship_sort = lambda column: calls.append(column)

    result = helpers.on_profile_ship_table_click(panel, _ClickEvent())

    assert result == "break"
    assert calls == ["apply"]


def test_profile_ship_table_click_ignored_when_in_main_ship_rule_unchecked() -> None:
    panel = _Panel(selected="PvE", order=["Default", "PvE"])
    panel._var_rule_in_main_ship = _BoolVar(False)
    panel._profile_ship_table = _ShipTableClick()
    calls: list[str] = []
    panel._on_profile_ship_sort = lambda column: calls.append(column)

    result = helpers.on_profile_ship_table_click(panel, _ClickEvent())

    assert result == "break"
    assert calls == []


def test_extract_profile_name_returns_trimmed_token() -> None:
    assert helpers._extract_profile_name("  Default ✅  ") == "Default ✅"
    assert helpers._extract_profile_name("PvE") == "PvE"


def test_profile_ship_table_double_click_toggles_apply_for_row() -> None:
    panel = _Panel(selected="PvE", order=["Default", "PvE"])
    table = _ShipTableDoubleClick()
    panel._profile_ship_table = table
    panel._profile_ship_row_to_ship_id = {"r1": 91}
    panel._profile_ship_checked_ids = set()
    panel._profile_menu_icons = {}

    result = helpers.on_profile_ship_table_double_click(panel, _ClickEvent(y=10))

    assert result == "break"
    assert panel._profile_ship_checked_ids == {91}
    assert table.updated["r1"]["text"] == "[x]"


def test_profile_ship_table_double_click_ignored_when_in_main_ship_rule_unchecked() -> None:
    panel = _Panel(selected="PvE", order=["Default", "PvE"])
    panel._var_rule_in_main_ship = _BoolVar(False)
    table = _ShipTableDoubleClick()
    panel._profile_ship_table = table
    panel._profile_ship_row_to_ship_id = {"r1": 91}
    panel._profile_ship_checked_ids = set()
    panel._profile_menu_icons = {}

    result = helpers.on_profile_ship_table_double_click(panel, _ClickEvent(y=10))

    assert result == "break"
    assert panel._profile_ship_checked_ids == set()


def test_in_main_ship_toggle_disables_ship_table_when_unchecked_for_custom_profile() -> None:
    panel = _Panel(selected="PvE", order=["Default", "PvE"])
    panel._var_rule_in_main_ship = _BoolVar(False)
    panel._profile_ship_table = _StateAwareShipTable()

    helpers.on_profile_in_main_ship_toggle(panel)

    assert panel._profile_ship_table.state_calls[-1] == ("disabled",)


def test_in_main_ship_toggle_enables_ship_table_when_checked_for_custom_profile() -> None:
    panel = _Panel(selected="PvE", order=["Default", "PvE"])
    panel._var_rule_in_main_ship = _BoolVar(True)
    panel._profile_ship_table = _StateAwareShipTable()

    helpers.on_profile_in_main_ship_toggle(panel)

    assert panel._profile_ship_table.state_calls[-1] == ("!disabled",)


def test_in_main_ship_toggle_keeps_ship_table_disabled_for_default_profile() -> None:
    panel = _Panel(selected="Default", order=["PvE", "Default"])
    panel._var_rule_in_main_ship = _BoolVar(True)
    panel._profile_ship_table = _StateAwareShipTable()

    helpers.on_profile_in_main_ship_toggle(panel)

    assert panel._profile_ship_table.state_calls[-1] == ("disabled",)


def test_profile_rule_toggle_applies_immediately() -> None:
    panel = _Panel(selected="PvE", order=["Default", "PvE"])
    panel._profile_ship_table = _StateAwareShipTable()
    panel._var_rule_in_main_ship = _BoolVar(False)
    panel._var_rule_in_srv = _BoolVar(True)
    panel._var_rule_in_fighter = _BoolVar(False)
    panel._var_rule_on_foot = _BoolVar(False)
    panel._var_rule_in_wing = _BoolVar(False)
    panel._var_rule_in_taxi = _BoolVar(False)
    panel._var_rule_in_multicrew = _BoolVar(False)
    panel._selected_ship_ids_for_rules = lambda: []
    calls: list[tuple[str, list[dict[str, str]]]] = []

    def _set_rules(profile_name: str, rules: list[dict[str, str]]) -> None:
        calls.append((profile_name, list(rules)))

    panel._set_profile_rules_callback = _set_rules

    helpers.on_profile_rule_toggle(panel)

    assert panel._profile_ship_table.state_calls[-1] == ("disabled",)
    assert calls == [("PvE", [{"context": "InSRV"}])]
    assert panel.refresh_count == 1


def test_profile_ship_table_double_click_applies_rules_immediately() -> None:
    panel = _Panel(selected="PvE", order=["Default", "PvE"])
    table = _ShipTableDoubleClick()
    panel._profile_ship_table = table
    panel._profile_ship_row_to_ship_id = {"r1": 91}
    panel._profile_ship_checked_ids = set()
    panel._profile_menu_icons = {}
    panel._var_rule_in_main_ship = _BoolVar(True)
    panel._var_rule_in_srv = _BoolVar(False)
    panel._var_rule_in_fighter = _BoolVar(False)
    panel._var_rule_on_foot = _BoolVar(False)
    panel._var_rule_in_wing = _BoolVar(False)
    panel._var_rule_in_taxi = _BoolVar(False)
    panel._var_rule_in_multicrew = _BoolVar(False)
    panel._selected_ship_ids_for_rules = lambda: helpers.selected_ship_ids_for_rules(panel)
    calls: list[tuple[str, list[dict[str, int | str]]]] = []

    def _set_rules(profile_name: str, rules: list[dict[str, int | str]]) -> None:
        calls.append((profile_name, list(rules)))

    panel._set_profile_rules_callback = _set_rules

    result = helpers.on_profile_ship_table_double_click(panel, _ClickEvent(y=10))

    assert result == "break"
    assert panel._profile_ship_checked_ids == {91}
    assert table.updated["r1"]["text"] == "[x]"
    assert calls == [("PvE", [{"context": "InMainShip", "ship_id": 91}])]
    assert panel.refresh_count == 1


def test_profile_table_double_click_active_column_sets_current_profile() -> None:
    panel = _Panel(selected="PvE", order=["Default", "PvE"])
    table = _ProfileTableDoubleClick(row_id="row2", column_id="#1")
    panel._profile_table = table
    calls: list[str] = []
    panel._on_profile_set_current = lambda: calls.append("set_current")

    helpers.on_profile_table_double_click(panel, _ClickEvent(x=5, y=10))

    assert table.selection_id == "row2"
    assert table.focus_id == "row2"
    assert calls == ["set_current"]
