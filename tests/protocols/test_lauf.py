from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from ld import io_input, protocols


FIXTURES = Path(__file__).parent / "fixtures" / "lauf"


def _intersections_match(actual: dict, expected: dict, tol: float = 0.05) -> None:
    """Dict-keyed comparison so the test is robust to rows dropped because of
    no in-range root (per Anna 2026-05-13 feedback). Only checks targets where
    BOTH actual and expected have a non-None intensitaet."""
    a_by = {r["laktat"]: r for r in actual["intersections"]}
    e_by = {r["laktat"]: r for r in expected["intersections"]}
    for lak, e_row in e_by.items():
        if e_row["intensitaet"] is None:
            assert a_by.get(lak, {}).get("intensitaet") is None, \
                f"lak={lak}: expected None, got {a_by.get(lak)}"
            continue
        a_row = a_by.get(lak)
        assert a_row is not None and a_row["intensitaet"] is not None, \
            f"lak={lak}: expected {e_row['intensitaet']}, got missing/None"
        assert abs(float(a_row["intensitaet"]) - float(e_row["intensitaet"])) < tol, \
            f"lak={lak}: v mismatch {a_row['intensitaet']} vs {e_row['intensitaet']}"


def test_rainier_snapshot():
    test_run = io_input.parse_input(FIXTURES / "rainier.xlsx")
    result = protocols.analyze(test_run)
    actual = json.loads(json.dumps(asdict(result), default=str))
    expected = json.loads((FIXTURES / "rainier_expected.json").read_text())

    assert abs(actual["v_max"] - 11.4375) < 0.01
    _intersections_match(actual, expected)


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


def test_sarah_snapshot():
    """Sarah Seckendorf 23.05.2024 — last step complete, v_max=13.0."""
    test_run = io_input.parse_input(FIXTURES / "sarah.xlsx")
    result = protocols.analyze(test_run)
    actual = json.loads(json.dumps(asdict(result), default=str))
    expected = json.loads((FIXTURES / "sarah_expected.json").read_text())

    assert abs(actual["v_max"] - 13.0) < 0.01
    _intersections_match(actual, expected)


def test_sarah_pflichtpruefungen():
    """Sarah's test is fully complete — all pflichtpruefungen should pass."""
    test_run = io_input.parse_input(FIXTURES / "sarah.xlsx")
    result = protocols.analyze(test_run)

    letzte = next(p for p in result.pflichtpruefungen if p.name == "letzte_stufe")
    assert letzte.ok, "Last step is complete, should not be flagged"

    ausbelastung = next(p for p in result.pflichtpruefungen if p.name == "ausbelastung")
    assert ausbelastung.ok
