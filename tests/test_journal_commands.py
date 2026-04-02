from __future__ import annotations

from overlay_plugin.journal_commands import build_command_helper


class _DummyRuntime:
    def __init__(self) -> None:
        self.messages: list[str] = []
        self.status_overlay_calls: list[tuple[str, ...]] = []
        self.profile_overlay_calls: list[tuple[tuple[str, ...], str]] = []
        self.controller_launches = 0
        self.controller_enabled = True
        self.controller_should_fail = False
        self.opacity_calls: list[int] = []
        self.opacity_enabled = True
        self.group_set_calls: list[tuple[bool, tuple[str, ...] | None, str]] = []
        self.group_toggle_calls: list[tuple[tuple[str, ...] | None, str]] = []
        self.toggle_enabled = True
        self.toggle_should_fail = False
        self.group_status_enabled = True
        self.profile_switch_calls: list[str] = []
        self.profile_cycle_calls: list[int] = []
        self.profile_status_enabled = True
        self.profiles = ["Default", "Mining"]
        self.current_profile = "Default"
        self.group_states = {
            "BGS-Tally Colonisation": True,
            "BGS-Tally Objectives": True,
        }

    def send_test_message(self, text: str, x: int | None = None, y: int | None = None) -> None:
        self.messages.append(text)

    def launch_overlay_controller(self) -> None:
        if not self.controller_enabled:
            raise RuntimeError("disabled")
        if self.controller_should_fail:
            raise RuntimeError("boom")
        self.controller_launches += 1

    def set_payload_opacity_preference(self, value: int) -> None:
        if not self.opacity_enabled:
            raise RuntimeError("disabled")
        self.opacity_calls.append(value)

    def _set_plugin_groups_enabled(
        self, enabled: bool, *, group_names: list[str] | None = None, source: str = ""
    ) -> None:
        if not self.toggle_enabled:
            raise RuntimeError("disabled")
        targets = tuple(group_names) if group_names is not None else None
        self.group_set_calls.append((bool(enabled), targets, source))
        resolved = list(group_names) if group_names is not None else list(self.group_states.keys())
        for target in resolved:
            if target in self.group_states:
                self.group_states[target] = bool(enabled)

    def _toggle_plugin_groups_enabled(self, *, group_names: list[str] | None = None, source: str = "") -> None:
        if not self.toggle_enabled:
            raise RuntimeError("disabled")
        if self.toggle_should_fail:
            raise RuntimeError("boom")
        targets = tuple(group_names) if group_names is not None else None
        self.group_toggle_calls.append((targets, source))
        resolved = list(group_names) if group_names is not None else list(self.group_states.keys())
        for target in resolved:
            if target in self.group_states:
                self.group_states[target] = not self.group_states[target]

    def get_plugin_group_status_lines(self) -> list[str]:
        if not self.group_status_enabled:
            raise RuntimeError("disabled")
        return [
            f"{name}: {'On' if enabled else 'Off'}"
            for name, enabled in sorted(self.group_states.items(), key=lambda item: item[0].casefold())
        ]

    def send_group_status_overlay(self, lines: list[str]) -> None:
        self.status_overlay_calls.append(tuple(lines))

    def send_profile_status_overlay(self, profiles: list[str], current_profile: str = "") -> None:
        self.profile_overlay_calls.append((tuple(profiles), str(current_profile)))

    def set_current_profile(self, profile_name: str, source: str = "chat") -> dict[str, object]:
        self.profile_switch_calls.append(profile_name)
        self.current_profile = profile_name
        return {
            "profiles": list(self.profiles),
            "current_profile": self.current_profile,
            "manual_profile": self.current_profile,
        }

    def get_profile_status(self) -> dict[str, object]:
        if not self.profile_status_enabled:
            raise RuntimeError("disabled")
        return {
            "profiles": list(self.profiles),
            "current_profile": self.current_profile,
            "manual_profile": self.current_profile,
        }

    def cycle_profile(self, direction: int, source: str = "chat") -> dict[str, object]:
        self.profile_cycle_calls.append(int(direction))
        if not self.profiles:
            return self.get_profile_status()
        try:
            current_idx = next(
                idx for idx, value in enumerate(self.profiles) if value.casefold() == self.current_profile.casefold()
            )
        except StopIteration:
            current_idx = 0
        step = -1 if int(direction) < 0 else 1
        self.current_profile = self.profiles[(current_idx + step) % len(self.profiles)]
        return self.get_profile_status()


def build_helper(
    runtime: _DummyRuntime | None = None,
    *,
    toggle_argument: str | None = None,
) -> tuple[_DummyRuntime, object]:
    runtime = runtime or _DummyRuntime()
    helper = build_command_helper(
        runtime,
        command_prefix="!overlay",
        toggle_argument=toggle_argument,
        legacy_prefixes=["!overlay"],
    )
    return runtime, helper


def test_non_sendtext_events_ignored():
    runtime, helper = build_helper()
    assert helper.handle_entry({"event": "Location"}) is False
    assert runtime.messages == []


