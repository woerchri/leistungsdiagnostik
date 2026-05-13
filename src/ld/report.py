from __future__ import annotations

from pathlib import Path

from docx.shared import Cm
from docxtpl import DocxTemplate, InlineImage

from ld.types import AnalysisResult


_TEMPLATE_PATH = Path(__file__).parent.parent.parent / "templates" / "report.docx"
_PLOT_WIDTH_CM = 16.0


def render(
    result: AnalysisResult,
    plot_path: Path,
    out_path: Path,
    interpretation: dict[str, str] | None = None,
) -> Path:
    doc = DocxTemplate(_TEMPLATE_PATH)

    sport_labels = {
        "lauf": "Laufen",
        "rad": "Radfahren",
        "triathlon-rad": "Triathlon – Rad",
        "triathlon-lauf": "Triathlon – Lauf",
        "unspezifisch": "Unspezifisch",
    }

    interp = interpretation or {}
    context = {
        "athlete": {
            "vorname": result.test_run.athlete.vorname,
            "name": result.test_run.athlete.name,
            "alter": result.test_run.athlete.alter,
            "gewicht_kg": result.test_run.athlete.gewicht_kg,
            "groesse_m": result.test_run.athlete.groesse_m,
            "geschlecht": result.test_run.athlete.geschlecht or "—",
            "sportart_label": sport_labels[result.test_run.athlete.sportart],
            "trainingsziel": result.test_run.athlete.trainingsziel,
            "wettkampfziel": result.test_run.athlete.wettkampfziel,
            "trainingsumfang_wo": result.test_run.athlete.trainingsumfang_wo,
            "leistungsniveau": result.test_run.athlete.leistungsniveau,
        },
        "testprotokoll": {
            "testdatum": result.test_run.testprotokoll.testdatum.strftime("%d.%m.%Y"),
            "uhrzeit": result.test_run.testprotokoll.uhrzeit,
            "durchfuehrungsort": result.test_run.testprotokoll.durchfuehrungsort,
            "testleiter": result.test_run.testprotokoll.testleiter,
            "geraet": result.test_run.testprotokoll.geraet,
            "besonderheiten": result.test_run.testprotokoll.besonderheiten,
            "anfangsintensitaet": result.test_run.testprotokoll.anfangsintensitaet,
            "stufeninkrement": result.test_run.testprotokoll.stufeninkrement,
            "stufendauer_min": result.test_run.testprotokoll.stufendauer_min,
        },
        "vmax_display": round(result.v_max, 2),
        "ausbelastung_de": "ja" if result.test_run.testprotokoll.ausbelastung else "nein",
        "steps": result.test_run.steps,
        "intersections": result.intersections,
        "zones": result.zones_final,
        "diagram": InlineImage(doc, str(plot_path), width=Cm(_PLOT_WIDTH_CM)),
        "failed_checks": [p for p in result.pflichtpruefungen if not p.ok],
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
        "interp_zonen": interp.get("zonen", "[Interpretation: ausstehend]"),
        "interp_empfehlungen": interp.get("empfehlungen", "[Interpretation: ausstehend]"),
    }

    doc.render(context)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_path)
    return out_path
