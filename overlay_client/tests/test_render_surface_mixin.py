import math
from types import SimpleNamespace
from typing import Any, Optional, Tuple

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor

from overlay_client.group_transform import GroupKey
from overlay_client.legacy_store import LegacyItem
from overlay_client.paint_commands import _MessagePaintCommand, _RectPaintCommand, _VectorPaintCommand
from overlay_client.render_surface import RenderSurfaceMixin, _MeasuredText, _OverlayBounds, _ScreenBounds


class _StubMode:
    value = "fit"


class _StubTransform:
    def __init__(self) -> None:
        self.scale = 1.0
        self.scaled_size = (1.0, 1.0)
        self.mode = _StubMode()
        self.overflow_x = False
        self.overflow_y = False


class _StubMapper:
    def __init__(self, scale_x: float = 1.0, scale_y: float = 1.0) -> None:
        self.scale_x = scale_x
        self.scale_y = scale_y
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.transform = _StubTransform()


class _StubSurface(RenderSurfaceMixin):
    def __init__(self) -> None:
        # Only initialise members touched by the tested helpers.
        self._width = 100
        self._height = 50
        self._line_widths = {}
        self._line_width_defaults = {}
        self._text_cache = {}
        self._text_block_cache = {}
        self._text_cache_generation = 0
        self._text_cache_context: Optional[Tuple[str, Tuple[str, ...], float]] = None
        self._font_fallbacks: Tuple[str, ...] = ()
        self._font_family = "Test"
        self._measure_stats: dict[str, Any] = {}
        self._text_measurer = None
        self._dev_mode_enabled = False
        self._debug_config = SimpleNamespace(group_bounds_outline=False, payload_vertex_markers=False)
        self._grouping_adapter = None
        self._debug_message_point_size = 0.0
        self._last_logged_scale = None
        self._font_scale_diag = 0.0
        self._font_min_point = 1.0
        self._font_max_point = 72.0

    def width(self) -> int:
        return self._width

    def height(self) -> int:
        return self._height

    def devicePixelRatioF(self) -> float:
        return 2.0

    def _compute_legacy_mapper(self) -> _StubMapper:
        return _StubMapper()

    def _viewport_state(self) -> SimpleNamespace:
        width, height = self._render_surface_logical_size()
        return SimpleNamespace(width=float(width), height=float(height), device_ratio=1.0)

    def _update_message_font(self) -> None:
        return None

    def _current_physical_size(self) -> Tuple[float, float]:
        return (100.0, 50.0)

    def format_scale_debug(self) -> str:
        return "scale-debug"


class _StubFill:
    def __init__(self, scale: float = 1.0) -> None:
        self.scale = scale

    def screen_x(self, value: float) -> float:
        return value

    def screen_y(self, value: float) -> float:
        return value


class _StubGroupContext:
    def __init__(self) -> None:
        self.fill = _StubFill()
        self.transform_context = None
        self.scale = 1.0
        self.selected_anchor = None
        self.base_anchor_point = None
        self.anchor_for_transform = None
        self.base_translation_dx = 0.0
        self.base_translation_dy = 0.0


class _RectStubMapper:
    pass


class _RectSurface(_StubSurface):
    def __init__(self) -> None:
        super().__init__()
        self._line_width_defaults = {"legacy_rect": 2}

    def _line_width(self, key: str) -> int:
        return self._line_widths.get(key) or self._line_width_defaults.get(key, 1)

    def _viewport_state(self) -> object:
        return object()

    def _group_offsets(self, group_transform) -> Tuple[float, float]:  # noqa: ANN001
        return (0.0, 0.0)

    def _group_anchor_point(self, *args, **kwargs):  # noqa: ANN002, ANN003
        return None

    def _group_base_point(self, *args, **kwargs):  # noqa: ANN002, ANN003
        return None

    def _should_trace_payload(self, plugin_name: Optional[str], item_id: str) -> bool:
        return False

    def _compute_rect_transform(self, *args, **kwargs):  # noqa: ANN002, ANN003
        return ([(0.0, 0.0), (2.0, 0.0), (0.0, 1.0), (2.0, 1.0)], [], None, None)


