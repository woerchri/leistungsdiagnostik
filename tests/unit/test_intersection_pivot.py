"""Schwellenschnittpunkt-Tabelle Pivot — Anna 2026-05-13 Round 2 + Round 3 2026-05-17.

Layout: Spaltenköpfe = gültige Laktatwerte. Zeilen = Geschwindigkeit/Pace/HF.

Filtering for the WORD report (Round 3):
  - Ungültige Laktatwerte (None-Schnittpunkt) → komplett weggelassen.
  - `2.5` → komplett weggelassen (auch wenn Pipeline einen Wert berechnet).
  - `8.0` → nur wenn Wert ≤ x_data_max (wirklich erreicht).
JSON/Codex bleiben dagegen unverändert — Trainer sieht alles zum Korrigieren.
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


def test_pivot_renders_only_word_whitelist_columns(tmp_path):
    """Round 3 (Anna 2026-05-17): the Word report applies the Word whitelist
    on top of the per-row validity check.

    Rainier fixture:
      - lk=1.0 / 1.5 → no in-range cubic root → dropped (Round 2 rule).
      - lk=2.5 → has a valid root (7.658) but is on Round-3 word-blacklist → dropped.
      - lk=8.0 → root at 12.024 lies past x_data_max=12.0 → "not reached" → dropped.
      - lk=2.0 / 3.0 / 4.0 / 6.0 → visible.
    """
    result, docx_path = _render(tmp_path)
    text = docx2txt.process(str(docx_path))

    section = text[
        text.find("Schwellenschnittpunkte"):text.find("Trainingsbereiche")
    ]
    # Section should NOT contain the marker placeholder (post-render replaced it).
    assert "<<INTERSECTION_PIVOT>>" not in section
    # Round-3 visible laktat targets.
    for lk in ["2.0", "3.0", "4.0", "6.0"]:
        assert lk in section, f"Expected lk={lk} as column header"
    # Round-3 hidden laktat targets.
    for lk in ["1.0", "1.5", "2.5", "8.0"]:
        assert lk not in section, (
            f"lk={lk} must NOT be a Word pivot column (Round-3 whitelist + reached-only)"
        )
    # Pivot has metric labels as row 0:
    assert "Geschwindigkeit (km/h)" in section
    assert "Pace (min/km)" in section
    assert "Herzfrequenz (bpm)" in section


def test_pivot_column_count_matches_word_visible_rows(tmp_path):
    """Header row has one cell per Word-visible laktat + the label cell."""
    from docx import Document

    from ld.report import _WORD_REPORT_LAKTAT_WHITELIST, _WORD_REPORT_LAKTAT_REACHED_ONLY

    result, docx_path = _render(tmp_path)
    doc = Document(str(docx_path))

    pivot = None
    for table in doc.tables:
        first_col_texts = [r.cells[0].text.strip() for r in table.rows if r.cells]
        if "Geschwindigkeit (km/h)" in first_col_texts:
            pivot = table
            break
    assert pivot is not None, "Pivot table not found"

    steps = result.test_run.steps
    measured_xs = [s.intensitaet for s in steps if s.laktat_mmol is not None]
    x_data_max = max(measured_xs)

    def _word_visible(r) -> bool:
        if r.intensitaet is None:
            return False
        if r.laktat not in _WORD_REPORT_LAKTAT_WHITELIST:
            return False
        if r.laktat in _WORD_REPORT_LAKTAT_REACHED_ONLY and r.intensitaet > x_data_max:
            return False
        return True

    visible_count = sum(1 for r in result.intersections if _word_visible(r))
    # n_cols = label column + one per Word-visible laktat value
    assert len(pivot.rows[0].cells) == visible_count + 1, (
        f"Expected {visible_count + 1} columns, got {len(pivot.rows[0].cells)}"
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
