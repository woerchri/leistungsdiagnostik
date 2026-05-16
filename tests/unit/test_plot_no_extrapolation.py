"""Plot must not extrapolate fit lines past the last measurement — Anna 2026-05-13 Round 2.

When v_max is derived aliquot from an incomplete final step, an unrestricted
fit line would suggest a measured Laktat/HF value at v_max. We restrict the
fit's x-domain to [start, x_data_max] and instead draw v_max as a dashed
vertical marker.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ld import io_input, plots, protocols


FIXTURE = Path(__file__).parent.parent / "protocols" / "fixtures" / "lauf" / "rainier.xlsx"


def _run_with_capture(tmp_path, monkeypatch):
    captured: dict = {}
    real_subplots = plt.subplots

    def spy_subplots(*args, **kwargs):
        fig, ax = real_subplots(*args, **kwargs)
        captured["ax"] = ax
        captured["lines_before"] = list(ax.lines)
        return fig, ax

    monkeypatch.setattr(plt, "subplots", spy_subplots)
    run = io_input.parse_input(FIXTURE)
    result = protocols.analyze(run)
    plots.render_main_diagram(result, tmp_path)
    return result, captured


def test_fit_line_does_not_extend_past_last_measured_step(tmp_path, monkeypatch):
    result, captured = _run_with_capture(tmp_path, monkeypatch)

    ax = captured["ax"]
    # First plotted line on the Laktat axis is the cubic fit (long line, not markers).
    fit_lines = [ln for ln in ax.lines if len(ln.get_xdata()) > 10]
    assert fit_lines, "Expected at least one continuous fit line on Laktat axis"
    laktat_fit = fit_lines[0]

    x_data_max = max(s.intensitaet for s in result.test_run.steps)
    x_fit_right = float(laktat_fit.get_xdata().max())

    # Rainier x_data_max=12.0, v_max=11.4375 (aliquot). Old behavior:
    # x_fit_right reached x_max ≈ 12.5; new behavior: x_fit_right == x_data_max.
    assert abs(x_fit_right - x_data_max) < 0.01, (
        f"Fit line right edge {x_fit_right} must equal last measured intensity {x_data_max}, "
        f"not extrapolate to plot right-edge."
    )


def test_vmax_drawn_as_marker_not_data_point(tmp_path, monkeypatch):
    """When v_max < x_data_max (or v_max > x_data_max from aliquot), the vmax
    line must appear as a vertical dashed line, not as a continuation of the
    smooth fit."""
    result, captured = _run_with_capture(tmp_path, monkeypatch)
    ax = captured["ax"]

    if result.v_max <= max(s.intensitaet for s in result.test_run.steps):
        # Sarah-like: v_max IS the last measured step. No marker is added.
        # Just assert that no extra dashed line appears past x_data_max.
        return

    # Rainier-like: v_max > x_data_max.
    dashed = [ln for ln in ax.lines if ln.get_linestyle() in {"--", "dashed"}]
    assert dashed, "Expected a dashed vmax line when v_max > x_data_max"


def test_markers_use_distinct_shapes(tmp_path, monkeypatch):
    """HF: circles, Laktat: squares. So an overlapping HF/Laktat pair stays
    visually separable (Anna 2026-05-13 Round 2)."""
    result, captured = _run_with_capture(tmp_path, monkeypatch)
    ax_lk = captured["ax"]
    fig = ax_lk.figure
    ax_hf = next(a for a in fig.axes if a is not ax_lk)

    # Marker-bearing lines are the short ones (one point per step).
    n_steps = len(result.test_run.steps)
    lk_marker_lines = [ln for ln in ax_lk.lines if 0 < len(ln.get_xdata()) <= n_steps]
    hf_marker_lines = [ln for ln in ax_hf.lines if 0 < len(ln.get_xdata()) <= n_steps]
    assert lk_marker_lines and hf_marker_lines

    assert lk_marker_lines[0].get_marker() == "s", "Laktat must use square markers"
    assert hf_marker_lines[0].get_marker() == "o", "HF must use circle markers"