class _CacheCaptureSurface(RenderSurfaceMixin):
    def __init__(self) -> None:
        self._render_pipeline = SimpleNamespace(_last_payload_results={})
        self._group_cache_generations = {}
        self._group_log_pending_base = {}
        self._group_log_pending_transform = {}
        self._group_log_next_allowed = {}
        self._logged_group_bounds = {}
        self._logged_group_transforms = {}
        self._payload_log_delay = 0.0
        self._cache_write_metadata = {}
        self.captured_base = None
        self.captured_transform = None

    def _update_group_cache_from_payloads(self, base_payloads, transform_payloads):  # noqa: ANN001
        self.captured_base = dict(base_payloads)
        self.captured_transform = dict(transform_payloads)
        return set()


def test_group_cache_skips_degenerate_payloads() -> None:
    surface = _CacheCaptureSurface()
    visible_key = ("PluginA", "G1")
    hidden_key = ("PluginA", "G2")
    rect_key = ("PluginA", "G3")
    surface._render_pipeline._last_payload_results = {
        "cache_base_payloads": {
            visible_key: {"plugin": "PluginA", "suffix": "G1"},
            hidden_key: {"plugin": "PluginA", "suffix": "G2"},
            rect_key: {"plugin": "PluginA", "suffix": "G3"},
        },
        "cache_transform_payloads": {
            visible_key: {"min_x": 0, "min_y": 0, "max_x": 10, "max_y": 10},
            hidden_key: {"min_x": 0, "min_y": 0, "max_x": 10, "max_y": 10},
            rect_key: {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0},
        },
        "active_group_keys": set(),
    }

    visible_item = LegacyItem(
        item_id="msg-1",
        kind="message",
        data={"__mo_ttl__": 1, "text": "hi"},
        plugin="PluginA",
    )
    hidden_item = LegacyItem(
        item_id="msg-2",
        kind="message",
        data={"__mo_ttl__": 0, "text": ""},
        plugin="PluginA",
    )
    rect_item = LegacyItem(
        item_id="rect-1",
        kind="rect",
        data={"w": 0, "h": 0},
        plugin="PluginA",
    )

    commands = [
        _MessagePaintCommand(
            group_key=GroupKey(*visible_key),
            group_transform=None,
            legacy_item=visible_item,
            bounds=(0, 0, 10, 10),
            overlay_bounds=(0.0, 0.0, 10.0, 10.0),
            effective_anchor=None,
            debug_log=None,
            text="hi",
        ),
        _MessagePaintCommand(
            group_key=GroupKey(*hidden_key),
            group_transform=None,
            legacy_item=hidden_item,
            bounds=(0, 0, 10, 10),
            overlay_bounds=(0.0, 0.0, 10.0, 10.0),
            effective_anchor=None,
            debug_log=None,
            text="",
        ),
        _RectPaintCommand(
            group_key=GroupKey(*rect_key),
            group_transform=None,
            legacy_item=rect_item,
            bounds=(0, 0, 0, 0),
            overlay_bounds=(0.0, 0.0, 0.0, 0.0),
            effective_anchor=None,
            debug_log=None,
        ),
    ]

    surface._apply_group_logging_payloads({}, {}, {}, {}, commands)

    assert surface.captured_base is not None
    assert surface.captured_transform is not None
    assert set(surface.captured_base.keys()) == {visible_key}
    assert set(surface.captured_transform.keys()) == {visible_key}


def test_reset_group_cache_clears_target_maps() -> None:
    cache_calls = {}

    class _CacheStub:
        def reset(self) -> None:
            cache_calls["reset"] = True

    class _ResetSurface(RenderSurfaceMixin):
        def __init__(self) -> None:
            self._group_cache = _CacheStub()
            self._last_visible_overlay_bounds_for_target = {("Plugin", "G1"): _OverlayBounds(0, 0, 10, 10)}
            self._last_overlay_bounds_for_target = {("Plugin", "G1"): _OverlayBounds(5, 5, 15, 15)}
            self._last_transform_by_group = {("Plugin", "G1"): object()}
            self._repaint_calls = []

        def _request_repaint(self, reason: str, *, immediate: bool = False) -> None:
            self._repaint_calls.append((reason, immediate))

    surface = _ResetSurface()
    surface.reset_group_cache()

    assert cache_calls.get("reset") is True
    assert surface._last_visible_overlay_bounds_for_target == {}
    assert surface._last_overlay_bounds_for_target == {}
    assert surface._last_transform_by_group == {}
    assert surface._repaint_calls == [("group_cache_reset", True)]


