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
    """Return Z1..Z6 with suggested boundaries from lactate curve.

    Heuristic (transparent, not fixed mmol cutoffs — see spec):
      Z2 upper: v at 2.0 mmol/L
      Z3 upper: v at 3.0 mmol/L
      Z4 upper: v at 4.0 mmol/L
      Z5 upper: v_max (aliquot-corrected)
      Z6: above v_max (no upper bound)
    """
    v_lk2 = _intersection_lookup(rows, 2.0)
    v_lk3 = _intersection_lookup(rows, 3.0)
    v_lk4 = _intersection_lookup(rows, 4.0)

    # (lower, upper) for Z2..Z6
    bounds = [
        (None,   v_lk2),
        (v_lk2,  v_lk3),
        (v_lk3,  v_lk4),
        (v_lk4,  v_max),
        (v_max,  None),
    ]

    zones: list[TrainingZone] = []
    for (name, ziel, rpe_lo, rpe_hi), (lo, hi) in zip(ZONE_META[1:], bounds):
        zones.append(_zone(name, ziel, rpe_lo, rpe_hi, lo, hi, hf_linear, is_lauf))

    z1 = TrainingZone(
        name="Z1",
        ziel="aktive Regeneration",
        rpe_min=0, rpe_max=2,
        intensitaet_min=None, intensitaet_max=None,
        pace_min_min_per_km=None, pace_max_min_per_km=None,
        herzfrequenz_min=None, herzfrequenz_max=None,
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
