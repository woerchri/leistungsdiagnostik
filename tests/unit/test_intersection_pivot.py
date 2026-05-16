"""Schwellenschnittpunkt-Tabelle Pivot — Anna 2026-05-13 Round 2.

Layout: Spaltenköpfe = gültige Laktatwerte. Zeilen = Geschwindigkeit/Pace/HF.
Ungültige Laktatwerte (None-Schnittpunkt) werden als ganze Spalte weggelassen.
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


def test_pivot_renders_only_valid_laktat_columns(tmp_path):
    """Rainier: lk=1.0 and 1.5 have no in-range root → must be absent from pivot."""
    result, docx_path = _render(tmp_path)
    text = docx2txt.process(str(docx_path))

    section = text[
        text.find("Schwellenschnittpunkte"):text.find("Trainingsbereiche")
    ]
    # Section should NOT contain the marker placeholder (post-render replaced it).
    assert "<<INTERSECTION_PIVOT>>" not in section
    # Valid laktat targets present as column headers.
    for lk in ["2.0", "2.5", "3.0", "4.0", "6.0", "8.0"]:
        assert lk in section, f"Expected lk={lk} as column header"
    # Pivot has metric labels as row 0:
    assert "Geschwindigkeit (km/h)" in section
    assert "Pace (min/km)" in section
    assert "Herzfrequenz (bpm)" in section


def test_pivot_column_count_matches_valid_rows(tmp_path):
    """Header row in the pivot table should have one cell per valid laktat
    value (plus the empty top-left label cell)."""
    from docx import Document

    result, docx_path = _render(tmp_path)
    doc = Document(str(docx_path))

    # Find the pivot table — it's the one with metric-label cells in column 0.
    pivot = None
    for table in doc.tables:
        first_col_texts = [r.cells[0].text.strip() for r in table.rows if r.cells]
        if "Geschwindigkeit (km/h)" in first_col_texts:
            pivot = table
            break
    assert pivot is not None, "Pivot table not found"

    valid_count = sum(1 for r in result.intersections if r.intensitaet is not None)
    # n_cols = label column + one per valid laktat value
    assert len(pivot.rows[0].cells) == valid_count + 1, (
        f"Expected {valid_count + 1} columns, got {len(pivot.rows[0].cells)}"
    )
    # 4 rows: header + 3 metric rows (Geschwindigkeit, Pace, HF)
    assert len(pivot.rows) == 4


def test_pivot_no_none_strings(tmp_path):
    """No 'None' literal anywhere in the pivot section — Anna 2026-05-13."""
    _, docx_path = _render(tmp_path)
    text = docx2txt.process(str(docx_path))
    section = text[
        text.find("Schwellenschnittpunkte"):text.find("Trainingsbereiche")
    ]
    assert "None" not in section


def test_pivot_drops_invalid_laktat_columns_explicitly(tmp_path):
    """For Rainier specifically — lk=1.0 and 1.5 have no in-range root and
    MUST be entirely absent (not rendered as '—' placeholder columns).
    Anna 2026-05-13 Round 1+2: "Nicht vorhandene Laktat-Schnittpunkte komplett
    entfernen"."""
    _, docx_path = _render(tmp_path)
    text = docx2txt.process(str(docx_path))
    section = text[
        text.find("Schwellenschnittpunkte"):text.find("Trainingsbereiche")
    ]
    # Must NOT appear as a column header in the pivot section.
    # (They may appear elsewhere as substrings in values — limit the scope.)
    header_line = section.split("\n")[1] if "\n" in section else ""
    assert "1.0" not in header_line, "lk=1.0 must NOT be a pivot column"
    assert "1.5" not in header_line, "lk=1.5 must NOT be a pivot column"