def test_other_bang_commands_ignored():
    runtime, helper = build_helper()
    assert helper.handle_entry({"event": "SendText", "Message": "!help"}) is False
    assert runtime.messages == []


def test_overlay_help_command():
    runtime, helper = build_helper()
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay help"}) is True
    assert runtime.messages[-1].startswith("Overlay commands:")


def test_overlay_help_uses_grouped_status_callback_when_available() -> None:
    runtime, helper = build_helper()
    grouped_messages: list[str] = []

    def _send_grouped(text: str) -> None:
        grouped_messages.append(text)

    runtime.send_command_status_overlay = _send_grouped  # type: ignore[attr-defined]
    runtime.send_test_message = lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("unexpected fallback"))  # type: ignore[method-assign]
    runtime, helper = build_helper(runtime)
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay help"}) is True
    assert grouped_messages
    assert grouped_messages[-1].startswith("Overlay commands:")
    assert runtime.messages == []


def test_overlay_launch_command():
    runtime, helper = build_helper()
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay"}) is True
    assert runtime.controller_launches == 1
    assert runtime.messages == []


def test_overlay_unknown_subcommand():
    runtime, helper = build_helper()
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay foo"}) is True
    assert runtime.messages == []


def test_overlay_cycle_subcommands_switch_profiles():
    runtime, helper = build_helper()
    runtime.current_profile = "Default"
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay next"}) is True
    assert runtime.current_profile == "Mining"
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay prev"}) is True
    assert runtime.current_profile == "Default"
    assert runtime.profile_cycle_calls == [1, -1]
    assert runtime.messages[-1] == "Overlay profile set to Default."
    assert runtime.group_set_calls == []
    assert runtime.group_toggle_calls == []
    assert runtime.opacity_calls == []


def test_overlay_opacity_numeric_command():
    runtime, helper = build_helper()
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay 42"}) is True
    assert runtime.opacity_calls == [42]
    assert runtime.controller_launches == 0
    assert runtime.messages == []


def test_overlay_opacity_percent_command():
    runtime, helper = build_helper()
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay 100%"}) is True
    assert runtime.opacity_calls == [100]
    assert runtime.controller_launches == 0
    assert runtime.messages == []


def test_overlay_opacity_out_of_range_ignored():
    runtime, helper = build_helper()
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay 101"}) is True
    assert runtime.opacity_calls == []
    assert runtime.controller_launches == 0
    assert runtime.messages == []


def test_overlay_opacity_invalid_value_ignored():
    runtime, helper = build_helper()
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay fifty"}) is True
    assert runtime.opacity_calls == []
    assert runtime.controller_launches == 0
    assert runtime.messages == []


def test_overlay_toggle_argument():
    runtime, helper = build_helper()
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay t"}) is True
    assert runtime.group_toggle_calls == [(None, "chat_toggle")]
    assert runtime.opacity_calls == []
    assert runtime.messages == []


def test_overlay_toggle_argument_case_insensitive():
    runtime, helper = build_helper()
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay T"}) is True
    assert runtime.group_toggle_calls == [(None, "chat_toggle")]


def test_overlay_toggle_argument_multi_character():
    runtime, helper = build_helper(toggle_argument="tog")
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay tog"}) is True
    assert runtime.group_toggle_calls == [(None, "chat_toggle")]


def test_overlay_opacity_takes_precedence_over_toggle():
    runtime, helper = build_helper()
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay t 60"}) is True
    assert runtime.opacity_calls == [60]
    assert runtime.group_toggle_calls == []
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay 60 t"}) is True
    assert runtime.opacity_calls == [60, 60]
    assert runtime.group_toggle_calls == []


def test_overlay_toggle_ignored_when_invalid_opacity_present():
    runtime, helper = build_helper()
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay t 101"}) is True
    assert runtime.opacity_calls == []
    assert runtime.group_toggle_calls == []


def test_overlay_launch_unavailable():
    runtime = _DummyRuntime()
    runtime.launch_overlay_controller = None  # type: ignore[assignment]
    runtime, helper = build_helper(runtime)
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay"}) is True
    assert "unavailable" in runtime.messages[-1].lower()


def test_overlay_opacity_unavailable():
    runtime = _DummyRuntime()
    runtime.set_payload_opacity_preference = None  # type: ignore[assignment]
    runtime, helper = build_helper(runtime)
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay 50"}) is True
    assert "opacity" in runtime.messages[-1].lower()


def test_overlay_toggle_unavailable():
    runtime = _DummyRuntime()
    runtime._toggle_plugin_groups_enabled = None  # type: ignore[assignment]
    runtime, helper = build_helper(runtime)
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay t"}) is True
    assert "toggle" in runtime.messages[-1].lower()


def test_overlay_launch_failure():
    runtime, helper = build_helper()
    runtime.controller_should_fail = True
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay"}) is True
    assert "failed" in runtime.messages[-1].lower()
    assert runtime.controller_launches == 0


