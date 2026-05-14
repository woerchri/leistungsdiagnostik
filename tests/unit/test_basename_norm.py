"""Tests for the XY_LD_Sportart_JJ_MM_TT output basename normalization
(Anna 2026-05-13 feedback)."""
from __future__ import annotations

from datetime import date

from ld.run import _normalize_basename
from ld.types import Athlete, Coaching, TestRun, TestStep, Testprotokoll


def _make_run(*, sportart="lauf", vorname="Rainier", name="Matzinger",
              testdatum=date(2024, 5, 23)) -> TestRun:
    return TestRun(
        athlete=Athlete(
            sportart=sportart, vorname=vorname, name=name,
            geburtsjahr=1968, geschlecht="m", gewicht_kg=70.0, groesse_m=1.79,
            trainingsziel="", wettkampfziel="", trainingsumfang_wo="",
            leistungsniveau="", email=None,
        ),
        testprotokoll=Testprotokoll(
            testdatum=testdatum, uhrzeit="14:00", durchfuehrungsort="X",
            testleiter="Y", geraet="Z", anfangsbelastung=7.0,
            stufeninkrement=1.0, stufendauer_min=4.0, stufenlaenge_m=None,
            besonderheiten="", letzte_stufe_vollstaendig=True,
            dauer_letzte_stufe_min=None, ausbelastung=True,
        ),
        steps=(TestStep(stufe=1, intensitaet=7.0, herzfrequenz_bpm=130, laktat_mmol=1.5, rpe=9),),
        coaching=Coaching("", "", "", "", "", ""),
    )


def test_rainier_lauf_24_05_23():
    assert _normalize_basename(_make_run()) == "RM_LD_Lauf_24_05_23"


def test_sport_label_capitalization():
    assert _normalize_basename(_make_run(sportart="rad", vorname="Anna", name="Wörndle")) == "AW_LD_Rad_24_05_23"
    assert _normalize_basename(_make_run(sportart="triathlon-lauf")) == "RM_LD_Triathlon-Lauf_24_05_23"
    assert _normalize_basename(_make_run(sportart="triathlon-rad")) == "RM_LD_Triathlon-Rad_24_05_23"
    assert _normalize_basename(_make_run(sportart="unspezifisch")) == "RM_LD_Unspezifisch_24_05_23"


def test_date_zero_padded():
    """JJ_MM_TT — single-digit months/days get zero-padded."""
    run = _make_run(testdatum=date(2026, 1, 5))
    assert _normalize_basename(run) == "RM_LD_Lauf_26_01_05"


def test_year_century_boundary():
    """Year takes the last two digits; 2099 → 99, 2100 → 00."""
    assert _normalize_basename(_make_run(testdatum=date(2099, 6, 12))) == "RM_LD_Lauf_99_06_12"
    assert _normalize_basename(_make_run(testdatum=date(2100, 6, 12))) == "RM_LD_Lauf_00_06_12"


def test_initials_uppercased():
    """Even if input is lowercase, the initials are upper-case in the basename."""
    run = _make_run(vorname="anna", name="wörndle")
    assert _normalize_basename(run) == "AW_LD_Lauf_24_05_23"
