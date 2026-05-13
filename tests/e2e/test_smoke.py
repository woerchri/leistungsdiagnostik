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

    data = json.loads((tmp_path / "rainier.json").read_text())
    assert abs(data["v_max"] - 11.4375) < 0.01

    docx_path = next(tmp_path.glob("rainier_draft_v*.docx"))
    text = docx2txt.process(str(docx_path))

    # v_max should appear
    assert "11.44" in text or "11.4375" in text or "11.4" in text

    # At least one intersection value should appear (stored as 3-decimal string in docx)
    for row in data["intersections"]:
        if row["intensitaet"] and float(row["intensitaet"]) > 7:
            # Try multiple precision formats
            v = float(row["intensitaet"])
            found = any(
                fmt in text
                for fmt in [f"{v:.3f}", f"{v:.2f}", f"{v:.1f}", str(v)]
            )
            assert found, f"Expected v≈{v} in docx, not found. Snippet: {text[:200]}"
            break

    # Interpretation placeholder should be present (no --interpret flag)
    assert "ausstehend" in text
