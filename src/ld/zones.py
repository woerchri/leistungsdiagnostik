from __future__ import annotations

from ld.protocols._common import _pace_min_per_km
from ld.types import IntersectionRow, LinearFit, TrainingZone


# Zone metadata: (name, ziel, rpe_min, rpe_max) — RPE on 0-10 scale (spec docx)
ZONE_META: tuple[tuple[str, str, int, int], ...] = (
    ("Z1", "aktive Regeneration",     0, 2),
    ("Z2", "aerobe Basis",            3, 4),
    ("Z3", "metabolische Stabilität", 5, 6),
    ("Z4", "Schwellenleistung",       7, 8),
    ("Z5", "VO2max-Reize",            9, 9),
    ("Z6", "neuromuskulär",           10, 10),
)


def _intersection_lookup(rows: tuple[IntersectionRow, ...], target_lk: float) -> float | None:
    for r in rows:
        if abs(r.laktat - target_lk) < 1e-9:
            return r.intensitaet
    return None


def suggest_zones(
    rows: tuple[IntersectionRow, ...],
    hf_linear: LinearFit,
    v_max: float,
    is_lauf: bool,
) -> tuple[TrainingZone, ...]:
    """Return suggested training zones from the lactate curve.

    Heuristic (Orientierungspunkte — NOT fixed mmol thresholds; see spec
    `samples/26_05_LD_Dateneingabe.docx` "Keine rein fixen mmol-Schwellen
    verwenden"):

      Z2 upper: v at 2.0 mmol/L       (aerobic base ceiling — orientation)
      Z3 upper: v at 3.0 mmol/L       (metabolic stability — orientation)
      Z4 upper: v at 4.0 mmol/L       (threshold — orientation)
      Z5 upper: v_max (aliquot)
      Z6:       above v_max — rendered as "MAX"

    These are SUGGESTIONS. The trainer confirms or adjusts via
    `/ld-report` dialogue or `ld.zones_cli`.

    Z1 (active recovery) is only emitted when Z2 has a valid upper bound;
    its values render as `< v_z2_upper` etc. on the report.

    Z6 is flagged `is_max_zone=True`; the report renders Intensität / HF /
    Pace as the literal word "MAX" (per Anna 2026-05-13 feedback).
    """
    v_lk2 = _intersection_lookup(rows, 2.0)
    v_lk3 = _intersection_lookup(rows, 3.0)
    v_lk4 = _intersection_lookup(rows, 4.0)

    # (lower, upper) for Z2..Z5 — Z6 is constructed separately as the max-zone
    bounds_z2_z5 = [
        (None,   v_lk2),
        (v_lk2,  v_lk3),
        (v_lk3,  v_lk4),
        (v_lk4,  v_max),
    ]

    zones: list[TrainingZone] = []
    for (name, ziel, rpe_lo, rpe_hi), (lo, hi) in zip(ZONE_META[1:5], bounds_z2_z5):
        zones.append(_zone(name, ziel, rpe_lo, rpe_hi, lo, hi, hf_linear, is_lauf))

    # Z6: above v_max — values rendered as "MAX" in report
    z6_name, z6_ziel, z6_rpe_lo, z6_rpe_hi = ZONE_META[5]
    z6 = TrainingZone(
        name=z6_name,
        ziel=z6_ziel,
        rpe_min=z6_rpe_lo,
        rpe_max=z6_rpe_hi,
        intensitaet_min=round(v_max, 3),
        intensitaet_max=None,
        pace_min_min_per_km=None,
        pace_max_min_per_km=(_pace_min_per_km(v_max) if is_lauf else None),
        herzfrequenz_min=int(round(hf_linear.predict(v_max))),
        herzfrequenz_max=None,
        is_max_zone=True,
    )
    zones.append(z6)

    # Z1 only when Z2 has a valid upper bound (otherwise no anchor for "<")
    if v_lk2 is None:
        return tuple(zones)

    z1 = TrainingZone(
        name="Z1",
        ziel="aktive Regeneration",
        rpe_min=0, rpe_max=2,
        intensitaet_min=None,
        intensitaet_max=round(v_lk2, 3),
        # Z1 pace: slower than v_lk2 pace, i.e. pace > pace(v_lk2)
        pace_min_min_per_km=(_pace_min_per_km(v_lk2) if is_lauf else None),
        pace_max_min_per_km=None,
        herzfrequenz_min=None,
        herzfrequenz_max=int(round(hf_linear.predict(v_lk2))),
        is_open_lower=True,
    )
    return (z1, *zones)


def _zone(
    name: str, ziel: str, rpe_lo: int, rpe_hi: int,
    intens_lo: float | None, intens_hi: float | None,
    hf_linear: LinearFit, is_lauf: bool,
) -> TrainingZone:
    return TrainingZone(
        name=name,
        ziel=ziel,
        rpe_min=rpe_lo,
        rpe_max=rpe_hi,
        intensitaet_min=round(intens_lo, 3) if intens_lo is not None else None,
        intensitaet_max=round(intens_hi, 3) if intens_hi is not None else None,
        # pace_min = slowest pace = lowest speed = lower bound
        pace_min_min_per_km=(_pace_min_per_km(intens_hi) if is_lauf and intens_hi else None),
        pace_max_min_per_km=(_pace_min_per_km(intens_lo) if is_lauf and intens_lo else None),
        herzfrequenz_min=(
            int(round(hf_linear.predict(intens_lo))) if intens_lo is not None else None
        ),
        herzfrequenz_max=(
            int(round(hf_linear.predict(intens_hi))) if intens_hi is not None else None
        ),
    )