def _message_command(
    key: Tuple[str, Optional[str]],
    *,
    item_id: str = "msg-1",
    text: str = "BGS",
    bounds: Tuple[int, int, int, int] = (100, 100, 180, 120),
    color: str = "white",
) -> _MessagePaintCommand:
    left, top, right, bottom = bounds
    return _MessagePaintCommand(
        group_key=GroupKey(*key),
        group_transform=None,
        legacy_item=LegacyItem(item_id=item_id, kind="message", data={"text": text}, plugin=key[0]),
        bounds=bounds,
        overlay_bounds=(float(left), float(top), float(right), float(bottom)),
        effective_anchor=None,
        debug_log=None,
        text=text,
        color=QColor(color),
        point_size=12.0,
        x=left,
        baseline=bottom - 4,
        text_width=max(0, right - left),
        ascent=max(0, bottom - top - 4),
        descent=4,
    )


def _rect_command(
    key: Tuple[str, Optional[str]],
    *,
    item_id: str = "rect-1",
    bounds: Tuple[int, int, int, int] = (90, 90, 210, 130),
    fill: str = "#80000000",
) -> _RectPaintCommand:
    left, top, right, bottom = bounds
    return _RectPaintCommand(
        group_key=GroupKey(*key),
        group_transform=None,
        legacy_item=LegacyItem(
            item_id=item_id,
            kind="rect",
            data={"x": left, "y": top, "w": right - left, "h": bottom - top, "fill": fill, "color": "none"},
            plugin=key[0],
        ),
        bounds=bounds,
        overlay_bounds=(float(left), float(top), float(right), float(bottom)),
        effective_anchor=None,
        debug_log=None,
        brush=QBrush(QColor(fill)),
        x=left,
        y=top,
        width=max(0, right - left),
        height=max(0, bottom - top),
    )


def _broad_group_bounds() -> _ScreenBounds:
    bounds = _ScreenBounds()
    bounds.include_rect(0, 0, 3440, 1440)
    return bounds


def test_shell_raster_crop_uses_visible_command_bounds_not_broad_group_bounds() -> None:
    surface = _StubSurface()
    key = ("BGS-Tally", "main")
    commands = [
        _message_command(key, bounds=(100, 100, 180, 120)),
        _rect_command(key, bounds=(90, 90, 210, 130)),
    ]

    content_bounds, diagnostics = surface._shell_raster_crop_snapshot(
        {
            "commands": commands,
            "anchor_translation_by_group": {},
            "translations": {},
            "translated_bounds_by_group": {key: _broad_group_bounds()},
            "transform_by_group": {},
        }
    )

    assert content_bounds is not None
    assert content_bounds.to_payload() == {"x": 90, "y": 90, "width": 120, "height": 40}
    assert diagnostics["crop_source"] == "visible_paint_contributors"
    assert diagnostics["crop_contributor_count"] == 2
    assert diagnostics["crop_largest_contributors"][0]["source"] == "rect"


def test_shell_raster_crop_excludes_empty_transparent_and_zero_size_contributors() -> None:
    surface = _StubSurface()
    key = ("Plugin", "main")
    commands = [
        _message_command(key, item_id="empty-message", text="", bounds=(0, 0, 200, 20)),
        _rect_command(key, item_id="transparent-rect", bounds=(0, 0, 300, 100), fill="#00000000"),
        _rect_command(key, item_id="zero-rect", bounds=(0, 0, 0, 100), fill="#80000000"),
        _message_command(key, item_id="visible-message", text="visible", bounds=(50, 60, 150, 80)),
    ]

    content_bounds, diagnostics = surface._shell_raster_crop_snapshot(
        {
            "commands": commands,
            "anchor_translation_by_group": {},
            "translations": {},
            "translated_bounds_by_group": {key: _broad_group_bounds()},
            "transform_by_group": {},
        }
    )

    assert content_bounds is not None
    assert content_bounds.to_payload() == {"x": 50, "y": 60, "width": 100, "height": 20}
    assert diagnostics["crop_contributor_count"] == 1
    assert diagnostics["crop_largest_contributors"][0]["item_id"] == "visible-message"


