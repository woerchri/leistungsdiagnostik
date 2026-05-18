"""Round 2 P0-1/P0-2: Reference fixture renders to exactly 5 pages.

Without this test, the 5-page layout goal is unenforced — Round 1 produced a
9-page report because nothing measured page count after render.

Skipped automatically when LibreOffice (soffice) is not installed. Install via
`brew install --cask libreoffice` to enable the assertion."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from ld import render_qa


REPO = Path(__file__).parent.parent.parent
FIXTURE = REPO / "tests" / "protocols" / "fixtures" / "lauf" / "rainier.xlsx"
SARAH_FIXTURE = REPO / "tests" / "protocols" / "fixtures" / "lauf" / "sarah.xlsx"
INTERP_SAMPLE = {
    "zusammenfassung": (
        "Rainier, dein Test zeigt eine saubere Laktatkurve mit klarer "
        "Schwellenpassage zwischen Stufe 4 und 5. Die HF reagiert linear. "
        "Subjektive Belastung steigt konsistent mit der Intensität. "
        "Aufgrund der unvollständig absolvierten letzten Stufe wird die "
        "Maximalgeschwindigkeit aliquot berechnet — interpretiere die "
        "obersten Zonen mit dieser Einschränkung. Insgesamt eine belastbare "
        "Testqualität, die als Trainingsausgangspunkt dient."
    ),
    "schwellen": (
        "Die individuelle aerobe Schwelle liegt im unteren Bereich deiner "
        "gemessenen Intensitäten. Der Übergang zur Schwellenleistung erfolgt "
        "deutlich vor der höchsten Stufe. Die Kurvenform mit starkem Anstieg "
        "zwischen den letzten beiden Stufen rechtfertigt eine konservative "
        "Schwellenwahl. Die HF-Verlaufslinie stützt diese Einordnung — siehe "
        "Tabelle für die genauen Werte."
    ),
    "coaching_ausblick_3_4_wochen": (
        "In den kommenden 3-4 Wochen sollte der Fokus auf Festigung der "
        "aeroben Basis liegen. Konkrete Leitlinien: 1) Volumen bei ca. 80% "
        "der bisherigen Wochenkilometer halten. 2) Eine Einheit pro Woche "
        "im oberen Z3-Bereich. 3) Kurze Tempowechsel (3-5 × 3 min Z4) statt "
        "längerer Schwellen-Blöcke."
    ),
    "ernaehrung": (
        "Vor längeren oder intensiven Einheiten kohlenhydratbetont und gut "
        "verträglich essen. Bei Einheiten über etwa 60-75 Minuten Kohlenhydrate "
        "und Flüssigkeit unterwegs planen. Nach belastenden Einheiten "
        "Kohlenhydrate plus Protein zur Regeneration kombinieren."
    ),
    "risiko": "Letzte Stufe nicht voll absolviert; v_max-Ableitung aliquot.",
}


def _has_soffice() -> bool:
    return render_qa.find_soffice() is not None


def _per_page_text(pdf_path):
    from pypdf import PdfReader
    return [p.extract_text() for p in PdfReader(str(pdf_path)).pages]


@pytest.mark.skipif(not _has_soffice(),
                    reason="LibreOffice nicht installiert — install: brew install --cask libreoffice")
def test_reference_renders_to_five_pages(tmp_path):
    """End-to-end: pipeline → patch interpretation → render PDF → count pages
    AND verify each page holds the content Anna's spec assigns to it."""
    import json

    subprocess.run(
        [sys.executable, "-m", "ld.run", str(FIXTURE), "--output-dir", str(tmp_path)],
        check=True, capture_output=True, text=True,
    )

    basename = "RM_LD_Lauf_24_05_23"
    interp_path = tmp_path / f"{basename}_interpretation.json"
    interp_path.write_text(json.dumps(INTERP_SAMPLE, ensure_ascii=False))

    subprocess.run(
        [sys.executable, "-m", "ld.patch_interpretation", str(tmp_path / basename)],
        check=True, capture_output=True, text=True,
    )

    final_docx = next(
        p for p in tmp_path.glob(f"{basename}_v*.docx")
        if "_draft_" not in p.name
    )

    pdf = render_qa.render_to_pdf(final_docx, out_dir=tmp_path)
    pages = render_qa.count_pages(pdf)

    assert pages == 5, (
        f"Referenzfall darf nur 5 Seiten haben, gerendert wurden {pages}. "
        f"Layout-Verdichtung erforderlich — siehe build_report_template.py."
    )

    # Page-content assertions — Anna's spec assigns specific sections to each
    # page. The page-count test alone passed even when the plot was on Page 3
    # instead of Page 2 (Round 2 audit caught this).
    texts = _per_page_text(pdf)
    # Round 4 follow-up (Anna 2026-05-18): "Sport AnnaLytics"-Subtext entfernt.
    # Cover-Anker ist jetzt nur noch der Titel + Athletenname.
    assert "Leistungsdiagnostik" in texts[0], "Page 1 must be the cover with the title"
    assert "Daten & Testablauf" in texts[1], "Page 2 must hold the data block"
    assert "Rohdaten" in texts[1], "Page 2 must hold the Rohdaten table"
    # Plot is an inline image — extracted text excludes it, but the section
    # heading 'Rohdaten der Teststufen & Diagramm' must be on Page 2.
    assert "Diagramm" in texts[1], "Page 2 must hold the diagram alongside Rohdaten"
    assert "Analyse" in texts[2] and "Schwellenschnittpunkte" in texts[2], \
        "Page 3 must hold the analysis tables"
    assert "Trainingsbereiche" in texts[2], "Page 3 must hold the zone table"
    # Round 3 (Anna 2026-05-17): heading renamed from "Nächste 3-4 Wochen" to "Empfehlungen".
    assert "Interpretation" in texts[3] and "Empfehlungen" in texts[3], \
        "Page 4 must hold the four interpretation blocks (Empfehlungen renamed in Round 3)"
    assert "Energie & Regeneration" in texts[3], \
        "Page 4 must include the nutrition block"
    assert "Trainerseite" in texts[4] and "Intern" in texts[4], \
        "Page 5 must be marked as the internal trainer page"


