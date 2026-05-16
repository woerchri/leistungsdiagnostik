"""Interpretation field plumbing — Anna 2026-05-13 Round 2 P1-4 + P1-5.

Page 4 has 4 sections: Zusammenfassung, Schwellen & Zonen, Nächste 3-4 Wochen,
Energie & Regeneration. The Codex JSON keys are zusammenfassung, schwellen,
coaching_ausblick_3_4_wochen, ernaehrung — with `empfehlungen` accepted as a
legacy fallback for `coaching_ausblick_3_4_wochen`.
"""
from __future__ import annotations

from pathlib import Path

import docx2txt

from ld import io_input, plots, protocols, report


FIXTURE = Path(__file__).parent.parent / "protocols" / "fixtures" / "lauf" / "rainier.xlsx"


def _render(tmp_path, interpretation):
    run = io_input.parse_input(FIXTURE)
    result = protocols.analyze(run)
    plot_path = plots.render_main_diagram(result, tmp_path / "plots")
    out = tmp_path / "out.docx"
    report.render(result, plot_path, out, interpretation=interpretation)
    return out


def test_all_four_section_headers_present(tmp_path):
    out = _render(tmp_path, interpretation=None)
    text = docx2txt.process(str(out))
    assert "Zusammenfassung" in text
    assert "Schwellen & Zonen" in text
    assert "Nächste 3-4 Wochen" in text
    assert "Energie & Regeneration" in text


def test_new_interp_keys_are_used(tmp_path):
    interp = {
        "zusammenfassung": "ZUSAMMENFASSUNG-MARKER",
        "schwellen": "SCHWELLEN-MARKER",
        "coaching_ausblick_3_4_wochen": "AUSBLICK-MARKER",
        "ernaehrung": "ERNAEHRUNG-MARKER",
    }
    out = _render(tmp_path, interp)
    text = docx2txt.process(str(out))
    for marker in interp.values():
        assert marker in text, f"Missing {marker!r} in rendered doc"


def test_legacy_empfehlungen_key_falls_back_to_coaching_ausblick(tmp_path):
    """During migration, Codex may still emit the old `empfehlungen` key. It
    must surface in the new 'Nächste 3-4 Wochen' block."""
    interp = {
        "zusammenfassung": "z",
        "schwellen": "s",
        "empfehlungen": "LEGACY-EMPF-MARKER",
        # No coaching_ausblick_3_4_wochen, no ernaehrung
    }
    out = _render(tmp_path, interp)
    text = docx2txt.process(str(out))
    assert "LEGACY-EMPF-MARKER" in text


def test_missing_ernaehrung_shows_placeholder(tmp_path):
    interp = {
        "zusammenfassung": "z",
        "schwellen": "s",
        "coaching_ausblick_3_4_wochen": "ausblick",
        # ernaehrung missing
    }
    out = _render(tmp_path, interp)
    text = docx2txt.process(str(out))
    # Placeholder must signal the gap so the operator notices.
    assert "ausstehend" in text
