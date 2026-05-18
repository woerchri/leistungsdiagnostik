from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import docx2txt


def test_full_pipeline(tmp_path):
    repo = Path(__file__).parent.parent.parent
    fixture = repo / "tests" / "protocols" / "fixtures" / "lauf" / "rainier.xlsx"
    result = subprocess.run(
        [sys.executable, "-m", "ld.run", str(fixture), "--output-dir", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"Pipeline failed:\n{result.stderr}"

    # Per Phase 7 normalization: output basename is XY_LD_Sport_JJ_MM_TT, NOT
    # the input filename. Rainier Matzinger / Lauf / 2024-05-23 → RM_LD_Lauf_24_05_23.
    json_path = tmp_path / "RM_LD_Lauf_24_05_23.json"
    data = json.loads(json_path.read_text())
    assert abs(data["v_max"] - 11.4375) < 0.01

    docx_path = next(tmp_path.glob("RM_LD_Lauf_24_05_23_draft_v*.docx"))
    text = docx2txt.process(str(docx_path))

    # v_max should appear (1-decimal display for km/h)
    assert "11.4" in text

    # At least one intersection value should appear (1-decimal display).
    for row in data["intersections"]:
        if row["intensitaet"] and float(row["intensitaet"]) > 7:
            v = float(row["intensitaet"])
            found = any(fmt in text for fmt in [f"{v:.3f}", f"{v:.2f}", f"{v:.1f}"])
            assert found, f"Expected v≈{v} in docx, not found."
            break

    # Interpretation placeholder should be present (no --interpret flag).
    assert "ausstehend" in text


def test_phase45_template_structure(tmp_path):
    """Locks in the 5-page A4 landscape layout produced after Phases 4+5.
    Anna 2026-05-13 acceptance gates: cover with sport-aware title, MAX zone,
    Z1 ≤ formatting, Pflichtprüfungen on internal page 5, lk=1.0/1.5 absent."""
    repo = Path(__file__).parent.parent.parent
    fixture = repo / "tests" / "protocols" / "fixtures" / "lauf" / "rainier.xlsx"
    subprocess.run(
        [sys.executable, "-m", "ld.run", str(fixture), "--output-dir", str(tmp_path)],
        check=True, capture_output=True, text=True,
    )
    docx_path = next(tmp_path.glob("RM_LD_Lauf_24_05_23_draft_v*.docx"))
    text = docx2txt.process(str(docx_path))

    # Cover: sport-aware title
    assert "Leistungsdiagnostik Laufen" in text
    # New terminology
    assert "Anfangsbelastung" in text
    assert "Maximalgeschwindigkeit" in text
    assert "Anfangsintensität" not in text  # old key removed
    # Pflichtprüfungen moved to internal page 5
    assert "Trainerseite" in text
    assert "Intern" in text
    # Zone rendering: Z6 = MAX
    zones_section = text[text.find("Trainingsbereiche"):text.find("Interpretation")]
    assert "MAX" in zones_section
    # Z1 uses ≤ Unicode (not raw <, which docxtpl strips from text content)
    assert "≤" in zones_section
    # No raw 'None' literals in zones table
    z1_block = zones_section[zones_section.find("Z1"):zones_section.find("Z2")]
    assert "None" not in z1_block
    # Schwellenschnittpunkte: lk=1.0 and 1.5 absent (no in-range root)
    intersection_section = text[
        text.find("Schwellenschnittpunkte"):text.find("Trainingsbereiche")
    ]
    # Round 3 (Anna 2026-05-17) — Word-Whitelist: 2.0, 3.0, 4.0, 6.0 present;
    # 2.5 always dropped; 8.0 only when reached (Rainier intersection at 12.024
    # lies past x_data_max=12.0 → dropped). 1.0/1.5 already dropped because
    # the cubic has no in-range root.
    for lk in ["2.0", "3.0", "4.0", "6.0"]:
        assert lk in intersection_section, f"Expected lk={lk} in Word report"
    for lk in ["1.0", "1.5", "2.5", "8.0"]:
        assert lk not in intersection_section, (
            f"lk={lk} must NOT appear in Word report (Round 3 whitelist + reached-only)"
        )
    # Footer contact present at least once (in body / footer XML)
    assert "anna-maria@woerndle.at" in text
    assert "+43 677 62150496" in text
