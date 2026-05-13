from __future__ import annotations

import numpy as np

from ld.errors import LDInputError
from ld.types import CubicFit, IntersectionRow, LinearFit, TestRun, TestStep


LAKTAT_TARGETS: tuple[float, ...] = (1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 6.0, 8.0)


def fit_cubic_laktat(steps: tuple[TestStep, ...]) -> CubicFit:
    """Degree-3 polynomial fit of laktat vs intensitaet, in intensitaet-space."""
    xs = np.array([s.intensitaet for s in steps if s.laktat_mmol is not None], dtype=float)
    ys = np.array([s.laktat_mmol for s in steps if s.laktat_mmol is not None], dtype=float)
    if len(xs) < 4:
        raise LDInputError(
            f"Mindestens 4 Laktatwerte für die kubische Anpassung benötigt; "
            f"gefunden: {len(xs)}."
        )
    # np.polyfit returns [a, b, c, d] for ax^3 + bx^2 + cx + d
    a, b, c, d = np.polyfit(xs, ys, deg=3)
    return CubicFit(a=float(a), b=float(b), c=float(c), d=float(d))


def fit_linear_hf(steps: tuple[TestStep, ...]) -> LinearFit:
    """Linear fit of HF vs intensitaet."""
    xs = np.array([s.intensitaet for s in steps if s.herzfrequenz_bpm is not None], dtype=float)
    ys = np.array([s.herzfrequenz_bpm for s in steps if s.herzfrequenz_bpm is not None], dtype=float)
    if len(xs) < 2:
        raise LDInputError(
            f"Mindestens 2 Herzfrequenzwerte für die lineare Anpassung benötigt; "
            f"gefunden: {len(xs)}."
        )
    slope, intercept = np.polyfit(xs, ys, deg=1)
    return LinearFit(slope=float(slope), intercept=float(intercept))


def compute_vmax(test_run: TestRun) -> float:
    """Aliquot calculation for max intensity.
    If last step complete: v_max = last step's intensitaet.
    If last step incomplete: v_max = prev_step + (dauer_letzte / stufendauer) * inkrement.
    """
    proto = test_run.testprotokoll
    steps = test_run.steps
    last = steps[-1]
    if proto.letzte_stufe_vollstaendig:
        return float(last.intensitaet)
    if proto.dauer_letzte_stufe_min is None:
        raise LDInputError(
            "Letzte Stufe ist unvollständig, aber 'Dauer letzte Stufe' fehlt."
        )
    if proto.dauer_letzte_stufe_min >= proto.stufendauer_min:
        return float(last.intensitaet)
    base = steps[-2].intensitaet if len(steps) >= 2 else proto.anfangsintensitaet - proto.stufeninkrement
    fraction = proto.dauer_letzte_stufe_min / proto.stufendauer_min
    return float(base + fraction * proto.stufeninkrement)


def intersection_table(
    cubic: CubicFit,
    hf_linear: LinearFit,
    intensitaet_min: float,
    intensitaet_max: float,  # last *measured* step's intensity (not aliquot v_max)
    is_lauf: bool,
) -> tuple[IntersectionRow, ...]:
    """For each fixed lactate target, find the smallest real root of cubic(x)=target
    in [intensitaet_min, intensitaet_max + 20%].
    Below-range roots → floor at intensitaet_min - 1 (matches historical xlsx behavior).
    Above-range → None.
    """
    rows: list[IntersectionRow] = []
    # 20% extrapolation window covers lactate values just beyond last measured step
    upper = intensitaet_max + 0.2 * (intensitaet_max - intensitaet_min)
    poly = np.poly1d([cubic.a, cubic.b, cubic.c, cubic.d])

    for target in LAKTAT_TARGETS:
        shifted = poly - target
        roots = shifted.roots
        real_positive = sorted(
            r.real for r in roots
            if abs(r.imag) < 1e-6 and r.real > 0
        )
        in_range = [r for r in real_positive if intensitaet_min <= r <= upper]
        if in_range:
            x = in_range[0]
        elif real_positive and max(real_positive) < intensitaet_min:
            # All roots below range → floor display (start - 1), matches historical
            x = intensitaet_min - 1.0
        else:
            x = None

        if x is None:
            rows.append(IntersectionRow(target, None, None, None))
            continue

        hf = int(round(hf_linear.predict(x)))
        pace = _pace_min_per_km(x) if is_lauf and x > 0 else None
        rows.append(IntersectionRow(
            laktat=target,
            intensitaet=round(float(x), 3),
            pace_min_per_km=pace,
            herzfrequenz_bpm=hf,
        ))
    return tuple(rows)


def _pace_min_per_km(v_km_h: float) -> str:
    """Convert km/h to pace as 'MM:SS' min/km."""
    if v_km_h <= 0:
        return "—"
    total_sec = 3600.0 / v_km_h
    minutes = int(total_sec // 60)
    seconds = int(round(total_sec - minutes * 60))
    if seconds == 60:
        minutes += 1
        seconds = 0
    return f"{minutes:02d}:{seconds:02d}"


def diagram_title(test_run: TestRun) -> str:
    """Spec format: '<Sportart>_<Start>_<Inkrement>_<Stufendauer>; <Datum>'."""
    proto = test_run.testprotokoll
    sportart_label = {
        "lauf": "Lauf",
        "rad": "Rad",
        "triathlon-rad": "Triathlon-Rad",
        "triathlon-lauf": "Triathlon-Lauf",
        "unspezifisch": "Unspezifisch",
    }[test_run.athlete.sportart]
    start = _trim_num(proto.anfangsintensitaet)
    inc = _trim_num(proto.stufeninkrement)
    dur = _trim_num(proto.stufendauer_min)
    datum = proto.testdatum.strftime("%d.%m.%Y")
    return f"{sportart_label}_{start}_{inc}_{dur}; {datum}"


def _trim_num(x: float) -> str:
    return str(int(x)) if float(x).is_integer() else str(x)
