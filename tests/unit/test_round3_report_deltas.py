"""Round 3 (Anna 2026-05-17) — render-level smoke tests for the deltas vs Round 2.

These tests anchor the visible-output changes so future edits to the template
or render layer don't silently regress them.

Covered:
  - Z6 HF column renders as "—" (NOT "MAX"); Z6 Intensität+Pace stay "MAX".
  - Testprotokoll on Page 2 shows the new Ruhelaktat / Steigung / Dauer-Felder.
  - Trainingsformen mini-table on Page 3 includes all six zones with the
    expected methodology phrasing.
  - Heading on Page 4 is "Empfehlungen" (renamed from "Nächste 3-4 Wochen").
"""
from __future__ import annotations

from pathlib import Path

import docx2txt

from ld import io_input, plots, protocols, report


FIXTURE = Path(__file__).parent.parent / "protocols" / "fixtures" / "lauf" / "rainier.xlsx"


def _render(tmp_path):
    run = io_input.parse_input(FIXTURE)
    result = protocols.analyze(run)
    plot_path = plots.render_main_diagram(result, tmp_path / "plots")
    out = tmp_path / "out.docx"
    report.render(result, plot_path, out, interpretation=None)
    return result, out


def test_z6_hf_field_is_dash_not_max(tmp_path):
    """Round 3: Z6 → Intensität+Pace = 'MAX', HF-Feld leer ('—')."""
    from docx import Document

    _, docx_path = _render(tmp_path)
    doc = Document(str(docx_path))

    zones_table = None
    for table in doc.tables:
        if not table.rows:
            continue
        header_texts = [c.text.strip() for c in table.rows[0].cells]
        if "Zone" in header_texts and "Ziel" in header_texts:
            zones_table = table
            break
    assert zones_table is not None, "Trainingsbereiche table not found"

    z6_row = next(
        r for r in zones_table.rows[1:] if r.cells and r.cells[0].text.strip() == "Z6"
    )
    cell_texts = [c.text.strip() for c in z6_row.cells]
    # Layout: Zone | Ziel | Intensität | Pace | HF | RPE
    assert cell_texts[2] == "MAX", f"Z6 Intensität sollte 'MAX' sein, war {cell_texts[2]!r}"
    assert cell_texts[3] == "MAX", f"Z6 Pace sollte 'MAX' sein, war {cell_texts[3]!r}"
    assert cell_texts[4] == "—", (
        f"Z6 HF sollte '—' sein (Round 3 Anna 2026-05-17), war {cell_texts[4]!r}"
    )


def test_testprotokoll_shows_new_round3_fields(tmp_path):
    """Round 3: Ruhelaktat, Steigung, Dauer letzte Stufe sichtbar im KV-Block.
    Rainier-Fixture hat keine Ruhelaktat-/Steigung-Werte (leeres Feld → '—'),
    aber 'Dauer letzte Stufe' = 1.75 min (unvollständige letzte Stufe)."""
    _, docx_path = _render(tmp_path)
    text = docx2txt.process(str(docx_path))
    # KV-Schlüssel sind sichtbar.
    assert "Ruhelaktat" in text
    assert "Steigung" in text
    assert "Dauer letzte Stufe" in text
    # Rainier-spezifisch: Dauer letzte Stufe = 1.75 min, also der Wert taucht auf.
    assert "1.75 min" in text


# Round 4 (Anna 2026-05-18): die separate Mini-Tabelle "Beschreibung / Methode
# Trainingsformen" wurde entfernt — Methode ist jetzt eine Spalte innerhalb
# der Trainingsbereiche-Tabelle (Variante A aus Round 3). Die entsprechenden
# Asserts wandern nach tests/unit/test_round4_report_deltas.py — dort wird
# geprüft (a) die Spalte existiert in Trainingsbereiche und (b) die alte
# Mini-Tabellen-Überschrift ist verschwunden.


def test_page4_heading_renamed_to_empfehlungen(tmp_path):
    """Round 3 P0-9 (Anna 2026-05-17): 'Nächste 3-4 Wochen' → 'Empfehlungen'."""
    _, docx_path = _render(tmp_path)
    text = docx2txt.process(str(docx_path))
    assert "Empfehlungen" in text
    assert "Nächste 3-4 Wochen" not in text


def test_cover_page_shows_contact_line(tmp_path):
    """Round 3 P0-3: small contact line at bottom of the cover page.
    Email and phone appear (also in the footer body of subsequent pages, but
    a positive sanity check that they exist somewhere covers both at once)."""
    _, docx_path = _render(tmp_path)
    text = docx2txt.process(str(docx_path))
    assert "anna-maria@woerndle.at" in text
    assert "+43 677 62150496" in text
