from __future__ import annotations

import json
import math

import pytest

from scripts import monitor_to_canonical


def test_converts_a_four_by_three_monitor_rect_to_canonical_coordinates() -> None:
    result = monitor_to_canonical.monitor_rect_to_canonical(
        monitor_width=2560,
        monitor_height=1920,
        x=200,
        y=400,
        width=600,
        height=800,
    )

    assert result == {"x": 100.0, "y": 200.0, "w": 300.0, "h": 400.0}


def test_default_fill_mode_reverses_uniform_scale_on_widescreen_monitor() -> None:
    result = monitor_to_canonical.monitor_rect_to_canonical(
        monitor_width=1920,
        monitor_height=1080,
        x=300,
        y=450,
        width=600,
        height=300,
    )

    assert result == {"x": 200.0, "y": 300.0, "w": 400.0, "h": 200.0}


def test_fit_mode_removes_letterbox_offset_before_scaling() -> None:
    result = monitor_to_canonical.monitor_rect_to_canonical(
        monitor_width=1920,
        monitor_height=1080,
        x=240,
        y=0,
        width=450,
        height=225,
        scale_mode="fit",
    )

    assert result == {"x": 0.0, "y": 0.0, "w": 400.0, "h": 200.0}


@pytest.mark.parametrize("monitor_width, monitor_height", [(0, 1080), (1920, -1), (math.inf, 1080)])
def test_rejects_non_positive_or_non_finite_monitor_dimensions(monitor_width: float, monitor_height: float) -> None:
    with pytest.raises(ValueError, match="positive finite"):
        monitor_to_canonical.monitor_rect_to_canonical(
            monitor_width=monitor_width,
            monitor_height=monitor_height,
            x=0,
            y=0,
            width=1,
            height=1,
        )


def test_command_line_outputs_canonical_rectangle_as_json(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = monitor_to_canonical.main(
        [
            "--monitor-width",
            "2560",
            "--monitor-height",
            "1920",
            "--x",
            "200",
            "--y",
            "400",
            "--w",
            "600",
            "--h",
            "800",
        ]
    )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == {"x": 100.0, "y": 200.0, "w": 300.0, "h": 400.0}
