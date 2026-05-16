from __future__ import annotations

from ld.protocols._common import (
    LAKTAT_TARGETS,
    _pace_min_per_km,
    fit_cubic_laktat,
    fit_linear_hf,
    compute_vmax,
    intersection_table,
)
from ld.types import (
    Athlete,
    Coaching,
    CubicFit,
    LinearFit,
    TestRun,
    TestStep,
    Testprotokoll,
)
from datetime import date


# RPE on Borg CR10 (0-10) — Anna 2026-05-13 Round 2.
_RAINIER_STEPS = (
    TestStep(stufe=1, intensitaet=7.0,  herzfrequenz_bpm=133, laktat_mmol=1.9, rpe=2),
    TestStep(stufe=2, intensitaet=8.0,  herzfrequenz_bpm=141, laktat_mmol=2.8, rpe=2),
    TestStep(stufe=3, intensitaet=9.0,  herzfrequenz_bpm=150, laktat_mmol=3.0, rpe=5),
    TestStep(stufe=4, intensitaet=10.0, herzfrequenz_bpm=159, laktat_mmol=3.8, rpe=7),
    TestStep(stufe=5, intensitaet=11.0, herzfrequenz_bpm=167, laktat_mmol=5.2, rpe=8),
    TestStep(stufe=6, intensitaet=12.0, herzfrequenz_bpm=173, laktat_mmol=7.9, rpe=9),
)

_RAINIER_PROTO = Testprotokoll(
    testdatum=date(2024, 5, 23),
    uhrzeit="14:00",
    durchfuehrungsort="Laufcamp Achensee",
    testleiter="Anna-Maria Wörndle",
    geraet="Laufband Atoll Achensee",
    anfangsbelastung=7.0,
    stufeninkrement=1.0,
    stufendauer_min=4.0,
    stufenlaenge_m=None,
    besonderheiten="1% Steigung",
    letzte_stufe_vollstaendig=False,
    dauer_letzte_stufe_min=1.75,
    ausbelastung=True,
)

_RAINIER_ATHLETE = Athlete(
    sportart="lauf",
    vorname="Rainier",
    name="Matzinger",
    geburtsjahr=1968,
    geschlecht="m",
    gewicht_kg=71.5,
    groesse_m=1.79,
    trainingsziel="",
    wettkampfziel="",
    trainingsumfang_wo="",
    leistungsniveau="",
)

_RAINIER_RUN = TestRun(
    athlete=_RAINIER_ATHLETE,
    testprotokoll=_RAINIER_PROTO,
    steps=_RAINIER_STEPS,
    coaching=Coaching("", "", "", "", "", ""),
)


def test_hf_linear_fit():
    fit = fit_linear_hf(_RAINIER_STEPS)
    assert abs(fit.slope - 8.2) < 0.3
    assert abs(fit.intercept - 75.9) < 1.0


def test_cubic_passes_through_data_approximately():
    fit = fit_cubic_laktat(_RAINIER_STEPS)
    for s in _RAINIER_STEPS:
        assert abs(fit.predict(s.intensitaet) - s.laktat_mmol) < 0.6


def test_pace_conversion():
    assert _pace_min_per_km(12.0) == "05:00"
    assert _pace_min_per_km(10.0) == "06:00"
    assert _pace_min_per_km(11.368) == "05:16" or _pace_min_per_km(11.368) == "05:17"


def test_vmax_aliquot():
    v = compute_vmax(_RAINIER_RUN)
    assert abs(v - 11.4375) < 0.001


def test_vmax_complete():
    from dataclasses import replace
    proto = replace(_RAINIER_PROTO, letzte_stufe_vollstaendig=True, dauer_letzte_stufe_min=None)
    run = replace(_RAINIER_RUN, testprotokoll=proto)
    v = compute_vmax(run)
    assert abs(v - 12.0) < 0.001


def test_intersection_rainier():
    cubic = fit_cubic_laktat(_RAINIER_STEPS)
    hf = fit_linear_hf(_RAINIER_STEPS)
    rows = intersection_table(cubic, hf, 7.0, 12.0, is_lauf=True)
    by_lak = {r.laktat: r for r in rows}

    assert by_lak[2.0].intensitaet is not None
    assert abs(by_lak[2.0].intensitaet - 7.064) < 0.01
    assert abs(by_lak[2.5].intensitaet - 7.658) < 0.01
    assert abs(by_lak[3.0].intensitaet - 8.707) < 0.01
    assert abs(by_lak[4.0].intensitaet - 10.230) < 0.01
    assert abs(by_lak[6.0].intensitaet - 11.368) < 0.01
    assert abs(by_lak[8.0].intensitaet - 12.023) < 0.01


def test_intersection_hf_rainier():
    cubic = fit_cubic_laktat(_RAINIER_STEPS)
    hf = fit_linear_hf(_RAINIER_STEPS)
    rows = intersection_table(cubic, hf, 7.0, 12.0, is_lauf=True)
    by_lak = {r.laktat: r for r in rows}

    assert abs(by_lak[4.0].herzfrequenz_bpm - 159.82) < 1
    assert abs(by_lak[6.0].herzfrequenz_bpm - 169.15) < 1


def test_below_range_rows_are_none():
    """Per Anna 2026-05-13 feedback: targets without a valid in-range root return
    a row with all values None. The report layer drops these entirely — no
    floor values, no `-` placeholders, no extrapolated fantasy numbers."""
    cubic = fit_cubic_laktat(_RAINIER_STEPS)
    hf = fit_linear_hf(_RAINIER_STEPS)
    rows = intersection_table(cubic, hf, 7.0, 12.0, is_lauf=True)
    by_lak = {r.laktat: r for r in rows}
    # Rainier's lactate starts at 1.9 mmol — 1.0 and 1.5 have no in-range root.
    for target in (1.0, 1.5):
        assert by_lak[target].intensitaet is None
        assert by_lak[target].herzfrequenz_bpm is None
        assert by_lak[target].pace_min_per_km is None


def test_intersection_picks_larger_root_when_multiple():
    """Per Anna 2026-05-13 feedback: when a cubic has multiple in-range roots
    for a target, the LARGER x is the physiologically relevant crossing.

    Construct a synthetic cubic with a known double-crossing at lactate=2.0:
      f(x) = (x - 8)(x - 11)(x - 14) / 6 + 2
    Roots at x=8, 11, 14 with three crossings of 2.0 in [7, 15]; we want 14.
    """
    # Expand: (x-8)(x-11)(x-14) = x^3 - 33x^2 + 354x - 1232
    # Divide by 6 → coefficients
    cubic = CubicFit(a=1/6, b=-33/6, c=354/6, d=-1232/6 + 2.0)
    hf = LinearFit(slope=10.0, intercept=80.0)
    rows = intersection_table(cubic, hf, 7.0, 15.0, is_lauf=False)
    by_lak = {r.laktat: r for r in rows}
    # The three real roots of f(x)-2.0=0 are 8, 11, 14; all in [7, 15.0 + 20%=16.6].
    # We must pick the LARGEST.
    assert by_lak[2.0].intensitaet is not None
    assert abs(by_lak[2.0].intensitaet - 14.0) < 1e-3


def test_laktat_targets():
    assert LAKTAT_TARGETS == (1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 6.0, 8.0)
