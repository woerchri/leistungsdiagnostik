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
_COLOR_LAKTAT = "tab:red"
_COLOR_HF = "tab:blue"


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

    x_min = proto.anfangsintensitaet
    x_max = result.v_max
    x_fine = np.linspace(x_min, x_max, 200)
    lk_fit = np.array([result.cubic.predict(x) for x in x_fine])
    hf_fit = np.array([result.hf_linear.predict(x) for x in x_fine])

    fig, ax_lk = plt.subplots(figsize=_FIGSIZE, dpi=_DPI)

    # Laktat (left axis, red)
    ax_lk.plot(x_fine, lk_fit, color=_COLOR_LAKTAT, linewidth=2)
    ax_lk.plot(x_data, lk_data, "o", color=_COLOR_LAKTAT, markersize=6)
    ax_lk.set_xlabel(_x_label_de(result))
    ax_lk.set_ylabel("Laktat (mmol/l)", color=_COLOR_LAKTAT)
    ax_lk.tick_params(axis="y", labelcolor=_COLOR_LAKTAT)
    lk_max = float(np.nanmax(lk_data)) if len(lk_data) else 8.0
    ax_lk.set_ylim(0, lk_max + 1.0)
    lk_tick = 1 if lk_max <= 7 else 2
    ax_lk.set_yticks(np.arange(0, lk_max + 1.0 + 0.1, lk_tick))

    # HF (right axis, blue)
    ax_hf = ax_lk.twinx()
    ax_hf.plot(x_fine, hf_fit, color=_COLOR_HF, linewidth=2)
    ax_hf.plot(x_data, hf_data, "o", color=_COLOR_HF, markersize=6)
    ax_hf.set_ylabel("Herzfrequenz (bpm)", color=_COLOR_HF)
    ax_hf.tick_params(axis="y", labelcolor=_COLOR_HF)
    hf_clean = hf_data[~np.isnan(hf_data)]
    if len(hf_clean):
        hf_min = math.floor((float(hf_clean.min()) - 10) / 10) * 10
        hf_max = math.ceil(float(hf_clean.max()) / 10) * 10
    else:
        hf_min, hf_max = 70, 200
    ax_hf.set_ylim(hf_min, hf_max)
    ax_hf.set_yticks(np.arange(hf_min, hf_max + 1, 10))

    # X axis ticks at increment
    inc = proto.stufeninkrement
    ax_lk.set_xticks(np.arange(x_min, x_max + inc / 2, inc))
    ax_lk.set_xlim(x_min, x_max)

    fig.suptitle(result.diagram_title, fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(out_path, format="png")
    plt.close(fig)
    return out_path


def _x_label_de(result: AnalysisResult) -> str:
    sport = result.test_run.athlete.sportart
    if sport in {"lauf", "triathlon-lauf"}:
        return "Geschwindigkeit (km/h)"
    if sport in {"rad", "triathlon-rad"}:
        return "Leistung (W)"
    return "Stufe"
