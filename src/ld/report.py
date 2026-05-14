from __future__ import annotations

from pathlib import Path

from docx.shared import Cm
from docxtpl import DocxTemplate, InlineImage

from ld.types import AnalysisResult


_TEMPLATE_PATH = Path(__file__).parent.parent.parent / "templates" / "report.docx"
# A4 landscape gives ~25 cm usable width; plot is wide for readability.
_PLOT_WIDTH_CM = 22.0


def _x_axis_label(sport: str) -> str:
    """Matches plots.py axis labels — sportart-aware."""
    if sport in {"lauf", "triathlon-lauf"}:
        return "Geschwindigkeit (km/h)"
    if sport in {"rad", "triathlon-rad"}:
        return "Leistung (W)"
    return "Stufe"


def render(
    result: AnalysisResult,
    plot_path: Path,
    out_path: Path,
    interpretation: dict[str, str] | None = None,
) -> Path:
    doc = DocxTemplate(_TEMPLATE_PATH)

    sport = result.test_run.athlete.sportart
    sport_labels = {
        "lauf": "Laufen",
        "rad": "Radfahren",
        "triathlon-rad": "Triathlon – Rad",
        "triathlon-lauf": "Triathlon – Lauf",
        "unspezifisch": "Unspezifisch",
    }
    # Per-sport intensity unit (Anna 2026-05-13: "Einheit sichtbar machen").
    intensity_units = {
        "lauf": "km/h",
        "rad": "W",
        "triathlon-rad": "W",
        "triathlon-lauf": "km/h",
        "unspezifisch": "Stufe",
    }
    # v_max label by sport (Anna 2026-05-13: "v_max immer als Maximalgeschwindigkeit
    # formulieren" — applies to LAUF; analogous labels for RAD/UNSPEZ).
    v_max_labels = {
        "lauf": "Maximalgeschwindigkeit",
        "rad": "Maximalleistung",
        "triathlon-rad": "Maximalleistung",
        "triathlon-lauf": "Maximalgeschwindigkeit",
        "unspezifisch": "Maximalstufe",
    }
    intensity_unit = intensity_units[sport]
    v_max_label = v_max_labels[sport]
    is_lauf = sport in {"lauf", "triathlon-lauf"}

    # 1-decimal rounding ONLY for km/h DISPLAY (Anna 2026-05-13).
    # JSON keeps full precision; this affects the docx render only.
    def _round_intensity(v: float | None) -> float | str | None:
        if v is None:
            return None
        return round(v, 1) if is_lauf else round(v, 0)

    def _render_intersections() -> tuple:
        """Drop rows with no valid root; format for display."""
        out = []
        for r in result.intersections:
            if r.intensitaet is None:
                continue
            out.append({
                "laktat": r.laktat,
                "intensitaet": _round_intensity(r.intensitaet),
                "pace_min_per_km": r.pace_min_per_km,
                "herzfrequenz_bpm": r.herzfrequenz_bpm,
            })
        return tuple(out)

    def _render_zones() -> tuple:
        """Pre-format zones for display:
          - is_max_zone (Z6) → all intensity/pace/HF cells show "MAX"
          - is_open_lower (Z1) → "< x" / "> p" formatting
          - rpe shown as single value when min == max (Z5: 9, Z6: 10)
        """
        out = []
        for z in result.zones_final:
            if z.is_max_zone:
                v_range = "MAX"
                hf_range = "MAX"
                pace_range = "MAX"
            elif z.is_open_lower or (z.intensitaet_min is None and z.intensitaet_max is not None):
                # Z1 (and Z2 when lk≈1.0/1.5 not anchored) render as "≤ upper".
                # Using ≤/≥ Unicode (U+2264 / U+2265) avoids the XML-escape issue
                # where docxtpl/python-docx strips raw `<` from text content.
                hi = _round_intensity(z.intensitaet_max)
                v_range = f"≤ {hi} {intensity_unit}" if hi is not None else "—"
                hf_range = f"≤ {z.herzfrequenz_max}" if z.herzfrequenz_max else "—"
                pace_range = f"≥ {z.pace_min_min_per_km}" if z.pace_min_min_per_km else "—"
            else:
                lo = _round_intensity(z.intensitaet_min)
                hi = _round_intensity(z.intensitaet_max)
                v_range = f"{lo} – {hi}" if (lo is not None and hi is not None) else "—"
                if z.herzfrequenz_min and z.herzfrequenz_max:
                    hf_range = f"{z.herzfrequenz_min} – {z.herzfrequenz_max}"
                else:
                    hf_range = "—"
                if z.pace_max_min_per_km and z.pace_min_min_per_km:
                    pace_range = f"{z.pace_max_min_per_km} – {z.pace_min_min_per_km}"
                else:
                    pace_range = "—"
            rpe = (
                str(z.rpe_min) if z.rpe_min == z.rpe_max
                else f"{z.rpe_min} – {z.rpe_max}"
            )
            out.append({
                "name": z.name,
                "ziel": z.ziel,
                "intensitaet_range": v_range,
                "herzfrequenz_range": hf_range,
                "pace_range": pace_range,
                "rpe": rpe,
            })
        return tuple(out)

    interp = interpretation or {}
    proto = result.test_run.testprotokoll
    athlete = result.test_run.athlete
    context = {
        "athlete": {
            "vorname": athlete.vorname,
            "name": athlete.name,
            # Optional fields render as "—" when missing (Anna 2026-05-13).
            "alter": athlete.alter if athlete.alter is not None else "—",
            "geburtsjahr": athlete.geburtsjahr if athlete.geburtsjahr is not None else "—",
            "email": athlete.email or "—",
            "gewicht_kg": athlete.gewicht_kg,
            "groesse_m": athlete.groesse_m,
            "geschlecht": athlete.geschlecht or "—",
            # Sportart label exposed on BOTH athlete (for the cover title) and
            # testprotokoll (for the data section). Anna 2026-05-13 wanted the
            # sport tag in the test protocol, but the cover title naturally
            # belongs to "the athlete's diagnostic" — duplicate is intentional.
            "sportart_label": sport_labels[sport],
            "trainingsziel": athlete.trainingsziel,
            "wettkampfziel": athlete.wettkampfziel,
            "trainingsumfang_wo": athlete.trainingsumfang_wo,
            "leistungsniveau": athlete.leistungsniveau,
        },
        "testprotokoll": {
            "testdatum": proto.testdatum.strftime("%d.%m.%Y"),
            "uhrzeit": proto.uhrzeit,
            "durchfuehrungsort": proto.durchfuehrungsort,
            "testleiter": proto.testleiter,
            "geraet": proto.geraet,
            "besonderheiten": proto.besonderheiten,
            # Anna 2026-05-13: Sportart moves into Testprotokoll-Sektion of the report.
            "sportart_label": sport_labels[sport],
            # Display values with units (Anna 2026-05-13: "Einheit sichtbar machen").
            "anfangsbelastung_display": f"{_round_intensity(proto.anfangsbelastung)} {intensity_unit}",
            "stufeninkrement_display": f"{_round_intensity(proto.stufeninkrement)} {intensity_unit}",
            "stufendauer_min": proto.stufendauer_min,
            "nachbelastungslaktat_3min": (
                f"{proto.nachbelastungslaktat_3min_mmol} mmol/l"
                if proto.nachbelastungslaktat_3min_mmol is not None else "—"
            ),
            "nachbelastungslaktat_5min": (
                f"{proto.nachbelastungslaktat_5min_mmol} mmol/l"
                if proto.nachbelastungslaktat_5min_mmol is not None else "—"
            ),
            # Legacy alias for the current binary template (removed after Phase 4 rebuild).
            "anfangsintensitaet": _round_intensity(proto.anfangsbelastung),
            "stufeninkrement": _round_intensity(proto.stufeninkrement),
        },
        # v_max label by sport (Anna 2026-05-13 — "Maximalgeschwindigkeit").
        "v_max_label": v_max_label,
        "v_max_display": f"{_round_intensity(result.v_max)} {intensity_unit}",
        # Legacy alias for the current binary template (removed after Phase 4 rebuild).
        "vmax_display": _round_intensity(result.v_max),
        "ausbelastung_de": "ja" if proto.ausbelastung else "nein",
        "steps": result.test_run.steps,
        # Drop intersection rows without a valid in-range root — per Anna 2026-05-13
        # feedback, "keine Fantasiewerte". JSON keeps the full tuple (with None
        # entries) for diagnostic purposes; only the report hides them.
        "intersections": _render_intersections(),
        "zones": _render_zones(),
        # Raw zones for templates that still want field-level access (Phase 4 cleanup).
        "zones_raw": result.zones_final,
        "diagram": InlineImage(doc, str(plot_path), width=Cm(_PLOT_WIDTH_CM)),
        # X-axis label for tables (matches the plot's x-axis).
        "x_axis_label": _x_axis_label(sport),
        # `failed_checks` kept for the legacy template; `internal_failed_checks` is
        # the new key consumed by Page 5 of the rebuilt 5-page template
        # (Anna 2026-05-13 — Pflichtprüfungen must NOT appear in athlete sections).
        "failed_checks": [p for p in result.pflichtpruefungen if not p.ok],
        "internal_failed_checks": [p for p in result.pflichtpruefungen if not p.ok],
        "coaching": {
            "verletzungen": result.test_run.coaching.verletzungen,
            "aktuelle_probleme": result.test_run.coaching.aktuelle_probleme,
            "staerken": result.test_run.coaching.staerken,
            "schwaechen": result.test_run.coaching.schwaechen,
            "geplante_wettkaempfe": result.test_run.coaching.geplante_wettkaempfe,
            "trainernotizen": result.test_run.coaching.trainernotizen,
        },
        "interp_zusammenfassung": interp.get("zusammenfassung", "[Interpretation: ausstehend]"),
        "interp_schwellen": interp.get("schwellen", "[Interpretation: ausstehend]"),
        # Trainingsbereiche prose dropped per Anna 2026-05-13 (it just repeats the table).
        # Empfehlungen takes the role the old "zonen" key played.
        "interp_empfehlungen": interp.get("empfehlungen", "[Interpretation: ausstehend]"),
        # Optional Page-5 internal narrative (currently not produced by the LLM step).
        "interp_risiko": interp.get("risiko", None),
        # Legacy alias for the current binary template (removed after Phase 4 rebuild).
        "interp_zonen": interp.get("zonen", "[Interpretation: ausstehend]"),
    }

    doc.render(context)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_path)
    return out_path