def test_shell_raster_crop_ignores_transparent_group_background() -> None:
    surface = _StubSurface()
    key = ("Plugin", "main")
    command = _message_command(key, bounds=(50, 60, 150, 80))
    transform = SimpleNamespace(background_color="#00000000", background_border_color="", background_border_width=0)

    content_bounds, diagnostics = surface._shell_raster_crop_snapshot(
        {
            "commands": [command],
            "anchor_translation_by_group": {},
            "translations": {},
            "translated_bounds_by_group": {key: _broad_group_bounds()},
            "transform_by_group": {key: transform},
        }
    )

    assert content_bounds is not None
    assert content_bounds.to_payload() == {"x": 50, "y": 60, "width": 100, "height": 20}
    assert diagnostics["crop_contributor_count"] == 1


def test_shell_raster_crop_keeps_full_width_visible_vector_line() -> None:
    surface = _StubSurface()
    surface._line_width_defaults = {"vector_line": 2, "vector_marker": 2, "vector_cross": 2}
    key = ("Plugin", "vectors")
    command = _VectorPaintCommand(
        group_key=GroupKey(*key),
        group_transform=None,
        legacy_item=LegacyItem(
            item_id="vector-1",
            kind="vector",
            data={"points": [{"x": 0, "y": 50}, {"x": 3440, "y": 50}]},
            plugin=key[0],
        ),
        bounds=(0, 50, 3440, 50),
        overlay_bounds=(0.0, 50.0, 3440.0, 50.0),
        effective_anchor=None,
        debug_log=None,
        vector_payload={"base_color": "white", "points": [{"x": 0, "y": 50}, {"x": 3440, "y": 50}]},
        scale=1.0,
        base_offset_x=0.0,
        base_offset_y=0.0,
    )

    content_bounds, diagnostics = surface._shell_raster_crop_snapshot(
        {
            "commands": [command],
            "anchor_translation_by_group": {},
            "translations": {},
            "translated_bounds_by_group": {key: _broad_group_bounds()},
            "transform_by_group": {},
        }
    )

    assert content_bounds is not None
    payload = content_bounds.to_payload()
    assert payload["width"] >= 3440
    assert payload["height"] > 0
    assert diagnostics["crop_largest_contributors"][0]["source"] == "vector"


def test_line_width_respects_override_defaults() -> None:
    surface = _StubSurface()
    surface._line_width_defaults = {"custom": 7}
    assert surface._line_width("custom") == 7
    surface._line_widths["custom"] = 3
    assert surface._line_width("custom") == 3


def test_update_auto_legacy_scale_uses_overlay_module_scale_fn(monkeypatch: pytest.MonkeyPatch) -> None:
    import overlay_client.overlay_client as overlay_module

    calls: list[Tuple[float, float]] = []

    def fake_scale_fn(mapper: _StubMapper, state: Any) -> Tuple[float, float]:
        calls.append((mapper.scale_x, mapper.scale_y))
        return 0.5, 0.25

    monkeypatch.setattr(overlay_module, "legacy_scale_components", fake_scale_fn, raising=False)

    surface = _StubSurface()
    mapper = _StubMapper(scale_x=1.5, scale_y=2.0)
    surface._compute_legacy_mapper = lambda: mapper  # type: ignore[assignment]
    surface._update_auto_legacy_scale(100, 50)

    assert calls == [(1.5, 2.0)]
    expected_diag = math.sqrt((0.5 * 0.5 + 0.25 * 0.25) / 2.0)
    assert math.isclose(surface._font_scale_diag, expected_diag, rel_tol=1e-6)
    assert surface._last_logged_scale is not None


