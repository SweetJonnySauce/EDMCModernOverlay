import overlay_controller.controller.layout as layout


def test_selected_option_index_matches_case_insensitive() -> None:
    options = ["Default", "Mining", "Combat"]
    assert layout._selected_option_index(options, "mining") == 1


def test_selected_option_index_returns_none_when_missing() -> None:
    options = ["Default", "Mining", "Combat"]
    assert layout._selected_option_index(options, "Trade") is None


def test_selected_option_index_returns_none_for_empty_selection() -> None:
    options = ["Default", "Mining", "Combat"]
    assert layout._selected_option_index(options, "") is None
