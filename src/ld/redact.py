from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from ld.types import AnalysisResult


def write_redacted(result: AnalysisResult, out_path: Path) -> Path:
    """Strip identifying fields (Name, Geburtsjahr, Email) before LLM consumption.
    Derived `alter` is preserved in `alter_fuer_interpretation` when available.
    """
    data = asdict(result)
    athlete = data["test_run"]["athlete"]
    athlete["vorname"] = "Athlet:in"
    athlete["name"] = "X"
    athlete["geburtsjahr"] = None
    athlete["email"] = None
    # alter may be None if geburtsjahr was omitted — that's fine.
    data["alter_fuer_interpretation"] = result.test_run.athlete.alter
    out_path.write_text(json.dumps(data, indent=2, default=str, ensure_ascii=False))
    return out_path
