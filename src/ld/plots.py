from __future__ import annotations

import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from ld.types import AnalysisResult


_FIGSIZE = (10.0, 6.0)
_DPI = 150
_COLOR_LAKTAT = "#E63946"   # Rot — Laktatkurve
_COLOR_HF = "#1F77B4"        # Blau — HF-Linie

# Training-zone background palette (Anna 2026-05-13 — transparent, hochwertig).
# Names mirror the German feedback labels. Alpha tuned for printability without
# overwhelming the data lines.
_ZONE_COLORS: dict[str, str] = {
    "Z1": "#9CC8E6",  # Hellblau
    "Z2": "#7ED957",  # Grün
    "Z3": "#FFD93D",  # Gelb
    "Z4": "#E0B100",  # Dunkelgelb
    "Z5": "#FF8A33",  # Orange
    "Z6": "#E63946",  # Rot
}
_ZONE_ALPHA = 0.18


def render_main_diagram(result: AnalysisResult, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "diagramm.png"

    proto = result.test_run.testprotokoll
    steps = result.test_run.steps
    x_data = np.array([s.intensitaet for s in steps], dtype=float)
    lk_data = np.array([
        s.laktat_mmol if s.laktat_mmol is not None else np.nan for s in steps
    ])
    hf_data = np.array([
        s.herzfrequenz_bpm if s.herzfrequenz_bpm is not None else np.nan for s in steps
    ])

    # X-axis range: include start, last measured step AND v_max (whichever is
    # rightmost), plus padding so the last data point stays visible.
    # Bug Anna flagged 2026-05-13: "letzter Datenpunkt ist nicht mehr sichtbar".
    x_min = proto.anfangsbelastung
    x_data_max = float(np.nanmax(x_data)) if len(x_data) else x_min
    x_rightmost = max(result.v_max, x_data_max)
    x_padding = proto.stufeninkrement * 0.5  # half an increment of breathing room
    x_max = x_rightmost + x_padding

    x_fine = np.linspace(x_min, x_max, 200)
    lk_fit = np.array([result.cubic.predict(x) for x in x_fine])
    hf_fit = np.array([result.hf_linear.predict(x) for x in x_fine])

    fig, ax_lk = plt.subplots(figsize=_FIGSIZE, dpi=_DPI)

    # --- Training-zone background bands (drawn FIRST so data plots over them).
    _draw_zone_bands(ax_lk, result, x_min=x_min, x_max=x_max)

    # --- Laktat (left axis, red).
    ax_lk.plot(x_fine, lk_fit, color=_COLOR_LAKTAT, linewidth=2, zorder=3)
    ax_lk.plot(x_data, lk_data, "o", color=_COLOR_LAKTAT, markersize=6, zorder=4)
    ax_lk.set_xlabel(_x_label_de(result))
    ax_lk.set_ylabel("Laktat (mmol/l)", color=_COLOR_LAKTAT)
    ax_lk.tick_params(axis="y", labelcolor=_COLOR_LAKTAT)

    # Y-axis (laktat): from 0 to max + 1.0, ticks every 1 or 2 depending on range.
    lk_clean = lk_data[~np.isnan(lk_data)]
    lk_max = float(lk_clean.max()) if len(lk_clean) else 8.0
    ax_lk.set_ylim(0, lk_max + 1.0)
    lk_tick = 1 if lk_max <= 7 else 2
    ax_lk.set_yticks(np.arange(0, lk_max + 1.0 + 0.1, lk_tick))

    # --- HF (right axis, blue).
    ax_hf = ax_lk.twinx()
    ax_hf.plot(x_fine, hf_fit, color=_COLOR_HF, linewidth=2, zorder=3)
    ax_hf.plot(x_data, hf_data, "o", color=_COLOR_HF, markersize=6, zorder=4)
    ax_hf.set_ylabel("Herzfrequenz (bpm)", color=_COLOR_HF)
    ax_hf.tick_params(axis="y", labelcolor=_COLOR_HF)

    # Y-axis (HF): min = round-down(min-10), max = round-up(max) + 10
    # (Anna 2026-05-13 — old +0 was clipping the top marker visually).
    hf_clean = hf_data[~np.isnan(hf_data)]
    if len(hf_clean):
        hf_min = math.floor((float(hf_clean.min()) - 10) / 10) * 10
        hf_max = math.ceil(float(hf_clean.max()) / 10) * 10 + 10
    else:
        hf_min, hf_max = 70, 200
    ax_hf.set_ylim(hf_min, hf_max)
    ax_hf.set_yticks(np.arange(hf_min, hf_max + 1, 10))

    # X-axis ticks at the increment, ranging start..x_max.
    inc = proto.stufeninkrement
    # Tick the explicit step intensities + the padded right edge.
    last_step_tick = math.floor(x_data_max / inc) * inc if inc > 0 else x_data_max
    tick_count = int(round((last_step_tick - x_min) / inc)) + 1 if inc > 0 else 2
    ticks = [x_min + i * inc for i in range(tick_count)]
    ax_lk.set_xticks(ticks)
    ax_lk.set_xlim(x_min, x_max)

    fig.suptitle(result.diagram_title, fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(out_path, format="png")
    plt.close(fig)
    return out_path


def _draw_zone_bands(ax, result: AnalysisResult, *, x_min: float, x_max: float) -> None:
    """Draw a translucent vertical band for each training zone.

    Per Anna 2026-05-13 — Z1 hellblau, Z2 grün, Z3 gelb, Z4 dunkelgelb,
    Z5 orange, Z6 rot. Bands sit behind the data (zorder=1).

    A zone's `intensitaet_min`/`intensitaet_max` are clamped to the visible
    plot range so Z1 (open lower) and Z6 (open upper / is_max_zone) still
    paint a stripe at the edges of the chart.
    """
    for zone in result.zones_final:
        color = _ZONE_COLORS.get(zone.name)
        if color is None:
            continue
        lo = zone.intensitaet_min if zone.intensitaet_min is not None else x_min
        hi = zone.intensitaet_max if zone.intensitaet_max is not None else x_max
        # Clamp to the visible range; skip if there's no overlap.
        lo = max(lo, x_min)
        hi = min(hi, x_max)
        if hi <= lo:
            continue
        ax.axvspan(lo, hi, color=color, alpha=_ZONE_ALPHA, zorder=1, linewidth=0)


def _x_label_de(result: AnalysisResult) -> str:
    sport = result.test_run.athlete.sportart
    if sport in {"lauf", "triathlon-lauf"}:
        return "Geschwindigkeit (km/h)"
    if sport in {"rad", "triathlon-rad"}:
        return "Leistung (W)"
    return "Stufe"
