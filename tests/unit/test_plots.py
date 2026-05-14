"""Plot rendering tests — assert behaviour (axis ranges, zone bands), not pixel-level output.
PNG bytes vary across matplotlib versions; we test invariants instead."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ld import io_input, plots, protocols


FIXTURE = Path(__file__).parent.parent / "protocols" / "fixtures" / "lauf" / "rainier.xlsx"


def _render(tmp_path):
    run = io_input.parse_input(FIXTURE)
    result = protocols.analyze(run)
    out = plots.render_main_diagram(result, tmp_path)
    return result, out


def test_plot_file_written(tmp_path):
    _, out = _render(tmp_path)
    assert out.exists()
    assert out.suffix == ".png"
    assert out.stat().st_size > 1_000  # not an empty file


def test_x_axis_includes_last_measured_step(tmp_path, monkeypatch):
    """Per Anna 2026-05-13: 'letzter Datenpunkt ist nicht mehr sichtbar'.
    x-axis must extend past the last measured step intensity, not stop at v_max."""
    captured: dict = {}
    real_subplots = plt.subplots

    def spy_subplots(*args, **kwargs):
        fig, ax = real_subplots(*args, **kwargs)
        captured["ax"] = ax
        return fig, ax

    monkeypatch.setattr(plt, "subplots", spy_subplots)
    result, _ = _render(tmp_path)

    ax = captured["ax"]
    x_left, x_right = ax.get_xlim()
    last_step = max(s.intensitaet for s in result.test_run.steps)
    # Rainier last step is 12.0; v_max is 11.4375 (aliquot).
    # Old behavior clipped x at v_max → datapoint at 12.0 invisible.
    assert x_right > last_step, (
        f"x-axis right edge {x_right} must extend past last step intensity {last_step}"
    )


def test_hf_axis_max_has_plus_10_padding(tmp_path, monkeypatch):
    """Per Anna 2026-05-13: HF y-max = round-up(max)/10 * 10 PLUS 10."""
    captured: dict = {}
    real_subplots = plt.subplots

    def spy_subplots(*args, **kwargs):
        fig, ax = real_subplots(*args, **kwargs)
        captured["ax_lk"] = ax
        return fig, ax

    monkeypatch.setattr(plt, "subplots", spy_subplots)
    result, _ = _render(tmp_path)

    # The HF axis is the twinx of ax_lk; find it.
    ax_lk = captured["ax_lk"]
    twins = ax_lk.figure.axes
    ax_hf = next(a for a in twins if a is not ax_lk)
    _, hf_top = ax_hf.get_ylim()

    hf_values = [s.herzfrequenz_bpm for s in result.test_run.steps if s.herzfrequenz_bpm]
    # Rainier max HF is 173 → round-up to 180 → +10 = 190.
    import math
    expected_top = math.ceil(max(hf_values) / 10) * 10 + 10
    assert hf_top == expected_top, f"HF axis top should be {expected_top}, got {hf_top}"


def test_zone_bands_drawn(tmp_path, monkeypatch):
    """Each emitted zone (Z1..Z6) draws an axvspan band."""
    captured: dict = {}
    real_subplots = plt.subplots
    spans: list = []

    def spy_subplots(*args, **kwargs):
        fig, ax = real_subplots(*args, **kwargs)
        # Wrap axvspan to count calls
        real_axvspan = ax.axvspan

        def spy_axvspan(*a, **kw):
            spans.append((a, kw))
            return real_axvspan(*a, **kw)

        ax.axvspan = spy_axvspan
        captured["ax"] = ax
        return fig, ax

    monkeypatch.setattr(plt, "subplots", spy_subplots)
    result, _ = _render(tmp_path)

    # Rainier has all 6 zones present (Z1 is emitted because Z2-upper is valid).
    emitted_zone_count = len(result.zones_final)
    assert len(spans) == emitted_zone_count, (
        f"Expected {emitted_zone_count} zone bands, got {len(spans)}"
    )
    # Bands should be drawn with alpha < 1 (transparent).
    for args, kwargs in spans:
        assert kwargs.get("alpha", 1.0) < 1.0
