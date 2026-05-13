from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from ld import io_input, protocols


FIXTURES = Path(__file__).parent / "fixtures" / "lauf"


def test_rainier_snapshot():
    test_run = io_input.parse_input(FIXTURES / "rainier.xlsx")
    result = protocols.analyze(test_run)
    actual = json.loads(json.dumps(asdict(result), default=str))
    expected = json.loads((FIXTURES / "rainier_expected.json").read_text())

    assert abs(actual["v_max"] - 11.4375) < 0.01

    for a_row, e_row in zip(actual["intersections"], expected["intersections"]):
        if a_row["intensitaet"] is not None and e_row["intensitaet"] is not None:
            assert abs(float(a_row["intensitaet"]) - float(e_row["intensitaet"])) < 0.05, \
                f"lak={a_row['laktat']}: v mismatch {a_row['intensitaet']} vs {e_row['intensitaet']}"


def test_rainier_pflichtpruefungen():
    test_run = io_input.parse_input(FIXTURES / "rainier.xlsx")
    result = protocols.analyze(test_run)
    names = {p.name for p in result.pflichtpruefungen}
    assert "letzte_stufe" in names
    assert "laktatsprung" in names
    # HF is monotonic in Rainier data
    hf_check = next(p for p in result.pflichtpruefungen if p.name == "hf_monotonic")
    assert hf_check.ok

    # Last step is incomplete → flagged
    letzte = next(p for p in result.pflichtpruefungen if p.name == "letzte_stufe")
    assert not letzte.ok
