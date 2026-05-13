from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from ld.types import AnalysisResult


def write_redacted(result: AnalysisResult, out_path: Path) -> Path:
    data = asdict(result)
    athlete = data["test_run"]["athlete"]
    athlete["vorname"] = "Athlet:in"
    athlete["name"] = "X"
    # Keep derived age, remove identifying year
    data["alter_fuer_interpretation"] = result.test_run.athlete.alter
    athlete["geburtsjahr"] = None
    out_path.write_text(json.dumps(data, indent=2, default=str, ensure_ascii=False))
    return out_path
