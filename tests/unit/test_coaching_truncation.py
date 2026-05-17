"""Page-5 Trainernotizen truncation — Anna 2026-05-17 Round 2.1 decision #2.

To guarantee "immer 5 Seiten, immer gleiche Struktur" (decision #1), long
trainer notes are truncated to per-field char caps before render. Full text
remains in the JSON; the docx gets the summary.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import docx2txt

from ld import io_input, plots, protocols, report
from ld.types import Coaching


FIXTURE = Path(__file__).parent.parent / "protocols" / "fixtures" / "lauf" / "rainier.xlsx"


def _render_with_coaching(tmp_path, coaching: Coaching):
    run = io_input.parse_input(FIXTURE)
    run = replace(run, coaching=coaching)
    result = protocols.analyze(run)
    plot_path = plots.render_main_diagram(result, tmp_path / "plots")
    out = tmp_path / "out.docx"
    report.render(result, plot_path, out, interpretation=None)
    return out


def test_short_trainernotizen_pass_through(tmp_path, capsys):
    short = Coaching(
        verletzungen="keine", aktuelle_probleme="—",
        staerken="Grundlage", schwaechen="Tempo",
        geplante_wettkaempfe="Achensee", trainernotizen="kurz",
    )
    out = _render_with_coaching(tmp_path, short)
    text = docx2txt.process(str(out))
    assert "kurz" in text
    # No truncation warning expected.
    captured = capsys.readouterr()
    assert "gekürzt" not in captured.out


def test_long_trainernotizen_truncated_with_warning(tmp_path, capsys):
    long_text = "Sehr ausführliche Notizen zum letzten Trainingsblock. " * 20  # ~1100 chars
    coaching = Coaching(
        verletzungen="keine", aktuelle_probleme="—",
        staerken="Grundlage", schwaechen="Tempo",
        geplante_wettkaempfe="Achensee", trainernotizen=long_text,
    )
    out = _render_with_coaching(tmp_path, coaching)
    text = docx2txt.process(str(out))
    # The rendered output ends with the ellipsis marker.
    assert "…" in text, "Truncated text must end with ellipsis"
    # Warning printed to stdout (the operator sees this in their pipeline output).
    captured = capsys.readouterr()
    assert "trainernotizen" in captured.out and "gekürzt" in captured.out


def test_long_short_field_also_truncated(tmp_path, capsys):
    long_text = "Schwächen: " + ("zu viele um sie hier aufzulisten. " * 10)  # ~330 chars
    coaching = Coaching(
        verletzungen="keine", aktuelle_probleme="—",
        staerken="Grundlage", schwaechen=long_text,
        geplante_wettkaempfe="Achensee", trainernotizen="kurz",
    )
    _render_with_coaching(tmp_path, coaching)
    captured = capsys.readouterr()
    assert "schwaechen" in captured.out and "gekürzt" in captured.out


def test_missing_coaching_field_renders_emdash(tmp_path):
    coaching = Coaching(
        verletzungen="", aktuelle_probleme="",
        staerken="", schwaechen="",
        geplante_wettkaempfe="", trainernotizen="",
    )
    out = _render_with_coaching(tmp_path, coaching)
    text = docx2txt.process(str(out))
    # The Trainernotizen table should contain — placeholders.
    notes_section = text[text.find("Trainernotizen"):]
    assert "—" in notes_section