def test_shell_raster_render_size_override_is_scoped() -> None:
    surface = _StubSurface()
    surface._width = 46
    surface._height = 173
    surface._font_scale_diag = 0.18

    assert surface._render_surface_logical_size() == (46, 173)
    with surface._temporary_shell_raster_render_size((3440, 1440)):
        assert surface._render_surface_logical_size() == (3440, 1440)
        assert surface._font_scale_diag > 0.18

    assert surface._render_surface_logical_size() == (46, 173)
    assert surface._font_scale_diag == 0.18
    assert not hasattr(surface, "_shell_raster_render_size_override")


def test_legacy_render_context_uses_shell_raster_render_size_override() -> None:
    surface = _StubSurface()
    surface._width = 46
    surface._height = 173

    with surface._temporary_shell_raster_render_size((3440, 1440)):
        context = surface._build_legacy_render_context()

    assert context.width == 3440
    assert context.height == 1440


def test_measure_text_uses_injected_measurer_and_resets_context() -> None:
    surface = _StubSurface()
    surface._text_cache = {"placeholder": (1, 2, 3)}
    surface._text_block_cache = {"placeholder": (4, 5)}

    surface._ensure_text_cache_context("TestFamily")

    assert surface._text_cache == {}
    assert surface._text_block_cache == {}
    assert surface._text_cache_generation == 1
    assert surface._text_cache_context == ("TestFamily", (), 2.0)

    measurer_calls: list[Tuple[str, float, str]] = []

    def measurer(text: str, point_size: float, family: str) -> _MeasuredText:
        measurer_calls.append((text, point_size, family))
        return _MeasuredText(width=10, ascent=2, descent=1)

    surface._text_measurer = measurer
    measured = surface._measure_text("hello", 12.0, "TestFamily")

    assert measured == (10, 2, 1)
    assert measurer_calls == [("hello", 12.0, "TestFamily")]


def test_qcolor_from_background_parses_rgba() -> None:
    color = RenderSurfaceMixin._qcolor_from_background("#11223344")
    assert isinstance(color, QColor)
    assert (color.red(), color.green(), color.blue(), color.alpha()) == (0x22, 0x33, 0x44, 0x11)


def test_qcolor_from_background_accepts_named_colors() -> None:
    color = RenderSurfaceMixin._qcolor_from_background("red")
    assert isinstance(color, QColor)
    assert color.isValid()


def _build_rect_command(surface: _RectSurface, border_spec: str, *, fill_spec: str = "#112233"):
    legacy_item = LegacyItem(
        item_id="rect-1",
        kind="rect",
        data={"color": border_spec, "fill": fill_spec, "x": 1.0, "y": 2.0, "w": 3.0, "h": 4.0},
        plugin="plugin",
    )
    return surface._build_rect_command(legacy_item, _RectStubMapper(), GroupKey("plugin"), None, None)


@pytest.mark.parametrize("border_spec", ["", "none", "dd5500,"])
def test_rect_command_invalid_border_color_skips_pen(monkeypatch: pytest.MonkeyPatch, border_spec: str) -> None:
    surface = _RectSurface()
    monkeypatch.setattr(
        "overlay_client.render_surface.build_group_context",
        lambda *args, **kwargs: _StubGroupContext(),
    )

    cmd = _build_rect_command(surface, border_spec)

    assert cmd is not None
    assert cmd.pen.style() == Qt.PenStyle.NoPen
    assert cmd.brush.color().name() == QColor("#112233").name()


def test_rect_command_valid_border_color_uses_pen(monkeypatch: pytest.MonkeyPatch) -> None:
    surface = _RectSurface()
    monkeypatch.setattr(
        "overlay_client.render_surface.build_group_context",
        lambda *args, **kwargs: _StubGroupContext(),
    )

    cmd = _build_rect_command(surface, "#ff00ff")

    assert cmd is not None
    assert cmd.pen.style() == Qt.PenStyle.SolidLine
    assert cmd.pen.color().name() == QColor("#ff00ff").name()
    assert cmd.pen.width() == surface._line_width("legacy_rect")
