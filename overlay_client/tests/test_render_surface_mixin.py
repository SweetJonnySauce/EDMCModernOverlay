import math
from types import SimpleNamespace
from typing import Any, Optional, Tuple

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QPen

from overlay_client.group_transform import GroupKey
from overlay_client.legacy_store import LegacyItem
from overlay_client.paint_commands import _CirclePaintCommand, _MessagePaintCommand, _RectPaintCommand, _VectorPaintCommand
from overlay_client.render_surface import (
    RenderSurfaceMixin,
    _MeasuredText,
    _OverlayBounds,
    _ScreenBounds,
    _StrokeWidthSpec,
)


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
    def __init__(self, scale: float = 1.0) -> None:
        self.fill = _StubFill()
        self.transform_context = None
        self.scale = scale
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


class _CircleSurface(_RectSurface):
    def __init__(self) -> None:
        super().__init__()
        self.rect_transform_calls: list[Tuple[object, ...]] = []

    def _group_offsets(self, group_transform) -> Tuple[float, float]:  # noqa: ANN001
        return (getattr(group_transform, "dx", 0.0), getattr(group_transform, "dy", 0.0))

    def _compute_rect_transform(self, *args, **kwargs):  # noqa: ANN002, ANN003
        self.rect_transform_calls.append(args)
        return (
            [(100.2, 200.4), (140.7, 200.4), (100.2, 220.9), (140.7, 220.9)],
            [(90.0, 190.0), (130.0, 190.0), (90.0, 210.0), (130.0, 210.0)],
            (80.0, 180.0, 150.0, 230.0),
            (101.0, 201.0),
        )


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


