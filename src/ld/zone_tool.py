"""Visuelles Zonen-Tool — interaktive Slider zur Anpassung der Trainingszonen.

Per Anna 2026-05-13 Feedback: "Tool erstellen, bei dem man selbstständig die
farblichen Übergänge als Regler manuell verschieben kann."

Aufruf (nach `uv pip install -e ".[visual]"`):

    uv run streamlit run src/ld/zone_tool.py

Das Tool liest `output/<basename>.pkl`, zeigt den aktuellen Plot mit den vier
verschiebbaren Zonengrenzen (Z2/Z3/Z4/Z5 Obergrenzen), und schreibt beim
"Übernehmen"-Klick die neuen Werte über `ld.zones_override.apply()` zurück,
inklusive neuem Draft-Bericht.

Nicht-deterministische Prosa bleibt weiterhin Codex' Aufgabe — dieses Tool
manipuliert nur die Zonengrenzen.
"""
from __future__ import annotations

import pickle
import tempfile
from dataclasses import replace
from pathlib import Path

# Streamlit is an optional dependency (see pyproject.toml `[project.optional-dependencies]`).
try:
    import streamlit as st
except ImportError as e:
    raise SystemExit(
        "streamlit fehlt. Installiere mit:\n"
        "    uv pip install -e '.[visual]'\n"
        "und starte erneut mit `uv run streamlit run src/ld/zone_tool.py`."
    ) from e

from ld import plots, zones
from ld.types import AnalysisResult, TrainingZone


_OUTPUT_DIR = Path("output")


def _list_pickles() -> list[Path]:
    return sorted(_OUTPUT_DIR.glob("*.pkl"))


def _zone_upper(zones_tuple: tuple[TrainingZone, ...], name: str) -> float | None:
    for z in zones_tuple:
        if z.name == name:
            return z.intensitaet_max
    return None


def _apply_overrides_to_result(
    result: AnalysisResult, z2_u: float, z3_u: float, z4_u: float, z5_u: float
) -> AnalysisResult:
    """Recompute zones with hard overrides — used by the live preview before
    the user commits via `ld.zones_override.apply()`."""
    new_zones = []
    overrides = {"Z2": z2_u, "Z3": z3_u, "Z4": z4_u, "Z5": z5_u}
    for z in result.zones_final:
        if z.name in overrides:
            new_zones.append(replace(z, intensitaet_max=overrides[z.name]))
        else:
            new_zones.append(z)
    # Chain lower bounds to the previous zone's upper.
    chained: list[TrainingZone] = []
    prev_upper: float | None = None
    for z in new_zones:
        if z.is_open_lower:
            # Z1 — open lower; mirror Z2's new upper as Z1's display upper for consistency.
            z2_new = next((nz for nz in new_zones if nz.name == "Z2"), None)
            new_upper = z2_new.intensitaet_max if z2_new else z.intensitaet_max
            chained.append(replace(z, intensitaet_max=new_upper))
        elif z.is_max_zone:
            # Z6 — lower = previous zone's new upper.
            chained.append(replace(z, intensitaet_min=prev_upper))
        else:
            chained.append(replace(z, intensitaet_min=prev_upper))
            prev_upper = z.intensitaet_max
    return replace(result, zones_final=tuple(chained))


def main() -> None:
    st.set_page_config(page_title="Leistungsdiagnostik — Zonen", layout="wide")
    st.title("Leistungsdiagnostik — Zonen anpassen")

    pkls = _list_pickles()
    if not pkls:
        st.warning(f"Keine `.pkl`-Datei in `{_OUTPUT_DIR}/` gefunden. "
                   f"Erst `uv run python -m ld.run input/<datei.xlsx>` ausführen.")
        return

    selected = st.selectbox("Auswertung wählen", pkls, format_func=lambda p: p.name)
    result: AnalysisResult = pickle.loads(selected.read_bytes())

    athlete = result.test_run.athlete
    proto = result.test_run.testprotokoll
    st.caption(
        f"**{athlete.vorname} {athlete.name}** · {athlete.sportart.title()} · "
        f"{proto.testdatum.strftime('%d.%m.%Y')} · {proto.durchfuehrungsort}"
    )

    # Slider-Bereich: anfangsbelastung bis ~10% über v_max
    x_min = float(proto.anfangsbelastung)
    x_max = float(result.v_max)
    slider_top = x_max * 1.05
    step = 0.05 if athlete.sportart in {"lauf", "triathlon-lauf"} else 1.0
    fmt = "%.1f km/h" if athlete.sportart in {"lauf", "triathlon-lauf"} else "%.0f"

    z2_def = _zone_upper(result.zones_final, "Z2") or x_min + (x_max - x_min) * 0.25
    z3_def = _zone_upper(result.zones_final, "Z3") or x_min + (x_max - x_min) * 0.50
    z4_def = _zone_upper(result.zones_final, "Z4") or x_min + (x_max - x_min) * 0.75
    z5_def = _zone_upper(result.zones_final, "Z5") or x_max

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Obergrenzen der Zonen")
        z2_u = st.slider("Z2 (aerobe Basis)", x_min, slider_top, float(z2_def), step=step, format=fmt)
        z3_u = st.slider("Z3 (metab. Stabilität)", z2_u, slider_top, max(float(z3_def), z2_u), step=step, format=fmt)
        z4_u = st.slider("Z4 (Schwellenleistung)", z3_u, slider_top, max(float(z4_def), z3_u), step=step, format=fmt)
        z5_u = st.slider("Z5 (VO2max)", z4_u, slider_top, max(float(z5_def), z4_u), step=step, format=fmt)

        st.divider()
        commit = st.button("Übernehmen & Bericht neu erzeugen", type="primary")

    with col2:
        st.subheader("Vorschau")
        preview_result = _apply_overrides_to_result(result, z2_u, z3_u, z4_u, z5_u)
        with tempfile.TemporaryDirectory() as tmp:
            plot_path = plots.render_main_diagram(preview_result, Path(tmp))
            st.image(str(plot_path), use_container_width=True)

    if commit:
        from ld import zones_override
        basename_path = str(selected).removesuffix(".pkl")
        zones_override.apply(basename_path, {
            "Z2_upper": z2_u,
            "Z3_upper": z3_u,
            "Z4_upper": z4_u,
            "Z5_upper": z5_u,
        })
        st.success(
            f"Zonen gespeichert für `{selected.stem}`. Neuer Draft im "
            f"`output/`-Ordner.\n\nDanach Codex `/ld-report` "
            f"erneut ausführen, um die Interpretation zu erzeugen."
        )


if __name__ == "__main__":
    main()