@pytest.mark.skipif(not _has_soffice(),
                    reason="LibreOffice nicht installiert")
def test_draft_also_renders_to_five_pages(tmp_path):
    """The draft (without patched interpretation) should also fit in 5 pages."""
    subprocess.run(
        [sys.executable, "-m", "ld.run", str(FIXTURE), "--output-dir", str(tmp_path)],
        check=True, capture_output=True, text=True,
    )
    draft = next(tmp_path.glob("RM_LD_Lauf_24_05_23_draft_v*.docx"))
    pdf = render_qa.render_to_pdf(draft, out_dir=tmp_path)
    pages = render_qa.count_pages(pdf)
    assert pages == 5, (
        f"Draft darf nur 5 Seiten haben, gerendert wurden {pages}."
    )


@pytest.mark.skipif(not _has_soffice(),
                    reason="LibreOffice nicht installiert")
def test_sarah_reference_renders_to_five_pages(tmp_path):
    """Second reference fixture (Sarah — complete last step, no aliquot vmax)
    must also hit exactly 5 pages. Round 2.1 — Anna 2026-05-17 hard-5-cap."""
    subprocess.run(
        [sys.executable, "-m", "ld.run", str(SARAH_FIXTURE), "--output-dir", str(tmp_path)],
        check=True, capture_output=True, text=True,
    )
    draft = next(tmp_path.glob("SS_LD_Lauf_*_draft_v*.docx"))
    pdf = render_qa.render_to_pdf(draft, out_dir=tmp_path)
    pages = render_qa.count_pages(pdf)
    assert pages == 5, (
        f"Sarah-Draft muss 5 Seiten haben, gerendert wurden {pages}."
    )