def test_overlay_group_on_off_commands_target_and_global():
    runtime, helper = build_helper()
    assert helper.handle_entry({"event": "SendText", "Message": '!overlay on "BGS-Tally Objectives"'}) is True
    assert runtime.group_set_calls[-1] == (True, ("BGS-Tally Objectives",), "chat_on")
    assert runtime.opacity_calls == []

    assert helper.handle_entry({"event": "SendText", "Message": "!overlay off"}) is True
    assert runtime.group_set_calls[-1] == (False, None, "chat_off")
    assert runtime.opacity_calls == []


def test_overlay_group_action_phrase_coercion():
    runtime, helper = build_helper()
    forms = [
        '!overlay on "BGS-Tally Objectives"',
        '!overlay "BGS-Tally Objectives" on',
        '!overlay turn "BGS-Tally Objectives" on',
        '!overlay turn on "BGS-Tally Objectives"',
    ]
    for form in forms:
        assert helper.handle_entry({"event": "SendText", "Message": form}) is True
    assert runtime.group_set_calls == [
        (True, ("BGS-Tally Objectives",), "chat_on"),
        (True, ("BGS-Tally Objectives",), "chat_on"),
        (True, ("BGS-Tally Objectives",), "chat_on"),
        (True, ("BGS-Tally Objectives",), "chat_on"),
    ]


def test_overlay_group_action_phrase_coercion_for_off_and_toggle():
    runtime, helper = build_helper()
    off_forms = [
        '!overlay off "BGS-Tally Objectives"',
        '!overlay "BGS-Tally Objectives" off',
        '!overlay turn "BGS-Tally Objectives" off',
        '!overlay turn off "BGS-Tally Objectives"',
    ]
    toggle_forms = [
        '!overlay toggle "BGS-Tally Objectives"',
        '!overlay "BGS-Tally Objectives" toggle',
        '!overlay turn "BGS-Tally Objectives" toggle',
        '!overlay turn toggle "BGS-Tally Objectives"',
    ]

    for form in off_forms:
        assert helper.handle_entry({"event": "SendText", "Message": form}) is True
    assert runtime.group_set_calls == [
        (False, ("BGS-Tally Objectives",), "chat_off"),
        (False, ("BGS-Tally Objectives",), "chat_off"),
        (False, ("BGS-Tally Objectives",), "chat_off"),
        (False, ("BGS-Tally Objectives",), "chat_off"),
    ]

    for form in toggle_forms:
        assert helper.handle_entry({"event": "SendText", "Message": form}) is True
    assert runtime.group_toggle_calls == [
        (("BGS-Tally Objectives",), "chat_toggle"),
        (("BGS-Tally Objectives",), "chat_toggle"),
        (("BGS-Tally Objectives",), "chat_toggle"),
        (("BGS-Tally Objectives",), "chat_toggle"),
    ]


def test_overlay_status_command_outputs_sorted_lines():
    runtime, helper = build_helper()
    runtime.group_states["BGS-Tally Colonisation"] = False
    runtime.group_states["EDMCModernOverlay Group Status"] = False
    runtime.group_states["EDMCModernOverlay Plugin Status"] = True
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay status"}) is True
    assert runtime.status_overlay_calls == [
        (
            "BGS-Tally Colonisation: Off",
            "BGS-Tally Objectives: On",
        )
    ]
    assert runtime.messages == []


def test_overlay_status_command_falls_back_to_chat_message_when_overlay_sender_unavailable():
    runtime = _DummyRuntime()
    runtime.send_group_status_overlay = None  # type: ignore[assignment]
    runtime, helper = build_helper(runtime)
    runtime.group_states["BGS-Tally Colonisation"] = False
    runtime.group_states["EDMCModernOverlay Group Status"] = False
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay status"}) is True
    assert runtime.messages
    output = runtime.messages[-1]
    assert output.splitlines() == [
        "BGS-Tally Colonisation: Off",
        "BGS-Tally Objectives: On",
    ]


def test_overlay_profile_switch_command() -> None:
    runtime, helper = build_helper()
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay profile Mining"}) is True
    assert runtime.profile_switch_calls == ["Mining"]
    assert runtime.messages[-1] == "Overlay profile set to Mining."


def test_overlay_profile_cycle_subcommand() -> None:
    runtime, helper = build_helper()
    runtime.current_profile = "Default"
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay profile next"}) is True
    assert runtime.current_profile == "Mining"
    assert runtime.profile_cycle_calls == [1]


def test_overlay_profiles_command() -> None:
    runtime, helper = build_helper()
    runtime.current_profile = "Mining"
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay profiles"}) is True
    assert runtime.profile_overlay_calls == [(("Default", "Mining"), "Mining")]
    assert runtime.messages == []


def test_overlay_logical_commands_do_not_mutate_opacity_and_numeric_opacity_still_works():
    runtime, helper = build_helper()

    assert helper.handle_entry({"event": "SendText", "Message": '!overlay on "BGS-Tally Objectives"'}) is True
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay off"}) is True
    assert helper.handle_entry({"event": "SendText", "Message": "!overlay toggle"}) is True
    assert runtime.opacity_calls == []

    assert helper.handle_entry({"event": "SendText", "Message": "!overlay 55"}) is True
    assert runtime.opacity_calls == [55]
