from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from ld.types import AnalysisResult


def write_redacted(result: AnalysisResult, out_path: Path) -> Path:
    """Strip strong identifiers (Nachname, Geburtsjahr, Email) before LLM
    consumption. Vorname BLEIBT — der Codex-Prompt verlangt persönliche
    Ansprache mit Vornamen ("Rainier, deine Schwelle …"), und ohne Vornamen
    in der JSON müsste Codex jedes Mal nachfragen.

    Anna 2026-05-18 (Screenshot-Feedback): "warum fragt er nach dem Namen,
    wenn der schon im Input ist?" — weil wir ihn vorher unnötig redacted
    hatten. Vorname allein ist kein starker Identifier; Nachname + Geburtsjahr
    + Email zusammen wären es. Die strippen wir weiter.

    Derived `alter` wird in `alter_fuer_interpretation` mitgeführt, wenn
    `geburtsjahr` gesetzt war (sonst None).
    """
    data = asdict(result)
    athlete = data["test_run"]["athlete"]
    # Vorname bleibt im Klartext — wird in der Interpretation als Anrede gebraucht.
    athlete["name"] = "X"
    athlete["geburtsjahr"] = None
    athlete["email"] = None
    # alter may be None if geburtsjahr was omitted — that's fine.
    data["alter_fuer_interpretation"] = result.test_run.athlete.alter
    out_path.write_text(json.dumps(data, indent=2, default=str, ensure_ascii=False))
    return out_path