def _build_rect_command(
    surface: _RectSurface,
    border_spec: str,
    *,
    fill_spec: str = "#112233",
    thickness: float | None = None,
):
    data = {"color": border_spec, "fill": fill_spec, "x": 1.0, "y": 2.0, "w": 3.0, "h": 4.0}
    if thickness is not None:
        data["thickness"] = thickness
    legacy_item = LegacyItem(
        item_id="rect-1",
        kind="rect",
        data=data,
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


@pytest.mark.parametrize(("scale", "expected_width"), [(0.5, 2), (1.0, 2), (2.0, 2)])
def test_explicit_rect_thickness_uses_unscaled_logical_pixels(
    monkeypatch: pytest.MonkeyPatch,
    scale: float,
    expected_width: int,
) -> None:
    surface = _RectSurface()
    monkeypatch.setattr(
        "overlay_client.render_surface.build_group_context",
        lambda *args, **kwargs: _StubGroupContext(scale=scale),
    )

    cmd = _build_rect_command(surface, "#ff00ff", thickness=2)

    assert cmd.pen.width() == expected_width
    assert cmd.pen.joinStyle() == Qt.PenJoinStyle.MiterJoin


@pytest.mark.parametrize(("scale", "thickness", "expected_width"), [(0.5, 1, 1), (1.0, 1, 1), (2.0, 1, 1), (2.0, 3, 3)])
def test_explicit_circle_thickness_uses_unscaled_logical_pixels(
    monkeypatch: pytest.MonkeyPatch,
    scale: float,
    thickness: float,
    expected_width: int,
) -> None:
    surface = _CircleSurface()
    monkeypatch.setattr(
        "overlay_client.render_surface.build_group_context",
        lambda *args, **kwargs: _StubGroupContext(scale=scale),
    )

    cmd = _build_circle_command(surface, thickness=thickness)

    assert cmd.pen.width() == expected_width
    assert cmd.pen.joinStyle() == Qt.PenJoinStyle.BevelJoin


def test_omitted_rect_thickness_keeps_unscaled_legacy_default(monkeypatch: pytest.MonkeyPatch) -> None:
    surface = _RectSurface()
    monkeypatch.setattr(
        "overlay_client.render_surface.build_group_context",
        lambda *args, **kwargs: _StubGroupContext(scale=2.0),
    )

    cmd = _build_rect_command(surface, "#ff00ff")

    assert cmd.pen.width() == surface._line_width("legacy_rect")


def test_omitted_circle_thickness_keeps_unscaled_legacy_default(monkeypatch: pytest.MonkeyPatch) -> None:
    surface = _CircleSurface()
    monkeypatch.setattr(
        "overlay_client.render_surface.build_group_context",
        lambda *args, **kwargs: _StubGroupContext(scale=2.0),
    )

    cmd = _build_circle_command(surface, thickness=None)

    assert cmd.pen.width() == surface._line_width("legacy_rect")


def test_explicit_rect_thickness_uses_miter_join_without_changing_legacy_join(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    surface = _RectSurface()
    monkeypatch.setattr(
        "overlay_client.render_surface.build_group_context",
        lambda *args, **kwargs: _StubGroupContext(),
    )

    explicit_command = _build_rect_command(surface, "#ff00ff", thickness=2)
    legacy_command = _build_rect_command(surface, "#ff00ff")

    assert explicit_command.pen.joinStyle() == Qt.PenJoinStyle.MiterJoin
    assert legacy_command.pen.joinStyle() == Qt.PenJoinStyle.BevelJoin


def test_explicit_stroke_resolution_copies_the_source_pen(monkeypatch: pytest.MonkeyPatch) -> None:
    surface = _RectSurface()
    monkeypatch.setattr(
        "overlay_client.render_surface.build_group_context",
        lambda *args, **kwargs: _StubGroupContext(scale=2.0),
    )
    source_pen = QPen(QColor("#ff00ff"))
    source_pen.setWidth(9)
    legacy_item = LegacyItem(item_id="pen-copy", kind="rect", data={}, plugin="plugin")

    cmd = surface._build_bounded_shape_command(
        legacy_item,
        _RectStubMapper(),
        GroupKey("plugin"),
        None,
        None,
        kind="rect",
        pen=source_pen,
        brush=QBrush(Qt.BrushStyle.NoBrush),
        stroke_width=_StrokeWidthSpec(explicit_pixel_width=2),
        raw_x=1,
        raw_y=2,
        raw_w=3,
        raw_h=4,
    )

    assert source_pen.width() == 9
    assert cmd.pen is not source_pen
    assert cmd.pen.width() == 2


def _build_circle_command(
    surface: _CircleSurface,
    *,
    border_spec: str = "#ff00ff",
    fill_spec: str = "#112233",
    group_transform=None,
    thickness: Optional[float] = 5.0,
):
    data = {
        "color": border_spec,
        "fill": fill_spec,
        "x": 10.0,
        "y": 20.0,
        "radius": 3.0,
    }
    if thickness is not None:
        data["thickness"] = thickness
    legacy_item = LegacyItem(
        item_id="circle-1",
        kind="circle",
        data=data,
        plugin="plugin",
    )
    return surface._build_circle_command(legacy_item, _RectStubMapper(), GroupKey("plugin"), group_transform, None)


def test_circle_command_derives_square_and_reuses_transformed_group_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    surface = _CircleSurface()
    monkeypatch.setattr(
        "overlay_client.render_surface.build_group_context",
        lambda *args, **kwargs: _StubGroupContext(),
    )
    group_transform = SimpleNamespace(dx=1.25, dy=-2.5)

    cmd = _build_circle_command(surface, group_transform=group_transform)

    assert isinstance(cmd, _CirclePaintCommand)
    assert surface.rect_transform_calls[0][7:11] == (7.0, 17.0, 6.0, 6.0)
    assert surface.rect_transform_calls[0][11:13] == (1.25, -2.5)
    assert cmd.pen.width() == 5
    assert cmd.pen.color().name() == QColor("#ff00ff").name()
    assert cmd.brush.color().name() == QColor("#112233").name()
    assert (cmd.x, cmd.y, cmd.width, cmd.height) == (100, 200, 40, 20)
    assert cmd.bounds == (100, 200, 140, 220)
    assert cmd.overlay_bounds == (100.2, 200.4, 140.7, 220.9)
    assert cmd.base_overlay_bounds == (90.0, 190.0, 130.0, 210.0)
    assert cmd.reference_overlay_bounds == (80.0, 180.0, 150.0, 230.0)
    assert cmd.effective_anchor == (101.0, 201.0)
    assert cmd.cycle_anchor == (120, 210)
    assert cmd.debug_vertices == [(100, 200), (140, 200), (100, 220), (140, 220)]


@pytest.mark.parametrize(
    ("border_spec", "fill_spec"),
    [("none", "#112233"), ("not-a-colour", ""), ("#ff00ff", "not-a-colour")],
)
def test_circle_command_uses_no_pen_or_no_brush_for_transparent_styles(
    monkeypatch: pytest.MonkeyPatch,
    border_spec: str,
    fill_spec: str,
) -> None:
    surface = _CircleSurface()
    monkeypatch.setattr(
        "overlay_client.render_surface.build_group_context",
        lambda *args, **kwargs: _StubGroupContext(),
    )

    cmd = _build_circle_command(surface, border_spec=border_spec, fill_spec=fill_spec)

    assert cmd is not None
    if border_spec in {"none", "not-a-colour"}:
        assert cmd.pen.style() == Qt.PenStyle.NoPen
    if not fill_spec or fill_spec == "not-a-colour":
        assert cmd.brush.style() == Qt.BrushStyle.NoBrush


def test_circle_dispatch_contributes_square_bounds_anchor_and_cycle_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    surface = _CircleSurface()
    circle = LegacyItem(
        item_id="circle-dispatch",
        kind="circle",
        data={"color": "#ff00ff", "fill": "#112233", "x": 10, "y": 20, "radius": 3, "thickness": 5},
        plugin="plugin",
    )
    group_key = GroupKey("plugin", "group")
    surface._payload_model = SimpleNamespace(store=SimpleNamespace(items=lambda: [(circle.item_id, circle)]))
    surface._group_coordinator = SimpleNamespace(resolve_group_key=lambda *args: group_key)
    surface._grouping_helper = SimpleNamespace(get_transform=lambda key: SimpleNamespace(dx=1.25, dy=-2.5))
    surface._override_manager = object()
    monkeypatch.setattr(
        "overlay_client.render_surface.build_group_context",
        lambda *args, **kwargs: _StubGroupContext(),
    )

    commands, bounds_by_group, overlay_bounds_by_group, anchors_by_group, transforms_by_group = (
        surface._build_legacy_commands_for_pass(_RectStubMapper(), None)
    )

    assert len(commands) == 1
    assert isinstance(commands[0], _CirclePaintCommand)
    assert bounds_by_group[group_key.as_tuple()].__dict__ == {
        "min_x": 100,
        "min_y": 200,
        "max_x": 140,
        "max_y": 220,
    }
    assert overlay_bounds_by_group[group_key.as_tuple()].__dict__ == {
        "min_x": 100.2,
        "min_y": 200.4,
        "max_x": 140.7,
        "max_y": 220.9,
    }
    assert anchors_by_group == {group_key.as_tuple(): (101.0, 201.0)}
    assert transforms_by_group[group_key.as_tuple()].dx == 1.25
    assert commands[0].cycle_anchor == (120, 210)
