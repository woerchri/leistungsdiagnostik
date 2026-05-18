"""Redaction layer: what goes into the LLM-facing JSON.

Round 4 follow-up (Anna 2026-05-18, Screenshot-Feedback): Codex hat nach dem
Vornamen gefragt, obwohl der im Input stand — weil `_for_llm.json` ihn
vorher mit "Athlet:in" ersetzte. Anna's eigene Repo-Regel verlangt persönliche
Vorname-Ansprache. Vorname bleibt daher jetzt im Klartext; Nachname,
Geburtsjahr und Email werden weiterhin redacted.
"""
from __future__ import annotations

import json
from pathlib import Path

from ld import io_input, protocols, redact


FIXTURE = Path(__file__).parent.parent / "protocols" / "fixtures" / "lauf" / "rainier.xlsx"


def _run_redact(tmp_path):
    run = io_input.parse_input(FIXTURE)
    result = protocols.analyze(run)
    out = tmp_path / "for_llm.json"
    redact.write_redacted(result, out)
    return json.loads(out.read_text())


def test_redaction_keeps_vorname(tmp_path):
    """Round 4 follow-up: Vorname bleibt im Klartext, damit Codex direkt
    ansprechen kann ('Rainier, deine Schwelle …') statt nachfragen zu müssen."""
    data = _run_redact(tmp_path)
    athlete = data["test_run"]["athlete"]
    assert athlete["vorname"] == "Rainier", (
        f"Vorname sollte im Klartext bleiben, war {athlete['vorname']!r}"
    )
    # Sicherheit gegen Regression auf den alten "Athlet:in"-Platzhalter.
    assert athlete["vorname"] != "Athlet:in"


def test_redaction_strips_strong_identifiers(tmp_path):
    """Nachname, Geburtsjahr, Email werden weiterhin redacted — diese
    drei zusammen wären ein starker Identifier, daher unverändert PII-strip."""
    data = _run_redact(tmp_path)
    athlete = data["test_run"]["athlete"]
    assert athlete["name"] == "X", f"Nachname sollte redacted sein, war {athlete['name']!r}"
    assert athlete["geburtsjahr"] is None, (
        f"Geburtsjahr sollte None sein, war {athlete['geburtsjahr']!r}"
    )
    assert athlete["email"] is None, f"Email sollte None sein, war {athlete['email']!r}"


def test_redaction_preserves_alter_for_interpretation(tmp_path):
    """Das abgeleitete `alter` wird in `alter_fuer_interpretation` mitgeführt,
    damit die Interpretation z.B. altersgerechte HF-Bemerkungen machen kann
    ohne das Geburtsjahr selbst zu kennen."""
    data = _run_redact(tmp_path)
    # Rainier-Fixture: Geburtsjahr 1968 → Alter abhängig vom heutigen Datum.
    alter = data.get("alter_fuer_interpretation")
    assert alter is not None and isinstance(alter, int) and 30 < alter < 100, (
        f"alter_fuer_interpretation sollte plausibles Alter sein, war {alter!r}"
    )
